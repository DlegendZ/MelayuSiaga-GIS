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

