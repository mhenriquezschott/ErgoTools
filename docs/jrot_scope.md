# Original JROT scope chooser — F122, 2026-10-08

The source is rotation_scope_dialog.py, reached by the active JROT Choose Scope
button. The migrated dialog retains its 680×560 minimum, title/support text,
shift row, checkable plant/section/line/station hierarchy, alternating rows,
stretch/content-sized header, expanded initial tree, count label and bottom
Cancel/Use scope row. Layout is taken from source, not recreated from images.
Processed plant/section/line/station icons are reused. Action buttons now use
existing packaged Cancel/Apply icons instead of platform Qt stock glyphs, as
required by the UI asset rule. No new asset or dependency was added.

application.rotation_scope reads the saved hierarchy/jobs through a read-only
port. Original separate query behavior is retained: any active placement can
supply a shift; only active jobs with active placements supply selectable station
contexts. Duplicate placements collapse into one full workplace identity. An
inactive-job-only shift can therefore show an empty tree. Profile availability
is checked later by the scheme/optimization workflows, not this scope selector.
No database connection, SQL, settings write, migration or save is inside the UI.

The dialog receives immutable options and the previously selected workplace
tuples. Its result contains exact checked station/shift contexts; translated
captions never become identity keys. Changing shift rebuilds the source-style
candidate tree. Empty acceptance keeps the original in-place prompt and the
window open. Cancel/Escape do not publish the edited selection; the containing
form must replace its pending scope only on Accepted. Main-form integration is
still pending, so this slice does not claim applied-scope save behavior there.
Scope selection has no physical quantities or metric/imperial conversion.

Initial parent states are now derived from checked leaves (the original left
checked children under unchecked parents). A single QSignalBlocker batch handles
subtree propagation and bottom-up mixed parent states, followed by one count
update. Tests confirm one external itemChanged event instead of recursive
cascades. English/Spanish counts, titles, types, prompts and action text are
localized, while workplace names and shift IDs remain the saved strings.

Validation: 953 native tests pass (five focused new cases), 96.84% coverage;
Ruff/format (451 files), strict mypy (205 source files), architecture and builds
pass. Actual native source/new comparisons use the original class body and query
on a synthetic reference-shaped database, without importing its application or
changing its files. English heading, supporting text, tree, count and action-row
rectangles match at minimum and 1000×800 sizes. Eighteen captures were inspected:
two original comparisons and 16 new localized expanded/collapsed, selected/mixed,
empty shift/project, prompt and resize states. No clipping was found. Focus and
packaged action icons differ, so full pixel parity is not claimed. There is no
VTK/avatar or results panel in this chooser; those adjacent regions are outside
this modal and will be checked with the containing form/integrated window.

Independent extracted-wheel real EN/ES actions, empty-selection protection,
returned identities and Escape pass. All 500 reference hashes and approved lock
remain unchanged. Evidence: f122_validation.json, artifacts/f122-check.log,
artifacts/f122-wheel.log and artifacts/jrot-scope. Capture/wheel scripts are
archived under docs/reference as validation-only text.

Next: original JROT scheme form using this chooser and tested scheme persistence,
with worker/target editing and usable save/load/delete. Then optimizer/comparison
transfer, safe owned worker cancellation/closure and main navigation integration.
JROT remains disabled in the main application. Original-format compatibility,
comprehensive copied-project validation and final integrated UI/workflow/platform
acceptance remain in the existing plan. No reliable overall percentage/date exists.
