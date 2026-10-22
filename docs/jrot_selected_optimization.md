> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in [the owner decision record](job_management_simplification_decisions.md)
> and [current database inventory](database_tables.md). Removed APIs are not supported.

# Selected-tool JROT workflow — F125, 2026-10-09

F126 adds original comparisons and HiGHS integration; see
[jrot_comparison.md](jrot_comparison.md). Pending-action statements below describe F125.

The existing original-layout RotationDialog now accepts an injected
RotationOptimizer and connects Optimize Tool, the right-hand result table and
Use as Current. CBC handles the selected LiFFT/DUET/ST problem through the F120
adapter. Multi-tool optimization/comparison and the main JROT action are still
pending. No dependency, reference-code or operational-project change occurred.

## Source mapping and retained behavior

Reviewed reference src/rotation_layout.py: onOptimizeClicked (2101),
handleOptimizationError (2239), handleOptimizationResult (2244),
displayOptimizedTable (2285), clearOptimizedTable (2380),
transferOptimizedToCurrent (2394), cancelOptimization (3316),
OptimizationWorker (3351) and Overlay (3397). Line numbers describe the frozen
working reference, not this package. The source controls are reused through the
F124 form, rather than reconstructed from screenshots.

The original worker/time-block result headers, 50px result rows, 70px worker
column, 100px block columns, 700px column budget, one-decimal percentages and
averages, damage colors and integer mean RGB are retained. Narrow tables retain
the source horizontal scrollbar. Actual English result/transfer rectangles,
row heights, column widths and cell text match source-generated controls at
1480x740 and 1720x1000. Spanish labels follow the established localized form.
Result cells are read-only: allowing arbitrary edits to an optimizer result
would invalidate its constraints. Exact identities live in UserRole; transfer
never parses displayed/localized text. Recorded unit strings are retained and
not converted by the optimizer or transfer. Missing unit captions follow the
existing manual-grid Metric display fallback; stored evidence is not modified.

Use as Current replaces current assignments, keeps the right-hand preview and
updates the existing row calculations/recommendations. It never saves. Explicit
Save persists the frozen worker/assignment/profile/placement links with
SINGLE_TOOL provenance only after transfer. Saving a preview alone leaves the
current scheme's provenance unchanged. Manual edits clear preview/applied
provenance; changing the displayed tool clears the mismatched preview without
mislabeling an already transferred schedule. New/load/scope reset clears results.
Current column widths remain those of the migrated F123 grid instead of the
source transfer's hardcoded 950px allocation, which could clip recommendations.

## Ownership, boundaries and concrete corrections

application.rotation_preparation freezes only scheduled profiles' required
probabilities into RotationProblem. Zero is valid; missing tool probabilities,
foreign projects/profiles and nonpositive limits are rejected. No UI, storage
read, unit conversion or concrete solver enters the application layer.

RotationSolveController owns one QThread for one immutable problem and injected
optimizer port. The thread reads no widgets/repository, validates the returned
schedule/backend/stage evidence and exposes its result only after completion.
GUI callbacks then render or report failure; neither optimization nor transfer
writes the project. The limit field accepts 1–180 whole minutes; invalid input
produces a localized prompt rather than silently falling back to another limit.
The selected-tool button requires a complete grid with selected-tool evidence.
No speculative project-switch or multi-user mechanism was added.

The source dim overlay, centered animated white heading and original progress
bar style/size are retained. Progress represents elapsed time budget, never
scientific confidence or backend progress. The heading box is wider to fit
localized cancellation text. The overlay uses the dialog's local rectangle and
resizes with it, correcting the source child/global-geometry mismatch. A real
styled Cancel control with the packaged asset makes the source's cancellation
handler accessible (its original control was commented out).

Cancel marks the owned run for discard; it does not forcibly terminate CBC or
release ownership while the solver is running. The bounded solver may continue
until its configured time limit. The overlay remains visible, editing/another
solve is blocked, and the GUI stays responsive. Escape and the window-manager
close action cancel/defer rejection until the finished callback joins final
thread cleanup. Errors unlock the form, retain current edits and report a
localized failure with logged diagnostics. Closing does not save implicitly.

## Validation and remaining work

982 native tests pass, including ten new focused cases (96.71% combined
statement/branch coverage). Ruff/format (466 files), strict mypy (214
source files), architecture and wheel/sdist gates pass. Actual CBC balances a
two-worker/two-target sample from 0%/80% averages to 40% each while retaining
all target occurrences. Controlled workers verify GUI responsiveness, one-run
ownership, Cancel/Escape/window close, invalid backend/error retention and
provenance boundaries. Preparation tests cover exact ownership, zero, missing
measurements and unused pool jobs. Synthetic projects only.

Twenty-two native captures were inspected: two original result comparisons and
20 new EN/ES empty/manual, minimum/enlarged busy/result, cancelling, selected,
transferred and invalid-limit message states. Both panels, adjacent controls,
labels and bottom rail remain visible. There is no VTK/avatar in the original
JROT form. Whole-window pixel identity is not claimed: source comparison stubs
leave unrelated source controls enabled/empty and locale/selection states differ.
Independent extracted-wheel native EN/ES actual CBC preview/transfer/Save/reopen
passes with exact mixed-unit evidence and no project writes before Save. All
500 reference hashes and the approved dependency lock are unchanged. Capture,
wheel and evidence scripts are archived as docs/reference/f125-*.py.txt.

Next: connect HiGHS multi-tool optimization to the original comparison windows,
single-tool comparison and result transfer, then main workspace composition.
Compare/Optimize All Tools and main JROT remain disabled. GLPK is excluded.
Legacy-format compatibility, the copied comprehensive project and final
integrated UI/workflow/platform acceptance remain in the established plan.
Overall completion percentage and finish date remain unvalidated.
