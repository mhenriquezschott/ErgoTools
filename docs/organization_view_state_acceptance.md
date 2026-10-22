# Organization working view preservation — verified, 2026-10-19

Owner confirms Shift clocks and live Undo work, then reports that Optional details
collapses during Undo and location branches collapse after Delete/Undo. Bounded
private-project reproduction identifies forced optional-toggle reset, wholesale tree
replacement without expansion retention and discarded deleted-record selection.
Qt's automatic ancestor reveal during reselection also changes intentionally closed
branches, even if the initial tree rebuild restored them.

## Accepted behavior

Optional details keeps the user's current open/closed state across form rebuild,
accepted edit, navigation, Delete and shared Undo/Redo for locations and independent
shifts. Existing initial collapsed appearance is unchanged for a fresh dialog.

Before replacing tree items, the dialog remembers expanded AND collapsed flags by
complete location ancestry. Surviving branches use current user flags; temporarily
removed subtree identities retain their last flags until this dialog closes, so
Undo can restore them at the same depth. Internal edit/replay selection reapplies
those flags after Qt's automatic ancestor reveal. Explicit navigation and creation
of new records keep normal reveal behavior.

Undo restoring a deleted record reselects it unless the user has since selected
another record. Still-deleted identities leave the existing empty selection view;
replay no longer opens an unrelated blank Plant form. A later deliberate collapse
or different selection is respected. Cancelled deletion remains inert; deletion
reference protection, removal consent and exact shared source replay are unchanged.

All retained view choices belong to the open OrganizationDialog, using typed paths
and booleans rather than retired Qt item references. They add no database columns,
settings, history snapshots or dirty state. No application/domain/storage change,
extra Save, assessment version, dependency or reference write was introduced.

## Validation

Required native Linux `bash tools/check.sh`: **1,834 passed, zero failures/skips,
94.50% coverage**, all standards/format/types (265), architecture, naming,
documentation/review and builds pass. Native focused organization/shared-save suite:
123 passed. Independent extracted wheel: **139 passed / 78 subtests**, all 243
package Python files and both guides equal reviewed source; converter excluded.
Final full-gate wheel hash equals the independently tested build.

Maintained regressions cover all five organization levels in both languages, open
and closed details, repeated edit/Delete/Undo/Redo, actual Delete cancellation,
exact private hierarchy and saved bytes, mixed sibling/hidden-descendant flags,
user collapse/selection after deletion and fresh-dialog initial state. UI-only
changes add no history or dirty flag. Existing clock, native typing, validation,
organization, assignment and unified-save regressions continue to pass.

Twenty-eight native EN/ES captures inspected, including Line A with ST01/ST02,
confirmation, empty deleted view, actual consent-button Redo, repeated restored
selection, Shift expanded/collapsed replay and minimum-size control fit. Both Help
paragraphs rendered and inspected. No new clipping. An initial capture harness used
QMessageBox.done for the static Redo question, which cancels without a clicked
standard button; final captures use the actual Yes button and assert the source is
deleted/restored before recording. No application change was needed for that
harness correction.

Two maintained files substantively reviewed; exact documentation hashes/inventory
updated. Current inventory: 431 files / 3,016 functions / 412 classes / 315 constants,
zero pending/gaps. Architecture, shared-saving contract and bilingual guides updated.
Owner workflow, both maintained comprehensive fixtures and uv.lock retain their
starting hashes. Linux migration/cleanup remains 100%; Windows/macOS deferred.

Evidence: [reproduction](../artifacts/organization_view_state/reproduction.json),
[validation](../artifacts/organization_view_state/validation.json),
[visuals/protections](../artifacts/organization_view_state/visual_validation.json),
[package](../artifacts/organization_view_state/package.json).

## Next owner check

Restart, open Organization and expand the hierarchy and Optional details. Edit a
Shift/location value and Undo/Redo; the current panel should remain open. Delete
Line A then Undo: Line A should return selected with ST01/ST02 still revealed;
Redo/Undo should repeat correctly. Do not Save unwanted deletions. Await feedback
before continuing the four-worker workplace association test. No new milestone.
