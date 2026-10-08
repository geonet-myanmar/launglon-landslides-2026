"""Web-map tiles of the drone orthos at native resolution.

512 px WebP tiles in the XYZ scheme (Leaflet: tileSize 512, zoomOffset -1), one set per area:
  tiles/kadet/     Ngone Min Taung + Ka Det Nge Htein
  tiles/thabyar/   the merged Tha Byar flights, 9.0 cm
  tiles/panyit/    road to Pa Nyit, 7.0 cm, to z21
  tiles/kadetgyi/  the merged Ka Det Gyi flights, 8.0 cm
  ../launglon-landslides-tiles/zalut/   the merged Pyin Gyi - Za Lut flights, 9.7 cm - published from its own repo
                   (EXTERNAL) to keep this Pages site under GitHub's 1 GB limit
  ../launglon-landslides-tiles/rabe/    the merged Ra Be flights, 9.2 cm - same tile repo
usage: python 10_tiles.py [kadet|thabyar|panyit|kadetgyi|zalut|rabe]
The deepest level, z20 in 512 px tiles, is 7.3 cm/px at 13.9 N - finer than both flights (10.1 and
8.0 cm), so nothing is reduced. Lower levels are 2x2 averages of their children. Where the flights meet,
the finer Ka Det Nge Htein flight is drawn over Ngone Min Taung. Blank tiles are skipped.
Taw Kye keeps the pyramid of its own pipeline (tiles/tawkye/, copied by step 11).
"""
import math
import numpy as np, rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import Affine
from rasterio.windows import Window
from PIL import Image
from sites import ROOT, d

SETS = {"kadet": ("nmt", "kdnh"), "thabyar": ("tby",), "panyit": ("pny",), "kadetgyi": ("kdg",), "zalut": ("pgz",), "rabe": ("rbe",)}  # later sites drawn on top
# tile sets published from a separate repo to keep this Pages site under GitHub's 1 GB limit (the page loads them by URL)
EXTERNAL = {"zalut": ROOT.parent / "launglon-landslides-tiles", "rabe": ROOT.parent / "launglon-landslides-tiles"}  # -> geonet-myanmar/launglon-landslides-tiles
ZMAX_SET = {"panyit": 21}  # Pa Nyit is 7.0 cm: z20 (7.2 cm) would reduce it, z21 is 3.6 cm
ZMAX_DEFAULT, ZMIN, TS = 20, 13, 512
R = 20037508.342789244


def tile_range(z, bounds_ll):
    w, s, e, n = bounds_ll

    def xy(lon, lat):
        x = (lon + 180) / 360 * 2 ** z
        y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * 2 ** z
        return x, y
    x0, y0 = xy(w, n)
    x1, y1 = xy(e, s)
    return int(x0), int(x1), int(y0), int(y1)


def main(name):
    ZMAX = ZMAX_SET.get(name, ZMAX_DEFAULT)
    OUT = EXTERNAL.get(name, ROOT / "tiles") / name
    res = 2 * R / (2 ** ZMAX * TS)
    grid = Affine(res, 0, -R, 0, -res, R)
    srcs = [rasterio.open(d(t, "ortho", "ortho_4326.tif")) for t in SETS[name]]
    W = H = 2 ** ZMAX * TS
    vrts = [WarpedVRT(s, crs="EPSG:3857", transform=grid, width=W, height=H, resampling=Resampling.bilinear) for s in srcs]
    have = set()
    for s, v in zip(srcs, vrts):
        x0, x1, y0, y1 = tile_range(ZMAX, s.bounds)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if (tx, ty) in have:
                    continue
                win = Window(tx * TS, ty * TS, TS, TS)
                out = np.zeros((4, TS, TS), np.uint8)
                for vv in vrts:
                    a = vv.read(window=win)
                    m = a[3] > 0
                    out[:, m] = a[:, m]
                if out[3].max() == 0:
                    continue
                p = OUT / str(ZMAX) / str(tx) / f"{ty}.webp"
                p.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(out.transpose(1, 2, 0), "RGBA").save(p, "WEBP", quality=82, method=4)
                have.add((tx, ty))
            print(f"z{ZMAX} {s.name[-30:]} row {ty - y0 + 1}/{y1 - y0 + 1}  tiles {len(have)}", flush=True)
    for z in range(ZMAX - 1, ZMIN - 1, -1):
        nxt = set()
        for px, py in {(x // 2, y // 2) for x, y in have}:
            canvas = Image.new("RGBA", (2 * TS, 2 * TS))
            for dx in (0, 1):
                for dy in (0, 1):
                    c = OUT / str(z + 1) / str(2 * px + dx) / f"{2 * py + dy}.webp"
                    if c.exists():
                        canvas.paste(Image.open(c).convert("RGBA"), (dx * TS, dy * TS))
            p = OUT / str(z) / str(px) / f"{py}.webp"
            p.parent.mkdir(parents=True, exist_ok=True)
            canvas.resize((TS, TS), Image.BOX).save(p, "WEBP", quality=82, method=4)
            nxt.add((px, py))
        have = nxt
        print(f"z{z}: {len(nxt)} tiles", flush=True)


if __name__ == "__main__":
    import sys
    for n in (sys.argv[1:] or list(SETS)):
        main(n)
