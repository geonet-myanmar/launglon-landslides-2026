"""Collect the three drone-surveyed sites into one payload, export GIS deliverables, render the dashboard.

Outputs
  outputs/launglon_landslides_2026.gpkg   per site: landslides, outwash, buildings, reach zones, exclusions, crown/toe
  outputs/landslides.csv, outputs/buildings.csv, outputs/summary.json   (all three sites, `site` column)
  index.html                              standalone page (doctype + head) for GitHub Pages / local use
  dist/artifact-body.html                 the same body fragment without the wrapper
src/template.html is the single source of truth for the page; never hand-edit index.html.
"""
import json
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point, box
from sites import ROOT, SITES, d

SITE = "https://geonet-myanmar.github.io/launglon-landslides-2026/"
OUTD = ROOT / "outputs"
TK = ROOT / "data/tawkye"
RAW = ROOT / "data/raw"
REGION = box(98.09, 13.76, 98.22, 13.93)
WEB_SIMPLIFY_M = 0.2  # display outlines only; the GeoPackage keeps the 0.1 m outlines

# Ground reports, Dawei Watch (Burmese), data/source/dawei_watch_2026-09-26_10-02.txt
REPORTS = {
    "kdnh": {"source": "Dawei Watch, 29 Sep - 2 Oct 2026", "deaths": 15, "recovered": 12, "missing": 3,
             "houses": "more than 30", "houses_n": 30,
             "lines": ["15 people died, the highest toll of any village in the disaster (2 Oct).",
                       "12 bodies recovered and 3 people still missing on 1 Oct, when the body of a 27-year-old woman "
                       "was found under the debris six days after the landslide.",
                       "More than 30 houses destroyed, according to residents (29 Sep); the village was designated a "
                       "red-level disaster area and a rescue team reached it on 28 Sep.",
                       "In neighbouring Ka Det Gyi, outside the survey, a mother and her son died when a slope collapsed "
                       "onto their garden."]},
    "nmt": {"source": "Dawei Watch, 26 Sep - 2 Oct 2026", "deaths": None, "houses": None,
            "lines": ["No report names Ngone Min Taung or Htein Gyi in Dawei Watch coverage to 2 Oct 2026."]},
    "tawkye": {"source": "Dawei Watch, 1-2 Oct 2026", "deaths": 5, "recovered": 2, "missing": 3,
               "houses": "42", "houses_n": 42,
               "lines": ["5 people died - two men, a nun and two women; the bodies of three had not been recovered on 1 Oct.",
                         "42 houses destroyed. Heavy-machinery crews clearing the blocked road reached the village on 1 Oct."]},
}
REGIONAL = {"launglon_deaths": 31, "launglon_asof": "1 Oct 2026", "district_deaths": 41, "district_asof": "2 Oct 2026",
            "source": "Dawei Watch, 2 Oct 2026"}
META = {
    "kdnh": {"mmr": "ကဒက်ငယ်ထိန်", "gsd_cm": 8.0, "file": "KadetNgelHtein_Ortho.kmz", "tiles": "kadet",
             "mimu": [("Ka Det Nge Htein", "177156", "inside")]},
    "nmt": {"mmr": "", "gsd_cm": 10.1, "file": "NgoneMinTaung_Ortho.kmz", "tiles": "kadet",
            "mimu": [("Htein Gyi", "177157", "inside")]},
    "tawkye": {"name": "Taw Kye", "mmr": "တောကျဲ", "gsd_cm": 3.75, "file": "TawKyel_Village_Landslide.kmz + TawKyel_Plan-2.kmz",
               "flown": "2026-10-02", "tiles": "tawkye", "mimu": [("Taw Kye", "177208", "inside")]},
}
TK_TYPES = {"LS-01": "channel", "LS-04": "channel"}
TK_EDGE = {"LS-01": ("crown", "Mud fan fed by a channel entering from outside the survey."),
           "LS-09": ("toe", "Continues beyond the surveyed area.")}


def r1(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 1)


def gj(g, prec=7, simplify=None):
    g = g.copy()
    if simplify:
        g["geometry"] = g.to_crs(32647).geometry.simplify(simplify).to_crs(g.crs if g.crs.to_epsg() != 4326 else 4326) \
            if g.crs.to_epsg() == 32647 else g.to_crs(32647).geometry.simplify(simplify).to_crs(4326).values
    dd = json.loads(g.to_crs(4326).to_json(drop_id=True))

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], prec), round(c[1], prec)]
    for f in dd["features"]:
        f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
        for k, v in list(f["properties"].items()):
            if isinstance(v, float) and np.isnan(v):
                f["properties"][k] = None
    return dd


def label_pt(geom):
    p = max(getattr(geom, "geoms", [geom]), key=lambda q: q.area).representative_point()
    return list(gpd.GeoSeries([p], crs=32647).to_crs(4326).iloc[0].coords[0])


def load_site(s):
    """Uniform structure for every site: landslides (UTM), terrain by id, buildings, zones, runout, footprint, extras."""
    if s == "tawkye":
        sl = gpd.read_file(TK / "landslides_utm.gpkg")
        sl["kind"] = "landslide"
        terr = {t["id"]: t for t in json.load(open(TK / "terrain.json"))}
        for i, t in terr.items():
            t["type"] = TK_TYPES.get(i, "open")
            t["crown_at_edge"] = TK_EDGE.get(i, ("",))[0] == "crown"
            t["toe_at_edge"] = TK_EDGE.get(i, ("",))[0] == "toe"
            row = sl[sl.id == i].iloc[0]
            t["name"], t["description"] = row["name"], row["description"]
        b = gpd.read_file(TK / "buildings_utm.gpkg")
        zones = gpd.read_file(TK / "reach_zones.geojson")
        runout = json.load(open(TK / "runout_summary.json"))
        runout["open_ids"] = ["LS-02", "LS-03", "LS-05", "LS-06", "LS-07", "LS-08", "LS-09"]
        runout["channel_id"] = "LS-04"
        fp = pd.concat([gpd.read_file(TK / f"footprint_{t}_flight.geojson") for t in ("landslide", "plan2")])
        fp = gpd.GeoDataFrame(geometry=[fp.to_crs(32647).union_all()], crs=32647)
        tks = json.load(open(TK / "summary.json"))
        excl = gpd.GeoDataFrame(columns=["id", "name", "description", "geometry"], geometry="geometry", crs=4326)
        shift = tks["footprint_shifts"]
        return sl, terr, b, zones, runout, fp, excl, shift
    inv = d(s, "inventory")
    sl = gpd.read_file(inv / "landslides_utm.gpkg")
    terr = {t["id"]: t for t in json.load(open(inv / "terrain.json"))}
    b = gpd.read_file(inv / "buildings_utm.gpkg")
    zones = gpd.read_file(d(s, "hazard", "reach_zones.geojson"))
    runout = json.load(open(d(s, "hazard", "runout_summary.json")))
    fp = gpd.read_file(inv / "footprint.geojson").to_crs(32647)
    env = gpd.read_file(inv / "envelopes.geojson")
    excl = env[env.kind == "exclude"][["id", "name", "description", "geometry"]]
    shift = json.load(open(inv / "footprint_shift.json"))
    return sl, terr, b, zones, runout, fp, excl, shift


def build_site(s, gpkg):
    sl, terr, b, zones, runout, fp, excl, shift = load_site(s)
    ls = sl[sl.kind == "landslide"]
    ow = sl[sl.kind == "outwash"]
    surv = b[~b.status.isin(["not_surveyed", "not_building"])].copy()
    for c in ("note", "reach", "landslide"):
        if c not in surv:
            surv[c] = ""
        surv[c] = surv[c].fillna("")
    rows = []
    for _, r in ls.iterrows():
        t = terr[r["id"]]
        hit = surv[surv["landslide"].str.split(",").apply(lambda L: r["id"] in L)]
        rows.append({
            "id": r["id"], "name": t["name"], "type": t["type"], "description": t["description"],
            "area_m2": round(r["area_m2"]), "soil_m2": round(r["soil_m2"]), "grey_m2": round(r["grey_m2"]),
            "crown_z": t["crown_z"], "toe_z": t["toe_z"], "H_m": t["H_m"], "L_m": t["L_m"],
            "reach_angle_deg": t["reach_angle_deg"], "azimuth_deg": t["azimuth_deg"],
            "crown_at_edge": t.get("crown_at_edge", False), "toe_at_edge": t.get("toe_at_edge", False),
            "slope_mean_deg": t["slope_mean_deg"], "ndvi_pre_source": t["ndvi_pre_source"],
            "source_m2": round(t["zone_m2"]["source"]), "transport_m2": round(t["zone_m2"]["transport"]),
            "runout_m2": round(t["zone_m2"]["runout"]),
            "destroyed": int((hit.status == "destroyed").sum()), "damaged": int((hit.status == "damaged").sum()),
            "edge": int((hit.status == "edge").sum()),
            "crown": t["crown_lonlat"], "toe": t["toe_lonlat"], "label": label_pt(r.geometry)})
    rows.sort(key=lambda x: x["id"])
    st = surv.status.value_counts().to_dict()
    standing = surv.status.isin(["clear", "edge", "outwash"])
    reach = {"standing_in_A": int((standing & (surv.reach == "A")).sum()),
             "standing_in_B": int((standing & (surv.reach == "B")).sum()),
             "standing_outside": int((standing & (surv.reach == "")).sum()),
             "affected": int(surv.status.isin(["destroyed", "damaged"]).sum()),
             "affected_in_AB": int((surv.status.isin(["destroyed", "damaged"]) & (surv.reach != "")).sum())}
    by_type = {k: int(sum(r["area_m2"] for r in rows if r["type"] == k)) for k in ("open", "channel", "minor")}
    n_type = {k: sum(1 for r in rows if r["type"] == k) for k in ("open", "channel", "minor")}
    meta = META[s]
    name = meta.get("name") or SITES[s]["name"]
    flown = meta.get("flown") or SITES[s]["flown"]
    vil = gpd.read_file(RAW / "village_points_tni.geojson")
    summ = {
        "key": s, "name": name, "mmr": meta["mmr"], "flown": flown, "gsd_cm": meta["gsd_cm"], "file": meta["file"],
        "survey_ha": round(fp.area.iloc[0] / 1e4, 1), "tiles": meta["tiles"],
        "n_landslides": len(rows), "n_by_type": n_type, "area_total_m2": int(sum(r["area_m2"] for r in rows)),
        "area_by_type_m2": by_type, "area_runout_flat_m2": int(sum(r["runout_m2"] for r in rows)),
        "outwash_m2": int(ow.area_m2.sum()) if len(ow) else 0,
        "largest": max(rows, key=lambda r: r["area_m2"])["id"],
        "buildings_surveyed": int(len(surv)), "buildings_status": {k: int(v) for k, v in st.items()},
        "not_building": int((b.status == "not_building").sum()),
        "overrides": int((surv.get("status_auto", surv.status) != surv.status).sum()) if "status_auto" in surv else 0,
        "reach": reach, "runout": runout, "footprint_shift": shift, "report": REPORTS[s],
        "mimu": [{"name": n, "pcode": p, "where": w,
                  "mmr": vil[vil.VLG_PCODE.astype(str) == p].iloc[0].VLG_MMR,
                  "lon": vil[vil.VLG_PCODE.astype(str) == p].iloc[0].geometry.x,
                  "lat": vil[vil.VLG_PCODE.astype(str) == p].iloc[0].geometry.y} for n, p, w in meta["mimu"]],
        "vt": vil[vil.VLG_PCODE.astype(str) == meta["mimu"][0][1]].iloc[0].VT,
        "vt_pcode": vil[vil.VLG_PCODE.astype(str) == meta["mimu"][0][1]].iloc[0].VT_PCODE,
        "bounds": list(fp.to_crs(4326).total_bounds),
        "n_exclusions": int(len(excl)),
    }
    # ---- GIS export
    sl_out = ls.copy()
    sl_out["site"] = name
    for k in ("name", "type", "description"):
        sl_out[k] = [terr[i][k] for i in sl_out["id"]]
    sl_out.to_file(gpkg, layer=f"{s}_landslides", driver="GPKG")
    if len(ow):
        ow.assign(site=name).to_file(gpkg, layer=f"{s}_outwash", driver="GPKG")
    surv.assign(site=name).to_file(gpkg, layer=f"{s}_buildings", driver="GPKG")
    zones.to_crs(32647).assign(site=name).to_file(gpkg, layer=f"{s}_runout_reach_zones", driver="GPKG")
    if len(excl):
        excl.to_crs(32647).assign(site=name).to_file(gpkg, layer=f"{s}_exclusions", driver="GPKG")
    gpd.GeoDataFrame([{"id": r["id"], "kind": k, "z_m": r["crown_z"] if k == "crown" else r["toe_z"], "geometry": Point(r[k])}
                      for r in rows for k in ("crown", "toe")], crs=4326).to_crs(32647).to_file(
        gpkg, layer=f"{s}_crown_toe_points", driver="GPKG")
    fp.assign(site=name).to_file(gpkg, layer=f"{s}_survey_extent", driver="GPKG")
    # ---- web geometry
    bcols = ["bid", "source", "status", "landslide", "overlap", "f_grey", "f_soil", "f_veg", "reach", "note"]
    bweb = surv[[c for c in bcols if c in surv] + ["geometry"]].copy()
    lw = ls[["id", "geometry"]].copy()
    lw["type"] = [terr[i]["type"] for i in lw["id"]]
    geo = {"landslides": gj(lw, simplify=WEB_SIMPLIFY_M), "buildings": gj(bweb),
           "zones": gj(zones[["zone", "alpha_deg", "label", "geometry"]], 6),
           "footprint": gj(fp, 6)}
    if len(ow):
        geo["outwash"] = gj(ow[["id", "area_m2", "geometry"]], simplify=WEB_SIMPLIFY_M)
    if len(excl):
        geo["exclusions"] = gj(excl, 6)
    csv_rows = [{"site": name, **{k: v for k, v in r.items() if k not in ("crown", "toe", "label")}} for r in rows]
    bcsv = surv.drop(columns="geometry").assign(site=name)
    return {"summary": summ, "landslides": rows, "geo": geo}, csv_rows, bcsv


def rain_series(p):
    r = json.load(open(p))
    hourly = r["hourly"]
    return {"daily": [{"date": k, "mm": v} for k, v in r["daily"].items() if k <= "2026-10-02"],
            "night_26_27": round(sum(v or 0 for k, v in hourly.items() if "2026-09-26T20" <= k < "2026-09-27T06"), 1),
            "d25_28": round(sum(v for k, v in r["daily"].items() if "2026-09-25" <= k <= "2026-09-28"), 1),
            "sep_total": round(sum(v for k, v in r["daily"].items() if k < "2026-10-01"), 1),
            "fetched": r["fetched_utc"], "grid": [r["grid_lat"], r["grid_lon"]]}


def main():
    OUTD.mkdir(exist_ok=True)
    gpkg = OUTD / "launglon_landslides_2026.gpkg"
    if gpkg.exists():
        gpkg.unlink()
    sites, csv_rows, bcsv = {}, [], []
    for s in ("kdnh", "nmt", "tawkye"):
        sites[s], c, b = build_site(s, gpkg)
        csv_rows += c
        bcsv.append(b)
    pd.DataFrame(csv_rows).to_csv(OUTD / "landslides.csv", index=False)
    pd.concat(bcsv).to_csv(OUTD / "buildings.csv", index=False)
    rain = {"kadet": rain_series(ROOT / "data/source/rainfall_openmeteo_kadet.json"),
            "tawkye": rain_series(TK / "rainfall_openmeteo_tawkye.json")}
    # ---- MIMU context
    vil = gpd.read_file(RAW / "village_points_tni.geojson")
    vil = vil[vil.intersects(REGION)][["VILLAGE", "VLG_MMR", "VLG_PCODE", "VT", "TS", "geometry"]]
    vt = gpd.read_file(RAW / "adm4_vt_tanintharyi.geojson")
    vt = vt[vt.intersects(REGION)][["VT", "VT_MMR", "VT_PCODE", "TS", "geometry"]]
    vt["geometry"] = vt.geometry.simplify(0.0002)
    ts = gpd.read_file(RAW / "adm3_townships.geojson")
    ts = ts[ts.TS == "Launglon"][["TS", "TS_MMR", "TS_PCODE", "geometry"]]
    ts["geometry"] = ts.geometry.simplify(0.0005)
    roads = gpd.read_file(RAW / "roads.geojson").clip(REGION)[["Road_Type", "geometry"]]
    sch = gpd.read_file(RAW / "schools_lower.geojson")
    sch = sch[sch.intersects(REGION)][["schoolname", "geometry"]]
    S = {k: v["summary"] for k, v in sites.items()}
    total = {
        "n_landslides": sum(x["n_landslides"] for x in S.values()),
        "area_m2": sum(x["area_total_m2"] for x in S.values()),
        "destroyed": sum(x["buildings_status"].get("destroyed", 0) for x in S.values()),
        "damaged": sum(x["buildings_status"].get("damaged", 0) for x in S.values()),
        "standing_in_A": sum(x["reach"]["standing_in_A"] for x in S.values()),
        "standing_in_B": sum(x["reach"]["standing_in_B"] for x in S.values()),
        "deaths": sum(x["report"]["deaths"] or 0 for x in S.values()),
        "survey_ha": round(sum(x["survey_ha"] for x in S.values()), 1),
        "outwash_m2": sum(x["outwash_m2"] for x in S.values()),
    }
    summary = {"sites": S, "total": total, "regional": REGIONAL,
               "rain": {k: {kk: vv for kk, vv in v.items() if kk != "daily"} for k, v in rain.items()}}
    json.dump(summary, open(OUTD / "summary.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    payload = {"sites": sites, "total": total, "regional": REGIONAL, "rain": rain,
               "ctx": {"villages": gj(vil, 6), "vt": gj(vt, 6), "township": gj(ts, 5), "roads": gj(roads, 6),
                       "schools": gj(sch, 6)}}
    tpl = (ROOT / "src/template.html").read_text(encoding="utf-8")
    body = tpl.replace("/*__DATA__*/null", json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str))
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist/artifact-body.html").write_text(body, encoding="utf-8")
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Launglon Landslides 2026</title>
<meta name="description" content="Drone-orthomosaic analysis of the 26-27 Sep 2026 landslides at Ka Det Nge Htein, Ngone Min Taung and Taw Kye, Launglon Township, Tanintharyi Region, Myanmar.">
<link rel="canonical" href="{SITE}">
<meta property="og:url" content="{SITE}">
<meta property="og:title" content="Launglon landslides, 26-27 Sep 2026: three drone surveys">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M2 28 L13 8 L19 18 L23 13 L30 28 Z' fill='%23b8742a'/%3E%3C/svg%3E">
</head>
<body>
"""
    (ROOT / "index.html").write_text(head + body + "\n</body>\n</html>\n", encoding="utf-8")
    print("index.html", round((ROOT / "index.html").stat().st_size / 1e6, 2), "MB")
    print(json.dumps(total, indent=1))
    for k, x in S.items():
        print(k, x["n_landslides"], x["n_by_type"], x["area_total_m2"], x["buildings_status"], x["reach"])


if __name__ == "__main__":
    main()
