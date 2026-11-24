# JROT unsuccessful solve handling

Owner-requested correction, 15 November 2026. Scope: infeasible and bounded
no-result outcomes in guided JROT, with a reproducible example in the current
workflow test project. No new milestone, solver model, dependency or schema change.

## Cause and behavior

The native adapter already rejected infeasible or unusable primal results. The
presentation displayed only inline diagnostics, then refreshed the controller.
That refresh could restore a previously kept matrix; later navigation could replace
the unsuccessful-attempt text with the usual retained-result status. The view could
therefore look as if the latest attempt had succeeded.

The application error now carries a portable failure reason. The adapter maps
actual native evidence to proven infeasibility, time exhaustion without a usable
result, or another failure; presentation code does not parse diagnostic strings.
Only a trustworthy infeasible model status is presented as proof of impossibility.

The controller owns a window-local failed-attempt context and message. It clears
new preview/result widgets, disables result actions and prevents fallback to an old
run in both optimization and comparison pages. A localized warning dialog and
prominent persistent banner explain the outcome and what to review. The source
baseline/proposal and previously kept result remain intact. A retry or context
change retires the owned notice, including its matching bottom error, without
clearing unrelated form errors.

Failed attempts are not persisted as accepted runs. On reopening, an older kept
run can still be shown with its retained identity/timestamp. Explicit Cancel
preserves the existing behavior: it applies nothing and can restore an earlier
kept matrix, clearly prefixed by the cancellation notice. A late result whose
input context changed retains its rejection warning and cannot be kept.

A time limit without a complete validated result leaves no new matrix, even if
an earlier optimization pass succeeded. A validated feasible incumbent returned
within a bounded pass remains usable, but is explicitly described as feasible
with optimality unproven. The objective, staffing restrictions, risk thresholds,
weights, pass budgets and ceiling tolerance are unchanged.

## Example and preservation

The owner confirmed the application was saved and closed before publication.
`test_projects/native/jrot_workflow_optimization_test01.ergprj` now includes
**Demo 21 · Infeasible combined restrictions**, using existing workers/Jobs and
six equal blocks. See [manual steps and proof](jrot_infeasible_example.md).

Preparation used a private copy. Actual HiGHS checks cover all seven tool subsets,
both generation and optimization: 14 infeasible runs and 14 corresponding feasible
runs after removing V03's adjacency restriction. Static staffing passes first.
Only the new rotation row is added to the maintained project. All original SQL
rows, remembered selection and schema are exact; integrity and foreign-key checks
pass. Other maintained projects and the dependency lock are unchanged.

Local before/prepared copies and publication evidence are under
`artifacts/jrot_failures_20261115/`. They are review/recovery artifacts, not extra
maintained projects. Remove disposable copies after owner acceptance if no longer
needed; do not restore the whole old backup over subsequent user edits.

## Verification

- Twenty-seven new tests cover portable failure categories, real infeasibility,
  one/two/three-tool rules, first-/second-pass limits with/without valid incumbents,
  proposal generation, prior kept runs, navigation, retry and notice ownership.
- The final full regression passes **2,910 tests** with **91.97% coverage**
  in 958.15 seconds (exit 0).
- The final focused solver/lifecycle/comparison group passes **110 tests**.
  Its broader checks also preserve cancellation and late-result rejection behavior.
- Eighteen final English/Spanish native captures are inspected on private
  Xvfb/GLX with Qt XCB. Timeout captures are controlled worker-boundary cases;
  deterministic adapter tests separately exercise actual native status/primal
  extraction. No artificial claim of a hardware-dependent real timeout is made.
- Standards, strict types (358), architecture, documentation structure/review and
  wheel/source builds pass. Packaged runtime bytes match all four changed modules;
  an independently imported wheel passes the real infeasible/relaxed solve pair.
- The required check script stops at 23 supplied proposal-original filename
  violations. Their names/bytes are preserved; no blanket exclusion is added.
- A complete run against a superseded intermediate revision was interrupted after
  focused checks exposed needed lifecycle corrections. It is archived as such and
  is not acceptance evidence. The final full run and coverage are recorded in
  `artifacts/jrot_failures_20261115/validation.json`.

Native Windows/macOS rendering is not revalidated in this slice. Accepted Linux
migration scope remains 100%; this correction adds no progress points. No
repository publication or reference-checkout change is performed.
