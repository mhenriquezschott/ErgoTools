# HiGHS-only JROT runtime

All new rotations use highspy 1.11.0 directly. There is no solver-selection setting
or PuLP/CBC runtime dependency. Previously saved results retain their original solver
attribution as read-only provenance; this cannot select an old execution engine.

## Mathematical behavior

Original workflow: one-tool minimax and existing three-tool ceiling/spread objectives
remain. Guided workflow: all seven nonempty tool subsets use minimax followed by spread
minimization while preserving first-pass ceilings. Generation remains feasibility-only.
One-worker-per-Job/block, fixed/excluded/adjacency rules, duration weighting, break policy,
opaque IDs, 0.01 relative gap, 0.0001 ceiling slack and 0.00001 binary tolerance remain.
No repetition/damage/risk calculator or project schema changes are introduced.

The direct model uses the same linear coefficients and bounds. Each solve pass copies
the current native model into a fresh HiGHS instance. This matters because clearSolver
alone does not reset elapsed runtime. Each fresh pass gets its full requested seconds;
no prior incumbent/time is silently reused. Native API/model/primal statuses are checked
before independent numeric, binary, staffing/rule and ceiling checks. Limited feasible
incumbents are labeled feasible; missing incumbents fail. Only validated results are
retained for subsequent ceiling reads; failure never substitutes an earlier pass.

## Preferences and installation

Personal settings version11 omits the solver-choice field. Version10's former field is
recognized only when decoding that old version, discarded and never exposed as a user
setting; all other options survive. Read alone writes nothing. Future saves use version11.
Fresh Settings and saved projects require no manual solver selection.

Installation follows [the platform setup guide](installation.md). Linux uses the
locked desktop extra; Windows and macOS use their platform trial requirements.
Native Windows/macOS execution remains a separate deployment acceptance step.

## Verification

The regression suite covers known optima, infeasible restrictions, unequal durations,
all nonempty tool subsets, secondary balancing, cancellation and saved-result compatibility.
`tests/test_highs_runtime.py` checks direct native execution without PuLP, while
`tests/test_jrot_known_solutions.py` compares schedules with independently known answers.
Run `bash tools/check.sh` for the complete required Linux gate.

## Native startup order on Windows

The desktop composition root imports highspy before PyQt5. In the Windows 11,
Python 3.13.14, highspy 1.11.0 deployment probe, Qt-first imports caused native
access violation `0xc0000005` during automatic-thread MIP execution. The early-initialization probe
(import plus a brief HiGHS instance/version read) completed the same model in a Qt
worker with the expected optimum; limiting
the native solve to one thread also passed, but is not required by this correction.

Initialization order is centralized in bootstrap, shared by installed and module
entry points. Automatic solver threading, model coefficients, limits and scientific
calculations remain unchanged. Fresh-process regressions observe the actual first Qt
import; in-process cached imports cannot verify this boundary. The probe does not separate import order from early instance creation, identify
the underlying native DLL or certify every Windows optimization scenario. The
minimal import-order correction still requires a Windows saved-project retest. Repeat a real saved-project solve
after updating the application.
