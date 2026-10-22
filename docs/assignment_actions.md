# Worker assignment actions and requested design clarification

## Approved changes

Menu icons use exactly 25 logical pixels. Only QMenu receives that metric; normal
Qt display scaling applies and toolbar/button metrics do not change.

Worker Management's Job assignments table now has two processed-icon actions per row:
Change assignment opens the existing explicit job/workplace/shift picker; Remove
assignment asks confirmation and ends that active assignment. Both commit immediately,
like Add assignment, while leaving unsaved worker details intact. Pending dropdown
classifications must be saved before Change/Remove so a table rebuild cannot discard
them. Cancelling either modal leaves the catalog unchanged. Actions are localized and
have tooltips/accessibility names. Existing same-workplace dropdown classification and
Save changes behavior remain.

The row dropdown intentionally offers only active jobs placed at that row's exact
station and shift. Change can select another active placement, including another
workplace; it rejects a workplace/shift already occupied by another active assignment
for the selected worker rather than overwriting it. Add still lists only active jobs
with active station/shift placements. Neither action invents a placement for a job.

Application job_assignment.change_worker_assignment produces an immutable catalog;
ProjectWorkspace.replace_jobs commits it through the existing expected-value adapter.
Removal closes the row rather than physically deleting referenced history. Change
closes the source and creates a successor. Existing assessment sources/results remain
attached to their original assignment and remain readable. No global management Undo
is introduced; confirmed Remove is not an assessment-edit history operation.

## Why Workplaces (2) appears

The count is the selected Job's total active placements, each a specific station and
shift. It is not a count of Plants or Sections. The tree groups those leaf stations
under their Plant/Section/Line. A partially checked parent means some of its descendant
stations are selected for the current shift. Therefore two placements can be displayed
under two of three Sections, with the third Section unselected. Selecting a parent
applies to its descendant stations, not a new section-level assignment. The count
spans all shifts; the picker footer separately reports the current shift count.

## JROT constraints audit — no model change authorized or implemented

The portable immutable RotationProblem and RotationOptimizer port separate domain
rules from the PuLP adapter and Qt orchestration. The adapter's _base_model currently
builds three fixed constraints: exactly one target per worker per time block, at most
one worker per target per block, and preservation of the original total uses of each
target across the whole scheme. RotationProblem.validate_schedule independently checks
worker identities, block counts, target totals and per-block uniqueness. Solver output
cannot bypass those checks merely by reporting feasibility.

CBC single-tool minimizes the maximum worker average risk. HiGHS multi-tool runs its
existing two-stage ceiling/spread objectives, including retained first-stage ceilings.
There is no GLPK and no settings-driven optional-rule registry today. Separation makes
extension contained, but does not mean the requested future constraints already exist.

For later approved work, add typed optional rule/settings values to the portable
problem contract, translate enabled rules into solver constraints in the adapter,
and mirror their checks in domain schedule validation. Settings/UI/store should feed
those values rather than contain solver expressions. Preserve an unchanged default
problem and add focused enabled/disabled/infeasible cases. Freeze-worker rules must
specify whether they fix the whole current row or specific blocks. Consecutive-risk
rules must define the threshold and which tool(s) classify high risk. These are future
feature decisions, not blockers for this correction or permission to expand scope.

## Save As versus Backup — current actual behavior

Start in study.ergprj. Change task 1 without pressing Save. Save As study_variant.ergprj
creates and opens a new working project including the current accepted assessment
edits; study.ergprj keeps its last saved values. Continue working in study_variant.

Instead, Backup saved project study_backup.ergprj copies the already saved project
and keeps study.ergprj active. The unsaved task edit remains in the editor and is not
in that backup. Save first if the backup should contain it. Both outputs are complete
native projects including embedded plant images. They serve different purposes:
Save As starts a new working copy; Backup takes a saved-state safety copy without
switching the working file. Both are useful, though a user who always saves then uses
Save As and reopens the original can achieve a similar result with additional steps.


## Acceptance and evidence

Both requested implementation areas are **2/2 complete (100%)**. The requested
Workplaces, JROT architecture and Save As/Backup explanations are documented above.
No new milestone, dependency or JROT feature was added; fixed Linux/cleanup ledgers
remain 12/12 and 6/6. The reference application remains untouched.

Final required gate: **1,337 tests passed, zero failures/skips; 95.74% combined
statement/branch coverage**. Coverage is an execution measure, not a test pass rate.
Ruff, formatting, strict mypy (258 sources/tools), architecture/naming, complete
structural documentation, independent source review inventory (415 maintained files)
and wheel/source builds passed. Six changed/new maintained Python files have renewed
semantic documentation reviews. See artifacts/assignment_actions_final_check.log and
artifacts/assignment_actions_reviewed_files.json.

Eight added focused cases verify immutable assignment closure/succession, ownership,
invalid destinations/types, occupied destinations, no-op, actual bilingual row buttons,
modal cancellation, pending classification protection, unsaved detail retention and
native database reopen with unchanged assessment ownership/source. Existing task-scroll
and worker/classification regressions continue to pass.

Twenty-eight native English/Spanish captures were inspected: populated, enlarged,
empty and expanded dropdown worker forms; Change picker unselected/selected; Remove
confirmation/cancellation and successful Change/Remove; Project/Workplace/Edit and
PLOT/JROT menus. All 194 comprehensive saved sources/results and permanent fixture
bytes were unchanged; mutations ran only on disposable copies. Native evidence is
artifacts/assignment_actions_review/validation.json and its PNGs.

Visual inspection caught Qt5 stylesheet menu painting requesting the small-icon metric
without a widget; the proxy now supplies 25 for that unbound query too. Explicit button
metrics remain delegated and toolbar/button icon sizes remain unchanged. Source comments
and a regression cover this actual Qt painting path, rather than just its menu layout
metric. The owner-workspace Undo/Redo PNGs differed from their older manifest hashes;
the bytes were preserved, their exact static mirror verified and manifest hashes/local
revision provenance updated while retaining previous hashes/origin. The first gate's
two asset-integrity subtest failures are retained in artifacts/assignment_actions_check.log;
the final gate passes with the registered existing artwork.

Restart the application for these changes. Change/Remove are explicit immediate
management commits and do not enter assessment Undo/Redo. Windows/macOS native checks
remain deferred as agreed. No calculation or optimizer constraint changed.
