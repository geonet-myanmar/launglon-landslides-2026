"""Merge the two Tha Byar flights (5 Oct 2026) into one ortho, so every later step treats Tha Byar as one site.

TharByar_Plan_1 (village and western slopes, 9.5 cm) and TharByar_Plan_2 (northern hills, 9.0 cm) overlap in a
~500 m strip. In that strip they agree to 0.3-0.5 m (phase correlation on six 120 m patches: tb1 -> tb2
dE +0.24..+0.36, dN -0.30..-0.50 m), so neither is shifted. Both are resampled onto Plan 2's finer lat/lon grid,
extended to the union of the flights - Plan 1 is upsampled by 6 %, nothing is reduced.
In the overlap each pixel comes from the SHARPER flight: mean |Laplacian| of grey per 16 x 16 px cell, median-
smoothed over 5 x 5 cells (~7 m), larger wins. Orthomosaics smear towards their edges, and Plan 1 is smeared
over ~250 m east of 98.1285 E - a distance-to-edge rule kept that smear, sharpness does not. Plan 1's smeared
strip that Plan 2 does not cover is an exclusion area in 02_envelopes.py.
Writes data/tby/ortho/ortho_4326.tif and data/tby/ortho/source.tif (1 = plan 1, 2 = plan 2, 1/16 grid).
"""
import numpy as np, rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window
from scipy.ndimage import laplace, median_filter
from sites import d

STEP = 4096
F = 16


def main():
    s1, s2 = (rasterio.open(d(t, "ortho", "ortho_4326.tif")) for t in ("tb1", "tb2"))
    dx, dy = s2.res
    # data extent (alpha) of both flights, from 1/16 overviews
    ext = []
    for s in (s1, s2):
        a = s.read(4, out_shape=(s.height // F, s.width // F), resampling=Resampling.nearest)
        r, c = np.nonzero(a)
        t = s.transform * s.transform.scale(s.width / a.shape[1], s.height / a.shape[0])
        ext.append((t * (c.min(), r.max() + 1), t * (c.max() + 1, r.min())))
    W = min(e[0][0] for e in ext); S = min(e[0][1] for e in ext)
    E = max(e[1][0] for e in ext); N = max(e[1][1] for e in ext)
    width, height = int(np.ceil((E - W) / dx)), int(np.ceil((N - S) / dy))
    T = from_origin(W, N, dx, dy)
    print(f"merged grid {width} x {height}, px {dx:.3e} x {dy:.3e} deg, extent {W:.5f} {S:.5f} {E:.5f} {N:.5f}")
    # which flight wins, on a 1/16 grid: sharpness of each flight per cell
    oh, ow = -(-height // F), -(-width // F)
    To = T * T.scale(F, F)
    vrts = [WarpedVRT(s, crs=s.crs, transform=T, width=width, height=height, resampling=Resampling.bilinear)
            for s in (s1, s2)]
    sharp = np.zeros((2, oh, ow), np.float32)
    valid = np.zeros((2, oh, ow), bool)
    for r in range(0, height, STEP):
        for c in range(0, width, STEP):
            h, w = min(STEP, height - r), min(STEP, width - c)
            for k, v in enumerate(vrts):
                a = v.read(window=Window(c, r, w, h)).astype(np.float32)
                if a[3].max() == 0:
                    continue
                lap = np.abs(laplace(a[:3].mean(0)))
                ok = a[3] > 250
                hh, ww = -(-h // F), -(-w // F)
                pad = lambda x: np.pad(x, ((0, hh * F - h), (0, ww * F - w)))
                n = pad(ok).reshape(hh, F, ww, F).sum((1, 3))
                sm = pad(lap * ok).reshape(hh, F, ww, F).sum((1, 3))
                sl = (slice(r // F, r // F + hh), slice(c // F, c // F + ww))
                sharp[k][sl] = np.where(n > 0, sm / np.maximum(n, 1), 0)
                valid[k][sl] = n >= F * F * 0.9
        print(f"  sharpness row {r}/{height}", flush=True)
    sharp = np.stack([median_filter(x, 5) for x in sharp])
    src = np.zeros((oh, ow), np.uint8)
    src[valid[0]] = 1
    src[valid[1] & (~valid[0] | (sharp[1] > sharp[0]))] = 2
    out = d("tby", "ortho")
    out.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out / "source.tif", "w", driver="GTiff", width=ow, height=oh, count=1, dtype="uint8",
                       crs=s2.crs, transform=To, compress="deflate") as o:
        o.write(src, 1)
    print("overview cells from plan 1 / plan 2:", int((src == 1).sum()), int((src == 2).sum()))
    prof = dict(driver="GTiff", width=width, height=height, count=4, dtype="uint8", crs=s2.crs, transform=T,
                tiled=True, blockxsize=512, blockysize=512, compress="deflate", predictor=2, BIGTIFF="YES",
                photometric="RGB")
    with rasterio.open(out / "ortho_4326.tif", "w", **prof) as dst:
        for r in range(0, height, STEP):
            for c in range(0, width, STEP):
                h, w = min(STEP, height - r), min(STEP, width - c)
                win = Window(c, r, w, h)
                pick = src[r // F:(r + h - 1) // F + 1, c // F:(c + w - 1) // F + 1]
                a1 = vrts[0].read(window=win)
                a2 = vrts[1].read(window=win)
                if a1[3].max() == 0 and a2[3].max() == 0:
                    continue
                pick = np.repeat(np.repeat(pick, F, 0), F, 1)[r % F:r % F + h, c % F:c % F + w]
                o = np.where((pick == 2)[None], a2, a1)
                # where the winner has no data at full resolution (edge of a 16 px cell), take the other flight
                miss = o[3] == 0
                o[:, miss] = np.where((pick[miss] == 2)[None], a1[:, miss], a2[:, miss])
                dst.write(o, window=win)
            print(f"  row {r}/{height}", flush=True)
    print("wrote", out / "ortho_4326.tif")


if __name__ == "__main__":
    main()
