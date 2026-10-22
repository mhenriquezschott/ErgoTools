# Workplace toolbar, project dialogs and assessment interaction history

The five owner-requested areas are **5/5 complete (100%)**. No milestones, dependencies,
scientific formula changes or reference edits were added. Migration/cleanup stay 12/12
and 6/6. Native Windows/macOS testing remains deferred.

## Project format and Properties

Project Open/Save/Save As/Backup filters advertise only .ergprj, with English/Spanish
product labels and automatic .ergprj default suffix for project destinations. CSV
export remains .csv. The old generic .sqlite suffix exposed the container format in
an owner-facing project picker; it is no longer offered. No format/schema conversion
was required. Existing repository validation rejects unrelated SQLite containers,
including one deliberately renamed .ergprj, without modifying their bytes.

Properties was checked rather than removed: its existing owned read-only dialog works
for saved projects, showing title/description, file/path, date/time, language and units.
It is unavailable with no saved project, including unsaved temporary projects. Native
English and Spanish dialogs and actual Project-menu invocation were verified. Existing
legacy path fields display N/A when not applicable to the single-file native format.

## Toolbar and menu layout

Main groups, separated only between groups:

- Undo / Redo
- New / Open / Save
- PLOT / JROT
- Organization / Jobs

Export remains in Project and leaves the toolbar. Work Setup is now Workplace
(Spanish: Lugar de trabajo), retaining Organization and Jobs and Risk Profiles.
Existing processed Plant/Job icons and callbacks are reused. Settings/Help retain
menu access. Caption sizing and modest button-width adjustment keep all nine controls
visible at 1550×1040, with a complete Organization caption; main_final_en/es captures
supersede intermediate header sizing captures. Model, cards, task area, context/footer
and bottom controls stay visible. Enlarged Spanish view was checked at 1800×1120;
the previously recorded Spanish minimum-width text-fit limit is unchanged.

## Undo/Redo behavior and boundaries

AssessmentInteractions is an application-layer, project-session timeline of accepted
worker/tool/workplace/context changes and source revision intervals. It replays the
existing DocumentSession histories rather than creating duplicate source commands.
Main toolbar/menu/shortcuts share the existing focus-aware action owner. Focused text
editors retain local typing Undo, including protection against falling through when
typing history is empty. Tool/worker controls use the chronological interaction history.

Example: select DUET, change a rating, select ST. Undo returns to DUET with that rating;
the next Undo restores the prior rating. Redo reapplies the rating then returns to ST.
A new accepted edit/navigation discards the superseded Redo branch. Worker navigation
restores the exact previous context and remains reversible without writing projects.
Cancellation during ordinary Save/Discard/Cancel leaves the history cursor unchanged.

Worker/context departure still resolves dirty source choices and ends that source-edit
scope, as before. View navigation remains reversible; it does not undo a durable Save,
resurrect explicitly discarded edits or recreate deleted records. The timeline clears
on project close/switch and is not saved in the project. This is not global database
Undo. Returning through tool tabs retains their existing source sessions and history.

DUET rating and ST task-type selectors commit valid grid inputs immediately in one
reversible source edit. Presenter context rebinds without rebuilding controls inside
the signal. If numeric text is invalid/unparseable, it remains pending and must be
corrected before commitment; no input is silently discarded. Original ST label/model
conventions, frozen calculations, source precision and stored results are unchanged.

## Acceptance evidence

Full approved Linux gate: **1,320 tests passed, zero failures/skips; 95.77% combined
statement/branch coverage**. Ruff/format, strict types (257 source/tool files),
architecture, naming, structural documentation, substantive hash review and builds
pass. Fourteen changed/new maintained files were reviewed; all 412 maintained files
have no pending documentation reviews/structural gaps.

Focused checks passed 47 tests covering existing assessment navigation, scientific
conventions, typing shortcuts, avatar behavior and new chronological source/navigation
replay. New tests exercise immediate DUET/ST choices, ordering/Redo branching, worker
navigation/cancel/no-write, exact toolbar groups/visibility, real Properties/Open/Save
modals and unrelated SQLite rejection. Existing pending-selector assertions were
updated to the approved immediate-commit behavior, retaining exact scientific tests.

Native EN/ES evidence covers main populated/empty, Workplace menu, Properties, file
filters, selector changes/Undo, tool navigation/Undo and worker navigation/Undo/Redo.
Final EN/ES header captures additionally confirm all nine toolbar controls visible
without elision/overflow. Relevant component states were visually inspected; earlier
unchanged VTK/PLOT/JROT evidence is reused. All 194 comprehensive-project saved sources
and results plus permanent fixture bytes remain unchanged after the disposable-copy
scenario. Bilingual guides document the controls and exact history boundaries.

Evidence: artifacts/workplace_check.log, workplace_focused_final.log,
workplace_guides.log, workplace_reviewed_files.json and
workplace_interactions_review/validation.json. Packages/delivery are refreshed locally;
nothing is installed, published or pushed. Restart running instances to load changes.
