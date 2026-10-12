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
An installable plugin and real-data findings will be delivered after their acceptance gates pass.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/unit
```

The plugin core uses only the Python standard library and must import independently of QGIS.
Target platforms: QGIS 3.44 (Qt5) and QGIS 4.x (Qt6); neither has been tested yet.
Local commits are made as work passes checks. No push or release is authorized.

## Data sources and licenses

See [data sources](docs/DATA_SOURCES.md). Real inputs are not committed until
redistribution terms are confirmed. Roads/buildings: © OpenStreetMap contributors, ODbL.
Synthetic records are restricted to `tests/fixtures/`.

## License

Project code is GPL-2.0-or-later. Copyright © 2026 Raynald Arvan Lim,
Alden Viriya Tanudjaja, Moses Handoyo. Data retains its own terms.
