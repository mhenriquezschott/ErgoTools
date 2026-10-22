# Workplace table fill, complete actions and contextual help — 2026-10-19

Owner reported three remaining defects in the previous table correction: unused
space at the right, a shrunken No Job selector, a clipped trash-button border and
Job help shown while hovering unrelated cells. This supersedes the initial table's
visual acceptance. The owner already confirmed workplace assignment Undo/Redo;
that behavior and the current four-worker workflow remain the active context.

## Layout and hover contracts

One presentation sizing pass first measures all location/header minima, every Job
choice and complete row-action layout. It adds native selector text/arrow insets and
table-cell padding. The optional Job column receives positive spare viewport width,
and every selector declares the resulting content width. Compact location columns
retain their readable widths. Actual overflow keeps the intrinsic widths and reveals
horizontal scrolling. Minimum row height and Actions width include the full widgets,
cell padding and grid separator, keeping both button borders inside their cells.

An owned single-shot Qt timer coalesces viewport Show/Resize events, including changes
from vertical scrolling. Rebuilding, clearing, widening and narrowing recompute from
intrinsic values rather than retaining the previous filled width. The viewport watch
is absent until construction completes; calendar/directory event behavior is retained.
Reentrancy protection and QObject-owned teardown keep this presentation work out of
project mutation, dirty state and Undo/Redo. No new custom table or alternate workflow.

The table has no generic tooltip. Headers have localized column descriptions; each
location/Shift value has its localized column name and full literal value. Job help
contains the current draft choice and optional-Job explanation, updating immediately
when changed. Its popup choices carry their literal full value. The Actions cell gap
has column-specific help; Change and Remove retain separate localized button help.
English/Spanish text is maintained in the existing worker catalog.

## Validation and limits

The existing workflow test module now checks viewport fill and growth/shrink behavior,
complete selector text fields, complete button rectangles, both conditional scrollbars,
reachable last rows/Actions, timer settling, empty tables, all header/data/control
help and live Job-tooltip changes. Existing worker/assessment/shared-Save regressions
are reused. A failed early constructor probe exposed a viewport watch installed
before the assignment table existed; an explicitly initialized watch now prevents
calendar construction events from touching an unbuilt table. No operational project
was involved.

Final required native Linux gate: **1,956 passed, zero failures/skips,
94.42% coverage**; strict types269, standards/format/architecture/naming/
documentation/review and wheel/sdist builds pass. Focused workflow31 and worker40
checks pass. Independent wheel: **223 passed / 78 subtests**, all
247 Python files and both guides exact; all loaded modules isolated and final
wheel equals the tested wheel.
Evidence is in
[validation](../artifacts/worker_assignment_table_refinement/validation.json).

Twenty-seven native XCB captures were inspected: EN/ES empty/compact/long/many-row
states, minimum/enlarged resizing, complete action borders, full long selected Job,
column/header/Job/Remove help, and Ana's actual four-worker organization on a private
copy. Native QHelpEvent delivery verifies the displayed help text. Both Help guide
sections are updated. Three changed source/test files receive renewed substantive
review and hashes. Current native format remains 18; current project files and uv.lock
remain unchanged by this task. No schema, scientific calculation, dependency or
reference write. Linux migration/cleanup remains 100%, with Windows/macOS deferred.

Next: preserve the existing Ana workplace assignment with main Save, restart, and
review this corrected Worker Management table and hover behavior before resuming
workplace Save/reopen testing. Do not add a duplicate assignment or jump to assessment
association. Owner acceptance of this final layout remains pending.
