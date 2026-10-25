> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in the owner decision record
> and [current database inventory](database_tables.md). Removed APIs are not supported.

# Job Management measurement controls and Approve — F67

The original `JobWindow.createRiskMeasurementTable` supplies the layout:
LiFFT/DUET/ST rows, three columns, bold centered headers, 35-pixel row height,
first-column content sizing and two stretched numeric columns. The extracted
`JobRiskTable` keeps those rules and the original table/header stylesheet. It
uses the existing characterized model probability functions and palettes.
English and Spanish headers/error messages use the shared desktop catalog.

Loading a profile displays its saved probability without recalculating it. A
user damage edit calculates the probability once; a signal blocker prevents the
programmatic result/color updates from calling back into the edit handler. One
form-edit notification is emitted. New/draft damage fields are editable; approved/
retired fields stay selectable but read-only. Fully blank rows are omitted.

## Intentional differences

The original damage handler returned early on invalid text, leaving its previous
probability visible. The new table clears that obsolete result and applies the
original neutral color. Negative/nonfinite/nonnumeric evidence cannot be saved.
Zero damage retains the original edit-time 0.0/white treatment; loading saved zero
retains the original model palette treatment. These are UI display policies, not
new scientific claims about zero exposure.

Unchanged and edited saved rows retain their original unit labels and notes;
new rows use the explicitly supplied project unit system. The original payload
relabeled every row using the parent's current system. This component does not
silently convert or relabel stored evidence. Damage-to-probability evaluation
requires neither moment conversion nor a TST force direction, so this does not
resolve or bypass the outstanding task-calculation scientific review gates.

## Approve behavior

The original Approve button saves draft form controls and approves within one
transaction, without saving job-name/description controls. Optional edited
profile evidence now passes through the existing workspace/repository approval
operation and commits with approval. Validation/storage failure retains the
previous saved draft. This is a direct requirement of the existing control.

## Evidence and limits

574 tests pass (8 new cases), including real Qt signals/flags/form values and
SQLite failure/retry during approval. An initially mistyped LiFFT probability
expectation was checked against the original Python 3.10 environment: damage 1
produces 84.9 percent at the original one-decimal display rounding.

Native XCB captures under the approved new Qt baseline compare the original
AST-extracted table-construction method with the new component in the original
stylesheet. Numeric contents and colors are supplied identically for a layout
comparison; this capture is not an independent scientific-color test. Inspected:
populated, selected, locked, invalid, empty and Spanish at 520x220. No clipped
headers/cells were observed. This is component visual acceptance only: the full
Job Management window and adjacent panels still require integration/inspection.
There are no VTK regions, expandable nodes or icons in this original table.
See `reference/f67-capture.py.txt` and `f67_validation.json`.

The component is not yet exposed in the desktop launch harness. Next work is
the original Job Management window's evidence controls, selection/navigation,
and connecting the migrated table, saves, profile actions and workplace editor.
Search/deletion and final localization also remain part of that full workflow.
No schema, dependency or scientific formula change was made.
