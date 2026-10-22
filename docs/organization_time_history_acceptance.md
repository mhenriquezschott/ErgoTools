# Organization clocks and shared Undo — verified, 2026-10-19

Owner reports that Shift description/start-time edits do not enable Undo and that
time inputs accept text. Both issues reproduced on a private copy of the saved
four-worker workflow project. The organization tree and independent shift persist;
the saved file has Workflow Plant / Packing / Line A / ST01 + ST02 and shift 1,
with 12 standalone assessments/results and no assignments or Jobs. No owner-file
writes were performed.

## Cause and correction

OrganizationDialog already accepted valid form edits on navigation/Close, but it
never supplied ProjectHistoryActions with pending-edit inspection or dynamic editor
change notifications. Therefore a clean shared cursor stayed disabled while fields
were being edited. This affects every organization level; shifts were not using a
separate history engine. Time fields were ordinary unvalidated line editors, with
no 24-hour acceptance rule.

Existing-record drafts now use the same pending callback contract as Workers.
All optional line/multiline fields, including numeric fields, refresh the shared
Undo/Redo availability. Valid pending input enables Undo immediately; Redo stays
unavailable until that new edit is reversed or cancelled. Mouse history buttons
take focus, accept the form once and replay the project cursor. Keyboard Undo in
a focused text editor remains native. Multiple pending fields in one record form
are accepted together at replay/navigation/Close; this is the existing record
acceptance boundary, not a new per-keystroke project history. Cancel reloads the
record without adding a command. New records retain their existing acceptance
and removal-confirmation policy. Main Save remains the durable write boundary.

Plant and Shift start/end fields retain standard QLineEdit controls, with a Qt
regular-expression validator for optional 24-hour HH:mm strings. Labels explicitly
state 24 h / HH:mm, blank controls show HH:mm, and localized tooltips explain
00:00-23:59 and optional emptiness. Native typing/paste rejects letters and invalid
clock strings. Acceptance also rejects malformed/incomplete nonempty input with
localized guidance, preserving the form and private/saved data. Empty values stay
None; no midnight sentinel or automatic normalization is invented. Overnight shifts
such as 22:00 to 06:00 remain valid; no start-before-end rule is imposed.

## Validation

Required native Linux `bash tools/check.sh`: **1,790 passed, zero failures/skips,
94.47% coverage**. Ruff/format, strict types (265), architecture, naming,
documentation structure/review and wheel/source builds pass. Native focused tests:
79 passed. Independent wheel: 95 passed / 78 subtests; all 243 package Python files
and both guides equal current reviewed source. Final gate wheel SHA matches the
independently tested wheel.

Maintained tests cover every optional field at every organization level, repeated
mouse Undo/Redo to the same baseline, pending availability, native text Undo,
Cancel, invalid typed/pasted/programmatic clock data, exact range boundaries,
optional blanks, overnight shifts, new-record validation, main Save and reopen.
Initial full-run failure was confined to the new typing test's inactive-window
setup; explicit activation and a real-focus assertion corrected the harness.
The subsequent native focused and full runs pass; application code did not change
for that test correction. See the test setup note for the earlier result.

Twenty-six native EN/ES captures inspected: collapsed/expanded/current/new Shift,
description and time pending/Undo/Redo, invalid correction, empty optional times,
minimum size and both Plant clock fields after scrolling. Existing theme, footer,
labels and history buttons fit. Both updated packaged Help sections rendered and
inspected. Architecture, shared-saving contracts and user guides updated. Three
maintained files substantively reviewed and exact hashes certified; inventory is
431 files / 3,006 functions / 412 classes / 315 constants, zero pending/gaps.

Evidence: [reproduction](../artifacts/organization_time_history/reproduction.json),
[validation](../artifacts/organization_time_history/validation.json),
[visuals](../artifacts/organization_time_history/visual_validation.json),
[package](../artifacts/organization_time_history/package.json),
[test setup note](../artifacts/organization_time_history/test_setup_note.json).
Owner workflow, both maintained comprehensive fixtures and uv.lock retain their
starting hashes. No schema, calculations, dependencies, reference files or permanent
test projects changed. Linux migration/cleanup remains 100%; Windows/macOS remain
explicitly deferred. No milestone added.

## Next owner check

Restart and open shift 1. Edit its description or change 08:00 to 09:30: Undo should
become available immediately. Click the title-row Undo and Redo without closing.
Try letters and a partial time to confirm restriction/correction guidance. Restore
the desired 08:00/16:00 values before main Save. Await owner feedback before
associating Ana with ST01; the organization workflow test remains active.
