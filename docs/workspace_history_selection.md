# Assignment-aware workspace selection — F46

This is the workspace portion of the documented worker/job assessment workflow,
following F45 historical persistence. AssignmentSelection carries an exact project,
assignment ID and assessment model. The optional HistoryRepository capability
returns validated saved history. ProjectWorkspace.select_assignment selects that
pair's current assessment without worker/workplace fallback.

Closed assignments remain addressable for history viewing. The future active-work
presenter must separately enforce assignment/placement eligibility; this operation
does not claim an old assignment is currently eligible. Missing current ownership
raises KeyError rather than borrowing a successor's assessment. Foreign projects
and foreign adapter history are rejected.

The existing synchronous lifecycle contract applies: Cancel or missing dirty
consent returns an incomplete transition without repository I/O. Saved ownership
and the candidate source are loaded before saving the active source. Load/save
errors preserve the active session; source revision changes during selection and
nested transitions are rejected. Selecting the same document retains its dirty
state and undo history, including when Save or Discard was supplied. Recent-file
preferences and project connection ownership do not change.

Repository history validation includes source existence/model and assignment
membership. This is not a database transaction spanning lookup, old-source save
and activation, and does not offer cross-process current-version locking. Explicit
current-version changes remain pending. The project coordinator remains
single-threaded; UI callbacks must not invoke concurrent transitions.

Two new integration scenarios exercise multiple paths with real version-six
projects: closed/successor selection, dirty consent, same-document behavior,
missing/foreign identities, load/save failures, reentrant transition/source edits,
foreign adapter results and unsupported adapters. All 448 tests pass; total
coverage 98.94%, history access and workspace modules 100%. Ruff/format, strict
mypy (99 files), architecture and builds pass. The extracted wheel selects both
historical and successor assessments. All 500 original files and the dependency
lock are unchanged; see f46_validation.json.

The Qt dialog and temporary harness are not wired to this capability yet.
Assignment-aware presenter snapshots, creation/current-version lifecycle and
pending-text/dirty-choice host integration remain next. No schema, scientific
formula, dependency or UI change occurred.
