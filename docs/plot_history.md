# PLOT source history — M06

`application.plot_history.PlotPositionHistory` reuses the existing
`DocumentSession`; Qt does not own a competing undo stack. Pure typed commands
carry project/document identity, expected source, replacement geometry and stable
translation keys. Failed/foreign/stale commands and no-ops preserve usable history.
Unchanged immutable records are shared; no image bytes, figures or widgets enter
source snapshots. Coordinates remain original-image pixels in both unit systems.

## Operations and Save

A mouse drag or Control-drag scale produces one command on release, regardless
of intermediate move events. Worker visibility/inclusion/lock previews, accepted
coordinate/scale edits, Save All's validated batch and Cancel restoration are
reversible source changes. Undo/Redo restores graphics in place, retaining selection
and avoiding stale animation item references. Job moves preserve station identity,
peer interlocks and the source fanout offset. Undo of first placement can restore
an absent anchor; it does not manufacture a persisted origin. Saved worker points
are independent of subsequent job-anchor changes.

Original Save/Save All/Cancel controls remain. Save itself is not a history entry.
Selected worker/job saves merge only their chosen records into the persisted
baseline; other drafts remain unsaved. The shared engine marks a full committed
snapshot clean only after its atomic writer succeeds. Because partial saves do not
commit the entire draft, PLOT's dirty/close guard compares current geometry with
its committed baseline. Cancel can restore that baseline without another database
write. Undo after Save makes a draft dirty; Redo back to the saved source clears
it. A new source edit after Undo clears Redo. Failed persistence retains validated
batch intent and raw typed values for correction/retry or history reversal.

Save now preserves exact source coordinates/scale when their displayed formatted
text is unchanged. A rounded display projection must not create a second edit
when saving a drag. Accepted changed text still receives finite/range validation.
Job Save preserves station tuple order, avoiding a false dirty state after commit.
Both concrete acceptance failures have focused regressions.

## Qt routing and lifetime

PLOT's styled Edit menu exposes localized Undo/Redo operation labels and enabled
state, the existing processed Undo icon, and Qt's platform-standard key bindings.
The Redo action is text, as in the existing integrated edit actions. Shortcuts
belong to this modal window. Line edits keep native typing undo even when their
local history is empty. Unaccepted coordinate strings block document replay
outside the field rather than being silently discarded. Save or existing Cancel
resolves those strings. Both English and Spanish catalog entries are required.

The earlier M06 acceptance below used selection-local geometry history. The
owner-approved analysis extension now uses one modal chronological history;
see the extension section. Historically, history was routed to the applied
PLOT selection document. A clean Apply preserves
that document's history. Returning to a different selection routes its own cached
history when its committed geometry is still current; if another selection saved
shared geometry, an obsolete full-snapshot history is replaced before binding to
the new source. The cache is local to the modal lifetime; closing it after dirty
consent releases its drafts/history. History is not persisted in project files and
cannot cross project handles. The integrated assessment editor's history remains
independent. No global window lookup, SQL or application event bus was added.

Viewport zoom/opacity, chart presentation settings, opening image files and export
side effects are outside source-marker history, consistent with the accepted
plan's distinction between source commands, view state and file operations.
Existing map image Save/preview behavior is retained and covered by regressions.

## Evidence and retention

Six new regression cases (including EN/ES parameterization) cover gestures,
focus/typing, branching, explicit and partial saves, batch failure, exact fractional
values, Cancel, zero/missing anchors, real multi-station storage and clean Apply.
The new wheel passes 83 focused PLOT checks using native XCB and the full approved
gate passes 1,168 tests with 96.37% combined coverage, strict types, lint, format,
architecture and both builds. Native comprehensive-copy acceptance verifies actual
buttons, menu actions, shortcuts, failure/retry, close rejection and independent
reopen in both languages. Twelve captures were inspected individually.

A measured 1,000-command history over the comprehensive project's 100 worker
records retained 1,111,440 traced bytes (peak 1,126,456 bytes) in this run. This is
measurement evidence, not a universal memory bound. Retention policy is small
immutable position snapshots with shared unchanged records, released with the
modal document; large images/charts are excluded. There is no silent truncation
or newly introduced generic retention framework.

See `m06_acceptance.md`, `m06_validation.json` and
`artifacts/m06-history-native/verification.json` for exact evidence. Wider shared
localization/resize acceptance remains the existing M09 deliverable; no additional
milestone or dependency was introduced.

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
