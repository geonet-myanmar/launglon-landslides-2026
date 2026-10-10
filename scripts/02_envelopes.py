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

L, P, F = "line", "poly", "file"


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
    # Ka Det Gyi, Nyaungdon and Wet Thar Kin (6 Oct 2026, two flights merged). Two split zones on the forested hills
    # west of the villages; the fields north-west of the village road are the continuation of Ka Det Nge Htein's
    # sediment fan (KD-OW). The part of the survey already mapped at Ka Det Nge Htein is left out (sites.minus_sites).
    "kdg": [
        ("KGN", "Hills north of the stream", "landslide", 5, P, [
            (98.13600, 13.87700), (98.14600, 13.87700), (98.14600, 13.88000), (98.13600, 13.88000)], 0,
         "Zone split into connected scars and scoured channels."),
        ("KGS", "Hills south of the stream", "landslide", 5, P, [
            (98.13950, 13.87700), (98.14380, 13.87700), (98.14500, 13.87520), (98.15050, 13.87480), (98.15050, 13.87050),
            (98.14700, 13.87000), (98.14600, 13.86550), (98.14150, 13.86550), (98.13950, 13.87000)], 0,
         "Zone split into connected scars and scoured channels."),
        ("KG-OW", "Fields under sediment", "outwash", 9, P, [
            (98.13400, 13.88120), (98.13600, 13.88150), (98.13750, 13.88120), (98.13880, 13.88180), (98.13980, 13.88220),
            (98.14050, 13.88300), (98.14100, 13.88450), (98.14080, 13.88580), (98.13800, 13.88620), (98.13400, 13.88620)], 0,
         "Grass fields north of the village road under fresh sediment: the eastern part of the fan that spread from "
         "the mouth of Ka Det Nge Htein's KD-01 debris flow (building footprints are cut out of the area)."),
        ("KX-1", "Clearing bare in Jan 2026", "exclude", 0, P, box_ll(98.13855, 13.87985, 98.13935, 13.88075), 0,
         "Clearing already bare on the Esri Vivid image of 10 Jan 2026 (now crossed by debris)."),
        ("KX-2", "Compound", "exclude", 0, P, box_ll(98.14580, 13.87195, 98.14675, 13.87310), 0,
         "Buildings and a yard already bare on 10 Jan 2026."),
        ("KX-3", "Track to the compound", "exclude", 0, L, [  # traced on the ortho at 0.33 m/px
            (98.14517, 13.87243), (98.14523, 13.87280), (98.14532, 13.87310), (98.14538, 13.87340), (98.14545, 13.87364),
            (98.14551, 13.87379), (98.14560, 13.87420), (98.14575, 13.87460), (98.14600, 13.87500), (98.14640, 13.87550)], 3,
         "Track bare on 10 Jan 2026 (debris crossed it; the track is cut out)."),
        ("KX-14", "Hairpin of the track and a roof", "exclude", 0, P, box_ll(98.14503, 13.87158, 98.14556, 13.87223), 0,
         "Track hairpin bare on 10 Jan 2026 and a roof beside it."),
        ("KX-4", "Earthworks bare in Jan 2026", "exclude", 0, P, box_ll(98.14880, 13.87090, 98.15060, 13.87170), 0,
         "Earthworks beside the road, already bare on 10 Jan 2026."),
        ("KX-5", "Village road to Nyaungdon", "exclude", 0, L, [
            (98.14740, 13.87498), (98.14800, 13.87500), (98.14900, 13.87496), (98.14960, 13.87490), (98.15060, 13.87490)], 3,
         "Unsealed road, bare on 10 Jan 2026."),
        ("KX-6", "Track across the hill", "exclude", 0, L, [
            (98.14838, 13.87380), (98.14870, 13.87343), (98.14880, 13.87316), (98.14889, 13.87298), (98.14959, 13.87298),
            (98.15044, 13.87297), (98.15060, 13.87297)], 3,
         "Track bare on 10 Jan 2026."),
        ("KX-15", "Clearing edge bare in Jan 2026", "exclude", 0, P, box_ll(98.14945, 13.87250, 98.14998, 13.87295), 0,
         "Rejected on chip review: the edge of a clearing and a track, already bare on 10 Jan 2026."),
        ("KX-7", "Road south of the hill", "exclude", 0, L, [
            (98.14990, 13.87140), (98.15020, 13.87150), (98.15060, 13.87160)], 4, "Road bare on 10 Jan 2026."),
        ("KX-8", "Houses and yards", "exclude", 0, P, box_ll(98.15015, 13.87050, 98.15060, 13.87080), 0,
         "Rejected on chip review: a roof and yard, not a landslide."),
        ("KX-9", "Wet Thar Kin houses and yards", "exclude", 0, P, box_ll(98.13595, 13.87840, 98.13775, 13.88005), 0,
         "Rejected on chip review: roofs, yards and paths of Wet Thar Kin, not a landslide."),
        ("KX-10", "Plantation rows", "exclude", 0, P, box_ll(98.14238, 13.87760, 98.14275, 13.87802), 0,
         "Rejected on chip review: young plantation rows, not a landslide."),
        ("KX-11", "Roofs at the north edge", "exclude", 0, P, box_ll(98.14570, 13.87975, 98.14605, 13.88005), 0,
         "Rejected on chip review: roofs and a yard, not a landslide."),
        ("KX-12", "Patches by the compound", "exclude", 0, P, box_ll(98.14590, 13.87160, 98.14640, 13.87205), 0,
         "Rejected on chip review: yards beside the compound buildings."),
        ("KX-13", "Shade under trees", "exclude", 0, P, box_ll(98.14995, 13.87222, 98.15048, 13.87255), 0,
         "Rejected on chip review: shade and leaf litter under trees, not a landslide."),
    ],
    # Ra Be, on the Ra Be - Kyauk Twin road (8 Oct 2026, two flights merged). Slides and scoured channels cover the
    # hillside on both sides of the road; the whole survey is one split zone (the 55 ha shared with Pyin Gyi - Za Lut
    # stays with that site, sites.minus_sites). The smeared southern edge of the flights is left out.
    "rbe": [
        ("RB-OW", "Fields under sediment east of the road", "outwash", 3, P, [
            (98.15000, 13.71215), (98.15150, 13.71220), (98.15300, 13.71250), (98.15350, 13.71400), (98.15200, 13.71420),
            (98.15050, 13.71420), (98.15010, 13.71300)], 0,
         "Grass fields east of the road under sand spread from the large flow that crossed the road here."),
        ("RB-01", "Debris flow across the road", "landslide", 2, P, [
            (98.14550, 13.71170), (98.14560, 13.71300), (98.14750, 13.71330), (98.14900, 13.71360), (98.14960, 13.71460),
            (98.15050, 13.71460), (98.15060, 13.71100), (98.14900, 13.71100), (98.14900, 13.71200), (98.14800, 13.71210),
            (98.14700, 13.71190)], 0,
         "The longest open-slope flow: it broke away on the hillside west of the road, ran 400 m east, buried the road "
         "and spread debris along it and sand over the fields beyond it (RB-OW)."),
        ("RZ", "Hillside on both sides of the road", "landslide", 5, P, [
            (98.14000, 13.70200), (98.14700, 13.70160), (98.14900, 13.70120), (98.15000, 13.70220), (98.15300, 13.70300),
            (98.15600, 13.70350), (98.16000, 13.70350), (98.16000, 13.71800), (98.14000, 13.71800)], 0,
         "Zone split into connected scars and scoured channels."),
        ("RX-1", "Ra Be - Kyauk Twin road", "exclude", 0, L, [  # traced on the ortho at 0.6-1.0 m/px
            (98.15065, 13.71655), (98.15063, 13.71599), (98.15051, 13.71487), (98.15037, 13.71412), (98.15027, 13.71347),
            (98.15015, 13.71281), (98.14999, 13.71216), (98.14982, 13.71170), (98.14970, 13.71114), (98.14968, 13.71048),
            (98.14979, 13.70983), (98.14984, 13.70918), (98.14973, 13.70843), (98.14956, 13.70778), (98.14937, 13.70712),
            (98.14913, 13.70666), (98.14881, 13.70645), (98.14875, 13.70621), (98.14866, 13.70563), (98.14854, 13.70504),
            (98.14842, 13.70445), (98.14830, 13.70381), (98.14810, 13.70316), (98.14794, 13.70269), (98.14770, 13.70234),
            (98.14734, 13.70210), (98.14698, 13.70175), (98.14650, 13.70152), (98.14590, 13.70131), (98.14530, 13.70122),
            (98.14470, 13.70134), (98.14410, 13.70116), (98.14350, 13.70119), (98.14290, 13.70134), (98.14230, 13.70146),
            (98.14182, 13.70163), (98.14100, 13.70200)], 5,
         "Unsealed road and its cut banks, bare on 10 Jan 2026."),
        ("RX-2", "Track south", "exclude", 0, L, [
            (98.14850, 13.70387), (98.14860, 13.70328), (98.14880, 13.70269), (98.14896, 13.70210), (98.14920, 13.70140)], 3,
         "Track bare on 10 Jan 2026 (debris has since run down it)."),
        ("RX-3", "Plot bare in Jan 2026", "exclude", 0, P, box_ll(98.14990, 13.71520, 98.15070, 13.71640), 0,
         "Earthworks beside the road, already bare on the Esri Vivid image of 10 Jan 2026."),
        ("RX-4", "Fish ponds", "exclude", 0, P, box_ll(98.15050, 13.71430, 98.15200, 13.71530), 0,
         "Fish ponds and bunds, already there on 10 Jan 2026."),
        ("RX-5", "Cleared plantation", "exclude", 0, P, box_ll(98.14250, 13.70380, 98.14430, 13.70610), 0,
         "A plantation plot felled or burnt since January: grey trunks and litter with no slide scar or runout."),
        ("RX-6", "Cleared plantation", "exclude", 0, P, box_ll(98.14450, 13.70240, 98.14530, 13.70340), 0,
         "A plantation plot felled or burnt since January, as RX-5."),
        ("RX-7", "Terraced plantation", "exclude", 0, P, box_ll(98.14100, 13.70270, 98.14320, 13.70470), 0,
         "Terraced young plantation and its paths, already there on 10 Jan 2026."),
        ("RX-8", "Cultivated plot", "exclude", 0, P, box_ll(98.15102, 13.71527, 98.1526, 13.71668), 0,
         "Rejected on chip review: a cultivated plot north of the ponds, with crop rows on 10 Jan 2026."),
        ("RX-9", "Canopy gaps", "exclude", 0, P, box_ll(98.14578, 13.71392, 98.14621, 13.71443), 0,
         "Rejected on chip review: canopy gaps and scrub, not a landslide."),
        ("RX-10", "Smeared flight edge", "exclude", 0, P, box_ll(98.14282, 13.71029, 98.1434, 13.71075), 0,
         "Rejected on chip review: smeared ground at the edge of the flight."),
        ("RX-11", "Scrub patch", "exclude", 0, P, box_ll(98.1508, 13.70929, 98.15118, 13.70962), 0,
         "Rejected on chip review: scrub and litter, not a landslide."),
        ("RX-12", "Scrub patch", "exclude", 0, P, box_ll(98.14852, 13.71545, 98.14887, 13.71592), 0,
         "Rejected on chip review: scrub and canopy gaps, not a landslide."),
        ("RX-13", "Plantation rows", "exclude", 0, P, box_ll(98.14429, 13.70416, 98.14476, 13.70457), 0,
         "Rejected on chip review: plantation rows, not a landslide."),
        ("RX-14", "Garden plot", "exclude", 0, P, box_ll(98.15047, 13.71417, 98.15092, 13.71433), 0,
         "Rejected on chip review: a garden plot beside a house."),
        ("RX-15", "Strip bare in Jan 2026", "exclude", 0, P, box_ll(98.14947, 13.70851, 98.14963, 13.7089), 0,
         "Rejected on chip review: a strip beside the road already pale on 10 Jan 2026."),
    ],
    # Pyin Gyi and Za Lut (7 Oct 2026, two flights merged): forested hills west of the road through the villages.
    # The village flow, the road fan and the two large channel systems are drawn; the rest of the hills is a split zone.
    "pgz": [
        ("PG-01", "Village debris flow", "landslide", 1, P, [
            (98.16555, 13.70610), (98.16700, 13.70600), (98.16760, 13.70600), (98.16820, 13.70580), (98.16900, 13.70560),
            (98.16910, 13.70500), (98.16850, 13.70470), (98.16780, 13.70440), (98.16720, 13.70440), (98.16690, 13.70480),
            (98.16620, 13.70520), (98.16555, 13.70570)], 0,
         "A debris flow off the hill west of the road that crossed the road and buried the block of houses between the road "
         "and the paddies in the middle of the village; the ground was being dug out with machinery on 7 Oct."),
        ("PG-03", "Road debris flow", "landslide", 2, P, [  # both banks traced on the ortho at 0.8 m/px
            (98.16720, 13.71020), (98.16620, 13.71040), (98.16520, 13.71060), (98.16450, 13.71040), (98.16400, 13.70980),
            (98.16370, 13.70900), (98.16340, 13.70820), (98.16330, 13.70740), (98.16310, 13.70680), (98.16240, 13.70620),
            (98.16170, 13.70580), (98.16100, 13.70520), (98.16080, 13.70470), (98.16140, 13.70440), (98.16220, 13.70500),
            (98.16290, 13.70570), (98.16360, 13.70630), (98.16420, 13.70680), (98.16520, 13.70740), (98.16520, 13.70770),
            (98.16440, 13.70770), (98.16440, 13.70830), (98.16520, 13.70880), (98.16580, 13.70920), (98.16620, 13.70960),
            (98.16700, 13.70970)], 0,
         "The main channel flow: fed by the scars at the head of the valley (PG-04), it scoured a channel of grey sand and "
         "boulders north-east down the valley, spread across the road north of the village and ran on as a fan beyond it."),
        ("PG-04", "South-west channels", "landslide", 3, P, [
            (98.15700, 13.70350), (98.15780, 13.70520), (98.16000, 13.70500), (98.16200, 13.70540), (98.16330, 13.70620),
            (98.16360, 13.70600), (98.16220, 13.70480), (98.16080, 13.70440), (98.16030, 13.70300), (98.16000, 13.70200),
            (98.15920, 13.70200), (98.15900, 13.70330), (98.15820, 13.70330)], 0,
         "Two broad scars at the head of the valley and a third channel from the south, which joined and fed the road "
         "debris flow (PG-03); their upper parts run beyond the flight."),
        ("PG-05", "North-west valley flow", "landslide", 3, P, [
            (98.15230, 13.71330), (98.15330, 13.71270), (98.15420, 13.71150), (98.15500, 13.71060), (98.15460, 13.71030),
            (98.15380, 13.71070), (98.15300, 13.71180), (98.15220, 13.71280)], 0,
         "A debris flow down the valley at the north-west edge of the survey with a side scar from the east."),
        ("PG-OW1", "Fields under sediment north-west", "outwash", 9, P, [
            (98.15150, 13.71330), (98.15240, 13.71330), (98.15280, 13.71460), (98.15300, 13.71650), (98.15260, 13.71750),
            (98.15180, 13.71680), (98.15110, 13.71560)], 0,
         "Grass fields and fish ponds at the valley mouth under fresh sand and gravel (ponds and paths excluded)."),
        ("PGZ", "Hills west of the road", "landslide", 6, P, [
            (98.15500, 13.71200), (98.16120, 13.71200), (98.16400, 13.71000), (98.16400, 13.70700), (98.16300, 13.70650),
            (98.16000, 13.70600), (98.15700, 13.70600), (98.15600, 13.70800), (98.15500, 13.71000)], 0,
         "Zone split into connected scars and scoured channels."),
        ("PX-1", "Road through Za Lut and Pyin Gyi", "exclude", 0, L, [
            (98.15990, 13.71720), (98.16020, 13.71660), (98.16030, 13.71580), (98.16060, 13.71500), (98.16100, 13.71430),
            (98.16160, 13.71350), (98.16230, 13.71290), (98.16310, 13.71250), (98.16380, 13.71210), (98.16450, 13.71110),
            (98.16520, 13.71000), (98.16560, 13.70930), (98.16620, 13.70880), (98.16640, 13.70800), (98.16660, 13.70760),
            (98.16700, 13.70700), (98.16730, 13.70660), (98.16740, 13.70600), (98.16740, 13.70540), (98.16740, 13.70470),
            (98.16720, 13.70420), (98.16700, 13.70360), (98.16710, 13.70300), (98.16720, 13.70240), (98.16740, 13.70180),
            (98.16770, 13.70120), (98.16800, 13.70070)], 4,
         "Road bare on 10 Jan 2026 (debris was cleared from it by 7 Oct; the road itself is cut out)."),
        ("PX-2", "Fish ponds and bunds", "exclude", 0, P, box_ll(98.15100, 13.71450, 98.15240, 13.71520), 0,
         "Fish ponds and their bunds, already there on 10 Jan 2026."),
        ("PX-3", "Rectangular cleared plot", "exclude", 0, P, box_ll(98.16595, 13.70430, 98.16675, 13.70480), 0,
         "Rejected on chip review: a rectangular plot with straight cut edges - cleared by people since January, not a slide."),
        ("PX-4", "Rock slab bare in Jan 2026", "exclude", 0, P, box_ll(98.15940, 13.70595, 98.16015, 13.70672), 0,
         "Rejected on chip review: a dark striated rock slab, already a dark bare patch on 10 Jan 2026."),
        ("PX-5", "Rock slab bare in Jan 2026", "exclude", 0, P, box_ll(98.15958, 13.70738, 98.16006, 13.70769), 0,
         "Rejected on chip review: a dark striated rock slab, already a dark bare patch on 10 Jan 2026."),
        ("PX-6", "Rock slab bare in Jan 2026", "exclude", 0, P, box_ll(98.15910, 13.70619, 98.15930, 13.70654), 0,
         "Rejected on chip review: a dark rock slab, already bare on 10 Jan 2026."),
        ("PX-7", "Standing roof at the flow edge", "exclude", 0, P, box_ll(98.16745, 13.70448, 98.16785, 13.70482), 0,
         "A roof still standing at the south edge of PG-01; cut out so it is not counted as debris."),
        ("PX-8", "Standing roof at the flow edge", "exclude", 0, P, box_ll(98.16745, 13.70560, 98.16770, 13.70590), 0,
         "A roof still standing at the north edge of PG-01; cut out so it is not counted as debris."),
    ],
    # The road to Pa Nyit (5 Oct 2026): forested hillside east of the village where the road winds down in hairpins.
    "pny": [
        ("PN-02", "Head slide", "landslide", 1, P, [
            (98.08580, 13.99720), (98.08760, 13.99725), (98.08765, 13.99800), (98.08640, 13.99800), (98.08580, 13.99770)], 0,
         "Open-slope slide on the east side of the stream head; its debris ran west into the scoured channel."),
        ("PN-03", "Bank slide", "landslide", 1, P, box_ll(98.08455, 13.99425, 98.08560, 13.99480), 0,
         "Small slide off the east bank of the channel, above the road."),
        ("PN-04", "Hairpin slides", "landslide", 2, P, [
            (98.08300, 13.99135), (98.08380, 13.99110), (98.08530, 13.99120), (98.08560, 13.99160), (98.08600, 13.99260),
            (98.08440, 13.99285), (98.08350, 13.99265), (98.08310, 13.99230)], 0,
         "A cluster of slope failures on and below the road where it winds down in hairpins: debris lay across the road "
         "and ran down the slope below it - the road blockage reported between Launglon and Pa Nyit."),
        ("PN-01", "Stream channel debris flow", "landslide", 3, L, [
            (98.08700, 13.99870), (98.08660, 13.99820), (98.08620, 13.99760), (98.08550, 13.99660), (98.08470, 13.99590),
            (98.08450, 13.99510), (98.08370, 13.99460), (98.08350, 13.99430), (98.08360, 13.99360), (98.08340, 13.99300),
            (98.08310, 13.99280), (98.08280, 13.99230), (98.08230, 13.99180), (98.08190, 13.99170)], 18,
         "A forested stream scoured to bare rock and gravel for about 900 m, from the top of the survey down across "
         "the road at the S-bend and on to the south-west edge."),
        ("PN-05", "East channel", "landslide", 3, L, [
            (98.08900, 13.99540), (98.08860, 13.99480), (98.08820, 13.99460), (98.08790, 13.99400), (98.08780, 13.99320),
            (98.08800, 13.99250)], 16,
         "A gully scoured down the slope east of the main stream."),
        ("PN-06", "North-east channel", "landslide", 3, P, [
            (98.08960, 13.99480), (98.08990, 13.99520), (98.09060, 13.99560), (98.09140, 13.99600), (98.09160, 13.99560),
            (98.09080, 13.99510), (98.09000, 13.99460)], 0,
         "A wide scoured channel at the north-east edge of the survey; it continues beyond the flight."),
        ("PN-07", "Slides above the S-bend", "landslide", 1, P, box_ll(98.08370, 13.99318, 98.08412, 13.99372), 0,
         "Two small slides on the slope just above the road where it crosses the stream."),
        ("PX-4", "Patch already brown in Jan 2026", "exclude", 0, P, box_ll(98.08552, 13.99318, 98.08598, 13.99362), 0,
         "Rejected on chip review: a fresh-looking scar above the road, but the spot is already brown on the Esri Vivid "
         "image of 10 Jan 2026, so it may predate the storm."),
        ("PX-1", "Road to Pa Nyit", "exclude", 0, L, [  # traced on the drone ortho at 0.3 m/px
            (98.08000, 13.99470), (98.08050, 13.99450), (98.08100, 13.99400), (98.08150, 13.99345), (98.08169, 13.99329),
            (98.08191, 13.99319), (98.08222, 13.99304), (98.08244, 13.99280), (98.08281, 13.99265), (98.08303, 13.99274),
            (98.08316, 13.99281), (98.08323, 13.99274), (98.08327, 13.99260), (98.08338, 13.99253), (98.08363, 13.99257),
            (98.08378, 13.99264), (98.08391, 13.99257), (98.08400, 13.99243), (98.08416, 13.99239), (98.08428, 13.99234),
            (98.08433, 13.99222), (98.08434, 13.99203), (98.08447, 13.99191), (98.08466, 13.99184), (98.08472, 13.99170),
            (98.08481, 13.99155), (98.08488, 13.99136), (98.08497, 13.99118), (98.08513, 13.99100), (98.08534, 13.99081),
            (98.08556, 13.99074), (98.08588, 13.99074), (98.08613, 13.99077), (98.08644, 13.99068), (98.08700, 13.99130),
            (98.08750, 13.99120), (98.08800, 13.99110)], 5,
         "Unsealed road and its cut banks, bare on 10 Jan 2026."),
        ("PX-2", "Rock outcrop", "exclude", 0, P, box_ll(98.08200, 13.99395, 98.08290, 13.99510), 0,
         "Dark rock outcrop already bare on the Esri Vivid image of 10 Jan 2026."),
        ("PX-3", "Dark patch bare before", "exclude", 0, P, box_ll(98.08635, 13.99350, 98.08700, 13.99410), 0,
         "Dark wet patch, already brown on the Esri Vivid image of 10 Jan 2026."),
    ],
}


# Main road through Tha Win and Taw Kye (OpenStreetMap, checked on the ortho: within 2-3 m), south to north
THW_ROAD = [(98.15734, 13.7711), (98.15669, 13.77227), (98.15653, 13.77276), (98.15607, 13.77725), (98.15609, 13.77781),
            (98.15624, 13.77838), (98.15812, 13.78348), (98.15825, 13.78408), (98.15844, 13.78644), (98.15859, 13.78742),
            (98.15876, 13.78821), (98.15924, 13.78912), (98.15933, 13.78966), (98.15945, 13.79161), (98.15932, 13.79436),
            (98.15934, 13.7947), (98.1596, 13.79616), (98.15967, 13.79636), (98.15983, 13.7971), (98.15984, 13.79734),
            (98.15983, 13.79757), (98.15948, 13.79919), (98.15944, 13.7995), (98.15966, 13.80125), (98.15978, 13.80157),
            (98.16009, 13.80211), (98.16027, 13.80254), (98.16041, 13.80422), (98.16041, 13.80454), (98.16038, 13.80468),
            (98.16024, 13.80498), (98.16005, 13.80524), (98.15977, 13.80554), (98.15956, 13.80586), (98.15932, 13.80706),
            (98.15923, 13.8085), (98.15926, 13.80886), (98.15956, 13.80978), (98.15959, 13.80996), (98.15955, 13.81156),
            (98.15963, 13.81202)]
LHL_ROAD = [(98.15132, 13.75438), (98.15217, 13.75557), (98.15239, 13.75581), (98.15282, 13.75606), (98.15428, 13.75674),
            (98.15453, 13.75702), (98.15483, 13.75789), (98.1551, 13.75846), (98.15641, 13.76041), (98.15691, 13.76107),
            (98.15807, 13.7628), (98.15818, 13.76321), (98.15812, 13.76447), (98.15789, 13.76588), (98.15785, 13.76635),
            (98.15784, 13.76751), (98.15774, 13.7691), (98.15734, 13.7711)]

# Tha Win (8 Oct 2026, northern block of the 4-flight delivery): forested hills west of the road from Tha Win north past
# Taw Kye. The 2 Oct Taw Kye survey keeps the ground it covers (sites.minus_sites). The northern valley flow and the
# sediment it spread to the road are drawn; through Tha Win the zone stops at the foot of the hill and the sediment in the
# village is outwash; everything else on the hills is one split zone (TZ).
THW_FOOT = [(98.1555, 13.7707), (98.1555, 13.7732), (98.1550, 13.7752), (98.1540, 13.7767), (98.1533, 13.7777),
            (98.1530, 13.7789), (98.1540, 13.7796), (98.1544, 13.7804), (98.1560, 13.7811), (98.1564, 13.7825),
            (98.1570, 13.7840)]  # foot of the hill behind Tha Win (village and gardens to the east), south to north
ENV["thw"] = [
    ("TW-01", "Northern valley debris flow", "landslide", 2, P, [
        (98.14918, 13.80918), (98.15014, 13.80926), (98.1505, 13.80844), (98.1513, 13.80765), (98.15234, 13.80687),
        (98.15314, 13.80624), (98.15378, 13.80562), (98.15458, 13.80515), (98.1555, 13.80499), (98.1555, 13.80245),
        (98.1545, 13.80249), (98.1533, 13.80261), (98.1529, 13.80296), (98.15322, 13.80358), (98.1530, 13.8045),
        (98.1524, 13.8052), (98.1515, 13.8060), (98.1510, 13.8067), (98.1503, 13.8074), (98.14962, 13.80804),
        (98.14922, 13.80859)], 0,
     "The largest flow: a debris flow from a wide scar at the head of the valley north-west of Taw Kye, which ran 700 m "
     "south-east down the valley, scouring it to grey sand, and spread over the valley floor where the western channel "
     "joins it. Its sediment continues east to the road (TW-OW1) and south into the 2 Oct Taw Kye survey (LS-01)."),
    ("TW-OW1", "Valley mouth under sediment", "outwash", 3, P, [
        (98.1555, 13.8018), (98.1555, 13.8052), (98.1570, 13.8057), (98.1590, 13.8057), (98.15977, 13.80554),
        (98.16005, 13.80524), (98.16024, 13.80498), (98.16041, 13.80454), (98.16041, 13.80422), (98.16027, 13.80254),
        (98.16009, 13.80211), (98.1598, 13.8018)], 0,
     "Fields and scrub at the mouth of the northern valley under grey sand and orange mud from TW-01, up to the road."),
    ("TW-OW4", "Paddies east of the road under sediment", "outwash", 3, P, [
        (98.1604, 13.8020), (98.1620, 13.8020), (98.1625, 13.8040), (98.1628, 13.8055), (98.1606, 13.8057),
        (98.1604, 13.8045)], 0,
     "Paddies east of the road, green on 10 Jan 2026, now under orange mud where the valley flow's sediment crossed the road."),
    ("TW-OW2", "West Tha Win under sediment", "outwash", 3, P, [
        (98.1530, 13.7789), (98.1533, 13.7777), (98.1540, 13.7767), (98.1548, 13.7762), (98.15605, 13.7764),
        (98.15607, 13.77725), (98.15609, 13.77781), (98.1562, 13.7784), (98.1555, 13.7792), (98.1544, 13.7796),
        (98.1540, 13.7796)], 0,
     "The western part of Tha Win, between the foot of the hill and the road, under the sand and debris of the two "
     "channels that meet behind the village."),
    ("TW-OW3", "North Tha Win under sediment", "outwash", 3, P, box_ll(98.1552, 13.7810, 98.1566, 13.7826), 0,
     "Gardens at the north end of Tha Win under sand from the channel behind them."),
    ("TW-OW5", "Field beside the road under sediment", "outwash", 3, P, box_ll(98.15822, 13.80843, 98.1592, 13.80957), 0,
     "A grass field beside the road at the north edge of the survey under mud washed down from the slides above it "
     "(TZ-08); flat ground, so not a slide of its own."),
    ("TZ", "Hills west of the road", "landslide", 5, P,
     [(98.140, 13.7707)] + THW_FOOT + [(x, y) for x, y in THW_ROAD if 13.7841 < y < 13.812] + [(98.1596, 13.812), (98.140, 13.812)], 0,
     "Zone split into connected scars and scoured channels."),
    ("TX-1", "Main road", "exclude", 0, L, THW_ROAD, 5, "The road through Tha Win and Taw Kye and its cut banks."),
    ("TX-2", "Compound bare in Jan 2026", "exclude", 0, P, box_ll(98.1570, 13.7862, 98.1586, 13.7880), 0,
     "A compound beside the road, already bare on the Esri Vivid image of 10 Jan 2026 (debris has since run into it)."),
    ("TX-3", "Roadside yards", "exclude", 0, P, box_ll(98.1555, 13.7838, 98.1595, 13.7856), 0,
     "Houses and yards beside the road, bare on 10 Jan 2026."),
    ("TX-4", "Terraced clearing", "exclude", 0, P, box_ll(98.1487, 13.8043, 98.1510, 13.8062), 0,
     "A terraced clearing above the western channel, already cleared on 10 Jan 2026."),
    ("TX-5", "Smeared flight edge", "exclude", 0, P, box_ll(98.1470, 13.7870, 98.1490, 13.7912), 0,
     "Rejected on chip review: smeared ground at the west edge of the flights."),
    ("TX-6", "Track loop", "exclude", 0, P, box_ll(98.15814, 13.80606, 98.15932, 13.80707), 0,
     "Rejected on chip review: a looping track and clearing already bare on 10 Jan 2026."),
    ("TX-7", "Roadside gardens", "exclude", 0, P, box_ll(98.15829, 13.80701, 98.1593, 13.80843), 0,
     "Rejected on chip review: gardens and a field beside the road, partly bare on 10 Jan 2026."),
    ("TX-8", "Road edge", "exclude", 0, P, box_ll(98.15918, 13.80555, 98.15961, 13.8073), 0,
     "Rejected on chip review: the edge of the road."),
    ("TX-9", "Yard bare in Jan 2026", "exclude", 0, P, box_ll(98.15761, 13.78583, 98.15833, 13.78623), 0,
     "Rejected on chip review: sandy ground beside the compound (TX-2), already bare on 10 Jan 2026."),
    ("TX-10", "Road edge", "exclude", 0, P, box_ll(98.15851, 13.78835, 98.15903, 13.78881), 0,
     "Rejected on chip review: the road edge and a yard bare on 10 Jan 2026."),
    ("TX-11", "Yard and canopy gaps", "exclude", 0, P, box_ll(98.15446, 13.77362, 98.15515, 13.77478), 0,
     "Rejected on chip review: a yard beside a hut and canopy gaps, not a landslide."),
]
# Lel Hla (8 Oct 2026, southern block of the same delivery): forested hills west of the road through Lel Hla. The long
# flow that reached the road is drawn, its fan east of the road is outwash; the zone stops at the foot of the hill
# (village and gardens to the east). The smeared south-west corner of the flights is left out.
ENV["lhl"] = [
    ("LL-01", "Debris flow to the road", "landslide", 2, P, [
        (98.14664, 13.76693), (98.14871, 13.76701), (98.14986, 13.7670), (98.151, 13.7668), (98.15186, 13.76631),
        (98.153, 13.7661), (98.15443, 13.76596), (98.1550, 13.7658), (98.1556, 13.7654), (98.1566, 13.7651),
        (98.1574, 13.7656), (98.15797, 13.7656), (98.15800, 13.7632), (98.1572, 13.7632), (98.1565, 13.7636),
        (98.1555, 13.7638), (98.1545, 13.7642), (98.15414, 13.76451), (98.15329, 13.76518), (98.15243, 13.76535),
        (98.15243, 13.76444), (98.15157, 13.76451), (98.14914, 13.76479), (98.14829, 13.76521), (98.14664, 13.76613)], 0,
     "A debris flow that broke away in two prongs on the hills west of Lel Hla, ran 1.2 km east down a forested valley, "
     "scouring it to grey sand, and reached the road at the south end of the village; its fan crossed the road (LL-OW1)."),
    ("LL-OW1", "Gardens east of the road under sediment", "outwash", 3, P, [
        (98.1581, 13.7630), (98.1581, 13.7645), (98.1590, 13.7643), (98.1600, 13.7636), (98.1604, 13.7628),
        (98.1598, 13.7625), (98.1588, 13.7627)], 0,
     "Gardens and scrub east of the road, green on 10 Jan 2026, now under the sand of LL-01's fan."),
    ("LZ", "Hills west of Lel Hla", "landslide", 5, P, [
        (98.140, 13.755), (98.1541, 13.755), (98.1541, 13.7645), (98.1550, 13.7660), (98.1550, 13.7707),
        (98.140, 13.7707)], 0,
     "Zone split into connected scars and scoured channels."),
    ("LX-1", "Main road", "exclude", 0, L, LHL_ROAD, 5, "The road through Lel Hla and its cut banks."),
    ("LX-2", "Plot bare in Jan 2026", "exclude", 0, P, box_ll(98.1572, 13.7633, 98.1579, 13.7654), 0,
     "Plots beside the road, already bare on the Esri Vivid image of 10 Jan 2026 (LL-01's debris has since covered them)."),
    ("LX-3", "Smeared flight corner", "exclude", 0, P, box_ll(98.1465, 13.7560, 98.1520, 13.7600), 0,
     "The south-west corner of the flights is smeared (orthorectification edge); left out."),
    ("LX-4", "Rock slab", "exclude", 0, P, box_ll(98.14875, 13.76716, 98.14927, 13.76753), 0,
     "Rejected on chip review: a rock slab already dark and bare on 10 Jan 2026."),
    ("LX-5", "Rock slabs", "exclude", 0, P, box_ll(98.14767, 13.76277, 98.1482, 13.76343), 0,
     "Rejected on chip review: rock slabs already bare on 10 Jan 2026."),
    ("LX-6", "House and yard", "exclude", 0, P, box_ll(98.15371, 13.761, 98.15413, 13.76141), 0,
     "Rejected on chip review: a house, its yard and track."),
    ("LX-7", "Cleared plantation", "exclude", 0, P, box_ll(98.15201, 13.76196, 98.15314, 13.7631), 0,
     "Rejected on chip review: young plantation on ground already cleared on 10 Jan 2026."),
    ("LX-8", "Rock slab", "exclude", 0, P, box_ll(98.15312, 13.76345, 98.15351, 13.76375), 0,
     "Rejected on chip review: a rock slab already dark on 10 Jan 2026."),
    ("LX-9", "Rock slab", "exclude", 0, P, box_ll(98.15093, 13.76376, 98.15139, 13.76406), 0,
     "Rejected on chip review: a rock slab already dark on 10 Jan 2026."),
]

# Ti Zit (9 Oct 2026, two flights that meet without overlapping). North: the hills east and north of the tidal flat
# behind Ti Zit's beach; the flat, the beach and the village were sand, mud and yards on 10 Jan 2026 and are left out,
# except the fan the eastern slides spread over grass and scrub (TZ-OW1). South: 3.5 km of forested coast; the zone
# stops at the back of the beach (the debris fans on the beach and in the sea are not mapped).
ENV["tzt"] = [
    ("TZ-OW1", "Fan below the eastern slides", "outwash", 3, P, [
        (98.0905, 13.9143), (98.0870, 13.9147), (98.0855, 13.9142), (98.0850, 13.9128), (98.0860, 13.9118),
        (98.0884, 13.9110), (98.0905, 13.9103)], 0,
     "Grass and scrub at the foot of the hill east of the tidal flat, now under the sand and boulders the eastern slides "
     "spread across the track and down to the houses at the edge of the flat."),
    ("TN", "Hills east and north of the tidal flat", "landslide", 5, P, [
        (98.0780, 13.9157), (98.0838, 13.9157), (98.0870, 13.9147), (98.0885, 13.9143), (98.0890, 13.9124),
        (98.0884, 13.9113), (98.0905, 13.9100), (98.0925, 13.9085), (98.0955, 13.9085), (98.0955, 13.9235),
        (98.0780, 13.9235)], 0,
     "Zone split into connected scars and scoured channels."),
    ("TS", "Coastal hills south-east of Ti Zit", "landslide", 5, P, [
        (98.0990, 13.9035), (98.1120, 13.9035), (98.1120, 13.8710), (98.0947, 13.8710), (98.0947, 13.8726),
        (98.0946, 13.8733), (98.0944, 13.8745), (98.0950, 13.8751), (98.0951, 13.8771), (98.0952, 13.8789),
        (98.0943, 13.8794), (98.0939, 13.8803), (98.0939, 13.8812), (98.0943, 13.8822), (98.09495, 13.88345),
        (98.0951, 13.8850), (98.0965, 13.8858), (98.0985, 13.8862), (98.0992, 13.8875), (98.0992, 13.8890),
        (98.0985, 13.8904), (98.0978, 13.8915), (98.0972, 13.8928), (98.0990, 13.8935)], 0,
     "Zone split into connected scars and scoured channels; its western edge is the back of the beach."),
    ("ZX-1", "Compound bare in Jan 2026", "exclude", 0, P, box_ll(98.0868, 13.9133, 98.0905, 13.9152), 0,
     "A levelled compound beside the track, already bare on the Esri Vivid image of 10 Jan 2026 (the eastern slides' "
     "debris has since run across it)."),
    ("ZX-2", "Young plantation", "exclude", 0, P, box_ll(98.0903, 13.9108, 98.0932, 13.9133), 0,
     "Rows of young plantation on cleared ground."),
    ("ZX-3", "Young plantation", "exclude", 0, P, box_ll(98.0808, 13.9186, 98.0824, 13.9202), 0,
     "Rows of young plantation on cleared ground."),
    ("ZX-4", "Plantation rows", "exclude", 0, P, box_ll(98.08573, 13.91496, 98.0864, 13.9154), 0,
     "Rejected on chip review: rows of young plantation below the TN-05 slide."),
    ("ZX-5", "Square earthworks", "exclude", 0, P, box_ll(98.07921, 13.91567, 98.07966, 13.91603), 0,
     "Rejected on chip review: a square cut plot beside the track, earthworks rather than a slide."),
    ("ZX-6", "Houses and yards", "exclude", 0, P, box_ll(98.0897, 13.91038, 98.09022, 13.91099), 0,
     "Rejected on chip review: houses and yards at the edge of the village."),
    ("ZX-7", "Yard by the track", "exclude", 0, P, box_ll(98.08263, 13.91567, 98.08294, 13.91601), 0,
     "Rejected on chip review: a yard beside the track."),
    ("ZX-8", "Plot bare in Jan 2026", "exclude", 0, P, box_ll(98.08839, 13.91118, 98.08876, 13.91144), 0,
     "Rejected on chip review: a plot by the track, already bare on 10 Jan 2026."),
    ("ZX-9", "Dry scrub", "exclude", 0, P, box_ll(98.08034, 13.91883, 98.08083, 13.91928), 0,
     "Rejected on chip review: scattered bare patches in dry scrub, as on 10 Jan 2026."),
    ("ZX-10", "Sandy gardens and tracks", "exclude", 0, P, box_ll(98.09897, 13.89956, 98.1007, 13.90137), 0,
     "Rejected on chip review: sandy gardens, a clearing, houses and tracks behind the north end of the beach, pale or brown on 10 Jan 2026."),
    ("ZX-11", "Garden plots and tracks", "exclude", 0, P, box_ll(98.09897, 13.89527, 98.10018, 13.89855), 0,
     "Rejected on chip review: garden plots, plantation rows and straight tracks, not landslides."),
    ("ZX-12", "Canopy gaps", "exclude", 0, P, box_ll(98.10135, 13.90106, 98.1018, 13.90153), 0,
     "Rejected on chip review: canopy gaps."),
    ("ZX-13", "Beach edge and paths", "exclude", 0, P, box_ll(98.09736, 13.89106, 98.09913, 13.8933), 0,
     "Rejected on chip review: the beach edge, a path and sandy scrub behind the beach, pale on 10 Jan 2026."),
    ("ZX-14", "Beach edge", "exclude", 0, P, box_ll(98.0946, 13.87233, 98.09499, 13.87314), 0,
     "Rejected on chip review: the edge of the beach."),
    ("ZX-15", "Plantation rows", "exclude", 0, P, box_ll(98.10621, 13.90143, 98.10658, 13.9018), 0,
     "Rejected on chip review: plantation rows at the edge of the flight."),
]

# Ti Zit watershed (10 Oct 2026): the forested basin north-east of Ti Zit, whose valleys drain south-west into the eastern
# part of the village. The hills are four split zones (WN, WM, WE, WV); where the valley flows spread sand between the houses the
# ground is outwash (WS-OW1). The road from the village up the valley and over the hills (OpenStreetMap, checked on the
# ortho) is excluded with its cut banks. Ground already covered by the 9 Oct Ti Zit flights stays with Ti Zit.
TZW_ROAD = [(98.0937, 13.90756), (98.09443, 13.90757), (98.09555, 13.90801), (98.09615, 13.90836), (98.09684, 13.90882),
            (98.0978, 13.9093), (98.0981, 13.90947), (98.09838, 13.91011), (98.09911, 13.91122), (98.09941, 13.91147),
            (98.10014, 13.91222), (98.10094, 13.91294), (98.10141, 13.91352), (98.10179, 13.91382), (98.10189, 13.91414),
            (98.10195, 13.91444), (98.10183, 13.91462), (98.10181, 13.91486), (98.10204, 13.91532), (98.10223, 13.91595),
            (98.1029, 13.91647), (98.10313, 13.91683), (98.10375, 13.91734), (98.10457, 13.91792), (98.1047, 13.9184),
            (98.10522, 13.91844), (98.10579, 13.91859), (98.10664, 13.91864), (98.10644, 13.91912), (98.10607, 13.91948),
            (98.10646, 13.91951), (98.10716, 13.91892), (98.10789, 13.91865), (98.10847, 13.91858), (98.10921, 13.91875),
            (98.10957, 13.91852), (98.10984, 13.91848), (98.11034, 13.91863), (98.11084, 13.91927), (98.1118, 13.91992),
            (98.11274, 13.92013), (98.11343, 13.92066), (98.11437, 13.92077), (98.11519, 13.91983), (98.11536, 13.92043),
            (98.11616, 13.92053), (98.11702, 13.92152), (98.11756, 13.92321), (98.1182, 13.92385), (98.12027, 13.92414),
            (98.12132, 13.92472), (98.12219, 13.92536), (98.12298, 13.92612)]
TZW_SOUTH_ROAD = [(98.09615, 13.90836), (98.09659, 13.90777), (98.09708, 13.90711), (98.09731, 13.90626), (98.09769, 13.90559),
                  (98.09815, 13.90518), (98.09857, 13.90387), (98.09888, 13.90317), (98.09911, 13.9022), (98.09968, 13.9011)]
# cut between the west network (WN) and the large slide north of the road (WM), south to north
TZW_CUT_N = [(98.1068, 13.9175), (98.1068, 13.9185), (98.1066, 13.9190), (98.1056, 13.9195), (98.1051, 13.9200),
             (98.1053, 13.9205), (98.1060, 13.9210), (98.10676, 13.9215), (98.1065, 13.9222), (98.1065, 13.9231),
             (98.1050, 13.9235), (98.1042, 13.9240), (98.1042, 13.9246), (98.1070, 13.9250), (98.1080, 13.9254),
             (98.1080, 13.9320)]
# cut between the slides on the east ridge (WE) and the two valley flows below them (WV), west to east
TZW_CUT_S = [(98.1005, 13.9150), (98.1020, 13.9150), (98.1030, 13.9152), (98.1040, 13.9150), (98.1050, 13.91484),
             (98.1060, 13.9148), (98.1070, 13.9148), (98.1080, 13.9150), (98.1090, 13.9155), (98.1100, 13.9150),
             (98.1110, 13.9146), (98.1120, 13.9143), (98.1140, 13.9143), (98.1150, 13.9140), (98.1250, 13.9140)]


def tzw_zone(half, part):
    """One of the four Ti Zit watershed zones as a coordinate list: half N / S of the road, then part W / E (north
    half) or N / S (south half) of the cut traced through that half."""
    road = Polygon([(98.090, 13.9075)] + TZW_ROAD + [(98.124, 13.9270)] +
                   ([(98.124, 13.931), (98.090, 13.931)] if half == "N" else [(98.124, 13.900), (98.090, 13.900)]))
    if half == "N":
        side = Polygon([(98.080, 13.890), (TZW_CUT_N[0][0], 13.890)] + TZW_CUT_N + [(98.080, TZW_CUT_N[-1][1])])  # west of the cut
    else:
        side = Polygon([(TZW_CUT_S[0][0], 13.940)] + TZW_CUT_S + [(TZW_CUT_S[-1][0], 13.940)])  # north of the cut
    g = road.intersection(side) if part in ("W", "N") else road.difference(side)
    g = max(getattr(g, "geoms", [g]), key=lambda q: q.area)
    return list(g.exterior.coords)


ENV["tzw"] = [
    ("WS-OW1", "East Ti Zit under sediment", "outwash", 3, P, [
        (98.0935, 13.9080), (98.0955, 13.9072), (98.0985, 13.9070), (98.1000, 13.9080), (98.1000, 13.9095),
        (98.1005, 13.9110), (98.1000, 13.9118), (98.0990, 13.9118), (98.0975, 13.9100), (98.0955, 13.9093),
        (98.0935, 13.9092)], 0,
     "The eastern part of Ti Zit, where the two valley flows from the watershed came out of the hills and spread sand and "
     "debris between the houses and along the road."),
    # four zones (one zone of the whole basin, 1.4 Gpx, does not fit in RAM): either side of the road, which is excluded
    # anyway, and each half cut again along a line traced through the gap between its feature clusters
    ("WN", "Watershed hills north-west of the road, west", "landslide", 5, P, tzw_zone("N", "W"), 0,
     "Zone split into connected scars and scoured channels."),
    ("WM", "Watershed hills north-west of the road, east", "landslide", 5, P, tzw_zone("N", "E"), 0,
     "Zone split into connected scars and scoured channels."),
    ("WE", "Watershed hills south-east of the road, east ridge", "landslide", 5, P, tzw_zone("S", "N"), 0,
     "Zone split into connected scars and scoured channels."),
    ("WV", "Watershed hills south-east of the road, the two valleys", "landslide", 5, P, tzw_zone("S", "S"), 0,
     "Zone split into connected scars and scoured channels."),
    ("WX-1", "Road up the valley", "exclude", 0, L, TZW_ROAD, 4,
     "The road from Ti Zit up the valley and over the hills and its cut banks, bare on 10 Jan 2026 (debris has since run "
     "down it)."),
    ("WX-2", "Road south of the village", "exclude", 0, L, TZW_SOUTH_ROAD, 4, "A village road, bare on 10 Jan 2026."),
    ("WX-3", "Concrete road on the hills", "exclude", 0, F, "road_traced.geojson", 0,
     "The new concrete road over the hills, traced on the ortho (its OpenStreetMap line is 10-20 m off here): bare on 10 Jan 2026 as a track."),
    ("WX-4", "Yard and houses", "exclude", 0, P, box_ll(98.09722, 13.90623, 98.0986, 13.90711), 0,
     "Rejected on chip review: houses and yards at the edge of the village."),
    ("WX-5", "Houses", "exclude", 0, P, box_ll(98.09434, 13.90923, 98.09507, 13.91018), 0,
     "Rejected on chip review: houses and yards in the village."),
    ("WX-6", "Yards", "exclude", 0, P, box_ll(98.09758, 13.91099, 98.09787, 13.91129), 0,
     "Rejected on chip review: yards in the village."),
    ("WX-7", "Sandy clearing", "exclude", 0, P, box_ll(98.09997, 13.90888, 98.10024, 13.90919), 0,
     "Rejected on chip review: a clearing already bare on 10 Jan 2026."),
    ("WX-8", "Plantation plot", "exclude", 0, P, box_ll(98.10184, 13.90838, 98.10363, 13.90985), 0,
     "Rejected on chip review: plantation plots and rows, cleared before 10 Jan 2026."),
    ("WX-9", "Dark patches", "exclude", 0, P, box_ll(98.10157, 13.90633, 98.10203, 13.90669), 0,
     "Rejected on chip review: dark ground and rock, as on 10 Jan 2026."),
    ("WX-10", "Dark patches", "exclude", 0, P, box_ll(98.10483, 13.9111, 98.10554, 13.91194), 0,
     "Rejected on chip review: dark burnt or rocky ground, as on 10 Jan 2026."),
    ("WX-11", "Scattered patches", "exclude", 0, P, box_ll(98.1053, 13.91718, 98.10636, 13.91771), 0,
     "Rejected on chip review: scattered patches in scrub."),
    ("WX-12", "Dark rock", "exclude", 0, P, box_ll(98.11389, 13.91659, 98.1143, 13.91709), 0,
     "Rejected on chip review: dark rock slabs, already bare on 10 Jan 2026."),
    ("WX-13", "Road shoulder", "exclude", 0, P, box_ll(98.11203, 13.91964, 98.11297, 13.92008), 0,
     "Rejected on chip review: the road shoulder and patches beside it."),
    ("WX-14", "Dark patches", "exclude", 0, P, box_ll(98.11401, 13.91736, 98.11426, 13.91769), 0,
     "Rejected on chip review: dark ground, as on 10 Jan 2026."),
    ("WX-15", "Dark patches", "exclude", 0, P, box_ll(98.11187, 13.91751, 98.11219, 13.9178), 0,
     "Rejected on chip review: dark ground, as on 10 Jan 2026."),
    ("WX-16", "Dark patches", "exclude", 0, P, box_ll(98.11112, 13.91272, 98.11135, 13.91302), 0,
     "Rejected on chip review: dark rock, as on 10 Jan 2026."),
    ("WX-17", "Scrub patches", "exclude", 0, P, box_ll(98.10876, 13.91424, 98.10915, 13.91454), 0,
     "Rejected on chip review: scattered patches in scrub."),
    ("WX-18", "Burnt grass", "exclude", 0, P, box_ll(98.10572, 13.92075, 98.10619, 13.92121), 0,
     "Rejected on chip review: dark burnt grass, as on 10 Jan 2026."),
    ("WX-19", "Burnt grass", "exclude", 0, P, box_ll(98.1092, 13.92071, 98.10958, 13.92119), 0,
     "Rejected on chip review: dark burnt grass, as on 10 Jan 2026."),
    ("WX-20", "Plantation rows", "exclude", 0, P, box_ll(98.10329, 13.91845, 98.10351, 13.91893), 0,
     "Rejected on chip review: plantation rows."),
]


def build(site):
    rows = []
    for i, name, kind, prio, typ, coords, hw, desc in ENV[site]:
        split = kind == "landslide" and "-" not in i  # a bare prefix marks a zone
        if typ == F:  # a polygon traced on the ortho and kept as a file beside the envelopes
            g = gpd.read_file(d(site, "inventory", coords)).to_crs(32647).union_all()
        else:
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
