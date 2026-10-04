"""Earth Engine and OSM inputs for both new sites, each at its own native grid.

- Copernicus GLO-30 DEM, 2024_1 release (30 m, pre-event surface)
- VIDA combined Google+Microsoft building footprints (pre-event)
- OpenStreetMap buildings (Overpass)
- Sentinel-2 L2A pre-event NDVI and RGB, Jan-Apr 2026 median (10 m)
- list of Sentinel-2 scenes after 26 Sep 2026
One AOI covers both surveys (they sit ~1 km apart) plus a ~1.5 km margin for the hill crests,
matching the Taw Kye run so the runout model sees the whole catchments.
"""
import json, os, urllib.parse, urllib.request
import ee
from sites import ROOT

ee.Initialize(project=os.environ["EE_PROJECT"])
OUT = ROOT / "data/ee"
OUT.mkdir(parents=True, exist_ok=True)
W, S, E, N = 98.100, 13.860, 98.165, 13.922
AOI = ee.Geometry.Rectangle([W, S, E, N])


def download(img, name, scale, crs="EPSG:32647"):
    if (OUT / name).exists():
        print("have", name); return
    url = img.getDownloadURL({"region": AOI, "scale": scale, "crs": crs, "format": "GEO_TIFF"})
    urllib.request.urlretrieve(url, OUT / name)
    print("wrote", name)


def overpass(q):
    """Overpass mirrors in turn: the main instance 504s under load."""
    for host in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                 "https://maps.mail.ru/osm/tools/overpass/api/interpreter"):
        for _ in range(2):
            try:
                req = urllib.request.Request(host, data=urllib.parse.urlencode({"data": q}).encode(),
                                             headers={"User-Agent": "launglon-landslides/1.0"})
                return json.load(urllib.request.urlopen(req, timeout=180))
            except Exception as e:  # noqa: BLE001
                print("  overpass", host, e)
    raise RuntimeError("all Overpass mirrors failed")


dem = ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1").filterBounds(AOI).select("DEM").mosaic()
download(dem.toFloat(), "cop30_dem_utm.tif", 30)

bld = ee.FeatureCollection("projects/sat-io/open-datasets/VIDA_COMBINED/MMR").filterBounds(AOI)
if not (OUT / "vida_buildings.geojson").exists():
    gj = bld.getInfo()
    print("VIDA buildings:", len(gj["features"]))
    (OUT / "vida_buildings.geojson").write_text(json.dumps(gj))

q = (f'[out:json][timeout:120];(way["building"]({S},{W},{N},{E});'
     f'relation["building"]({S},{W},{N},{E}););out geom;')
osm = overpass(q)
feats = [{"type": "Feature", "properties": {"osm_id": e["id"], **e.get("tags", {})},
          "geometry": {"type": "Polygon", "coordinates": [[[p["lon"], p["lat"]] for p in e["geometry"]]]}}
         for e in osm["elements"] if e["type"] == "way" and len(e.get("geometry", [])) >= 4]
print("OSM buildings:", len(feats))
(OUT / "osm_buildings.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))

s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(AOI)
pre = s2.filterDate("2026-01-01", "2026-05-01").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
print("pre-event S2 scenes:", pre.size().getInfo())


def mask(i):
    scl = i.select("SCL")
    return i.updateMask(scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)))


download(pre.map(mask).map(lambda i: i.normalizedDifference(["B8", "B4"])).median().rename("ndvi").toFloat(),
         "s2_ndvi_pre_2026JanApr.tif", 10)
download(pre.map(mask).select(["B4", "B3", "B2"]).median().toUint16(), "s2_rgb_pre_2026JanApr.tif", 10)

post = s2.filterDate("2026-09-27", "2026-10-05")
info = post.aggregate_array("system:index").getInfo(), post.aggregate_array("CLOUDY_PIXEL_PERCENTAGE").getInfo()
print("post-event S2:", list(zip(*info)))
