"""Collect the ten drone-surveyed sites into one payload, export GIS deliverables, render the dashboard.

Outputs
  outputs/launglon_landslides_2026.gpkg   per site: landslides, outwash, buildings, reach zones, exclusions, crown/toe
  outputs/landslides.csv, outputs/buildings.csv, outputs/summary.json   (all ten sites, `site` column)
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
REGION = box(98.055, 13.66, 98.22, 14.04)
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
REPORTS["tby"] = {
    "source": "Dawei Watch, 27 Sep - 2 Oct 2026", "deaths": 3, "recovered": 3, "missing": 0,
    "houses": "nearly 40", "houses_n": 40, "houses_label": "nearly 40 houses buried or damaged",
    "lines": ["3 people of one family died in the landslide west of the main road: Daw Aye Win (about 50) and her "
              "6-year-old granddaughter were found under the debris on 30 Sep, the girl's mother on 1 Oct (2 Oct).",
              "Nearly 40 houses buried or damaged (2 Oct). On 29 Sep residents counted at least 4 houses almost "
              "completely destroyed and nearly 200 with sediment washed inside, with rubber, cashew and other "
              "plantations buried; a mother and her son were then missing.",
              "About three football pitches of land buried west of the Dawei-Launglon road (30 Sep).",
              "The Tha Byar bridge on the Dawei-Launglon road, undermined by the stream and landslide debris on 29 Sep, "
              "collapsed on the morning of 30 Sep; traffic was sent round via the Inn Zauk junction and Wei Di - Pyin Htein.",
              "Rescue teams reached Tha Byar on 27 Sep, clearing debris and boulders from the road by the monastery and the "
              "Pyin Sa Thi Maw turn-off; low-lying parts of the village were flooded to head height.",
              "A resident recalled a 1997 landslide on the same ridge, long grown over, and said this one was larger."]}
REPORTS["rbe"] = {
    "source": "Dawei Watch, 29-30 Sep 2026", "deaths": None, "houses": None,
    "houses_note": "no houses reported destroyed",
    "lines": ["Landslides cut the roads from 26 Sep: Ra Be, Kyauk Pon, Za Lut Pyin Gyi, the Kyauk Twin village tract and other "
              "villages at the end of the Launglon peninsula were cut off and short of food (29 Sep).",
              "The Kyauk Twin village tract - Wea Ma Kaik, Kyauk Twin, Sun Gyi and Chaung Hpyar Gyi, about 350 households near "
              "Sin Htauk beach - is reached by the road west from Ra Be through the forested hills; with the Launglon - Shin "
              "Maw road buried in many places, no relief had reached it five days after the road was cut (30 Sep).",
              "No report gives deaths or destroyed houses at Ra Be or along this road."]}
REPORTS["pgz"] = {
    "source": "Dawei Watch, 28 Sep - 2 Oct 2026", "deaths": 1, "recovered": 1, "missing": 0,
    "houses": "about 20", "houses_n": 20, "houses_label": "about 20 houses destroyed or uninhabitable",
    "deaths_note": "reported for Za Lut Pyin Gyi; where in the village is not stated",
    "lines": ["At Za Lut Pyin Gyi a man over 60, U Tun Po, was swept away by water during the landslide on the night of "
              "26 Sep; his body was found on 28 Sep tangled in the wires of a fallen power pole. Another man, buried near "
              "his house, was dug out by villagers at about 8 pm on 26 Sep and taken to Dawei hospital on 30 Sep (30 Sep).",
              "About 20 houses lost: 10 near the five pagodas completely buried, and 10 inside the village filled with "
              "sediment so they can no longer be lived in (30 Sep).",
              "The road has been cut since 26 Sep; about 200 people were trapped, sheltering at the monastery and drinking "
              "rainwater. Rescuers heading south to Kyauk Ni Maw had to clear a large landslide at Za Lut (30 Sep).",
              "Za Lut Pyin Gyi was one of five villages the authorities designated red-level disaster areas (28 Sep)."]}
REPORTS["kdg"] = {
    "source": "Dawei Watch, 26-28 Sep 2026", "deaths": 2, "recovered": 2, "missing": 0, "houses": None,
    "deaths_note": "in an orchard a few miles from the village, probably outside the survey",
    "houses_note": "no houses reported destroyed",
    "lines": ["A mother and son, Daw Khin Aye (over 70) and U Myo Thein (about 45, the deputy village administrator), were "
              "found dead under landslide debris in their rubber and durian orchard on the evening of 28 Sep; residents "
              "said the whole orchard was filled with debris. The orchard is a few miles from Ka Det Gyi village, so "
              "probably outside this survey (28 Sep).",
              "On 26 Sep, with heavy rain still falling, families living close to the hills at Ka Det Gyi had packed "
              "their belongings and some had moved away (26 Sep).",
              "No report names Nyaungdon or Wet Thar Kin, and none reports houses lost at Ka Det Gyi."]}
REPORTS["pny"] = {
    "source": "Dawei Watch, 28-30 Sep 2026", "deaths": 0, "houses": None,
    "houses_note": "2 houses buried in Pa Nyit village, 1.7 km west (outside the survey)",
    "lines": ["Landslides after the heavy rain of 27 Sep blocked the road at two places: one between Launglon and Pa Nyit, "
              "one between Pa Nyit and Kan Pa Ni. Shan Maw, Pein Ne Chaung and Kyon Ga Nan, reached through Pa Nyit, were "
              "cut off (28 Sep).",
              "In Pa Nyit village two houses were buried; no one was hurt, and villagers moved to safer ground (28 Sep).",
              "The road near the Karen Gyi bridge, cut since 27 Sep, was repaired on 30 Sep, opening the way for food and "
              "rescue vehicles to Karen Gyi, Kan Pa Ni and Pa Nyit.",
              "Villagers recalled the 1997 landslides on the Launglon peninsula, when a slope collapse at Pa Nyit buried "
              "about 100 houses and 61 people died in the mud."]}
REPORTS["thw"] = {
    "source": "Dawei Watch, 29 Sep - 1 Oct 2026", "deaths": None, "houses": None,
    "houses_note": "no houses reported destroyed",
    "lines": ["Landslide debris blocked the road between Taw Kye and Tha Win; search and rescue teams were clearing it on "
              "30 Sep, and the heavy-machinery crew clearing the blocked roads reached the edge of Tha Win that day.",
              "Further south, debris also blocked the road between Tha Win and Tha Kyet Taw; residents were still clearing it "
              "when rescue teams reached Tha Win (update to a 29 Sep report).",
              "No report gives deaths or destroyed houses at Tha Win. The 5 deaths and 42 houses reported for Taw Kye are "
              "given under Taw Kye, whose 2 Oct survey this one surrounds."]}
REPORTS["lhl"] = {
    "source": "Dawei Watch, 29 Sep - 1 Oct 2026", "deaths": None, "houses": None,
    "houses_note": "no houses reported destroyed",
    "lines": ["No report names Lel Hla. It lies on the road between Tha Win and Tha Kyet Taw, which debris blocked; residents "
              "were still clearing it when rescue teams reached Tha Win (update to a 29 Sep report).",
              "Tha Kyet Taw, 0.7 km south of the survey and the head of Lel Hla's village tract, is one of at least eight "
              "villages at the end of the peninsula cut off by landslides since 26 Sep and short of food (29 Sep, 1 Oct)."]}
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
META["tby"] = {"mmr": "သဗျာ", "gsd_cm": 9.0, "file": "TharByar_Plan_1.kmz + TharByar_Plan_2.kmz", "tiles": "thabyar",
               "mimu": [("Tha Byar", "177126", "inside")]}
META["pny"] = {"mmr": "ပညစ်လမ်း", "gsd_cm": 7.0, "file": "PaNyit_Road.kmz", "tiles": "panyit",
               "mimu": [("Pa Nyit", "177151", "1.7 km west of the survey")]}
META["kdg"] = {"mmr": "ကဒက်ကြီး", "gsd_cm": 8.0, "file": "KadetGyi_WetTharKin_Plan-1.kmz + KadetGyi_ChaeTawYar_Plan-2.kmz",
               "tiles": "kadetgyi",
               "mimu": [("Wet Thar Kin", "177162", "inside"), ("Ka Det Gyi", "177160", "90 m beyond the survey edge"),
                        ("Nyaungdon", "177161", "130 m beyond the survey edge")]}
META["pgz"] = {"mmr": "ပြင်ကြီး - ဇလွတ်", "gsd_cm": 9.7, "file": "PyinGyi_Plan_1.kmz + PyinGyi_Plan_2.kmz",
               "tiles": "zalut",
               "mimu": [("Pyin Gyi", "177216", "1.4 km south of the survey"), ("Za Lut", "177215", "1.5 km south of the survey")]}
META["rbe"] = {"mmr": "ရဘဲ", "gsd_cm": 9.2, "file": "Yabae_KyaukTwin_RD_1.kmz + Yabae_KyaukTwin_RD_2.kmz",
               "tiles": "rabe",
               "mimu": [("Ra Be", "177207", "1.0 km north of the survey"), ("Kyauk Twin", "177217", "3.1 km west, at the end of the road")]}
META["thw"] = {"mmr": "သဝင်", "gsd_cm": 10.0, "file": "Thakyattaw_Yabel_4Plan_Combine.kmz (northern block)",
               "tiles": "thawin",
               "mimu": [("Tha Win", "177209", "inside"), ("Taw Kye", "177208", "in the 2 Oct Taw Kye survey, 160 m beyond this one")]}
META["lhl"] = {"mmr": "လယ်လှ", "gsd_cm": 10.0, "file": "Thakyattaw_Yabel_4Plan_Combine.kmz (southern block)",
               "tiles": "thawin",
               "mimu": [("Lel Hla", "177204", "200 m south of the survey"), ("Tha Kyet Taw", "177203", "0.7 km south of the survey")]}
SITE_ORDER = ("tby", "pny", "nmt", "kdnh", "kdg", "tawkye", "thw", "lhl", "rbe", "pgz")  # north to south
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
        "nearest_standing_m": r1(surv[surv.status.isin(["clear", "edge", "outwash"])]["dist_m"].min()) if "dist_m" in surv else None,
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
           "zones": gj(zones[~(zones.geometry.isna() | zones.geometry.is_empty)][["zone", "alpha_deg", "label", "geometry"]], 6),  # zone B is empty where no channel out-ran the open slides
           "footprint": gj(fp, 6)}
    if len(ow):
        geo["outwash"] = gj(ow[["id", "name", "description", "area_m2", "geometry"]], simplify=WEB_SIMPLIFY_M)
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
    for s in SITE_ORDER:
        sites[s], c, b = build_site(s, gpkg)
        csv_rows += c
        bcsv.append(b)
    pd.DataFrame(csv_rows).to_csv(OUTD / "landslides.csv", index=False)
    pd.concat(bcsv).to_csv(OUTD / "buildings.csv", index=False)
    rain = {"tby": rain_series(ROOT / "data/source/rainfall_openmeteo_tby.json"),
            "pgz": rain_series(ROOT / "data/source/rainfall_openmeteo_pgz.json"),
            "rbe": rain_series(ROOT / "data/source/rainfall_openmeteo_rbe.json"),
            "thw": rain_series(ROOT / "data/source/rainfall_openmeteo_thw.json"),  # Lel Hla is in the same model cell
            "pny": rain_series(ROOT / "data/source/rainfall_openmeteo_pny.json"),
            "kadet": rain_series(ROOT / "data/source/rainfall_openmeteo_kadet.json"),
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
        "in_sediment": sum(x["buildings_status"].get("outwash", 0) for x in S.values()),
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
<meta name="description" content="Drone-orthomosaic analysis of the 26-27 Sep 2026 landslides at Tha Byar, the road to Pa Nyit, Ngone Min Taung, Ka Det Nge Htein, Ka Det Gyi, Taw Kye, Tha Win, Lel Hla, Ra Be and Pyin Gyi - Za Lut, Launglon Township, Tanintharyi Region, Myanmar.">
<link rel="canonical" href="{SITE}">
<meta property="og:url" content="{SITE}">
<meta property="og:title" content="Launglon landslides, 26-27 Sep 2026: ten drone surveys">
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
