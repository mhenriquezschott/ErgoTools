# PLOT Responsive Layout

## Purpose

`PlantLayoutWindow` originally used a fixed 1390 x 940 dialog and absolute
`setGeometry()` coordinates. The window is now managed by nested Qt layouts,
size policies, stretch factors, and horizontal splitters. Existing widgets,
signals, scene items, database behavior, and calculations remain in place.

## Region Ownership

The dialog root is a `QVBoxLayout` with two principal regions:

1. `filters_group`: side-by-side Tool and Workplace scopes above the
   collapsible Worker demographics filter, with a fixed action column.
2. `plotMainSplitter`: the fused tool rail and plant `QGraphicsView` on the
   left, with tabbed Summary/Worker details and Outcome panels on the right.

The splitters preserve useful defaults while allowing users to dedicate more
space to the map, chart, worker editor, or outcome panel.

## Internal Layouts

- PLOT always displays one plant image. Its default scope is the first plant,
  all sections/lines/stations beneath it, and shift 1 when available.
- Workplace filtering uses a styled hierarchy dialog whose top-level items are
  plants; selecting a plant includes every descendant without implying that
  multiple plants can share the canvas.
- Demographic ranges use a compact horizontal Min/Max layout.
- Each demographic range is a self-contained labeled block with numeric
  steppers; expanding it cannot resize the Tool or Workplace selectors.
- The tool rail and summary use vertical layouts.
- Worker selection, marker state, position, navigation, and save actions use a
  compact side-panel layout.
- Worker identity remains concise in the selector; its plant, section, line,
  station, shift, and tool assignment appears in a separate context strip.
- Worker search opens a live-filtered results table scoped to the active plant
  filters, with distinct identity, name, workplace, and shift columns.
- The Worker assessment panel previews the same circle/female or triangle/male
  marker and result color used on the plant canvas.
- The animated aggregate-risk gauge, risk-band legend, and highlights span the
  lower Outcome region beneath the map and detail tabs.
- Filtered summary values occupy the left side of Outcome, risk ranges occupy
  the center, and the current risk label plus gauge anchor the far right.
- Summary figures are explicitly reattached to the existing Matplotlib canvas
  when graph types change, preventing stale backing-buffer pixels.
- Tools Overview exposes three focused risk charts: by tool, by sex and tool,
  and by age range and tool. Each includes a compact interpretation note.
- Graph Settings controls shared presentation options and exports the current
  figure as PNG, JPEG, SVG, or PDF.
- Highlight details open in a station table while Outcome retains a concise
  warning message.

The plant view and summary canvas have expanding size policies. The filters
and worker editor reserve enough vertical space for their controls without
overlap at the supported minimum size of 1300 x 1045.

## Resizing Contract

- Legacy window reference: 1390 x 940.
- Current default window size: 1460 x 1060. The additional width preserves the
  map reference beside the wider detail tabs; the additional height holds the
  aggregate Outcome panel below the map without shrinking the canvas.
- Legacy plant-view widget reference: 970 x 580. The current framed
  `QGraphicsView` has a 966 x 580 viewport at the default window size; changes
  must preserve that effective map area within frame-width tolerance.
- Supported minimum: 1300 x 1045.
- Maximize is enabled through the native window controls.
- The plant canvas receives most additional width and height.
- Summary and outcome panels have minimum widths and user-adjustable splitter
  boundaries.
- No control should use absolute position as its runtime source of truth.

## Icon Contract

PLOT uses the processed ErgoTools assets in `assets/ui-icons` for filter,
map, worker, navigation, and export actions. New actions must use a matching
processed asset or be reported as an explicit icon gap before release.

## Verification

`tests/test_plot_responsive_ui.py` loads `tests/test3.ergprj`, processes the
deferred scene/chart population, captures default, enlarged, expanded-filter,
workplace-dialog, Worker-tab, and empty states. It verifies the reference map
size, control containment, a populated station scope, and restoration of the
default single-plant scope.
