# Reusable LiFFT result presentation — F29, 2026-09-30

`presentation/lifft_results.py` builds immutable per-task output rows and aggregate card data from a complete, current LiFFT evaluation. It is widget-independent and intended for the eventual reference-parity assessment view. No window, layout, button or interaction changed, and this slice does not extend the temporary harness's workflow as the final design.

Rows carry stable task identity, one-decimal moment, four-decimal cumulative damage, reference contribution text and optional color. Format precision matches the original `lifftCalculateResults` label assignments and existing fixtures. The display snapshot records source calculation units; input display preferences do not relabel or convert calculated moments. None row colors explicitly instruct a view to clear styling.

An absent/stale/noncomplete/other-model evaluation produces no display snapshot. Views must clear both task outputs and aggregate cards in that case. Metric source remains unavailable pending its existing scientific review, including a manually constructed complete outcome. The function does not calculate, parse input, normalize units or mutate history.

For otherwise complete LiFFT outcomes, source/task/contribution IDs and ordering must match exactly. Missing/reordered output rows, wrong model types, missing/foreign summaries and unit mismatches raise ValueError before any complete display is returned. This prevents accidental positional mixing or silently truncated zip operations. These structural checks do not independently revalidate scientific formulas or authenticate arbitrarily fabricated result values; callers still use AssessmentEvaluator.

Five new tests cover 1,075 imperial task reference vectors, 29 nonempty imperial summary groups, exact precision/order/colors, immutable snapshots, stale/reloaded/foreign session rejection, undo restoration, review/failure states and malformed result associations. All 293 tests pass; combined coverage is 98.53%, new module 100%. Ruff/format, strict mypy (79 files), architecture and builds pass. Independent package/reference/lock evidence is in `f29_validation.json`.

The owner's clarified final targets are now recorded in `final_targets.md` and AGENTS.md. The comprehensive existing project remains a later integration target, not this component's test fixture. Next component work should continue auditing original assessment-context behavior and building reusable model/presenter contracts using small fixtures, while keeping eventual integrated UI/workflow parity explicit.
