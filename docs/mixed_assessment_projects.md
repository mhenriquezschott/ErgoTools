# Mixed-assessment projects — F17

## Explicit formats and compatibility

AssessmentProjectFile creates project metadata format ergotools.project version 2 with draft-store marker ergotools.assessment-drafts version 1. Its existing draft_documents table addresses project/document IDs; payloads are tagged ergotools.assessment-document envelopes, version 1, whose kind is lifft or duet and whose source is the unchanged model-specific version-one draft format. Unknown kinds, versions, fields and mismatched inner/outer formats are rejected. Neither task results nor presentation state is persisted.

The adapter also opens existing modernization version-one LiFFT projects through LifftSqliteStore. Their format, metadata and payloads remain unchanged; attempted DUET writes fail explicitly. Read plus a rejected DUET save was verified byte-for-byte unchanged. LiFFT writes remain compatible with the original ProjectFile API. There is no implicit upgrade, Save As or original application's legacy .ergprj migration. Standalone DUET draft databases are not project files. The older ProjectFile reader rejects version-two mixed files.

Creation remains exclusive and removes only its own incomplete new file after initialization failure. Open uses mode=rw and never creates missing files. Metadata and document project identities are checked; unknown versions and foreign rows are rejected. Connection ownership, close/context behavior and cleanup guarantees follow the established project adapter. Failed connection acquisition has a defensive cleanup branch not reached by this test slice; no blanket 100% coverage claim applies to the new project adapter.

## Transactional model identity

AssessmentSqliteStore validates the incoming source before a write transaction. Within BEGIN IMMEDIATE it verifies storage metadata, reads any prior payload, validates that payload and requires the same source type before upserting. A DUET draft cannot overwrite a LiFFT document ID or vice versa. Corrupt stored payloads also block replacement because their model identity cannot be established. Rejection rolls back and retains existing documents; a subsequent valid save succeeds.

The shared SqliteDraftStore now offers this transactional replacement hook. Existing single-model stores retain their behavior through a no-op hook. This does not add general concurrent-edit version conflicts: single-writer/owner-thread usage remains the contract. New model IDs are persisted through the repository API; a user-facing assessment catalog/add workflow remains next work.

## Workspace and edits

OwnedProject and ProjectWorkspace are now generic over the source state, preserving the existing transition implementation. An AssessmentDraft type alias explicitly lists LiFFT and DUET. LifftProjectEdit and DuetProjectEdit adapt existing model commands into a mixed session, preserve document scope/history labels, and reject the wrong source type before applying changes. Per-tool task commands remain authoritative for their task validation.

Same-file/same-document switching preserves the active session/history. Switching to a different document requires the existing dirty Save/Discard/Cancel decision; target validation precedes the current save. Each activated document starts a newly loaded session, so histories are not cached across document switches. Edits/undo/redo work within the active session; explicit Save commits only that source. The tests exercise both models and reopening the file. This is backend coordination, not a runnable GUI. Per-model preparation APIs are still typed to their own sessions; a mixed-session result/preparation presenter remains to be designed rather than using unsafe casts.

## Evidence

Eleven new tests cover both models in a real file, guarded cross-model replacement, byte-preserved version-one reads/rejected writes, version-one LiFFT write compatibility, mixed workspace save/switch/cancel/history, wrong-model commands, failed target loading, corrupt source overwrite rejection, strict tagged envelopes, exclusive/missing/foreign path protection, unknown metadata and initialization/first-save cleanup. All earlier regressions pass. Test-owned raw SQLite connections are explicitly closed as well as transaction-scoped; resource warnings remain failures.

195 tests pass. Combined coverage is 99.45%; the new project adapter is 99% (one defensive cleanup branch unexercised), and other new modules are 100%. Ruff/format, strict mypy across 58 files, architecture and builds pass. Independent mixed-workspace package and unchanged-source/lock results are in f17_validation.json. No dependency or UI changes occurred; original application files and operational databases remain untouched.

## Next work

Add an explicit assessment catalog and create-assessment operation within an already open version-two project, preserving dirty decisions and existing IDs. Then reconcile mixed-session preparation/result freshness. Version-one upgrades, Save As, TST, GUI/VTK integration, scientific review, LiFFT metric review and legacy migration remain pending. There is no runnable replacement desktop app yet.
