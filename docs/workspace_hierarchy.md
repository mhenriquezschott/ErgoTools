# Workspace catalog access and refresh — F36

The optional HierarchyRepository port supplies validated load and atomic
expected-source replacement. ProjectWorkspace.read_hierarchy returns an immutable
HierarchySnapshot owned by the current workspace/project handle. It invalidates
previous snapshots before loading; a failed refresh therefore cannot leave old
callbacks eligible to write.

replace_hierarchy requires that exact latest snapshot object, checks project
identity and delegates expected-value replacement to the repository. SQLite
compares the currently saved hierarchy under BEGIN IMMEDIATE before any update.
A conflict rejects the write without overwriting separately saved changes.
Membership/orphan validation from F35 still applies in the same transaction.
Successful replacement returns a fresh snapshot; failed writes leave the current
snapshot eligible for retry. A conflict needs a refresh and deliberate reapplication
of the desired change, not an automatic overwrite.

## Lifecycle decisions

Snapshots are scoped to the project handle, not the active assessment. Switching
documents in the same project retains them. Successful project creation/switch or
close invalidates them; a failed transition retains them. An equal copied snapshot,
another workspace's snapshot or a previously closed project's snapshot is rejected.
Reentrant workspace operations are rejected during catalog I/O.

Catalog replacement commits immediately as an explicit operation. It does not save
assessment tasks, clear their dirty state, change active selection, alter assessment
undo/redo or update recent-file preferences. Assessment Undo therefore does not undo
a catalog save. This API is not a catalog edit session or pending-text policy.
Future UI editors must give catalog changes their own clear commit/cancel behavior.

The repository compares values, not a persistent generation counter: it cannot
detect an external change that returns to exactly the same saved content. This
provides stale-value protection, not multi-writer merging or a general concurrency
protocol. Low-level save_hierarchy remains the explicit unguarded initialization/
replacement API; workspace edits use replace_hierarchy.

## Validation and remaining scope

377 tests pass, including ten new scenarios on temporary version-four projects.
Coverage is 100% for the new port module and workspace. Full standards, strict
mypy (88 files), architecture and build gates pass. Tests cover active dirty-history
and recency preservation, copied/foreign/stale snapshots, failed refresh, SQL retry,
expected-value conflict, orphan rejection, project switching/reopening and unsupported
adapters/formats. Independent package/source/lock evidence: `f36_validation.json`.

No schema, default file format, dependency or UI changed. There is no automatic
widget refresh: a caller must rebuild dependent options from the returned snapshot.
Complete catalog editors, catalog undo, pending widget text and final UI parity
remain pending. Next: atomic assessment creation plus binding, so a failed bind
cannot leave a newly created unbound document in that combined workflow.
