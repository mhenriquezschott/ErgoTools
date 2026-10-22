# Workspace job editing contract — F41

ProjectWorkspace now exposes read_jobs, jobs_are_current and replace_jobs through
the optional JobRepository port. JobSnapshot holds the immutable persisted
JobCatalog; only the latest object issued by the current workspace/project handle
confers edit authority. Equal copies and snapshots from another workspace do not.

Refresh invalidates the previous job snapshot before I/O, including when reading
fails. Successful replacement publishes a new snapshot. Failed validation or SQL
writes leave the current token available for a corrected retry. A database value
conflict requires refreshing and reconciling changes before retrying.

The adapter compares the expected complete JobCatalog under the same BEGIN
IMMEDIATE write lock used for hierarchy validation and three-table replacement.
A conflict raises ValueError before any deletion. This is value comparison, not
a persistent revision counter: a change away from and back to identical data is
not detected. There is no automatic merge or cross-process notification.

Snapshot ownership lasts for the project handle. Switching assessments in the same
project retains it; successful cross-project switch, project creation or close
invalidates it. Failed or cancelled transitions preserve the current ownership.
Nested transitions are rejected during repository I/O.

Job commits do not save the active assessment, clear its dirty marker, alter its
undo history or update recent-file preferences. Hierarchy and job snapshot tokens
are independent; storage revalidates current hierarchy membership under the write
lock. They do not constitute a combined chooser snapshot. Host integration must
validate the job snapshot as well as hierarchy and active assessment state before
accepting a context selection.

This adds safe snapshot replacement, not a historical reassignment command or job
editor. Closing prior assignments, preserving historical assessment links and
integrating pending text/dirty choices remain required. The existing low-level
save_jobs method remains available for explicit repository seeding/replacement;
interactive editing should use the workspace expected-value path.

Validation: ten new real-database workspace cases cover dirty assessment isolation,
forged/stale/foreign tokens, reopened handles, same-project selection, failed reads,
external commits, rollback/retry, invalid owners, nested transitions and unsupported
repositories. All 422 tests pass; total coverage 98.89%. Job access, workspace and
job storage reach 100%. Ruff/format, strict mypy (94 files), architecture and builds
pass. The extracted wheel independently exercises a concurrent saved-value conflict.
See f41_validation.json and the archived verification script. All 500 original
files and the dependency lock remain unchanged; no schema or UI change occurred.
