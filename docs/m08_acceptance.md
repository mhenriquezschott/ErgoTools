# M08 accepted — JROT optimization and Apply

M08 earns its fixed **2.25 points**: **92.75/100**, 8/12 complete, **18.75/26**
remaining-baseline points earned and **7.25 overall points left**. M09 next.

M08.1 closes actual **CBC single-tool** and **HiGHS two-stage all-tool** flows.
The original read-only optimizer receives the same immutable comprehensive-copy
inputs as the migrated adapter. Its backend factory follows the approved routing;
its objectives and constraints are unchanged. All three single-tool minimax
objectives and the all-tool ceiling/spread objective match. Returned schedules
are independently checked for worker/block coverage, target totals and per-block
uniqueness; equivalent alternative assignments need not be byte-identical.
Existing exhaustive tiny-fixture oracles provide a separate numerical check.

CBC preview/other-tool comparison and HiGHS three-tab comparison perform no writes.
Use as Current/Apply creates one source edit; Undo/Redo restores both the exact
schedule and SINGLE_TOOL/ALL_TOOLS provenance. Explicit Save and independent
reopen retain original IDs and frozen profile IDs **12, 5, 19** in the comprehensive
copy; synthetic regressions retain newer profiles **3, 4** and mixed recorded units.
Manual editing clears optimization provenance; Undo after Save can restore it,
even with no injected optimizer. Source history intentionally clears transient
preview/comparison windows. The archive, assessments and job catalog remain equal.

M08.2 closes the existing bounded timeout/incumbent, no-incumbent, infeasible,
backend-error and cancel/close paths through focused regression checks. Deterministic
termination evidence checks feasible stopped runs and rejection without a usable
incumbent. Cancel suppresses publication and retains the owned worker until the
bounded backend exits; source replay/actions are disabled during that ownership.
No forced termination, fallback backend, GLPK or new optimizer feature was added.
The original 1% relative gap and per-stage budget remain unchanged.

Final batch gate: **1,178 passing tests, 96.40% coverage**, all required
standards and both builds pass. Independent wheel JROT tests and EN/ES native
comprehensive-copy solver/Apply/Undo/Save/reopen acceptance pass. All 22 batch
captures are inspected; F125/F126 geometry, busy/cancelling and wide-scroll evidence
remain valid for unchanged controls. No dependency or reference modification.

See [validation and objective values](m08_validation.json),
[bounded review](m07_m08_review.md), [history contracts](jrot_history.md), and R012.
Shared UI/units/avatar closure, final cross-feature validation and delivery remain
M09–M12; they are not claimed complete by this JROT acceptance.
