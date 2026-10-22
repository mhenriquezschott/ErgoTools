# Job workplace selection — F58

The original JobWorkplaceDialog in src/job_window.py supplies a selection across
shifts to replace_active_job_placements in src/job_placement_repository.py.
The migrated operation and presenter preserve that contract while removing SQL
and project ownership decisions from future widget event handlers.

replace_active_placements is pure. It deactivates removed placements, reactivates
the highest-ID inactive placement for newly selected workplaces, or allocates a
new placement. Existing dates, notes, worker assignments, assessment links and
other jobs are retained. An inactive job may still have its placements edited,
as in the original operation. Empty selection makes a job organization-neutral;
duplicate selections collapse. Existing active selections remain untouched.

New placement IDs use the snapshot maximum and deterministic workplace ordering.
The original iterates a set, so allocation order across multiple new workplaces
is not a stable reference guarantee. The migrated operation makes this explicit;
expected-value persistence rejects concurrent additions instead of reusing IDs.
Existing identities and highest-ID reactivation behavior remain preserved.
As in the reference, reactivation retains old date bounds; this step does not
reinterpret validity dates or introduce a new business rule.

JobWorkplaces loads workspace-owned hierarchy/job views and supplies all station/
shift choices plus the active selection. Save validates exact view authority and
membership, then uses atomic expected-value job replacement. A successful save
returns a fresh view. Old callbacks fail after refresh, save or project close.
Invalid requests and I/O failures leave saved data intact; retry is possible
while authority remains valid. External job changes are detected under the write
lock and require reload. External hierarchy changes receive repository membership
validation; the presenter is not a cross-process subscription mechanism.

Saving placement selection does not save/discard assessment source edits, change
their undo history, transfer assessments, or delete worker assignments. Historical
assignment protection remains enforced by the existing repository. No new schema,
dependency or UI is introduced.

Four captured reference cases execute the original function using the original
Python baseline and an in-memory SQLite fixture; no operational files are used.
The source SHA is recorded in tests/fixtures/job_placements_reference.json and
verified by reference/f58-verify.py.txt. Eight added test cases cover reference
transitions, duplicates, missing/untyped selections, all-shift persistence, dirty
source protection, assessment ownership, stale callbacks, I/O retry and competing
saved changes. Both new modules have 100% combined coverage.

All 500 tests pass; overall combined coverage is 98.96%. Ruff/format, strict mypy
(103 source files), architecture checks, builds and isolated-wheel save/reactivation
pass. All 500 original files and dependency lock remain unchanged. Evidence is
f58_validation.json. No visual acceptance is claimed because no UI changed.

Next: migrate the existing JobWorkplaceDialog layout and interaction code onto
this presenter, retaining its shift selections, hierarchy checks, filtering and
buttons, and verify its native states. The final integrated job/worker screens,
full worker records and broader project setup are still incomplete.
