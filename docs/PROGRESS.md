# Execution progress

## 2026-10-12 — Phase 0

- Read `docs/EXECUTION_SPEC.md` v1.0; implementation follows its phase gates.
- Confirmed authors with the user: Raynald Arvan Lim, Alden Viriya Tanudjaja,
  and Moses Handoyo. The actual group has three students; lecturer confirmation
  is pending because the assignment/spec says two.
- Created the package structure, developer environment configuration, CSV templates,
  GPL-2.0-or-later license, and data handling rules. Plugin loading is not yet implemented.
- No real inputs, verified events, findings, or map screenshots exist yet.
- Local Python: 3.12. Docker CLI is installed, but the Linux engine is not running.
- Human tasks: lecturer alignment, PPID/Satu Data download and verification,
  safe-point/closure verification, and the redistribution decision.
- Git policy: local commits only; no push, remote release, or publication.
- Phase 0 checks: Python compile succeeds; pytest executes with zero tests (exit 5),
  explicitly permitted by the Phase 0 acceptance criterion. CSV templates are present.

## 2026-10-12 — Phase 2 accepted

- Implemented all six pure Python core modules: schemas, normalization/validation,
  cross-source deduplication, episode grouping, priority/ranking, and pedestrian network access.
- Tests were written before each implementation; initial missing-module failures were
  expected TDD checks. All 96 unit cases pass on Python 3.12.8; core line coverage is 99.18%.
- Ruff lint and formatting pass. The AST-based purity test confirms no QGIS or Qt imports.
- Tests cover all class rules and all six access-status rows, source priority, unassigned
  rows, parallel road edges, closure dates/names, rounding, and deterministic outputs.
- Added the unit CI workflow with the 90% coverage gate. CI has not run remotely because
  no push is authorized. The QGIS job is deferred to Phase 3 with the plugin implementation.
- Summary counters: `rows_kept` counts valid source rows before explosion;
  `exploded_rows` counts output rows originating from multi-RW source rows. Retained table
  rows (including duplicates) determine unassigned/depth-missing counts and years covered.
- Source-level deduplication preserves rows from the canonical source, as same-source rows
  are not duplicates under FR-1; other sources point to the selected canonical event UID.
- The unassigned table row is excluded from RW ranking and episode counts; its VERIFY
  marker requests checking and is not a spatial priority classification.
- Phase 1 proceeds in parallel. Phase 3 remains gated by real `inputs.gpkg`, validated
  `events_all.csv`, source metadata, and known year coverage. No real-data finding is claimed.

## 2026-10-12 — Phase 1 inputs prepared; event review pending

- The user started Docker Desktop. Development runs use QGIS 3.44.15-Solothurn /
  Python 3.12.3 from `qgis/qgis:3.44.15-noble`, image digest
  `sha256:497c1629c68ced7735dc25c25e33ada0040f5144099e92b78fae978bdf233466`.
  QGIS 4.x and Windows plugin acceptance are not tested yet.
- Added acquisition, explicit Satu Data mapping, PPID extraction, merge validation,
  and QGIS metric-input preparation scripts. Raw snapshots and checked CSVs cannot
  be silently overwritten. All six command help checks pass without QGIS imports.
- Acquired official administrative data: 9 RW (01–09), one kelurahan boundary.
  Metric boundary area is 47.989568 ha; dissolved RW/kelurahan area ratio is
  1.000000000008, meeting the ±5% gate; all prepared geometries are valid.
- Derived the exact 1000 m metric buffer bbox before the OSM query. Clipped context
  contains 3,154 road and 34,617 building features; 440 candidate safe points remain N.
  `data/processed/inputs.gpkg` has five EPSG:32748 layers and was reopened and checked
  in QGIS. Its SHA-256 is `a4be6c4a90bee76b5df32b30961b242b16a5c0604b2667a8e9e63ef410d7305a`.
  The final preparation script was also rerun successfully to an independent `.tmp`
  package with the same layer counts, checking every post-clip geometry and CRS.
- The user downloaded the PPID 2025 PDF. Inspected all target-area tables visually,
  including headerless continuation pages. The 18-column profile excludes the monthly
  summary, handles April numeric impact cells and June RW labels without equals signs.
  Full extraction yields 28 source rows / 56 normalized RW rows; zero schema errors
  and no missing depths. The initial 15-row shortlist was incomplete and superseded.
- Every PPID row remains `verified=N`, `location_confidence=UNKNOWN`. References
  include viewer page, table, source NO and original date. Shared impact totals are
  not allocated to individual RWs; Nihil remains NULL; source times do not imply a
  next-day duration or verified road closure. A review guide is beside the draft.
- Source registry contains DKI-RW, DKI-KEL, OSM-20261012 and PPID25 with checksums.
  Downloaded real datasets remain gitignored pending redistribution confirmation.
- Validation: 111 unit tests, Ruff lint, formatting and whitespace checks pass;
  core coverage remains 99.18%. Phase 1 is not yet
  accepted: human PPID verification, Satu Data availability per year, the final merged
  event table and accepted year coverage remain pending. Phase 3 has not started.
- All commits remain local; no push has been performed.

## 2026-10-12 — Satu Data exports acquired and audited

- Continued independent Phase 1 work while awaiting the user's PPID row verification.
  The national catalog exposed direct publisher export URLs that were not visible
  in the text-only Satu Data page. Downloaded four immutable CSV snapshots and metadata.
- Exact target filtering found 51 rows in the 2020-labeled export, 6 in 2023, 9 in
  2024, and 9 in the general export whose publisher periods include 2025 and 2026.
  Raw row totals are 902, 194, 260, and 392 respectively.
- Added a reproducible source-granularity audit. The 2020 target rows have 33 date
  transcription issues, 18 period/date conflicts, and 36 RW=0 cases (overlapping).
  The other exports lack exact event dates and RW codes and remain context only.
  No date/RW cross product or synthetic calendar day was created; no Satu Data event
  table was published. Eligible exports for 2021/2022 remain unresolved, not proven absent.
- Fixed repeated UTF-8 BOM handling in publisher CSV headers. Added a converter guard
  against assigning affected-RW counts to `rw_raw`. Regression cases use TESTVILLE.
- The independent acquisition audit does not satisfy the human PPID check required
  in §6 D1. Phase 1 remains pending that check, source-use decisions and events_all.csv;
  Phase 3 has not started. No data verification flag was changed.
- Validation: all 116 unit cases pass; core coverage 99.18%; lint and formatting pass.
  Commit remains local; no push.

## 2026-10-12 — PPID accepted by user; Phase 1 working set accepted

- Raynald explicitly accepted Claude's independent second check of all 28 rows and
  instructed Y/RW flags. The report describes separate pdftotext extraction, visual
  checks and completeness checks. This is user-authorized delegated AI review, not
  direct human row checking; the exception is recorded in the execution specification.
- Saved `data/clean/events_ppid_2025.csv` with the exact provenance note
  `checked 2026-10-12 by Claude (delegated by Raynald)` in every row. The only changed
  fields relative to the original draft are verified, location_confidence and notes.
  The original draft and source PDF remain unchanged. A checksum review receipt
  beside the clean CSV records source, draft, report and clean-file identities.
- Retained all three Nihil affected KK/people pairs as NULL (not zero). Added source
  inconsistency notes on p.14 NO 15 / 6 July and p.15 NO 20 / 7 July: evacuation totals
  58 KK/184 people and 104 KK/352 people exceed affected totals 44 KK/125 people.
  Kept JUMLAH TERDAMPAK values unchanged as instructed.
- Ran `merge_sources.py`: 28 source rows / 56 normalized RW rows, all Y/RW; zero
  schema errors, warnings or duplicates; zero missing depths; accepted coverage [2025].
  Source inconsistencies remain in notes and are not concealed by the schema result.
- Phase 1 acceptance criteria are met for the current PPID-only working set: validated
  inputs.gpkg, schema-valid events_all.csv, documented sources and known event coverage.
  Satu Data exports remain excluded with documented granularity/conflict limitations;
  2021/2022 availability remains unresolved. No multi-year finding is claimed.
- Code is unchanged by this data acceptance; the previous 116 passing tests and 99.18%
  core coverage remain the latest unit result. Data integrity was checked by comparing
  every clean row against the draft/report and by running the real import validator.
- Downloaded/accepted datasets remain local and gitignored pending redistribution
  confirmation. Documentation is committed locally; no push.

## 2026-10-13 — Phase 3 accepted

- Implemented the kmflood provider, all five algorithms, idempotent plugin/menu
  lifecycle, Qt5/Qt6 field and IO adapters, five bundled QML styles, and offline
  child-algorithm pipeline. Outputs include every required package layer and source
  verification/inconsistency notes in the added events.notes field.
- All spatial inputs are transformed to EPSG:32748. RW origin points use pointOnSurface;
  safe points and closures marked verified require cited source fields. Missing evidence
  remains UNKNOWN. Scenario membership never changes the priority class.
- Export writes a temporary package, embeds default styles, closes the SQLite reader,
  checkpoints WAL, then atomically replaces the destination only with explicit OVERWRITE.
  Qt6 style-result enums are inspected by their integer value; Success is zero.
- Integration acceptance: **12/12 pass in each runtime**. Covers five algorithm IDs,
  all 11 package layers, typed dates/integers and NULL, default styles reopened from
  the package, deterministic tables, protected existing output, CRS reprojection,
  retained provenance, row/schema errors, unverified opt-in, citation rejection,
  plugin menu reload, ZIP activation and qgis_process pipeline execution.
- Runtime 1: qgis/qgis:3.44.15-noble, QGIS 3.44.15-Solothurn, Qt 5.15.13, Python 3.12.3;
  digest sha256:497c1629c68ced7735dc25c25e33ada0040f5144099e92b78fae978bdf233466.
- Runtime 2: qgis/qgis:4.2.3-trixie, QGIS 4.2.3-Belém do Pará, Qt 6.8.2, Python 3.13.5;
  digest sha256:56c69c92e316aa679e5c30ebf7fcfd89fd1124ec728106ec0cced1c71a28d877.
- The 116 core/acquisition unit cases still pass with 99.18% core coverage; Ruff
  lint/format pass. Both exact QGIS tags are in the CI matrix. Remote CI is unrun
  because no push is authorized. All integration containers ran with network disabled.
- Added a reproducible ZIP builder and isolated-profile qgis_process wrapper, with
  optional offline Docker execution. Local ZIP is 59,982 bytes, excludes bytecode,
  tests and real sample datasets. Human redistribution confirmation remains pending.
- Windows manual install, native UI screenshots and independent clean-clone acceptance
  are still pending; automated interface tests are not described as human UI testing.
- The earlier automatic approval-review usage failure expired; the previously blocked
  PPID25 registry provenance update was completed after the reported reset time.
- Commit is local only. Phase 4 now proceeds on the accepted 2025 working set.

## 2026-10-13 — Phase 4 accepted by Raynald

- Real input run: `scripts/run_pipeline_cli.py --docker --overwrite`, offline
  QGIS 3.44.15; 4.048 seconds for the child pipeline. The measured container time
  passes the 30-second target; native Windows timing is pending. Package has all
  eleven application layers/tables, default styles, provenance and run metadata.
- Counts: HIGH=2, MEDIUM=2, VERIFY=0, NO_RECORD=5 across nine RW. PPID 2025 only:
  28 source rows → 56 normalized RW rows; zero schema errors/warnings/duplicates,
  zero missing depth and zero unassigned RW. Three Nihil source impact pairs stay
  NULL; two source evacuation/affected-count inconsistencies remain in notes.
- Top five units, ordered by class then rank (NO_RECORD has no recorded evidence):

| RW | Class / within-class rank | Records / episodes | Reason |
|---|---|---|---|
| 04 | HIGH / 1 | 25 / 16 | Maximum source depth 300 cm; access UNKNOWN |
| 05 | HIGH / 2 | 25 / 16 | Maximum source depth 300 cm; access UNKNOWN |
| 07 | MEDIUM / 1 | 3 / 1 | Depth 300 cm; one episode; access UNKNOWN |
| 08 | MEDIUM / 2 | 3 / 1 | Depth 300 cm; one episode; access UNKNOWN |
| 01 | NO_RECORD / 1 | 0 / 0 | No recorded event (≠ safe); field verification required |

RW 04/05 share the same 25 source rows for Jl. Kebon Pala II, RT 12–13 in RW 04
and RT 10–11 in RW 05. Their episode counts must not be summed. RW polygons are
reporting units; whole-RW inundation is not established. RW 07/08 share three source
rows. All nine units need field checking. All 252 RW/date access rows are UNKNOWN:
440 candidate targets, zero verified targets, no verified closure table, zero routes.
No baseline distance average is claimed under verified-only defaults.

Sensitivity uses REC_MED=2 and episode gap=2 days throughout:

| REC_HIGH | DEPTH_HIGH_CM | Changed RW | HIGH / MEDIUM / VERIFY / NO_RECORD |
|---|---|---|---|
| 2 | 30 | None | 2 / 2 / 0 / 5 |
| 2 | 50 | None | 2 / 2 / 0 / 5 |
| 2 | 80 | None | 2 / 2 / 0 / 5 |
| 3 | 30 | None | 2 / 2 / 0 / 5 |
| 3 | 50 | None | 2 / 2 / 0 / 5 |
| 3 | 80 | None | 2 / 2 / 0 / 5 |
| 4 | 30 | None | 2 / 2 / 0 / 5 |
| 4 | 50 | None | 2 / 2 / 0 / 5 |
| 4 | 80 | None | 2 / 2 / 0 / 5 |

Robustness: exclude the five Genangan source rows (ten normalized rows); RW 04/05
retain 20 records and **15 episodes each, HIGH**. No class changes. Thresholds were
not tuned to produce the map. Reports are local `results.run.json` and
`results.sanity.json`; the latter records the exact receipt:
`result_review = "Accepted by Raynald 2026-10-13"`. New reports default to pending.

Context only: the Satu Data export's publisher periods 2019–2020 list RW 04/05/07/08
in many 2020 months, RW 01–03/06 within January–February 2020, and no explicit RW 09.
Dates are unverified and excluded from classification. This shows the limitations
of NO_RECORD and one episode in RW 07/08 in the 2025 working set; it does not prove
absence of flooding. Context and source-row precision are carried into README,
F2 caption, methodology and the brief draft.

Raynald reviewed F2 and explicitly accepted the results and framing on 2026-10-13,
authorizing Phase 5. The corrected real output now says `1 episode` for RW 07/08.
The 116 unit tests still pass, with 99.18% core coverage. Data stays local and
uncommitted; no push. Phase 5 licensing was decided separately: public ZIP without
sample_data, with unresolved DKI/PPID redistribution permission.
