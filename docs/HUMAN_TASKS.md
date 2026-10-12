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

## Group-size exception confirmed — 2026-10-13

Raynald confirmed that this group has an exception permitting all three members.
Group-size approval is resolved; do not ask for it again.

## Lecturer framing/language alignment (2 minutes to send)

Send this draft yourself; the agent will not contact the lecturer:

> Pak Fabian, kelompok kami terdiri dari Raynald Arvan Lim, Alden Viriya Tanudjaja,
> dan Moses Handoyo, sesuai pengecualian kelompok tiga orang kami. Kami memilih
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

## Phase 4 accepted and Phase 5 licensing decided — 2026-10-13

Raynald accepted the real results and framing. All access remains UNKNOWN with the
verified-only defaults. The public plugin ZIP must exclude sample_data: DKI boundary
and PPID redistribution permission is unconfirmed. This licensing decision is complete.
`dist/km_flood_priority-local-data.zip` is separate, local and gitignored; attach it
to the lecturer only if the lecturer permits it. Never commit or release that bundle.

## Remaining human gates

- Safe-point/closure verification can improve future runs; the accepted run proceeds
  with UNKNOWN and makes no route safety claim.
- Windows QGIS 3.44.15 pipeline/style acceptance is complete. Style recheck v2
  passed in 1.16 s, operated by Claude on Raynald's laptop under his instructions,
  with five callback/restoration logs and Categorized priority without reopening.
  No further style recheck is needed for this unchanged plugin build.
- Record the optional 30–60 second demo using [this checklist](figures/README.md).
- Phase 6: another member performs a clean-copy reproduction using
  [the clean-clone guide and report](REPRODUCIBILITY_CHECK.md); tester selection
  can wait until Alden or Moses is available. Then the group finalizes
  the [brief draft](TECHNICAL_BRIEF.md) to at most two A4 pages and exports the PDF.
  Raynald authorized merge/push on 2026-10-13; remote CI/release are being prepared.

