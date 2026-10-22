# Save availability — owner-requested workflow improvement

The owner requests main Save disabled when nothing needs saving and enabled for
unsaved data. The previous loaded-project-only policy is replaced in the integrated
main toolbar, underlying command button and Project menu by one pure projection of
existing project dirty tracking, temporary first-Save state and pending task input.
No extra dirty flag, history engine, automatic calculation or persistence path exists.
Diagnostic harnesses retain their existing policy. Save As remains available.

Pending input enables Save before field completion, including invalid text so the
existing validation can explain the problem. Returning unaccepted text to the saved
value disables Save. Accepted changes enable it; Undo back to the saved data disables
it, while Redo away from that baseline enables it. Saving retains history: Undo of a
saved edit needs Save again, and Redo back to that newly saved state is clean.
Cancelled first Save and failed publication retain availability. Empty temporary
projects need first Save; a clean saved empty project does not. Worker/organization/
Job and analysis edits use the existing shared session notification, including edits
accepted while a management window remains open. View-only history is not data dirt.

Only two presentation modules, one new focused test module and an existing menu test change. The projection
reads no catalogue authorities, accepts no source and writes no database. Session
subscription uses the existing weak-method lifetime policy and ignores deleted native
windows. Existing pending validation and Save publication remain authoritative.
Changed modules/functions and test contracts are substantively reviewed; exact hashes
are in artifacts/save_availability_review/documentation_review.json and the maintained
review manifest/inventory. No dependency, schema, formula or reference changes.

Focused checks: 50 passed (20 new cases plus existing navigation/unified-save checks).
The first full gate found three historical assertions requiring Save disabled after
assessment deletion. Private deletion needs Save under the approved new behavior;
those expectations now require Save enabled and unsaved project data. Cancellation,
unique ownership/recreation, inputs and native reopen checks are retained. Corrected
menu plus new Save checks: 24 passed. The preceding 1,662-pass/3-failure gate is kept
separately as preliminary_check.log, not represented as final acceptance.
Coverage includes three tools, English/Spanish, metric/imperial, pending/no-op/invalid
inputs, first Save/cancellation, worker notification, failure retry, calculation and
Undo/Redo on both sides of Save. Native XCB/Xvfb :112 captures cover each tool in both
languages: clean saved, pending input and mouse-toolbar Save (18 captures). All eighteen
inspected through full-window overviews and enlarged toolbar strips, with an original
full-size LiFFT pending capture also inspected. Save becomes gray when disabled and
retains the existing blue icon when enabled; no geometry/style change or clipping.
VTK, gauges, task grid and bottom controls remain visible. Four additional native
Project menu captures (clean/dirty, EN/ES) were inspected at original crop resolution: Save
is gray when clean, enabled when dirty, and Save As stays enabled (22 total captures).

Final required native Linux gate: 1,665 passed, zero failures/skips, 94.34% coverage;
standards/types (265), architecture/naming, documentation/review and builds pass.
Independent wheel: 54 tests passed; all 243 Python files and both packaged guides
match reviewed source. See validation.json in the same artifact folder and STATUS. Older validation is retained as historical.
Linux migration/cleanup remain 100%; Windows/macOS remain deferred, with no new
milestone. The old dist/linux M5 bundle is not republished as part of this source change.

The owner's workflow file was read only. Ana's corrected standalone DUET contains
OMNI-RES 2 / 200 repetitions and 4 / 100, with a complete 17.798849159944304% result
(displayed 17.8%). No
organization has been added. Next owner step: restart, reopen the workflow project,
verify Save starts disabled, edit one field, Save, and verify it disables again. Then
resume independent assessment entry and the previously requested Reset/trash/saved-data
chooser testing before organization setup. Their confusing wording was observed but
is not repaired in this bounded Save change.
