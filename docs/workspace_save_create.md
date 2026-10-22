# F10 — explicit Save/New and cleanup diagnostics

Completed 2026-09-28 without dependency or UI changes. ProjectWorkspace now exposes save() and create(...); ProjectFile.create_with_document initializes the first source draft before returning ownership.

## Explicit Save

save() returns False when no document is active. Otherwise it uses the current owned repository and the existing session save contract: commit before marking clean, preserve history/identity, propagate failure, release the busy guard and allow retry. It does not change recent history or create a new destination. Undo after a successful save is dirty; redo to the saved revision is clean.

## New project ordering

The workspace accepts an optional injected creator with `(location, metadata, document_id, initial)` arguments. Without a creator, New fails explicitly. Unknown/blank location and document identity are rejected; an exact active location is rejected before any save. Dirty New requires an explicit Save or Discard choice; Cancel/missing consent does no I/O.

If Save is chosen, saving the current project finishes before the new file is created. Consequently a later creation failure leaves the same session active but may leave it clean, because the requested save actually succeeded. This intentional ordering avoids a new orphan project when saving the old draft fails. Discard is not applied until successful new activation.

The concrete initializer validates the key and serialized initial draft before creating anything. Exclusive creation rejects all existing destinations. It creates the project metadata, saves the first draft and returns the owned handle only after persistence succeeds. Initial-document write failures close the handle and remove the newly created incomplete file; retry can then use the destination. Filesystem close/unlink failures can interrupt this cleanup and propagate; crash/power-loss recovery and cleanup under simultaneous filesystem failures are not certified. Parent directories remain caller-owned.

The workspace checks creator metadata, reloads/verifies the initial snapshot, and ensures the prior session has not changed during creation before activating a new clean session. A returned candidate rejected by these postconditions is closed, but its completed file is not deleted automatically: preserve potentially valid user data and let the caller report/review it. Such a case differs from an incomplete initialization failure inside the creator. Current project ownership remains unchanged. Successful activation releases the old handle and updates recent history; cleanup/settings failures remain separate warnings.

New is not Save As: it takes explicit new project metadata and initial source data, does not copy an existing project, and never overwrites an existing destination. Save As still requires the separate policy decision from the accepted plan.

## Diagnostic retention

Pending resource releases now retain a frozen ReleaseDiagnostic with operation=`project.close`, the fully qualified exception type and errno when supplied by an OSError. Raw exception text, tracebacks and document contents are not retained in these records. The read-only release_diagnostics tuple reflects pending failures; successful retry removes the entry and failed retry replaces it with the latest technical context. Full logging, user-facing recovery UI and an operation-ID scheme are still pending. This supersedes F9's limitation that only warning keys/counts were available; other ownership/concurrency limits remain.

## Evidence and next work

Thirteen new tests cover complete New persistence, explicit Save/history, save failure/retry, dirty cancellation, old-save failure before creation, current-state retention after creation failure, initial-write cleanup/retry, existing/active destination protection, pre-file input validation, adapter postcondition rejection, edits during initialization, cleanup exception/errno privacy and settings warnings. All 133 tests pass; combined statement/branch coverage 99.38%, modified production modules 100%. Ruff/format, strict mypy (31 source/tool files), architecture and package builds pass. f10_validation.json records isolated package/source/lock verification.

The next useful slice is reference characterization of the actual LiFFT calculation and typed result/input-validation contracts. Keep valid-input parity separate from any proposed scientific corrections; the metric-moment expression remains an explicit review issue before workflow integration. This foundation still lacks full project context mapping, GUI adapters and native visual acceptance; it is not a complete replacement application.
