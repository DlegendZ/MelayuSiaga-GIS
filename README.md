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
111 unit tests with 99.18% core coverage. Official boundaries and an OSM snapshot have
been acquired and a five-layer metric GeoPackage prepared. The downloaded PPID PDF
has produced 28 source-located draft rows; human verification and Satu Data year
availability checks remain pending. An installable plugin
and real-data findings follow their acceptance gates.

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
Target plugin platforms: QGIS 3.44 (Qt5) and QGIS 4.x (Qt6); plugin integration is pending.
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
contains the two official boundary sources, the 2026-10-12 OSM snapshot, and PPID25.

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

Phase 1 is accepted only when the prepared inputs, valid event table, source registry,
and actual recorded year coverage are available. The full pipeline CLI, plugin ZIP,
screenshots, sensitivity analysis and technical brief are pending later phases.

## License

Project code is GPL-2.0-or-later. Copyright © 2026 Raynald Arvan Lim,
Alden Viriya Tanudjaja, Moses Handoyo. Data retains its own terms.
