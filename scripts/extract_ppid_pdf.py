"""Extract PPID page text/tables and draft only explicitly mapped, source-located rows."""

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    from ._common import ROOT, write_csv, write_json
except ImportError:
    from _common import ROOT, write_csv, write_json

from km_flood_priority.core.normalize import normalize_name, parse_date
from km_flood_priority.core.schema import EVENT_COLUMNS

MONTHS_ID = {
    name: number
    for number, name in enumerate(
        (
            "januari",
            "februari",
            "maret",
            "april",
            "mei",
            "juni",
            "juli",
            "agustus",
            "september",
            "oktober",
            "november",
            "desember",
        ),
        start=1,
    )
}


def flat(value):
    return " ".join((value or "").split())


def source_date(value):
    parts = flat(value).lower().split()
    if len(parts) != 3 or parts[1] not in MONTHS_ID:
        raise ValueError(f"Unrecognized Indonesian source date: {value!r}")
    result = date(int(parts[2]), MONTHS_ID[parts[1]], int(parts[0]))
    if result.year != 2025:
        raise ValueError(f"2025 profile received a different source year: {value!r}")
    return result.isoformat()


def affected_count(value, unit):
    value = flat(value)
    if value.lower() == "nihil" or not value:
        return ""  # Preserve ambiguity; the human decides whether Nihil means zero.
    # April omits the unit suffix; the inspected KK/JIWA column headers provide it.
    match = re.fullmatch(rf"(\d+)(?:\s+{unit})?", value, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Ambiguous affected {unit} cell: {value!r}; transcribe manually")
    return match[1]


def draft_timur_2025(
    tables_by_page, source_id, *, kelurahan="KAMPUNG MELAYU", kecamatan="JATINEGARA"
):
    """Inspected 18-column PPID layout, including continuation pages without headers.

    Column 3/4 are affected KK/people; columns 13/14 are evacuees/sites and must never
    be substituted. Location is read only from ALAMAT, not evacuation-site names.
    """
    title_seen = header_seen = units_seen = False
    for _, tables in tables_by_page:
        for table in tables:
            for cells in table:
                if not cells:
                    continue
                title_seen |= (
                    "LAPORAN DATA KEJADIAN BANJIR & GENANGAN WILAYAH JAKARTA TIMUR"
                    in flat(cells[0]).upper()
                    and "TAHUN 2025" in flat(cells[0]).upper()
                )
                header_seen |= (
                    len(cells) == 18
                    and [flat(cell).upper() for cell in cells[:3]] == ["NO", "TANGGAL", "ALAMAT"]
                    and flat(cells[3]).upper() == "JUMLAH TERDAMPAK"
                    and flat(cells[6]).upper() == "KETINGGIAN AIR"
                )
                units_seen |= len(cells) == 18 and [flat(c).upper() for c in cells[3:5]] == [
                    "KK",
                    "JIWA",
                ]
    if not (title_seen and header_seen and units_seen):
        raise ValueError(
            "Unrecognized PPID layout; inspect PDF and use explicit mapping/transcription"
        )
    target = normalize_name(kelurahan), normalize_name(kecamatan)
    result = []
    for page_no, tables in tables_by_page:
        for table_no, table in enumerate(tables, start=1):
            for cells in table:
                if not cells or not flat(cells[0]).isdigit():
                    continue
                # Page 1 is a 17-column monthly summary, not dated/addressed events.
                if len(cells) == 17 and flat(cells[1]).lower() in MONTHS_ID:
                    continue
                if len(cells) != 18:
                    raise ValueError(f"p.{page_no}: numeric row has unexpected column count")
                number, raw_date, address = map(flat, cells[:3])
                location = re.search(r"\bKel\.\s*(.*?)\s*,?\s*\bKec\.\s*(.*)$", address, re.I)
                if location is None:
                    if normalize_name(kelurahan) in normalize_name(address):
                        raise ValueError(
                            f"p.{page_no}, NO {number}: ambiguous administrative address"
                        )
                    continue
                area = tuple(normalize_name(part.strip(", ")) for part in location.groups())
                if area != target:
                    continue
                rw_rt = re.findall(
                    r"\bRW\.?\s*(\d{1,2})\s*(?:=\s*)?RT\s*:?\s*([\d,\s]+)(?=\bRW|\bKel|$)",
                    address,
                    re.I,
                )
                rw_labels = re.findall(r"\bRW\.?\s*(\d{1,2})\b", address, re.I)
                if not rw_rt or rw_labels != [rw for rw, _ in rw_rt]:
                    raise ValueError(
                        f"p.{page_no}, NO {number}: RW/RT address needs manual transcription"
                    )
                depth = re.fullmatch(
                    r"(\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*cm)"
                    r"\s*\((Banjir|Genangan)\)",
                    flat(cells[6]),
                    re.I,
                )
                if depth is None:
                    raise ValueError(f"p.{page_no}, NO {number}: unrecognized water-height cell")
                row = dict.fromkeys(EVENT_COLUMNS, "")
                row.update(
                    {
                        "event_id": f"PPID25-P{page_no}-T{table_no}-NO{number}",
                        "source_id": source_id,
                        "source_ref": (
                            f"p.{page_no};table {table_no};source NO {number};date {raw_date}"
                        ),
                        "event_date": source_date(raw_date),
                        "kota": "JAKARTA TIMUR",
                        "kecamatan": area[1],
                        "kelurahan": area[0],
                        "rw_raw": ",".join(dict.fromkeys(rw for rw, _ in rw_rt)),
                        "rt_raw": "; ".join(f"RW {rw}: RT {flat(rt)}" for rw, rt in rw_rt),
                        "address_raw": address,
                        "depth_raw": depth[1],
                        "affected_kk": affected_count(cells[3], "KK"),
                        "affected_people": affected_count(cells[4], "Jiwa"),
                        "duration_raw": f"Source start {flat(cells[7])}; receded {flat(cells[8])}; "
                        "end date unspecified; elapsed duration not inferred",
                        "location_confidence": "UNKNOWN",
                        "verified": "N",
                        "notes": "Draft only; human must verify every field and assign confidence; "
                        f"source type {depth[2]}; original depth {flat(cells[6])}; "
                        f"affected KK cell {flat(cells[3])}; people cell {flat(cells[4])}; "
                        "affected counts are shared source totals, not allocated per RW; "
                        "Nihil left NULL; evacuation-site fields do not verify safe points",
                    }
                )
                result.append(row)
    if not result:
        raise ValueError(
            "No target-area rows extracted; inspect source and profile before proceeding"
        )
    return result


def review_markdown(rows, input_path):
    lines = [
        "# PPID 2025 transcription review",
        "",
        f"Source: `{input_path.name}`. Page numbers below are PDF viewer page numbers.",
        "",
        "Every row remains `verified=N` and `location_confidence=UNKNOWN`. This is a "
        "transcription draft, not a priority result. Review takes approximately 10–15 minutes.",
        "",
        "1. Open the original PDF and the draft CSV side by side.",
        "2. For each row, check source NO, date, ALAMAT, RW/RT, water height and affected "
        "KK/people. Use JUMLAH TERDAMPAK, not JUMLAH PENGUNGSI.",
        "3. Correct mismatches. Counts apply to the combined address/RWs; do not sum "
        "exploded RW copies. Nihil is left blank until you decide its meaning from the source.",
        "4. For checked rows whose RW is stated in ALAMAT, set `location_confidence=RW` "
        "and `verified=Y`. Keep unchecked rows at N; retain source references.",
        "5. Save UTF-8 comma-separated CSV as `data/clean/events_ppid_2025.csv`. "
        "Alternatively, report the exact checked rows/corrections to the agent; only the "
        "human's check can authorize verification flags.",
        "",
        "| Date | RW in ALAMAT | Depth | Affected KK | Affected people | Source reference |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        values = [
            row[key] or "NULL"
            for key in (
                "event_date",
                "rw_raw",
                "depth_raw",
                "affected_kk",
                "affected_people",
                "source_ref",
            )
        ]
        lines.append("| " + " | ".join(values) + " |")
    lines += [
        "",
        "The February Genangan record is retained with its original source type. "
        "No elapsed duration or road closure is inferred from the source times/text. "
        "Safe-point names in the evacuation column are evidence candidates, not verified targets.",
        "",
    ]
    return "\n".join(lines)


def draft_rows(
    tables_by_page, mapping, source_id, *, kelurahan="KAMPUNG MELAYU", kecamatan="JATINEGARA"
):
    result = []
    required = {"event_date", "kota", "kelurahan", "kecamatan"}
    if required - set(mapping):
        raise ValueError("PPID mapping must explicitly identify date, city, kelurahan and district")
    for page_no, tables in tables_by_page:
        for table_no, table in enumerate(tables, start=1):
            if not table:
                continue
            headers = [" ".join((value or "").split()) for value in table[0]]
            if len(headers) != len(set(headers)) or set(mapping.values()) - set(headers):
                continue
            for row_no, values in enumerate(table[1:], start=2):
                if len(values) != len(headers):
                    continue
                source = dict(zip(headers, values, strict=True))
                row = dict.fromkeys(EVENT_COLUMNS, "")
                row.update(
                    {
                        field: " ".join((source[column] or "").split())
                        for field, column in mapping.items()
                    }
                )
                if (normalize_name(row["kelurahan"]), normalize_name(row["kecamatan"])) != (
                    normalize_name(kelurahan),
                    normalize_name(kecamatan),
                ):
                    continue
                # Unparseable dates remain in the draft, visibly flagged, for human correction.
                try:
                    parse_date(row["event_date"])
                    date_note = ""
                except ValueError:
                    date_note = "; source date needs ISO transcription"
                row.update(
                    {
                        "event_id": f"PPID25-P{page_no}-T{table_no}-R{row_no}",
                        "source_id": source_id,
                        "source_ref": f"p.{page_no};table {table_no};row {row_no}",
                        "verified": "N",
                        "location_confidence": "UNKNOWN",
                        "notes": "Draft only; human must verify every field and assign confidence"
                        + date_note,
                    }
                )
                result.append(row)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-id", default="PPID25")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--mapping", type=Path, help="JSON canonical field -> exact PDF table header")
    mode.add_argument(
        "--profile",
        choices=["ppid-jakarta-timur-2025"],
        help="Inspected 2025 18-column layout; all rows remain unverified",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "data/interim/ppid_2025_draft.csv")
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(
            f"Draft exists: {args.output}; use another --output to preserve human edits"
        )
    try:
        import pdfplumber
    except ImportError:
        parser.error("Install requirements-dev.txt in .venv; pdfplumber is development-only")
    pages, tables_by_page = [], []
    with pdfplumber.open(args.input) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text, tables = page.extract_text() or "", page.extract_tables()
            pages.append({"page": number, "text": text, "tables": tables})
            tables_by_page.append((number, tables))
    write_json(args.output.with_suffix(".pages.json"), pages)
    if not any(page["text"].strip() for page in pages):
        write_csv(args.output, EVENT_COLUMNS, [])
        raise ValueError(
            "PDF has no extractable text; run OCR on a copy, then re-extract. "
            "Keep original PDF; every OCR field requires human verification."
        )
    mapping = json.loads(args.mapping.read_text(encoding="utf-8")) if args.mapping else None
    if args.profile:
        rows = draft_timur_2025(tables_by_page, args.source_id)
    else:
        rows = draft_rows(tables_by_page, mapping, args.source_id) if mapping else []
    write_csv(args.output, EVENT_COLUMNS, rows)
    write_json(
        args.output.with_suffix(".meta.json"),
        {
            "source_path": str(args.input.resolve()),
            "source_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "page_count": len(pages),
            "profile": args.profile,
            "mapping": mapping,
            "draft_rows": len(rows),
            "human_verified": False,
        },
    )
    args.output.with_suffix(".review.md").write_text(
        review_markdown(rows, args.input), encoding="utf-8"
    )
    print(
        f"Extracted {len(pages)} pages; draft contains {len(rows)} unverified rows: {args.output}"
    )
    if not rows:
        print(
            "Inspect .pages.json and provide --mapping for explicit table columns; "
            "merged/ambiguous table cells require manual transcription. No values were guessed."
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"extract_ppid_pdf: {error}")
