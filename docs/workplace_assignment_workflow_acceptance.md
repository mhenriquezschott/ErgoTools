# Workplace-first assignment workflow — 2026-10-19

Owner approved replacing Job-centric worker assignment wording and the flat Job-first
picker with workplace-first selection. The same picker also enables direct standalone
assessment association without a separate Worker Management prerequisite.

## Behavior and ownership

Worker Management now uses **Workplace assignments**, **Assigned workplaces**,
**Assign workplace…**, **Job (optional)** and **No Job**. The status counts workplace
assignments and those with a Job separately; a workplace-only record is valid. The
new `WorkplaceAssignmentDialog` selects a real station through the existing hierarchy,
then a project Shift and an optional active Job placed at that exact workplace/shift.
It receives immutable catalogs and returns identities; it performs no storage writes.
Change preselects the current station/shift/Job and supports a workplace without a Job.
Original assignment rows remain historical owners of their existing assessments.
The retired `WorkerPlacementDialog` was removed, with imports/callers/tests updated;
there is no compatibility alias, duplicate picker or private-owner access.

**Associate assessment** in the main UI uses the same workplace-first selector. It
reuses an existing active same-worker assignment with its Job unchanged and locked.
Otherwise acceptance creates the missing real assignment and binds the selected
standalone assessment in one native transaction, through an application capability
port. Cancellation/invalid membership or a write failure creates no orphan assignment.
One shared Undo action reverses creation and association together; Redo restores them.
Existing removal confirmation and single main Save policy remain in force. Other
tools, exact scientific inputs/results and source identities are unchanged. Existing
destination assessment data cannot be overwritten. Ordinary Select assessment context
remains view navigation and does not move observations or create assignments.

Native format remains **18**. No dependency, formula, database table or fixture
migration. The three current native test projects retain their original bytes.

## Validation

Final native Linux gate: **1,946 passed, zero failures/skips, 94.40% coverage**;
standards/format/types (269), architecture/naming/documentation and wheel/sdist builds
pass. Independent wheel: **213 passed / 78 subtests**; all 247
Python files and both guides equal source; all loaded package modules use the isolated
extraction. Final wheel equals the tested wheel. Twenty-one new focused regressions pass.
Evidence is recorded in
[validation](../artifacts/workplace_assignment_workflow/validation.json). New tests
exercise all three tools, optional Jobs, assignment reuse and Job conflict rejection,
real SQLite failure after assignment insertion, invalid destinations, cancellation,
private editing, main Save/reopen and shared Undo/Redo. Existing assignment transition
reference-oracle checks remain unchanged. Input/result SQL rows remain exact through
association, replay and reopening, including all 12 assessments on a private copy of
the owner's workflow project.

Twenty-eight native XCB captures cover English/Spanish Worker Management empty and
populated assignments, new/Change/association pickers, No Job/Job menus, existing Job
locking, no-organization and parent selections, minimum/enlarged forms, and integrated
main association/Undo with VTK and settled results/bottom controls. Both updated Help
sections were rendered and inspected. The renamed English tab initially clipped;
its shared minimum width was corrected, the redundant Spanish-only width removed,
and final captures regenerated. The interrupted earlier gate is explicitly partial;
only the complete post-correction gate counts as acceptance.

Sixteen maintained source/test files received substantive contract review and renewed
review hashes. All 439 maintained files / 3,095 functions / 416 classes / 323 constants
are reviewed, with zero pending reviews or structural gaps. Current architecture,
API, optional-context, main Save, development and bilingual Help documentation are
updated. Linux migration/cleanup remains 100%; no new milestone. Windows/macOS remain
deferred. Owner interaction acceptance is pending.

## Reference discrepancy

A read-only audit found ten differences against the historical 500-file reference
manifest: two documentation files, src/main.py, three tests and four compiled cache
files. Their recorded modification timestamps are 2026-10-12, preceding this task.
The discrepancy was reported to the owner and is listed with exact historical/current
hashes in [protection evidence](../artifacts/workplace_assignment_workflow/protection_validation.json).
The reference checkout was not written or repaired. The existing manifest was not
rewritten to conceal these differences. All three current fixtures and uv.lock match
the task's protection baseline exactly.

Next: restart ErgoTools, reopen the unchanged workflow project and check the new
assignment/association controls before resuming the agreed four-worker workflow.


## Owner follow-up — table widths

Owner confirmed assignment Undo/Redo in Worker Management, then requested complete
column values/headers and conditional horizontal/vertical scrolling. The bounded
layout correction is recorded in [table acceptance](worker_assignment_table_acceptance.md).
Its validation supersedes this checkpoint's package hashes and gate counts.
