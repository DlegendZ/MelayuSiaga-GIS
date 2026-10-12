# Human tasks

## Start now: verify the PPID draft (10–15 minutes)

The user saved `data/raw/ppid/REKAP_BANJIR_TAHUN_2025.pdf`. Extraction has completed:
28 draft rows, all `verified=N` and `location_confidence=UNKNOWN`.

1. Open `data/interim/ppid_2025_draft.review.md` and the original PDF side by side.
2. Check each cited page/NO against date, ALAMAT, RW/RT, water height, affected KK and
   people. Use the **JUMLAH TERDAMPAK** columns; evacuation totals are separate.
3. Correct mismatches. Source totals shared between RWs are not allocated per RW.
   `Nihil` remains NULL; the source does not specify a next-day date for receding times.
4. For rows you checked with explicitly stated RW codes, set `location_confidence=RW`
   and `verified=Y`; leave unchecked rows at N. Save UTF-8 comma-separated CSV as
   `data/clean/events_ppid_2025.csv`, or tell the agent exactly which rows you checked
   and any corrections. Only your check can authorize these verification flags.
5. Start with PDF page 3, NO 17: 29 January 2025, RW 04/05, 130 cm, 91 KK, 280 people
   (under 2 minutes). Then work through the remaining references in the review table.

Required by `EXECUTION_SPEC.md` §6 D1: "[H] checks every row against the PDF,
sets `location_confidence`, sets `verified=Y`". Extraction and agent visual review
do not satisfy that human acceptance step.

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
   have been registered. Complete the review above.
2. Open the [2020 Satu Data dataset](https://satudata.jakarta.go.id/open-data/detail/data-kejadian-bencana-banjir-di-provinsi-dki-jakarta-tahun-2020).
   Download the CSV to `data/raw/satudata/`. Check the same title for each year 2021–2025;
   record unavailable years explicitly. Send the original filenames and source URLs.
3. Append to the existing `data/clean/sources.csv` (or copy the source template if absent) and record
   each download's source ID, title, publisher, URL, download date, years, and stated terms.
4. After checks, tell the agent which Satu Data years were actually available or missing.
   Recorded 2025 dates in the PPID draft do not establish multi-year coverage.
5. Use the safe-point and closure templates for source-backed values. Candidate sites
   remain `verified=N`. Missing verified evidence is allowed and yields UNKNOWN access.

## Later gates

- Before Phase 4: confirm safe points/closures, or explicitly proceed with UNKNOWN.
- Before Phase 5: decide whether official boundaries/events may be redistributed.
- Docker Desktop was started by the user. QGIS 3.44.15-noble was downloaded for development.
  For final Windows manual acceptance, install QGIS 3.44 LTR from [QGIS Downloads](https://qgis.org/download/).
- Phase 6: perform the Windows acceptance and a clean-clone reproduction by another member.

