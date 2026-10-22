# Workspace selection by assessment context — F32

`ProjectWorkspace.select_context(context, choice=...)` resolves a saved assessment
inside the current project using the optional AssessmentBindings port. It changes
the active document only: it neither moves/copies assessment data nor changes
project connections, paths, recent-file preferences or persisted bindings.

## Selection and failure ordering

1. Reject a nested transition or invalid dirty-choice value using the existing
   workspace guard. Cancel, or an absent choice when dirty, returns an incomplete
   TransitionOutcome without repository I/O.
2. Require an open project, matching project identity and the ownership adapter.
   Older formats keep their explicit unsupported-format error; no migration runs.
3. Resolve the exact context and verify its reverse document binding. Missing
   contexts raise KeyError. Foreign or inconsistent adapter identities fail.
4. Prepare the target session before any current save. If an adapter unexpectedly
   changes current revision/dirty state during lookup/loading, abort selection
   and retain that session, including the unexpected edit.
5. If the resolved document is already active, return success with the exact same
   session and history. Otherwise, save the current draft only for Save, then
   activate the prepared target. Discard does not write the old draft.

Lookup, binding, load and save failures propagate while retaining active session
ownership. The transition guard clears after failure so the caller can retry.
Successful transitions create a clean target session with no inherited undo
history. Old source units, bindings and other model documents remain intact.

## Same-context and caller responsibilities

A same-context selection with Save or Discard is a no-op, like the existing
same-document switch; explicit workspace.save remains the way to save without
switching. Because context resolution requires repository access, a dirty draft
with no decision returns incomplete even when the requested context would resolve
to that same document. This differs from document-ID switching, which can identify
the no-op without I/O. UI integration should suppress redundant selection events
when the active context is already known, and must resolve pending uncommitted
widget text separately from committed session edits.

The port is now runtime-checkable for capability discovery. That check establishes
method availability, not supported file version or correctness; adapter errors
and reverse-binding checks remain explicit. Selection is synchronous and uses
the existing dedicated single-owner connection contract. It does not establish
multi-writer snapshot consistency or background task coordination.

## Validation and remaining scope

325 tests pass, including ten new workspace scenarios against small temporary
SQLite projects. Tests cover all three models, Save/Discard/Cancel, no-op history,
settings/connection preservation, missing/failed targets, real SQL save failure
and retry, foreign/inconsistent adapter results, nested transitions, unexpected
edits, missing projects and unsupported formats/adapters. The workspace module
has 100% combined statement/branch coverage. All standards, strict typing,
architecture and build gates pass. Independent wheel/reference/lock evidence is
in `f32_validation.json`.

No UI, schema, dependency or scientific model changed. Worker/workplace catalog
migration, combined create-and-bind behavior and selector presentation are still
pending. Next audit the reference worker/workplace catalog contracts and migrate
them with focused fixtures; keep final integrated UI and comprehensive copied
project validation as later acceptance targets.
