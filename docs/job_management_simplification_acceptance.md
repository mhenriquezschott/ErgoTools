# Job Management simplification — Linux verification complete, 2026-10-20

The owner-authorized change is implemented and verified. Owner acceptance and interactive
workflow testing are separate and remain pending. The original Linux migration and
cleanup remain 100%; no milestone, dependency, formula or reference change was added.

## Delivered behavior

Job Management has one current, independently optional LiFFT/DUET/ST value per Job.
Profile versions, evidence metadata and approval/current/retired controls and database
structures are removed. Direct cumulative-damage entry retains the established
probability conversion. Expand **Calculate or copy tool values** for three compact
calculators: start with one task, add/remove up to 100, Calculate or Clear the selected
tool. There is no avatar or additional calculator popup. Exact inputs, source units,
ST convention, per-task outputs and aggregates survive the sole main Save/reopen.

**Use worker assessment…** copies inputs AND matching calculated outputs from a usable
standalone or assigned worker assessment. The picker identifies worker, workplace,
optional Job and calculation availability. This is an independent copy, with no live
link, association, recalculation or worker-data mutation. Partial/stale results cannot
be copied. Subsequent source and Job edits are independent.

Each accepted input edit is a separate shared project Undo/Redo step. Task insertion,
removal, calculation, clearing, mode changes, copying and Job edits use the same history
as the main window. Removing/replacing populated inputs asks consent; Cancel retains
values. Editing tasks clears stale outputs until Calculate. Main Save publishes the
project; Job Management introduces no separate integrated Save.

PLOT and JROT use current Job values, including summaries, eligibility, tooltips, CSV,
comparison, solver preparation and retained drafts. Saved rotations preserve their
worker/Job/placement arrangements; changed numeric Job risks invalidate optimization
provenance and require an explicit rerun. CBC single-tool/HiGHS multi-tool routing and
existing scientific behavior remain intact.

## Database and fixture safety

Native format 19 stores one `risk_measurements` row per Job/tool; there are no
`risk_profiles` or `risk_metadata` tables. Exact task inputs use the existing assessment
codec; output rows include a source digest to reject mismatched stale data. This is
source/result integrity, without alternate assessment or Job versions. Surviving Job
parents are updated in place, preventing cascading removal of retained risks during
workplace/assignment edits. Transaction/fault tests cover rollback of risk and dependent
rotation changes together.

External conversion supports earlier full native formats 8–18, uniquely retains each
Job's selected values, removes older profile/evidence records and rewrites saved target
keys without changing arrangements. Ambiguous selections stop specifically; originals
remain private-copy conversion inputs. Formats 14–18 preserve worker source/result
payloads exactly. Earlier approved conversion rules remain separate from runtime code.

All three maintained native fixtures were updated **in place**:

| Project | Worker sources/results | Jobs | Schemes | Selected Job/tool values |
|---|---:|---:|---:|---:|
| workflow_4_workers.ergprj |12|0|0|0|
| comparative_risk_test.ergprj |194|12|7|35|
| integrated_test.ergprj |194|12|5|36|

The final read-only comparison with the pre-change archive proves exact unrelated SQL
rows, worker payloads, image BLOBs, selected values, scheme arrangements and timestamps;
all integrity/foreign-key checks pass. Migrated direct values receive no invented tasks.
See [final preservation evidence](../artifacts/job_simplification/final_native_preservation.json).

## Validation

- Required native Linux XCB `bash tools/check.sh`: **1984 passed, zero failures/errors/
  skips, 94.33% combined branch coverage**; Ruff, formatting 707 files, strict typing 273 source
  files, architecture, naming, documentation and wheel/source builds pass.
- Current wheel, extracted outside the source tree with converter imports blocked:
  **181 focused tests pass** for Job calculators/storage/shared history, PLOT and JROT,
  including real solver paths. All packaged members match current source/resources;
  the independently tested wheel is byte-identical to the final root dist wheel.
- Actual modal worker copying on private copies of all three fixtures, with
  recalculation blocked: exact inputs/task outputs/totals survive main Save, reopen,
  Save As and backup. All original non-Job data remain exact.
- **42 native EN/ES application captures inspected**, covering compact/expanded,
  blank/calculated three-tool states, minimum widths, many tasks, selected/empty/
  populated copy picker, actual four-worker contexts, PLOT Job/comparison, JROT and
  changed main menu captions. Two packaged bilingual guide renders also inspected.
  Unchanged VTK acceptance is reused; no renderer changes were made.
- 96 changed/new maintained files substantively reviewed and exact hashes renewed.
  Current inventory: 445 Python/stub files, 3113 functions, 418 classes, 312 constants;
  zero pending reviews or structural gaps. Inventory generation does not grant review.

Evidence: [validation](job_management_simplification_validation.json),
[source review](job_management_simplification_review.md),
[decisions](job_management_simplification_decisions.md),
[full gate](../artifacts/job_simplification/full_gate.log),
[package check](../artifacts/job_simplification/independent_package.json),
[copy/reopen proof](../artifacts/job_simplification/native_copy_acceptance.json) and
[visual inspection](../artifacts/job_simplification/visual_validation.json).
Earlier interrupted/stage logs are diagnostic, not final acceptance. One later gate
failure was an inactive-Xvfb-dialog test precondition; explicit test activation fixed
it without changing production focus behavior. Final full gate passes.

## Limits, recovery and next owner review

The two comprehensive fixtures retain pre-existing partial DUET/ST worker results.
They are visible but require a complete matching calculation before copying; migration
does not silently recalculate them. The workflow fixture has four complete worker
results per tool and was used to verify all three copy paths.

The finite pre-change archive, exact baseline hashes, review evidence and final native
hashes are retained under `artifacts/job_simplification`. Before any rollback, close
ErgoTools and stage the archive in a private directory; compare hashes against
`baseline_files.json`. Restore affected code and format 18 fixtures as one coherent
checkpoint, never just an old database under the new runtime. Current format 19 files
can reopen directly; older full files use the external upgrade flow. This archive is
not an automatic application backup or a duplicate maintained test project. After
owner acceptance it can be removed; retain the validation and decision records.

The root `dist` wheel/source package and current `tools/run.sh` represent this change;
`dist/linux` remains the explicitly historical frozen delivery. Windows/macOS native
acceptance remains deferred. Interactive testing stays paused at
[the exact workflow bookmark](workflow_testing_pause.md); the Bruno/Ana Follow worker
step is still unperformed. Ready for owner review of Job Management before resuming.
