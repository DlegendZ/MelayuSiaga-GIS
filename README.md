# MelayuSiaga-GIS — KM Flood Priority

QGIS plugin in development for **verification priority based on recorded flood events**
at RW scale in Kelurahan Kampung Melayu, Kecamatan Jatinegara, Kota Jakarta Timur.
No recorded event (≠ safe). Access without verified supporting evidence is UNKNOWN.

## Assignment context

BINUS GIS Final Project. Authors: Raynald Arvan Lim (`raynald.lim@binus.ac.id`),
Alden Viriya Tanudjaja (`alden.tanudjaja@binus.ac.id`), Moses Handoyo (`moses.handoyo@binus.ac.id`).
The three-person group and study area framing await lecturer confirmation.

## Development status

The [execution specification](docs/EXECUTION_SPEC.md) defines the phase gates.
See [progress](docs/PROGRESS.md) and [human tasks](docs/HUMAN_TASKS.md).
Phase 0 setup and Phase 2 core are complete. The core and acquisition helpers pass
116 unit tests with 99.18% core coverage. Official boundaries and an OSM snapshot have
been acquired and a five-layer metric GeoPackage prepared. The downloaded PPID PDF
has produced 28 source-located rows, accepted by Raynald after Claude's delegated
independent check. The clean and merged event tables pass validation, with coverage
**2025 only**. Four Satu Data CSVs were audited and excluded because they are monthly
context or require source resolution. Phase 1 input acceptance is complete for this
PPID-only working set. Phase 3 is accepted: all five Processing algorithms, menu lifecycle,
embedded styles and the offline pipeline pass **12 integration tests on each of QGIS
3.44.15 and 4.2.3**, including ZIP activation and qgis_process execution. Windows manual
acceptance and real-data findings are the next gates.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/unit
```

To repeat the coverage and lint checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit --cov=km_flood_priority/core --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check km_flood_priority scripts tests
```

The plugin core uses only the Python standard library and must import independently of QGIS.
Tested plugin platforms: QGIS 3.44.15 (Qt5) and QGIS 4.2.3 (Qt6).
Input preparation uses `qgis/qgis:3.44.15-noble`, verified against the
[official Docker tags](https://hub.docker.com/r/qgis/qgis/tags).
Local commits are made as work passes checks. No push or release is authorized.

## Data sources and licenses

See [data sources](docs/DATA_SOURCES.md). Real inputs are not committed until
redistribution terms are confirmed. Roads/buildings: © OpenStreetMap contributors, ODbL.
Synthetic records are restricted to `tests/fixtures/`.

## Acquire and prepare inputs

Start Docker Desktop with Linux containers, then run these from the repository root.
Raw snapshots cannot be silently overwritten; select another `--date` for a new acquisition.

```powershell
.\.venv\Scripts\python.exe scripts/fetch_admin_boundaries.py
docker pull qgis/qgis:3.44.15-noble
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/repo" --workdir /repo -e QT_QPA_PLATFORM=offscreen --entrypoint python3 qgis/qgis:3.44.15-noble scripts/build_inputs.py --prepare-bbox-only
.\.venv\Scripts\python.exe scripts/fetch_osm.py
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/repo" --workdir /repo -e QT_QPA_PLATFORM=offscreen --entrypoint python3 qgis/qgis:3.44.15-noble scripts/build_inputs.py
```

The preparation script validates administrative areas, repairs/reprojects geometry,
clips context layers, and writes `data/processed/inputs.gpkg` plus a validation report.
Its five layers are `rw`, `kelurahan_boundary`, `roads`, `buildings`, `safe_points`.
Register snapshot metadata in `data/clean/sources.csv`. The current registry already
contains the two official boundary sources, the 2026-10-12 OSM snapshot, PPID25,
and the four audited Satu Data snapshots.

Download event datasets yourself using [the human checklist](docs/HUMAN_TASKS.md).
After a PDF is available, the agent extracts a draft with `extract_ppid_pdf.py`; every
draft row needs a human check. `convert_satudata.py` requires an inspected mapping
for the actual year's columns (`--mapping`, template in `data/templates/`); it fails
on unknown columns. Converted rows remain `verified=N` until checked. Once canonical
CSVs and source records are ready, `merge_sources.py` creates `events_all.csv` and a
validation report. Never map a count of affected RW to an RW code field.

For the inspected PPID 2025 layout, run:

```powershell
.\.venv\Scripts\python.exe scripts/extract_ppid_pdf.py data/raw/ppid/REKAP_BANJIR_TAHUN_2025.pdf --profile ppid-jakarta-timur-2025
```

The script creates `data/interim/ppid_2025_draft.csv`, extracted pages, a checksum
metadata file, and `ppid_2025_draft.review.md` with human review instructions.
The profile handles continuation pages, excludes the monthly summary, reads RW
labels separately from RT numbers, and keeps affected counts separate from evacuees.
It leaves `Nihil` impact cells NULL and flags all rows unverified with UNKNOWN confidence.
Existing draft CSVs are protected: use another `--output` to repeat extraction.

Audit the downloaded publisher exports without generating canonical events:

```powershell
.\.venv\Scripts\python.exe scripts/audit_satudata.py data/raw/satudata/satudata_2020_20261012.csv data/raw/satudata/satudata_2023_20261012.csv data/raw/satudata/satudata_2024_20261012.csv data/raw/satudata/satudata_general_20261012.csv
```

The report is `data/interim/satudata_audit.json`. Monthly aggregate exports lack
event dates and RW identities; the 2020 export contains inconsistent period/date
fields. See the [source audit](docs/DATA_SOURCES.md#satu-data-granularity-audit--2026-10-12)
before using these datasets. The CSV reader handles repeated leading UTF-8 BOMs
without modifying raw files; the converter rejects affected-RW count fields as RW codes.

Phase 1 is accepted only when the prepared inputs, valid event table, source registry,
and actual recorded year coverage are available. These input gates are now met.
Screenshots, real-data sensitivity and the technical brief follow their later gates.

## Local plugin and pipeline

Build the installable ZIP, with real sample data excluded by default:

```powershell
.\.venv\Scripts\python.exe scripts/package_plugin.py
```

Install `dist/km_flood_priority-1.0.0.zip` through QGIS Plugins → Install from ZIP;
follow [the Windows guide](docs/USER_GUIDE.md). The ZIP contains only the plugin root,
code and assets; no tests, bytecode or synthetic/real datasets are bundled by default.

Run the real local working set through qgis_process in an isolated offline container:

```powershell
.\.venv\Scripts\python.exe scripts/run_pipeline_cli.py --docker
```

The wrapper uses a disposable QGIS profile, loads the repository plugin, and writes
`data/processed/results.gpkg` plus `results.run.json`. Existing outputs are protected;
use another filename or explicitly add `--overwrite`. In a QGIS/OSGeo4W shell, omit
`--docker`. Optional candidate targets remain flagged; missing verified evidence yields UNKNOWN.

| Integration runtime | Acceptance |
|---|---|
| `qgis/qgis:3.44.15-noble` | 12 tests pass, including ZIP/CLI |
| `qgis/qgis:4.2.3-trixie` | 12 tests pass, including ZIP/CLI |
| Native Windows desktop | Pending human acceptance |

Repeat either container test with `python3 -m pytest tests/qgis -q` using the Docker
mount pattern above. The CI matrix contains both exact tags; remote CI has not run
because no push is authorized.

## License

Project code is GPL-2.0-or-later. Copyright © 2026 Raynald Arvan Lim,
Alden Viriya Tanudjaja, Moses Handoyo. Data retains its own terms.
