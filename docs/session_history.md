# F3 — document session, history and save coordination

Completed 2026-09-27 with the existing approved environment. No library or Python version changed. This implements a usable in-memory application core and storage contract; it does not implement project-file persistence or a UI.

## Ownership and contracts

`application/session.py` owns a `DocumentSession[State]` for exactly one immutable `DocumentKey(project_id, document_id)`. These identifiers are not file paths or translated names. Blank identities are rejected. Separate documents/projects use separate session instances, without global active-document state. A future project-session coordinator owns selection, routing, close decisions and pending tasks.

State must be a deeply immutable value (for example frozen dataclasses with tuples). This generic contract cannot enforce deep immutability at runtime; mutable widgets, lists, dictionaries, arrays and ORM entities must not be used as snapshots. The test Draft is a fixture, not a production assessment schema. Domain schemas and concrete edit commands arrive with the first assessment use case.

An `EditCommand` identifies its document and stable action-label key, validates and returns a replacement snapshot through a pure `apply` method. It must not mutate its input, perform I/O or create external side effects. A wrong owner, blank label, failed validation or equal-state result leaves history unchanged. No-ops preserve redo. Command exceptions propagate to the future use-case/UI boundary; the session remains available for retry.

Undo/redo restores retained immutable source snapshots rather than executing callbacks. This avoids an undo callback partially changing state or causing external effects. It combines commands for edit validation with snapshot history for reversal. Each new edit has a unique, increasing session-local revision ID; these numbers are neither project format versions nor durable database revisions. Editing after undo discards redo without reusing revision IDs. Undo/redo labels expose localization keys or None when the action is unavailable.

The accepted plan proposes minimal before/after command data. This first core retains whole immutable snapshots instead; unchanged nested values can be shared, but memory limits and compact deltas are deliberately unresolved. Before migrating large PLOT/JROT documents, measure retention and add a tested policy rather than retaining unbounded large snapshots. Coalesced drags/grouped edits, focus-aware shortcuts, calculated-result invalidation and action-label catalogs are also pending.

## Clean state and persistence boundary

New sessions default to unsaved/dirty. Successfully loaded snapshots must be constructed with persisted=True. The clean marker tracks the last persisted revision, not content equality: an independent edit that happens to reproduce old content remains dirty; a true no-op creates no revision.

`DocumentStore.save(document, state)` must atomically persist the supplied snapshot or raise while preserving previously persisted data. That is an adapter requirement, not proof of disk atomicity. `DocumentSession.save` marks clean only after the adapter returns successfully. Save is not an undo entry. Undo after save makes the draft dirty; redo to the saved revision makes it clean again. A lost saved branch stays dirty until another successful save. Failed saves preserve both history and clean marker, and can be retried.

The model is synchronous and single-owner-thread. Mutating operations cannot reenter an edit/save callback; reads remain possible. It is not thread-safe and does not support background save acknowledgements or concurrent writers. Future background adapters need captured revision/identity tokens and stale-result handling; do not weaken the guard to add concurrency.

## Scope and reference boundary

The reference main.py saveFile entry point calls saveToolsData for an existing project and otherwise opens project dialogs. Those GUI/database workflows have not been copied or executed. F3 is tested against the accepted architecture's new history semantics, not represented as reference equivalence for undo behavior.

There is no Save As, dirty-close dialog, file opening, recent-files service, settings adapter, transaction implementation, schema migration, auto-save or disk write in this slice. In particular the plan's Save As policy decision is still pending before the project-file slice. No UI changed, so no visual acceptance is claimed or required here. No operational database was opened.

## Verification

Twelve new workflow tests cover new/loaded state, edit/save/undo/redo, undo to the loaded revision, a discarded saved branch, no-ops and failed commands after undo, failed save and retry, empty history, both dimensions of ownership, independent sessions, invalid IDs/labels and reentrant edit/save failures. All 43 project tests pass; overall combined statement/branch coverage is 98.07%, session.py is 100%. Ruff, formatting, strict mypy (18 source/tool files), architecture rules and builds pass. In-memory adapter tests exercise the contract but do not prove real storage atomicity. `f3_validation.json` records independent wheel and reference-integrity checks.

## Next slice

Define the first immutable assessment draft and concrete commands, including structured validation and stable error codes. Use it to guide persistence/project-lifecycle contracts and a transaction-capable adapter, then settings/recent files. Resolve metric-moment scientific review before assessment formula integration. Propose exact GUI/scientific/VTK dependency versions before installation. Connect shortcuts and dialogs only when their UI slice can be visually verified.

## M06 implemented PLOT specialization

The initial pending notes above are historical. PLOT now uses the same history
engine for coalesced released gestures, accepted settings/batches and Cancel,
with native typing routing and complete EN/ES action labels. Partial selected
saves require a persisted-source baseline for PLOT's dirty guard; a full snapshot
Save retains DocumentSession's clean revision. Position-only immutable snapshots
share unchanged records and release with the modal document; a 1,000-edit,
100-worker comprehensive-copy measurement retained about 1.11 MB. This is not a
universal memory bound. [PLOT history](plot_history.md) documents the implemented
retention/ownership policy and focused/full/native acceptance evidence.
