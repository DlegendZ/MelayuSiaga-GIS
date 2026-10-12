# Figure and Windows evidence slots

F1/F2/F3 are generated from the real accepted working set by
`scripts/render_figures.py`. F2's full claim limits and robustness are in
[F2_caption.md](F2_caption.md). Map exports do not substitute for S1/S2 screenshots.

S1_pipeline.png and S2_results.png are now supplied: genuine QGIS 3.44.15 Windows
screenshots, operated by Claude under Raynald's instructions (reported 2026-10-13).
S2 shows the styled package after reopening, before the GUI automatic style fix;
it does not claim a manual rerun of that fix. Both screenshots are embedded in README.
The demo remains pending. Preserve these originals; record new captures separately.

Style recheck v2 PASSED on 2026-10-13, QGIS 3.44.15 Windows, reported by Raynald:
**Claude operated Raynald's laptop under Raynald's instructions**. The original
`dist/local-data/S2_style_recheck_v2.png` and `S2_style_recheck_v2_log.jpg` were copied
unchanged here and embedded/linked in README. They show Categorized priority and
five callback/restoration logs after a 1.16 s run, without reopening. They are
acceptance evidence, not replacements for the original map/attribute-table S2.

## Capture on Windows (5 minutes after installation)

1. Install `dist/km_flood_priority-1.0.0.zip` in QGIS. Open Processing Toolbox and
   expand KM Flood Priority. Open Run full pipeline… with the actual local inputs.
2. Capture **S1_pipeline.png** with the provider and pipeline dialog visible;
   the input parameters must be legible. Use Windows Snipping Tool, then save here.
3. Run the pipeline to a new output. Open the styled result map and the
   `rw_priority` attribute table. Show RW, episode counts, classes and access.
4. Capture **S2_results.png** with both map and attribute table visible. Record
   QGIS version, tester, date, pass/fail and any correction in `docs/PROGRESS.md`.
5. Record a 30–60 second **demo.gif** or **demo.mp4**: ZIP installation → pipeline
   parameters and Run → resulting map and attributes. Keep captions explicit:
   recorded 2025 verification priority; UNKNOWN access; paired RW counts not summed.

After the recording exists, enable its prepared Markdown embed in README and
remove the corresponding pending entry. For MP4, use a normal download/play link.
Do not create substitute screenshots or label generated maps as UI evidence.

The Windows acceptance checklist and current parameter table are in
[USER_GUIDE](../USER_GUIDE.md). Installation may take 10–15 minutes separately from
the five-minute evidence capture. A different group member must also perform the
clean-copy reproduction before final submission acceptance.
