# Launglon landslides, 26-27 Sep 2026: three drone surveys

Dashboard and analysis of the landslides at **Ka Det Nge Htein** (ကဒက်ငယ်ထိန်), **Ngone Min Taung** (the slopes south of
Htein Gyi) and **Taw Kye** (တောကျဲ), Launglon Township, Tanintharyi Region, Myanmar, from post-event drone orthomosaics,
with MIMU, Copernicus DEM, Sentinel-2, Esri Vantor imagery of 10 Jan 2026, OSM/Microsoft footprints, Open-Meteo
rainfall and Dawei Watch reports.

Open `index.html` (it needs `tiles/`, `assets/` and `outputs/` beside it).

## Results (from `outputs/summary.json`)
| | Ka Det Nge Htein | Ngone Min Taung | Taw Kye |
|---|---|---|---|
| flown / resolution | 3 Oct, 8.0 cm | 4 Oct, 10.1 cm | 2 Oct, 3.75 / 5.68 cm |
| landslides (area) | 9 (16.2 ha) | 26 (20.7 ha, 8 channels + 14 minor) | 9 (20.6 ha) |
| + fields under sediment | 15.7 ha | - | - |
| buildings destroyed / damaged | 25 / 2 | 0 / 1 | 36 / 12 |
| reported (Dawei Watch) | 15 dead, >30 houses | none | 5 dead, 42 houses |
| reach angle open / channel | 16.2 / 13.2 deg | 14.8 / 11.6 deg | 17.6 / 13.4 deg |
| standing buildings in runout zone A | 39 | 29 | 101 |

## Pipeline (`scripts/`, run in order; `sites.py` holds per-site settings)
| step | script | does |
|---|---|---|
| 01 | `01_mosaic_kmz.py` | KML super-overlay -> GeoTIFF at native resolution (KMZs read from `../`) |
| 02 | `02_envelopes.py` | interpreter envelopes, outwash, exclusions -> `data/<site>/inventory/envelopes.geojson` |
| 03 | `03_fetch_ee.py` (set `EE_PROJECT`) | GLO-30 DEM, Sentinel-2 NDVI, VIDA + OSM footprints |
| 04 | `04_classify.py` | per-pixel classes + 1 m majority bare mask; ExG threshold at each flight's histogram valley |
| 05 | `05_inventory.py` | outlines = bare mask inside envelopes minus exclusions; split zones -> grouped components |
| 06 | `06_terrain.py` | crown, toe, H, L, reach angle, edge flags, slope zones, pre-event NDVI |
| 07 | `07_buildings.py` | footprint shift, native-pixel fractions, status (+ `building_overrides.csv`) |
| 08 | `08_runout.py` | energy-line runout reach calibrated per site |
| 09 | `09_rainfall.py` | Open-Meteo model rainfall (cached) |
| 10 | `10_tiles.py` | 512 px WebP XYZ tiles to z20 (7.3 cm/px) in `tiles/kadet/` |
| 11 | `11_import_tawkye.py` | copies the Taw Kye products, tiles and photos from `../tawkye-landslide-2026` |
| 12 | `12_build_page.py` | `outputs/` (GeoPackage, CSV, summary) and `index.html` from `src/template.html` |

Never hand-edit `index.html`; edit `src/template.html` and re-run step 12.

Hand-made inputs: the envelope coordinates in `02_envelopes.py` (drawn against the Esri Vantor image of 10 Jan 2026),
the feature names in `sites.py`, and `data/kdnh/inventory/building_overrides.csv` (13 statuses changed after checking
image chips, each with its reason).

## Not in this repository
The KMZ deliveries and the native-resolution rasters built from them (`data/*/ortho/`, `data/*/class/`) are kept out
of git. Steps 06-09 and 12 run from what is committed; steps 01, 04, 05, 07 and 10 need the KMZs.

Live page: https://geonet-myanmar.github.io/launglon-landslides-2026/
