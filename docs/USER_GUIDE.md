# KM Flood Priority user guide

The local ZIP is installable. Automated acceptance passed on QGIS 3.44.15 and 4.2.3,
including ZIP activation through qgis_process. Windows desktop acceptance and
screenshots must still be performed by a group member.

## Install and run on Windows

1. Install **QGIS 3.44 LTR** using the Windows installer from [QGIS Downloads](https://qgis.org/download/).
   Download/installation usually takes 10–15 minutes. Start QGIS after installation.
2. Plugins → Manage and Install Plugins → Install from ZIP. Select
   `dist/km_flood_priority-1.0.0.zip` and install it. The plugin menu has Run full
   pipeline…, Load sample data and Help; the Processing Toolbox has five algorithms.
3. Drag `data/processed/inputs.gpkg` into QGIS and select its five layers. This build
   excludes real sample data while redistribution terms are unresolved; Load sample
   data explains this. Synthetic fixtures are not demonstration sample data.
4. Open KM Flood Priority → Run full pipeline…; select the inputs below, leave the
   thresholds at their documented defaults and choose a new output filename. Run.
5. Open the result GeoPackage in a new project and select all layers. Check styles,
   source notes, priority reasons and UNKNOWN access. Disable and re-enable the plugin;
   menu entries must be removed and restored once, with no console error.

| Parameter | Current local input |
|---|---|
| RW_LAYER | `inputs.gpkg`, layer `rw` |
| RW_FIELD | `wadmrw` |
| ROADS | `inputs.gpkg`, layer `roads` |
| SAFE_POINTS | `inputs.gpkg`, layer `safe_points`; all current candidates remain N |
| KELURAHAN_BOUNDARY | `inputs.gpkg`, layer `kelurahan_boundary` |
| EVENTS_CSV | `data/processed/events_all.csv` |
| SOURCES_CSV | `data/clean/sources.csv` |
| KELURAHAN / KECAMATAN | `KAMPUNG MELAYU` / `JATINEGARA` |
| CLOSURES_CSV | Leave blank while no dated verified closure table exists |
| EVENT_DATES | Leave blank in the pipeline: all imported event dates |
| USE_UNVERIFIED_SAFE_POINTS | False; opt-in candidates stay flagged and do not establish safety |
| EPISODE_GAP_DAYS / REC_HIGH / REC_MED / DEPTH_HIGH_CM | `2` / `3` / `2` / `50` |

## Read the results

The five spatial layers have embedded defaults. Priority categories show recorded-event
verification priority; dashed outlines indicate field-check needs. Labels show RW and
episode counts. Green lines are reachable event routes; grey dashed lines are baseline
routes. Red origin crosses appear only with CUT_OFF evidence. Unverified candidates are
hollow and explicitly labelled. Zero-distance paths have a status/distance row and no line.

The six tables contain normalized events (including notes and duplicates), validation
issues, access by RW/date, priority including unassigned evidence, sources and run_info.
The run metadata records versions, UTC timestamp, UUID, parameters and actual event years.

**No recorded event (≠ safe).** Access without verified evidence is UNKNOWN. Sources
with incomplete dates/RW identity are excluded from the current event table. Shared
source impact totals are not allocated to individual RWs and must not be summed over
exploded rows. The current accepted PPID check was delegated to Claude by Raynald;
its provenance is retained in events.notes.

## Manual acceptance record

| Check | Status |
|---|---|
| ZIP enables and pipeline runs through qgis_process on 3.44.15 and 4.2.3 | Automated pass |
| All five algorithm IDs, field types, styles, deterministic tables, CRS and UNKNOWN rules | Automated pass |
| Menu lifecycle across two reloads | Automated interface test pass |
| Windows ZIP install and native menu/toolbox interaction | Human pending |
| Fresh-project styles, screenshots S1/S2 and clean-clone run by another member | Human pending |

Capture S1: styled result map with legend and RW labels. Capture S2: pipeline parameters
and successful result/log. Record QGIS version, tester, date and any correction in
`docs/PROGRESS.md`. These screenshots must come from the actual Windows acceptance;
headless maps are not substituted for human UI screenshots.

