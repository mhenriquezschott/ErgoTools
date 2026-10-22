# Assessment selection presenter — F38

AssessmentSelector owns widget-independent catalog and selection callbacks for one
ProjectWorkspace. SelectionCatalog exposes the workspace-issued hierarchy snapshot
and reference-compatible WorkerOptions. UI code can read the existing hierarchy
child queries, including empty parents, without parsing worker captions or deriving
IDs from positions. Refresh never selects a default worker, workplace or model.

prepare requires an explicit worker ID, complete workplace and AssessmentKind.
Catalog membership is checked before constructing AssessmentContext. Incomplete
widget selections remain outside a complete AssessmentSelection; no first-item
fallback is invented for missing data. Preparing another choice invalidates the
previous one even if validation subsequently fails.

## Callback and source ownership

Only the presenter's current SelectionCatalog and exact AssessmentSelection objects
are accepted. Copies with equal values and objects from other presenters fail.
Workspace.hierarchy_is_current provides a read-only identity check, reusing the
existing project-handle/snapshot lifetime rules. Catalog refresh/replacement or
project changes invalidate old views; successful selection/creation consumes the
request. Active session identity and revision must still match preparation, so a
callback cannot silently apply old dirty-choice intent to another source.

Cancel or absent dirty consent leaves the request retryable. Lookup and SQL failures
also remain retryable when its source/catalog is still current. select delegates
to context lookup; create checks initial source model *before* any current save,
then delegates to the atomic creation workflow. Missing existing bindings can be
followed by deliberate creation using the same explicit choice. No implicit
creation occurs during lookup.

## UI integration boundaries

This is not a new window or a specification for the final layout. The Qt adapter
must resolve uncommitted widget text before calling select/create, rebuild dependent
options after refresh and restore visible selection on cancellation/failure. It
must use the reference layout, assets and interaction patterns; the temporary
LiFFT harness is unchanged. Complete partial-selection cascade policy and worker/job
editors are not implemented here. Snapshot checks track known workspace refreshes,
not external file monitoring; repository integrity checks still apply at I/O.

## Validation

396 tests pass, including eight new end-to-end presenter scenarios using temporary
version-four projects. Tests cover all three models, explicit IDs containing spaces,
reference labels/order, empty parents, Save/Discard/Cancel, mismatched source models,
foreign/copied/stale callbacks, catalog refresh/failure, active edits/switches,
missing membership/bindings, SQL rollback and retry. The presenter has 100% combined
statement/branch coverage; overall coverage is 98.80%. Standards, strict mypy
(89 files), architecture and builds pass. `f38_validation.json` records independent
package/reference/lock checks. No UI, schema, dependency or scientific gate changed.

Next: connect these workflows to reference-aligned selection controls with explicit
pending-text and cancellation handling, then visually inspect all affected states.
Full worker/job metadata and editing remain separate subsequent migration work.
