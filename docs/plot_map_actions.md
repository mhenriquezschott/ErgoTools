# Original PLOT map controls — F117, 2026-10-08

The composed PLOT map rail now enables zoom-in, zoom-out, reset, opacity and
capture whenever saved or preview image pixels exist. Source labels, processed
icons, button dimensions, spacing, tooltips and palette are retained. CSV export
is the one remaining disabled rail action. No dependency changed.

## Source mapping and preserved behavior

Reference `src/plant_layout.py` lines 4221–4290 define the actual view handlers.
Zoom-in arms a crosshair then scales 1.5 times about the clicked location using
Qt's AnchorUnderMouse; it resets the anchor/cursor after the one click. Zoom-out
uses 1/1.5 with a 1:1 floor and does nothing below that floor. The original opacity
implementation cycles 0.9, 0.8, 0.7, 1.0, excluding the background. Its historical
docstring describes different values; the executable source is the reference.

`PlotLayoutCanvas` owns these transient view operations and source-image pixel
coordinates. Fitted reset emits the existing scale projection so marker display
geometry stays consistent; it never replaces a saved dataset or marker draft.
Image replacement clears armed zoom. Only an armed left click is consumed;
ordinary right clicks still reach the existing worker context menu instead of
being unexpectedly treated as zoom. Zoomed cropping is intentional; reset and
resize continue to fit the complete map.

Reference `savePlantLayoutImage` at 4530 grabs the current QGraphicsView, including
its actual scaling and markers, and saves PNG via a Save dialog. PlotMapPanel
retains that workflow, PNG/All Files filters and plant/timestamp suggestion.
The default leaf filename sanitizes platform-invalid characters in literal plant
names. A chosen path is used as-is, with PNG encoding, matching the source.
Cancellation performs no capture/write. A False return from Qt's encoder or an
exception reports a localized actionable error; the source ignored False.
Capture never writes the project map/positions or changes assessment state.

## Documented correction: reset without reapplying filters

The source actual-size button calls Apply as a self-described temporary transform
workaround. Its effective visible result is a fitted map, rather than literal
identity-scale pixels. The new handler fits directly, cancels armed zoom and
preserves edited positions, visibility/style drafts, saved results and summary
identity. It uses the existing canvas; it does not add timers, results refreshes
or global parent callbacks. No formula or unit policy changes.

## Deletion audit and next PLOT integration

The original responsive rail's eighth control is grtool9 CSV export. The hidden
grtool8 control rewrites an experimental index.html and is not a visible final
workflow. There is no separate PLOT deletion button/handler in plant_layout.py.
The earlier checkpoint's general deletion item was not grounded in this source;
no new destructive PLOT action will be added. Existing assessment deletion stays
with the integrated assessment UI and its own migrated workflow.

Next is grtool9's saved worker CSV export, followed by production navigation
composition and actual integrated editor handoff. That export uses the saved
worker dataset and excludes layout/style fields; review its exact source columns
in plot_position_repository.py before implementation. PLOT remains disabled in
main navigation while this final rail workflow is incomplete. JROT follows PLOT,
using the owner's CBC/HiGHS routing; GLPK is excluded.

## Validation and limits

Four focused native tests use real rail/map clicks in EN/ES, verify armed zoom
without moving markers, four opacity steps/background exclusion, original zoom
limits, reset with pending marker intent, exact current-view PNG pixels at
minimum/enlarged sizes, cancel, False/exception encoder failures, portable chooser
names and absent-map disable/zoom cancellation. Project data remain unchanged.
Eighteen native artifacts show minimum, armed, zoomed, opacity, reset, enlarged,
empty, localized encoder error and actual exported PNG states. Complete map,
chart/outcome regions and rail were inspected. Zoomed cropping is intentional;
fitted states preserve the full source image and adjacent fixed-format regions.

A reviewed AST subset of the original opacity/zoom-out handlers runs against the
same real view/scene: four opacity steps and six scales agree exactly. No legacy
module is imported or reference asset loaded into production. No new whole-host
pixel-parity claim is made. The extracted wheel independently repeats real EN/ES
map clicks, pending-edit reset, min/enlarged exact PNG pixels and no-write lifecycle.

892 tests pass; combined coverage is 96.88%. Ruff/format, strict mypy, architecture
and wheel/sdist gates pass. All 500 reference hashes and approved lock remain
unchanged. See f117_validation.json, artifacts/f117-check.log,
artifacts/f117-wheel.log, artifacts/f117-capture.log and artifacts/plot-map-actions.
Capture/wheel/reference verification scripts are archived under docs/reference as
f117-*.py.txt; they are evidence fixtures rather than new production tooling.
