# F8 — new-project metadata, connection ownership and open outcomes

Completed 2026-09-28 without dependency changes. This creates a deliberate new-format project container around the F5 draft store, not legacy .ergprj compatibility.

## Metadata and ownership

`domain/project.py` defines immutable ProjectMetadata with project_id, title and default_units. Identity is explicit and independent of path/title. Defaults apply to future assessments only; persisted draft units remain authoritative. Metadata edits, timestamps, scientific model provenance and assignment/context mappings are not implemented yet. The format version does not imply a scientific model version.

`infrastructure/project_file.py` owns a dedicated SQLite connection. Use ProjectFile.create/open and a context manager or explicit close. Load/save operations enforce the one-project identity before reaching the draft adapter. Close is idempotent and closed handles reject I/O; it never implicitly saves drafts. Resolve dirty consent through DocumentLifecycle before releasing the project handle. Metadata remains readable as an immutable snapshot after close.

Creation requires a nonexistent file via exclusive creation; existing files are never overwritten or adopted. Parent-directory selection/creation belongs to the caller. Draft schema initialization and metadata insertion complete before a handle is returned. Setup failures close the connection and remove the newly created incomplete file; broad exception handling here exists only to release resources before re-raising. This does not promise crash-atomic publication: an interrupted process can leave an incomplete file that must be diagnosed explicitly, not silently adopted. Concurrent modification of the destination path during creation is unsupported.

Opening uses an encoded SQLite file URI with mode=rw, so a missing path is not silently created; names with Unicode, spaces, # and ? are tested. The draft format, one metadata record, project marker/version and absence of foreign project IDs are validated. Unknown/corrupt containers are rejected without migration. This is a single-writer owner-thread adapter: external metadata mutation, multi-process contention, hot-journal recovery and native crash durability are not acceptance claims. Direct constructor use transfers cleanup responsibility to its caller; the factories handle failed adoption automatically.

## Container format

The project_metadata table holds format=`ergotools.project`, version=1, project_id, title and default_units. The embedded draft_metadata/draft_documents tables retain their F5 format/version unchanged. A plain F5 draft database is not automatically upgraded into a project; the new factory requires explicit project metadata at creation. Existing record serializers and numeric behavior are unchanged. No legacy database or operational project was opened or migrated.

## Recent-history integration

`application/open_document.py` combines the existing lifecycle with SettingsStore. It validates a supplied normalized location, opens/selects the requested document, and only then loads/updates/saves recent history. Cancellation performs no settings I/O. Document errors propagate and do not write recency. Settings I/O/format errors instead return OpenOutcome(opened=True, warning_key="settings.recent_update_failed"); English/Spanish catalogs contain that warning. It must be presented as a settings warning, not as document-open failure. Programmer errors outside expected I/O/validation exceptions still propagate.

The caller must associate the location with the repository and select the document identity correctly. The wrapper does not derive identities from file names, instantiate project handles, switch repository connections, retry settings writes automatically or delete missing-file entries. Selecting the already-open identity follows F6 semantics and may refresh its recency without replacing history.

## Validation and next work

Twelve new tests cover create/save/close/reopen, preserved project and record units, exclusive creation, missing-file open, owner mismatch, closed handles, context cleanup, initialization/connection failures and retry, future versions, foreign records, metadata validation, real project+settings integration, separate settings warning, cancel and failed open. All 106 tests pass, total combined statement/branch coverage 99.21%, three new production modules 100%. Ruff/format, strict mypy (30 source/tool files), architecture and builds pass. `f8_validation.json` records isolated package/source/lock checks.

Next: project-switch orchestration that prepares a candidate connection/document before releasing the current project and preserves the old project on failure/cancel. Then implement explicit project creation/selection use cases and UI-facing diagnostic results. Save As policy is still pending confirmation before that workflow, and no Save As behavior has been added. GUI version approval and the metric-moment scientific review gate remain open. No visual interface changed.
