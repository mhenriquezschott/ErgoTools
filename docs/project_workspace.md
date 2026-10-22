# F9 — owned project switching

Completed 2026-09-28. `application/project_workspace.py` manages one active new-format project and LiFFT document using an OwnedProject protocol and an injected opener. Application code imports no SQLite or filesystem adapter. No dependency changes or GUI changes occurred.

## Transition policy

The platform caller supplies normalized location strings and an opener returning a fresh exclusively owned project handle. Do not return the current handle for another location or alias the same writable file through different paths. The caller must normalize aliases/case/symlinks appropriately before this boundary. ProjectWorkspace owns returned handles and active sessions; external code must not close those handles.

A switch validates nonblank location/document identity and an explicit CloseChoice. Cancel and a dirty draft without consent acquire no candidate and perform no I/O. A same-file/same-document request retains the active session and unsaved history. Same-file document changes reuse the connection. Different-file switches acquire and validate a candidate project and load its requested document before saving the old draft. Candidate/open/load failures leave the old session active; acquired candidates are released. Save failure also releases the candidate while preserving the old dirty draft/history. Revision/dirty-marker changes during candidate loading reject stale transitions. The owner-thread busy guard rejects recursive workspace transitions.

After target validation and requested save succeed, the candidate session becomes active and clean. Old-handle cleanup and recent-history updates then run as separate post-activation work. Their warning keys are returned together in TransitionOutcome, so a completed switch is not misreported as an open failure. The common recency helper is reused by the F8 single-repository open wrapper. The owner must route subsequent edits to workspace.active, not retain an old editor target.

Close uses the same dirty-choice/save ordering, then detaches the active state and releases its connection. It does not save automatically, create a project, perform Save As or decide a new identity. A workspace-level explicit save action and project-creation workflow are still pending; current saves happen through the tested transitions or document-session layer.

## Resource cleanup failures

Close can fail after activation or detachment. Such handles remain owned in a pending-release list, exposed through pending_release_count. retry_releases retries only detached handles and reports how many remain. A failed candidate cleanup does not mask the original load/save error; callers can inspect pending_release_count after an exception. Successful activation/close carries project.cleanup_failed if release fails. English/Spanish catalogs contain the warning.

The broad Exception catch is restricted to the resource-cleanup boundary: it retains the handle and reports/retries failure, rather than discarding ownership or reversing a committed transition. Detailed exception diagnostics are not yet retained in a logging subsystem; that remains a limitation. BaseException process-control signals are not swallowed by the cleanup handler. This policy is synchronous and single-threaded, not certified asynchronous cancellation, multi-writer synchronization or crash recovery. The process must not exit assuming all resources are released while pending_release_count is nonzero.

## Verification and next work

Fourteen new tests cover consent/cancel/no I/O, save/discard switching, opener/load/save failures and candidate release, retry, same-file reuse, post-activation cleanup/settings warnings, pending cleanup after a failed load, close/save failure recovery, recursive callbacks, edits during candidate load and a real two-file SQLite integration with settings persistence. All 120 project tests pass; combined statement/branch coverage 99.32%, new workspace module 100%. Ruff/format, strict mypy (31 source/tool files), architecture and builds pass. Isolated package/reference/lock checks are recorded in f9_validation.json.

Next: explicit workspace save and new-project/initial-document creation use cases, with initialization failure cleanup and UI-facing diagnostics. Avoid treating this connection coordinator as a finished desktop workflow. Save As policy is still pending confirmation before implementation. Metric-moment scientific review, GUI/library version approval, legacy identity mapping and visual acceptance remain outstanding gates for their relevant slices.
