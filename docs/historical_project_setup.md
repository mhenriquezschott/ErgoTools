# Initialized historical projects — F57

AssessmentProjectFile.create_initialized_historical creates a version-six project
from explicit metadata, hierarchy, job catalog, historical entry and first source.
It validates project identity, job/hierarchy membership, assignment existence,
model identity and source encoding before creating a destination. It uses the
existing stores and format; it is not a legacy import or schema migration.

The returned connection owns a fully persisted setup and first assessment.
Factories reject existing paths exclusively. Initialization errors close the new
connection and remove the new file; existing destinations are not adopted or
removed. Each adapter commits its own operation. This is exception cleanup, not
a single transaction spanning setup or crash-atomic publication. As with existing
creation factories, concurrent readers during construction, power-loss recovery
and cleanup failures require later publication/recovery policy.

Inputs explicitly specify version/status/currentness. The factory does not invent
workers, infer ownership from labels or enforce active-only selection; the setup
presenter will supply that policy. Worker entries remain identity/name records,
not complete demographics. Full worker editing and the existing setup UI are
still pending. The temporary window's default New action is unchanged.

Source units are retained exactly, independently of project defaults. Ten
parameterized round trips exercise LiFFT imperial/metric sources with nonempty
tasks, DUET, and TST imperial/metric sources against both project defaults.
DUET has no force/length unit field. These are storage checks, not evidence of
resolved LiFFT/TST scientific conversion gates.

Six additional cases cover failures at all three persistence steps with same-path
retry, invalid ownership/model preflight, existing-destination preservation and
actual ProjectWorkspace creation, dirty cancellation, editing/save and reopen.
The workspace uses its existing injected creator interface. Its established
ordering saves an old source, when explicitly requested, before calling creation;
a failed creation can therefore leave that old source saved. Cancel performs no
creation. No new coordinator abstraction or UI control was introduced.

Validation: 492 tests pass, combined coverage 98.95%; Ruff/format, strict mypy
(101 source files), architecture and builds pass. The isolated wheel creates and
reopens a metric-default project retaining an imperial source and exact hierarchy,
jobs and historical ownership. All 500 reference files and the dependency lock
remain unchanged. See f57_validation.json and reference/f57-verify.py.txt.
No UI changed, so this step requires no new visual acceptance.

Next: connect setup/work-management use cases to migrated existing screens, using
the original UI code and behavior as the starting point. Complete worker records,
integrated three-model workflows, metric/imperial acceptance, PLOT/JROT and copied
comprehensive-project validation remain unfinished.
