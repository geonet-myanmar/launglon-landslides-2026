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
    # Tha Byar (5 Oct 2026, two flights merged). The main valley flow, its large side slides and the southern
    # flow are drawn; the channel network on the ridge west of the valley is a split zone (TC).
    "tby": [
        ("TB-03", "Long slide", "landslide", 1, P, [
            (98.11400, 14.01230), (98.11580, 14.01260), (98.11650, 14.01300), (98.11720, 14.01380), (98.11760, 14.01470),
            (98.11820, 14.01500), (98.11750, 14.01550), (98.11650, 14.01560), (98.11550, 14.01470), (98.11470, 14.01380), (98.11400, 14.01300)], 0,
         "A 500 m open-slope failure on the east face of the ridge: it broke away at about 165 m and ran north-east "
         "down to the floor of the main valley, stripping the forest to bare soil."),
        ("TB-04", "West-bank slide", "landslide", 1, P, [
            (98.11940, 14.00860), (98.11980, 14.00910), (98.12100, 14.00920), (98.12170, 14.00900), (98.12170, 14.00840),
            (98.12050, 14.00830)], 0,
         "Slope failure on the west bank of the debris fan, whose debris slid east into the fan above the village."),
        ("TB-02", "North-west tributary flow", "landslide", 3, P, [
            (98.11170, 14.01600), (98.11170, 14.01850), (98.11200, 14.01920), (98.11550, 14.01940), (98.11580, 14.01800),
            (98.11500, 14.01740), (98.11400, 14.01730), (98.11300, 14.01700), (98.11240, 14.01650), (98.11220, 14.01580)], 0,
         "A tributary from the north-west hills scoured into a wide braided bed of sand and gravel that joins the main "
         "valley flow at the north edge of the survey."),
        ("TB-05", "Southern debris flow", "landslide", 4, P, [
            (98.11660, 14.00080), (98.11700, 13.99940), (98.11950, 13.99930), (98.12050, 14.00000), (98.12080, 14.00120),
            (98.12100, 14.00220), (98.12150, 14.00280), (98.12300, 14.00290), (98.12420, 14.00310), (98.12420, 14.00390),
            (98.12250, 14.00380), (98.12050, 14.00360), (98.11970, 14.00300), (98.11930, 14.00180), (98.11850, 14.00120),
            (98.11750, 14.00120)], 0,
         "A debris flow that enters the survey from the south-west as a broad braided deposit, bends north-east and runs "
         "east along a scoured channel into the southern part of the village."),
        ("TB-01", "Main valley debris flow", "landslide", 5, P, [
            # south-west bank, downstream
            (98.11530, 14.01920), (98.11530, 14.01870), (98.11570, 14.01750), (98.11650, 14.01660), (98.11750, 14.01580),
            (98.11850, 14.01480), (98.11950, 14.01380), (98.12050, 14.01320), (98.12130, 14.01270), (98.12160, 14.01180),
            (98.12170, 14.01100), (98.12160, 14.01000), (98.12100, 14.00970), (98.12050, 14.00920), (98.12130, 14.00830),
            (98.12180, 14.00780), (98.12220, 14.00720),
            # fan toe
            (98.12320, 14.00680), (98.12420, 14.00680), (98.12480, 14.00730),
            # north-east bank, upstream
            (98.12500, 14.00800), (98.12460, 14.00880), (98.12400, 14.00950), (98.12330, 14.01000), (98.12310, 14.01100),
            (98.12360, 14.01200), (98.12320, 14.01300), (98.12260, 14.01400), (98.12200, 14.01460), (98.12050, 14.01520),
            (98.11920, 14.01600), (98.11800, 14.01700), (98.11730, 14.01800), (98.11730, 14.01920)], 0,
         "The debris flow of the main valley: the forested stream from the northern hills was scoured into a channel "
         "30-60 m wide over 1.3 km, and it dumped a fan of boulders, sand and logs at the head of Tha Byar, where "
         "January's image shows forest and orchards."),
        ("TC", "Ridge channel network west of the valley", "landslide", 6, P, [
            (98.11150, 14.01700), (98.11500, 14.01660), (98.11650, 14.01600), (98.11850, 14.01480), (98.12000, 14.01380),
            (98.12100, 14.01280), (98.12140, 14.01180), (98.12150, 14.01000), (98.12050, 14.00950), (98.11950, 14.00830),
            (98.12100, 14.00750), (98.12120, 14.00600), (98.12080, 14.00450), (98.12150, 14.00380), (98.12000, 14.00350),
            (98.11800, 14.00350), (98.11550, 14.00350), (98.11500, 14.00600), (98.11500, 14.01000), (98.11150, 14.01100)], 0,
         "Zone split into connected scars and scoured channels."),
        ("TB-OW1", "Village and fields under sediment", "outwash", 9, P, [
            (98.12220, 14.00700), (98.12500, 14.00720), (98.12620, 14.00780), (98.12750, 14.00800), (98.12900, 14.00810),
            (98.12970, 14.00800), (98.12970, 14.00400), (98.12250, 14.00400), (98.12250, 14.00550)], 0,
         "Houses, orchards and the fields across the main road under sand and mud spread from the fan of the main "
         "valley flow (building footprints are cut out of the area)."),
        ("TB-OW2", "Southern village and fields under sediment", "outwash", 9, P, [
            (98.12420, 14.00400), (98.12970, 14.00400), (98.12970, 13.99850), (98.12550, 13.99850), (98.12450, 14.00050),
            (98.12350, 14.00150), (98.12250, 14.00280), (98.12420, 14.00310)], 0,
         "The southern part of the village and the fields on both sides of the road under sediment spread from the "
         "southern debris flow; all were grass, paddy or orchard on 10 Jan 2026."),
        ("TX-1", "Smeared edge of the flight", "exclude", 0, P, box_ll(98.12830, 14.00780, 98.13060, 14.01000), 0,
         "Plan 1 is smeared here (orthorectification edge) and Plan 2 does not reach: false bare ground."),
        ("TX-2", "Dawei-Launglon road", "exclude", 0, L, [
            (98.12597, 13.99880), (98.12620, 14.00100), (98.12640, 14.00200), (98.12680, 14.00300), (98.12710, 14.00400),
            (98.12730, 14.00500), (98.12740, 14.00600), (98.12755, 14.00700), (98.12790, 14.00760), (98.12850, 14.00800),
            (98.12950, 14.00830), (98.13050, 14.00860)], 5,
         "Unsealed main road, bare on 10 Jan 2026."),
        ("TX-3", "Clearing bare in Jan 2026", "exclude", 0, P, box_ll(98.11995, 14.01175, 98.12135, 14.01290), 0,
         "Plot already cleared to bare soil on the Esri Vivid image of 10 Jan 2026 (now strewn with debris)."),
        ("TX-4", "Crop rows in a field", "exclude", 0, P, box_ll(98.11850, 14.01215, 98.11945, 14.01270), 0,
         "Rejected on chip review: crop rows in a field, not a landslide."),
        ("TX-5", "Canopy gaps in plantation", "exclude", 0, P, box_ll(98.12030, 14.00495, 98.12110, 14.00592), 0,
         "Rejected on chip review: canopy gaps in plantation, not a landslide."),
        ("TX-6", "Canopy gaps in plantation", "exclude", 0, P, box_ll(98.11990, 14.00348, 98.12060, 14.00390), 0,
         "Rejected on chip review: canopy gaps in plantation, not a landslide."),
        ("TX-7", "Shade and a yard under trees", "exclude", 0, P, box_ll(98.12095, 14.00368, 98.12138, 14.00396), 0,
         "Rejected on chip review: shade and a yard under trees beside a house, not a landslide."),
        ("TX-8", "Shade under trees", "exclude", 0, P, box_ll(98.11803, 14.00365, 98.11838, 14.00388), 0,
         "Rejected on chip review: shade under trees, not a landslide."),
        ("TX-9", "Canopy gaps in plantation", "exclude", 0, P, box_ll(98.11760, 14.01610, 98.11900, 14.01680), 0,
         "Rejected on outline review: canopy gaps in the plantation beside the main channel."),
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
