# M02 — Worker Management acceptance complete

M02 earns its fixed 1.5 points: **80.5/100 overall; 2/12 milestones complete;
6.5/26 remaining-baseline points earned, 19.5 still to earn**. M03 Organization
and Jobs is next, not started in this batch. No milestone/weight/scope expansion.

## M02.1 — original visible form

Read-only original WorkerWindow constructors, layout and stylesheet were compared
under the same approved Qt baseline at 1360×760 and 1600×900 in both unit systems.
The four states are selected/collapsed, expanded/populated, assignments and new.
Sixteen cases match the compared named visible control types, rectangles, button
icon sizes and text after restoring the original `Note:` notification prefix.
Spanish uses `Nota:` through the existing catalog. No layout or control redesign.
Original database callbacks and hidden experimental tabs are stubbed in this layout
oracle. Matched fixture values isolate form geometry; this is not validation of
legacy data-unit inference. Directory population/selection in the oracle is fixture
projection; real directory paging/filter/selection behavior reuses existing tests.

Representative individual original/new images, EN/ES details and assignments,
minimum/enlarged states and placement selection were visually inspected. The final
independent wheel adds nine full-window captures covering EN metric/ES imperial
Save success, populated details, assignments, new/collapsed, invalid-ID/enlarged and
an empty project, plus two expanded assignment-option views. All eleven packaged
PNGs were inspected. Notification messages remain readable; optional fields, tabs,
buttons and directory stay organized at both sizes. No integrated VTK/card/footer
region changed: the modal leaves those existing controls in the owning main window.

## M02.2 — units and complete editing workflows

Existing F72 tests are reused for optional details, Save/Cancel/reopen, directory
filter/paging, protected deletion, assignment creation decisions and SQLite rollback
with retry. Strengthened unit cases now check height AND weight, birth/hiring dates,
sex, reopen in the opposite unit system and exact unchanged canonical Save values.
Names and other text remain preserved independently of translated captions.

Three new integrated modal regressions cover LiFFT, DUET and ST. Choosing another
worker's existing assignment returns to that worker's current assessment for the
active tool. Unsaved worker-name edits survive the nested placement picker and are
discarded on Close. Independent database reopen proves worker catalogs, assignment
catalog, history ownership and the previous assessment source remain unchanged.
Existing reassignment tests prove the earlier assignment is closed and retained,
the new assignment is active, and historical assessments keep their original owner.
No source formula or assessment result was changed.

Validation: **12 focused cases passed; 1,157 total tests, 96.49% coverage**. Ruff,
format, strict mypy, architecture and Hatchling build passed. The independent wheel
passed both units, EN/ES, Save/independent reopen, new/Cancel, invalid/Close,
assignment options and empty-project checks. All 500 reference hashes and uv.lock
are unchanged. No dependency/environment installation.

## Existing limits remain in their assigned milestones

F72 already documented that original Worker.height/weight store raw form numbers
without per-row unit identity. Original saveWorker/loadWorkerDetails confirms raw
write/read; the importer comment that all rows are necessarily cm/kg is not proof.
M04.3 must review conversion policy against actual original-data evidence before
final compatibility acceptance. No conversion data or code changed during M02.
This is the existing original-data acceptance work, not a new milestone or blocker
to verified new-format body-unit workflows.

Assignment-protected worker deletion remains the documented conservative behavior;
M02 does not enable original cascading destruction of historical owners. Hidden
experimental anthropometry stays under M11's existing feature-disposition review,
with no new visible controls. Whole-app shared localization/VTK/platform checks
remain M09/M12. These were not certified by the worker-form comparison.

Evidence: m02_validation.json; artifacts/m02-comparison/, artifacts/m02-packaged/,
m02-focused.log, m02-check.log, m02-wheel.log. Execution scripts are retained in
docs/reference/m02-*.py.txt. No repeated validation is needed absent a new change.
