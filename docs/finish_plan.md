# Finite finish plan v1 — Linux migration complete

The owner approved M01 onward and explicitly authorized M07/M08 together. This is the
fixed replacement for rolling F checkpoints and open-ended acceptance batches.
No application, dependency, environment or reference file is changed by this review.

## Review findings

- F149–F155 were implementation/check logs, not completed remaining deliverables.
  Calling such checkpoints milestones obscured unfinished acceptance and was a
  reporting/planning failure. New F numbers will not define future progress.
- The prior broad G4 buckets gave no credit for smaller corrections, so reporting
  checkpoint completion beside an unchanged percentage was unhelpful.
- The prior machine ledger was stale: B1 still listed dirty-transition Save and
  Save As failure acceptance after F153 completed both, C4 omitted F155 workflow
  evidence, and its verification field still named F149. Completed work must not
  be assigned again as new work. The old file is historical provenance only.
- Existing implementations and F155 evidence show 1,148 passing tests and 96.48%
  coverage. This review does not rerun tests or certify final parity. Source review
  confirms the restored summary component and ST source-unit header are present.
- Stage 6 already calls for Linux/Windows/macOS native acceptance. Only the Linux
  baseline is approved/tested here; target access and version approvals are a
  known M12 blocker that must be resolved explicitly, not hidden until handoff.

## Fixed accounting

Keep 74 as the inherited reporting anchor, NOT a newly measured percentage of
engineering hours. Do not increase it retroactively to make recent work appear
more productive. The previous 26 remaining scope points are partitioned exactly
once into the 12 milestones below: no weight changes or added product scope.

`overall = 74 + sum(points for milestones completed with acceptance evidence)`

`remaining-plan progress = sum(completed milestone points) / 26 × 100`

Current position: **12/12 milestones closed; 26/26 fixed remaining points
earned; 100/100 of owner-approved Linux scope; zero remaining.** Owner explicitly
defers Windows/macOS native acceptance on 2026-10-11; those tests have not passed.
A milestone earns its fixed points only when all its acceptance items close.
Partial work is reported as checked items, not a completed milestone or new F number.
Report percentages to two decimal places where needed.
The authoritative executable data is [finish_progress.json](finish_progress.json).

## The complete remaining milestone list

| ID | Deliverable | Points | Overall once M01 through this row close |
|---|---|---:|---:|
| M01 | Assessments and shared editing | 5 | 79% |
| M02 | Worker Management | 1.5 | 80.5% |
| M03 | Organization and Jobs | 2.25 | 82.75% |
| M04 | Project lifecycle and original-data compatibility | 2.5 | 85.25% |
| M05 | PLOT filters and risk results | 1.25 | 86.5% |
| M06 | PLOT maps, charts and exports | 2.5 | 89% |
| M07 | JROT schedule and scope | 1.5 | 90.5% |
| M08 | JROT optimization and Apply | 2.25 | 92.75% |
| M09 | Shared UI, localization, units and avatar | 1.75 | 94.5% |
| M10 | Final comprehensive-project acceptance | 0.75 | 95.25% |
| M11 | Code/feature inventory and final documentation | 2.5 | 97.75% |
| M12 | Native delivery and handoff | 2.25 | 100% |

## Fixed acceptance items

### M01 — Assessments and shared editing

Original ledger coverage: C1, C2, C3, C4.

- [x] **M01.1** Close remaining integrated LiFFT, DUET and ST control/layout comparisons against original code; use F151–F155 numeric/style evidence rather than repeat it.
- [x] **M01.2** Close worker/context navigation, task-count, Reset/Delete, versions, keyboard focus and modal cancellation; reuse F152/F155 evidence for cases already passed.
- [x] **M01.3** Dispose of the known in/inch and saved-versus-fresh shade differences (R010) explicitly; retain source/result provenance and original ST direction mapping. No scientific corrections.

### M02 — Worker Management

Original ledger coverage: D1.

- [x] **M02.1** Compare original worker form: empty/new, populated/selected and optional-details states; retain original visible fields, layout, icons and actions.
- [x] **M02.2** Verify height/weight in both units, assignment edit, validation, Save/Cancel and independent reopen; preserve historical assessment ownership.

### M03 — Organization and Jobs

Original ledger coverage: D2, D3.

- [x] **M03.1** Compare hierarchy/shift and Jobs/profile/placement forms in empty, populated and selected/expanded states.
- [x] **M03.2** Close organization create/edit/delete and shift relationships; close job/profile version, approval/current/retirement and placement workflows with Save/Cancel/reopen and referenced-record protection.

### M04 — Project lifecycle and original-data compatibility

Original ledger coverage: B1, B2.

- [x] **M04.1** Close New/Open/Save/Save As/Close, recent/missing files, properties/details, transfer, CSV, backup/restore against the original supported workflows and approved differences.
- [x] **M04.2** Reuse F150/F153 atomic Save/Save As and failure evidence; do not reimplement these completed paths.
- [x] **M04.3** On comprehensive-project copies, verify original archived fields, record ownership, conversion output identity and export precision/status; confirm originals remain unchanged.

### M05 — PLOT filters and risk results

Original ledger coverage: E1.

- [x] **M05.1** Compare matched copied-data filters, worker/job counts, missingness and Individual/Job/Comparison outputs with original PLOT.
- [x] **M05.2** Close original filter/result control appearance and Apply/Cancel/empty-result behavior; retain approved aggregation semantics.

### M06 — PLOT maps, charts and exports

Original ledger coverage: E2, E3.

- [x] **M06.1** Close original map image/marker placement, selection, worker/job controls and Save/load behavior, including undo/redo.
- [x] **M06.2** Close chart settings, highlights, details and export content against original controls/results, including empty/populated/selected states. Dormant transforms remain archived.

### M07 — JROT schedule and scope

Original ledger coverage: F1.

- [x] **M07.1** Close original worker/job scope chooser, targets, schedule grid, profile/assignment relationships, edit/undo/redo and Save/reopen.
- [x] **M07.2** Resolve known Spanish scope-summary clipping R006 at its documented minimum size; verify selected IDs and expanded scope selection.

### M08 — JROT optimization and Apply

Original ledger coverage: F2, F3.

- [x] **M08.1** Close matched-input single-tool CBC and multi-tool HiGHS feasibility/objective comparisons, result comparison, Apply/Undo/Save/reopen and frozen profile provenance.
- [x] **M08.2** Verify existing timeout/cancel/infeasible paths; compare objective/constraints rather than demand identical alternative optima. No GLPK, solver replacement or new optimization feature.

### M09 — Shared UI, localization, units and avatar

Original ledger coverage: G1, G2.

- [x] **M09.1** Close integrated header/footer/navigation plus approved menu/settings exceptions; retain original style, controls and workflows.
- [x] **M09.2** Complete EN/ES visible labels/tooltips/dialogs and metric/imperial display/save/export matrix on the forms listed below; resolve known sidebar-caption concern R011 after checking individual images and font geometry.
- [x] **M09.3** Close VTK region/camera/rotate/zoom/reset, settled gauge values, keyboard navigation and minimum/enlarged window checks with no clipping. Reuse existing widget evidence; no renderer replacement.

### M10 — Final comprehensive-project acceptance

Original ledger coverage: G3.

- [ ] **M10.1** Run one recorded copied-project scenario: workers/organization/jobs, all three assessments Calculate/Save, PLOT, CBC/HiGHS Apply/Save, transfer/export/backup and reopen.
- [ ] **M10.2** Compare final persisted results, ownership, risk outputs and workflows with the original; verify original file hashes. Reuse component-level evidence instead of repeating all unit tests manually.

### M11 — Code/feature inventory and final documentation

Original ledger coverage: A3, H1.

- [ ] **M11.1** Close the original-active-entry-point inventory with each item mapped to its migrated implementation/evidence or an explicitly approved exclusion; classify hidden experimental data and dormant fields without enabling new UI.
- [ ] **M11.2** Complete the public API/units/errors/scientific-source documentation review and remaining behavior dispositions within existing features.
- [ ] **M11.3** Update the actual user/developer/recovery guides, retire obsolete preview instructions, verify Help opens the packaged current guide; no new documentation framework.

### M12 — Native delivery and handoff

Original ledger coverage: H2.

- [x] **M12.1** Verify clean independent Linux installation/launcher, packaged assets, VTK, CBC/HiGHS, offline use and backup/restore without the reference checkout.
- [x] **M12.2** (Closed by explicit owner deferral; native tests NOT RUN.) Close the original Stage 6 Windows/macOS native acceptance on actual targets with explicitly approved exact dependencies. This is a KNOWN availability/version-approval blocker, not new scope.
- [x] **M12.3** Deliver install/run/recovery instructions and final evidence. Do not replace/publish the reference application. If native targets are unavailable, report incomplete and ask for an explicit deferral decision; never call untested platforms complete.

## Bounded UI and quality checks

Assessment forms: integrated main window, LiFFT/DUET/ST grids, assessment/context
and saved-data picker, task-count modal, version picker. Management: Worker,
Organization, Jobs/profiles/placements, worker transfer. PLOT: main/filter/results,
workplace, map, graph/settings/highlight/detail/export controls. JROT: main,
scope/schedule/targets, comparison/Apply controls. Shared: project properties and
details, preferences, Authors/Help, file/dirty/delete dialogs, body region/gauge.
This is a review of existing visible surfaces, not authorization to add forms.

For each owning milestone, compare original control/layout code first and inspect
its relevant empty, populated, selected/expanded and error/cancel states. Use
minimum/enlarged states for resizable windows; inspect complete avatar, cards,
headers/footers and bottom controls. Reuse F151–F155 and earlier valid evidence
where the relevant code/state is unchanged. Feature comparisons happen once in
the owning milestone; M09 checks shared behavior and remaining language/units
coverage, not a second complete migration of every form. M10 is one cross-feature
scenario, not another component audit.

Every completed code milestone retains typed/documented APIs, established naming,
layer boundaries, approved dependencies and mandatory tools/check.sh. Focused
regressions cover the actual change. Do not redesign working forms, add speculative
infrastructure, expand scientific models, replace VTK or introduce GLPK.
Documentation-only work uses document/ledger validation, not another full UI suite.

## Work limits, approval and reporting

1. The owner approved this baseline and continuation with M01. Only the next
   single listed milestone is the current batch; no scope extensions are implied.
2. Use M01–M12 only, in order, ONE per batch as now requested.
   Do not add, split, renumber or substitute milestones. If a milestone does not
   finish, keep that same milestone open and explain its exact remaining item.
3. Each milestone permits one evidence/reference comparison pass and one bounded
   correction pass for its stated acceptance items, followed by required checks.
   If it needs additional implementation work/passes, stop affected work and
   obtain approval for the extension before continuing. This is a stop rule,
   not a guarantee that unknown defects cannot exist.
4. Report any newly found defect, extra work, scope change, new infrastructure,
   unexpected blocker or proposed additional milestone before implementing it.
   State what was found, why it matters, affected milestone, concrete proposed
   work, bounded effort/token estimate or uncertainty, and progress/date impact.
   Record the owner's decision in change_requests. No approval means no extra work.
5. A known issue listed above belongs to its named milestone. A new issue may be
   recorded while unaffected already-approved work continues; recording it is not
   authorization to repair it. No catch-all "polish", "hardening" or "more tests"
   milestones. No silent exceptions by calling new work part of an old milestone.
6. Every progress report states: active milestone ID; acceptance items closed and
   remaining; actual changes/evidence; milestones closed out of 12; earned points
   out of 26; overall percentage; next fixed IDs; blockers/approval requests.
   Show estimated remaining effort as a separate estimate with assumptions when
   evidence supports it. Do not derive a finish date from F counts or invent one.
7. M12 is incomplete without required platform evidence or the owner's explicit
   scope/deferral decision. Deferral is not a passed test. Preserve the full-scope
   score and disclose any separately approved delivery scope; no automatic 100%.
8. Finish means all accepted milestone criteria close, handoff is delivered and
   no approved required work remains. Do not continue with unsolicited improvements.

## Change control register

CR001: owner approves one-at-a-time execution starting M01, Linux parity and
old-project compatibility first, Windows/macOS VM acceptance afterward. Known
frontend platform requirements remain applicable; no untested native claims.
Milestone count/weights remain unchanged. Any approved revision
must preserve the old baseline and display old/new scope, points and completion
impact; no quiet denominator or weight adjustment.


## Owner platform sequencing clarification — CR001

Deliver Linux functional and visual equivalence with original projects compatible
or converted first. Review known Qt/Python frontend platform requirements as they
apply to the current work. Windows/macOS VM checks follow a working Linux version;
they do not block earlier milestones or trigger a separate cross-platform rewrite.
M12 retains its scope/points and sequences Linux delivery before later VM evidence.
No platform-dependent dependency installation is authorized by this clarification.


## M01 execution disposition

M01.1/M01.3 verified; M01.2 awaits CR002 ST keyboard order. See m01_acceptance.md
and m01_validation.json. Current 74/100, zero milestone credit pending closure;
M01 closes at 79/100. No weights/count change, no M02 started. CR002 asks for a
local restore-order correction or explicit acceptance of current row-by-row order.


## M01 closed — CR002 resolved

Owner directs original ST Tab order. Local correction and focused/full/packaged
native checks passed; all M01 acceptance items now verified. Earned 5 points:
79/100 overall, 1/12 milestones complete, 21 points left to earn. M02 next,
not started. The earlier pending-disposition note is historical and superseded.


## M02 closed

Both M02 criteria verified; original notification prefix restored with no layout
change. Twelve focused cases, full standards/build/regression gate and packaged
native visual states passed. See m02_acceptance.md and m02_validation.json.
Earned 1.5 points: **80.5/100**, 2/12 complete, 6.5/26 earned, 19.5 left.
M03 next, not started. Existing raw legacy worker units remain M04 review;
no new milestone, weight or scope extension.


## M03 closed

Organization/Jobs original-source comparison and all listed persisted workflows
verified. No production change required. Sixty-four focused packaged regressions,
actual integrated management actions and native visual evidence pass; unchanged
M02 full gate reused. See m03_acceptance.md and m03_validation.json.
Earned 2.25 points: **82.75/100**, 3/12 complete, 8.75/26 earned, 17.25 left.
M04 next, not started. No milestone/weight expansion or extra repair added.


## M04 closed — CR003 resolved

Owner directs legacy worker measurements to follow the project's declared units.
Converted editable values normalize to cm/kg; exact raw source/archive retained.
Original New/first-Save timing and empty-project Open restored within existing
M04 scope. Focused/full/packaged native checks pass; see m04_acceptance.md and
m04_validation.json. Earned 2.5 points: **85.25/100**, 4/12 complete, 11.25/26
earned, 14.75 left. M05 next, not started. No milestone/weight expansion.


## M05 closed

Original-source query/control comparison, 48 matched copied-data cases, 41 focused
packaged tests and native PLOT state acceptance pass. Existing F131 recovered
records and F113 paired/missingness semantics explicitly accounted for. No code
correction required. See m05_acceptance.md and m05_validation.json. Earned 1.25
points: **86.50/100**, 5/12 complete, 12.50/26 earned, 13.50 left. M06 next,
not started. No milestone/weight/scope expansion.


## M06 complete — original workflows and approved history

M06.1 and M06.2 verified. Original map/chart/export evidence is retained; required
PLOT undo/redo is implemented with application-owned commands, localized actions,
focus-aware typing, explicit/partial Save, failure recovery, exact geometry and
station order. Final full gate: 1,168 tests, 96.37% coverage and all standards/build
checks pass. Final wheel: 83 focused PLOT checks. Native comprehensive-copy EN/ES
history and independent reopen pass; 12 final captures inspected. Reference and
approved lock unchanged. CR004 removal was mistaken and withdrawn; criterion
and all weights unchanged. See m06_acceptance.md, m06_validation.json and
plot_history.md. Award existing 2.5 points: **89.00/100; 6/12; 15/26 earned;
11 left**. M07 next; not started in this batch.


## M07/M08 accepted batch — 2026-10-10

Owner authorized both together; all four fixed criteria close. M07 earns 1.50
and M08 earns 2.25 points, with no changed weight or added scope. See their
acceptance/validation records and m07-m08-review. Current total is 92.75/100,
8/12 complete; M09 next, not started. R006 is closed; R012 records noncritical
choices for later review. No additional milestone was introduced.


## M09 partial acceptance — 2026-10-11

M09.2/M09.3 verified: shared EN/ES/unit/avatar matrix, bounded Authors translation,
R011/Transfer disposition and current native inspection. Full approved gate passes
1,180 tests, 96.40% coverage; focused wheel and 34 native captures pass. M09.1
remains open for CR005 original project-caption decision. Prepared patch unapplied;
no points awarded. Progress remains **92.75/100; 8/12 complete**. M10 not started.
See m09_review.md and m09_validation.json. Fixed scope/weights remain unchanged.


## M09 accepted after CR005 approval — 2026-10-11

Owner approved original project-caption restoration. All three fixed criteria
close; final gate 1,184 tests, 96.40% coverage and required standards/builds pass.
Final rebuilt-wheel caption regressions and 14 inspected native captures supplement
34 earlier shared captures; unchanged M01–M08 evidence reused. All reference/lock
hashes unchanged. Award existing **1.75 points: 94.50/100; 9/12; 20.50/26 earned;
5.50 left**. M10 next, not started. See m09_acceptance.md and m09_validation.json.


## M10 accepted — 2026-10-11

Owner-approved CR006 restores exact Copy/Move result preservation. Both fixed
M10 criteria pass on the rebuilt wheel and comprehensive copy, including original
calculations, PLOT, both solver routes, exact transferred/exported results, backup
and native reopen. All reference/lock hashes unchanged. Required full gate: 1,207
tests, 96.42% coverage; 12 final captures inspected. See m10_acceptance.md and
m10_validation.json. Award existing 0.75 points: **95.25/100; 10/12 complete;
21.25/26 earned; 4.75 left**. No milestone/weight expansion. M11 next, unstarted.


## M11 accepted — 2026-10-11

Original inventory, semantic API documentation and current packaged EN/ES Help/
user/dev/recovery guides close all three fixed criteria. Owner-approved CR007
restores the original Search form. Final gate: 1,221 tests/96.41% coverage and
all standards/builds pass; 30 packaged tests/77 subtests, original geometry and
native/bilingual guide inspection pass. Reference/lock unchanged. Earn existing
2.50 points: **97.75/100; 11/12 complete; 23.75/26 earned; 2.25 left**. M12 next,
not started/authorized here. No added milestone, weight or dependency. See
m11_acceptance.md and m11_validation.json.


## M12 accepted — owner confirms Linux completion scope, 2026-10-11

Linux independent install/launcher/assets/VTK/solvers/offline backup/reopen and
handoff are verified. Owner explicitly states the migration finishes with Linux;
Windows/macOS native testing follows later, after confirming Linux behavior
against the prior codebase. M12.2 closes by approved deferral, not a passed native
test. M12.3's explicit decision is satisfied. See m12_acceptance.md and validation.
Award unchanged 2.25 points: **100/100 Linux scope; 12/12; 26/26 earned; zero left**.
Full final code gate 1,226 tests/96.42%; installed/native and prior M01–M11 evidence
reused. No new milestones, dependencies or speculative repairs are authorized.
