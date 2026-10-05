"""Landslide inventory: native-resolution outlines inside the interpreter envelopes.

For every envelope (data/<site>/inventory/envelopes.geojson, priority order - an earlier
envelope keeps any overlap), as at Taw Kye:
  1. read the 1 m-majority bare-ground mask and the class raster at native resolution
  2. keep bare pixels inside the envelope, minus every `exclude` area (ground already bare
     on the 10 Jan 2026 Esri Vivid image: clearings, tracks, yards)
  3. drop bare specks < 10 m2 and fill holes < 10 m2 (roof-sized gaps, shadows)
  4. count soil/debris vs grey (scoured rock, roofs, grey mud) pixels -> areas
  5. vectorise, simplify 0.1 m
`outwash` envelopes go through the same steps but are kept as their own kind. Where the outwash spreads through
a village (sites.py outwash_minus_buildings: Tha Byar), pre-event OSM + VIDA footprints buffered 1 m are cut out
first, so grey roofs are not counted as sediment.
A `split` envelope is a zone: its cleaned mask is cut into 8-connected components (>= 20 m2),
components within 6 m of each other are grouped (canopy and fallen trees break a scoured channel
into pieces), and each group >= 200 m2 becomes its own landslide (ids by area, largest first);
smaller ones are counted, not mapped.
Core filter (sites.py core_filter: Tha Byar, whose valley envelopes border rubber plantation): in a drawn
landslide envelope only bare components >= 500 m2, and components within 5 m of one, are kept - isolated
canopy gaps in the plantation (classified bare) are dropped.
Writes landslides.geojson (EPSG:4326), landslides_utm.gpkg and footprint.geojson per site.
"""
import sys
import numpy as np, pandas as pd, rasterio, geopandas as gpd
from rasterio import features
from rasterio.windows import from_bounds, Window
from rasterio.enums import Resampling
from scipy import ndimage as ndi
from shapely.geometry import shape, box
from shapely.ops import unary_union
from pyproj import Geod
from sites import SITES, d, ee_dir

MIN_PART_M2 = 10.0
MIN_HOLE_M2 = 10.0
SPLIT_MIN_M2 = 200.0  # smallest group kept as its own landslide inside a split zone
GROUP_M = 6.0         # components closer than this (canopy over a channel, a fallen tree) are one landslide
PART_MIN_M2 = 20.0    # components smaller than this are not grouped (tree-fall gaps, specks)
CORE_M2 = 500.0
CORE_NEAR_M = 5.0
GEOD = Geod(ellps="WGS84")


def pixel_area(ds):
    lat = (ds.bounds.top + ds.bounds.bottom) / 2
    lon = (ds.bounds.left + ds.bounds.right) / 2
    _, _, dx = GEOD.inv(lon, lat, lon + ds.res[0], lat)
    _, _, dy = GEOD.inv(lon, lat, lon, lat + ds.res[1])
    return dx * dy


def footprint(site):
    """Data footprint of the flight (alpha > 0) from its 1/16 overview, EPSG:4326."""
    with rasterio.open(d(site, "ortho", "ortho_4326.tif")) as s:
        f = 16
        a = s.read(4, out_shape=(s.height // f, s.width // f), resampling=Resampling.nearest)
        t = s.transform * s.transform.scale(s.width / a.shape[1], s.height / a.shape[0])
    return unary_union([shape(g) for g, v in features.shapes((a > 0).astype(np.uint8), transform=t) if v == 1])


def clean(mask, px_area):
    lab, n = ndi.label(mask)
    if n:
        sizes = ndi.sum_labels(np.ones_like(lab, np.uint8), lab, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes * px_area >= MIN_PART_M2
        mask = keep[lab]
    lab, n = ndi.label(~mask)
    if n:
        sizes = ndi.sum_labels(np.ones_like(lab, np.uint8), lab, index=np.arange(1, n + 1))
        edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))  # outside, not a hole
        fill = np.zeros(n + 1, bool)
        fill[1:] = sizes * px_area < MIN_HOLE_M2
        fill[edge] = False
        mask = mask | fill[lab]
    return mask


def core_filter(mask, pa):
    """Keep components >= CORE_M2 and those within CORE_NEAR_M of one (distance on a ~0.5 m block grid)."""
    lab, n = ndi.label(mask, structure=np.ones((3, 3), bool))
    if n == 0:
        return mask
    sizes = ndi.sum_labels(np.ones_like(lab, np.uint8), lab, index=np.arange(1, n + 1)) * pa
    core = np.zeros(n + 1, bool)
    core[1:] = sizes >= CORE_M2
    f = max(int(round(0.5 / np.sqrt(pa))), 1)
    H, W = mask.shape
    hh, ww = -(-H // f), -(-W // f)
    cm = np.zeros((hh * f, ww * f), bool)
    cm[:H, :W] = core[lab]
    coarse = cm.reshape(hh, f, ww, f).any((1, 3))
    near = ndi.distance_transform_edt(~coarse) * (f * np.sqrt(pa)) <= CORE_NEAR_M
    rr = np.minimum(np.arange(H) // f, hh - 1)
    cc = np.minimum(np.arange(W) // f, ww - 1)
    hit = np.unique(lab[mask & near[rr][:, cc]])
    keep = np.zeros(n + 1, bool)
    keep[hit] = True
    keep[0] = False
    out = keep[lab]
    print(f"    core filter: {n} components, kept {int(keep.sum())} ({out.sum() * pa:,.0f} of {mask.sum() * pa:,.0f} m2)", flush=True)
    return out


def split_zone(e, mask, cls, wt, pa):
    lab, n = ndi.label(mask, structure=np.ones((3, 3), bool))
    sizes = ndi.sum_labels(np.ones_like(lab, np.uint8), lab, index=np.arange(1, n + 1)) * pa
    objs = ndi.find_objects(lab)
    comps = []
    for li in np.nonzero(sizes >= PART_MIN_M2)[0] + 1:
        sl = objs[li - 1]
        m = lab[sl] == li
        c = cls[sl]
        t = wt * wt.translation(sl[1].start, sl[0].start)
        geom = unary_union([shape(g) for g, v in features.shapes(m.astype(np.uint8), mask=m, transform=t) if v == 1])
        comps.append({"geometry": geom, "area": m.sum() * pa, "soil": (m & (c == 2)).sum() * pa,
                      "grey": (m & (c == 3)).sum() * pa})
    cg = gpd.GeoDataFrame(comps, crs=4326).to_crs(32647)
    groups = gpd.GeoDataFrame(geometry=list(getattr(u := cg.buffer(GROUP_M / 2).union_all(), "geoms", [u])), crs=32647)
    cg["group"] = gpd.sjoin(gpd.GeoDataFrame(geometry=cg.representative_point(), crs=32647), groups,
                            predicate="within")["index_right"]
    agg = cg.dissolve("group", aggfunc={"area": "sum", "soil": "sum", "grey": "sum"})
    agg = agg[agg.area >= SPLIT_MIN_M2].sort_values("area", ascending=False)
    small = sizes.sum() - agg.area.sum()
    print(f"  {e['id']}: {n} components, {len(cg)} >= {PART_MIN_M2:.0f} m2 -> {len(groups)} groups, "
          f"{len(agg)} >= {SPLIT_MIN_M2:.0f} m2 ({agg.area.sum():,.0f} m2); {small:,.0f} m2 in smaller pieces not mapped",
          flush=True)
    out = []
    for k, (_, r) in enumerate(agg.iterrows(), 1):
        out.append({"id": f"{e['id']}-{k:02d}", "name": "", "kind": "landslide", "description": "",
                    "area_m2": round(r.area, 1), "soil_m2": round(r.soil, 1), "grey_m2": round(r.grey, 1),
                    "envelope_in_survey_m2": None, "geometry": r.geometry.simplify(0.1)})
        print(f"    {out[-1]['id']}: {r.area:,.0f} m2", flush=True)
    return out


def footprints_ll(site):
    """Pre-event OSM + VIDA building footprints buffered 1 m, EPSG:4326 (outwash through a village)."""
    e = ee_dir(site)
    g = pd.concat([gpd.read_file(e / f).to_crs(32647).geometry for f in ("osm_buildings.geojson", "vida_buildings.geojson")])
    return gpd.GeoSeries(g.buffer(1.0), crs=32647).union_all(), g


def run(site):
    inv = d(site, "inventory")
    bld = footprints_ll(site)[0] if SITES[site].get("outwash_minus_buildings") else None
    env = gpd.read_file(inv / "envelopes.geojson").sort_values(["priority", "id"])
    excl = env[env.kind == "exclude"].union_all() if (env.kind == "exclude").any() else None
    env = env[env.kind != "exclude"]
    fp = footprint(site)
    taken, rows = None, []
    with rasterio.open(d(site, "class", "bare.tif")) as db, rasterio.open(d(site, "class", "class.tif")) as dc:
        pa = pixel_area(db)
        for _, e in env.iterrows():
            g = e.geometry if taken is None else e.geometry.difference(taken)
            taken = e.geometry if taken is None else taken.union(e.geometry)
            if excl is not None:
                g = g.difference(excl)
            if bld is not None and e["kind"] == "outwash":
                g = g.difference(gpd.GeoSeries([bld], crs=32647).to_crs(4326).iloc[0])
            g = g.intersection(fp)
            w = from_bounds(*g.bounds, transform=db.transform).round_offsets().round_lengths()
            w = w.intersection(Window(0, 0, db.width, db.height))
            wt = db.window_transform(w)
            inside = features.rasterize([g], out_shape=(w.height, w.width), transform=wt, fill=0,
                                        default_value=1, dtype="uint8").astype(bool)
            mask = clean((db.read(1, window=w) == 1) & inside, pa) & inside
            cls = dc.read(1, window=w)
            if e.get("split", 0):
                rows += split_zone(e, mask, cls, wt, pa)
                continue
            if SITES[site].get("core_filter") and e["kind"] == "landslide":
                mask = core_filter(mask, pa)
            area = mask.sum() * pa
            parts = [shape(s) for s, v in features.shapes(mask.astype(np.uint8), mask=mask, transform=wt) if v == 1]
            poly = gpd.GeoSeries([unary_union(parts)], crs=4326).to_crs(32647).iloc[0].simplify(0.1)
            rows.append({"id": e["id"], "name": e["name"], "kind": e["kind"], "description": e["description"],
                         "area_m2": round(area, 1), "soil_m2": round((mask & (cls == 2)).sum() * pa, 1),
                         "grey_m2": round((mask & (cls == 3)).sum() * pa, 1),
                         "envelope_in_survey_m2": round(gpd.GeoSeries([g], crs=4326).to_crs(32647).area.iloc[0], 1),
                         "geometry": poly})
            print(f"  {site} {e['id']} ({e['kind']}): {area:,.0f} m2 (vector {poly.area:,.0f} m2), window {w.width}x{w.height}", flush=True)
    out = gpd.GeoDataFrame(rows, crs=32647).sort_values("id")
    out.to_file(inv / "landslides_utm.gpkg", driver="GPKG")
    out.to_crs(4326).to_file(inv / "landslides.geojson", driver="GeoJSON")
    gpd.GeoDataFrame({"site": [site]}, geometry=[fp], crs=4326).to_file(inv / "footprint.geojson", driver="GeoJSON")
    ls = out[out.kind == "landslide"]
    print(site, "landslides", len(ls), round(ls.area_m2.sum()), "m2; outwash", round(out[out.kind == "outwash"].area_m2.sum()), "m2")


if __name__ == "__main__":
    for s in (sys.argv[1:] or list(SITES)):
        run(s)
