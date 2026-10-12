# Human tasks

## PPID review accepted — 2026-10-12

Raynald explicitly accepted Claude's independent second check and authorized all
28 rows as `verified=Y`, `location_confidence=RW`. This is delegated AI review,
not a claim of direct human visual checking. The original draft remains N/UNKNOWN.

The checked table is `data/clean/events_ppid_2025.csv`, with review provenance in
the adjacent `.review.json`. Every row records
`checked 2026-10-12 by Claude (delegated by Raynald)`. Three Nihil impact pairs remain
NULL. Source NO 15 (6 July) and NO 20 (7 July) retain the affected totals 44 KK/125
people and note that the source evacuation totals exceed them.

`data/processed/events_all.csv` passes validation: 28 source rows, 56 normalized
RW rows, zero schema errors, zero duplicates, all Y/RW, recorded coverage 2025.
No further PPID row review is required for this accepted working set.

## Lecturer alignment (2 minutes to send)

Send this draft yourself; the agent will not contact the lecturer:

> Pak Fabian, kelompok kami terdiri dari Raynald Arvan Lim, Alden Viriya Tanudjaja,
> dan Moses Handoyo (3 orang). Apakah jumlah anggota ini diperbolehkan? Kami memilih
> Kota Jakarta Timur dengan fokus analisis RW Kelurahan Kampung Melayu, Jatinegara,
> dan produk berupa plugin QGIS untuk prioritas verifikasi berdasarkan catatan banjir.
> Apakah framing dan produk ini sesuai? Untuk technical brief maksimal 2 halaman,
> apakah kami gunakan bahasa Inggris?

Implementation continues while this confirmation is pending, as permitted by Phase 0.

## Phase 1: download and verify real event data

1. Preserve the downloaded PPID original unchanged; its source link and checksum
   have been registered. PPID review is accepted as recorded above.
2. The agent downloaded the located Satu Data exports (2020, 2023, 2024, general
   2025/2026) to `data/raw/satudata/` and audited them. Do not redownload those files.
   The [source audit](DATA_SOURCES.md#satu-data-granularity-audit--2026-10-12) documents
   why these exports are excluded from the current event table.
   Eligible dated RW events for 2021/2022 remain unresolved; 2023–2025 exports are
   monthly context only, and the 2020 export has date/period conflicts.
3. Append to the existing `data/clean/sources.csv` (or copy the source template if absent) and record
   each download's source ID, title, publisher, URL, download date, years, and stated terms.
4. The accepted working set currently uses PPID 2025 only. Additional Satu Data
   sources can be investigated and added later if dated RW evidence is resolved.
   No multi-year coverage or missing-year absence is asserted.
5. Use the safe-point and closure templates for source-backed values. Candidate sites
   remain `verified=N`. Missing verified evidence is allowed and yields UNKNOWN access.

## Later gates

- Before Phase 4: confirm safe points/closures, or explicitly proceed with UNKNOWN.
- Before Phase 5: decide whether official boundaries/events may be redistributed.
- Docker Desktop was started by the user. QGIS 3.44.15-noble was downloaded for development.
  For final Windows manual acceptance, install QGIS 3.44 LTR from [QGIS Downloads](https://qgis.org/download/).
- Phase 6: perform the Windows acceptance and a clean-clone reproduction by another member.

