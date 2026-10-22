# F84 — integrated task-count Settings

The existing Settings toolbar action opens the original owned modal for the active
LiFFT, DUET or ST source. No new controls, assets or layout were introduced. The
modal retains its default count of 10, integer range 1–100 and Set Tasks/Cancel
interaction. It is a task-grid operation; it does not implement the remaining
application preferences window or menu enhancements.

Cancel leaves source and pending editor text untouched. Acceptance intentionally
abandons pending text and creates fresh blank rows, including when the requested
count equals the current count. DUET defaults to OMNI-Res scale 0; ST defaults to
Handling Loads with absent numeric inputs. This follows the original clearing
operation. One Undo restores committed source; discarded pending text is not an
undo snapshot. Redo restores the accepted rows. Results are invalidated, preserving
the existing scientific gates. Source units, assessment identity, original assignment
and historical version do not change. The operation never edits another tool.

`SetDuetTaskCount` and `SetTstTaskCount` are typed immutable application commands,
with expected-source, count, blank-row and unique-identity checks. Presenters own
new task identities and execute through existing project history. The window routes
the accepted modal result to the active presenter. Source units remain separate
from display units. The accepted row count is persisted with the source using the
existing Save mechanism, not stored as a global count preference.

Six parameterized native regression cases exercise both tools: actual modal Cancel
with invalid pending input; accepted 1 and 100 rows; fresh identities; Undo/Redo;
Save/reopen and other-tool preservation; same-count clearing; Spanish modal and
confirmation; invalid presenter counts and invalid/stale command replacements.
The large-grid header assertion waits for the existing queued synchronization to
finish. A fixed short delay had sampled an unfinished native layout; investigation
required no production layout change.

The required gate passed with 668 tests and 96.93% combined statement/branch
coverage, strict mypy on 137 source files, lint/format, architecture and both builds.
The extracted wheel was tested with the approved interpreter/dependencies from an
isolated temporary directory. It passed actual modal Cancel/accept, unit retention,
Save/reopen, Undo, other-tool preservation and renderer cleanup.

Native captures under `artifacts/task-count-integration/` show English DUET and
Spanish ST: default and selected maximum modals, Cancel retaining invalid text,
one blank row, populated Undo and row 100 with sticky headers. At 1550×1015 no new
clipping was observed around the viewport, cards, labels or bottom controls. VTK
framebuffers were composed into Qt captures using the F78 capture method; these
are actual native renders, not inferred avatar placeholders. This is scoped visual
acceptance of the changed operation, not final same-platform whole-app parity.

Evidence is in `f84_validation.json`, `artifacts/f84-check.log` and archived
`reference/f84-verify.py.txt` / `reference/f84-capture.py.txt`. All 500 recorded
reference file hashes and the approved lock remain unchanged. The reference
application/environment and operational datasets were not edited. Remaining
menu/preferences, saved-data selection/Delete and scientific decisions are still
open; this slice does not implement PLOT/JROT or legacy import.
