> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in the owner decision record
> and [current database inventory](database_tables.md). Removed APIs are not supported.

# Risk-profile draft creation and editing — F62

JobRiskCatalog.create_draft now validates project/job membership, allocates the next
per-job version from the existing maximum and accepts an explicit new profile ID.
It can create a blank profile or copy a same-job profile in any lifecycle state.
The reference names are preserved: New estimate - revision, or the copied name
plus ' - revision'. These are persisted initial names, not translated UI labels.

Copying retains measurements, units, source reference, methodology, sample size,
assessment date and notes. It resets status/currentness to draft/noncurrent and
source_type to expert, including copies of study/imported evidence. This matches
the original create_draft_profile behavior; it is not an inferred provenance fix.
Other profiles and the current approved profile remain unchanged.

edit_draft requires expected content matching the current snapshot, draft status,
and unchanged profile ID, job ID, version, status and currentness. Name is trimmed
and must be nonblank. Empty optional evidence strings become None; whitespace-only
optional strings are retained as the original repository does. Measurements with
both numeric values missing are omitted. Partial values and valid zeros remain.
This is the repository-level rule, not permission to bypass the UI's paired-entry
validation. Immutable catalog replacement means rejected edits leave input intact.

validate_jobs also checks every existing profile's parent job and project. This
will be used by the persistence boundary. New IDs are caller-provided; atomic
storage must enforce competing writer and identity checks. These domain methods
alone do not prevent a caller constructing arbitrary replacement catalogs; the
future store must expose guarded operations rather than unrestricted approved
profile updates.

Original create_draft_profile and save_draft_profile were executed via AST extraction
under the original Python baseline against in-memory SQLite. Fixtures compare
blank, copied and edited records, including version gaps, provenance reset,
partial measurements, null normalization and retained units. No operational
database or original file was modified.

Five new cases cover reference comparisons, first versions and bad ownership,
approved/retired edit rejection, stale expected records, and lifecycle/identity
tampering. All 525 tests pass; combined coverage 99.01%, risk domain 100%.
Ruff/format, strict mypy (106 source files), architecture, builds and extracted-wheel
copy/edit/approval protection pass. Original 500 files and dependency lock are
unchanged. No UI, schema or scientific formula change.
Evidence: f62_validation.json, reference/f62-capture.py.txt and f62-verify.py.txt.

Next: transactional profile storage with job membership, version uniqueness,
expected-state conflict detection and approved-evidence protection, followed by
workspace/presenter and original Job Management control wiring.
