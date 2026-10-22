> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in [the owner decision record](job_management_simplification_decisions.md)
> and [current database inventory](database_tables.md). Removed APIs are not supported.

# JROT edit history — M07/M08

JROT now reuses `application.session.DocumentSession` rather than a second Qt
undo stack. `RotationEditState` and `ReplaceRotationEdit` are immutable application
values; domain/application contain no Qt, SQL, solver or I/O imports. Partial cell
rows, block count, applied scope, frozen `RotationPool` and optimization provenance
are captured together. Unchanged immutable records are shared between snapshots.
Opaque worker/target/profile/assignment IDs are restored directly; replay does not
query current approved profiles or infer identity from translated captions.

One committed dropdown edit, Delete batch, applied/cleared scope or optimized
Apply creates one command. No-ops retain Redo. The original M07 scope excluded selected risk tool. The owner-approved extension
below now includes tool and accepted pending scope state. Raw scheme-ID and
optimization-limit typing, solver preview and comparison tabs remain native text
or transient display state. Manual edits clear optimized provenance;
Undo restores the prior provenance, including after a successful Save. Preview
alone never changes the current grid or provenance. Both CBC Use as Current and
HiGHS comparison Apply use the same command boundary.

`RotationHistoryActions` provides styled Edit/Editar and Undo/Redo with platform
standard window-scoped bindings and the existing processed Undo icon. Editable
combos report the combo as Qt's focus owner: their line editor retains native
text Undo even when empty. During an owned solve source replay and actions are
disabled; no worker is terminated. Replaying source closes comparisons and clears
transient previews while retaining the restored applied provenance for Save.

Save validates a complete scheme then uses the existing atomic repository writer.
The history clean marker moves only after success; Save itself is not an edit.
Failed writes leave current intent, saved metadata and history intact. Undo after
Save changes the draft only. Original metadata and exact frozen links survive
saving a restored optimized revision, with or without an injected optimizer.

History is scoped to one selected scheme in this modal window. Original New,
load/navigation/search, Cancel restoration and confirmed deletion start fresh
histories; closing discards the unsaved modal draft as before. Undo is not an
implicit database write or a cross-scheme recovery mechanism. Existing explicit
Save, Cancel and deletion confirmation remain authoritative.

R006 uses compact multi-selection counts (`N sel.` / `N selec.`) in the existing
five-level summary, with complete selected names in tooltips and the scope chooser.
Native comprehensive-copy checks demonstrate the full 4/6/8/16 counts at 1480x740
without changing control widths, font sizes or row placement. English had the same
narrow-count issue and receives the same presentation-only fix. There is no
measurement conversion, solver formulation or stored-data change.

## Analysis selections and keyboard history — owner-approved extension

Main assessments, PLOT and JROT use Edit > Undo/Redo and platform-standard
shortcuts (verified Linux desktop: Ctrl+Z and Ctrl+Shift+Z; use the
bindings displayed in the Edit menu on your platform). Focused text editors retain native
typing history, including when it is empty; modal dialogs do not replay the main
assessment history. Task-grid rebuilds retain document shortcuts without keeping
references to deleted input widgets.

PLOT uses one chronological session for marker edits and analysis configuration.
Apply records the accepted demographic setup, including its enabled flag, sex and
all canonical bounds. Disabled, unpaired and reversed bounds are retained exactly
even when they do not constrain the effective dataset. Tool selection, accepted
workplace selection, Clear and immediate risk-mode Apply are also reversible.
Tool selection still requires Apply to update results, preserving the existing
workflow. Undo restores both the selected controls and the applied dataset.
Replay reuses saved result projections from this modal session and reloads scope
images through existing consent/failure policy. Rejected scope restoration leaves
the history cursor unchanged. Geometry uses the same session and saved baseline;
analysis changes alone do not make saved map geometry dirty or write the project.

JROT history includes the displayed risk tool, All Jobs/workplace selection mode,
accepted pending workplace selections, applied scope/frozen pool, grid and applied
optimization provenance. Accepting the scope chooser and subsequently pressing
Apply are separate steps. Cancelled selection adds none. Undo of pending choices
does not rebuild them from current database records or change the applied pool.
Existing solver ownership disables replay until the owned solve finishes.

History supports multiple steps with no configured count limit, while the editing
session exists. A new accepted edit after Undo clears Redo; no-ops and rejected
operations retain it. Save is explicit and does not add a history entry. History
is not persisted across application/modal close or JROT scheme load/New/Cancel.
Confirmed deletions, transfers, file effects and management commits are not made
globally reversible by this extension.

All existing Save/Save All controls remain. Moving saving to the main UI and adding
arrow controls are later decisions; neither is implemented in this extension.
