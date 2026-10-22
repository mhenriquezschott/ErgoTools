# Active JROT optimizer migration — F120, 2026-10-08

## Implemented boundary

`domain.rotation` supplies frozen, slotted WorkerRotation, RotationRisk,
RotationProblem and RotationSolution values. Target keys are opaque identities,
not editable cell labels; the upcoming repository/UI must map job, placement and
profile identities onto these keys. Percent coefficients remain dimensionless;
no metric/imperial conversion or localized parsing happens inside optimization.
Zero is valid; missing/nonfinite/negative/over-100 probabilities, duplicate workers
or risk keys, inconsistent blocks and nonpositive limits are rejected explicitly.
The current manual schedule may contain collisions; only the returned optimized
schedule must satisfy per-block uniqueness.

`application.rotation_optimization.RotationOptimizer` is an injected port with
no solver, Qt or storage dependency. The concrete PuLP adapter owns a fresh model
per call; no database reads/writes, UI callbacks or import-time solves occur.
Future persistence owns frozen profile provenance; this slice does not create a
new database format or implement that repository.

## Retained source behavior and concrete corrections

The reviewed active reference is src/rotation_optimizer.py. Single-tool minimizes
maximum worker average probability with CBC only. Multi-tool uses HiGHS for both
stages: minimize sum of tool ceilings; retain each attained ceiling plus 0.0001
percentage points; minimize sum of ceiling-minus-floor spreads. One assignment
per worker/block, total target occurrences and one worker per target/block are
retained. Relative gap is 0.01 and each stage receives the full requested seconds.
The source's redundant unused maximum variable in multi-tool is omitted.

The owner-approved routing supersedes the reference backend helper that preferred
HiGHS for both paths. Missing or failed required solvers raise an actionable
RotationOptimizationError without fallback. Numeric variable names use indices,
so distinct keys such as 'job-A' and 'job A' cannot collide during PuLP label
sanitization. Worker order and target identities survive extraction.

Every variable must be finite and binary within 0.00001; each block must select
one target. A separate domain check verifies worker identities/order, block
counts, target totals and per-block uniqueness. Multi-tool extraction additionally
checks actual schedule averages against first-stage ceilings. Neither a claimed
optimal status nor a merely populated variable list bypasses these checks.
No-incumbent stages raise instead of publishing stale first-stage assignments.
Feasible stopped runs retain FEASIBLE evidence even if PuLP reports the problem
status as Optimal. OPTIMAL means the backend's report under its 1% gap/numeric
tolerances, not proof of an exact mathematical global optimum. Both multi-tool
stage statuses are retained; no probability formula or injury model was changed.

PuLP ships no type marker. `typings/pulp/__init__.pyi` describes just the exercised
3.2.2 public API for strict mypy, without Any or blanket type suppression. Only
its upstream naming spellings have narrow naming exceptions. This development
stub ships in the source archive; the runtime wheel uses installed PuLP itself.

## Verification and limits

26 focused regression cases cover actual CBC/HiGHS routing, zero risk, source
label collisions, missing/invalid coefficients, infeasible target totals, required
backend errors, fractional/absent/nonfinite variables, incomplete blocks, changed
target totals and collisions, feasible stopped status and stage-two no-incumbent /
ceiling violations. Two- and three-worker fixtures independently enumerate legal
schedules to check min-max and the conditional two-stage objective; these checks
do not mirror the MILP implementation. Deterministic injected termination records
test timeout acceptance policy; no flaky wall-clock timeout benchmark is claimed.

The native XCB full gate passes 924 tests, 96.92% coverage, Ruff/format (441 files),
strict mypy (199 source files), architecture and wheel/sdist builds. Independent
extracted-wheel actual solves pass with all ErgoTools imports confined to the
extraction. All 500 reference file hashes remain unchanged. Only the approved
PuLP/highspy additions enter the lock; all 33 prior entries retain versions.
Evidence: f120_validation.json, artifacts/f120-check.log, artifacts/f120-wheel.log.

No UI was changed; no new visual captures were needed or claimed. JROT's main
button is still disabled. Next: scoped scheme persistence and original-layout
edit/save/load/delete form, then optimization/comparison transfer with owned
worker cancel/close lifecycle and main integration. The adapter alone does not
supply background threading, cancellation, localization or visual acceptance.
Original-format compatibility, copied comprehensive project integration and
whole-application/platform acceptance remain in the established plan. No reliable
whole-app completion percentage or finish date is established.
