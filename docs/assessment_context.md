# Assessment ownership and assignment lookup — F30

The reference identifies assessment data by worker ID, plant, section, line,
station, shift and tool ID within a project database. Shift is part of ownership,
not a display preference. A linked job is optional metadata; changing job
assignment must not silently relocate the assessment.

`WorkplaceContext` records all five workplace identifiers. `WorkerContext` adds
explicit project and worker identity, and `AssessmentContext` adds the existing
model enum. All are immutable, hashable values. Exact spelling, case and
whitespace are preserved. They do not derive identifiers from labels or paths.
These types are separate from DocumentKey: assigning existing drafts to contexts
and storing that association need a subsequent reviewed persistence slice.

`AssignmentSnapshot` carries repository-owned identity and eligibility flags.
`resolve_assessment_assignment` matches project, worker and all five workplace
fields, then requires an active assignment, a non-null job placement and an
active placement. It performs no I/O or mutation. A future repository adapter
must enforce placement/context consistency and normalize database flags to bool.
The snapshot is not a complete worker/job model.

## Reference evidence and deliberate boundary differences

The capture script in `reference/f30-capture.py.txt` extracts the actual
`worker_assignments` function and `assessmentAssignmentForContext` method using
AST, without importing the Qt application. It runs under the unchanged reference
Python 3.10.18 against a tiny in-memory SQLite schema. Frozen outputs and source
hashes are in `tests/fixtures/assessment_context_reference.json`. Normal tests
consume this fixture without locating the reference checkout.

Thirteen cases cover eligible/missing/inactive links, worker changes, each of the
five workplace fields, case and whitespace, and an inactive job. Every fixture
uses future assignment dates and expired placement dates: the original lookup
ignores these dates and job activity. The separate reference placement-options
selector *does* filter job activity; do not reuse this resolver as that selector.

The new typed boundary rejects blank/non-string identifiers and raw tool strings;
it does not reproduce the reference's arbitrary str coercion or combo-label
parsing. Adapters must explicitly map reference tool IDs LiFFT/DUET/ST to the
existing AssessmentKind enum. Incomplete UI selection must remain separate from
a valid domain context. Legacy empty identifiers need an explicit import policy.

The reference schema permits only one active assignment per worker/workplace
through a partial unique index. The new resolver rejects duplicate active rows,
even if one lacks an eligible placement. This is an explicit corruption guard;
the original method returns the first eligible row if given schema-invalid data.
The synthetic capture schema tests query behavior, not all reference schema
constraints. Cross-project isolation and malformed/duplicate guards are tested
separately as new contracts.

## Validation and remaining integration

304 tests pass; eleven additional test cases include all thirteen reference
vectors. Both new production modules have 100% combined coverage. The complete
standards, typing, architecture and distribution gates pass. See
`f30_validation.json` for package and reference integrity evidence.

No widget, database format, dependency or scientific formula changed. These
contracts are not yet connected to the temporary desktop harness or persisted
assessment catalog. Next: define explicit context-to-document association and
its storage/lifecycle behavior using focused temporary projects, then connect
worker/workplace selection incrementally. Preserve the final integrated UI and
comprehensive copied-project validation targets in `final_targets.md`.
