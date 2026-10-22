# Explicit risk-capable projects — F64

AssessmentProjectFile.create_with_risk_profiles explicitly creates format seven.
It includes historical assessment ownership, hierarchy/jobs and the risk tables
introduced in F63. Existing creation factories still produce their original
formats; opening a file does not upgrade it, and default desktop New is unchanged.
Creation remains exclusive and cleans incomplete new files on failure.

Version-seven open validates risk metadata, typed records and job membership
before returning a usable handle. Historical assessment validation still runs,
and context-only binding APIs remain prohibited for historical formats.
Risk reads/mutations load jobs and validate their hierarchy on the same connection
inside the risk store transaction. Closed handles and unsupported formats reject
risk operations; supports_job_risk reports capability without database I/O.

The adapter exposes risk read, create/copy draft, edit, approve, select current and
retire methods. These delegate to the tested explicit transactional store APIs,
preserving expected-catalog conflict checks and approved-evidence protection.
Worker assessment sources/currentness and source units are independent of job
risk operations. No scientific conversion, formula or unit inference is introduced.

JobCatalogStore's change callback now composes assessment-history protection and
risk-profile parent-job protection within the job-write transaction. A job with
any draft, approved or retired profile cannot be removed through save_jobs or
replace_jobs. Rename/description/activity updates retain identity and remain
allowed. This is a protective restriction at the new adapter boundary; a future
explicit job deletion/archive workflow must resolve retained profiles deliberately,
rather than reproducing a cascade that could invalidate JROT provenance.
Direct SQL mutations are unsupported; subsequent validation detects damaged data.

Fifteen added cases cover complete project lifecycle/reopen, historical source
coexistence with differing project/source units, every profile status retaining
its job, display/activity edits, assessment-reference protection, old-format
non-upgrade, damaged metadata/orphan records/missing tables, competing project
handles, closed capability, exclusive creation and cleanup on schema failure.
All 550 tests pass; combined coverage 99.02%. Ruff/format, strict mypy (107 source
files), architecture, builds and an isolated-wheel version-seven lifecycle and
parent-job protection check pass. All 500 original files and dependency lock
remain unchanged. No UI changed. Evidence: f64_validation.json and
reference/f64-verify.py.txt.

Next: workspace-owned risk snapshot/operation ports and Job Management presenters,
then existing screen controls. No full risk-management UI, legacy import,
automatic format upgrade, risk timestamp/audit history, JROT frozen-reference
integration or complete job deletion policy is claimed by this slice.
