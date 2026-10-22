# Legacy typed catalog compatibility — F129

Original workers, organization, jobs, placements, assignments and every job-risk
profile version now map to existing immutable domain models. The comprehensive
copy validates all 28 workers, 12 jobs, 38 placements, 104 assignments, 19 profiles
and 56 measurements without source writes. Next: historical assessments/tasks and
cached evidence. Destination conversion and integrated legacy UI acceptance remain.

Source mapping: schema_migrations.py version-eight Worker, Plant/Section/Line/
Station/Shift, WorkplaceContext, Job/JobPlacement/WorkerAssignment and
JobRiskProfile/JobRiskMeasurement. Reference worker fields store height in cm and
weight in kg; display-unit preferences do not change their persisted meaning.
Split calendar fields become exact ISO dates; partially missing dates fail rather
than acquiring guessed values. Worker names/metadata preserve None and empty text.
Source state/zipcode map to established region/postal_code fields. Organization
attributes use the established typed field registry, with exact ancestry.

Job placements and worker assignments retain their numeric IDs, active/closed
flags, optional placement, notes and date boundaries. Profiles retain exact IDs,
versions, lifecycle/current flags, provenance, sample sizes, notes and recorded
unit strings. Missing and zero damage/probability remain different. Existing
hierarchy/job/risk validation checks all cross-catalog links and ambiguous current
versions; readers never reassign workers, promote profiles or normalize statuses.
Strict SQLite primitive parsing rejects malformed numeric/flag/tool storage.

The source has extra unused worker anthropometry and organization visual fields.
They remain available in the immutable raw read snapshot and are outside this
existing domain projection; this is not a complete exporter and does not discard
or rewrite those source fields. Map assets/positions, rotations and historical
sources still need their reviewed conversion path before full legacy import.

Focused tests use a frozen source-shaped version-eight DDL fixture containing no
operational records. Synthetic cases exercise closed/current owners, historical
risk versions, missing/zero/mixed-unit evidence, metadata and malformed boundaries.
The comprehensive copy and independent wheel exercise the same adapter with all
real catalog rows. No Qt view or dependency changed. Overall percentage/finish
date remain unvalidated.

Validation: 1024 tests pass; 96.71% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f129_validation.json and artifacts/f129-*.log.
