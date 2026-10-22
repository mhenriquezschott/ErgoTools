# Migrated Job workplace dialog — F59

JobWorkplaceDialog follows the existing class in src/job_window.py: 840 x 590,
minimum 720 x 500, original margins/spacing, title/subtitle, text filter, shift
selector, three-column tristate hierarchy, status and Clear/Save/Cancel row.
Applicable stylesheet rules were extracted from the original main workspace and
Job Management styles. The seven original processed icons are packaged inputs.
No redesigned control arrangement or new application navigation was introduced.

The host supplies a JobWorkplaces presenter, its loaded JobWorkplaceView, icons
and optional remembered shift. Widget construction does no database reads. Local
checkbox state spans all shifts. Filtering hides rows without dropping selections;
Clear affects all stations of only the displayed shift, including hidden rows.
Save persists through the presenter once and accepts only on success; Cancel
discards local selections without writes. Failure displays the existing warning
pattern and leaves the editor open. The save reentrancy guard also spans the
warning's nested event loop.

Signals connect once after initial construction. Programmatic rendering uses
QSignalBlocker, which restores the prior block state on exit, and never recaptures
intermediate checkbox changes. User item changes capture selection/status without
another render. Tests observe zero itemChanged emissions during repeated shift
switching. This verifies this component, not application-wide event optimization
or background-thread safety.

Remembered shift is explicit input/output rather than mutation of a parent
window's hidden dictionary. It becomes available only after successful Save.
Exact shift identities are retained instead of trimming stored names. Save errors
remain a presentation recovery boundary; persistent diagnostics and translated
error mapping still need integration. English reference labels/tooltips are
preserved in this slice; Spanish/localized strings remain pending and this dialog
is not claimed to have complete internationalization.

Six added Qt cases cover shift rendering, filtering/hidden selections, clear and
save across shifts, cancellation, hierarchy parent checkboxes, stale views,
failure/reentrant retry, empty hierarchy and preferred shifts. All 506 tests pass;
overall combined coverage 98.97%, new dialog 99.11%. Ruff/format, strict mypy
(104 source files), architecture and builds pass. An extracted-wheel test uses
actual buttons to clear/save and verifies persistence and historical ownership.

Native XCB captures cover collapsed/expanded/selected, filtered, empty shift,
empty hierarchy, error popup and the minimum-size window. The complete labels,
tree and bottom controls fit without clipping. The original dialog class and its
actual stylesheet expressions were extracted via AST for a same-environment
comparison using synthetic choices. They were run under the approved NEW Qt
baseline, not presented as original-environment compatibility tests. Window
geometry/control placement match in the inspected states; focus differs between
some captures. No VTK/results region exists in this dialog.
This is component-level visual evidence, not full application/platform parity.

All 500 reference files and dependency lock remain unchanged; no schema or
scientific formula changed. Evidence: f59_validation.json, reference/f59-capture.py.txt
and reference/f59-verify.py.txt.

Next: integrate localized messages and host lifecycle when connecting this dialog
to migrated Job Management. Full job risk/profile controls, worker management,
project setup navigation and integrated assessment screens remain incomplete.
