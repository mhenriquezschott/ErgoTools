> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in [the owner decision record](job_management_simplification_decisions.md)
> and [current database inventory](database_tables.md). Removed APIs are not supported.

# JROT source characterization — F119, 2026-10-08

This is a source review and concrete dependency proposal, not a completed JROT
implementation. Main navigation remains disabled for JROT. F118 PLOT integration
is unchanged. No production code, interface, database or environment was changed.

## Active source and layout

`rotation_layout.py` constructs `RotationLayoutWindow.initResponsiveUI`, not the
older fixed-geometry `initUI`. Retain its 1480×900 default, 1480×740 minimum,
10-pixel root margins, 8-pixel spacing, title/subtitle, rotation setup groups,
segmented risk basis, workplace breadcrumbs/scope selector, editable scheme ID,
worker count 1–10, time blocks 2–10 (default 4), minute limit 1–180 (default 1),
record navigation/actions, current/optimized horizontal splitter (6:5), bottom
Compare/Optimize Tool/Optimize All Tools/Close rail and disclaimer. Preserve
processed icons and source stylesheet. Native size/localization checks are still
required when the migrated form exists.

`rotation_scope_dialog.py` supplies the one-shift, multiple-station tree selector
(minimum 680×560). `comparerotation_window.py` compares the single-tool optimized
schedule under the other tools; `compareopallrotation_window.py` shows per-tool
current/optimized tabs and applies a selected tool back to the main JROT form.
The active single-tool result handler updates the embedded optimized table.
The standalone `optimizedrotation_window.py` and old optimizer methods must not
be adopted merely because they exist; migrate the active call path.

## Rotation data and scoring

The reference repository retains scheme scope, worker assignment identity,
job/placement identity and the exact profile ID/version/source. New schemes use
eligible workers and active jobs with current approved profiles. Loading saved
schemes retrieves their stored target profiles and historical worker assignments.
Risk data comes from job profiles, not worker assessments. Missing probability
is unavailable; numeric zero remains valid. Probabilities are percentage values;
there is no unit conversion of these dimensionless optimization coefficients.
Retain each measurement's unit evidence and existing metric/imperial rendering.

The current table displays worker, one target per block, average and recommendation;
averages use original row-order arithmetic and one-decimal display. Labels are
presentation values: immutable target identity must carry job/placement/profile
keys instead of parsing multiline cell text in the migrated application. UI
translations must not change tool IDs, risk values or persisted identities.
Explicit scheme Save persists current assignments; optimizing/comparing does not
implicitly save. Use as Current transfers the result before an explicit Save.
New/search/navigation/cancel/delete and saved provenance need focused persistence
and real-control tests, not just solver tests.

## Active model and behavior to retain

Both active QThread workers call `rotation_optimizer.py`; duplicate embedded
`build_optimization_model`, old no-thread handlers and `optimise_multi_tool*`
implementations are not the source of the current optimization results.

Shared constraints: exactly one target per worker per time block; preserve each
target's total occurrence count over the whole input schedule; at most one worker
at a target in any given block. Input must contain unique workers, complete
blocks, supported targets and all requested profile probabilities. Preserve
scoped placement identity when defining a target.

Single-tool: minimize the maximum worker average probability. Multi-tool: first
minimize the sum of per-tool maximum worker averages, then minimize the sum of
per-tool maximum-minus-minimum averages while bounding each first-stage ceiling
by its attained value plus 0.0001. Source solver parameters are relative gap 0.01
and the chosen limit in seconds, per stage; the two-stage overlay uses twice that
limit. Preserve objectives/tolerances; they are not approval to alter science.

The reference backend helper prefers HiGHS for both paths if available. Owner
routing supersedes that helper: explicitly select CBC for single-tool and HiGHS
for multi-tool, with an actionable failure if the required solver is unavailable;
no silent backend substitution and no GLPK.

Concrete robustness work: validate extracted solver schedules against every
constraint, not just one selected target per cell; distinguish a feasible
incumbent from proven optimal status; validate finite/missing risks before solve.
Reference cancellation requests suppression of a result, without force-killing
the solver. Retain safe cancellation and own the worker lifetime through actual
finish; prevent a second run or window destruction while a solve still owns its
resources. Do not add multi-user or speculative project-switch infrastructure.
Reference form has no explicit closeEvent/reject worker-lifetime protection.
This is an actual background-solve lifecycle issue to address during integration.

## Next executable slices

1. Approve/install the exact [solver proposal](jrot_dependency_proposal.md), then
   migrate the active optimization adapter and immutable input/result values.
   Verify routing and constraints against small known-answer fixtures, feasible
   timeout/no-incumbent behavior and the two-stage objective.
2. Migrate scoped scheme persistence with frozen profile/assignment links, then
   compose the source layout into a usable edit/save/load/delete workflow.
3. Connect optimization, comparison/transfer and safe cancel/close ownership;
   inspect EN/ES, metric/imperial, empty/populated/selected/error, minimum/enlarged
   states, and enable the actual main action after usable workflow validation.
4. Continue the existing plan: original-format compatibility, the comprehensive
   project on a copy, and final integrated UI/workflow/platform acceptance.

No whole-application completion percentage or finish date is validated. The last
code gate remains F118: 898 passing tests and 96.88% coverage. No duplicate full
suite or visual capture was run for this documentation-only checkpoint.
