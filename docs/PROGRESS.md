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
## 2026-10-13 — Phase 5 local deliverables ready; human/remote gates pending

- **Licensing decision §6.3 (Raynald): public ZIP WITHOUT sample_data.** DKI boundary
  and PPID redistribution permission remains unconfirmed. The entire sample_data
  directory is excluded from the default ZIP, including its README. Load sample data
  now shows an information message with the reason and the exact README reproduction
  heading/URL; no exception or layer addition occurs when the data is absent.
- Prepared `dist/km_flood_priority-1.0.0.zip`: 60,244 bytes, one km_flood_priority/
  root, no datasets/tests/bytecode/sample_data, CRC passes, below 10 MB. SHA-256:
  `63e64e1e97d2b14fc9c00ea5d2da5e0ac49caa2ab6f37d117522ada89e0ea0ac`.
- Prepared separate **local-only** `dist/km_flood_priority-local-data.zip`: 3,524,433
  bytes; inputs.gpkg + events_all.csv + sources.csv, SHA-256 manifest and instructions.
  All three extracted input files match their sources byte for byte. SHA-256:
  `0ebe1cfb39a4836c16f077892fb9a9516a80330d0d04ff2309e4fa4bae560abb`.
  Public distribution is explicitly false in the manifest. This bundle and all dist/
  files remain gitignored; never commit or release the data bundle. Attach it to the
  lecturer only if the lecturer permits it, as Raynald instructed.
- Produced and visually inspected F1 locator, F2 priority map, and F3 method diagram
  from real data. F1 uses 65 official indicative Jakarta Timur kelurahan polygons.
  F2 includes the RT addresses, shared 25-source-row caution and whole-RW claim limit;
  its caption includes historical context and both robustness checks. Attribution,
  scale and north arrows are present. F3 uses explicit SVG arrowheads for PNG support.
- Rewrote README in the required section order, with a Windows OSGeo4W/QGIS Python
  path using standard library + bundled QGIS bindings and no extra packages. The
  fetch_admin → metric bbox → fetch_osm → build_inputs sequence ends in inputs.gpkg.
  Manual PDF URL/name/SHA-256, checked CSV transcription/registry/merge, current
  input hashes and offline pipeline alternative are documented. Updated methodology,
  source attribution/licensing, user guide, bundled help and human task list.
- Prepared actual S1/S2/demo filenames and commented README embed slots, plus a
  five-minute screenshot checklist and 30–60 second demo plan. S1/S2 are still pending
  Windows captures; map exports are not labelled UI screenshots. Drafted the brief
  using accepted real numbers for the humans' maximum two-page A4 layout; no final
  brief PDF or product screenshot is claimed.
- Verification: 116 unit tests pass; latest core coverage 99.18%. All 12 integration
  tests pass on EACH of QGIS 3.44.15 and 4.2.3, including the missing-data message.
  After excluding the full sample_data directory, ZIP activation/CLI tests were rerun
  and passed on both versions. Ruff lint/format and Git whitespace checks pass.
  SQLite integrity, preserved six NULL normalized impact pairs, four normalized
  source-inconsistency notes, singular 1 episode, active documentation links and ZIP
  exclusions passed the artifact audit. Accepted priority values remain unchanged.
- **Phase 5 is not globally accepted yet:** native Windows manual testing/screenshots,
  remote CI, tag/release and a release-based quick start remain pending. Remote actions
  are deferred under the owner's commits-without-push instruction, not reported as
  passing. Lecturer alignment, independent clean-copy reproduction and final brief
  PDF also remain human gates. Local implementation/docs/artifacts are ready for them.
## 2026-10-13 — Windows operation recorded; GUI style loading repaired

1. Raynald reported the completed native Windows run on **QGIS 3.44.15**: pipeline
   **1.72 s**; priority_table, access_by_rw and events identical to accepted Phase 4.
   Operator: **Claude under Raynald's instructions on Raynald's laptop**. This is
   user-reported delegated operation, not a claim that Raynald operated each UI step.
   The reported native timing satisfies the 30-second target for that run.
2. Supplied and visually inspected S1_pipeline.png and S2_results.png; embedded them
   in README and S2 in the brief draft. Provenance: **screenshot asli Windows,
   dioperasikan Claude atas instruksi Raynald**. S1 shows the provider and pipeline
   dialog; S2 shows the reopened result package with category styles and attributes.
   S2 predates the GUI automatic style fix and is not presented as a manual rerun
   of that fix. Screenshot originals were preserved unchanged. SHA-256:
   S1 `754b7dfea33f62590f6c87045508f3335263f8aeab02ef9b6db3875114f59539`;
   S2 `6818b4e7ad76340c3c6be6e2249711bfdc50c168f5321685c4364d2102b2e26f`.
3. Reproduced the reported bug with an integration test using QGIS's actual
   `handleAlgorithmResults` GUI completion path: rw_priority was singleSymbol even
   though reopening the same package loaded categorizedSymbol. Added a per-spatial-
   layer postprocessor that binds the final OUTPUT_GPKG URI, calls loadDefaultStyle,
   and repaints after the GUI loader finishes. Python callback wrappers are retained
   by the processing context so garbage collection cannot discard their overrides.
   This changes presentation only; classification/access/import rules are unchanged.
4. Verification after the repair: **13 integration tests pass on each of QGIS
   3.44.15/Qt5 and 4.2.3/Qt6**. The new test checks all eleven automatically loaded
   layers, the final priority source URI, categorizedSymbol, all four category values,
   labels and target/route categories without manual reopening. It also passes on
   the installed **native Windows QGIS 3.44.15** in an additional offscreen test
   (1 test, 6.39 s). Existing repository pytest dependencies were reused; nothing
   was installed into QGIS. Unit tests: 116 pass, 99.18% core coverage. Ruff lint,
   format, SQLite/NULL/provenance/ZIP/link audits and whitespace checks pass.
5. Raynald confirmed a group-specific exception allowing **three members**; updated
   the spec, README and human task list, removing the pending group-size question.
   Rebuilt local plugin ZIP: **60,700 bytes**, SHA-256
   `5635a24b8455e9b2ae3d44609d108f199ff4dd6462c5c2f225867b958a024f6f`;
   still excludes the entire sample_data directory. The separate local data bundle
   is unchanged, ignored and unreleased. All commits remain local; **no push**.

Windows desktop recheck of the rebuilt ZIP is documented in USER_GUIDE (two minutes).
The original Windows operation and screenshots are recorded as completed; the
repaired build's desktop recheck is a separate pending deployment check. Demo,
independent clean-copy reproduction, final two-page PDF and framing/language
alignment remain pending. Remote CI/tag/release remain deferred under the owner's
no-push instruction; this update does not claim global Phase 5/6 acceptance.

## 2026-10-13 — Failed desktop style recheck; module-level callback repair

1. Raynald reported that the previous 60,700-byte ZIP failed the native Windows
   QGIS 3.44.15 style recheck after installation, restart, a fresh project and
   `data/processed/style_recheck.gpkg`. Pipeline data succeeded in **1.2 s**, with
   **28 source / 56 normalized rows and zero errors**, but rw_priority, safe_points
   and access_routes remained singleSymbol. No postprocessor error was logged.
   Inspected and preserved the original local screenshot
   `dist/local-data/S2_style_recheck_FAILED.png` (gitignored), SHA-256
   `23dc3b14bd696619703cf145b5af051855a8d7c311450d021d1a1a6b14672874`.
2. Reproduced the failure on the installed Windows runtime before changing the
   repair: transferred C++ completion results into a new QgsProcessingContext,
   released the execution wrapper, forced garbage collection and ran QGIS's actual
   `processing.gui.Postprocessing.handleAlgorithmResults`. Priority remained
   singleSymbol. The earlier test retained the same Python context wrapper, so its
   pass did not establish callback survival across GUI wrapper lifetimes. This
   supersedes the earlier claim that a context attribute protects those callbacks.
3. Replaced context-owned Python references with the module's
   `PackageStylePostProcessor._instances` list and a create factory. Each queued
   output has its own retained callback. C++ still owns the objects; stale SIP
   wrappers are pruned after C++ context destruction on the next creation.
   `postProcessLayer(name)` now logs entry with the final source URI, calls
   loadDefaultStyle after GUI layer loading, repaints and logs the restored renderer.
   The postprocessor remains the chosen after-load restoration path. An additional
   project-signal/timer fallback was considered but is not installed: context-transfer
   and actual GUI worker tests now explicitly require callback execution for all
   five layers, including when the old wrapper is no longer reachable.
4. Verification: **14 integration tests pass on EACH QGIS 3.44.15/Qt5 (32.30 s)
   and 4.2.3/Qt6 (35.26 s)**. The two GUI cases use a fresh completion context;
   one runs through the same QgsProcessingAlgRunnerTask used by AlgorithmDialog.
   Neither test retains a postprocessor or execution-context reference after
   execution. Both assert final priority URI, categorizedSymbol, four categories,
   labels, target/route categories, roads/boundary colours and widths, all five
   entry/success logs and no embedded-style error. The same two cases pass on
   **native Windows QGIS 3.44.15 (2.89 s)**. Unit checks: **116 pass, 99.18% core
   coverage**. Roads and kelurahan_boundary intentionally retain singleSymbol
   renderers; their defined grey roads / dark outline distinguish valid styling
   from the random defaults. Analysis, source data and accepted classes are unchanged.
5. Rebuilt **local** `dist/km_flood_priority-1.0.0.zip`: **60,930 bytes**, SHA-256
   `b136fd06beb6f91f3eb8bf90dedcb77db1c4fe33b384bddee8de41a84e4fbfff`.
   Public ZIP still excludes sample_data; the separate local-only data bundle is
   unchanged. Updated README, USER_GUIDE, HUMAN_TASKS and brief test counts to
   distinguish the failed desktop check from the replacement build's automated
   passes. Native desktop recheck of this ZIP is **pending**, using a new
   `data/processed/style_recheck_v2.gpkg` and the five callback logs. All commits
   stay local; **no push**, tag or release.
