# Disposable JROT workflow prototype — 2026-10-20

Owner-authorized, semi-functional mockup for discussion with the JROT team. This
implements the Yes / existing-rotation walkthrough, using the current ErgoTools
visual theme and English/cm/N. It does not replace production JROT or complete
future JROT requirements. The completed Linux migration remains 100%; no milestone
or schema change is introduced. Owner Job/workplace workflow testing stays paused.

## Current meeting revision — 2026-10-21

Use the clean six-worker `test_projects/native/jrot_workflow_demo.ergprj`. See
[jrot_meeting_demo.md](jrot_meeting_demo.md) for contents and the Friday walkthrough.
The drawer now uses the header blue with white text, Yes/No are large buttons, and
workplace/shift and Job/worker choices open themed read-only trees. Sidebar and Back
allow free review; missing inputs prevent calculations, not navigation. Restrictions
are optional and remain preview-only. Full stored tasks versus direct-only values are
explicit. Latest evidence is jrot_prototype_meeting_validation.json; the October 20
evidence below remains historical. No database/core change accompanies this revision.

## Launch and walkthrough

Run the existing application normally. Open **Settings → General**, check
**Enable Developer Menu for this session**, and Apply. Open
**Developer Menu → JROT workflow prototype…**. It also works without a loaded project.
The switch starts off after each application restart and is never serialized.
Changing only this checkbox bypasses ordinary preference/project Apply operations.
Cancel retains its previous runtime state. Ordinary preference changes still use
the existing Settings workflow.

1. Select an existing Plant/Section/Line and Shift, or use all available Jobs.
   Review shift duration, equal blocks and equal worker/Job counts. Yes advances;
   No remains visible and explains that its branch is unavailable.
2. Select real project Jobs, calculated samples or empty temporary Jobs. Temporary
   names are editable. Project options can be filtered by line/shift placement;
   physical Stations remain project context rather than substitutes for Jobs.
3. Select existing workers or temporary participants. Add/remove fixed-Job,
   excluded-Job and no-consecutive-high-risk rule previews. These rules do **not**
   constrain either the matrix or the optimizer in this mockup.
4. Enter the existing rotation matrix. Every block must contain each Job exactly
   once. The starter matrix is explicitly simulated, not a loaded saved scheme.
   A balanced example can replace it locally.
5. Reuse existing Job values or enter task names and LiFFT/DUET/ST inputs. Task +/-
   retains other rows/tools; Clear tool starts one blank task. Calculate uses the
   existing application calculators. Numeric edits invalidate stale outputs.
   Progress distinguishes Ready/In progress/Not entered. Skip is unavailable data,
   never zero; choose a complete single tool or complete all three to continue.
6. Review separate worker schedule-average and intrinsic Job-risk tables. Run real
   optimization, then compare maximum, mean, population SD and range per tool.
   Existing CBC solves a single tool; existing HiGHS runs the two-stage all-three
   route. Schedule cells display the first selected tool, identified in the status;
   comparison covers every selected tool. Report/export buttons are disabled.

Move over the left notch to animate the steps panel open; leaving collapses it.
Pin keeps it open. Opening reallocates real width rather than covering controls.
Back retains scratch input; task grids and pages scroll when the window is narrow.
No Undo/Redo, save, Apply-to-project or report publication exists in this prototype.
Closing discards all working values. Closing during a solve waits for the bounded
solver call, suppresses its result and safely destroys the thread afterwards.

The overview has seven numbered stages, while individual slide/screen numbers differ.
The prototype keeps that overview numbering: task entry and calculation/validation
share stages 3–4 on one page; baseline is 5; optimization/comparison are 6.1/6.2;
stage 7 is represented by the disabled report actions on comparison. Setup uses
1.1–1.3. No additional persistent workflow or compliance semantics are invented.

## Isolation and architecture

Only three existing source files change: bootstrap composition, the main window's
runtime Developer menu/Settings handling, and the Settings checkbox. The original
main-toolbar widths remain unchanged. Five isolated modules own detached
catalog projection/scratch calculations, prototype widgets, dialog workflow and
solver-thread orchestration, including temporary selector windows. Domain/application remain Qt/storage/solver independent.
No production task widget, JROT widget, calculator, optimizer, command/history,
codec, schema or preference DTO is modified. Existing packaged icons are reused.

The composition root borrows three read-only catalog loads, immediately detaches
immutable values and gives the dialog no repository, file path, write callback or
main editing session. Jobs with task sources are copied to cm/N with the existing
unit policy and recalculated locally; direct Job values remain exact. Samples are
explicitly labeled and calculated, never invented results. Names, skips and rule
previews remain local structures, outside persisted DTOs. The real optimizer receives
only validated immutable numbers/schedules, without the preview rules.

## Judgments and questions for later discussion

- Existing Shift start/end suggest elapsed duration, including overnight shifts.
  Equal clocks currently suggest 24 hours in the mockup. Duration remains editable
  and descriptive only: it does not rescale repetitions/day or model coefficients.
  Ask the team whether breaks should be excluded and what unequal blocks would mean.
- Show both intrinsic Job risk and worker schedule averages in separate tabs. These
  are different quantities; worker averages are comparison measures, not new injury
  probabilities. Confirm which should appear in the eventual report.
- Prototype bounds: 1–12 workers/Jobs/blocks, 1–100 tasks per Job/tool and 1–30 seconds
  per solver stage. These are demo layout/run bounds, not new production limits.
- Worker/Job counts match initially: exactly one worker per Job/block. The source
  project provides a catalog, not an automatically imported rotation. Duplicate Jobs
  or workers and incomplete selected-tool calculations prevent calculation, while
  sidebar and Back review remain available.
- Task names are optional scratch metadata. Real constraints, configurable thresholds,
  any-two-tool optimization and report contents remain future design decisions.
  No new storage design is inferred from this prototype.
- A missing or skipped tool is unavailable. Other complete single tools can still
  run; all-three requires every selected Job to have all three complete values.
- The comparison shows truthful distribution changes, not guaranteed improvement in
  population mean. With unchanged Jobs/staffing/workload that mean stays the same.
  Do not infer compliance or elimination of hazardous Jobs from redistribution.

These decisions keep the demonstration moving under the owner's explicit instruction
without changing the requirements discussion in jrot_wireframe_discussion.md.

## Evidence and private fixture copy

Basic owner-requested tests cover the full sample flow, all three single-tool routes,
all-three, mixed real/sample/entered data, invalid staffing/No branch, task editing,
navigation, runtime Settings, project isolation, animated width and safe solver close.
Existing Settings/navigation/Save tests also run: 59 source cases pass, with 13
prototype cases also passing from the independent wheel. All 330 packaged files
match source. Static checks/builds pass and 32 native capture states are inspected.
See jrot_prototype_validation.json
for final commands/counts, native captures, source-review hashes and unchanged-file
checks. The prior full production gate remains historical; no new full-suite coverage
percentage is claimed for this limited mockup.

`artifacts/jrot_prototype/comparison_safety_copy.ergprj` is the owner's authorized
byte-identical private QA copy; copy_record.json records its source/hash. It is not
a parallel maintained fixture, operational project or migration target. Remove that
copy after owner prototype acceptance. There are no source-file backups or temporary
prototype tables to clean up. All three maintained native fixtures remain untouched.

To remove this prototype later: remove the three documented composition/Settings/menu
hooks, five prototype modules and their basic test, then renew their review inventory.
No database rollback or project conversion is required.
