"""Model rainfall at the two new sites for context (Open-Meteo best-match model, NOT gauge data), as at Taw Kye.

The sites are 1.2 km apart, so one point between them is fetched. Cached with the fetch time:
forecast-hour values are later replaced by analysis values, so a re-fetch will not match exactly.
"""
import datetime as dt, json, urllib.parse, urllib.request
from sites import ROOT

OUT = ROOT / "data/source/rainfall_openmeteo_kadet.json"
LAT, LON = 13.8920, 98.1330  # between Ka Det Nge Htein and Ngone Min Taung


def get(params):
    with urllib.request.urlopen("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.loads(r.read())


def main():
    base = {"latitude": LAT, "longitude": LON, "timezone": "Asia/Yangon"}
    d = get({**base, "daily": "precipitation_sum", "start_date": "2026-09-01", "end_date": "2026-10-03"})
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
    main()
