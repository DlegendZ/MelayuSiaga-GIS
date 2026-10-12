# Data sources and licenses

Official boundaries and an OSM snapshot were acquired on **2026-10-12**. The user
downloaded the PPID PDF; 28 source-located event rows were extracted as unverified
drafts. Human verification and Satu Data availability checks are still pending. Working downloads are
gitignored until redistribution terms are confirmed.

| ID | Publisher / source | Use | Retrieval and terms |
|---|---|---|---|
| D1 | [PPID Kota Jakarta Timur, 2025 flood recap](https://timur.jakarta.go.id/ppid/storage/files/setko-260609-075654-x938X6Z0-REKAP_BANJIR_TAHUN_2025_compressed.pdf) | Recorded events | Human download completed 2026-10-12; 23 pages, 28 draft rows; verification and redistribution terms pending |
| D2 | [Satu Data Jakarta](https://satudata.jakarta.go.id/open-data/detail/data-kejadian-bencana-banjir-di-provinsi-dki-jakarta-tahun-2020) | Multi-year events | Available years 2020–2025 and actual CSV columns must be checked |
| D3 | [Dinas Cipta Karya, Tata Ruang, dan Pertanahan DKI Jakarta — RW](https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted/ADMINISTRASI_AR_RW/FeatureServer/18) | RW analysis units | Acquired 2026-10-12, 9 RW (01–09); redistribution permission unresolved |
| D4 | [DKI kelurahan layer 85](https://gis-dpmptsp.jakarta.go.id/arcgis/rest/services/Hosted/Batas_Administrasi_Kelurahan_DKI_Jakarta/FeatureServer/85) | Boundary | Acquired 2026-10-12, one polygon; indicative administrative boundaries |
| D5 | [OpenStreetMap contributors / Overpass](https://overpass-api.de/api/interpreter) | Roads, buildings, candidate sites | Acquired 2026-10-12; © OpenStreetMap contributors, ODbL; 440 candidates are unverified |
| D6 | BPBD / Kelurahan Kampung Melayu | Verified safe points | Human request and verification pending |
| D7 | Cited event text / official bulletins | Verified road closures | Human curation pending |

Keep one row per actual source in `data/clean/sources.csv`, using the source template.
Public access does not establish permission to redistribute the dataset. Students
must decide redistribution before Phase 5; exclude sample data while terms are unclear.

## Snapshot provenance

| File | SHA-256 |
|---|---|
| `rw_kampung_melayu_20261012.geojson` | `3cc01656f67ae4fe8f4f7df32302b7580c2628882368db9ecf752d4e19c7ac6d` |
| `kelurahan_kampung_melayu_20261012.geojson` | `f03e9d0091df14e62180774bc82dca910986956f0a897110ce37e4eb817670af` |
| `REKAP_BANJIR_TAHUN_2025.pdf` | `d1f070b4460f79733b5290abf8857200884eaa4ab24db65665d38c2b767a9708` |

Each raw snapshot has a `.meta.json` containing the full query, retrieval timestamp,
endpoint and checksum. The OSM bbox was derived by QGIS from the official boundary
buffered by 1000 m in EPSG:32748, then transformed to EPSG:4326. The fetched bbox
contains 4,483 road ways and 46,640 building ways before clipping; these are context
features, not counts of populated houses or flood exposure.

Boundary validation in QGIS measured 47.989568 ha. The dissolved RW/boundary area
ratio was 1.000000000008, within the required ±5%; the difference from the cited
47.83 ha was within ±15%. Every prepared administrative geometry was valid.

The prepared GeoPackage contains 9 RW, 1 kelurahan polygon, 3,154 road features,
34,617 building features and 440 candidate safe points, all in EPSG:32748. Every
candidate remains `verified=N`; these counts do not establish evacuation suitability.

The PPID draft contains source dates in 2025 only, with direct RW labels 04/05 and
07/08. Normalization yields 56 RW rows with zero schema errors; this is a draft
validation, not accepted findings. Each source row cites the PDF page, table and
source NO. Water-height qualifiers (Banjir/Genangan) are preserved in notes. Affected
KK/people are shared source totals and cannot be summed over exploded RW copies.

Accepted year coverage remains pending human review and the Satu Data availability
audit. The 2020 listing does not establish Kampung Melayu records for other years.

