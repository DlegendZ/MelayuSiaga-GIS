"""Adapter evidence checks beyond the already-tested pure Python rules."""

import csv

import pytest
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingContext,
    QgsProcessingException,
    QgsVariantUtils,
)


def import_parameters(inputs):
    return {
        "OUTPUT_EVENTS": "TEMPORARY_OUTPUT",
        "OUTPUT_ISSUES": "TEMPORARY_OUTPUT",
        **{
            key: inputs[key]
            for key in (
                "RW_LAYER",
                "RW_FIELD",
                "KELURAHAN",
                "KECAMATAN",
                "EVENTS_CSV",
                "SOURCES_CSV",
            )
        },
    }


def access_parameters(inputs):
    return {
        "OUTPUT_ACCESS": "TEMPORARY_OUTPUT",
        "OUTPUT_ROUTES": "TEMPORARY_OUTPUT",
        **{key: inputs[key] for key in ("RW_LAYER", "RW_FIELD", "ROADS", "SAFE_POINTS")},
    }


def test_import_keeps_notes_null_and_reports_bad_row(synthetic_inputs):
    import processing

    path = synthetic_inputs["EVENTS_CSV"]
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    rows[0]["event_date"] = "invalid date"
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    context = QgsProcessingContext()
    result = processing.run(
        "kmflood:import_validate", import_parameters(synthetic_inputs), context=context
    )
    assert result["OUTPUT_SUMMARY"]["errors"] == 1
    assert result["OUTPUT_EVENTS"].featureCount() == 7
    assert any(
        QgsVariantUtils.isNull(feature["rw_no"])
        for feature in result["OUTPUT_EVENTS"].getFeatures()
    )
    assert all(
        feature["notes"] == "Synthetic only; no real place or finding"
        for feature in result["OUTPUT_EVENTS"].getFeatures()
    )


def test_missing_csv_columns_fail_with_clear_schema_message(synthetic_inputs):
    import processing

    with open(synthetic_inputs["EVENTS_CSV"], "w", encoding="utf-8") as handle:
        handle.write("test_column\nTESTVILLE\n")
    with pytest.raises(QgsProcessingException, match="event_date"):
        processing.run("kmflood:import_validate", import_parameters(synthetic_inputs))


def test_geographic_roads_and_origins_reproject_to_metric(synthetic_inputs):
    import processing

    inputs = access_parameters(synthetic_inputs)
    for key in ("RW_LAYER", "ROADS", "SAFE_POINTS"):
        inputs[key] = processing.run(
            "native:reprojectlayer",
            {
                "INPUT": inputs[key],
                "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:4326"),
                "OUTPUT": "memory:",
            },
        )["OUTPUT"]
    result = processing.run("kmflood:test_access", inputs)
    lengths = {
        feature["rw_no"]: feature["baseline_length_m"]
        for feature in result["OUTPUT_ACCESS"].getFeatures()
    }
    assert lengths == pytest.approx({1: 300, 2: 200, 3: 100, 4: 50}, abs=0.03)
    assert result["OUTPUT_ROUTES"].crs().authid() == "EPSG:32748"


def test_unverified_target_opt_in_keeps_unknown_and_flags(synthetic_inputs):
    import processing

    safe = synthetic_inputs["SAFE_POINTS"]
    feature = next(safe.getFeatures())
    index = safe.fields().indexOf("verified")
    assert safe.dataProvider().changeAttributeValues({feature.id(): {index: "N"}})
    inputs = access_parameters(synthetic_inputs)
    result = processing.run("kmflood:test_access", {**inputs, "USE_UNVERIFIED_SAFE_POINTS": True})
    assert all(
        feature["access_status"] == "UNKNOWN"
        and feature["targets_verified"] == "N"
        and "unverified_targets" in feature["status_reason"]
        for feature in result["OUTPUT_ACCESS"].getFeatures()
    )


def test_verified_target_without_source_citation_is_rejected(synthetic_inputs):
    import processing

    safe = synthetic_inputs["SAFE_POINTS"]
    feature = next(safe.getFeatures())
    assert safe.dataProvider().changeAttributeValues(
        {feature.id(): {safe.fields().indexOf("source_ref"): ""}}
    )
    inputs = access_parameters(synthetic_inputs)
    with pytest.raises(QgsProcessingException, match="source_ref"):
        processing.run("kmflood:test_access", inputs)
