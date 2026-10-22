# LiFFT assessment aggregation — F12

## Scope and contracts

`domain.assessments.lifft_summary.summarize_lifft_tasks` consumes calculated LifftTaskResult snapshots from one explicit measurement system. It returns immutable LifftSummary/LifftContribution values with stable ordered task identities, cumulative damage, contribution percentages and optional probability on the 0-1 scale. It does not calculate inputs, persist results, coordinate a session or integrate a GUI. The metric display review gate remains unchanged.

The total uses explicit row-order `+=` on already-rounded task damage. Python 3.13 changed built-in sum behavior relative to the reference runtime, so substituting sum/fsum would alter some results. The total is not rounded before evaluating probability or dividing contributions. Shares use round(damage / total * 100, 1); three equal tasks produce 33.3 each, with no artificial residual redistribution. Empty and zero-damage summaries have zero contributions and probability None: the positive-damage model has not been evaluated, and zero injury probability is not asserted.

The API rejects blank/duplicate task identities, mixed/invalid measurement systems, boolean/negative/nonfinite damage and total overflow with existing structured/localizable issue keys. It consumes results from the task-calculation boundary; it does not certify manually constructed result moments or invent upper physical limits.

`presentation.desktop.theme.lifft_summary` produces a complete immutable display snapshot. Probability is rounded on the 0-100 scale before strict limits: values below 5 display `< 5`; values above 90 display `> 90`; exact boundaries retain one decimal. Zero total displays the reference `0.0` placeholder. Positive total damage displays four decimals. Task colors are suppressed if the rounded contribution is zero, even if task damage is positive. None is the explicit clear-color instruction, rather than the legacy string `none`. Decimal-point formatting preserves current behavior; locale-aware number formatting remains pending.

## Reference findings and deliberate differences

The actual `src/main.py:lifftCalculateResults` method adds rounded task results in order and updates contribution labels, colors and summary probability. It warns on incomplete inputs but continues with partial/zero row values, including a zero-repetitions preview. That incomplete-input policy is not adopted here: this API accepts calculated results only. The later application assessment coordinator must distinguish an incomplete draft from a complete zero-damage result and explicitly decide preview behavior.

On zero recalculation the original method resets numerical arrays and summary labels but does not reset all row labels, background styles or VTK actor state. A formerly populated view can therefore retain stale values/colors. The new stateless display snapshot explicitly clears colors and supplies zero shares. This is a documented intended correction for a future view; no existing widget or renderer has been changed or visually accepted.

Job-window probability/color handling differs from the assessment view (including zero handling and no 5/90 display bounds). This assessment-specific display policy must not be silently reused for job/PLOT summaries. Scientific correctness and metric moment conversion remain separate unresolved review topics.

## Evidence and reproduction

The fixture `tests/fixtures/lifft_summary_reference.json` records 60 cases using the original interpreter, `3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]`. Reference main.py SHA-256: `6e8a65a2ba7370b1dbda199110e3cfbe0b9f62d91ed9677ceea9f8483b3e2fc5`. Method AST SHA-256: `0fdbf022e6d78bed7c5e4ec5f4bb0bfacb023f56de8e6aec497d310c82a4ef9f`.

The capture extracted the actual method AST, compiled it unchanged, and bound the original LiFFT class. Minimal inert label/status/actor/render stand-ins supplied only the methods used by the source. It did not import or launch Qt, access application databases, or write reference bytecode. Numerical arrays, label text and color state were captured after execution. This is method-level characterization, not GUI testing. The capture harness is archived as `reference/f12-capture.py.txt`; it is audit material, not production tooling and must be reviewed before any deliberate fixture regeneration.

Thirty task groups were crossed with imperial and metric units. Cases include empty/zero inputs, damage rounding to zero, ordinary/high totals, equal thirds, small relative contributions, large totals, and 21 deterministic multi-task groups. Tests compare exact totals, contribution arrays, probability/damage text and all task/summary colors. Additional tests cover zero-state replacement, row-order floating-point behavior, strict display boundaries, invalid values/identities/units, overflow and immutability.

149 tests pass on approved Python 3.13.14; combined coverage is 99.00%, with both new modules at 100%. Ruff, formatting, strict mypy (36 files), architecture and package builds pass. Independent wheel/reference/lock evidence is in `f12_validation.json`.

## Next work

Define application-level assessment validation/completeness and result freshness across edit/undo/load, including an explicit incomplete-preview policy. Keep the scientific metric review prerequisite visible before complete assessment-workflow/GUI integration. Other assessment tools, legacy migration, Save As policy, visual checks and native packaging remain pending. No dependency or runtime baseline changed.
