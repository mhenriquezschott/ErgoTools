# Assignment dialog host flow — F50

AssignmentDialogHost composes pending-text resolution, saved hierarchy/job views,
the existing styled modal context dialog and assignment-aware workspace selection.
This is reusable desktop orchestration for the documented worker/job workflow,
not a new main-window action.

The owning editor injects resolve_pending and choose_dirty callbacks. Pending
resolution must explicitly apply or discard text and return True, or cancel with
False. False performs no catalog I/O. Applied text remains an edit even if the
later dialog is cancelled. The host then reads project shifts, refreshes job
options and executes the modal dialog.

Rejected dialogs return an incomplete transition. Acceptance must supply an
AssignmentRequest, and the hierarchy snapshot must still be current. If the active
source is dirty, the injected callback supplies Save/Discard/Cancel; the presenter
rechecks job/request/source freshness before selection. Missing current assessment
ownership raises KeyError rather than creating anything automatically.

Reentrant host calls are rejected. Dialogs close and receive deleteLater on all
exits, including failures; the busy guard resets for retry. Exceptions propagate
to the owning window's error display. Successful callers must rebind/render the
new active source. This component does not implement new message-box styling,
creation controls, current-version transitions or main-window composition.

Three new Qt integration cases cover pending cancellation without reads, clean
selection, modal cancellation, dirty Cancel/Save, invalid modal results, recovery,
reentrancy and hierarchy invalidation. Native XCB capture executes the real modal
loop and records selected, collapsed, empty, stale and shift-popup states at
700 x 540. All were visually inspected without visible clipping and match F49
image hashes. The existing palette/assets/layout are retained; no VTK is in this
window and no new icons are needed.

All 461 tests pass, total coverage 98.98%, new host module 100%. Ruff/format, strict
mypy (101 files), architecture and builds pass. An extracted-wheel smoke uses a
real modal event loop to select the successor assessment. All 500 original files
and the dependency lock are unchanged; see f50_validation.json. No schema,
dependency or scientific change occurred.

The main window still needs to supply concrete editor callbacks and invoke this
host. The standalone LiFFT harness remains temporary; full integrated parity is
not implied by this reusable coordinator.
