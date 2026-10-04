"""Import the finished Taw Kye products (tawkye-landslide-2026 pipeline, 3 Oct 2026) into data/tawkye/.

Taw Kye was analysed with the same method (its scripts 01-12); nothing is recomputed here. The copies
are committed so the dashboard rebuilds without the Taw Kye workspace. Tiles and media are copied
into tiles/tawkye/ and assets/tawkye/ so the page is self-contained.
Source: a sibling folder ../tawkye-landslide-2026 (override with TAWKYE_DIR).
"""
import os, shutil
from pathlib import Path
from sites import ROOT

SRC = Path(os.environ.get("TAWKYE_DIR", ROOT.parent / "tawkye-landslide-2026"))
FILES = ["data/inventory/landslides_utm.gpkg", "data/inventory/buildings_utm.gpkg", "data/inventory/terrain.json",
         "data/inventory/envelopes.geojson", "data/inventory/footprint_landslide_flight.geojson",
         "data/inventory/footprint_plan2_flight.geojson", "data/inventory/footprint_shifts.json",
         "data/inventory/building_overrides.csv", "data/hazard/reach_zones.geojson", "data/hazard/runout_summary.json",
         "data/source/rainfall_openmeteo_tawkye.json", "outputs/summary.json", "outputs/landslides.csv"]


def main():
    dst = ROOT / "data/tawkye"
    for f in FILES:
        o = dst / Path(f).name
        o.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC / f, o)
    a = ROOT / "assets/tawkye"
    a.mkdir(parents=True, exist_ok=True)
    for p in (SRC / "assets").glob("*.jpg"):
        shutil.copy2(p, a / p.name)
    t = ROOT / "tiles/tawkye"
    if t.exists():
        shutil.rmtree(t)
    shutil.copytree(SRC / "tiles", t)
    n = sum(1 for _ in t.rglob("*.webp"))
    # the Taw Kye MIMU download (bbox 97.85-98.45 E, 13.45-14.15 N) also covers the two new sites
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for p in (SRC / "data/raw").glob("*.geojson"):
        shutil.copy2(p, raw / p.name)
    print(f"copied {len(FILES)} data files, {len(list(a.iterdir()))} images, {n} tiles, MIMU layers from {SRC}")


if __name__ == "__main__":
    main()
