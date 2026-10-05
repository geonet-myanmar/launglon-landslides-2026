# Launglon landslides, 26-27 Sep 2026: five drone surveys

Dashboard and analysis of the landslides at **Tha Byar** (သဗျာ), the **road to Pa Nyit** (ပညစ်), **Ngone Min Taung** (the slopes south of Htein Gyi),
**Ka Det Nge Htein** (ကဒက်ငယ်ထိန်) and **Taw Kye** (တောကျဲ), Launglon Township, Tanintharyi Region, Myanmar, from
post-event drone orthomosaics, with MIMU, Copernicus DEM, Sentinel-2, Esri Vantor imagery of 10 Jan 2026,
OSM/Microsoft footprints, Open-Meteo rainfall and Dawei Watch reports.

Open `index.html` (it needs `tiles/`, `assets/` and `outputs/` beside it).

## Results (from `outputs/summary.json`)
| | Tha Byar | Pa Nyit road | Ngone Min Taung | Ka Det Nge Htein | Taw Kye |
|---|---|---|---|---|---|
| flown / resolution | 5 Oct, 9.5 + 9.0 cm (2 flights) | 5 Oct, 7.0 cm | 4 Oct, 10.1 cm | 3 Oct, 8.0 cm | 2 Oct, 3.75 / 5.68 cm |
| landslides (area) | 23 (49.8 ha) | 7 (3.4 ha) | 26 (20.7 ha, 8 channels + 14 minor) | 9 (16.2 ha) | 9 (20.6 ha) |
| + ground under sediment | 32.6 ha (village and fields) | - | - | 15.7 ha (paddy) | - |
| buildings destroyed / damaged | 2 / 4, 41 standing in sediment | 0 / 0 (one hut in survey) | 0 / 1 | 25 / 2 | 36 / 12 |
| reported (Dawei Watch) | 3 dead, nearly 40 houses | road blocked; 2 houses in Pa Nyit village (outside survey), no deaths | none | 15 dead, >30 houses | 5 dead, 42 houses |
| reach angle open / channel | 14.0 / 8.0 deg | 20.6 / 16.4 deg | 14.8 / 11.6 deg | 16.2 / 13.2 deg | 17.6 / 13.4 deg |
| standing buildings in runout zone A | 1 (model fails here, see below) | 1 | 29 | 39 | 101 |

**Tha Byar runout:** the flows that reached the village ran along a valley floor that the 30 m DEM shows as flat and
lumpy (forest canopy). The energy-line model only moves debris downhill, so it stalls there at any angle (even 3 deg
covers 55 % of TB-01) and none of the 47 destroyed, damaged or in-sediment buildings fall in its zones. The page says
so; the zones were not tuned to hide it (back-analysis in the `08_runout.py` docstring).

## Pipeline (`scripts/`, run in order; `sites.py` holds per-site settings)
| step | script | does |
|---|---|---|
| 01 | `01_mosaic_kmz.py` | KML super-overlay -> GeoTIFF at native resolution (KMZs read from `../`) |
| 01b | `01b_merge_tby.py` | merges the two Tha Byar flights onto the finer grid; the sharper flight wins in the overlap |
| 02 | `02_envelopes.py` | interpreter envelopes, outwash, exclusions -> `data/<site>/inventory/envelopes.geojson` |
| 03 | `03_fetch_ee.py south\|north\|west` (set `EE_PROJECT`) | GLO-30 DEM, Sentinel-2 NDVI, VIDA + OSM footprints -> `data/ee/`, `data/ee_tby/`, `data/ee_pny/` |
| 04 | `04_classify.py` | per-pixel classes + 1 m majority bare mask; ExG threshold at each flight's histogram valley |
| 05 | `05_inventory.py` | outlines = bare mask inside envelopes minus exclusions; split zones -> grouped components |
| 06 | `06_terrain.py` | crown, toe, H, L, reach angle, edge flags, slope zones, pre-event NDVI |
| 07 | `07_buildings.py` | footprint shift, native-pixel fractions, status (+ `building_overrides.csv`) |
| 08 | `08_runout.py` | energy-line runout reach calibrated per site |
| 09 | `09_rainfall.py` | Open-Meteo model rainfall (cached; an existing cache is kept) |
| 10 | `10_tiles.py kadet\|thabyar\|panyit` | 512 px WebP XYZ tiles to z20 (7.3 cm/px) in `tiles/kadet/`, `tiles/thabyar/`; to z21 in `tiles/panyit/` (the flight is 7.0 cm) |
| 11 | `11_import_tawkye.py` | copies the Taw Kye products, tiles and photos from `../tawkye-landslide-2026` |
| 12 | `12_build_page.py` | `outputs/` (GeoPackage, CSV, summary) and `index.html` from `src/template.html` |

Never hand-edit `index.html`; edit `src/template.html` and re-run step 12.

Hand-made inputs: the envelope coordinates in `02_envelopes.py` (drawn against the drone orthos and the Esri Vantor
image of 10 Jan 2026), the feature names and edge overrides in `sites.py`, and `data/<site>/inventory/building_overrides.csv`
(each status changed after checking image chips, with its reason).

Tha Byar specifics (all switched on in `sites.py`): the two flights agree to 0.3-0.5 m and are merged, not shifted;
drawn envelopes keep only bare patches >= 500 m2 or within 5 m of one (rubber-plantation canopy gaps read as bare);
roofs are cut out of the village outwash and "standing in sediment" is tested on a 3 m ring around each footprint;
TB-01 and TB-05 enter across the survey edge, so the channel calibration uses TB-03's crown to TB-01's toe.

Pa Nyit road specifics: no village in the survey (Pa Nyit, MIMU 177151, is 1.7 km west); the road was traced on the
ortho and excluded with its cut banks (debris lying on it is not counted); only one real building (a hut) - four
Microsoft footprints on canopy or grass were dropped; PN-01's toe is at the survey edge, so its 16.4 deg is an upper bound.

## Not in this repository
The KMZ deliveries and the native-resolution rasters built from them (`data/*/ortho/`, `data/*/class/`) are kept out
of git. Steps 06-09 and 12 run from what is committed; steps 01, 01b, 04, 05, 07 and 10 need the KMZs.

Live page: https://geonet-myanmar.github.io/launglon-landslides-2026/
