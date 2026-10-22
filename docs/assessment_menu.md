# F87 — visible assessment menus and recreation

The owner explicitly allows additions/reorganization of the main top menu required
by the architecture/application features; see the archived UI requirements. The
integrated preview previously hid the temporary development row, making New
assessment inaccessible after Delete. This slice exposes existing functionality in
Project/Edit menus without duplicating callbacks or changing task-grid layouts.

`AssessmentMenu` receives the existing command buttons, their localized metadata
and the host's availability refresh. Menu actions invoke those owned handlers;
processed button icons are reused. Menu opening refreshes availability, and source
changes synchronize enabled states. Project provides New, Open, Save, New assessment,
Assessment context, New blank version and Set current version. Edit provides
Undo/Redo. This is the initial integrated menu subset; Save As, recent projects,
project close and final View/Tools/Help operations are not claimed.

New assessment is available when a historical project is open even if its active
source is absent. The user chooses the worker and then an eligible classified
assignment in the existing modal. Cancellation at either step creates nothing.
The current empty tab determines the tool, including ST. Explicit creation creates
15 blank original-default rows. Source-specific operations become available again,
and ordinary edit/Save persists the new document. Other saved sources remain intact.

The existing assignment dialog host now allocates one plus the highest remaining
version for the exact assignment/tool, instead of assuming version 1. This matters
when Delete removed version 1 but version 2 remains: recreation is version 3.
It never deletes retained versions or silently replaces/demotes an existing current
assessment; current ownership conflicts are rejected by existing persistence guards.
With no retained versions, creation starts at version 1. No schema/dependency/session
infrastructure changes were needed.

Four focused cases cover each tool's actual menu action after Delete, worker-choice
and assignment-modal cancellation, next-version allocation, blank defaults,
edit/Save/reopen, unchanged other sources and rejection of a second current creation.
A separate menu history case verifies Undo/Redo and closed-project availability.
Native regression/standards gates pass: 682 tests, 96.85% combined coverage,
strict mypy on 140 source files, lint/format, architecture and both builds.

Native captures under `artifacts/assessment-menu/` cover empty/populated Project
menus, Edit, expanded/selected assignment dialogs and empty/recreated windows for
all three tools. Minimum 1550 by 1015 and enlarged 1920 by 1200 were inspected; no
new clipping was observed for the actual native avatar, cards, headers or bottom
controls. Native VTK framebuffers are composed using the F78 capture method.
Menus reuse the current palette/control treatment. Spanish menu/main captions work;
the preexisting assignment-context modal remains English. Its catalog migration and
Qt stock dialog translation remain outstanding and are not presented as full i18n.

The isolated extracted wheel passed visible menu Delete/recreate/cancel, three-tool
editing and Save/reopen, exact ownership preservation and renderer cleanup.
`f87_validation.json` records all 500 unchanged reference hashes, unchanged lock,
wheel/capture hashes; gate output is `artifacts/f87-check.log`. Reproduction scripts
are archived in `reference/f87-capture.py.txt` / `reference/f87-verify.py.txt`.
Synthetic projects only were used. The reference application/environment remains
untouched. Scientific review gates and remaining application migration targets
continue unchanged. The next step is Settings/preferences and remaining menus.
