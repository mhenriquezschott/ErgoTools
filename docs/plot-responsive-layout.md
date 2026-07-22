# PLOT Responsive Layout

## Purpose

`PlantLayoutWindow` originally used a fixed 1390 x 940 dialog and absolute
`setGeometry()` coordinates. The window is now managed by nested Qt layouts,
size policies, stretch factors, and horizontal splitters. Existing widgets,
signals, scene items, database behavior, and calculations remain in place.

## Region Ownership

The dialog root is a `QVBoxLayout` with four regions:

1. `filters_group`: a two-row `QGridLayout` containing location, shift, tool,
   worker, optional filters, and filter actions.
2. `plotMainSplitter`: the tool rail plus plant `QGraphicsView` on the left and
   the summary/chart group on the right.
3. `plotLowerSplitter`: worker controls on the left and outcome/highlights on
   the right.
4. `statusBar`: coordinate and operation feedback.

The splitters preserve useful defaults while allowing users to dedicate more
space to the map, chart, worker editor, or outcome panel.

## Internal Layouts

- Plant and shift filters use horizontal layouts.
- Worker and other filters use grid layouts.
- The tool rail and summary use vertical layouts.
- Worker selection and coordinate controls use a horizontal layout above the
  existing worker-property grid.
- Outcome content uses a horizontal image/text layout.

The plant view and summary canvas have expanding size policies. The filters
and worker editor reserve enough vertical space for their controls without
overlap at the supported minimum size of 1300 x 900.

## Resizing Contract

- Default size: 1390 x 940.
- Supported minimum: 1300 x 900.
- Maximize is enabled through the native window controls.
- The plant canvas receives most additional width and height.
- Summary and outcome panels have minimum widths and user-adjustable splitter
  boundaries.
- No control should use absolute position as its runtime source of truth.

## Temporary Icon Gaps

The processed ErgoTools set is used where a matching asset exists. Dedicated
styled assets are still needed for:

- Zoom in
- Zoom out
- Actual size / 1:1 view
- Capture image
- Opacity / transparency
- Clear/reset filters
- Apply filters

Those actions retain their existing temporary icons until matching designer
assets are supplied. Open, save, hierarchy view, search, ordering, navigation,
and export use processed ErgoTools assets.

## Verification

`tests/test_plot_responsive_ui.py` loads `tests/test3.ergprj`, processes the
deferred scene/chart population, captures default and enlarged states, and
asserts that the plant canvas grows while worker, plot, and scene data remain
available.
