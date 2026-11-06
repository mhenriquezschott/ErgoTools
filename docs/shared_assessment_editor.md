# Shared assessment editor

The production Main and Jobs windows now reuse one task-grid implementation for
LiFFT, DUET and ST. Compact worker/Job task-copy previews use the same grid in read-only
selection mode. Production guided JROT also uses this shared editor and the same import actions.

## Components and ownership

| Component | Responsibility |
| --- | --- |
| AssessmentTaskGrid | Tool columns, native numeric/select controls, task IDs, row selection, fixed headers, scrolling, precision and read-only task output labels. |
| AssessmentCellEdit | Frozen completed-cell intent: task ID, field name and exact numeric token or selector item data. It is not an accepted source command. |
| AssessmentActionRow | Equal Clear/Calculate actions, optional built-in or supplied +/- task controls, packaged icons and common heights. Hosts set captions/tooltips and connect commands. |
| AssessmentEditorSection | Task content or tabs, optional status, shared totals view and action row. Settled grid geometry aligns main totals under Damage. |
| Main tool panels | Presenter-context binding, display/source-unit conversion, pending/invalid text, cell commands, exact existing per-tool result formatting and input_committed notification. |
| JobTaskEditor | Thin Job binding over AssessmentTaskGrid: established numeric validators, immutable source replacement, pending input and source_edited. No alternate renderer remains here. |
| Job Management | Job ownership, starter templates, direct values, calculation, source copies, placements and shared project history. |

No grid/section opens a project, calls SQL, performs scientific calculations, saves a
file or creates an Undo stack. Existing presenters/application services retain those
responsibilities. Task names use the existing native task fields (current format 24).
The import refinement changes no project format, scientific formulas, optimizer, worker
defaults or one-starter-task Job policy.

## Reuse contract

Construct AssessmentTaskGrid with tool, language, decimal convention, display precision
and input-unit metadata. load_source binds an exact immutable source or display-only
projection and optional matching outputs; it never accepts those values into a project.
Main dimensional panels supply projected source-shaped values, then retain their existing
presenter context for actual editing. Source units and saved-output units remain distinct.

cell_finished emits AssessmentCellEdit for a completed numeric cell or selector. Numeric
values retain source_text precision, not a rounded visible float. input_edited marks
pending numeric text without accepting it. Main adapters keep existing full-row parsing
and cell-specific commands so stale contexts and unfinished siblings retain their rules.
Job adapters keep their source validators. Invalid text never becomes a source merely
because the grid emits an intent. read_only disables all input acceptance, while
selectable provides task-copy checkboxes and independent selection notifications.

worker_layout retains the established Main column minima/stretch and ST no-horizontal-
scroll policy. Ordinary Job grids retain their own established responsive column minima.
compact reduces read-only preview density. These configure one rendering path; they do
not select different calculators or business rules. Hosts do not manufacture alternative
row layouts. Original ST Tab order remains all direction selectors, then numeric fields.

Grid geometry changes are coalesced onto the event loop and horizontal headers follow
the body scrollbar. Main totals follow geometry_changed through the shared section;
Job's tabbed/direct summary retains its host alignment callback. Native typing Undo and
per-cell project replay remain separate as before.

## Lifetime and replay safety

Each rebind increments a projection generation before retiring focus/controls. Completion
signals retain task identity and that generation; retired cells cannot acquire a new
row's identity. Native completion callbacks hold weak grid/control references, preventing
reference cycles and final FocusOut callbacks into partially collected Python state.
Queued geometry work checks native lifetime before reading child layouts.

Existing complete-cell commands and automatic results remain one chronological project
action. Opening/rebinding the grid creates no history. Explicit Calculate and Clear keep
their host-owned behavior, prompts and sole main Save.

## Validation

Shared-grid and host regressions cover exact cell identity, stale-control completion,
read-only previews, task-count/history behavior, unit/precision preservation and scroll/
header alignment. The required development check includes structural documentation and
explicit reviewed-source hashes. See [development](development.md) for current checks.


## Names and spreadsheet extension

`task_names` is a separate row-aligned array of editable name selectors (read-only labels
in copy previews). `inputs` and `input_fields` continue to contain only established numeric
or choice fields. `task_name_finished` carries exact row ID/name/optional definition ID.
`Task names…` explicitly adds a reusable definition or renames the selected definition;
typing a name alone never creates a shared identity. Creating a definition and choosing
it are separate reversible edits. Names are optional and do not count as numeric input.

`AssessmentTaskActions` receives canonical-source read/accept, atomic Paste acceptance,
catalog read/replace,
before-action validation, units and decimal callbacks. It owns no history or calculations.
Hosts commit pending names before Save/navigation, preserve per-cell chronology and reject
obsolete previews. A completed local name is one history action; pasted inputs and newly
registered reusable names share one atomic project action. Only mapped name cells in
included destination rows participate. Existing names are reused with NFC/case/outer-space
matching; explicit existing references remain intact. Undo confirms removal and restores
prior sources/results/catalog; Redo restores the same IDs. New names are not created
during preview or Cancel. Weak project subscriptions refresh other open grids only
when catalog definitions change; unfinished name typing defers that refresh until
completion. Project switches and Qt destruction detach those listeners; callbacks
already copied into a notification batch explicitly ignore destroyed Qt objects.

`Copy cells` writes headers and full-precision editable values as TSV. `Paste` uses a
compatible saved per-tool mapping; the adjacent import button always opens the shared
editable preview. Workers, Jobs and guided JROT use the same panel, also embedded in
Settings. See [import and paste](assessment_import.md) for file/sheet/range selection,
encoding, mapping, strict validation and preference ownership. Single-cell text paste
remains native. One accepted rectangle is one existing host history action; the grid
never owns a calculator, project writer or separate Undo stack.


## Personal optional columns

`assessment_column_keys` owns semantic display order; the grid derives header/input/output
positions from those keys. `AssessmentColumns` permits only optional fields to be hidden.
`set_column_preferences` changes visibility/minima/stretch without rebuilding controls or
accepting a source. Signal guards preserve pending text; required fields stay visible.
Header alignment follows visible columns, and overall result totals fall back to available
panel space when Damage is hidden. Personal settings use a read-only instance of this
same grid for live sample previews. See [column visibility](task_column_visibility.md).


## Selected-row deletion

Click a task number to select its whole row. Shift-click extends a consecutive range;
Ctrl-click adds/removes separate rows. Input cells and task numbers highlight the exact
selection, and Copy describes/copies those input values. An ordinary input click or
Escape clears the selection; existing Shift-click rectangular cell selection also
selects its affected rows for deletion. Read-only copy-preview checkboxes are separate.

`− Task` removes all selected rows in one acceptance/history transaction. If any row
contains entered data or a name, confirmation covers the complete batch; Cancel changes
nothing. Without a range, worker editors preserve their existing last-row fallback,
while Job editors use the focused row. Retained task IDs, names, units, source precision
and order are unchanged. One shared Undo restores the entire source/result state.
Worker assessments retain one blank starter if every row is removed; Jobs retain their
existing empty-source/starter projection. The same behavior applies to all tools in
Main, Job Management and JROT. No new history engine or database format is introduced.


## Shared assessment tabs

Main, Job Management and guided JROT compose the same measured assessment tab control.
Full captions are measured with their themed bold font and icon allowance, including
closing parentheses. If the strip is constrained it scrolls instead of shortening the
captions. Stable `assessmentTabs` object-ID theme selectors apply equally to Qt and
shared widget subclasses, preserving the white tabs and teal selection cue. PLOT's
shorter overview captions reuse the measured bar with its 12-pixel text setting.

## Dark desktop defaults and result selectors

ErgoTools-owned light forms resolve their text/control palette independently of a
dark desktop palette. Controls receive those defaults before Qt polishes their
explicit styles; colored results, avatar labels and selected states keep their own
colors. The application palette and native file/color/font choosers are unchanged.
The shared theme observes widget polish and owned-window show/palette events without
walking descendants or changing data/history. It detaches before Qt shutdown; the
light palette template is shared without rebuilding its roles for every task cell.
Native macOS visual acceptance remains
separate from automated dark-palette checks on Linux.

`AssessmentResultTabs` reuses the measured tool tab bar for the guided JROT review,
optimization and comparison selectors. Explicit short-caption/icon spacing and teal
selected styling avoid native Cocoa miniature segmented tabs; switching tabs still
shows the same stored solution without another solve.
