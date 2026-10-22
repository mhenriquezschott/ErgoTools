# Personal Undo limit — owner-requested bounded history

The owner requests 25 backward steps by default, configurable from 1 to 50 at
application level. Tools > Settings > General > Undo steps owns this personal
preference in English/Spanish. Apply persists it and updates the open shared session
immediately; Cancel retains the previous value. The value applies to future project
sessions too. No .ergprj column, table, codec version or history archive is added.

One shared project chronology remains authoritative for main assessments, Workers,
organization/Jobs, PLOT and JROT. The budget counts completed operations, including
existing reversible navigation. At most budget plus one immutable states remain.
Successful new commands release oldest excess history; no-ops and rejected commands
retain Redo. Revision IDs remain monotonic, and eviction never changes the current
source/result, recalculates, writes a file or resets the saved-data marker. Save keeps
the retained Undo/Redo branch; opening a project starts a new history as before.

Lowering the budget preserves current data and gives nearest preceding Undo steps
priority; Redo occupies remaining capacity and may be shortened. Raising the budget
cannot recover discarded steps. The UI explains the consequence. Pruning itself is
not undoable and does not require project Save. Text fields retain native typing Undo;
this setting controls shared project operations. Generic diagnostic DocumentSessions
retain their existing unlimited policy unless explicitly configured.

Implementation extends the existing DocumentSession with an idle-checked positive
capacity setter and a small snapshot-trimming helper. ProjectEditingSession validates
the application range and notifies all borrowing actions. ProjectWorkspace loads the
personal budget at activation; Preferences Apply updates the live owner. UserSettings
uses one shared default/range/validation definition. JsonSettingsStore writes personal
format 6, strictly accepts old formats 1-5 with default 25 without rewriting on load,
and rejects invalid/noninteger/bool/out-of-range or malformed settings without reset.
The pre-existing future-version test now uses 7 instead of newly supported 6.
Existing camera/decimal tests expect v6 only after explicit writes. The existing gauge
compatibility fixture removes undo_limit when manufacturing v1-4 payloads, preserving
strict unknown-field rejection rather than loosening the parser. The preliminary full
run (1,695 passed, six compatibility-expectation failures) is retained separately; it
is not represented as final acceptance.

Focused gate: 102 tests and two subtests passed, including 36 new cases for capacity
1/25/50, exact overflow/Undo/Redo, stable revision IDs, branch truncation, saved markers,
shrink while undone, increase after loss, no-op/failed/reentrant behavior, old preference
formats, invalid data, factory policy loading, view-only cleanliness, and actual modal
Apply/Cancel/persistence/task replay across all tools and both languages. Existing
PLOT/JROT/shared history gate: 31 passed. Final required native Linux gate: **1,701 passed, zero failures/skips, 94.35% coverage**;
standards/types (265), architecture/naming, documentation/review and builds pass.
Independent wheel: **167 tests and two subtests passed**; all 243 package Python
files and both packaged EN/ES guides equal reviewed source. Exact package hashes and
results are recorded in artifacts/undo_limit_review/validation.json and STATUS.

Twelve native XCB/Xvfb :113 Settings captures were inspected: General selected with
expanded section tree, no project and populated project, limits 1/25/50, EN/ES.
Contact sheets cover all states; the Spanish loaded/50 original was also inspected
at full size. Label, explanatory note, spin control and Apply/Cancel footer fit;
existing theme and layout remain intact. Owner file was copied only into temporary
private QA locations, never opened for writing. Exact evidence and hashes are under
artifacts/undo_limit_review. Seven package modules and five test modules receive
substantive review; no scientific model, native storage, dependency or reference edits.

Linux migration/cleanup remains 100%, no new milestone; Windows/macOS are deferred.
The old dist/linux M5 bundle is not republished. Next owner step: restart, open the
workflow project and verify General shows 25; choose a small limit, Apply and check
that shared Undo stops there. Restore 25 and resume independent assessment entry and
bottom-button review before organization setup.
