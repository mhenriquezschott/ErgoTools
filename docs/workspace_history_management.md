> Historical checkpoint, superseded by the owner-directed removal of assessment versions.
> See [current ownership contract](single_assessment_ownership.md). The version UI/API described below no longer exists.

# Workspace history management — F53

ProjectWorkspace.read_history publishes an immutable HistorySnapshot. Only the
latest exact snapshot object issued for the current project handle authorizes
select_current_version. Equal copies, earlier refreshes and reopened handles do
not confer authority. Failed refresh invalidates old authority before I/O.

Version updates delegate to the repository's atomic expected-history comparison.
Success publishes a new snapshot; validation/write failure leaves the current
snapshot available for retry. Conflicting saved values require refresh. An
inconsistent adapter result invalidates authority and raises; this does not imply
that an already committed adapter write was rolled back.

Version changes do not activate another document, save source edits, clear dirty
state, alter undo history or update recent-file settings. The currently open
document may therefore become noncurrent and remain editable. The future UI must
display this explicitly; selecting the new current source is a separate transition
with existing Save/Discard/Cancel rules.

Successful project switch/create/close clears history authority. Same-project
document selection retains it. Successful historical assessment creation also
clears it because it adds ownership records. Job/hierarchy views are separate
capabilities; repository operations still revalidate saved references.

The optional MutableHistoryRepository port adds current-version mutation without
requiring it from every history reader. Unsupported adapters and older formats
fail explicitly. Source data changes are not revision-tracked by this history
snapshot; its authority concerns ownership/version metadata.

Three integration scenarios cover copied/stale views, dirty-source/undo isolation,
same-project switching and reopened handles, failed refresh/write, competing
creation, successful creation invalidation, foreign/inconsistent adapter results,
nested calls and unsupported adapters. All 469 tests pass; total coverage 98.92%,
history access and workspace 100%. Ruff/format, strict mypy (101 files), architecture
and builds pass. Extracted-wheel authority and current-version checks pass.
All 500 reference files and the dependency lock are unchanged; f53_validation.json
records the evidence.

This completes the workspace safety layer for version management in the worker/job
migration. Version and creation controls still need presenter/UI composition.
No schema, dependency, scientific or UI change occurred.
