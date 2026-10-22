# Transactional catalog persistence — F35

`AssessmentProjectFile.create_catalogued` explicitly creates project version four
with an empty WorkHierarchy and support for assessment bindings. Default creation
still produces version two, create_contextual still produces version three, and
opening versions one through three never migrates them. Catalog APIs on those
formats raise StoreFormatError. Existing files are never overwritten by creation.

## Storage and integrity decision

One constrained work_catalog row stores a version-one JSON hierarchy payload.
Ordered arrays retain workers, stations, shifts and all parent records, including
empty parents. Exact IDs, case, whitespace, optional names and list order survive
round trips. The strict decoder rejects duplicate JSON members, unknown fields,
unsupported versions, invalid value shapes, duplicate identities and orphan
hierarchy records through the existing typed domain validation.

This is a whole selection snapshot, not full worker/PLOT data or a normalized
editable database of every application record. A single-row write makes catalog
replacement atomic without introducing partial order updates. Referential rules
between JSON records and assessment bindings are enforced by these adapters,
not SQL foreign keys; direct SQL mutation remains unsupported.

Saving acquires BEGIN IMMEDIATE on the dedicated connection, validates the current
catalog, validates incoming project identity and every existing binding's worker,
station and shift membership, then replaces the payload and commits. Failure rolls
back and preserves the prior catalog. Removal of unreferenced empty parents or
workers is allowed; removing a referenced owner fails. Display-name changes and
reordering do not change assessment identity. Corrupt current data is rejected
rather than silently repaired by replacement.

Version-four binding writes inject membership validation into the existing binding
store while its write lock is held. Missing catalog owners prevent binding; the
saved draft remains unbound and can be retried after a valid catalog save. Version
three retains its existing catalog-independent behavior. Opening version four
validates both catalog and existing bindings before returning the owned handle.

## Validation

367 tests pass, including fourteen new cases. New storage module coverage is 100%;
combined project coverage is 98.73%. Standards, strict typing (87 files),
architecture and builds pass. Tests cover ordered/empty-parent round trips,
renames, referenced owner removal, missing new owners and retry, real SQL abort
recovery, corrupt payloads/references, foreign projects, old-format byte equality,
failed creation cleanup and closed handles. Independent package/reference/lock
verification is in `f35_validation.json`.

Only temporary synthetic projects were used. Original files, dependencies and UI
remain unchanged. No scientific formulas or review gates changed.

## Remaining work

Catalog saves commit immediately at the repository boundary. There is no catalog
edit session, undo history, workspace save/discard coordination, automatic stale
selector refresh, combined create-and-bind transaction, import or editor UI yet.
Repeated validation favors integrity over large-catalog optimization; characterize
real dataset costs before adding caching or incremental writes. Existing
single-owner/thread and no multi-writer merge guarantees remain.

Next expose catalog loading/saving through the workspace with explicit lifecycle
semantics and selection refresh rules, then implement combined assessment creation
and binding. Final integrated UI and copied comprehensive-project validation
remain the eventual acceptance targets.
