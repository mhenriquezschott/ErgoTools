# Workplace assignment table sizing — 2026-10-19

The owner confirmed workplace assignment Undo/Redo in Worker Management, then reported
that the Plant value was clipped while narrower Station values had excess room.
This correction is limited to that assignment table's presentation and documentation.

Location, Shift and Actions columns now use native full-content/header sizing over
all rows. Word wrapping is disabled; values remain on one line. Job is measured from
its complete available choices and header, with a useful 160 logical-pixel minimum
when empty or containing only No Job. The selector's arrow, text inset and table-cell
padding use Qt style geometry. The calculated minimum is declared on the selector
itself so Qt's initial editor layout cannot fall back to a smaller cached size hint.
The measured Job column is fixed until refitting, so a manual header drag cannot
shrink it below its selector and overlap the adjacent Actions column.
Headers and unrelated narrow columns do not inherit the width of a long Plant name.

Both scrollbars use ScrollBarAsNeeded. Short data fits without artificial scrolling;
long columns and enough rows reveal the respective scrollbars. At a given window
size, actual language/font/header widths determine whether overflow exists. Emptying
or rebuilding the rows refits the Job column rather than retaining a previous long
value's width. Default row height, row actions, pending Job editing, shared history,
main Save, metrics/imperial values and ownership/calculations are unchanged.

Required final native Linux gate: **1,954 passed, zero failures/skips,
94.41% coverage**; strict types269, standards/format/architecture/naming/
documentation/review and wheel/sdist builds pass. The focused workflow module passes
29 cases, including eight new table scenarios. Independent wheel: **221 passed /
78 subtests**, all 247 package Python files/both Help guides exact;
all loaded package modules use the isolated extraction and final wheel equals tested.
Validation is recorded in
[the machine-readable record](../artifacts/worker_assignment_table/validation.json).
Eight additional parametrized cases in the existing maintained workflow test module
cover EN/ES empty/short/long/many rows, complete headers/data, actual selector text area,
conditional scrolling, reachable Actions/last row, shrinking and clean project state.
Native checks use disposable synthetic projects; current test files are not modified.

Twenty-two native XCB captures cover EN/ES empty, typical full Plant value, No Job and
selected Jobs, minimum/enlarged windows, long values at both scroll ends, full long
Job text, cleared rows and 35 assignments at top/bottom. Actual first-display and
selected-value text fit was checked after including both selector and cell geometry.
The earlier interrupted gate predates this native Job-fit correction and is partial;
only the final complete gate counts. The two changed source/test files received
substantive documentation review and renewed hashes/inventory.

No dependency, schema, formula, reference write or fixture migration. Linux migration
and cleanup remain 100%; no new milestone. Windows/macOS remain deferred. Owner UI
feedback on the final column layout is pending. Existing accepted association/history
behavior is reused rather than redesigned.

Next: preserve the owner's pending assignment with main Save before restarting to
load the changed UI. Resume at Worker Management table review and assignment
Save/reopen; do not jump to assessment association before that workflow is verified.


## Owner layout rejection and accepted correction scope

Owner feedback rejects the unused right strip, shrunken Job selectors, clipped trash
button border and generic table tooltip in this initial layout. These are actual UI
defects despite the earlier automated/native review. The new bounded correction and
stronger full-viewport/control/hover checks are recorded in
[refinement acceptance](worker_assignment_table_refinement_acceptance.md); its final
evidence supersedes this table layout's visual acceptance and package hashes.
