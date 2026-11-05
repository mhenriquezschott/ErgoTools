# Named rotation scenarios

Normal guided JROT uses scenario persistence and copied timing; see
[jrot_guided_entry.md](jrot_guided_entry.md). The normal JROT toolbar/menu continues to edit
its compatible schemes until the later guided/Legacy promotion checkpoint.

## Identity and incomplete work

A scenario has an immutable ID, editable name, planned local date and optional description.
Names are labels, so two scenarios may share a name or Line without becoming the same
record. A new accepted scenario requires its date. Earlier schemes keep their original IDs,
names, arrangements, descriptions and provenance; unknown dates and timing remain unknown.
An older optimization flag is not a reproducible new accepted run.

Current inputs hold the selected hierarchy/Shift, an independent clock/timing copy,
participants, Job/placement positions, selected tools and optional schedules. Baseline
and proposed arrangement are separate. A baseline is entered or explicitly promoted from
a saved result during rework. `baseline=None` means no baseline exists. An entered but unfinished matrix uses explicit `None` cells, which can be saved
and edited but cannot become solver input or an accepted run. An empty tuple before
participants are selected means Yes, observation exists but entry has not begun; it differs
from None. Native 23 admits that draft and does not permit a workerless accepted run. No blank becomes a fake Job,
zero risk or assumed current assignment. Completed rows reuse `WorkerRotation`.

## Accepted result context

A scenario can retain one immutable accepted `RotationRun`. It contains the exact planning
inputs, solution, source-bound Job values/tasks/results, frozen Job/worker/task labels,
selected tools, actual backend and ordered stage statuses, explicit settings, model version
and UTC completion timestamp. This context belongs to the rotation; it does not restore
selectable Job risk profiles. Current Job data still have one current value set per tool.
The run codec stores an integrity fingerprint over its exact context without rounding.
Reusable task IDs inside frozen sources are historical provenance; frozen task_names,
rather than the live task catalog, supply their original displayed labels.

Renaming or describing the scenario leaves its run intact. Changing current inputs or Job
measurements makes that run detectably stale, while its original evidence remains available.
Descriptive task/catalog renames do not change scientific freshness. Unknown positive model
versions remain readable evidence but cannot be treated as a current supported result.
Late result acceptance checks the captured planning inputs and current numerical Job data;
a pure scenario rename can survive, while changed inputs cannot accept a retired result.
Acceptance also independently validates staffing and hard restrictions. It does not prove
exact solver optimality. See [jrot_planning.md](jrot_planning.md) for model2 and boundary freshness.

Explicit duplication creates another identity and source-scenario provenance. Reworking an
optimized result copies that run's inputs and promotes its arrangement to the new baseline
once. It leaves the original baseline and accepted run intact and grants the duplicate no
optimization claim. Source provenance remains meaningful even if the source is later deleted.
Confirmation/re-optimization screens belong to the later guided-workflow checkpoints.

## Project ownership and persistence

`RotationScenarioRepository` borrows the active project's connection/session through
`ProjectWorkspace.rotation_scenarios()`. Guarded create/edit/delete operations use exact
expected state and one transaction/shared history step. Creation selects the new identity;
deleting the selected record clears selection in that same transaction. Read-only opening
creates nothing. Main Save alone publishes accepted edits; Undo/Redo, Save As, backup and
reopen preserve the whole record and selection coherently.

Last-viewed identity is independent view state in optional
`project_display_settings.last_rotation_id`. Opening chooses that existing record, otherwise
case-insensitive name/ID order. A stale ID uses a read-only fallback. An empty catalog means
new step 1 with the drawer open; saved selection means the drawer starts collapsed when the
guided development screen is used. Decimal/unit/disclosure updates retain the rotation choice.

Current references protect workers, Line, Shift, scope and exact assignment/placement
ownership through every ordinary and combined catalog-write path. Inactive historical links
remain valid. Selecting or applying a scenario never reassigns permanent workers, changes
assessments or moves PLOT markers. Shift template edits cannot rewrite a scenario's copied
clock or timing. Frozen old run evidence is not reinterpreted through live display catalogs.

Native 22 reuses `rotation_schemes`: compatible rows keep codec 2; guided rows use a distinct
`ergotools.rotation-scenario` tag, version 1. The compatible editor omits guided records and
refuses overwriting/deleting one through a stale selection. The project validates both
families. Guided data under an older native marker is rejected. Full-format conversion is
external; the 21→23 upgrade changes only the native marker and preserves all old table
values and timestamps without inventing dates, breaks, view choices or runs.

The current native marker is 23. Its 22→23 conversion validates the source capability and
changes only that marker. Existing guided payloads, runs, table values and timestamps stay
exact; new empty observed drafts hidden under native22 are rejected. Guided editing requires
the current format. No table, column, formula or optimizer change accompanies this marker.

## Native24 weighted-run contract

Guided codec2 adds typed worker restrictions and explicit previous/following boundary snapshots.
The model2 run retains exact duration weights and selected tools. Codec1/model1 evidence
remains readable without being promoted to a new-model result. See jrot_planning.md.

## Frozen comparisons and explicit rework

J07 displays accepted-run evidence with its frozen coefficients/timing and qualifies stale
current sources. Default rework creates another identity and promotes the result once;
confirmed replacement keeps the old immutable run until it is explicitly replaced.
No additional storage is needed. See jrot_comparisons.md.
