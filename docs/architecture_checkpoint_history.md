# Architecture and foundation decisions

The accepted modular-monolith, ports/adapters and desktop MVP design is detailed in [the archived plan](reference/modernization-plan.md). This document records implemented boundaries and outstanding work.

| Layer | Responsibility | Allowed internal dependencies |
|---|---|---|
| domain | Pure data, rules and calculations | domain |
| application | Use cases and adapter contracts | application, domain |
| infrastructure | Resource, storage and solver adapters | infrastructure, application, domain, resources |
| presentation | Views, presenters and display mappings | presentation, application, domain |
| resources | Packaged read-only assets | resources |

A future `ergotools.bootstrap` composition root wires concrete implementations. Domain/application currently allow standard-library imports only, with prohibited platform/I/O mechanisms checked explicitly. These checks are architectural regression guards, not a Python security sandbox; semantic review still checks filesystem access, cycles, global state and ownership.

## Decisions, 2026-09-27

1. The new destination is an independent repository, branch `modernization/foundation`, without a remote or initial commit. This avoids sharing administrative state with the dirty reference checkout. Provenance records the reference commit and a hash manifest of the actual working files, not just HEAD. No legacy code history has been rewritten.
2. The project-local ordinary GIL CPython 3.13.14 and five exact developer-tool versions were explicitly approved, including locked transitive dependencies. No application-library dependency is needed in this slice. Python 3.13.15 was not available through the installed uv manager; no manager/system upgrade was made.
3. Risk category identity is a domain enum. Colors, English display labels and range labels belong to presentation; stable message keys prepare localization. The four existing colors/texts and finite numeric threshold behavior are preserved. The new typed API rejects NaN/infinities with ValueError instead of silently classifying them. This is a documented invalid-input contract change, not scientific validation or approval to alter formulas; reconcile call sites before GUI integration. String-to-number parsing belongs at input boundaries.
4. `BodyRenderer` defines state/reset/close operations using immutable Python values. Qt widgets and VTK actors never cross this boundary. It is an initial contract, not a finished renderer; camera, picking and overlay requirements must be reviewed against real workflows when its adapter is implemented. VTK imports are restricted to modules prefixed `presentation.desktop.rendering.vtk_`.
5. Package resources contain 61 processed PNG icons and 8 anatomical STL models, copied unchanged and hash-verified. Their existing asset names remain stable; snake_case naming applies to Python modules. No visual redesign or GUI window has been implemented.

## Required next foundations

Units, localization catalogs, session state, dirty/save semantics, reversible commands, recent projects/settings and persistence ports remain Stage 1 deliverables. Message keys alone do not implement localization. The rendering contract alone does not establish native packaging compatibility. Design these through small tested use cases before the first complete assessment workflow. Retain metric/imperial behavior after auditing existing conversions; do not introduce silent scientific corrections.

## F2 update — 2026-09-27

The initial model-unit normalization/display policy and four-key English/Spanish risk catalog are implemented and tested; see [audit and decisions](units_localization_audit.md). This supersedes the earlier statement that only message keys exist. Units and localization are still partial: generic quantities, switching, numeric formats and full translated views remain pending. No runtime dependency was introduced. Metric moment behavior is isolated pending scientific review before assessment integration; no physical formula correction was made.

## F3 update — 2026-09-27

`application/session.py` now supplies document-scoped immutable snapshot history, a pure edit-command protocol and synchronous save coordination. See [session/history decisions](session_history.md) for clean-marker behavior, snapshot retention tradeoffs and storage guarantees still required from adapters. This is the in-memory document core, not a complete project/session lifecycle. No dependency or GUI change occurred.

## F4 update — 2026-09-27

The first concrete source document is `domain.assessments.lifft_draft.LifftDraft`; its original units and task identities survive edits and history. Application commands insert, replace and remove tasks with explicit scope and stale-snapshot checks. [LiFFT draft decisions](lifft_draft.md) distinguish missing-input detection from scientific validity and document pending persistence/context mapping. No calculator, unit-switch action or database adapter is implied.

## F5 update — 2026-09-27

The LiFFT draft has a strict version-one JSON codec and a transactional SQLite adapter, documented in [draft storage](draft_storage.md). The caller owns a dedicated connection; creation accepts only an empty database, saves commit before the clean marker changes, and failed writes roll back. This is a separate new draft format, not legacy .ergprj compatibility or full project persistence. No third-party runtime dependency was added.

## F6 update — 2026-09-28

`application.document_lifecycle` owns single-document switching/closing with explicit save/discard/cancel semantics. Target validation precedes release of the current session; failed I/O retains it. See [lifecycle decisions](document_lifecycle.md) for caller-owned connections, dialog/reentrancy boundaries and pending project-level behavior.

## F7 update — 2026-09-28

Application-owned UserSettings separates language/default units and recent locations from assessment state. The Language enum moved into this contract and remains re-exported by presentation.localization. A separate versioned JSON adapter performs same-directory atomic replacement; no real user path is wired yet. See [settings decisions](user_settings.md) for failure semantics, recency policy and platform/UI limits.

## F8 update — 2026-09-28

ProjectMetadata owns stable identity/title/default units. ProjectFile factories own and close a dedicated new-format SQLite connection and reject foreign document keys. An application open wrapper updates recent history after success and reports settings failures separately. See [project-file decisions](project_files.md) for format markers, resource cleanup, creation limits and pending cross-file switching.

## F9 update — 2026-09-28

ProjectWorkspace owns cross-file candidate/active project handles via an application protocol. It validates candidates before saving/releasing the old project, reuses same-file connections, and retains failed cleanup handles for retry. Completed transitions report cleanup/settings warnings separately. [Workspace decisions](project_workspace.md) document ownership, same-location rules and diagnostic/concurrency limitations.

## F10 update — 2026-09-28

Workspace Save preserves history and marks clean only after commit. New uses an injected creator that initializes project metadata and its first source document; candidate postconditions precede activation. Cleanup retries now retain exception type/errno without raw error text. See [Save/New decisions](workspace_save_create.md) for failure ordering, incomplete-file cleanup limits and pending Save As policy.

## F11 update — 2026-09-28

The isolated LiFFT task calculator and frozen result belong to domain; unchanged lookup data has its own domain module. Continuous task colors belong to presentation. Structured validation uses the existing draft issue contract and localized catalogs. [Calculation decisions](lifft_calculation.md) record reference fixtures, exact rounding, explicit invalid-input differences and the scientific/metric integration gate. No assessment aggregation or GUI integration is implied.

## F12 update — 2026-09-28

LiFFT aggregation consumes calculated task snapshots and returns immutable domain summary/contribution records. Explicit row-order addition preserves reference arithmetic across Python versions. Zero-total probability is absent; assessment-specific bounded text and clear-color instructions belong to presentation. [Summary decisions](lifft_summary.md) distinguish reference parity, stale-state correction and pending application/GUI integration. The metric scientific-review gate remains open.

## F13 update — 2026-09-28

Application-level LiFFT preparation binds immutable source/issues to origin session and revision without invoking the model. Shared domain validation serves calculation and all-field issue collection. Freshness checks distinguish undo restoration from reload/new-branch identity; they require the actual active session and are not automatic UI/cache invalidation. [Preparation decisions](lifft_preparation.md) record incomplete-input policy, reference lifetime and unresolved integration gates.

## F14 update — 2026-09-28

DUET task calculation and immutable source/results live in domain; its distinct continuous palette remains presentation-owned. Shared issues/numeric validation now belong to a tool-independent assessments.validation module, with prior LiFFT exports preserved. [DUET decisions](duet_calculation.md) record reference parity, selector input changes and pending assessment workflow migration. No GUI or dependency change occurred.

## F15 update — 2026-09-28

DUET aggregation/display now use immutable model-specific summaries. LiFFT and DUET share sequential damage aggregation and bounded assessment probability formatting; probability expressions, unit metadata and palettes remain model-specific. Prior LiFFT contribution/formatter exports remain aliases. [DUET summary decisions](duet_summary.md) document display precision, zero-state clearing and limited validation-precedence/class-name changes from consolidation. No GUI or persistence integration occurred.

## F16 update — 2026-09-28

DUET now has source draft/history commands, input preparation and typed version-one persistence. Transaction mechanics and strict JSON primitives are shared, while tool-specific codecs and database markers remain separate. Existing LiFFT formats/imports remain compatible. [DUET workflow decisions](duet_workflow.md) document failure recovery, invalid-source storage limits and pending multi-assessment ProjectFile/Workspace integration. No legacy or operational database was changed.

## F17 update — 2026-09-28

AssessmentDraft explicitly unites supported source types; the workspace/repository ownership protocols are generic. Mixed project version two uses tagged model payloads with transactional type-identity checks, while existing version-one files route through their unchanged LiFFT codec/store. Typed edit adapters prevent wrong-model commands. [Mixed-project decisions](mixed_assessment_projects.md) document compatibility, session history boundaries and pending catalog/create/preparation integration. No automatic migration or GUI was added.

## F18 update — 2026-09-28

The optional CatalogProject capability adds immutable persisted entries and exclusive assessment insertion to the owned workspace. Listing is read-only; creation resolves dirty intent, preflights duplicates, saves the old source if requested, then commits insertion before activation. Shared storage checks uniqueness under the write lock. [Catalog decisions](assessment_catalog.md) document saved-count semantics, failure ordering, version-one compatibility and pending GUI/result integration.

## F19 update — 2026-09-28

Mixed-session preparation and AssessmentEvaluator now bind complete DUET/imperial LiFFT results to exact source/session/revision identity. Explicit outcome states distinguish invalid input, scientific-review gating and numeric failure from complete results. Metric LiFFT is blocked at this use-case boundary pending review. [Evaluation decisions](assessment_evaluation.md) document cache lifecycle, failure clearing and caller-owned UI/event responsibilities. No GUI or persistence schema changed.

## F20 update — 2026-09-28

TST now has an isolated typed task/result boundary with explicit direction identities and structured input/overflow errors. Its unrounded model moment and original formula order are preserved. TST/DUET share only the verified-identical presentation palette, retaining separate probability mappings. [TST decisions](tst_calculation.md) document reference provenance and pending metric review, summary and project integration.

## F21 update — 2026-09-28

TST aggregation/display remain isolated, using shared summation and assessment-label policy. Actual-method capture exposed the legacy selector 1/2 swap; its compatibility adapter lives in presentation, while domain direction IDs keep their formula meanings. [TST summary audit](tst_summary.md) corrects the F20 mapping description and requires direction-label plus metric review before live evaluation integration. No UI changed.

## F22 update — 2026-09-29

TST source joins the explicit assessment union, with immutable drafts, model-scoped commands and a strict model-direction codec. Existing tagged mixed storage/catalog/workspace contracts now handle three models without table migration; version-one projects remain LiFFT-only. Mixed evaluation validates TST but returns direction/metric review issues without calculation or results. [TST workflow decisions](tst_workflow.md) record serialization compatibility, transaction recovery and source freshness. No UI or dependency changed.

## F23 update — 2026-09-29

Unit display is an immutable application projection from original LiFFT/TST source, not a persisted source-unit mutation. Centralized model input conversions preserve compatibility factors, missing/signed values and exact same-unit identity, with numeric failure guards. Existing session/revision freshness protects projected views; evaluation gates continue to use source units. [Unit display audit](unit_display.md) records the approved correction to original relabel-only behavior and why F22's proposed source-conversion commands were superseded. GUI and projected-unit editing remain pending.

## F24 update — 2026-09-29

`edit_display_input` applies one deliberately edited projected quantity through the existing LiFFT/TST history commands. Session/revision freshness precedes validation and conversion; exact projected-value re-entry preserves source precision and redo. Source units and untouched fields remain unchanged. [Projected edit contracts](unit_edits.md) document caller responsibility for current display-unit context, rollback/retry evidence and pending locale/GUI boundaries. No scientific model, dependency or schema changed.

## F25 update — 2026-09-29

Explicit decimal grammar and full-precision editor formatting belong to presentation, independent of language/units and OS locale. `edit_display_text` translates one deliberately edited text field through parsing and the existing application conversion/history boundary. [Numeric input contracts](numeric_input.md) document separator ambiguity policy, precision/range limits, invariant persistence and remaining presenter context ownership. No domain formulas, dependency versions, schema or UI changed.

## F26 update — 2026-09-29

`AssessmentEditor` owns immutable projection/decimal edit contexts. Identity plus source freshness rejects obsolete callbacks, including preference toggle-back and equal foreign contexts. Binding invalidates prior interpretation before potentially failing; successful edits release it while invalid/no-op submissions remain retryable. [Edit-context contracts](edit_context.md) define pending-text and lifecycle obligations for the forthcoming desktop adapter. No GUI, dependency or schema changed.

## F27 audit — 2026-09-29

The first Qt desktop slice now has an audited visual contract and exact-version dependency proposal matching the reference Qt stack. Source/style/package evidence is archived; installation awaits owner approval. No GUI, dependency declaration or lockfile changed. See [desktop scope](desktop_first_slice.md) and [dependency proposal](desktop-dependency_proposal.md). VTK remains a subsequent isolated adapter slice.

## F28 update — 2026-09-29

The Qt LiFFT preview is wired through `bootstrap`, an injected workspace/icon/catalog boundary, a widget-independent presenter and a desktop-only window. Explicit Apply/Discard protects uncommitted text; committed history/storage/evaluation use existing services. Eleven Qt tests and native/offscreen inspection cover this slice. Three approved Linux Qt pins were added without altering existing versions. [Desktop report](desktop_preview.md) records visual corrections, launch instructions and limitations. VTK and complete desktop parity remain pending.

## F29 update — 2026-09-30

[Owner final targets](final_targets.md) explicitly distinguish the temporary harness from the final integrated reference-parity UI. Small early fixtures remain appropriate; the comprehensive project is reserved for later copied-data integration validation. Reusable source-bound LiFFT result rows now preserve reference precision/order/colors without widget or layout changes. [Result presentation contracts](lifft_result_presentation.md) document freshness, structural guards and scientific review boundaries.

## F30 update — 2026-09-30

Immutable workplace/worker/assessment identities now express the reference's
exact ownership fields independently of document sessions and widgets. A pure
assignment resolver preserves active assignment/placement eligibility, project
isolation and read-only selection; duplicate active owners fail explicitly.
[Context decisions](assessment_context.md) distinguish reference lookup from
placement-option filtering and document typed-boundary differences. Association
persistence, repository adapters and selector integration remain pending.

## F31 update — 2026-09-30

The optional AssessmentBindings port separates persisted ownership from task
history. Explicitly created project version three adds unique document/context
associations with model/project validation under the write lock. Existing formats
and default creation remain unchanged; no implicit migration occurs.
[Persistence decisions](assessment_binding.md) document idempotency, conflict
rollback, unbound drafts, missing catalog constraints and pending workspace
selection/create-and-bind integration.

## F32 update — 2026-09-30

Workspace context selection now consumes the optional ownership port, validates
both lookup and reverse binding, prepares a target before current save, and
preserves active ownership on failure. Same-document selections retain history;
new targets get clean independent sessions. [Selection decisions](context_selection.md)
document dirty-consent ordering, same-context differences from ID-based switches,
reentrancy protection and pending catalog/presentation integration. No schema or
UI change occurred.

## F33 update — 2026-09-30

WorkCatalog now supplies immutable project selection data and validates exact
worker/station/shift membership. Worker options keep IDs separate from reference
labels; available workplace projection preserves the reference cross product.
[Catalog audit](work_catalog.md) documents ordering/tie policy, space-containing
IDs, station ancestry, empty-parent limitations and pending catalog persistence.
Small synthetic reference fixtures and real binding/workspace tests establish
this boundary without operational data, schema changes or new widgets.

## F34 update — 2026-09-30

WorkHierarchy composes the existing WorkCatalog with explicit plant/section/line
identities, retaining empty parents and validating complete ancestry. Child
queries preserve snapshot order and distinguish absent from empty parents.
[Hierarchy contracts](work_hierarchy.md) record captured reference behavior,
ordering limitations and requirements for atomic, binding-safe persistence.
No schema or widget changed; complete record editing and PLOT metadata are pending.

## F35 update — 2026-09-30

Explicit version-four projects persist ordered WorkHierarchy snapshots with a
strict versioned codec. Catalog replacement and new binding validation share
SQLite write-lock protection; referenced worker/station/shift removal fails
atomically. [Storage decisions](hierarchy_persistence.md) distinguish adapter
referential guards from SQL foreign keys, preserve old formats, and document
pending catalog history/workspace/UI integration. No default creation or UI changed.

## F36 update — 2026-09-30

Workspace-owned hierarchy snapshots now protect refresh/edit callbacks across
project lifetimes. Optional repository replacement compares expected data under
the same write lock as binding-integrity checks. [Lifecycle decisions](workspace_hierarchy.md)
keep catalog commits separate from assessment dirty/history state and document
value-comparison limits, retry semantics and pending editor/create-and-bind work.
No schema, dependency or UI changed.

## F37 update — 2026-09-30

The mixed project repository now composes source insertion and binding under one
write transaction. Explicit transaction-owned adapter helpers retain standalone
operation behavior. Workspace creation optionally accepts context and requires an
atomic capability, with occupied ownership preflight before old-save handling.
[Creation contracts](bound_assessment_creation.md) document rollback, failure ordering,
version compatibility and pending presentation/catalog editor integration.

## F38 update — 2026-09-30

AssessmentSelector publishes immutable catalog views and complete explicit choices,
using exact presenter/workspace snapshot and active-source identities to reject
stale callbacks. Selection and atomic creation delegate to existing lifecycle
services; model checks precede current save. [Presenter contracts](assessment_selection_presenter.md)
document retry behavior and pending Qt selection/text integration. No widget changed.

## F39 update — 2026-10-01

A reusable Qt classified-context chooser now mirrors the active reference dialog,
using injected immutable assignment display records, packaged icons and the tested
selection presenter. Acceptance returns intent for host dirty-text/choice handling,
without hidden I/O or parent-window access. [Dialog evidence](assessment_context_dialog.md)
records native visual corrections and the missing persisted assignment/host wiring.
The temporary harness and main-window geometry remain unchanged.

## F40 update — 2026-10-01

Explicit version-five repositories persist typed job/placement/assignment
snapshots. Transactional replacement and hierarchy guards reject dangling
historical references; public job reads use a single SQLite snapshot.
The widget-independent classified projection preserves assessment eligibility
without job-activity/date filtering. [Persistence contracts](job_catalog_persistence.md)
record exact reference overlap semantics, adapter-enforced relationships and
pending editing/history/workspace integration. Existing formats and widgets
remain unchanged; the default factory still creates version two.

## F41 update — 2026-10-01

The optional JobRepository port and workspace-issued JobSnapshot now govern
interactive job snapshot replacement. Object identity rejects stale callbacks;
the adapter compares expected saved values under its existing write transaction.
Project lifetime controls snapshot ownership without changing assessment history.
[Workspace contracts](workspace_jobs.md) document retry/conflict behavior, independent
hierarchy tokens and pending historical reassignment/chooser integration.
No dependency, schema or visual behavior changed.

## F42 update — 2026-10-01

A pure application assignment transition preserves the reference distinction
between no-op selection, in-place classification and closing/replacing classified
history. Explicit business date and identity inputs avoid hidden clock/storage
coupling. Workspace expected-value replacement supplies atomic commit and current
hierarchy validation. [Transition audit](job_assignment_transitions.md) records
reference fixture evidence and pending batch changes/historical assessment links.
No schema, dependency, scientific or visual behavior changed.

## F43 update — 2026-10-01

Typed batch classification requests now produce one immutable replacement while
preserving closed assignment history and reference metadata semantics. Requests
target original snapshot rows; successor identities cannot collide across a batch.
[Batch audit](job_classification_batches.md) distinguishes this from the single-worker
entry point and records reference captures, atomic commit composition and pending
historical assessment ownership. No schema, dependency or UI change occurred.

## F44 update — 2026-10-01

The domain now models assessment versions and current ownership by assignment/model,
retaining closed assignment history without workplace fallback. Reference table
and index fixtures characterize independent status/currentness and unique version
identities. [Ownership decisions](assessment_history_ownership.md) distinguish this
pure contract from pending historical persistence, source validation and protected
assignment mutation. Existing context bindings and all schemas remain unchanged.

## F45 update — 2026-10-01

Opt-in version-six projects persist assignment-scoped ownership and atomically
compose historical links with draft insertion. An injected job-store guard protects
referenced assignment/placement identities under the existing write lock. Read
validation checks source models and exact assignment membership.
[Storage decisions](assessment_history_persistence.md) document allowed initial
classification, mutable metadata, disabled context-only binding in version six
and pending assignment-aware workspace/selector integration. Existing formats,
dependencies and UI remain unchanged.

## F46 update — 2026-10-01

AssignmentSelection and the optional HistoryRepository port connect historical
ownership to workspace document selection. Closed assignments remain explicitly
addressable while active eligibility stays a presenter responsibility. Existing
consent/load-before-save/revision guards protect the active session.
[Selection contracts](workspace_history_selection.md) record concurrent-access
limits and pending creation/current-version/presenter/UI integration. No schema,
dependency or visual behavior changed.

## F47 update — 2026-10-02

HistoricalProject adds validated preflight and atomic creation to the optional
workspace capability. Preflight precedes old-source save; final constraints remain
transactional and activation follows commit. [Creation contracts](workspace_history_creation.md)
document separate-save failure semantics, explicit version/currentness inputs and
pending presenter/current-version/UI integration. No schema, dependency or visual
behavior changed.

## F48 update — 2026-10-02

AssignmentSelector publishes workspace-owned job views and explicit assignment
requests, checking active eligibility and callback/source freshness before historical
selection or creation. [Presenter contracts](assignment_selection_presenter.md)
record retry semantics, explicit version/currentness inputs, external-change limits
and pending dialog/host integration. No schema, dependency or UI change occurred.

## F49 update — 2026-10-02

The shared classified-context dialog now accepts matching legacy or historical
presenter/catalog capabilities. Historical options derive from the saved job
snapshot and acceptance returns exact assignment intent. [Dialog contracts](assignment_context_dialog.md)
record explicit shift inputs, pending-text ordering, native visual evidence and
remaining host wiring. Existing appearance and older format support are preserved;
no schema, dependency or scientific changes occurred.

## F50 update — 2026-10-02

AssignmentDialogHost composes injected editor decisions with the real modal chooser
and assignment-aware selection. Pending text resolves before snapshots; dialog
acceptance precedes dirty consent. Cleanup and a reentrancy guard cover all exits.
[Host contracts](assignment_dialog_host.md) record real modal/native evidence and
the remaining concrete main-window callback wiring. No schema, dependency or
scientific changes occurred.

## F51 update — 2026-10-02

The temporary LiFFT window now composes AssignmentDialogHost with its concrete
pending-text and dirty-choice handling. A no-I/O repository/workspace capability
flag gates the action to historical projects. Existing worker-picker style and
packaged icons are reused; successful selection rebinds source and clears results.
[Window integration](window_assignment_context.md) records native visual acceptance,
version-six/LiFFT limits and remaining creation/current-version/final UI work.
No schema, dependency or scientific changes occurred.

## F52 update — 2026-10-02

Explicit current-version selection preserves independent status and immutable
assignment/model ownership. The repository compares expected history under its
write lock and atomically clears/sets current flags without changing source data.
[Lifecycle decisions](assessment_current_version.md) distinguish reference schema
constraints from the new explicit adapter operation and document pending workspace/
UI composition. No schema, dependency, UI or scientific changes occurred.

## F53 update — 2026-10-03

Workspace-issued HistorySnapshot identities and the optional mutable history port
guard current-version callbacks across refresh and project lifetimes. Repository
value comparison remains atomic; source editing/activation is separate.
[Management contracts](workspace_history_management.md) document retry and adapter
failure semantics, creation invalidation and pending UI composition. No schema,
dependency, scientific or visual change occurred.

## F54 update — 2026-10-03

The temporary LiFFT window exposes explicit current-version management using
workspace history snapshots and source-revision guards. Currentness changes do
not switch/save the source; version/currentness labels make this visible.
[Window decisions](window_current_version.md) record native visual checks, localization,
reference-scope limits and pending creation/final UI work. No schema, dependency
or scientific formula changed.

## F55 update — 2026-10-03

The temporary LiFFT window composes blank-version creation with explicit
confirmation, dirty consent and stale source/history guards. The existing
transactional creation API persists an empty noncurrent source; currentness
remains a separate decision. [Creation UI contracts](window_blank_version.md)
record validation, native visual evidence and pending first-assessment/worker-job
setup work. No schema, dependency or scientific formula changed.

## F56 update — 2026-10-03

AssignmentDialogHost now shares the modal flow between explicit existing selection
and current version-one creation. The temporary LiFFT window supplies an empty
source in the open source's recorded units. Hierarchy authority is rechecked after
dirty consent, alongside the presenter's job/source guards. Existing preflight
and transactional persistence retain ownership and duplicate protection.
[First-assessment contracts](window_first_assessment.md) document cancellation,
native visual evidence, unit policy and missing empty-project/worker-job setup.
No schema, dependency or scientific formula change occurred.

## F57 update — 2026-10-03

Explicit initialized historical creation validates setup and source ownership
before filesystem writes, then composes existing persistence adapters. It obeys
the current workspace creator interface and preserves recorded units independently
of project defaults. [Setup contract](historical_project_setup.md) documents
exception cleanup versus crash atomicity and pending UI/full-worker integration.
No new schema, dependency, coordinator abstraction or UI control was introduced.

## F58 update — 2026-10-03

Job workplace selections now have a pure transition and a widget-independent
presenter using existing hierarchy/job snapshot authority and atomic replacement.
The source reference's deactivate/reactivate behavior preserves historical owners.
[Workflow contracts](job_workplace_management.md) record deterministic new-ID
allocation, source-edit isolation and pending original-dialog migration.
No new schema, dependency or UI was introduced.

## F59 update — 2026-10-03

The Job workplace dialog now consumes typed presenter state and packaged icons
instead of SQL, filesystem asset lookup and parent-window state discovery.
Original layout and selection behavior are retained. QSignalBlocker separates
programmatic rendering from checkbox intent; a save guard spans modal warnings.
[Dialog contract](job_workplace_dialog.md) records visual comparison evidence,
explicit remembered-shift ownership and pending localization/host integration.
No schema, dependency or scientific formula changed.

## F60 update — 2026-10-03

The workplace dialog consumes explicit language and shared catalog messages.
JobWorkplaceHost owns modal resource lifetime and returns typed saved context
without parent-window state discovery or assessment-save coupling.
[Lifecycle/localization contract](job_workplace_localization.md) records generic
localized error recovery, type-only diagnostics and pending owning-screen wiring.
No schema, dependency or scientific formula changed.

## F61 update — 2026-10-03

Job risk evidence and lifecycle now use immutable typed domain records separate
from worker assessment history. Pure approval/current/retirement transitions
retain source evidence and per-job ownership. [Lifecycle audit](job_risk_lifecycle.md)
records original-code comparisons, explicit finite/type validation, scientific
limits and pending persistence/approved-edit enforcement. No UI, schema,
dependency or scientific formula changed.

## F62 update — 2026-10-03

Risk catalogs now expose explicit draft creation/copy and expected-content editing.
Profile identity and lifecycle cannot change through edit, and non-draft evidence
is protected. [Draft contracts](job_risk_drafts.md) record exact reference provenance/
normalization behavior and required future transactional enforcement. No UI,
schema, dependency or scientific formula changed.

## F63 update — 2026-10-03

JobRiskStore owns read/write transactions on a borrowed connection with same-
connection parent-job access. Explicit lifecycle commands enforce domain rules
under the write lock and verify persisted results before commit.
[Storage decisions](job_risk_persistence.md) record conflict/rollback guarantees
and pending project-format/job-removal integration. Existing formats and
dependencies remain unchanged; no UI or scientific formula changed.

## F64 update — 2026-10-03

Explicit format seven composes risk persistence with historical assessments.
The project adapter validates risk records on open and supplies same-transaction
hierarchy/job access. Job writes compose assessment and profile reference guards.
[Format contract](risk_project_format.md) documents retained old formats, protected
job-removal semantics and pending workspace/UI integration. No dependency,
UI or scientific formula changed.

## F65 update — 2026-10-04

Workspace-issued JobRiskSnapshot identities and the optional JobRiskRepository
port guard profile lifecycle operations across project lifetimes and refreshes.
Expected domain results are compared with adapter outputs; source editing and
management persistence remain independent. [Workspace contracts](workspace_job_risk.md)
record retry/invalidation semantics and pending presenter/UI composition.
No schema, dependency, UI or scientific formula changed.

## F66 update — 2026-10-04

Job Management Save now has a pure form operation and one transaction covering
job fields and profile evidence. The project adapter exposes it through the
existing risk repository contract; workspace publication updates both views
without changing the active assessment session. Targeted job upserts retain
placement/assignment rows. [Save behavior and limits](job_management_save.md)
records original modal behavior, immutable evidence and the outstanding UI work.
There is no new multi-user or background synchronization requirement.

## F67 update — 2026-10-04

Original measurement-table controls now use an explicit typed value boundary,
existing domain calculators and presentation palettes. Qt edit signals are blocked
during loading/derived-result updates. The existing approval operation accepts
optional draft edits and commits them with approval, as the reference button
requires. No new storage schema or generic layer was added. [Component evidence
and remaining window integration](job_risk_table.md).

## F68 update — 2026-10-04

`JobManagementDialog` ports the original layout/evidence controls and calls the
existing workspace operations. It composes `JobRiskTable` and `JobWorkplaceHost`;
SQL remains in infrastructure and scientific functions remain in domain.
Bootstrap provides an explicit modal preview and exclusive synthetic demo factory.
The default LiFFT harness remains available. No schema or dependency was added.
[Runnable behavior and incomplete controls](job_management_preview.md).

## F69 update — 2026-10-04

The existing management/domain, workspace and risk-store interfaces now support
confirmed job deletion. One transaction composes history preflight, risk cascades,
placement removal and assignment unclassification. No new generic layer/schema
was introduced. Profile ordering handles deletion gaps. [Deletion behavior and
future JROT restrictions](job_deletion.md) distinguish retained history protection
from original foreign-key behavior.

## F70 update — 2026-10-04

The Job Management form uses stable entries in the shared desktop language
catalog. Locale and Qt message-button translation are window-local; stored
records and unit identities stay independent. Bootstrap reads saved language
and accepts an explicit temporary preview override. No new dependency/schema
or generic translation framework was introduced. [Behavior and evidence](job_management_language.md).

## F71 update — 2026-10-04

The existing LiFFT preview directly owns the Job Management modal through its
workspace, language, display-unit and packaged-icon dependencies. A private
location/job pair remembers the last stored selection during the window session;
no persistence schema or generic host layer was introduced. The modal exposes a
read-only selected-job identity that excludes unsaved identifier text. Management
writes do not refresh the assessment editor. Profile reload chooses its target
before rendering once. This remains preview integration, not the final main UI.

## F72 update — 2026-10-04

`WorkerManagementDialog` ports the reviewed original visible layout and uses
existing hierarchy, classification and assignment operations. Immutable worker
details use canonical cm/kg body quantities; hierarchy payload v2 retains v1
readability. The optional WorkerRepository command composes existing job writes
and hierarchy replacement in one transaction, with workspace snapshot publication
only after success. SQL remains in infrastructure; presentation owns form text.
The preview consumes explicit assignment intent after modal Close and respects
assessment dirty decisions. Country suggestions require no new dependency.
[Behavior, format consequences and incomplete parity](worker_management.md).

## F73 update — 2026-10-04

`OrganizationDialog` ports the reviewed original organization form. Immutable
organization metadata belongs to the existing `WorkHierarchy`; pure edit commands
compose new snapshots and the existing repository guards saved references. SQL
stays in infrastructure. Hierarchy payload v3 retains v1/v2 reads, without SQL
schema changes. New preview projects explicitly select the already-supported
format seven, closing the synthetic organization → job → worker → assessment UI
workflow. No renderer, dependency or speculative synchronization layer was added.
[Behavior and compatibility](organization_management.md).

## F74 update — 2026-10-04

`LifftTaskPanel` owns the reviewed original grid's widgets and pending text.
`LifftPresenter.commit_grid` parses all cells and reverses display projections
before submitting one `ReplaceLifftInputs` command; that command preserves source
units/task identities and uses existing mixed-session undo. Reset reuses the same
source command. Existing evaluation/storage operations remain unchanged. A shared
reference main-window stylesheet supports subsequent integrated UI ports. The
opt-in harness hides its former single-field editor, while original main-window
composition remains pending. [Behavior and limits](lifft_task_panel.md).


## F75 shared desktop composition

`MainNavigation` owns only Qt widgets and surname/filter/order state. Immutable
catalog data and actual assessment assignment context enter through `update_state`;
callbacks enter through construction. Stored IDs travel through combo item data.
There is no SQL, assessment mutation or renderer dependency in this view.
`LifftWindow` temporarily composes it with the F74 panel and reuses existing
application lifecycle/assignment selection operations. Owned modal dialogs remain
modal; no background concurrency infrastructure was added. See
[shared navigation](main_navigation.md) for transitional ownership and incomplete
main-window areas.


## F76 grid-specific workflow

The existing evaluator exposes an explicit LiFFT grid preview entry point alongside
its unchanged strict entry point. Both share numeric calculation, freshness and
scientific-review checks. Temporary preview inputs never become source snapshots;
PARTIAL outcomes retain missing-field issues. Presentation labels the incomplete
preview, while strict result consumers continue rejecting it. The owned task-count
form collects a count; its presenter uses an immutable application command for one
undoable source reset. No additional renderer/thread/persistence infrastructure was
introduced. See [workflow review](lifft_grid_workflow.md).


## F77 original side panels

The desktop owner composes `BodyRegionPanel`, task tabs and `ResultsSidebar` in the
original horizontal layout. Sidebar state comes from typed current evaluation and
canonical source, never widget parsing or periodic polling. `result_scales` owns
only Qt animation/drawing. The left viewport reserves the reference VTK size hint;
its actual renderer and controls remain unconnected. No Qt/VTK objects cross the
portable application boundary. See [panel behavior](main_panels.md).

## F82 update — 2026-10-05

The original ST task component owns widgets/pending text; `TstPresenter` uses the
existing portable unit projection and review-gated evaluator. `ReplaceTstInputs`
provides atomic whole-grid history with identity/source-unit protection. Explicit
model directions remain source data; no legacy selector swap or import inference is
adopted. [Component and review boundary](tst_task_panel.md). Main-tab routing is next.

## F83 update — 2026-10-05

The integrated window routes shared operations to the committed LiFFT/DUET/ST
source and its existing presenter. The ST component uses original selection,
ownership and persistence ports; no new lifecycle infrastructure was introduced.
Shared cards distinguish review from ready, while the renderer receives the portable
shoulder state with no unapproved color. [Integration and limits](tst_integration.md).

## F84 — task-count commands

DUET/ST task-count replacement uses typed immutable application commands and the
existing document history. UUID creation stays at the presenter boundary; commands
validate expected source, blank rows, count and identities. The integrated window
routes the existing modal to the active tool. Source units/ownership remain intact;
no storage schema, dependency or renderer contract changed. See
[task-count integration](task_count_integration.md).

## F85 — saved tool-data browser

A pure presentation mapping turns saved current history/jobs into immutable
worker/tool options. The desktop modal returns an exact option; the host resolves
pending/dirty intent and calls existing `select_assignment`. No new selector/session
infrastructure or storage changes were introduced. Closed ownership remains
addressable. See [saved tool data](saved_tool_data.md).

## F86 — exact assessment deletion

A portable optional repository capability removes the confirmed open assessment.
The workspace releases its session only after success; the SQLite adapter atomically
deletes source/ownership and compacts positions. The desktop owns confirmation and
retains an empty tool identity separately from source data. No automatic promotion,
assignment/catalog deletion or schema change occurs. See
[assessment deletion](assessment_deletion.md).

## F87 — visible menus and version allocation

The menu component delegates to existing desktop command owners and shares their
availability/captions. No second edit policy is added. The assignment dialog host
allocates the next historical version within exact assignment/tool scope; storage
still rejects current ownership conflicts. See [assessment menus](assessment_menu.md).

## F88 — injected preferences

Bootstrap shares the existing SettingsStore with the workspace and desktop host.
The owned dialog returns choices; the host validates input, atomically saves
language/default units and updates projection. Source data and user preferences
remain separate; no schema or dependency changed. See
[preferences](preferences_dialog.md).

## F89 — recent history and Close

The menu renders injected saved locations and delegates commands to the desktop
host. Listing performs no project storage access. The host reuses the existing
Open picker/workspace switch and Close lifecycle, while history edits use the
shared atomic settings adapter independently of pending assessment input.
Renderer lifetime belongs to the window rather than the current project.
See [recent projects and Close](recent_project_menu.md).

## F90 — portable snapshot transitions

SnapshotProject is an optional owned-project capability. The workspace validates
and activates the copy without saving the original; Backup releases its copy
without changing session/history/settings. SQLite/filesystem work stays in the
repository adapter, using validated temporary copies and exclusive publication.
No schema or dependency changed. See [snapshots](project_snapshots.md).

## F91 — read-only summary export

Application-owned immutable export rows retain saved ownership and evaluation
status. Injected loaders own read-only project access; existing grid evaluators
derive summaries without editing. Presentation maps CSV columns/percent scale;
the infrastructure writer owns BOM/quoting and exclusive complete publication.
No project schema or dependency changed. See [export](assessment_export.md).

## F92 — atomic original worker transfer

A pure domain plan validates selected current tools and exact owner contexts.
The workspace coordinates explicit dirty-source consent; an optional typed
repository port commits copies, new assignment and selected source removals under
one write transaction. Qt owns the original modal selections and messages without
SQL. Source values/units, older history and job profiles are retained. See
[worker transfer](assessment_transfer.md). No schema or dependency changed.

## F93 — injected original Help assets

Bootstrap injects immutable manual/logo bytes into the desktop host. The owned
Authors form renders exact reference credits and receives its logo; the desktop
launcher atomically caches the PDF and delegates local-file handling to Qt.
Help bypasses edit commits and owns errors independently of project state.
No portable-core, project schema or dependency change. See
[Help workflow](help_workflow.md).

## F94 — shared decimal preference

DecimalConvention is a portable typed contract shared by settings and numeric
presentation. Settings version two persists it; strict version-one reads default
to point without writing. Bootstrap restores it before view binding; the owned
Settings host validates old-policy input before saving/rebinding. No project
schema, algorithm or dependency changed. See [decimal preferences](decimal_preferences.md).

## F95 — transfer language boundary

The presentation catalog translates construction-time captions rather than walking
populated record widgets. Owned localized messages preserve explicit consent
without global translation state. Typed transfer/storage rules are unchanged.
See [scope and native message parity item](transfer_localization.md).

## F96 — optional animated renderer capability

The portable optional port receives policy and resolved user selection only.
Qt captures tab intent; VTK owns the GUI-thread timer, elapsed clock, path and
cancellation. Ordinary data refresh is separate from explicit camera motion.
User settings version three persists boolean policy with read-only old-format
compatibility. See [View camera behavior](camera_animation.md).

## F97 — read-only original project details

The workspace exposes immutable metadata from its owned connection without I/O.
The desktop receives metadata/location and owns the original modal rows, locale,
literal-text escaping and long-value elision. It bypasses edit acceptance and
refresh, preserving pending assessments. No storage schema, dependency or
renderer contract changed. Current-format gaps remain explicit N/A values;
see [mapping and legacy parity limits](project_properties.md).

## F98 — original metadata collection and storage

The portable ProjectMetadata owns optional literal description, local creation
clock and shared Language identity; application.settings re-exports Language.
Bootstrap creates format eight; the adapter stores one typed details record and
retains old readers without migration. The desktop owns the source-derived form,
creation clock and display mapping. Cancel precedes input parsing; accepted details
use existing validation/consent. Stored title drives the header. See
[compatibility and lifecycle limits](project_details.md).

## F99 — copy metadata intent

The workspace's optional MetadataSnapshotProject port accepts immutable same-
identity metadata for Save As and validates the returned copy before activation.
The existing SQLite snapshot adapter edits only its unpublished copy transaction;
format-seven full copies gain format-eight details, without source migration.
Desktop form prefill/acceptance precedes input parsing. Backup and callers omitting
metadata retain their previous behavior. See [scope](save_as_details.md).

## F100 — PLOT scope and read-only image boundary

The portable PlotScope validates one-plant hierarchy intent; load_plant_layout
uses an injected PlantLayoutReader after validation. FilePlantLayouts owns explicit
path associations and read-only filesystem access. Qt owns modal checks, localized
captions, scene decoding and coalesced aspect fitting. Coordinates remain original
pixels. No database schema, renderer or production navigation changed. See
[component behavior and remaining integration](plot_layout_components.md).

## JROT solver decision — owner, 2026-10-06

The eventual solver adapter must route single-tool optimization to CBC and
multi-tool optimization to HiGHS. GLPK is excluded from the migrated solver set.
This is a recorded target, not a solver installation or an early JROT implementation.
Exact dependencies remain subject to approval; the reference remains untouched.

## F101 — project-owned plant map storage

PlantLayoutImage is portable encoded data; the application validates scope before
an injected explicit writer. Infrastructure owns file decoding and transactional
SQLite blobs. Explicit image save upgrades full projects to nine; ordinary open
and preview do not. Snapshots preserve map bytes and metadata edits preserve the
format version. Qt canvas and production navigation are unchanged. See
[storage differences and remaining UI integration](plant_image_persistence.md).

## F102 — original PLOT map region with owned edit intent

PlotMapPanel owns Qt controls, selected scope and pending preview. It receives
portable reader/writer and an importer callback, avoiding infrastructure imports
and global main-window lookup. Same-scope selection avoids redundant refresh;
scope consent and failed operations preserve current intent. Original geometry
and processed icons are retained. Standard logging keeps adapter diagnostics out
of localized user messages. See plot_map_controls.md for composition limits.

## F103 — original PLOT filter intent

Workplace controls receive a typed map-acceptance callback and publish labels only
after accepted scope intent. The Qt modal owns its selection lifetime; the map owns
pending image consent. Tool controls publish AssessmentKind once per change,
independently of future applied result filters. Literal labels/escaped tooltips
preserve data identity without window growth or markup interpretation. See
plot_filter_controls.md for source mapping and remaining composition.

## F104 — portable predicates and explicit applied selection

PlotDemographics owns source-compatible pure worker predicates with explicit year
and canonical units. PlotFilterSelection freezes typed scope/tool/risk/demographics.
The Qt filter panel owns editable intent and exact canonical bounds; unit/decimal
projection cannot feed rounded values back into them. An injected callback owns
result publication; only successful Apply replaces the applied snapshot. Clear
accepts the map scope before resetting controls. No SQL or historical dataset
joins enter the presentation component. See plot_demographic_filters.md.

## F105 — saved PLOT datasets

PlotResultRepository combines existing read-only project capabilities. The
application validates scope/ownership and selects active/current saved sources
before sharing the saved evaluator with export. Immutable PlotResults contains
selected/all-tool worker rows and active job placements with optional approved
evidence. Infrastructure owns the separate connection; no Qt/SQL enters selection.
Compute-before-publication preserves results on read failure. Position/rendering
integration remains separate. See plot_result_datasets.md.

## F106 — original-pixel geometry and atomic position persistence

PlotPositions owns immutable station/assignment geometry and pure initialize,
ensure and move operations. The borrowed SQLite adapter validates typed records;
the project adapter owns format-ten upgrade and the transaction. Identity guards
retain historical geometry and reject orphans. Result loading exposes saved
positions without creating markers or accepting editor state. Pixel geometry has
no body-unit conversion or renderer coupling. Intentional removal must be composed
with final deletion workflows. See plot_position_persistence.md.

## F107 — owned marker rendering and position intent

PlotMarkerItem separates original-image geometry from Qt view scaling and owns
paint/mouse/saved snapshots. PlotMarkerLayer composes immutable saved datasets
through injected save/error/selection callbacks; no SQL or global window enters
presentation. Canvas signals clear items before scene replacement and synchronize
view scale. Explicit commit accepts geometry only after persistence succeeds;
Cancel restores the saved snapshot. Pending image/result replacement rejects real
unsaved intent. Original worker/job overview and parent consent compose next.
See plot_marker_rendering.md for source equivalence, fixes and remaining scope.

## F108 — original placement overview composed with marker intent

PlotJobOverview consumes typed saved result rows and stable marker owner IDs;
PlotMarkerLayer publishes Qt change/selection notifications without SQL/window
coupling. Combo projection blocks feedback; original X/Y controls own partial
text until explicit finite validation/Save. Existing transactional persistence
accepts the shared anchor. Locate releases its temporary Qt reference on
selection/rebuild/close. Worker counterpart and full details tabs compose next.
See plot_job_overview.md for source mapping and remaining integration.

## F109 — worker visual previews and atomic batch settings

PlotWorkerControls owns partial fields and source visual controls. PlotMarkerLayer
keeps typed worker draft settings separately from saved results and reuses its
worker paint composition when hidden workers are shown. Save validates the batch
before one injected project transaction; successful publication accepts only the
committed workers and preserves other drafts. No per-worker SQL/event pumping,
body-unit conversion or global window access enters this flow. Unplaced absence
is retained until explicit placement. Surrounding overview composes next.
See plot_worker_visual_controls.md for differences and limits.

## F110 — original worker overview and stable assignment drafts

PlotWorkerOverview consumes immutable saved rows and marker-layer notifications;
selector disclosure/order never reloads storage or changes assessment selection.
Source preview painting is owned by a separate 72-pixel QWidget. WorkerControls
retain partial fields per assignment for real navigation and batch Save. Body
unit display uses the existing pure projection; result probability scales remain
explicit. Locate releases temporary scene references on selection/rebuild/close.
Original search/context handoff and complete PLOT composition remain next.
See plot_worker_overview.md for source mapping and deliberate differences.


## F111 — modal worker search with stable assignment handoff

PlotWorkerPicker consumes an immutable saved-row snapshot and owns Qt filtering,
hierarchy, localized controls and a nullable assignment-ID result. It has no
storage/editor dependency. Worker Overview composes the modal result with the
existing marker selection or hidden/unplaced row selection; alphabet disclosure
uses stable identity rather than source dataset indices. Cancel performs no state
change, and existing per-worker visual drafts survive accepted navigation.
See plot_worker_search.md for source mapping, corrections and remaining PLOT work.


## F112 — worker context actions and injected editor handoff

Worker graphics items inject a screen-position context operation. MarkerLayer owns
the source menu and reuses transactional settings persistence; lock is typed draft
intent. Load injects SummaryExportRow -> bool, with no parent/window lookup or SQL.
The main editor validates current saved ownership and composes existing input/
dirty policy and workspace selection. PLOT parent close consent remains an explicit
future host responsibility. See plot_context_actions.md for corrections and scope.


## F113 — read-only summary datasets and owned chart figures

PlotSummary aggregates immutable saved PlotResults in the application layer using
stdlib arithmetic; membership, units, observations and paired comparison are
independent of Qt and storage. Presentation creates owned Matplotlib figures
without pyplot globals. Missing evidence has no bar, while source axes/styles and
localized text remain. Original Tools Overview/settings/viewer composition is
next. See plot_summaries.md for corrections, source comparisons and limits.


## F114 — original Tools Overview and owned graph workflows

PlotToolsOverview consumes immutable saved datasets without SQL/window coupling.
PlotGraphSettings owns validated presentation values; the modal dialog owns its
local draft and injects export with the active dialog as owner. PlotFigureViewer
owns a separately regenerated figure, preserving the embedded canvas lifecycle.
PlotChartCanvas adapts the approved backend's unannotated Qt methods with narrow
typed call boundaries, fits actual-size labels, and leaves queued resize drawing
to that backend. Replacement figures receive one click binding each. No renderer,
Qt or file export enters the application summary layer. See
plot_graph_workflows.md for source geometry, deliberate corrections and limits.


## F115 — original outcome composition and typed station warnings

PlotOutcomePanel consumes saved immutable summaries and results without storage
access. plot_highlights groups observed >50% values by full StationKey and returns
immutable StationHighlight values in the application layer. PlotHighlightDialog
owns its modal table; PlotRiskGauge reuses owned animation with reviewed PLOT
painting. Resize reflows labels/minimum bounds without publishing datasets or
restarting gauges. No Qt, image, filesystem or numeric-library dependency enters
summary/highlight calculations. See plot_outcome_summary.md for source mapping,
explicit clipping/identity corrections and pending full-host composition.


## F116 — original PLOT host ownership

PlotWindow composes injected saved-result/job/position/image capabilities with
reviewed PLOT panels. Read-before-publication Apply and one-way applied mode/tab
projection preserve explicit saves. Exact saved-assessment handoff uses the F112
editor port; parent closure follows host consent and accepted editor selection.
No parent globals, concrete storage, source assets or new asynchronous mechanism
are introduced. Actual layout minima and the source rail title style prevent
composition clipping. See plot_host.md for behavior and remaining map actions.


## F117 — original PLOT transient map controls

PlotLayoutCanvas owns one-click zoom, reset and marker opacity; these operations
never change saved snapshots or coordinates. PlotMapPanel owns the source PNG
chooser/view capture and reports Qt encoder failures. Reset replaces the legacy
Apply workaround with direct fit, retaining pending marker drafts and results.
Map-only action availability follows actual decoded pixels. See
plot_map_actions.md for source mapping, preserved scale/opacity policies,
reference comparisons, the deletion audit and remaining CSV/main integration.


## F118 — integrated PLOT with a borrowed project port

PlotRepository combines existing result/image/position capabilities and is borrowed
from ProjectWorkspace after full-project validation. The desktop/bootstrapped
modal uses that same handle, preserving format state during explicit upgrades.
Plot CSV formatting consumes immutable saved snapshots; the infrastructure writer
owns complete UTF-8 publication. Main navigation injects modal opening and existing
exact-assessment handoff rather than acquiring storage/global window state.
QDialog rejection and window closure share consent. See plot_integration.md for
source columns, body-unit/version provenance, lifecycle and remaining parity work.


## F119 JROT characterization — 2026-10-08

JROT will follow the existing immutable domain/application and injected infrastructure adapter boundaries. The source review identifies the active optimizer rather than duplicate legacy methods. No new production contract or solver dependency has been introduced; see jrot_migration.md.


## F120 JROT optimization — 2026-10-08

Immutable rotation data/constraint checks live in domain; RotationOptimizer and
its failure type live in application. PuLP/CBC/HiGHS remain entirely inside the
infrastructure adapter. Models own no project or Qt objects. Preserve this port
when integrating the original scheme form; see jrot_optimization.md. Worker
thread ownership and cancellation belong to the pending desktop integration.


## F121 JROT saved schemes — 2026-10-08

RotationScheme values own exact links and pure reference checks; the application repository port has no SQL/solver types. RotationSchemeStore borrows the project connection, which owns format-eleven upgrade, validation and commits. Hierarchy checks avoid recursive job/profile loads. See jrot_persistence.md.


## F122 original JROT scope chooser — 2026-10-08

The read-only RotationScopeReader and immutable options prepare saved catalog choices without SQL/Qt coupling. The original desktop chooser consumes those options, returns exact workplace identities, and owns one blocked checkbox propagation batch. It does not persist or optimize. See jrot_scope.md.


## F123 original JROT worker/time-block grid — 2026-10-09

RotationPoolReader borrows saved hierarchy/jobs/risks; immutable choices separate exact assignment/profile links from labels. RotationTable owns Qt item-data identities and blocked row-only repainting, without SQL or solver imports. Manual scheme construction is separate from persistence; containing form composition remains next. See jrot_grid.md.


## F124 original JROT scheme form — 2026-10-09

RotationForm builds original controls; RotationDialog owns modal scheme commands through RotationRepository, which combines read-only catalog and explicit scheme persistence ports. Neither imports storage/solvers or owns a project handle. Pending/applied scope, frozen links and post-commit UI state are explicit; no speculative callback layer was added. See jrot_form.md.


## F125 selected-tool JROT optimization — 2026-10-09

RotationDialog accepts an optional RotationOptimizer port; RotationSolveController owns exactly one bounded QThread. Immutable application preparation requires exact scheduled profile evidence; the worker never touches widgets/repository. GUI completion owns result rendering, explicit transfer/provenance and deferred closure. No concrete solver imports in presentation. Main/HiGHS comparison integration is still pending; see jrot_selected_optimization.md.


## F126 JROT comparisons and HiGHS — 2026-10-09

RotationComparisonDialog renders the original normal-window single/all comparison layouts over immutable schedules and pool evidence; Apply emits intent only. RotationSolveController shares one owned worker for CBC/one stage or HiGHS/two stages and owns modeless child lifetime. Transfer preserves SINGLE_TOOL/ALL_TOOLS provenance until explicit Save/manual edit. No solver/storage imports in views; main composition is next. See jrot_comparison.md.


## F127 — workspace-owned main JROT composition

RotationRepository is a runtime-checkable application capability combining pool
reads with explicit scheme persistence. ProjectWorkspace borrows that capability
from its one full-project adapter, with no new connection or implicit schema
migration. Bootstrap alone composes the concrete PulpRotationOptimizer and modal
RotationDialog. The integrated main navigation checks project capability/opener
availability and opens JROT without committing any assessment panel's pending
text. Modal worker/comparison ownership is unchanged; disposal follows actual
completion and leaves the workspace repository open. See jrot_main_integration.md.


## F128 legacy compatibility

Original XML/SQLite version-eight projects now have a tested read-only adapter.
The comprehensive copied fixture passes integrity and reference checks: 30 tables,
28 workers, 191 historical assessments, 19 risk profiles and seven JROT schemes.
Next: typed organization/worker/job/risk catalogs, then historical task sources.
No destination conversion or integrated legacy-project UI acceptance is claimed. See f128_legacy_compatibility.md and f128_validation.json for mapping, checks and remaining limits.


## F129 legacy compatibility

Original workers, organization, jobs, placements, assignments and every job-risk
profile version now map to existing immutable domain models. The comprehensive
copy validates all 28 workers, 12 jobs, 38 placements, 104 assignments, 19 profiles
and 56 measurements without source writes. Next: historical assessments/tasks and
cached evidence. Destination conversion and integrated legacy UI acceptance remain. See f129_legacy_compatibility.md and f129_validation.json for mapping, checks and remaining limits.


## F130 legacy compatibility

All 191 normalized historical assessments and 3,532 task rows in the comprehensive
copy now have a tested read-only compatibility mapping, with exact assignment/
version/current/status identity, units, source inputs, notes and cached evidence.
Next: reconcile three older records absent from normalized history, map PLOT/JROT
assets/provenance, and implement explicit atomic destination conversion before
integrated copied-project UI validation. Raw ST selector interpretation still
requires the documented scientific/UI decision; no implicit conversion is made. See f130_legacy_compatibility.md and f130_validation.json for mapping, checks and remaining limits.


## F131 legacy compatibility

The comprehensive copy now has a conflict-free recovery plan for all 194 original
assessment summaries and 3,577 task rows: 191 exact old/current matches plus three
recovered records/45 rows on their existing assignments 101, 102 and 104. Next:
PLOT companion images/geometry and saved JROT provenance, then explicit conversion.
No source or destination records are written by this read-only recovery plan. See f131_legacy_compatibility.md and f131_validation.json for mapping, checks and remaining limits.


## F132 legacy compatibility

The comprehensive copied project now maps all four exact plant images, 16 station
anchors and 100 assignment markers, with 191 raw assessment markers and original
plant display metadata retained. Next: saved JROT schemes/provenance, followed by
explicit destination conversion and integrated copied-project validation. See f132_legacy_compatibility.md and f132_validation.json for mapping, checks and remaining limits.


## F133 legacy compatibility

All seven original saved schemes now map to the established typed JROT models,
including 45 frozen target records, 179 assignment cells, exact scopes and original
manual/single-tool/all-tool provenance. Existing forms load every copied scheme in
EN/ES; actual CBC and HiGHS/Apply pass on the small saved source scheme. Next:
explicit atomic destination conversion with complete source evidence preservation,
then integrated copied-project validation. ST direction choice is still pending. See f133_legacy_compatibility.md and f133_validation.json for mapping, checks and remaining limits.


## F134 legacy compatibility

Complete typed snapshots now create a validated new-format project through a
hidden same-directory file and exclusive publication. Original approved/retired
profiles, historical ownership, PLOT images/positions and saved rotation links
survive exact read-back and reopen. Next: retain complete original XML/database
and image-name evidence; ST direction choice remains required before full source
conversion. Overall completion percentage and finish date remain unvalidated. See f134_legacy_compatibility.md and f134_validation.json for mapping, checks and remaining limits.


## F135 legacy compatibility

New-format twelve stores the exact original XML, a consistent read-only SQLite
snapshot and all referenced image bytes/names alongside the editable typed data.
Original cached results, task moments, raw selectors, timestamps, plant display
fields and schema objects remain recoverable after edits, backup and removal of
the copied source files. Next: connect an explicit converter, blocking source
conflicts and unresolved ST directions before destination creation. No reliable
overall completion percentage or finish date yet. See f135_legacy_compatibility.md and f135_validation.json for mapping, checks and remaining limits.


## F136 legacy compatibility

An explicit converter now takes an original XML project and publishes a separate
new-format-twelve repository with exact typed records and a complete source
archive. A small original-shaped project opens in the integrated application,
including recovered LiFFT, historical DUET, Worker Management, PLOT and saved
JROT. The comprehensive project currently blocks its 56 unresolved ST sources
before creating any destination. Next: review the original ST selector-to-model compatibility mapping,
then finish complete conversion and desktop Open integration. Overall percentage
and finish date remain unvalidated. See f136_legacy_compatibility.md and f136_validation.json for mapping, checks and remaining limits.


## F137 legacy compatibility

ST sources now record an explicit direction convention: existing version-one
new-format documents retain their model-code interpretation; imported original
UI sources retain their visible choices and the original 1/2 calculator swap.
All 1,650 frozen reference numerical vectors match through this mapping. No
scientific correction or owner direction answer is required for compatibility.
Next: convert all original assessments together, with source evidence intact.
Overall functional-parity percentage and finish date remain unvalidated. See f137_legacy_compatibility.md and f137_validation.json for mapping, checks and remaining limits.


## F138 legacy compatibility

The entire comprehensive project copy now converts into one new-format-twelve
file: 194 assessments/3,577 task rows, including all 56 ST sources, 28 workers,
12 jobs, 104 assignments, all 19 risk-profile versions, four maps/geometry and
seven saved JROT schemes. Reopen and backup retain exact typed records and the
complete source archive. Next: connect explicit conversion to desktop Open,
then exercise the converted copy through the integrated EN/ES workflows.
Overall full-parity percentage and finish date remain unvalidated. See f138_legacy_compatibility.md and f138_validation.json for mapping, checks and remaining limits.


## F139 legacy compatibility

The integrated main Open/recent workflow recognizes an original XML project,
asks for a separate converted-copy destination and then selects an assessment.
The destination alone enters recent history. Cancellation, existing-file and
missing-image failures retain the current workspace and unsaved source edits.
Next: comprehensive integrated copy validation. Full parity percentage and finish
date remain unvalidated. See f139_legacy_compatibility.md and f139_validation.json for mapping, checks and remaining limits.


## F140 legacy compatibility

The comprehensive project now opens through the integrated desktop as a separate
converted copy, with all 194 assessments/3,577 task rows and seven JROT schemes.
EN/ES native validation passes across LiFFT/DUET/ST, metric/imperial projection,
ST edit/undo/redo/save/reopen, Worker/Job/Organization Management, PLOT and real
CBC/HiGHS optimization followed by Apply/Save/backup. This completes the requested
F137–F140 four-milestone batch. Full-parity percentage/finish date remain unvalidated. See f140_legacy_compatibility.md and f140_validation.json for mapping, checks and remaining limits.


## F141 legacy compatibility

Converted projects now show original cached task outputs and totals in the
existing LiFFT/DUET/ST grids and result cards, explicitly marked Recorded /
Registrado. All 194 original/recovered sources are bound to their exact original
inputs. Editing hides historical evidence; undo can restore it, and saving an
edited source never makes the old result current. Fresh calculation gates remain.
Overall completion percentage and finish date remain unvalidated. See f141_legacy_compatibility.md and f141_validation.json for mapping, checks and remaining limits.


## F142 legacy compatibility

The original PLOT call path and active loadImageNew implementation were audited.
Stored Plant rotation/crop/mirror/other transform fields are not applied by that
loader. The migrated canvas matches its original pixel coordinates, scene bounds,
aspect-preserving fit, Top/Left alignment and hidden scrollbars, including resize.
Introducing dormant transforms would change the original behavior. They remain
archived for review rather than being activated. Next: readable assessment choices
and numeric inputs. Overall percentage/finish date remain unvalidated. See f142_legacy_compatibility.md and f142_validation.json for mapping, checks and remaining limits.


## F143 legacy compatibility

Integrated Open now offers tool, worker/name, complete workplace/shift and exact
version/assignment labels while keeping the stored document identity unchanged.
Narrow LiFFT/DUET/ST numeric inputs start at their leading digits, retaining full
precision and exact no-edit round trips. Existing recent-project Open, cancellation
and conversion behavior remain tested. Next: integrated comparison/visual checks
of this batch. Overall percentage and finish date remain unvalidated. See f143_legacy_compatibility.md and f143_validation.json for mapping, checks and remaining limits.


## F144 legacy compatibility

The F141–F144 batch completes historical result display, active-original PLOT
loader characterization, readable assessment selection and precise numeric
input display. Recorded outputs now use original tool palettes for task cells,
result cards and the avatar. Pending text immediately hides the previous recorded
outputs; repeated refreshes preserve the gauge animation target. Comprehensive
EN/ES workflows are validated on separate converted copies. Overall percentage
and finish date remain unvalidated; this is four milestones, not final acceptance. See f144_legacy_compatibility.md and f144_validation.json for mapping, checks and remaining limits.


## F145 implemented workflow

Fresh metric LiFFT now uses the characterized domain calculator through the
application service and reusable result presenter. Original normalization,
rounding and legacy moment-display arithmetic remain unchanged; this is behavioral
compatibility, not scientific certification. Missing/invalid inputs, source-unit
provenance, history and failure handling remain explicit. C1 gains usable-workflow
credit after frozen references, Calculate/Save/reopen and native checks pass. See f145_compatibility.md for evidence and limits.


## F146 implemented workflow

ST Calculate now runs the existing characterized calculator through the typed
application service, honoring each document's recorded direction convention.
The task grid, result cards, gauge and replaceable body renderer consume typed
results; calculation and unit policy stay outside Qt. C3 gains G3 usable-workflow
credit: overall fixed-scope progress is 73.25/100 (approximately 73%). See f146_compatibility.md for evidence and limits.


## F147 implemented workflow

Saved summary exports now preserve exact-source archived results with explicit
recorded status. The read-only application contract checks source equality before
using evidence; edited sources take the characterized fresh calculator path.
No calculation is run for an unchanged archived source. Per-assessment recorded
units are retained, including DUET's labels independent of project defaults.
This closes CSV compatibility within B1's existing G3 credit; no extra scope
points are claimed simply for completing another checkpoint. See f147_compatibility.md for evidence and limits.


## F148 implemented workflow

The copied comprehensive project now completes fresh Calculate, edit, undo/redo,
Save, CSV export and reopen across LiFFT, DUET and ST. All 194 sources evaluate
without mutation: 103 complete and 91 partial grids. The native integrated
scenario also saves/cancels/reopens a worker edit, opens PLOT, runs actual CBC and
HiGHS optimization, applies/saves a multi-tool rotation, and verifies backup,
archive retention and unchanged original inputs. G3 gains its usable-integration
gate: fixed-scope progress is 74/100 complete and 26/100 remaining. See f148_compatibility.md for evidence and limits.


## F149 implemented workflow

F149 verifies the reported main-window clipping without changing the application's
layout or behavior. Full-resolution F148 PNGs contain the labels and regions that
appeared absent in combined previews; R007 was not an established application
layout defect. The record is corrected rather than adding repaint callbacks.
The application wheel remains byte-for-byte identical to F148. Overall scope
progress remains 74/100 complete and 26/100 remaining; no final gate is awarded. See f149_compatibility.md for evidence and limits.


## F150 implemented workflow

Explicit Save now commits the current successful LiFFT/DUET/ST calculation with its unchanged or edited source in one SQLite transaction. Reopen/export prefer that exact-source saved result while the original archive remains separately readable and unchanged. Save As writes current results into the copy before adoption. Focused native pending-input and storage-failure regressions pass. Overall fixed-scope progress remains 74/100; final B1/C4 acceptance still needs its remaining lifecycle/navigation comparisons. See f150_compatibility.md for evidence and limits.


## F151 implemented workflow

LiFFT and DUET controls were compared by executing the original form-building methods in an isolated harness under the approved Qt baseline, without importing the original application's startup or touching its database. Headers, column/control types, DUET rating labels, button icons and matched parent-container captures now have direct source-based evidence. The measured DUET Calculate icon mismatch was corrected from 26 to the original 28 pixels. Overall scope progress remains 74/100; this checkpoint closes comparison subcriteria, not complete C1/C2 final acceptance. See f151_compatibility.md for evidence and limits.


## F152 implemented workflow

ST's Calculate icon now matches the original 28-pixel asset treatment. Original ST headers, column control types and direction selector labels are compared directly under the approved Qt baseline. The expanded Open assessment picker now uses the existing management/JROT styled delegate, fixing selected white text painted on a white background. EN/ES native selected/expanded states, all 194 captions, exact selection identity, modal behavior and cancellation pass. Overall scope remains 74/100; C3/C4 final workflow and full original-window acceptance are not claimed complete. See f152_compatibility.md for evidence and limits.


## F153 implemented workflow

Save during document/context/project transitions now uses the same atomic source/result persistence as explicit Save. An injected owner-thread result provider supplies only the active exact-source calculation after the target has been validated. No new background processing or modal ownership changes. All three tools pass switch Save, unchanged ownership/reopen, Save As success and retained-session failure acceptance. Current fixed-scope progress stays 74/100 while final lifecycle and original-window acceptance remains. See f153_compatibility.md for evidence and limits.


## F154 implemented workflow

Restored the original integrated inline totals for DUET and the original 13px/15px labels, risk backgrounds, rounded corners and luminance-based foreground for LiFFT and DUET. The original constructors hide totals, but refreshAssessmentSummary/styleToolResultSummary/alignToolSummary show them on the live result path. The previous empty-space interpretation was incomplete. A small typed, documented presentation component now owns those repeated controls; panels still own evaluation and exact-source historical selection. Progress remains 74/100; this bounded comparison does not claim complete-window G4 acceptance. See f154_compatibility.md for evidence and limits.


## F155 implemented workflow

Restored the original integrated ST inline totals using the same documented presentation component as LiFFT/DUET. Fixed an observed unit-label defect: switching display units projected ST inputs but also relabeled unchanged source-unit moments. The moment header now follows source/result units, matching the established LiFFT policy. The reference direction selectors and their calculator mapping remain unchanged. Current fixed-scope progress remains 74/100; full original-window and cross-feature final acceptance is still open. See f155_compatibility.md for evidence and limits.

## M06 — PLOT position source history

PLOT now reuses DocumentSession through application.plot_history; Qt actions
project localized history labels and focus-aware shortcuts, without a separate
Qt undo stack. Typed immutable position snapshots exclude images/charts; Save
merges only the selected worker/station subset into the persisted baseline.
Dirty state accounts for partial commits; replay never writes storage.
[Contracts, document lifetime and measured retention](plot_history.md) include
released gesture coalescing and clean Apply routing. No dependency added.


## M07/M08 JROT edit/apply history

Immutable `application.rotation_history` snapshots reuse `DocumentSession`. The
Qt adapter handles native typing focus and window-scoped actions; the dialog owns
source projection and the existing atomic rotation repository port. Solver threads
carry immutable inputs/results only. Apply is one reversible source command;
Save is a separate commit and clean marker. Frozen pool/provenance survives replay
without catalog reads. See jrot_history.md and m07/m08 acceptance records.
