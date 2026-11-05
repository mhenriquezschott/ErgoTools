# Current ErgoTools architecture

The accepted design is a modular monolith with ports/adapters and desktop
presenters. One integrated Qt application hosts LiFFT/DUET/ST, PLOT and JROT.

| Layer | Current responsibility | Internal dependencies |
|---|---|---|
| domain | Immutable sources, units, validation, calculators, risk bands, ownership, jobs, map geometry, rotation constraints | domain |
| application | Evaluation, document/session history, workspace/project lifecycle, selection/catalog operations, PLOT/JROT use cases and ports | application, domain |
| infrastructure | Strict codecs, parameterized transactional SQLite, native snapshots and source-bound calculations, resources/settings/CSV, direct HiGHS adapter | infrastructure, application, domain, resources |
| presentation | Typed projections, English/Spanish text, Qt dialogs/tasks/charts, interaction/animation and theme | presentation, application, domain |
| resources | Local icons, models, guides and reference PDF | resources |
| bootstrap | Compose concrete adapters and presenters after QApplication exists | composition root exception |

## Ownership and persistence

`DocumentSession` owns source snapshots, dirty/clean markers and scoped history.
`ProjectWorkspace` owns repository handles, save/discard/cancel and transitions.
Forms collect drafts and call services; they do not run SQL. The native adapter owns explicit transactions and, for integrated editing, a private
in-memory working connection plus the durable baseline connection. Main Save publishes
accepted project data atomically. Failed saves retain editor intent;
new/snapshot publication is exclusive and validates before activation. SQLite
source/history/result/catalog writes commit together where a use case requires it.

Worker assignments and assessment documents are stable identities. Reassignment
does not reattach historical observations. JROT retains exact worker/Job/placement arrangements and resolves each Job's
single current risk set. Source units, saved output units and display preferences are separate.
Each assessment has one replaceable calculation bound to its exact saved
inputs. Save retains calculator precision; display rounding and gauge clipping
belong to presentation. Saving changed inputs invalidates the old result atomically;
Calculate/Save replaces it. New/native files contain no imported observation store
or original SQLite archive. Original source files remain unchanged outside them.
CR003 body-unit normalization and established ST formula conventions remain intact.
Copy/Move preserves the sole matching result without recalculation. There is one assessment per assignment/tool; there is no assessment-version history.

Format 17 removes dated incident/event attributes from recurring Shift metadata.
The domain rejects them; external conversion removes them before native validation,
with no runtime legacy decoding or new SQL tables. Exact format-14/15/16 sources and
results are retained.

## Replaceable integrations

`BodyRenderer` exchanges immutable state/reset/close operations. Qt/VTK actors
never enter domain/application. VTK imports stay in the reviewed `vtk_*` rendering
adapter, which owns assets, anatomical parts, camera, motion and native teardown.
Replacing VTK later is an adapter/UI task, not a calculator/storage rewrite.
The shared risk gauge and damage bar are custom presentation components; fixed
task headers synchronize actual column widths instead of space-padded strings.

Pure rotation preparation produces plain constraints/risks. The optimizer port
is implemented by `HighsRotationOptimizer` for the original workflow and
`HighsRotationPlanner` for guided rotations. Both use the approved highspy1.11.0
API directly for every tool subset; no solver switch, PuLP or bundled CBC remains;
Qt worker orchestration owns cancellation/previews and never changes source from
a solver thread. Acceptance requires an explicit user action; guided results use Keep optimization result.
Only the main Save publishes accepted changes. Packaging and platform setup are described in installation.md.

## Standards and evidence

See coding_standards.md and api_contracts.md for names, docstrings, units, errors,
numeric policy and extensibility. AST gates enforce layer direction, portable core
imports and VTK confinement; they do not replace semantic/visual/scientific review.
Initial languages are English/Spanish with stable language/message identities;
user data is literal and never translated. Future mobile UI work can reuse the
core/ports but requires its own presentation layer; no mobile work is in scope.



## Analysis history extension

PLOT now combines immutable PlotEditState geometry, PlotFilterState controls and
applied selection in one DocumentSession; canonical bounds retain disabled and
unpaired values. RotationEditState includes displayed risk tool and pending
scope controls separately from the applied pool. Main assessment Qt actions
route platform shortcuts to native typing or existing application history.
No global database undo, new storage format or unified Save is introduced.
See plot_history.md and jrot_history.md for lifetime and persistence boundaries.

## Optional external migration utility

`tools/project_migration/ergotools_migration` owns original-schema reading,
reconciliation and earlier full native format upgrades. Application code never
imports it; `ExternalProjectMigration` checks container/envelope headers and invokes
an optional external process. The wheel contains none of the tool. Native use,
Save As and Backup require no original folders, archive or converter.

Format 15 / result envelope 3 stores one calculated result per assessment.
Conversion recalculates every version from saved inputs using the same evaluator
as interactive Calculate, retaining intrinsic original formula rounding but no
additional save-time rounding/clipping. Prior formats 12/13 and full formats 8–11
with obsolete result envelopes are upgraded externally. Their old outputs/archive
tables are discarded in a memory copy, never decoded into a second result store.
Invalid outcomes have no fabricated result; partial grid results retain explicit
status/issues. Older diagnostic native source formats retain their supported
capabilities; full-format conversion accepts formats 8–13.

Manually authored job-risk estimates and frozen approved profile references are
distinct source data, not duplicate computed assessment results; they remain intact.
PLOT/export use the sole matching saved result. If no result exists, the existing
read-only persisted-input evaluation path computes a temporary summary without
writing another result. Guided conversion owns a temporary-directory lifetime in the desktop.
The localized consent dialog invokes only the injected process callback. Workspace
switch accepts remember=False to exclude temporary paths; first Save As publishes
the complete native snapshot and then releases temporary backing. Repository/source
ownership and source-bound calculation contracts remain unchanged.

## Assessment browsing and retained tool drafts

`AssessmentNavigation` resolves worker/tool saved contexts with exact assignment IDs,
saved history and per-user remembered contexts. It does not create records or import Qt
or SQL. `ProjectWorkspace` retains the tab sessions behind its one active editing
session, resolves all dirty drafts at worker/context/project departure, and saves edited
previews only after explicit consent. `PreparedSnapshotProject` lets the application
write retained edits to the adapter's private snapshot before exclusive publication.
The native adapter owns cleanup, backup, validation and publication; the main-window
presenter owns status text, the saved-location browser, dialogs and same-Job creation confirmation.


## Project display precision and renderer overlays

DisplayPrecision is an immutable domain value (0–8 decimal places per continuous
input, moment, probability, damage and contribution group). ProjectMetadata carries
it. The optional ProjectPreferencesRepository application port updates display-only
metadata; AssessmentProjectFile owns atomic SQLite storage. Native format 15 accepts
an optional project_display_settings record and supplies defaults when absent.
Sources, calculation results and document history are not rewritten by formatting.

PrecisionLineEdit separates the exact source token from its compact visible value;
unchanged commits/native Undo retain the source, deliberate edits commit user text.
One PreferencesDialog combines user preferences, project display settings and opt-in
confirmed active-assessment reset. Existing application commands own reset/Undo.
BodyViewState transports independent camera focus and all available region colors.
AssessmentNavigation resolves sibling sources by exact assignment and retained edits;
the injected renderer adapter owns actor updates. No other workplace is substituted.


## Anatomical selection and visible local history controls

SelectableBodyRenderer is an optional typed callback capability. The VTK adapter uses
its built-in actor picker only for simple left clicks on visible colored meshes;
neutral anatomy/background and drags do not select. Widget/render coordinate conversion
supports pixel scaling. Candidate clicks retain their press outside VTK until release. Confirmed drags
forward that press once before their first native move; click release queues selection
without starting native camera interaction. Closed adapters ignore callbacks. The desktop maps BodyRegion to existing tool tabs,
retaining validation, edits/context and accepted-selection animation policy.

Main toolbar history routes through AssessmentHistoryActions. PLOT and JROT toolbars
reuse their existing QAction instances, so menus, shortcuts, enablement, text-field
history and solver interlocks share one owner without another Undo stack. Settings and
Help retain menu access. Redo is a package-owned static mirrored asset, not a runtime
transform or dependency. No domain/source/result/project storage policy changes.


## Chronological assessment interaction replay

AssessmentInteractions is an application-layer, project-session timeline of exact
AssessmentView selections and intervals in existing DocumentSession source history.
AssessmentHistoryActions observes accepted changes, routes focused text Undo locally,
and restores worker/tool/context through ordinary AssessmentNavigation/ProjectWorkspace
services. Replay synchronizes observation baselines without recursively recording itself.
Project departure clears the timeline. Worker/context Save/Discard resolution remains
an explicit source-history boundary; view navigation stays reversible, while discarded
or detached source edits are not resurrected. New accepted operations truncate Redo.

DUET/ST selector signals commit only their own choice immediately and rebind the
presenter context without rebuilding controls inside the signal. Numeric fields use
the same cell boundary on focus departure/Enter. Invalid sibling text remains pending. Calculators, source ownership, unit precision and saved-result policy are
unchanged. Main setup actions use processed Plant/Job icons and share existing callbacks
with Workplace; Export remains in Project. File filters advertise only .ergprj while
adapter schema/format validation continues rejecting unrelated SQLite containers.


## Task viewport restoration, menu sizing and native Properties

Edit-time scrollbar offsets belong to AssessmentHistoryActions in the presentation
layer, keyed to application InteractionStep values; no widget/scroll state enters
AssessmentInteractions, domain sources or project persistence. Pending numeric edits
retain their initial viewport until accepted. Source replay clears retiring focus,
restores both offsets, then makes one owned zero-delay layout-settle pass guarded by
current document/revision and native widget lifetime. Removed history entries release
their GUI snapshots. Task frames publish minimum/maximum layout geometry so fifty-row
and shorter replacements update QScrollArea ranges without focus chasing the last row.

MenuIconStyle is an idempotently installed Qt proxy, overriding PM_SmallIconSize only
for QMenu by approximately 20%; all other style metrics delegate to the matching base.
QApplication owns the proxy and its fresh base, avoiding deletion/ownership conflicts.
ProjectPropertiesDialog displays supplied native metadata/path through themed read-only
fields and plain-text description. It reads no SQL, infers no filesystem timestamps,
shows no sidecar folders, and edits neither pending assessment input nor preferences.
See icon_editing.md for authoritative package-resource paths and asset review rules.


## Explicit worker assignment editing

The desktop row actions call the pure application change_worker_assignment operation,
then one expected-value ProjectWorkspace.replace_jobs commit. Immutable current rows
are closed and retained; a replacement uses a new identity even if its workplace is
different. Historical assessment ownership never moves. Duplicate occupied destination
contexts are rejected. Confirmation/local text/processed icons stay in presentation;
SQL and protected-reference validation stay in the existing repository adapter. See
assignment_actions.md for immediate-save, pending-dropdown and JROT extension boundaries.


## Worker ownership and removed assessment versions — format 16

AssignmentAssessment contains document_id, worker_id, optional assignment_id and kind.
AssessmentHistory represents an ordered unique ownership catalog, including assessments whose worker
assignment has ended; it contains no assessment version/status/currentness state. The
name records assignment history, not alternate assessment versions. The SQLite table is
assessment_ownership, with unique assigned and standalone owners, a stable document key
and an optional deferred foreign key to worker_assignments. Source/result payloads remain separate
scientific inputs/outputs, each bound to that exact document. The unused full-project
assessment_bindings table is absent. Hierarchy validation traverses actual ownership and
assignment rows, rejecting missing worker/workplace references. Foreign keys are enabled
on owned repository connections; unique ownership is also enforced by immutable domain
construction. Version creation/current-selection methods, port capability and UI handlers
are removed, including menu text and export columns. File/codec compatibility markers remain distinct. Jobs have one current risk set,
without a profile-version lifecycle.

The external tool upgrades earlier full formats 8–15. Format-14/15 upgrades preserve all
unrelated SQLite rows/payloads and JROT timestamps exactly; older result-envelope upgrades
retain their approved recalculation policy. Conversion stages privately, validates and
publishes exclusively. It rejects populated duplicate assessment groups before mutation;
only a proven empty noncurrent duplicate LiFFT draft with no entered values/result may
be removed. Test projects are updated in place at their established
test_projects/native paths; obsolete copies are not retained alongside them. No runtime compatibility table or hidden assessment-version API is retained.

## Current optional organization contract

Native format 16 supports direct worker assessment ownership with an optional real
workplace assignment. Jobs are optional for PLOT Individual analysis; JROT All Jobs
remains independent of individual assessments and organization. New projects create
no artificial defaults or orphan assessment. Existing Default names are retained.
See ownership, UI, migration and rollback.


## Personal assessment-gauge marker preferences

GaugeMarkerSettings is an immutable application preference contract (visibility
and percentage-point spacing), independent of scientific domain calculations.
UserSettings owns it; the JSON adapter introduced markers in personal format 5 and
currently writes format 7. Formats 1-6 remain readable without writes on load; marker
defaults apply before format 5 and result-animation defaults apply before format 7. Native project format 16
and project databases are unchanged. Gauge annotations use existing presentation
band limits and preserve the arc/needle geometry and animated scale engine.
The main desktop host saves right-click changes before applying them; Settings
uses its existing Apply/Cancel/input-resolution policy. Presentation widgets never
access preference files themselves. RiskGauge owns one painter/menu implementation with main and compact PLOT profiles;
PlotRiskGauge is only a compatibility adapter. Bootstrap injects the personal settings
port into PLOT, which persists before updating all three gauges. The main host reloads
appearance after the modal closes. PreferencesDialog owns a tree and retained page
drafts; the host still owns Apply, cancellation and reset consent. Owned forms/prompts
share scoped dialog styling; system file/color/font selectors use platform defaults,
without native-dialog overrides or custom file browsing. See
settings_shared_gauge_acceptance.md; gauge_markers_acceptance.md records the first slice.

## Owner-directed PLOT/JROT layout follow-up

History adapters retain their QAction/shortcut/focus routing and expose two title-row
buttons; they no longer construct menu bars/toolbars. RotationForm exposes its existing
title row and PlotWindow owns its localized title row. PLOT sizing propagates real rail
and wrapped-chart minima through a non-collapsible splitter and root minimum constraint;
PlotToolsOverview recomputes its minimum on width/mode changes. Standalone context
navigation is a separate footer action; it never becomes a workplace node or persisted
assignment. See plot_layout_followup_acceptance.md for the approved visual changes.


## Current single project Save and chronological history

Owner-approved 2026-10-18. The integrated bootstrap enables private editing through
EditingRepository; native stores use an in-memory working connection. All existing
validation and transaction ownership remains in adapters. ProjectEditingSession reuses
DocumentSession for opaque native checkpoints and immutable accepted editor state.
Main Save is the sole durable commit, including workers/organization/Jobs/assessments/
PLOT and complete JROT schemes. Closing editors retains valid session edits. Shared
Qt action adapters expose the same cursor, native typing and removal confirmations.
Viewport caches remain presentation-only. No new schema/table/dependency is added.
This supersedes earlier scoped/local-save history boundaries in this document.
See [contracts and lifecycle](single_project_save.md).


Task capacity remains source-local per worker/tool/context. Pure count commands validate
an unchanged retained prefix and fresh appended defaults; the shared document/session
history owns truncation replay. Domain task-presence rules distinguish unused selectors
from entered measurements; grid evaluation filters unused-slot completeness issues
without mutating scientific sources or changing strict validation APIs. Settings merely
projects the current ownership and requests a validated count through existing presenters.


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

Save availability is a pure presentation projection of ProjectWorkspace.has_unsaved_changes, temporary first-Save state and pending task text. LifftWindow.refresh_save_controls synchronizes the existing command button, toolbar action and menu action without accepting input or accessing catalogue authorities. AssessmentHistoryActions registers a weak session notification for management edits and refreshes availability on pending task changes. Diagnostic sessions retain their existing Save policy. No second dirty flag or persistence path is introduced.

Shared project history is bounded by UserSettings.undo_limit (25 by default, integer 1-50). ProjectWorkspace reads this personal policy when activating ProjectEditingSession; Settings Apply updates the live session and notifies every borrowing editor. DocumentSession.set_history_limit is the existing generic timeline capacity boundary: it keeps current state and stable revision IDs, gives preceding Undo priority, and retains Redo only within remaining capacity. The saved-data baseline is held independently by ProjectEditingSession, so pruning never changes project dirt or publishes data. Generic diagnostic document sessions remain unlimited unless explicitly configured. No project column, table or version stores this preference.

The owner-approved Clear assessment action replaces the separate assessment Reset/trash controls. LifftWindow owns one localized confirmation and dispatches only to the active tool presenter's existing reversible input replacement. Panels own their single Clear control and inject the host operation; isolated diagnostic panels retain a local command fallback. Ownership, task IDs/count and original units survive. Private staging uses the existing shared session with assessment.clear as its operation label; no source deletion, automatic calculation, durable Save, extra history or new assessment is introduced.


## Organization form clocks and pending history

OrganizationDialog uses standard Qt validators for optional Plant/Shift HH:mm
controls. Domain organization attributes and native serialization stay unchanged.
Its pending callback and dynamic text-change subscriptions project valid existing
record drafts into the existing ProjectHistoryActions, matching Workers. Mouse
replay completes form acceptance; native typing Undo keeps field ownership. No new
application history engine or persistence port is introduced. See single_project_save.md.


## Organization view state during record replay

OrganizationDialog owns transient expansion flags keyed by full location ancestry
and a preferred existing-record identity. Qt items are never retained across model
replacement. Form construction leaves the optional-details widget's chosen state
intact; refresh and internal reselection preserve exact branch flags, including
subtrees temporarily absent because of Delete. Shared replay still restores only
project data through the existing session; view choices add no history or storage.
See single_project_save.md for deletion/reselection and fresh-dialog behavior.


## Standard optional clock adapter

OptionalTimeEdit subclasses Qt QTimeEdit rather than building a clock parser or
custom dropdown layout. It owns only nullable display/value conversion, retained
invalid loaded text and change notification; standard Qt handles keyboard sections,
formatting and stepping. OrganizationDialog validates Shift day intent at its existing
acceptance boundary and serializes only canonical start/end clock attributes. The
following-day checkbox is inferred on load, not persisted as redundant configuration.
Shared history recognizes a focused QTimeEdit's internal native line editor. No
application/domain/storage/dependency change is required; existing organization
view retention is unchanged. See single_project_save.md for exact day-pair rules.

Organization cleanup (format 18): domain metadata enforces ISO opening/creation
dates and whole-minute daily durations in decimal hours. Presentation adapters use
standard Qt calendars and native hour/minute quantities. Shifts in use is a derived
Plant-specific usage label, outside form edits/storage. External conversion removes obsolete
Station attributes and the Plant count before strict validation, never at runtime.


## Workplace-first workflow — 2026-10-19

The shared WorkplaceAssignmentDialog is a pure presentation picker receiving immutable
hierarchy and Job snapshots. Worker Management composes existing pure assignment
transitions; main association calls ProjectWorkspace.associate_assessment_at_workplace
through the optional WorkplaceAssociationRepository port. The native adapter owns one
transaction for assignment reuse/creation and ownership binding, with rollback and one
outer shared-history notification. No Qt, clock or SQL enters the application port;
the caller injects the effective date. Source/result rows are not rewritten.


## Explicit contextual assessment creation — 2026-10-19

Worker Management returns worker selection only; its accepted workplace edits never
request assessment navigation/creation on close. AssessmentContextDialog presents
immutable existing/missing owner state and Open/Create assessment intent for the exact
worker/tool/assignment. It performs no writes. The main host preserves pending-input
resolution and same-Job consent, resolves retained drafts, refreshes catalog authority,
and creates only a still-missing owner through AssignmentSelector and ProjectWorkspace.
Existing transactional native creation and shared project history own the mutation.
AssessmentNavigation then activates that exact owner. Main Save remains the only durable
publication. Standalone association, scientific sources/results, schema and dependencies
are unchanged. See explicit_context_creation_acceptance.md.

## Current Job calculator boundary — native 19

Domain JobRiskValues/JobRiskMeasurement/JobTaskResult own one immutable current tool set,
optional exact task source and matching per-task outputs. Application job_calculation
uses the existing scientific evaluator and copies only source-matched complete results.
Job Management owns task-first tool tabs, optional direct-entry fields and one selected-tool
result panel derived from the actual main ResultsSidebar, with its key metrics and an
additional legend. Missing Job tools show one presentation-only blank starter in task mode; browsing
cannot create persisted source rows. Direct mode has no task template. The first cell
edit accepts the template; + Task appends to it. Clearing or removing the last stored
source restores the starter. Assessment controls shares the actual precision editors and
descriptive native selectors between main panels and Job grids. JobTaskEditor uses the
main column order, sticky headers, display precision and original ST keyboard order;
ToolResultSummary is the same inline summary component as the main panels.
AssessmentTaskGrid now owns the common row/control/header/scroll implementation for
all main tool panels, Job tools and compact copy previews. AssessmentEditorSection
and AssessmentActionRow compose shared content/totals/actions, with context selection
in Main and task-count controls in Jobs. The thin JobTaskEditor binding accepts Job
source edits; main panels retain presenter contexts, unit conversion and validation.
AssessmentCellEdit transports immutable task/field/exact-token intent; the grid does
not accept canonical source state, calculate, save or create a history stack. Main
result formatting remains presenter-specific to preserve existing source/display units.
See shared_assessment_editor.md for lifecycle, configuration and acceptance contracts.
JobDirectValues occupies the existing Job summary damage cell in direct mode; its
preview signal updates the single probability row without accepting typing. It retains
exact stored measurements and derives deliberately changed
manual values through the established tool functions. Worker/Job copying routes through
existing workspace mutations with replacement consent and shared project history.
No formulas, SQL or ownership links are introduced by the view.
JobValuePicker renders immutable CopySource/CopyCandidate snapshots. JobAssessmentDialog
and JobCopyDialog adapt existing read-only catalogs, then revalidate the selected identity
on explicit Copy. Filtering/navigation/Cancel never mutate source or destination. A disclosure renders
selected source tasks through JobTaskCopyDetails embedded as a spanning child tree
row. Its compact read-only JobTaskEditor shows populated rows with original task
numbers, bounded row-dependent height and copy-only identity checkboxes. All/None
controls share the Task # header; blank capacity is not offered for selection. Explicit partial Copy calls application copy_job_tasks: full selections
retain exact results; calculated subsets use the existing evaluator; blank/uncalculated
subsets retain source inputs without fabricated outputs. Source units/order/convention
remain exact and source identity is revalidated before accepting the copy. AlphabetNavigation fills the
related selector width and uses a modest main-sized 16-pixel hover preview.
secondary_history_controls shares the adjacent icon/caption button presentation across
secondary windows; existing action owners retain shortcuts, native typing, pending
acceptance, solver blocking and shared replay. The main toolbar is unchanged.
JobCalculationSummary and JobResultPanel share the existing tool palette, RiskGauge and
DamageScale; UI grouping and segmented input modes introduce no storage or history layer.
The worker picker reads standalone/assigned assessments without navigating or linking them.
Infrastructure owns strict JSON/source codecs, one Job/tool SQL row and atomic updates.
JROT draft refresh runs in the application layer both on reopening and at main Save;
PLOT reads current values on Apply/restoration. No dependency, solver or formula changes.


## Normal and compatibility JROT presentation

Normal toolbar/Tools JROT composes JrotDialog over shared project/history services.
Compatibility-only UI adapters use legacy_jrot_* modules and a separately enabled Legacy
menu. Both Legacy and Developer visibility default off and are session-only, independent
switches. Developer currently has no installed experimental tools. The disposable scratch
runtime/model and its sample mutation paths have been removed; normal opening creates no
workers, Jobs, scenario defaults or sample data. Prior archives retain historical code.
Existing calculator, optimizer, storage and application/domain modules remain shared and
neutral. An exact presentation-path allowlist in the architecture gate permits these named
compatibility views without admitting old-schema converter readers into the application.

Job tool selection is retained as the immutable session-only `jobs.tool` editor value
in ProjectEditingSession. A completed tab change is a chronological view action;
pending data is accepted first, replay restores the tool under signal guards, and
view-only navigation does not change project dirty state or native storage.

## Completed-input automatic calculation and personal display animation

Main task panels emit input_committed only after a changed, validated cell edit.
Bulk form acceptance retains its existing Save/creation-consent owner and does not
invoke automatic staging. The replay preparer explicitly calculates newly accepted
pending input before Undo, so Redo restores the completed input and its result. The
main host invokes its existing evaluator; only COMPLETE automatic outcomes are
retained. Missing/invalid started rows clear obsolete automatic display, while explicit
Calculate retains its established partial-review behavior. ProjectWorkspace's explicit
stage_calculation automatic option persists the source-matched output into private
state and synchronizes the current input checkpoint, without adding a Calculate action.
Source typing and result display never write the durable file. Shared Undo/Redo restores
inputs and their matching outputs together; exact units and ST conventions are retained.
Job automatic calculation uses the same saved-result evaluator in application
job_calculation; the source and its complete output are accepted by one existing Job
mutation. Viewing an existing source or copying retained results does not recalculate it.

UserSettings format 7 adds independent strict booleans for risk-gauge and cumulative-
damage animation. Defaults retain the old animated display, and loading earlier
personal versions never rewrites them. No native project/schema migration is involved.
result_animation_preferences applies injected choices to an explicitly owned widget
subtree; it performs no settings I/O or global window discovery. The main/Job/PLOT
composition owners supply preferences. Disabling a scale settles its displayed value
at the existing target; it never changes calculator output. Avatar animation retains
its original separate renderer capability, grouped beside these controls in Settings.


Job navigation retains the selected real Job ID in the shared project session under
jobs.selection. Dropdown, navigation arrows and exact-ID search converge on load_job,
which accepts the previous Job's pending values before recording job.selection as a
nonpersistent view action. Replay restores both jobs.selection and jobs.tool before
rebinding actual catalogs. Initial display and selection caused by record creation or
deletion project into their existing checkpoints, adding no extra navigation action.
Opening/selecting alone does not write the file or mark project data dirty.


Job Management projects the currently edited Job ID/name into the task-area heading
without accepting metadata or recording history. Copy-picker alphabet availability is
computed from its detached source catalog independently of the current letter filter;
absent initials are disabled, matching the main worker navigator's availability rule.
Search and explicit Copy/source revalidation remain unchanged.


ProjectCaption retains exact localized project/status text and a complete tooltip, but
uses content-independent size hints and paint-time fitting beneath the existing brand.
It prefers one/two lines at the normal font, then readable reduction and extreme-only
middle elision. Main toolbar Minimum sizing reserves actual action hints. Text fitting
never feeds shortened content back into project metadata/status or affects Undo/Save.


## Worker controls and nested Assessment browser — 2026-10-29

MainNavigation keeps selector/order/navigation/actions on its compact first row and the
shared adaptive alphabet below. Standalone and the eliding current-selection summary
live in the worker area. ExpandableSection owns only a clipped presentation widget and
a 190ms sine-eased maximum-height animation. It grows the same worker frame around the
full-width browser below the alphabet. User toggles animate from the current height,
including rapid reversal; project loading and history restoration settle immediately.
The worker area uses fixed 36px/28px rows, a 65px inner height and a painted backing. Disclosure projects visibility/history/Save/brand status only; it never repopulates selectors or initials. Repeated refreshes do not restart motion. Context visibility does not select data or
validate pending task input. The existing project context_expanded preference retains
explicit choices; missing/NULL now defaults collapsed. No new persistence is introduced.
The integrated BodyRegionPanel retains its 220px minimum and 400px preferred viewport.

AssessmentNavigation.select_worker_default is the main worker-control policy:
current-tool standalone first, otherwise the exact alphabetically first saved workplace
owner, otherwise a deferred standalone preview. It ignores remembered paths for this
operation while preserving explicit selection/tool-switch APIs and shared history.
Only saved sources qualify: an empty active assignment cannot shadow an older saved
owner at the same path. Navigation and project opening create no assessment records.

AssessmentLocationBrowser projects only current-worker/current-tool saved sources.
Its five cascading selectors retain literal path values. Headings count relevant unique
entries, excluding placeholders. Station carries the selected source probability/color;
other stations show ranges for varying outputs, without invented averages. Shift has
only its identity. Job has a separate read-only cell, or an exact-document selector
when several saved owners share the complete path. Historical status/dates and literal
Job ID/name remain distinct from Shift. Programmatic population blocks signals;
rejected pending input restores the accepted path. A subtle dynamic-property outline
identifies the actual source, independently of categorical risk colors. Availability and
selection summaries remain visible when the browser is hidden or standalone is open.

Transfer is the single Copy/Move workflow. TransferRequest permits a None source
assignment only with an explicit source_worker_id. The pure planner resolves that
worker's standalone tool, or the exact assigned source; cross-worker None ownership
cannot be confused. Existing transactional source/result transfer and shared history
are reused. Copy preserves the source; Move removes only selected sources after all
inserts succeed. No new schema or scientific calculation is involved. The redundant
multi-copy dialog, copy port/planner/repository method and main action are removed.

### PLOT map occurrence and navigation contracts (2026-10-27)

All three map modes project the same applied worker-assignment rows, visibility,
size/scale and original-image coordinates. The Job key tag changes paint only: both
MarkerKey tags carry an assignment ID, never a placement ID. Job-only squares use
current Job risk and IDs; missing Job evidence is neutral/dashed. There are no
fabricated origin points or Job-specific station-anchor/fan-out edits. Geometry edits
use the existing assignment position application port, retaining original station
anchor seeding semantics. No schema or calculation change is required.

Job charts/outcome metrics continue to describe the scoped Job placement catalog;
explicit map-square/unmapped-assignment counts distinguish those populations.
PlotResultSelector/PlotResultPicker consume detached applied rows and publish exact
assignment selections through a searchable workplace/shift/Job tree. They do not
query storage or create edit history. The retired worker-only picker is removed.

PlotLayoutCanvas owns local magnifier/Pan modes, cursors, cue, bounded pointer zoom
and resize-stable fit/center. Gestures are consumed before marker dragging. Hidden
scroll offsets implement panning without visible plant-image scrollbars. Completed navigation gestures enter session-only history without writing or altering
image-pixel geometry. Accepted
filter state enters shared project history after its local filter command, preventing
the next geometry gesture from accidentally bundling a preceding risk-view change.


PLOT zoom clarification (2026-10-28): the canvas fitted signal and fitted_scale
property expose the unzoomed image fit. Marker initial dimensions normalize to that
baseline; user magnification remains in the graphics-view transform and scales image,
glyphs, borders and labels together. Recreated markers use the same baseline even
while zoomed. Stored coordinates and individual symbol multipliers are unchanged.


PLOT persistent-tool/history clarification (2026-10-28): cursor tool choice is local;
completed zoom, pan, Fit and opacity gestures publish validated immutable
PlotNavigationState values. PlotEditState holds them alongside geometry/filters. The
existing map/project DocumentSession engines record and replay those views; no second
Qt undo stack or navigation SQL is introduced. The first gesture seeds its previous
view without an extra action. Automatic resize/fit projection is not an edit. Replays
retain the current cursor tool, apply original-image centers and relative magnification,
and suppress nested commands. A plant change invalidates the prior plant's view.
Navigation stays nonpersistent in ProjectEditingSession, so it does not dirty the file.

Integrated Cancel movement retains a view-local previous assignment marker for each
completed move, restores the selected marker as one shared reversible operation, and
clears the affordance on dataset/replay reconstruction. Coordinate drafts can instead
be discarded. Post-acceptance refresh projects final flags after synchronous model
acceptance. Diagnostic explicit-save cancellation still restores its saved baseline.
Job chart labels are identities only; overview map counts include all visible
occurrences of the selected Job, independent of scoped placement summary weighting.


PLOT Locate/outline clarification (2026-10-28): Individual worker glyphs share the
Comparison navy edge without changing shape or risk fill. The common Locate canvas
helper centers on the marker bounds using Qt image-edge clamping and retains relative
zoom/tool choice. It publishes the completed viewport change through existing
session-only navigation history; no assignment geometry or schema is changed.


PLOT zoom ceiling (2026-10-28): MAX_PLOT_ZOOM in the application view-history
contract is 3.0 (300% of fitted image). Both immutable snapshot validation and
canvas click/wheel clamping use this single value. It changes session view behavior
only; no project schema, stored geometry or scientific formula changes.


PLOT zoom-controls clarification (2026-10-28): the authoritative ceiling supersedes
300% and is now MAX_PLOT_ZOOM = 4.0 (400% of fitted image). Zoom Out/Pan disable at
fit; direct requests cannot arm them there, and returning to fit clears either active
mode. Both magnifier tooltips project current relative zoom and cap through existing
navigation/fit signals, including replay. This remains session-only view behavior.


## Explicit workplace assessment creation/replacement — 2026-10-29

The browser's Add action remains available with no saved workplace sources, while its
location selectors remain empty/disabled. LifftWindow reuses WorkplaceAssignmentDialog
in reuse-existing mode for all real hierarchy stations/project shifts, with an optional
compatible Job. The current worker/tool remain fixed. Existing destinations need a
No-default replace confirmation. Declining changes nothing; Yes supplies a new
blank 15-task source. Cancel and invalid pending input do not change ownership.

WorkplaceAssessmentRepository is an optional typed application port. ProjectWorkspace
stages retained drafts and calls add_workplace_assessment with the exact expected
existing document ID (None requires absence). The SQLite adapter atomically validates
membership, reuses/creates the active assignment, inserts blank ownership/source or
replaces the existing source at the same ID, and clears only that source's result.
Any failure rolls everything back. The operation emits one shared project edit;
selection remains an ordinary chronological navigation step. Retained target sessions
reload the blank source so old cached data cannot overwrite the replacement. Empty
sources save/reopen without fabricated results. Existing native schema/format,
scientific calculators, standalone sources and unrelated records remain unchanged.


The same-Job/different-workplace creation warning is retained through the shared
pre-insertion duplicate-workplace query. It works even before a new assignment exists;
declining creates nothing. Existing historical owners remain historical observations:
Add targets the active assignment at the chosen workplace, not an unrelated older Job.


## Static worker-strip painting and picker evidence — 2026-10-29

Full rectangle traces confirm the worker controls already keep the same X/Y/width/
height while the lower browser animates. BufferedControls addresses remaining repaint
churn, not source/navigation geometry: it draws one device-aware pixmap in a temporary
mouse-transparent QLabel above the original live controls. Animation Running freezes;
Stopped releases the pixmap. Reversal renews it, real resizing thaws it, and ordinary
MainNavigation.update_state settles the animation/thaws before changing source/tool/
language so data never remains hidden behind a stale snapshot. No timers, copied input
controls, persistence or native-window hacks are introduced. The buffered strip remains
65px; group animation stays 190ms with existing visibility/history policy.

The disclosure and summary now share a horizontal layout across the buttons' row,
right-aligning the disclosure and giving the label all remaining space. Hierarchy/Job
columns use name-weighted stretches; Shift measures identifiers within a compact bound.
ContextValueLabel paints inside contentsRect, allowing the read-only Job's leading inset
to align with the heading's icon/text structure without affecting zero-margin callers.

WorkplaceAssignmentDialog optionally accepts immutable WorkplaceAssessmentPreview rows
for the current worker/tool and a tool caption. None retains its original two-column
assignment UI. A supplied tuple enables a third assessment column for the selected
shift: Saved percentage with shared risk color, Saved/Not calculated, New, or Historical.
Only active owners advertise replacement; historical-only evidence stays distinct and
protected. An owned delegate keeps badge colors readable on selection while native
selection remains in the hierarchy/type columns. The hierarchy takes remaining width;
evidence/type columns fit their content. Main Add supplies saved result percentages,
not calculations or source links. The picker remains read-only until existing host
consent and transactional creation/replacement run; no schema/domain/formula changes.


## Shared worker assessment actions

The main tool action row exposes Clear, +/- Task and Calculate; the redundant saved-grid
modal is retired in favor of the existing canonical Find Assessment. Add and Delete
remain explicit controls in the Assessment location browser. Delete selects saved-only
current-worker/tool data and uses ProjectWorkspace's validated exact-document deletion;
the existing SQLite transaction and shared project history own data/Undo. Navigation
falls back to another saved source or a deferred standalone preview. No schema, version
model or scientific formula changes. A single read-only badge delegate renders saved
risk values in Add, Find/Delete and both sides of Transfer. Destination badges follow
worker/shift/tool ownership. Standalone destinations use explicit project/worker
identity; occupied selected tools require replacement consent before the atomic transfer.


Consented Transfer targets (2026-10-29) extend the existing pure TransferRequest/Plan,
not WorkerContext or database ownership tables. StandaloneDestination carries project/
worker identities only. Replacement is explicit/default-off in the domain boundary;
SQLite target deletion/copy/Move-source removal is one transaction. Historical owners
and unselected tools are protected. Removed target session caches are discarded after
success. Main Save/history remains authoritative; active Move selects its new exact
owner. Find ordering and destination badges are presentation changes only.


## Reusable task labels and spreadsheet edits — native 20

This section supersedes earlier native-19 current-format references. `TaskDefinition`
in the domain contains only project-local ID, name and optional description. Existing
immutable tool rows carry optional fallback names/references while retaining independent
numeric inputs, row IDs and ST conventions. `task_has_data` remains the scientific
predicate; `task_has_content` additionally protects label-only rows from silent removal.

`TaskCatalogRepository` is a capability on current project adapters. `ProjectWorkspace`
stages active sources before catalog edits, then uses the existing project history.
`TaskCatalogStore` borrows the project connection and never commits or creates tables on
read. Worker source writes validate references under their transaction; Job requests validate
references before the existing private-store transaction. Definition
renames do not rewrite scientific sources/results. Native 20 adds one catalog table;
That earlier compatibility step supported full formats 8–19; current native 22 conversion
also accepts format 20, as described below. Production has no legacy decoder.

`assessment_clipboard` parses bounded quoted TSV into a fully validated immutable source,
using the shared domain numeric grammar and established unit conversion. It performs no
SQL, Qt operations, formula execution or scientific calculation. The desktop preview owns
column/header mapping, units, decimal choice and cancellation. Its prepared replacement
becomes one guarded source command; the existing host performs automatic calculation and
shared Undo/Redo. IDs/derived columns cannot be pasted. Unmapped cells stay unchanged;
mapped blank cells clear their fields. Appended rows receive fresh source-row IDs.

`AssessmentTaskGrid` owns the common name controls and action toolbar. Name controls are
separate from numeric `inputs` to preserve host field/index contracts. `AssessmentTaskActions`
binds source, catalog, units, validation and acceptance callbacks in Main and Job editors.
Read-only copy previews resolve names through the same catalog and preserve metadata in
independent full/subset copies. The experimental guided JROT editor remains isolated;
adopting this component is a later checkpoint. Formulas, solvers and dependencies do not
change in this slice.


## Relative Shift timing — native 21

`domain.rotation_timing` owns minute intervals, shared breaks, complete work budgets and
pure projection into working clock pieces. Productive minutes must be positive; blocks
cover them exactly once and exclude breaks. Equal budgets divide integer remainders among
earlier blocks. A boundary edit changes only two neighbors and keeps total work constant.
`application.rotation_timing` resolves canonical recurring Shift clocks, validates optional
Shift-owned templates and exposes a guarded repository capability. Clock arithmetic is
planned local time, without calendar/DST or physiological recovery inference.

`RotationTimingStore` strictly decodes one JSON payload per Shift and borrows the project
transaction. `AssessmentProjectFile` validates templates on open and all hierarchy write
paths, records template identities for destructive replay warnings, and stores one edit
under the existing project cursor. Snapshot/Save As/backup retain timing through the same
complete project boundary. Native 21 introduced one initially empty timing table;
external upgrades preserve every preexisting value and never seed a timing or dated run.

`RotationTimingDialog` reuses native optional clock editors, shared secondary history
buttons and the owned dialog palette. Completed valid cells and boundary gestures accept
one edit; incomplete rows/durations remain local and block replay until corrected or
explicitly discarded on close. An unchanged initial preview writes nothing; Use this timing
explicitly accepts it. Count changes rebalance equally, with confirmation for unequal
budgets. Break edits retain unequal prefixes and adjust the last budget; insufficient
remaining work is rejected. Count/mode changes deliberately replace that duration draft.

`RotationTimeline` is a reusable drawing/input widget: mouse movement is preview-only,
release commits the final snapped point once, Escape/click jitter writes nothing, and
keyboard arrows nudge the selected cut. The same immutable model backs clock tables and
geometry. Native Shift controls preserve their standard frames/arrows. No solver, risk
formula or existing rotation codec changes. The current JROT window still uses its
established equal-block model; integrated copied scenario timing belongs to J04/J05 and
weighted solves to J06.


## Named scenario persistence — native 22

RotationInputs/RotationScenario separate incomplete current planning data from an immutable
accepted RotationRun. RotationDraftRow stores explicit unentered matrix cells; complete rows
reuse WorkerRotation. Creation requires a local planned date; current older codec-2 schemes
project to unresolved scenario views without invented dates/timing/runs. Freeze current Job
values and resolved task labels at acceptance; source measurements retain their own units.

Application lifecycle helpers own creation, ordering, read-only fallback, copied Shift timing,
duplication and late-run acceptance. Run freshness compares exact current planning inputs
and numerical Job data, ignoring descriptive task metadata. The run's frozen labels/evidence
never use later live catalogs for their original display. Unknown model versions are readable
but never current supported results. No new optimizer/scientific formula is introduced.

RotationScenarioStore reuses rotation_schemes with a distinct strict tagged codec and guarded
expected-state edits. Project validation covers ordinary hierarchy, combined worker/Job and
Job-catalog paths. Legacy-compatible storage omits guided rows and rejects destructive writes
through stale older selections. The native marker prevents an older format hiding guided data.
Selection stays in optional display state and survives other display changes. SQL snapshots,
shared history and main publication retain all fields atomically. Normal guided JROT composes these ports and shared widgets, with selected-subset/duration/
constraint planning and frozen result comparisons.

## Guided entry composition

JrotDialog owns expected-state scenario/page projection through the shared editing owner.
Pure rotation_entry transformations reshape cells by worker/position identity and expose
destructive consequences before acceptance. JrotJobPanel composes existing shared task,
calculator-result and source-copy widgets; it introduces no calculation formulas. The neutral
WorkflowDrawer and WorkplaceScopePicker are neutral reusable controls.
RotationTimingDialog accepts paired read/write callbacks
when editing an independent scenario copy; its original Shift-template path is unchanged.
Normal JROT opens this composition; Legacy is a separate optional menu. See jrot_guided_entry.md.

## Guided duration-aware planning

RotationPlanningProblem owns pure weighted-score, staffing and hard-rule validation.
RotationPlanningOptimizer is the solver port; HighsRotationPlanner implements the approved
HiGHS stages without changing the older optimizer builders. Preparation freezes current
Job and explicit neighboring-run evidence. An owned Qt worker receives no workspace/write
capability. The GUI keeps successful optimization as a preview; explicit Keep optimization result
rechecks sources before one shared history edit, leaving the original baseline unchanged.
Step 04 generation accepts only the requested proposal and stays on that page; step 07
only optimizes. Every guided optimization subset now minimizes ceilings then ranges,
preserving first-pass bounds. Historical single-pass single-tool evidence remains readable;
new settings identify both objectives without changing score/model interpretation.
Native24/codec2/model2 separate the new contract from retained codec1/model1 evidence.
See jrot_planning.md for objective limits and nonrecursive neighbor qualification.

## Guided comparison boundary

See jrot_comparisons.md. Pure rotation_comparison projects frozen run distributions and
same-context deltas; it has no live catalog or solver dependency. JrotResultTable is shared
by proposal, retained and compact comparison matrices. JrotComparisonPanel projects exact
retained evidence, keeping stale/unsupported status. Summary cards and statistics reuse
one frozen run; optional schedule/worker details never invoke the solver. Rework uses existing
scenario lifecycle/history ports; no schema/codec or alternate Job profile is introduced.
Main Save remains the only project publisher. Legacy cannot overwrite guided payloads.


## Shared file and clipboard inputs

`application.assessment_import` defines profiles, finite string tables, the file-reader
port and strict interpretation into the existing clipboard mapper. Infrastructure's
`SpreadsheetValueReader` owns read-only CSV/TSV/XLSX access and explicit encoding/range
limits. Desktop composition injects it through `AssessmentEditorPreferences`; the same panel
is used by worker/Job/guided JROT actions and embedded Settings. No renderer, calculator,
solver or database dependency enters the portable import core. See
[import contracts](assessment_import.md).


## Personal editor presentation and visual timing

`AssessmentEditorPreferences` now owns explicit per-host import and column preference
composition; it replaces the narrower import-service name. Personal column changes use
owned Qt signals and never enter project history. The pure optional-column contract lives
in application; the same grid supplies Settings previews and real editor presentation.

`rotation_timing_actions` prepares complete split/join/remove/break proposals against the
existing minute model. Timeline gestures remain preview-only until release and use the
same acceptance ports and shared history as manual clocks/durations. Editor proposals now
require uninterrupted blocks and split work at breaks. Confirmed equalization moves pauses
to block boundaries while preserving names/durations; the stored compatible model remains
unchanged. No
schema, solver or scientific formula changes are required.

TaskNameDialog manages existing project definitions through the workspace catalog port. It has no SQL, independent history or Save. Shared measured AssessmentToolTabs reserve semibold caption/icon geometry and allow horizontal compression/scrolling without clipping selected tool names or displacing result panels.

## Uniform segment editor update — 2026-11-01

The current editor uses application.rotation_segments for both work and pauses. Removal extends immediate neighbors (sole neighbor at an edge, half to each inside). It may extend breaks; the host confirms reduced work time. Move applies to both types with local translation or whole-segment reordering; all interior boundaries resize neighbors. Coordinated equal/count edits preserve type totals and honor both equality choices; Equal breaks shares the existing pause budget. Positive-budget impossibilities reject without implicit deletion or extra work blocks. Break equality is inferred from saved durations, not a new stored field. Both tables have matching controls and keep full shift coverage. This supersedes earlier editor statements requiring removal of a break before removing adjacent work; explicit Join still preserves intervening intervals. Existing expected-state/scenario consent/history and native24 remain unchanged.

## Rotation validation cost

Rotation-reference validation reuses one validated hierarchy snapshot and one current
Job catalog per pass. Reading a hierarchy itself validates saved feature references,
including rotations; rereading it for every rotation would multiply whole-catalog work.
The native adapter validates every record against the same transaction-local snapshots.
It retains no validation cache across edits, source changes or Undo/Redo. The catalog
scaling regression measures SQL work for five and 25 plans and still rejects a corrupt
reference in the last plan. Numeric/solver behavior and native schema are unchanged.

## Visual preferences and display reports

See [Settings previews and diagnostics](settings_previews_and_diagnostics.md) for the
reused gauge/bar controls, packaged avatar recording, launch flags, per-OS report
locations and read-only DPI observation. Reporting defaults on for Windows/macOS
and off for Linux; it never changes the platform scaling policy or project format.


## Pasted-name acceptance

The shared assessment action controller passes only the validated input rectangle and
mapped/included name-row identities to `ProjectWorkspace.accept_task_paste`. A detached
application plan reuses/creates existing task definitions; a compound project action
combines those catalog entries with worker/Job source acceptance and derived results.
No schema or scientific calculation changes are needed. Failure restores both native
checkpoint and existing live replay observers; one confirmed Undo reverses the batch.
Ordinary local typed names keep their earlier behavior. Main Save publishes accepted
catalog and source edits together. Weak project notifications update reusable choices
in other open editors while preserving unfinished name text.
