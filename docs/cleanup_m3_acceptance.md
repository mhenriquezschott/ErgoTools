# M3 acceptance — owned file and resource names

**M3 complete, 4/6 cleanup milestones (66.67%).** M4 is authorized in the same
batch and now starts; M5 remains separate. No dependency, formula or UI redesign.

429 owned files renamed: 42 packaged resources and 387 documentation records.
Names now use descriptive English snake_case, including job_management.png,
view_3d_zoom_light.png, lower_back.stl, body_avatar.stl and user_guide_en.html.
Code module names already followed snake_case. Icon identities, runtime resource
lookups, help/cache names, documentation links and ledger references are synchronized.
All 71 reference-manifest assets retain exact original bytes and immutable original
reference_path provenance. Original project paths/names/data are untouched.

The new tools.check_naming gate rejects invalid owned names and case-insensitive
collisions; required check.sh includes it. Three focused negative tests cover bad
resource/document names, explicit external conventions and portable collisions.
The mapping/exceptions are in [naming evidence](../artifacts/cleanup-m3-naming.json).
Standard README/AGENTS/STATUS/package markers, frozen docs/reference source evidence,
original fixture sidecars and generated cache/build/evidence names retain necessary
conventions. The captured tests/fixtures/reference_plot_load.py.txt is original
source text, not an executable maintained module. No broad owned-resource exception.

Required full gate: **1,267 tests passed, 96.36% coverage**, Ruff/format, strict
mypy (248 modules), architecture/naming zero violations and builds pass. Resource/
help/body/naming focused checks passed 22 tests and 81 subtests. The extracted wheel
matches every current source/resource byte, excludes the external tool, and runs
integrated EN/ES LiFFT/DUET/ST, VTK, PLOT/JROT and Save As/Backup with converter imports
blocked. All ten captures inspected; unchanged asset appearance/geometry confirmed.
PLOT capture gauges were animating and are not numerical comparison evidence.
Reference 500 hashes and approved lock unchanged. Existing calculator and native
fixture evidence is reused; no unrequested schema or visual repair was introduced.

See [validation](cleanup_m3_validation.json), [current progress](cleanup_progress.json)
and [standards](coding_standards.md). M4 must still complete every substantive
file/function/constant review; naming success does not imply documentation acceptance.
