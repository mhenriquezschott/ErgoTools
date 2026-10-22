# PLOT marker rendering and explicit position saves — F107

This slice ports the reviewed `visualworkertool.py` and `visualjobmarker.py`
rendering into an owned Qt item and marker layer. Their original code defines
shapes, colors, dimensions, selection borders and scale behavior; captures verify
that implementation. The native harness combines existing filters, map panel and
saved results. It is not the complete original PLOT window or final acceptance.

## Preserved behavior

Female workers use circles, male workers triangles and unspecified sex hexagons.
Individual markers use the original continuous tool damage palettes. Comparison
markers contain an 18%-inset worker shape inside a job-colored square; absent job
risk uses a dashed frame. Job markers use the original 38-pixel square, shortened
job ID, contrasting text and blue selection. Missing station anchors display the
original dashed placeholder at (18, 18), without saving it during rendering.
Shared-station job placements retain the original nine-pixel display fanout.
Worker visibility, size, scale, lock and enabled flags come from saved geometry.
Unplaced workers remain absent rather than receiving fabricated coordinates.
Scientific-review results remain neutral and tooltips report unavailable risk.

Original-image coordinates remain separate from Qt view scale and body units.
Inverse view scaling retains source rounding and the original Ctrl-drag worker
scaling formula. Qt's normal drag preserves the grabbed point. Selection publishes
one stable worker-assignment/job-placement key through an injected callback.
English/Spanish tooltips escape literal names and convert worker probability from
its canonical fraction into displayed percent; job evidence is already percent.

## Code improvements and deliberate differences

`PlotMarkerItem` owns local geometry, paint, mouse intent and a saved edit snapshot.
`PlotMarkerLayer` owns dataset composition and injected save/error/selection
operations. Neither imports SQL, the global main window or reference code. Shapes
are painted directly rather than creating/removing child items while painting.
Source paint primitives and worker-border ordering preserve native output.
Qt receives `prepareGeometryChange` before marker resizing. Canvas fit changes
update visual scale without changing stored points; layer items are released
before scene clearing to avoid deleted C++ wrappers.

Moving/scaling records pending intent once on release. Save invokes the existing
transactional position writer; only success accepts the draft. A failed writer
logs diagnostics, reports a localized message and retains the edit for retry.
Cancel restores the last saved position and scale. Job movement disables peer
markers until Save/Cancel. Accepted job saves rerender shared station placements
without rewriting saved worker points. Pending edits reject dataset/map replacement
instead of disappearing. Final parent consent controls remain to be composed.

Zero-valued anchors are preserved; source `value or 18` incorrectly treated zero
as missing. Renderer loading never silently creates or persists worker positions.
The original cursor-centered coordinate update/rounding is replaced by Qt's normal
grab-offset drag while preserving original-image top-left position semantics.

## Evidence

Five focused regression cases cover both languages, individual/comparison/job
composition, failure/retry, Cancel, zero anchors and shared placement fanout,
actual viewport drag/Ctrl scaling, locked items, resize stability, visibility,
neutral scientific gates, literal tooltips and rejected plant/pending replacement.
All 848 native baseline tests pass; coverage is 96.24%. Ruff check/format, strict
mypy (175 source files), architecture and wheel/sdist builds pass.

The isolated extracted wheel renders all three views, saves/reopens actual
synthetic projects, retries a controlled save failure and retains worker geometry
after a zero-anchor job save. All 500 reference hashes and the approved dependency
lock remain unchanged. See `f107_validation.json` and `artifacts/f107-check.log`,
`artifacts/f107-wheel.log`, `artifacts/f107-native.log`.

Twenty-one native captures under `artifacts/plot-markers` cover source/new glyphs,
English/Spanish empty, populated, comparison/selected, job pending/Cancel/saved,
Spanish Save error and enlarged compositions. Review covered map/rail/filter
containment at 1460×1060 and 1920×1200. Three same-platform synthetic source/new
marker images match pixel-for-pixel; this establishes fixture rendering parity,
not application-wide or cross-platform parity. Existing dark map-title contrast
is a known earlier limitation; no contrast improvement is claimed here.
Capture/verifier scripts are archived in `docs/reference/f107-*.py.txt`.

## Next and limits

Production PLOT navigation remains disabled. The next slice integrates the
original worker/job overview, position fields/buttons and context-menu actions
with these owned selection/save operations, then summaries and complete window
composition. Worker creation/visibility controls, Load Into Tool handoff, parent
close consent and remaining map actions still require integration. No final PLOT
layout, VTK, scientific model, dependency, unit policy or project format changed.
JROT remains subsequent work: CBC for single-tool, HiGHS for multi-tool, no GLPK.
Overall completion percentage and finish date remain unvalidated; the old 67%
figure is not reused as a reliable application-parity estimate.
