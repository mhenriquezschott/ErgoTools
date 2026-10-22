# Owner clarification — final targets and incremental validation, 2026-09-30

The final target is ONE integrated ErgoTools application containing LiFFT, DUET, Shoulder Tool, PLOT and JROT. Preserve the current application's visual appearance, dimensions/proportions, control placement, dialogs, toolbars, interactions and workflows. Refactor the implementation into the accepted architecture; do not preserve inappropriate coupling simply to retain appearance.

The owner's detailed instructions are archived in `reference/owner-ui-requirements-2026-09-30.txt`. The subsequent clarification authorizes continued incremental work: immediate full UI reproduction and immediate support for the comprehensive project are NOT required. Use small isolated fixtures/temporary projects now, progressively integrated tests later, and final application-level validation once sufficient functionality exists.

F28's standalone LiFFT window is a TEMPORARY DEVELOPMENT HARNESS. Its single-field editor, Apply/Discard arrangement, simplified task table and separate layout do not define the final UX and are not authorization to replace the reference assessment workflows. Existing reusable source, history, parsing, calculation, persistence and presenter contracts should support the eventual reference layout. Review their event policies when connecting original-style controls, rather than imposing the harness's controls on the final application.

The owner identifies `../tests/ErgoTools_ComparativeRiskTest.ergprj` relative to the current codebase as the comprehensive FINAL integration/validation dataset, containing workers, jobs/workstations, assessments, PLOT layout data, JROT rotation schemes and their relationships. Its contents have not been audited in this slice. Locate and verify it when integration reaches that stage; use a copy and never overwrite the original. It is not the required main fixture for early component tests.

Permitted changes include the owner's stated menu/settings enhancements and actual bug, interlock, recursive-event, resize/DPI/platform, responsiveness and error-handling corrections. These are not broad redesign permission. Document proposed visual/workflow improvements separately and obtain approval before implementing them in the final UI. Prior explicit unit-preservation corrections remain recorded; resolve any future conflict with reference behavior explicitly.

Final acceptance must include same-platform, same-size/DPI/theme/font comparisons of original and migrated windows, expanded/selected/empty/populated/error states, identical control placement and workflows, integrated tool navigation and the copied comprehensive project's cross-feature behavior. No current foundation coverage percentage or harness screenshot counts as final UI/workflow parity.

Continue using the independent new-project environment and approved exact dependency baseline. Preserve the working reference and system Python. Do not accelerate into whole-UI copying or redesign; migrate tested components incrementally toward these final targets.

## Owner decision — JROT solver routing, 2026-10-06

Use CBC for single-tool optimization and HiGHS for multi-tool optimization.
Drop GLPK from the migrated solver set. This supersedes historical alternatives
in the proposal; do not change the reference application. Exact solver/library
versions and binaries still require the documented approval before installation.
Implement and verify this routing when the migration reaches JROT, after PLOT.

## Reaffirmed modernization requirements — M06 owner clarification

Original UI/workflow parity does not cancel approved improvements. Undo/redo is
required across the application, including PLOT. The accepted plan explicitly
includes marker move/scale history, application-owned commands, focus-aware Qt
actions and transactional Save/clean-state semantics. M06.1 remains unchanged;
the proposal to remove history because it is absent in legacy PLOT was mistaken
and withdrawn. Initial localization must fully implement English and Spanish,
with architecture that supports additional languages later. See
[accepted history requirements](reference/modernization-plan.md#undoredo-and-save-semantics)
and [bounded M06 correction](m06_review.md).


## Final Linux disposition — 2026-10-11

M01–M12 are accepted for Linux; original UI/workflow and copied comprehensive
dataset evidence is recorded in their acceptance files (especially M10).
The early-stage dataset/harness notes above are historical, not current gaps.
Owner confirms Linux as migration completion target and explicitly defers native
Windows/macOS tests. Confirming expected Linux behavior against the prior codebase
remains the owner's first acceptance priority. Reference/operational files stay
untouched; no automatic replacement or publishing is authorized.
