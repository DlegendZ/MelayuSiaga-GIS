# Independent reproduction from a clean clone

The Windows style issue is resolved. The next human gate is an available group
member following the README from a clean clone, per EXECUTION_SPEC §§12 and 14.
Alden or Moses can run it; Raynald does not need to assign a name in advance.
Record the actual tester and operator after execution. Do not count the agent's
bundle/clone preparation as the independent student check.

**Time:** allow 45–60 minutes for the complete README path with fresh data
preparation; 20–30 minutes for the accepted-snapshot pipeline path. QGIS/Git
installation time is separate. The snapshot path alone does not establish fresh
Windows acquisition/preparation. No push is required for either path.

## Five steps on the tester's Windows laptop

1. Copy `dist/MelayuSiaga-GIS-reproduce.bundle` and its adjacent `.info.txt` from
   Raynald's laptop to your Downloads folder. This is a local Git source/history
   bundle, not a public release. It excludes untracked datasets and dist artifacts.
   Have Git and QGIS 3.44 LTR available. Open **OSGeo4W Shell** and check:

   ```bat
   git --version
   where python-qgis-ltr
   python-qgis-ltr -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
   ```

   If Git or the launcher is unavailable, record the message and ask Raynald for
   setup help. README explains the full-path launcher alternative. Do not install
   Python packages into QGIS.

2. Clone the bundle into a **new directory** using these cmd/OSGeo4W commands:

   ```bat
   git clone --branch codex/flood-priority-foundation "%USERPROFILE%\Downloads\MelayuSiaga-GIS-reproduce.bundle" "%USERPROFILE%\MelayuSiaga-dryrun"
   cd /d "%USERPROFILE%\MelayuSiaga-dryrun"
   git log -1 --oneline
   git status --short
   ```

   Confirm the commit agrees with the `.info.txt` file and initial status is empty.
   If that destination already exists, choose a new name; preserve previous work.
   There should be no prepared inputs.gpkg or event CSV in this clean checkout.

3. Follow [README → Windows with QGIS Python](../README.md#windows-with-qgis-python)
   in order: fetch_admin_boundaries → build_inputs --prepare-bbox-only → fetch_osm
   → build_inputs, then prepare the event/source CSVs and merge_sources. This uses
   QGIS's bundled Python and standard library, with no additional packages.
   Download the PPID original manually and check its documented checksum.
   Fresh OSM counts can differ; record retrieval dates and exact source IDs.

   Group members may reuse the already accepted 28-row event CSV from the separate
   local data ZIP: copy its events_all.csv to data/clean/events_ppid_2025.csv and
   keep its existing notes/NULLs. Use its sources.csv as the starting registry,
   then record the fresh boundary/OSM snapshot IDs and metadata required by README.
   This reuses accepted transcription; no new PPID row review is required for the
   unchanged working set. Keep the ZIP separate while building new inputs.

   Alternatively, to check only the accepted snapshot, use its inputs.gpkg,
   events_all.csv and sources.csv as local inputs. Record **snapshot pipeline only**
   in the report and leave fresh acquisition/preparation unchecked. The local data
   ZIP stays private; lecturer attachment requires permission, and it is never a
   public release asset.

4. Build and install the plugin from the clean clone:

   ```bat
   python-qgis-ltr scripts/package_plugin.py
   ```

   Install its dist/km_flood_priority-1.0.0.zip, restart QGIS, create a new project
   and load all five inputs.gpkg layers. Run full pipeline using the
   [parameter table](USER_GUIDE.md#install-and-run-on-windows), defaults and a new
   output filename data/processed/independent_dryrun.gpkg. Inspect results without
   reopening: priority/safe points/routes Categorized; roads/boundary styled as
   designed; five postProcessLayer and five restored log entries. For the unchanged
   accepted events, expect 28 source / 56 normalized rows, zero errors, 2 HIGH /
   2 MEDIUM / 5 NO_RECORD and all access UNKNOWN. RW 04/05 share source rows;
   never add their episode counts. Record differences rather than changing rules.

5. Fill the report below, capture the actual pipeline log and styled map/priority
   table, and send the report and evidence to Raynald. Preserve your output package
   locally. Compare findings/attributes with Phase 4; generated fid/run_id, timing
   and GeoPackage byte hashes may differ. A failure remains open until traced and
   corrected; completing a snapshot-only test leaves acquisition/preparation pending.

## Result report to copy

```text
Independent reproduction report
Tester name:
Actual operator (include delegation, if any):
Date:
QGIS version:
Clean-clone commit:
Mode: complete README / snapshot pipeline only
Fresh acquisition and input preparation: PASS / FAIL / NOT RUN
Event CSV: accepted unchanged / newly checked (describe)
Input validation: RW count, geometry/CRS checks, source IDs
Pipeline: seconds; rows in/normalized; errors/warnings
Findings: HIGH/MEDIUM/VERIFY/NO_RECORD counts; access statuses
Styles: immediate Categorized priority; five entry/restoration logs
Phase 4 comparison: matched findings / differences (describe)
Evidence and output paths:
Errors and steps needed to reproduce them:
Overall result: PASS / FAIL / PARTIAL
```

The group's two-page brief layout/PDF and lecturer framing/language alignment remain
separate human steps. Remote CI, tag and GitHub Release remain deferred by Raynald's
no-push instruction. The optional video is not a blocker for this reproduction check.
