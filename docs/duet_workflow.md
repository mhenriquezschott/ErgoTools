> Current owner-approved task-capacity and unused-row policy (2026-10-18)
> supersedes historical clear-on-count-change and unused-slot partial-status wording
> below. See current behavior.

# DUET source workflow and persistence — F16

## Source, edits and preparation

DuetDraft owns an ordered immutable tuple of DuetTask values with distinct stable IDs. AddDuetTask, ReplaceDuetTask and RemoveDuetTask are document-scoped commands using the existing generic DocumentSession history. They preserve task identity/order, reject stale snapshots and wrong-document operations, and leave history/clean markers untouched after failures or equal-state edits. Action labels have English/Spanish messages. Source drafts carry no measurement-system tag because DUET scale/repetitions require no metric conversion.

prepare_duet captures the source/session/revision and all field issues in row order. The scale check is now shared with calculate_duet_task, and repetitions use the tool-independent numeric validator. Empty drafts need a task; missing fields never become zero. Complete zero inputs remain present. The freshness contract mirrors LiFFT: edits invalidate, undo can restore the exact captured revision, new branches/reloads/other sessions cannot reuse a prior preparation merely because values match, and saving without editing preserves freshness. These checks are available APIs, not a wired live result cache. Callers pass the actual active session and release preparations when closing/switching so private origin references do not unnecessarily retain sessions.

## Versioned source storage

The JSON format is `ergotools.duet-draft`, version 1, with exact format/version/tasks fields. Each task contains task_id, omni_res_scale and repetitions. Missing values are null, scale is an integer or null, and repetitions retain finite numeric precision including signed/fractional values for correction. Out-of-range integer scales also remain editable source; preparation/calculation reject them. Booleans, fractional scale representations, nonfinite numbers, unknown fields/versions, duplicate members/IDs and malformed structures are rejected. In-memory tasks may temporarily hold invalid runtime values; not all invalid values are serializable. Derived results/colors/translations are never stored in this codec.

DuetSqliteStore uses the independent `ergotools.duet-drafts` database marker, version 1. It requires an explicitly initialized empty database and caller-owned idle default-mode SQLite connection. It addresses documents by project/document identity, validates serialization before writing, and verifies the format inside a BEGIN IMMEDIATE transaction. Failure rolls back; DocumentSession marks clean only after successful commit. Load validates the entire payload. Closing the connection remains the caller's responsibility.

LiFFT and DUET now share SqliteDraftStore's transaction/identity/version mechanics and draft_json's strict primitives. The LiFFT database marker (`ergotools.drafts`), JSON format and API imports remain compatible; DocumentFormatError and StoreFormatError remain available from their previous modules as the same exception classes. All previous persistence/project tests pass. The adapters reject the other model's database marker, and creation refuses any pre-existing schema. No implicit schema adoption or operational migration occurs.

These are separate typed draft stores, not a multi-assessment project format. The existing ProjectFile/ProjectWorkspace integration still uses LiFFT. DUET is not yet selectable through that manager. A deliberate combined format/version design and compatibility tests are required next; neither adapter silently repurposes an existing project. No multi-writer conflict policy or power-loss certification is claimed.

## Verification

Twelve new tests cover add/replace/remove with undo/redo, stale/wrong-scope/invalid-position/duplicate operations, immutable input snapshots, ordered issues, freshness, precise/missing/signed JSON round trips, corrupt schemas/payloads, real temporary-file close/reopen, missing document identity and translations. A real SQLite trigger rejects an update: the test proves rollback, retention of stored source, continued dirty status and successful retry after removing the trigger. Cross-tool open/create attempts are rejected without destroying the original schema.

All 184 tests pass on approved Python 3.13.14. Combined coverage is 99.44%; new modules are 100%. Ruff/format, strict mypy (53 files), architecture and source/wheel builds pass. Independent package/source/dependency results are in `f16_validation.json`. Original application files, environment and operational databases remain untouched.

## Remaining work

Next design and implement explicit multi-assessment project ownership/routing so LiFFT and DUET coexist safely, with format versioning and open/save/history tests. GUI integration, full model coordination, scientific review, LiFFT metric-moment review, legacy migration and native packaging remain pending. This milestone has no new UI or runtime dependency.
