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

JROT has two explicit scope modes.

### All Jobs

**All Jobs** is organization-neutral. Its pool contains all active Workers and every
active Job with a current approved Job Risk Profile. It does not create or assume a
Plant, Station, Shift, Job Placement, or Worker Assignment.

A saved organization-neutral scheme has no `RotationSchemeScope` rows. Its rotation
targets identify a Job and frozen Job Risk Profile; `job_placement_id` is null.

### Workplace

**Workplace** uses real organizational assignments. **Choose Scope** opens a hierarchy
tree containing Stations with active Job Placements. Shift is a separate single-value
selector above the tree. The tree permits multiple Stations and branches in the same
selection.

After **Apply Scope**:

- eligible Job targets are active Job Placements in the selected Station/Shift contexts;
- eligible Workers have an active Worker Assignment in one of those contexts;
- the displayed hierarchy summarizes the applied contexts;
- the current table is rebuilt because entries outside the new pool are invalid;
- Worker count is capped by available Workers and Job targets, preserving the
  one-Job-per-Worker-per-time-block optimization constraint.

**Clear Scope** returns to All Jobs and rebuilds the pool. Selecting a workplace does
not transfer a Worker, move a Job, or modify organization records.

## Rotation Schemes

The Rotation ID combo selects an existing scheme or accepts a new ID. Workers and
Time blocks determine table dimensions. The navigation buttons select the first,
previous, next, or last saved scheme.

- **New** clears the selected record and prepares an unsaved schedule using the
  currently applied scope.
- **Save** requires every Worker row and time block to have an eligible value.
- **Delete** removes the scheme, its scope, targets, and assignments after confirmation.
- **Search** selects a saved scheme by exact Rotation ID.
- **Cancel** abandons the current edit and reloads the first saved scheme.

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

## Optimization

Before either optimization starts, JROT verifies that:

- every table row has a Worker and every time block has a Job target;
- every assigned target has the measurements required by the requested operation;
- missing results remain unavailable and are never treated as zero risk.

**Optimize Tool** minimizes the maximum average Worker risk for the selected Risk
basis while preserving how many times every Job target occurs in the current schedule.

**Optimize All Tools** uses LiFFT, DUET, and Shoulder measurements, first minimizing
per-tool Worker risk ceilings and then minimizing the remaining Worker spread while
preserving target totals.

The UI captures plain schedule and risk data before starting a background worker.
Solver threads do not read Qt widgets or discover an active window. Cancellation marks
the result for discard; an in-progress solver call is allowed to finish safely rather
than terminating its thread forcibly.

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
  persistence, organization-wide UI, workplace-scope UI, and visual captures.
