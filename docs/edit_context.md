# Presenter edit-context ownership — F26, 2026-09-29

`AssessmentEditor` now owns the exact source projection and decimal convention used to initialize an editor. Its immutable `EditContext` is captured with callbacks. This closes the F24/F25 gap where source freshness alone could not distinguish obsolete display settings. It is a widget-independent presenter boundary, not a rendered interface.

## Lifecycle contract

Bind with the actual active session, display measurement system and explicit decimal convention. Every bind creates a distinct context, even if values compare equal. A toggle away and back cannot revive an older editor; another presenter or a reconstructed equal dataclass cannot supply the owner's context. Identity checks precede numeric parsing and source mutation.

Binding first clears the previous context. Unsupported units/conventions, unitless DUET or numeric projection failures therefore leave no usable old interpretation. This is intentional fail-closed behavior for a failed view transition; source and history remain unchanged. The owner may retry binding after correcting the problem.

Submit with the exact context captured when the editor was initialized and the actual current session. An obsolete context raises localized `validation.stale_editor`. Valid contexts reuse the tested text parsing, unit conversion and document-scoped commands. Invalid text retains context for correction. Exact-value re-entry preserves context and creates no history entry. A successful source edit clears context; undo does not revive that consumed editor.

Clear on close or workspace switch to release the retained projection/session reference. External edits invalidate source freshness; rebind when rendering their result. If no rebind/clear occurred, undo can restore the original source snapshot's eligibility, consistent with existing preparation contracts. After any rebind, older context identity is permanently invalid. Caller-supplied closed/foreign/reloaded sessions cannot pass the source check.

## Desktop integration requirements

The first desktop presenter must capture contexts in callbacks, rather than substituting whichever context is current when delayed callbacks arrive. Rebind after source rendering or display-unit/decimal changes; clear before switching/closing a document. Initialization must use full-precision editor formatting, and only deliberate field edits may be submitted.

This class owns interpretation, not pending text or widgets. Rejected text must remain available for correction/copying or explicit dismissal. It does not automatically discard or commit a partially edited value when preferences change. The GUI needs a visible, tested policy for that interaction, including focus changes, delayed signals and error display. Source evaluation gates and project lifecycle still belong to their existing owners.

No GUI, VTK adapter, settings persistence, runtime dependency or schema changed. Next work is the first desktop slice's runtime/style audit and a concrete exact-version dependency proposal; installation requires the existing explicit approval rule.

## Evidence

Eight new tests cover both dimensional models, accepted/no-op/invalid submissions, context immutability, unit/decimal toggles, equal/foreign contexts, failed binding, close/reload/session changes, external edits and undo/redo, independent owners and translated errors. All 277 tests pass. Combined coverage is 99.61%; the new module has 100% statement/branch coverage. Ruff/format, strict mypy (73 files), architecture and builds pass. Independent wheel, original-file and dependency-lock verification are recorded in `f26_validation.json`.
