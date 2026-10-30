> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in [Job Management](job_management.md), the
> [shared editor](shared_assessment_editor.md) and [current database inventory](database_tables.md).
> Removed APIs are not supported.

# Job risk evidence and lifecycle — F61

The existing JobWindow.saveJob, newProfileVersion, approveSelectedProfile,
makeSelectedProfileCurrent and retireSelectedProfile depend on job-level risk
profiles. These are separate from worker assessment version/status records.
The new domain/job_risk.py supplies immutable typed measurements, provenance,
profiles and a project-owned catalog for that workflow.

Measurements retain model identity, cumulative damage, probability_percent,
unit label and notes. None is missing; zero is valid. Partially complete records
are representable because the reference repository supports them, even though
the UI requires paired entries. Probability range is 0–100; negative, boolean
and nonfinite values are explicitly rejected at the new typed boundary. This
finite/type guard is a deliberate boundary strengthening, not a formula change
or silent cleanup of legacy data. Legacy reconciliation remains pending.

Profile evidence includes name, source category/reference, methodology, sample
size, assessment date text and notes. IDs and versions are explicit; measurements
are unique per model. Profile IDs, per-job versions and current profiles are
unique in a catalog. Like the reference schema, the catalog can represent
status/current combinations beyond normal lifecycle outputs; import must not
silently reinterpret existing data. Parent job membership is a future storage
validation obligation, not inferred from profile text.

Approve accepts only a draft with at least one complete model measurement, changes
it to approved/current and clears currentness only within the same job. Other
profile statuses remain unchanged. Make current requires approved status.
Retire accepts draft/approved records, clears their current flag and never picks
a fallback. Repeated retirement fails. All operations produce new snapshots
without changing evidence or unrelated jobs. Approval does not establish
scientific validity or completeness for every model required by JROT.

Ten reference scenarios execute the original approve/current/retire functions
extracted via AST under the original Python baseline, using in-memory SQLite.
The legacy derived-color/table synchronizer is replaced with a call recorder
during this narrow characterization. Thus the fixture establishes lifecycle
behavior, not numerical color correctness or legacy materialized-table parity.
The source SHA and capture script are retained. Existing science gates remain.

Ten added tests cover the reference scenarios, evidence retention, immutability,
numeric boundaries/partial data, duplicate identities, source/sample validation
and wrong-state transitions. All 520 tests pass; combined coverage 99.00% and
new module 100%. Ruff/format, strict mypy (106 source files), architecture, builds
and isolated-wheel lifecycle smoke pass. Original 500 files and dependency lock
remain unchanged. No UI, schema or scientific formula changed.
Evidence: f61_validation.json, reference/f61-capture.py.txt and f61-verify.py.txt.

Still pending: draft creation/copy/edit rules, transactional storage and job
membership/immutable-approved enforcement at that boundary, timestamps,
workspace/presenter integration, original Job Management controls and PLOT/JROT
consumers. Public frozen records alone do not prevent a caller constructing a
modified approved record; persistence must enforce that lifecycle restriction.
