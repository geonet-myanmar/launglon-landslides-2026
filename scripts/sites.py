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
}


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
