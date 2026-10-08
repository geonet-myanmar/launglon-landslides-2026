"""Model rainfall at the two new sites for context (Open-Meteo best-match model, NOT gauge data), as at Taw Kye.

Ka Det Nge Htein and Ngone Min Taung are 1.2 km apart, so one point between them is fetched; Tha Byar, 13 km
north, and the road to Pa Nyit, 5 km west of Tha Byar, have their own. Cached with the fetch time: forecast-hour values are later replaced by analysis values, so a
re-fetch will not match exactly - an existing cache is kept (delete it to re-fetch).
usage: python 09_rainfall.py [kadet|tby|pny|pgz|rbe]
"""
import datetime as dt, json, sys, urllib.parse, urllib.request
from sites import ROOT

POINTS = {"kadet": (13.8920, 98.1330, "2026-10-03"),  # between Ka Det Nge Htein and Ngone Min Taung
          "tby": (14.0090, 98.1250, "2026-10-05"),    # Tha Byar, head of the debris fan
          "pny": (13.9945, 98.0855, "2026-10-05"),    # road to Pa Nyit, the scoured stream
          "pgz": (13.7060, 98.1640, "2026-10-07"),    # Pyin Gyi - Za Lut, the road debris flow
          "rbe": (13.7090, 98.1500, "2026-10-08")}    # Ra Be - Kyauk Twin road


def get(params):
    with urllib.request.urlopen("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.loads(r.read())


def main(key):
    LAT, LON, end = POINTS[key]
    OUT = ROOT / f"data/source/rainfall_openmeteo_{key}.json"
    if OUT.exists():
        print("have", OUT.name); return
    base = {"latitude": LAT, "longitude": LON, "timezone": "Asia/Yangon"}
    d = get({**base, "daily": "precipitation_sum", "start_date": "2026-09-01", "end_date": end})
    h = get({**base, "hourly": "precipitation", "start_date": "2026-09-24", "end_date": "2026-09-29"})
    out = {"source": "Open-Meteo forecast API, best-match model (not gauge data)",
           "fetched_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
           "lat": LAT, "lon": LON, "grid_lat": d["latitude"], "grid_lon": d["longitude"],
           "daily": dict(zip(d["daily"]["time"], d["daily"]["precipitation_sum"])),
           "hourly": dict(zip(h["hourly"]["time"], h["hourly"]["precipitation"]))}
    OUT.write_text(json.dumps(out, indent=1))
    for k, v in out["daily"].items():
        if "2026-09-22" <= k:
            print(k, v)
    print("grid", out["grid_lat"], out["grid_lon"], "Sep total", round(sum(v or 0 for k, v in out["daily"].items() if k < "2026-10-01"), 1))


if __name__ == "__main__":
    for k in (sys.argv[1:] or list(POINTS)):
        main(k)
