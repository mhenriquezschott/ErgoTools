> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in [Job Management](job_management.md), the
> [shared editor](shared_assessment_editor.md) and [current database inventory](database_tables.md).
> Removed APIs are not supported.

# Transactional risk-profile storage — F63

JobRiskStore borrows one owner-thread SQLite connection and a job-loader callback.
The loader must read the parent JobCatalog on the same connection without owning
transactions. Reads use one snapshot transaction. Every mutation uses BEGIN
IMMEDIATE, reads jobs/profiles, compares the expected catalog, applies an explicit
domain operation, writes changed records and validates the saved result before
commit. Failure rolls back the complete operation.

Public operations are create_draft, edit_draft, approve, make_current and retire.
There is no public unrestricted catalog replacement. Draft evidence checks and
lifecycle rules therefore execute again under the write lock. Stale or foreign
expected catalogs fail. Approval clears old currentness before setting the new
flag, within one transaction and a partial unique index. Evidence records are
rewritten only when measurements change; currentness changes preserve them.
Post-write rereading rejects trigger-induced divergence before commit.

The isolated risk schema has a project/version marker, ordered profile rows and
ordered per-profile measurements. SQL constraints enforce profile IDs, job/version
uniqueness, one current profile per job and one measurement per model. Typed reads
add provenance/numeric/status validation and reject orphan measurements or missing
parent jobs. Creation requires an explicit caller transaction; nested store calls
are rejected without committing the caller's work. Connections remain caller-owned.

This is a new schema component, not an upgrade to AssessmentProjectFile. Existing
project formats 1–6 and default creation remain unchanged. No operational project
was opened or modified. RiskStore tests create dedicated synthetic SQLite files.
Integration must add an explicit new project-format factory and ensure job changes
cannot remove referenced jobs; the standalone store cannot police arbitrary SQL
or separate job edits. Project open validation, metadata timestamps, workspace
ports and UI wiring remain pending. Legacy JobMeasurement/color synchronization
is not implemented and no scientific formula changed.

Ten added cases cover full lifecycle save/reopen, copied source units/evidence,
approved edit rejection, competing connections, foreign expected snapshots,
failures after current demotion/evidence deletion/new-profile insertion, invalid
metadata/orphan data/missing jobs/enums, nested transaction rejection and trigger
mutation detection. All 535 tests pass; combined coverage 99.03%, new store 100%.
Ruff/format, strict mypy (107 source files), architecture and builds pass.
An isolated-wheel lifecycle/reopen smoke also verifies approved edit protection.
All 500 original files and dependency lock remain unchanged; no UI changed.
See f63_validation.json and reference/f63-verify.py.txt.

Next: explicit project-format integration with reference protection, then
workspace/presenter and original Job Management screen wiring. Overall estimate
is approximately 67%, a qualitative scope estimate reflecting accumulated
management UI/domain/storage progress, not a measured code fraction or schedule.
