# M01 — assessment acceptance complete

Only M01 was worked and is now complete. All three acceptance items are verified.
The fixed twelve milestones and 26 remaining baseline points are unchanged.
M01 earns five points: **79/100; 1/12 milestones complete, 5/26 earned, 21 remaining**.
M02 Worker Management is next, not started in this batch.

## Evidence and bounded corrections

Original AST constructors plus the original live sticky-header, summary alignment
and styling paths run read-only under the approved project Qt baseline, with equal
parent/font/size. Six tools/units cases at two sizes match task column rectangles,
header strings, summary rectangles and button rectangles. The initial constructor
harness missed the original live button repolish; including that actual path
removed an apparent six-pixel difference without changing application layout.
This is a source-layout comparison, not proof of every native platform's rendering.
Numeric outputs/row styles/directions reuse F154/F155's isolated original full-app
oracle; do not repeat formula characterization. Fresh row color was not populated
in the AST geometry oracle; row color evidence comes from F154/F155.

The known R010 corrections are presentation-only. LiFFT/ST imperial arm labels
now use original active `in`, with `cm` preserved. Fresh saved summaries retain
original four-place text rounding but derive their palette shade from the already
saved row damages, added in original row order. No source formula recalculation,
archive replacement, schema change or data rounding change occurs. Archives use
their recorded summary; absent row evidence falls back to it. Zero fresh damage
retains the fresh clear background. Original ST direction mapping and moment-unit
provenance remain unchanged. Saved probability text follows existing original Save
precision/boundary handling; this work does not change it.

Required gate: 1,152 tests, 96.48% combined coverage, Ruff, format, strict types,
architecture and Hatchling packaging passed. Focused display regressions: 18 passed.
The independent wheel ran six tool/unit Save/reopen cases and 18 fresh/saved/pending
integrated captures with live VTK, EN/ES and minimum/enlarged sizes. All individual
images were visually inspected: assessment headers, columns, totals, buttons and
adjacent VTK/cards/footer remain readable and contained. Known shared UI concerns
remain in M09, including R011; no full localization/whole-window acceptance claimed.
The wheel runner's final caption retains historical F155 wording; its actual script,
case report and artifact directory are M01, not another F checkpoint.

Reuse F152 for expanded EN/ES assessment selection, exact identity and modal Cancel;
F155 for task count 1–100/default 10, versions, Reset/Undo, selected closed-assignment
data, default-No/Yes deletion and independent reopen protecting other records.
Existing context, task-count, deletion and saved-data regressions passed in the full
gate. Do not manually repeat these accepted cases without a concrete failure.

## CR002 — newly discovered ST keyboard difference

Original setup creates every direction combo before numeric editors, so Tab visits
all direction selectors first, then numeric fields. Migration constructs each row
in order, so Tab visits direction, arm, load, repetitions, then the next row.
LiFFT/DUET sampled forward order matches. The user was asked whether to restore
original ST order with one local setTabOrder change and focused forward/backward
regression, or approve the current row order as an intentional improvement.
No answer has been received and no ST focus repair has been made. This is the only
remaining M01 disposition; do not extend validation or start M02 while it is pending.
Approval is required by the owner's scope-control instruction in AGENTS.md, not a
hypothetical safety concern. No milestone or points are proposed to be added.

Reference hashes: all 500 unchanged. uv.lock unchanged. No environment/dependency,
reference tree, scientific model, signal-refresh or threading change.

Artifacts: `artifacts/m01-comparison/`, `artifacts/m01-main-window/`,
`artifacts/m01-focused.log`, `artifacts/m01-check.log`, `artifacts/m01-wheel.log`.
Reproducible execution scripts are retained in `docs/reference/m01-*.py.txt`.


## CR002 resolution — original behavior restored

The owner explicitly directed preserving the original Tab order and recording any
alternative for later review. QWidget.setTabOrder now chains all ST direction
selectors before the numeric editors, matching original setupTSTTab construction.
This local presentation change does not touch input values, signals or calculator
logic. Regression tests verify exact control identity for Tab/Backtab, initial load
and rebuild, with no pending edit or source mutation. The reference-constructor
comparison samples all 20 direction selectors followed by numeric editors, in both
units at both sizes, with zero remaining comparison differences. Four selected
panel images and three integrated final-wheel images were individually inspected.

Final gate after the keyboard change: **1,154 tests**, required lint/format/types/
architecture/coverage/build passed. See m01_validation.json for exact coverage.
The packaged ST application also passes forward/backward keyboard navigation and
fresh/Save-reopen/pending display with live VTK. Earlier M01 evidence is reused
for unchanged tools and workflows. The earlier pending-decision text above is
historical and is superseded by this resolution; no answer or blocker remains.
No M02 work performed. No new milestone, formula or dependency changes.
