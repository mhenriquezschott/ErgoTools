# Workspace-owned risk operations — F65

JobRiskRepository describes the optional project capability and six existing
read/mutation operations. JobRiskSnapshot carries saved risk data; its exact
object identity and originating project handle establish callback authority.
Equal copies and views issued by other workspaces confer no authority.

ProjectWorkspace now exposes risk capability, refresh, creation/copy, draft edit,
approval, current selection and retirement. Each operation checks current view
authority, computes its expected domain result, calls the transactional repository,
and verifies the returned committed data. Inconsistent results revoke authority;
the caller must reload because an adapter may already have committed. Ordinary
write failures retain authority for deliberate retry; external saved-data conflicts
require refresh. Refresh revokes old authority before I/O, including on failure.

A successful profile operation returns a new view. Cross-project switch, new-project
activation, close and successful job replacement invalidate risk views. Same-project
document changes retain project-scoped risk authority. Creation preflight loads
current jobs without publishing a competing job-edit snapshot; the repository
rechecks membership and expected risk state under its write lock. Busy guards
reject nested adapter callbacks.

Risk operations never save/discard the active assessment, replace its session,
change its undo/redo revision, or update recent-project preferences. They commit
immediately as management operations, separate from assessment edit history.
Unsupported old formats fail explicitly and are not upgraded.

Nine new cases cover full workflow with a dirty source, settings/source persistence
isolation, copied snapshots, refresh/job-change/project-lifetime invalidation,
write retry, inconsistent adapter results, failed/foreign refreshes, unsupported
formats, nested preflight calls and external writer conflict. All 559 tests pass;
combined coverage 99.00%. Ruff/format, strict mypy (108 source files), architecture
and builds pass. Isolated-wheel verification runs create/edit/approve/current/
retire through the workspace and reopens the resulting project.
All 500 original files and dependency lock remain unchanged. No schema, UI or
scientific formula changed. Evidence: f65_validation.json and f65-verify.py.txt.

Next: Job Management presenters to prepare selected-job/profile actions and view
state, then original screen wiring and translated control/error states. These
workspace APIs do not constitute a finished management UI or legacy import.
