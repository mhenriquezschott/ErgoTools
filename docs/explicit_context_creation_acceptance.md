# Explicit assessment creation from context — 2026-10-19

The owner approved removing assessment creation on Worker Management close because
adding several assignments left only the last assignment as hidden creation intent.
The owner has accepted the preceding table layout and confirmed Ana's No Job workplace
assignment survives main Save/reopen. This is a bounded workflow correction, not a new
migration milestone. Linux migration/cleanup remains 100%; Windows/macOS remain deferred.

## Behavior and ownership

Worker Management retains worker and workplace edits without switching or creating an
assessment. Its obsolete assessment-return fields and close-time creation branch are
removed. The assignment notification explicitly directs users to the main context picker.
A source-free project can still show its first worker's standalone preview without
creating a database assessment.

Select assessment context identifies the worker and active LiFFT/DUET/ST tool, shows
Saved/Not created ownership, and presents Open assessment or Create assessment for the
selected exact workplace/shift. Create inserts one blank default 15-task assessment for
that assignment/tool into private project state. Other assignments/tools and standalone
sources/results are unchanged. Main Save writes it; Cancel creates nothing. Opening an
existing assessment does not create a duplicate. If accepted draft staging has already
created this exact owner, it is reused without replacing entered values.

The existing same-Job/different-location warning is reused before explicit creation.
Consent is separate from the picker intent and cancellation retains the current view.
The host refreshes catalog/session authority after consent and pending-source resolution.
AssignmentSelector and the existing ProjectWorkspace/native creation transaction own
persistence; dialogs contain no SQL. Creation is reversible through existing shared
history, with confirmation before Undo removes the new assessment; assignment records
remain. Redo restores the same assessment identity. Standalone assessment navigation and
Associate assessment remain separate operations.

## Validation

Final required native gate: **1,965 passed, zero failures/skips, 94.43% coverage**;
strict types269, standards/format/architecture/naming/documentation/review and builds
pass. Independent wheel: **255 passed / 78 subtests**, all247 Python files and both
packaged guides exact, all loaded modules isolated. Thirteen changed files reviewed;
439 maintained files / 3,112 functions / 416 classes / 323 constants, zero pending/gaps.

Full gate/package evidence is recorded in
[validation](../artifacts/explicit_context_creation/validation.json) and current STATUS.
Native inspection found Spanish initialization overriding the preselected Open
caption; a bilingual initial-selection regression and conditional legacy caption fix
cover that defect. Initial native gate attempts aborted (one during garbage collection,
one at QApplication initialization); a direct probe subsequently confirmed the separate
X display was unavailable. Those attempts are not accepted evidence. The final gate
uses xvfb-run with a command-owned no-reset display. The existing shared main-navigation
fixture used by the new tests also processes deleteLater through Qt deferred deletion
at teardown, matching the established saved-tool fixture policy. This improves explicit
test resource ownership; it is not asserted to explain the display shutdown. No
production garbage-collection suppression or application workaround was added.

Focused regressions use three distinct No Job assignments before closing management,
all three tools in English/Spanish, no automatic prompt/navigation, exact first-selected
assignment creation, Cancel, main Save/reopen, opening existing data, same-Job Yes/No,
shared removal-consent Cancel/Yes and Undo/Redo, and existing preview input retention.
The first-worker/source-free scenario is updated to create explicitly from the picker.
Existing independent worker/assignment/association, history and ownership checks remain.
The broader organization integration scenario also creates explicitly through its
existing diagnostic selection host instead of relying on management close.

Twenty-eight native Linux XCB captures on private copies of the actual four-worker
project were inspected: EN/ES worker assignment notices, empty worker contexts, every
tool's selected missing/existing contexts, minimum/enlarged layout and created main
assessment view. Full-size selected controls/worker tables and both updated packaged
Help paragraphs were inspected. VTK was disabled for these dialog-focused captures;
its unchanged renderer evidence is reused, not claimed as newly visually inspected.

The owner's saved workflow database was checked read-only: exactly Ana W01's active
ST01 / Shift 1 assignment with placement_id NULL, no Jobs/placements, and all twelve
assessment owners standalone. Twelve source/result rows remain. No current test project
was modified by implementation or validation; all scenario writes used temporary copies.
Native format stays 18; no schema, migration, formula, dependency or reference changes.
Root dist packages are rebuilt; frozen dist/linux delivery remains historical.

## Next owner check

Restart ErgoTools, open the saved workflow project and select Ana / LiFFT. Worker
Management should close without any assessment question. In Select assessment context,
choose ST01 / Shift 1: it should show Not created and Create assessment. Creating there
should show a separate blank grid; Standalone assessment should return to Ana's existing
data. Main Save publishes an intentionally created assessment. Continue one workflow
step at a time after owner feedback; do not jump to association or more organization.
