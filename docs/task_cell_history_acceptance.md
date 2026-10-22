# Task-input history granularity — owner correction, 2026-10-18

The owner expects Arm 50 followed by Load 60 to reverse Load first, then Arm. Earlier
corrections addressed Undo availability and repeated view refresh, but the grid still
submitted multiple pending cells as one source command. Those tests missed the
multi-field transaction boundary. This checkpoint corrects that boundary across every
task input in LiFFT, DUET and ST, rather than introducing another history engine.
Linux migration and cleanup remain complete at 100%; no additional milestone is active.

## Accepted history contract

A numeric field completes when the user leaves it or presses Enter. Each rating or
direction choice completes immediately. Each completion submits only its stable task
ID/input column through the existing bound presenter/parser and immutable source
command. One completed cell is one step in the existing ProjectEditingSession cursor.
Leaving a field for a menu/dialog is also normal completion; read-only actions such
as Open project folder do not parse inputs themselves or perform a durable Save.
The command never sweeps other unfinished widget values into that step. Valid siblings
can complete while another cell contains invalid text; the invalid text stays local
and project replay remains interlocked until correction. Revisited fields add new
chronological steps. Focused text Ctrl+Z keeps native typing Undo; individual keystrokes
are not separate project commands. Unchanged completion adds none and retains Redo.

For the owner's example, Task 2 is initially blank:

| Operation | Arm | Load |
| --- | --- | --- |
| Enter Arm, then move to Load | 50 | blank |
| Enter Load | 50 | 60 |
| Main Undo | 50 | blank |
| Main Undo again | blank | blank |
| Main Redo | 50 | blank |
| Main Redo again | 50 | 60 |

The last still-focused valid numeric cell completes before mouse toolbar replay, so
it reverses first even without Enter/Tab/Calculate. Completed input never rebuilds its
widgets or steals the next field's focus. The existing Modified/context projection
updates when the completed field enters shared history, without waiting for Calculate. Programmatic projection disables completion
before retiring focused controls, preventing phantom edits during replay/reload.
Source-bound results clear on changed inputs and return exactly when Undo restores
their matching source. No automatic calculation, durable Save or assessment version is
introduced. Main Save remains the only publication boundary; explicit bulk operations
keep their own atomic command boundary.

## Implementation and architecture

The existing pure parse_grid/commit_grid paths accept an optional cell selection. Task
identity/order, exact source/display binding and coordinate validity precede mutation.
Only the selected text/choice is parsed or converted; unselected canonical values and
selector conventions remain exact, even when their widgets contain invalid text. The
default None retains whole-grid acceptance for existing explicit bulk callers.
Numeric editingFinished and selector signals capture stable task/column coordinates.
The existing host notification stages accepted commands into the shared private project
session. No second stack, SQL/table/schema, calculator, dependency or application/domain
history change is made. All seven changed package files remain in presentation.

## Regression evidence

The new completion-boundary regression fails against the preceding accepted wheel:
leaving the first field still leaves project revision 0 instead of accepting one edit.
The current focused module contains 106 cases:

- 72 across all nine input types, both languages/units, populated/empty rows, and
  Tab/Enter/mouse completion; actual widgets, one revision per field and every
  intermediate Undo/Redo source/result are checked.
- 12 last-pending-field/revisited-field cases covering the exact owner sequence.
- 12 invalid-sibling cases showing valid edits stay separate through correction.
- Three coordinate/stale-binding/no-op/native-typing cases.
- Four comma-decimal/opposite-display-unit cases preserving untouched 49.05 exactly.
- Three programmatic projection cases proving retiring controls create no history.

Main Save/reopen checks retain the final source; inspection/replay does not change
project bytes. Existing focused regressions also pass (168 pass, two native-OpenGL
cases skipped in the early offscreen run); the required native full gate supersedes
that limited run. The preliminary gate found three older whole-grid grouping expectations (1,642 pass,
three fail); those source-history assertions now follow the approved individual-cell
boundary while retaining their calculation, invalid-input, Reset and reopen checks.
The native corrective focus suite passes 120 tests. Native package results,
documentation review and the final gate are recorded in STATUS and
artifacts/task_cell_history_review.

Final required native gate: **1,645 passed, zero failures/skips, 94.35% combined
coverage**; strict types (265), standards/format, architecture/naming, complete
documentation/review and builds pass. The independent extracted wheel passes **166
focused tests**; all 243 package Python files and both guides match reviewed source.
All ten changed maintained files are substantively reviewed: 429 files / 2,971
functions / 412 classes / 312 constants, zero pending reviews or structural gaps.
Seven changed package files are presentation only; 236 package Python files and
76 resources remain byte-equal to the previous accepted wheel.

## Native UI and protection evidence

Thirty native XCB/Xvfb :111 captures cover both entered values, Undo second only, Undo
first/result restoration, Redo first only and Redo second, for all three tools in EN/ES.
All raw states were inspected through enlarged detail and full-window contact sheets,
including task inputs, toolbar availability, VTK, gauges/result cards and bottom controls.
Controls retain their established layout; no changed-state clipping was observed at
the captured size. UI geometry, labels, themes and the original ST Tab order are unchanged.
Captures use private copies and recalculate only those copies; the owner workflow file
and both maintained comprehensive projects remain untouched. Protected hash records
also cover uv.lock. Scientific/domain/application/storage code and the original reference
checkout are unchanged. Windows/macOS acceptance remains deferred.

Restart ErgoTools, load the existing workflow project and repeat Task 2 Arm 50 then
Load 60. Main Undo should now clear only Load, then Arm on the following press; Redo
restores them in order. Continue the existing owner workflow testing without adding
milestones or unrelated repairs.
