# Launglon landslides, 26-27 Sep 2026: ten drone surveys

Dashboard and analysis of the landslides at **Tha Byar** (သဗျာ), the **road to Pa Nyit** (ပညစ်), **Ngone Min Taung** (the slopes south of Htein Gyi),
**Ka Det Nge Htein** (ကဒက်ငယ်ထိန်), **Ka Det Gyi** (ကဒက်ကြီး, with Nyaungdon and Wet Thar Kin) **Taw Kye** (တောကျဲ), **Tha Win** (သဝင်), **Lel Hla** (လယ်လှ), the **Ra Be - Kyauk Twin road** (ရဘဲ) and **Pyin Gyi - Za Lut** (ပြင်ကြီး - ဇလွတ်), Launglon Township, Tanintharyi Region, Myanmar, from
post-event drone orthomosaics, with MIMU, Copernicus DEM, Sentinel-2, Esri Vantor imagery of 10 Jan 2026,
OSM/Microsoft footprints, Open-Meteo rainfall and Dawei Watch reports.

Open `index.html` (it needs `tiles/`, `assets/` and `outputs/` beside it).

## Results (from `outputs/summary.json`)
| | Tha Byar | Pa Nyit road | Ngone Min Taung | Ka Det Nge Htein | Ka Det Gyi | Taw Kye | Tha Win | Lel Hla | Pyin Gyi - Za Lut | Ra Be road |
|---|---|---|---|---|---|---|---|---|---|---|
| flown / resolution | 5 Oct, 9.5 + 9.0 cm (2 flights) | 5 Oct, 7.0 cm | 4 Oct, 10.1 cm | 3 Oct, 8.0 cm | 6 Oct, 8.0 + 8.0 cm (2 flights) | 2 Oct, 3.75 / 5.68 cm | 8 Oct, 10.0 cm (northern block of one 4-flight mosaic) | 8 Oct, 10.0 cm (southern block) | 7 Oct, 10.4 + 9.7 cm (2 flights) | 8 Oct, 9.2 + 9.2 cm (2 flights) |
| landslides (area) | 23 (49.8 ha) | 7 (3.4 ha) | 26 (20.7 ha, 8 channels + 14 minor) | 9 (16.2 ha) | 21 (10.6 ha) | 9 (20.6 ha) | 32 (66.4 ha, 12 channels + 7 minor) | 5 (11.4 ha) | 12 (12.2 ha) | 21 (30.0 ha) |
| + ground under sediment | 32.6 ha (village and fields) | - | - | 15.7 ha (paddy) | 7.8 ha (fields, end of the KD-01 fan) | - | 18.2 ha (west of Tha Win, valley mouth, paddies) | 1.7 ha (gardens east of the road) | 0.9 ha (fields at a valley mouth) | 1.5 ha (fields east of the road) |
| buildings destroyed / damaged | 2 / 4, 41 standing in sediment | 0 / 0 (one hut in survey) | 0 / 1 | 25 / 2 | 0 / 0, 1 standing in sediment | 36 / 12 | 3 / 0, 11 standing in sediment | 0 / 0, 1 at edge, 2 in sediment | 8 / 2 | 0 / 0 (4 buildings in survey) |
| reported (Dawei Watch) | 3 dead, nearly 40 houses | road blocked; 2 houses in Pa Nyit village (outside survey), no deaths | none | 15 dead, >30 houses | 2 dead in an orchard a few miles away (probably outside survey) | 5 dead, 42 houses | road Taw Kye - Tha Win blocked; no deaths or houses reported | not named; Tha Win - Tha Kyet Taw road blocked | 1 dead, about 20 houses destroyed or uninhabitable | roads cut, Kyauk Twin tract isolated; no deaths reported |
| reach angle open / channel | 14.0 / 8.0 deg | 20.6 / 16.4 deg | 14.8 / 11.6 deg | 16.2 / 13.2 deg | 12.6 / 18.1 deg (zone B empty) | 17.6 / 13.4 deg | 18.2 / 12.2 deg | 19.1 / 15.5 deg | 13.8 / 13.1 deg | 12.8 / 15.0 deg (zone B empty) |
| standing buildings in runout zone A | 1 (model fails here, see below) | 1 | 29 | 39 | 142 | 101 | 6 (192 in zone B) | 4 (47 in zone B) | 51 | 3 |

**Tha Byar runout:** the flows that reached the village ran along a valley floor that the 30 m DEM shows as flat and
lumpy (forest canopy). The energy-line model only moves debris downhill, so it stalls there at any angle (even 3 deg
covers 55 % of TB-01) and none of the 47 destroyed, damaged or in-sediment buildings fall in its zones. The page says
so; the zones were not tuned to hide it (back-analysis in the `08_runout.py` docstring).

## Pipeline (`scripts/`, run in order; `sites.py` holds per-site settings)
| step | script | does |
|---|---|---|---|---|---|
| 01 | `01_mosaic_kmz.py` | KML super-overlay -> GeoTIFF at native resolution (KMZs read from `../`); a site `bbox` takes one block of a delivery (Tha Win, Lel Hla) |
| 01b | `01b_merge_flights.py` | merges the two flights of Tha Byar, Ka Det Gyi, Pyin Gyi - Za Lut and Ra Be onto the finer grid; the sharper flight wins in the overlap |
| 02 | `02_envelopes.py` | interpreter envelopes, outwash, exclusions -> `data/<site>/inventory/envelopes.geojson` |
| 03 | `03_fetch_ee.py south\|north\|west\|southeast\|zalut\|rabe\|thawin` (set `EE_PROJECT`) | GLO-30 DEM, Sentinel-2 NDVI, VIDA + OSM footprints -> `data/ee/`, `data/ee_tby/`, `data/ee_pny/`, `data/ee_kdg/`, `data/ee_pgz/`, `data/ee_rbe/`, `data/ee_thw/` |
| 04 | `04_classify.py` | per-pixel classes + 1 m majority bare mask; ExG threshold at each flight's histogram valley |
| 05 | `05_inventory.py` | outlines = bare mask inside envelopes minus exclusions; split zones -> grouped components |
| 06 | `06_terrain.py` | crown, toe, H, L, reach angle, edge flags, slope zones, pre-event NDVI |
| 07 | `07_buildings.py` | footprint shift, native-pixel fractions, status (+ `building_overrides.csv`) |
| 08 | `08_runout.py` | energy-line runout reach calibrated per site |
| 09 | `09_rainfall.py` | Open-Meteo model rainfall (cached; an existing cache is kept) |
| 10 | `10_tiles.py kadet\|thabyar\|panyit\|kadetgyi\|zalut\|rabe\|thawin` | 512 px WebP XYZ tiles to z20 (7.3 cm/px) in `tiles/kadet/`, `tiles/thabyar/`, `tiles/kadetgyi/`; to z21 in `tiles/panyit/` (the flight is 7.0 cm) |
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

Ka Det Gyi specifics: the two flights disagree by a steady 1.3 m E / 0.4 m N, so Plan 1 is moved onto Plan 2
(`sites.MERGE_SHIFT`) before merging; the 4.3 ha also covered by the Ka Det Nge Htein flight is left to that site
(`minus_sites`); the automatic footprint shift (+4.75 m E) is pulled off the roofs by bare grey yards, so a zero shift
is set by eye (`footprint_shift`). KGN-01's debris continues through a clearing bare in January (excluded) to within a
few metres of two houses by Wet Thar Kin's road; no channel out-ran the open slides, so zone B is empty.

Pyin Gyi - Za Lut specifics: the flights disagree by a steady 0.2 m E / 2.2 m N and Plan 1 is moved before merging; the
MIMU points of both villages lie 1.4 km south of the survey (the settlement imaged is the stretch along the road
further north); PG-03's calibration path runs from PG-04's crown to PG-03's toe; three rock slabs bare in January are
excluded. **Its tiles are published from a separate repo**, geonet-myanmar/launglon-landslides-tiles (folder
`../launglon-landslides-tiles/`, `10_tiles.py` EXTERNAL), because with them this site would reach 969 MB of GitHub
Pages' 1 GB limit; the page loads them from https://geonet-myanmar.github.io/launglon-landslides-tiles/zalut/.
Future tile sets should go there too.

Ra Be specifics: the flights disagree by a steady 4.9 m E / 1.0 m N (largest offset of any pair) and RD_1 is moved
before merging; the 55 ha shared with Pyin Gyi - Za Lut is left to that site (`minus_sites`); the whole hillside is one
split zone (RZ) plus the road-crossing flow RB-01; RZ-01/03/04 are channel networks. Tiles: `rabe/` in the tile repo.

Tha Win and Lel Hla specifics: `Thakyattaw_Yabel_4Plan_Combine.kmz` is one depth-8 super-overlay (3,488 leaves, 10.0 cm)
mosaicked by the provider from four flights; its leaves form two blocks, cut into two sites by `bbox` in step 01 (Tha Win,
northern, 546 ha; Lel Hla, southern, 209 ha). The northern block surrounds the whole 2 Oct Taw Kye survey, which keeps its
ground (`minus_sites: ["tawkye"]`, also applied to Tha Win's runout zones). TW-01 is the feeder of Taw Kye's LS-01 mud fan.
Through Tha Win the split zone stops at the foot of the hill and the sediment in the village is outwash (yards bare in
January are not slides). A roadside mud deposit (TW-OW5) and a valley-floor scour (TZ-20, typed channel) are kept from
setting the open-slope reach angle. One ExG threshold (0.045, both blocks pooled) for the one delivery. Tiles: `thawin/`
in the tile repo.

## Not in this repository
The KMZ deliveries and the native-resolution rasters built from them (`data/*/ortho/`, `data/*/class/`) are kept out
of git. Steps 06-09 and 12 run from what is committed; steps 01, 01b, 04, 05, 07 and 10 need the KMZs.

Live page: https://geonet-myanmar.github.io/launglon-landslides-2026/
