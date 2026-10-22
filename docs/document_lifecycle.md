# F6 — document open/close coordination

Completed 2026-09-28. `application/document_lifecycle.py` coordinates one active DocumentSession using an application-owned read/write protocol; SQLite remains outside application imports. No dependencies or GUI changed.

## Decisions

- `DocumentRepository` extends the save port with load of a complete validated immutable snapshot. The F5 SQLite adapter satisfies it structurally.
- The coordinator adopts an optional new or loaded initial session without I/O. It owns the active reference, not a database connection or a global current window.
- CloseChoice has stable SAVE, DISCARD and CANCEL identities. Cancel always returns False with no I/O. Dirty transitions without an explicit choice also return False; this requests a decision from the caller rather than guessing discard. Clean/empty transitions require no dirty decision.
- Opening the already-active identity returns success while retaining the exact session/history and performing no I/O. This is selection, not reload; explicit reload remains future work. Cancel still cancels that request.
- Opening another identity first loads/validates the target, then saves the current dirty draft if requested, and finally changes the active reference. A failed load performs no save/discard. A failed requested save retains the old active session/history and dirty marker. The candidate is never installed partially.
- Discard only releases the old active reference after a successful transition; it neither deletes persisted data nor writes the unsaved draft. Close with Save commits before release. A repeated close on an empty coordinator succeeds without I/O.
- New loaded sessions start clean with empty history. History is session-local and is not stored/reconstituted by document loading.
- A busy guard rejects recursive lifecycle operations during storage callbacks. A changed revision/dirty marker during target loading aborts the switch, retaining the latest current draft. This is a synchronous owner-thread guard, not asynchronous or multi-thread synchronization.

## Caller responsibilities and limitations

A future presenter must show Save/Discard/Cancel when a dirty transition lacks a decision, bind that decision to the current identity/revision, and prevent stale modal replies from discarding newer edits. This API has no dialogs or asynchronous decision tokens. UI focus, keyboard shortcuts and dialog translations remain pending. Returning False does not itself show a dialog.

Route actions only to the coordinator's active session. Discard/close detaches a reference; it does not invalidate other Python references that callers may have retained. Repository connections remain caller-owned and open until explicitly closed. This slice is a single-document coordinator, not a workspace with many open tabs, project-file connection swapping, background tasks, project metadata, recent files, Save As or legacy format migration. One repository instance must correctly route its project/document keys. Save As policy is still pending before that workflow.

## Verification

Twelve new tests cover missing consent/cancel with no I/O, save/discard switches, load-before-save ordering, load/save failure retention and retry, discard close, clean/empty transitions, same-identity selection, unknown choices, recursive lifecycle callbacks, direct edits during load and real SQLite save/close/reopen. All 82 tests passed; overall combined statement/branch coverage 98.96%, the new module 100%. Ruff/format, strict mypy (25 source/tool files), architecture and builds passed. `f6_validation.json` records independent package and unchanged reference/lock checks.

No UI or scientific formula changed. Next: project metadata and settings/recent-document behavior through explicit contracts, keeping listing separate from file opening or migration. Before Save As, confirm whether only the new destination is written (the plan's proposal). The metric-moment review and GUI dependency approvals remain gates for their respective slices.
