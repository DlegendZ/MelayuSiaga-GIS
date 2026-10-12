import csv
from pathlib import Path

import pytest


@pytest.fixture
def raw_event():
    path = Path(__file__).parents[1] / "fixtures" / "events.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return next(csv.DictReader(handle))


@pytest.fixture
def importer():
    from km_flood_priority.core.normalize import import_events

    def run(rows, **kwargs):
        return import_events(
            rows,
            rw_numbers={4, 5},
            source_ids={"SYNTHETIC", "OTHER"},
            kelurahan="TESTVILLE",
            kecamatan="TEST DISTRICT",
            **kwargs,
        )

    return run
