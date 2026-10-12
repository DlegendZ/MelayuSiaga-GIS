# KM Flood Priority user guide

The local ZIP is installable. Automated acceptance passed on QGIS 3.44.15 and 4.2.3,
including ZIP activation and GUI result loading. Raynald reported a Windows run
on QGIS 3.44.15: 1.72 s, with priority_table, access_by_rw and events identical to
Phase 4. The operator was Claude under Raynald's instructions. S1/S2 are genuine
Windows screenshots. S2 shows the package reopened before the automatic style fix.
The first repaired ZIP failed Raynald's desktop style recheck (pipeline 1.2 s,
28 source / 56 normalized rows, zero errors). The replacement retains callbacks
at module level and passes two native Windows GUI regression paths; its desktop
recheck is pending. The earlier same-context test did not cover wrapper lifetime.

## Install and run on Windows

1. Install **QGIS 3.44 LTR** using the Windows installer from [QGIS Downloads](https://qgis.org/download/).
   Download/installation usually takes 10–15 minutes. Start QGIS after installation.
2. Plugins → Manage and Install Plugins → Install from ZIP. Select
   `dist/km_flood_priority-1.0.0.zip` and install it. The plugin menu has Run full
   pipeline…, Load sample data and Help; the Processing Toolbox has five algorithms.
3. Drag `data/processed/inputs.gpkg` into QGIS and select its five layers. This build
   excludes real sample data by Raynald's 2026-10-13 licensing decision; Load sample
   data explains unresolved permission and points to
   [README → Reproduce from scratch](../README.md#reproduce-from-scratch).
   The separate local data ZIP may be attached to the lecturer only if authorized.
   Synthetic fixtures are not demonstration sample data.
4. Open KM Flood Priority → Run full pipeline…; select the inputs below, leave the
   thresholds at their documented defaults and choose a new output filename. Run.
5. Check the automatically loaded result: rw_priority must already show categories
   and labels without reopening the file. Open the GeoPackage in a new project and
   select all layers to check the saved styles too. Check
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
| GUI loader uses final package styles without reopening | Fresh-context and background-worker regression pass on Qt5, Qt6 and native Windows 3.44.15 |
| Menu lifecycle across two reloads | Automated interface test pass |
| Windows operation and reopened-package styles; S1/S2 | Reported by Raynald, operated by Claude under his instructions |
| First repaired ZIP desktop style recheck | FAILED on Windows 3.44.15; pipeline data succeeded in 1.2 s |
| Replacement ZIP desktop recheck; independent clean-copy run | Pending |

Capture S1: Processing Toolbox showing the provider and the pipeline dialog.
Capture S2: styled result map with the rw_priority attribute table open.
Record QGIS version, tester, date and any correction in
`docs/PROGRESS.md`. These screenshots must come from the actual Windows acceptance;
headless maps are not substituted for human UI screenshots.

S1/S2 have now been supplied and are embedded in README. A future capture of the
fixed automatic loading should be labelled as a new run; the current S2 is retained
as evidence of the original reopened-package view.

## Recheck the updated ZIP (2 minutes)

1. Install the rebuilt `dist/km_flood_priority-1.0.0.zip`, then close and reopen QGIS
   to clear the previously imported plugin modules.
2. Run the same local inputs to **data/processed/style_recheck_v2.gpkg**. Inspect rw_priority immediately:
   HIGH/MEDIUM/VERIFY/NO_RECORD categories and RW/episode labels must appear without
   manually reopening the file. Layer Properties → Symbology should show Categorized.
3. In the Processing dialog's Log tab, check five `postProcessLayer(name)` entries
   and five `restored name style (...)` entries for rw_priority, safe_points,
   access_routes, roads and kelurahan_boundary. Record the result and save the new
   screenshot as `dist/local-data/S2_style_recheck_v2.png`. Keep the failed evidence.

Expected renderers: rw_priority, safe_points and access_routes are Categorized.
roads and kelurahan_boundary intentionally use Single Symbol: roads are grey
`#bdbdbd` at 0.15 mm; the boundary has a dark `#252525` outline at 0.8 mm with no
fill. Their renderer type alone does not indicate failure. The log must confirm
restoration for all five layers. No data transcription is required.

Save the actual screenshots as `docs/figures/S1_pipeline.png` and
`docs/figures/S2_results.png`. A 30–60 second installation → pipeline → map demo
can be saved as `demo.gif` or `demo.mp4` in that folder. Follow the
[capture checklist](figures/README.md); README contains prepared embed slots.

The accepted run gives RW 04/05 HIGH (16 episodes each), RW 07/08 MEDIUM (one
episode each), and five NO_RECORD RW. RW 04/05 share 25 source rows for Jl. Kebon
Pala II, RT 12–13 in RW 04 and RT 10–11 in RW 05. Counts must not be added across
the paired RW and no whole-RW inundation is claimed. All access is UNKNOWN.

