# F85 — original saved tool-data selection

Reference sources reviewed read-only: `src/main.py` toolGridAction (shared by the
three task-grid buttons) and `src/tooldatadialog.py`. This is the six-column Plant,
Section, Line, Station, Shift, Tool dialog; the hierarchy-based assessment-context
chooser in the bottom bar remains a separate operation.

`SavedToolOption` and `saved_tool_options` map saved current ownership records to
immutable display choices, filtered by worker and tool. Closed assignments remain
browsable because assessments retain original assignment ownership. Noncurrent
versions and other workers/tools are omitted. No saved row is synthesized for a
missing source. The view receives choices; no database access or window lookup is
hidden in it. Project history validation rejects foreign/missing assignment links.

`ToolDataDialog` retains the reference 800 by 400 initial size, scrollable table,
six columns, sorting, single full-row selection, Close on the left and Load on the
right. Double-click invokes the same selection action. Rows are read-only: editing
displayed workplace labels cannot alter ownership. Each cell stores its immutable
choice so sorting never changes the target. Tooltips expose assignment, version and
job identities to distinguish retained assignments sharing the same workplace.
English/Spanish captions and existing stylesheet are used; no new icons are needed.
The original modal's editable-label behavior is deliberately removed as an input
robustness correction; labels are metadata rather than editable project records.

The host opens the modal without committing pending task text. Close leaves that
text and source unchanged. Load commits valid text through the existing presenter,
retaining invalid input when parsing fails, then resolves Save/Discard/Cancel for a
dirty source. The existing workspace `select_assignment` opens the exact saved
current source; it does not reassign a worker or promote a historical version.
Pending edits committed before a dirty Cancel remain in the active document/history.
Choosing the same source uses existing no-transition semantics. Results are cleared
on successful Load so prior-tool results are not displayed for the new owner.
Sources without historical ownership cannot browse; the grid button is disabled.

Five focused tests cover all three actual grid-button/modal workflows: Close with
invalid pending text, invalid Load retaining source, valid dirty Cancel, Save and
Discard between exact same-workplace owners, Save/reopen, filtering of other workers
and noncurrent versions, foreign history rejection, Spanish empty-table warnings,
sorting identity and styled header width. The first native captures exposed clipped
headings: column minima now include the polished header's font metrics and padding.
This preserves automatic sizing/content scrolling rather than manually spaced text.

The required gate passes with 673 tests and 96.91% combined coverage, strict
mypy on 139 source files, lint/format, architecture and source/wheel builds.
Native captures in `artifacts/saved-tool-data/` cover each tool's unselected/selected
modal and loaded main window, Spanish selected/empty states. Corrected headings are
legible; native avatar, cards, labels and bottom controls remain unclipped at
1550 by 1015. Actual VTK framebuffers are composed using the documented F78 method.
This is scoped visual acceptance, not final whole-app reference parity.

The isolated extracted wheel with approved dependencies passes three-tool modal
Cancel/Load, Save/reopen, exact closed-owner selection, preserved current markers
and native cleanup. `f85_validation.json` records all 500 unchanged reference hashes,
unchanged dependency lock, build and capture hashes. Scripts are archived as
`reference/f85-capture.py.txt` and `reference/f85-verify.py.txt`; gate output is
`artifacts/f85-check.log`. Only synthetic temporary projects were exercised.

The original Delete operation remains disabled and is next. It is separate from
Reset: reference Delete removes saved results and tool association for the context.
An atomic persistence operation and explicit confirmation must be migrated before
connecting it. No deletion API, dependency change, legacy import or PLOT/JROT
implementation is claimed by this checkpoint.
