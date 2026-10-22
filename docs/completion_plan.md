> Superseded for future execution/progress by [finish_plan.md](finish_plan.md)
> and [finish_progress.json](finish_progress.json), pending owner approval.
> The following is historical; its rolling F batches and stale remaining entries
> are not authorization to continue implementation.

# Completion plan and fixed progress baseline — 2026-10-10

This initial scope review paused implementation at F144. It answered the owner's request
for a bounded completion plan and measurable remaining work. No application,
reference file, dependency or environment was changed. Evidence is current code,
checkpoint records and tests already recorded at F144; no suite was rerun for
this documentation-only review.

## What the F numbers mean

The accepted plan has seven stages (0–6) in
[modernization-plan.md](reference/modernization-plan.md#ordered-stages).
F1–F144 are sequential implementation/check/audit checkpoints, planned in small
slices as the work proceeded. They were not a fixed 144-step list defined at the
start. Calling every F a milestone and reporting four F numbers as a measure of
scope completion was misleading. F142, for example, was a characterization audit
that needed no production change. Checkpoint count, Python-file count, test count
and coverage percentage do not measure application completion.

The architectural/staged plan exists and substantial code implements it, but a
current weighted feature/acceptance ledger should have been maintained earlier.
Older STATUS entries also contain historical pending lists; they are not the
current backlog. This document supersedes those lists for progress reporting.
It does not change the agreed product, UI, dependency or solver requirements.

## How progress is calculated

There are **23 bounded deliverables totaling 100 scope points** below. Weights
reflect relative scope and are engineering judgments, not measured hours.
Each deliverable earns four cumulative gates, each worth 25% of its weight:

1. **G1 — characterized:** original behavior, target boundary and acceptance
   criteria are documented.
2. **G2 — implemented:** modern code and focused regression coverage exist for
   the established slice. An unresolved calculation path prevents G3, even if the
   isolated formula module is implemented.
3. **G3 — usable workflow:** applicable integrated persistence, failure, units,
   language and history checks pass. A window merely opening is insufficient.
4. **G4 — accepted:** required final matched-input/reference visual and workflow
   checks for that deliverable pass, and its intentional differences are approved
   or resolved. Infrastructure-only rows use their applicable architecture,
   baseline/resource acceptance instead of UI comparison.

`completion = sum(weight × gates_complete / 4)`

`remaining = 100 − completion`

A failed or unverified criterion cannot earn credit. The same concern is scored
once: e.g. fresh calculation gates in C1/C3, platform packaging in H2, final
cross-feature scenario in G3. Individual final parity checks and the final
cross-feature acceptance run are different requirements. G3 credit in an existing
row describes its tested slice; G4 still requires final reference acceptance.

**Baseline: 70.25 points complete; 29.75 points remaining. Report this as roughly
70% complete / 30% remaining**, not a precise time forecast. This replaces the
withdrawn 67% estimate. It is an auditable initial scope estimate, not a claim that
70.25% of development hours have elapsed or that all unknown defects are known.
The weights were set in this review and have not been empirically calibrated.

Do not increase the percentage for a new test, cosmetic fix or F checkpoint by
itself. Credit changes only when a listed gate closes with evidence. Weights and
scope stay fixed; a newly discovered issue is assigned to an existing row. A real
new requirement needs an explicit scope-change entry showing the old/new total
and its effect on the estimate. Reopening a failed gate reduces credit visibly.

## Current position by work area

| Area | Scope points | Earned | Remaining |
|---|---:|---:|---:|
| Foundation and feature audit | 10 | 8.5 | 1.5 |
| Projects and original-data compatibility | 10 | 7.5 | 2.5 |
| Three assessments and shared editing | 20 | 12 | 8 |
| Workers, organization and Jobs | 15 | 11.25 | 3.75 |
| PLOT | 15 | 11.25 | 3.75 |
| JROT | 15 | 11.25 | 3.75 |
| Shared UX and full integration | 10 | 6.75 | 3.25 |
| Documentation and native delivery | 5 | 1.75 | 3.25 |
| **Total** | **100** | **70.25** | **29.75** |

## Deliverable ledger and exact work remaining

A score of 75% means implemented and workflow-tested, with final acceptance open.
It does not mean that one quarter of the code still needs writing. Conversely,
C1/C3 are genuine unfinished functional paths, not just screenshot checks.

| ID | Deliverable | Weight | Gates | Earned | Remaining exit criteria and evidence |
|---|---|---:|---:|---:|---|
| A1 | Architecture, standards and automated gates | 4 | 4/4 | 4 | No new framework work; retain gates on actual changes. Evidence: [docs/coding_standards.md](docs/coding_standards.md); [tools/check_architecture.py](tools/check_architecture.py); [docs/f144_validation.json](docs/f144_validation.json). |
| A2 | Approved runtime, packaged assets and replaceable adapters | 3 | 4/4 | 3 | Retain exact baseline and adapter boundaries; native delivery is H2. Evidence: [docs/development.md](docs/development.md); [src/ergotools/presentation/desktop/rendering/vtk_body_renderer.py](src/ergotools/presentation/desktop/rendering/vtk_body_renderer.py); [docs/f144_validation.json](docs/f144_validation.json). |
| A3 | Feature/behavior ledger and code documentation review | 3 | 2/4 | 1.5 | Close source-to-feature inventory, hidden-data handling, remaining intentional differences and public-API documentation review; give each an explicit disposition. Evidence: [docs/reference/modernization-plan.md](docs/reference/modernization-plan.md); [docs/architecture.md](docs/architecture.md); [docs/review_register.md](docs/review_register.md). |
| B1 | Project lifecycle, transfer and assessment CSV compatibility | 6 | 3/4 | 4.5 | Resolve reference CSV versus new CSV differences (cached results, added fields, precision/clipping); verify agreed Save/Save As/backup/transfer behavior and round trips on copied data. Evidence: [docs/STATUS.md](docs/STATUS.md#f87-historical-checkpoint); [docs/assessment_export.md](docs/assessment_export.md); [tests/test_summary_export.py](tests/test_summary_export.py). |
| B2 | Original-project conversion, historical ownership and evidence | 4 | 3/4 | 3 | Complete final reference-to-converted feature acceptance including archived fields and output identity; retain original files unchanged. Evidence: [docs/f140_legacy_compatibility.md](docs/f140_legacy_compatibility.md); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md); [src/ergotools/infrastructure/legacy_conversion.py](src/ergotools/infrastructure/legacy_conversion.py). |
| C1 | LiFFT calculation and integrated UI | 6 | 2/4 | 3 | Close the fresh metric calculation gate with explicit original-behavior policy and matched vectors; then Calculate/Save/reopen/export in both units and final original-layout comparison. Evidence: [src/ergotools/application/assessments/evaluation.py](src/ergotools/application/assessments/evaluation.py); [tests/test_lifft_calculation.py](tests/test_lifft_calculation.py); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| C2 | DUET calculation and integrated UI | 4 | 3/4 | 3 | Complete same-platform original-window/control/behavior acceptance; address actual observed differences only. Evidence: [tests/test_duet_calculation.py](tests/test_duet_calculation.py); [docs/STATUS.md](docs/STATUS.md#f80-historical-checkpoint); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| C3 | Shoulder Tool calculation and integrated UI | 6 | 2/4 | 3 | Reconcile the remaining fresh-ST gate with the now-preserved reference direction convention and metric policy; complete Calculate/Save/reopen/export and final original-layout comparison. Evidence: [src/ergotools/application/assessments/evaluation.py](src/ergotools/application/assessments/evaluation.py); [docs/f137_legacy_compatibility.md](docs/f137_legacy_compatibility.md); [tests/test_tst_calculation.py](tests/test_tst_calculation.py). |
| C4 | Shared task editing, context selection, versions and history | 4 | 3/4 | 3 | Verify final worker/context/version navigation, task-count/reset/delete and keyboard/modal behavior against original; inspect expanded assessment picker. Evidence: [docs/STATUS.md](docs/STATUS.md#f85-historical-checkpoint); [tests/test_desktop_legacy_open.py](tests/test_desktop_legacy_open.py); [docs/f143_legacy_compatibility.md](docs/f143_legacy_compatibility.md). |
| D1 | Worker directory, optional details and assignments | 6 | 3/4 | 4.5 | Final original-form comparison including optional/selected/empty states, height/weight units and assignment behavior. Hidden experimental data disposition is A3, not a new visible UI. Evidence: [src/ergotools/presentation/desktop/worker_management_dialog.py](src/ergotools/presentation/desktop/worker_management_dialog.py); [tests/test_worker_management.py](tests/test_worker_management.py); [docs/STATUS.md](docs/STATUS.md#f72-historical-checkpoint). |
| D2 | Organization hierarchy and shifts | 4 | 3/4 | 3 | Final original-form comparison and accepted create/edit/delete/shift workflows on copied data. Evidence: [src/ergotools/presentation/desktop/organization_dialog.py](src/ergotools/presentation/desktop/organization_dialog.py); [docs/STATUS.md](docs/STATUS.md#f73-historical-checkpoint). |
| D3 | Jobs, placements and risk-profile lifecycle | 5 | 3/4 | 3.75 | Final original-form/workflow comparison for profile versions, approval/current/retirement and placement relationships. Evidence: [src/ergotools/presentation/desktop/job_management_dialog.py](src/ergotools/presentation/desktop/job_management_dialog.py); [docs/job_risk_lifecycle.md](docs/job_risk_lifecycle.md); [docs/f140_legacy_compatibility.md](docs/f140_legacy_compatibility.md). |
| E1 | PLOT scope, demographics and three risk views | 5 | 3/4 | 3.75 | Final original comparison of counts, missingness, filters and Individual/Job/Comparison results on matched copied inputs. Evidence: [docs/STATUS.md](docs/STATUS.md#f105-historical-checkpoint); [docs/STATUS.md](docs/STATUS.md#f116-historical-checkpoint); [tests/test_plot_results.py](tests/test_plot_results.py). |
| E2 | PLOT maps, markers and worker/job controls | 5 | 3/4 | 3.75 | Final map/marker/save/load/selection comparison; dormant Plant transforms remain archived, not activated. Evidence: [docs/f142_legacy_compatibility.md](docs/f142_legacy_compatibility.md); [docs/STATUS.md](docs/STATUS.md#f110-historical-checkpoint); [docs/STATUS.md](docs/STATUS.md#f117-historical-checkpoint). |
| E3 | PLOT charts, details and exports | 5 | 3/4 | 3.75 | Final original chart/settings/details/export comparison including units, language, selected and empty states. Evidence: [docs/STATUS.md](docs/STATUS.md#f114-historical-checkpoint); [docs/STATUS.md](docs/STATUS.md#f118-historical-checkpoint); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| F1 | JROT scope, schedule editing and persistence | 6 | 3/4 | 4.5 | Final original-form/scope/grid comparison, saved profiles/assignments and R006 Spanish scope-summary clipping. Evidence: [docs/STATUS.md](docs/STATUS.md#f124-historical-checkpoint); [docs/f133_legacy_compatibility.md](docs/f133_legacy_compatibility.md); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| F2 | JROT single-tool CBC and comparison/apply | 4 | 3/4 | 3 | Final matched-input feasibility/objective and comparison/Apply/Save acceptance; do not require identical alternate optima. Evidence: [docs/STATUS.md](docs/STATUS.md#f125-historical-checkpoint); [src/ergotools/infrastructure/pulp_rotation_optimizer.py](src/ergotools/infrastructure/pulp_rotation_optimizer.py); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| F3 | JROT multi-tool HiGHS and comparison/apply | 5 | 3/4 | 3.75 | Final two-stage objective/provenance and comparison/Apply/Save acceptance. CBC single / HiGHS multi; no GLPK. Evidence: [docs/STATUS.md](docs/STATUS.md#f126-historical-checkpoint); [src/ergotools/infrastructure/pulp_rotation_optimizer.py](src/ergotools/infrastructure/pulp_rotation_optimizer.py); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| G1 | Cross-app localization, unit projection and decimal input | 4 | 3/4 | 3 | Close full EN/ES text/tooltip/dialog review and mixed-unit save/reopen/export acceptance. Calculation gates count only in C1/C3. Evidence: [docs/STATUS.md](docs/STATUS.md#f94-historical-checkpoint); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md); [tests/test_model_units.py](tests/test_model_units.py). |
| G2 | Avatar, gauges, resizing and desktop interaction | 3 | 3/4 | 2.25 | Final original size/DPI/font comparison, VTK/camera, tab/keyboard and no-clipping states. Platform-specific checks count in H2. Evidence: [docs/STATUS.md](docs/STATUS.md#f81-historical-checkpoint); [docs/STATUS.md](docs/STATUS.md#f96-historical-checkpoint); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| G3 | Complete comprehensive-project acceptance | 3 | 2/4 | 1.5 | One complete copied-project run including fresh calculations for all tools, management changes, PLOT, both JROT paths, save/export/backup/reopen and original comparison; gates prevent claiming this today. Evidence: [docs/f140_legacy_compatibility.md](docs/f140_legacy_compatibility.md); [docs/f144_legacy_compatibility.md](docs/f144_legacy_compatibility.md). |
| H1 | Current user/developer/recovery documentation | 2 | 2/4 | 1 | Update operational guide from final app; retire stale preview guidance, document import/restore and remaining behavior decisions; verify actual Help launch. Evidence: [docs/development.md](docs/development.md); [src/ergotools/presentation/desktop/manual_launcher.py](src/ergotools/presentation/desktop/manual_launcher.py); [docs/final_targets.md](docs/final_targets.md). |
| H2 | Clean native installation and supported-platform acceptance | 3 | 1/4 | 0.75 | Native distribution/launcher/resource/solver/offline/restore checks on Linux and supported Windows/macOS targets. Current approved desktop extra is Linux-only; versions on new targets still require approval. Missing hardware blocks acceptance, not implementation progress elsewhere. Evidence: [pyproject.toml](pyproject.toml); [docs/development.md](docs/development.md); [docs/reference/modernization-plan.md](docs/reference/modernization-plan.md). |

## Priority and finish sequence

1. **Complete functional gaps first (C1/C3/B1/G3).** Fresh metric LiFFT and all
   fresh ST calculations are still blocked in application evaluation. F137
   resolved reference ST selector interpretation; it did not remove that gate.
   Reconcile the remaining gate with preserved reference behavior. Validate
   existing formulas; do not silently introduce a scientific correction. Present
   a concrete decision only if compatibility cannot proceed without one. Finish
   calculation-to-save/reopen/export behavior and the CSV compatibility decision.
2. **Close original-window acceptance (C4/D/E/F/G1/G2).** Use original control and
   layout code as the primary reference, with matched same-platform size/DPI/font
   views for verification. Fix actual differences inside the corresponding row.
   Include expanded/selected/empty/populated/error states, R004 popup verification
   and R006 Spanish JROT scope-summary clipping. Existing windows are already
   implemented; this is comparison/correction work, not rebuilding them all.
3. **Close the comprehensive application scenario (G3/B2).** Finish the whole
   copied-project sequence after fresh calculations work, comparing original and
   migrated data/results. F140/F144 already prove many integrated paths, including
   actual CBC/HiGHS Apply/Save/backup; they do not prove every final workflow.
4. **Close inventory/docs and native delivery (A3/H).** Classify all remaining
   original active entry points, preserve dormant data, update user/recovery
   documentation, and test clean native delivery on supported platforms. Native
   hardware/runtime unavailability is a named acceptance limitation, not grounds
   to claim completion. Future mobile UIs or replacing VTK are outside this job.

Planned next checkpoints, before any implementation resumes:

| Checkpoint | Work package | Concrete exit |
|---|---|---|
| F145 | C1 | Reference-compatible fresh metric LiFFT path or an exact documented owner decision preventing it; focused calculation/save/reopen evidence. A blocked decision does not earn G3. |
| F146 | C3 | Reference-compatible fresh ST path using established direction convention and metric policy; focused calculation/save/reopen evidence. |
| F147 | B1 | CSV compatibility resolved and tested on saved/copied data, including recorded evidence and status/precision policy. |
| F148 | G3 | Integrated fresh-calculation/save/export/reopen scenario across all three tools and copied-project features; update earned gates, without claiming final UI/platform acceptance. |

These are planned checkpoint scopes, not a promise that each takes one turn or
that four checkpoint numbers automatically earn four gates. If a scope cannot
close, report the exact unfinished criterion instead of substituting unrelated
micro-work. Further four-checkpoint batches must identify the existing row and
exit criterion before work begins. The end is all 23 deliverables at G4, with
explicitly approved exclusions recorded; no F-number target defines the end.

## Scope findings that do not justify new features

- Original main.py Cut/Paste and Export/Export As handlers show placeholder
  messages; the actual supported data export is exportToCSV. Do not invent new
  project-report/export engines to fill those placeholders. Compare the supported
  CSV behavior and document the approved menu changes.
- Original worker_window.py constructs experimental Head/Neck, Upper Body and
  Lower Body tabs and then hides tabs from index 2 onward. A3 must classify their
  stored-data handling; do not add new visible measurement forms without approval.
  Ordinary height/weight fields are already implemented and use unit conversion.
- F142 proved the active PLOT image loader does not apply dormant Plant transforms.
  Their archive preservation does not require a new transform editor.
- New findings are expected in a migration, but they belong to finite acceptance
  criteria above or the review register. They do not create unlimited infrastructure
  work, automatic new features or an ever-growing denominator.

## Evidence and reporting discipline

The authoritative machine-readable ledger is [progress_baseline.json](progress_baseline.json).
At F144, 1,095 tests passed with 96.45% statement/branch coverage and required code,
architecture/build checks. Native packaged EN/ES copied-project checks passed.
This review rechecked all 500 reference file hashes and the dependency lock, and
checked that the evidence paths above exist; it did not repeat application tests.

Future updates report: rows/gates closed; evidence; completed/remaining points;
concrete next exits; and blocking decisions if any. A time-based finish forecast
needs comparable throughput on these remaining work packages; past F counts were
unequal and are not a defensible schedule. Report scope progress now instead of
leaving the percentage indefinitely unestimated.


### F145 credit update

C1 G3 closed with f145_compatibility.md evidence. Current score: 71.75/100 complete; 28.25 remaining. Weights remain fixed.


### F146 credit update

C3 G3 closed with f146_compatibility.md evidence. Current score: 73.25/100 complete; 26.75 remaining. Weights remain fixed.


### F147 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 73.25/100 complete; 26.75 remaining. Weights remain fixed.


## Ordered checkpoints after F148 — existing acceptance rows

| Checkpoint | Existing row(s) | Concrete exit |
|---|---|---|
| F149 | G2 | Isolate and fix R007 main-window rendering/resize states using original code constraints; inspect full labels, VTK, cards and bottom controls at minimum/enlarged sizes. No general refresh framework. |
| F150 | B1/C4 | Match original Calculate/Save/export/reopen for unchanged imported inputs (R008), keeping original archive and fresh saved-result provenance distinct; focused failure/pending-source regressions. |
| F151 | C1/C2 | Compare integrated LiFFT/DUET controls, layout and workflows against original code at matched dimensions/inputs, including metric/imperial labels, incomplete grids and saved result behavior. Earn G4 only for all satisfied criteria. |
| F152 | C3/C4 | Complete original ST/control/context comparison and expanded assessment selection verification, retaining direction conventions, localization and modal behavior. Record any remaining criterion explicitly rather than substituting infrastructure work. |

These packages close existing acceptance criteria. They add no scope points or
new product features. Subsequent management/PLOT/JROT final acceptance, docs and
native platform delivery stay in the 23-row ledger.


### F148 credit update

G3 G3 closed with f148_compatibility.md evidence. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### Owner pacing update — F149

The owner now requests ONE milestone at a time until instructed otherwise.
F149 is the only implementation checkpoint authorized for this turn. The F150–F152
rows above remain ordered upcoming work, not an instruction to execute a batch.
This supersedes the previous four-checkpoint pacing and does not change scope.


### F149 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### F150 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### F151 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### F152 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### Current owner pacing — F150–F152

The latest owner instruction supersedes the F149 one-checkpoint limit: work THREE
milestones at a time until changed. The ordered F150–F152 batch is complete as
bounded implementation/comparison checkpoints. It does not close every final gate
in B1/C1/C2/C3/C4. Weights and earned gate credit remain 74/100.

### Next bounded batch — existing remaining criteria

| Checkpoint | Existing rows | Concrete exit |
|---|---|---|
| F153 | B1/C4 | Close calculated-result persistence during dirty document/context switching, plus Save As success/failure acceptance, without changing modal ownership or adding background infrastructure. |
| F154 | C1/C2/G1 | Complete populated original integrated LiFFT/DUET result-path comparison in both units, including saved-result source/display labels and summary placement. Record exact unresolved differences; award G4 only on complete acceptance. |
| F155 | C3/C4 | Complete populated ST and context/version/reset/count/delete acceptance against the original workflows; preserve direction conventions and reuse the verified readable picker. |

Management/PLOT/JROT/platform/documentation final acceptance remains in the fixed
23-row ledger. These checkpoints close existing criteria; no new product scope.


### F153 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### F154 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### F155 credit update

No additional gate credit: this closes part of an already scored workflow. Current score: 74/100 complete; 26 remaining. Weights remain fixed.


### F153–F155 batch disposition and next bounded batch

F153 completes dirty-transition Save and Save As persistence/failure acceptance.
F154/F155 restore verified live inline summaries and compare all three tools'
matched metric/imperial result paths. F155 also corrects ST's output-unit header
and exercises versions, currentness, closed-context loading, Reset/Undo, task
count and exact confirmed deletion. No complete-window G4 credit: spelling,
whole-window proportions/text and final comprehensive/platform acceptance remain.
The score is still 74/100; checkpoints are not percentage increments.

| Checkpoint | Existing row | Concrete exit |
|---|---|---|
| F156 | D1 | Original Worker Management populated/selected/optional/empty form comparison; height/weight projections, assignment edits and Save/reopen on disposable data; fix observed deviations only. |
| F157 | D2 | Original organization hierarchy/shifts form and create/edit/delete/selection comparison, EN/ES states, related-assessment protection and copied-data persistence. |
| F158 | D3 | Original Jobs/profile form and version/current/approval/retirement/placement workflow acceptance; preserve archived ownership and source, record remaining differences explicitly. |

Continue three checkpoints per owner instruction. After management acceptance,
proceed to the existing PLOT and CBC/HiGHS JROT final criteria, comprehensive
cross-feature acceptance, then inventory/docs/native delivery. R010/R011 remain
within existing G1/G2 final text/resize work. No new scope or dependency request.
