# ErgoTools modernization rules

## Owner-authorized GitHub main setup — 2026-10-22

Owner authorizes replacing remote main with the current complete codebase, retaining
all other branches as untouched backups. Existing main history may remain through a
normal replacement commit. Verified owner SSH access is available. Routine Git
status/diff/fetch/add/commit/push for owner-requested reviewed work on main needs no
repeated permission. This supersedes the historical no-automatic-push restriction
for this repository/main within requested work only. No force/mirror push, branch
removal, security-settings change, reference writes or unrelated implementation.
Use the main-only remote refspec and respect branch protection/concurrent changes.
Read docs/repository_setup.md and branch baseline. Dependency/architecture/docs/test
rules continue. Personal credentials, environments, caches, artifacts and dist stay
untracked. Retain applicable authorship/third-party notices.

## Owner-directed prototype meeting refinement — 2026-10-21

Owner authorizes the blue/white drawer, visible Yes/No choices, familiar read-only
hierarchy/shift/Job/worker picker windows, free Back/sidebar review navigation with
calculation-only readiness gates, and one clean additional native fixture named
`test_projects/native/jrot_workflow_demo.ergprj`. Six workers, six source-calculated
Jobs and realistic multi-plant organization use current schema/APIs only. This new
fixture is explicitly requested, not an unauthorized duplicate. All prior production
code/schema/calculator/optimizer/dependency/reference protections remain. Prototype
restrictions stay optional and visual only; close discards inputs. Verify full real
and mixed-data flows, record disposable windows/removal instructions and actual native
visual evidence. Basic prototype checks remain authorized; no new milestones.


## Current owner authorization — isolated JROT prototype, 2026-10-20

Owner authorizes a disposable English/cm/N Yes-path developer mockup. Only existing
Settings/menu/composition hooks may change; no production schema/calculator/optimizer
or workflow changes. Developer switch defaults off and never persists. Detached project
catalogs, explicit samples and entered tasks may run existing real CBC single-tool or
HiGHS all-three optimization. Worker rules are visual only; No path, reports, history
and two-tool optimization remain unavailable. Close discards all scratch data. Owner
permits a private comparison-project artifact copy, basic tests/documentation (rather
than a repeated full gate) and best judgment with recorded doubts. No new milestones.
See docs/jrot_prototype.md and current STATUS. Hands-on owner tests remain paused.

Read `docs/STATUS.md`, `docs/architecture.md`, `docs/coding_standards.md` and `docs/development.md` before work. The accepted detailed plan and owner authorization are in `docs/reference/`; historical proposal wording there is superseded by the owner's authorization and recorded decisions.

- Work in this new project only. Keep the reference checkout and its Conda environment unchanged. Do not reset, clean, stash or modify it. Never use operational databases as migration test targets.
- Final target: ONE integrated LiFFT/DUET/ST/PLOT/JROT application with reference visual/workflow parity; see `docs/final_targets.md`. The standalone preview is a temporary harness, not the final layout. Use focused early fixtures; the comprehensive reference project is a final integration target, tested only on a copy.
- Preserve the integrated application's behavior and appearance. Use this package's copied processed icons and model assets; do not load runtime assets from the reference tree. Preserve palette, typography, spacing, tooltips and interactions. Normalize any new icons and report missing assets.
- Inspect every changed UI window and expanded/selected/empty/populated state, including VTK, result cards and bottom controls for clipping. If rendering is unavailable, record the exact manual verification required; do not claim visual acceptance.
- Dependency baseline: Python 3.13.14 and exact versions in `uv.lock`. The owner explicitly approved the foundation versions and their locked transitive dependencies, plus the F28 Linux desktop extra: PyQt5 5.15.11, PyQt5-Qt5 5.15.17 and PyQt5-sip 12.17.0. The owner also explicitly approved the F78 VTK dependency set in docs/vtk-dependency_proposal.md for this new environment on 2026-10-04. The owner also approved PuLP 3.2.2 with bundled Linux CBC 2.10.3 and highspy/HiGHS 1.11.0 in docs/jrot_dependency_proposal.md on 2026-10-08. Do not change Python, package versions or ranges, or introduce dependencies outside that approval without explicit version approval. Never modify the reference environment.
- Migrate reviewed components incrementally, not bulk copies of legacy modules. Keep the domain/application independent of Qt, storage, solvers and renderers. VTK stays inside its replaceable rendering adapter; it is not being replaced in this migration.
- Run `bash tools/check.sh` for each completed code slice. Record actual results and limitations. No blanket lint/type suppression to obtain a pass.
- Update STATUS, behavior differences, evidence and next steps at every checkpoint. Report a rough overall completion percentage, distinguishing foundation work from full functional parity. No automatic publishing, pushing or replacement of the current application.

- Owner instruction, 2026-10-10: work THREE milestones at a time until the owner
  changes that instruction. This supersedes the earlier one-milestone and four-milestone batch
  instruction. Record noncritical inconsistencies and strange
  reference comments in docs/review_register.md for later review; do not block
  authorized compatibility work on them. Ask about critical changes or fixes when
  a decision is required. Preserve original behavior unless a correction is approved.


## Owner stop and scope-control instruction — supersedes rolling checkpoints

The owner explicitly paused implementation on 2026-10-10 for a finite completion
plan. Read docs/finish_plan.md and docs/finish_progress.json first. The proposed
M01–M12 baseline awaits owner review; do not resume implementation until approved.
After approval, three fixed milestones per batch remain the requested pacing.
Do not invent/add/split/expand milestones or carry out newly discovered extra
work without reporting it and obtaining the owner's explicit approval first.
No new defect repair may be disguised as extending an existing milestone.
Use the documented one-comparison/one-correction-pass stop rule; request approval
for extra work rather than iterating indefinitely. Report fixed milestone IDs,
actual acceptance evidence and exact points. F logs are historical, not milestones.
Reference/dependency/UI/standards protections above remain in force.


## Latest owner authorization — overrides pause/pacing above

The owner approves M01 continuation, ONE milestone at a time until changed.
Use the fixed finish-plan/finish-progress ledger; prior three-per-batch text is
historical. Linux original-functionality/visual parity and old-project compatibility
come first. Windows/macOS VM testing follows a ready Linux version; known frontend
Qt/Python OS requirements remain relevant now. Do not treat deferred VM tests as
passed or let them block Linux migration. Scope-change/extra-work approval rules
and approved dependency baseline remain binding.


## Latest original-behavior decision — CR002

Owner explicitly directs the original ST Tab order; no further clarification is
needed for that choice. Preserve original calculation behavior. Alternative UI
behavior can be recorded for later review rather than substituted now. CR002 is
closed; M01 complete at 79/100. Continue one fixed milestone per batch; M02 next.


## Current fixed finish checkpoint

M06 complete at 89.00/100; 6/12 complete, 15/26 earned, 11 points left. M07 next,
not started; continue ONE fixed milestone per batch. Read STATUS, finish-progress,
m06-review, m06-acceptance, m06-validation and plot-history. Required PLOT undo/redo
is implemented and accepted; CR004 removal was rejected and withdrawn. Original
UI parity coexists with approved application undo/redo and extensible initial
English/Spanish localization. Final gate: 1,168 tests, 96.37% coverage; 83 native
packaged PLOT tests and comprehensive-copy EN/ES history/reopen acceptance pass.
Twelve changed-UI captures inspected; reference/lock unchanged. Reuse valid M06
evidence; no further repeated gate without changes/failures. M07 uses original
JROT schedule/scope workflow; CBC single-tool, HiGHS multi-tool, no GLPK. All
scope-control, original-reference, standards and dependency protections continue.


## Latest owner batch authorization — M07 and M08

The owner explicitly authorizes completing M07 and M08 together, superseding
one-milestone pacing for this batch. Resolve noncritical questions using judgment
and record them in the session and review register for later review; stop only
for a genuinely critical decision. Fixed scope and weights remain unchanged.
Starting progress 89.00/100; completion of both yields 92.75/100.


## Current authoritative finish checkpoint — M07/M08 accepted

M07 and M08 complete at 92.75/100, 8/12 closed, 18.75/26 earned, 7.25 points left.
Read STATUS, finish-progress, m07-acceptance, m08-acceptance, their validation
records, m07-m08-review and jrot-history. Final native XCB gate: 1,178 tests,
96.40% coverage, required standards/builds pass. Packaged focused JROT tests and
native comprehensive-copy EN/ES workflows pass; 22 captures inspected. All 500
reference hashes and approved lock unchanged. CBC single-tool/HiGHS multi-tool
routing and original objectives/constraints remain intact; no GLPK. R006 closed;
R012 records noncritical history/count choices for later review. M09 next, not
started. The latest two-milestone authorization covered M07/M08 only; do not
silently extend the batch into M09. Fixed scope/weight and owner-approval rules
remain unchanged. Reuse valid evidence; do not repeat gates without a reason.


## Latest owner authorization — M09

On 2026-10-11 the owner directs M09 only. Resume its three fixed criteria from
92.75/100; completion yields 94.50/100. Previous M07/M08 batch is complete and
does not authorize M10. Scope, weights, original UI and dependency rules remain.


## Latest M09 handoff — 2026-10-11

M09 only authorized. M09.2/M09.3 verified; M09.1 awaits owner CR005 caption
repair/exception decision. See docs/m09_review.md and prepared patch in
reference/m09-header-proposal.patch.txt. Do not apply pending patch without the
owner's reply, award M09 points early, or start M10. Ledger remains 92.75/100.


## Owner CR005 approval — 2026-10-11

Owner replies yes to restoring original header/footer project captions within M09.
Apply prepared caption patch, verify EN/ES lifecycle/pending inputs and native fit,
and finish M09 only. No authorization to start M10; scope/weights unchanged.


## Current authoritative finish checkpoint — M09 accepted

M09 complete at 94.50/100; 9/12 complete, 20.50/26 earned, 5.50 points left.
Owner explicitly approved CR005; original header/footer captions restored.
Read docs/STATUS.md, m09_acceptance.md, m09_review.md and m09_validation.json.
Final native XCB gate: 1,184 tests, 96.40% coverage, all standards/builds pass.
Final wheel caption regressions and 14 native captures pass; 34 earlier shared
captures and valid M01–M08 component checks reused. Reference/lock unchanged.
M10 is next, not started; current authorization ends with M09. Fixed weights,
scope-control, original UI/dependency protections and one-milestone pacing remain.


## Latest owner authorization — M10

Owner directs M10 only on 2026-10-11. Run the fixed final copied-project scenario
and original comparison/hash checks. Reuse valid component evidence; no speculative
work or repeated full suite without changed code/failure. M11 not authorized.
Starting progress 94.50/100. Original/dependency/scope protections remain binding.


## Owner CR006 approval — 2026-10-11

Owner answers yes to bounded atomic Copy/Move result-preservation repair and
focused/full/final M10 validation. The numerical example is saved-summary rounding,
not a formula discrepancy. No added milestone/points/dependencies; M11 not authorized.
See docs/m10_transfer_result_proposal.md.


## Current authoritative checkpoint — M10 accepted

M10 complete at 95.25/100; 10/12 closed, 21.25/26 earned, 4.75 points left.
Owner-approved CR006 preserves exact saved/imported results during Copy/Move;
no formula, UI or dependency change. Read docs/m10_acceptance.md, review and
validation. Full native XCB gate: 1,207 tests, 96.42% coverage; standards/builds
pass. Rebuilt wheel: 23 focused regressions, final comprehensive-copy scenario
with backup reopen and fresh/imported actual transfer probes pass. Twelve final
captures inspected; 500 reference hashes and approved lock unchanged. Reuse valid
evidence; do not repeat the gate without code changes/failures. M11 next, not
authorized/started. Fixed scope/weights and original/dependency protections remain.


## Latest owner authorization — M11

Owner directs M11 only on 2026-10-11: active-entry-point inventory, API/behavior
documentation review and current packaged/user/developer/recovery guides. Start
95.25/100; completion yields 97.75/100. M12 not authorized. Fixed scope, original
UI/reference/dependency protections and extra-repair approval remain binding.


## Owner CR007 approval — 2026-10-11

Owner explicitly approves original Search restoration as proposed in
docs/m11_search_proposal.md. Implement and validate within M11; fixed weights
and dependencies unchanged. M12 remains unstarted/unauthorized.


## Current authoritative checkpoint — M11 accepted

M11 complete at 97.75/100; 11/12 closed, 23.75/26 earned, 2.25 points remain.
Owner explicitly approved CR007 original Search restoration. All three M11
criteria verified: original active/dormant/hidden inventory, API units/errors/
scientific documentation, current packaged bilingual Help and user/dev/recovery
guides. Read docs/STATUS.md, m11_acceptance.md, m11_review.md and validation.
Final Linux XCB gate: 1,221 tests, 96.41% coverage; standards/types/builds pass.
Independent wheel: 30 focused tests/77 subtests, original Search geometry matches
three sizes, 12 native Search captures and bilingual browser guides inspected.
All 236 package Python files/current guide bytes match wheel; reference 500 files
and approved lock unchanged. Reuse valid M01–M10 evidence; no repeated validation
without concrete cause. M12 next, unstarted and not authorized in this batch.
Fixed scope/weights, dependency/reference protection and one-milestone pacing stay.


## Owner authorization — M12, 2026-10-11

Owner directs M12 native delivery/handoff. Start 97.75/100. Verify independent
Linux installation/launcher, assets/VTK/CBC/HiGHS/offline backup/restore and known
frontend platform requirements. Native Windows/macOS acceptance is not inferred;
if targets unavailable, prepare Linux evidence/instructions then ask explicit
deferral decision under M12.3. Fixed scope/weights/dependencies/reference rules stay.


## Current authoritative M12 handoff — Linux verified, native decision pending

Linux independent delivery is concrete/verified; progress stays 97.75/100 until
owner resolves native Windows/macOS deferral per M12.3. Read docs/STATUS.md,
m12_acceptance.md, m12_validation.json, m12_review.md and linux_delivery.md.
Full gate 1,226 tests/96.42%, all standards/builds pass; final wheel 21 focused
tests/77 subtests. Separate installed Python/env, all runtime pins/assets, VTK,
CBC/HiGHS, disconnected-network comprehensive-copy backup/reopen and four native
captures verified. Reference/lock unchanged. Existing Windows VMs are off; no
validated target environment or configured macOS target. Do not claim OS tests
passed. Ask explicit deferral/closure decision; do not repeat tests/add milestones
while waiting. If owner approves Linux closure with deferred OS acceptance, record
that decision and close original M12 at 100/100 without labeling those OSs tested.


## Authoritative owner closure — Linux migration complete, 2026-10-11

Owner explicitly confirms the migration finishes with Linux; Windows/macOS native
tests are later work, after confirming expected behavior and original-codebase
parity on Linux. This supplies M12.3's required scope/deferral decision and
supersedes pending-decision text above. M12 closes at 100/100 of approved Linux
scope, 12/12 milestones, 26/26 fixed remaining points. Windows/macOS remain
untested, explicitly deferred; never label them passed. Read current STATUS,
finish-progress, m12-acceptance/validation and linux-delivery. Accepted M01–M11
original parity/integration evidence remains valid. No further implementation
or repeated gates without concrete changes/failures or owner-requested work.
Prioritize owner Linux acceptance and bounded reproduction of actual mismatches;
do not invent rolling milestones. Reference/dependency/scope protections remain.


## Owner-requested Linux parity correction — positional project launch

After closure the owner identifies the original positional command-line project
workflow as missing and reaffirms Recent Projects. Restore that bounded original
entry point via existing Open/conversion/error/recent policy, document and verify
it; no new milestone/points/dependency or redesign. Recent Projects already exists
under Project in EN/ES and retains ten successful locations. Reference stays
read-only. Record correction evidence in docs/cli_project_acceptance.md.


## Positional project launch correction verified

The bounded owner-requested original CLI entry point is restored through existing
Open policy. Recent Projects already existed and is verified in native EN/ES.
Current gate 1,232 tests/96.51%, all standards/builds pass; independent wheel
34 tests/77 subtests; five native captures inspected. Current delivery hashes
are in artifacts/cli-project-package.json, acceptance/validation in docs/cli-project-*.
Historical M12 evidence remains historical. Linux scope remains 100/100; no new
milestone/points/dependency; reference/lock unchanged. No further unrequested work.


## Owner-approved analysis-history extension

Owner authorizes reversible PLOT filter/demographic enabled-and-value state,
tool/mode/workplace selections, corresponding JROT risk-tool/pending/applied
scope state, and main assessment document shortcuts. Keyboard/menu only;
no new arrow controls. Existing PLOT/JROT Save controls remain; moving Save
to the main UI is a future decision, not authorized here. Use the existing
DocumentSession engine with scoped chronological state, preserve explicit
Save, native typing and solver ownership. No new milestone/points/deps.

## Analysis-history extension accepted

Owner-approved keyboard/menu extension complete; fixed Linux migration stays
100/100, 12/12. Current full gate: 1,242 tests/96.48% coverage, all standards/
builds pass; current wheel 66 tests/77 subtests, 238 Python files/guides equal.
Eighteen native EN/ES captures inspected; copied project bytes, reference/lock
unchanged. Read analysis-history-acceptance/validation and STATUS. Save buttons
remain; unified saving and arrows await future owner direction. No new milestone,
points or dependencies; no repeated gate or additional implementation without cause.

## Current owner authorization — cleanup M1 only

Read cleanup_plan.md and cleanup_progress.json. Owner approves five fixed follow-up
milestones, authorizes M1 now, and holds user testing until ALL maintained code
has substantive file/function/constant documentation. Converter must be outside
src/ergotools and removable. Native files contain all plants/images/data/results;
no runtime old-schema decoding. M2 owns new guided/unsaved migration workflow;
M3 names, M4 complete documented symbol inventory, M5 acceptance. No added scope,
dependencies, formula changes or reference writes. New/changed interfaces fully
documented now; moved-file gaps tracked, never falsely certified as complete.

## Authoritative cleanup checkpoint — M1 accepted

Cleanup M1 complete at 1/5, 20%; M2 not started/authorized. Read current STATUS,
cleanup-plan/progress, cleanup-m1-acceptance/validation and documentation inventory.
Full gate 1,251 tests/96.45% coverage; independent wheel excludes converter and
native EN/ES workflows pass with tool imports blocked. Native format13 embeds
original observations separately from later saved outputs; format12 upgrades are
external. Original references/lock unchanged. Final documentation-only edits have
the same executable AST as tested code. Reuse valid checks, no speculative work.
User acceptance remains held until complete per-file/function/constant M4 review
and M5 acceptance. Do not claim moved-file docstrings or test coverage establish
complete documentation. M2 guided unsaved migration/native fixtures is next only
on owner instruction. No scope/dependency/UI redesign/reference writes permitted.

## Owner authorization — M1R

Owner explicitly approves M1R before M2. Six fixed cleanup milestones now run
M1, M1R, M2, M3, M4, M5; progress is completed/6. M1R replaces M1 dual-result
preservation: one authoritative result set per assessment version; conversion
recalculates from stored inputs using established formulas/units/ST conventions.
Persist calculator precision without additional save/display rounding or clamping;
UI/export formatting is separate. Remove duplicate result storage/fallback; correct
previous converted files and regenerate native test projects. Inputs remain missing
where missing; partial/failed results are explicit. No formula/dependency/reference
changes. M2 remains unstarted. All changed APIs require substantive documentation.

## Authoritative cleanup checkpoint — M1R accepted

M1R complete, 2/6 (33.33%); M2 awaits owner instruction. This supersedes M1's
dual-result policy. Native format14/result envelope3 keeps one source-bound result
per assessment version; external conversion recalculates original/past converted
inputs and removes duplicate caches. Save adds no rounding/clamping. Formulas,
intrinsic rounding, units, ST mapping, dependencies, reference and UI unchanged.
Read cleanup-m1r-acceptance/validation and current STATUS/progress/inventory.
Full gate 1,256 tests/96.37% coverage; native EN/ES main/PLOT/JROT, Save As/Backup,
ten inspected captures and original-calculator oracle pass. Reuse evidence.
Two supported permanent native fixtures regenerated; two other samples have
documented pre-existing schema/metadata limitations, no repair authorized.
M4 remaining documentation reviews are pending; owner testing remains held.

## Owner authorization — M2

Owner directs M2 only: guided EN/ES external upgrade, cancellation/failure,
temporary unsaved activation and explicit first Save, original/native fixture
organization and sidecar-independent checks. Start 2/6 (33.33%), completion
3/6 (50%). M3 remains unauthorized; no schema-support expansion or dependencies.

## Authoritative cleanup checkpoint — M2 accepted

M2 complete, 3/6 (50%); M3 awaits owner instruction. Read current STATUS,
cleanup-m2-acceptance/validation, cleanup-progress and documentation inventory.
Guided EN/ES optional external conversion opens temporary native backing and
requires first Save; cancellation/errors preserve current project, temporary
paths are never recent, original metadata/units are retained and cleanup follows
repository release. Originals/native fixture folders are separate; 27 original
copy hashes and isolated native relationships/images/schemes verified.
Full gate 1,264 tests/96.39% coverage; standards/types (247)/architecture/builds
pass. Extracted wheel native consent/first Save/reopen passes with converter
imports blocked; 16 captures inspected. Reference 500 hashes/lock unchanged.
No formula/dependency/schema/UI redesign. Two unsupported samples and existing
New pre-save restrictions documented. M4 documentation/M5 owner testing hold
remain; do not claim all code is documented. Reuse valid checks. No M3 work yet.

## Owner batch authorization — M3 and M4

Owner authorizes M3 names and M4 complete substantive code documentation together.
Use judgment for trivial issues and record them for review after M4; stop only for
a critical decision. Fixed scope remains six milestones: start 3/6 (50%), completion
5/6 (83.33%). M5 is separate and not authorized. No dependency/formula/reference
changes or UI redesign. Renamed current documents use snake_case; frozen originals,
reference evidence and external/generated naming conventions are explicit exceptions.

## Authoritative batch checkpoint — M3 accepted, M4 authorized

M3 accepted, 4/6 (66.67%); continue M4 under the owner's M3/M4 authorization.
Current docs use snake_case paths, including cleanup_plan/progress and coding_standards.
M3 full gate 1,267 tests/96.36% coverage; types (248), naming/architecture and builds
pass. All ten native EN/ES main/VTK/PLOT/JROT captures inspected; converter imports
blocked, reference 500 hashes and approved lock unchanged. Resource bytes unchanged.
M4 requires substantive documentation of every maintained module/symbol/constant
with individual source hashes and enforcement, including private/nested functions,
tests, stubs and removable conversion tooling. Do not certify boilerplate or mere
section presence. Reuse M3 functional/visual checks for doc-only changes; run final
required gate once M4 is ready. User testing and M5 remain held/separate.


## Current M4 documentation checkpoint — 173/399 reviewed

M3 accepted; M4 remains authorized and in progress within the owner's M3/M4 batch.
Read docs/cleanup_m4_review.md and exact documentation inventory/hash evidence.
173 files / 759 functions reviewed; 226 files remain (78 desktop, localization,
147 tests). Do not certify pending code from headings or restart reviewed batches.
All application executable AST, existing tools and stub remain M3-equivalent;
reference/lock unchanged. Current standards pass. Reuse valid M3 native captures
and full gate until executable changes or final M4 acceptance justify a new run.
Fixed progress stays 4/6, 66.67%; M5 not authorized or started. Complete remaining
substantive review, gate integration and final acceptance before awarding M4.


## Authoritative cleanup checkpoint — M4 accepted

M4 complete under the owner's explicit instruction to finish it. Fixed cleanup
progress 5/6 (83.33%); M5 unstarted and requires owner instruction. All 401 maintained
Python/stub files, 2,672 named functions (private/nested included), 391 classes and
301 uppercase constants reviewed; two shell entries reviewed. Zero pending reviews
or structural gaps. Both documentation checks are required by tools/check.sh.
Read docs/cleanup_m4_acceptance.md, its validation, inventory and independent
reviewed hashes. Editing a file invalidates its review; inventory regeneration must
never certify it. Review actual contracts before explicitly updating its hash.
Final approved Linux gate: 1,282 tests all passed, 96.25% combined coverage, strict
types (250), standards/architecture/naming/documentation/builds pass. All 397 existing
Python/stub executable ASTs unchanged; reuse M3's ten inspected native captures for
unchanged UI. Reference 500 hashes, original fixtures 27 hashes, resources and lock
unchanged. No M5 work, formula/schema/UI repair or dependency change authorized.


## Latest owner authorization — complete M5

Owner explicitly instructs completing M5 in full. Fixed scope: final Linux
regression/standards/build/resource/relocation/backup checks, uncovered-path review
and current delivery guides/artifacts. No extra milestones, dependency/formula/UI
changes or reference edits. Reuse valid prior evidence; no speculative repairs.
Start 5/6 (83.33%); accept only when criteria close, then 6/6 (100%). Native
Windows/macOS acceptance remains deferred.


## Final authoritative cleanup checkpoint — M5 accepted

Owner explicitly authorized complete M5; all six fixed cleanup milestones are now
accepted for Linux: 6/6 (100%). No additional implementation milestone is active.
Owner testing is ready. Read docs/cleanup_m5_acceptance.md, its validation/coverage
review and docs/linux_delivery.md. Final Linux gate 1,282 passed/zero failures,
96.25% coverage; types 250, standards/naming/architecture/documentation/builds pass.
401 files/2,672 functions/391 classes/301 constants and two shell entries remain
reviewed; zero pending reviews/gaps. Both relocated native comprehensive fixtures,
exact full-database snapshots/restore, real CBC/HiGHS Qt threads and positional
CLI/EN/ES recency pass. Sixteen native captures inspected with enlargement.
Final guide-only updates passed 16 tests/77 subtests. Independent dist/linux delivery
contains current packages, pinned requirement export, install/checksums, two native
fixtures and optional removable external converter/wrapper. Reference 500 hashes,
original fixture 27 hashes, native fixtures, original assets and lock unchanged.
Known unsupported samples/minimum-width Spanish text fit/coverage limits are recorded;
no new repair/UI/schema/formula/dependency work was added. Windows/macOS remain deferred.
Future changes invalidate per-file review hashes and require substantive review;
do not silently expand this completed plan or claim owner testing already passed.


## Owner-directed database correction — 2026-10-13

The owner rejects alternate assessment versions for the same worker Job assignment/tool.
Do not restore New blank version, Set current version, their handlers/mutation port, or
assessment version/status/currentness columns. Native format 15 enforces one assessment
per assignment/tool through assessment_ownership and validated source/result relationships.
Source/result rows store inputs and their single calculated output, never alternate copies.
Job risk-profile versions used by the original JROT workflow and file/codec format versions
are separate required functionality; do not confuse them with the removed feature.

Every database table, column, key and relationship must have a documented functional or
configuration purpose. Do not retain loose tables/values for speculative history. Trace
and test dependencies before schema changes; ask about genuinely ambiguous real data.
External conversion works on private copies, preserves originals and publishes exclusively.
Competing populated duplicate assessments must stop for a specific decision, never be
silently discarded. Current tests use test_projects/native; update these fixtures
in place when their format changes. Do not create parallel current fixture folders. Read docs/single_assessment_ownership.md,
docs/database_tables.md and STATUS for current acceptance and scope.

## Owner-approved optional assessment organization — 2026-10-13

Native format 16 uses direct required worker ownership and an optional real assignment.
No manufactured defaults, assessment versions, redundant business tables or automatic
backups. Existing Default organization in the two test projects is genuine and retained.
Maintain both native test fixtures at their established paths, updating in place.
Read docs/optional_assessment_context.md for exact workflows, integrity and rollback.

Accepted 2026-10-14: optional organization complete; 1,347 tests pass, 95.45% coverage,
standards/docs/builds pass, both fixtures updated in place, 15 native captures inspected.
Reuse this evidence; no further unrequested implementation or repeated validation.

## Owner-approved single project Save and shared history — 2026-10-18

The owner explicitly approves retaining valid management/analysis edits and using the
main Save for the entire project, with synchronized chronological Undo/Redo in editor
windows. This supersedes older local-save/scoped-history boundaries above. Do not
restore separate integrated Save controls or silently discard valid edits on Close.
Four worker additions are four actions; closing the editor adds no action. Confirm
record-removing replay, retain cancelled operations and native typing history.

Read docs/single_project_save.md, its acceptance and current STATUS. Verified Linux
gate: 1,400 passed, zero failures/skips, 94.28% coverage; required standards/types/docs/
review/builds pass. Independent final wheel 50 tests; 64 EN/ES captures inspected.
42 changed files substantively reviewed; 428 maintained files/2,926 functions remain
reviewed with zero pending/gaps. Native/personal formats stay 16/5; no new tables,
assessment versioning, dependencies, formulas, automatic backup or fixtures.

Both maintained native fixtures remain unchanged. The owner workflow project is live
user testing data, not a frozen acceptance fixture; current read-only review finds
four workers and Diego at 65 kg. Never restore the earlier 85 kg checkpoint over it.
No reference writes: ten old manifest differences have October 12 dates and are
recorded in protection evidence, not labelled matching. Current root dist packages
are verified; the frozen dist/linux bundle is not republished. Migration/cleanup stay
100%; Windows/macOS remain deferred. Owner testing resumes after restart; do not
invent milestones, repeat gates without cause, or add unrelated improvements.


## Worker pending form Undo correction — 2026-10-18

Owner's saved-project reopen/Diego weight edit exposed an untested availability gap:
Undo checked only accepted history, so Close was needed to enable it. Corrected by
pure pending existing-worker form inspection and mouse focus on shared history
buttons. No separate stack, per-keystroke project acceptance or durable dialog Save.
Native typing Undo/Redo, invalid text and new-worker boundaries remain preserved.
Read docs/worker_pending_undo_acceptance.md and current STATUS. Native gate 1,406
passed/zero failures/skips, 94.29%; required standards/types/docs/review/builds pass.
Forty focused and forty independent-wheel tests pass; twelve native EN/ES metric/
imperial captures inspected. Three changed files substantively re-reviewed; all
428 files/2,929 functions reviewed, zero pending/gaps. Both maintained fixtures/lock
unchanged; owner workflow project not opened by checks, reference not written.
Migration/cleanup remain 100%, OS deferrals unchanged. Restart/retest pending; no
unrelated implementation or repeated gate without concrete cause.


## Owner-approved task-capacity correction — verified 2026-10-18

Owner approves the task-grid audit fixes and clarifies count ownership is independent
per project, worker, tool and real assignment/standalone context. Preserve that scope;
no global count settings or new tables are needed. Counts default 15, range 1-100.
Increasing retains prefix data/IDs; shrinking drops only tail rows with Cancel-default
consent for entered data; same-count Apply is a no-op. Invalid typing is never silently
erased. Shared Undo/Redo restores removed inputs and exact matching saved results.
Unused slots do not make populated assessments incomplete; started incomplete rows and
empty/no-probability states retain honest validation. Do not reintroduce clear-on-count
change or force users to fill every slot. Settings identifies worker/tool/context and
shared checkbox outlines stay visible under inherited styles.

Read current STATUS, task_grid_resize_acceptance and validation. Native gate 1,449
passed, zero failures/skips, 94.30%; standards/types (265), architecture/naming/docs/
review/builds pass. Independent wheel 100 tests, 243 package Python files and both
bilingual guides equal source. Twenty changed files substantively reviewed; all 428
files/2,944 functions remain reviewed, zero pending/gaps. Twenty-four native EN/ES
captures inspected, 18 indicator-frame checks pass; VTK/result cards/bottom controls
checked. Known Settings tree/footer clipping is recorded separately without extra repair.

No reference/fixture/owner-project writes, schema/dependency/formula changes, new
milestone or assessment versioning. Owner's live workflow project now has one Ana
LiFFT task from the earlier owner reset; do not restore historical 15-row snapshots.
Older saved status metadata refreshes only through Calculate/main Save, never automatic
Open rewriting. Root dist rebuilt; frozen dist/linux not republished. Migration/cleanup
remain 100%; Windows/macOS remain deferred. Owner restart/manual acceptance next.


## Owner-reported pending task-input Undo correction — accepted 2026-10-18

LiFFT/DUET/ST valid pending input now exposes main Undo before Calculate, using the
existing shared history prepare/pending hooks and pure existing grid parsing. Mouse
toolbar replay takes focus; focused text shortcuts remain native. Undo restores exact
prior inputs/results; Redo invalidates obsolete results. Invalid input is retained and
no-op input preserves the branch. Main Save remains the only durable publication.
Read docs/task_input_undo_acceptance.md and STATUS. Required native gate: 1,461 passed,
zero failures/skips, 94.35% coverage; standards/types/docs/builds pass. Independent wheel
90 focused tests; eighteen EN/ES captures inspected. Nine changed files substantively
reviewed; inventory 428 files / 2,957 functions, zero pending/gaps. Models/application/
infrastructure, uv.lock, both maintained fixtures and owner workflow file unchanged.
Linux migration/cleanup remain 100%; no new milestone. Resume owner workflow testing;
no unrelated implementation or repeated gates without concrete cause.


## Owner repeated task Undo and Project folder action — accepted 2026-10-18

Shared replay UI refresh now keys operation plus destination, fixing fresh branches
returning to the same earlier revision without refreshing widgets. Seventy-two cases
cover all nine input types, populated/empty rows, both languages/units and repeated
branches/Redo. Project > Open project folder delegates saved-project parent directory
to the independent OS file manager; disabled with no project or before first Save.
No pending-input acceptance, Save, custom browser or dependent child window is added.
Read STATUS and docs/repeated_task_undo_and_folder_acceptance.md. Required native gate:
1,539 passed, zero failures/skips, 94.32% coverage; standards/types/docs/builds pass.
Independent wheel 175 tests; 26 application states and one independent Nautilus capture
inspected. Private desktop startup limitations are explicitly recorded. Five maintained
files substantively reviewed; 428 files / 2,961 functions, zero pending/gaps. Both native
fixtures, owner workflow, models/application/storage, reference and uv.lock unchanged.
Linux migration/cleanup remain 100%; no new milestone. Resume owner workflow testing.


## Owner field-by-field task-history correction — verified 2026-10-18

Task-grid pending-field grouping is superseded. Every completed LiFFT/DUET/ST cell
is one existing source command/shared project history step: numeric departure/Enter
or immediate selector choice. Only that cell is parsed; invalid siblings remain
local and valid cells complete separately. Last-focused input completes before toolbar
Undo. Revisited cells, native typing, no-ops, exact source-bound results and unchanged
precision are verified. Projection suppresses completion of retiring controls. The
existing Modified/context projection updates on source acceptance without task-widget
rebuild; pure-focus catalogue-authority protection remains. No extra stack, schema,
assessment version, formula, dependency or automatic Save. Read STATUS and
docs/task_cell_history_acceptance.md. Final native gate: 1,645 pass, zero failures/skips,
94.35%; standards/types/docs/builds pass. New regression module 106 cases; extracted
wheel 166 tests; 30 final EN/ES native captures inspected. Ten changed files reviewed;
429 files / 2,971 functions, zero pending/gaps. Both native fixtures, owner workflow,
models/application/storage, reference and lock unchanged. Migration/cleanup stay 100%;
no new milestone. Resume owner workflow testing after restart; no unsolicited work.

## Owner-requested Save availability — verified code checkpoint, 2026-10-19

Main toolbar/menu Save now project existing dirty/pending/first-Save state, including
management notifications and deletion with no active assessment. Saved state disables
Save; Undo/Redo reflects the saved baseline. Save As remains available; invalid input
validation, explicit calculation and publication are unchanged. Read STATUS and
save_availability_acceptance/validation. Final native gate 1,665 passed/94.34%, zero
failures/skips, all standards/builds; independent wheel 54 passed. Four changed files
substantively reviewed; 430 files/2,976 functions, zero pending/gaps. Owner/native
fixtures, models/storage/reference/lock untouched. Linux migration/cleanup stays 100%;
no new milestone. Next owner test: restart/reopen, clean Save disabled, edit enables,
Save disables; resume independent data entry and bottom-button review afterward.

## Owner-requested application Undo limit — verified, 2026-10-19

Settings > General > Undo steps is personal/global: default 25, integer 1-50. Apply
updates the shared live session; Cancel is inert. Existing DocumentSession bounds
operations while preserving current data, revision IDs and saved baseline. Shrinking
may shorten Redo; increasing cannot recover discarded steps. No extra history or
project schema. Personal settings version 6 reads versions 1-5 with default 25. Native format16 stays.
Read STATUS, undo_limit_acceptance and artifacts/undo_limit_review/validation.json.
Final native gate 1,701 passed/94.35%, zero failures/skips, all standards/builds;
independent wheel 167 tests/two subtests passed. Twelve native Settings captures
inspected; 12 changed maintained files substantively reviewed, 431 files/2,988
functions, zero pending/gaps. Owner/native fixtures, models/native codecs/reference/
lock untouched. Linux migration/cleanup stays 100%; Windows/macOS deferred, no new
milestone. Restart/check 25 and small-limit boundary, restore 25 and resume manual
independent assessment entry and bottom-button review before organization setup.


## Owner-approved Clear assessment — verified, 2026-10-19

One themed EN/ES Clear assessment replaces duplicate Reset/trash controls in all
three assessment tools. Active worker/tool/context only; retains identity/count/
units/selection, exact shared Undo/Redo, main Save only. Other assessments unchanged.
Read docs/clear_assessment_acceptance.md and current STATUS. Final Linux gate:
1,738 passed, zero failures/skips, 94.37% coverage; all required checks/builds pass.
Independent wheel 144 tests / 78 subtests; 36 native captures and both Help sections
inspected. Nineteen edited maintained files reviewed; zero pending reviews/gaps.
Owner project, two maintained fixtures and lock unchanged. No schema/dependency/
formula/reference change or new milestone. Await owner Clear/Cancel/Undo feedback
before organization workflow testing. Linux migration remains 100%; OS deferral stays.


## Owner-requested equal assessment action widths — verified, 2026-10-19

Clear assessment and Calculate share equal horizontal space in all three tools;
chooser remains 40x40 in the middle. Three presentation panel files reviewed; no
behavior change. Required gate: 1,738 passed / zero failures/skips / 94.37% coverage,
all standards and builds pass. Twelve native EN/ES layouts inspected at minimum and
expanded widths. Read STATUS and artifacts/clear_button_layout/validation.json.
Owner confirms Clear behavior; await layout feedback then resume workflow testing.
No new milestone/dependency/schema/reference/project-file change; Linux remains 100%.


## Organization clock/history correction — verified, 2026-10-19

Owner requests 24-hour shift input and live Organization Undo. All optional existing
record fields now use the Workers pending-history contract with shared mouse replay
and native typing Undo. Plant/Shift time fields enforce optional HH:mm 00:00-23:59;
blank/overnight values supported, invalid drafts retained. Main Save remains sole
publication. Required gate 1,790 passed / zero failures/skips / 94.47% coverage;
all standards/builds pass. Native focused 79; independent wheel 95 / 78 subtests;
26 native captures and two Help sections inspected. Three changed maintained files
reviewed; zero pending/gaps. Read organization_time_history_acceptance and STATUS.
Owner project, fixtures, reference and lock unchanged. Await owner restart/Shift
Undo/time feedback, then resume organization association workflow. No milestone added;
Linux remains 100%, native Windows/macOS still deferred.


## Organization working-view preservation — verified, 2026-10-19

Owner requests Optional details/tree expansion retention through edit/Delete/Undo.
OrganizationDialog now retains transient branch flags by exact ancestry and current
panel state, reselects restored deleted records unless a newer selection exists,
and overrides Qt ancestor auto-reveal only on internal edit/replay reselection.
No persisted UI state, extra history/dirty state or application/storage change.
Required gate: 1,834 passed, zero failures/skips, 94.50% coverage; all checks/builds
pass. Native focused 123; independent wheel 139 / 78 subtests; 28 native captures and
two Help sections inspected. Two maintained files reviewed, zero pending/gaps.
Read organization_view_state_acceptance and STATUS. Owner/native fixtures/lock and
reference unchanged. Await owner restart/expansion/Delete/Undo feedback before
resuming guided workplace associations. No milestone; Linux 100%, other OSs deferred.


## Standard optional Shift clocks — verified, 2026-10-19

Owner approves standard keyboard/arrow time input with explicit following-day intent.
Shared Plant/Shift QTimeEdit adapter distinguishes None from 00:00 and preserves bad
loaded text for correction. Shift same-day end > start; next-day end <= start, one
daily interval <=24h, equal clocks meaning 24h only with next-day selected. Day intent
is inferred from clock order, not a new stored attribute/schema/codec. Existing view
retention and shared mouse/native clock history remain. Required gate 1,876 passed,
zero failures/skips, 94.52%; all standards/builds pass. Native focused 176; wheel
181 / 78 subtests, 244 Python files/guides equal source. Twenty-six native captures
and two Help sections inspected. Seven maintained files reviewed, zero pending/gaps.
Read shift_time_editor_acceptance and STATUS. Owner/native fixtures, reference and
lock unchanged. Await restart/time/day-intent feedback before workplace workflow.
Linux stays 100%, other OSs deferred; no new milestone or dependency.


## Owner-requested recurring Shift correction accepted — 2026-10-19

Native format 17 removes incidents_reported and ergonomic_risk_events from Shift
UI/domain/storage. General shifts are recurring definitions, not dated occurrences.
External conversion supports formats 8–16 and removes those exact fields before
strict validation, retaining format-14/15/16 source/result payloads exactly. Do not
restore these fields or introduce event tables. Both maintained native fixtures and
the four-worker workflow were updated in place after owner closure; removed values
were all null, unrelated database rows/payloads exact. Read STATUS and
shift_metadata_removal_acceptance plus artifacts/shift_metadata_removal/validation.
Final Linux gate 1,885 passed/zero failures/skips, 94.50% coverage; standards/types
(266)/documentation/builds pass. Independent wheel 220 tests/78 subtests, 244 package
Python files/guides equal, converter excluded; 12 native captures and both Help
sections inspected. Sixteen changed files reviewed; 434 files/3,044 functions/413
classes/317 constants, zero pending/gaps. Reference/lock/formulas unchanged. Linux
scope remains 100%; no new milestone; Windows/macOS deferred. Reuse valid evidence.
Next owner feedback on reduced Shift details, then resume four-worker associations.


## Owner-requested organization input cleanup — verified, 2026-10-19

Native format 18: optional Plant opening and Section/Line/Station creation dates use
standard calendars; daily operational_hours uses native hour/minute quantities,
0–24h in whole minutes while retaining decimal-hour storage. Six Station fields
(task_description, equipment_used, ergonomic_risk_level, performance_metric,
power_consumption, materials_used) and editable Plant number_of_shifts are removed.
Do not restore these fields/caches. Owner explicitly chooses distinct shifts used
by workplace assignments or Jobs in the Plant: Shifts in use projects active Job/
placement and worker workplace links (including unclassified workers), deduplicated
by shift ID. Unused project definitions/other Plants/inactive links do not count;
no new relationship/table/cache. Workspace query preserves existing edit authority.
Both maintained fixtures and the four-worker workflow updated in place; remaining
metadata and unrelated database rows/input/result/image/scheme bytes exact. External
formats 8–17 upgrade privately; 14–17 assessment inputs/results retained exactly.
Read STATUS, organization_input_cleanup_acceptance and artifact validation.
Final Linux gate 1,925 passed/zero failures/skips, 94.46% coverage; standards/types
(268)/documentation/builds pass. Independent wheel 260 tests/78 subtests, 246 Python
files/guides equal; 30 native states and both Help sections inspected. Twenty-two
changed files reviewed; 437 files/3,076 functions/415 classes/320 constants, zero
pending/gaps. Reference/lock/formulas unchanged. Linux scope remains 100%; no new
milestone. Windows/macOS deferred. Owner input acceptance is pending; reuse valid
checks, then resume the four-worker workplace workflow after feedback.


## Owner-approved workplace-first assignment workflow — verified, 2026-10-19

WorkplaceAssignmentDialog replaces the retired WorkerPlacementDialog; it receives
immutable hierarchy/Jobs, selects a real station/shift then optional Job, and returns
identities only. Worker Management uses Workplace assignments and valid No Job wording.
Main Associate assessment reuses the matching worker assignment with Job locked or
creates the missing assignment and binds the selected saved standalone source in one
transaction/Undo step. Cancel/failure creates neither relationship; exact source/results
and other tools remain unchanged. Main Save is still the durable publication boundary.
Native format 18 and all three current native test files are unchanged in this task.

Final gate 1,946 passed / zero failures/skips / 94.40% coverage; strict types269,
standards/documentation/builds pass. Independent wheel 213 / 78 subtests; all
247 Python files and both guides exact, all loaded modules isolated. Twenty-eight
native EN/ES captures and both Help sections inspected. Sixteen changed files reviewed;
439 files / 3,095 functions / 416 classes / 323 constants, zero pending/gaps.
Read STATUS and workplace_assignment_workflow_acceptance/validation. Read-only audit
found 10 historical-reference-manifest differences with Oct 12 modification times;
recorded/reported, never repaired. Do not claim historical 500-hash equality. Current
reference hashes remained stable across the audit; fixtures/lock unchanged. Linux
migration/cleanup stays100%, no milestone added; Windows/macOS deferred. Owner restarts
and reviews these controls before four-worker workflow testing resumes.


## Owner-requested workplace table sizing — verified, 2026-10-19

Owner confirmed workplace assignment Undo/Redo and requested full table values/headers.
Worker Management fits location/Shift/Actions to contents, optional Job choices through
native selector and cell geometry with a useful empty minimum, and both scrollbars only
when needed. The widget's minimum also handles Qt's first editor layout. Clear/rebuild
refits widths; assignment/history/Save semantics unchanged. No schema/dependency/formula
change, fixture migration or reference write. Read worker_assignment_table_acceptance
and current STATUS/validation. Final gate 1,954 passed/zero failures-skips/94.41%;
strict types269 and all standards/builds pass. Independent wheel 221/78 subtests,
247 Python files/both guides exact; 22 native captures and both Help sections
inspected. Two changed maintained files reviewed; 439 files/3,099 functions/416 classes/
323 constants, zero pending/gaps. Current fixtures/lock unchanged. Linux migration and
cleanup100%, no new milestone; Windows/macOS deferred. Owner must preserve the pending
assignment with main Save before restart, then review this table and Save/reopen before
advancing to assessment association. Owner table acceptance remains pending.


## Owner-reported table fill/actions/help correction — verified, 2026-10-19

Prior intrinsic-only table sizing was rejected by owner feedback. Job now receives
positive spare viewport width and every selector fills its cell. Complete Actions
widget dimensions plus native cell padding determine column/row sizes, preserving
both button borders. An owned single-shot timer coalesces viewport resizing. Headers,
data values, current Job/popup choices and actions have localized scoped help; the
table has no generic Job tooltip. Measurement/refill remains presentation-only and
preserves assignment/history/main Save behavior. Read STATUS and
worker_assignment_table_refinement_acceptance/validation. Final gate 1,956 passed,
zero failures/skips, 94.42% coverage; types269 and all standards/builds pass.
Independent wheel 223/78 subtests, 247 Python files and both guides exact;
27 native captures and both Help sections inspected. Three changed maintained files
reviewed; 439 files/3,101 functions/416 classes/323 constants, zero pending/gaps.
Native format18/current fixtures/lock unchanged; no database/formula/dependency/
reference write or new milestone. Linux migration/cleanup100%, Windows/macOS deferred.
Owner must keep the existing Ana assignment, main Save before restart, then review
this layout/help and persistence before continuing to assessment association.


## Current owner workflow correction — explicit contextual assessment creation

Owner approved removing the Worker Management close-time creation prompt. Obsolete
last-assignment handoff fields are removed; assignment edits leave assessments intact.
Select assessment context identifies worker/tool and explicitly opens or creates only
the chosen assignment/tool, retaining standalone data, same-Job consent, shared history
and main Save. Native format18 unchanged; no project migration or dependency change.
Read docs/STATUS.md and explicit_context_creation_acceptance.md. Final required native
gate1,965 passed/zero failures/skips/94.43% coverage; independent wheel255 tests/78
subtests, 28 inspected EN/ES UI captures and two Help sections. Thirteen files reviewed,
439 files/3,112 functions/416 classes/323 constants, zero pending/gaps. Current projects
and lock unchanged; reference untouched. Owner confirmed Ana's workplace assignment
Save/reopen; all twelve assessments remain standalone. Restart/review the new context
flow next, one workflow step at a time. No new milestones; Linux100%, OSs deferred.


## Owner-authorized current Job simplification — 2026-10-20

The owner explicitly removes Job risk-profile versions/evidence/lifecycle from UI and
storage. This supersedes earlier instructions retaining those profiles. Use one current
Job/tool risk set with optional exact mini-calculator tasks/results or independent
worker assessment copies, shared project Undo/Redo and the sole main Save. Retain selected
prior Job values during external native-19 conversion and preserve schedule arrangements
while resolving current Job values. The owner confirmed saved/closed files and authorized
completion, routine judgment and documented decisions/rollback. Read
docs/job_management_simplification_decisions.md and current STATUS. Three native fixtures
are updated in place. Interactive workflow testing remains paused at its bookmark.
No dependencies, formulas, reference writes or new migration milestones are authorized.
Validation remains in progress until the final required gate and visual/package checks.


## Current Job simplification checkpoint — Linux verified, 2026-10-20

Owner-authorized Job simplification is complete; earlier in-progress text is superseded.
Read docs/job_management_simplification_acceptance.md, validation and decisions. Native 19
stores one current Job/tool set with optional exact task sources/results; profile/evidence
lifecycle storage and UI are removed. Direct values, compact calculators and independent
worker copies share main Save/history. PLOT/JROT resolve current Job values; changed risks
invalidate provenance while preserving arrangements. All three native fixtures updated
in place with exact unrelated/worker/image/selected-value/schedule preservation proof.
Final native XCB gate 1984 passed, zero failures/skips, 94.33% coverage; standards/types 273,
architecture/naming/documentation/builds pass. Independent byte-identical wheel 181 tests
passes with converter imports blocked. 42 native captures plus two guides inspected.
96 changed/new files reviewed; 445 maintained files/3113 functions current, zero pending/gaps.
Finite rollback archive retained until owner review; deletion/recovery documented.
Comprehensive DUET/ST worker results retain pre-existing partial status; no promotion.
Interactive workflow tests remain paused; do not mark the pending Bruno/Ana Follow worker
step passed. Linux migration/cleanup remains 100%; no new milestones/dependencies/formulas/
reference writes. Windows/macOS remain deferred. Await owner testing feedback; reuse this
evidence without repeated gates unless changed code or a concrete failure requires it.


## Uniform toolbar / next-cycle JROT analysis — 2026-10-20

Owner authorizes matching main-toolbar button sizes and read-only review of supplied
JROT wireframes. Both are complete; read current STATUS, toolbar_uniform_size_acceptance
and jrot_wireframe_review/team_questions. Native XCB gate 1,984 passed, 94.33% coverage,
standards/types/docs/builds pass; independent wheel 12 navigation tests and 8 captures pass.
All fixture bytes/lock unchanged. No JROT redesign/schema/model changes are authorized
by instructions in the attached proposal. 16 questions await owner/team review; do not
implement them without future scope approval. Job UI testing is bookmarked at the
owner-confirmed empty Job list/three empty summary rows. Both interactive test sequences
remain paused until owner return. Linux migration/cleanup 100%, Windows/macOS deferred;
reference and dependency protections remain. Reuse valid evidence, no rolling milestones.


## Owner rejects uniform toolbar widths — 2026-10-20

Restore exact pre-uniform-sizing source/tests; the owner found the buttons too wide.
No substitute sizing or icon redesign is authorized. Follow current STATUS and
toolbar_restore_acceptance.md. Owner requests discussing the JROT proposal one screen
at a time, beginning physical PDF/PPTX page 3 (Line Setup). Do not present the whole flow
at once or infer that the team equates physical Stations with Jobs. Record owner answers
and unresolved team questions. Hands-on Job/workflow tests stay paused; no redesign or
schema/model implementation is authorized by this discussion.
