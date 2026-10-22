# Repeated task Undo and Open project folder — 2026-10-18

Current granularity contract: the owner subsequently requires one completed task cell
per history step. See [task-cell history acceptance](task_cell_history_acceptance.md).
The checkpoint evidence below remains historical; availability/rebind fixes are reused.


The owner reports a second edit/Undo of Ana's Task 2 leaving the newly typed value
visible while Undo becomes exhausted. The owner also requests an independently owned
system file-manager window through the Project menu. These are bounded owner-directed
Linux corrections/additions, not new milestones; migration and cleanup remain 100%.

## Reproduction and correction

The added repeated-edit regression fails on the previous implementation: source and
matching result have already been restored, but the actual replacement input widget
still contains `50` instead of its baseline value. Shared history UI refresh previously
remembered only the destination revision. A new edit after Undo forms a fresh branch;
Undo can return to that same destination again, incorrectly suppressing the UI rebind.

The existing adapter now identifies each refresh by **operation and destination**.
Returning to the same destination from a different operation refreshes the window;
reentrant refreshes within one replay remain suppressed. Source persistence, history
chronology, pending parsing, calculations and native typing are unchanged. No second
history stack or automatic calculation/Save is added.

Seventy-two regressions cover all nine input widgets (LiFFT arm/load/repetitions,
DUET rating/repetitions, ST direction/arm/load/repetitions), Task 1 populated and Task 2
initially empty, both languages and both unit systems. Each starts from a saved/reopened
fifteen-row assessment, performs five fresh edit/Undo branches with identical then
different values, and interleaves Redo/Undo. Assertions inspect actual recreated widgets,
exact source/result state, history boundaries and unchanged durable files. This includes
360 fresh branch reversals and 216 intervening Redo/Undo pairs. Prior single-edit,
invalid-input, resizing and persistence checks remain intact.

## Project folder action

**Project > Open project folder** / **Proyecto > Abrir carpeta del proyecto** appears
beside Properties, reusing the processed open icon. It is enabled when a saved project
is loaded, including an empty project, and disabled after Close or before the first
Save of a new/converted unsaved project. Direct host calls enforce the same guards.
It delegates the absolute parent directory through Qt's QDesktopServices/local-file URL,
which safely encodes spaces, accents and URL-special characters. The OS owns the file
manager; ErgoTools adds no embedded browser, owned child dialog or dependent process.
Opening the folder accepts no pending task text, changes no selection/history and
performs no Save. A rejected desktop-service request shows a localized warning.

Six new cases verify EN/ES captions, loaded/closed/unsaved enablement, Unicode/space/hash
paths, accepted/rejected service responses, localized errors and unchanged invalid
pending text/source/history/file. Mocked URL tests characterize the application boundary;
they do not establish actual OS-window lifetime.

## Native UI and independent OS verification

Twenty-six XCB/Xvfb :110 captures cover second-edit pending/Undo/Redo states for all
three tools in EN/ES, loaded/closed/unsaved Project menus and both launch-error messages.
All were inspected, including VTK, task rows, gauges, result cards and bottom controls.
The changed controls/menu/error text fit at the captured native size. One additional
system screenshot shows Nautilus at the requested directory after the ErgoTools test
process exited, proving independent lifetime. Its private QA project is removed after
inspection; no parallel maintained test project is retained.

The real OS check required a private D-Bus session with its display set before service
activation and without inherited VS Code Snap/GIO/GTK overrides. Initial inherited-Snap
portal activation failed; early checks also observed only service startup. The final
bounded wait observed the correct Nautilus directory after the ErgoTools process exited.
The private desktop emitted portal/secret-service startup delays and a gio timeout before
the window appeared; this is recorded, not claimed as normal-desktop responsiveness.
No launcher/environment/system repair is included. Windows/macOS remain deferred.

## Checkpoint evidence and next step

Required native gate: **1,539 tests pass, zero failures/skips, 94.32% combined
coverage**. Ruff/format, strict types (265), architecture/naming, documentation/review
and builds pass. The independent extracted wheel passes **175 focused
tests**; all 243 package Python files and both guides equal reviewed source. Logs and
package hashes are recorded in artifacts/repeated_task_undo_review. Explicit substantive review covers all five
changed maintained files; 428 files / 2,961 functions / 412 classes / 312 constants,
zero pending reviews or structural gaps. The owner workflow project,
both maintained native fixtures, scientific/application/storage code, reference checkout
and dependency lock are unchanged. Temporary projects/copies are used for all tests.

Restart ErgoTools and retry Ana's repeated Task 2 `50` → Undo sequence, including new
branches and Redo. The displayed inputs and matching result should restore on every
reversal. Try Project > Open project folder and leave its window open while closing
ErgoTools. Continue the existing owner workflow testing; no extra milestone is active.
