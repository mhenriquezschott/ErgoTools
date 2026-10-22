# Single project Save and shared history — Linux verification, 2026-10-18

The owner authorizes simplifying project saving and exposing one shared chronological
Undo/Redo in editor windows. This bounded workflow correction is implemented and
verified; Linux migration/cleanup remain 100%, without additional milestones.
Owner acceptance of the revised manual workflow is the next step.

## Accepted behavior

Main Save writes accepted workers/demographics, organization, assignments, Jobs/risk
profiles, assessment inputs/results, PLOT images/geometry and complete JROT schemes
as one native project. Management/analysis windows retain valid edits when closed;
internal navigation no longer asks for a separate Save/Discard. Leaving the project
still offers Save/Discard/Cancel. Invalid form text remains available for correction
or explicit cancellation. Application preferences keep their own Apply/Cancel.

Add worker accepts one record and starts another. Existing workers remain editable.
Four additions are four operations: Undo removes W04, then W03, individually; closing
Worker Management adds no action. Its controls and those in organization, Jobs, PLOT,
JROT and the main window use the same project cursor. Record-removing replay identifies
what will be removed and defaults to Cancel. Rejecting confirmation consumes no step.
Restoration, ordinary edits and navigation need no removal confirmation; focused text
editors retain typing Undo. Save retains Undo/Redo, including a pending Redo branch.

PLOT accepts validated gestures, coordinate changes and imported images privately.
Apply to all remains an explicit batch operation. JROT retains partial grid, ID, frozen
pool, scope and provenance across closure/reopening; incomplete entered content blocks
Save/Save As with actionable EN/ES guidance. Complete schedules, including applied
CBC/HiGHS output, join main Save. Unaccepted solver previews remain separate.

Save As publishes accepted content exclusively and activates a clean project session.
Backup copies the last durable Save; exports read accepted open-project data without
saving it. External file effects are not undone. Undo history remains transient and
ends when the project session closes or switches. No schema/table/version/history
storage, dependency, formula, automatic backup or duplicate fixture was introduced.
Native/personal formats remain 16/5; metric/imperial scientific conventions are intact.

## Actual verification

- Required `bash tools/check.sh`: **1,400 passed, zero failures/skips, 94.28% combined
  coverage**; strict types (265), Ruff, formatting, architecture, naming, documentation
  structure/review and wheel/source builds pass.
- All 428 maintained Python/stub files remain reviewed, with zero pending reviews or
  structural gaps. The 42 changed files received renewed substantive contract reviews;
  the inventory covers 2,926 functions, 412 classes and 312 constants.
- The independently extracted final wheel passes **50 native checks** covering worker,
  shared history, source/result transition, solver, partial draft and navigation behavior.
  All 243 packaged Python files and both HTML guides equal current reviewed source;
  the optional external converter remains outside the application wheel.
- **64 EN/ES native captures inspected**: empty/populated/expanded management forms,
  assignments, main LiFFT/DUET/ST with VTK, PLOT analysis/demographics, JROT partial/
  reopened/complete states, removal consent, settings, validation and delete tooltips.
- Tests verify real read-only SQLite publication failure/retry, exact multi-source
  rollback, private-versus-durable reopening, Save As/last-Save Backup, cancelled
  removal consent, native rich-text Undo and Qt teardown/reentrant activation.
- Disposable copies of both maintained comprehensive projects verify exact checkpoint
  restoration through Undo/Redo. Main Save changes only the expected worker-catalog
  row; all unrelated table rows, inputs/results, images and rotation schemes remain exact.
  The maintained fixture bytes are unchanged.

The native tests caught and corrected reentrant session initialization through Qt
focus/collection, focus-only refresh invalidating an editor's Job authority and a
previously empty view seed preventing initial navigation history. The retained-source
and file-boundary assertions were updated to the approved workflow; they were not
replaced with unconditional success assertions.

## Protected files and handoff limits

The owner workflow project was read only, not seeded/corrected/saved. Its current four
workers include Diego at 65 kg; the earlier 85 kg checkpoint is historical. It still
contains no organization, assignments, Jobs or assessments. Reopen it after restarting
the application before resuming owner-driven tests.

The approved lock is unchanged. No original reference file/environment was written.
A read-only comparison finds 490/500 files matching the old manifest and ten differences
with October 12 modification dates, predating this work. The exact paths/current hashes
are recorded; they were neither restored nor falsely reported as matching.

Existing narrow Spanish assignment Actions and JROT recommendation tables can need
horizontal table scrolling/enlargement. Standard message-button captions follow the
available Qt/system locale; owned message content is EN/ES. These existing limits were
recorded without unrelated redesign. Native Windows/macOS acceptance remains deferred.
The rebuilt current packages are under root `dist/`; this correction does not republish
the frozen `dist/linux` bundle. Owner desktop workflow acceptance is not inferred from
these automated/native checks.

[Contract and architecture](single_project_save.md),
[validation](../artifacts/single_project_save_validation.json),
[required gate](../artifacts/single_project_save_final_check.log),
[visual review](../artifacts/single_project_save_review/visual_validation.json),
[protection details](../artifacts/single_project_save_review/protections.json).
