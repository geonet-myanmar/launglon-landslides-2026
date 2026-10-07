"""Runout-reach screening calibrated on each site's mapped landslides (energy line / Fahrboeschung), as at Taw Kye.

Every DEM cell on slope >= SRC_SLOPE is a potential source. Debris spreads to all lower neighbours
(multiple flow direction) in order of decreasing elevation, carrying the height of an energy line of
gradient tan(alpha):  h_next = h + (z - z_next) - tan(alpha) * step.  A cell is within reach while h >= 0.

Per site, two runs from the observed reach angles:
  open     alpha = smallest reach angle of its open-slope slides whose crown and toe both lie inside the survey
  channel  alpha = reach angle of the channelised flow that reached settlement or paddy
           (KD-01 at Ka Det Nge Htein, NM-04 at Ngone Min Taung - Taw Kye used LS-04). At Tha Byar no channelised
           flow has its source inside the survey, so the path is the long slide's crown (TB-03) to the toe of the
           valley flow it joined (TB-01, fan in the village): H and L between those two points.
Zone A = reach of an open-slope flow; zone B = reached only by a channelised one.
Zones are kept within 250 m of each survey so the two neighbouring sites do not overlap on the map.
Pure screening on a 30 m pre-event DEM: no volume, no velocity cap, no obstacle effect.
At Tha Byar it fails: the valley floor between TB-03 and the village is flat and lumpy on the DEM (forest canopy),
and debris only moves to lower cells, so it stalls there at any angle. Back-analysis 2026-10-05: alpha 8/7/6/5/4/3
deg covers 48/54/55/55/55/55 % of TB-01 and 0/6/6/6/6/6 of the 47 destroyed, damaged or in-sediment buildings
(filling depressions first changes nothing - filled pits become flats). Reported on the page, not tuned away.
"""
import json, sys
import numpy as np, rasterio, geopandas as gpd
from rasterio import features
from shapely.geometry import shape
from shapely.ops import unary_union
from sites import SITES, d, ee_dir

SRC_SLOPE = 20.0
CHANNEL = {"kdnh": "KD-01", "nmt": "NM-04", "tby": ("TB-03", "TB-01"), "pny": "PN-01", "kdg": "KGN-02", "pgz": ("PG-04", "PG-03")}  # tuple: crown of one, toe of the other
CLIP_M = 250


def reach(z, slope, res, alpha_deg):
    t = np.tan(np.radians(alpha_deg))
    H, W = z.shape
    h = np.full(z.shape, -np.inf)
    h[slope >= SRC_SLOPE] = 0.0
    nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for idx in np.argsort(-z, axis=None):
        r, c = divmod(int(idx), W)
        hc = h[r, c]
        if hc < 0:
            continue
        zc = z[r, c]
        for dr, dc in nb:
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and z[rr, cc] < zc:
                hn = hc + (zc - z[rr, cc]) - t * res * (1.4142135 if dr and dc else 1.0)
                if hn > h[rr, cc]:
                    h[rr, cc] = hn
    return h


def run(site, z, slope, T, prof):
    out = d(site, "hazard")
    out.mkdir(exist_ok=True)
    terr = {t["id"]: t for t in json.load(open(d(site, "inventory", "terrain.json")))}
    open_ids = [i for i, t in terr.items() if t["type"] == "open" and not t["crown_at_edge"] and not t["toe_at_edge"]]
    a_open = min(terr[i]["reach_angle_deg"] for i in open_ids)
    ch = CHANNEL[site]
    if isinstance(ch, tuple):
        c, t = terr[ch[0]], terr[ch[1]]
        from pyproj import Geod
        L = Geod(ellps="WGS84").inv(*c["crown_lonlat"], *t["toe_lonlat"])[2]
        H = c["crown_z"] - t["toe_z"]
        a_chan = round(float(np.degrees(np.arctan2(H, L))), 1)
        print(f"{site} channel path {ch[0]} crown -> {ch[1]} toe: H {H:.1f} m, L {L:.0f} m, alpha {a_chan} deg")
    else:
        a_chan = terr[ch]["reach_angle_deg"]
    ch_ids = list(ch) if isinstance(ch, tuple) else [ch]
    fp = gpd.read_file(d(site, "inventory", "footprint.geojson")).to_crs(32647).geometry.iloc[0]
    clip = fp.buffer(CLIP_M)
    zones = {}
    for name, a in (("open", a_open), ("channel", a_chan)):
        h = reach(z, slope, T.a, a)
        with rasterio.open(out / f"reach_{name}.tif", "w", **prof) as o:
            o.write(np.where(np.isfinite(h), h, -9999).astype("float32"), 1)
        m = (h >= 0).astype(np.uint8)
        zones[name] = unary_union([shape(g) for g, v in features.shapes(m, transform=T) if v == 1]).intersection(clip)
        print(f"{site} {name}: alpha {a} deg, reach within {CLIP_M} m of the survey {zones[name].area / 1e4:.1f} ha")
    zA = zones["open"]
    zB = zones["channel"].difference(zA)
    gz = gpd.GeoDataFrame({"zone": ["A", "B"], "alpha_deg": [a_open, a_chan],
                           "label": [f"Within reach of an open-slope debris flow (alpha {a_open} deg)",
                                     f"Within reach only of a channelised flow (alpha {a_chan} deg)"]},
                          geometry=[zA, zB], crs=32647)
    gz.to_crs(4326).to_file(out / "reach_zones.geojson", driver="GeoJSON")
    slides = gpd.read_file(d(site, "inventory", "landslides_utm.gpkg"))
    slides = slides[slides.kind == "landslide"]
    calib = {}
    for _, r in slides.iterrows():
        if r["id"] in open_ids or r["id"] in ch_ids:
            zz = zones["channel"] if r["id"] in ch_ids else zA
            calib[r["id"]] = round(r.geometry.intersection(zz).area / r.geometry.area, 3)
    print(site, "share of each calibration landslide inside its modelled reach:", calib)
    b = gpd.read_file(d(site, "inventory", "buildings_utm.gpkg"))
    b["reach"] = np.where(b.geometry.intersects(zA), "A", np.where(b.geometry.intersects(zB), "B", ""))
    b.to_file(d(site, "inventory", "buildings_utm.gpkg"), driver="GPKG")
    b.to_crs(4326).to_file(d(site, "inventory", "buildings.geojson"), driver="GeoJSON")
    surv = b[~b.status.isin(["not_surveyed", "not_building"])]
    tab = surv.groupby(["status", "reach"]).size().unstack(fill_value=0)
    print(tab.to_string())
    json.dump({"alpha_open": a_open, "alpha_channel": a_chan, "open_ids": open_ids, "channel_id": "+".join(ch_ids),
               "src_slope": SRC_SLOPE, "clip_m": CLIP_M,
               "zoneA_ha": round(zA.area / 1e4, 2), "zoneB_ha": round(zB.area / 1e4, 2),
               "calibration_share_inside": calib,
               "buildings_surveyed_by_status_reach": {s: {k: int(v) for k, v in row.items()} for s, row in tab.iterrows()}},
              open(out / "runout_summary.json", "w"), indent=1)


if __name__ == "__main__":
    for s in (sys.argv[1:] or list(SITES)):
        with rasterio.open(ee_dir(s) / "cop30_dem_utm.tif") as src:
            z = src.read(1).astype(np.float64)
            T = src.transform
            prof = src.profile
        with rasterio.open(ee_dir(s) / "slope_deg.tif") as src:
            slope = src.read(1)
        prof.update(dtype="float32", nodata=-9999, compress="deflate")
        run(s, z, slope, T, prof)
