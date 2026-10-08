"""Stitch a KML super-overlay (quadtree of GroundOverlays) into one GeoTIFF at native resolution.

Same delivery format as the Taw Kye surveys: every leaf is a 512x512 tile in plain lat/lon
(EPSG:4326) at the deepest quadtree level (checked: 729 leaves for Ngone Min Taung, 776 for
Ka Det Nge Htein, all at depth 6), so each lands on integer offsets of the deepest grid.
Interior leaves are JPEG (no alpha -> fully valid), edge leaves PNG with alpha.
Written tile by tile - the 32768^2 grid never sits in RAM.
Tha Byar's two flights (tb1, tb2: 1031 and 949 leaves, depth 6, 9.5 / 9.0 cm) are mosaicked here and merged
into data/tby/ by 01b_merge_flights.py; Ka Det Gyi's (kg1, kg2: 844 and 889 leaves, 8.0 cm) into data/kdg/.
Thakyattaw_Yabel_4Plan_Combine.kmz (8 Oct) is one mosaic of four flights at depth 8 (3,488 leaves, 10.0 cm) whose
root box is 13 x 13 km but whose leaves form two separate blocks; a site with a `bbox` (sites.py: Tha Win, the northern
block, and Lel Hla, the southern one) takes only the leaves inside it, on a grid cropped to them.
"""
import io, sys, zipfile, xml.etree.ElementTree as ET
import numpy as np, rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window
from PIL import Image
from sites import SITES, FLIGHTS, SRC, d

NS = {"k": "http://www.opengis.net/kml/2.2"}


def overlays(z):
    kml = ET.fromstring(z.read("doc.kml"))
    out = []
    for go in kml.iter("{%s}GroundOverlay" % NS["k"]):
        b = go.find("k:LatLonBox", NS)
        box = {t: float(b.find("k:" + t, NS).text) for t in ("west", "east", "south", "north")}
        out.append((go.find("k:Icon/k:href", NS).text, box))
    return out


def run(tag):
    z = zipfile.ZipFile(SRC / {**SITES, **FLIGHTS}[tag]["kmz"])
    ovs = overlays(z)
    root = next(b for h, b in ovs if h.startswith("a."))
    depth = max(ord(h[0]) - ord("a") for h, _ in ovs)
    n = 2 ** depth * 512
    dx = (root["east"] - root["west"]) / n
    dy = (root["north"] - root["south"]) / n
    print(f"{tag}: depth {depth}, grid {n}x{n}, px {dx:.3e} x {dy:.3e} deg")
    out = d(tag, "ortho", "ortho_4326.tif")
    out.parent.mkdir(parents=True, exist_ok=True)
    prof = dict(driver="GTiff", width=n, height=n, count=4, dtype="uint8", crs="EPSG:4326",
                transform=from_origin(root["west"], root["north"], dx, dy), tiled=True,
                blockxsize=512, blockysize=512, compress="deflate", predictor=2, BIGTIFF="YES",
                photometric="RGB")
    ovs = [(h, b) for h, b in ovs if ord(h[0]) - ord("a") == depth]
    bb = {**SITES, **FLIGHTS}[tag].get("bbox")
    if bb:  # this block's leaves only, on the grid cut down to them
        ovs = [(h, b) for h, b in ovs if bb[0] < (b["west"] + b["east"]) / 2 < bb[2] and bb[1] < (b["south"] + b["north"]) / 2 < bb[3]]
        c0 = min(round((b["west"] - root["west"]) / dx) for _, b in ovs)
        r0 = min(round((root["north"] - b["north"]) / dy) for _, b in ovs)
        c1 = max(round((b["west"] - root["west"]) / dx) for _, b in ovs) + 512
        r1 = max(round((root["north"] - b["north"]) / dy) for _, b in ovs) + 512
        root = {"west": root["west"] + c0 * dx, "north": root["north"] - r0 * dy}
        prof.update(width=c1 - c0, height=r1 - r0, transform=from_origin(root["west"], root["north"], dx, dy), SPARSE_OK=True)
        print(f"  {len(ovs)} leaves in bbox, grid {c1 - c0}x{r1 - r0}")
    with rasterio.open(out, "w", **prof) as dst:
        for i, (href, b) in enumerate(ovs):
            c0 = round((b["west"] - root["west"]) / dx)
            r0 = round((root["north"] - b["north"]) / dy)
            im = Image.open(io.BytesIO(z.read(href))).convert("RGBA")
            a = np.asarray(im).transpose(2, 0, 1)
            assert a.shape == (4, 512, 512), (href, a.shape)
            dst.write(a, window=Window(c0, r0, 512, 512))
            if i % 200 == 0:
                print(f"  {i}/{len(ovs)}", flush=True)
    print("wrote", out)


if __name__ == "__main__":
    for t in (sys.argv[1:] or [s for s in SITES if "kmz" in SITES[s] and "+" not in SITES[s]["kmz"]] + list(FLIGHTS)):
        run(t)
