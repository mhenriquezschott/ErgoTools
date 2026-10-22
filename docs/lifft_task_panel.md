# Original LiFFT task controls — F74

Run from the new project:

```bash
.venv/bin/python -m ergotools.bootstrap --original-lifft-controls
```

This hosts the reviewed original task controls inside the existing temporary
preview. The flag preserves the previous harness for existing tests and does not
create another final application. New/Open, management and assessment-context
controls still use the migrated workspace. Create a project and add tasks through
the harness toolbar, or open a small compatible synthetic project with tasks.
The final row-count/settings workflow and default 15-row initialization belong to
the original main-window/settings migration; this component renders saved tasks.

## Ported code and behavior

The reference sources are `main.py`'s `setupLiFFTTab`, `SyncedHeaderLayout`,
`createStickyHeader`, `bindStickyHeader`, `syncStickyHeaders`, `alignToolSummary`,
`styleAssessmentControls` and `mainWorkspaceStyleSheet`. Widget classes, seven
column positions, scrolling, invisible header width constraints, fonts, original
processed icons, tooltips, result formats and bottom control dimensions are ported
and typed. The reference source tree is not modified or imported at runtime.
The shared main stylesheet is reformatted CSS without changing its rules.

The grid owns pending text; calculations, conversions and persistence stay in the
existing presenter/services. Calculate and Save parse every entered cell before
committing one source/history command. Invalid text cannot partially commit earlier
valid cells. A failed parse leaves entered text available for correction. Exact
unchanged projected values retain canonical precision. Reset clears all task
inputs without deleting saved assessment identities and is undoable as one change.
The harness Remove task action follows the focused grid row and is undoable.

Calculated rows show moment with one decimal, damage with four decimals and the
existing contribution percentage/colors. Editing clears displayed calculated
results. Grid reload hides old widgets immediately before deferred Qt deletion,
preventing previous-project rows/colors from painting after a clear. Headers update
on geometry events, with coalesced updates, rather than the reference main window's
periodic summary refresh. Header scrolling accounts for the vertical scrollbar's
width; input columns and sticky columns continue to align at the scroll limit.

Inputs accept the existing explicit decimal convention. English/Spanish controls
translate separately from stored records. Lever arm/load project into selected
display units; derived moment labels stay in recorded units, since the cached model
result is calculated from the recorded source. Units are not silently relabeled.
Scientific metric review gates remain in force; no formula is corrected here.

## Remaining parity and intentional harness differences

This is the task-control component, not the original integrated main window.
The body model, shared context bars, result sidebar, original menu/settings and
DUET/ST/PLOT/JROT navigation have not been integrated in this checkpoint.

The original saved-assessment Delete button is present but disabled until its
original deletion workflow is migrated. It must not accidentally delete a task.
The original grid button currently opens existing assessment-context selection;
its complete original task-data dialog remains pending. The standalone harness's
single-field editor and duplicate result card are hidden in original-controls mode.
No menu/settings redesign is implemented by this flag.

The existing evaluator requires complete valid task rows. The reference calculates
available rows and some partial moments; its handling of blank/partial rows still
needs an explicit compatibility decision before final assessment parity. The new
grid does not bypass that established evaluator contract. Fractional repetitions
remain supported by the migrated source/model contract rather than adding the
reference editor's integer-only restriction. Record these differences, not a claim
of complete original calculation-interaction parity.

## Evidence

Seven focused tests cover atomic multi-cell calculation and save/reopen, invalid
text and Reset/undo, units/decimal changes and rejected preference transitions,
sticky header scrolling and bottom geometry, invalid/cancelled Close followed by
retry, focused-row removal/undo and immediate cleared-project painting.
All 614 regression tests, baseline standards, typing, architecture and package
builds pass. Extracted-wheel edit/calculate/save/reopen passes independently.

Native comparison uses only extracted reference methods and synthetic temporary
values on the same Qt/host. At 900×480 the original/new summary region is
`(9,349,882,76)` and Reset/Delete/Calculate geometry matches. Empty, populated,
calculated, scrolled and translated states plus both 960×680 preview languages
were inspected. Narrow component captures requested at 620px grew to their Qt
minimum of roughly 758–761px; actual dimensions are recorded in the evidence.
Horizontal scrolling exposes remaining columns there. This is not VTK, Windows/
macOS or complete main-window visual acceptance. Screenshots are validation of
ported code, not the implementation source.

See `f74_validation.json`, `artifacts/lifft-task-panel`, and archived native/package
scripts in `docs/reference`. All 500 reference file hashes and `uv.lock` match
the preceding baseline. No project payload, SQL schema or dependency changed.


## F76 subsequent integration

The original-style grid now supports an explicitly marked incomplete-row preview
and the original task-count dialog. This supersedes earlier pending/full-row-only
statements about grid interaction above. Strict preparation and non-grid evaluation
remain unchanged. See [current workflow and limits](lifft_grid_workflow.md).
