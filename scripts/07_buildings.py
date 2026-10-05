"""Pre-event building footprints vs the post-event drone ortho, per site, as at Taw Kye.

1. Merge OSM and VIDA (Microsoft ML) footprints; a VIDA footprint overlapping an OSM one by
   > 30 % of the smaller is a duplicate and is dropped.
2. Footprints and ortho disagree by a few metres. Find the shift (+-8 m, 0.25 m steps) that
   maximises the grey-roof fraction inside footprints away from the landslides (> 20 m), on a
   0.25 m class grid. Shifted footprints are in the ortho's frame, the frame of the outlines.
3. Per footprint, at NATIVE resolution: fraction of vegetation / soil / grey / shadow inside the
   footprint shrunk by 0.5 m, and overlap with landslide and outwash outlines.
4. Status:
     destroyed    >= 30 % inside a landslide and no roof left (grey < 0.30, soil >= 0.40)
     damaged      >= 30 % inside a landslide, roof still visible
     edge         within 10 m of a landslide
     outwash      >= 30 % inside the sediment-covered fields (standing in sediment or water). Where the outwash
                  runs through a village and its outline excludes footprints (sites.py outwash_minus_buildings),
                  the test is >= 30 % of a 3 m ring around the footprint under sediment
     clear        otherwise;  not_surveyed if outside the flight
   data/<site>/inventory/building_overrides.csv (visual check of every destroyed / damaged / edge /
   outwash chip) replaces the automatic status where the interpreter disagreed.
"""
import csv, json, sys
import numpy as np, rasterio, geopandas as gpd, pandas as pd
from rasterio import features
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import from_bounds, Window
from shapely.affinity import translate
from sites import SITES, d, ee_dir

RES = 0.25
SHIFTS = np.arange(-8, 8.01, 0.25)


def merged_footprints(fp, EE):
    osm = gpd.read_file(EE / "osm_buildings.geojson").to_crs(32647)
    osm = osm[osm.intersects(fp.buffer(20))]
    osm = gpd.GeoDataFrame({"source": "OSM", "src_id": osm["osm_id"].astype(str)}, geometry=osm.geometry.buffer(0), crs=32647)
    vida = gpd.read_file(EE / "vida_buildings.geojson").to_crs(32647)
    vida = vida[vida.intersects(fp.buffer(20))]
    vida = gpd.GeoDataFrame({"source": "VIDA/" + vida["bf_source"].astype(str), "src_id": vida["id"].astype(str)},
                            geometry=vida.geometry.buffer(0), crs=32647)
    j = gpd.sjoin(vida, osm, how="left", predicate="intersects")
    dup = set()
    for i, r in j.dropna(subset=["index_right"]).iterrows():
        a, b = vida.geometry[i], osm.geometry[int(r["index_right"])]
        if a.intersection(b).area > 0.3 * min(a.area, b.area):
            dup.add(i)
    vida = vida.drop(index=list(dup))
    b = pd.concat([osm, vida], ignore_index=True)
    b = b[b.geometry.area >= 4].reset_index(drop=True)
    print(f"OSM {len(osm)}, VIDA kept {len(vida)} (dropped {len(dup)} duplicates) -> {len(b)}")
    return b


def class_grid(site, bounds):
    x0, y0, x1, y1 = bounds
    W, H = int((x1 - x0) / RES), int((y1 - y0) / RES)
    T = from_origin(x0, y1, RES, RES)
    with rasterio.open(d(site, "class", "class.tif")) as s, \
         WarpedVRT(s, crs="EPSG:32647", transform=T, width=W, height=H, resampling=Resampling.mode, nodata=0) as v:
        return v.read(1), T


def best_shift(site, b, slides, fp):
    sel = b[b.geometry.within(fp) & (b.geometry.distance(slides) > 20)]
    x0, y0, x1, y1 = sel.total_bounds
    cls, T = class_grid(site, (x0 - 10, y0 - 10, x1 + 10, y1 + 10))
    grey = (cls == 3).astype(np.float32)
    lab = features.rasterize([(g, 1) for g in sel.geometry], out_shape=cls.shape, transform=T, dtype="uint8")
    rr, cc = np.nonzero(lab)
    best = (-1, 0, 0)
    for dx in SHIFTS:
        for dy in SHIFTS:
            r2 = rr - int(round(dy / RES))
            c2 = cc + int(round(dx / RES))
            ok = (r2 >= 0) & (r2 < cls.shape[0]) & (c2 >= 0) & (c2 < cls.shape[1])
            s = grey[r2[ok], c2[ok]].mean()
            if s > best[0]:
                best = (s, dx, dy)
    base = grey[rr, cc].mean()
    print(f"{site}: {len(sel)} footprints; grey fraction {base:.3f} unshifted -> {best[0]:.3f} at dE {best[1]:+.2f} dN {best[2]:+.2f} m")
    return {"dE": float(best[1]), "dN": float(best[2]), "grey_before": round(float(base), 3),
            "grey_after": round(float(best[0]), 3), "n_used": int(len(sel))}


def fractions(src, geom_ll):
    w = from_bounds(*geom_ll.bounds, transform=src.transform).round_offsets().round_lengths()
    w = w.intersection(Window(0, 0, src.width, src.height))
    cls = src.read(1, window=w)
    m = features.geometry_mask([geom_ll], out_shape=cls.shape, transform=src.window_transform(w), invert=True)
    v = cls[m & (cls > 0)]
    if v.size == 0:
        return None
    return {k: float((v == i).mean()) for k, i in (("veg", 1), ("soil", 2), ("grey", 3), ("dark", 4))}


def run(site):
    inv = d(site, "inventory")
    fp = gpd.read_file(inv / "footprint.geojson").to_crs(32647).geometry.iloc[0]
    fp_in = fp.buffer(-1)
    b = merged_footprints(fp, ee_dir(site))
    b["bid"] = [f"{site.upper()}-B{i:04d}" for i in range(len(b))]
    out = gpd.read_file(inv / "landslides_utm.gpkg")
    slides = out[out.kind == "landslide"]
    sl_union = slides.union_all()
    ow = out[out.kind == "outwash"]
    ow_union = ow.union_all() if len(ow) else None
    shift = best_shift(site, b, sl_union, fp_in)
    rows = []
    with rasterio.open(d(site, "class", "class.tif")) as src:
        for _, r in b.iterrows():
            g0 = r.geometry
            rec = {"bid": r["bid"], "source": r["source"], "src_id": r["src_id"], "area_m2": round(g0.area, 1)}
            if not g0.centroid.within(fp_in):
                rec["status"] = "not_surveyed"
                rows.append((rec, g0))
                continue
            g = translate(g0, shift["dE"], shift["dN"])
            inner = g.buffer(-0.5)
            if inner.is_empty or inner.area < 2:
                inner = g
            fr = fractions(src, gpd.GeoSeries([inner], crs=32647).to_crs(4326).iloc[0])
            ov = g.intersection(sl_union).area / g.area
            if ow_union is None:
                ovw = 0.0
            elif SITES[site].get("outwash_minus_buildings"):
                ring = g.buffer(3.0).difference(g)
                ovw = ring.intersection(ow_union).area / ring.area
            else:
                ovw = g.intersection(ow_union).area / g.area
            dist = g.distance(sl_union)
            hit = slides[slides.intersects(g)]
            near = slides.loc[slides.distance(g).idxmin(), "id"] if dist <= 10 else ""
            rec.update(overlap=round(ov, 3), overlap_outwash=round(ovw, 3), dist_m=round(dist, 1),
                       landslide=",".join(hit.sort_values("id")["id"]) if len(hit) else near,
                       **{f"f_{k}": round(v, 3) for k, v in (fr or {}).items()})
            if fr is None:
                rec["status"] = "not_surveyed"
            elif ov >= 0.3:
                rec["status"] = "destroyed" if (fr["grey"] < 0.30 and fr["soil"] >= 0.40) else "damaged"
            elif dist <= 10:
                rec["status"] = "edge"
            elif ovw >= 0.3:
                rec["status"] = "outwash"
            else:
                rec["status"] = "clear"
            rows.append((rec, g))
    df = gpd.GeoDataFrame([r for r, _ in rows], geometry=[g for _, g in rows], crs=32647)
    df["status_auto"] = df["status"]
    df["note"] = ""
    ov_p = inv / "building_overrides.csv"
    if ov_p.exists():
        n = 0
        for o in csv.DictReader(open(ov_p, encoding="utf-8")):
            m = df["bid"] == o["bid"]
            if m.any():
                df.loc[m, "status"] = o["status"]
                df.loc[m, "note"] = o.get("note", "")
                n += 1
        print("applied", n, "overrides")
    df.to_file(inv / "buildings_utm.gpkg", driver="GPKG")
    df.to_crs(4326).to_file(inv / "buildings.geojson", driver="GeoJSON")
    json.dump(shift, open(inv / "footprint_shift.json", "w"), indent=1)
    print(df["status"].value_counts().to_string())


if __name__ == "__main__":
    for s in (sys.argv[1:] or list(SITES)):
        run(s)
