# Data sources and licenses

Official boundaries and an OSM snapshot were acquired on **2026-10-12**. The user
downloaded the PPID PDF and accepted Claude's delegated independent check of all
28 rows. Those rows are Y/RW by Raynald's explicit instruction; the original draft
remains unverified. Four Satu Data CSV exports were also downloaded and audited.
Unresolved Satu Data year/source checks remain recorded limitations. Working downloads are
gitignored until redistribution terms are confirmed.

| ID | Publisher / source | Use | Retrieval and terms |
|---|---|---|---|
| D1 | [PPID Kota Jakarta Timur, 2025 flood recap](https://timur.jakarta.go.id/ppid/storage/files/setko-260609-075654-x938X6Z0-REKAP_BANJIR_TAHUN_2025_compressed.pdf) | Recorded events | Human download completed 2026-10-12; 23 pages, 28 Y/RW rows accepted by Raynald after delegated Claude review; redistribution terms pending |
| D2 | [Satu Data Jakarta / national catalog](https://data.go.id/dataset/dataset/data-kejadian-bencana-banjir-di-provinsi-dki-jakarta-tahun-2020) | Supplementary source audit | Four original CSVs acquired 2026-10-12; none accepted for date/RW event analysis; see audit below |
| D3 | [Dinas Cipta Karya, Tata Ruang, dan Pertanahan DKI Jakarta — RW](https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted/ADMINISTRASI_AR_RW/FeatureServer/18) | RW analysis units | Acquired 2026-10-12, 9 RW (01–09); redistribution permission unresolved |
| D4 | [DKI kelurahan layer 85](https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted/Batas_Administrasi_Kelurahan_DKI_Jakarta/FeatureServer/85) | Boundary | Acquired 2026-10-12, one polygon; indicative administrative boundaries |
| D5 | [OpenStreetMap contributors / Overpass](https://overpass-api.de/api/interpreter) | Roads, buildings, candidate sites | Acquired 2026-10-12; © OpenStreetMap contributors, ODbL; 440 candidates are unverified |
| D6 | BPBD / Kelurahan Kampung Melayu | Verified safe points | Human request and verification pending |
| D7 | Cited event text / official bulletins | Verified road closures | Human curation pending |

Keep one row per actual source in `data/clean/sources.csv`, using the source template.
Public access does not establish permission to redistribute the dataset.
**Decision §6.3, Raynald 2026-10-13:** the public plugin ZIP excludes `sample_data`.
DKI boundary and PPID redistribution permission has not been confirmed. Real working
inputs and the separate `dist/km_flood_priority-local-data.zip` remain local and
gitignored. The latter is for a lecturer attachment only if the lecturer authorizes
it; it must not be committed or publicly released. The public build's Load sample
data action explains this decision and points to README → Reproduce from scratch.

## Snapshot provenance

| File | SHA-256 |
|---|---|
| `rw_kampung_melayu_20261012.geojson` | `3cc01656f67ae4fe8f4f7df32302b7580c2628882368db9ecf752d4e19c7ac6d` |
| `kelurahan_kampung_melayu_20261012.geojson` | `f03e9d0091df14e62180774bc82dca910986956f0a897110ce37e4eb817670af` |
| `jakarta_timur_kelurahan_20261013.geojson` | `b517ad6556e75ae3fea29c190067f3d2ada8b282650bb9e85f2f96e0c6b411c4` |
| `REKAP_BANJIR_TAHUN_2025.pdf` | `d1f070b4460f79733b5290abf8857200884eaa4ab24db65665d38c2b767a9708` |

Each raw snapshot has a `.meta.json` containing the full query, retrieval timestamp,
endpoint and checksum. The OSM bbox was derived by QGIS from the official boundary
buffered by 1000 m in EPSG:32748, then transformed to EPSG:4326. The fetched bbox
contains 4,483 road ways and 46,640 building ways before clipping; these are context
features, not counts of populated houses or flood exposure.

The 2026-10-13 locator acquisition queries D4 layer 85 with
`wadmkk='JAKARTA TIMUR'`: 65 indicative kelurahan polygons in EPSG:32748. This is
context for F1 only; it does not add event evidence or change the nine RW units.
The study marker is derived from the Kampung Melayu boundary, not a surveyed point.

Boundary validation in QGIS measured 47.989568 ha. The dissolved RW/boundary area
ratio was 1.000000000008, within the required ±5%; the difference from the cited
47.83 ha was within ±15%. Every prepared administrative geometry was valid.

The prepared GeoPackage contains 9 RW, 1 kelurahan polygon, 3,154 road features,
34,617 building features and 440 candidate safe points, all in EPSG:32748. Every
candidate remains `verified=N`; these counts do not establish evacuation suitability.

The accepted PPID table contains source dates in 2025 only, with direct RW labels
04/05 and 07/08. Normalization yields 56 RW rows with zero schema errors and zero
duplicates. All 28 source rows are Y/RW under the user-authorized delegated review
exception documented in the execution spec. Each source row cites the PDF page, table and
source NO. Water-height qualifiers (Banjir/Genangan) are preserved in notes. Affected
KK/people are shared source totals and cannot be summed over exploded RW copies.

Accepted event-year coverage is **2025 only**. The 2020 listing does not establish
accepted Kampung Melayu event records for other years. Source NO 15 (6 July) and
NO 20 (7 July) have evacuation counts exceeding affected counts; these source
inconsistencies are noted, while JUMLAH TERDAMPAK values remain unchanged. Nihil in
affected KK/people remains NULL for 28 February, 5 August and 10 August.

## Satu Data granularity audit — 2026-10-12

The national catalog embeds the publisher's direct CSV export URLs. They were
downloaded unchanged from `satudata.jakarta.go.id`, with retrieval metadata and
SHA-256 sidecars in `data/raw/satudata/`. The download work is complete for the four
located exports; their contents must not be treated as automatically usable events.

| Dataset label | Catalog | Source rows / target-area rows | Current use |
|---|---|---|---|
| 2020 | [2020 catalog](https://data.go.id/dataset/dataset/data-kejadian-bencana-banjir-di-provinsi-dki-jakarta-tahun-2020) | 902 / 51 | Source review required: 33 target rows lack a single full date, 18 full dates conflict with the period field, 36 have RW=0; issue counts overlap |
| 2021 | [Older general-disaster listing](https://proxyapps.data.go.id/dataset/?_tags_limit=0&organization=provinsi-dki-jakarta&tags=Provinsi) | CSV not acquired | A 2021 general-disaster title was located; an eligible flood event export was not located in this bounded audit; availability unresolved |
| 2022 | No eligible event export located in this bounded audit | CSV not acquired | Availability unresolved; hazard-point/count datasets are not dated RW events |
| 2023 | [2023 catalog](https://data.go.id/dataset/dataset/data-kejadian-bencana-banjir-tahun-2023) | 194 / 6 | Context only: monthly aggregates lack event dates and actual RW codes |
| 2024 | [2024 catalog](https://data.go.id/dataset/dataset/data-kejadian-bencana-banjir-tahun-2024) | 260 / 9 | Context only: monthly aggregates lack event dates and actual RW codes |
| General export, publisher periods 2025/2026 | [General catalog](https://data.go.id/dataset/dataset/data-kejadian-bencana-banjir1) | 392 / 9 | Context only: monthly aggregates; the rolling export also contains 2026 data |

The target filter checks both Kampung Melayu and Jatinegara. For example, the 2020
export records `periode_data=201912` alongside `tanggal_kejadian=06/12/2020`.
Other rows list several dates and several RWs without stating which RW was affected
on which date. No Cartesian expansion, inferred calendar day, or inferred RW is made.
The `jumlah_rw_terdampak` and `jumlah_terdampak_rw` fields are counts, not unit codes.
The converter now rejects mappings from those fields to `rw_raw`.

| Raw snapshot | SHA-256 |
|---|---|
| `satudata_2020_20261012.csv` | `fce1271e61dee02b004ac384355072871a9dd0aa8753120fcc92b52853d1fe29` |
| `satudata_2023_20261012.csv` | `e6405f578609ccf5688fa69af224bf7c3200391ef961d97aab2b1062683b7ea1` |
| `satudata_2024_20261012.csv` | `679a1bdcee4d557c8244c7530f3c789f02605870bd7d6dae74018be1097859f8` |
| `satudata_general_20261012.csv` | `56985260f278425aa01dd73a8f8208dee90f90dce78d0564da151abef5c13f1f` |

Reproduce the local audit with `scripts/audit_satudata.py` (command in the README).
Detailed source row references are in `data/interim/satudata_audit.json`. The report
is an acquisition-quality audit, not a flood-priority finding. No canonical Satu Data
event CSV was created. These exports are excluded from the current PPID-only working
set, with 2021/2022 unresolved availability and other limitations recorded explicitly.
Future inclusion requires source resolution and a new acceptance, not inferred values.

For context only, the publisher periods 2019–2020 list RW 04/05/07/08 in many 2020
months, RW 01–03/06 within January–February 2020, and no explicit RW 09. The six
2020 period rows list: January 01–08; February 03–08; March/April/September
04/05/07/08; May 04/05/06/07/08. Dates remain unverified and none of these rows are
used in classification. This shows that NO_RECORD and one episode in RW 07/08 are
limitations of the accepted 2025 working set; it does not prove no flooding in RW 09.

