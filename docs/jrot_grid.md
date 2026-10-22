# Original JROT worker/time-block grid — F123, 2026-10-09

Source: rotation_layout.py, active initResponsiveUI current panel (lines 418–429),
ComboBoxDelegate (104–151), _targetDisplayLabels/_refreshRotationPool (929–959),
renderEmptyRotationTable (1010–1077), handleCellChanged/generateSuggestion
(1469–1591), showContextMenu/clearTableCell/keyPressEvent (1637–1675).
Pool selection follows rotation_repository.py rotation_workers/rotation_targets
(102–196). The active source layout is the starting point; captures verify it.

The grid preserves 60px rows, 80px worker, 110px time-block and average columns,
160px starting recommendation width, stretch-last-column, bold two-line headers,
continuous damage colors, multiline probability cells and original advisory
thresholds. Wide grids retain the reference horizontal scrollbar. Complete advice
is also available in a tooltip. At enlarged size, recommendations fit without
scrolling. Derived columns cannot be edited. EN/ES headings, unavailable text,
recommendations and provenance captions are localized; saved names/IDs/units are
unchanged. Spanish uses Trab. plus the full Trabajador tooltip to avoid clipping
at the original worker width. No new icon or dependency is required.

application.rotation_pool reads saved hierarchy/jobs/risks exactly once each.
Organization scope includes all workers without assignment links. Workplace
scope chooses the lowest active assignment ID per worker, matching the original
query, and active placements of active jobs with current approved profiles.
Profiles lacking the selected probability are excluded from new dropdown choices;
zero remains selectable. Loading a saved scheme uses its exact target profiles
and reinstates original worker assignment links, including retired evidence and
closed assignments. No new connection, SQL, conversion, calculation or write is
in the grid. Recorded Metric/Imperial labels remain in tooltips and profiles.

RotationTable stores opaque worker/target keys in Qt UserRole, with keys as combo
item data. Display captions, translated text, multiline IDs and repeated station
names cannot redirect identity. Full workplace ancestry disambiguates repeated
station captions. Dropdowns exclude workers and targets already used in their
column, while saved manual collisions may still load as in the persistence
contract. Load validates the evidence pool before replacing edits. current_scheme
builds a complete MANUAL value only; the containing form must preserve appropriate
saved metadata/provenance and perform explicit save/delete through its repository.

Each edit updates one row under QSignalBlocker, then emits one changed signal.
Changing tool repaints recorded evidence without dirtying links; missing selected
tool evidence shows Unavailable and never carries over the previous average/color.
Delete clears selected editable cells in one batch. There is no per-cell database
query or disconnect/reconnect loop. Popup review found the native combo menu
delegate painted selected text white on white; the existing QStyledItemDelegate
pattern from Worker/Job Management and assessment panels fixes it within the
established stylesheet. No visual redesign was introduced.

Validation: 965 native tests pass (12 new focused cases), 96.79% combined
coverage. Ruff/format (456 files), strict mypy (208 source files), architecture,
wheel and sdist pass. Tests cover actual delegate commits, column exclusions,
colliding captions/multiline IDs, zero/missing evidence, source recommendation
boundaries, one notification per edit, Delete, invalid loads retaining edits and
an actual grid→project save→close/reopen→grid edit→save→delete workflow. The latter
is an isolated synthetic project, not the reference operational dataset.

Sixteen native captures were inspected: two source comparisons plus fourteen new
EN/ES empty/populated/enlarged/missing/dropdown/selected/cleared states. English
row height, column widths and table geometry match the source in 800×430 and
1180×600 component shells. Reference horizontal content scrolling at the smaller
size remains; it is not full-form visual acceptance. The containing form's rail,
other panel and all adjacent regions will be checked when connected. No VTK or
result sidebar exists in this isolated component. Full application parity is not
claimed. Independent extracted-wheel native EN/ES delegate edits, exact identities,
saved-grid reload, missing/zero display and Delete pass. All 500 reference hashes
and the approved dependency lock are unchanged. Evidence: f123_validation.json,
artifacts/f123-check.log, artifacts/f123-wheel.log and artifacts/jrot-grid.

Next: original containing JROT setup/scope/scheme controls and usable save/load/
delete/cancel/navigation; then optimization/comparison transfer, owned worker
cancellation/closure and integrated main action. CBC single-tool/HiGHS multi-tool
routing remains implemented, GLPK excluded. Main JROT is still disabled. Legacy
compatibility, copied comprehensive-project integration and final workflow/UI/
platform acceptance remain. No reliable whole-application percentage/date exists.
