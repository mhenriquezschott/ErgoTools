# Shared assessment editor

The production Main and Jobs windows now reuse one task-grid implementation for
LiFFT, DUET and ST. Compact worker/Job task-copy previews use the same grid in read-only
selection mode. The experimental JROT workflow is unchanged and can adopt this API later.

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
responsibilities. The refactor changes no native format, settings format, formulas,
optimizer, worker defaults or one-starter-task Job policy.

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
