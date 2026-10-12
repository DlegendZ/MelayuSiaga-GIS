import json
from pathlib import Path

import pytest

from scripts._common import read_csv, save_snapshot, write_csv
from scripts.audit_satudata import inspect_source
from scripts.convert_satudata import convert
from scripts.extract_ppid_pdf import draft_rows, draft_timur_2025
from scripts.fetch_admin_boundaries import validate_rw
from scripts.fetch_osm import convert_elements, overpass_query

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_csv_template_comments_are_not_data():
    headers, rows = read_csv(Path(__file__).parents[2] / "data/templates/events_template.csv")
    assert "event_id" in headers
    assert rows == []


def test_csv_quotes_and_newlines_roundtrip(tmp_path):
    rows = [{"event_id": "TEST-1", "notes": 'Contains comma, quote " and\nnewline'}]
    path = tmp_path / "test.csv"
    write_csv(path, rows[0], rows)
    assert read_csv(path)[1] == rows
    with pytest.raises(FileExistsError):
        write_csv(path, rows[0], [{"event_id": "OTHER", "notes": "replacement"}])
    assert read_csv(path)[1] == rows


def test_csv_repeated_utf8_bom_does_not_change_first_column(tmp_path):
    path = tmp_path / "publisher_export.csv"
    path.write_bytes(b"\xef\xbb\xbf\xef\xbb\xbfevent_id,notes\r\nTEST-1,TESTVILLE\r\n")
    headers, rows = read_csv(path)
    assert headers == ["event_id", "notes"]
    assert rows == [{"event_id": "TEST-1", "notes": "TESTVILLE"}]


def test_source_mapping_filter_and_verification():
    headers, rows = read_csv(FIXTURES / "satudata.csv")
    mapping = json.loads((FIXTURES / "satudata_mapping.json").read_text())
    output, dropped = convert(
        headers,
        rows,
        mapping,
        year=2025,
        source_id="SYNTHETIC",
        kelurahan="TESTVILLE",
        kecamatan="TEST DISTRICT",
    )
    assert dropped == 1
    assert output[0]["event_date"] == "2025-03-04"
    assert output[0]["verified"] == "N"
    assert output[0]["source_ref"] == "row 2"
    assert output[0]["location_confidence"] == "RW"


def test_unknown_csv_column_stops_conversion():
    headers, rows = read_csv(FIXTURES / "satudata.csv")
    mapping = json.loads((FIXTURES / "satudata_mapping.json").read_text())
    with pytest.raises(ValueError, match="unknown"):
        convert([*headers, "unknown_new_column"], rows, mapping, year=2025, source_id="SYNTHETIC")


def test_affected_rw_count_cannot_be_mapped_to_spatial_rw_code():
    headers, rows = read_csv(FIXTURES / "satudata.csv")
    mapping = json.loads((FIXTURES / "satudata_mapping.json").read_text())
    count_column = "jumlah_rw_terdampak"
    headers = [count_column if name == "test_rw" else name for name in headers]
    rows = [
        {count_column if key == "test_rw" else key: value for key, value in row.items()}
        for row in rows
    ]
    mapping["column_map"]["rw_raw"] = count_column
    with pytest.raises(ValueError, match="count.*RW code"):
        convert(headers, rows, mapping, year=2025, source_id="SYNTHETIC")


def test_monthly_aggregate_is_context_without_inventing_date_or_rw():
    rows = [
        {
            "periode_data": "202503",
            "bulan": "2",
            "kelurahan": "TESTVILLE",
            "kecamatan": "TEST DISTRICT",
            "jumlah_rw_terdampak": "4",
        }
    ]
    result = inspect_source(list(rows[0]), rows, kelurahan="TESTVILLE", kecamatan="TEST DISTRICT")
    assert result["usage"] == "context_only"
    assert result["target_rows"][0]["issues"] == ["no_exact_event_date", "no_rw_codes"]
    assert result["target_rows"][0]["rw_raw"] == ""


def test_source_period_date_conflict_and_unknown_rw_require_review():
    rows = [
        {
            "periode_data": "201912",
            "tanggal_kejadian": "06/12/2020",
            "rw": "0",
            "kelurahan": "TESTVILLE",
            "kecamatan": "TEST DISTRICT",
        }
    ]
    result = inspect_source(list(rows[0]), rows, kelurahan="TESTVILLE", kecamatan="TEST DISTRICT")
    assert result["usage"] == "source_review_required"
    assert result["target_rows"][0]["issues"] == ["period_date_conflict", "rw_unassigned"]


def test_monthly_list_of_dates_is_not_expanded_to_rw_date_cross_product():
    rows = [
        {
            "periode_data": "202001",
            "tanggal_kejadian": "tgl. 01, 09, 18 Januari",
            "rw": "RW 01, 02",
            "kelurahan": "TESTVILLE",
            "kecamatan": "TEST DISTRICT",
        }
    ]
    result = inspect_source(list(rows[0]), rows, kelurahan="TESTVILLE", kecamatan="TEST DISTRICT")
    assert len(result["target_rows"]) == 1
    assert result["target_rows"][0]["issues"] == ["date_needs_source_transcription"]


def test_osm_candidates_never_auto_verified():
    elements = json.loads((FIXTURES / "osm.json").read_text())["elements"]
    roads, buildings, candidates = convert_elements(elements + elements, "SYNTHETIC")
    assert len(roads) == 1
    assert len(buildings) == 1
    assert len(candidates) == 2
    assert all(row["verified"] == "N" and row["capacity"] == "" for row in candidates)
    assert all("TESTVILLE" in row["name"] for row in candidates)


def test_ppid_draft_retains_page_and_requires_human_confidence(raw_event):
    table = [list(raw_event), list(raw_event.values())]
    mapping = {field: field for field in raw_event}
    rows = draft_rows(
        [(7, [table])], mapping, "SYNTHETIC", kelurahan="TESTVILLE", kecamatan="TEST DISTRICT"
    )
    assert rows[0]["source_ref"] == "p.7;table 1;row 2"
    assert rows[0]["verified"] == "N"
    assert rows[0]["location_confidence"] == "UNKNOWN"


def timur_table():
    # Synthetic table follows the inspected source layout; every place is TESTVILLE.
    title = ["LAPORAN DATA KEJADIAN BANJIR & GENANGAN WILAYAH JAKARTA TIMUR MARET TAHUN 2025"]
    header = [
        "NO",
        "TANGGAL",
        "ALAMAT",
        "JUMLAH TERDAMPAK",
        None,
        "PENYEBAB",
        "KETINGGIAN AIR",
        "Waktu",
        None,
        "JUMLAH KORBAN",
        None,
        None,
        None,
        "JUMLAH PENGUNGSI",
        "JUMLAH TEMPAT PENGUNGSIAN",
        "KERUGIAN",
        "BANTUAN",
        "DOKUMENTASI",
    ]
    subheader = [None, None, None, "KK", "JIWA"] + [None] * 13
    record = [
        "9",
        "2 Maret 2025",
        "Jl. TESTVILLE\nRW 04 = RT 12, 13\nRW 05 = RT : 10, 11\nKel. TESTVILLE\nKec. TEST DISTRICT",
        "17 KK",
        "51 Jiwa",
        "TEST cause",
        "25 cm\n(Genangan)",
        "22:15",
        "3:00",
    ] + ["Nihil"] * 9
    return [title + [None] * 17, header, subheader, record]


def test_ppid_profile_continuation_rows_and_rw_not_rt_numbers():
    table = timur_table()
    continuation = table[-1].copy()
    continuation[0:2] = ["10", "3 Maret 2025"]
    continuation[2] = continuation[2].replace(" = ", " ")
    continuation[3:5] = ["17", "51"]
    other_area = continuation.copy()
    other_area[2] = other_area[2].replace("Kel. TESTVILLE", "Kel. OTHER TESTVILLE")
    rows = draft_timur_2025(
        [
            (1, [[["1", "Januari"] + ["TEST summary"] * 15]]),
            (6, [table]),
            (7, [[continuation, other_area]]),
        ],
        "SYNTHETIC",
        kelurahan="TESTVILLE",
        kecamatan="TEST DISTRICT",
    )
    assert len(rows) == 2
    assert rows[0]["rw_raw"] == "04,05"
    assert rows[0]["rt_raw"] == "RW 04: RT 12, 13; RW 05: RT 10, 11"
    assert rows[0]["depth_raw"] == "25 cm"
    assert rows[0]["affected_kk"] == "17"
    assert rows[0]["affected_people"] == "51"
    assert rows[0]["event_date"] == "2025-03-02"
    assert rows[1]["source_ref"] == "p.7;table 1;source NO 10;date 3 Maret 2025"
    assert rows[1]["location_confidence"] == "UNKNOWN"
    assert all(row["verified"] == "N" for row in rows)
    assert "not allocated" in rows[0]["notes"]
    assert "Genangan" in rows[0]["notes"]
    assert "22:15" in rows[0]["duration_raw"]
    assert "end date unspecified" in rows[0]["duration_raw"]


def test_ppid_profile_nihil_is_preserved_as_unknown_not_zero():
    table = timur_table()
    table[-1][3:5] = ["Nihil", "Nihil"]
    rows = draft_timur_2025(
        [(5, [table])], "SYNTHETIC", kelurahan="TESTVILLE", kecamatan="TEST DISTRICT"
    )
    assert rows[0]["affected_kk"] == rows[0]["affected_people"] == ""
    assert "Nihil" in rows[0]["notes"]


@pytest.mark.parametrize("column,value", [(1, "32 Maret 2025"), (6, "very high"), (3, "17/19 KK")])
def test_ppid_profile_ambiguous_fields_stop_for_transcription(column, value):
    table = timur_table()
    table[-1][column] = value
    with pytest.raises(ValueError):
        draft_timur_2025(
            [(6, [table])], "SYNTHETIC", kelurahan="TESTVILLE", kecamatan="TEST DISTRICT"
        )


def test_ppid_profile_rejects_unrecognized_layout():
    with pytest.raises(ValueError, match="layout"):
        draft_timur_2025([(1, [[["1", "2 Maret 2025", "TESTVILLE"]]])], "SYNTHETIC")


def test_raw_snapshot_cannot_be_silently_overwritten(tmp_path):
    target = tmp_path / "snapshot.json"
    save_snapshot(target, b"{}", url="https://example.invalid/test", query="TEST")
    info = json.loads(target.with_suffix(".meta.json").read_text())
    assert len(info["sha256"]) == 64
    with pytest.raises(FileExistsError):
        save_snapshot(target, b"changed", url="https://example.invalid/test")
    assert target.read_bytes() == b"{}"


def test_rw_numbers_must_be_unique():
    features = [{"properties": {"wadmrw": "004"}, "geometry": {"type": "Polygon"}}] * 2
    with pytest.raises(ValueError, match="unique"):
        validate_rw({"features": features})


def test_overpass_bbox_validation():
    with pytest.raises(ValueError, match="bbox"):
        overpass_query([1, 2, 0, 3])
