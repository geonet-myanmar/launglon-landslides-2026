"""Terrain metrics per landslide from the Copernicus GLO-30 DEM (pre-event surface, 30 m), as at Taw Kye.

Per landslide:
  crown / toe     highest / lowest DEM point on the outline (bilinear, outline densified 2 m)
  H, L            crown-to-toe drop and horizontal distance; H/L = tan(reach angle)
  edge            crown or toe within 15 m of the edge of the flight: the scar runs on beyond the
                  survey, so H and L are minimums
  zones           area on DEM slope >= 20 deg (source), 8-20 (transport), < 8 (runout)
  ndvi_pre        mean Jan-Apr 2026 Sentinel-2 NDVI over the outline and its source zone
Also writes slope / hillshade rasters (one DEM covers both sites) and data/<site>/inventory/terrain.json.
"""
import json, sys
import numpy as np, rasterio, geopandas as gpd
from rasterio import features
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from scipy.ndimage import map_coordinates
from sites import SITES, ROOT, TYPES, NMT_NAMES, d

ZONES = [("source", 20, 90), ("transport", 8, 20), ("runout", 0, 8)]
EE = ROOT / "data/ee"


def dem_products():
    with rasterio.open(EE / "cop30_dem_utm.tif") as src:
        z = src.read(1).astype(np.float64)
        T = src.transform
        prof = src.profile
    gy, gx = np.gradient(z, T.a)
    sl = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    hs = np.sin(np.radians(45)) * np.cos(sl) + np.cos(np.radians(45)) * np.sin(sl) * np.cos(np.radians(315) - aspect)
    prof.update(dtype="float32", count=1, compress="deflate")
    slope = np.degrees(sl)
    for name, arr in (("slope_deg", slope), ("hillshade", hs)):
        with rasterio.open(EE / f"{name}.tif", "w", **prof) as o:
            o.write(arr.astype("float32"), 1)
    return z, slope, T


def names(site, g):
    if site == "kdnh":
        env = gpd.read_file(d(site, "inventory", "envelopes.geojson")).set_index("id")
        return {i: (env.loc[i, "name"], TYPES[site][i], env.loc[i, "description"]) for i in g["id"]}
    out = {}
    gu = g.set_index("id")
    for i in g["id"]:
        if i in NMT_NAMES:
            n, t, x, y, desc = NMT_NAMES[i]
            p = gpd.GeoSeries([Point(x, y)], crs=4326).to_crs(32647).iloc[0]
            dist = gu.loc[i].geometry.distance(p)
            assert dist < 30, f"{i} is {dist:.0f} m from where it was named - split-zone numbering changed; update NMT_NAMES"
            out[i] = (n, t, desc)
        else:
            out[i] = ("Minor scar", "minor", "Small scar or channel fragment.")
    return out


def run(site, z, slope, T):
    tr = rasterio.transform.AffineTransformer(T)
    with rasterio.open(EE / "s2_ndvi_pre_2026JanApr.tif") as s:
        ndvi = s.read(1).astype(np.float64)
        tr_n = rasterio.transform.AffineTransformer(s.transform)

    def sample(arr, xs, ys, t=tr):
        r, c = t.rowcol(xs, ys, op=lambda v: v)  # fractional, pixel-corner based -> shift to centres
        return map_coordinates(arr, [np.asarray(r) - 0.5, np.asarray(c) - 0.5], order=1, mode="nearest")

    zone_polys = {}
    for name, lo, hi in ZONES:
        m = ((slope >= lo) & (slope < hi)).astype(np.uint8)
        zone_polys[name] = unary_union([shape(g) for g, v in features.shapes(m, transform=T) if v == 1])
    edge = gpd.read_file(d(site, "inventory", "footprint.geojson")).to_crs(32647).geometry.iloc[0].boundary
    g = gpd.read_file(d(site, "inventory", "landslides_utm.gpkg"))
    g = g[g.kind == "landslide"]
    nm = names(site, g)
    out = []
    for _, r in g.iterrows():
        geom = r.geometry
        pts = []
        for p in getattr(geom, "geoms", [geom]):
            n = max(int(p.exterior.length / 2), 4)
            pts += [p.exterior.interpolate(i / n, normalized=True) for i in range(n)]
        xs = np.array([p.x for p in pts])
        ys = np.array([p.y for p in pts])
        zz = sample(z, xs, ys)
        i_hi, i_lo = int(zz.argmax()), int(zz.argmin())
        crown, toe = Point(xs[i_hi], ys[i_hi]), Point(xs[i_lo], ys[i_lo])
        H = float(zz[i_hi] - zz[i_lo])
        L = float(crown.distance(toe))
        azim = (np.degrees(np.arctan2(toe.x - crown.x, toe.y - crown.y)) + 360) % 360
        minx, miny, maxx, maxy = geom.bounds
        gxs, gys = np.meshgrid(np.arange(minx + 1, maxx, 2.0), np.arange(maxy - 1, miny, -2.0))
        inside = features.geometry_mask([geom], out_shape=gxs.shape, invert=True,
                                        transform=rasterio.transform.from_origin(minx, maxy, 2.0, 2.0))
        sl = sample(slope, gxs[inside], gys[inside])
        nd = sample(ndvi, gxs[inside], gys[inside], tr_n)
        name, typ, desc = nm[r["id"]]
        out.append({"id": r["id"], "name": name, "type": typ, "description": desc,
                    "crown_z": round(float(zz[i_hi]), 1), "toe_z": round(float(zz[i_lo]), 1),
                    "H_m": round(H, 1), "L_m": round(L, 1), "H_over_L": round(H / L, 3) if L else None,
                    "reach_angle_deg": round(float(np.degrees(np.arctan2(H, L))), 1), "azimuth_deg": round(float(azim)),
                    "crown_at_edge": bool(crown.distance(edge) < 15), "toe_at_edge": bool(toe.distance(edge) < 15),
                    "slope_mean_deg": round(float(sl.mean()), 1), "slope_p90_deg": round(float(np.percentile(sl, 90)), 1),
                    "crown_lonlat": list(gpd.GeoSeries([crown], crs=32647).to_crs(4326).iloc[0].coords[0]),
                    "toe_lonlat": list(gpd.GeoSeries([toe], crs=32647).to_crs(4326).iloc[0].coords[0]),
                    "ndvi_pre_mean": round(float(np.nanmean(nd)), 2),
                    "ndvi_pre_source": round(float(np.nanmean(nd[sl >= 20])), 2) if (sl >= 20).any() else None,
                    "zone_m2": {k: round(geom.intersection(v).area, 1) for k, v in zone_polys.items()}})
        o = out[-1]
        print(site, o["id"], o["type"], {k: o[k] for k in ("crown_z", "toe_z", "H_m", "L_m", "reach_angle_deg",
                                                         "crown_at_edge", "toe_at_edge", "slope_mean_deg", "ndvi_pre_source")})
    json.dump(out, open(d(site, "inventory", "terrain.json"), "w"), indent=1)


if __name__ == "__main__":
    z, slope, T = dem_products()
    for s in (sys.argv[1:] or list(SITES)):
        run(s, z, slope, T)
