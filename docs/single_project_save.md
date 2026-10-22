# One project Save and shared Undo/Redo

Owner-approved workflow change, 2026-10-18. Linux migration and cleanup remain
complete at 100%; this is the bounded owner-testing correction, not a new milestone.
Linux verification passes: 1,400 tests, 94.28% combined coverage, required standards/
review/build checks, 50 independent-wheel tests and 64 inspected EN/ES captures.
See [acceptance and limitations](single_project_save_acceptance.md). The subsequent
[pending worker Undo correction](worker_pending_undo_acceptance.md) passes 1,406 tests
at 94.29% coverage, forty independent-wheel tests and twelve additional UI captures.

## User contract

The integrated application's main Save writes all accepted project data together:
workers/demographics, organization, assignments, Jobs/risk profiles, assessment
inputs/results, plant images/geometry and complete JROT schemes. Closing a management
or analysis window retains accepted changes in the open project. It does not write
the `.ergprj` file. Closing or switching the project offers Save/Discard/Cancel.
Invalid form fields stay available for correction or explicit form cancellation.
Application preferences retain their own Apply/Cancel policy outside the document.

Add worker accepts one worker and prepares the next entry. Switching workers or
closing Worker Management accepts valid detail edits. Its title-row Undo/Redo uses
exactly the same chronological project history as the main window. Four additions
are four actions: Undo removes W04, then W03; Redo restores their complete details.
Closing the window is not a history action. Existing worker records remain editable.
For an existing worker, a valid pending form change enables title-row Undo immediately,
including after reopening a saved project with empty history. Clicking Undo accepts
and reverses that one edit without closing the dialog. Pending edits temporarily
disable project Redo without consuming its branch; returning to the loaded values
restores availability. Native typing Undo remains local to the focused field.
New records still require Add worker, navigation or Close for acceptance.
Actions needing a new record (assignment, child workplace, Job workplaces) accept
valid form data first; they do not require a local Save or closing/reopening.

Organization and Job windows retain valid edits on navigation/close. PLOT accepts
images, released marker gestures and validated coordinate/flag changes into the
project session. Apply to all remains a validated batch operation, not a Save.
JROT retains partial grids and scope/identity/provenance across window closure.
An entered incomplete rotation blocks main Save/Save As until completed or cancelled;
no rows are silently dropped and no draft database table is introduced. Solver
preview still requires explicit Apply/Use as current; only accepted choices enter
project content. CBC/HiGHS routing and scientific formulas remain unchanged.

Main Save preserves Undo/Redo, including a pending Redo branch. One completed worker
edit is one operation. UI navigation/filter actions remain reversible without removal
warnings. A replay that removes records identifies those records and requires
confirmation with Cancel as default. Cancellation consumes no history step. Restoring
records and ordinary field/navigation changes need no removal warning. Focused text
editors keep their native typing history; solver ownership still blocks replay.

Save As validates and publishes accepted content to a new exclusive destination,
leaving the original file unchanged. The copy opens as a new clean project session;
Undo history remains session-local, not part of the native file. Backup continues to
copy the last main-Save baseline and does not include unsaved session content.
Exports read accepted open-project data and do not Save it implicitly. Separate file
exports (CSV, graph images, captures), Save As and Backup remain explicit file actions.

## Architecture and storage

`ProjectWorkspace` enables private editing for the integrated composition;
low-level repositories and diagnostic harnesses preserve their explicit-write
contracts. `EditingRepository` is an optional application port. Its native adapter
copies the owned SQLite connection to private memory and recomposes its existing
stores there. Existing transactional/expected-authority/source/result validation
continues to run. Only `commit_editing` publishes private state through SQLite's
atomic destination backup transaction. The durable baseline survives failed commits;
private edits remain retryable. No automatic backup, project sidecar, dependency,
schema version, table or persisted assessment-version/history feature is added.
Native project format remains 16 and personal preferences remain format 5.

`ProjectEditingSession` reuses `DocumentSession` for a single chronological history
of compressed opaque native checkpoints and deeply immutable accepted editor values.
The application does not parse SQL/native bytes. Native restoration validates the
same project before replacing private state. Undo/Redo restores relationships,
images and the sole matching calculated results together. Record inventories support
specific removal confirmations. These transient revisions are not assessment versions
and are never persisted in the business schema.

The workspace invalidates catalog authorities and rebinds live source sessions on
replay, retaining immutable source identity when it matches restored native data.
`replace_from_owner` invalidates stale contexts; `amend_current` synchronizes derived
output/automatic projections without inventing a Save action. Assessment, PLOT and
JROT Qt adapters share the application cursor; weak subscriptions and native owner
cleanup prevent retired editors from retaining windows. Assessment task viewport
positions remain presentation-only, indexed by the replayed action identity.

First-assessment same-Job creation consent remains at main Save/Save As. Private
preview acceptance does not bypass it. Consent markers live only in session history;
no business column/table is added. Successful consent survives a failed Save retry.
Existing canonical cm/kg demographics, source measurement systems, calculator
precision, EN/ES localization and project ownership uniqueness remain authoritative.

## Verification and handoff

Focused end-to-end regressions cover four workers, worker edits/navigation, shared
buttons/cancelled removal consent, organization/Job close, private versus durable
reopen, failed commits/retry, Save As/last-Save Backup, PLOT move/reopen and JROT
partial/reopen/complete Save. Existing integration expectations are updated to check
accepted private content separately from the durable file, rather than restoring the
old local-save behavior. Required checks, packaged-source checks, native captures,
remaining limitations and actual counts are recorded in the final acceptance evidence.

The owner's `test_projects/native/workflow_4_workers.ergprj` is verification input
only. It is not seeded, corrected or rewritten by this change. Owner workflow testing
can resume at four workers after restarting the application; owner acceptance
remains pending.
Native Windows/macOS acceptance remains deferred; no new platform result is inferred.


## Assessment input granularity — owner correction, 2026-10-18

The earlier pending-grid acceptance boundary grouped fields and is superseded. Each
completed LiFFT/DUET/ST cell is now one shared-history command: focus departure/Enter
for numeric fields, immediate completion for selectors. Only that cell is accepted;
invalid siblings remain local. Arm 50 then Load 60 gives Undo Load, then Undo Arm, and
Redo follows the same order. Revisited fields create new chronological steps. The
existing source command and ProjectEditingSession still own the single timeline; no
extra stack, persistent assessment version, table or result copy is introduced. The
last valid field completes before toolbar Undo, which restores only that field first.
Focused typing Undo and explicit atomic bulk operations retain their established
boundaries. Main Save remains the sole durable publication. See task_cell_history_acceptance.md.

## Save availability

The main toolbar and Project menu share the existing project dirty state. Save is disabled for a clean loaded project, enabled for private data changes or pending task input, and remains enabled until a first Save of a temporary project. Shared session notifications update it for management edits without closing the management window. Undo/Redo reflects the saved data baseline; view-only navigation does not require Save. Cancelled or failed Save retains availability. Existing input validation, explicit calculation and atomic publication remain authoritative.

The personal Undo limit does not reset the durable Save baseline. Evicting history cannot mark changed data clean; Undo/Redo within retained history continues to update Save availability against that baseline. Changing the budget alone never requires project Save. History remains session-local and is not serialized in .ergprj files.

Clear assessment changes only the active worker/tool/context inputs/results in the private project. It retains the owned editable grid and is one shared Undo step; it never clears another tool or requires creating a replacement assessment. Cancel leaves pending text; Main Save publishes confirmed clearing. Undo after failed publication still restores the saved source/results. The former separate Reset/trash controls are superseded by this one action.


## Organization pending edits and optional clock input — 2026-10-19

Existing organization forms now expose valid pending changes to the same
ProjectHistoryActions contract used by Workers. All dynamically created line and
multiline fields refresh availability. Mouse history buttons take focus, accept the
current record once and replay the shared cursor; keyboard Undo in a focused text
field remains native. No second stack or per-keystroke project snapshots are added.
Multiple pending fields in one record form are accepted together at replay,
navigation or Close. Cancel discards that pending form; main Save publishes.

Plant and Shift start/end editors use standard QLineEdit regex validation with
visible 24-hour HH:mm labels, placeholder and localized range/optional guidance.
Empty values remain None; complete values retain exact HH:mm strings. Incomplete or
invalid nonempty times block acceptance without losing text or creating a record.
There is no start-before-end restriction: overnight shifts remain valid. Validation
is a presentation form contract, not a new schema or converter normalization.


## Organization view preservation — 2026-10-19

Optional details retains its current widget state through form rebuilds, navigation,
accepted edits and shared replay. Tree refresh captures expanded and collapsed flags
by complete location ancestry, keeping absent paths only for this dialog's lifetime
so a deleted subtree can recover its previous expansion on Undo. Surviving branches
always use the user's latest flags. Internal edit/replay reselection reapplies those
flags after Qt's automatic ancestor reveal; explicit navigation and new-record reveal
remain unchanged. A restored deleted record is reselected unless the user has since
chosen another record. A still-missing identity leaves the existing empty selection
state rather than a fabricated new record form.

These are presentation-only choices. No database/settings serialization, additional
Undo operations, assessment versions or application history stack is introduced. A
fresh Organization dialog retains its established initial collapsed view.


## Standard optional clocks and explicit Shift day intent — 2026-10-19

This supersedes the plain-line-editor clock input above. Plant/Shift start/end fields
use OptionalTimeEdit, a standard Qt QTimeEdit adapter. Qt owns hours/minutes, colon,
zero padding, keyboard parsing and arrows. The adapter distinguishes absence from
valid midnight and retains unparseable historical text for correction. Valid short
hours display canonically; editing/saving the record writes HH:mm. Focusing an absent
clock does not supply midnight. Ctrl+A/Delete clears; invalid paste is inert.

Shift day choice is form-only intent, not a new business field. Same-day requires
end > start. Following-day requires end <= start, representing one daily interval
(up to 24h; equal clocks mean 24h only when following-day is selected). Loaded complete
pairs infer following-day from that same ordering; partial/absent values stay optional
and disable the day selector. The draft baseline includes day intent so an unchecked
overnight pair cannot silently close/save. Invalid pairs retain input and stored data.
Canonical clocks alone are serialized through the existing organization attributes.

Mouse replay remains the existing shared record operation. Keyboard Undo in a focused
QTimeEdit routes to its native internal line editor; other spin/date controls retain
their existing handling. Optional details and tree choices continue to be retained.


## Workplace-first workflow — 2026-10-19

Workplace assignment creation and standalone assessment association now form one
atomic private action when no assignment exists. Cancellation writes neither record;
one shared Undo/Redo step reverses/restores both. Existing assignments are reused
without changing their optional Job. Main Save publishes the relationship along with
the unchanged scientific source/results. Worker Management assignment alone selects
a context; it does not relocate standalone data.
