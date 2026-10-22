# Job, placement and assignment persistence — F40

Explicit `AssessmentProjectFile.create_with_jobs` creates a version-five project
with hierarchy, assessment bindings and three ordered relationship tables.
Default creation remains version two; versions one through four are not upgraded.
Only synthetic temporary databases were used for this checkpoint.

## Preserved behavior

Immutable typed `Job`, `JobPlacement` and `WorkerJobAssignment` records form a
project-scoped `JobCatalog`. IDs are separate from display names. Dates and notes,
inactive history and assignments without a placement survive save/reopen.
Empty job names remain allowed by the reference SQL contract.

A placement must reference an existing job and exact station/shift. Assignment
owners must exist in the work hierarchy, including inactive history. Linked
placements must have the same workplace as their assignment. Duplicate IDs and
multiple active assignments for one worker/workplace are rejected.

Active placements for the same job/workplace cannot overlap. Endpoints are
inclusive and absent bounds use the reference SQL sentinels 0001-01-01 and
9999-12-31. Dates retain the reference lexical TEXT comparison; this is not new
calendar validation. Eight cases execute the extracted original INSERT trigger
under reference Python 3.10.18; the archived capture also installs the original
UPDATE trigger. The regression fixture tests the resulting snapshot invariant,
not a migrated historical reassignment command.

`classified_assignments` produces widget-independent chooser records, sorted by
plant, section, line, station and shift. Assessment eligibility uses assignment
and placement activity. It deliberately ignores job activity and date bounds,
matching the earlier reference assessment lookup audit. The separate job editor
may need different eligibility rules. The existing Qt dialog reexports the moved
`ClassifiedAssignment` type; no widget behavior or geometry changed here.

## Transaction and ownership contracts

Snapshot replacement acquires BEGIN IMMEDIATE, validates existing and incoming
relationships against the current hierarchy, and replaces all three tables in one
transaction. A failure after deletes/inserts restores the complete previous
snapshot. Hierarchy replacement also validates job references, preventing removal
of workers, stations or shifts used by active or historical records.

Public job reads use one SQLite read transaction for hierarchy and relationship
validation and result construction. A WAL-mode concurrent-writer regression proves
that a committed rename cannot mix versions within one read. Open rejects damaged
links rather than silently repairing them. Connections remain project-owned.

Cross-table referential checks live in the typed adapter, not SQL foreign keys.
Direct SQL editing is unsupported. Stored activity flags are checked on read.
Position columns preserve input order; chooser sorting is a separate projection.

## Limits and next steps

This is a repository snapshot API, not a user-facing assignment editor. F41 adds workspace refresh tokens and atomic expected-value conflict detection;
see [workspace jobs](workspace_jobs.md). Snapshot replacement does not implement closing a previous assignment
and creating its successor, or protect historical row identity across arbitrary
replacement. Those lifecycle contracts are required before exposing editing.

Existing assessment bindings identify worker/workplace/model; historical links
to particular assignment records have not been migrated. Job risk profiles,
complete worker metadata, legacy import and integrated UI wiring remain pending.
The final comprehensive reference project will be validated on a copy later.

## Evidence

412 tests pass (11 new), combined statement/branch coverage 98.87%; new storage and
option projection modules reach 100%, job domain 98.70%. Ruff, formatting, strict
mypy (93 files), architecture and source/wheel builds pass. The isolated wheel smoke
exercises version-five save/reopen, bound assessment creation and classified
projection alongside earlier workspace/dialog workflows. See
[f40_validation.json](f40_validation.json). All 500 original files and the approved
dependency lock match their recorded hashes. No visual change is claimed.
