> Historical implementation record. Its original controls, storage and pending-work
> statements are superseded by the [current documentation index](README.md),
> [user guide](user_guide.md) and [API contracts](api_contracts.md).

# Assignment-aware context dialog — F49

The existing styled AssessmentContextDialog now supports both the earlier
context-based selector and the historical AssignmentSelector. Matching selector
and catalog types are mandatory. In assignment mode, choices come directly from
selector.options; the legacy supplied option tuple cannot override saved ownership.
The host supplies the project shift list explicitly so empty shifts remain visible.

Acceptance prepares an AssignmentRequest using the exact assignment ID instead of
converting it back into worker/workplace identity. It performs no source save,
creation or activation. A stale job snapshot disables acceptance and asks the user
to reopen. Empty shifts disable acceptance. Legacy context mode remains supported
for older project formats; callers distinguish the returned request type.

The host must resolve pending widget text before preparing a selection. If source
edits occur after acceptance, the prepared request becomes stale and must be
prepared again. Dirty consent and select/create actions remain host responsibilities.
This component is not yet wired into the temporary harness or final main window.

Palette, typography, geometry, processed icons, tooltips and buttons are retained.
No icons were added. Native XCB screenshots at 700 x 540 were captured and visually
inspected for populated/selected, collapsed, empty, stale and expanded shift-popup
states. Labels, summary and bottom controls fit without visible clipping; the
complete dialog was inspected. There is no VTK region in this window. Evidence is
in artifacts/assignment-dialog and hashed in f49_validation.json; capture script
is archived in docs/reference/f49-capture.py.txt.

Three new real-Qt cases exercise saved assignment request handoff, empty/stale
states and invalid composition. All 458 tests pass; total coverage 98.97%, dialog
100%. Ruff/format, strict mypy (100 files), architecture and builds pass. The
extracted-wheel smoke accepts an assignment request and selects through its
presenter. All 500 original files and the dependency lock remain unchanged.

This advances the context-control step of worker/job migration. Host pending-text/
dirty-choice composition, current-version lifecycle and final integrated UI still
remain. No schema, dependency or scientific change occurred.
