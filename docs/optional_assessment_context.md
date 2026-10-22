# Workplace-first assignment and assessment association — 2026-10-19

Worker Management uses **Workplace assignments**, **Assigned workplaces** and
**Assign workplace…**. Choose a real station through the existing location hierarchy,
then a Shift and an optional compatible Job. **No Job** is a valid assignment;
the summary counts workplaces and Jobs separately, without a completeness warning.
Change uses the same picker, including the option to change to a workplace without
a Job; historical assessment ownership stays attached to its original assignment.

Creating a workplace assignment does not move a standalone assessment. In the main
window, **Associate assessment** selects a workplace/shift and optional Job directly.
An existing active same-worker assignment is reused with its Job shown and locked;
otherwise acceptance creates the missing assignment and binds the selected assessment
in one repository transaction. No separate Worker Management operation is required.
Cancel or failure leaves no new assignment. Existing destination assessment data is
rejected, never overwritten. Inputs, exact results and document identity are unchanged;
other tools are not implicitly associated. One shared Undo step reverses both new
assignment creation and association; Redo restores them together. The main Save
publishes accepted private changes. Replaying a removal uses the existing warning.

Native format remains **18**; no table, dependency, formula or fixture migration.
All three native test projects remain unchanged while this workflow is validated on
private copies. See [current acceptance](workplace_assignment_workflow_acceptance.md).

---

# Organization field cleanup — format 18, 2026-10-19

Native format 18 removes six Station attributes (task_description, equipment_used,
ergonomic_risk_level, performance_metric, power_consumption, materials_used) and
Plant number_of_shifts. Dates are canonical ISO calendar dates; operational_hours
is a daily decimal-hour duration in whole minutes from 0 to 24. The UI derives
Shifts in use from distinct active Job placements or worker workplace assignments
in that Plant. Unused project Shift definitions do not count; no new table is added. External formats 8–17 convert on a private copy. Existing
format-14/15/16/17 source/result payloads remain exact. Current native test projects
were updated in place. See [acceptance](organization_input_cleanup_acceptance.md).

---

# Shift metadata correction — format 17, 2026-10-19

The owner removed `incidents_reported` and `ergonomic_risk_events` from recurring
Shift records. Format 17 retains the same SQL tables and keys; those two attribute
pairs are absent from `work_catalog` JSON and rejected by the domain contract.
Format 16 requires the existing external conversion workflow, which removes exactly
these attributes without recalculating or changing unrelated rows. Original legacy
files remain unchanged; their converter now excludes these fields. Both maintained
native fixtures and the four-worker workflow file were updated at their existing
paths. See [acceptance](shift_metadata_removal_acceptance.md).

---

# Optional assessment organization — native format 16

Owner-approved scope, 2026-10-13. The review scenarios are standalone worker
assessments, PLOT worker analysis with optional Jobs, independent Job-based JROT,
and their integrated use. Existing Default organization names in maintained test
projects are genuine owner-entered data and must remain unchanged.

## Data contract

`assessment_ownership` replaces its prior definition in place:

```sql
CREATE TABLE assessment_ownership (
    document_id TEXT PRIMARY KEY NOT NULL,
    worker_id TEXT NOT NULL,
    assignment_id INTEGER REFERENCES worker_assignments(id)
        DEFERRABLE INITIALLY DEFERRED,
    kind TEXT NOT NULL CHECK(kind IN ('lifft', 'duet', 'tst')),
    position INTEGER NOT NULL UNIQUE,
    UNIQUE(assignment_id, kind)
);
CREATE UNIQUE INDEX standalone_assessment_owner
    ON assessment_ownership(worker_id, kind)
    WHERE assignment_id IS NULL;
```

There is one assessment per worker/tool without context, and one per assignment/tool
with context. Worker identity is required and validated against the typed work_catalog
inside repository transactions. For an assigned assessment its worker must equal the
assignment's worker. Workers currently reside in the validated catalog payload rather
than a separate SQL worker table; no fictitious SQL foreign key is claimed.

Inputs and the sole matching calculation remain in draft_documents and
saved_assessment_results. No second output, assessment version, archive or additional
business table is added. The existing worker_assignments.placement_id is already nullable;
that represents a real workplace/shift with no Job. The uniqueness rule remains one
active assignment per worker at an exact station/shift. A worker may use other stations
in the same shift, and Jobs may have many placements across stations and shifts.

New creates a genuinely empty format-17 project; it creates no default worker, plant,
shift, Job, orphan source or result. Worker ID is the minimum worker identity.

## User workflows and UI

A user selects a worker and tool, enters inputs, calculates and saves. Organization is
optional. Blank previews remain in memory until entered data is explicitly saved.
Worker Management only manages workers and workplace assignments; closing it never
asks to create or switches an assessment. Select assessment context identifies the
worker/tool and exact workplace. Open assessment opens an existing owner, while Create
assessment deliberately creates one blank source for the selected assignment/tool in
private project state. Main Save publishes it. Cancel creates nothing. The existing
same-Job warning still applies when another location already has that worker/tool/Job.

Standalone sources can be browsed, exported and updated normally; absent organization
is shown as absent, never fabricated or interpreted as zero risk.

The Assessment context checkbox is in the existing footer. With no organization the
context frame is hidden and reserves no height. Checking it reveals optional controls.
Opening a project with organization, or adding its first real plant, expands the frame.
Manual collapse is session-local; reopening a populated project expands it again without
storing a redundant project preference. The organization's saved presence drives this.

Worker Management uses the workplace-first picker described above. Jobs remain optional
for worker-based PLOT. Change and Remove preserve historical assessment ownership.

Follow worker / Keep context select views only. The context picker opens saved views
and exposes the explicit Create assessment action for missing assignment/tool data. The explicit
Standalone assessment choice inside Select assessment context returns to a worker/tool with no organizational association.
Associate assessment is available for a saved standalone assessment. Its workplace-first
picker atomically reuses or creates a same-worker assignment and changes only that
tool's ownership link. Source identity, inputs, result bytes and other tools remain
unchanged. Existing destination assessment data causes a conflict, never overwrite.
Integrated navigation retains edits privately; cancellation writes no association.
Association participates in the shared project Undo/Redo history. Its single action
restores standalone ownership and removes a just-created assignment together. A later new standalone
preview receives its own unused identity.

Keep context can select a workplace where a worker has no assignment. That view says
Assignment required and cannot save there; the user can add a real assignment without
a Job, or return to Standalone assessment. No assignment is implicitly manufactured.

PLOT Individual mode reads only associated assessments in its selected real workplace
scope. Missing Job evidence does not block worker results. Job and Comparison modes use
Job evidence only where available; missing values remain unavailable rather than zero.
Unassigned assessments stay accessible in the main application and exports. Empty
stations and workers with no tool data do not produce fabricated result rows.

JROT All Jobs uses worker identities and approved Job profiles without individual
assessments, placements or organization. Workplace Scope additionally uses actual
placements/assignments. CBC single-tool and HiGHS all-tool behavior, frozen profiles,
rotation blocks and saved provenance remain unchanged. Inferred schedule exposure is
not stored as an individual worker assessment.

A linked assessment stays attached to its original assignment after reassignment.
Ordinary context changes never move/copy it. Explicit existing Copy/Move remains scoped
to assigned assessments; standalone data must be associated before workplace transfer.
Multiple assessment occasions/versions are not part of this change.

## Existing files and clean test fixtures

The separately removable converter in tools/project_migration upgrades earlier full
formats 8–16 into format 17. It fills worker_id from the existing exact assignment,
preserving all organization, Jobs, inputs/results, PLOT images/geometry and JROT rows.
Formats 14/15 preserve calculation payloads and unrelated timestamps exactly. The previous
approved older-output recalculation policy and populated-duplicate rejection remain.
Old user projects use the existing guided external upgrade workflow, never runtime legacy
mode. Current normal projects need no converter.

The two maintained test files are updated IN PLACE at test_projects/native. No backup
or parallel current fixture folder is created. Existing originals remain the already
established reference inputs; no new historical copies are retained for this correction.

## Rollback considerations

Repository mutations use transactions; failed first Save or association rolls back source,
result and ownership together as applicable. Failed conversion never publishes a partial
output. The maintained-fixture update validates an in-memory upgraded database before its
single in-place schema transaction and compares every unrelated table afterward.

Returning to format 15 is representable only when EVERY assessment has a real assignment,
its worker matches that assignment, and assignment/tool uniqueness still holds. Then a
reviewed transactional conversion can restore the four prior ownership columns and
metadata 15. Once standalone data exists, a downgrade requires explicit same-worker
assignment decisions; dropping standalone sources or inventing default organization is
forbidden. No automatic downgrade or hidden duplicate tables are implemented. Do not run
old code against format-17 files. No backups are created unless the owner requests them.

## Verification

Focused tests in test_optional_assessment_context cover all three standalone tools,
source/result identity through association, foreign-worker/duplicate refusal, SQL unique
constraints, referenced-worker protection, English/Spanish first Save and collapse,
Job-optional picker selection, actual association controls and subsequent navigation,
and real CBC/HiGHS job-only solve/save/reopen. Existing assessment, unit, history, PLOT,
JROT, lifecycle, conversion and golden-calculation regressions remain required.
Final gate and native visual evidence are recorded in STATUS and the validation artifact.

Acceptance, 2026-10-14: 1,347 tests passed, zero failures/skips, 95.45% coverage;
strict types, architecture/naming, documentation/inventory and builds pass. All 418
maintained files have structural documentation, and the 53 changed files were reviewed
against their actual contracts. Fifteen native EN/ES captures inspected; both established
fixtures updated in place with all unrelated data preserved. See STATUS and
artifacts/optional_assessment_validation.json for current delivery evidence.

Owner UI follow-up, 2026-10-17: standalone navigation is a separate, full-size footer
button in the existing context chooser, outside the workplace hierarchy. Clicking
it returns standalone navigation intent; Cancel preserves the current view. Association-only pickers
continue requiring a real assignment. The separate conditional Associate assessment
action and all Save/Discard/Cancel behavior remain unchanged.


## Current project Save boundary — 2026-10-18

The owner-approved single-Save workflow supersedes immediate/local-save wording above.
Accepted inputs and real association/assignment operations update only private project
state until the main Save. Same-Job first-assessment consent remains at main Save/Save As,
with session-local consent retained across failed-save retry. Worker/context navigation
retains accepted sources without Save/Discard prompts. Association and other record
operations share project Undo/Redo; replay removing records requires confirmation.
The format-16 ownership/uniqueness/result contract remains unchanged. See
[single project Save](single_project_save.md).
