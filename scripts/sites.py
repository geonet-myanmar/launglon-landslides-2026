"""Per-site configuration shared by every step. Two new drone surveys are processed here;
Taw Kye (26 Sep 2026) was processed by the tawkye-landslide-2026 pipeline and its products
are imported by step 11."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent  # the KMZ deliveries sit beside the project folder

SITES = {
    "nmt": {
        "name": "Ngone Min Taung", "kmz": "NgoneMinTaung_Ortho.kmz", "flown": "2026-10-04",
        # vegetation threshold = valley of the bimodal excess-green histogram (overcast flight, low saturation)
        "exg": 0.015,
    },
    "kdnh": {
        "name": "Ka Det Nge Htein", "kmz": "KadetNgelHtein_Ortho.kmz", "flown": "2026-10-03",
        "exg": 0.06,
        "mimu_pcode": "177156",
    },
    # two flights merged into one ortho by 01b_merge_flights.py; its own Earth Engine area (data/ee_tby/)
    "tby": {"name": "Tha Byar", "kmz": "TharByar_Plan_1.kmz + TharByar_Plan_2.kmz", "flown": "2026-10-05",
            "exg": 0.027, "ee": "ee_tby", "mimu_pcode": "177126",
            "outwash_minus_buildings": True, "core_filter": True},  # outwash spreads through the village: roofs are not sediment
    # road to Pa Nyit, 5 Oct 2026, one flight; own Earth Engine area (data/ee_pny/)
    "pny": {"name": "Pa Nyit road", "kmz": "PaNyit_Road.kmz", "flown": "2026-10-05", "exg": 0.027, "ee": "ee_pny"},
    # Ka Det Gyi, Nyaungdon and Wet Thar Kin, 6 Oct 2026: two flights merged by 01b_merge_flights.py (MERGES); own EE area
    "kdg": {"name": "Ka Det Gyi", "kmz": "KadetGyi_WetTharKin_Plan-1.kmz + KadetGyi_ChaeTawYar_Plan-2.kmz",
            "flown": "2026-10-06", "exg": 0.034, "ee": "ee_kdg",
            "minus_sites": ["kdnh"], "outwash_minus_buildings": True,
            # the automatic roof-grey fit (+4.75 m E) is pulled by bare grey yards and moves compound footprints off
            # their roofs; OSM footprints sit on the drone roofs unshifted (checked at 0.2-0.3 m/px), VIDA ones are
            # scattered 3-10 m west, so no shift is applied and every footprint near sediment or a slide is checked
            "footprint_shift": (0.0, 0.0)},  # 4.3 ha overlap with the Ka Det Nge Htein survey stays with Ka Det Nge Htein
    # Pyin Gyi and Za Lut, 7 Oct 2026: two flights merged by 01b_merge_flights.py (MERGES); own EE area
    "pgz": {"name": "Pyin Gyi - Za Lut", "kmz": "PyinGyi_Plan_1.kmz + PyinGyi_Plan_2.kmz", "flown": "2026-10-07",
            "exg": 0.034, "ee": "ee_pgz", "outwash_minus_buildings": True},
    # Ra Be, on the Ra Be - Kyauk Twin road, 8 Oct 2026: two flights merged by 01b_merge_flights.py (MERGES)
    "rbe": {"name": "Ra Be", "kmz": "Yabae_KyaukTwin_RD_1.kmz + Yabae_KyaukTwin_RD_2.kmz", "flown": "2026-10-08",
            "exg": 0.041, "ee": "ee_rbe",
            "minus_sites": ["pgz"]},  # 55 ha shared with the Pyin Gyi - Za Lut survey stays with that site
    # Taw Kye, Tha Win and Lel Hla, 8 Oct 2026: one KMZ, four flights already mosaicked by the provider, in two
    # separate blocks -> two sites cut from it by `bbox` in step 01; one Earth Engine area (data/ee_thw/)
    "thw": {"name": "Tha Win", "kmz": "Thakyattaw_Yabel_4Plan_Combine.kmz", "bbox": (98.14, 13.7707, 98.17, 13.812),
            "flown": "2026-10-08", "exg": 0.045, "ee": "ee_thw", "outwash_minus_buildings": True,
            "minus_sites": ["tawkye"]},  # the 2 Oct Taw Kye survey (finer, 3.75 / 5.68 cm) keeps the ground it covers
    "lhl": {"name": "Lel Hla", "kmz": "Thakyattaw_Yabel_4Plan_Combine.kmz", "bbox": (98.14, 13.755, 98.17, 13.7707),
            "flown": "2026-10-08", "exg": 0.045, "ee": "ee_thw"},
    # Ti Zit, 9 Oct 2026: two flights that meet without overlapping, joined by 01b_merge_flights.py (MERGES); own EE area
    "tzt": {"name": "Ti Zit", "kmz": "Tizit_Plan_1.kmz + Tizit_Plan_2&3.kmz", "flown": "2026-10-09", "exg": 0.048,
            "ee": "ee_tzt", "outwash_minus_buildings": True},
    # Ti Zit watershed, 10 Oct 2026: one delivery (several flights mosaicked by the provider), 8.5 cm; it overlaps the
    # 9 Oct Ti Zit flights, which keep the ground they cover; own Earth Engine area (data/ee_tzw/)
    "tzw": {"name": "Ti Zit watershed", "kmz": "Ti_zit_Watershed_combine.kmz", "bbox": (98.090, 13.900, 98.124, 13.931),
            "flown": "2026-10-10", "exg": 0.04,
            "ee": "ee_tzw", "outwash_minus_buildings": True, "minus_sites": ["tzt"]},
    # 11 Oct 2026, three deliveries. Ti Zit village: the village centre, in the gap between the 9 Oct flights; the ground
    # those flights and the 10 Oct watershed survey already cover stays with them
    "tzv": {"name": "Ti Zit village", "kmz": "Ti_zit_village.kmz", "flown": "2026-10-11", "exg": 0.045, "ee": "ee_1011",
            "outwash_minus_buildings": True, "minus_sites": ["tzt", "tzw"]},
    "snh": {"name": "San Hlan", "kmz": "SannLan_Village.kmz", "flown": "2026-10-11", "exg": 0.05, "ee": "ee_1011",
            "outwash_minus_buildings": True},
    "ykt": {"name": "Yan Kin Taung", "kmz": "YanKinTaung.kmz", "bbox": (98.110, 13.885, 98.131, 13.912),
            "flown": "2026-10-11", "exg": 0.048, "footprint_shift": (0.0, 0.0), "ee": "ee_1011",  # one footprint: no fit
            "outwash_minus_buildings": True, "minus_sites": ["nmt", "kdnh", "tzw"]},
    # 13 Oct 2026, five deliveries in four places. Launglon Town: two flights merged by 01b_merge_flights.py (MERGES)
    "lgt": {"name": "Launglon Town", "kmz": "LaungLone_Plan_1.kmz + LaungLone_Plan_2.kmz", "flown": "2026-10-13", "exg": 0.045,
            "ee": "ee_1013n", "outwash_minus_buildings": True, "minus_sites": ["tby"]},
    "knr": {"name": "Kan Pa Ni - Pa Nyit road", "kmz": "Kanpani_Panyit_RD.kmz", "flown": "2026-10-13", "exg": 0.045, "ee": "ee_1013n",
            "outwash_minus_buildings": True},
    "khg": {"name": "Kayin Gyi", "kmz": "Kayingyi_combine.kmz", "flown": "2026-10-13", "exg": 0.045, "ee": "ee_1013n",
            "outwash_minus_buildings": True},
    "cpg": {"name": "Chaung Hpyar Gyi", "kmz": "ChaungPhyarGyi_Village.kmz", "flown": "2026-10-13", "exg": 0.04,
            "ee": "ee_1013s", "outwash_minus_buildings": True},
    "ktr": {"name": "Kyauk Twin road", "kmz": "Kyauktwin_RD.kmz", "flown": "2026-10-13", "exg": 0.04, "ee": "ee_1013s",
            "outwash_minus_buildings": True, "minus_sites": ["rbe", "pgz"]},
}
# KMZ deliveries that are mosaicked by step 01 but are not sites of their own
FLIGHTS = {
    "tb1": {"kmz": "TharByar_Plan_1.kmz"},  # village and western slopes, 9.5 cm
    "tb2": {"kmz": "TharByar_Plan_2.kmz"},  # northern hills, 9.0 cm
    "kg1": {"kmz": "KadetGyi_WetTharKin_Plan-1.kmz"},  # 8.0 cm
    "kg2": {"kmz": "KadetGyi_ChaeTawYar_Plan-2.kmz"},  # 8.0 cm
    "pg1": {"kmz": "PyinGyi_Plan_1.kmz"},  # 10.4 cm
    "pg2": {"kmz": "PyinGyi_Plan_2.kmz"},  # 9.7 cm
    "rb1": {"kmz": "Yabae_KyaukTwin_RD_1.kmz"},  # 9.2 cm
    "rb2": {"kmz": "Yabae_KyaukTwin_RD_2.kmz"},  # 9.2 cm
    "tz1": {"kmz": "Tizit_Plan_1.kmz"},  # Ti Zit village and the hills around it, 11.1 cm
    "tz2": {"kmz": "Tizit_Plan_2&3.kmz"},  # the hills to the south-east, 10.0 cm (two flights mosaicked by the provider)
    "lg1": {"kmz": "LaungLone_Plan_1.kmz"},  # Launglon Town, south, 11.3 cm
    "lg2": {"kmz": "LaungLone_Plan_2.kmz"},  # Launglon Town, north, 11.0 cm
}
MERGES = {"tby": ("tb1", "tb2"), "kdg": ("kg1", "kg2"), "pgz": ("pg1", "pg2"), "rbe": ("rb1", "rb2"), "tzt": ("tz1", "tz2"), "lgt": ("lg1", "lg2")}  # site: (flight 1, flight 2), merged by 01b_merge_flights.py
# metres to move flight 1 onto flight 2 before merging (phase correlation in the overlap; omitted = no shift)
MERGE_SHIFT = {"kdg": (1.32, 0.36), "pgz": (0.16, -2.2), "rbe": (-4.9, 1.04),
               "lgt": (1.0, -0.1)}  # Launglon Town: a gradient, 0 m E in the east to 2 m in the west - the middle value


def ee_dir(site):
    """Earth Engine / OSM inputs for a site: data/ee (south area) or the site's own area."""
    return ROOT / "data" / SITES.get(site, {}).get("ee", "ee")


def d(site, *parts):
    p = ROOT / "data" / site
    for x in parts:
        p = p / x
    return p


# Feature names and types. type: open (open-slope slide or flow), channel (scoured channel or gully),
# minor (scar or channel fragment < 1,000 m2, mapped but not described). Ka Det Nge Htein names come
# from its envelopes. Ngone Min Taung features are numbered by area by the split zone, so each name
# carries the point it was given for, and step 06 checks the feature is still there.
TYPES = {
    "thw": {"TW-01": "channel"},
    "lhl": {"LL-01": "channel"},
    "rbe": {"RB-01": "open"},
    "pgz": {"PG-01": "open", "PG-03": "channel", "PG-04": "channel", "PG-05": "channel"},
    "pny": {"PN-01": "channel", "PN-02": "open", "PN-03": "open", "PN-04": "open", "PN-05": "channel", "PN-06": "channel", "PN-07": "open"},
    "tby": {"TB-01": "channel", "TB-02": "channel", "TB-03": "open", "TB-04": "open", "TB-05": "channel"},
    "kdnh": {"KD-01": "channel", "KD-02": "open", "KD-03": "open", "KD-04": "open", "KD-05": "open",
             "KD-06": "channel", "KD-07": "open", "KD-08": "channel", "KD-09": "channel"},
}
NMT_NAMES = {  # id: (name, type, representative lon, lat, description)
    "NM-01": ("West river channel", "channel", 98.12602, 13.89597,
              "The largest scoured channel: a stream bed stripped to sand and boulders from the south-west hills to the "
              "north edge of the survey, with its south-east tributary."),
    "NM-02": ("North-west channels", "channel", 98.12281, 13.90110,
              "Tributary channels in young plantation west of the monastery, scoured and buried in sand."),
    "NM-03": ("Central channel", "channel", 98.12792, 13.89662,
              "A forested stream scoured from the foot of the southern hill north to the monastery road."),
    "NM-04": ("South channel network", "channel", 98.13097, 13.89587,
              "The east-west stream at the foot of the southern hill and the branch that comes down to it from the south."),
    "NM-05": ("Road slide", "open", 98.13130, 13.90069,
              "The largest open-slope failure: a stepped scar in red soil below the pagoda hill whose debris reached the road."),
    "NM-06": ("South edge scar", "open", 98.13445, 13.89503,
              "Open-slope scar at the southern edge of the survey; its upper part lies beyond the flight."),
    "NM-07": ("Plantation flow", "open", 98.12924, 13.90070,
              "Debris flow through a plantation down to the road east of the monastery."),
    "NM-08": ("Curving slide", "open", 98.13247, 13.89990,
              "Slide east of the pagoda whose debris curved north-east around a grass field."),
    "NM-09": ("West branch channel", "channel", 98.12330, 13.89901, "Scoured side channel joining the west river channel."),
    "NM-10": ("South-west gully", "channel", 98.12398, 13.89614, "Gully scoured down the south-west hillside."),
    "NM-11": ("North edge channel", "channel", 98.12807, 13.90414, "Channel scour at the northern edge of the survey."),
    "NM-12": ("East gully", "channel", 98.13629, 13.89646, "Gully scour at the east end of the south channel network."),
}
TBY_NAMES = {  # Tha Byar split zone TC (ridge west of the main valley)
    "TC-01": ("North-spur channel network", "channel", 98.11795, 14.01037,
              "Branching channels scoured down the north side of the spur west of the valley, draining east along a "
              "gully that joins the main valley flow."),
    "TC-02": ("West-edge channel", "channel", 98.11674, 14.00569,
              "A channel scoured down the west edge of the survey that spread sand among the trees where the spur's "
              "southern channels meet, above the southern debris flow."),
    "TC-03": ("Ridge gullies", "channel", 98.11330, 14.01375,
              "Gullies scoured down the east face of the ridge beside the long slide."),
    "TC-04": ("Twin channels", "channel", 98.11774, 14.00738, "Two parallel channels scoured down the west flank of the spur."),
    "TC-05": ("Spur slide", "open", 98.11958, 14.00590, "Open-slope failure on the south flank of the spur."),
    "TC-06": ("Spur chute", "open", 98.11892, 14.00670, "Narrow debris chute on the south flank of the spur."),
    "TC-07": ("North-west edge channel", "channel", 98.11244, 14.01615, "Channel scoured at the north-west edge of the survey."),
    "TC-08": ("West-edge gully", "channel", 98.11655, 14.00980, "Gully scoured at the west edge of the survey."),
    "TC-09": ("South-west channel", "channel", 98.11700, 14.00381, "Scoured channel near the south-west edge of the survey."),
    "TC-10": ("Scar beside the long slide", "open", 98.11702, 14.01325, "Small open-slope scar beside the toe of the long slide."),
}
KDG_NAMES = {  # Ka Det Gyi split zones KGN (hills south of Wet Thar Kin) and KGS (hills west of Ka Det Gyi and Nyaungdon)
    "KGN-01": ("Wet Thar Kin debris flow", "open", 98.13925, 13.87742,
               "The largest failure: a hook-shaped scar on the hill south of Wet Thar Kin whose debris turned north and "
               "ran down to the clearing beside the village road, with a scoured channel below it to the west."),
    "KGN-02": ("East gullies", "channel", 98.14479, 13.87830, "Two parallel gullies scoured down the north face of the hills."),
    "KGN-03": ("North-running gully", "channel", 98.14350, 13.87870, "A gully scoured north down the hillside towards the fields."),
    "KGS-01": ("Chutes above the compound", "open", 98.14549, 13.87485,
               "Five chutes on the hill west of Ka Det Gyi that converged on the track and ran south to the compound "
               "in the valley; one slid off the slope below the track."),
    "KGS-02": ("South-tip channels", "channel", 98.14463, 13.86804,
               "Branching channels scoured down the south end of the ridge to the edge of the survey."),
    "KGS-03": ("South-tip chute", "channel", 98.14350, 13.86716,
               "A long chute and its twin scoured down the western side of the south end of the ridge."),
    "KGS-04": ("Slide across the hill track", "open", 98.14900, 13.87361,
               "A wide slide in plantation west of Nyaungdon whose debris crossed the hill track."),
    "KGS-05": ("West chute", "open", 98.14084, 13.87649, "A long narrow chute down the west face of the hills."),
    "KGS-06": ("Plantation slide", "open", 98.14786, 13.87244, "A slide through young plantation on the east face of the hill."),
    "KGS-07": ("Hillside channel", "channel", 98.14452, 13.87093, "A narrow channel scoured down the west face of the ridge."),
    "KGS-08": ("Twin scars", "open", 98.14762, 13.87133, "Two small scars on the east face of the hill."),
    "KGS-09": ("Upper gully", "channel", 98.14268, 13.87663, "A gully on the north side of the hills."),
    "KGS-10": ("Small slide", "open", 98.14815, 13.87171, "A small slide on the east face of the hill."),
}
PGZ_NAMES = {  # Pyin Gyi - Za Lut split zone PGZ (hills west of the road)
    "PGZ-01": ("Long chute", "open", 98.15886, 13.70827,
               "A 400 m chute scoured east down the hillside towards the road debris flow."),
    "PGZ-02": ("North chute", "open", 98.15887, 13.71010, "A long chute on the hillside north of the long chute."),
}
RBE_NAMES = {  # Ra Be split zone RZ (hillside on both sides of the Ra Be - Kyauk Twin road)
    "RZ-01": ("South-central channel network", "channel", 98.15381, 13.70496,
              "A network of scoured channels and one wide flow east of the road that converge south-east towards the "
              "edge of the survey; it continues beyond the flight."),
    "RZ-02": ("West slide", "open", 98.14442, 13.70947,
              "The largest single slide: a 4.5 ha scar on the west hill, stripped to orange and grey soil, with a channel below it."),
    "RZ-03": ("Road-corridor network", "channel", 98.14784, 13.71043,
              "Side slides and channels west of the road that ran down onto it, and the deposits they left along it."),
    "RZ-04": ("East channel network", "channel", 98.15460, 13.70565, "Branching channels scoured down the slopes east of the road."),
    "RZ-05": ("Twin slides below RB-01", "open", 98.14725, 13.71155, "Two slides just south of RB-01 whose debris ran east."),
    "RZ-06": ("North gully", "channel", 98.14753, 13.71454, "A 400 m gully scoured east down to the road in the north."),
    "RZ-07": ("West chute", "open", 98.14481, 13.70597, "A long narrow chute on the west hill."),
    "RZ-08": ("Slide west of the road", "open", 98.14765, 13.70510, "A slide whose debris ran east onto the road."),
    "RZ-09": ("Slide above the road", "open", 98.14781, 13.70396, "A slide on the slope above the road."),
    "RZ-10": ("Slide at the road bend", "open", 98.14758, 13.70289, "A slide just above the bend where the road turns west."),
    "RZ-11": ("East gully", "channel", 98.15435, 13.70684, "A gully on the east slopes."),
    "RZ-12": ("Small slide", "open", 98.15212, 13.70301, "A small slide near the southern edge."),
    "RZ-13": ("Side slide", "open", 98.14778, 13.70748, "A small slide west of the road."),
}
THW_NAMES = {  # Tha Win split zone TZ (hills west of the road from Tha Win north past Taw Kye)
    "TZ-01": ("Western valley channel network", "channel", 98.14986, 13.80415,
              "The western branch of the northern valley: a channel scoured from the west edge of the survey to where it "
              "joins TW-01, with the slides and gullies that fed it from both sides."),
    "TZ-02": ("Channel network behind Tha Win", "channel", 98.15326, 13.78091,
              "Channels scoured east from the hills that meet behind Tha Win, and the wide slide that came down to them "
              "from the north; their sand spread through the west of the village (TW-OW2)."),
    "TZ-03": ("Channel network south of Taw Kye", "channel", 98.15087, 13.78903,
              "Branching channels scoured east down the hills south of Taw Kye; they run into the 2 Oct Taw Kye survey, "
              "which maps their lower reaches."),
    "TZ-04": ("South-western flow", "channel", 98.15352, 13.77524,
              "A wide debris flow down a valley from the south-west edge of the survey that turned north and reached the "
              "south-west corner of Tha Win."),
    "TZ-05": ("Channel network west of Taw Kye", "channel", 98.14903, 13.79839,
              "Channels scoured down the hills west of Taw Kye, feeding the southern branch of the northern valley."),
    "TZ-06": ("Twin slides above the valley flow", "open", 98.15325, 13.80681,
              "Two slides on the north side of the valley that merged and ran south into TW-01."),
    "TZ-07": ("Slides north of the valley mouth", "open", 98.15594, 13.80724,
              "Slides on the hill north of the valley mouth whose debris ran south-east towards the road."),
    "TZ-08": ("Slides above the road in the north", "open", 98.15732, 13.80878,
              "Slides on the hill west of the road at the north edge of the survey."),
    "TZ-09": ("Head channels of the valley flow", "channel", 98.14862, 13.80803,
              "Channels scoured down the hills at the head of the northern valley, joining TW-01 below its scar."),
    "TZ-10": ("Long chute into the Taw Kye survey", "open", 98.15524, 13.78891,
              "A long straight chute east down the hill south of Taw Kye; its toe is in the 2 Oct Taw Kye survey."),
    "TZ-11": ("Slide west of Taw Kye", "open", 98.15035, 13.79752, "A slide on the hills west of Taw Kye."),
    "TZ-12": ("Western chute", "open", 98.14856, 13.78593, "A chute on the western hills."),
    "TZ-13": ("Channel to north Tha Win", "channel", 98.15437, 13.78222,
              "A channel scoured east to the gardens at the north end of Tha Win (TW-OW3)."),
    "TZ-14": ("Chute above Tha Win", "open", 98.15137, 13.78177, "A chute on the hills north-west of Tha Win."),
    "TZ-15": ("Twin gullies", "channel", 98.15086, 13.79185, "Two gullies on the hills south-west of Taw Kye."),
    "TZ-16": ("Slide at the Taw Kye survey edge", "open", 98.15663, 13.78958, "A slide just outside the 2 Oct Taw Kye survey."),
    "TZ-17": ("Slide west of the gap", "open", 98.15449, 13.79686, "A slide west of the gap in the 8 Oct imagery."),
    "TZ-18": ("West-edge chute", "open", 98.14657, 13.80307, "A chute at the west edge of the survey."),
    "TZ-19": ("South-edge gully", "channel", 98.15267, 13.77272, "A gully at the southern edge of the block."),
    "TZ-20": ("Side channel", "channel", 98.15130, 13.77976, "A side channel scoured on the valley floor behind Tha Win."),
    "TZ-21": ("North channel", "channel", 98.15114, 13.80828, "A narrow channel north of the valley flow's scar."),
    "TZ-22": ("North-edge scar", "open", 98.15331, 13.80901, "A scar at the north edge of the survey."),
    "TZ-23": ("Small slide", "open", 98.15408, 13.78925, "A small slide south of Taw Kye."),
    "TZ-24": ("Side slide", "open", 98.15384, 13.79284, "A small slide west of the Taw Kye survey."),
}
LHL_NAMES = {  # Lel Hla split zone LZ (hills west of Lel Hla)
    "LZ-01": ("Long gully", "channel", 98.15011, 13.76077, "A gully scoured south-east down the hills south of LL-01."),
    "LZ-02": ("Slide and chute", "open", 98.14772, 13.76176, "A slide on the southern hills and the chute below it."),
    "LZ-03": ("North chute", "open", 98.15332, 13.76731, "A long narrow chute on the hill north of LL-01."),
    "LZ-04": ("North-edge slide", "open", 98.15191, 13.76807, "A slide at the north edge of the block."),
}
TZT_NAMES = {  # Ti Zit split zones TN (hills east and north of the tidal flat) and TS (coastal hills to the south-east)
    "TN-01": ("North channel", "channel", 98.08255, 13.91797,
              "A channel scoured from the northern hills down through plantation to the track west of the flat."),
    "TN-02": ("Eastern slide", "open", 98.09178, 13.91595,
              "A long slide on the hill east of the flat whose debris ran south-west into the fan at its foot (TZ-OW1)."),
    "TN-03": ("Twin slide", "open", 98.08988, 13.91608, "A wide slide beside TN-02 that fed the same fan."),
    "TN-04": ("Plantation slide", "open", 98.08669, 13.91575, "A slide through young plantation above the track."),
    "TN-05": ("West slide", "open", 98.07998, 13.91633, "A narrow slide in the west of the block."),
    "TS-01": ("Southern channel network", "channel", 98.09641, 13.88508,
              "The largest feature: a network of channels scoured west through the forest that reaches the sea at the "
              "south end of the beach, with the slides that fed it."),
    "TS-02": ("East-central channel network", "channel", 98.10616, 13.88783,
              "Branching channels scoured down the eastern hills that join TS-01."),
    "TS-03": ("North-east channel network", "channel", 98.10545, 13.89904,
              "Branching channels scoured down the hills in the north-east of the block, draining west towards the beach."),
    "TS-04": ("Central valley flow", "channel", 98.10233, 13.89299,
              "A wide debris flow down a forested valley from scars on both sides, running north-west towards the beach."),
    "TS-05": ("Coastal channel network", "channel", 98.09406, 13.88045,
              "Channels scoured down to the small southern beach, where their debris reached the sea."),
    "TS-06": ("Slide to the beach", "open", 98.09958, 13.89049,
              "A wide slide whose debris ran west down to the back of the beach."),
    "TS-07": ("South-edge channel", "channel", 98.09626, 13.87456,
              "A channel scoured west to the sea along the southern edge of the survey."),
    "TS-08": ("Long slide", "open", 98.09743, 13.87969, "A long straight slide down the coastal hill."),
    "TS-09": ("South-east gully", "channel", 98.10319, 13.87528, "A gully at the eastern edge of the flight."),
    "TS-10": ("Plantation slide", "open", 98.09919, 13.88124, "A slide through plantation on the coastal hill."),
    "TS-11": ("Hillside channel", "channel", 98.10280, 13.89576, "A channel scoured west on the hills north of TS-04."),
    "TS-12": ("Twin slides", "open", 98.10238, 13.87611, "Two parallel slides in the south of the block."),
    "TS-13": ("East-edge gully", "channel", 98.10487, 13.87623, "A gully at the eastern edge of the flight."),
    "TS-14": ("Small slide", "open", 98.10199, 13.88600, "A small slide beside TS-01."),
    "TS-15": ("East-edge slide", "open", 98.10758, 13.89594, "A slide at the eastern edge of the flight."),
    "TS-16": ("Twin scars", "open", 98.09941, 13.88920, "Two scars beside TS-06."),
}
TZW_NAMES = {  # Ti Zit watershed split zones WN, WM (north-west of the road), WE (east ridge), WV (the two valleys)
    "WN-01": ("Western channel network", "channel", 98.09909, 13.92061,
              "The largest feature: a network of channels scoured south-west down the western half of the basin, joining "
              "the valley that the road follows down into Ti Zit."),
    "WN-02": ("West-edge slide", "open", 98.09277, 13.91739, "A wide slide at the western edge of the survey."),
    "WN-03": ("North-edge channel", "channel", 98.09935, 13.92627, "A channel at the northern edge of the survey."),
    "WM-01": ("Great slide above the road", "open", 98.11070, 13.92191,
              "A 10 ha slope failure on the hill north of the road over the ridge: a wide scar stripped to orange soil, "
              "whose debris ran south over the road."),
    "WM-02": ("Slide at the road hairpin", "open", 98.10657, 13.91974,
              "A slide that came down across the hairpin bend where the road climbs out of the valley."),
    "WE-01": ("East-ridge slide complex", "open", 98.11739, 13.91837,
              "Wide scars side by side on the west face of the eastern ridge, merging below into the head of the east "
              "valley; 18 ha."),
    "WE-02": ("Ridge gully network", "channel", 98.11007, 13.91744, "Gullies scoured south down the ridge below the road."),
    "WE-03": ("Slide below the road", "open", 98.10485, 13.91778, "A slide down from the road into the valley head."),
    "WE-04": ("Slide below the road bend", "open", 98.10370, 13.91627, "A slide below the road where it bends."),
    "WE-05": ("East-edge slide", "open", 98.12130, 13.91606, "A slide at the eastern edge of the survey."),
    "WE-06": ("Ridge gully", "channel", 98.11492, 13.91622, "A gully on the east ridge."),
    "WE-07": ("Ridge chute", "channel", 98.11381, 13.91643, "A long narrow chute on the east ridge."),
    "WE-08": ("Slide beside the road", "open", 98.10574, 13.91831, "A slide below the road."),
    "WE-09": ("Small slide", "open", 98.10665, 13.91814, "A small slide below the road."),
    "WV-01": ("East valley flow", "channel", 98.10858, 13.91173,
              "A debris flow that scoured the east valley for 1.5 km, from the foot of the east ridge west to the road, "
              "and ran on down the road valley into the eastern part of Ti Zit (WS-OW1)."),
    "WV-02": ("South valley flow", "channel", 98.10603, 13.90670,
              "A debris flow down the south valley from a fan of scars at its head, which came out at the south-east corner "
              "of the village."),
    "WV-03": ("South-edge slide", "open", 98.10300, 13.90316, "A slide at the southern edge of the survey."),
    "WV-04": ("Valley-side slide", "open", 98.11568, 13.90982, "A long slide on the south side of the east valley."),
    "WV-05": ("East valley slide", "open", 98.11612, 13.91148, "A slide on the south side of the east valley."),
    "WV-06": ("South slide", "open", 98.10366, 13.90265, "A slide near the southern edge of the survey."),
    "WV-07": ("Twin south slide", "open", 98.10298, 13.90271, "A slide beside WV-06."),
    "WV-08": ("Valley-side chute", "open", 98.10245, 13.91124, "A chute on the north side of the lower east valley."),
    "WV-09": ("Valley-side chute", "open", 98.10281, 13.91073, "A chute on the north side of the lower east valley."),
}
TZV_NAMES = {  # Ti Zit village zone TV (the hillside at its eastern tip)
    "TV-01": ("Plantation slide", "open", 98.10180, 13.90249, "A slide through plantation on the low hill east of the village."),
    "TV-02": ("Twin chutes", "open", 98.10266, 13.90212, "Two chutes on the same hill, beside TV-01."),
    "TV-03": ("Edge slide", "open", 98.10575, 13.90173, "A slide at the eastern edge of the flight."),
}
SNH_NAMES = {  # San Hlan zones SN (hills north of the village) and SS (hills south-east)
    "SN-01": ("North chute", "open", 98.07953, 13.94673, "A narrow chute in the forest north of the creek valley."),
    "SS-01": ("Slide below the hill track", "open", 98.08248, 13.93765,
              "A slope failure in orange soil below the track on the hill south-east of the village."),
    "SS-02": ("Rocky channel", "channel", 98.08469, 13.93849, "A small channel scoured to grey rock."),
}
YKT_NAMES = {  # Yan Kin Taung zones YN, YM, YS (pieces cut by a zone boundary are merged in step 05)
    "YS-01": ("Western channel network", "channel", 98.11584, 13.90007,
              "The largest feature: branching channels scoured west and south-west across the middle and south of the "
              "hills, with the wide slides that fed them; 38 ha."),
    "YN-01": ("Northern channel network", "channel", 98.12020, 13.90713,
              "Parallel channels and slides scoured west down the northern hills."),
    "YM-01": ("Central flow", "channel", 98.12144, 13.90265, "A wide debris flow scoured west down the middle of the hills."),
    "YN-02": ("North-east flow", "channel", 98.12424, 13.90529,
              "A flow from the plantation at the east edge, with the slides at its head."),
    "YN-03": ("North channel", "channel", 98.12218, 13.90589, "A channel scoured west beside YN-01."),
    "YS-02": ("South-east slides", "open", 98.12748, 13.89466, "Wide scars side by side at the south-east edge of the flight."),
    "YN-04": ("North-west slide", "open", 98.11512, 13.90866, "A wide slide in the north-west of the hills."),
    "YN-05": ("North-edge flow", "channel", 98.11973, 13.90995, "A flow along the northern edge of the flight."),
    "YM-02": ("Central chute", "open", 98.12005, 13.90309, "A chute beside the central flow."),
    "YM-03": ("Western chute", "open", 98.11673, 13.89748, "A long chute in the west of the hills."),
    "YN-06": ("West-edge slide", "open", 98.11324, 13.90631, "A slide at the western edge of the flight."),
    "YN-07": ("East-edge chute", "open", 98.12517, 13.90875, "A chute at the eastern edge of the flight."),
    "YS-03": ("South chute", "open", 98.11625, 13.89570, "A chute in the south of the hills."),
    "YS-04": ("South gully", "channel", 98.11937, 13.89597, "A gully in the south of the hills."),
    "YN-08": ("Small slide", "open", 98.11404, 13.90867, "A small slide in the north-west."),
    "YM-04": ("Side chute", "open", 98.11764, 13.89815, "A chute on the west of the hills."),
    "YS-05": ("South-east slide", "open", 98.12557, 13.89338, "A slide in the south-east."),
}
LGT_NAMES = {  # Launglon Town zone LT (rubber-planted hills north and west of the town)
    "LT-01": ("North-west channel network", "channel", 98.11016, 13.98727,
              "The largest feature: slides on the hills north-west of the town that joined a channel scoured south-west "
              "through the plantation."),
    "LT-02": ("Slides on the north-west hill", "open", 98.10867, 13.99127, "Wide slides side by side in orange soil."),
    "LT-03": ("Slide above the town", "open", 98.11789, 13.98575, "A wide slide on the hill directly north of the town."),
    "LT-04": ("North-west edge slides", "open", 98.10749, 13.99248, "Slides at the north-west edge of the flight."),
    "LT-05": ("Northern channel", "channel", 98.11478, 13.99022, "A channel scoured west through the plantation."),
    "LT-06": ("Western creek scour", "channel", 98.10392, 13.97563, "The creek west of the town scoured and filled with sand."),
    "LT-07": ("Western creek, upper", "channel", 98.10754, 13.97829, "The creek scoured down from the north-west channels."),
    "LT-08": ("North-east slides", "open", 98.11915, 13.99273, "Parallel slides on the north-east hill."),
    "LT-09": ("Long chute", "open", 98.11551, 13.98472, "A long chute down the hill north of the town."),
    "LT-10": ("Chute beside it", "open", 98.11713, 13.98483, "A chute beside LT-09."),
    "LT-11": ("East slide", "open", 98.11909, 13.98751, "A slide on the eastern hill."),
    "LT-12": ("Slide above the houses", "open", 98.11379, 13.98406, "A slide whose toe is just above the northern houses."),
    "LT-13": ("Northern slide", "open", 98.11797, 13.99133, "A slide on the north-east hill."),
}
KHG_NAMES = {  # Kayin Gyi zones KN, KS (merged across their boundary)
    "KS-01": ("Main valley channel", "channel", 98.09649, 14.05646,
              "The stream scoured down the main valley from the south to the village, where its sediment spread between "
              "the houses (KG-OW1)."),
    "KS-02": ("South-east channel", "channel", 98.10047, 14.06275,
              "A channel scoured north-west from the south-east hills to join the main valley at the village."),
    "KS-03": ("Side channel", "channel", 98.10347, 14.05969, "A side channel joining KS-02."),
    "KS-04": ("Eastern channel", "channel", 98.10597, 14.06190, "A channel on the eastern hills."),
    "KS-05": ("Valley slide", "open", 98.10160, 14.05328, "A slide on the side of the south-east valley."),
    "KS-06": ("South slide", "open", 98.09641, 14.05057, "A slide near the south edge of the flight."),
    "KN-01": ("Slide east of the village", "open", 98.10332, 14.07324, "A slide on the hill east of the village."),
}
CPG_NAMES = {  # Chaung Hpyar Gyi zone CZ
    "CZ-01": ("Great slide and its channels", "channel", 98.10054, 13.75547,
              "A 20 ha slope failure in closed forest, with the channels it fed running south-east down the valleys."),
    "CZ-02": ("Eastern channel", "channel", 98.10843, 13.75223, "A channel scoured down the eastern valley."),
}
KTR_NAMES = {  # Kyauk Twin road zone KT
    "KT-01": ("Debris flow across the road", "channel", 98.14023, 13.70944,
              "A debris flow scoured west down a valley from slides at its head, which crossed the road and spread a fan "
              "towards the tidal creek."),
    "KT-02": ("North slides", "open", 98.13572, 13.71334, "Slides on the hill north of the road."),
}
KNR_NAMES = {  # Kan Pa Ni - Pa Nyit road zone KR
    "KR-01": ("Slide east of the road", "open", 98.07833, 14.02948, "A long slide down to the road from the east."),
    "KR-02": ("Slide at the road bend", "open", 98.07754, 14.02382, "A wide slide across the road at the southern bend."),
    "KR-03": ("Slides above the road", "open", 98.07407, 14.03144, "Slides on the slope above the road."),
    "KR-04": ("Gully below the road", "channel", 98.06926, 14.03527,
              "A gully scoured down below the road in the north, its bed broken by fallen trees."),
    "KR-05": ("Slide to the road", "open", 98.07831, 14.02717, "A slide that reached the road."),
    "KR-06": ("North-east slide", "open", 98.07219, 14.03722, "A slide near the north edge of the flight."),
}
SPLIT_NAMES = {"nmt": NMT_NAMES, "tby": TBY_NAMES, "kdg": KDG_NAMES, "pgz": PGZ_NAMES, "rbe": RBE_NAMES,
               "thw": THW_NAMES, "lhl": LHL_NAMES, "tzt": TZT_NAMES, "tzw": TZW_NAMES,
               "tzv": TZV_NAMES, "snh": SNH_NAMES, "ykt": YKT_NAMES,
               "lgt": LGT_NAMES, "khg": KHG_NAMES, "cpg": CPG_NAMES, "ktr": KTR_NAMES, "knr": KNR_NAMES}
# Landslides that enter the survey across its edge: the automatic crown (highest point on the outline) is then not
# the source, so H, L and the reach angle are minimums. Set by inspection where the 15 m edge test misses it.
EDGE_OVERRIDE = {"tby": {"TB-01": "crown", "TB-05": "crown"}, "pny": {"PN-06": "crown"}}
