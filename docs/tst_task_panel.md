# Original Shoulder Tool task component — F82

`TstTaskPanel` ports the control construction in reference `main.py:setupTSTTab`.
It is an embeddable component for the original integrated layout; no permanent
standalone application or new launcher is introduced. The main preview ST tab
remains disabled until shared selection/lifecycle/status/avatar routing is connected.

The eight columns retain reference minima (55,190,95,58,80,145,115,85), stretch
factors and grid margins. Task-type dropdowns retain their 220px maximum width,
reference English/Spanish labels and styled popup. Sticky headers follow actual
first-row control widths, including deferred layout after rebuild/translation;
empty grids use the hidden header row. The reference hides inline totals but
retains two 30px rows; the migrated component preserves that spacing. Original
processed button icons, palette, tooltips, Reset cap and 40px bottom controls are
used. Delete and task-data selection stay disabled until real operations exist.

## Input ownership, history and units

The view owns pending text. `TstPresenter` owns a typed display context and existing
application services, not widgets, SQL or file handles. `ReplaceTstInputs` parses
all rows before a single reversible source change, retaining order, task identities
and source units. Invalid text leaves every editor and source unchanged. Missing
fields remain None. Finite signed input can be stored for correction, but application
validation prevents its scientific evaluation. Reset clears numeric fields and
selects Handling Loads as one undo step. Save/reopen preserves these source values.

Arm/force display projects from original cm/N or inches/lbf. Changed values convert
back using the reviewed compatibility factors, while unchanged projections retain
exact original source values. Display-unit switching does not mutate history.
Decimal separator is explicit, independent of language. Translation changes captions
and task labels without emitting edits or replacing pending text.

## Scientific boundary and direction identities

The original UI labels downward/horizontal while its calculation swaps their indices.
That unresolved discrepancy remains documented in F21. The new-format source already
stores explicit model identities, so this component's combo item data is the matching
`TstDirection` value, not a numeric UI index. The old compatibility selector adapter
is not used, and this is not a resolution of legacy imports or scientific behavior.
No legacy directions are inferred or silently converted in this slice.

Calculate commits valid text, invokes the existing application evaluator and reports
its structured issue through the injected callback. Otherwise valid ST remains
REVIEW_REQUIRED (`review.tst_direction`, plus `review.tst_metric_moment` for metric
source). Incomplete/invalid source is INVALID_INPUT first. No ST task result, summary,
color or probability is exposed, and the view never invokes the isolated calculator
to bypass review. Existing characterized formula fixtures remain unchanged.
A future scientific decision must explicitly address labels/index mapping and metric
moment conversion before final calculation parity can be claimed.

## Verification and next slice

Five native tests cover atomic edit/Undo/Redo/Save/reopen, rejected text/Reset/missing
values, units/language/comma input, review/context/identity checks, and original
column geometry/rebuild/resize/empty states. The read-only AST visual harness renders
actual original control methods without importing the legacy application or opening
operational projects. Original/new body and Calculate rectangles match at 980×650.
Expanded selection, populated, empty, invalid, review-gated, Spanish, metric and
1500×850 enlarged states were inspected in `artifacts/tst-task-panel/`.

Full gates: 657 native tests, 96.79% combined coverage, strict mypy over 137 source
files, architecture, lint/format and both builds. The independently extracted wheel
passes ST editing/review, Save/reopen, Reset/Undo, unit projection and enlarged headers.
All 500 reference hashes and approved lock are unchanged (`f82_validation.json`).

Next connect ST into the main application with worker/assignment/tool selection,
Save/Discard/Cancel, shared status/cards and native shoulder camera. Scientific
review gates, scientific-result acceptance, original-project import and final
copied-project/platform parity remain separate outstanding work.
