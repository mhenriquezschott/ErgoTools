# Single-worker assignment transitions — F42

The pure application operation assign_worker returns an AssignmentChange containing
the replacement JobCatalog and selected assignment ID. Commit it through
ProjectWorkspace.replace_jobs using the snapshot from which it was computed.
An external commit causes the existing expected-value guard to reject replacement;
the caller must refresh and recompute, never reuse the old result blindly.

This reproduces assign_worker_to_job_placement in the reference
src/job_placement_repository.py:

- Require an active placement and active job at the exact requested workplace.
- With no active assignment, create a new assignment starting on the supplied date.
- Selecting the current placement returns the unchanged catalog and identity.
- Classifying an unclassified assignment retains its ID and existing start date;
  an absent start becomes the supplied date.
- Changing a classified placement closes the old assignment, retaining an existing
  end date or supplying one, and appends a new active assignment with a new ID.
- Reference notes are preserved exactly for each operation. Inactive history
  remains unchanged.

The caller supplies a date (not datetime) and a new integer ID. The ID must be
unused when a new row is needed; it is ignored for no-op/classification cases.
Automatic ID allocation remains a host/repository integration responsibility.
A collision fails before commit. Calendar-date injection replaces the reference's
implicit date.today call; application composition must supply the intended local
business date. Dates already stored remain reference-compatible lexical text.

The operation rejects wrong project/workplace, missing or inactive placement/job,
invalid ID/date types and reversed resulting date ranges. It has no hierarchy
argument: worker membership is checked by the repository under the write lock
when committing. Calling the pure function alone does not prove worker existence.

The new fixture captures five executions of the actual reference function under
reference Python 3.10.18 with a fixed date and minimal synthetic SQL tables.
It isolates transition behavior; full reference schema constraints are characterized
separately by the F40 overlap fixture. Tests compare exact IDs, dates, activity and
notes. Additional cases check invalid requests, preserved history/start dates,
no-op identity and a real workspace/database commit preserving assessment data.

F43 separately migrates update_worker_assignment_jobs; see
[batch classification](job_classification_batches.md). Neither operation creates a
UI editor or attaches assessments to historical assignment IDs. Existing assessment bindings still identify worker/workplace/model. Do not
claim final historical assessment parity from retained assignment rows alone.

Validation: 426 tests pass, total coverage 98.90%, new module 100%; Ruff/format,
strict mypy (95 files), architecture and builds pass. Extracted-wheel reassignment
and reopen pass. All 500 original files and the dependency lock are unchanged.
See f42_validation.json and archived capture/verification scripts. No schema,
scientific formula, dependency or UI change.
