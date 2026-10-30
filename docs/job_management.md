# Job Management

A Job is an assessed activity, distinct from a physical Station. Job Management maintains
its ID, name, description, workplace availability and one current value set for each tool.
It has no profile/evidence/version selector. Source tasks and calculated results are kept
with the Job; copies are independent of their worker or Job origins.

The left panel navigates Jobs and groups metadata, workplace placements and source reuse.
The middle tool tabs use the same LiFFT/DUET/ST grid, input controls, column order and
result formatting as the main worker assessment UI. The selected-tool panel shows its
risk gauge, damage bar, metrics and common risk ranges. Project identity is visible above
the editor. Tool and Job navigation share the project history without creating data edits.

Task inputs is the default for an empty tool and displays one unsaved starter row. Plus /
minus Task adjusts the source up to 100 rows. Removing entered rows requires confirmation;
shared Undo restores the removed tasks and matching results. Valid complete input updates
calculations automatically; Calculate remains available. Blank unused rows are ignored.
Direct result mode instead accepts cumulative damage in the colored total cell and derives
probability through the established tool function, without recording invented tasks.

Copy from worker searches that tool's standalone and workplace assessments. Copy from Job
selects another Job's corresponding tool. Expand a source to inspect read-only populated
tasks and select all or a subset. Full copies retain exact source/results; calculated
subsets are recalculated through the existing calculator. Uncalculated input remains
uncalculated. Source records stay unchanged and replacing Job data requires consent.

Workplaces manages where a Job is available. It does not change task results merely by
placing the Job or assign a worker implicitly. Valid edits stay in the shared project
session when the window closes; only main Save writes the project. Secondary Undo/Redo
uses the main chronological history. Relevant risk changes invalidate old optimization
provenance while preserving saved JROT worker/Job arrangements.

See [shared editor](shared_assessment_editor.md), [database tables](database_tables.md),
[Worker Management](worker_management.md) and [API contracts](api_contracts.md).
