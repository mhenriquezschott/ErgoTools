> Current owner-approved task-capacity and unused-row policy (2026-10-18)
> supersedes historical clear-on-count-change and unused-slot partial-status wording
> below. See [current behavior](task_grid_resize_acceptance.md).

# Original task-count and incomplete-row workflow — F76

Launch with `.venv/bin/python -m ergotools.bootstrap --integrated-preview`.
This checkpoint completes two reference interactions within the incremental main
preview. It does not complete the model/result panels or the final Settings window.

## Reviewed reference behavior

`openNumTasksDialog` creates a bold count label, spinbox range 1-100 starting at 10,
and Set Tasks/Cancel row. `numTasksSetButtonClicked` clears and rebuilds the active
tool tab at that count, then shows confirmation. The new owned `TaskCountDialog`
ports these controls and labels directly, adding Spanish captions. Its presenter
issues one `SetLifftTaskCount` command: old source is retained in history for Undo,
while new blank slots have distinct stable IDs. Source units do not change.
No database access or global window lookup belongs in the form.

Settings currently exposes this reference task-count operation only. Without an
active LiFFT source it is disabled. Cancel preserves the current grid and pending
text. Set Tasks may clear invalid pending text, like Reset; Undo restores the last
committed source, not invalid text that was never part of the document. Source
changes occur only after modal acceptance. The existing source-bound evaluator
clears when task slots reset. Configuration of language/units through final
Settings, menu integration, and task counts for DUET/ST views remain upcoming.

`lifftCalculateResults` warns on missing fields but proceeds through rows. Complete
rows calculate normally. Arm/load without repetitions call the model with rep=0
for moment-only output. Missing arm/load leave zero row outputs. Complete-row
rounded damage contributes to the total in reference row order.

## Explicit grid preview boundary

`AssessmentEvaluator.evaluate_lifft_grid` implements that reviewed workflow using
the existing strict calculator and aggregator. Temporary numeric inputs exist only
for deriving outputs; original missing values stay None and are persisted unchanged.
Every source slot has a result at the same position/ID, so later populated rows
never move into earlier unused rows. Missing fields produce PARTIAL status and
ordered required-field issues. The window displays a translated warning identifying
that totals include complete rows only. An all-blank grid has zero damage, no
modeled probability, and PARTIAL status; it makes no zero-injury-risk claim.

Bad numeric inputs still invalidate the whole calculation, unlike the reference's
silent conversion of invalid strings to missing values. That established correction
remains intentional. Metric scientific-review failures still suppress results.
There is no gate bypass. Strict `evaluate`, `prepare_assessment`, `prepare_lifft`,
and complete-result display contracts remain strict for other callers; partial
previews must not be consumed as complete saved/job risk results. This explicit
UI-only policy supersedes F74/F75's pending incomplete-row migration, while the
original strict F13 preparation contract remains available unchanged.

## Evidence and limitations

Six focused regressions cover complete/blank/moment-only/missing-arm/load rows,
strict versus grid evaluation and unchanged source, all-blank and invalid cases,
metric review preservation, grid Calculate/Save/reopen with real None values,
English/Spanish warning and its removal after completing all rows, actual owned
modal Cancel/Set/Undo including invalid pending text, and reset preconditions.
All 627 tests pass with 96.79% coverage and all required quality gates.

Native task-count controls match the extracted original at 183×112. Spanish labels
fit at 249×112. Main preview states are inspected at 1550×1015, including mixed
rows, Spanish results, reset-five state, maximum count and confirmation. The
confirmation and original dialog were characterized without importing the original
application or touching its databases. Characterization script and wheel workflow
are archived under `docs/reference/`; captures are under
`artifacts/lifft-grid-workflow/`; hashes/results are in `f76_validation.json`.

The left VTK avatar and right results sidebar remain planned, not removed. Until
integrated, the task component uses central width and there is no full main-window
visual-parity claim. VTK dependency/version approval precedes adapter installation.
No reference file, dependency lock, schema or file format changed in F76.


## F77 subsequent integration

The original result sidebar and body-panel layout are now integrated. Earlier
statements about missing side-panel structure are historical. The VTK avatar and
its view interactions remain pending. See [current panel limits](main_panels.md).
