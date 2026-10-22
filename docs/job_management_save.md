# Job Management Save — F66

## Original control behavior

The reference `src/main.py` opens `JobWindow` with `exec_()` at line 5313.
Normal main-window interaction and project switching are therefore blocked while
this modal dialog is open. The application is single-user. Backend snapshot
checks must not be described as a multi-user requirement or evidence of an actual
project-switching defect in the original modal workflow.

Reference `src/job_window.py:914` saves job name/description and draft evidence
with one commit. Approved/retired selections save only job fields. With no
selected profile, the form requires at least one complete measurement and saves
an approved profile through `save_job_with_measurements` in
`src/job_risk_repository.py:432`. These branches were inspected directly; this
checkpoint does not claim full original-screen or legacy-schema equivalence.

## Implemented operation

`domain.job_management.save_job_details` prepares both catalogs. The project
adapter and workspace expose the combined operation. Job names/descriptions are
trimmed, saved jobs become active, and IDs reject the original ASCII-space case.
Measurement values retain their explicit units; no formulas or conversions run.
Draft evidence remains draft. Approved/retired evidence cannot be changed. A
first profile requires a complete measurement and becomes approved/current;
zero values are valid. The initial default name/methodology follow the reference.
The caller supplies an unused first-profile ID with version one and draft flags.
Existing New version remains the explicit operation for subsequent versions.

One SQLite transaction upserts the job's display fields and writes its profile.
Existing job ordering, workplace placements and worker assignments remain intact.
A failed write rolls back both changes. Successful workspace saves publish both
updated views without saving or replacing the active assessment document.

## Deliberate boundary and remaining integration

A new profile cannot be appended through Save when profiles already exist: the
caller must select a saved profile or use New version. This avoids invoking the
reference repository's compatibility fallback, which can overwrite an approved
current profile when called without a selected profile. Preserve the normal
modal selection workflow when connecting controls; do not claim this fallback
is migrated. Metadata-only saves require an existing job with a profile.

Legacy JobMeasurement materialization, timestamps, import and full deletion
policy remain outside this operation. The full Job Management window is not yet
wired. No UI, stylesheet, schema, dependency or scientific formula changed.
Next is original-screen integration, including navigation/selection, form parsing,
actions, and the already migrated workplace dialog. Retain modal behavior and
perform native visual checks once controls are migrated.

## Validation

Seven added cases cover initial save/reopen, draft and immutable-profile branches,
invalid forms, actual SQLite failures during job/measurement writes with retry,
and workspace saving while assessment edits remain unsaved. Full checks pass:
566 tests, 98.89% combined coverage, Ruff/format, strict mypy, architecture and
wheel/source builds. Isolated-wheel creation/reopen passes. All 500 baseline
reference files and uv.lock hashes match. See `f66_validation.json` and the
reproducible `reference/f66-verify.py.txt` script. These checks do not constitute
final application acceptance or scientific-model validation.
