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
| Rotation | Probability percent, ordered blocks/targets and stable Job/placement IDs | Pure validation raises ValueError; optimizer has explicit outcome/cancel state; no solver-thread UI/source mutation | application/rotation_*.py; domain/rotation.py; infrastructure/highs_rotation_optimizer.py; M07/M08 |
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


## Task metadata and clipboard

TaskDefinition uses a nonblank project-local ID/name and optional text description.
Task rows keep optional fallback name/reference independent of their numeric identity.
Constructors reject invalid metadata with ValueError. Current project adapters validate
reference membership and protect used definitions from deletion. Catalog writes use
expected-state checks and shared project history; rename never rewrites source/result
bytes. Format 20 is the current integrated contract.

`prepare_assessment_paste` returns one immutable replacement or raises ValueError for
mapping/size/capacity problems. `ClipboardRowError` retains the failed target row and its
DraftError/ValueError detail for localized field feedback. Scientific calculation is not
performed by parsing. The complete batch validates before acceptance; stale expected source
rejects, Cancel is a no-op, and one accepted batch is one shared Undo step. Full-precision
copy and unchanged projected values preserve source precision under unit changes.


## Rotation timing contracts

Relative intervals and productive budgets are exact whole minutes, with a daily span of
1–1440. Breaks are nonoverlapping half-open intervals; adjacent pauses are permitted.
Every block has at least one productive minute. Equal blocks differ by at most one minute,
with earlier blocks receiving remainders. Projection covers working minutes exactly once.
`averaging_minutes` is productive time when subtracting breaks and full span otherwise;
work is never assigned to breaks. This is a planning-index policy, not a recovery/dose model.

Shift clocks require canonical 24-hour text. End at/before start follows the existing next-
day convention; equal clocks mean an explicitly accepted 24-hour recurring Shift. Missing
clocks are not zero. Templates use relative offsets, so same-span clock moves retain them;
duration changes or owner removal are rejected until explicit clear. All normal and combined
hierarchy writes validate those references. `replace_shift_timing` requires the exact prior
value and existing owner under a transaction. Runtime errors, invalid/stale values and
SQLite failures preserve the accepted project checkpoint. Corrupt codecs raise StoreFormatError.

Timeline gestures emit complete proposals without storage/history ownership. The host
rejects foreign/retired project ownership, validates pending cells and uses shared history.
Unfinished data is never partially written. Opening is read-only; snap size is session-only.
Saved current JROT schemes, coefficients and optimizer routing remain unchanged.


## Named scenarios

RotationScenarioRepository exposes read-only name/ID ordered catalogs, one exact expected-state
replace and independent last-view selection. Creation/deletion updates selection atomically;
unknown/stale IDs use pure opening fallback, never an automatic record. New accepted plans
require local dates; legacy unknowns stay None. Partial entered schedule cells remain None and
cannot be solver-ready. RotationRun validates complete staffing/context and retains exact
source-bound coefficients, labels, timing, settings and ordered stage statuses. It is not an
optimality certificate. apply_rotation_run accepts a rename but rejects changed input/risk
ownership before a guarded write. No solver or GUI is invoked by these lifecycle functions.

Store errors distinguish corrupt payloads (StoreFormatError), stale/invalid commands
(ValueError), missing current write capability (RuntimeError) and SQLite failures. Transactions
roll back data, selection and history together. Main Save alone publishes. See
[complete scenario contracts](rotation_scenarios.md).

### Guided entry (development)

rotation_entry helpers prepare whole immutable replacements without persistence. Reshaping
retains surviving cells by exact worker/position identity and reports every lost entered
cell for No-default consent. set_rotation_cell changes one baseline slot when observation
exists, otherwise one proposal slot. Catalog/readiness helpers never infer participants,
Job coefficients, a baseline or a solved result.

JrotDialog/JrotJobPanel borrow the active workspace/editor owner. Accepted edits use existing
scenario/Job APIs, clean view navigation uses immutable project editor state, and Main Save
alone publishes. RotationTimingDialog paired read_target/write_target callbacks distinguish
scenario timing from its original Shift template; stale expected timing and session ownership
are guarded. Production entry never imports prototype sample data or its session mutation.
Native23 admits empty entered drafts before participant selection; older native22 drafts are
validated before a marker-only external upgrade. See jrot_guided_entry.md.

## Duration-aware planning

RotationInputs.rules stores closed typed FixedPosition, ExcludedPosition and NoAdjacentHigh
values. Optional RotationBoundary snapshots use exact run signatures and local minute clocks.
RotationPlanningProblem validates dates/timing, complete required coefficients, perfect
staffing and every hard rule independently of backend status. RotationPlanningOptimizer.solve
returns only a detached proposal; accepted_rotation_run rejects feasibility-only generation.
apply_rotation_run rechecks numerical sources and validates the schedule before replacement.
run_is_current requires the current catalog for explicit neighboring-source checks.
The GUI retains a fresh successful optimization only after explicit Keep optimization
result, as one undoable edit with the original baseline unchanged. Replacing a retained
run requires consent; an unkept preview is not published by Main Save. Step 04 feasibility
generation accepts only the requested proposal, with replacement consent, and stays in 04;
step 07 only optimizes. Main Save stores runs;
worker cancellation cannot write or terminate
native solver threads. See jrot_planning.md for units, stages and failure behavior.

## Guided comparison boundary

See jrot_comparisons.md. Pure rotation_comparison projects frozen run distributions and
same-context deltas; it has no live catalog or solver dependency. JrotResultTable is shared
by proposal, retained and compact comparison matrices. JrotComparisonPanel projects exact
retained evidence with cards, tool statistics and optional details, retaining stale/unsupported
status. Rework uses existing
scenario lifecycle/history ports; no schema/codec or alternate Job profile is introduced.
Main Save remains the only project publisher. Normal/Legacy promotion remains J08.


## Assessment import and personal profiles

`ImportProfile` is immutable and validates one allowed mapping per field; version-8
personal settings store one profile per tool. `ImportTable` contains detached strings.
`TabularFileReader.read(location, profile, sheet, cell_range)` returns bounded values or
raises policy `ValueError` / filesystem `OSError`, without saving a source file.
`prepare_import` normalizes explicit number formatting and delegates to the existing
atomic assessment clipboard mapper. It returns a replacement source, never accepts it.
Hosts own stale-source checks, automatic calculations, history and Main Save.

File/preview limits and blank/unmapped semantics are documented in
[import and paste](assessment_import.md). Settings sample rows are never assessments.
Workbook formulas are not evaluated; mapped numeric formulas are invalid input.


## Optional columns and graphical timing

`AssessmentColumns(kind, hidden)` accepts unique optional semantic keys only; required
inputs cannot be hidden. User settings format9 adds a per-tool tuple, defaulting to all
columns visible for old personal files. `AssessmentEditorPreferences.bind` connects owned
editable grids to import/visibility ports; `refresh_columns` publishes accepted app choices.
No project data or sample values are serialized by the Settings preview.

`split_work_block`, `join_work_blocks`, `remove_work_block`, `change_timing_break`,
`draw_timing_break` and `join_timing_breaks` return complete immutable timings or raise
ValueError without accepting a change. Removing either kind extends its immediate neighbors; work removal can extend pauses
and therefore requires review when productive time decreases. Joining pauses
requires touching intervals. Existing ownership/expected-state/scenario-consent/history
ports remain authoritative.

Structural timing edits preserve assignments only for unchanged clock-span blocks. Split
or joined blocks receive empty cells, with explicit consent for every affected entered
cell. Untouched later blocks retain their original assignments instead of shifting by
array index. No assignment is inferred; Undo restores timing and cells together.

`separate_work_blocks` normalizes compatible interrupted budgets for an explicit editor proposal. `edit_contiguous_breaks` preserves independent clock cuts. `equalize_contiguous_timing` preserves pause lengths/names while moving them to block boundaries; impossible positive budgets are rejected. The UI confirms coordinated count and clock changes before accepting. TaskNameDialog uses existing load/replace_task_definitions ports and shared project history; referenced IDs cannot be deleted.

## Uniform segment editor update — 2026-11-01

The current editor uses application.rotation_segments for both work and pauses. Removal extends immediate neighbors (sole neighbor at an edge, half to each inside). It may extend breaks; the host confirms reduced work time. Move applies to both types with local translation or whole-segment reordering; all interior boundaries resize neighbors. Coordinated equal/count edits preserve type totals and honor both equality choices; Equal breaks shares the existing pause budget. Positive-budget impossibilities reject without implicit deletion or extra work blocks. Break equality is inferred from saved durations, not a new stored field. Both tables have matching controls and keep full shift coverage. This supersedes earlier editor statements requiring removal of a break before removing adjacent work; explicit Join still preserves intervening intervals. Existing expected-state/scenario consent/history and native24 remain unchanged.

Guided single-tool optimization now records two passes, preserving minimax ceilings
before range minimization. Historical single-pass runs remain supported by RotationRun.
The unchanged settings field records objective policy; no schema/model version change.
See jrot_secondary_balance_review.md for compatibility and acceptance.


## Ordered assessment-row removal

`application.assessment_task_rows.remove_assessment_rows(source, rows)` accepts a
nonempty tuple of zero-based integer positions. Duplicates are harmless; invalid,
negative, boolean and out-of-range positions raise ValueError. The returned same-tool
immutable source retains exact unselected tasks in source order. Removing all tasks
creates one blank starter. Job hosts retain their own existing empty-source projection
when all selected rows are removed. Confirmation, pending input acceptance, calculation,
history and persistence remain host responsibilities.

`AssessmentTaskGrid.selected_task_rows(fallback)` returns explicit header rows, then
cell-range rows, then the host default. `AssessmentTaskActions.remove_selected` validates
pending input, confirms entered data once, rejects a changed source after a modal, and
accepts one source replacement. ImportRowHeader emits inclusion intent only; the shared
import panel stages reversible exclusions and maps diagnostics back to visible source
rows before invoking the unchanged immutable prepare_import contract.


## HiGHS-only optimization

`HighsRotationOptimizer` and `HighsRotationPlanner` use highspy1.11.0 directly.
No engine-selection constructor, capability protocol, preference or alternate runtime
exists. Guided planning retains minimax then spread objectives for all seven tool subsets;
the original single-tool workflow retains its original one-pass minimax. Each pass loads
the exact model into a fresh native HiGHS instance with its own full time budget and
0.01 relative gap. Returned primal validity, feasibility, binary values, staffing/rules
and first-pass ceilings are checked independently. A failed later pass never publishes
stale first-pass values. Application/domain remain independent of native solver types.

Native solver provenance in previously kept runs remains truthful and readable, including
historical one-pass results. Such metadata cannot select a solver or enable an old engine.
Settings version11 discards the obsolete version10 comparison field on reading and never
serializes a solver preference. Other settings, project schema, coefficients, objectives
and calculator formulas remain unchanged. PuLP and its bundled CBC are removed from the
lockfile, runtime, trial requirements and typing boundary. See highs_only.md.


## Atomic pasted task names

`application.task_catalog.reusable_pasted_names` plans source references/catalog records
for an exact set of destination task IDs and an injected identity factory. It preserves
measurements, row IDs and literal fallback names, reuses NFC/trim/casefold matches without
merging existing IDs, and rejects invalid rows/references/duplicate generated identities.
`ProjectWorkspace.accept_task_paste` stages prior edits, accepts catalog/source/calculation
through guarded host ports, and records one `assessment.paste` action. Failed/rejected
acceptance rolls back both participants and live views without losing the Redo branch.

`ProjectEditingSession.action` composes existing checkpoints/history: nested records
and automatic `synchronize` calls defer to the final action checkpoint. Rollback notifies
ordinary replay observers without moving the history cursor. Existing `stage` semantics
remain unchanged. Source/catalog writes retain their existing validated transactional
ports and native schema. Main Save alone publishes durable data.

Shared-grid Paste computes the exact mapped/included destination name rows for both
quick paste and reviewed imports. Undo Paste always requests removal consent, including
pastes that only reuse existing names or contain numeric columns. Redo uses the exact
checkpoint identities. Catalog subscriptions are weak, detached at project switch/Qt
destruction, and never overwrite pending literal name typing.
