# Migration review register

Owner instruction, 2026-10-09: record noncritical inconsistencies here and continue
one fixed M milestone at a time (latest owner instruction, 2026-10-10). Critical
decisions may still require owner input.
This register does not authorize scientific corrections or final UI differences.

| ID | Finding | Migration policy | Later review |
|---|---|---|---|
| R001 | Original main.py swaps ST dropdown indices 1/2 before pyTST; pyTST comments name the internal codes oppositely. This does not prove a scientific error. | Preserve visible choices AND the executed reference mapping through an explicit source convention. Preserve existing new-format/model-code documents. No owner answer required for compatibility. | Review model comments/scientific intent separately; existing scientific gates remain. |
| R002 | Original cached assessment results are retained in the source archive but are not fresh evaluation caches in the migrated UI. | Never silently label old results as newly calculated. | Complete historical-result display compatibility before final parity acceptance. |
| R003 | Original plant transform/display metadata is archived; not every field drives the new PLOT view yet. | Preserve raw source fields and exact referenced image bytes. | Complete relevant transform/display parity before final acceptance. |

## R004 — assessment picker presentation and popup capture

The existing Open picker uses stable raw document IDs, including recovered legacy IDs. This remains functional but is not final owner-facing assessment-selection parity. EN/ES selected-state text is visible. Expanded popup grabs are blank/black on this compositor and require manual visual confirmation; no expanded-state acceptance is claimed. Improve selection descriptions within original workflow during final parity review. No owner answer needed now.

## R005 — long numeric values in narrow assessment input fields

F140's comprehensive ST source contains a floating representation such as
8.900000000000005. At minimum width the Load field can horizontally scroll to
its trailing digits after loading, obscuring the leading value. Retain the exact
stored number and unit provenance; improve readable formatting/cursor placement
with a focused no-edit round-trip regression. No formula or saved-data rounding
is authorized by this finding. This is a display correction for the next parity
work, not a reason to block conversion.

## R003 follow-up — F142 active-loader audit

The active original showPlantImage -> loadImageNew path reads image_name and fits original image pixels. It does not apply stored Plant rotation/crop/mirror/etc. Exact scene/fit/resize characterization passes against that frozen original method. Do not activate dormant fields as a compatibility fix. Raw fields remain archived; broader PLOT parity is still subject to final acceptance.


F143 follow-up (R004/R005): Open choices now identify tool, worker/name, workplace/shift and version/assignment. Stored IDs stay unchanged. Numeric controls retain full precision and start at leading digits. EN/ES selected states pass; expanded popup grabs remain blank and need manual verification.


## R002 follow-up — F144 historical display

Original cached totals/rows are now shown with Recorded / Registrado provenance,
original tool colors and exact source binding. Pending text clears the displayed
historical outputs immediately. Fresh calculation approval gates remain unchanged.

## R006 — Spanish JROT scope summary at minimum width

The selected station count in the Spanish JROT scope can truncate at 1480x740.
The scope and selected IDs remain correct; the current tooltip/chooser carries
the full context. Check the original layout constraints and improve this narrow
summary during the next visual parity slice. No solver or stored-data change is
required. This is not final visual acceptance.


## F145 metric compatibility policy

Preserve the characterized original metric normalization and moment-display
expression through fresh LiFFT calculation. This closes the application barrier
without certifying the physical conversion or changing formulas. Any scientific
correction remains a separate owner-reviewed change.

## R007 — synthetic unbound-project sidebar captions

F145 actual metric-source native capture shows numeric key metrics but some static
sidebar captions are not visibly painted after replacing a project with a synthetic
unbound source. Bound comprehensive-project captures show these captions. Verify
this specific state during G2 acceptance; do not claim final visual parity from the
synthetic capture or add general refresh infrastructure.


## R001 follow-up — F146 live ST compatibility

Fresh calculation now honors each source's explicit direction convention using
all frozen model vectors for both conventions. The original UI label/formula
inconsistency remains preserved; no scientific correction was made.

## R007 follow-up — F148 broader main-window render/capture states

The comprehensive EN DUET and EN/ES LiFFT captures after switching/resizing also
show missing/clipped captions or left-side regions; ES DUET pending capture has
similar artifacts. The final ES ST pending capture also shows missing regions.
This is not limited to synthetic unbound sources. ST populated, PLOT
and JROT populated captures are readable. Isolate actual widget geometry/painting
versus capture artifacts against the original layout in F149. Do not claim these
states have passed final visual acceptance or add general refresh infrastructure.

## R008 — Save of a fresh calculation with unchanged imported inputs

Reference main.py saveFile -> saveToolsData -> saveLiFFTToolData reads the result
labels (around lines 7030 onward) and writes WorkerStationShiftErgoTool totals
(around 7091 onward), including when inputs are unchanged. The new read-only CSV
export preserves exact-source archived evidence; an in-memory recalculation alone
does not replace that evidence. Edited-source Calculate/Save/export works.
Complete fresh saved-result provenance under existing B1/C4 acceptance, preserving
the original archive separately and avoiding a false source edit to mark freshness.
This is a concrete compatibility gap, not a new report engine or scientific fix.


## R007 disposition — F149 verification corrected

Full-resolution F148 source PNGs contain the captions and regions reported absent
when reviewing combined previews. No application layout defect was established.
F149 checks owned CPU captures, individual full-resolution PNGs, visible caption
ink, control rectangles, adjacent-pixel preservation and full-body framing across
20 EN/ES states. The application wheel is unchanged from F148. R007 closes as a
visual-verification finding, not as a production repaint/layout fix. Final
same-platform/size/DPI original comparison remains in the acceptance ledger.
See f149_compatibility.md; do not add refresh infrastructure on this basis.


## R004 disposition — F152

Expanded EN/ES assessment selection is now captured and inspected on the native
approved Qt baseline with all 194 human-readable captions. The selected row was
white on white with Qt's native menu delegate; applying the same styled delegate
used in management/JROT restores white text on branded teal. The pixel regression
and exact-choice/modal/cancellation checks pass. R004 closes; this does not award
all of C4's remaining navigation/history acceptance criteria. See f152_compatibility.md.

## R008 disposition — F150 explicit Save path

Explicit Calculate/Save/export/reopen now prefers a matching fresh saved result,
with source and outputs committed atomically and original import evidence kept
unchanged. Save As also passes the current result into the copy. Original Save
precision/boundary handling is characterized. Remaining B1/C4 criterion: implicit
dirty-transition Save still writes source only, and needs the same calculation
persistence acceptance before final lifecycle parity. No artificial input edit or
archive replacement is used. See f150_compatibility.md.

## Form comparison limits — F151/F152

Read-only source constructors, headers, control types, selector captions and icon
sizes are compared using the approved Qt baseline. DUET/ST Calculate icons now
match the original 28 pixels. Initial constructor-only LiFFT summary visibility
is not proof of an integrated application discrepancy: original alignToolSummary
(lines 4237–4244) explicitly shows these labels on the integrated result path.
Final populated integrated comparison must include that path, rather than treating
the constructor harness as the complete original application. No layout redesign
or new refresh callbacks follow from this observation.


## R008 closed — F153

Dirty-transition Save now commits matching current source/result together, as
explicit Save already does. Invalid targets fail before Save; failed storage
retains the dirty session; Cancel/Discard never write results. Save As success
and result-write failure retain original ownership/data. See f153_compatibility.md.

## R009 closed — F154/F155 live summary visibility

Original constructors initially hide summary labels, but the integrated live
refresh calls alignToolSummary, which shows them for all three tools. Full-app
oracle on an isolated copy confirms this. DUET/ST inline totals are restored;
all tools share original styling and real damage-column alignment. No change
to scientific values or reference files. See f154/f155_compatibility.md.

## R010 open — final unit abbreviation and summary provenance text

The original active setUnitText uses "in", whereas its constructors and migrated
forms use "inch". Both denote the same unit; retain current spelling pending
final G1 text disposition. Original loadToolsData recalculates rows and then
restores archived summaries; migration keeps recorded/saved evidence explicit.
Rounded saved damage may yield a palette shade differing from unrounded fresh
results. Existing source/evidence policy remains; do not silently recalculate or
replace archive fields to force screenshot identity. No owner decision blocks
current compatibility work. Final whole-window acceptance remains open.

## R011 review — Spanish sidebar caption in minimum-size ST pending capture

Individual f155-main-window/tst-metric-pending.png appears to truncate the left
edge of Repeticiones in the unchanged key-metrics sidebar. The larger/populated
states differ. Check the label's actual text rectangle/font metrics and individual
PNG before changing layout: F149 showed combined previews can mislead. This is
assigned to existing G1/G2 text/resize acceptance, not a new infrastructure task.
No final no-clipping/text acceptance is claimed from rectangle containment alone.


## R010 disposition — M01

Active imperial arm headers now use original `in`. Fresh Save/reopen palette shades
use retained row precision; stored summary values and immutable archive evidence
remain unchanged. Archive/source provenance and original Save probability precision
remain explicit. Focused tests and 18 integrated native states pass; see
m01_acceptance.md. No silent original-input recalculation introduced.

## CR002 pending — M01 ST keyboard order

Original Tab visits all direction combos first; migrated Tab visits each row's
combo and numeric fields in sequence. No change made. Owner choice pending under
scope-control rule: restore original order with a small local correction/regression,
or accept row order as an intentional improvement. No new milestone/points.


## CR002 closed — original ST keyboard order retained

Owner: "AS THE ORIGINAL BASE CODE DO IT". Direction selectors are visited first,
then numeric editors, exactly as original setupTSTTab. Tests cover Tab/Backtab and
rebuilds; original-code comparison passes both units/sizes. No calculation changes.
Optional later review only: assess whether row-by-row Tab order would improve
entry ergonomics. It is not authorized for this migration or a new milestone.


## M02 original form disposition

Visible original layout retained; original `Note:` prefix restored (`Nota:` in ES).
Sixteen source-layout cases and packaged state review passed. No new UI workflow.
Original saveWorker writes raw height/weight and loadWorkerDetails reads them raw,
confirming the F72 unit-provenance warning. The legacy_catalogs._worker comment
claiming every row is cm/kg is not established by that code. Review the existing
M04.3 conversion policy using original-data evidence; do not change imported values
or infer worker units from a project's current UI label during M02. This remains
original-data compatibility work, not an added milestone or new M02 requirement.


## M03 existing wording/behavior disposition

F68 already records generic Job Save success wording in place of three original
branch-specific messages. M03 retains it as a noncritical message review item;
Save behavior/results are covered and unchanged. No extra repair or milestone is
authorized here. Existing M09/M11 presentation/disposition review must retain this
explicit difference until final wording is accepted or a correction authorized.
The already documented referenced-record protections remain active; no historical
assessment owners are cascaded away. See m03_acceptance.md for comparison limits.


## M04 worker-unit audit and finite lifecycle work

Original Worker save/load writes displayed numbers unchanged and has no row unit
tag/history. The universal cm/kg importer comment is unsupported. Comprehensive
project declares Metric and has ten nonempty measurement rows; current conversion
preserves their numbers exactly but cannot establish entry-unit history. Required
owner policy question pending. No raw source rewrite or silent unit inference.
See m04_review.md for the existing New/first-Save and empty-project Open gaps and
the one bounded remaining correction batch; M04 is explicitly incomplete.
Existing Spanish Transfer explanatory paragraphs remain English; retain under M09
whole-app localization acceptance, without adding a milestone or certifying them.


## M04 final disposition — CR003

Owner authorizes interpretation of legacy body measurements using the declared
project units, normalized only in converted editable records to canonical cm/kg.
Prior pending-policy notes are superseded; no source/archive rewrite or numeric
range inference. Original New/first-Save and empty Open corrections verified.
See m04_acceptance.md. Existing Spanish Transfer paragraph review remains M09.


## M05 final disposition — existing migration policies

Raw comprehensive original PLOT queries omit three old-table LiFFT sources which
F131 already recovers on assignments 101/102/104. Converted all-shift count is 100
versus 97 in the raw normalized table. Matched-data original SQL agrees exactly;
raw and matched comparisons are retained. Existing F113 paired difference and
missing-observation rules remain explicit (two comprehensive cases differ from
unpaired original subtraction). No new defect repair or scope added. See
m05_acceptance.md and m05_validation.json.


## R006 closed — M07 scope-summary clipping

The existing narrow count labels now show `N sel.` in English and `N selec.` in
Spanish, with complete selected member names in tooltips. The source control
layout and opaque selected contexts are unchanged. Native comprehensive-copy
4-plant/6-section/8-line/16-station selection fits at 1480x740 in both languages;
expanded chooser selected IDs and Apply/Undo/Redo/Cancel are verified. See
m07_acceptance.md and artifacts/m07-m08-native/verification.json.

## R012 — M07/M08 noncritical choices for later owner review

No answer was needed to finish the authorized batch. Compact scope-count wording
preserves the existing geometry; the tooltip and chooser retain full names. The
new Edit/Editar menu follows the already accepted PLOT history treatment and uses
platform-standard bindings (Linux Redo includes Ctrl+Shift+Z). History is scoped
to the selected modal scheme: New/load/Cancel/confirmed deletion reset it, and
Undo/Redo clears transient comparison/preview views while retaining applied
source provenance. Confirmed database deletion remains its existing separate
operation; draft Undo does not resurrect deleted records. These choices avoid
adding cross-scheme recovery, solver features or new milestones. They can be
reviewed after M08 without blocking it; see jrot_history.md.


## R011 disposition — M09 shared native review

Closed without layout change. Individual original/current Spanish ST pending
images show Repeticiones in full. Current ink x=1..76 fits 113 px; Momento máximo
x=1..112 fits the same width. All 34 current shared captures inspected; see
m09_review.md and artifacts/m09-native/verification.json. Spanish Transfer
explanatory paragraphs also render translated from the existing catalog; the
M04/M09 concern is closed without a new Transfer change.

## CR005 / R013 — original project captions, awaiting owner decision

Read-only original live update (main.py 4188–4194) adds Current Project: in header
and footer plus • Loaded in the header. Migrated MainNavigation shows the name
alone. Prior F75 layout harness supplied bare names and did not validate that live
update. Proposed original-caption restoration is reviewable in
reference/m09-header-proposal.patch.txt, NOT applied. Owner asked to approve the
bounded repair or approve current captions as an exception. Fixed M09.1 remains
open; no new milestone, weight or data/formula/dependency change. See m09_review.md.


## CR005 / R013 disposition — owner approved and implemented

Owner answered yes on 2026-10-11. Original live header/footer captions restored
with EN/ES equivalents; no data/calculation/dependency change. Empty/unsaved/first
Save/Close and pending text checks pass, including literal persisted metadata.
Final wheel's 14 main-window captures inspected at 1550×1015/1800×1200; full
project title ink fits. See m09_acceptance.md and m09_validation.json. CR005 closed;
M09 complete at 94.50/100. No extra milestone or hidden scope expansion.


## CR006 / R014 — transfer result preservation, approval pending

M10 copied-project and independent one-click probes confirm input-only transfer
loses exact saved/archived results and their units/provenance. Original copies
summary and result rows. No repair applied. See m10_transfer_result_proposal.md
and m10_review.md; fixed progress remains 94.50/100.


## CR006 / R014 closed — exact transfer results

Owner answered yes after rounding clarification. Copy/Move preserves exact
saved/imported outputs, units and provenance; formulas unchanged. Full gate
1,207 tests, 96.42% coverage, 23 packaged regressions and final comprehensive
scenario/reopen pass. See m10_acceptance.md. M10 earns fixed 0.75 points to
95.25/100; no additional milestone. Earlier pending wording is historical.


## CR007 / R015 — original Find Assessment form missing

M11 active-path inventory confirms original Search opens WorkerSearchDialog;
new Search opens the selected-worker context chooser. One original form is
missing. Bounded proposal in m11_search_proposal.md, awaiting owner approval.
No repair applied; progress remains 95.25/100.


## CR007 / R015 disposition — owner approved original Search restoration

Owner explicitly answered “Approve original Search restoration”. Original Search
controls/layout and filters restored over typed project snapshots; no SQL in the
form. Sorted selections carry exact assignment/model identity, including closed
owners and multiple historical assignments at the same workplace. Cancel retains
invalid pending text. Accepted selection uses existing Save/Discard/Cancel and
cross-worker selection. English control geometry matches the source constructor
at opening/minimum/enlarged sizes. Spanish labels fit using local text constraints;
the original compact English surname caption and minimum-width table scrolling
remain as in the reference. No additional original route gap was found in this
bounded inventory. See m11_acceptance.md and feature_inventory.md. No added points,
dependencies, scientific changes or speculative infrastructure.

## Owner-deferred saving and arrow controls — post-migration

Owner wants to consider replacing PLOT/JROT Save buttons with main-window Save
and placing back/forward arrows later. This is a future interaction/ownership
decision, not an approved change in the keyboard/menu history extension or an
outstanding migration defect. Existing explicit saving remains. Review before
implementation how main-window Save obtains modal draft ownership, persistence
scope and failure/discard consent. No new milestone or implementation is authorized.

Visual observation from final history captures: unchanged compact Spanish PLOT
tabs use native scrolling, and the long main-window organization caption reaches
the right button boundary at minimum width. Retain these for owner Linux review;
no layout repair is included in the keyboard/menu history extension.

## M1R — existing sample limitations and stale caches

Two supported comprehensive original projects regenerated successfully (194
assessment versions each). Their calculations match original code for all 388
versions / 7,154 task rows. Each original contains 29 ST cached totals inconsistent
with its saved inputs after rounding to four places. Owner-approved M1R discards
these stale caches and stores recalculated original-formula outputs; no scientific
correction or extra milestone is introduced. Only count-level comparison evidence
is recorded, not a second per-assessment output dataset.

Two other original samples remain unsupported: JROT_EpiSalmonTestStudy01.ergprj
fails the existing schema-version-8 requirement; test3.ergprj fails existing nonblank
title validation. Source files remain untouched. Supporting/repairing those inputs
would be separate owner-approved scope, not hidden work in M1R or a silent new
milestone. They are not claimed converted. See cleanup-m1r-projects.json.

## Cleanup M2 noncritical notes

The temporary converted copy intentionally reuses the existing New-project
pre-save UI policy: the header says no project loaded and management/PLOT/JROT/
export stay disabled until Save, while its actual assessments/results are editable.
An explicit localized bottom message identifies conversion and requests Save.
A different unsaved caption/control policy is future owner review, not silently
added scope. Original required Name/Description form remains compact: long names
scroll within its QLineEdit and are retained literally. No layout redesign.
The earlier JROT schema and blank-title original remain unsupported as recorded
under M1R; copying their originals does not claim successful conversion.


## Cleanup M4 documentation findings — resolved within documentation scope

Stale prose referred to future integration, an immutable imported result archive,
ambiguous helper returns and a global JROT menu point. Reviewed against current
bodies/callers, these descriptions now explain the integrated host, sole matching
result cache, concrete helper return types and viewport coordinates. Existing
historical regression names remain where they identify earlier compatibility
scenarios; they do not imply an archive inside new native projects. No runtime
behavior or new defect repair was introduced. No owner decision blocks M4.


## Cleanup M5 final acceptance review

M5 is complete for Linux at 6/6 (100%). No newly discovered critical defect or
scope repair was added. All uncovered paths are reviewed in cleanup_m5_coverage_review.md.
Native minimum-size Spanish captures show long selected combo text elision, PLOT tab
overflow scrolling and a tight main organization button caption. These existing
text-fit observations are for later owner UI review; default/enlarged controls and
workflows remain accessible. PLOT gauge captures may be mid-animation; scientific
validation uses exact saved/evaluated values. Two unsupported original samples remain
as already documented. User testing can begin; native Windows/macOS stays deferred.

## Owner-approved context-navigation follow-up — 2026-10-12

The owner supplied the updated reference's Work Setup/Follow worker/Keep context,
automatic Open, classified Saved/New picker and creation warning behavior and explicitly
authorized translating it into the new architecture. The mandatory Open picker and
rejected-worker navigation are replaced. This supersedes historical picker integration
notes, including R004's intermediate Open flow. No new milestone or unapproved scope.
See assessment_navigation_acceptance.md and assessment_navigation_validation.json.


## Display-preferences acceptance — owner-supplied icons and existing fit limit

R005's long-float display is resolved by project precision plus exact-token editors;
source/results remain exact. Fractional repetition sources are preserved while the
approved default display is whole numbers. See icon_inventory.md for dedicated Redo,
Retire and optional action-specific replacements; appropriate existing assets are
reused meanwhile. No invented arrow icon or unrelated system icon was introduced.
The previously documented Spanish main-window minimum-width text fit remains outside
this bounded correction; native 1800×1120 fits. No new milestone was added.


## Context chooser follow-up — compact saved-standalone caption observation

2026-10-17: owner requested moving standalone navigation inside the context picker.
That change is implemented. During native composite inspection at 1548×1040,
the saved-standalone VTK image overlaps the top of the body-region caption while
Associate assessment remains visible. Enlarged 1800×1120 EN/ES captures fit.
No live-layout versus capture-cause conclusion, visual waiver or extra repair is
claimed. Confirm live during owner testing before defining a separate correction.
Evidence: artifacts/context_chooser_review/main_standalone_es.png and corresponding
large captures; docs/context_chooser_acceptance.md. No new milestone or points.


## Gauge-marker follow-up — existing integer animation behavior

2026-10-17: isolated marker tests called the existing _AnimatedScale.set_value with
an integer target. Qt interpolation between its float start and integer end produced
no current value. Repeating with the API's float percentage target exercised normal
interpolation. _AnimatedScale and DamageScale executable ASTs match the pre-change
wheel; neither was repaired as part of marker appearance. Production percentage
callers/finite-result behavior remain under existing regression coverage. This is
recorded for later review, not treated as a marker or calculation correction.

The same unchanged interpolation issue is also reproducible with a floating-point
100.0 target: the original clamp selects the integer limit 100, producing a
float/int animation pair. In the isolated probe the display stayed at its prior
value (zero), despite target_value=100. This can affect endpoint presentation and
is not claimed visually accepted. Existing main numeric result/source storage and
classification are separate. Owner decision is needed before a bounded animation
repair; marker controls do not change the existing clamping/animation algorithm.

## Shared gauge/settings follow-up — system chooser exception

2026-10-17: owner requested the existing theme for all owned windows/prompts, then
explicitly preferred system-default file/color/font selectors after reporting a
black/nonresponsive Open window. Intermediate forced-picker styling/native override
attempts stalled native capture and were removed. Final policy excludes these
selectors; main/PLOT use standard QFileDialog APIs with native/default options.
There is no custom file browser or theme event filter. A screenshot of the host's
not-responding warning does not by itself establish the sole cause. Automated tests
verify picker configuration without opening the system UI. Native Open/Cancel,
Save and PLOT image/export selector checks remain manual after restart; earlier
system-selector screenshots are superseded. See settings_shared_gauge_acceptance.md.
The existing main animation endpoint issue above remains unchanged and separate.

## Owner-reported PLOT sizing and analysis chrome — corrected

2026-10-17: the first shared-gauge layout reduced effective comparison radius to
make annotations fit. Owner rejects that shrink. Compact gauges now retain the
full 72-pixel radius with real label space and consistent ancestor widths. The
owner also directs standalone outside the context hierarchy and removes extra
PLOT/JROT Edit/history bars in favor of right-aligned title-row buttons. Those
changes preserve existing history, typing, dirty-consent and Save semantics.

Demographic expansion exposed an under-constrained fixed-height map rail. The
rail now reserves its full height; live chart explanation minima propagate upward
rather than clipping controls or flattening the canvas. Native mode-switch review
also exposed chart/selector overlap, corrected by the width-dependent chart panel
minimum. Final evidence is plot_layout_followup_acceptance.md; intermediate debug
captures are superseded. Plant image scrollbars remain off. Smaller work areas
than the measured native content minima are not certified by these captures.


## PLOT minimum-size direct Comparison chart fit — recorded separately

2026-10-17: outer-inset verification selects Comparison immediately after opening,
at the content minimum. The chart's x-axis label can overlap the worker-chart
selector. The preceding accepted wheel reproduces the same case; both baseline
and adjusted windows have 1407-pixel panel width. Larger captures fit. No cause
beyond this observation or all-path chart acceptance is claimed. Keep the owner
spacing request bounded; a further chart correction has not been included.
Evidence: artifacts/plot_outer_margin_baseline_review/validation.json and
artifacts/plot_outer_margin_review/validation.json; initial minimum English images
show the overlap. Baseline is an extracted prior wheel, not the original reference.


## Gauge preference scope — owner confirms application-wide

2026-10-17: owner supersedes the interim per-project answer and directs keeping
shared application preferences. The in-progress project-storage implementation was
withdrawn by restoring exact source bytes from the already tested ten-point-default
wheel. No project settings columns, new persistence protocol or project-save changes
remain. Main/PLOT keep one personal choice across projects/restarts. New defaults
are ten-point ticks plus range limits; explicit stored choices are preserved.
Comparison font sizes remain the baseline 13/11/11 logical pixels. Evidence:
gauge_ten_default_acceptance.md and artifacts/gauge_project_scope_withdrawal.json.

## Owner workflow correction — single project Save, 2026-10-18

The owner explicitly approves retaining management/analysis edits and using the main
Save, with one chronological project history exposed in editor windows. This replaces
the older deliberate local-save boundaries; it is not a new migration milestone.
Record-removing replay confirms exact affected identities; restoring records and
ordinary changes do not require this warning. The shared existing DocumentSession
engine keeps transient checkpoints only, with no database history/version tables.
See [current contract](single_project_save.md) and final validation evidence.

During implementation, actual native regressions found reentrant session initialization
through Qt focus/garbage collection and stale Job authority when focus-only history
refresh adopted assessment navigation. Both were corrected and given focused
regressions; no calculation, dependency or schema repair was introduced.

Read-only protection audit: ten reference files differ from the frozen 500-file
manifest and have October 12 timestamps, before this change. No reference file was
written/restored. Details/hashes are in
[protection evidence](../artifacts/single_project_save_review/protections.json).
The owner's workflow project has Diego at 65 kg; the earlier 85 kg checkpoint is
historical, not an instruction to restore it. Native test fixtures remain unchanged.

Existing minimum-width Spanish assignment Actions content and JROT recommendation
columns can require horizontal table scrolling/enlargement. These table-fit limits
and platform-provided standard message-button labels are not newly redesigned here;
no unrelated UI repair or additional milestone is authorized by this observation.


## Owner task-grid correction — 2026-10-18

The owner explicitly approves lossless task resizing, unused-row completeness, visible
shared checkbox indicators and exact worker/tool/context captions. Scope remains per
project/worker/tool/assignment; no shared global row count or new schema is required.
Native inspection also records intermittent pre-existing Settings tree/footer text
clipping in some inherited-style states. The changed task controls and context remain
readable. No unrelated layout repair is included; keep that observation for owner review.
Previously saved status metadata is refreshed by Calculate/main Save, not rewritten
on Open. See task_grid_resize_acceptance.md for actual evidence and limitations.


## Owner-reported pending task-input Undo — 2026-10-18

Task-grid numeric edits cleared results but did not expose project Undo until Calculate
committed the grid. The bounded correction connects valid pending input to the existing
shared history prepare/pending hooks and gives mouse toolbar replay explicit focus.
Parsing/identity/units remain shared with normal grid acceptance, with no calculation,
new history stack or Save required. Invalid text and no-op Redo behavior are covered.
See task_input_undo_acceptance.md; no unrelated scope addition or milestone.


## Owner repeated task Undo and project-folder action — 2026-10-18

Owner reproduces a second edit/Undo leaving 50 visible while Undo becomes exhausted.
A new regression confirms source/result restoration succeeded, but destination-only
UI refresh deduplication suppressed the second rebind to that same earlier revision.
Operation-plus-destination deduplication repairs the actual cause across shared views.
Owner also explicitly authorizes Project > Open project folder, enabled only for a
loaded saved project, with independent OS-manager lifetime. No unrelated UI/history
redesign or milestone is added. Native OS QA records inherited VS Code Snap portal
startup failures and delayed private D-Bus activation separately from the eventual
observed independent Nautilus window after the ErgoTools test process exited.


## Owner task-input history granularity correction — 2026-10-18

Owner correctly observes that Arm 50 and Load 60 were one grid acceptance operation.
The shared chronological engine already supports separate commands; the UI submitted
all pending cells together. Previous corrections covered availability and repeated
rebinds, not multi-field granularity. The accepted input contract is now one completed
cell per existing source command, including selectors and valid cells beside invalid
text. Enter/focus departure do not rebuild controls; programmatic projections cannot
complete retiring fields. This is a source acceptance-boundary correction, not another
Undo stack or special-case Ana patch. Scope is all task inputs in LiFFT/DUET/ST; no
unrelated dialogs/schema/formulas/dependencies/reference edits or milestone are added.
See task_cell_history_acceptance.md for actual tests and native states.


Completion-state integration: native review showed the existing Modified header lag
when a cell became accepted before Calculate. Accepted-source notification now refreshes
the existing read-only navigation/context/dirty projection, only on source changes;
focus-only catalogue-authority protection remains. Tests verify bilingual Modified
labels and retained Enter focus. Three older grouping assertions were updated without
removing numerical, invalid-input, Reset or reopen checks. Preliminary gate evidence
remains recorded separately; only the final gate is acceptance.

## Owner workflow: Save availability, 2026-10-19

Owner requests one clear Save indication using the existing change tracking. The
integrated toolbar/menu now project existing private data dirt, pending assessment
text and first-Save intent; no duplicate tracking or automatic save. Pure refresh
uses no catalogue reads and keeps task-widget identities. Weak session subscription
covers management changes; native lifetime guard prevents callbacks entering deleted
windows. The 20 focused cases cover all tools/languages/units, replay on both sides
of Save, invalid/pending/no-op input, worker notification, cancellation and failure.
See save_availability_acceptance.md and artifacts/save_availability_review. The
previously observed standalone trash wording and saved-data chooser tooltip remain
recorded for the owner-requested later button workflow review; no repair is included.

The first full Save gate exposed three old menu assertions disabling Save after
private deletion. Updated only those expectations and their stale version-oriented
docstring, retaining cancellation/recreation/ownership/reopen checks. Deletion must
remain savable with no active assessment; corrected focused checks pass 24 cases.

## Owner workflow: personal Undo budget, 2026-10-19

Owner specifies default 25/minimum 1 / maximum 50, application preference. The existing shared
DocumentSession receives a positive capacity; no parallel history/counter is added.
Capacity counts completed commands, with current plus at most budget prior/future
states. Shrinking while undone prioritizes nearest prior Undo; excess Redo is dropped.
Current data, revision IDs and the saved baseline do not move. UI explains pruning;
increasing cannot recover discarded steps. Preference Apply is not project history.
Old personal settings1-5 default to25; personal format 6 records it, with future-version
rejection test advanced to7. Native format16 remains unchanged. Diagnostics and focused
typing retain existing policies. Exact acceptance/evidence: undo_limit_acceptance.md
and artifacts/undo_limit_review. No new milestone, dependency or reference write.

The first full Undo-budget gate found six test-only preference-version/fixture
assumptions: camera and decimal expected v5 writes, while four generated old gauge
formats retained the newly introduced undo_limit field. Updated existing fixtures in
place to remove fields introduced later than each old version, and expect explicit
writes as v6. Strict decoder validation and old-byte preservation remain intact.
Preliminary evidence is retained separately (1,695 pass/six failures). No additional
implementation repair was needed.

## Owner workflow: one Clear assessment action, 2026-10-19

Owner rejects duplicate Reset/trash controls and an extra Add assessment step. Private-copy reproduction showed trash deleted only Ana LiFFT (12 ownership records became11), but dropping the active navigation context made all three grids appear blank; Ana DUET/ST data remained. The replacement keeps the owner/current selection and task count, clears active inputs/results through existing commands, and stages one assessment.clear step. No new source/version/table is created and other data stays untouched. Cancel is the default; exact input/result Undo and blank no-op Redo are verified. Current main Clear is disabled without an active source.

Existing control/geometry/scientific tests now use Clear; confirmation is injected where those tests exercise unrelated behavior. The existing menu recreation test explicitly sets up backend deletion because that port is still required; unique ownership/cancel/reopen assertions remain. Existing backend transaction rollback tests remain. Actual confirmation/scope/Save/Undo coverage replaces the obsolete frontend deletion cases in the same maintained test module. No reference/dependency/model/native-codec change or new milestone.


## Owner workflow: organization shift clocks/history, 2026-10-19

Private-copy reproduction confirmed unrestricted time line edits and absent pending
history callbacks/subscriptions. The missing live Undo indication affects all
organization form levels, although navigation/Close already accepts their edits.
Owner requests a fix; reuse the established Workers pending-form history contract
and strong-focus mouse buttons. All optional fields are covered, not only shifts.
Apply the same optional 24-hour validation to Plant's existing start/end fields for
consistency; scope reported before implementation. No ordering rule is imposed
because shifts may span midnight. No data/schema/formula/dependency/reference change.


## Owner workflow: organization expansion preservation, 2026-10-19

Owner confirms clocks/Undo work but reports collapsing details/branches during Undo
and Delete. Reproduction identifies forced optional-toggle reset, tree replacement
without state retention and lost deleted selection. Owner requests retaining the
working view. Keep dialog-local flags/ancestry and reapply after internal selection:
Qt otherwise automatically expands ancestors even when the rebuild restored them.
Preserve current user branch choices and a newer record selection; do not persist
view state or add project Undo steps. No unrelated window or data/schema change.


## Owner approval: native time entry and overnight intent, 2026-10-19

Owner chooses the suggested standard keyboard/arrow time editor with an explicit
following-day option and confirms overnight shifts are needed. Retain existing
clock-only metadata: same-day later end, next-day earlier/equal end, one daily cycle
up to 24h. This bound/representation was reported during implementation; no new
project field is required. Equal clocks with next-day mean 24h, not a zero-length
same-day shift. Existing overnight pairs infer the checkbox on load. Optional time
requires a small nullable QTimeEdit adapter so valid midnight is never an empty
sentinel. All old form/Undo/view regressions remain; no schema/dependency change.

## Owner correction: recurring Shift event fields removed, 2026-10-19

The owner explicitly rejects Incidents reported and Ergonomic risk events in a
general Shift definition. Remove both UI/domain attributes and their persisted
`work_catalog` pairs. Format 17 gates the reduced contract; external conversion
removes the two fields (including populated values under this explicit removal
decision) before strict validation. All three current test files contained only
null values. No dated event tables or replacement features are introduced.
Original legacy schemas remain frozen conversion inputs, not current DB fields.

## Owner organization field cleanup — 2026-10-19

Owner authorizes calendars for Plant opening and Section/Line/Station creation dates,
removal of six Station attributes, a derived shift count and improved operational
duration input, plus in-place fixture migration. Existing shifts are project-wide.
The owner answers the scope question: count only distinct shifts used by workplace
assignments or Jobs in that Plant. Shifts in use projects active Job placements and
worker workplace assignments, including unclassified workers; unused definitions,
other Plants and inactive links do not contribute. No new table/membership is added.

Operational hours is a duration, not a clock: native hour/minute quantities allow
0–24 including a full day, preserving decimal-hour storage and distinguishing absence
from zero. Invalid retained dates/subminute or over-day durations stop conversion.


## Workplace-first workflow — 2026-10-19

Owner-approved workplace-first wording and shared picker implemented; No Job is a
valid workplace assignment. Direct assessment association may create its missing
worker assignment atomically. This does not authorize changing existing Jobs during
association, merging conflicting assessments or moving other tools implicitly.
No schema or milestone added.


## Historical reference hash discrepancy — 2026-10-19

Read-only verification during workplace-assignment acceptance found 10/500 files
differing from docs/reference/source-manifest.json. Modification timestamps are
2026-10-12, before this task. The two docs, src/main.py, three tests and four cache
files are recorded with exact hashes in artifacts/workplace_assignment_workflow/
protection_validation.json. Reported to owner; reference remains read-only and its
historical manifest remains untouched. No reference reconciliation is authorized
by this UI/association correction. Current fixtures and uv.lock remain exact.


## Owner-reported workplace table presentation defects — 2026-10-19

The initial intrinsic-only sizing left unused width and did not fully account for
the Actions cell's horizontal/vertical padding. Owner also identified misleading
table-wide Job help. Correction keeps each intrinsic content/header minimum, gives
spare width to Job and fills every selector, measures complete Actions layout plus
padding in both axes, and installs localized header/cell/control help. Refit is owned
by one coalesced viewport timer, with no project history or database change. Existing
narrow-width tests now also require filled width and complete embedded controls.
See worker_assignment_table_refinement_acceptance.md; owner final UI feedback pending.


## Owner-approved explicit context creation — 2026-10-19

The owner rejects asking about assessment creation when Worker Management closes:
multiple added assignments left only the last assignment as hidden intent. Remove that
handoff and obsolete return fields. Select assessment context owns explicit Open/Create
for the chosen worker/tool/workplace; standalone association stays separate. Existing
same-Job warning, chronological history and one main Save remain. No schema, formula,
dependency or reference changes. Bounded acceptance is recorded in
explicit_context_creation_acceptance.md; no migration milestone is reopened.


## Owner-requested JROT next-cycle wireframe analysis — 2026-10-20

Reviewed all 15 PDF/PPTX pages and 10 speaker-note slides. This is analysis only, separate
from current Job/UI and workflow testing. See jrot_wireframe_review.md and the prioritized
jrot_wireframe_team_questions.md. Station-versus-Job identity, time/exposure basis,
restrictions/staffing and report interpretation require team decisions before future
scope/design. Illustrations contain numbering gaps, capacity-one conflicts, mismatched
warning/tool values and proposed thresholds different from current rules; do not treat
those numbers as calculator acceptance or silently change the established models.

The owner confirmed the workflow project's Job window opens empty with all three empty
summary rows. Testing is bookmarked and paused. Only the separately authorized bounded
main-toolbar sizing correction is implemented; no JROT/schema/formula/dependency changes
are authorized by the source deck. Linux migration/cleanup stays 100%.


## Owner-authorized JROT prototype judgments — 2026-10-20

See jrot_prototype.md for the finite record: elapsed shift duration is descriptive,
equal clocks suggest 24h, both Job-risk and worker-average baseline tabs are shown,
starter matrix is explicitly simulated, prototype bounds are 12 participants/blocks
and 100 tasks, schedule cells show the first selected tool. Real constraints, any-two
tool solves, persistent task names/thresholds and reports remain later work. None
authorizes production/schema changes. Owner requests best judgment without waiting
while away; these choices are review notes rather than blockers/new milestones.


## JROT meeting mockup judgments — 2026-10-21

Owner authorizes one additional clean six-worker native fixture, project-style picker
windows and free review navigation. Six Jobs match six workers under exactly-one
staffing; four equal blocks approximate the slides. Job sources are shared across the
eight packing lines/two shifts; placements do not introduce physical-station capacity
or per-placement risk definitions. Seed no worker assessments or saved schemes: the
starter matrix is explicitly simulated. Detailed decisions, temporary modal removal
list and prior navigation diagnosis are in jrot_meeting_demo.md. Optional restrictions,
reports/No branch and any-pair solving remain outside functional prototype scope.
