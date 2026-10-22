# Assessment catalog and creation — F18

## Persisted catalog

AssessmentEntry is an immutable application value containing DocumentKey, stable AssessmentKind (lifft/duet) and persisted task count. AssessmentProjectFile.list_assessments reads only its project's saved source documents, validates them and returns entries ordered by SQLite BINARY document-ID order. It does not save, mutate active history, calculate results or update recent-file settings. Counts describe saved source, not unsaved edits. One corrupt payload fails the catalog request rather than silently omitting an assessment or returning a partial list.

Catalog reads currently deserialize all source payloads to validate model identity/counts. This is deliberate for the small initial format, not an optimized large-project index. No assessment title, rename/delete UI, task preview or search index is implied. Model IDs are stable values independent of language.

## Exclusive insertion and workspace creation

The shared draft store now exposes insert in addition to save. Insert validates the incoming codec before starting BEGIN IMMEDIATE, then checks the existing row under the write lock and raises DocumentExistsError if its ID exists. It never replaces an existing same-model or other-model document. The existing model-identity hook and transaction rollback remain in force. Save retains its prior upsert behavior. There is no new schema or dependency version.

AssessmentProjectFile routes insert_assessment through the appropriate store and enforces project ownership/version rules. Version-one files can list and insert LiFFT only, without upgrade. Version-two files accept both supported models. Existing legacy ProjectFile instances do not expose the catalog capability; callers use AssessmentProjectFile to opt into version-aware catalog access.

ProjectWorkspace detects the optional CatalogProject capability. list_assessments returns an empty tuple when no project is active, rejects unsupported adapters explicitly, and otherwise guards the synchronous read. create_assessment requires an active capable project and a valid document ID. Dirty Cancel or no decision returns without catalog/write I/O. A duplicate-ID preflight happens before any requested old save. Then an explicitly requested old save completes, exclusive insertion commits, and a clean new DocumentSession becomes active. Creation is not an undo command, does not close/reopen the project, and does not change recent-file settings.

If the old save fails, no new document is inserted. If insertion fails after an old save succeeds, the same old session remains active and may now be clean. Discard abandons the old unsaved history only after successful creation; failures retain it. Preflight is not the uniqueness guarantee: the transactional insert check still rejects an ID appearing after preflight. No implicit overwrite, project migration or retry is performed. Source codec validation happens at insertion, so an invalid requested source can fail after an authorized old save; that ordering is intentional and matches project creation semantics.

These are owner-thread synchronous adapter contracts. Catalog and insert implementations must not mutate the active session as a side effect. The workspace guards its own reentrant operations; asynchronous jobs and arbitrary callback-driven session mutation remain outside this contract.

## Evidence and remaining scope

Ten new tests cover stable persisted catalogs versus unsaved task counts, immutable entries, no-I/O cancellation, save/create/reopen, discard, duplicate preflight and transactional rejection, real SQLite insertion failure after old save, old-save failure, version-one compatibility, corrupt payloads, closed/no-project state and unsupported adapters. Resource ownership uses explicit connection close scopes.

205 tests pass on approved Python 3.13.14. Combined coverage is 99.48%; catalog/domain identity additions and modified workspace/store operations are fully covered. The mixed-project adapter retains one unexercised defensive connection-failure branch from F17. Ruff/format, strict mypy (59 files), architecture and source/wheel builds pass. Independent package/reference/dependency evidence: f18_validation.json. All original files and dependency versions remain unchanged.

Next reconcile model-specific preparation with mixed sessions and bind derived results to exact source/revision identities. GUI/model integration, TST and remaining models, scientific validation, LiFFT metric review, legacy migration, version-one upgrades and native packaging are pending. There is no runnable replacement desktop app yet.
