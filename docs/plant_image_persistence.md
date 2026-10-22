# F101 — explicit PLOT image import/save and portable project copies

This slice supplies the image import/save use case and project persistence for
the F100 components. It does not yet integrate production PLOT Open/Save controls;
the main PLOT entry remains disabled until the original window is usable.

## Reference contract and deliberate storage improvement

The untouched reference plant_layout.py loadSelectedPlantImage (line 6486) previews
PNG/JPG without saving. savePlantImage (line 7728) copies to a plant-name sidecar
and updates Plant metadata separately. loadPlantImage (line 7794) reconstructs the
sidecar location and clears the map if absent. The new implementation preserves
separate preview and explicit Save operations, original encoded pixels, exact
plant identity, and the existing image-space canvas. No image is persisted just
by selection, decoding or preview.

New-format projects store encoded image bytes in their SQLite file. This deliberate
internal storage change keeps Save As/Backup self-contained and makes replacement
atomic instead of coordinating a file copy and separate database update. Plant
names are SQL parameters, never paths or filenames. The reference project format
and sidecars are not changed or imported by this slice. Legacy import must resolve
sidecars on a copy when that stage is reached.

## Boundaries and transaction behavior

PlantLayoutImage owns immutable nonempty encoded bytes without Qt, Pillow, paths,
unit conversion or rendering. import_plant_image reads .png/.jpg (case insensitive),
checks actual PNG/JPEG format and decodes the full image using approved Pillow
11.3.0, retaining the exact original bytes. Filesystem/decoder errors propagate.
Pillow is imported only for the image feature, not for older project startup or
the portable core. No dependency version or allowed range changed.

save_plant_layout validates the selected hierarchy/shift before invoking the typed
writer port. The owned AssessmentProjectFile checks the current saved plant under
its transaction and persists through PlantLayoutStore. read/load_plant_image serves
the existing reader port. Missing image records return None; invalid records reject
loading rather than masquerading as a missing map. Open and snapshots validate
persisted image data. Pending assessment source, history and settings are untouched.

Format nine adds plant_layout_images(plant PRIMARY KEY, image BLOB). Explicit first
image save upgrades a full format-seven/eight project in the same transaction:
seven gains one nullable details record, eight retains existing details. Ordinary
open/read/preview leaves old versions untouched. Partial formats one through six
are not implicitly upgraded for PLOT. Explicit format-nine fixture creation is
supported; normal New still creates eight until an image is saved.

SQL failure after image insertion rolls back the new schema, metadata version and
previous image together. The in-memory version changes only after commit; retry
works. Save As editing metadata preserves version nine, and Backup/ordinary copies
retain all map bytes. Hierarchy replacement cannot silently orphan a saved map.
Plant deletion with a map currently requires a future explicit image-removal policy;
no unrequested deletion control is introduced here.

## Verification and remaining UI work

Fourteen new cases exercise PNG/JPG across formats seven/eight/nine, read-only
preview, explicit save, literal path-like names, original dimensions/bytes, removed
external source, reopen, Save As metadata and Backup. Injected SQL failures verify
both schema upgrade and replacement rollback. Invalid/unsupported/missing files,
unknown plants, partial/closed repositories, plant-removal guards and corrupt
stored images are checked. Three native component paths preserve pending invalid
LiFFT/DUET/ST input, current session state and settings.

All 797 native tests pass, 96.41% combined statement/branch coverage. Ruff/format,
strict mypy over 165 source files, architecture and wheel/sdist pass. No production
window or layout code changed. Additional xcb component captures inspect preview,
saved/reloaded map and enlarged replacement; full image corners remain visible.
The isolated extracted wheel checks actual modal scope selection, preview/save,
removed source, replacement/resize, corrupt-import retention, reopen and format-nine
Save As/Backup. All 500 reference hashes and the approved dependency lock match.
Evidence: f101_validation.json, artifacts/f101-check.log, artifacts/plant-image-save
and archived reference/f101-verify.py.txt.

Next: compose the original PLOT window and connect its existing Open/Save tool-rail
controls, scope and read-only map loading to these tested APIs. Add original worker/
job markers, filters and summaries incrementally. Current fixture/API workflows
are not final production UI acceptance. Metric/imperial display and legacy sidecar
import remain later PLOT acceptance requirements; image pixels are unit-independent.
JROT follows PLOT, with the owner's recorded CBC single-tool/HiGHS multi-tool route
and GLPK excluded. No solver was installed or modified. Overall application
completion percentage and finish date remain unvalidated.
