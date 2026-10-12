# EXECUTION SPEC — Kampung Melayu Flood Verification-Priority (QGIS Plugin)

**Document type:** Software Requirements Specification + Build Plan (combined), written for a coding agent.
**Course:** GIS Final Project — "Spatial Problem Solving for Indonesian Cities and Provinces" (BINUS, lecturer: Fabian Surya Pramudya, Ph.D.)
**Group:** Raynald Arvan Lim (`raynald.lim@binus.ac.id`), Alden Viriya Tanudjaja (`alden.tanudjaja@binus.ac.id`), Moses Handoyo (`moses.handoyo@binus.ac.id`). Three members confirmed by the user on 2026-10-12; lecturer approval is pending because R1 specifies two.
**Spec version:** 1.0 — 2026-10-12
**Status:** Approved for execution

---

## 0. How to use this document (read first, coding agent)

1. This document is the **single source of truth**. If something here conflicts with your own preference, follow this document. If something here is impossible or wrong, **stop and report**; do not silently redesign.
2. Work **phase by phase** (§12). Each phase has explicit acceptance criteria. Do not start a phase until the previous phase's criteria pass, except where a phase is marked *parallel*.
3. Tasks are tagged:
   - **[A]** — the agent does it alone.
   - **[H]** — a human (the students) must do it. The agent prepares templates and instructions, then **waits**. Never fabricate the output of an [H] task.
   - **[A+H]** — the agent drafts, the human verifies or approves.
4. **Never invent data.** Real data comes only from the sources in §6. Synthetic data is allowed **only** in `tests/fixtures/`. It must be obviously fake (e.g. kelurahan name `TESTVILLE`), and it must never appear in deliverables, figures, or the brief.
5. Keep scope tight (§3.3, non-goals). The grading ceiling for a QGIS plugin is already 100%. Extra architecture earns nothing and adds risk.
6. At the end of every phase, update `docs/PROGRESS.md` with: what was done, test results, open issues, and anything waiting on [H].

---

## 1. Context

### 1.1 Assignment requirements (verbatim intent from the guideline)

| # | Requirement | Where satisfied |
|---|---|---|
| R1 | Groups of 2; pick **one city or province** in Indonesia | Study area framed as **Kota Jakarta Timur**, analysis focus **Kelurahan Kampung Melayu** (§2.2) |
| R2 | Identify a specific spatial problem; show how spatial data, GIS analysis and visualization help understand, assess or address it | §2, §7 |
| R3 | **Technical Brief, 2 pages**: problem definition, study area, data sources, GIS methodology, key spatial findings, proposed solution/recommendation, screenshot/URL of product | §11 |
| R4 | **Deployed source code** in the group repository, with documentation sufficient to reproduce | §9, §10 |
| R5 | **GIS application**: choose one. Chosen: **QGIS Plugin** (max 100%). Must provide meaningful GIS functionality for the problem and be successfully deployed and operated within QGIS | §4, §5, §8 |

**Group exception — confirmed by Raynald 2026-10-13:** this group is permitted three
members: Raynald Arvan Lim, Alden Viriya Tanudjaja and Moses Handoyo. R1 above retains
the general guideline; the group-size confirmation task is resolved for this project.

**Why a QGIS plugin and not a web app:** a static web app caps at 85%. Reaching 100% with a web app needs a framework, backend, and database. A functional plugin reaches 100% with a smaller, more testable surface. The research document already specifies three plugin processes, and this spec implements exactly those.

### 1.2 Source research (summary of `Riset GIS_ Banjir Kampung Melayu.pdf`)

- **Question:** Which RT/RW most need verification and prioritization for flood preparedness, and is access to safe points still passable during floods?
- **Area:** Kelurahan Kampung Melayu, Kecamatan Jatinegara, Jakarta Timur. Recorded area **47.83 ha**.
- **Evidence anchor:** The 2025 Jakarta Timur flood recap (PPID) lists Jalan Kebon Pal in RW 04 and RW 05. These are *recorded events*, not proof of highest hazard.
- **Claim limits:** There is no defensible RT ranking yet. RT boundaries, multi-year coverage, depth, safe points, and cut roads all need verification. Scenarios are not observations.
- **Method:** (1) extract events into a structured table; (2) prepare geometry in a metric CRS; (3) measure recurrence per unit, keep max depth separate, show empty data, and use scenarios only as a comparator; (4) test access per event with verified closures, outputting *unknown* when data is missing; (5) classify into high / medium / needs-verification.
- **Plugin processes named in research:** `import_dan_validasi`, `hitung_prioritas`, `uji_akses`. Export a GeoPackage with result layers, events, source metadata, update date, and data quality. **MVP at RW scale**; RT and routing are enabled only after the supporting data is verified.

### 1.3 Known limitations (accepted, not violations)

1. The study area is small, so this is a **local verification tool**, not a regional pattern study. Frame it that way.
2. One year of data is weak evidence of recurrence. **Mitigation:** add multi-year RW-level records from Satu Data Jakarta (§6, D2).
3. OSM data age and completeness vary. **Mitigation:** use official DKI RW and kelurahan polygons for boundaries (§6, D3/D4). Use OSM only for roads and buildings, and record the snapshot date.

---

## 2. Problem definition & scope

### 2.1 Problem statement (use in brief)

Kampung Melayu sits on the Ciliwung floodplain and appears repeatedly in Jakarta flood reports. However, the available records are scattered across PDFs and open-data tables, have mixed location precision (street, RW, sometimes only kelurahan), and do not say whether residents could reach a safe point during each event. Local responders therefore lack a transparent, reproducible way to decide **which RW to verify and prepare first**.

### 2.2 Study area framing

- **City (assignment unit):** Kota Administrasi Jakarta Timur, DKI Jakarta.
- **Analysis unit:** Kelurahan Kampung Melayu (Kec. Jatinegara), at **RW level** (MVP).
- **Network context area:** the kelurahan polygon buffered by **1,000 m**, because roads and safe points may lie just outside the kelurahan.
- **Warning:** "Cipinang Melayu" (Kec. Makassar) is a *different* kelurahan. Every filter must use both kelurahan = Kampung Melayu **and** kecamatan = Jatinegara.

### 2.3 What the product answers

1. Per RW: how many **distinct flood episodes** are recorded, across which years, with what maximum recorded depth, and how precise the location records are.
2. Per RW: a **verification-priority class** (HIGH / MEDIUM / VERIFY / NO_RECORD) with a human-readable reason.
3. Per RW and per event date: whether a route to a **verified** safe point exists on the road network after removing **verified** closed roads. If inputs are missing, the answer is **UNKNOWN**, never a claimed-safe route.
4. Data-quality transparency: unassigned records, coarse locations, missing depths, and years covered.

---

## 3. Product definition

### 3.1 Product

A QGIS plugin, **"KM Flood Priority"** (folder/package name `km_flood_priority`, Processing provider id `kmflood`). It adds:

- A **Processing provider** with 5 algorithms (§5).
- A **plugin menu** (`Plugins → KM Flood Priority`) with: *Run full pipeline…*, *Load sample data*, *Help*.
- Bundled **styles** (.qml) and **sample data** (the real processed inputs, if licensing allows; see §6.3).

### 3.2 Target users and usage

- **Primary user (for grading):** the lecturer. They install the plugin from a ZIP, click *Load sample data*, then *Run full pipeline…*, and see a styled priority map within minutes.
- **Secondary user (story):** a kelurahan or BPBD analyst who updates the event CSV and reruns the pipeline.

### 3.3 Non-goals (do NOT build)

- No web app, backend server, database server, or hosting.
- No hydrological or hydraulic modelling, no ML, no real-time feeds or APIs called from inside the plugin.
- No custom Qt dialogs or `.ui` files. Processing auto-generated dialogs are the UI.
- No RT-level analysis in v1.0. It is designed as a stretch (§13) and only enabled if RT polygons and RT-coded events are verified.
- No external Python dependencies inside the plugin (no geopandas, shapely, networkx, or pandas). Use only the stdlib and the QGIS API.

---

## 4. Technical constraints & platform

| Item | Decision |
|---|---|
| QGIS versions | Must run on **QGIS 3.44 LTR** (Qt5) **and QGIS 4.x** (Qt6). QGIS 4.0 shipped in March 2026 and is Qt6-only; 3.44 is the current 3.x LTR; 4.2 is planned as the first 4.x LTR. |
| `metadata.txt` | `qgisMinimumVersion=3.40`, `qgisMaximumVersion=4.99`. **Do not** add `supportsQt6`; that flag is deprecated and ignored. Compatibility is read from the version range. |
| Python | Whatever ships with QGIS (3.12+ on 3.44/4.x). Write code compatible with **Python 3.10+**. |
| Qt imports | Only via `qgis.PyQt.*`. Never `import PyQt5`/`PyQt6` directly. |
| Qt5/Qt6 compat rules | (1) Use fully scoped enums, e.g. `Qt.AlignmentFlag.AlignLeft`. (2) Use `exec()`, never `exec_()`. (3) `QAction`: `try: from qgis.PyQt.QtGui import QAction` / `except ImportError: from qgis.PyQt.QtWidgets import QAction`. (4) No compiled `resources.qrc`; load icons by file path. (5) Field types via `QMetaType.Type.*` (e.g. `QMetaType.Type.QString`, `Int`, `Double`, `QDate`), never `QVariant.String`. Centralize this in `qgis_glue/fields.py`. |
| CRS | Analysis and storage CRS: **EPSG:32748 (WGS 84 / UTM 48S)**, metres. All length and area computations happen in this CRS. Lat/lon inputs (EPSG:4326) are reprojected on import. |
| Output format | GeoPackage (`.gpkg`), with styles embedded via the `layer_styles` table. |
| License | **GPL-2.0-or-later** (QGIS plugin convention). Data keeps its own terms (§6.3). |
| OS | Must work on Windows (OSGeo4W/standalone installer). Students likely use Windows; all scripts must be OS-neutral (pathlib, no bash-only steps in the user path). |

---

## 5. Functional requirements — Processing algorithms

All algorithms live under provider `kmflood` (group names in brackets). Every algorithm:

- Has a `shortHelpString()` explaining inputs, outputs, and **claim limits** (FR-G1).
- Writes progress through `feedback.setProgress()` and readable messages through `feedback.pushInfo()`/`reportError()`.
- Is deterministic: same inputs and parameters produce identical outputs, apart from `run_id`/timestamp fields.
- Accepts file paths or loaded layers where sensible.

### FR-1 `kmflood:import_validate` — Import & validate events [1. Data]

**Purpose:** Turn raw transcribed and open-data records into one normalized, deduplicated events table plus a validation report.

**Inputs**

| Param | Type | Required | Notes |
|---|---|---|---|
| `EVENTS_CSV` | file (.csv, UTF-8) | yes | Canonical schema (§7.1). Multiple sources are concatenated beforehand by `scripts/merge_sources.py`, or use `EXTRA_EVENTS_CSV`. |
| `EXTRA_EVENTS_CSV` | file | no | Optional second CSV, same schema. |
| `SOURCES_CSV` | file | yes | Source registry (§7.2). Every `source_id` in events must exist here. |
| `RW_LAYER` | vector polygon | yes | Official RW polygons, already clipped to Kampung Melayu. Must contain an RW number field. |
| `RW_FIELD` | field of RW_LAYER | yes | Default `wadmrw`. |
| `KELURAHAN` | string | yes | Default `KAMPUNG MELAYU`. |
| `KECAMATAN` | string | yes | Default `JATINEGARA`. |
| `SOURCE_PRIORITY` | string | no | Comma-separated `source_id` order used to choose the canonical row when duplicates exist. Default: rows with depth win, then CSV order. |

**Processing rules**

1. **Schema check:** missing required columns → `ERROR`, algorithm fails with a clear message listing them.
2. **Filter:** keep rows where normalized `kelurahan` = `KELURAHAN` and `kecamatan` = `KECAMATAN` (case and whitespace insensitive, `KP.`→`KAMPUNG`). Report other rows as `INFO dropped_other_area` with a count.
3. **Date:** parse `event_date` as ISO `YYYY-MM-DD`. Unparseable → `ERROR` for that row (row excluded, still reported).
4. **RW normalization:** extract all integers from `rw_raw` ("RW 04", "04/05", "4 dan 5", "004"). Each integer must exist in `RW_LAYER`; otherwise `WARNING rw_not_in_layer` and the row stays with `rw_no = NULL`.
   - **Multiple RW in one row → explode** into one row per RW. `event_uid = <event_id>#<rw_no>`.
   - No RW → `rw_no = NULL`; `location_confidence` must be `KELURAHAN` or `UNKNOWN`, else `WARNING confidence_mismatch`.
5. **Depth:** parse `depth_raw` → `depth_min_cm`, `depth_max_cm`. Accept `"40"`, `"30-50"`, `"30 – 50 cm"`, `"0.5 m"`, `"50cm"`. Unparseable or blank → NULL plus `INFO depth_missing`. Values > 600 cm → `WARNING depth_implausible` (kept).
6. **Location confidence** must be one of `ADDRESS | RT | RW | RW_INFERRED | KELURAHAN | UNKNOWN` (§7.1). Invalid → `ERROR`.
7. **Deduplication:** rows with the same `(event_date, rw_no)` from **different** `source_id`s are duplicates. Keep one canonical row (per `SOURCE_PRIORITY`); others get `duplicate_of = <canonical event_uid>` and are excluded from counts but kept in the table.
8. **Sources:** every `source_id` must exist in `SOURCES_CSV` → else `ERROR`.

**Outputs**

| Output | Type | Content |
|---|---|---|
| `OUTPUT_EVENTS` | table (no geometry) | Normalized events (§7.3) |
| `OUTPUT_ISSUES` | table | Validation issues (§7.4) |
| `OUTPUT_SUMMARY` | dict in result + log | counts: rows_in, rows_kept, rows_dropped_area, exploded_rows, duplicates, rw_unassigned, depth_missing, years_covered (sorted list), errors, warnings |

**Failure policy:** the algorithm **fails** only on schema errors or when zero valid rows remain. Row-level errors exclude the row and are reported.

---

### FR-2 `kmflood:test_access` — Access test to safe points [2. Analysis]

**Purpose:** For each RW, and optionally per event date, determine whether a verified safe point is reachable on the road network after removing verified closed roads.

**Inputs**

| Param | Type | Required | Notes |
|---|---|---|---|
| `RW_LAYER` | vector polygon | yes | Same as FR-1 |
| `ROADS` | vector line | yes | OSM roads in the network context area (§2.2), with `osm_id`, `highway`, `name` |
| `SAFE_POINTS` | vector point | no | Schema §7.6. May be empty or omitted. |
| `CLOSURES_CSV` | file | no | Schema §7.5 |
| `EVENT_DATES` | string | no | Comma-separated ISO dates. Empty = baseline only. Special value `ALL` = every date in `CLOSURES_CSV`. |
| `USE_UNVERIFIED_SAFE_POINTS` | bool | no | Default **False** |
| `EXCLUDED_HIGHWAY` | string | no | Default `motorway,motorway_link,construction,proposed,raceway,bus_guideway` |
| `SNAP_TOLERANCE_M` | number | no | Default 50. Max distance from an origin or safe point to the nearest network node. |

**Method**

1. Reproject everything to EPSG:32748.
2. **Graph:** every polyline vertex becomes a node (coordinates rounded to 0.01 m so shared OSM vertices merge). Consecutive vertices form undirected edges weighted by Euclidean length, tagged with the source `osm_id` and normalized `name`. Exclude `EXCLUDED_HIGHWAY` types. Undirected is intentional: this is pedestrian evacuation, so one-way rules are ignored. Document this.
3. **Origins:** one origin per RW = `pointOnSurface()` of the RW polygon, snapped to the nearest node. If the nearest node is farther than `SNAP_TOLERANCE_M` → status `UNKNOWN`, reason `origin_off_network`.
4. **Targets:** safe points with `verified = Y`, or all of them if `USE_UNVERIFIED_SAFE_POINTS`. Snap as above; unsnappable points are reported and skipped.
5. **Baseline:** multi-source Dijkstra from all targets gives the distance and nearest target for every origin.
6. **Per event date:** remove edges whose `osm_id` matches a verified closure `road_ref` (`road_ref_type = OSM_ID`), or whose normalized name matches (`NAME`) for that date. Rerun Dijkstra.
7. **Status rules (normative):**

| Condition | `access_status` | `status_reason` |
|---|---|---|
| No usable targets | `UNKNOWN` | `no_verified_safe_points` |
| Origin off network | `UNKNOWN` | `origin_off_network` |
| Baseline row (no date) | `UNKNOWN` | `baseline_only_closures_not_assessed` (the baseline distance is still reported) |
| Date given, no verified closures for that date | `UNKNOWN` | `closures_not_verified_for_date` (baseline distance reported) |
| Date given, verified closures exist, path found | `REACHABLE` | `path_after_verified_closures` |
| Date given, verified closures exist, no path | `CUT_OFF` | `no_path_after_verified_closures` |

   If unverified safe points were used, append `;unverified_targets` to `status_reason` and set `targets_verified = N`.

**Outputs**

| Output | Type | Content |
|---|---|---|
| `OUTPUT_ACCESS` | table | §7.7, one row per (rw_no, event_date or `BASELINE`) |
| `OUTPUT_ROUTES` | line layer | Route geometry per row where a path exists (baseline and event) |
| `OUTPUT_GRAPH_STATS` | log/result | nodes, edges, removed_edges per date, connected components count |

**Implementation note:** the graph and Dijkstra live in **pure Python** (`core/network.py`, stdlib `heapq`) so they can be unit-tested without QGIS. The QGIS layer only extracts coordinates and attributes, then builds output layers.

---

### FR-3 `kmflood:compute_priority` — Verification-priority classification [2. Analysis]

**Purpose:** Aggregate the normalized events per RW and assign a transparent priority class.

**Inputs**

| Param | Type | Required | Default |
|---|---|---|---|
| `EVENTS` | table (FR-1 output) | yes | — |
| `RW_LAYER` | polygon | yes | — |
| `RW_FIELD` | field | yes | `wadmrw` |
| `ACCESS` | table (FR-2 output) | no | — |
| `SCENARIO_LAYER` | polygon/table with RW list | no | Optional Pantau Banjir scenario RW list (comparator only) |
| `EPISODE_GAP_DAYS` | int | no | **2** (0 disables episode merging) |
| `REC_HIGH` | int | no | **3** |
| `REC_MED` | int | no | **2** |
| `DEPTH_HIGH_CM` | int | no | **50** |

**Definitions (normative)**

- **Countable record:** `duplicate_of IS NULL` **and** `rw_no IS NOT NULL` **and** `location_confidence ∈ {ADDRESS, RT, RW, RW_INFERRED}`.
- **Episode:** per RW, sort the distinct countable `event_date`s. Dates whose gap from the previous date is ≤ `EPISODE_GAP_DAYS` belong to the same episode. `n_episodes` = number of episodes. This prevents "4 March" and "5 March 2025" from counting as two floods.
- `n_records` = countable records; `n_years` = distinct years; `max_depth_cm` = max of `depth_max_cm` over countable records (NULL if none); `depth_known_n` = countable records with depth.
- `low_conf_share` = share of countable records with `RW_INFERRED`.
- `access_worst` = the worst status across event rows from ACCESS for this RW (`CUT_OFF` > `UNKNOWN` > `REACHABLE`), or `NOT_RUN` if ACCESS was not supplied.

**Classification (normative, evaluated in order)**

```
if n_records == 0:                                     class = NO_RECORD
elif n_episodes >= REC_HIGH and (
        (max_depth_cm is not None and max_depth_cm >= DEPTH_HIGH_CM)
        or access_worst == "CUT_OFF"):                 class = HIGH
elif n_episodes >= REC_MED
        or (max_depth_cm is not None and max_depth_cm >= DEPTH_HIGH_CM)
        or access_worst == "CUT_OFF":                  class = MEDIUM
else:                                                  class = VERIFY

needs_field_check = (depth_known_n == 0) or (low_conf_share >= 0.5) or (access_worst in {"UNKNOWN","NOT_RUN"})
```

- `class_reason`: a generated sentence, e.g. `"3 episodes (2020–2025), max depth 120 cm, access UNKNOWN (no verified safe points)"`.
- `rank_in_class`: order by `n_episodes` desc, `max_depth_cm` desc (NULLs last), `last_date` desc.
- **Kelurahan-level records** (`rw_no` NULL) are never assigned to an RW. They are counted in a summary row `rw_no = NULL`, `rw_label = "Unassigned (kelurahan-level)"` in the table output only, without geometry.
- `scenario_flag`: `YES`/`NO` if SCENARIO_LAYER is given, else `NA`. **Never** used in classification.

**Outputs:** `OUTPUT_PRIORITY` (polygon, §7.8) and `OUTPUT_PRIORITY_TABLE` (same attributes, including the unassigned row, no geometry).

**Wording rule:** labels and help text say *"verification priority based on recorded events"*. Never say *"flood risk"*, *"flood-prone"*, or *"safe"*. `NO_RECORD` is labelled **"No recorded event (≠ safe)"**.

---

### FR-4 `kmflood:export_package` — Build result GeoPackage [3. Output]

**Inputs:** outputs of FR-1/2/3, `SOURCES_CSV`, input layers (RW, roads, safe points), `OUTPUT_GPKG` path.

**Behaviour:** write one GeoPackage containing the layers in §7.9. Embed the default style for each spatial layer (`saveStyleToDatabase`, default = true). Write `run_info` (parameters as JSON, plugin version, QGIS version, timestamp, `run_id` UUID) and `sources`. Overwrite only if the user confirms (Processing's standard output-overwrite behaviour).

**Acceptance:** opening the GPKG in a clean QGIS by drag-and-drop shows all layers already styled.

---

### FR-5 `kmflood:run_pipeline` — Full pipeline [0. Pipeline]

Runs FR-1 → FR-2 → FR-3 → FR-4 using child algorithms (`processing.run(..., context=context, feedback=feedback, is_child_algorithm=True)`). It exposes the union of the important parameters (with the same defaults) and an `OUTPUT_GPKG`, and adds the result layers to the project when run from the GUI. This is the main demo entry point.

---

### FR-G General plugin requirements

- **FR-G1** Each algorithm's help explains purpose, inputs, outputs, and the claim limits from §2.3/FR-3.
- **FR-G2** Menu actions: *Run full pipeline…* opens `processing.execAlgorithmDialog("kmflood:run_pipeline")`. *Load sample data* adds the bundled sample inputs, styled, and zooms to the kelurahan. *Help* opens the bundled `help/index.html` in the browser.
- **FR-G3** `unload()` removes all menu entries and the provider without errors. Reloading via Plugin Reloader must work.
- **FR-G4** No network access from the plugin at runtime.
- **FR-G5** All user-facing text is in English. Short Indonesian aliases may appear in help (e.g. "Import & validate (import_dan_validasi)") to link back to the research.

### 5.1 Non-functional requirements

| ID | Requirement | Check |
|---|---|---|
| NFR-1 | The full pipeline on real data completes in < 30 s on a normal laptop | Timed in Phase 4 |
| NFR-2 | Loads without errors or warnings in the QGIS Python console on 3.44 and 4.x | Phase 5 matrix |
| NFR-3 | `core/` has ≥ 90% line coverage | `pytest --cov` |
| NFR-4 | Deterministic outputs (except run_id/timestamp) | Test: run twice, compare attribute tables |
| NFR-5 | Reproducible from a clean clone using README steps | Phase 6 dry run by the *other* student |
| NFR-6 | Plugin ZIP < 10 MB | Packaging script asserts |

---

## 6. Data plan

### 6.1 Datasets

| ID | Dataset | Source | Role | Who | Status at spec time |
|---|---|---|---|---|---|
| D1 | **Rekap Kejadian Banjir Jakarta Timur 2025** (PDF) | PPID Kota Jakarta Timur (link in research §Sources #1) | Events 2025 with date, address, RT/RW, impact | **[H]** download and transcribe | Not yet downloaded |
| D2 | **Data Kejadian Bencana Banjir Provinsi DKI Jakarta** per year (CSV) | Satu Data Jakarta (`satudata.jakarta.go.id` / `data.jakarta.go.id`). The 2020 dataset has fields: city, kecamatan, kelurahan, rw, affected RT/KK/people, water height (cm), event date, inundation duration. | Multi-year events at RW level (fixes limitation #2) | **[H]** download each available year 2020–2025; **[A]** write the converter | Availability per year **must be verified**; the 2020 dataset is confirmed to exist |
| D3 | **RW polygons** (`ADMINISTRASI_AR_RW`) | DKI ArcGIS REST: `https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted/ADMINISTRASI_AR_RW/FeatureServer/18` — EPSG:32748, supports GeoJSON query, max 2000 records. Fields include `wadmkd` (kelurahan), `wadmkc` (kecamatan), `wadmrw` (RW number), `luaswh`. Basemap 1:1000 (2022); copyright **Dinas Cipta Karya, Tata Ruang, dan Pertanahan DKI Jakarta**; kelurahan boundaries are marked *indicative*. | Analysis units | **[A]** fetch script (run by [H] if the agent has no network) | Endpoint verified; Kampung Melayu filter **not yet run** |
| D4 | **Kelurahan boundary** | Same server: `Hosted/Batas_Administrasi_Kelurahan_DKI_Jakarta/FeatureServer` (discover the layer id). Cross-check: BIG administrative boundaries (research #6). | Study area outline, area check vs 47.83 ha | [A] / [H] | Endpoint listed, not yet inspected |
| D5 | **OSM roads + buildings** | Overpass API snapshot (preferred, small area) or Geofabrik Java extract (research #7) | Network for FR-2; context | [A] fetch script | — |
| D6 | **Safe points** (evacuation sites, capacity) | BPBD DKI / Kelurahan Kampung Melayu. Candidates may be seeded from OSM (school, mosque, kantor kelurahan, community hall) as `verified=N`. | Targets for FR-2 | **[H]** request and verify; [A] seeds candidates | Not available |
| D7 | **Road closures per event** | Derived by [H] from D1/D2 text (e.g. "Jl. Kebon Pal tergenang") and news or BPBD bulletins; each row has a source | FR-2 per-date test | **[H]** curate | Not available |
| D8 | **Pantau Banjir RW scenario list** (optional) | `pantaubanjir.jakarta.go.id` (research #3–5) | Comparator only | [H] optional | Download rights unclear; skip if unavailable |
| D9 | **RT polygons** (stretch only) | Same server: `Hosted/Batas_Administrasi_RT/FeatureServer` | §13 stretch | [A] inspect only | Listed, not inspected |

### 6.2 Data acquisition procedures

**D3/D4 — `scripts/fetch_admin_boundaries.py` [A]** (stdlib `urllib` only):

1. Query distinct names first, because the exact spelling is unknown:
   `.../FeatureServer/18/query?where=wadmkd LIKE '%MELAYU%'&outFields=wadmkd,wadmkc&returnDistinctValues=true&returnGeometry=false&f=json`
   Print the results. Pick the values where kecamatan = JATINEGARA.
2. Fetch the polygons:
   `.../query?where=wadmkd='<EXACT>' AND wadmkc='<EXACT>'&outFields=*&returnGeometry=true&outSR=32748&f=geojson`
   Note: the layer has Z values. Add `returnZ=false` and drop Z on import.
3. Save raw output to `data/raw/admin/rw_kampung_melayu_<YYYYMMDD>.geojson`, plus a `.meta.json` with the URL, query, retrieval timestamp, feature count, and SHA-256.
4. Repeat for the kelurahan layer → `kelurahan_kampung_melayu_<date>.geojson`.
5. **Validation (script asserts):** ≥ 1 RW feature; RW numbers unique; dissolved RW area vs kelurahan area within ±5%; kelurahan area vs 47.83 ha within ±15% (warn otherwise, do not fail); all geometries valid after `makeValid`.

If the agent environment blocks the network: produce the script, then mark the task **[H] run `python scripts/fetch_admin_boundaries.py`** and wait.

**D5 — `scripts/fetch_osm.py` [A]:** an Overpass query over the bbox of (kelurahan buffered 1000 m, transformed to EPSG:4326) for `way["highway"]` and `way["building"]`, plus candidate safe-point amenities (`amenity=school|place_of_worship|community_centre|townhall`, `office=government`). Use `out geom;` so geometry is inline. Convert to GeoJSON with the stdlib. Save the raw JSON, GeoJSON, and `.meta.json` (query, timestamp, Overpass endpoint). Attribution: "© OpenStreetMap contributors, ODbL".

**D1 — PPID transcription [A+H]:**
1. [H] downloads the PDF to `data/raw/ppid/`.
2. [A] tries text extraction (`pdfplumber`, run in a dev venv, **not** inside the plugin). If the PDF is scanned, [A] runs OCR (`ocrmypdf`/`tesseract`) and flags low confidence.
3. [A] pre-fills `data/interim/ppid_2025_draft.csv` (canonical schema) with **only** Kampung Melayu rows. Every row records `source_ref = "p.<page>"`.
4. [H] checks every row against the PDF, sets `location_confidence`, sets `verified=Y`, and saves `data/clean/events_ppid_2025.csv`. The agent never marks rows verified without user authorization.

**User-authorized PPID25 exception, 2026-10-12:** Raynald accepted Claude's independent
second check (pdftotext extraction, visual row checks and completeness check) and
explicitly instructed the agent to set all 28 rows to `verified=Y` and
`location_confidence=RW`. The report is `data/interim/ppid_2025_draft.check.md`.
Record `checked 2026-10-12 by Claude (delegated by Raynald)` in every row. This is
user-approved delegated AI review, not a claim that a human visually checked every row.
Preserve Nihil impact cells as NULL and source inconsistencies in notes. This exception
applies only to the explicitly accepted PPID25 rows; other sources remain unverified.

**D2 — Satu Data Jakarta [A+H]:** [H] downloads each year's CSV to `data/raw/satudata/`. [A] writes `scripts/convert_satudata.py`, which maps columns to the canonical schema (column names differ by year; keep a per-year mapping dict, fail loudly on unknown columns). Filter to Kampung Melayu + Jatinegara and set `location_confidence = RW`. Output goes to `data/clean/events_satudata_<year>.csv`.

**Merge — `scripts/merge_sources.py` [A]:** concatenates `data/clean/events_*.csv` → `data/processed/events_all.csv`, then validates the schema.

**D6/D7 — templates [A], content [H]:** [A] creates `data/templates/safe_points_template.csv` and `closures_template.csv`, plus `data/interim/safe_point_candidates_osm.csv` seeded from OSM with `verified=N`. [H] fills the real values with sources.

### 6.3 Licensing & attribution

- `docs/DATA_SOURCES.md` lists every dataset: publisher, URL, retrieval date, license or terms, and how it was used.
- **[H] decision before Phase 5:** may the DKI RW/kelurahan polygons and the processed events be **redistributed** in the repo and plugin ZIP?
  - If yes, or for academic use with attribution: ship `sample_data/km_inputs.gpkg`.
  - If unclear: do **not** ship them. Ship only the fetch scripts and instructions, and make *Load sample data* show a message pointing to the README.
- OSM: ODbL attribution in README, help, and figures.

### 6.4 Repository data layout

```
data/
  raw/          # untouched downloads + .meta.json (gitignored if license disallows)
  interim/      # drafts, OCR output, candidates (agent-generated, not verified)
  clean/        # human-verified CSVs (one per source)
  processed/    # merged CSV + inputs.gpkg (EPSG:32748) + results.gpkg
  templates/    # empty CSV templates with header + 1 commented example row
```

---

## 7. Data schemas (normative)

All CSVs are UTF-8, comma-separated, with a header row. Dates are ISO `YYYY-MM-DD`. Use empty strings for NULL.

### 7.1 Canonical events CSV (input to FR-1)

| Column | Type | Req | Description |
|---|---|---|---|
| `event_id` | str | yes | Unique within source, e.g. `PPID25-0007`, `SDJ2023-0142` |
| `source_id` | str | yes | FK to sources CSV |
| `source_ref` | str | yes | Page/row/sheet locator, e.g. `p.3`, `row 142` |
| `event_date` | date | yes | First date of the record |
| `kota` | str | yes | e.g. `JAKARTA TIMUR` |
| `kecamatan` | str | yes | e.g. `JATINEGARA` |
| `kelurahan` | str | yes | e.g. `KAMPUNG MELAYU` |
| `rw_raw` | str | no | As written in the source |
| `rt_raw` | str | no | As written in the source |
| `address_raw` | str | no | e.g. `Jl. Kebon Pal` |
| `depth_raw` | str | no | As written, e.g. `30-50 cm` |
| `affected_rt_count` | int | no | |
| `affected_kk` | int | no | |
| `affected_people` | int | no | |
| `duration_raw` | str | no | |
| `location_confidence` | enum | yes | `ADDRESS` (verified point), `RT`, `RW` (RW stated in source), `RW_INFERRED` (RW inferred by transcriber from street name), `KELURAHAN`, `UNKNOWN` |
| `verified` | Y/N | yes | Human-checked against the source |
| `notes` | str | no | |

### 7.2 Sources CSV

`source_id, title, publisher, url, retrieved_on, license_terms, format, coverage_years, notes`

### 7.3 Normalized events table (FR-1 output)

`event_uid, event_id, source_id, source_ref, event_date (date), year (int), kelurahan, kecamatan, rw_no (int|NULL), rt_raw, address_raw, depth_min_cm (int|NULL), depth_max_cm (int|NULL), affected_kk, affected_people, location_confidence, verified, duplicate_of (str|NULL)`

### 7.4 Validation issues table

`issue_id, event_id, row_number, field, severity (ERROR|WARNING|INFO), code, message`

Codes (fixed list): `missing_column, bad_date, rw_not_in_layer, confidence_mismatch, depth_missing, depth_unparsed, depth_implausible, unknown_source, invalid_confidence, dropped_other_area, duplicate`.

### 7.5 Closures CSV

`closure_id, event_date, road_ref_type (OSM_ID|NAME), road_ref, verified (Y/N), source_id, source_ref, notes`

### 7.6 Safe points (CSV with lon/lat, or point layer)

`sp_id, name, sp_type, capacity (int|NULL), lon, lat, verified (Y/N), source_id, source_ref, notes`

### 7.7 Access table (FR-2 output)

`rw_no, event_date (str: date or BASELINE), access_status (REACHABLE|CUT_OFF|UNKNOWN), status_reason, nearest_sp_id, route_length_m (real|NULL), baseline_length_m (real|NULL), targets_verified (Y/N), removed_edges (int)`

### 7.8 Priority layer (FR-3 output, polygon EPSG:32748)

`rw_no, rw_label, kelurahan, n_records, n_episodes, n_years, first_date, last_date, max_depth_cm, depth_known_n, max_affected_kk, low_conf_share, access_worst, priority_class, needs_field_check (Y/N), class_reason, rank_in_class, source_refs (str, ";"-joined), scenario_flag, run_id`

### 7.9 Result GeoPackage layers (FR-4)

| Layer | Geometry | Notes |
|---|---|---|
| `rw_priority` | Polygon | Styled (§8.3) |
| `priority_table` | none | Includes the unassigned row |
| `events` | none | Normalized events |
| `validation_issues` | none | |
| `access_by_rw` | none | |
| `access_routes` | LineString | Styled by status |
| `safe_points` | Point | Styled verified vs unverified |
| `roads` | LineString | Context, light style |
| `kelurahan_boundary` | Polygon | Outline style |
| `sources` | none | Copy of the sources CSV |
| `run_info` | none | One row: run_id, timestamp, plugin_version, qgis_version, parameters_json, years_covered |

---

## 8. Architecture

### 8.1 Repository layout

```
<repo-root>/
├─ README.md                    # §10
├─ LICENSE                      # GPL-2.0-or-later
├─ EXECUTION_SPEC.md            # this file
├─ docs/
│  ├─ PROGRESS.md               # phase log (agent updates)
│  ├─ DATA_SOURCES.md
│  ├─ METHODOLOGY.md            # human-readable version of §5/§7 rules
│  ├─ USER_GUIDE.md             # install + run with screenshots
│  ├─ TECHNICAL_BRIEF.md        # draft content (§11)
│  └─ figures/                  # generated PNGs for brief/README
├─ data/                        # §6.4
├─ scripts/
│  ├─ fetch_admin_boundaries.py
│  ├─ fetch_osm.py
│  ├─ convert_satudata.py
│  ├─ extract_ppid_pdf.py       # dev-only, uses pdfplumber
│  ├─ merge_sources.py
│  ├─ build_inputs.py           # PyQGIS standalone: clip/reproject → data/processed/inputs.gpkg
│  ├─ run_pipeline_cli.py       # qgis_process wrapper for reproducible runs
│  ├─ render_figures.py         # PyQGIS headless map export → docs/figures
│  └─ package_plugin.py         # builds dist/km_flood_priority-<ver>.zip
├─ km_flood_priority/           # THE PLUGIN (zip root folder)
│  ├─ __init__.py               # classFactory(iface)
│  ├─ metadata.txt
│  ├─ plugin.py                 # menu actions, provider registration
│  ├─ provider.py               # QgsProcessingProvider (id "kmflood")
│  ├─ algorithms/
│  │  ├─ import_validate.py
│  │  ├─ test_access.py
│  │  ├─ compute_priority.py
│  │  ├─ export_package.py
│  │  └─ run_pipeline.py
│  ├─ core/                     # PURE PYTHON — no qgis imports allowed
│  │  ├─ schema.py              # enums, column specs, dataclasses
│  │  ├─ normalize.py           # rw/depth/date/name parsing, explode, dedupe
│  │  ├─ episodes.py            # episode grouping
│  │  ├─ priority.py            # aggregation + classification + reasons
│  │  ├─ network.py             # graph build, closures, multi-source Dijkstra, path
│  │  └─ validation.py          # issue objects, summary
│  ├─ qgis_glue/
│  │  ├─ fields.py              # Qt5/Qt6-safe QgsField factory
│  │  ├─ io.py                  # layer/CSV ↔ core dataclasses
│  │  └─ styles.py              # apply .qml, save to gpkg
│  ├─ styles/                   # *.qml
│  ├─ help/index.html
│  ├─ sample_data/              # only if license OK (§6.3)
│  ├─ icon.svg
│  └─ LICENSE
├─ tests/
│  ├─ unit/                     # pytest, no QGIS
│  ├─ qgis/                     # pytest with qgis.testing.start_app
│  └─ fixtures/                 # SYNTHETIC ONLY (kelurahan "TESTVILLE")
├─ requirements-dev.txt         # pytest, pytest-cov, pdfplumber, ruff
└─ .github/workflows/ci.yml
```

**Hard rule:** `km_flood_priority/core/` must not import `qgis` or `PyQt`. CI enforces this with a grep test.

**`metadata.txt` (template):**
```ini
[general]
name=KM Flood Priority
qgisMinimumVersion=3.40
qgisMaximumVersion=4.99
description=Verification-priority and safe-point access analysis for recorded floods in Kelurahan Kampung Melayu, Jakarta Timur.
about=Imports and validates flood event records, groups them into episodes per RW, classifies RW by verification priority, tests network access to verified safe points under verified road closures, and exports a styled GeoPackage. Results describe recorded events, not flood risk.
version=1.0.0
author=<STUDENT_A>, <STUDENT_B>
email=<EMAIL>
repository=<REPO_URL>
tracker=<REPO_URL>/issues
homepage=<REPO_URL>
hasProcessingProvider=yes
category=Analysis
tags=flood,jakarta,priority,network analysis,evacuation,processing
icon=icon.svg
experimental=False
```

### 8.2 Data flow

```
PPID PDF ──extract+[H] verify──► events_ppid_2025.csv ─┐
Satu Data CSVs ──convert──────► events_satudata_*.csv ─┼─merge─► events_all.csv ─┐
                                                        │                          ▼
DKI ArcGIS RW/Kel ──fetch──► raw geojson ──build_inputs──► inputs.gpkg ──► FR-1 import_validate
OSM Overpass ──fetch──► raw json ─────────────────────────┘                        │
safe_points.csv, closures.csv ([H]) ─────────────────────────► FR-2 test_access ◄──┤
                                                                       │            │
                                                     FR-3 compute_priority ◄────────┘
                                                                       │
                                                     FR-4 export_package ─► results.gpkg ─► figures, brief
```

### 8.3 Styles (bundled .qml)

- `rw_priority`: categorized on `priority_class` — HIGH `#d7191c`, MEDIUM `#fdae61`, VERIFY `#ffffbf` with diagonal hatch, NO_RECORD `#d9d9d9` with dot pattern. Legend labels: "High verification priority", "Medium", "Needs verification (weak evidence)", "No recorded event (≠ safe)". Labels: `rw_label` + `n_episodes`. Dashed outline where `needs_field_check = 'Y'`.
- `access_routes`: green solid for REACHABLE event routes, grey dashed for BASELINE, red for CUT_OFF origins (origin markers).
- `safe_points`: filled marker if verified, hollow if not, labelled "(unverified)".
- `kelurahan_boundary`: thick dark outline, no fill.

---

## 9. Quality: testing strategy

### 9.1 Unit tests (`tests/unit`, run with plain `pytest`)

Minimum cases. Each one is a test function.

- **normalize:** `"RW 04"→[4]`, `"04/05"→[4,5]`, `"4 dan 5"→[4,5]`, `""→[]`. Depth: `"30-50 cm"→(30,50)`, `"0.5 m"→(50,50)`, `"40"→(40,40)`, `"tinggi"→(None,None)`. Kelurahan names `"Kp. Melayu"` / `" KAMPUNG  MELAYU "` match. Explode creates `event_uid` with the `#rw` suffix.
- **dedupe:** two sources with the same date and RW → one canonical; the one with depth wins; `duplicate_of` is set.
- **episodes:** dates [2025-03-04, 2025-03-05, 2025-07-07] with gap 2 → 2 episodes; gap 0 → 3.
- **priority:** one fixture per class (HIGH via depth, HIGH via CUT_OFF, MEDIUM via recurrence only, MEDIUM via depth only, VERIFY, NO_RECORD). Kelurahan-level rows never reach an RW. `needs_field_check` logic. Ranking order with NULL depths.
- **network:** a hand-built grid graph: shortest distance correct; multi-source picks the nearest target; removing a bridge edge → CUT_OFF; an origin beyond the snap tolerance → UNKNOWN; shared vertices merge at 0.01 m rounding.
- **status rules:** every row of the FR-2 status table has a test.
- **purity:** a test greps `core/` for `import qgis|PyQt` → must find nothing.

### 9.2 QGIS integration tests (`tests/qgis`)

Run inside Docker images of **QGIS 3.44** and a **QGIS 4.x** image. Check the exact tags on Docker Hub (`qgis/qgis`) before relying on them, and record the tags used in CI.

- The provider loads; all 5 algorithm ids exist.
- `run_pipeline` on the synthetic fixtures produces a GPKG with every layer in §7.9, with correct feature counts and styles present in `layer_styles`.
- Field types are correct (int/real/date/string).
- Determinism: run twice → identical attributes, excluding run_id/timestamp.
- CLI path: `qgis_process plugins enable km_flood_priority` then `qgis_process run kmflood:run_pipeline -- ...` exits 0.

Headless example (adapt the tag):
```
docker run --rm -v "$PWD":/repo -w /repo qgis/qgis:<TAG> \
  bash -c "pip install pytest && xvfb-run -a python3 -m pytest tests/qgis -q"
```

### 9.3 Manual acceptance (human, on the students' own QGIS)

A checklist in `docs/USER_GUIDE.md`, executed on Windows with QGIS 3.44 LTR, plus QGIS 4.x if installed:
1. Plugins → Manage and Install → *Install from ZIP* → no error.
2. The menu shows 3 actions; the Processing Toolbox shows "KM Flood Priority" with 5 algorithms.
3. *Load sample data* shows the styled map.
4. *Run full pipeline…* with the defaults completes; result layers are added and styled.
5. Open the result GPKG in a fresh project → styled.
6. Disable and re-enable the plugin → no errors.
7. Take the screenshots listed in §11.3.

### 9.4 CI (`.github/workflows/ci.yml`)

Two jobs: (1) `unit` on ubuntu-latest + Python 3.12: ruff, pytest with coverage ≥ 90% on `core/`; (2) `qgis` in the QGIS 3.44 container running `tests/qgis`. Optionally a third job for QGIS 4.x, allowed to fail only if the image is unavailable, and documented.

---

## 10. Documentation deliverables

### 10.1 README.md (required sections, in order)

1. Title, one-paragraph summary, screenshot of the styled map.
2. **Assignment context** (course, group members, study area).
3. **Quick start for graders:** download the release ZIP → install from ZIP → *Load sample data* → *Run full pipeline…*. Max 6 steps, with screenshots.
4. **What it computes:** a short version of FR-1..FR-3, the class rules table, and the claim limits.
5. **Reproduce from scratch:** environment, data download (which steps need a human), `fetch_*` scripts, `build_inputs.py`, `run_pipeline_cli.py`, expected outputs and checksums.
6. **Data sources & licenses** (link to `docs/DATA_SOURCES.md`) with OSM attribution.
7. **Limitations** (§1.3 + access UNKNOWN semantics).
8. **Development:** run tests, package the plugin, compatibility matrix tested.
9. License.

### 10.2 Other docs

`docs/METHODOLOGY.md` (rules in prose plus a flow figure), `docs/USER_GUIDE.md` (§9.3 checklist with screenshots), `docs/DATA_SOURCES.md` (§6.3), `km_flood_priority/help/index.html` (a condensed user guide).

---

## 11. Technical Brief (2 pages) — content plan

The agent drafts `docs/TECHNICAL_BRIEF.md` with **real numbers from the Phase 4 run**. The humans finalize the layout in Word or Google Docs and export to PDF. **Hard limit: 2 pages A4.** Ask the lecturer whether the brief should be English or Indonesian (default English, matching the guideline).

### 11.1 Section budget

| Section (required by guideline) | Budget | Content |
|---|---|---|
| Problem definition | ~80 words | §2.1, tightened |
| Study area | ~50 words + small locator map | Jakarta Timur → Kampung Melayu (47.83 ha), RW count from data |
| Data sources | compact table (5–7 rows) | D1–D7 used, year coverage, precision |
| GIS methodology | ~120 words + 1 flow figure | normalize → episodes → classify; network access with verified-only rule; EPSG:32748 |
| Key spatial findings | ~120 words + **main map** | ≥ 3 quantified findings (§11.2) |
| Proposed solution / recommendation | ~100 words | Field verification order (HIGH first); drainage/preparedness checks on recurrent RW; collect safe points and closures to turn UNKNOWN into tested access; improve location reporting (RW/RT on every record) |
| Product | 1 screenshot + repo URL + release URL | Plugin running in QGIS |

### 11.2 Findings template (fill with real values, never guesses)

1. "Across `<years_covered>`, `<k>` of `<N>` RW have ≥ `<REC_HIGH>` recorded flood episodes; RW `<list>` rank highest."
2. "`<x>`% of records lack depth and `<y>` records are only located at kelurahan level, which limits RT-level conclusions."
3. Access: either "With `<m>` verified safe points and verified closures for `<dates>`, RW `<list>` had no path…" **or** "Access is UNKNOWN for all RW because no verified safe points or closures are available; baseline routes to `<n>` candidate points average `<d>` m." The second version is an honest, valid finding.
4. Optional: agreement/disagreement with the Pantau Banjir scenario RW list.

### 11.3 Figures & screenshots (generated by `scripts/render_figures.py` where possible)

- F1 Locator map (Jakarta Timur → kelurahan).
- F2 Main map: `rw_priority` + routes + safe points + legend + scale bar + north arrow + attribution.
- F3 Method flow diagram (simple boxes; can be drawn in draw.io).
- S1 QGIS screenshot: Processing Toolbox with the provider plus the pipeline dialog.
- S2 QGIS screenshot: result map with the attribute table of `rw_priority` open.

---

## 12. Execution plan (phases)

### Phase 0 — Setup & alignment
- [A] Create the repo structure (§8.1), LICENSE, `.gitignore`, `requirements-dev.txt`, empty docs, and `docs/PROGRESS.md`.
- [A] Create CSV templates (§7) in `data/templates/`.
- [H] Confirm with the lecturer (short message): study area framing (§2.2), QGIS plugin as the product, and brief language. **Proceed in parallel; adjust if the lecturer objects.**
- **Accept when:** the repo builds; `pytest` runs (0 tests OK); templates exist.

### Phase 1 — Data acquisition *(parallel with Phase 2)*
- [A] Write `fetch_admin_boundaries.py` and `fetch_osm.py`; run them if the network allows, otherwise hand them to [H].
- [H] Download D1 (PPID PDF) and D2 (Satu Data CSVs, every available year 2020–2025). Record the URL and date in `sources.csv`.
- [A] `extract_ppid_pdf.py` → draft CSV; `convert_satudata.py` → clean CSVs for Satu Data.
- [H] Verify the PPID draft row by row → `data/clean/events_ppid_2025.csv`.
- [A] Seed `safe_point_candidates_osm.csv` (`verified=N`).
- [H] Request safe points and capacity from Kelurahan/BPBD (deadline: before Phase 4; if no response, proceed with UNKNOWN). Curate closures from the event text with sources.
- [A] `merge_sources.py`, then `build_inputs.py` → `data/processed/inputs.gpkg` (layers: `rw`, `kelurahan_boundary`, `roads`, `buildings`, `safe_points`) in EPSG:32748.
- **Accept when:** inputs.gpkg exists and the validation asserts in §6.2 pass; `events_all.csv` passes the schema check; `DATA_SOURCES.md` is filled in; `years_covered` is known.

### Phase 2 — Core library (pure Python)
- [A] Implement `core/*` exactly per §5 and §7, with tests from §9.1 written first (TDD).
- **Accept when:** all unit tests pass; coverage ≥ 90%; the purity test passes.

### Phase 3 — QGIS plugin
- [A] `metadata.txt`, `__init__.py`, `plugin.py`, `provider.py`, `qgis_glue/*`, the 5 algorithms, styles, help, icon.
- [A] QGIS integration tests (§9.2) on synthetic fixtures in 3.44 and 4.x containers.
- **Accept when:** the integration tests pass on 3.44 (and on 4.x, or the reason it was not run is documented); the plugin ZIP installs in a container QGIS via `qgis_process plugins enable`.

### Phase 4 — Real-data run & findings
- [A] Run `run_pipeline_cli.py` on the real inputs → `data/processed/results.gpkg`.
- [A] Sanity report in `docs/PROGRESS.md`: counts per class; top 5 RW with reasons; validation issue counts; timings (NFR-1); a sensitivity table (REC_HIGH ∈ {2,3,4} × DEPTH_HIGH ∈ {30,50,80}) showing which RW change class.
- [A+H] Review the results together. If something looks wrong, trace it to the source row; never tweak thresholds to make a "nicer" map without recording why in METHODOLOGY.md.
- **Accept when:** results.gpkg opens styled; the findings in §11.2 can be filled with real numbers.

### Phase 5 — Packaging, docs, figures
- [H] Licensing decision (§6.3) → include or exclude `sample_data/`.
- [A] `package_plugin.py` → `dist/km_flood_priority-1.0.0.zip` (excludes tests, `__pycache__`, `.pyc`; asserts < 10 MB; zip root folder = `km_flood_priority/`).
- [A] `render_figures.py` → F1, F2 in `docs/figures/`.
- [A] Write the README, METHODOLOGY, USER_GUIDE, DATA_SOURCES, and help HTML.
- [A] CI green; tag `v1.0.0`; create a **GitHub Release** with the ZIP attached.
- **Accept when:** CI is green; the release exists; the README quick start works from the release ZIP.

### Phase 6 — Brief, final QA, submission
- [A] Draft `docs/TECHNICAL_BRIEF.md` with real numbers.
- [H] Manual acceptance (§9.3) on a Windows laptop: install from the release ZIP and take screenshots S1/S2.
- [H] **Reproducibility dry run:** the student who did *not* run Phase 4 follows the README from a clean clone.
- [H] Lay out the 2-page brief, export PDF, check the page count, and submit the brief PDF + repo URL + release URL.
- **Accept when:** every item in §14 is checked.

---

## 13. Stretch goals (only after §14 is fully green)

1. **Building-based access:** origins = residential building centroids per RW; report the share of buildings with a path (`buildings` layer already fetched). Note that OSM buildings are not equal to inhabited houses.
2. **RT level:** inspect D9; if RT polygons exist for Kampung Melayu **and** ≥ 30% of records carry RT codes, add `UNIT_LEVEL = RW|RT` to FR-1/FR-3. Otherwise document why not.
3. **Print layout template** (.qpt) bundled with the plugin for one-click map export.

---

## 14. Final Definition of Done (submission checklist)

- [ ] Plugin ZIP installs from ZIP on QGIS 3.44 LTR (Windows) with no errors; tested on QGIS 4.x or documented why not.
- [ ] 5 Processing algorithms work; the full pipeline produces a styled result GPKG.
- [ ] Results are based on real, human-verified data; synthetic data appears only in tests.
- [ ] No output or document uses "flood-prone", "risk", or "safe" claims beyond §2.3; NO_RECORD is labelled "≠ safe"; access without verified inputs is UNKNOWN.
- [ ] Repo: README per §10.1, DATA_SOURCES with attribution, METHODOLOGY, USER_GUIDE, LICENSE.
- [ ] Clean-clone reproduction succeeded by the second student.
- [ ] CI green; tag `v1.0.0`; GitHub Release with the plugin ZIP.
- [ ] Technical Brief: exactly ≤ 2 pages, contains all 7 required items, ≥ 3 quantified findings, product screenshot + repo URL + release URL.
- [ ] `docs/PROGRESS.md` final entry summarizes versions tested and known limitations.

---

## 15. Risk register

| Risk | Likelihood | Impact | Mitigation / fallback |
|---|---|---|---|
| PPID PDF unavailable or scanned | Med | Med | OCR path; if unavailable, Satu Data years alone still support the method. Record the gap. |
| Satu Data years missing for Kampung Melayu | Med | High | Use whatever years exist plus PPID 2025; report `years_covered` honestly. The method is unchanged. |
| ArcGIS endpoint down or renamed | Low–Med | High | Save raw downloads immediately (`data/raw`); fallback to the BIG kelurahan boundary + a manually digitized RW from the Pantau Banjir RT map, marked lower confidence. |
| Redistribution not allowed | Med | Low | Ship scripts only; *Load sample data* explains how to fetch. |
| No safe points / closures | High | Low | Designed behaviour: UNKNOWN plus baseline distances to unverified candidates (clearly labelled). This is a valid finding and recommendation. |
| Qt6 incompatibility | Med | High | §4 compat rules; CI on both versions; no custom widgets. |
| RW numbering mismatch (e.g. "004" vs "4") | High | Med | Integer normalization in FR-1; the `rw_not_in_layer` warning surfaces leftovers. |
| Duplicate events across sources inflate recurrence | High | High | FR-1 dedupe plus FR-3 episode merging. |
| Lecturer requests a different area or app type | Low | High | Phase 0 confirmation early; core logic is area-agnostic (parameters for kelurahan/kecamatan). |

---

## 16. Glossary

- **RW / RT** — Rukun Warga / Rukun Tetangga, the neighbourhood units below kelurahan.
- **Episode** — a group of recorded flood dates in one RW separated by ≤ `EPISODE_GAP_DAYS`.
- **Verification priority** — the order in which RW should be field-checked and prepared, derived from recorded events. It is not a hazard or risk estimate.
- **Verified** — a human checked the value against a cited source (`verified = Y`).
- **Baseline route** — the shortest path on the full network with no closures applied; informative only.
