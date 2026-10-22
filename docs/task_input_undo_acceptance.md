# Pending task-input Undo — owner-reported correction, 2026-10-18

Current granularity contract: the owner subsequently requires one completed task cell
per history step. See [task-cell history acceptance](task_cell_history_acceptance.md).
The checkpoint evidence below remains historical; availability/rebind fixes are reused.


Follow-up: the owner subsequently found a repeated-branch UI refresh defect. Its
reproduction, operation/destination correction and expanded acceptance are in
[repeated task Undo and folder acceptance](repeated_task_undo_and_folder_acceptance.md).
The evidence below characterizes the earlier single-edit correction.

The owner reports Ana's fifteen-row LiFFT assessment with Task 1 calculated: entering
Task 2 clears results but does not enable Undo until Calculate. The previous adapter
observed only accepted source history, while grid text remained pending until a commit.
This is a bounded Linux behavior correction; migration and cleanup remain 100% complete.
No additional milestone, dependency, schema, formula or assessment version is introduced.

## Correction and contracts

Each tool's existing grid parser now has a pure inspection boundary shared by normal
commit and history availability. It keeps task identities, display interpretation,
decimal rules, canonical units, missing values and unchanged source precision intact.
Panels project their existing widgets once through the same row-reading method for
both inspection and acceptance. A valid changed source exposes main Undo immediately,
including a started incomplete second task; inspection does not accept input, create
history, truncate Redo, calculate or save. Invalid/stale input blocks project replay;
valid no-op text preserves the existing history branch.

The existing ProjectHistoryActions prepare/pending hooks accept a grid edit immediately
before replay, stage it through the shared application session, then Undo restores the
previous source and its exact matching calculation. Redo restores the edited inputs and
clears the obsolete result. This adds no second history stack. Mouse Undo/Redo toolbar
buttons take focus so they dispatch project replay; keyboard shortcuts in a text field
retain native typing Undo. Normal Calculate and main Save retain their existing roles.

## Acceptance evidence

Twelve new real-control regressions cover LiFFT/DUET/ST, English/Spanish and both unit
systems. Each creates, calculates, saves and reopens a disposable fifteen-row assessment
with only Task 1 populated. It checks empty initial history, immediate pending Undo,
unchanged accepted source/file during inspection, actual mouse replay, exact source and
result recovery, invalid text and native typing Undo, preserved Redo, and main Save/reopen.
Existing resizing, ownership and result tests remain in place.

Native XCB/Xvfb :109 visual verification uses private copies of the owner workflow
project. Eighteen raw captures cover pending, Undo and Redo for all three tools in EN/ES;
all were inspected, including toolbar states, task rows, VTK, gauges, result cards and
bottom controls. Ana's 13.2% result returns without recalculation; DUET and ST similarly
restore their matching results. No changed-interface clipping was observed at the
captured size. Existing unrelated Settings fit observations remain in the review register.

Required native gate: **1,461 tests passed, zero failures/skips, 94.35% combined
coverage**. Ruff/format, strict types (265), architecture/naming, documentation/review
and wheel/sdist builds pass. The independent extracted wheel passes **90 focused
tests**; all 243 package Python files and both guides equal current reviewed source.
Nine changed maintained files are substantively reviewed; inventory has 428 files /
2,957 functions / 412 classes / 312 constants, zero pending reviews/gaps. Logs, explicit
review decisions, captures and package evidence are in artifacts/task_input_undo_review. The protected-file hash record covers both maintained
native fixtures, the owner workflow project and uv.lock. They are not edited by this
correction; captures and regressions use private copies or temporary native projects.
The original reference checkout is untouched. Windows/macOS remain deferred.

Restart the application to load the correction. Resume the owner's existing workflow:
enter a Task 2 value, click main Undo before Calculate, verify Task 2 is blank and the
previous result returns; Redo should restore the input with results cleared. Only main
Save publishes the selected final state. No automatic owner-file rewrite is performed.
