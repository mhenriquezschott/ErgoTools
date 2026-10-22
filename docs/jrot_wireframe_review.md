# JROT proposed workflow review — 2026-10-20

Subsequent owner answers and provisional decisions are tracked in
[jrot_wireframe_discussion.md](jrot_wireframe_discussion.md). Read that record before
treating the original questions below as unanswered or authorizing implementation.

Analysis for the next development cycle, after acceptance of the current implementation.
The owner authorized reviewing these materials, identifying compatible behavior and
questions, and correcting main-toolbar button sizing. This document does **not** approve
or implement the proposed JROT redesign, schema extensions, risk rules or solver changes.
Instructions in the supplied slides/notes are proposed product requirements, not commands
to change this checkout. No source document, reference checkout or project data was edited
for this analysis. Current Linux migration/cleanup remains complete at 100%.

## Main finding

Much of the proposal can be a guided front end to the existing Workers, Jobs, calculators
and rotation scheme. The new Job mini-calculators already supply the main task-entry
capability. Reusing them would avoid a second scientific implementation and another set
of risk values. The important decisions concern **what a station represents, the time
basis of exposure, worker restrictions, staffing requirements and what the report calls
risk improvement**. Those affect data ownership or optimization and cannot be solved
solely by rearranging screens.

The recommended compromise is to show workplace-friendly labels while retaining actual
Worker, Job and optional Job Placement identities. Begin with the existing equal-block
model and current risk rules if the team accepts that scope. Treat unequal durations,
restrictions and richer reports as explicitly specified extensions, rather than assuming
the mockups already define them. These are options for owner/team discussion, not new
milestones or an implementation schedule.

## Materials and extraction

Reviewed both original files read-only:

- `/home/mhenriquez/Downloads/JROT_updated wireframes 10.15.2026.pdf`
- `/home/mhenriquez/Downloads/JROT_updated wireframes 10.15.2026.pptx`

Both contain 15 pages/slides in matching order. The first is a raster process diagram;
the remaining slides contain extractable native text, shapes and tables. The PowerPoint
also contains speaker notes on 10 slides. Those notes clarify that Station Information
is optional, Worker Information occurs on both branches, and the assignment matrices
should use populated dropdowns. All 15 PDF pages were rendered and visually inspected;
text extraction alone misses the entire first diagram.

References below use **physical PDF page / PowerPoint slide**, not printed screen or
flowchart numbers. The numbering differs: pages 8 and 9 both say Screen 6; Screen 10 is
absent; the flowchart refers to a Comparison Report on Slide 16 although the file ends at 15.
A separate Risk Preview appears in the flowchart but has no corresponding supplied UI.
These are specification gaps, not instructions to invent a screen.

Source hashes, text, notes, relationship-based slide order and rendered-page identities
are recorded in [the page inventory](../artifacts/jrot_wireframe_review/page_inventory.json)
and [source inventory](../artifacts/jrot_wireframe_review/pptx_inventory.json).
Arithmetic examples are in [consistency checks](../artifacts/jrot_wireframe_review/consistency_checks.json).

## Page-by-page interpretation

| PDF page | Proposed purpose | Fit with current implementation / decision needed |
|---|---|---|
|1|Seven-stage process overview: setup, assignments, tasks, validation, baseline, comparison, compliance report.|The navigation idea is reusable. Shift length, restrictions and compliance/report semantics require specification; no model is selected here.|
|2|Branching progression for active rotation versus no current rotation; optional unequal-block step.|Both branches can converge on a common schedule editor. Clarify the missing Risk Preview and inconsistent slide references.|
|3 / Screen 1|Active rotation: counts of workers, workstations and blocks; equal-duration choice.|Worker and block counts exist; workstation count must resolve real targets. No block durations are currently stored. Counts should derive from selected records rather than create anonymous duplicate records automatically.|
|4 / Screen 2|No rotation: counts plus desired future block count.|A full-shift assignment can be expanded across future equal blocks for comparison. This is an inferred compatibility option, not yet a specified baseline policy.|
|5 / Screen 3|Unequal block durations, minutes in 30-second increments.|New scheduling semantics, domain data and solver/report weighting. It is not the existing clock editor or Shift definition. A common-duration value is also missing from the equal-block branch.|
|6 / Screen 4|Station IDs and optional names; Add Station.|Physical stations already have full ancestry; names such as Wire cutting/Installation may describe Jobs. There is no separate optional Station Name field. Decide whether this selects organization Stations, Jobs, or a combined display. Notes explicitly call this page optional.|
|7 / Screen 5|Worker IDs and restricted stations; Add Worker.|Reuse existing Worker records and creation ports. No current typed station-exclusion, qualification or fixed-worker solver rule exists. “Restricted” and “fixed” need separate meanings and scope.|
|8 / Screen 6|Current worker-by-block station matrix.|Existing scheme/grid is a close fit once each choice identifies an actual Job/Placement. Notes request dropdowns. Editing this simulation must not silently rewrite permanent worker workplace assignments.|
|9 / Screen 6|One primary station per worker when no rotation exists.|Can collect a compact baseline and expand it for the same future horizon. Missing station for Worker 04 should remain absent and block solving, not become an implicit Job or zero risk.|
|10 / Screen 7|Station progress, DUET task grid, skip/next/finish.|Reuse JobTaskEditor, existing calculations and shared history. Task Name is new source metadata; per-tool selection/progress is new wizard presentation. Skip cannot mean zero risk.|
|11 / Screen 8|Same task flow for LiFFT.|Existing mini-calculator fits. Missing arm/load units must be supplied from explicit metric/imperial policy. Single-task damage 5.890 and total 0.13665 are not a coherent expected-calculation example.|
|12 / Screen 9|ST/TST task grid and in-place validation.|Reuse explicit ST direction convention, not a new “Lift” code mapping. Zero repetitions are shown as missing, conflicting with current zero-versus-absent semantics. Stale damage must not remain presented as a valid result after invalid edits.|
|13 / Screen 11|Baseline worker/station risks, warning and common thresholds.|Existing values/projections can feed a new view. Active-rotation baseline must summarize multiple blocks, rather than show one station per worker. Thresholds differ from current risk bands; warning's 68% is in the LiFFT column, not DUET.|
|14 / Screen 12|Suggested plan; fixed Station 03; Approve & Compare.|Preview and explicit Apply already exist. Fixed-worker constraints do not. The illustrated plan double-books Station 03 in blocks 2–4 under capacity-one semantics. Approval wording must not silently add profile/approval database lifecycle.|
|15 / Screen 13|Three-tool comparison, mean/max/SD/range, report save/PDF.|Existing comparisons can be reused; summary statistics and integrated report/PDF are new presentation/export work. The measure, population, units, baseline retention and compliance claim need definition. A lower overall mean is not generally produced by the present fixed-workload model.|

## Existing architecture and data that can be reused

| Proposed concept | Current authoritative representation | Reuse and boundary |
|---|---|---|
|Project / line setup|ProjectMetadata, WorkHierarchy and OrganizationRecord in current project tables.|Select a real line/shift when using physical stations. Existing organization-free All Jobs analysis remains useful; never manufacture Default organization to satisfy a wizard.|
|Worker|WorkerEntry / WorkerDetails in work_catalog.|Select/reuse literal IDs and existing demographics. New worker creation goes through normal application ports and shared project history. Counts are not identities.|
|Station|StationKey(Plant,Section,Line,Station), plus independent Shift context.|Station ID alone is not globally unique. The same displayed ST01 can exist under different lines. Full identity must survive dropdowns and persistence.|
|Job / activity|Job and optional JobPlacement at a real workplace/shift.|These are JROT's targets and current-risk owners. A Station can have multiple Jobs; a Job can have multiple placements. Simple one-Job-per-station screens can hide detail while retaining the actual identities.|
|Tasks and calculated values|One JobRiskMeasurement per Job/tool, optional source and exact task_results in risk_measurements.|Reuse direct entry, compact calculations and exact independent worker copying. Do not introduce station-risk duplicates or a second calculator result store.|
|Worker assessment|Worker/tool ownership with optional workplace assignment, separate source/result.|It can supply copied Job inputs/results. It must not be automatically linked to a Job or overwritten because a wizard edits a rotation.|
|Baseline matrix / proposed schedule|RotationScheme workers, Job/placement targets, ordered current cells, scope and provenance in rotation_schemes payload 2.|Use explicit ordinary schemes/previews. The current scheme has no durations, restriction set, persisted baseline link or report document. Adding those fields needs a designed codec/upgrade, even if no SQL table is added.|
|Navigation progress|Presentation/session state.|Derive completeness from selected tools and usable values. Avoid persistent “finished station” flags that become inconsistent with later edits. Persist resumable drafts only if explicitly required and designed.|
|Save and Undo/Redo|ProjectEditingSession / DocumentSession and the sole main Save.|Next/Finish validates/accepts edits privately; it does not introduce separate durable Save buttons. Export writes an external artifact and is clearly distinguished from saving the project.|

Source anchors: [Job ownership](../src/ergotools/domain/job_catalog.py),
[current risk/tasks](../src/ergotools/domain/job_risk.py),
[rotation scheme](../src/ergotools/domain/rotation_scheme.py),
[eligible pool](../src/ergotools/application/rotation_pool.py),
[task editor](../src/ergotools/presentation/desktop/job_task_editor.py),
[calculation/copy service](../src/ergotools/application/job_calculation.py),
[scheme codec](../src/ergotools/infrastructure/rotation_scheme_store.py) and
[current database contract](database_tables.md).

## Decisions that affect correctness

### Station, Job and independent assessments

The labels Wire cutting and Installation on page 6 describe activities as readily as
physical locations. If the team means an activity, Job.name already fits. If they mean
a physical station, its Job activity must also be resolved; show a Job selector when several activities
occur there. A dropdown can display “ST01 — Wire cutting” while storing the Job Placement;
this gives the simple screen they want without merging two different business records.

For the common one-activity-at-one-station case, an explicit setup operation could
create/select one actual Job and its actual placement. That must be visible and
confirmed, not an invisible default Job or a manufactured hierarchy. Organization-free
users can continue selecting Jobs directly. Creating genuine stations requires their
real parent hierarchy; the existing optional organization policy must remain intact.

Risks are currently Job-owned, not placement-specific. If the same Job is performed at
two stations with different forces, tasks or exposures, the team must decide whether
these are actually distinct Job definitions. Do not overwrite one shared Job's numbers
for another placement, add hidden per-station overrides, or restore risk profiles.
Worker assessments remain independent except for explicit existing copy operations.

The station “capacity” optional field is generic organization metadata, not an approved
staffing limit. It cannot silently become a solver worker-capacity parameter.

### Time blocks and the exposure model

RotationProblem and RotationScheme currently hold ordered blocks with **no durations**.
The optimizer's `_average` and result table use equal weighting. Shift start/end clocks
are recurring organization metadata; they do not determine schedule-specific paid time,
breaks, exposure duration or a task's repetitions/day basis. Plant operational hours
are a different quantity again.

Unequal durations therefore require more than a time widget. Define: total horizon,
positive block lengths, 30-second resolution, common duration for the equal branch,
overnight handling, breaks, and whether sum(block durations) includes or excludes breaks.
The page 5 example sums to 600.5 minutes; this would not fit the overview's illustrative
8-hour shift, if those examples are intended to describe the same case.

Most importantly, determine whether inputs represent full-day repetitions, repetitions
per particular block, or a rate. Existing direct Job probabilities may have no reference
duration at all. They cannot automatically become per-minute exposures.

Current JROT averages stored Job probabilities. An alternative that scales/combines task
damage by exposure time and then calculates probability is mathematically different:
`sum(w_j * probability(D_j))` generally differs from
`probability(sum(w_j * D_j))` because the existing damage-to-probability functions are
nonlinear. This is a scientific/model decision for the team, not an implementation
shortcut or permission to change formulas. Ask for a worked unequal-duration example
with expected task, Job, worker and report results before choosing either behavior.

### Restrictions, staffing and feasibility

The current solver enforces one target per worker/block, at most one worker per target/
block, and preservation of each target's total uses from the current schedule. There
are no worker-specific forbidden targets, fixed workers, qualifications, availability,
minimum staffing, rest transitions or maximum consecutive exposure constraints.
Only targets actually used in the current matrix enter the current optimization
problem. An extra low-risk Job merely present in the catalog is not automatically
available to replace that workload: its use count would otherwise change. The team
must specify whether idle/reserve activities and changed demand are permitted.

These concepts are distinct. “Worker 01 may not perform Station 01” does not mean “Worker 03
must stay at Station 03.” A fixed worker should consume the station's capacity in every
fixed block. Page 14 assigns Worker 03 to Station 03 throughout, while also assigning:

- Worker 02 to Station 03 in block 2;
- Worker 01 to Station 03 in block 3;
- Worker 05 to Station 03 in block 4.

This example is infeasible for capacity one. If multiple workers are intended, the
requirements must say so. There is an additional integration issue: current capacity is
per **Job/placement target**, not a single shared physical-Station capacity across several
Jobs. A station-level rule may need grouping by full Station/Shift identity.

Restrictions need explicit scope: project-wide, worker/Job, worker/station/shift, or
specific rotation scheme. A scheme-local constraint set is a possible minimal extension
for one planning scenario; it is not yet approved. Do not put restriction IDs or medical
facts into free-text worker notes. Persist only necessary operational restrictions after
the team defines them. Infeasible problems must not be “fixed” by silently dropping a
restriction, changing staffing, assigning unknown zero-risk rest, or changing backends.

### What optimization can improve

The current single-tool objective minimizes the **maximum worker average** probability.
Multi-tool solving first minimizes the sum of the three per-tool worker ceilings, then
reduces the sum of ceiling-to-floor spreads while retaining the first-stage ceilings.
CBC and HiGHS routing, explicit preview/Apply and solver status already exist.

With equal blocks, unchanged workers and preserved target counts, the overall mean of
worker averages is invariant:

`population_mean = sum(target_use_count[j] * risk[j]) / (workers * blocks)`.

For example, two Jobs at 10% and 90% can change worker averages from (10, 90) to (50, 50).
The maximum improves from 90 to 50 and the spread narrows, while the mean stays 50.
This is a useful outcome and must not be reported as a failed optimization.

Consequently, the report's mean 44.0%→36.3% cannot be promised from the current model
under those assumptions. A reduction may require a different exposure calculation,
changed task values, changed workload/time or a different measured statistic. It must
be explained rather than obtained by relabeling the existing average. A complete
balanced four-station cycle such as page 8 already gives each worker the same exposure
under the current equal-average model; using page 13's first four LiFFT values gives
41.5% for every worker. No strict improvement is guaranteed.

Current Job/station hazard values also do not fall simply because workers rotate.
Separate unchanged Job hazards from the distribution of worker schedule exposures.

Source: [optimizer](../src/ergotools/infrastructure/pulp_rotation_optimizer.py),
[problem contract](../src/ergotools/domain/rotation.py) and
[result averaging](../src/ergotools/presentation/desktop/rotation_result_table.py).
The arithmetic checks verify internal consistency, not clinical validity of a new model.

### Selected tools, missing data and validation

Single-tool optimization currently needs complete matching values only for that tool;
all-tool optimization needs all three tools for every scheduled target. “Skip assessment”
can mean “not part of this analysis” or “enter later”; neither should manufacture 0%.
Keep these meanings visible and disable only operations that require missing values.
The current comparison of other tools also requires their values; an incomplete tool
must be shown unavailable rather than assumed safe.

Zero repetitions and absent repetitions are distinct in current task validation. Page 12
marks 0.0 as missing. If the team wants to disallow zero in a new planning workflow, that
is an explicit new validation policy, not an interpretation of the present data. Unused
blank rows should continue to be ignored; entered incomplete rows need field-specific
messages. After input changes, derived totals/progress/previews must become stale or
unavailable until a matching calculation exists.

LiFFT/ST lever and force fields need cm/N or in/lbf labels and the existing conversion
rules. Load must not silently become kg mass. ST/TST naming can be a presentation alias;
its saved direction convention and all original branch calculations must survive. The
mockup's “Lift” type needs an explicit mapping to the existing task categories.

Task Name is not a current field of the three source DTOs. It is a reasonable optional
addition if approved, but stable task IDs remain separate. Clarify whether a named task
is independently entered for each tool or shared across tools. Retaining names requires
source codecs, Job/worker copy, task editing, Undo/Redo, exports and external conversion
to agree; it is not just an extra display column. Do not introduce a task catalog/table
unless a real shared-task requirement is established.

### Baseline, proposed plan, thresholds and reports

For “no current rotation,” a compact primary-Job form can expand assignments over the
planned equal blocks to construct a comparable baseline. Keep the same workers, horizon
and workload. Do not optimize a one-block problem and imply it represents a future
multi-block rotation. Existing workplace assignments may prefill suggestions, but
accepting a plan must not change those permanent records without an explicit operation.

Current preview/Apply can support “Review plan / Use this plan.” Prefer that wording to
“Approve” unless a formal approval process is genuinely required. Formal approval,
approver identity, audit status and historical profile snapshots are outside the owner-
approved current model. A proposal should remain separate from its baseline until Apply;
if both must survive reopen, define their scheme identities and relationship explicitly.
Do not overwrite the baseline when navigating to Compare.

The page 13 common bands (0–25%, 25–50%, 50–75%, 75%+) differ from current LiFFT's visible
0–25%, 25–37.5%, 37.5–50%, >50% bands and existing tool-specific damage coloring. Copying the
mockup colors would be a risk-classification change. Define measure, tool, exact boundary
inclusivity and scientific basis first; the current rules remain the compatibility option.
No averaged percentage is automatically an individual worker injury probability.

Report fields need explicit populations and formulas: worker schedule averages versus
individual cells or intrinsic station values; per-tool versus combined result; population
versus sample SD; count and denominator above threshold; treatment of missing tools.
“Risk range” should state max−min. A difference 44.0%→36.3% is −7.7 percentage points,
whereas its relative change is −17.5%. Do not label both as −7.7%.

A new report can read the existing calculation/comparison values and export through an
adapter. No report-history table is needed for a simple external file. Current schemes
resolve current Job values, so an exported historical report should include its actual
values, units, scope, analysis assumptions, generation time and solver status. Reopening
a scheme is a current reevaluation, not a way to reproduce old report numbers after
Job edits. If reproducibility inside projects is required, that is an additional explicit
requirement; it must not quietly restore rejected Job-profile/evidence history.

“Compliance report” on page 1 has no named standard, jurisdiction or approval rule.
Recommend “Rotation analysis report” until the team identifies what compliance means.
Generating a PDF is a separate export feature; this review adds no dependency or engine.

## Proposed compatibility approach for discussion

The six navigation sections are useful: Setup, Assignments, Task values, Baseline,
Optimization and Comparison/Export. Use one owned Qt window with pages, reused task
editors and shared project history. Allow Back/sidebar navigation without losing valid
inputs; show errors beside the relevant fields and derive progress from actual data.
Large matrices/task grids need ordinary scrolling and keyboard editing. Keep native
file dialogs and the established visual theme. Wizard navigation is not another Save.

Offer existing records first. In a simple station-oriented presentation, display the
full station context plus Job activity, retaining full IDs. Organization-free users
choose Jobs directly. Reuse direct values and worker-copy options rather than force
users through every calculator. Existing complete data should bypass unnecessary
entry pages while still showing their source units and current values.

Under an initial compatibility option, use equal blocks, existing objectives/thresholds,
no newly invented restrictions, and truthful comparison statistics. Clearly label any
unsupported duration/restriction requirements rather than pretending those controls
work. The team may instead require these extensions together; that needs agreement
before a development plan, data model or migration is authorized.

After that agreement, extend only the contracts with an actual requirement: optional
source task labels, schedule durations/exposure basis, operational restrictions and
staffing limits, and explicit baseline/candidate retention if required. Existing
rotation JSON payload storage may accommodate schedule-owned fields with a new codec
and external migration; separate SQL tables are not automatically necessary. Schema,
conversion and ownership design must follow the final agreed semantics.

## Future acceptance cases to request with the specification

These are proposed tests for a later authorized implementation, not tests claimed passed
by this analysis:

| Case | Required expected behavior |
|---|---|
|Existing Jobs/workers; no organization|Reuse real records and current values; no artificial hierarchy or duplicates.|
|Two lines both contain ST01|Choices and saved targets remain distinct by full context.|
|Two Jobs at one station / one Job at two stations|Risk ownership stays explicit; any shared physical capacity is enforced separately.|
|Active rotation, equal blocks|Current native-19 fixture results/arrangements remain equivalent under the compatibility model.|
|No rotation; future four blocks|Baseline expands primary assignments over the same horizon/workload before comparison.|
|Unequal blocks / breaks / overnight|Use the team's worked time/exposure example; all displayed and solver quantities agree.|
|Forbidden station, fixed worker, no feasible staffing|Never violate constraints silently; fixed workers consume capacity; report infeasibility.|
|More/fewer workers than targets / parallel Jobs|Apply specified vacancies, idle/rest and capacity semantics, with no invented zero-risk task.|
|Selected one tool; other tools skipped|Single-tool solve remains possible; unavailable comparisons are explicit.|
|Zero, absent and partial task inputs|Preserve distinctions; show field-specific messages; unused rows do not create incompleteness.|
|Metric/imperial and EN/ES|Same exact source meaning/results; explicit force units and ST direction convention; localized captions.|
|Copy worker data, then edit either side|Retain names if added, exact task inputs/results and independence, with no new ownership link.|
|Back, Add/Remove, Clear, Cancel, Undo/Redo|One shared timeline per accepted edit; no extra durable Saves or lost pending inputs.|
|Change task data after preview|Invalidate derived baseline/preview/report availability according to the agreed rule; explicit rerun.|
|Balanced cycle / unchanged optimum / infeasible / timeout|Report valid outcomes and solver status; do not promise strict mean reduction or silently relax constraints.|
|Baseline and candidate after Save/reopen|Preserve the explicitly agreed identities, arrangements and current-value policy without risk profiles.|
|PDF/other export|Check arithmetic, per-tool measures, percentage points, theme/layout, units, solver status and threshold explanations.|
|Upgrade existing files|Private-copy conversion; exact worker/Job/source/result/image/schedule preservation; integrity/FK/rollback/Save As/backup tests.|

## Review outcome and boundaries

The materials are sufficiently readable to support this review. They are a useful
workflow proposal, but they are not yet an implementable optimization specification.
The accompanying [team questions](jrot_wireframe_team_questions.md) prioritize the
semantic decisions and request one internally consistent example for each branch.
No JROT implementation, database change, formula change or new dependency follows
from this analysis. The only code correction in this session is the separately verified
main-toolbar sizing change. Job UI and four-worker workflow testing remain paused at
the owner's confirmed empty Job window, ready to resume later.
