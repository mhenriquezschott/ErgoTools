# JROT Functional Specification

This specification defines the current Job Rotation Optimization Tool behavior after
integration with Jobs, Job Risk Profiles, Job Placements, Worker Assignments, and the
shared workplace hierarchy.

## Purpose and Risk Basis

JROT defines, saves, optimizes, and compares rotation schedules. A table row is a
Worker and each time-block cell is a Job target. The Risk basis control changes the
Job measurement displayed and used by **Optimize Tool**:

- **LiFFT** uses the Job target's LiFFT measurement.
- **DUET** uses the Job target's DUET measurement.
- **Shoulder** uses the Job target's Shoulder Tool (`ST`) measurement.

Changing Risk basis does not filter Workers or Jobs and does not change the saved
rotation scope. For a saved scheme it reevaluates the same frozen profile versions;
it does not silently switch the scheme to a newer Job profile.

## Rotation Scope

JROT has two explicit scope modes. **All Jobs** and **Workplace** determine which
Workers and Job targets may be placed in the matrix. They must not be confused with
**Optimize Tool** and **Optimize All Tools**, which determine which risk measurements
are used after the matrix has been defined.

### All Jobs

**All Jobs** is organization-neutral. Its pool contains all active Workers and every
active Job with a current approved Job Risk Profile. It does not create or assume a
Plant, Station, Shift, Job Placement, or Worker Assignment.

Consequently, an All Jobs scheme may combine any active Worker with any eligible Job,
regardless of Plant, Section, Line, Station, Shift, current Worker Assignment, or Job
Placement. It represents a general or hypothetical rotation design like the original
JROT workflow, not necessarily an immediately deployable workplace schedule.

A saved organization-neutral scheme has no `RotationSchemeScope` rows. Its rotation
targets identify a Job and frozen Job Risk Profile; `job_placement_id` is null.

### Workplace

**Workplace** uses real organizational assignments. **Choose Scope** opens a hierarchy
tree containing Stations with active Job Placements. Shift is a separate single-value
selector above the tree. The tree permits multiple Stations and branches in the same
selection.

The selection workflow is:

1. Select **Workplace**.
2. Press **Choose Scope**.
3. Choose one Shift and check one or more Stations. Checking a Plant, Section, or Line
   checks its descendant Stations.
4. Press **Use scope** to stage the selection and review its hierarchy summary.
5. Press **Apply Scope** to rebuild the eligible Worker and Job pools and the matrix.

The tree shows only Stations having at least one active Job Placement for the chosen
Shift. A usable scope additionally requires at least one active Worker Assignment and
at least one active Job Placement whose Job has a current approved risk profile.

After **Apply Scope**:

- eligible Job targets are active Job Placements in the selected Station/Shift contexts;
- eligible Workers have an active Worker Assignment in one of those contexts;
- the displayed hierarchy summarizes the applied contexts;
- the current table is rebuilt because entries outside the new pool are invalid;
- Worker count is capped by available Workers and Job targets, preserving the
  one-Job-per-Worker-per-time-block optimization constraint.

A Worker is eligible because of an active assignment to one of the selected workplace
contexts. The Worker does not need a direct assignment to every Job in the pool. A Job
is eligible because it has an active placement in a selected context. JROT may rotate
any eligible Worker among the eligible Job targets.

For example, if Station A on Shift 1 has Workers `W001` and `W002` and active
placements for `Job-001` and `Job-002`, both Workers may rotate between both Jobs. A
Worker without an active assignment to Station A on Shift 1 is excluded.

When several Stations are selected, the pool is their union. For example:

```text
Shift 1
Station A: Workers W001, W002; Jobs Job-001, Job-002
Station B: Worker W003;       Job Job-003
```

The eligible pool contains all three Workers and all three targets. The current model
may rotate any of those Workers across those targets; it does not constrain a Worker to
remain at the Worker's original Station or model walking time. If the same Job is
placed at two Stations, the two Job Placements are distinct targets and their matrix
occurrences are preserved separately.

**Clear Scope** returns to All Jobs and rebuilds the pool. Selecting a workplace does
not transfer a Worker, move a Job, or modify organization records.

### Scope Advantages and Limitations

**All Jobs advantages:**

- preserves the flexible original JROT workflow;
- supports hypothetical planning before workplace data is complete;
- permits comparison of Jobs and Workers from anywhere in the project;
- requires less organizational setup and can expose theoretically balanced rotations.

**All Jobs limitations:**

- may propose physically or operationally impossible rotations;
- ignores Station distance, Shift compatibility, travel time, qualifications, staffing,
  availability, and production constraints;
- has no Job Placement or Worker Assignment provenance and therefore must be treated as
  a design scenario rather than an operational schedule.

**Workplace advantages:**

- restricts the pool using real Station/Shift Job Placements and Worker Assignments;
- preserves exact workplace, placement, assignment, and risk-profile provenance;
- distinguishes the same Job at different Stations;
- reduces accidental mixing of unrelated organizational areas and is more suitable for
  operational planning and auditing.

**Workplace limitations:**

- requires the workplace hierarchy, Job Placements, and Worker Assignments first;
- incomplete or outdated assignments can exclude otherwise valid candidates;
- a multiple-Station scope currently permits movement across every selected Station;
- does not model distance, travel time, training, qualifications, breaks, production
  order, or staffing demand beyond one Worker per target in a time block;
- a narrow scope may provide too few targets to improve the risk distribution.

Use All Jobs to ask, "What is the best theoretical distribution among these Workers
and Jobs?" Use Workplace to ask, "What rotation can be designed from the Workers and
Job Placements available in this selected area and Shift?"

### Switching Scope

All Jobs and Workplace are alternative scopes for one editor, not simultaneous matrix
tabs. Applying another scope rebuilds the current matrix and clears its optimized
result. An unsaved matrix from the previous scope is discarded; the database is not
changed until **Save** is pressed.

Saved scopes are independent only when they use different Rotation IDs. For example,
`ROT-AllJobs-01` and `ROT-Workplace-A-01` remain separate saved schemes. If an existing
All Jobs scheme is loaded, changed to Workplace, and saved with the same Rotation ID,
the saved record is updated: its old scope, targets, and assignments are replaced by
the Workplace definition. **Cancel** instead restores the saved scheme that was active
before the scope change.

## Rotation Schemes

The Rotation ID combo selects an existing scheme or accepts a new ID. Workers and
Time blocks determine table dimensions. The navigation buttons select the first,
previous, next, or last saved scheme.

- **New** clears the selected record and prepares an unsaved schedule using the
  currently applied scope.
- **Save** requires every Worker row and time block to have an eligible value.
- **Delete** removes the scheme, its scope, targets, and assignments after confirmation.
- **Search** selects a saved scheme by exact Rotation ID.
- **Cancel** abandons the current edit and restores the saved scheme that was active
  before **New**, **Apply Scope**, or **Clear Scope**.

New schedules and applied scope changes are unsaved drafts. Navigation, Delete, and
Search are disabled while a draft is active so they cannot operate on a saved scheme
whose table is no longer displayed. Saving or cancelling returns those controls to
their position-appropriate states.

Saving is one database transaction. It records:

- scope contexts, or no contexts for All Jobs;
- the exact Job Placement for each scoped target;
- the exact Job Risk Profile version used by each target;
- the Worker and, for scoped schedules, its source Worker Assignment;
- each zero-based time block and its Rotation Target;
- whether the saved schedule is manual, selected-tool optimized, or all-tool optimized.

Legacy schemes migrate as All Jobs schemes. Their historical Plant and Shift text did
not prove assignment-backed scope and is therefore not converted into invented Job
Placements. Legacy assignments and their selected profile versions remain preserved.

## Table Behavior

The Worker column accepts eligible Workers without duplicate rows. Each time-block
column accepts eligible Job targets without duplicating the same target in that time
block. A scoped target label includes its Station; a longer hierarchy label is used
when short labels would collide.

Each populated target cell shows Job target and outcome probability, uses the shared
ISO/tool-specific derived risk color, and exposes profile version/source provenance in
its tooltip. The Avg. column is the mean outcome probability for that Worker. The
Recommendation column describes whether rotation alone appears adequate or Job
redesign should be considered.

The matrix does not need to use every eligible Worker or target. It must use distinct
Workers, contain one eligible target in every time block, and avoid assigning the same
target to two Workers in the same time block.

## Optimization

Before either optimization starts, JROT verifies that:

- every table row has a Worker and every time block has a Job target;
- every assigned target has the measurements required by the requested operation;
- missing results remain unavailable and are never treated as zero risk.

**Optimize Tool** minimizes the maximum average Worker risk for the selected Risk
basis while preserving how many times every Job target occurs in the current schedule.

For example, if the input matrix contains `Job-A` twice, `Job-B` twice, and `Job-C`
twice, the optimized matrix must contain those same totals. The optimizer may change
which Worker performs each occurrence and its time-block sequence; it does not remove
work or introduce a different target.

**Optimize All Tools** uses LiFFT, DUET, and Shoulder measurements, first minimizing
per-tool Worker risk ceilings and then minimizing the remaining Worker spread while
preserving target totals.

The UI captures plain schedule and risk data before starting a background worker.
Solver threads do not read Qt widgets or discover an active window. Cancellation marks
the result for discard; an in-progress solver call is allowed to finish safely rather
than terminating its thread forcibly.

The active MILP backend is HiGHS. CBC is retained only as a runtime fallback if
HiGHS cannot initialize; GLPK is not used by the active optimization path. The tested
optimizer baseline is Python 3.10.18, PuLP 3.2.2, and highspy 1.11.0.

**Use as Current** copies the optimized schedule into the editable table. The user must
press **Save** to persist it. **Compare** requires an optimized result and opens the
current-versus-optimized comparison for the selected Risk basis.

## Required Empty and Error States

- A scope with no active Job placement or no active Worker assignment is reported as
  an empty rotation scope.
- A Job target missing a required approved measurement blocks optimization and lists
  the target and tool.
- A saved historical scheme may continue to display a frozen profile that is no longer
  current; this is intentional reproducibility, not stale loading.
- A deleted Worker, Job, placement, profile, or assignment referenced by a scheme is
  protected by database foreign keys rather than silently orphaning the scheme.
- Solver infeasibility, missing incumbents, and solver failures are shown as errors and
  do not replace the current schedule.

## Automated and Visual Coverage

- `tests/test_rotation_repository.py` covers migration, pools, frozen profiles, and
  scope/provenance integrity.
- `tests/test_rotation_optimizer.py` covers selected-tool and all-tool optimization
  using plain data snapshots.
- `tests/test_jrot_profile_ui.py` covers profile preflight, both background optimization
  modes, result transfer, both comparison views, scheme save/reload, provenance
  persistence, organization-wide UI, workplace-scope UI, draft cancellation/control
  states, and visual captures.
