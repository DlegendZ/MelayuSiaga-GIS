# Human tasks

## Start now: lecturer alignment (2 minutes to send)

Send this draft yourself; the agent will not contact the lecturer:

> Pak Fabian, kelompok kami terdiri dari Raynald Arvan Lim, Alden Viriya Tanudjaja,
> dan Moses Handoyo (3 orang). Apakah jumlah anggota ini diperbolehkan? Kami memilih
> Kota Jakarta Timur dengan fokus analisis RW Kelurahan Kampung Melayu, Jatinegara,
> dan produk berupa plugin QGIS untuk prioritas verifikasi berdasarkan catatan banjir.
> Apakah framing dan produk ini sesuai? Untuk technical brief maksimal 2 halaman,
> apakah kami gunakan bahasa Inggris?

Implementation continues while this confirmation is pending, as permitted by Phase 0.

## Phase 1: download and verify real event data

1. Download the 2025 Jakarta Timur PPID flood recap PDF from the source linked in the
   research document. Save it unchanged in `data/raw/ppid/`; send its filename and URL.
2. Open the [2020 Satu Data dataset](https://satudata.jakarta.go.id/open-data/detail/data-kejadian-bencana-banjir-di-provinsi-dki-jakarta-tahun-2020).
   Download the CSV to `data/raw/satudata/`. Check the same title for each year 2021–2025;
   record unavailable years explicitly. Send the original filenames and source URLs.
3. Copy `data/templates/sources_template.csv` to `data/clean/sources.csv` and record
   each download's source ID, title, publisher, URL, download date, years, and stated terms.
4. After the agent produces the PPID draft, compare every row with its PDF page.
   Correct the values, set `verified=Y` only after checking, and save the checked file
   as `data/clean/events_ppid_2025.csv`.
5. Use the safe-point and closure templates for source-backed values. Candidate sites
   remain `verified=N`. Missing verified evidence is allowed and yields UNKNOWN access.

## Later gates

- Before Phase 4: confirm safe points/closures, or explicitly proceed with UNKNOWN.
- Before Phase 5: decide whether official boundaries/events may be redistributed.
- Phase 3 testing: start Docker Desktop (Linux containers) or provide the installed QGIS path.
- Phase 6: perform the Windows acceptance and a clean-clone reproduction by another member.

