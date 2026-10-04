"""Interpreter-drawn envelopes, one per landslide (plus outwash and exclusion areas).

Drawn by eye on the drone orthos beside the Esri World Imagery mosaic of 10 Jan 2026
(Vantor Vivid, 0.34 m - the latest pre-event image). As at Taw Kye, an envelope only
separates a landslide from its neighbours, roads, yards and fields; the outline itself
is the native-resolution bare-ground mask inside it (05_inventory.py).
Chutes are drawn as a centre line buffered by a half-width; larger bodies as polygons.
Priority: a lower number keeps any overlap (narrow chutes before the trunk flow they join).

kind
  landslide   failure scar + its runout. An envelope with split=True is a zone instead: every
              connected bare-ground component inside it (>= 200 m2) becomes its own landslide,
              used where a dendritic network of scoured channels would need dozens of envelopes
  outwash     fields under fresh sediment or muddy water spread from a debris-flow mouth;
              mapped and reported apart, never added to landslide area
  exclude     ground already bare on 10 Jan 2026 (clearings, tracks, yards); cut from every outline
"""
import json
import geopandas as gpd
from shapely.geometry import LineString, Polygon
from sites import d

L, P = "line", "poly"


def box_ll(w, s, e, n):
    return [(w, s), (e, s), (e, n), (w, n)]


# east limit 98.1372 / 98.1362: the last ~100 m of the flight's east edge is smeared (orthorectification edge)
NMT_ZONE = [(98.1215, 13.8935), (98.1372, 13.8935), (98.1372, 13.8972), (98.1362, 13.8988), (98.1336, 13.8988), (98.1336, 13.9019),
            (98.1300, 13.9019), (98.1300, 13.9050), (98.1215, 13.9050)]
ENV = {
    "kdnh": [
        # id, name, kind, priority, type, coords, half-width m, description
        ("KD-02", "West chute", "landslide", 1, L, [(98.13030, 13.88990), (98.13129, 13.88873), (98.13214, 13.88800)], 22,
         "Narrow debris slide off the east flank of the KD-01 amphitheatre, running into the main channel."),
        ("KD-03", "Long chute", "landslide", 1, L, [(98.13195, 13.89072), (98.13283, 13.88924), (98.13375, 13.88830)], 22,
         "The longest open-slope chute on the north wall of the valley, ending on the debris fan above the corridor."),
        ("KD-04", "Twin scar", "landslide", 1, P, [(98.13320, 13.89055), (98.13450, 13.89030), (98.13495, 13.88930),
                                                    (98.13490, 13.88835), (98.13385, 13.88835), (98.13320, 13.88980)], 0,
         "Two scars side by side on the north wall - a narrow upper one and a wide lower one - whose debris merged."),
        ("KD-05", "Slide onto the old clearing", "landslide", 1, L, [(98.13385, 13.89112), (98.13440, 13.89090), (98.13470, 13.89060)], 14,
         "Forest slope that failed onto a clearing already bare in January 2026 (the clearing itself is excluded)."),
        ("KD-06", "North-east gully", "landslide", 1, L, [(98.13395, 13.89215), (98.13450, 13.89195), (98.13485, 13.89150),
                                                         (98.13552, 13.89109), (98.13600, 13.89085), (98.13650, 13.89080)], 18,
         "Debris flow scoured down a forested gully towards the north end of the village."),
        ("KD-07", "North tip slide", "landslide", 1, P, [(98.13055, 13.89540), (98.13190, 13.89540), (98.13185, 13.89350),
                                                         (98.13060, 13.89340)], 0,
         "Open-slope slide at the northern tip of the survey, high on the ridge."),
        ("KD-08", "North gully track", "landslide", 1, L, [(98.13080, 13.89262), (98.13157, 13.89298), (98.13209, 13.89323),
                                                          (98.13273, 13.89317), (98.13330, 13.89280)], 16,
         "Narrow scour track in a forested gully on the upper slope."),
        ("KD-09", "South gully track", "landslide", 1, L, [(98.13100, 13.88580), (98.13214, 13.88545), (98.13321, 13.88528),
                                                          (98.13386, 13.88516)], 14,
         "Debris track along the stream on the south side of the valley, ending above the school."),
        ("KD-01", "Main valley debris flow", "landslide", 5, P, [
            (98.12760, 13.88960), (98.12890, 13.88930), (98.12910, 13.89075), (98.13005, 13.89085), (98.13045, 13.89000),
            (98.13090, 13.88900), (98.13180, 13.88830), (98.13300, 13.88850), (98.13400, 13.88825), (98.13460, 13.88790),
            (98.13500, 13.88750), (98.13620, 13.88740), (98.13680, 13.88730), (98.13680, 13.88640), (98.13640, 13.88580), (98.13500, 13.88580),
            (98.13490, 13.88650), (98.13450, 13.88662), (98.13415, 13.88655), (98.13380, 13.88660), (98.13250, 13.88660), (98.13100, 13.88680), (98.13000, 13.88710),
            (98.12900, 13.88700), (98.12800, 13.88720), (98.12760, 13.88760)], 0,
         "The large debris flow of the valley: an amphitheatre-shaped source scar and the scoured stream channel west of it fed "
         "one flow that cut a corridor through the middle of Ka Det Nge Htein, where houses and the road stood in January."),
        ("KD-OW", "Fields under sediment", "outwash", 9, P, [
            (98.13660, 13.88800), (98.14120, 13.88850), (98.14180, 13.88600), (98.14000, 13.88400), (98.13850, 13.88150),
            (98.13520, 13.88150), (98.13550, 13.88350), (98.13620, 13.88500), (98.13650, 13.88640)], 0,
         "Paddy fields beyond the corridor mouth under fresh sediment or muddy water, with flow streaks fanning out from it."),
        ("KX-1", "Clearing bare in Jan 2026", "exclude", 0, P, [
            (98.13440, 13.88980), (98.13495, 13.88980), (98.13510, 13.89050), (98.13530, 13.89090), (98.13490, 13.89090),
            (98.13450, 13.89050)], 0, "Clearing and track visible on the Esri Vivid image of 10 Jan 2026."),
    ],
    "nmt": [
        ("NM", "Slopes and channels south of the road", "landslide", 5, P, NMT_ZONE, 0,
         "Zone split into connected scars and scoured channels."),
        ("NX-1", "Monastery compound", "exclude", 0, P, [(98.1278, 13.9015), (98.1300, 13.9015), (98.1300, 13.9030),
                                                          (98.1278, 13.9030)], 0,
         "Buildings, yards and the plantation rows east of them, 10 Jan 2026."),
        ("NX-2", "Village road", "exclude", 0, L, [(98.1275, 13.90166), (98.1300, 13.90168), (98.1320, 13.90175),
                                                   (98.1330, 13.90184), (98.1340, 13.90190), (98.1360, 13.90200)], 4,
         "Unsealed road, 10 Jan 2026."),
        ("NX-3", "Pagoda compound", "exclude", 0, P, [(98.1297, 13.8987), (98.1307, 13.8987), (98.1307, 13.8999),
                                                      (98.1297, 13.8999)], 0, "Pagoda, yard and access track, 10 Jan 2026."),
        ("NX-4", "Excavation", "exclude", 0, P, [(98.1336, 13.8994), (98.1347, 13.8994), (98.1357, 13.9002),
                                                 (98.1357, 13.9017), (98.1336, 13.9017)], 0,
         "Earth excavation already bare on 10 Jan 2026."),
        ("NX-5", "Red earthworks at the edge of the excavation", "exclude", 0, P, box_ll(98.13316, 13.90137, 98.13360, 13.90161), 0,
         "Rejected on chip review: red earthworks at the edge of the excavation, not a landslide."),
        ("NX-6", "Plantation rows at the smeared north edge of the flight", "exclude", 0, P, box_ll(98.12902, 13.90408, 98.12958, 13.90443), 0,
         "Rejected on chip review: plantation rows at the smeared north edge of the flight, not a landslide."),
        ("NX-7", "Rusty roof and yard", "exclude", 0, P, box_ll(98.13655, 13.89659, 98.13700, 13.89696), 0,
         "Rejected on chip review: rusty roof and yard, not a landslide."),
        ("NX-8", "Canopy gaps in plantation", "exclude", 0, P, box_ll(98.12690, 13.89720, 98.12734, 13.89782), 0,
         "Rejected on chip review: canopy gaps in plantation, not a landslide."),
        ("NX-9", "Canopy gaps in plantation", "exclude", 0, P, box_ll(98.13628, 13.89767, 98.13660, 13.89811), 0,
         "Rejected on chip review: canopy gaps in plantation, not a landslide."),
        ("NX-10", "Bare patches in a grass field", "exclude", 0, P, box_ll(98.13078, 13.89848, 98.13129, 13.89868), 0,
         "Rejected on chip review: bare patches in a grass field, not a landslide."),
        ("NX-11", "Footpath under trees", "exclude", 0, P, box_ll(98.13534, 13.89663, 98.13597, 13.89679), 0,
         "Rejected on chip review: footpath under trees, not a landslide."),
    ],
}


def build(site):
    rows = []
    for i, name, kind, prio, typ, coords, hw, desc in ENV[site]:
        split = kind == "landslide" and "-" not in i  # a bare prefix marks a zone
        g = LineString(coords) if typ == L else Polygon(coords)
        g = gpd.GeoSeries([g], crs=4326).to_crs(32647).iloc[0]
        if typ == L:
            g = g.buffer(hw, cap_style="round")
        rows.append({"id": i, "name": name, "kind": kind, "priority": prio, "split": int(split), "description": desc,
                     "geometry": g})
    gdf = gpd.GeoDataFrame(rows, crs=32647)
    out = d(site, "inventory", "envelopes.geojson")
    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_crs(4326).to_file(out, driver="GeoJSON")
    print(site, gdf.groupby("kind").size().to_dict())


if __name__ == "__main__":
    for s in ENV:
        build(s)
