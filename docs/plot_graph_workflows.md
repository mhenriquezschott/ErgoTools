# F114 — original PLOT Tools Overview and graph workflows

Reviewed reference source: `src/plant_layout.py`,
`configureResponsiveLayout` (Tools Overview region), `PlotMapSymbolLegend`,
`PlotGraphSettingsDialog`, `defaultGraphSettings`, `applyGraphSettings`,
`setSummaryFigure`, `onPlotClicked`; and `src/plotviewerdialog.py`,
`PlotViewerDialog`. Source layouts and controls were the implementation starting
point. Screenshots verify that implementation; they did not define a replacement
layout.

`PlotToolsOverview` composes the existing saved-result summaries and owned figures
with the original three-choice selector, descriptions, symbol legend and Graph
Settings button. Original 330–420-pixel width limits, 155-pixel minimum chart
height, margins, spacing, stretches and processed settings icon are retained. Job
mode hides the worker selector without losing its selection. Empty results clear
old charts. English/Spanish controls and descriptions are independent of saved
identities and dimensionless risk data; measurement-unit selection never converts
these percentages or changes assessments.

`PlotGraphSettings` is an immutable, validated presentation value. The original
modal dialog edits its own copy: Apply redraws with the accepted settings, Close
or Escape discards changes, Reset changes only the local draft. Save exports the
currently applied chart, without implicitly applying unfinished settings. The
chooser and its messages are owned by the active modal dialog. Show title,
legend, grid, bar values, default/risk/custom axis maximum and 80–140% text scale
retain the original controls and ranges. Job values use the horizontal X axis;
worker values use Y. Settings and chart browsing perform no project writes.

`PlotFigureViewer` retains the original 900 x 650 window, Matplotlib navigation
controls and Save Plot button. It receives a separate regenerated figure. Closing
or navigating it cannot detach, resize or clear the embedded chart. Graph Settings
export retains PNG/JPEG/SVG/PDF and suffix selection; the expanded viewer retains
PNG/JPEG/all-files and its no-success-popup behavior. Both preserve 300 DPI and
tight output bounds. Cancel writes nothing. Export errors are logged and shown
locally, leaving the window open. File-filter captions are localized as well.

## Corrections and explicit visual differences

- Reference expanded views share the embedded figure, which can transfer its
  canvas and change its dimensions. The new viewer owns a separate figure.
- Each replacement Matplotlib figure owns its event registry. The chart click
  binding is attached once to every replacement, so switching charts or applying
  settings preserves click-to-expand. The regression requires a real native click
  and verifies that the modal viewer was actually visited; test timers are owned
  and stopped, preventing callbacks leaking into later tests.
- Chart margins adapt to actual Qt canvas dimensions after resizing. Over-wide
  titles wrap at the chosen text scale. This corrects clipping at 330 pixels and
  140% text size without repeated font multiplication, repeated bar annotations or
  an extra synchronous redraw in the resize callback. Default source styles remain.
- Saved results alone drive chart refresh. Marker visual/position previews reuse
  the same saved-data figure; a successful explicit Save publishes the new saved
  result and updates summary membership. No refresh query or per-preview chart
  rebuild is introduced.
- Viewer toolbar Home/Back/Forward/Zoom/Save use existing processed application
  equivalents. Pan/Subplots/Customize retain the reference Matplotlib assets:
  corresponding processed assets do not exist. Their captions are localized.
  These are retained reference controls; no unrelated icon set was introduced.
- Export errors show a localized concise message; technical details remain in the
  log instead of untranslated exception text in the UI.

## Acceptance and remaining work

Seven focused cases exercise real modal Apply/Close/Reset, Save with unfinished
settings, native chart-click viewer entry, independent canvas ownership,
pan/zoom/home, saved enable vs preview membership, all worker/job modes, empty
clear, numeric control contracts, title/label rendered bounds, real PNG/JPEG/SVG/
PDF files, PNG 300-DPI metadata, suffix selection, Cancel and failure retention.
The full baseline gate passes 877 tests with 96.57% combined coverage, Ruff,
formatting (418 files), strict mypy (189 source files), architecture, wheel and
source archive. The independent extracted-wheel smoke checks localized modal
settings, actual viewer entry/navigation, narrow 140% title bounds, job scale,
selector retention, real 300-DPI export and unchanged positions/history on reopen.

Sixty-four native captures were inspected: English/Spanish narrow/enlarged,
individual/comparison/job, all worker charts, empty, expanded selector, default/
custom/maximum settings, actual export errors, viewer pan/zoom/empty and adjacent
map resizing. Both English settings fixtures, all three source symbol legends and the
complete focus-normalized source panel match pixel-for-pixel. Recorded settings
and panel child geometries also match exactly. The initial panel comparison
differed at 2,906 pixels solely within its differently focused selector; after
matching focus on the Graph Settings button, all pixels match. The viewer comparison retains source controls but records the separate
figure, margin and processed-icon corrections. No main-window avatar, assessment
cards or bottom controls changed in this slice. Synthetic neighboring-map captures
are not evidence of the full final PLOT host.

All 500 reference hashes and the approved dependency lock are unchanged. Evidence:
`f114_validation.json`, `artifacts/f114-check.log`, `artifacts/f114-wheel.log`,
`artifacts/f114-capture.log`, `artifacts/f114-extra-capture.log`,
`artifacts/plot-graph-workflows`, and archived capture/verification scripts in
`reference/`.

Next: original outcome summary/gauges and complete PLOT host composition, including
parent close/load consent and remaining map/deletion actions. Tools Overview is
ready to compose into that host; production PLOT is still disabled. JROT follows
with CBC single-tool, HiGHS multi-tool and no GLPK. No dependency changes were
made. Overall completion percentage and finish date remain unvalidated.
