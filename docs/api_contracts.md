# API, units, errors and scientific behavior contracts

The integrated application uses typed ports/adapters, source-bound results and one shared
project editing session. The reviewed-source inventory and documentation checks described
in [coding standards](coding_standards.md) cover maintained code; they do not establish
external scientific validity or replace behavioral/native verification.

| Contract family | Units/identity/lifetime | Error and side-effect policy | Main source/evidence |
|---|---|---|---|
| Assessment drafts/calculators | Task IDs and source MeasurementSystem are immutable; missing is None; force is N/lbf, lever arm cm/in | DraftError/InputIssue for invalid inputs; finite arithmetic/model validation; no I/O or translated strings | domain/assessments; lifft_calculation.md, duet_calculation.md, tst_calculation.md; M01/M10 |
| Assessment summary/evaluation | Damage dimensionless; probabilities 0–1 internally and explicit percent at saved/export boundary | Complete/partial/invalid/unavailable outcomes; no fabricated zero; source/session identity binds results | application/assessments/evaluation.py; domain/assessments/*_summary.py; M01 |
| Saved calculations | One exact-source result per version; calculator damage/percent precision, no save clipping | Atomic replace/invalidation; absent/failed results remain explicit; Copy/Move preserves matching output | application/saved_results.py; infrastructure/saved_result_store.py; cleanup M1R |
| Worker/workplace/job/history | IDs plus full plant/section/line/station/shift; worker body cm/kg, dates ISO | ValueError for invalid/cross-project references; referenced records protected; historical ownership retained | domain/worker_details.py, work_hierarchy.py, job_catalog.py, assessment_history.py; M02/M03 |
| Session/workspace | Caller-owned immutable snapshots and dedicated repository handles | Save/Discard/Cancel explicit; failure retains active document; snapshot/backup exclusively publishes destination; backup excludes drafts | application/session.py, project_workspace.py; M04/M10 |
| SQLite/JSON | Versioned strict fields and typed finite values; project/document keys | DocumentFormatError/StoreFormatError/ValueError reject malformed data; sqlite3/OSError propagate to owned UI boundary; caller-owned transaction in stores | infrastructure/*_store.py, assessment_project_file.py; M04/M10 |
| External conversion | Original files unchanged; recalculate saved inputs using established formulas/units/ST convention | One authoritative result per assessment; discard old caches/archive in output; unsupported/conflicting sources fail | tools/project_migration; cleanup M1R/M2 |
| PLOT | Scene coordinates in original-image pixels; risks retain saved worker/assignment/tool and current Job identity | Missing demographic/result observations explicit; typed reversible geometry; accepted edits remain private until main Save; images/exports owned by adapters | application/plot_*.py, domain/plot_positions.py; M05/M06 |
| Rotation | Probability percent, ordered blocks/targets and stable Job/placement IDs | Pure validation raises ValueError; optimizer has explicit outcome/cancel state; no solver-thread UI/source mutation | application/rotation_*.py; domain/rotation.py; infrastructure/pulp_rotation_optimizer.py; M07/M08 |
| Settings/localization/parsing | Stable language/decimal/unit IDs; user names/notes literal | JSON atomic replacement; malformed numbers/locale grouping rejected; failed settings write reported separately from project commit | application/settings.py; infrastructure/settings_store.py; M09 |
| Renderer and Qt views | BodyRenderer immutable states; native VTK resources remain adapter-owned | Dispose timers/interactors explicitly; no Qt/SQL/VTK in portable core; failed owned commands report and retain input | application/contracts/body_renderer.py; presentation/desktop/rendering/vtk_body_renderer.py; M09 |
| Assets/Help | Package-relative resource bytes; fixed local cached guide filenames | Reject resource traversal/missing assets; QSaveFile complete commit before QDesktopServices launch; Help never saves project input | infrastructure/resources.py; presentation/desktop/manual_launcher.py; M11 |

## Preserved scientific policies

LiFFT follows original pyLiFFT.py version 1.4.0; DUET follows pyDUET.py 1.3.0;
ST follows pyTST.py 0.1.2. Calculator module docstrings and linked component
documents retain source hashes, coefficients, lookup values, characterized rounding
and frozen tests. M10 executes original mathematical classes in memory and compares
task outputs and summaries. These are original-equivalence checks, not external
scientific certification.

Model load constants (2.54 cm/in, characterized 4.45 N/lbf) and the original metric
moment display expression remain explicit in domain/model_units.py. They are not
silently replaced by a general physical-units converter. Worker body conversion
is separate. The original ST UI's direction labels and formula indices disagree;
the explicit source convention preserves its results and original Tab order.
Any scientific correction needs its own reviewed/approved change.

Sequential aggregation retains original order; model task rounding differs from
saved-summary rounding. 0.98249 rounds to 0.9825 at four places, not a new formula.
M1R recalculates original saved inputs; old cached outputs are not retained in native
projects. Missing inputs and failed/partial calculations remain explicit.
CSV uses stable English identifiers, percent values and point decimals; UI language
and display units do not reinterpret stored source data.

## Review dispositions

R001/ST convention and metric expression remain intentionally preserved scientific
review notes. R002/archived display, R003/dormant plant fields, R004/picker,
R005/numeric display, R006/scope labels, R007/capture artifacts, R008/fresh Save,
R010/shades/unit abbreviations, R011/captions, R013/project captions and R014/CR006
have their accepted dispositions in review_register.md and M01–M10 evidence.
R012 records scheme-scoped history/deletion decisions for later review, not new
features. R015/CR007 restores the approved original Search form using typed exact-owner
selection and existing dirty-input policy. The public-symbol inventory confirms
docstring presence; semantic review also covers units, errors, side effects and
scientific-source limitations at the API family level. See feature_inventory.md for per-source classification.

M2 Open consent supplies external CLI guidance, creates caller-owned temporary
native backing and activates only after native selection succeeds. Workspace
switch remember=False suppresses temporary recent paths. First Save publishes
all supported native data, retaining original metadata and unit meaning; close
consent covers unsaved project publication even with a clean assessment. Expected
conversion failures retain the active workspace and show localized guidance.


## Current project editing boundary

EditingRepository exposes begin/checkpoint/restore/commit without leaking SQL into
application services. Direct adapters remain durable; integrated ports atomically
accept into private state, and ProjectWorkspace.save commits the whole file.
ProjectEditingSession uses immutable ProjectEditState and the existing DocumentSession
engine. Worker and analysis windows subscribe weakly to the same chronological cursor.
Save failures retain edits; Save As validates accepted drafts; Backup reads the durable
baseline. This supersedes older per-editor persistence/Undo boundaries in the table.
See single_project_save.md and the current acceptance evidence.


## Owner-approved task-capacity behavior (2026-10-18)

Assessment row count is independent for each project/worker/tool/real assignment (or
standalone owner), default 15 and range 1-100. Existing count commands preserve the
exact retained prefix and append only fresh default rows; same-count requests are
no-ops. GUI acceptance preserves valid pending text and blocks invalid text. Removing
entered trailing rows requires Cancel-default consent. Shared project replay restores
truncated inputs and the exact matching result checkpoint. Only main Save publishes.
Grid evaluation ignores wholly unused default slots for completeness when at least
one row is entered; started incomplete rows retain explicit issues, all-blank sources
claim no evaluated probability, and strict preparation/evaluate APIs stay strict.
Numeric formulas, unit conversions, intrinsic rounding, source IDs and row positions
are unchanged. New calculations save the corrected complete/partial classification;
previously saved classification metadata remains historical until recalculated/saved.


Task-input history contract (2026-10-18, superseding pending-grid grouping): valid
LiFFT/DUET/ST edits expose main Undo immediately. Each numeric input completes on
focus departure or Enter; a rating/direction choice completes immediately. Each
completed cell is one command on the existing shared project cursor, without widget
rebuild, calculation or Save. Acceptance selects only that cell; another unfinished
or invalid widget is never swept into its command. Invalid text stays local and
blocks global replay until corrected, while valid siblings can complete separately.
The last still-focused valid input completes before mouse toolbar replay. Undo and
Redo therefore restore one completed input at a time and recover the exact matching
result when returning to its source. Focused Ctrl+Z remains native typing Undo, no-op
completion adds no history and only main Save publishes data. Explicit bulk commands
retain their atomic boundary. See task_cell_history_acceptance.md for evidence.


Repeated task-edit replay correction (2026-10-18): UI replay refresh deduplication
uses the operation and destination revision together. A fresh branch may return to
the same earlier destination and must still rebind widgets and matching results.
Nested notifications within that one replay remain suppressed. Shared chronology,
pending parsing, native typing, numerical models and Save boundaries are unchanged.
Project > Open project folder delegates a saved project's absolute parent directory
through QDesktopServices with a local-file URL. It is unavailable without a project
or before first Save and performs no input parsing itself. Normal field completion
on focus departure still applies. The OS owns the external
file-manager lifetime; no application child dialog/process is created. See
repeated_task_undo_and_folder_acceptance.md for evidence and desktop-test conditions.

## Shared history capacity

UserSettings.undo_limit validates strict integers 1-50 (bool rejected), default 25. Preference JSON v6 stores it; versions 1-5 load with 25 without being rewritten on read. ProjectWorkspace supplies it when creating the integrated editing owner. ProjectEditingSession.set_undo_limit applies it immediately and notifies all shared action adapters; it does not record an Undo step or change project data/dirt.

DocumentSession.set_history_limit accepts a positive integer or None (generic diagnostic unlimited policy), rejects invalid values and busy/reentrant mutation, and preserves current state, revision allocation and the saved marker. Capacity counts operations: at most limit plus one immutable states remain. Oldest excess Undo snapshots are removed on successful new edits. Reducing capacity while undone retains current state and nearest prior Undo first, then any Redo fitting the budget. No-op/failed commands preserve Redo and failed saves keep dirt. Increasing capacity cannot recover discarded states. Native focused text-editor Undo retains its established local typing behavior.

## Clear assessment

The active worker/tool/context retains its document identity, ownership, units, task IDs/order and configured count. Confirmed Clear removes numeric inputs and calculated results; DUET selectors return to zero and ST selectors to Handling Loads. Cancel retains pending text and accepted source/results. Existing source commands make Clear one shared operation; Undo/Redo restores exact source/results without recalculation. An already blank Clear is a no-op preserving Redo. Main Save publishes the blank owned assessment; other workers/tools/contexts stay unchanged.

ProjectWorkspace.stage_assessments accepts a keyword-only nonblank operation label (default assessment.edit; the explicit Clear action uses assessment.clear). Blank labels raise ValueError before private source mutation. Existing staging validation/failure and explicit publication policy remain unchanged. LifftWindow.clear_assessment owns consent and active-kind dispatch; confirm_clear_assessment identifies the project, worker, tool and available workplace context, uses the existing theme/icons and defaults to Cancel. No active source means no confirmation or mutation. The duplicate delete handler/widget is removed; underlying exact-source deletion ports remain for required lifecycle/integrity operations and tests.


## Workplace-first workflow — 2026-10-19

ProjectWorkspace.associate_assessment_at_workplace(document_id, workplace, placement_id,
effective_date=...) stages accepted integrated drafts and calls the optional repository
capability. It returns the exact AssignmentAssessment and invalidates Job/history
snapshots. The repository requires a saved standalone source, real worker/station/shift,
compatible optional Job and a calendar date. It reuses only an active same-worker
assignment with the same Job, otherwise creates one. Ownership uniqueness is checked
inside the same SQLite transaction. Any failure rolls back creation and binding;
KeyError identifies missing membership, ValueError invalid/conflicting ownership and
sqlite3.Error adapter failures. Successful creation/binding is one Undo step and stays
private until main Save. Existing associate_assessment(document_id, assignment_id)
remains available for callers with an explicit saved assignment.


## Current Job risks and independent calculators — format 19

JobRiskCatalog.for_job returns the sole JobRiskValues, or a transient empty set. Each
JobRiskMeasurement holds one tool's current dimensionless damage and 0-100 probability,
recorded unit label, optional immutable task source and exact JobTaskResult rows in source
order. Sources use their declared units/ST convention. None is absence, including before
calculation. Editing tasks invalidates all aggregate/per-task outputs. Direct entries
have no task source or outputs; no profile identity/status/evidence fields remain.

save_job_details replaces current values atomically; None preserves them and an empty
set removes them. Expected Job/risk snapshots guard against stale writers. Job metadata,
risks and affected rotation provenance roll back together. Replacing assignments/placements
upserts surviving Jobs so foreign-key cascading cannot erase current risks.

job_measurement_from_assessment reads any owned standalone or assigned source and its
matching complete calculation. Missing/stale/partial outputs fail; copying never recalculates
or changes source ownership. job_measurement_from_result retains exact inputs, task outputs
and totals. calculate_job_measurement calls the existing evaluator; no new formula exists.

RotationTarget identifies Job/optional placement, without profile ID. Payload codec 2 has
no saved numerical coefficients. refresh_rotation_draft resolves current values before
main Save as well as UI reopen, preventing retained closed windows from restoring obsolete
optimization provenance. Numeric edits retain arrangement cells and require an explicit
solver rerun; PLOT projections/CSV use current complete values with no evidence columns.


## Assessment browsing and Transfer

TransferRequest.source_assignment_id is an exact assignment ID, or None with a required
source_worker_id for standalone assessments. A provided worker identity must match an
assigned owner. Destination is either WorkerContext (worker, station and shift) or
StandaloneDestination (project and worker only). No fake workplace is used.
The pure plan_transfer validates all selected tools/identities/conflicts before writing.
The existing adapter copies exact sources and matching results in one transaction;
Move removes only the selected sources after successful destination creation. Main Save
publishes accepted data and shared Undo/Redo replays the operation. Copy/Move are user
choices in the existing Transfer dialog, with no redundant copy-specific port or action.

ProjectWorkspace.saved_assessment_result(document_id) remains read-only. The location
browser uses exact source IDs to distinguish historical assignments and shows only the
current worker/tool's saved assessments. Disclosure changes visibility, never ownership.


## Worker navigation defaults and compact browser — 2026-10-29

AssessmentNavigation.select_worker_default(worker_id, kind, blank) selects that tool's
existing standalone first, otherwise the saved workplace with the case-insensitive
alphabetically first Plant/Section/Line/Station/Shift path. Ties prefer an active saved
owner then stable assignment/document identity. Missing sources produce a deferred
standalone preview. Blank active assignments are not candidates. Explicit exact-owner
selection and generic remembered-context/tool-switch behavior remain separate APIs.
Selection uses existing chronological history and pending-input resolution; it never
creates ownership, copies sources or saves the public project.

AssessmentLocation separates optional Job (ID, name) from historical detail. Five
browser combos store literal path elements, including Shift; the separate Job cell
stores exact document IDs only when disambiguation needs a selector. The selected
signal emits that exact saved identity. Placeholders and rejected input restore the
accepted source projection. Headings count unique relevant options, not source rows.
ExpandableSection owns animation/lifetime only; it never reads/writes project state.
MainNavigation highlights the actual source and advertises available workplace data.
The existing nullable disclosure preference now has a collapsed display fallback;
explicit saved choices and main Save/Undo/Redo retain their established contracts.


## Add or replace workplace assessment

WorkplaceAssessmentRepository[State].add_workplace_assessment(worker_id, workplace,
placement_id, document_id, initial, effective_date=..., expected_document_id=None)
returns exact AssignmentAssessment. The source type establishes the tool. A saved
worker/station/shift is required; existing active assignments retain their Job. None
expected ID rejects every existing destination; a confirmed ID must match exactly.
Creation uses a fresh document ID; replacement retains the existing ID and ownership,
replaces inputs with the supplied blank source and removes its saved result. Assignment,
source, ownership and result changes are one transaction. ValueError reports ownership,
Job/date/stale-destination conflicts, KeyError missing membership; failures retain all
records. ProjectWorkspace invalidates catalog/target-session caches after success.

The GUI uses the shared hierarchy picker and No-default replacement consent. Blank
15-row sources are saved immediately into private editing state, may be published empty
by main Save, and participate in shared Undo/Redo. No scientific result is invented.
The disclosure's narrow projection does not rebuild worker/alphabet/location controls;
it refreshes history/Save and the brand Modified indicator without moving stable rows.


The same-Job/different-workplace creation warning is retained through the shared
pre-insertion duplicate-workplace query. It works even before a new assignment exists;
declining creates nothing. Existing historical owners remain historical observations:
Add targets the active assignment at the chosen workplace, not an unrelated older Job.


## Assessment presentation polish

BufferedControls.freeze/thaw own only an ephemeral device-aware presentation pixmap.
The overlay is mouse-transparent/unfocusable; original controls retain input and state.
A real resize clears the cache. MainNavigation cancels/settles an active reveal before
ordinary source/tool/language projection, then clears the buffer. Existing history and
visibility persistence remain outside this component.

WorkplaceAssignmentDialog accepts optional assessments: tuple[WorkplaceAssessmentPreview,
...] and assessment_tool. Each preview contains a literal WorkplaceContext, optional
saved probability percentage and active-assignment flag. None preserves the legacy
picker; an empty tuple shows New states. The selected shift filters badges without
loading/saving sources. Historical observations cannot be silently presented as current
replacement targets. Missing calculations remain explicit, never zero. Badge colors use
the shared classify_probability/RISK_APPEARANCES policy and survive row selection.


## Explicit worker assessment management

`ProjectWorkspace.delete_assessment(snapshot, document_id)` validates the latest
issued history authority, then invokes the existing transactional source/result
removal adapter. It clears only that document's browsing/session caches and active
pointer if selected; unrelated pending text remains intact. The host records the
confirmed removal and fallback view together in shared project history before
refreshing widgets, so GUI synchronization cannot amend the pre-deletion state.
No workplace/Job/worker is removed. `delete_active_assessment` delegates to this
exact-document operation for existing clients.

Find and Delete use immutable `SearchAssessment` rows with document ID, exact
`AssignmentSelection`, optional Job and historical flag. The shared modal optionally
accepts saved percentages; absent result is explicit, never a calculation. Delete
limits rows to current worker/tool and asks No-default confirmation. Search preserves
all current-tool worker sources and exact standalone/historical ownership. The retired
ToolDataDialog/saved_tool_options implementation is removed; Search is canonical.

Main tool panels reuse AssessmentActionRow's optional task buttons and the existing
presenter count command (1–100). Removal of entered trailing data requires consent.
AssessmentTaskGrid.focus_task defers reveal until coalesced header/row layout; a source
bind cancels pending focus. The host owns calculation and shared history, not the grid.
AssessmentBadgeDelegate reads display/background roles only and is shared by Find,
Delete, Add and Transfer. Transfer's destination columns use active exact worker,
station, shift and tool ownership, plus standalone ownership. Replacement requires
explicit consent and uses the existing transaction with exact rollback/history.


## Consented transfer replacement and standalone targets — 2026-10-29

TransferRequest.replace_existing defaults False: noninteractive callers still reject
occupied selected tools unless explicitly authorized. plan_transfer emits separate
replaced_documents (active target tools) and removed_documents (Move source tools).
A standalone target validates worker/project membership and creates no assignment.
An assigned target resolves only the active exact worker/station/shift owner; historical
observations remain. Identical source/destination owners always fail, even with consent.

The SQLite adapter preloads source payloads, removes approved targets, inserts exact
source/result copies, then removes selected Move sources under one write transaction.
Failure rolls back all steps. Unselected tools, Jobs, historical owners and workplace
assignments remain. ProjectWorkspace invalidates removed/replaced browsing sessions so
revisiting the destination cannot expose retired values. UI confirms the replacement
list, then checks it again after pending-source acceptance; changed targets require
reopening instead of silently expanding consent. Snapshot checks repeat under the lock.
Main host opens the destination after moving the displayed source; shared Undo restores
the old selection and data together. No schema/version/formula change or project upgrade.
