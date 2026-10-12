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

