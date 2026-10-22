# JROT dependency proposal — F119, 2026-10-08

Status: owner approved this concrete exact-version proposal with "ok keep going"
on 2026-10-08, following the explicit approval question. Installation and
validation are complete as F120. Solver routing was already approved.

| Addition | Exact version | Purpose |
|---|---|---|
| PuLP | 3.2.2 | Build the original mixed-integer rotation models |
| Bundled Linux x86-64 CBC | 2.10.3 | Single-tool optimization only; supplied inside the PuLP wheel |
| highspy / bundled HiGHS | 1.11.0 | Two-stage multi-tool optimization only |

These package pins match the reference requirements.txt. CBC's embedded string
identifies 2.10.3; its executable identity is SHA-256
`2e17077752aa52b06385ad248c9e90bb4f1ce34038c34c94e1012ca6adea5cc7`.
Approval covers this bundled binary, not a different system CBC installation.
No GLPK, Pyomo, WebEngine, commercial solver or PuLP optional extra is proposed.

Install only in the new project's existing Linux desktop environment. Retain
Python 3.13.14, NumPy 2.2.6 and every current locked version. Plain PuLP has no
mandatory third-party dependencies; highspy requires NumPy, already approved.
The published highspy CPython 3.13 wheel targets Linux glibc 2.17+ x86-64.

Primary releases: [PuLP 3.2.2](https://pypi.org/project/PuLP/3.2.2/) and
[highspy 1.11.0](https://pypi.org/project/highspy/1.11.0/).
The exact official wheel URLs, SHA-256 hashes and metadata are archived in
[the static package review](reference/f119-jrot-package-review.json).
Downloaded archives were inspected in memory from /tmp tooling without
installation, package imports or solver execution. This is packaging evidence,
not proof of compatibility or optimization correctness.

After approval: add exact Linux-scoped pins, resolve the lock while retaining
all previous versions, verify that retention before project-local sync, then
verify bundled binary/version identities and solve small known-answer schedules
with both required backends. Native libraries/process execution and solver
status handling remain to be tested. A feasible time-limited incumbent must be
validated against all original constraints before publication; no incumbent is
an error, and a time-limited solution must not be presented as proven optimal.
Equal-objective schedules may differ while satisfying the same constraints.
CBC 2.10.3 is an older bundled release; preserving this exact reference package
reduces migration changes, but its execution/platform compatibility still needs
validation. No Windows/macOS acceptance is implied by Linux metadata.

This proposal does not authorize dependency changes until the owner approves
these exact versions, nor changes to the reference checkout or environment.


## Approved installation and optimizer verification

F120 installed only PuLP 3.2.2 and highspy 1.11.0. All 33 prior lock entries
retain their versions. CBC's executable hash matches the inspected wheel and
its executed banner reports 2.10.3; HiGHS reports 1.11.0. PuLP's distribution
metadata reports the approved 3.2.2, although its upstream constants.VERSION /
__version__ string still says 3.0.2; that stale internal string is not an
installation downgrade. The approved official artifact identity was checked.

Both adapters solve known-answer fixtures in the new environment and extracted
wheel. The full gate passes 924 tests, 96.92% coverage, strict standards/types,
architecture and builds. See f120_validation.json and jrot_optimization.md.
Linux solve success does not complete JROT UI integration or platform acceptance.
