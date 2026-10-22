# Public README, fresh captures and desktop trial setup verified — 2026-10-22

Owner-requested README retains the logo and starts with an early index, then presents
ErgoTools, PLOT and the current production JROT. Nineteen new real images include the
native VTK avatar, management/calculator forms, PLOT modes/charts and real CBC/HiGHS
production rotations. Related small images use grouped galleries; the future JROT
workflow is not advertised. Publications/conferences remain without the Role column.
The existing Apache License 2.0 file and logo are unchanged.

Current installation.md documents Linux and explicit Windows/macOS trial recipes,
updates and desktop shortcuts/aliases using new checkout-owned launchers. The owner
explicitly approves Windows Qt 5.15.2 because 5.15.17 has no Windows wheel; macOS keeps
5.15.17. Other exact pins, Linux environment, uv.lock and pyproject remain unchanged.
Binary resolution passes on Windows x64 and Mac Intel/arm64; native installation,
GUI/VTK, solvers and desktop activation are NOT RUN. Bash launcher behavior is tested
on Linux; Windows batch has static review only. Native acceptance remains pending.

Required native XCB gate: **2,004 passed, zero failures/skips, 94.31% coverage**;
standards, strict types 279, architecture/naming/docs/review and both builds pass.
The existing source-review gate now covers .cmd/.command alongside .sh; 11 focused
inventory tests pass. Four changed/new code files substantively reviewed; all 452
Python/stub files, 3,249 functions, 430 classes, 321 constants and four entry scripts
reviewed, zero pending/gaps. Five GitHub-rendered stationary README sections inspected;
all internal paths/anchors pass. Private capture copies are removed. No maintained
fixture, production source, schema or calculation changes. Protected reference and
its environment are not written. Linux migration/cleanup remains 100%; owner Job/
workflow testing stays paused and native Windows/macOS acceptance stays deferred.

See [README refresh validation](readme_refresh_validation.json). Main-only publication
is owner-authorized, preserving other branches; ref evidence is recorded locally in
artifacts/readme_refresh. No new milestone or unrelated work.

---

# GitHub main replaced and remotely verified — 2026-10-22

The owner explicitly authorizes uploading the current complete workspace to GitHub
mhenriquezschott/ErgoTools/main and leaving other branches untouched. Owner SSH access
already works; no token or credential change is required. All 17 branch tips are
recorded in repository_branch_baseline.json. One normal replacement commit preserves
main history; no force push, mirror or branch deletion. Existing legal notices remain.
Main now contains the current codebase at initial replacement commit
`cac9218e913e3dbd4ff178d15c1bdee2d4adafba`. All 16 other branch tips and all tags
are unchanged. Direct ref comparison and a clean archived-checkout import/four-native-
project check pass; all 1,440 payload files preserve exact working bytes.
See repository_setup.md and repository_publication.json. Environments, caches, artifacts/dist and personal state are
excluded. No application/dependency/fixture changes or repeated functional gate are
part of this repository operation; valid prototype/production evidence below is reused.
Linux migration/cleanup remains 100%; native Windows/macOS remain deferred.

---

# JROT meeting prototype refined and clean project verified — 2026-10-21

Load **test_projects/native/jrot_workflow_demo.ergprj** for the owner's Friday demo.
Six named/demographic workers and six Jobs with two populated task rows per tool:
18 calculated measurements/36 task rows. Two plants, four sections, eight lines,
24 stations, two shifts and valid placements use existing format19/domain/native APIs.
No worker assessments or saved schemes are seeded; the main worker grid is therefore
empty by design. The prototype uses the populated Job sources and results.

Owner-requested changes: header-blue/white animated drawer; prominent Yes/No buttons;
familiar themed hierarchy/shift and searchable Job/worker pickers; free Back/sidebar
review; calculation-only readiness checks; optional rule notice and clear source-data
availability. Six real defaults and mixed real/sample/entered data complete the Yes
flow with real CBC single-tool/HiGHS all-three optimization. No branch, pairs, reports,
Undo/Redo and actual rule enforcement remain unavailable. Nothing prototype-related
is saved; the Developer switch is still session-only/off after restart.

Final focused Linux XCB checks: **64 passed**, zero failures/skips. Independent final
wheel: **18 prototype tests passed**, 331 packaged files match source. Standards,
strict types 279, architecture/naming/docs/review pass; 452 files, 3,248 functions,
430 classes and 321 constants reviewed, zero pending/gaps. **35 native UI states
inspected**, including new modal trees, populated/empty/partial and minimum/bottom
states. Basic-test exception remains owner-authorized; no new full-suite coverage
claim is made. Build/current package evidence is in jrot_prototype_meeting_validation.json.

Only two existing prototype modules and their test change, plus one isolated selector
module, one removable developer fixture builder and the single requested native file.
The three existing native projects, production Settings/menu/composition hooks,
calculators/optimizer/schema sources, other production code, uv.lock and pyproject are
exact baseline bytes. Fixture integrity/FKs pass; all shared schema definitions match
existing format19 structures. No reference checkout/environment writes. The normal lazy
worker-result table is absent because no worker results exist; no repair/table added.

Read [meeting walkthrough/data/decisions](jrot_meeting_demo.md) and
[validation](jrot_prototype_meeting_validation.json). Temporary window removal is tracked
there. Owner Job/four-worker tests stay paused. Linux migration/cleanup remains 100%;
Windows/macOS and owner acceptance are not claimed. Prior prototype evidence follows
as historical checkpoints.

---

# JROT developer prototype — implemented and Linux-verified, 2026-10-20

The owner-authorized Yes-flow mockup is ready for team review. Enable Settings →
General → **Enable Developer Menu for this session**, Apply, then use **Developer
Menu → JROT workflow prototype…**. It starts off again on restart; inputs disappear
on close. Project/sample/new task inputs use existing calculators and real CBC
(single tool)/HiGHS (all three). Hover/pin navigation reallocates width. Constraints
are visibly preview-only; No branch, pairs, reports and Undo/Redo are unavailable.

Final focused native XCB run: **59 passed**, no failures/skips, including 13 new
prototype cases and existing Settings/navigation/Save checks. The independent wheel
passes all 13 prototype tests; all 330 packaged files match source. Standards, strict types
277, architecture/naming and substantive documentation checks pass; 450 maintained
files reviewed, zero pending/gaps. **32 native capture states inspected**, including
minimum sizes and scrolled bottom controls. The owner requested basic testing only;
the prior 1,984-test/94.33% full gate remains historical, not a new prototype claim.

Exactly three existing source files change for Settings/menu/composition hooks;
four isolated modules and one basic test are new. All other files in the 452-entry baseline,
three native fixtures, uv.lock and pyproject remain exact. No production JROT widget,
calculator/solver, schema, history or persistence contract changes. Reference checkout
and environment remain untouched. The private comparison copy and its cleanup note,
mockup judgments and limitations are documented in [jrot_prototype.md](jrot_prototype.md)
and [validation](jrot_prototype_validation.json). Hands-on Job/four-worker tests remain
paused; this prototype is not owner acceptance of future production JROT changes.
Linux migration/cleanup stays 100%; native Windows/macOS remain deferred.

---

# Owner-authorized JROT developer prototype — implementation/verification in progress

The owner now authorizes the isolated semi-functional Yes-path mockup described in
`jrot_prototype.md`, superseding discussion-only instructions for that prototype.
Developer Settings/menu integration is session-only, off on restart. Prototype input,
task names, worker-rule previews and results are disposable; project/schema/history and
personal preference storage must remain unchanged. English/cm/N, equal blocks, existing
calculators and existing real single-tool CBC/all-three HiGHS only. No branch, reports,
Undo/Redo, two-tool solves and enforcement of preview constraints are out of scope.
Use judgment for mockup decisions and record them; basic tests/documentation only,
plus native inspection. No new migration milestone or production JROT redesign.
The comparison fixture's authorized safety copy is an artifact, never a maintained
duplicate. Hands-on Job and four-worker workflow testing remains paused.

---

# JROT requirements discussion — current owner answers

See [the live discussion record](jrot_wireframe_discussion.md) before the original
sixteen questions. Owner specifies any nonempty tool subset, fixed/excluded-worker
rules, no consecutive high-risk Jobs using existing classifications initially, and
exactly one worker per participating Job/block. Configurable risk thresholds are a
later requirement, with storage/scope undecided. Within-shift-only enforcement is
provisional; ask whether it must also cross shift boundaries. This is discussion only,
not authorization for JROT/schema/solver implementation. Hands-on tests stay paused.

---

# Previous toolbar sizing restored; guided JROT discussion — 2026-10-20

The owner rejects the uniform toolbar widths as too wide. Exact pre-change source and
navigation tests are restored, byte-for-byte against the accepted Job checkpoint.
No alternative sizing or icon redesign is added. English/Spanish loaded headers/main
windows were inspected in four private-copy captures. Required native XCB gate: 1,984 passed, zero failures/skips, 94.33% coverage; all standards,
types, architecture/naming/documentation/builds pass. Rebuilt wheel matches the prior
independently tested Job wheel exactly; reuse its 181 package tests. See
toolbar_restore_acceptance.md and validation.

The owner requests discussing the proposed JROT workflow **one screen at a time**,
starting physical PDF/PPTX page 3 (Line Setup, Screen 1), without explaining the entire
flow at once. Station-versus-Job meaning is the first unresolved question; do not infer
that the team intends them to be identical. Record owner answers and distinguish those
from questions still requiring JROT-team clarification. This authorizes discussion only,
not redesign, schema/model changes or new milestones. The complete review and 16 questions
remain available as background, not an instruction to present them all at once.

Hands-on Job UI/workflow testing remains paused at the owner-confirmed empty Job window.
Linux migration/cleanup 100%; Windows/macOS deferred. Reference/dependencies/data stay
unchanged. The rejected uniform-sizing evidence below is historical, superseded here.

---

# Uniform toolbar verified; JROT wireframes reviewed — 2026-10-20

Owner-authorized small correction: all nine main-toolbar buttons share the widest
translated native width and the existing 75px height. English/Spanish captions fit;
Jobs no longer receives a narrower button than Organization. No icon/action/history,
formula, schema, dependency or reference changes. The two changed maintained files
and their documentation were substantively reviewed; hashes/inventory are current.

Final native XCB gate: **1,984 passed, zero failures/skips, 94.33% coverage**; standards,
strict types 273, architecture/naming/documentation/builds pass. Independent current
wheel: 12 native navigation tests pass outside source; source/resources match package.
Eight EN/ES header/main captures inspected, empty and privately loaded project states.
All three maintained test project bytes and uv.lock remain exact. See
[toolbar acceptance](toolbar_uniform_size_acceptance.md) and its validation.

Reviewed all 15 pages/slides of the supplied October 15 JROT wireframes, including the
raster overview and 10 speaker-note slides. Analysis only: **no JROT redesign or schema
work is authorized/implemented**. [The review](jrot_wireframe_review.md) maps reusable
UI/data to current contracts and separates proposed duration, restriction, staffing,
classification/report changes. [16 forwardable questions](jrot_wireframe_team_questions.md)
request team clarification. Original documents are unchanged; extraction/source/arithmetic
evidence is in artifacts/jrot_wireframe_review. No new milestones were created.

The owner confirms workflow_4_workers.ergprj opens and Jobs is empty with three empty
summary rows. No direct entry/calculator/copy owner tests were performed. Both Job UI
and earlier worker/workplace testing remain paused at workflow_testing_pause.md.
Linux migration/cleanup remains 100%; native Windows/macOS acceptance remains deferred.
Prior accepted Job functionality evidence below remains valid for unchanged behavior.

---

# Job Management simplification — verified, 2026-10-20

Owner-authorized Job changes are implemented and Linux-verified: one current risk set
per Job, optional embedded LiFFT/DUET/ST task calculators, exact independent worker
assessment copies, shared per-edit Undo/Redo and the sole main Save. Profile/evidence/
lifecycle UI and storage are removed. PLOT/JROT resolve current values; saved rotation
arrangements remain intact and changed risks invalidate optimization provenance.

Native format 19; all three maintained fixtures updated in place. Final comparisons
prove exact worker inputs/results, unrelated rows, images, selected Job values and
schedule arrangements/timestamps; integrity/FKs pass. No invented migrated tasks.

Final native XCB gate: **1984 passed, zero failures/skips, 94.33% coverage**; standards,
strict types 273, architecture, naming, documentation and builds pass. Independent
byte-identical wheel: 181 focused tests outside source with converter imports blocked.
Actual modal copy/main Save/reopen/Save As/backup checks pass on private copies of all
three fixtures. **42 native EN/ES application captures and two guide renders inspected**.
96 changed/new files substantively reviewed; 445 maintained Python/stub files, 3113 functions,
418 classes and 312 constants have current review hashes, zero pending/gaps.

Read [acceptance](job_management_simplification_acceptance.md),
[validation](job_management_simplification_validation.json),
[decisions/recovery](job_management_simplification_decisions.md) and source review.
The two comprehensive fixtures retain pre-existing partial DUET/ST worker results;
copying requires complete matching calculations. The four-worker fixture covers all
three tools. No worker results were silently recalculated. One finite rollback archive
is retained until owner review; cleanup is documented.

Interactive workflow testing remains paused at workflow_testing_pause.md. The pending
Bruno/Ana Follow worker step is not performed. Original Linux migration/cleanup stays
100%; no new milestone. Windows/macOS remain deferred. No formula/dependency/reference
changes. Root dist packages are current; the frozen dist/linux bundle is historical.
Owner review and workflow resumption await the owner's return.

---

# Workflow testing paused; Job simplification under discussion — 2026-10-19

Owner explicitly pauses interactive four-worker workflow testing while discussing a
longer Job Management task. Exact saved state and the unperformed next Follow worker
test are recorded in [the testing bookmark](workflow_testing_pause.md). Ana's LiFFT
association to ST01 has been saved/reopened and verified read-only; twelve sources and
results are unchanged. Eleven assessments remain standalone. Do not resume user tests
or mark the pending Bruno/Ana navigation check passed without owner feedback.

Owner requests removal of Job profiles/evidence/lifecycle/version UI and storage, one
current risk set per Job, optional compact task calculators, shared Undo/Redo testing
and in-place current/comparison fixture migration. This turn is review and clarification
only: no Job implementation or database mutation has started. Saved JROT profile
references, calculator input retention and direct-entry semantics require a clear
agreed contract first. The last completed code gate remains the checkpoint below.
No migration milestone is reopened; Linux migration/cleanup remains100%.

---

# Explicit assessment creation from context — verified, 2026-10-19

Owner approved removing the ambiguous assessment question when Worker Management
closes. Closing now retains worker/workplace changes and the active assessment; obsolete
last-assignment return state is removed. Select assessment context names the worker/tool
and offers Open assessment for existing data or Create assessment for the exact missing
assignment/tool. Creation inserts one blank 15-task source privately; main Save publishes
it. Cancel, existing standalone data, other contexts/tools and Associate assessment remain
unchanged. Existing same-Job consent and shared removal-confirmed Undo/Redo are preserved.

Final required native Linux XCB gate: **1,965 passed, zero failures/skips,
94.43% coverage**; strict types269, standards/format/architecture/naming/
documentation/review and wheel/sdist builds pass. Independent wheel: **255 passed /
78 subtests**, all247 Python files/both guides exact, all loaded modules isolated.
Twenty-eight native EN/ES captures and both updated Help paragraphs inspected. Initial
Spanish caption override was fixed and tested. Earlier display failures and one obsolete
integration-test expectation are documented, not accepted as passing evidence.
Thirteen changed files substantively reviewed; 439 files / 3,112 functions / 416 classes /
323 constants, zero pending/gaps. Test fixture teardown uses explicit Qt deferred deletion.

Owner accepted the preceding table layout and verified assignment Save/reopen. Read-only
inspection confirms Ana W01 at ST01 / Shift1 / No Job, no Jobs/placements, and twelve
standalone assessment owners/sources/results. Current native projects and uv.lock are
unchanged by this task. Native format18, formulas, dependencies and reference untouched.
Linux migration/cleanup stays100%; Windows/macOS remain deferred. No new milestone.

Next: restart and review Ana/LiFFT in Select assessment context; ST01 should offer Create
assessment. Keep the workflow sequential and existing standalone data intact; do not
jump to association or add duplicate assignments. Owner acceptance of this revised
creation flow is pending. [Acceptance](explicit_context_creation_acceptance.md),
[validation](../artifacts/explicit_context_creation/validation.json).

---

# Workplace table fill, action borders and hover help — verified, 2026-10-19

Owner feedback rejected the prior unused right strip, shrunken No Job selectors,
clipped trash border and generic Job tooltip. One intrinsic measurement/fill pass now
preserves complete location/header/Job minima and gives positive spare width to Job;
every selector fills that column. Native cell padding and full Actions layout determine
column width and row height, keeping both borders visible. An owned single-shot timer
coalesces viewport show/resize changes and settles without project edits/history.
Header descriptions, literal full cell values, current Job help/popup values and row
actions have appropriate EN/ES tooltips. Blank table space has no generic Job help.

Final required native Linux gate: **1,956 passed, zero failures/skips,
94.42% coverage**; strict types269, standards/format/architecture/naming/
documentation/review and wheel/sdist builds pass. Focused workflow31 and worker40
checks pass. Independent wheel: **223 passed / 78 subtests**, all
247 Python files and both guides exact; all loaded modules isolated and final
wheel equals the tested wheel.

Twenty-seven native captures inspected, including minimum/enlarged/long/many-row states,
complete action borders, actual hover popups and Ana's four-worker context on a private
copy. Both updated Help sections inspected. Three changed source/test files reviewed;
439 files / 3,101 functions / 416 classes / 323 constants, zero pending/gaps.
Current native files and uv.lock unchanged; no schema/formula/dependency/reference
write. Linux migration/cleanup100%; Windows/macOS deferred. No new milestone.

Next: preserve Ana's existing workplace assignment with main Save before restart, then
review this table and hover help and verify assignment persistence. Do not add another
assignment or jump to assessment association. Owner layout acceptance remains pending.
[Acceptance](worker_assignment_table_refinement_acceptance.md),
[validation](../artifacts/worker_assignment_table_refinement/validation.json).

---

# Worker workplace table sizing — verified, 2026-10-19

Owner confirmed assignment Undo/Redo, then requested complete workplace/Job values.
The assignment table now fits each location/header independently, fits complete Job
choices using native selector/cell geometry and declares the widget minimum for correct
first display. Empty Job columns retain a useful default; narrow Station/Shift columns
stay compact. Horizontal/vertical scrollbars appear only on actual overflow. Clearing
or rebuilding refits columns without project changes. Ownership/history/Save unchanged.

Required final native Linux gate: **1,954 passed, zero failures/skips,
94.41% coverage**; strict types269, standards/format/architecture/naming/
documentation/review and wheel/sdist builds pass. The focused workflow module passes
29 cases, including eight new table scenarios. Independent wheel: **221 passed /
78 subtests**, all 247 package Python files/both Help guides exact;
all loaded package modules use the isolated extraction and final wheel equals tested.

Twenty-two native EN/ES captures plus both Help sections inspected, covering full Plant
and long Job values, empty/cleared tables, both scroll directions, 35 rows, selected Jobs,
minimum/enlarged windows and bottom controls. Two changed source/test files substantively
reviewed; 439 files / 3,099 functions / 416 classes / 323 constants, zero pending/gaps.
Three maintained native projects and uv.lock unchanged; no schema/dependency/formula
change or reference write. Linux migration/cleanup remains100%; Windows/macOS deferred.

Next: preserve the owner's pending workplace assignment with main Save before restart,
then review Worker Management table and assignment persistence. Continue this workplace
assignment workflow before standalone assessment association. Final UI feedback pending.
[Acceptance](worker_assignment_table_acceptance.md),
[validation](../artifacts/worker_assignment_table/validation.json).

---

# Workplace-first assignment workflow — verified, 2026-10-19

Owner-approved Workplace assignments / Assigned workplaces / Assign workplace… replaces
Job-centric worker captions. The shared picker selects hierarchy station, Shift and
optional compatible Job. No Job is valid, with separate assignment/Job summary counts.
Change preselects the existing context and retains historical assessment owners.
Associate assessment directly reuses an existing worker assignment (Job unchanged)
or atomically creates the missing assignment and binds the saved standalone source.
One shared Undo/Redo action covers both; Cancel/failure leaves no orphan assignment.
Existing removal consent and main Save remain. Exact inputs/results/identities and
other tools are preserved. Native format 18, all three fixtures and uv.lock unchanged.

Final native Linux gate: **1,946 passed, zero failures/skips, 94.40% coverage**;
standards/format/types (269), architecture/naming/documentation and wheel/sdist builds
pass. Independent wheel: **213 passed / 78 subtests**; all 247
Python files and both guides equal source; all loaded package modules use the isolated
extraction. Final wheel equals the tested wheel. Twenty-one new focused regressions pass.

Twenty-eight native EN/ES captures, all changed minimum/enlarged/empty/selected/Job
states and main VTK/results/bottom controls, plus both Help sections inspected. Main
Undo Cancel/Yes/Redo confirms existing removal policy. Sixteen changed maintained files
substantively reviewed; 439 files / 3,095 functions / 416 classes / 323 constants,
zero pending/gaps. Linux migration/cleanup remains 100%; Windows/macOS deferred.

Read-only reference audit found ten differences against the historical 500-file
manifest, with October 12 timestamps preceding this task. Reported and recorded;
reference files/manifest remain untouched, current hashes stable across this audit.
Do not claim all 500 still match that historical manifest. See protection evidence.

Next: owner restarts, reopens unchanged workflow_4_workers.ergprj and reviews these
controls before resuming the four-worker workflow. No new milestone is active.
[Acceptance](workplace_assignment_workflow_acceptance.md),
[validation](../artifacts/workplace_assignment_workflow/validation.json).

---

# Organization input cleanup — verified, 2026-10-19

Owner-requested calendars now edit Plant opening and Section/Line/Station creation
dates, preserving optional ISO values; empty calendars start at today, with a real
first click providing a date. Native hour/minute controls edit daily Plant duration
(0–24h, including zero/full day), retaining decimal-hour storage without lossy rounding.
Six obsolete Station attributes and editable Plant number_of_shifts are removed from
form/domain/storage. Format **18** gates the typed contract; external formats 8–17
upgrade on a private copy, with exact format-14/15/16/17 assessment sources/results.

Owner explicitly chooses distinct shifts used by workplace assignments or Jobs in
that Plant. **Shifts in use** counts active Job/placement and worker workplace links,
including unclassified workers, deduplicating shift IDs. Unused definitions, inactive
links and other Plants do not contribute. The read-only workspace query preserves
edit snapshot authority and adds no table/cache/history step. Shared Job Undo/Redo
updates the count. Workflow Plant currently correctly shows 0 before usage exists.

Both maintained native fixtures and workflow_4_workers.ergprj were updated in place:
only retired attributes/format metadata changed, every other row/retained value and
input/result/image/scheme payload exact. Integrity/FK/reopen checks pass. No live file
handles were held during migration; no backup/duplicate fixtures were created.

Final Linux XCB gate: **1,925 passed, zero failures/skips, 94.46% coverage**;
standards/types (268)/architecture/naming/documentation/builds pass. Final count/input
focused 170; independent wheel 260 / 78 subtests, all 246 Python files/guides equal
source. Thirty native states and both Help sections inspected; final count states
refreshed and 20 unchanged calendar states reused. Twenty-two files substantively
reviewed; 437 files / 3,076 functions / 415 classes / 320 constants, zero pending/gaps.
Reference/lock/formulas unchanged. Linux migration/cleanup remains 100%; no new
milestone. Windows/macOS deferred; owner UI feedback remains pending.

Next: reopen the workflow project from Recent Projects, check the changed organization
inputs, then resume the agreed four-worker workplace association workflow. See
[acceptance](organization_input_cleanup_acceptance.md) and
[validation](../artifacts/organization_input_cleanup/validation.json).

---

# Recurring Shift event metadata removed — verified, 2026-10-19

Owner-requested Incidents reported and Ergonomic risk events are removed from the
Shift form, localization, domain contract and native stored attribute pairs. Native
format **17** gates this reduced contract. The existing external converter supports
full native formats 8–16, removes exactly these fields (empty or populated) before
strict validation and preserves format-14/15/16 sources/results exactly. Original
schemas/files remain frozen; no incident tables or replacement feature were added.

Both maintained fixtures and `workflow_4_workers.ergprj` were updated at their same
paths after the owner closed the live application. Removed values were all null;
full database comparisons prove every unrelated table/row, input/result/image/scheme
payload and timestamp unchanged. Integrity/FK checks and native reopen pass.

Required Linux XCB gate: **1,885 passed, zero failures/skips, 94.50% coverage**;
standards/types (266)/architecture/naming/documentation/builds pass. Focused 181;
independent wheel 220 / 78 subtests, all 244 Python files and both guides equal source.
Twelve native EN/ES Shift states and both updated Help sections inspected. Sixteen
maintained files reviewed; 434 files / 3,044 functions / 413 classes / 317 constants,
zero pending/gaps. No dependency/formula/reference change. Linux migration/cleanup
remains 100%; Windows/macOS deferred. No new milestone.

Next: restart, reopen the existing workflow project from Recent Projects and obtain
owner feedback before resuming four-worker workplace association testing. See
[acceptance](shift_metadata_removal_acceptance.md) and
[validation](../artifacts/shift_metadata_removal/validation.json).

---

# Standard optional clock editor — verified, 2026-10-19

Owner-approved standard Qt hour/minute entry now supports typing 8:30 / 0830,
zero-padding 8: with minutes selected, native arrows, optional clearing and a real
00:00 distinct from Not set. Plant/Shift share the nullable Qt adapter. Shift adds
explicit Ends the following day: same-day end > start, next-day end <= start for one
daily interval up to 24h. Existing overnight pairs infer the checked option on load;
no new project field/schema/codec version. Invalid intent retains inputs and data.
Mouse shared history and native clock typing Undo retain ownership; optional panels
and tree expansion remain preserved.

Required native Linux gate: **1,876 passed, zero failures/skips, 94.52% coverage**;
all standards/types (266)/documentation/builds pass. Native focused 176; independent
wheel 181 / 78 subtests, all 244 package Python files and both guides equal reviewed
source. Twenty-six final native states and two Help sections inspected; arrows/day
indicator visible, labels/footer fit. Seven maintained files reviewed; 433 files /
3,039 functions / 413 classes / 316 constants, zero pending/gaps. Owner workflow,
maintained native fixtures, lock and reference unchanged; no dependency/formula/data
change. Linux migration/cleanup remains 100%; Windows/macOS deferred.

Next: restart and owner time-editor/overnight feedback, then resume the guided
four-worker workplace association workflow. See
[acceptance](shift_time_editor_acceptance.md) and
[validation](../artifacts/shift_time_editor/validation.json).

---

# Organization view preservation — verified, 2026-10-19

Owner-reported collapses on Delete/Undo are corrected. Optional details retains its
chosen open/closed state for all locations and shifts. Tree rebuilds retain exact
expanded/collapsed branch flags, including removed subtrees restored by Undo.
Internal reselection preserves those flags through Qt's ancestor auto-reveal.
Undo reselects a restored deleted record unless the user has since selected another;
current user collapse/selection wins. Fresh dialogs retain their initial collapsed
view. All view choices are dialog-local, with no history/storage/dirty-state additions.

Required native Linux gate: **1,834 passed, zero failures/skips, 94.50% coverage**;
all standards/types/documentation/builds pass. Native focused: 123; independent wheel:
139 / 78 subtests, all 243 package Python files and both guides equal reviewed source.
Twenty-eight native states and two Help sections inspected; no new clipping. Two
changed maintained files reviewed; 431 files / 3,016 functions / 412 classes /
315 constants, zero pending/gaps. Owner workflow, maintained fixtures and lock
unchanged. No schema/formula/dependency/reference change or new milestone.
Linux migration/cleanup stays 100%; Windows/macOS deferred.

Next: owner restart and Organization details/tree Delete/Undo feedback, then resume
the four-worker workplace association workflow. See
[acceptance](organization_view_state_acceptance.md) and
[validation](../artifacts/organization_view_state/validation.json).

---

# Organization clocks and pending Undo — verified, 2026-10-19

Owner-reported Shift description/time edits now expose valid pending Undo/Redo
through the existing shared project history, consistently across all optional
organization fields. Mouse replay accepts/reverses the record form; native text
Undo remains local. No separate stack or additional Save. Plant/Shift start/end
fields reject non-clock input and show explicit optional 24-hour HH:mm guidance;
00:00-23:59, blank values and overnight shifts are supported. Invalid/incomplete
values retain the form and block acceptance without changing saved data.

Required native Linux gate: **1,790 passed, zero failures/skips, 94.47% coverage**;
all standards/types/documentation/builds pass. Native focused 79; independent wheel
95 tests / 78 subtests, 243 package Python files and both guides equal source.
Twenty-six native states and two Help sections inspected. Three changed maintained
files reviewed; 431 files / 3,006 functions / 412 classes / 315 constants, zero pending.
Owner workflow/maintained fixtures/lock hashes unchanged. No schema/formula/dependency/
reference changes. Linux migration/cleanup remains 100%; Windows/macOS deferred.

Next: restart and owner Shift description/time Undo/Redo feedback; resume guided
workplace association testing afterward. Organization structure is saved and all
12 worker assessments remain standalone. See
[acceptance](organization_time_history_acceptance.md) and
[validation](../artifacts/organization_time_history/validation.json).

---

# Equal assessment action widths — verified, 2026-10-19

Owner confirms Clear assessment behavior works. Requested visual follow-up complete:
Clear assessment and Calculate now share equal width in LiFFT/DUET/ST, with the
existing 40 × 40 chooser centered between them. Removed the legacy Clear width cap;
no behavior, labels, task data or history changes. Three panel sources reviewed and
hash inventory refreshed. Twelve native EN/ES states inspected at minimum/expanded
widths; no bottom-row clipping. Geometry allows a one-pixel split for odd free widths.

Required gate: **1,738 passed, zero failures/skips, 94.37% coverage**; all standards,
types, architecture, naming, documentation/review and builds pass. Owner workflow,
maintained fixtures and lock hashes unchanged. Linux migration/cleanup remains 100%;
Windows/macOS deferred. No new milestone. Next: owner layout feedback, then resume
guided workflow testing before organization setup.
See [acceptance](clear_assessment_acceptance.md#owner-feedback-and-equal-width-follow-up--2026-10-19)
and [validation](../artifacts/clear_button_layout/validation.json).

---

# Clear assessment — verified, 2026-10-19

Owner-approved single **Clear assessment** replaces Reset/trash in LiFFT/DUET/ST.
Confirmation defaults to Cancel. Clear affects only the active worker/tool/context;
keeps task rows, assessment identity, units and selection; one shared Undo restores
exact inputs/results. Other assessments remain intact. Main Save publishes changes.
The old trash blanked all panels because its deletion handler lost the active
context; private-copy inspection confirmed other tool data was not deleted.

Required Linux gate: **1,738 passed, zero failures/skips, 94.37% coverage**; all
standards/types/documentation/builds pass. Native focused: 126 / 78 subtests;
independent wheel: 144 / 78 subtests, all 243 package Python files/guides equal.
Thirty-six native captures and both updated Help sections inspected. Nineteen
changed source/test files reviewed; inventory 431 files / 2,997 functions /
412 classes / 315 constants, zero pending/gaps. Owner workflow/maintained fixtures
and lock hashes unchanged; no schema/formula/dependency/reference changes.

Next: owner restart, Ana LiFFT Clear/Cancel/Undo feedback before organization setup.
Linux migration/cleanup remains 100%; Windows/macOS deferred. No new milestones.
See [acceptance](clear_assessment_acceptance.md) and
[validation](../artifacts/clear_assessment_review/validation.json).

---

# Owner workflow — twelve standalone assessments saved and verified

Owner completed independent data entry for four workers across LiFFT/DUET/ST.
Read-only inspection of workflow_4_workers.ergprj confirms all 12 sources and complete
results are saved, every result matches its exact stored source, assignments are NULL,
and foreign-key checks are clear. Entered values and ST directions match the guided
inputs; Ana/Bruno earlier inputs remain intact. Fifteen task slots per assessment
remain, with unused slots ignored. No project writes or recalculation were performed.

Saved displayed probabilities (LiFFT / DUET / ST): Ana 13.2 / 17.8 / 12.2%; Bruno 24.2 /
29.7 / 61.7%; Carla 44.7 / 50.5 / 97.8%; Diego 13.2 / 8.7 / 7.2%. No workplace assignments.
Exact source/result evidence and owner-file SHA-256:
[standalone checkpoint](../artifacts/owner_workflow_standalone_checkpoint.json).

Next owner test before organization setup: Ana > LiFFT, Reset without Save, inspect
cleared task inputs/results and unchanged 15-row count, then main Undo once. Original
30cm/49.05N/100 repetitions and 13.2% should return. Keep this step separate from trash
and saved-data chooser testing; their previously observed wording awaits that review.
No implementation change or repeated regression gate. Current code acceptance below
remains 1,701 tests/94.35%, Linux migration/cleanup 100%; Windows/macOS deferred.

---

# Application Undo limit — verified, 2026-10-19

Owner requests default 25/minimum 1 / maximum 50 shared Undo steps, as a software preference.
Tools > Settings > General > Undo steps now exposes the personal integer budget
in EN/ES. Apply persists across projects/restarts and updates the live shared session;
Cancel keeps the existing policy. Main/Workers/organization/Jobs/PLOT/JROT continue
using the existing chronology. Current data, revision IDs and the saved baseline
are preserved. Oldest excess snapshots are released on new operations; shrinking
prioritizes nearest Undo and may shorten Redo. Raising cannot recover discarded
steps. The budget does not create an Undo command or require project Save.
Native typing Undo retains its existing policy; no parallel history is introduced.

Required final native Linux gate: **1,701 passed, zero failures/skips, 94.35% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Focused source checks: 102 passed/two subtests; existing shared analysis history 31;
corrected preference compatibility/new budget checks 70. Independent extracted wheel:
**167 passed/two subtests**, all 243 Python files and both packaged guides equal
reviewed source. Twelve EN/ES native General states inspected: expanded section tree,
empty/loaded project, 1/25/50, footer/note/control fit. No clipping or theme change.

Seven package modules and five maintained test modules changed and substantively
reviewed; 431 files / 2,988 functions / 412 classes / 315 constants, zero pending/gaps.
Personal settings format 6 records the preference; old formats 1-5 load read-only with
25. The existing future-version test uses 7; old gauge fixtures omit later fields and
camera/decimal explicit writes expect 6. The preliminary 1,695-pass/six-expectation-
failure full gate remains separate; strict decoding and compatibility assertions
were retained. Native format16, scientific models, native codecs, dependencies,
reference, both maintained fixtures and owner workflow file remain untouched.

Linux migration/cleanup remains **100%**; Windows/macOS deferred, no new milestone.
Restart, open the workflow project and check General shows 25, range 1-50. Apply a
small value and check shared Undo stops there; restore 25 and resume independent
assessment entry and bottom-button review before organization setup. Root dist
rebuilt; old dist/linux M5 bundle is not republished.
[Acceptance](undo_limit_acceptance.md),
[validation](../artifacts/undo_limit_review/validation.json).

---

# Save availability — verified, 2026-10-19

Owner requests Save disabled when no data needs saving. Main toolbar, Project menu
and underlying command now use existing private project dirt, temporary first-Save
intent and pending task input. Numeric typing enables Save before field completion;
invalid input still uses existing validation. Undo/Redo reflects the last saved data,
including after Save. Management edits notify the main controls without closing the
window. Private deletion remains savable with no active assessment. Cancel/failure
retains availability; saved empty projects are clean; Save As remains available.
No second dirty flag, automatic calculation/save or new history/persistence path.

Required native Linux gate: **1,665 passed, zero failures/skips, 94.34% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Twenty new cases plus existing navigation/unified Save checks pass 50 focused tests;
corrected menu plus new checks pass 24; independent wheel passes **54 tests**, all
243 Python files and both packaged guides equal source. The first full gate's three
historical Save-disabled-after-deletion expectations were corrected, with ownership,
cancellation/recreation and reopen assertions retained; preliminary evidence is separate.
Native EN/ES LiFFT/DUET/ST saved/pending/mouse-Save states and Project menu states
are inspected; see the acceptance and exact visual record below.

Only two presentation modules and two test modules changed. All four substantively
reviewed: 430 maintained files / 2,976 functions / 412 classes / 312 constants,
zero pending/gaps. Scientific/application/storage code, dependencies and reference
remain untouched; both maintained fixtures and owner workflow file retain their
recorded hashes. Ana's corrected standalone DUET is saved complete at **17.8%**
(OMNI-RES 2 / 200 and 4 / 100). No organization added.

Linux migration/cleanup remain **100%**; Windows/macOS deferred. No new milestone.
Restart, reopen workflow_4_workers and verify Save starts disabled, enables after
an input edit, then disables after main Save. Resume independent assessment entry
and the owner's Reset/trash/saved-data chooser review before organization setup.
Root dist rebuilt; frozen dist/linux M5 bundle is not republished.
[Acceptance](save_availability_acceptance.md),
[validation](../artifacts/save_availability_review/validation.json).

---

# Field-by-field task history — verified, 2026-10-18

Owner requires Arm 50 then Load 60 to reverse Load first, then Arm. Previous fixes
covered availability/repeated rebinds, but pending-grid acceptance still grouped fields.
That boundary is corrected for every task input in LiFFT/DUET/ST: numeric completion
on departure/Enter and each selector choice submit only that cell through the existing
bound parser/source command and shared ProjectEditingSession cursor. Valid siblings
can complete beside invalid text without batching it. No widget rebuild, automatic
calculation, extra stack, schema/table/version/dependency or durable Save is added.
The existing Modified/context projection updates on accepted source changes; pure-focus
catalogue-authority protection and native typing Undo remain intact.

Required final native Linux gate: **1,645 passed, zero failures/skips, 94.35% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
The preceding gate's three old grouping expectations were corrected while preserving
numerical, invalid-input, Reset and reopen checks; its evidence remains separate.
The new focused module has **106 cases** covering all nine inputs, both row states,
EN/ES, metric/imperial, Tab/Enter/mouse, pending/revisited fields, invalid siblings,
stale/coordinate/no-op/native Undo, exact comma/cross-unit precision and projection guards.
Independent extracted wheel: **166 tests pass**, all 243 Python files and both guides
match reviewed source. Thirty final native states inspected, including VTK, ordered
input replay, source-bound results, Modified labels and bottom actions.

Ten changed maintained files substantively reviewed; 429 files / 2,971 functions /
412 classes / 312 constants, zero pending reviews/gaps. Seven package Python files
changed, all presentation; 236 package Python files and 76 resources match the prior
accepted wheel. Models/application/storage, reference, both maintained native fixtures,
owner workflow file and uv.lock unchanged. Linux migration/cleanup remain **100%**;
Windows/macOS remain deferred. No new milestone or unrelated repair.

Restart ErgoTools and retry the existing workflow: Arm 50, Load 60, main Undo twice,
then Redo twice. Each completed input must restore separately without Calculate.
See [acceptance](task_cell_history_acceptance.md) and
[validation](../artifacts/task_cell_history_review/validation.json). Earlier checkpoints
below are historical; dist/linux's old M5 delivery bundle is not republished here.

---

# Repeated task Undo and Project folder — verified, 2026-10-18

Owner-reported repeated task-edit Undo defect corrected. Shared history restored data,
but destination-only refresh deduplication left stale widgets on a fresh branch back
to the same earlier revision. Operation-plus-destination deduplication now rebinds each
reversal while suppressing nested notifications. Seventy-two regressions cover all nine
numeric/selector inputs, populated/empty rows, EN/ES and metric/imperial: 360 fresh
branches plus 216 intervening Redo/Undo pairs. Existing parsing/results/Save are unchanged.

Owner-requested **Project > Open project folder** uses the independent system file
manager. It is enabled for a loaded saved project, including an empty one, disabled
with no project or before first Save, and does not accept pending edits or Save.
Bilingual captions/errors and encoded Unicode/space/hash paths are checked. A real
Nautilus window remained after the ErgoTools test process exited; the private desktop's
inherited-Snap portal failure/delayed startup is recorded, without a system/launcher repair.

Required native Linux gate: **1,539 passed, zero failures/skips, 94.32% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Independent extracted wheel: **175 tests pass**, all 243 Python files and both guides
match source. Twenty-six application captures plus one OS-manager capture inspected.
Five changed maintained files substantively reviewed; 428 files / 2,961 functions,
zero pending/gaps. Both native fixtures, owner workflow file and uv.lock unchanged;
scientific/application/storage code and reference checkout untouched.

Linux migration and cleanup remain **100% complete**; Windows/macOS remain deferred.
No extra milestone. Restart ErgoTools and retry repeated task edits/Undo/Redo, then
Project > Open project folder. See [acceptance](repeated_task_undo_and_folder_acceptance.md)
and [validation](../artifacts/repeated_task_undo_review/validation.json). Earlier checkpoints
below remain historical; the independent dist/linux M5 bundle is not republished here.

---

# Pending task-input Undo — verified, 2026-10-18

Owner-reported Ana/Task 2 defect corrected for LiFFT, DUET and ST. Valid pending grid
input now exposes main Undo before Calculate. Existing pure parsing rules drive
availability without accepting data or truncating Redo. Mouse Undo accepts one grid edit
through the existing shared session and restores the previous inputs and matching
result; Redo restores the edit with obsolete results cleared. Invalid text is retained,
no-op input preserves Redo and focused typing Undo stays native. Only main Save publishes.

Required native Linux gate: **1,461 passed, zero failures/skips, 94.35% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Independent extracted wheel: **90 focused tests pass**, all 243 package Python files
and both guides equal reviewed source. Eighteen native EN/ES pending/Undo/Redo captures
inspected, including VTK, result cards and bottom controls. Nine changed maintained
files substantively reviewed; 428 files / 2,957 functions, zero pending documentation
reviews/gaps. Source models, application and infrastructure are byte unchanged from
the previous accepted wheel. No dependency/schema/reference or test-project edits.

Linux migration and cleanup remain **100% complete**; Windows/macOS remain deferred.
No new milestone. Restart the application, then resume Ana's existing Task 2 workflow
and try main Undo before Calculate. See [acceptance](task_input_undo_acceptance.md) and
[validation evidence](../artifacts/task_input_undo_review/validation.json).

---

# Independent task counts and unused rows — verified, 2026-10-18

Owner-approved correction complete for Linux. Settings identifies project, worker,
tool, workplace/shift/optional Job or standalone context and shows visible checkbox
indicators. Task counts stay independent per project/worker/tool/assignment, default
15 and range 1-100. Growth appends blanks; shrink keeps the exact prefix and confirms
before removing entered trailing rows. Same-count Apply is a no-op. Valid pending
input is retained; invalid text stays for correction. Shared Undo/Redo restores
truncated inputs and matching results. Main Save remains the durable boundary.

Unused rows no longer make a populated grid incomplete; started missing-input rows
remain partial, and entirely empty assessments claim no modeled probability. PLOT,
result cards and exports use the consistent new classification. Numeric models,
conversions and intrinsic precision are unchanged. Older saved classification metadata
is refreshed by Calculate/main Save, with no automatic project rewrite on Open.

Required native gate: **1,449 passed, zero failures/skips, 94.30% combined coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Independent extracted wheel: **100 tests pass**; all 243 Python files and both guides
match source. All 20 changed maintained files substantively reviewed; 428 files /
2,944 functions reviewed, zero pending/gaps. Twenty-four EN/ES native captures inspected,
including VTK, result cards, checkbox states, exact Job/no-Job/standalone captions and
removal consent. Eighteen actual dialog-frame indicator measurements confirm visibility.

Both maintained native fixture hashes, infrastructure, model calculators and approved
lock remain unchanged. Owner workflow project was not modified by this change; it now
has one saved Ana LiFFT task from the owner's earlier manual reset. Never restore an
older 15-row snapshot over current owner data. No reference writes, new schema/table/
assessment versions/dependency or milestone. Migration/cleanup remain 100%; native
Windows/macOS acceptance deferred. Root dist packages rebuilt; frozen dist/linux unchanged.
Existing Settings tree/footer clipping observations remain separately recorded.

Next: restart, reopen the workflow project and test lossless task-count changes with
Ana's existing values. Recalculate/Save to refresh any old classification metadata;
no data re-entry is required. Owner desktop acceptance remains pending.

[Acceptance and limitations](task_grid_resize_acceptance.md),
[validation](../artifacts/task_grid_resize_validation.json).

---

# Task-grid behavior audit — owner review, 2026-10-18

Owner clarifies independent count scope: per project, per worker, per tool. That is
already how assessment source counts are stored. Default 15 / range 1–100 and
separate tools are present. No global count/default scheme is required.

Confirmed gaps: shared transparent-checkbox styling hides the unchecked outline;
current count changes clear every row (even same-count Apply); unused blank rows
produce PARTIAL status. Existing Undo/Redo restores the original source, but growth/
shrink must instead preserve retained rows and only append/remove trailing slots.
Original code also rebuilt/cleared on count changes, so retained-row resizing is the
owner's improvement. Original incomplete warnings do not override current direction.

Audit only: 23 focused offscreen tests pass; nine three-tool resizing/history probes
and three unused-row calculation probes reproduce current gaps. Five offscreen
captures inspected. Native display startup hit automatic approval-review timeout;
no native repair acceptance claimed. No implementation, project writes, repeated full
gate or new milestone/dependency. Current accepted code gate stays 1,406/94.29%.
Migration/cleanup remain 100%; OS deferrals unchanged.

Keep Ana's populated task and 14 unused slots; do not force a one-row reset or re-entry.
Her one-of-15 scenario is valid for the intended workflow. Next: owner reviews the
bounded correction proposal before implementation and subsequent workflow testing.

[Detailed findings and proposal](task_grid_behavior_review.md),
[audit evidence](../artifacts/task_grid_behavior_review/review.json).

---

# Owner standalone LiFFT checkpoint — saved/reopened, task-count clarification pending

Owner confirms Ana/LiFFT survives main Save, Project Close and Recent Projects reopen.
Read-only database verification: one W01 standalone LiFFT assessment, assignment NULL;
30 cm / 49.05 N / 100 repetitions; saved probability 13.190999733969136%, displayed
13.2%. Saved result source equals current inputs; foreign keys valid. Four workers,
no plants/stations/Jobs/assignments, no assessments for other workers or tools.

Discrepancy reported before changes: requested one task, but 15 task slots are saved,
14 entirely blank. The result records PARTIAL status and 42 required-field issues.
Owner clarifies the task-count control was unknown; the 15 visible rows were left
unchanged. Instructions omitted its location; no persistence defect established.
Guide Settings > Assessment > Reset task grid on Apply > Number of tasks 1; warn
that reset clears inputs, then re-enter the same values, Calculate and main Save.
Save/reopen/standalone ownership checks
pass; do not certify the intended complete one-task case or silently remove blank rows.
Project inspected read-only and bytes unchanged.

No implementation or repeated regression gate. Migration/cleanup remain 100%; accepted
code evidence stays 1,406 tests/94.29%. Hiring-date report is owner-resolved (future
selection); past dates work and no correction was required. Next: complete the guided one-task reset and verify the saved complete result,
then continue existing owner-driven workflow testing.

[Saved checkpoint evidence](../artifacts/owner_workflow_ana_lifft_checkpoint.json).

---

# Worker form Undo availability — verified, 2026-10-18

Owner-reported reopen → edit Diego 65 to 85 → disabled Undo reproduced and corrected.
The worker form now exposes valid pending existing-worker edits to shared Undo before
Close. Mouse Undo accepts/reverses the edit in the open window; Redo reapplies it.
Native typing Undo remains local; invalid input and new-worker acceptance boundaries
remain intact. Close retains session edits; only main Save writes the project file.
Earlier acceptance tests missed this pending-form availability case; their unchanged
coverage/evidence remains valid, supplemented by the new regressions.

Required native gate: **1,406 passed, zero failures/skips, 94.29% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Forty focused native checks and forty independent-wheel checks pass. Twelve EN/ES,
metric/imperial pending/Undo/Redo captures inspected. All three changed maintained
files substantively reviewed; all 428 files/2,929 functions remain reviewed with zero
pending/gaps. All 243 packaged Python files and both HTML guides match source.

No schema/dependency/formula change, reference/fixture writes, or new milestone.
The owner workflow project was not opened by these checks. Both maintained native
fixtures and approved lock remain unchanged. Root dist packages rebuilt; frozen
dist/linux bundle unchanged. Migration/cleanup stay 100%; Windows/macOS deferred.
Next: restart and repeat the weight edit/Undo with Worker Management still open,
then continue the existing owner workflow test. Owner acceptance remains pending.

[Correction and evidence](worker_pending_undo_acceptance.md),
[validation](../artifacts/worker_pending_undo_validation.json).

---

# One main project Save and shared history — verified, 2026-10-18

Owner-approved workflow correction complete for Linux. Worker, organization, Job,
assessment, PLOT and JROT editors retain accepted edits until main Save and share
chronological Undo/Redo. Four worker additions are four actions; closing their window
adds none. Record-removing replay confirms exact affected identities with Cancel as
default. Invalid form text and partial JROT drafts remain available; project departure
retains Save/Discard/Cancel. No dependency/schema/formula change or new milestone.

Required final native gate: **1,400 passed, zero failures/skips, 94.28% combined
coverage**. Standards/types (265), architecture/naming, documentation/review (428 files,
zero pending/gaps) and builds pass. All 42 changed maintained files substantively
reviewed. Independent final wheel: 50 native tests pass; all 243 Python files and both
HTML guides match reviewed source. Sixty-four EN/ES captures inspected, including VTK,
empty/populated/expanded editors, accepted assignments, PLOT demographics and retained
JROT partial/complete states. Copies of both maintained native fixtures verify exact
Undo restoration and preservation of unrelated table rows/results/images/schemes.

Both maintained fixture hashes and the approved lock remain unchanged. Owner workflow
project was read only: four workers, Diego 65 kg, no organization/Jobs/assignments/
assessments. No original reference writes; 490/500 old manifest hashes match, with ten
pre-existing October 12 differences recorded explicitly. Current root dist packages
are rebuilt/verified; the frozen dist/linux bundle is not republished here.

Migration/cleanup remain 100%; Windows/macOS native acceptance stays deferred.
Next: restart the application, reopen workflow_4_workers.ergprj and resume owner-driven
workflow testing. Owner desktop acceptance is pending; no unrelated improvement is
started. See the handoff for existing table-fit/platform-label limits.

[Acceptance](single_project_save_acceptance.md),
[workflow/architecture](single_project_save.md),
[validation](../artifacts/single_project_save_validation.json).

---

# Worker calendar correction and owner workflow pause — 2026-10-18

Owner reports four workers survive Save/close/reopen. Read-only saved-file review
confirms demographics and no organization/assignments/Jobs/assessments, with one
reported data difference: W04 weight is 85 kg versus the suggested 65 kg. Left intact.

Blank birth-date calendars now browse eighteen years before today without assigning
a birthday; saved dates remain unchanged. Eleven focused tests pass; eight native
EN/ES blank/saved form/popup captures inspected. Final required gate passes:
1,381 tests, zero failures/skips, 95.40% coverage; standards/types/
documentation/review/builds pass. Packaged changed source matches reviewed source.

Unified main Save is reviewed as a proposal: current worker commits are immediate,
Close drops unsaved form text, and main Save owns assessment drafts. Retained
worker drafts and project Save/Discard/Cancel integration are needed; no unified
saving implementation is included. Manual testing stays paused at workers.
Migration/cleanup remain 100%; no new milestones/dependencies/schema changes.

[Acceptance and proposal](worker_birth_calendar_acceptance.md),
[worker checkpoint](../artifacts/owner_workflow_workers_checkpoint.json).

---

# PLOT comparison typography aligned — implemented, 2026-10-17

Individual average / Job average share Risk ranges' 13 px heading rule. Their risk
subtitles now share the compact legend's 12 px rule, increased from 11 px. Only
presentation/desktop/theme/plot.py changes; colors/weights, bottom captions, gauge
geometry, tick preferences, data and other controls remain unchanged.

Final Linux gate: **1,379 passed, zero failures/skips; 95.40% coverage**.
Standards/types (262)/documentation (423)/review/build checks pass. The changed
stylesheet was substantively reviewed and matches the rebuilt wheel. Twelve native
EN/ES LiFFT/DUET/ST minimum/enlarged captures inspected; actual Qt font sizes and
rich-text width fit verified. Both maintained fixture bytes and approved lock match
this round's starting values. No project/reference/dependency/formula changes.

Migration/cleanup stay 100%; no new milestone. Existing chart-fit/animation
observations and deferred Windows/macOS acceptance remain separate.
Next: owner Linux visual feedback; no further implementation is active.

[Acceptance](comparison_gauge_typography_acceptance.md),
[validation](../artifacts/comparison_gauge_typography_validation.json).

---

# Application gauge defaults and persistence — implemented, 2026-10-17

Shared main/PLOT gauges now default to visible ticks every ten percentage points
and visible range limits. Explicit saved options are preserved. Pre-v5 personal
settings use the same defaults without writes on load. No project/dependency/
formula/reference changes. Native/personal formats remain 16/5.

Comparison typography has not changed: titles 13 px, risk subtitles/captions 11 px;
the full PLOT stylesheet equals the earlier Linux delivery baseline.

Final Linux gate: **1,379 passed, zero failures/skips; 95.40% coverage**.
Standards/types (262)/documentation (423)/reviews/builds pass. Three changed files
reviewed; both production modules and bilingual HTML guides match the rebuilt wheel.
Six native EN/ES main/PLOT/Settings captures inspected. Migration/cleanup stay 100%.

Owner confirms gauge choices are application preferences, shared across projects
and retained across restarts. The in-progress project-storage change was withdrawn;
source bytes match the tested wheel. No project schema/table change remains.
Next: owner testing feedback. No new milestone or additional implementation is active.

[Acceptance](gauge_ten_default_acceptance.md),
[validation](../artifacts/gauge_ten_default_validation.json).

---

# PLOT outer inset aligned with JROT — implemented, 2026-10-17

PLOT now has ten-pixel outer margins on all sides, matching JROT. Window dimensions
add 16 pixels of width and 4 of height to retain the internal panel space. Only
plot_window.py changes. No dependency, formula, project, history or reference edits.

Final Linux gate: **1,379 passed, zero failures/skips; 95.40% coverage**; standards,
types (262), documentation (423), review and builds pass. Eight EN/ES native captures
inspected; changed source equals wheel. Insets and preserved inner width verified.
Both maintained fixture bytes and approved lock remain unchanged this round.

A minimum-size chart-label/selector overlap on direct Comparison selection also
reproduces in the prior accepted wheel with the same interior width. It is recorded
separately, not repaired or visually accepted in this margin-only request.
Migration/cleanup remain 100%; no new milestone. Next: owner Linux testing feedback.

[Acceptance](plot_outer_margin_acceptance.md),
[validation](../artifacts/plot_outer_margin_validation.json).

---

# Owner-reported PLOT/JROT/context layout corrections — implemented, 2026-10-17

PLOT gauges retain their full compact arc radius and complete range labels. Standalone
assessment is a separate footer button outside the context hierarchy. PLOT and JROT
have Undo/Redo at the right of their main title row; extra menu/history bars are gone.
Existing shortcuts, typing/source history, solver interlocks and Save controls remain.
PLOT now reserves the full plant toolbar and useful chart height, propagating wrapped
text/demographic minima so the window grows rather than clipping. Image scrollbars
remain off. No calculation, ownership, schema, dependency or reference changes.

Final Linux XCB gate: **1,379 passed, zero failures/skips; 95.4% coverage**.
Standards/types (262)/documentation (423 files)/reviews/builds pass. Sixteen changed
code/test files substantively reviewed; ten production modules and both HTML guides
match the wheel. Forty-two native EN/ES captures inspected across disclosure/risk
modes, minimum/enlarged sizes, saved/draft JROT and empty/populated context. Final
geometry checks confirm full rail bounds, visible chart/control separation and no
plant-image scrollbars. Both maintained native projects and approved lock retain
this round's starting hashes; no fixture restore or parallel test projects.

Migration/cleanup stay 100%; no new milestone. Native Windows/macOS remain deferred.
Measured content minima and smaller-work-area limits are recorded in acceptance.
The previously recorded main animation endpoint issue remains unchanged/separate.
Next: owner Linux testing feedback; no additional implementation is active.

[Acceptance](plot_layout_followup_acceptance.md),
[validation](../artifacts/plot_layout_followup_validation.json),
[visual record](../artifacts/plot_layout_followup_review/validation.json).

---

# Shared gauges and section Settings — implemented, 2026-10-17

Owner-requested follow-up shares one RiskGauge implementation and personal marker
settings across main and all PLOT gauges. Settings now uses a section tree and
retained pages; range numbers have greater clearance from tick lines. Owned input
forms/prompts share the application theme. At the owner's explicit request, system
file/color/font selectors keep default native appearance: no forced Qt picker,
custom file browser or theme event filter.

Final Linux XCB gate: **1,379 passed, zero failures/skips;
95.41% coverage**. Standards/types (262)/documentation (423 files)/reviews/builds
pass. Twenty changed code/test files substantively reviewed. Fifteen production
modules and both HTML guides match the rebuilt wheel. Fifty-eight native owned-UI
captures inspected. Live system-picker responsiveness remains manual after restart;
automated tests verify configuration only. Earlier forced-picker screenshots/logs
are superseded. Existing main 100% animation issue remains unchanged and separate.

Native schema remains 16 and personal settings format 5. No formula/dependency/
reference changes or fixture writes by this implementation. Integrated fixture and
lock match recorded hashes. The owner's active comparative test project differs
from its earlier checkpoint and is preserved as-is; this is not a migration defect.
Migration/cleanup stay 100%; no new milestone. Windows/macOS acceptance is deferred.
Next: owner Linux feedback, including default native Open/Cancel and Save selectors.
No additional implementation is active.

[Acceptance and manual checks](settings_shared_gauge_acceptance.md),
[validation](../artifacts/settings_shared_gauge_validation.json).

---

# Configurable assessment-gauge markers — implemented, 2026-10-17

Owner-requested marker improvement is complete: main assessment gauge shows the
existing 0/25/37.5/50/100 range limits and unlabeled ticks every five percentage
points by default. Tick/label visibility is independent; intervals are configurable.
Owner selected both right-click immediate controls and saved Settings controls.
Both use the same personal preference; restart retains choices. EN/ES and metric/
imperial states are verified. Existing gauge arc/colors/needle geometry remain.

Final native gate: **1,369 passed, zero failures/skips; 95.47% coverage**. All
standards/types (261)/documentation (421 files)/review/build checks pass. Twelve
changed code/test files reviewed; eight packaged modules and bilingual HTML guides
match the rebuilt wheel. Twenty-two native captures inspected. Both native fixture
hashes match the session handoff; reference/approved lock unchanged. Project schema
stays 16; only personal settings advance to format 5, retaining read support for
versions 1-4. No dependencies/formulas/project data or PLOT gauge changes.

Separately reproduced: unchanged _AnimatedScale interpolation can retain a stale
value/needle at the 100% endpoint because its original clamp produces an integer
end value. This behavior is not visually accepted; no repair was included in marker
scope. See acceptance and review register for the concrete reproduction.

Migration/cleanup remain 100%; no new milestone or automatic extra implementation.
Next: owner visual testing of marker interval/visibility, and owner direction before
any separate animation repair. Windows/macOS native acceptance remains deferred.

[Acceptance and architecture](gauge_markers_acceptance.md),
[validation](../artifacts/gauge_markers_validation.json),
[native visual record](../artifacts/gauge_markers_review/validation.json).

---

# Context chooser follow-up — implemented, 2026-10-17

Owner-requested Standalone assessment choice is inside Select assessment context;
its separate main-window button is removed. The chooser supports workers without
assignments; association-only dialogs still require real assignments. No change
to ownership, source/results, schema 16, calculations, units or dependencies.

Final native gate: **1,348 passed, zero failures/skips; 95.45% coverage**; all
standards/types/documentation/build checks pass. Eighteen EN/ES captures inspected;
compact saved-standalone body-caption overlap is recorded, enlarged states fit.
No blanket compact visual acceptance is claimed. Both maintained fixture bytes
match this session's handoff; reference untouched. Migration/cleanup stay 100%.
Next: owner testing feedback; no additional implementation is authorized.

[Acceptance and limitation](context_chooser_acceptance.md),
[validation](../artifacts/context_chooser_validation.json).

---

# Optional assessment organization — complete, 2026-10-14

The owner-approved change is **100% complete**: direct worker assessment ownership,
optional real workplace/Job context, collapsible integrated controls, and scenario
integration with clean in-place test-project upgrades. Native format 16 requires a
worker and tool; its assignment link is optional. No artificial Default records,
assessment versions, duplicate calculation results or extra business tables are created.
Existing Default organization in both maintained fixtures is genuine and retained.

New starts an actually empty project. Standalone LiFFT/DUET/ST save without organization
or Jobs. The footer context checkbox reveals the optional frame without reserving height
when collapsed. Opening a project with real organization expands it. Associate assessment
links only the chosen saved tool to a same-worker real workplace; inputs/results stay
unchanged. PLOT Individual accepts workplace assignments without Jobs; JROT All Jobs
still needs only workers and approved Job risks. Existing station/shift uniqueness,
source units, original calculations, localization and historical reference protection stay.

Final baseline gate: **1,347 passed, zero failures/skips; 95.45% coverage**. Strict types
(259), naming/architecture, in-code documentation (418 maintained files), 53 changed-file
semantic reviews and builds pass. Fifteen native English/Spanish captures were inspected
at the target size and with enlargement. Main VTK/result cards/footer fit; no new icons
or dependencies. Actual association controls, rollback/conflicts and real CBC/HiGHS
job-only solve/save/reopen are verified.

Both test_projects/native files are updated IN PLACE to format 16 and open directly:
194 assessments/results each, four images each, seven/five JROT schemes. Every unrelated
row and exact source/result payload is unchanged. No backup or parallel fixture folder
was created. The external converter remains separately removable under tools/project_migration.

[Schema, workflows and rollback](optional_assessment_context.md),
[validation](../artifacts/optional_assessment_validation.json),
[fixture preservation](../artifacts/optional_assessment_fixture_validation.json).
Restart running application instances before owner testing. Original migration/cleanup
ledgers remain complete at 12/12 and 6/6; Windows/macOS native testing stays deferred.
No additional implementation is authorized by this completed task. Historical records follow.

---

# Test-project path correction — complete

The owner-requested fixture cleanup is complete. Both maintained format-15 files
now replace the outdated files at their established test_projects/native paths.
The duplicate test_projects/current folder is removed. Both files open without
migration, retain 194 assessments/results, and pass SQLite integrity/foreign-key
checks. No application logic, schema, dependencies or reference files changed.
Current launch instructions and packaged bilingual help use the established paths.
Previous upgrade evidence below records the earlier separate-copy procedure only.

---

# Current Linux correction — unrequested assessment versions removed completely

The four approved correction areas are **4/4 complete (100%)**: version UI/handlers,
version model/mutation API, database version storage, and conversion/workflow acceptance.
Each Job assignment/tool now has one assessment. Full native format 15 uses only
assessment_ownership(document_id, assignment_id, kind, position), with unique owner/tool
and enforced assignment foreign key. No assessment version/status/current flag or unused
full-project binding table remains. Job risk-profile/file-format versions remain functional.

Final gate: **1,334 tests passed, zero failures/skips; 95.66% combined coverage**;
all standards/docs/types/build checks pass (259 typed sources/tools, 417 maintained files,
55 changed files reviewed). Ten independent database/menu cases and thirteen native
English/Spanish captures accepted. Both current projects retain 194 assessments/results,
embedded images and seven/five schemes; integrity/FK checks pass. All unrelated format-14
rows including JROT timestamps and real inputs/results are preserved exactly. Old files
and reference application unchanged; no dependency, calculation or new milestone.
Fixed migration/cleanup ledgers remain 12/12 and 6/6.

Use test_projects/native/comparative_risk_test.ergprj or integrated_test.ergprj.
[Correction/upgrade contract](single_assessment_ownership.md),
[every table's purpose](database_tables.md), [validation](single_assessment_validation.json).
Restart existing app instances. Historical checkpoints follow.

---

# Current Linux follow-up — worker assignment actions and 25-pixel menus accepted

Both requested implementation areas are **2/2 complete (100%)**: exactly 25-logical-pixel
menu icons (including styled PLOT/JROT menus) and explicit per-row Change/Remove Job
assignment actions. History ownership is preserved; cancellation/pending classification
protections and English/Spanish UI are validated. The Workplaces count, current JROT
constraints/extension points and Save As versus Backup are [explained](assignment_actions.md).

Final gate: **1,337 tests passed, zero failures/skips; 95.74% combined coverage**;
required standards/docs/build checks pass (258 typed sources/tools, 415 reviewed files,
6 changed/new maintained files reviewed). Twenty-eight native captures inspected. All
194 saved sources/results and original fixture bytes unchanged. Existing edited Undo/
Redo artwork is preserved with refreshed integrity/provenance metadata. No added
milestones/dependencies/reference edits or JROT constraints; ledgers stay 12/12 and 6/6.

[Acceptance and behavior](assignment_actions.md),
[validation](assignment_actions_validation.json). Restart existing app instances.
Historical checkpoints follow.

---

# Current Linux follow-up — Properties, menu icons and assessment scroll accepted

The three requested correction areas are **3/3 complete (100%)**: themed native-only
Project Properties, approximately 20% larger menu icons, and edit-time viewport
restoration for assessment Undo/Redo. Icon editing/restart/manifest instructions are
[documented](icon_editing.md). Architecture, naming and documentation remain mandatory.

Final gate: **1,329 tests passed, zero failures/skips; 95.75% combined coverage**;
required standards/docs/build checks pass (258 typed sources/tools, 414 reviewed files,
12 changed/new files reviewed). Guide follow-up: 16 tests and 78 subtests passed.
Native English/Spanish states inspected, including Default worker DUET with 50 tasks
and first/middle-row replay. All 194 saved sources/results and fixture bytes unchanged.
No added milestones/dependencies/reference edits; fixed ledgers stay 12/12 and 6/6.

[Acceptance and scope](properties_scroll_acceptance.md),
[validation](properties_scroll_validation.json). Restart existing app instances.
Historical checkpoints follow.

---

# Current Linux follow-up — Workplace and assessment interaction history accepted

The five owner-requested areas are **5/5 complete (100%)**: .ergprj-only project
pickers/default suffix and invalid-container checks; grouped setup toolbar/menu export;
Workplace menu rename; verified working Properties retained; chronological assessment
worker/tool/context and immediate DUET/ST selector Undo/Redo. Save/Discard/Cancel and
native typing protections remain. No global database Undo is claimed.

Final gate: **1,320 tests passed, zero failures/skips; 95.77% combined coverage**;
required standards/docs/build checks pass (257 typed sources/tools, 412 reviewed files,
14 changed/new files reviewed). Native EN/ES behavior/layout inspected, including final
nine-button header fit. All 194 comprehensive saved sources/results and fixture bytes
remain unchanged. No added milestones/dependencies/reference edits; fixed ledgers
stay 12/12 and 6/6.

[Acceptance, behavior and scope boundaries](workplace_interactions_acceptance.md),
[validation](workplace_interactions_validation.json). Restart existing app instances.
Historical checkpoints follow.

---

# Current Linux correction — avatar click/rotation conflict fixed

The owner-reported defect was reproduced: held clicks reached VTK's camera handler
before release-time picking. Immediate-click tests had missed it. The viewport now
holds candidate clicks away from VTK and starts native dragging only after movement
exceeds five pixels. Correct tool selection and optional focus animation are preserved.

This bounded correction is **100% complete**. Final gate: **1,313 tests passed, zero
failures/skips; 95.80% combined coverage**; required standards/docs/build checks pass.
Twelve realistic held-click native EN/ES captures inspected. Both animation preferences,
neutral clicks, real dragging/release and all three tool selections verified. All 194
saved comprehensive sources/results and fixture bytes remain unchanged. No added
milestones/dependencies/reference edits; migration/cleanup stay 12/12 and 6/6.

[Cause, corrected behavior and evidence](avatar_click_acceptance.md),
[validation](avatar_click_validation.json). Restart running instances for this fix.
Historical checkpoints follow.

---

# Current Linux follow-up — visible history and avatar selection accepted

The owner's four requested changes are **4/4 complete (100%)**: static mirrored Redo
asset; first-position main Undo/Redo with menu-only Settings/Help; themed PLOT/JROT
history strips; built-in VTK colored-region selection with existing focus animation.
Final gate: **1,311 tests passed, zero failures/skips; 95.79% combined coverage**.
All standards/documentation/build checks pass; guide/resource follow-up 16 tests and
78 subtests passes. Twenty-three native EN/ES captures inspected. All 194 comprehensive
saved assessment sources/results and permanent fixture remain unchanged.
No added milestones/dependencies/reference edits. Migration/cleanup stay 12/12 and
6/6. Dedicated Retire icon remains pending; Redo is now supplied locally.

[Acceptance and behavior](history_toolbar_acceptance.md),
[validation](history_toolbar_validation.json), [icon inventory](icon_inventory.md).
Historical checkpoints follow.

---

# Current Linux follow-up — display, Settings, avatar and icons accepted

The four owner-approved corrections are **4/4 complete (100%)**: compact configurable
project display precision with exact data retention, unified Settings/task count,
simultaneous assessment body-region colors, and reuse/inventory of processed icons.
Final gate: **1,308 tests passed; zero failures/skips; 95.81% combined coverage**.
All required standards, documentation and build checks pass. Native EN/ES states were
inspected; all 194 comprehensive-project sources/results remain unchanged.
Missing dedicated icons and the existing Spanish minimum-width text-fit limitation
are documented. No new milestones/dependencies/reference edits. Fixed migration and
cleanup ledgers remain 12/12 and 6/6.

[Acceptance and limits](display_settings_acceptance.md),
[validation](display_settings_validation.json), [icon inventory](icon_inventory.md).
Historical checkpoints follow.

---

# Current Linux follow-up — popup/PLOT visual fixes accepted

The reported worker selector hover contrast and PLOT Apply Filters background are
fixed using the current original control styling. Worker popup selected/hovered rows
are white on teal; PLOT Apply reconnects to its existing teal style/white icon.
No assessment risk colors changed: all 313 original palette entries and 30,042
sampled damage mappings match exactly; categorical gauge colors/thresholds match too.

This requested follow-up is **100% complete**, with no added milestones/points.
Final gate: **1295 tests passed, zero failures/skips; 95.97% combined coverage**.
All required standards/documentation/build gates pass. Fourteen native English/Spanish
captures inspected, including popup selection/hover/keyboard and PLOT enlargement.
The reference, fixture data, dependency baseline and scientific calculations remain
untouched. Fixed migration/cleanup ledgers remain 12/12 and 6/6 respectively.

[Correction details and assessment-menu explanation](visual_corrections_acceptance.md),
[validation](visual_corrections_validation.json). Historical acceptance follows.

---

# Current Linux follow-up — assessment navigation accepted

The owner-approved updated-reference context behavior is implemented in the new
architecture: automatic project opening, all-worker navigation, Follow worker/Keep
context, remembered contexts, Saved/New assignment picker, retained tool drafts,
read-only unclassified data and same-Job/different-workplace Save confirmation.
Work Setup contains Organization and Jobs and Risk Profiles; Jobs leaves the toolbar.

**This follow-up is complete.** Final gate: **1293 tests passed, zero failures/skips;
96.02% combined coverage**. Required standards, complete changed-code documentation
review and builds pass. Twelve native EN/ES captures inspected at 1548×1040 and
1800×1120 with VTK; all 28 comprehensive-project workers navigable with DUET selected.
Browsing does not change project bytes. Reference tree, fixture files, formulas,
project format and approved dependencies remain untouched by this work.

Historical Linux migration remains 12/12 (100%); cleanup remains 6/6 (100%). No new
milestones/points or denominator changes. Windows/macOS native testing remains deferred.
Use the existing `bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"`.

[Current behavior, architecture and regression catalog](assessment_navigation_acceptance.md),
[validation](assessment_navigation_validation.json),
[native captures](../artifacts/assessment_context_review/validation.json).
Historical checkpoints below retain their original evidence and counts.

---

# Linux cleanup complete — M5 accepted

**6/6 fixed cleanup milestones complete, 100%.** M1, M1R, M2, M3, M4 and M5
are accepted. Owner acceptance testing can begin using the current native fixtures.
No added milestone or silent scope expansion. Native Windows/macOS testing remains
explicitly deferred; this completes the owner-approved Linux cleanup scope.

Final Linux gate: **1,282 tests passed, zero failures/skips; 96.25% combined coverage**.
Ruff/format, strict mypy (250), architecture/naming and both documentation checks pass.
All **401 Python/stub files, 2,672 functions, 391 classes and 301 constants**, plus
two shell entries, remain reviewed; zero pending reviews or structural gaps. Every
residual path in 86 files is reviewed and recorded. All collected tests pass;
coverage measures code execution, not the test pass rate.

Installed current application: both relocated self-contained projects (194 results,
four images each, seven/five rotations), exact whole-database Save As/Backup/restore,
real CBC/HiGHS Qt threads, positional relative/spaced CLI and EN/ES recency pass.
Sixteen native captures inspected, including main/PLOT/JROT enlargement and VTK for
all tools. Final guide-only updates pass 16 Help/resource tests and 77 subtests.
Final refreshed Linux artifacts/guides, separate removable converter and native
review projects are in dist/linux. No new application code/formula/schema/UI changes.

Run `bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"` from
this new project; use Save As for a personal copy. Or open
`test_projects/native/integrated_test.ergprj`. Each native file needs no original
folders or converter. Originals/reference/assets/lock remain unchanged. Existing
unsupported old samples and Spanish minimum-width text-fit observations are explicit
in the acceptance report; no unapproved repairs were added.

[M5 acceptance](cleanup_m5_acceptance.md), [validation](cleanup_m5_validation.json),
[coverage review](cleanup_m5_coverage_review.md), [Linux delivery](linux_delivery.md),
[fixed ledger](cleanup_progress.json), [documentation inventory](cleanup_documentation_inventory.json).

---

# Linux migration complete — M12 accepted

**100/100 of the owner-approved Linux scope; 12/12 milestones closed;
26/26 fixed remaining points earned.** On 2026-10-11 the owner confirms Linux
is the migration completion target. Windows/macOS native acceptance is explicitly
deferred to later work; no native success on those platforms is claimed.

Run `bash tools/run.sh` from the new project; installed command `ergotools`.
The launcher opens the integrated application with VTK and per-user preferences.
Pass --settings explicitly to retain earlier development preferences.

Independent installation, 17 exact runtime pins, 71 assets, VTK, CBC/HiGHS,
disconnected operation and comprehensive copied-project backup/reopen pass.
Historical pre-cleanup gate: 1,242 tests, 96.48% coverage; all standards/builds pass.
Historical pre-cleanup wheel: 66 focused tests/77 subtests; 238 Python files and guides match source.
M12 native evidence retained; five positional-startup/recent-menu EN/ES captures
inspected. Original reference and lock unchanged.

Original UI/workflow/calculation and comprehensive-copy parity evidence is in
the accepted M01–M11 records, especially [M10 integration](m10_acceptance.md).
Reuse that evidence. The owner will first confirm the Linux application against
the prior codebase in normal use; later Windows/macOS tests are separate follow-up.
Do not start speculative infrastructure, new milestones or unrequested repairs.
Record concrete mismatches for bounded review under existing scope control.

Owner-requested original positional CLI project opening is restored:
`bash tools/run.sh "/path/project.ergprj"`. Successful opens populate the existing
Project > Recent projects / Proyecto > Proyectos recientes menu. No extra
milestone/points/dependency. [Correction acceptance](cli_project_acceptance.md)
and [current validation](cli_project_validation.json) supersede historical M12
build hashes for the current wheel. The original completion evidence is retained.

[Launch/install/recovery](linux_delivery.md), [M12 acceptance](m12_acceptance.md),
[validation](m12_validation.json), [platform review](platform_review.md),
[fixed ledger](finish_progress.json), [delivery checksums](../dist/linux/SHA256SUMS).

Owner-approved analysis history extension is complete: PLOT accepted filters,
retained demographic activation/values, tool/view/workplace and marker edits share
one timeline; JROT tool and pending/applied scope join existing draft history.
Main assessments now have platform Undo/Redo shortcuts with native typing
ownership. Keyboard/menu only; existing Save controls remain. Eighteen EN/ES
native captures inspected; comprehensive project-copy bytes, reference and lock
unchanged. No new milestones/points/deps. Current wheel/hash evidence is in
[analysis history acceptance](analysis_history_acceptance.md) and
[validation](analysis_history_validation.json), superseding earlier delivery hashes.
Unified saving and arrow controls are deferred owner ideas. No further work is
authorized by this completed extension; normal owner Linux review comes next.

---

## Historical milestone records

# Active milestone — M12 delivery

Owner authorizes M12. Independent Linux install/launcher/offline recovery and
platform review in progress. Remains 97.75/100 until fixed criteria close.

---

# Current authoritative control state — M11 complete

**97.75/100 overall; 11/12 complete; 23.75/26 earned; 2.25 points remain.**
All three fixed M11 criteria are verified. Owner-approved CR007 restores original
Find Assessment Search from its source layout, with tool/name/alphabet/workplace
filters and exact historical/cross-worker selection. Cancel and dirty choices
preserve source intent. No added milestone, points, dependencies or formulas.

Original inventory: 41 top-level modules, 490 connections and event overrides;
active mappings and hidden/dormant classifications documented. Public-symbol
inventory: 1,322 symbols with docstrings; API unit/error/source review complete.
Current EN/ES user, developer/architecture/recovery guides replace obsolete
preview instructions. Help opens the current packaged localized offline guide.

Final gate: **1,221 tests, 96.41% coverage**, all standards/types/architecture and
builds pass. Independent wheel: 30 focused tests, 77 subtests, native source-layout
comparison and 12 inspected Search captures. EN/ES guide rendering inspected.
All 236 package Python files, guide bytes, 500 reference hashes and lock verified.
Accepted M01–M10 evidence reused. Reference and operational projects untouched.

[Acceptance](m11_acceptance.md), [validation](m11_validation.json),
[review](m11_review.md), [feature inventory](feature_inventory.md),
[fixed ledger](finish_progress.json).

Only M12 remains: independent Linux delivery/launcher/offline recovery and final
handoff, with native Windows/macOS acceptance explicitly deferred as documented.
M12 is not started or authorized in this batch. Do not repeat passed full checks
without changed code, failure or a concrete unresolved requirement.

---

## Historical M11 start and M10 records

# Active milestone — M11

Owner authorized M11 only; inventory and documentation review in progress.
95.25/100 until all three fixed criteria close. M12 not started.

---

# Current control state — M10 complete

**95.25/100 overall; 10/12 complete; 21.25/26 earned; 4.75 points left.**
M10 earns its fixed 0.75 points. Both final copied-project criteria are verified.
Owner-approved CR006 preserves exact saved/imported results during Copy/Move;
rounding, recorded/fresh status, unit labels and source binding survive reopen.
No formula, UI layout, dependency or reference change.

Final rebuilt-wheel scenario passes workers/organization/jobs, all three original-
equivalent Calculate/Save paths, PLOT, CBC/HiGHS Apply/Save, Transfer, all-tool
CSV exports, backup and native Spanish reopen. Final copy: 29 workers, 105
assignments, 197 summaries, seven schemes; 191 unchanged original summaries.
Twelve native captures inspected. All 500 reference hashes and approved lock
unchanged. Original immutable archive retained.

Required gate: **1,207 tests, 96.42% coverage**; lint/format/types/architecture and
wheel/sdist pass. Independent wheel passes 23 new transfer regressions and actual
fresh/imported transfer probes. Accepted M01–M09 evidence reused.

[Acceptance](m10_acceptance.md), [validation](m10_validation.json),
[review](m10_review.md), [fixed ledger](finish_progress.json).
Next: M11 inventory/documentation (2.50 points), then M12 delivery/platform
readiness (2.25 points). M11 not authorized/started. Windows/macOS native VM
testing remains deferred; only Linux XCB is claimed passed.

---

## Historical M10 pre-approval state

# Active milestone — M10 partial; CR006 approval requested

**94.50/100; 9/12 complete; 20.50/26 earned; 5.50 points left.**
Copied-project integration reached assessment/PLOT/JROT saves, exports and backup.
Transfer omits exact saved/archived result records; final acceptance stops there.
No new repair applied. See [review](m10_review.md), [validation](m10_validation.json)
and [bounded CR006 proposal](m10_transfer_result_proposal.md). M11 not started.
Full gate reused from M09; original 500 manifest files and approved lock unchanged.

---

# Active milestone — M10

Owner authorizes M10 on 2026-10-11. Final comprehensive copied-project scenario
in progress; 94.50/100 until both criteria close. M11 not started.

# Current control state — M09 complete

**94.50/100 overall; 9/12 complete; 20.50/26 earned; 5.50 points left.**
M09 earns its fixed 1.75 points after all three acceptance criteria close.
M09 approval covered its CR005 repair; subsequent M10 authorization is recorded above.

Owner-approved CR005 restores original Current Project:/Loaded header/footer
captions with Spanish equivalents. Empty/unsaved/first-Save/Close and pending
assessment edits retain original behavior; stored titles remain literal. Shared
EN/ES/unit/avatar checks pass. Authors prose is localized; R011 and Transfer
paragraph concerns close without unnecessary layout changes. No new milestone,
scientific change, dependency change or reference modification.

Final approved-baseline gate: **1,184 tests, 96.40% coverage**, standards/types/
architecture and wheel/sdist pass. Final independent wheel passes 30 caption/
lifecycle regressions and native EN/ES main-window acceptance. Fourteen final
captures inspected, supplementing 34 valid earlier shared captures and accepted
M01–M08 component evidence. Full project caption, VTK region, cards, task headers,
context/footer and bottom controls fit at 1550×1015 and 1800×1200. All 500 reference
manifest files and the exact dependency lock remain unchanged.

[Acceptance](m09_acceptance.md), [bounded review](m09_review.md),
[validation](m09_validation.json), [fixed ledger](finish_progress.json).
Next: M10's one final comprehensive copied-project workflow; M11 inventory/current
guides; M12 Linux delivery and deferred Windows/macOS native target decisions.
M10 was subsequently authorized by the owner. Linux XCB is
validated here; other platforms are not claimed passed.

---

## Historical M09 pre-approval state

**92.75/100; 8/12 complete; 18.75/26 earned; 7.25 points left.**
M09.2 and M09.3 pass; M09.1 awaits the owner's CR005 decision. No M09 completion
credit is awarded until all criteria close. M10 has not started.

Shared EN/ES/unit/avatar checks pass from the built wheel. Authors prose now
translates to Spanish with attribution, link, logo and original layout preserved.
R011's caption fits actual font ink and individual PNG; Transfer paragraphs render
Spanish already. No sidebar or Transfer layout change was necessary.

New original-parity finding: the live original header/footer prefix project names
with Current Project:, and the header adds • Loaded. The migrated UI omits both.
A concrete original-caption patch is prepared but NOT applied; the owner was asked
to approve the bounded repair or explicitly approve the current captions as an
exception, as required by the fixed-scope rule. See
[bounded review and evidence matrix](m09_review.md), [validation](m09_validation.json),
[prepared patch](reference/m09-header-proposal.patch.txt) and CR005/R013.

Full gate: **1,180 tests, 96.40% coverage**, all standards/types/architecture and
both builds pass. Independent extracted-wheel focused suite: 113 tests plus
60 subtests. Final native suite passes 12 source/display cases and 34 inspected
EN/ES captures. Valid M01–M08 evidence reused. All 500 reference manifest files
and approved dependency lock remain unchanged. Linux XCB only; other platforms
remain M12. No extra milestone or speculative infrastructure added.


---

## Historical M07/M08 control state

# Current control state — M07 and M08 complete; M09 next

**92.75/100 overall; 8/12 complete; 18.75/26 earned, 7.25 points left.**
The owner explicitly authorized both fixed milestones together. M07 earns 1.50
and M08 2.25 points; scope, criteria and weights are unchanged. M09 not started.

JROT now has application-owned Undo/Redo for partial cell edits, Delete batches,
applied/cleared scope and optimized Apply. Exact profile/assignment links and
optimization provenance are restored; Save is explicit and atomic, and failed
writes retain intent. Native text typing keeps its own Undo, including editable
scheme-name combos. New/load/Cancel/deletion reset scheme-local history. R006
scope counts fit at the original 1480x740 minimum in English and Spanish.

Actual original-source/migrated matched-input comparisons agree on objectives
and constraints for all three CBC single-tool runs and HiGHS all-tool optimization.
Both native comprehensive-copy EN/ES flows pass preview/comparison/Apply/Undo/Redo/
Save/reopen, with archive/assessments/jobs unchanged. Ten new focused history
regressions complement existing solver timeout/incumbent/infeasible/cancel tests.

Final gate: **1,178 tests, 96.40% coverage**, lint/format/strict types,
architecture and wheel/sdist pass. Independent extracted-wheel focused JROT and
native EN/ES comprehensive-copy acceptance pass. **22 captures inspected**;
unchanged original layout/busy/comparison evidence reused. All 500 reference
hashes and approved lock remain unchanged. Native XCB is the validated gate;
the failed offscreen VTK attempt is retained, not presented as a pass.

[Schedule acceptance](m07_acceptance.md), [optimization acceptance](m08_acceptance.md),
[history contracts](jrot_history.md), [bounded review](m07_m08_review.md), and
[fixed ledger](finish_progress.json). R012 records compact-count wording and modal
history boundaries for later review; no critical unanswered question. Next is
M09 shared UI/localization/units/avatar, followed by M10 final comprehensive
cross-feature acceptance, M11 inventory/docs and M12 Linux delivery/platform notes.
Stop at this authorized batch; no M09 work has been started.

---

## Historical M06 control state

# M06 completed checkpoint

**89.00/100 overall; 6/12 complete; 15/26 earned, 11 points left.**
M06 earns its existing 2.5 points after PLOT history acceptance. M07 not started;
continue one fixed milestone per batch. No scope, criterion or weight expansion.

PLOT now provides application-owned Undo/Redo for marker drag/scale, settings,
accepted coordinates/batches and Cancel restoration. Styled English/Spanish Edit
menus and standard shortcuts respect native typing undo and unfinished input.
Save remains explicit and is not a source edit. Failed writes retain intent;
Undo after Save changes only the draft. Exact geometry and station order are
preserved. CR004 removal was rejected and withdrawn; its original requirement
was retained and is now implemented. Extensible localization and app-wide
undo/redo remain approved modernization targets.

Final approved gate: **1,168 tests, 96.37% coverage**, lint/format/strict types,
architecture and both builds pass. Final wheel: **83 focused PLOT tests** pass.
Native comprehensive-copy EN/ES gesture/menu/Save/failure/close/reopen scenarios
pass; **12 final captures inspected** at normal, enlarged and minimum sizes.
Existing original chart/export and 370 CSV row comparisons remain valid evidence.
All 500 reference hashes and the approved lock remain unchanged; originals were
never written. Two concrete history integration failures were corrected: rounded
Save projections and station ordering. Native focus/hit-target harness fixes
required no further product change. See the review for retained audit logs.

[Acceptance](m06_acceptance.md), [validation](m06_validation.json),
[history contracts](plot_history.md), [bounded review](m06_review.md), and
[fixed progress ledger](finish_progress.json). Next fixed milestone is M07 — JROT
schedule/scope, preserving CBC single-tool and HiGHS multi-tool routing; no GLPK.

---

# Resumption checkpoint — 2026-10-10

**Current state: substantial implemented and tested LiFFT/DUET/ST/PLOT/JROT
functionality; final replacement acceptance remains incomplete.** The owner's
2026-10-10 scope review now establishes a fixed 100-point completion baseline:
**74 earned / 26 remaining, reported as approximately 74% / 26%.** This is
scope-weighted acceptance progress, not hours elapsed or a finish-date forecast.
See [the completion plan and remaining-work ledger](completion_plan.md) and
[its machine-readable baseline](progress_baseline.json). The former 67% figure
is superseded; historical checkpoint estimates remain historical only.

F numbers are sequential work/check/audit checkpoints, not a fixed original
milestone list or a percentage denominator. The accepted plan has stages 0–6.
The owner resumed implementation after the planning review; checkpoints must
close the listed deliverable criteria. All 500 reference hashes and the dependency
lock were rechecked unchanged. Latest full gate is F155: 1,148 passing tests and 96.48% coverage;
F153–F155 closes the latest three-checkpoint batch. See the current remaining
criteria and next bounded batch in completion_plan.md.

## Latest checkpoint: F155

Restored the original integrated ST inline totals using the same documented presentation component as LiFFT/DUET. Fixed an observed unit-label defect: switching display units projected ST inputs but also relabeled unchanged source-unit moments. The moment header now follows source/result units, matching the established LiFFT policy. The reference direction selectors and their calculator mapping remain unchanged. Current fixed-scope progress remains 74/100; full original-window and cross-feature final acceptance is still open.

1148 tests pass; 96.48% coverage. Required gates, wheel and reference/lock integrity pass. See [F155 evidence](f155_compatibility.md).

## F154 historical checkpoint

Restored the original integrated inline totals for DUET and the original 13px/15px labels, risk backgrounds, rounded corners and luminance-based foreground for LiFFT and DUET. The original constructors hide totals, but refreshAssessmentSummary/styleToolResultSummary/alignToolSummary show them on the live result path. The previous empty-space interpretation was incomplete. A small typed, documented presentation component now owns those repeated controls; panels still own evaluation and exact-source historical selection. Progress remains 74/100; this bounded comparison does not claim complete-window G4 acceptance.

1144 tests pass; 96.48% coverage. Required gates, wheel and reference/lock integrity pass. See [F154 evidence](f154_compatibility.md).

## F153 historical checkpoint

Save during document/context/project transitions now uses the same atomic source/result persistence as explicit Save. An injected owner-thread result provider supplies only the active exact-source calculation after the target has been validated. No new background processing or modal ownership changes. All three tools pass switch Save, unchanged ownership/reopen, Save As success and retained-session failure acceptance. Current fixed-scope progress stays 74/100 while final lifecycle and original-window acceptance remains.

1134 tests pass; 96.45% coverage. Required gates, wheel and reference/lock integrity pass. See [F153 evidence](f153_compatibility.md).

## F152 historical checkpoint

ST's Calculate icon now matches the original 28-pixel asset treatment. Original ST headers, column control types and direction selector labels are compared directly under the approved Qt baseline. The expanded Open assessment picker now uses the existing management/JROT styled delegate, fixing selected white text painted on a white background. EN/ES native selected/expanded states, all 194 captions, exact selection identity, modal behavior and cancellation pass. Overall scope remains 74/100; C3/C4 final workflow and full original-window acceptance are not claimed complete.

1124 tests pass; 96.42% coverage. Required gates, wheel and reference/lock integrity pass. See [F152 evidence](f152_compatibility.md).

## F151 historical checkpoint

LiFFT and DUET controls were compared by executing the original form-building methods in an isolated harness under the approved Qt baseline, without importing the original application's startup or touching its database. Headers, column/control types, DUET rating labels, button icons and matched parent-container captures now have direct source-based evidence. The measured DUET Calculate icon mismatch was corrected from 26 to the original 28 pixels. Overall scope progress remains 74/100; this checkpoint closes comparison subcriteria, not complete C1/C2 final acceptance.

1123 tests pass; 96.43% coverage. Required gates, wheel and reference/lock integrity pass. See [F151 evidence](f151_compatibility.md).

## F150 historical checkpoint

Explicit Save now commits the current successful LiFFT/DUET/ST calculation with its unchanged or edited source in one SQLite transaction. Reopen/export prefer that exact-source saved result while the original archive remains separately readable and unchanged. Save As writes current results into the copy before adoption. Focused native pending-input and storage-failure regressions pass. Overall fixed-scope progress remains 74/100; final B1/C4 acceptance still needs its remaining lifecycle/navigation comparisons.

1123 tests pass; 96.43% coverage. Required gates, wheel and reference/lock integrity pass. See [F150 evidence](f150_compatibility.md).

## F149 historical checkpoint

F149 verifies the reported main-window clipping without changing the application's
layout or behavior. Full-resolution F148 PNGs contain the labels and regions that
appeared absent in combined previews; R007 was not an established application
layout defect. The record is corrected rather than adding repaint callbacks.
The application wheel remains byte-for-byte identical to F148. Overall scope
progress remains 74/100 complete and 26/100 remaining; no final gate is awarded.

1108 tests pass; 96.45% coverage. Required gates, wheel and reference/lock integrity pass. See [F149 evidence](f149_compatibility.md).

## F148 historical checkpoint

The copied comprehensive project now completes fresh Calculate, edit, undo/redo,
Save, CSV export and reopen across LiFFT, DUET and ST. All 194 sources evaluate
without mutation: 103 complete and 91 partial grids. The native integrated
scenario also saves/cancels/reopens a worker edit, opens PLOT, runs actual CBC and
HiGHS optimization, applies/saves a multi-tool rotation, and verifies backup,
archive retention and unchanged original inputs. G3 gains its usable-integration
gate: fixed-scope progress is 74/100 complete and 26/100 remaining.

1104 tests pass; 96.45% coverage. Required gates, wheel and reference/lock integrity pass. See [F148 evidence](f148_compatibility.md).

## F147 historical checkpoint

Saved summary exports now preserve exact-source archived results with explicit
recorded status. The read-only application contract checks source equality before
using evidence; edited sources take the characterized fresh calculator path.
No calculation is run for an unchanged archived source. Per-assessment recorded
units are retained, including DUET's labels independent of project defaults.
This closes CSV compatibility within B1's existing G3 credit; no extra scope
points are claimed simply for completing another checkpoint.

1102 tests pass; 96.45% coverage. Required gates, wheel and reference/lock integrity pass. See [F147 evidence](f147_compatibility.md).

## F146 historical checkpoint

ST Calculate now runs the existing characterized calculator through the typed
application service, honoring each document's recorded direction convention.
The task grid, result cards, gauge and replaceable body renderer consume typed
results; calculation and unit policy stay outside Qt. C3 gains G3 usable-workflow
credit: overall fixed-scope progress is 73.25/100 (approximately 73%).

1098 tests pass; 96.43% coverage. Required gates, wheel and reference/lock integrity pass. See [F146 evidence](f146_compatibility.md).

## F145 historical checkpoint

Fresh metric LiFFT now uses the characterized domain calculator through the
application service and reusable result presenter. Original normalization,
rounding and legacy moment-display arithmetic remain unchanged; this is behavioral
compatibility, not scientific certification. Missing/invalid inputs, source-unit
provenance, history and failure handling remain explicit. C1 gains usable-workflow
credit after frozen references, Calculate/Save/reopen and native checks pass.

1096 tests pass; 96.45% coverage. Required gates, wheel and reference/lock integrity pass. See [F145 evidence](f145_compatibility.md).

## F144 historical checkpoint

The F141–F144 batch completes historical result display, active-original PLOT
loader characterization, readable assessment selection and precise numeric
input display. Recorded outputs now use original tool palettes for task cells,
result cards and the avatar. Pending text immediately hides the previous recorded
outputs; repeated refreshes preserve the gauge animation target. Comprehensive
EN/ES workflows are validated on separate converted copies. Overall percentage
and finish date remain unvalidated; this is four milestones, not final acceptance.

1095 tests pass, 96.45% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F144 compatibility evidence](f144_legacy_compatibility.md). Recorded-result display refinements visually inspected; see listed manual/final acceptance limits.

## F143 historical checkpoint

Integrated Open now offers tool, worker/name, complete workplace/shift and exact
version/assignment labels while keeping the stored document identity unchanged.
Narrow LiFFT/DUET/ST numeric inputs start at their leading digits, retaining full
precision and exact no-edit round trips. Existing recent-project Open, cancellation
and conversion behavior remain tested. Next: integrated comparison/visual checks
of this batch. Overall percentage and finish date remain unvalidated.

1093 tests pass, 96.47% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F143 compatibility evidence](f143_legacy_compatibility.md). Assessment-selection and numeric-display changes inspected; expanded popup remains a manual visual check.

## F142 historical checkpoint

The original PLOT call path and active loadImageNew implementation were audited.
Stored Plant rotation/crop/mirror/other transform fields are not applied by that
loader. The migrated canvas matches its original pixel coordinates, scene bounds,
aspect-preserving fit, Top/Left alignment and hidden scrollbars, including resize.
Introducing dormant transforms would change the original behavior. They remain
archived for review rather than being activated. Next: readable assessment choices
and numeric inputs. Overall percentage/finish date remain unvalidated.

1091 tests pass, 96.48% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F142 compatibility evidence](f142_legacy_compatibility.md). No UI changes.

## F141 historical checkpoint

Converted projects now show original cached task outputs and totals in the
existing LiFFT/DUET/ST grids and result cards, explicitly marked Recorded /
Registrado. All 194 original/recovered sources are bound to their exact original
inputs. Editing hides historical evidence; undo can restore it, and saving an
edited source never makes the old result current. Fresh calculation gates remain.
Overall completion percentage and finish date remain unvalidated.

1088 tests pass, 96.48% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F141 compatibility evidence](f141_legacy_compatibility.md). Historical result display added; see native evidence.

## F140 historical checkpoint

The comprehensive project now opens through the integrated desktop as a separate
converted copy, with all 194 assessments/3,577 task rows and seven JROT schemes.
EN/ES native validation passes across LiFFT/DUET/ST, metric/imperial projection,
ST edit/undo/redo/save/reopen, Worker/Job/Organization Management, PLOT and real
CBC/HiGHS optimization followed by Apply/Save/backup. This completes the requested
F137–F140 four-milestone batch. Full-parity percentage/finish date remain unvalidated.

1087 tests pass, 96.55% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F140 compatibility evidence](f140_legacy_compatibility.md). No UI changes.

## Planned next batch (F145–F148), revised after scope review

The owner requested a bounded remaining-work summary before implementation
continues. The [completion plan](completion_plan.md#priority-and-finish-sequence)
now maps the next checkpoints to fixed deliverables and exit criteria:

1. F145 / C1: close reference-compatible fresh metric LiFFT calculation and its
   save/reopen workflow; do not change scientific formulas without approval.
2. F146 / C3: close fresh ST calculation using established reference direction
   convention and the explicit metric policy, with save/reopen evidence.
3. F147 / B1: resolve and test supported CSV compatibility, recorded evidence and
   precision/status differences.
4. F148 / G3: run the complete copied-project fresh-calculation/save/export/reopen
   scenario; score only acceptance gates actually closed.

Then close original-window parity on existing assessment/management/PLOT/JROT
forms, remaining localization/resize states, current documentation and native
release/platform acceptance, as assigned to the fixed ledger. R004 popup review
and R006 Spanish scope-summary clipping remain. Do not create extra infrastructure
or silently add scope. New findings go into an existing deliverable or an explicit
scope-change record. Four checkpoints do not automatically mean four gates closed.

F141–F144 remains complete as a four-checkpoint batch. This planning review is not
another implementation milestone. Historical remaining lists below are superseded
by the current completion ledger; they must not be treated as current missing work.

## F139 historical checkpoint

The integrated main Open/recent workflow recognizes an original XML project,
asks for a separate converted-copy destination and then selects an assessment.
The destination alone enters recent history. Cancellation, existing-file and
missing-image failures retain the current workspace and unsaved source edits.
Next: comprehensive integrated copy validation. Full parity percentage and finish
date remain unvalidated.

1086 tests pass, 96.55% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F139 compatibility evidence](f139_legacy_compatibility.md). Open integration changes; see visual evidence and capture limitation.

## F138 historical checkpoint

The entire comprehensive project copy now converts into one new-format-twelve
file: 194 assessments/3,577 task rows, including all 56 ST sources, 28 workers,
12 jobs, 104 assignments, all 19 risk-profile versions, four maps/geometry and
seven saved JROT schemes. Reopen and backup retain exact typed records and the
complete source archive. Next: connect explicit conversion to desktop Open,
then exercise the converted copy through the integrated EN/ES workflows.
Overall full-parity percentage and finish date remain unvalidated.

1078 tests pass, 96.54% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F138 compatibility evidence](f138_legacy_compatibility.md). No UI changes.

## F137 historical checkpoint

ST sources now record an explicit direction convention: existing version-one
new-format documents retain their model-code interpretation; imported original
UI sources retain their visible choices and the original 1/2 calculator swap.
All 1,650 frozen reference numerical vectors match through this mapping. No
scientific correction or owner direction answer is required for compatibility.
Next: convert all original assessments together, with source evidence intact.
Overall functional-parity percentage and finish date remain unvalidated.

1078 tests pass, 96.54% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F137 compatibility evidence](f137_legacy_compatibility.md). No UI changes.

## F136 historical checkpoint

An explicit converter now takes an original XML project and publishes a separate
new-format-twelve repository with exact typed records and a complete source
archive. A small original-shaped project opens in the integrated application,
including recovered LiFFT, historical DUET, Worker Management, PLOT and saved
JROT. The comprehensive project currently blocks its 56 unresolved ST sources
before creating any destination. Next: review the original ST selector-to-model compatibility mapping,
then finish complete conversion and desktop Open integration. Overall percentage
and finish date remain unvalidated.

1072 tests pass, 96.54% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F136 compatibility evidence](f136_legacy_compatibility.md). No UI changes.

## F135 historical checkpoint

New-format twelve stores the exact original XML, a consistent read-only SQLite
snapshot and all referenced image bytes/names alongside the editable typed data.
Original cached results, task moments, raw selectors, timestamps, plant display
fields and schema objects remain recoverable after edits, backup and removal of
the copied source files. Next: connect an explicit converter, blocking source
conflicts and unresolved ST directions before destination creation. No reliable
overall completion percentage or finish date yet.

1068 tests pass, 96.55% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F135 compatibility evidence](f135_legacy_compatibility.md). No UI changes.

## F134 historical checkpoint

Complete typed snapshots now create a validated new-format project through a
hidden same-directory file and exclusive publication. Original approved/retired
profiles, historical ownership, PLOT images/positions and saved rotation links
survive exact read-back and reopen. Next: retain complete original XML/database
and image-name evidence; ST direction choice remains required before full source
conversion. Overall completion percentage and finish date remain unvalidated.

1059 tests pass, 96.62% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F134 compatibility evidence](f134_legacy_compatibility.md). No UI changes.

## F133 historical checkpoint

All seven original saved schemes now map to the established typed JROT models,
including 45 frozen target records, 179 assignment cells, exact scopes and original
manual/single-tool/all-tool provenance. Existing forms load every copied scheme in
EN/ES; actual CBC and HiGHS/Apply pass on the small saved source scheme. Next:
explicit atomic destination conversion with complete source evidence preservation,
then integrated copied-project validation. ST direction choice is still pending.

1046 tests pass, 96.69% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F133 compatibility evidence](f133_legacy_compatibility.md). No UI changes.

## F132 historical checkpoint

The comprehensive copied project now maps all four exact plant images, 16 station
anchors and 100 assignment markers, with 191 raw assessment markers and original
plant display metadata retained. Next: saved JROT schemes/provenance, followed by
explicit destination conversion and integrated copied-project validation.

1039 tests pass, 96.70% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F132 compatibility evidence](f132_legacy_compatibility.md). No UI changes.

## F131 historical checkpoint

The comprehensive copy now has a conflict-free recovery plan for all 194 original
assessment summaries and 3,577 task rows: 191 exact old/current matches plus three
recovered records/45 rows on their existing assignments 101, 102 and 104. Next:
PLOT companion images/geometry and saved JROT provenance, then explicit conversion.
No source or destination records are written by this read-only recovery plan.

1034 tests pass, 96.71% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F131 compatibility evidence](f131_legacy_compatibility.md). No UI changes.

## F130 historical checkpoint

All 191 normalized historical assessments and 3,532 task rows in the comprehensive
copy now have a tested read-only compatibility mapping, with exact assignment/
version/current/status identity, units, source inputs, notes and cached evidence.
Next: reconcile three older records absent from normalized history, map PLOT/JROT
assets/provenance, and implement explicit atomic destination conversion before
integrated copied-project UI validation. Raw ST selector interpretation still
requires the documented scientific/UI decision; no implicit conversion is made.

1030 tests pass, 96.71% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F130 compatibility evidence](f130_legacy_compatibility.md). No UI changes.

## F129 historical checkpoint

Original workers, organization, jobs, placements, assignments and every job-risk
profile version now map to existing immutable domain models. The comprehensive
copy validates all 28 workers, 12 jobs, 38 placements, 104 assignments, 19 profiles
and 56 measurements without source writes. Next: historical assessments/tasks and
cached evidence. Destination conversion and integrated legacy UI acceptance remain.

1024 tests pass, 96.71% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F129 compatibility evidence](f129_legacy_compatibility.md). No UI changes.

## F128 historical checkpoint

Original XML/SQLite version-eight projects now have a tested read-only adapter.
The comprehensive copied fixture passes integrity and reference checks: 30 tables,
28 workers, 191 historical assessments, 19 risk profiles and seven JROT schemes.
Next: typed organization/worker/job/risk catalogs, then historical task sources.
No destination conversion or integrated legacy-project UI acceptance is claimed.

1013 tests pass, 96.70% coverage; required gates, extracted wheel and reference/lock integrity pass. See [F128 compatibility evidence](f128_legacy_compatibility.md). No UI changes.

## F127 historical checkpoint

Main JROT toolbar navigation now opens the original modal form over the
workspace-owned project connection, with bootstrap-composed approved CBC/HiGHS.
Actual EN/ES solve -> comparison/Apply -> explicit Save -> reopen works. Opening
JROT preserves unfinished LiFFT/DUET/ST input; its worker finishes safely before
modal disposal. Full-project capability controls availability. No UI redesign.
[Source mapping and limits](jrot_main_integration.md).

1003 native tests pass (eleven new focused cases), 96.70% coverage;
Ruff/format (471 files), strict mypy (215 source files), architecture,
builds and independent extracted-wheel actual main/modal/solver/Save/reopen pass.
28 native images inspected, including main VTK buffers, minimum/enlarged main,
empty/populated/selected JROT and actual solver results in EN/ES. All 500 reference
hashes and the approved dependency lock are unchanged. Evidence:
f127_validation.json, artifacts/f127-check.log, artifacts/f127-wheel.log and
artifacts/jrot-main.

Next: legacy-project compatibility/import audit, comprehensive copied-project
cross-feature validation, then final UI/menu/workflow/platform acceptance. Main
JROT is now enabled for supported full projects. Overall completion percentage
and finish date remain unvalidated; the earlier 67% remains withdrawn.

## F126 historical checkpoint

JROT now supports the original single-tool comparison and tabbed all-tool
comparison, actual two-stage HiGHS, and explicit Apply -> Save with ALL_TOOLS
provenance. CBC stays selected-tool only; no GLPK/fallback. Source layouts and
modeless comparison behavior are retained; owned children close when their real
inputs change. [Source mapping and limits](jrot_comparison.md).

992 native tests pass (ten new focused cases), 96.71% coverage;
Ruff/format (469 files), strict mypy (215 source files), architecture/builds
and independent wheel EN/ES actual CBC/comparison and HiGHS/tabs/Apply/Save/reopen
pass. 32 final captures inspected. English table/tab/Apply dimensions and text
match source at both sizes; both panels and bottom controls remain visible.
All 500 reference hashes and approved dependency lock are unchanged. Evidence:
f126_validation.json, artifacts/f126-check.log, artifacts/f126-wheel.log and
artifacts/jrot-comparison.

Next: workspace-owned repository/bootstrap solver wiring, then enable/test actual
main JROT navigation. Main JROT remains disabled. Legacy compatibility,
comprehensive copied-project integration and final UI/workflow/platform acceptance
remain. Overall completion percentage and finish date remain unvalidated.

## F125 historical checkpoint

The original JROT form now runs selected-tool CBC optimization, displays its
read-only original result table and applies exact assignments through Use as
Current without saving. Explicit Save retains optimization provenance. One owned
worker keeps the GUI responsive; Cancel discards its result and Escape/window
close waits for bounded solver completion. [Source mapping and limits](jrot_selected_optimization.md).

982 native tests pass (ten new focused cases), 96.71% coverage;
Ruff/format (466 files), strict mypy (214 source files), architecture/builds
and independent wheel actual EN/ES CBC/transfer/Save/reopen pass. Twenty-two
native captures inspected. English result dimensions/text match source at both
sizes; both panels and bottom controls remain visible. All 500 reference hashes
and approved dependency lock are unchanged. Evidence: f125_validation.json,
artifacts/f125-check.log, artifacts/f125-wheel.log and artifacts/jrot-single-solve.

Next: original HiGHS multi-tool and single-tool comparison windows/transfer,
then main JROT integration. Compare/Optimize All Tools and main JROT remain
disabled. Legacy compatibility, comprehensive copied-project integration and
final UI/workflow/platform acceptance remain. Overall completion percentage
and finish date remain unvalidated.

## F124 historical checkpoint

The original responsive JROT form now connects its worker/time-block grid, exact
scope chooser and usable Save/New/Cancel/navigation/Search/confirmed Delete.
Source setup, both panels, splitter, rail and dimensions are preserved. Failed
reads/writes retain edits. EN/ES messages/buttons reuse packaged icons; localized
captions fit the narrow path and fixed buttons. [Source mapping and limits](jrot_form.md).

972 native tests pass (seven focused cases), 96.75% coverage; Ruff/format
(461 files), strict mypy (211 source files), architecture/builds and independent
wheel native Save/New/Cancel/reopen/confirmed Delete pass. Twenty-four final
captures inspected. English major rectangles match source at minimum/enlarged
sizes; both panels and bottom controls remain visible. Original wide-grid
scrolling remains. All 500 reference hashes and approved lock are unchanged.
Evidence: f124_validation.json, artifacts/f124-check.log, artifacts/f124-wheel.log
and artifacts/jrot-form.

Next: actual CBC single-tool/HiGHS multi-tool optimization, results/comparison
transfer and owned cancellation/closure, then main action integration. Those
buttons and main JROT remain disabled. Legacy compatibility, comprehensive
copied-project integration and final UI/workflow/platform acceptance remain.
Overall completion percentage and finish date remain unvalidated.

## F123 historical checkpoint

Original JROT worker/time-block editing is migrated with exact worker/placement/
profile identities, original grid dimensions, damage colors, recommendations and
per-column dropdown exclusions. Tool changes retain frozen links; missing evidence
clears derived results. One blocked row update replaces reconnect loops and cell
queries. Native selected dropdown visibility is corrected using the existing styled
delegate. [Source mapping and limits](jrot_grid.md).

965 native tests pass (12 focused cases), 96.79% coverage; Ruff/format
(456 files), strict mypy (208 source files), architecture/builds and extracted-wheel
native edits pass. Sixteen captures inspected; English component geometry matches
source at both sizes. Original wide-grid horizontal scrolling remains. All 500
reference hashes and approved lock unchanged. Evidence: f123_validation.json,
artifacts/f123-check.log, artifacts/f123-wheel.log and artifacts/jrot-grid.

Grid→project save→reopen→edit→save→delete is tested. The containing form's actual
buttons are still pending: next connect original setup/scope/scheme controls and
save/load/delete/cancel/navigation, then optimization/comparison and owned worker
lifecycle/main integration. Main JROT is disabled. Legacy compatibility,
comprehensive copied-project integration and final visual/workflow/platform
acceptance remain. Overall percentage and finish date remain unvalidated.

## F122 historical checkpoint

The original JROT scope chooser is migrated: one shift, checkable workplace tree,
source-sized layout and empty-selection prompt. It returns exact workplace
identities without writes/upgrades. Checkbox changes are batched and initial mixed
parent states are corrected. EN/ES text and packaged action icons follow the UI
rules. [Source mapping, visual checks and limits](jrot_scope.md).

953 native tests pass (five focused cases), 96.84% coverage; Ruff/format
(451 files), strict mypy (205 source files), architecture/builds and extracted-wheel
native scope actions pass. Eighteen captures inspected; English major control
rectangles match the source at minimum/enlarged sizes. No clipping. Full pixel
parity is not claimed. All 500 reference hashes and approved lock are unchanged.
Evidence: f122_validation.json, artifacts/f122-check.log, artifacts/f122-wheel.log
and artifacts/jrot-scope.

Next: containing original JROT scheme form, worker/target editing and usable
save/load/delete with this scope chooser; then optimization/comparison transfer,
owned cancellation/closure and main integration. JROT main action is disabled.
Remaining legacy compatibility, comprehensive copied-project integration and
final visual/workflow/platform acceptance are unchanged. Overall completion
percentage and finish date remain unvalidated.

## F121 historical checkpoint

JROT schemes now save/load/delete through the project-owned repository, retaining
original worker assignments and exact risk-profile/job-placement links. Explicit
Save atomically upgrades full projects to format eleven; reads never migrate.
Rollback, copy/reopen, retired evidence and closed assignments are covered.
Referenced records are protected, including the actual Job Management delete
path. Existing maps, geometry and assessment units survive; PLOT position saves
preserve the higher format. [Source mapping and limits](jrot_persistence.md).

948 native tests pass (24 new cases), 96.81% coverage; Ruff/format (446
files), strict mypy (202 source files), architecture/builds and independent
extracted-wheel persistence checks pass. All 500 reference hashes and the approved
lock are unchanged. No UI changed or new visual capture. Evidence:
f121_validation.json, artifacts/f121-check.log and artifacts/f121-wheel.log.

Next: original JROT scheme form and scope selector with usable edit/save/load/delete,
then optimizer/comparison transfer, owned worker cancellation/closure and main
integration. JROT remains disabled. Legacy compatibility, comprehensive copied
project validation and final integrated UI/workflow/platform acceptance remain.
Overall completion percentage and finish date remain unvalidated.

## F120 historical checkpoint

The active JROT optimizer is migrated behind an injected application port.
CBC handles single-tool minimax; HiGHS handles both multi-tool stages. Original
assignment constraints, 1% gap, per-stage time limit and ceiling tolerance are
retained. Immutable inputs reject invalid/missing risk data; independent schedule
checks reject infeasible/fractional results and stale no-incumbent outputs.
Stopped feasible runs retain that status rather than claiming exact optimality.
[Implementation, source mapping and limits](jrot_optimization.md).

The owner approved the proposed exact solver additions with "ok keep going".
Only PuLP 3.2.2 and highspy 1.11.0 were installed; all 33 prior lock entries retain
versions. Bundled CBC hash/version and HiGHS version match the approved proposal.
All 500 reference hashes are unchanged. 924 native tests pass (26 focused new
cases), 96.92% coverage; Ruff/format (441 files), strict mypy (199 source files),
architecture, builds and independent extracted-wheel actual solver checks pass.
No UI change or new visual capture. Evidence: f120_validation.json,
artifacts/f120-check.log and artifacts/f120-wheel.log.

Next: scoped scheme persistence and original-layout JROT edit/save/load/delete,
then optimization/comparison, safe worker cancellation/closure and actual main
integration. JROT remains disabled until the usable workflow is validated.
Remaining original-format compatibility, comprehensive copied-project validation
and final integrated UI/workflow/platform acceptance are unchanged. Overall
completion percentage and finish date remain unvalidated.

## F119 historical checkpoint

Original JROT active workflows, source layout, frozen profile/assignment links,
constraints, two-stage objective and cancellation behavior have been reviewed.
[Source mapping and next executable slices](jrot_migration.md). Exact proposal:
PuLP 3.2.2 with bundled CBC 2.10.3 for single-tool, highspy/HiGHS 1.11.0 for
multi-tool, no GLPK. These match the reference package pins. Official wheel
metadata and bundled CBC identity were inspected without installation/execution;
[approval proposal](jrot_dependency_proposal.md).

Awaiting explicit exact-version approval before modifying package pins, lock or
installed packages. No production/UI changes; JROT remains disabled. F118's
898-test code gate remains the latest code validation; it was not repeated for
this documentation-only slice. All 500 reference hashes and the approved lock
were verified unchanged. Evidence: f119_validation.json and
reference/f119-jrot-package-review.json. Overall completion percentage and finish
date remain unvalidated.

Next: approved solver installation and the active optimizer migration, then
source-layout scheme workflows, optimization/comparison and main integration.

## F118 historical checkpoint

**PLOT is now enabled in main navigation for open full projects.** The original
modal host, map controls, worker/job/graph/outcome panels and saved CSV export are
connected. The real Load into Tool context action selects the exact saved worker
and assessment model in the integrated UI. PLOT borrows the workspace-owned
connection, so explicit map saves and format upgrades update the same handle.
Opening/exporting/closing does not implicitly save assessment or marker edits.
Escape now uses the same unsaved edit consent as the window close button.
[CSV/source mapping, integration and remaining limits](plot_integration.md).

Validation: 898 native tests pass (six focused new cases), 96.88% coverage;
Ruff/format (433 files), strict mypy (196 source files), architecture and both
builds pass. Twenty window/modal/menu captures plus four actual VTK framebuffers
were inspected in EN/ES, including minimum/enlarged, populated/empty, CSV
success/error/no-data, context menu and main UI before/after handoff. Main images
compose the actual VTK back buffer at widget coordinates, following F78's
compositor limitation; they are not direct system screenshots. Extracted-wheel
actual main action, borrowed connection, CSV publication and DUET context-action
handoff pass without implicit project writes. All 500 reference hashes and the
approved lock remain unchanged. Evidence: f118_validation.json,
artifacts/f118-check.log, artifacts/f118-wheel.log and artifacts/plot-integration.

Next: characterize original JROT workflows/solver boundary and prepare its exact
dependency proposal before any installation. Owner routing remains CBC for
single-tool and HiGHS for multi-tool; no GLPK. Preserve original JROT source
layouts and behavior, then integrate it. Original-format project compatibility,
comprehensive copied-project integration validation and final application-level
visual/workflow acceptance remain outstanding; enabling PLOT does not establish
full application parity. Overall completion percentage and finish date remain
unvalidated.

## F117 historical checkpoint

Original PLOT map controls now work in the composed host: one-click zoom-in,
source zoom-out/1:1 floor, fitted reset, marker opacity and current-view PNG capture.
Reset preserves pending marker edits and saved results instead of reapplying
filters. PNG cancellation is silent; Qt encoder failures are reported. Controls
are disabled without actual map pixels. [Source mapping and limits](plot_map_actions.md).

Validation: 892 native tests pass (four focused cases), 96.88% coverage;
Ruff/format (428 files), strict mypy (193 source files), architecture and both
builds pass. Eighteen native map/modal/export captures inspected in EN/ES at
minimum/enlarged sizes. Reviewed source opacity and six zoom-out cases agree
exactly. Extracted-wheel actual clicks, pending-edit reset, exact PNG pixels,
resize and no-write lifecycle pass. All 500 reference hashes and approved lock
remain unchanged. Evidence: f117_validation.json, artifacts/f117-check.log,
artifacts/f117-wheel.log and artifacts/plot-map-actions.

Next: original saved PLOT worker CSV export, then main-navigation composition and
actual integrated assessment handoff testing. The deletion audit found no
separate PLOT deletion control/handler in the original source; the existing
assessment deletion workflow remains in the integrated assessment UI. This
resolves the earlier speculative PLOT deletion item rather than adding a new UI.
Production PLOT remains disabled until CSV/navigation integration is tested.
Then JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion
percentage and finish date remain unvalidated.

## F116 historical checkpoint

The original PLOT host now composes the migrated map/rail, filters, Tools Overview,
Worker Overview/Job Placement tabs and outcome strip. Actual Apply, immediate
risk-mode Apply, map selection/detail navigation, close cancellation and accepted
saved assessment handoff are connected. Opening/applying/closing never implicitly
saves a map or marker. Read failures retain the applied dataset; editor rejection
retains the window and image preview. [Source mapping and limits](plot_host.md).

Validation: 888 native tests pass (five focused host cases), 96.87% coverage;
Ruff/format (426 files), strict mypy (193 source files), architecture and both
builds pass. Twenty-two native host/modal captures were inspected, including
EN/ES, empty/populated, expanded, selected, minimum/enlarged, bottom worker
controls, close Cancel and read error. Extracted-wheel real host/mode/resize,
close Cancel, exact saved handoff and no-write lifecycle checks pass.
All 500 reference hashes and approved lock are unchanged. Evidence:
f116_validation.json, artifacts/f116-check.log, artifacts/f116-wheel.log and
artifacts/plot-host. Full source-host pixel equality is not claimed; composition
revealed and corrected minimum-size/worker-control clipping and the missing
source white rail-title style.

Next: complete the original map zoom/actual-size/opacity/capture/export actions,
audit/connect the original saved-data deletion workflow, then wire PLOT into
production navigation and verify the actual integrated editor handoff. The host
is composed and tested; production PLOT is still disabled while those actions
remain incomplete. Then JROT: CBC single-tool, HiGHS multi-tool, no GLPK.
Overall completion percentage and finish date remain unvalidated.

## F115 historical checkpoint

Original PLOT outcome metrics, single/comparison gauges and View details warning
workflow are composed. Saved membership drives the existing summaries; missing
risk stays unavailable and observed zero remains valid. Full station identity
prevents merging equally named stations. Original source controls and gauge
painting are retained, with documented minimum-size/heading/message clipping
corrections. [Source mapping, corrections and limits](plot_outcome_summary.md).

Validation: 883 native tests pass (six focused new cases), 96.70% coverage;
standards, strict mypy (192 source files), architecture and both builds pass.
Extracted-wheel actual localized warning dialog, outcome modes, minimum bounds,
wrapped messages, zero/absence, animation closure and no-write reopen pass.
All 21 source gauge fixtures and the focus-normalized warning dialog match pixels
exactly. Seventy-six native captures were inspected, including adjacent map/chart
resizing. Outcome-strip geometry corrections are recorded rather than claimed as
full-strip equality. All 500 reference hashes and approved lock are unchanged.
Evidence: f115_validation.json, artifacts/f115-check.log, artifacts/f115-wheel.log
and artifacts/plot-outcome.

Next: compose the complete original PLOT host, connect parent close/load consent
and remaining map/deletion actions into complete usable workflows. Production
PLOT remains disabled until that integration passes. Then JROT: CBC single-tool,
HiGHS multi-tool, no GLPK. Overall completion percentage and finish date remain
unvalidated.

## F114 historical checkpoint

Original PLOT Tools Overview now composes saved-data charts, the three-chart
selector, descriptions, symbol legend, Graph Settings and expanded viewer.
Apply/Close/Reset and real exports are connected; chart browsing does not save
project data. The viewer owns its own figure. Native checks caught and corrected
replacement-figure click binding, narrow-axis clipping and 140% title clipping.
[Source mapping, corrections and limits](plot_graph_workflows.md).

Validation: 877 native tests pass (seven focused new cases), 96.57% coverage;
standards, strict mypy (189 source files), architecture and both builds pass.
Extracted-wheel actual settings/viewer entry/navigation, narrow maximum-text
bounds, 300-DPI export and no-write reopen pass. Two settings fixtures, three
symbol legends and the focus-normalized full panel match source pixels exactly;
settings/panel child geometry also matches. Sixty-four native captures were
visually inspected, including localized error states and adjacent map resizing.
All 500 reference hashes and approved lock remain unchanged. Evidence:
f114_validation.json, artifacts/f114-check.log, artifacts/f114-wheel.log and
artifacts/plot-graph-workflows.

Next: original outcome summary/gauges and full PLOT host, including parent
close/load consent and remaining map/deletion actions. The panel is ready for
that host; production PLOT remains disabled. JROT: CBC single-tool, HiGHS
multi-tool, no GLPK. Overall completion percentage and finish date remain
unvalidated.

## F113 historical checkpoint

Original PLOT summary calculations and four chart figures are migrated: tool,
sex, age and placed-job risk. Saved enable controls membership; missing evidence
stays absent, observed zero remains valid, and comparison differences use paired
assignments. Source styling and localized chart text are preserved. The original
Tools Overview panel/settings/expanded viewer are not yet composed.
[Source mapping, corrections and limits](plot_summaries.md).

Validation: 870 native tests pass (five focused new cases), 96.43% coverage;
standards, strict mypy (182 source files), architecture and both builds pass.
Extracted-wheel summaries/localized figures/no-write reopen pass. Three source/
native chart fixtures match pixel-for-pixel; age differs only at documented
missing-bin zero-bar strokes (61 pixels). Thirty-four native captures were visually
inspected at normal/enlarged sizes. All 500 reference hashes and approved lock
remain unchanged. Evidence: f113_validation.json, artifacts/f113-check.log,
artifacts/f113-wheel.log and artifacts/plot-summary-charts.

Next: original Tools Overview panel, symbol legend, graph settings and expanded
viewer; then outcomes and full PLOT host, including parent close/load consent and
remaining map/deletion actions. Production PLOT remains disabled. JROT: CBC
single-tool, HiGHS multi-tool, no GLPK. Overall completion percentage and finish
date remain unvalidated.

## F112 historical checkpoint

Original worker marker right-click actions are now connected: Lock, Save and
Load into Tool Window. Saved identity replaces source label/parent-attribute
coupling. The integrated LiFFT/DUET/ST editor reuses its pending-input and
Save/Discard/Cancel behavior. Pending map edits block handoff; loading does not
save positions. Full PLOT parent close handling is not yet composed.
[Source mapping, corrections and limits](plot_context_actions.md).

Validation: 865 native tests pass (five focused new cases), 96.42% coverage;
standards, strict mypy (180 source files), architecture and both builds pass.
Extracted-wheel menu/lock/save/reopen, actual editor Cancel/Save and all three tool
handoffs pass. Both original/native English menu states match pixel-for-pixel.
Localized menus and complete integrated windows with native VTK frames were
visually inspected (20 evidence images). All 500 reference hashes and approved
lock remain unchanged. Evidence: f112_validation.json, artifacts/f112-check.log,
artifacts/f112-wheel.log and artifacts/plot-context-actions.

Next: original summaries and full PLOT composition, including parent close
consent/load sequence and remaining map/deletion actions. Production PLOT remains
disabled. JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion
percentage and finish date remain unvalidated.

## F111 historical checkpoint

Original PLOT worker search is now connected to Worker Overview. Live text and
exact hierarchy filtering return stable assignment identities; Select reveals the
correct worker outside the current alphabet filter. Cancel preserves partial
visual-setting edits. Hidden/unplaced workers are selected without fabricated
markers or writes. Original layout/icons/keyboard mnemonic and localization are
retained. [Source mapping, corrections and limits](plot_worker_search.md).

Validation: 860 native tests pass (three focused new cases), 96.40% coverage;
standards, strict mypy (180 source files), architecture and both builds pass.
Extracted-wheel actual modal Cancel/Select, draft preservation and unchanged
positions after reopen pass. Three original/native picker states match
pixel-for-pixel; 25 native captures were inspected, including both languages,
minimum/enlarged sizing and adjacent map/overview. All 500 reference hashes and
approved lock remain unchanged. Evidence: f111_validation.json,
artifacts/f111-check.log, artifacts/f111-wheel.log and artifacts/plot-worker-picker.

Next: original marker context actions/Load Into Tool, then summaries/full PLOT.
Production PLOT remains disabled. Parent close consent, remaining map/deletion
composition and final acceptance remain. JROT: CBC single-tool, HiGHS multi-tool,
no GLPK. Overall completion percentage and finish date remain unvalidated.

## F110 historical checkpoint

Original Worker Overview now composes selector/order/alphabet/navigation,
workplace context, worker details, saved assessment/job risk comparison, source
marker preview, Locate and F109 visual controls. Assignment identity and typed
per-worker drafts survive navigation/refresh; units project body metadata without
writes. Missing/scientific-review risk remains unavailable. Search is styled but
disabled until its original picker is migrated.
[Source mapping, differences and limits](plot_worker_overview.md).

Validation: 857 native tests pass (three focused new cases), 96.17% coverage;
lint/format, strict mypy (179 source files), architecture and both builds pass.
Extracted-wheel navigation/drafts/batch-save/units/Locate/reopen checks pass.
Three original/new preview fixtures match pixel-for-pixel. English/Spanish states,
390–510-pixel pane resizing and adjacent map containment were visually inspected.
All 500 reference hashes and approved lock remain unchanged. Evidence:
f110_validation.json, artifacts/f110-check.log, artifacts/f110-wheel.log and
artifacts/plot-worker-overview.

Next: original worker search picker and marker context/Load Into Tool handoff,
then summaries/full PLOT. Production PLOT remains disabled; full details tabs and
outcomes are not yet composed. Parent close consent, remaining map actions,
intentional deletion composition and final acceptance remain. JROT: CBC single-
tool, HiGHS multi-tool, no GLPK. Overall completion percentage and finish date
remain unvalidated.

## F109 historical checkpoint

Original Worker Overview visual-settings region now controls saved/draft marker
visibility, inclusion, lock, original-image X/Y and scale. Single Save validates
and commits settings; Save All validates the batch and writes once atomically.
Failed writes retain intent for retry; newly positioned workers initialize only
missing station anchors. Original success dialogs and English/Spanish controls
are retained. The surrounding Worker Overview is not yet composed.
[Behavior, source mapping and limits](plot_worker_visual_controls.md).

Validation: 854 native tests pass (three focused new cases), 96.31% coverage;
lint/format, strict mypy (177 source files), architecture and both builds pass.
Extracted-wheel actual late SQL batch rollback, retry and reopen pass. Native
source/populated controls match pixel-for-pixel; 25 captures cover localized
empty/flags/edit/error/saved/success/resized states and adjacent map containment.
All 500 reference hashes and approved lock remain unchanged. Evidence:
f109_validation.json, artifacts/f109-check.log, artifacts/f109-wheel.log and
artifacts/plot-worker-controls.

Next: original worker selector/alphabet/search/navigation, details and assessment
result/preview/Locate composition; then context actions/Load Into Tool, summaries
and full PLOT. Production PLOT remains disabled. Unplaced workers require explicit
coordinates before Save All; see the documented behavior difference. Parent close
consent, remaining map actions, intentional deletion composition and final
acceptance remain. JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall
completion percentage and finish date remain unvalidated.

## F108 historical checkpoint

Original PLOT Job Placement overview now composes with the saved marker layer:
selector/navigation, placement/risk/profile details, shared-station X/Y editing,
Save/Cancel, pending navigation locks and Locate pulses. Typed/dragged edits retain
intent on invalid/failed Save; accepted writes preserve worker coordinates.
English/Spanish captions and original grids/icons/spacing are retained.
[Source mapping, differences and limits](plot_job_overview.md).

Validation: 851 native tests pass (three focused new cases), 96.30% coverage;
lint/format, strict mypy (176 source files), architecture and both builds pass.
Extracted-wheel overview/save/retry/Cancel/reopen checks pass. Empty/populated
English overview fixtures match original-code captures pixel-for-pixel; 22 native
captures cover localized edit/empty/selected/resized states and adjacent map
containment. All 500 reference hashes and approved lock remain unchanged.
Evidence: f108_validation.json, artifacts/f108-check.log, artifacts/f108-wheel.log
and artifacts/plot-job-overview.

Next: original Worker Overview, visual/position/Save controls and marker context
handoff, then summaries and complete PLOT composition. Production PLOT remains
disabled; this completed component is not full-window parity. Parent close consent,
remaining map actions, intentional deletion composition and final acceptance remain.
JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion percentage
and finish date remain unvalidated.

## F107 historical checkpoint

PLOT now renders original worker/job markers from saved results and geometry.
Individual, comparison and job shapes/colors/selection preserve reviewed source
code. Native drag and Ctrl-scale produce explicit saveable intent; failed Save
retains edits, Cancel restores saved geometry, and job Save refreshes shared
station placements without moving saved workers. Rendering stays independent of
SQL/main-window lookup and body units. Zero anchors are preserved correctly.
[Source mapping, differences and limits](plot_marker_rendering.md).

Validation: 848 native tests pass (five focused new cases), 96.24% coverage;
lint/format, strict mypy (175 source files), architecture and both builds pass.
Extracted-wheel render/save/retry/Cancel/reopen checks pass. Three original/new
native marker fixtures match pixel-for-pixel. English/Spanish component compositions
were visually inspected at 1460×1060 and 1920×1200, including empty, populated,
selected, pending and error states. All 500 reference hashes and approved lock
remain unchanged. Evidence: f107_validation.json, artifacts/f107-check.log,
artifacts/f107-wheel.log and artifacts/plot-markers.

Next: original worker/job overviews, position controls/context actions and
selection handoff, then summaries and complete PLOT composition. Production PLOT
remains disabled; this is a component harness, not full-window parity. Parent
close consent, remaining map actions, intentional deletion composition and final
acceptance remain. JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall
completion percentage and finish date remain unvalidated.

## F106 historical checkpoint

PLOT datasets now carry typed station anchors and assignment-owned worker marker
positions. Original hidden/unplaced/inherited/manual semantics and first-worker
anchor initialization are preserved. Explicit position Save upgrades full projects
to format ten atomically; read-only loads do not migrate. Maps, reopen, Backup and
Save As retain geometry. Position identity/membership guards cover referenced
stations and historical or unassessed assignments.
[Source mapping, compatibility and limits](plot_position_persistence.md).

Validation: 843 native tests pass (15 focused new cases), 96.58% combined coverage;
lint/format, strict mypy (173 source files), architecture and both builds pass.
Extracted-wheel geometry matches six original movement states; save/results/copies/
reopen checks pass. Late schema/SQL failures roll back records and version.
No UI layout changed; F104 visuals remain applicable. All 500 reference hashes
and the approved lock remain unchanged. Evidence: f106_validation.json,
artifacts/f106-check.log and artifacts/f106-wheel.log.

Next: original marker rendering and move/save interactions, then worker/job
overviews and summaries in complete PLOT composition. Production PLOT remains
disabled; persisted geometry is not yet displayed as markers. Parent close consent,
remaining map actions, intentional deletion composition and final acceptance remain.
JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion percentage
and finish date remain unvalidated.

## F105 historical checkpoint

PLOT's Apply callback can now load saved selected-tool/all-tool worker results and
active job-placement results. Active/current assignment ownership, exact hierarchy
and shift filters, demographics, counts and current approved job evidence follow
the original normalized queries. Missing evidence stays absent; existing
scientific gates remain. CSV and PLOT share saved-source evaluation without
sharing their different closed-assignment selection rules.
[Behavior, source comparison and limits](plot_result_datasets.md).

Validation: 828 native tests pass (eight focused new cases), 96.54% combined coverage;
lint/format, strict mypy (171 source files), architecture and both builds pass.
Extracted-wheel datasets match 24 source-SQL scope/tool/demographic comparisons.
Actual Apply reads saved project data while preserving pending main edits and
project bytes. No UI layout changed; F104 visuals remain applicable. All 500
reference hashes and the approved lock remain unchanged. Evidence:
f105_validation.json, artifacts/f105-check.log and artifacts/f105-wheel.log.

Next: original station/worker positions and anchoring, then dataset rendering and
worker/job summaries in the complete PLOT composition. Production PLOT remains
disabled; data loading does not yet imply displayed markers or summaries. Parent
close consent, remaining map actions and final parity/acceptance remain. JROT:
CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion percentage and
finish date remain unvalidated.

## F104 historical checkpoint

The original PLOT filter grid now includes risk-view selection, optional worker
demographics and Apply/Clear. Source geometry/disclosure is retained. Immutable
predicates preserve paired-bound and birth-year behavior; canonical kg/cm bounds
survive repeated metric/imperial changes without rounding drift. Explicit decimal
input is independent of language. Unit headings avoid clipped values in narrow
fields. Apply failures retain the applied snapshot; Clear restores defaults after
map consent without automatically applying.
[Source mapping, differences and limits](plot_demographic_filters.md).

Validation: 820 native tests pass (nine focused new cases), 96.53% combined coverage;
lint/format, strict mypy (169 source files), architecture and both builds pass.
Native source-region and English/Spanish disclosure/populated/units/resize/Clear/error
checks and isolated-wheel Apply/units/decimal/failure/Clear checks pass. All 500
reference hashes and the approved lock remain unchanged. Evidence:
f104_validation.json, artifacts/f104-check.log and artifacts/f104-wheel.log.

Next: connect scoped historical worker/job result datasets, then original markers
and summaries in the complete PLOT window. Production PLOT remains disabled;
functional synthetic demographic predicates do not imply assessment query integration.
Parent close consent, remaining map actions and final parity/acceptance remain.
JROT: CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion percentage
and finish date remain unvalidated.

## F103 historical checkpoint

Original PLOT workplace/path blocks and exclusive tool buttons now compose with
the map panel. Actual modal choice updates labels only after map acceptance;
Cancel/discard-No/load failure preserves both. Typed tool selection emits once
per change without discarding map edits. Long/literal names fit with full escaped
tooltips; English/Spanish captions and literal shift identities are retained.
[Source mapping and remaining composition](plot_filter_controls.md).

Validation: 811 native tests pass (eight focused new cases), 96.48% combined coverage;
lint/format, strict mypy (167 source files), architecture and both builds pass.
Native source-region comparisons, empty/expanded/selected/default/enlarged and
literal-text checks pass. Extracted-wheel picker/map/label/preview/save/tool-intent
and discard-No checks pass. All 500 reference hashes and the approved lock remain
unchanged. Evidence: f103_validation.json, artifacts/f103-check.log.

Next: original risk-view/demographic filters and Apply/Clear, then scoped worker/job
results, markers and summaries in the complete PLOT composition. Production PLOT
remains disabled; current controls do not filter datasets yet. Parent close consent,
remaining map actions and final parity/acceptance remain. JROT solver routing is
recorded: CBC single-tool, HiGHS multi-tool, no GLPK. Overall completion percentage
and finish date remain unvalidated.

## F102 historical checkpoint

The original PLOT map/action rail is now a reviewed Qt component with working
Open/Save buttons: read-only preview, persisted save, failure retry, localized
messages and consent before discarding an unsaved map on scope change. Source
rail dimensions/icon order and expanding image canvas are retained. Remaining
rail actions are disabled. [Behavior and remaining composition](plot_map_controls.md).

Validation: 803 native tests pass (six focused new cases), 96.43% combined coverage;
lint/format, strict mypy (166 source files), architecture and both builds pass.
Source-extracted/English/Spanish no-scope/empty/preview/saved/error/consent/enlarged
states were inspected, including full map/rail containment. Isolated-wheel actual
button, chooser/message, failure/retry and saved reopen checks pass. All 500
reference hashes and the approved lock remain unchanged. Evidence:
f102_validation.json, artifacts/f102-check.log.

Next: original workplace/tool filter region and full PLOT window composition,
then worker/job markers and summaries. Production PLOT is still disabled; the
working component harness is not the complete production workflow. Parent modal
close consent, remaining rail actions and final parity/acceptance remain. JROT's
CBC single-tool/HiGHS multi-tool/no-GLPK decision remains recorded. Overall
percentage and finish date remain unvalidated.

## F101 historical checkpoint

PLOT image import/explicit save now works through the tested component APIs.
PNG/JPG validation retains original bytes; maps are stored transactionally inside
the project so reopen, Save As and Backup carry them without external files.
Full formats seven/eight upgrade to nine only on an accepted image save; failure
preserves schema/version/old map. Save As metadata edits retain nine. Pending
LiFFT/DUET/ST inputs stay unchanged. [Storage and workflow limits](plant_image_persistence.md).

Validation: 797 native tests pass (14 focused new cases), 96.41% combined coverage;
lint/format, strict mypy (165 source files), architecture and both builds pass.
The unchanged canvas's preview/reload/enlarged replacement states were inspected;
extracted-wheel scope/preview/save/reopen/copy checks pass. All 500 reference
hashes and the approved lock remain unchanged. Evidence: f101_validation.json,
artifacts/f101-check.log.

Next: compose the original PLOT window and connect its original Open/Save controls,
scope and saved-image loading; then markers/filters/summaries. Production PLOT is
still disabled; API/component tests are not an integrated production workflow.
Legacy sidecars, other final parity/acceptance and JROT remain. The owner's JROT
decision is recorded in final_targets.md: CBC single-tool, HiGHS multi-tool, no GLPK.
Exact solver dependency approval remains separate. Overall percentage and finish
date remain unvalidated; test coverage does not measure functional completion.

## F100 historical checkpoint

Migrated the original PLOT workplace-scope picker and read-only image canvas as
reviewed components. One-plant/parent-child checks, literal shifts, English/Spanish
captions and original pixel coordinates are preserved. Empty hierarchy parents
are retained; invalid images leave the current map intact, missing images clear
it, and resize fitting keeps the whole map visible. [Scope and limits](plot_layout_components.md).

Validation: 783 native tests pass (14 focused new cases), 96.40% combined coverage;
lint/format, strict mypy (162 source files), architecture and both builds pass.
Native source-derived picker/map comparisons, collapsed/expanded/selected/empty/
enlarged English/Spanish states and canvas resize/missing states were inspected.
Extracted-wheel modal selection/loading/invalid retention/resize checks pass.
All 500 reference hashes and the approved lock remain unchanged. Evidence:
f100_validation.json, artifacts/f100-check.log.

This is a component slice: production PLOT remains disabled, image associations
are injected, and image import/save/full-window panels are not yet implemented.
Next: persisted image import/save and composition of the original PLOT window.
JROT, remaining lifecycle/legacy/localization/scientific parity and final copied-
project/platform acceptance still remain. Overall percentage and finish date
remain unvalidated; test coverage is not application completion.

## F99 historical checkpoint

Integrated Save As now opens the original prefilled Name/Description form. Cancel
preserves pending input on all three tools; accepted copy details include fresh
creation time/language/unit defaults without modifying the original, assessment
source units or ownership/catalogs. Format-seven full projects upgrade only the
copy to eight; existing format-eight details are replaced in the copy. Backup and
callers omitting metadata retain prior behavior. [Scope and limits](save_as_details.md).

Validation: 769 native tests pass (nine focused new cases), 96.34% combined coverage;
lint/format, strict mypy (156 source files), architecture and both builds pass.
Source-derived/English/Spanish prefilled/edited/expanded forms, copied Properties
and integrated VTK/card/bottom layouts were inspected. Extracted-wheel Cancel,
copy upgrade/original isolation, details, Backup/reopen and second Save As pass.
All 500 reference hashes and the approved lock remain unchanged. Evidence:
f99_validation.json, artifacts/f99-check.log.

Next usable workflow: original PLOT plant/layout selection and saved-layout
loading, using the actual reference source. Earlier partial project formats retain
ordinary copying; unsaved-New/first-Save timing, sidecars/legacy import, remaining
localization/F95 message parity, renderer extras, scientific gates, PLOT/JROT and
final copied-project/platform acceptance remain. Overall percentage and finish
date remain unvalidated.

## F98 historical checkpoint

The integrated New workflow collects the original Name/Description form, records
creation date/time/language/units and shows the stored title in the main header.
Cancel preserves invalid pending input on all three tools; accepted details use
existing validation/dirty consent. Properties displays available saved details.
New files use format eight; older formats remain readable without automatic
rewriting. Save As/Backup/reopen preserve the new metadata.
[Workflow, compatibility and remaining parity](project_details.md).

Validation: 760 native tests pass (twelve focused new cases), 96.35% combined coverage;
lint/format, strict mypy (156 source files), architecture and both builds pass.
Native source-derived/English/Spanish empty/populated/expanded forms, persisted
Properties and named integrated VTK/card/bottom controls were inspected.
Extracted-wheel three-tool Cancel, creation, Properties, snapshots and reopen pass.
All 500 reference hashes and the approved lock remain unchanged. Evidence:
f98_validation.json, artifacts/f98-check.log.

Next usable workflow: original Save As prefilled Name/Description form. Exact
unsaved-New/first-Save timing, sidecars/legacy import, remaining localization/F95
message parity, renderer extras, scientific gates, PLOT/JROT and final copied-
project/platform acceptance remain. Overall percentage and finish date remain
unvalidated.

## F97 historical checkpoint

Project > Properties now opens the original 500 by 400 read-only field layout with
English/Spanish captions and Close workflow. It uses current project metadata and
location without accepting pending assessment text. Saved units are independent
of display units; Save As locations update, and no project disables the action.
Long/literal values are escaped and elided with full-value tooltips.
[Mapping and remaining metadata parity](project_properties.md).

Validation: 748 native tests pass (five focused new cases), 96.35% combined coverage;
lint/format, strict mypy (154 source files), architecture and both builds pass.
Native original-source-derived/default/Spanish/long-value/no-project menus and
integrated VTK/card/bottom layout checks pass. Extracted-wheel three-tool pending,
source/preferences, copied-location/Spanish and Close checks pass. All 500 reference
hashes and the approved lock are unchanged. Evidence: f97_validation.json,
artifacts/f97-check.log.

Next usable workflow: original New Project metadata collection/persistence. The
current format still lacks description, creation date/time, project language and
legacy sidecars; Properties explicitly shows N/A for these. Remaining localization,
F95 native message parity, renderer extras, scientific gates, PLOT/JROT, legacy
import and final copied-project/platform acceptance remain. Overall percentage
and finish date remain unvalidated.

## F96 historical checkpoint

The original View > Animated body-region focus now persists enabled/disabled
policy. Accepted mouse tool clicks use the original three-stage camera motion;
programmatic changes/ordinary refreshes do not animate. Disabling restores full
body; enabling/Reset focuses the active region. Manual controls and close cancel
motion. Pending assessment input remains untouched. [Behavior and compatibility](camera_animation.md).

Validation: 743 native tests pass (nine focused new cases), 96.34% combined coverage;
lint/format, strict mypy (153 source files), architecture and both builds pass.
Original interpolation/easing matches all three stage midpoints. English/Spanish
View, no-renderer, intermediate/settled tools, full-body off and enlargement were
inspected. Extracted-wheel actual motion completion, on/off, pending/preferences,
disabled restart and in-motion cleanup pass. Strict settings versions one/two remain
readable; explicit saves write version three. All 500 reference hashes and the
approved lock are unchanged. Evidence: f96_validation.json, artifacts/f96-check.log.

Next usable workflow: original project Properties/details. Remaining localization,
F95 native message parity, renderer extras, scientific gates, PLOT/JROT, legacy
import and final copied-project/platform acceptance remain. Overall percentage
and finish date remain unvalidated.

## F95 historical checkpoint

Worker Transfer now localizes supporting text, tooltips, empty guidance, Cancel /
All, full tool descriptions and owned confirmation/error/success buttons. Record
values are never translated; names matching English captions stay unchanged.
No remains consent's default/Escape choice. Native owned message button order/icons
differ from the earlier static capture and remain a final UI parity item.
[Behavior and limits](transfer_localization.md).

Validation: 734 native tests pass (five focused new cases), 96.37% combined coverage;
lint/format, strict mypy (152 source files), architecture and both builds pass.
English reference/new default, Spanish selected/minimum/enlarged/empty/filter,
tooltip/messages and native integrated VTK layouts were inspected. Extracted-wheel
Spanish consent, three-tool Copy/Move-Save, conflicts, units/history/settings and
cleanup pass. All 500 reference hashes and the dependency lock are unchanged.
Evidence: f95_validation.json, artifacts/f95-check.log.

Next usable workflow: original View camera animation/preferences. Remaining dialog /
main-prompt / stock-control localization and native message parity are recorded.
Original project details/sidecars, scientific gates, PLOT/JROT, legacy import and
final copied-project/platform acceptance remain. Overall percentage and finish date
remain unvalidated.

## F94 historical checkpoint

Tools > Settings now persists an explicit point/comma decimal convention separately
from language and units. New windows restore it before binding controls. Apply
validates pending input using the old convention; Cancel/invalid input/write failure
retain the old policy. Recorded source units/values are retained. Strict settings
version one loads read-only with point default; explicit saves write version two.
[Behavior and compatibility](decimal_preferences.md).

Validation: 729 native tests pass (four focused new cases), 96.34% combined coverage;
lint/format, strict mypy (151 source files), architecture and both builds pass.
English/Spanish selected/expanded Settings and all three native comma layouts were
inspected. Extracted-wheel modal Apply, comma input/projection, persisted restart,
source units and VTK cleanup pass. All 500 reference hashes and the dependency lock
are unchanged. Evidence: f94_validation.json, artifacts/f94-check.log.

Next: complete remaining dialog/stock-control localization review, then renderer
View animation/preferences. Original project details/sidecars, scientific gates,
PLOT/JROT, legacy import and final copied-project/platform acceptance remain.
No validated replacement overall percentage or finish date has been established.

## F93 historical checkpoint

The original Help menu and toolbar User Guide now open the packaged original PDF
through Qt's cross-platform document handler. About retains the exact English
credits/logo and original 600 by 700 form, with a fresh owned dialog on each open.
Help preserves pending assessment input and works without an open project.
Cache/viewer failures produce owned messages. [Behavior and limits](help_workflow.md).

Validation: 725 native tests pass (six focused new cases), 96.33% combined coverage;
lint/format, strict mypy (150 source files), architecture and both builds pass.
Same-platform original/new Authors, English/Spanish Help menus, owned error and
populated/empty native VTK layouts were inspected. Extracted-wheel resource hashes,
complete PDF publication, launcher requests, repeated About, three-tool pending /
source / settings preservation and cleanup pass. The actual external PDF viewer
was not launched; that remains a manual platform check. All 500 reference hashes
and the dependency lock are unchanged. Evidence: f93_validation.json,
artifacts/f93-check.log. The original English manual/credits body is retained.

Next: complete application preferences/localization and decimal persistence.
The original View animation command belongs to remaining renderer work. Project
details/sidecars, scientific gates, PLOT/JROT, legacy import and final copied-
project/platform acceptance remain. No validated replacement overall percentage
or finish date has been established.

## F92 historical checkpoint

The original Worker Transfer form is integrated into the worker strip. Selected
LiFFT/DUET/ST saved current versions can be copied or moved to another worker,
workplace or shift. Move is atomic; existing destination data rejects the entire
selection. Copy preserves pending input. Moving the open source requires explicit
Save/Discard/Cancel when dirty, then clears it after successful removal. Older
history and job profiles remain. [Behavior and limits](assessment_transfer.md).

Validation: 719 native tests pass (eight focused new cases), 96.38% combined
coverage; lint/format, strict mypy (148 source files), architecture and both builds
pass. Original/new default forms, selected Copy/Move, empty source/filter, minimum,
Spanish/enlarged, confirmation/error and integrated native VTK layouts were
inspected. Extracted-wheel actual modal No/Copy/Move-Save, conflicts, source units,
closed ownership, settings and renderer cleanup pass. All 500 reference hashes and
the dependency lock are unchanged. Evidence: f92_validation.json,
artifacts/f92-check.log. Principal Spanish controls are translated; supporting
copy/tooltips and stock Qt wording still need the full-language review.

Next: remaining View/Help operations and completion of application preferences /
localization / decimal persistence. Original project details/sidecars, scientific
gates, remaining renderer features, PLOT/JROT, legacy import and final copied-
project/platform acceptance remain. No validated replacement overall percentage
or finish date has been established.

## F91 historical checkpoint

Project > Export selected tool to CSV and the original Export toolbar now export
saved current summaries for all workers for LiFFT/DUET/ST. Export preserves pending
text, source/history, project and preferences. Current assessments remain attached
to their original historical assignment, including closed assignments; noncurrent
versions are excluded. Existing grid evaluators retain completed-row totals beside
blank slots with explicit partial status. Scientific/invalid outcomes export absent
results and status/issue keys. [Behavior and CSV differences](assessment_export.md).

Validation: 711 native tests pass (eight focused new cases), 96.63% combined
coverage; lint/format, strict mypy (144 source files), architecture and both builds
pass. Native English/Spanish menu states, selected CSV picker, three-tool pending
Export, no-data/error layouts were checked at 1550 by 1015. Error-state visual
review corrected inherited status wrapping that compressed avatar captions.
Extracted-wheel saved scope, ownership, pending/source/settings preservation,
scientific gates and native cleanup pass. All 500 reference hashes and the lock
are unchanged. Evidence: f91_validation.json, artifacts/f91-check.log.

Next: original worker-transfer workflow, then remaining menu/settings integration.
This is migrated source-derived CSV, not full legacy report/CSV format parity.
Original project details/sidecars, View/Help, full localization/decimal preferences,
scientific gates, remaining renderer features, PLOT/JROT, legacy import and final
copied-project/platform acceptance remain. Overall percentage and finish date
remain unvalidated after withdrawal of the former 67%.

## F90 historical checkpoint

Project > Save As and Backup saved project now expose complete new-format snapshots.
Save As includes validated current edits only in the selected source in the copy,
activates that clean copy and leaves the original unsaved file unchanged.
Backup includes persisted data only and retains pending text, source/history,
location and preferences. SQLite backup includes committed WAL data; temporary
validation and exclusive publication protect existing destinations. Ordinary
copy failures retain the current session; recency/cleanup failures after successful
activation remain separate warnings. [Behavior and limits](project_snapshots.md).

Validation: 703 native tests pass (eleven focused new cases), 96.62% combined
coverage; lint/format, strict mypy (141 source files), architecture and both builds
pass. Native English/Spanish populated/disabled menus, selected owned pickers,
Cancel/pending, three-tool copied main views, saved-only Backup and copied/closed
layouts were inspected at 1550 by 1015. Native avatar, cards, headers, labels and
bottom controls remain visible. Real picker Cancel/suffix acceptance and repeated
ordinary/native-VTK picker use pass. Extracted-wheel three-tool Save As/backup,
unchanged original sources, complete ownership/catalogs and renderer cleanup pass.
All 500 reference hashes and the lock are unchanged. Evidence: f90_validation.json,
artifacts/f90-check.log.

Next: assessment export, then worker transfer and remaining menu/settings
integration. Original project Name/Description editing and legacy image sidecars
are not yet migrated; Save As retains metadata. Native platform/filesystem,
legacy import and final copied-project acceptance remain. Scientific gates,
remaining overlays/camera animation, PLOT/JROT, View/Help and full localization/
decimal preferences remain unchanged. Overall percentage and finish date remain
unvalidated after withdrawal of the former 67%.

## F89 historical checkpoint

Project > Recent projects and Close project now complete the recent-history and
explicit close/reopen workflow. Recent entries use the existing bounded settings
history without opening databases while listing. Missing-file removal requires
confirmation; Clear history preserves preferences, source and pending task text.
Available entries use the same explicit assessment picker as Open. Cancelled or
failed target loads retain the current session. Close validates pending text, then
uses existing Save/Discard/Cancel handling; it clears the project while retaining
the main window and native renderer. [Behavior and limits](recent_project_menu.md).

Validation: 692 native tests pass (seven focused new cases), 96.84% combined
coverage; lint/format, strict mypy (141 source files), architecture and both builds
pass. Expanded populated/empty menus, actual missing-file/dirty-close prompts,
invalid/Cancel Close and English/Spanish closed main states were inspected.
Visual review found and corrected a clipped Spanish empty-grid summary label.
Avatar, cards, headers and bottom controls remain visible at 1550 by 1015.
Extracted-wheel three-tool Close/recent reopen, history isolation and renderer
retention/cleanup pass. All 500 reference hashes and the approved lock are unchanged.
Evidence: f89_validation.json, artifacts/f89-check.log.

Next: Save As/backup, followed by remaining menu/workflow integration.
Transfer/export, View/Help, full dialog localization and decimal preference
persistence remain. Scientific direction/metric moment gates, overlays/camera
animation, PLOT/JROT, legacy import and final copied-project/platform acceptance
remain unchanged. Overall percentage and finish date remain unvalidated after
withdrawal of the former 67%.

## F88 historical checkpoint

Tools > Settings now opens an owned application-preferences dialog for independent
language and unit choices. It uses the established stylesheet and packaged icons.
Cancel changes nothing, including pending task text. Apply validates pending text
before persisting preferences through the existing atomic settings adapter. Invalid
input retains source/preferences; failed settings writes retain the previous display
policy. Valid accepted task input remains a normal source edit and is rebound even
when settings persistence fails. Recorded source units and values are not rewritten
by display projection; recent-project history is retained. Fresh windows restore
saved language/units without requiring an open project. The existing toolbar Settings
still opens task count. [Behavior and limits](preferences_dialog.md).

Validation: 685 native tests pass (three focused tool workflows), 96.85%
combined coverage; lint/format, strict mypy (141 source files), architecture and both
builds pass. Native default/selected/expanded dialog, Cancel/pending, invalid Apply,
three-tool Spanish/metric and enlarged main states were inspected. Visual checking
corrected LiFFT's footer to show selected display units rather than recorded source
units. Source units remain intact. Extracted-wheel Cancel/Apply, three-tool unchanged
persisted sources, preference restoration and native cleanup pass. All 500 reference
hashes and the approved lock remain unchanged. Evidence: `f88_validation.json`,
`artifacts/f88-check.log`.

Next: remaining project-menu lifecycle operations (recent projects and explicit
project close), then other menu/workflow integration. Save As/backup, transfer/export,
View/Help, dialog language completion and decimal preference persistence remain.
The existing scientific direction/metric moment review gates remain unchanged;
Settings does not resolve those formulas/labels. Overlays/camera animation, PLOT/JROT,
legacy import and final copied-project/platform acceptance remain planned. Overall
percentage and finish date remain unvalidated after withdrawal of the former 67%.

## F87 historical checkpoint

Project/Edit menus now expose the existing project, assessment and Undo/Redo actions
in the integrated window, rather than leaving them hidden in the development row.
New assessment is available in an open historical project with no active source.
After Delete, the user can explicitly choose worker/assignment and recreate the
selected tool's blank grid, edit it and Save. Cancelling either choice preserves
the empty state. Creation allocates the next version for that exact assignment/tool;
retained older versions are preserved, and an existing current source is not silently
replaced or demoted. Menus reuse original handlers, processed icons, captions and
availability rules; no parallel edit policy is introduced. English/Spanish menu
captions work. [Workflow and current limits](assessment_menu.md).

Validation: 682 native tests pass (four focused new cases), 96.85% combined
coverage; lint/format, strict mypy (140 source files), architecture and both builds
pass. Native empty/populated Project menus, Edit menu, expanded/selected assignment
modal and empty/recreated main states were inspected. Minimum 1550 by 1015 and
enlarged 1920 by 1200 layouts retain visible native avatar, cards, headers and bottom
controls. An isolated extracted wheel passed visible menu Delete/recreate/cancel,
three-tool editing and Save/reopen, untouched other ownership and renderer cleanup.
All 500 reference hashes and the lock are unchanged. Evidence: `f87_validation.json`,
`artifacts/f87-check.log`.

Next: the application Settings/preferences integration and remaining menu operations.
Project/Edit menus are incremental, not the full final menu set; Save As/recent/close
and View/Tools/Help integration remain. The existing assignment modal still uses its
English captions, including under Spanish menus; dialog catalog/Qt stock-message
translation remains outstanding. Scientific decisions, overlays/camera animation,
PLOT/JROT, legacy import and final copied-project/platform acceptance remain planned.
Overall percentage and finish date remain unvalidated after withdrawal of the former
67% estimate. The three-tool Delete/recreate/edit/Save recovery workflow is now usable;
this does not establish full application parity.

## F86 historical checkpoint

The original Delete buttons are connected on LiFFT, DUET and ST. The owned Yes/No
confirmation defaults to No and explicitly identifies open-version deletion and
abandonment of its unsaved edits. No leaves source/pending text unchanged. Yes
immediately removes that saved source and its ownership record in one transaction;
other versions, tools, workers and assignments remain unchanged. No older version
is promoted. Failures preserve the active editor and roll back database writes.
The confirmed tool displays an empty grid, cleared results and disabled source
operations; existing data can be selected explicitly through another tool/worker or
Open. Deletion is separate from Reset and is not Undo. English/Spanish confirmation
text is supported; Qt stock Yes/No labels retain the current environment baseline.
[Scope and behavior differences](assessment_deletion.md).

Validation: 678 native tests pass (five focused new cases), 96.82% combined
coverage; lint/format, strict mypy (139 source files), architecture and both builds
pass. Native confirmation, No/pending and Yes/empty states were inspected on each
tool, including Spanish ST and actual VTK framebuffers. Visual checking corrected
a post-delete DUET/ST card-caption fallback to LiFFT, with a regression assertion.
The capture fixture's display name ST was corrected to internal document identifier
TST; no production change was needed for that fixture error. An isolated extracted
wheel passed actual default-No/refusal/acceptance for all three tools, reopen,
exact ownership scope, empty states and renderer cleanup. All 500 reference hashes
and the dependency lock remain unchanged. Evidence: `f86_validation.json` and
`artifacts/f86-check.log`.

Next: remaining integrated menu/settings workflows, including explicit new-assessment
creation from empty states. Scientific review decisions, simultaneous overlays/camera
animation, PLOT/JROT, legacy import and final copied-project/platform acceptance
remain planned. Overall percentage and finish date remain unvalidated after withdrawal
of the former 67% estimate; this checkpoint completes scoped saved-data deletion,
not full application parity.

## F85 historical checkpoint

The original six-column Tool Data Selection modal is migrated and connected to the
grid button on LiFFT, DUET and ST. It lists saved current assessments for the active
worker/tool, including retained closed assignments. Table sorting preserves exact
assignment identity. Close preserves pending text; Load validates pending inputs
then honors Save/Discard/Cancel before opening the chosen saved source. No missing
assessment is created, no current marker is promoted and ownership stays unchanged.
Reference scrollable table, 800 by 400 initial size, Close/Load placement and
selection/double-click behavior are retained, with English/Spanish captions and
existing application styling. Tooltip identities distinguish same-workplace owners.
[Behavior and evidence](saved_tool_data.md).

Validation: 673 native tests pass (five focused new cases), 96.91% combined
coverage; lint/format, strict mypy (139 source files), architecture and both builds
pass. Native unselected/selected and loaded-main states were inspected for all three
tools; Spanish selected/empty states were inspected. Styled header clipping observed
in the first captures was fixed with painted-font/padding-aware column sizing and
a regression assertion. Native main captures include actual VTK framebuffers.
The independently extracted wheel passed all three modal Cancel/Load operations,
Save/reopen, exact closed-owner selection, unchanged currentness and renderer cleanup.
All 500 reference hashes and the dependency lock remain unchanged. Evidence:
`f85_validation.json`, `artifacts/f85-check.log`.

Next: migrate the original saved-data Delete operation with an atomic persistence
contract, its confirmation and context-specific scope. The Delete buttons remain
disabled in this checkpoint; Reset is a separate source edit. Remaining menu/settings,
scientific review decisions, simultaneous overlays/camera animation, PLOT/JROT,
legacy import and final copied-project/platform acceptance remain planned.
Overall percentage and finish date remain unvalidated after withdrawal of the former
67% estimate; selection is now usable on all three tabs, not full application parity.

## F84 historical checkpoint

The original task-count Settings modal now operates on all three assessment tabs.
DUET/ST use its existing default of 10 and 1–100 limits. Cancel retains pending text,
including invalid input. Acceptance replaces only the active tool's rows with fresh
blank defaults, even when the count is unchanged; a single Undo restores the source.
ST source units, assessment ownership/version and other tools' data are preserved.
Save/reopen retains the accepted rows. Counts belong to each source, not a new
application-wide preference. English/Spanish history and confirmation are supported.
[Behavior and evidence](task_count_integration.md).

Validation: 668 native tests pass (six focused new workflows), 96.93% combined
coverage; lint/format, strict mypy (137 source files), architecture and both builds
pass. The actual owned modals were inspected at default/selected maximum, plus
Cancel/pending, one blank row, Undo/populated and row-100 bottom states in the main
window. English DUET and Spanish ST captures include actual native VTK framebuffers,
sticky headers, result cards and bottom controls. The large-rebuild regression waits
for the existing queued header synchronization rather than assuming a fixed 30 ms
settles layout; no production header-layout change was required. An independently
extracted wheel passed modal Cancel/accept, source-unit retention, Save/reopen,
other-tool preservation, Undo and native cleanup. All 500 reference hashes and the
approved dependency lock are unchanged. Evidence: `f84_validation.json`.

Next: migrate remaining saved-data/task-selection and Delete workflows, then the
remaining menu/settings integration. Existing scientific review gates remain;
ST direction semantics and ST/LiFFT metric moment conversion need resolution.
Simultaneous multi-tool overlays/camera animation, PLOT/JROT, legacy import and
final copied-project/platform acceptance remain planned. Three of three task tabs
and their task-count modal are connected; full application parity remains incomplete.
Overall percentage and finish date remain unvalidated after withdrawal of the former
67% estimate. This checkpoint adds usable workflow coverage, not a new overall estimate.

## F83 historical checkpoint

ST is now connected to the original integrated main window. All three assessment
tabs select their own source while sharing worker/assignment/context selection,
Save/Discard/Cancel, version creation, status/cards, footer and native viewport.
Open lists all three migrated document kinds; the older isolated LiFFT harness
remains LiFFT-only. Missing ST data requires explicit creation consent and retains
the original assignment, next historical version and current marker.

ST Calculate validates committed input and displays the existing scientific review
requirement. Review/invalid/pending states clear obsolete gauge/damage values and
anatomical overlays, without bypassing either direction or metric gate. The native
camera frames shoulders; original Shoulder captions and input metrics replace
previous-tool captions. Reset clears inputs and stale messages. Spanish captions,
unit projection and main-window enlargement remain supported. The Spanish shoulder
gauge caption wraps into two lines to prevent observed clipping.
[Connected workflows and remaining limits](tst_integration.md).

Validation: 662 native tests pass (five new integration workflows), 96.89% combined
coverage; lint/format, strict mypy (137 source files), architecture and both builds
pass. Native populated/review/expanded/Spanish/metric/pending-invalid/empty-bottom/
DUET-return/ST-return states were inspected at 1550×1015 and 1920×1200. Actual VTK
framebuffers are composed into Qt captures as documented in F78. Extracted-wheel
three-tool switching, ST review/cards/native scene, edit/Save/reopen and cleanup
pass. All 500 reference hashes and the approved dependency lock remain unchanged.
The existing LiFFT geometry test now waits for native layout/deferred header events
rather than assuming two event pumps settle them. Evidence: `f83_validation.json`.

Next: complete the original task-count Settings operation for DUET/ST, then remaining
menu/settings and saved-data/task-selection workflows. Scientific resolution of ST
selector semantics and ST/LiFFT metric moment conversion remains outstanding.
Retained simultaneous multi-tool overlays/camera animation, PLOT/JROT, legacy import,
final copied-project and platform acceptance remain planned. Three of three task
tabs are connected, but this does not mean all calculations or full UI/workflows
are accepted. Overall percentage and finish date remain unvalidated after withdrawal
of the former 67% estimate.

## F82 historical checkpoint

The original eight-column ST task component and its widget-independent presenter
are migrated. Original column minima/stretches, task-type control limits, zero-height
inline headers, sticky headers, hidden summary spacing and styled bottom controls
are preserved. English/Spanish original task labels and metric/imperial input
projections work without rewriting source values. No permanent standalone ST
application or new launcher was added.

Grid parsing commits all rows as one source/history change; invalid text remains
visible and source stays intact. Reset selects Handling Loads, clears numeric
inputs and supports Undo. Edited display quantities convert back to original units;
unchanged projected values preserve exact source values. New-format direction
identities are stored explicitly: the unresolved legacy selector swap is not used
or inferred for import. Calculate validates input and reports the existing review
gate; it exposes no ST results. Both direction and metric review gates remain.
[Scope and direction policy](tst_task_panel.md).

Validation: 657 native tests pass (five new focused workflows), 96.79% combined
coverage; lint/format, strict mypy (137 source files), architecture and both builds
pass. Native original/new component comparison at 980×650 gives identical body
(9,57,962,478) and Calculate (427,601,544,40) geometry. Populated, empty, expanded,
translated, invalid, review-gated, metric and 1500×850 enlarged states were inspected.
Empty headers now synchronize against actual hidden-row geometry instead of
retaining widths from previous content. The extracted wheel exercises edit/review,
Save/reopen, Reset/Undo, units and enlarged headers. All 500 reference hashes and
approved dependency lock remain unchanged. Evidence: `f82_validation.json`.

Next: connect this ST component to the integrated main tab, tool/document and
assignment selection, Save/Discard/Cancel, shared status/cards and shoulder camera,
while continuing to suppress unapproved scientific results. Delete/task-data
selection remain disabled until real operations exist. Other F80 parity work
remains planned. Integrated tabs still number two of three; the ST component is
not yet connected. Overall percentage and finish date remain unvalidated after
withdrawal of the former 67% estimate.

## F81 historical checkpoint

The integrated main window now opens at, and allows shrinking back to, the
reference 1550×1015 logical-pixel minimum. The fixed-size lock is removed;
enlargement uses the existing Qt layouts. The central LiFFT/DUET task area and
worker selector expand, side panels retain bounded widths, and bottom actions,
context bar and footer follow the window. No visual redesign was introduced.

The VTK adapter adjusts parallel-camera framing for taller, narrow viewports
without changing pose or relative user zoom. Reset View retains full-body coverage.
DUET sticky headers now observe rebuilt first-row control sizes as well as viewport
sizes: a language change/rebuild during enlargement previously used temporary
640px widget widths and clipped captions. Updates remain deferred/coalesced.

Validation: 652 native tests pass, 96.77% combined coverage; standards, strict mypy
(135 source files), architecture and both builds pass. Native populated, calculated,
translated, pending-invalid, reset, bottom-grid and full-body states were inspected
at 1550×1015, 1920×1200, 1550×1300 and 2100×1300. Captures compose the actual VTK
framebuffer into Qt layout images, as in F78. An independently extracted wheel
passes enlargement/header checks and existing integrated calculation/Save/reopen
workflows. All 500 reference-file hashes and the approved lock remain unchanged.
Evidence: `f81_validation.json`; [resizing behavior and limits](main_window_resize.md).

Next remains original ST controls and integrated selection, followed by the
remaining F80 parity work below. Two of three assessment tabs are connected;
overall percentage and finish date remain unvalidated. Smaller-screen layouts,
Windows/macOS and different DPI acceptance remain final validation work.

## F80 historical checkpoint

DUET is now connected inside the original integrated main window. The two migrated
assessment tabs (LiFFT and DUET) share project ownership, worker/context selection,
Save/Discard/Cancel transitions, result cards, footer and native avatar. No separate
DUET application or redesigned form was introduced. Open can select migrated
LiFFT/DUET documents; the older isolated LiFFT harness remains LiFFT-only.

Tool switching uses the current assignment's current assessment for the requested
kind. Missing data requires explicit creation consent, retains that assignment,
uses the next historical version and marks the new tool document current. Unbound
projects choose existing tool documents or explicitly create blank data. Invalid
pending input and canceled dirty decisions retain the original tab/text. Save
commits DUET input before persistence. Existing worker/context/version operations
route by the active tool rather than silently selecting LiFFT.

DUET Calculate updates typed row results, total/probability cards, completeness,
metrics and the four arm/hand overlays. The reviewed original camera shot frames
that region. Input changes/Reset/invalid results clear obsolete risk. Returning to
LiFFT restores its source, captions and camera; per-tool retained simultaneous
saved overlays remain a later parity task. English/Spanish body/card/footer/status
captions update with the active model; DUET remains dimensionless.
[Connected workflows and remaining limits](duet_integration.md).

Validation: 650 native tests pass (six new integration workflows), 96.76%
combined coverage; lint/format, strict mypy (135 files), architecture and both
builds pass. Native full-window populated/calculated/expanded/Spanish/invalid
switch/reset/bottom-scroll/LiFFT-return states were inspected at 1550×1015.
Actual VTK framebuffers are composed into Qt captures as documented in F78.
The extracted wheel exercises both tabs, project document listing, calculation,
shared cards/native scene, Save/reopen and cleanup. All 500 reference-file hashes
and the approved dependency lock remain unchanged. `f80_validation.json`.

Next: the original ST task controls and integrated selection. Full settings/menu
(including DUET task-count changes), saved-data Delete, task-data selection,
retained multi-tool overlays/camera animation, PLOT/JROT, legacy import and final
copied-project/platform validation remain planned. ST's scientific review gates
and LiFFT's metric gate remain intact. Two of three assessment tabs are connected;
this is not an overall migration percentage. The former 67% estimate remains
withdrawn; no reliable overall percentage or finish date is established.

## F79 historical checkpoint

The original DUET five-column task component and its widget-independent presenter
are migrated. OMNI-Res choices, reference column stretches/minima, sticky headers,
hidden-header and hidden-summary spacing, bottom buttons, processed icons and
expanded popup styling are preserved. Native comparison gives matching scroll
area (9,57,962,478) and Calculate button (427,601,544,40) geometry at 980×650.
English/Spanish captions and ratings translate without losing pending text.

Every grid edit parses before one source/undo change. Invalid text stays available
for correction; source remains unchanged. Reset restores scale zero and blank
repetitions as one undo step. Calculate gives explicitly PARTIAL totals for
complete rows beside missing slots, with zero outputs for those slots; strict
assessment evaluation still rejects missing input. Missing source fields stay
None through Save/reopen. Input changes immediately clear obsolete row colors.
DUET is dimensionless: display-unit changes do not convert ratings/counts.
[Component behavior and integration boundary](duet_task_panel.md).

Validation: 644 native tests pass (six new focused workflows), 96.85% combined
coverage; lint/format, strict mypy (135 files), architecture and both builds pass.
Original/new, expanded dropdown, empty/populated/calculated/error/Spanish and
narrow bottom-scroll states were inspected. An independently extracted wheel
exercises edit/partial calculation/Save/reopen/Reset/Undo and packaged icons. All
500 reference hashes and the F78 dependency lock remain unchanged.
Evidence: `f79_validation.json`; captures: `artifacts/duet-task-panel/`.

**Integration boundary:** this is an embeddable component, verified with synthetic
projects. The integrated preview's DUET tab remains disabled; no separate permanent
DUET application or UI redesign was added. Shared result cards/avatar, tool/document
switching and worker/context selection for DUET are the next required slice, then
the original ST view. Saved-data Delete and task-data selection remain disabled
until their real operations are connected. Full settings/menu, PLOT/JROT, legacy
import and final copied-project/platform acceptance remain planned. Scientific
review gates, file formats and approved dependencies are unchanged. Overall
percentage and finish date remain unvalidated after withdrawal of 67%.

## F78 historical checkpoint

The approved VTK dependency set is installed only in this new project's environment.
Python, Qt and all 22 previous lock entries retain their exact versions; eleven
approved runtime packages were added and their distributions locked. The integrated
preview now displays the original packaged avatar in its left panel. All eight
actor placements/transformed bounds and all four parallel-camera shots match the
reviewed original methods exactly. Rotate (20°), Zoom (1.15) and Reset View (full
body) are connected. Calculated LiFFT risk colors its back patch; edits, Reset and
unavailable results clear it. Ordinary color updates preserve the user's camera.
The adapter owns native cleanup; canceled window closure keeps it usable.
[Implementation, verification and remaining parity](vtk_body_renderer.md).

Validation: 638 tests pass on the approved native XCB baseline, including six new
VTK regressions; combined coverage 96.91%. Ruff/format, strict mypy (133 source
files), architecture and both builds pass. The documented offscreen run also
passes its 632 tests, skipping the six native OpenGL checks. An existing grid test
now explicitly activates its Qt window before testing keyboard focus; this fixes
a native test setup assumption, without changing application behavior. Native
empty/calculated/rotated/zoomed/full-body-reset/localized/input-reset views were
inspected at 1550×1015; the full-body model, sidebar and bottom controls fit.
Captures combine the actual VTK framebuffer with the Qt layout because direct
Qt/native screen capture is unreliable under this Wayland/XCB compositor.
Independent extracted-wheel rendering/calculation/save/reopen checks and all 500
unchanged reference-file hashes are recorded in `f78_validation.json`.

Next: original DUET and ST views, connecting their existing typed assessment
logic to the shared navigation, results and avatar. Full settings/menu, optional
camera animation, simultaneous retained per-tool overlays, PLOT/JROT, saved
assessment Delete, task-data selection, legacy import, project lifecycle and final
copied-project/native-platform validation remain on the plan. LiFFT metric/TST
scientific review gates remain unchanged. No reliable weighted overall percentage
or finish date replaces the withdrawn 67% estimate.

## F77 historical checkpoint

The integrated preview now has the original three-panel composition: left body
region/legend/view controls, central task tabs/grid and right risk/result cards.
The sidebar includes the animated original Qt gauge, damage scale, cumulative
value, key metrics and status. It receives current typed results directly, without
parsing labels or polling every 300 ms. Input edits/Reset/project transitions clear
obsolete results and stop old animations. Partial calculations retain Incomplete
status and their warning; blocked/absent probabilities show unavailable risk.
[Behavior and remaining renderer work](main_panels.md).

The left panel preserves its original sizes, legend and packaged light view icons.
Its viewport uses the reference QVTK widget's 400×400 preferred size, so the target
layout reserves the original 285-pixel side region. **The actual VTK avatar is not
integrated yet.** The preview says "3D view unavailable" and disables Rotate/Zoom/
Reset View. This is an explicit temporary viewport, not final avatar acceptance.

Validation: 632 tests pass (5 new), 96.86% coverage; Ruff/format, strict typing
(131 source files), architecture and builds pass. Native original/new sidebar
comparison and full empty/complete/partial/Spanish/100-row/scroll/reset states were
inspected at 1550×1015. Side panels, task headers, results and bottom controls fit.
The Spanish unavailable caption is abbreviated with a full tooltip to prevent
collision. Same-target color updates repaint without restarting animation. The
independent wheel exercises connected panels, calculations, persistence, owned
Settings Cancel and packaged icons. All 500 reference hashes and dependency lock
remain unchanged. No dependency/schema/format changes. `f77_validation.json`.

Next: implement the VTK renderer adapter and wire the three view controls after
approval of its exact runtime version/dependencies, then integrate remaining
DUET/ST views. Full settings/menu, PLOT/JROT, saved-assessment Delete, task-data
selection, legacy import, project lifecycle and copied-project final validation
remain on the plan. VTK/model clipping, native platform packaging and complete
main-window parity remain unverified. Overall percentage/finish date remain
unvalidated after withdrawal of 67%.

## F76 historical checkpoint

The original task-count and incomplete-row calculation workflows are connected
in the integrated preview. Settings opens the original owned **Set Number of
Tasks** form (1-100, initial 10). Cancel retains entered text, even invalid pending
text. Set Tasks clears the active grid as the reference does, but now in one
undoable edit; prior source units and values return on Undo. This is the task-count
part of Settings, not the complete final settings window.

The original-style task grid calculates complete rows alongside blank slots. With
arm/load but no repetitions it shows moment only; other incomplete rows show zero
outputs. Totals include only complete rows. These results have explicit PARTIAL
status and a localized incomplete-input warning. Blank source values stay None
through Save/reopen. Invalid numeric values and existing metric review gates still
block all outputs. The strict assessment evaluator and input preparation remain
unchanged for non-grid consumers; incomplete previews are not complete results.
[Behavior, reference review and limits](lifft_grid_workflow.md).

Validation: 627 tests pass (6 new), 96.79% coverage; Ruff/format, strict typing
(127 source files), architecture and package builds pass. Native original/new task
forms both measure 183×112 with matching controls; Spanish uses 249×112 without
clipping. Mixed complete/moment-only/blank grids, Spanish results, task count 100,
reset-five state and confirmation were inspected. Independent extracted-wheel
partial calculation/Save/reopen and actual owned task-count Cancel pass.
All 500 reference hashes and the approved lock remain unchanged. No schema,
format or dependency changes. Evidence: `f76_validation.json`.

Next: port the original right results sidebar and left model-panel layout around
the grid, then connect the VTK adapter after exact runtime-version approval.
Remaining DUET/ST views, PLOT/JROT, full settings/menu integration, legacy import,
project lifecycle and final copied-project validation stay on the established
plan. Original saved-assessment Delete and task-data grid dialog remain pending.
Full main-window parity, VTK clipping and Windows/macOS validation are incomplete.
Overall percentage/finish date remain unvalidated after withdrawal of 67%.

## F75 historical checkpoint

The original shared header/toolbar, worker navigation, assessment association bar
and footer now surround the F74 task component in an **integrated preview** at the
reference 1550×1015 size. This ports reviewed widget/layout code, not screenshots.
Launch with `--integrated-preview`; [behavior and limits](main_navigation.md).
New/Open/Save, Workers, Jobs, assessment/context selection, organization editing,
refresh, surname filtering/order and first/previous/next/last are connected.
The existing owned modal dialogs and lifecycle handlers are reused.

Worker selection carries stored IDs, never parses labels. Cancelled dirty
navigation restores the actual assessment's worker label and retains entered
cells; Save persists before switching. Missing saved assessments do not silently
create one or display old data under a new worker. Worker Management updates
navigation labels without rebuilding the task grid. Explicit new projects and
new blank assessments start with the reference default of 15 task rows; opening
existing files does not alter them.

Validation: 621 tests pass (7 new), 96.82% coverage; Ruff/format, strict typing
(126 source files), architecture and package builds pass. Native empty, populated,
calculated, filtered and Spanish/scrolling states were inspected. Shared toolbar
geometry and effective Qt layout margins match the original; the context bar is
compared directly. Spanish "Todos" fits instead of clipping into the English
18-pixel letter button. Isolated-wheel New/edit/Calculate/Save/reopen passes.
All 500 reference hashes and the approved lock remain unchanged.
Evidence: `f75_validation.json`; no dependency/schema/format change.

Five substantial management/selection dialogs remain migrated. This checkpoint
adds the shared integrated shell, not a completed final main window. The original
model/result sidebar, DUET/ST views and PLOT/JROT integration remain incomplete.
Unavailable toolbar actions and tabs are disabled visibly. Menu/settings UI,
original task-data dialog, saved-assessment Delete and configurable task count
remain pending. Task-tab captions still need localization. Current calculation
requires valid complete rows; original blank/partial-row behavior needs migration.
Metric scientific-review gates are unchanged; the units backend remains preserved.

Next: finish the original task-count/settings and blank/partial-row calculation
workflow, then the original result/model area and remaining tool views. VTK runtime
requires exact-version approval before installation. Legacy import, full project
lifecycle and final copied-project validation remain on the established plan.
Overall percentage and finish date remain unvalidated following withdrawal of 67%.

## F74 historical checkpoint

The reviewed original `setupLiFFTTab` controls now exist as `LifftTaskPanel`:
seven-column editable task grid, sticky header, derived moment/damage/shares,
aligned totals and original Reset/Delete/grid/Calculate button arrangement.
The original main-window stylesheet is a shared desktop theme. This component
runs inside the existing temporary harness with `--original-lifft-controls`; the
old single-field Apply/Discard editor and duplicate result card are hidden in this
mode. It is designed for placement in the original integrated main layout, not a
new standalone final LiFFT UI. [Launch, behavior and limits](lifft_task_panel.md).

Calculate/Save/navigation parse the entire entered grid before one atomic,
undoable input change. Invalid text leaves all cells and source intact. Reset
clears inputs in one undo step, including invalid pending text. Unchanged projected
values retain exact recorded quantities. Moment-result labels use recorded units;
body/force units remain separate. English/Spanish task controls are available.
Returning from cancelled Close retains a usable editor. Old rows hide immediately
when a project clears, before Qt's deferred deletion.

Validation: 614 tests pass (7 new), 96.79% coverage; Ruff/format, strict typing
(124 source files), architecture and package builds pass. Actual edit/calculate/
save/reopen, atomic rejection, Reset/undo, projected units/decimals, Close retry,
focused-row removal and cleared-grid painting pass. Native original/new component
captures are inspected at 900×480, including populated/calculated/empty/scrolling
states; both 960×680 harness languages are inspected. Summary and bottom-button
geometry match the reference at the comparison size. Header scrolling corrects
the original vertical-scrollbar width mismatch. Isolated-wheel grid workflow
passes; 500 reference hashes and dependency lock remain unchanged.
Evidence: `f74_validation.json`. No format/schema/dependency change in this slice.

Five substantial management/selection dialogs remain migrated. This slice adds a
usable assessment component, not another completed full application window.
Saved-assessment Delete and original task-data grid dialog remain incomplete;
metric scientific-review gates and incomplete-row policy are unchanged.

Next: port the original shared main-window context/navigation and assessment
container around this task panel, then its result sidebar/model panel and remaining
DUET/ST views. VTK runtime dependency requires exact-version approval before its
adapter is installed; no dependency change is made here. PLOT/JROT, legacy import,
full project lifecycle and final copied-project validation remain on the plan.
Overall percentage and finish date remain unvalidated following withdrawal of 67%.

## F73 historical checkpoint

The original Organization Management form now creates and edits plants, sections,
lines, stations and independent shifts from the assessment preview. Optional
operational fields persist. New preview projects start at the already-supported
format seven, enabling the complete synthetic UI workflow: create workplace and
shift → create/place job → create/assign worker → create its LiFFT assessment.
Worker Management and assessment selection from F72 remain integrated.
[Behavior, storage compatibility and limits](organization_management.md).

Validation: 607 tests pass (4 new), 96.82% coverage; Ruff/format, strict typing
(122 source files), architecture and package builds pass. Real SQLite failed
write/retry, cancel, duplicate identifiers, persistence and referenced-location
protection pass. Original/new native collapsed, expanded and scrolled-bottom
Plant captures match byte-for-byte on the same Qt/host. Empty, selected Station,
Shift and Spanish states and both minimum-size preview languages were inspected.
Isolated-wheel organization modal/create/save/reopen passes; all 500 reference
file hashes and dependency lock remain unchanged. Evidence: `f73_validation.json`.

Visible form milestone: five substantial migrated dialogs (Organization
Management, Job Management, Workplace Assignments, Assessment Context Selection,
Worker Management), plus the temporary LiFFT preview and nested pickers. This is
partial application integration, not five complete assessment modules.

Hierarchy payload writes version 3 and reads 1/2/3; SQL schema unchanged. Earlier
migration builds cannot read newly saved version-three catalogs. Referenced
locations/shifts are protected rather than reproducing all original deletion
cascades; legacy import and PLOT geometry remain pending.

Next: port the original LiFFT assessment screen and main-window context/navigation
using reviewed reference UI code and the existing tested services. Continue with
remaining DUET/ST assessment UI, then PLOT/JROT, original project lifecycle/import
and final copied-project integration/visual parity. Overall percentage and finish
date remain unvalidated after withdrawing the misleading 67% estimate.

## F72 historical checkpoint

The original visible Worker Management form now opens from the assessment
preview: create/edit details, filter/page/navigate workers, classify assignments,
and add a Job assignment through the original placement picker. Save commits
worker details and classifications together; Close can activate the exact added
assignment's LiFFT assessment, with an explicit prompt before creating a missing
one. Metric/imperial body quantities have explicit canonical units; English and
Spanish controls are available. [Behavior and limits](worker_management.md).

Validation: 603 tests pass (9 new), 97.34% coverage; standards, strict typing,
architecture and builds pass. Actual SQLite rollback/retry and both creation
choices pass. Original/new native minimum-size forms and expanded/selected states
inspected; isolated-wheel worker save/reopen passes. Reference files and lock
unchanged. Hierarchy payload writes version 2 and reads 1/2; SQL schema unchanged.
Evidence: `f72_validation.json`.

Visible form milestone: four substantial migrated dialogs (Job Management,
Workplace Assignments, Assessment Context Selection, Worker Management), plus the
temporary LiFFT preview and nested selection dialogs. This is not full final UI
parity. Worker deletion currently refuses saved assignments; hidden anthropometry,
legacy import and final assessment/main-window integration remain pending.

Next: original organization/workplace editing so a new project can create its
plants/sections/lines/stations/shifts and complete the worker → job → assessment
workflow from the UI. Follow with original assessment screens and integrated
navigation. PLOT/JROT and final copied-project validation remain on the plan.
Overall percentage and finish date remain unvalidated after withdrawing 67%.

## F71 historical checkpoint

Job Management opens from the existing LiFFT assessment preview for format-seven
projects. Its modal retains the last stored job selection for the same project
location during this window session. Assessment edits, input binding and undo
history remain intact; returning does not rebuild the assessment screen. Save
now renders its selected profile once instead of briefly loading the current
approved profile before a selected draft.

Validation: 594 tests pass, 98.06% coverage; Ruff/format, strict typing,
architecture and package builds pass. Isolated-wheel modal/save/reopen workflows
pass. Native minimum-size English/Spanish preview and approved/draft management
states inspected. All 500 reference file hashes and dependency lock unchanged.
See `f71_validation.json` and the integration section of `job_management_preview.md`.

This connects existing forms; it adds no new completed form and is not the final
original main window. Next: migrate the original worker-management form and wire
its worker/assignment selection into the existing assessment-context flow.
Original-project import, complete assessment screens, PLOT/JROT and final main
navigation remain pending. Overall percentage and finish date remain unvalidated
following withdrawal of the former 67% estimate.

## F70 historical checkpoint

Job Management now has shared English/Spanish form messages, tooltips, statuses,
placeholders and localized modal/search buttons. The preview honors saved language
or temporary `--job-language en|es`, without rewriting stored evidence or units.
[Launch and language behavior](job_management_language.md).

Validation: 591 tests pass (4 added), 98.05% coverage; standards/type/architecture,
package builds and isolated-wheel bilingual workflows/reopen pass. Spanish forms,
popups/date picker and nested dialogs inspected at the original minimum size.
Four English captures match F69 byte-for-byte. Original files/dependency lock
unchanged; no schema/scientific change. `f70_validation.json`.

Next: remaining Job Management integration details (selection state and final
application navigation), then the next integrated worker/project/assessment
workflow. Original-project import and JROT reference restrictions remain pending.
Overall completion percentage remains unvalidated after withdrawing 67%; no
reliable whole-application finish date is established.

## F69 historical checkpoint

Job Management Delete is enabled with the original confirmation, atomic removal
of job-owned profiles/placements, and retained worker assignments. Existing
assessment-history rules refuse deletion when an assessment records that job
classification. Cancel/failure preserve the form; success selects a survivor or
clears the last-job form. [Behavior and intentional difference](job_deletion.md).

Validation: 587 tests pass (7 added and last-job UI coverage extended), full
standards/type/architecture/build checks and isolated-wheel modal deletion/reopen
pass. Native confirmation, protected-history message and post-deletion layout
inspected. Original Python 3.10 in-memory DDL checks record baseline cascades and
rotation restrictions. Reference files/dependency lock unchanged; no schema or
scientific change. See `f69_validation.json`.

Next: full Job Management form translation and remaining parity details, then
final main-window integration. JROT reference restrictions must be integrated
before rotation records/import are supported. Overall percentage remains
unvalidated after withdrawing the prior 67% estimate; no reliable finish date yet.

## F68 historical checkpoint

The original-layout Job Management window is now runnable: job creation/editing,
selection/search/navigation, profile versioning/approval/currentness/retirement,
and nested workplace assignment use the migrated operations. Native dropdown
selection contrast is corrected using the existing palette.
[Launch instructions, behavior and limits](job_management_preview.md).

Run `.venv/bin/python -m ergotools.bootstrap --job-management-demo` from this root
for a separate persistent synthetic demo. No original project is imported or
modified. Delete remains explicitly disabled; full form translation and final
main-window integration remain unfinished. This is partial functional parity.

Validation: 580 tests pass (6 integrated cases added), 98.40% coverage;
Ruff/format, strict mypy, architecture, builds and isolated-wheel modal workflow/
reopen pass. Native original/new minimum-size layouts and important states
inspected. Baseline 500 reference files and dependency lock unchanged;
`f68_validation.json`. No schema, dependency or scientific formula change.

Next: complete Job Management deletion semantics, full form localization and its
remaining parity gaps, then connect it into the integrated application workflow.
Overall completion percentage remains unvalidated after withdrawing 67%; no
reliable overall finish date has been established.

## F67 historical checkpoint

Extracted the original measurement table into a typed Qt component with preserved
layout/style and English/Spanish messages. Profile loading retains saved results;
user edits update probability once. Invalid/cleared damage removes old results.
Approve now saves edited evidence and approves in one transaction, matching the
original control. [Behavior, differences and limits](job_risk_table.md).

Validation: 574 tests pass (8 added), 98.89% coverage; Ruff/format, strict mypy,
architecture, builds, isolated-wheel Qt/edit/approve/reopen checks pass. Native
XCB component states inspected against original table construction/style.
All 500 baseline reference files and dependency lock unchanged. No schema change.

The full Job Management window remains unfinished and the component is not yet
exposed by the launch harness. Next: original evidence controls/navigation and
integration of this table, profile actions, saves and workplace editor. No new
generic synchronization layers are planned. Overall completion remains unquantified
following withdrawal of the former unreliable 67% estimate; no finish date yet.

## F66 historical checkpoint

Implemented the original Job Management Save branches as one transaction:
job fields plus draft evidence, metadata-only changes with immutable approved/
retired evidence, and initial job/profile creation with complete measurements.
The operation is available through the project adapter and workspace; it leaves
assessment edits untouched. [Behavior and limits](job_management_save.md).

Validation: 566 tests pass (7 added), 98.89% coverage; Ruff/format, strict mypy,
architecture, builds and isolated-wheel create/reopen pass. Baseline reference
500 files and dependency lock unchanged; `f66_validation.json`.
No UI or schema change. The original screen is still not connected.

Next milestone: a working migrated original Job Management screen using these
operations and the existing workplace dialog. Complete only the supporting
operations required by those controls; do not expand generic defensive layers.
Preserve the original modal, single-user workflow. Then complete integrated
assessment/worker/project workflows, PLOT, JROT and final acceptance.

## F65 historical checkpoint

Connected risk-profile operations to workspace-owned snapshot authority and an
optional repository port. Refresh/project lifetime/job writes invalidate old
callbacks; successful operations issue fresh views. Assessment edits, revision
and recent-project preferences remain untouched.
[Workspace contract and limits](workspace_job_risk.md).

Validation: 559 tests pass (9 new cases); coverage 99.00%. Ruff/format, strict mypy
(108 source files), architecture, builds and isolated-wheel workspace workflow/
reopen pass. All 500 original files and dependency lock unchanged;
f65_validation.json. No schema, UI or scientific formula change.

Next: Job Management presenters for selected-job/profile actions and view state,
then original screen controls and localization integration. Workspace risk
operations now work; the complete management screen remains unfinished.
Overall estimated progress remains approximately 67%.
No reliable overall finish date is established.

## F64 historical checkpoint

Integrated risk storage into explicit version-seven projects, including capability
checks, open validation and all profile lifecycle operations. Job writes now
protect both historical assessment links and profile parent jobs. Existing
formats/default factories remain unchanged. [Format and limits](risk_project_format.md).

Validation: 550 tests pass (15 new cases); coverage 99.02%. Ruff/format, strict mypy
(107 source files), architecture, builds and isolated-wheel version-seven lifecycle/
reference protection pass. Original 500 files and dependency lock unchanged;
f64_validation.json. No UI or scientific formula change.

Next: workspace-owned risk snapshots/operation ports and Job Management presenters,
then existing screen wiring. The project adapter now persists risk profiles;
the workspace and final screen do not yet expose them. No automatic upgrade or
legacy import is included. Overall estimated progress remains approximately 67%.
No reliable overall finish date is established.

## F63 historical checkpoint

Added transactional risk-profile storage with explicit draft/lifecycle operations,
expected-catalog conflict checks, parent-job validation and post-write verification.
Failures restore prior evidence/currentness; approved/retired edits are rejected.
[Storage contract and integration limits](job_risk_persistence.md).

Validation: 535 tests pass (10 new cases); coverage 99.03%, store 100%. Ruff/format,
strict mypy (107 source files), architecture, builds and isolated-wheel lifecycle/
reopen pass. All 500 original files and dependency lock unchanged; f63_validation.json.
New isolated risk tables were added; existing project formats remain unchanged.
No UI or scientific formula change.

Next: explicit project-format integration and protection against removing referenced
jobs, then workspace/presenter and original screen wiring. The store is tested
against synthetic databases; AssessmentProjectFile does not yet expose it.
Overall estimated progress: approximately 67%, a qualitative scope estimate.
No reliable overall finish date is established.

## F62 historical checkpoint

Added blank/copied risk-profile drafts and guarded draft editing. Version allocation,
provenance reset and evidence normalization match original-code records. Approved/
retired edits, stale drafts and ownership/lifecycle tampering are rejected.
[Behavior and limits](job_risk_drafts.md).

Validation: 525 tests pass (5 new cases); coverage 99.01%, risk domain 100%.
Ruff/format, strict mypy (106 source files), architecture, builds and isolated-wheel
copy/edit/approval protection pass. Original 500 files and dependency lock unchanged;
f62_validation.json. No UI, schema or scientific formula change.

Next: transactional risk-profile persistence enforcing membership, conflicts and
approved-evidence protection, then workspace/presenter and original screen wiring.
These are tested domain operations; durable profiles and complete Job Management
remain unfinished. Overall estimated progress remains approximately 66%.
No reliable overall finish date is established.

## F61 historical checkpoint

Added typed job risk measurements/provenance and pure approval/current/retirement
rules, distinct from worker assessment history. Ten original-code scenarios
verify lifecycle behavior; evidence and unit labels remain unchanged.
[Contracts and remaining work](job_risk_lifecycle.md).

Validation: 520 tests pass (10 new cases); coverage 99.00%, new domain module 100%.
Ruff/format, strict mypy (106 source files), architecture, builds and isolated-wheel
lifecycle smoke pass. All 500 reference files and dependency lock unchanged;
f61_validation.json. No UI, schema or scientific formula change.

Next: profile draft creation/copy/edit rules and transactional persistence, then
workspace/presenter and original Job Management control wiring. The lifecycle
model is complete for this scope; profile persistence and full screen migration
are not complete. Overall estimated progress remains approximately 66%.
No reliable overall finish date is established.

## F60 historical checkpoint

Localized the workplace dialog in English/Spanish using the shared catalog;
identifiers and source units remain untouched. Added an explicit modal host
returning saved view/shift, with reentry protection and cleanup on all exits.
Save errors now use localized recovery text and type-only logging.
[Contracts and limits](job_workplace_localization.md).

Validation: 510 tests pass (4 new cases); coverage 98.98%. Ruff/format, strict mypy
(105 source files), architecture, builds and isolated-wheel Spanish host Save/Cancel
pass. Spanish minimum-size populated/empty/filter states and both-language errors
visually inspected. English collapsed/expanded/minimum captures unchanged from F59.
Original 500 files and dependency lock unchanged; f60_validation.json.

Next: owning Job Management record/profile workflows and original screen wiring.
The localized dialog and host are ready components; the final management screen
and menu route remain incomplete. No schema, dependency or scientific changes.
Overall estimated progress remains approximately 66%; no reliable finish date yet.

## F59 historical checkpoint

Migrated the original Job workplace dialog layout onto the tested presenter.
Shift selections, hierarchy checkboxes, filtering, Clear/Save/Cancel and saved
historical ownership are preserved. Signal-blocked rendering avoids checkbox
event cascades; Save guards nested modal reentry. [Contract and visual evidence](job_workplace_dialog.md).

Validation: 506 tests pass (6 new Qt cases); coverage 98.97%, dialog 99.11%.
Ruff/format, strict mypy (104 source files), architecture, builds and isolated-wheel
button save/reopen pass. Native original-source/migrated comparisons and empty,
expanded/selected, filtered, minimum-size and warning states inspected. Original
500 files and dependency lock unchanged; f59_validation.json. No schema change.

This is a migrated dialog component, not a finished Job Management screen or new
main-window route. Reference English labels remain; localization and host
lifecycle integration are next. Full risk/profile and worker management, project
setup navigation, integrated assessments, PLOT/JROT and final acceptance remain.
Overall estimated progress: approximately 66%, a rough scope estimate.
No reliable overall finish date is established.

## F58 historical checkpoint

Extracted Job Management's workplace-selection operation and connected it to
guarded workspace persistence through a UI-independent presenter. Deselection
deactivates placements; reselection restores the highest-ID inactive placement,
retaining metadata and assessment ownership. [Contracts and reference evidence](job_workplace_management.md).

Validation: 500 tests pass (8 new cases, including four captured reference
transitions); coverage 98.96%, both new modules 100%. Ruff/format, strict mypy
(103 source files), architecture, builds and isolated-wheel saves pass.
Original 500 files and dependency lock unchanged; f58_validation.json.
No UI, schema, dependency or scientific formula change.

Next: migrate the existing JobWorkplaceDialog onto this presenter and verify
native visual/interaction parity. This is a completed non-visual management
operation, not a finished management screen. Full worker records, integrated
assessments, PLOT/JROT and release acceptance remain incomplete.
Overall estimated progress remains approximately 66%; this is a rough scope
estimate, not a measured completion fraction. No reliable finish date yet.
Include the percentage, completed work and next milestone in every checkpoint
response, as the owner reiterated after F57.

## F57 historical checkpoint

Added validated historical project initialization: explicit hierarchy, worker/job
relationships and first assessment, using existing stores and workspace creation.
Checks ownership/model inputs before filesystem writes, protects existing paths,
and removes incomplete new files on setup failure. Recorded source units remain
independent of project defaults. [Contracts and limitations](historical_project_setup.md).

Validation: 492 tests pass (16 new cases); combined coverage 98.95%. Ruff/format,
strict mypy (101 source files), architecture, builds and isolated-wheel setup/reopen
pass. All 500 reference files and dependency lock unchanged; f57_validation.json.
No UI, schema, dependency or scientific formula change.

This completes a storage/workspace setup operation, not the setup screen. Default
New remains unchanged; full worker records and migrated worker/job/setup UI remain
next, followed by complete integrated assessments, PLOT/JROT and final acceptance.
The prior 66% remains only a rough historical scope estimate and is not a measured
fraction or reliable schedule. Workflow completion is the primary progress report;
no reliable overall finish date is established.

Owner clarification after F56: continue the accepted stages and test requirements.
Temporary harnesses remain allowed. Final UI migration starts from existing UI
code, with screenshots used for validation. Mobile UI and VTK replacement remain
future architectural possibilities, not current implementation scope. Both unit
systems remain mandatory; scientific conversion questions stay explicit gates.

## F56 historical checkpoint

Added New assessment to the temporary LiFFT window: choose an existing worker/job
assignment and create an empty current version 1. Reuses the styled context chooser,
dirty decisions and transactional creation; duplicate ownership is rejected.
Added a hierarchy freshness check after the modal dirty decision for both selection
and creation. [Behavior, evidence and limits](window_first_assessment.md).

Validation: 476 tests pass (2 new desktop scenarios); coverage 98.94%.
Ruff/format, strict mypy (101 source files), architecture and builds pass.
Isolated-wheel window creation/reopen passes. Native empty/populated/pending,
Spanish minimum layout, worker/expanded assignment chooser and created editor
inspected without clipping. All 500 original files and dependency lock unchanged;
evidence in f56_validation.json. No schema or scientific formula change.

Next: historical project setup and complete worker/job record workflows, then
integrated model UI. This action needs an open historical project and existing
assignments; it does not create workers/jobs or upgrade default projects.
Overall remains approximately 66%; no reliable overall finish date is established.

## F55 historical checkpoint

Added New blank version in the temporary LiFFT window, with explicit confirmation,
existing dirty-source decisions, fresh history/source checks and atomic creation.
New drafts are empty and noncurrent; previous current versions remain unchanged.
[Creation behavior and limits](window_blank_version.md).

Validation: 474 tests pass (3 new desktop scenarios); coverage 98.92%. Ruff/format,
strict mypy (101 files), architecture, builds and isolated-wheel blank creation/
reopen pass. Native empty/pending/blank, Spanish minimum layout, confirmation and
dirty-choice states inspected without clipping. Original 500 files and dependency
lock unchanged; evidence in `f55_validation.json`. No schema change.

Next: first-assessment/project setup and complete worker/job workflows, then
integrated model UI. This action needs an existing historical assignment link;
it does not create workers/jobs or upgrade default projects. Overall remains about
66%; PLOT/JROT, legacy import, scientific gates and release acceptance remain.
A reliable overall finish date is not established.

## F54 historical checkpoint

Connected current-version management to the temporary LiFFT window. A styled
version picker changes currentness while the editor stays open; visible version/
currentness labels distinguish noncurrent sources without saving their edits.
[Window contract and visual evidence](window_current_version.md).

Validation: 471 tests pass (2 new desktop scenarios); coverage 98.93%. Ruff/format,
strict mypy (101 files), architecture, builds and isolated-wheel version action
pass. Native empty/current/pending/noncurrent-dirty, Spanish minimum layout and
picker/popup states inspected without clipping. Original 500 files and dependency
lock unchanged; evidence in `f54_validation.json`. No schema change.

Next: historical version creation controls and complete worker/job workflows,
then integrated model UI. Overall approximately 66%; PLOT/JROT, legacy import,
scientific gates and release acceptance remain. The window is still a temporary
LiFFT harness. A reliable overall finish date is not established.

## F53 historical checkpoint

Added workspace-owned history snapshots and guarded current-version changes.
Refresh/project lifetime/creation invalidates old authority; successful changes
preserve active source, dirty state and undo history.
[Management contract](workspace_history_management.md).

Validation: 469 tests pass (3 new integration scenarios); coverage 98.92%,
history access/workspace 100%. Ruff/format, strict mypy (101 files), architecture,
builds and isolated-wheel history authority/current-version checks pass.
Original 500 files and dependency lock unchanged; evidence in `f53_validation.json`.
No schema or UI change.

Next: version-management and creation controls using these workspace safeguards,
then complete worker/job workflows and integrated model UI. Overall remains
approximately 65%; PLOT/JROT, import, scientific gates and release acceptance
remain. A reliable overall finish date is not established.

## F52 historical checkpoint

Added explicit atomic current-version selection within an assignment/model group.
Statuses, source data and other groups remain unchanged; expected-history comparison
and rollback protect conflicting or failed updates.
[Lifecycle contract and reference scope](assessment_current_version.md).

Validation: 466 tests pass (3 new integration cases); coverage 98.91%, history domain
100%. Ruff/format, strict mypy (101 files), architecture, builds and isolated-wheel
current selection/conflict/reopen pass. Original 500 files and dependency lock
unchanged; evidence in `f52_validation.json`. No schema or UI change.

Next: workspace-owned history snapshots and current-version/creation controls, then
complete worker/job workflows and integrated model UI. This checkpoint adds a
repository capability only. Overall remains approximately 65%; PLOT/JROT, import,
scientific gates and release acceptance remain. A reliable overall finish date
is not established.

## F51 historical checkpoint

Connected the assignment host to an Assessment context action in the temporary
LiFFT window. Historical projects can select a worker and saved LiFFT assignment,
with existing pending-text/dirty safeguards and editor rebinding.
[Window behavior and limits](window_assignment_context.md).

Validation: 463 tests pass (2 new desktop scenarios); coverage 98.94%. Ruff/format,
strict mypy (101 files), architecture, builds and isolated-wheel window action
pass. Native empty/populated/pending/Spanish/minimum-size and modal states inspected
without visible clipping. Original 500 files and dependency lock unchanged;
evidence in `f51_validation.json`. No schema or dependency change.

Next: historical assessment current-version lifecycle and creation controls, then
complete worker/job workflows and integrated model UI. The new action is LiFFT-only
and requires version-six data prepared through repository APIs; default projects
are not upgraded. Overall approximately 65%; PLOT/JROT, legacy import, scientific
gates and release acceptance remain. A reliable overall finish date is not established.

## F50 historical checkpoint

Added the reusable Qt host flow: pending-text resolution, modal assignment dialog,
dirty decision and workspace selection with cleanup/reentrancy guards.
[Host contract and visual evidence](assignment_dialog_host.md).

Validation: 461 tests pass (3 new Qt integration cases); coverage 98.98%, host 100%.
Ruff/format, strict mypy (101 files), architecture, builds and isolated-wheel real
modal selection pass. Five native 700 x 540 states inspected and match F49 images.
Original 500 files and dependency lock unchanged; evidence in `f50_validation.json`.
No schema or scientific change.

Next: concrete main-window/editor callback wiring and current-version lifecycle.
The reusable host executes the complete modal selection sequence but is not yet
invoked by a main-window action. Overall remains approximately 64%; full
worker/job UI, PLOT/JROT, import, scientific gates and release acceptance remain.
A reliable overall finish date is not established.

## F49 historical checkpoint

Adapted the styled context dialog to the assignment-aware presenter. Historical
mode derives options from saved job snapshots and returns exact assignment requests;
older context mode remains supported. [Contracts and visual evidence](assignment_context_dialog.md).

Validation: 458 tests pass (3 new real-Qt cases); coverage 98.97%, dialog 100%.
Ruff/format, strict mypy (100 files), architecture, builds and isolated-wheel
historical dialog acceptance/selection pass. Native 700 x 540 selected, collapsed,
empty, stale and popup states visually inspected. Original 500 files and dependency
lock unchanged; evidence in `f49_validation.json`. No schema change.

Next: host pending-text/dirty-choice composition and current-version lifecycle.
The reusable dialog is adapted; it is not yet wired into the temporary harness
or final main window. Overall approximately 64%; full worker/job UI, PLOT/JROT,
import, scientific gates and release acceptance remain. A reliable overall finish
date is not established.

## F48 historical checkpoint

Added a widget-independent assignment selector over saved job snapshots and the
historical workspace APIs. Exact assignment choices, snapshot/request identities
and active-source revision checks guard selection and creation.
[Presenter contract](assignment_selection_presenter.md).

Validation: 455 tests pass (4 new integration scenarios); coverage 98.97%,
new presenter 100%. Ruff/format, strict mypy (100 files), architecture, builds and
isolated-wheel presenter selection/creation pass. Original 500 files and dependency
lock unchanged; evidence in `f48_validation.json`. No schema or UI change.

Next: adapt the classified-context dialog to assignment-aware requests, then host
pending-text/dirty-choice integration with native visual inspection. Current-version
transitions remain separate lifecycle work. Overall remains approximately 63%;
final worker/job UI, PLOT/JROT, import, scientific gates and release acceptance
remain. A reliable overall finish date is not established.

## F47 historical checkpoint

Added workspace creation of assignment-linked assessments with non-mutating
preflight before any requested save of the old source. Final creation retains
atomic source/ownership checks and activates only after commit.
[Creation workflow contract](workspace_history_creation.md).

Validation: 451 tests pass (3 new integration scenarios covering multiple paths);
coverage 98.95%, workspace 100%. Ruff/format, strict mypy (99 files), architecture,
builds and isolated-wheel creation/reopen pass. Original 500 files and dependency
lock unchanged; evidence in `f47_validation.json`. No schema or UI change.

Next: assignment-aware presenter state and current-version lifecycle, then
context-dialog host integration with pending-text handling. These workspace
capabilities are not yet desktop controls. Overall remains approximately 63%;
complete worker/job UI, PLOT/JROT, import, scientific gates and release acceptance
remain. A reliable overall finish date is not established.

## F46 historical checkpoint

Added assignment-aware workspace selection over persisted historical ownership.
Exact assignment/model lookup opens closed or successor assessments independently
and preserves existing dirty-choice/failure safeguards.
[Workflow contract](workspace_history_selection.md).

Validation: 448 tests pass (2 new integration scenarios covering multiple paths);
coverage 98.94%, history access/workspace modules 100%. Ruff/format, strict mypy
(99 files), architecture, builds and isolated-wheel historical/successor selection
pass. Original 500 files and dependency lock unchanged; evidence in
`f46_validation.json`. No schema or UI change.

Next: assignment-aware presenter snapshots and creation/current-version lifecycle,
then context-dialog host integration with pending-text handling. The workspace
capability is implemented; the UI is not connected yet. Overall remains about 63%;
full worker/job UI, PLOT/JROT, import, scientific gates and release acceptance
remain. A reliable overall finish date is not established.

## F45 historical checkpoint

Completed the historical ownership storage slice of worker/job migration. Explicit
version-six projects atomically create assessment sources and assignment links;
job replacement protects referenced assignment/placement identities.
[Persistence contract and integration limits](assessment_history_persistence.md).

Validation: 446 tests pass (11 new); coverage 98.93%, new storage module 97.18%.
Ruff/format, strict mypy (98 files), architecture, builds and isolated-wheel
historical save/reopen/protection pass. Original 500 files and dependency lock
unchanged; evidence in `f45_validation.json`. No automatic format upgrade or UI change.

Next: assignment-aware workspace/selection capabilities and current-version
transitions, followed by host integration with pending-text/dirty-choice handling.
Version six deliberately rejects the old context-only binding API; it is not yet
wired into the desktop harness. Overall approximately 63%; full worker/job UI,
PLOT/JROT, legacy import, scientific review and release acceptance remain.
A reliable overall finish date is not established.

## F44 historical checkpoint

Added typed assignment-scoped assessment history with explicit versions, statuses
and currentness. Exact assignment/model lookup keeps prior assessments on closed
rows after reassignment. [Ownership contract](assessment_history_ownership.md).

Validation: 435 tests pass (4 new, including nine actual reference SQL cases);
coverage 98.94%, new module 100%. Ruff/format, strict mypy (97 files), architecture,
builds and isolated-wheel ownership checks pass. All 500 original files and
dependency lock unchanged; evidence in `f44_validation.json`. No schema or UI change.

Next: persist historical links with source/model validation, atomic creation and
protection against deleting or repurposing referenced assignments. Existing context
bindings remain unchanged. Then integrate persisted selection and dirty-choice
handling. Overall remains approximately 62%; final UI/PLOT/JROT/import/scientific
and release acceptance remain. No reliable finish date is established.

## F43 historical checkpoint

Added batch classification changes and removal, preserving prior rows and exact
reference notes/date behavior. Typed requests prepare one complete replacement;
late failures cannot publish partial changes. [Batch contract](job_classification_batches.md).

Validation: 431 tests pass (5 new, including six actual reference cases); total
coverage 98.92%, new module 100%. Ruff/format, strict mypy (96 files), architecture,
builds and isolated-wheel removal/reopen pass. All 500 original files and dependency
lock unchanged; evidence in `f43_validation.json`. No schema or UI change.

Next: historical assessment ownership and persisted context selection integration,
including host pending-text/dirty-choice handling. Full editing, main UI, PLOT/JROT,
legacy import, scientific gates and release acceptance remain. Overall remains
approximately 62%; no reliable finish date is established.

## F42 historical checkpoint

Added pure single-worker placement assignment transitions: unchanged selection,
in-place classification and closing/replacing classified assignments. Explicit date
and identity inputs support deterministic validation; guarded workspace persistence
commits the result. [Behavior and limitations](job_assignment_transitions.md).

Validation: 426 tests pass (4 new, including five actual reference cases); total
coverage 98.90%, new module 100%. Ruff/format, strict mypy (95 files), architecture,
builds and isolated-wheel transition/reopen pass. All 500 original files and
dependency lock unchanged; evidence in `f42_validation.json`.

Next: batch classification/removal semantics and historical assessment ownership,
then persisted context selection with pending-text/dirty-choice handling. UI,
full worker/job editing, PLOT/JROT, import, scientific gates and release acceptance
remain. Overall approximately 62%; no reliable finish date is established.

## F41 historical checkpoint

Added workspace-owned job snapshots and atomic expected-value replacement.
Stale/foreign callbacks and externally changed saved data cannot overwrite newer
records. Job commits preserve active assessment edits, undo history and settings.
[Editing contract and limitations](workspace_jobs.md).

Validation: 422 tests pass (10 new); combined coverage 98.89%. Ruff/format, strict
mypy (94 files), architecture and builds pass. Workspace/job port/storage coverage
is 100%. Extracted-wheel conflict handling, original 500 files and dependency lock
verified in `f41_validation.json`. No schema or UI change.

Next: reference-compatible assignment-history commands, then integrate persisted
job selection with the context dialog and host pending-text/dirty-choice flow.
Full job editing, historical assessment links, main UI, PLOT/JROT, import,
scientific gates and release acceptance remain. Overall estimate remains 61%;
this checkpoint strengthens editing safety rather than adding visible workflow
parity. A reliable finish date is not established.

## F40 historical checkpoint

Added explicit version-five job, placement and worker-assignment persistence,
with ordered immutable records, reference overlap rules, cross-hierarchy integrity
and atomic rollback. Classified chooser options now derive from saved records;
the Qt component and temporary harness behavior are unchanged.
[Contracts and limits](job_catalog_persistence.md).

Validation: 412 tests pass (11 new), combined coverage 98.87%. Ruff/format, strict
mypy (93 files), architecture and builds pass. Concurrent WAL reads retain one
snapshot. Extracted-wheel workflows, all 500 reference files and the unchanged
dependency lock verified in `f40_validation.json`. Existing project formats are
not upgraded; version five is explicit opt-in.

Next: workspace-owned job snapshots/conflict handling, assignment lifecycle and
dialog integration with pending-text/dirty-choice handling. Historical assessment
links, full worker/job editing, main UI, PLOT/JROT, import, scientific gates and
release acceptance remain. Overall approximately 61%; no reliable finish date is
established yet.

## F39 historical checkpoint

Added a reusable Qt classified-assignment chooser matching the active reference dialog, rather than hidden legacy inline controls. Shift filtering, leaf-only acceptance, current-context expansion, cancellation and stale-catalog rejection use injected records and the existing presenter. [Scope and native visual evidence](assessment_context_dialog.md). The component is not yet wired into the temporary harness.

Validation: 401 tests pass, including five real Qt cases; combined coverage 98.85%, new module 100%. Ruff/format, strict mypy (90 files), architecture and builds pass. Native 700 x 540 selected/collapsed/empty/stale/popup states inspected; fixed type-label clipping and selection gutter color. Package/reference/lock/image evidence: `f39_validation.json`. No dependency or schema change; original files unchanged.

Next: persist classified job/placement/worker-assignment records, then wire the dialog into integrated selection with pending-text and dirty-choice handling. Overall completion approximately 60%; complete worker/job editing, main UI, PLOT/JROT, import, scientific gates and release acceptance remain. No reliable finish date is established yet.

## F38 historical checkpoint

Added a widget-independent assessment selector over real catalog/workspace services. Exact view/request identities and active-source checks reject stale callbacks; explicit membership and model checks precede selection/creation. Cancellation and recoverable failures retain deliberate retry. [Contracts and UI responsibilities](assessment_selection_presenter.md).

Validation: 396 tests pass, including eight new presenter scenarios; combined coverage 98.80%, presenter 100%. Ruff/format, strict mypy (89 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f38_validation.json`. No UI, schema, dependency or scientific change; original files unchanged.

Next: reference-aligned selection controls with pending-text/cancellation handling and visual checks, then complete worker/job record editing. Overall completion remains approximately 59%; no new visible UI parity is claimed for this presenter slice. PLOT/JROT/import/scientific/release acceptance remain; no reliable finish date is established yet.

## F37 historical checkpoint

Added atomic source-plus-binding creation and optional workspace context creation. Failures roll back both new records; occupied identity/context preflight precedes current-save handling, and activation follows commit. Existing unbound creation and older project formats remain unchanged. [Contracts and limits](bound_assessment_creation.md).

Validation: 388 tests pass, including eleven new cases; combined coverage 98.77%, shared draft/binding stores and workspace 100%. Ruff/format, strict mypy (88 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f37_validation.json`. No schema, dependency, default format or UI change; original files unchanged.

Next: reusable catalog selection/creation presentation and editor integration with reference workflows, then complete worker/job records. Overall completion approximately 59%; full UI/PLOT/JROT/import/scientific/release acceptance remain. No reliable completion date is established yet.

## F36 historical checkpoint

Added workspace-owned catalog snapshots and atomic expected-value replacement. Refresh/save/project-lifetime rules reject stale or foreign callbacks, while preserving active assessment edits and history. Conflicts and failed writes leave saved data intact. [Lifecycle contract](workspace_hierarchy.md).

Validation: 377 tests pass, including ten new scenarios; combined coverage 98.76%, new port module and workspace 100%. Ruff/format, strict mypy (88 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f36_validation.json`. No schema, default format, dependency or UI change; original files unchanged.

Next: atomic assessment creation plus context binding, followed by catalog/editor integration. Overall completion remains approximately 58%; UI, complete worker/PLOT/JROT records, import, scientific gates and release acceptance remain. No reliable completion date is established yet.

## F35 historical checkpoint

Added explicit version-four catalog persistence with strict ordered snapshots and transactional protection of assessment bindings. New binding writes validate worker/station/shift membership under the write lock. Existing versions/default creation remain unchanged. [Contracts and limits](hierarchy_persistence.md).

Validation: 367 tests pass, including fourteen new cases; combined coverage 98.73%, new storage module 100%. Ruff/format, strict mypy (87 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f35_validation.json`. Original files and approved dependencies unchanged; no UI change.

Next: workspace catalog access and lifecycle/refresh rules, then combined assessment creation/binding. Catalog editing/history, complete worker/PLOT metadata and selectors remain pending. Overall completion approximately 58%; final integrated UI/PLOT/JROT/import/scientific/release work remains. A reliable completion date is not yet established.

## F34 historical checkpoint

Added explicit plant/section/line identity records around the existing worker/station/shift catalog. Empty parents survive; duplicates and orphan relationships fail before publication. Eleven actual reference query outputs establish child filtering/order behavior on focused fixtures. [Contracts and persistence requirements](work_hierarchy.md).

Validation: 353 tests pass, including sixteen new cases; combined coverage 98.69%, hierarchy module 100%. Ruff/format, strict mypy (86 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f34_validation.json`. No UI, schema or dependency change; original files unchanged.

Next: transactional hierarchy/catalog persistence, including explicit ordering, project isolation and protection of existing assessment bindings. Overall completion remains approximately 57%; hierarchy identities are now complete, but catalog persistence and end-user editing remain pending. Full UI/PLOT/JROT/legacy/scientific/release acceptance remain; no reliable finish date is established.

## F33 historical checkpoint

Added immutable worker/station/shift selection catalogs and reference-compatible worker options with separate stable IDs. Exact membership feeds the existing bound assessment selection; name changes cannot alter ownership. Captured actual reference methods with synthetic data. [Audit and limits](work_catalog.md).

Validation: 337 tests pass, including twelve new cases; combined coverage 98.66%, both new modules 100%. Ruff/format, strict mypy (85 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f33_validation.json`. No UI, schema or dependency change; original files unchanged.

Next: complete hierarchy contracts including empty parents, then catalog persistence with referential constraints and selector integration. Overall completion remains approximately 57%; this reusable selection boundary is not yet a persisted catalog or additional end-user workflow. Final UI/PLOT/JROT/legacy/scientific/release acceptance remain; a reliable finish date is not yet established.

## F32 historical checkpoint

Workspace selection now resolves exact assessment context with Save/Discard/Cancel, target validation before current save and failure retention. Same-document selections preserve history; context changes activate independent clean sessions without touching project connections or recency. [Contracts and limitations](context_selection.md).

Validation: 325 tests pass, including ten additional scenarios; combined coverage 98.63%, workspace module 100%. Ruff/format, strict mypy (83 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f32_validation.json`. No dependency, schema or UI change; original files unchanged.

Next: audit and migrate worker/workplace catalog contracts with small fixtures, then combined create/bind and selection presentation. Overall completion approximately 57%. The full integrated UI, PLOT/JROT, legacy import, scientific gates and release acceptance remain; no reliable finish date is established yet.

## F31 historical checkpoint

Added optional assessment-binding storage in explicitly created version-three projects. Exact project/worker/workplace/tool context resolves a saved document; source/model validation, immutable ownership and uniqueness prevent silent reassignment. Versions one/two and default desktop creation remain unchanged. [Contracts and limitations](assessment_binding.md).

Validation: 315 tests pass, including eleven additional cases; combined coverage 98.61%, both new modules 100%. Ruff/format, strict mypy (83 files), architecture and builds pass. Independent package/reference/lock evidence: `f31_validation.json`. Original files and dependency versions unchanged; no UI change.

Next: workspace context selection with save/discard/cancel and failure retention, followed by worker/workplace catalogs and combined create/bind behavior. Overall completion approximately 56%; full integrated UI, PLOT/JROT, legacy import, scientific gates and release acceptance remain. A reliable finish date is not yet established.

## F30 historical checkpoint

Added immutable project/worker/workplace/tool ownership and a pure assignment resolver. Thirteen captured reference cases establish exact context matching and separate assignment/placement activity. Duplicate active owners and untyped identities fail explicitly. [Contracts, reference evidence and limits](assessment_context.md).

Validation: 304 tests pass, including eleven new cases; combined coverage 98.56%, both new modules 100%. Ruff/format, strict mypy (81 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f30_validation.json`. No GUI, schema or dependency change.

Next: explicit context-to-document association and persistence/lifecycle contracts using small temporary projects, then incremental worker/workplace integration. Existing drafts are not yet bound to these contexts. Overall completion remains approximately 55%; this foundational slice does not establish additional end-user workflow parity. A reliable completion date still depends on remaining integration, scientific review and release validation.

## F29 historical checkpoint

Recorded the owner's [final target clarification](final_targets.md): ONE integrated application, reference visual/workflow parity, and incremental focused tests before comprehensive-project validation. F28's layout and Apply/Discard workflow are explicitly a temporary harness, not the final UI specification.

Added widget-independent, source-bound LiFFT output rows/cards, preserving reference precision/order/colors and rejecting stale/mismatched/unsupported outcomes. [Contracts](lifft_result_presentation.md). No GUI changed.

Validation: 293 tests pass, including five new tests covering 1,075 task vectors and 29 summary groups. Combined coverage 98.53%; new module 100%. Ruff/format, strict mypy (79 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f29_validation.json`. Dependencies and original files unchanged.

Next: continue original assessment-context characterization and reusable model/presenter integration with small fixtures. Do not prioritize immediate whole-UI reproduction or comprehensive-project support; preserve those final targets. Overall estimate stays 55%; test coverage is not a measure of full migration completeness.

## F28 historical checkpoint

Installed the three explicitly approved Qt versions only in the new project; every previous locked version remains fixed. Added a runnable styled LiFFT preview using the tested presenter/history/evaluation/workspace services. New/open/save, task editing, undo/redo, units/decimal/language controls, aggregate results and review gates work. [Launch, evidence and limitations](desktop_preview.md).

Validation: 288 tests pass, including eleven real Qt widget/dialog workflows. Combined coverage 98.50%; Ruff/format, strict mypy (78 files), architecture and builds pass. Native and offscreen rendering verified; inspected populated/empty/selected/scrolled/invalid/expanded states, English/Spanish, both units, dialogs and 1200×780/960×680 layouts. Fixed a clipped Spanish selector. Evidence: `f28_validation.json`. Original 500 files remain unchanged.

Next: per-task result presentation and keyboard/accessibility behavior, then additional desktop models. Metric/direction scientific gates remain; VTK, legacy files, work contexts and release packaging are pending. Qt filesystem chrome still uses host language; full desktop localization and cross-platform acceptance are not claimed.

## F27 historical audit (approval resolved in F28)

Prepared [the first desktop slice](desktop_first_slice.md), archived the reference stylesheet and verified official Linux wheel metadata for an exact [Qt dependency proposal](desktop-dependency_proposal.md). Proposed versions match the original application's installed Qt stack: PyQt5 5.15.11, PyQt5-Qt5 5.15.17 and PyQt5-sip 12.17.0. No installation, dependency/lock change or GUI implementation occurred. A dedicated Redo icon is missing; use styled text/menu action until a reviewed asset exists.

Baseline validation remains 277 passing tests, 99.61% coverage and all standards/build checks passing. Overall completion remains approximately 51%; this audit adds no GUI functionality. Evidence: `f27_validation.json`. Next: obtain exact-version approval, then implement and visually verify the scoped desktop slice; pending text handling and scientific gates must remain explicit.

## F26 historical checkpoint

Added presenter-owned immutable editing context, rejecting obsolete callbacks after source, unit, decimal or lifecycle changes. Exact context identity prevents toggle-back revival and foreign-owner submissions; invalid text remains retryable and successful edits release context. [Contracts and GUI obligations](edit_context.md).

Validation: 277 tests pass, including eight new ownership/lifecycle tests. Combined coverage 99.61%; the new module has 100% combined coverage. Ruff/format, strict mypy (73 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f26_validation.json`. No dependency, schema or UI changes.

Next: audit the first desktop slice's runtime requirements and reference visual style, then prepare a concrete exact-version GUI dependency proposal before requesting installation approval. Scientific review, remaining models, legacy migration and native packaging remain pending.

## F25 historical checkpoint

Added explicit decimal-point/comma parsing and full-precision editor formatting, independent of language and units. The text edit boundary rejects stale sources and invalid input before mutation, then uses the tested unit/history workflow. [Contracts and limits](numeric_input.md).

Validation: 269 tests pass, including ten new numeric/input workflow tests. Combined coverage 99.61%; both new modules 100%. Ruff/format, strict mypy (72 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f25_validation.json`. No dependency, schema or UI changes.

Next: presenter-owned edit context to reject obsolete display-unit/convention submissions, then prepare the first desktop slice and exact GUI dependency proposal. Scientific review, remaining models, legacy migration and native packaging remain pending.

## F24 historical checkpoint

Added explicit single-field editing from displayed units into recorded source units, using existing scoped history commands. Untouched source values remain exact; exact projected-value re-entry is a no-op. Stale/foreign views and invalid conversions fail before mutation. [Contracts and limitations](unit_edits.md).

Validation: 259 tests pass, including eight new workflow tests. Combined coverage 99.59%; the new module has 100% combined coverage. Ruff/format, strict mypy (70 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f24_validation.json`. No dependency, schema or UI changes.

Next: locale-aware numeric input boundaries with explicit decimal conventions independent of language/units. Scientific review, GUI, remaining models, legacy migration and native packaging remain pending.

## F23 historical checkpoint

Characterized 24 original unit-menu cases and implemented the accepted correction through immutable input display projections. Repeated toggles preserve exact source bytes, cumulative results and history; metric/direction review gates cannot be bypassed by display units. [Audit and design decision](unit_display.md).

Validation: 251 tests pass, including 11 new tests and all existing reference fixtures. Combined coverage 99.59%; new projection and conversion modules 100%. Ruff/format, strict mypy (69 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f23_validation.json`. No dependency, schema or UI changes.

Next: explicit edits from projected units with stale-view protection and exact retention of untouched source fields, followed by locale-aware input boundaries. Scientific review, GUI, remaining models, legacy migration and native packaging remain pending.

## F22 historical checkpoint

Added immutable TST drafts, scoped reversible task edits, strict model-ID serialization and mixed-project catalog/storage routing. All valid TST evaluations require direction review; metric TST also requires conversion review. No results are exposed while gated. [Contracts and compatibility](tst_workflow.md).

Validation: 240 tests pass, including 13 new workflow tests. Combined coverage 99.57%; the new TST draft/commands/codec modules have 100% combined coverage. Ruff/format, strict mypy (68 files), architecture and builds pass. Independent wheel/reference/lock evidence: `f22_validation.json`. No dependency or UI changes.

Next: characterize reference unit-switching behavior and source/history semantics before adding explicit conversion commands. Scientific review, GUI, remaining models, legacy migration and native packaging remain pending. No runnable replacement desktop application exists yet.

## F21 historical checkpoint

Added TST totals, ordered contributions and stateless display mappings, matching 70 actual-method captures. Discovered and preserved the reference UI's selector 1/2 swap; corrected F20's earlier direct-UI-mapping claim. Direction-label and metric conversion review are prerequisites before live TST evaluation integration. [Contracts and discrepancy](tst_summary.md).

Validation: 227 tests pass, including five new summary/mapping tests. Combined coverage 99.53%, new modules 100%. Ruff/format, strict mypy (65 files), architecture and builds pass. Independent package/reference/lock evidence: `f21_validation.json`. No dependency or UI changes.

Next: TST source draft, reversible editing and versioned persistence, then mixed-project source routing with review-required evaluation gates. GUI, scientific review and legacy migration remain pending; no runnable replacement desktop application exists yet.

## F20 historical checkpoint

Extracted typed TST task calculation, preserving all directions, piecewise arm moment, unrounded damage input and display/damage rounding. Added structured numeric guards and direction messages. TST and DUET now share their verified-identical palette while keeping separate probability mappings. [Contracts and evidence](tst_calculation.md).

Validation: 222 tests pass, including eight new tests, 1,650 task cases and 16 probability/color vectors. Combined coverage 99.52%, new TST/palette modules 100%. Ruff/format, strict mypy (63 files), architecture and builds pass. Independent package/reference/lock evidence: `f20_validation.json`. No dependency or UI changes.

Next: actual-method TST summary characterization, then typed aggregation/display and draft/history/storage integration. TST remains isolated; metric scientific review, GUI and legacy migration remain pending. No runnable replacement desktop application exists yet.

## F19 historical checkpoint

Added mixed-session preparation and complete evaluation for DUET/imperial LiFFT, with immutable source-bound results and explicit invalid/review/failure outcomes. The metric LiFFT review gate is enforced; current-result lookup rejects stale revisions and reloaded/switched sessions. No partial totals survive known or unexpected failures. [Contracts and limits](assessment_evaluation.md).

Validation: 214 tests pass, including nine new tests and 91 reference assessment groups through the evaluation service. Combined coverage 99.50%, new module 100%. Ruff/format, strict mypy (60 files), architecture and builds pass. Independent package/reference/lock evidence: `f19_validation.json`. No schema, dependency or UI changes.

Next: characterize/extract the TST task calculation boundary. Metric LiFFT remains review-required; GUI/event wiring, scientific validation, remaining models and legacy migration are pending. No runnable replacement desktop application exists yet.

## F18 historical checkpoint

Added persisted assessment catalogs and explicit create-assessment within the active project. Duplicate IDs are checked before an old save and again inside the insert transaction; failures preserve the old session, with clean state reflecting any successful requested save. Catalog reads never save unsaved edits. [Contracts and limits](assessment_catalog.md).

Validation: 205 tests pass, including ten new catalog/create/failure workflows. Combined coverage 99.48%. Ruff/format, strict mypy (59 files), architecture and builds pass. Independent package/reference/lock evidence: `f18_validation.json`. No schema, dependency or UI changes.

Next: mixed-session preparation and source-bound result freshness, preserving scientific/metric integration gates. GUI, TST/remaining models, scientific review and legacy migration remain pending; no runnable replacement desktop application exists yet.

## F17 historical checkpoint

Added explicit version-two mixed-assessment project files and tagged source codecs, preserving version-one LiFFT read/write compatibility without automatic migration. Transactional model-identity guards prevent cross-tool overwrite. The existing workspace is now generic, with typed model edit adapters and verified Save/Discard/Cancel/history transitions. [Contracts and limits](mixed_assessment_projects.md).

Validation: 195 tests pass, including 11 mixed-format/workspace/failure tests. Combined coverage 99.45%; new project adapter 99%, other new modules 100%. Ruff/format, strict mypy (58 files), architecture and builds pass. Independent package/reference/lock evidence: `f17_validation.json`. No dependency or UI changes.

Next: assessment catalog and create-assessment operation within an open version-two project, followed by mixed-session preparation/result freshness. Version-one upgrades, TST, GUI, scientific review and legacy migration remain pending; no runnable replacement desktop application exists yet.

## F16 historical checkpoint

Added DUET source drafts, reversible scoped task commands, complete input preparation/freshness checks and strict version-one JSON/SQLite persistence. Shared transaction and JSON validation implementations with LiFFT while preserving its schema/API compatibility. DUET stores use a distinct marker; combined project integration is not yet implemented. [Contracts and limits](duet_workflow.md).

Validation: 184 tests pass, including 12 new workflows and real SQLite failure/rollback/retry plus file close/reopen. Combined coverage 99.44%, new modules 100%. Ruff/format, strict mypy (53 files), architecture and builds pass. Independent package/reference/lock evidence: `f16_validation.json`. No dependency or UI changes.

Next: multi-assessment project ownership/routing and explicit format versioning so LiFFT and DUET coexist in the project manager safely. The existing ProjectFile/Workspace still uses LiFFT. Live GUI/model coordination, scientific review and legacy migration remain incomplete; no runnable replacement desktop application exists yet.

## F15 historical checkpoint

Added immutable DUET totals/contributions and complete stateless display mappings. Shared validated row-order arithmetic and bounded probability formatting with LiFFT while retaining each model's probability/palette. Preserved five-decimal row versus four-decimal total display; zero-result mappings explicitly clear stale colors/shares. [Contracts and differences](duet_summary.md).

Validation: 172 tests pass, including six new tests and 63 actual-method DUET summary cases; prior LiFFT fixtures still pass. Combined coverage 99.37%, new/modified summary modules 100%. Ruff/format, strict mypy (46 files), architecture and builds pass. Independent package/reference/lock evidence: `f15_validation.json`. No dependency or UI changes.

Next: DUET source draft, edit/history and preparation contracts, then versioned persistence. Live GUI/result coordination, scientific validation and LiFFT metric review remain incomplete. No runnable replacement desktop application exists yet.

## F14 historical checkpoint

Extracted immutable DUET task/results, unchanged lookup/probability arithmetic and presentation-owned continuous colors. Integer scale validation follows the existing 0–10 selector; unsupported legacy coercion/indexing behavior is explicitly rejected. Common issues/numeric guards moved to a tool-independent module with LiFFT compatibility exports. [Contracts and audit](duet_calculation.md).

Validation: 166 tests pass, including eight new tests, 198 frozen task cases and 16 probability/color cases; combined coverage 99.35%, new modules 100%. Ruff/format, strict mypy (42 files), architecture and builds pass. Independent package/reference/lock evidence: `f14_validation.json`. No dependency or UI changes.

Next: actual-method characterization of DUET assessment summaries, then typed aggregation/display mappings. DUET draft/history/storage and live UI coordination remain incomplete; scientific review and LiFFT metric review remain open. No runnable replacement desktop application exists yet.

## F13 historical checkpoint

Added immutable LiFFT source preparation with complete ordered input issues and session/revision freshness checks. Shared input guards now serve both calculator and preparation. Empty drafts are explicitly incomplete; missing values never become zero or partial totals. [Contracts and limitations](lifft_preparation.md).

Validation: 158 tests pass, including nine new preparation/freshness tests and SQLite save/load; combined coverage 99.33%, both new modules 100%. Ruff/format, strict mypy (38 files), architecture and builds pass. Independent package/reference/lock evidence: `f13_validation.json`. No dependency or UI changes.

Next: characterize DUET's model and assessment call sites for the next pure calculation slice. LiFFT live result coordination/UI remain pending, with the metric scientific-review gate open. The preparation contract is not an automatically wired result cache. No runnable replacement desktop application exists yet.

## F12 historical checkpoint

Added immutable LiFFT assessment summaries and ordered task contributions, preserving row-order addition and reference rounding. Presentation owns bounded probability text and color mappings. Zero totals carry no evaluated probability and provide explicit display clearing rather than stale widget state. [Contracts and differences](lifft_summary.md).

Validation: 149 tests pass, including eight new tests and 60 captures from the actual reference assessment method; combined coverage 99.00%, both new modules 100%. Ruff/format, strict mypy (36 files), architecture and builds pass. Independent package/reference/lock evidence: `f12_validation.json`. No dependency or UI changes.

Next: application assessment validation/completeness and result freshness across edit/undo/load, with explicit incomplete-preview semantics. The scientific metric review gate remains open before complete workflow/GUI integration; no runnable replacement desktop application exists yet.

## F11 historical checkpoint

Extracted typed, immutable LiFFT task results, the unchanged damage lookup and positive-damage probability expression. Kept the continuous palette in presentation. Missing/negative/boolean inputs and overflow have explicit guards with localized messages. [Calculation contract and limitations](lifft_calculation.md).

Validation: 141 tests pass, including eight new tests and 2,150 frozen task cases plus 13 probability cases; combined coverage 98.92%. Ruff/format, strict mypy (34 files), architecture and builds pass. Independent package/reference/lock evidence: `f11_validation.json`. No dependency or UI changes.

Next: characterize assessment aggregation, contributions and zero-total/display-risk behavior at actual reference call sites, then define typed assessment results. Scientific validation and the metric-moment review gate remain open before workflow integration. There is no runnable replacement GUI yet.

## F10 historical checkpoint

Added explicit workspace Save and New with first-document persistence, candidate postcondition checks, protected existing destinations and initialization-failure cleanup. Requested saving of the current project precedes New; a failed creation retains that session. Pending cleanup now records exception type/errno without raw messages. [Decisions and limitations](workspace_save_create.md).

Validation: 133 tests pass, including 13 new Save/New workflows; combined coverage 99.38%, modified production modules 100%. Ruff/format, strict mypy (31 files), architecture and builds pass. Independent package/reference/lock evidence: `f10_validation.json`. No dependency or UI changes.

Next: characterize actual LiFFT calculations against the unchanged reference and define typed result/input-validation contracts. Do not silently correct scientific/model behavior. The metric-moment review issue, Save As policy, assignment/context migration and GUI remain pending.

## F9 historical checkpoint

Added ProjectWorkspace with owned candidate/active repositories, explicit dirty decisions, save-before-release, same-file connection reuse and failure-safe candidate cleanup. Settings/old-handle release warnings do not undo successful activation. Failed cleanup handles remain owned for explicit retry. [Decisions and limits](project_workspace.md).

Validation: 120 tests pass, including 14 new workspace workflows and real two-file switching; combined coverage 99.32%, workspace module 100%. Ruff/format, strict mypy (31 files), architecture and builds pass. Independent wheel/source/lock evidence: `f9_validation.json`. No dependency or UI changes.

Next: explicit workspace save and new-project/initial-document creation use cases, with failure cleanup and UI-facing diagnostic results. Save As policy, full scientific model migration and GUI remain pending. Cleanup warnings currently expose stable keys/counts; detailed logging is not yet implemented.

## F8 historical checkpoint

Added immutable project metadata and owned ProjectFile connections with exclusive creation, validated existing-file open, identity enforcement and cleanup. Successful document opens now update recent history; settings failures return a separate localized warning without undoing the open. [Decisions and limits](project_files.md).

Validation: 106 tests pass, including 12 new project/integration workflows; combined coverage 99.21%, new modules 100%. Ruff/format, strict mypy (30 files), architecture and builds pass. Isolated package/source/lock results: `f8_validation.json`. No dependency changes or legacy project migration.

Next: cross-file project-switch coordination, preserving the current project when candidate setup/open fails or the owner cancels. Handle-level connection ownership is complete for this slice; the application still needs coordinated ownership across multiple project files. Save As, GUI and scientific model work remain pending.

## F7 historical checkpoint

Added immutable user preferences and bounded recent-document history, separate from saved assessment units. Language is now application-owned with a compatible presentation re-export. Versioned settings JSON is validated strictly and replaced atomically; failure tests retain prior settings. Listing history never opens its documents. [Decisions and limitations](user_settings.md).

Validation: 94 tests pass, including 12 new settings tests; combined coverage 99.08%, new modules 100%. Ruff/format, strict mypy (27 files), architecture and builds pass. Independent package/source/lock checks: `f7_validation.json`. No dependency changes and no real user settings were altered.

Next: project metadata and repository connection ownership; integrate successful open with recent-history updates while reporting settings-write failures separately. Platform paths, missing-file UI, full project manager, Save As and GUI remain pending.

## F6 historical checkpoint

Added single-document open/close coordination with explicit save/discard/cancel choices, load-before-save ordering, same-document history retention and failed-I/O recovery. The application depends only on a repository protocol; the existing SQLite adapter is exercised in integration tests. [Decisions and caller responsibilities](document_lifecycle.md).

Validation: 82 tests pass, including 12 new lifecycle workflows; combined coverage 98.96%, new module 100%. Ruff/format, strict mypy (25 files), architecture and builds pass. Package/reference/lock evidence: `f6_validation.json`. No dependency changes or UI modifications.

Next: project metadata and settings/recent-document behavior. This is not a complete project-file manager or GUI; callers still own connections and must handle dirty-choice dialogs. Save As policy remains pending, as does scientific review before metric-moment integration.

## F5 historical checkpoint

Implemented strict version-one LiFFT draft serialization and a SQLite DocumentStore adapter. Identity, original units, missing values, order and numeric precision round-trip. Invalid data/versions are rejected; explicit initialization refuses existing schemas. Real SQL failure tests prove rollback and dirty-state retention with successful retry. [Format, transaction contract and limitations](draft_storage.md).

Validation: 70 tests pass, including 14 new storage tests; total combined coverage 98.83%, both new modules 100%. Ruff/format, strict mypy (24 files), architecture and builds pass. Isolated package/source/lock verification: `f5_validation.json`. No dependency changes; only temporary test databases were written.

Next: application-level load/open/close coordination and explicit dirty-state choices; then project lifecycle, settings/recent files. Save As policy remains to be confirmed before implementation. This storage format does not read/migrate legacy projects, provide multi-writer conflict handling, or certify power-loss recovery. Calculation and GUI work remain pending.

## F4 historical checkpoint

Added immutable LiFFT tasks/drafts with original units, stable task IDs and explicit missing fields. Task insertion/replacement/removal uses the F3 history and rejects stale or wrongly scoped edits. Structured validation issues and action labels have English/Spanish messages. [Decisions and limits](lifft_draft.md) distinguish structural completeness from physical/model validation.

Validation: 56 tests pass, including 13 new assessment workflows; total combined coverage 98.51%, both new production modules 100%. Ruff/format, strict mypy (22 files), architecture and builds pass. Isolated wheel/source/lock results: `f4_validation.json`. No dependency versions changed.

Next: versioned draft serialization with round-trip/corruption tests, then a transactional storage adapter against temporary test data. Full LiFFT calculation, scientific validation, context/legacy-ID mapping, locale numeric input, unit switching and GUI remain pending. The metric-moment review gate is still open.

## F3 historical checkpoint

Implemented `DocumentSession`, scoped edit commands, immutable snapshot undo/redo, monotonic revision identities, dirty tracking and a synchronous storage port. Failed commands/saves preserve usable state; cross-document and nested operations are rejected. [Decisions, contracts and limitations](session_history.md) explain the boundary.

Validation: 43 tests pass, including 12 new session workflows; overall combined coverage 98.07%, session.py 100%. Ruff/format, strict mypy (18 files), architecture checks and builds pass. Independent wheel and reference-tree verification are recorded in `f3_validation.json`. No dependency versions changed.

No disk persistence, complete project coordinator, Save As/close UI, background saving, history memory bound or Qt shortcut routing exists yet. Deeply immutable snapshots and pure commands are required contracts. The next slice should supply a real assessment draft/commands and guide transactional persistence/project lifecycle. The metric-moment review gate remains open.

## F2 historical checkpoint

Added immutable model input normalization, the explicitly isolated reference moment-display policy, and English/Spanish risk catalogs with independent language contexts. No dependency versions changed. [Audit, decisions and limitations](units_localization_audit.md) preserve the reference behavior and unresolved integration questions.

Validation: 31 tests pass, including 48 new reference conversion vectors; combined coverage 97.35%, both new modules 100%. Ruff/format, strict mypy (17 files), architecture checks and package builds pass. Wheel smoke and reference-tree integrity results are in `f2_validation.json`.

Remaining limitation: these are partial unit/localization foundations, not live unit switching or a translated GUI. The original metric moment expression needs scientific review before assessment integration. Spanish risk terminology needs review when displayed in the first localized UI. Session/save/history contracts are next.

## Completed F1

- Independent new repository and package layout in the owner-approved destination. The reference checkout remains the behavioral source, with provenance and hashes saved locally.
- Approved project-local Python 3.13.14; five exact developer tools and transitive dependencies locked. No system/Conda upgrade and no GUI/solver dependencies.
- Pure risk-category function with separate immutable display mapping and stable localization keys.
- Initial UI-independent body-renderer port; VTK dependency confinement enforced, actual adapter pending.
- Local copies of 61 processed icons and 8 STL assets, packaged and integrity-tested.
- Naming/docstring/import/format/type/architecture gates, behavioral tests and a source/wheel build.

## F1 historical verification

18 tests passed on Python 3.13.14, covering 1,013 reference risk inputs, invalid values, immutable renderer state, RGB bounds, resource safety/integrity and nine architecture scenarios. Combined statement/branch coverage: 96.35% (90% gate); migrated production modules: 100%. Ruff lint/format, strict mypy across 15 files, architecture checks and both builds passed. Negative Ruff probes detected missing documentation/annotations and invalid naming. Independent wheel smoke verified all 69 packaged assets and classification. Hash comparison verified all 500 pre-existing reference files unchanged with no added/deleted files. See `foundation_validation.json`, the resource manifest, fixture metadata and local `artifacts/` reports.

## Decisions and limitations

See [architecture decisions](architecture.md) and [approved dependencies](dependency_proposal.md). The nonfinite-input guard is an explicit typed API difference requiring call-site reconciliation before workflow integration. Finite reference behavior is preserved. The isolated positive-damage LiFFT probability function is implemented; scientific model validation, application assessment coordination, operational database migration, full GUI, complete localization/units workflow, full project/session lifecycle, solver and VTK rendering remain incomplete. No UI changed, so no window visual acceptance was required in F1. Native platform and avatar inspection will be needed with the first relevant UI slice.

The repository has no commit or remote yet; work exists as files in the approved destination. Historical documents under `reference/` retain their original proposal wording. Owner authorization and current decision records supersede that status.

## Next work, in order

1. Read this checkpoint, architecture/coding/development documents and owner authorization. Run `bash tools/check.sh` to establish the starting state.
2. Read the F2 audit. Preserve its model-specific conversion policy and integration gates; expand unit/localization support through actual workflows rather than assuming all conversions are covered.
3. Follow final_targets.md: incrementally characterize original assessment contexts and build reusable model/presenter components with focused fixtures. The harness is temporary; its controls are not the final workflow. Preserve scientific gates. Visually inspect any later GUI changes against the original application. Display toggles must remain read-only projections rather than source conversion commands. Keep TST direction/metric and LiFFT metric evaluation gates intact. Scientific review remains separate from behavioral parity. Save As requires its separate policy decision. Platform paths, GUI and legacy/context migration remain pending.
4. Qt desktop (F28) and the exact VTK runtime set (F78) are approved/installed. Additional solver or dependency changes still require exact-version approval. Preserve the current style and packaged assets.
5. Stage 2: first end-to-end assessment slice, project save/open, units/language/history behavior and visually verified UI. Then remaining assessments/work management, PLOT, JROT, and full parity/native packaging as in the accepted plan.

At each milestone update this file with scope, evidence, limitations, decisions, next actions and overall percentage. Keep the reference code/environment untouched. No production dependency may point to that tree.
