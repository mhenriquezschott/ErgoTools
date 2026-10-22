# Original integrated side panels — F77

Launch `.venv/bin/python -m ergotools.bootstrap --integrated-preview`.
The preview now has the original left/model, central/tasks and right/results
composition. The VTK avatar is still pending; its absence is explicit.

## Reviewed UI code and ownership

`setupResultsSidebar`, `RiskGauge.paintEvent`, `DamageScale.paintEvent`,
`setupControlPanel`, `bodyPanelDivider` and the active main composition supply the
control geometry and layout. Card margins/heights, gauge arc/needle/fonts, palette,
scale, legend, spacing and processed light icons are preserved. The preferred
400×400 viewport size comes from the reference environment's
`QVTKRenderWindowInteractor.sizeHint`; no VTK module is imported by the new code.
Body-panel widths remain 240-285, results 230-260; the target window remains
1550×1015. Screenshots verify the source port instead of defining geometry.

The left viewport temporarily says "3D view unavailable" and disables its view
buttons. No model or actor is simulated. Native complete-avatar/clipping checks
must follow the actual renderer adapter. The renderer dependency remains subject
to exact-version approval; no runtime package has been installed here.

`ResultsSidebar` receives canonical source and `evaluator.current(active)` results
from the owning window. It does not access SQL, parse widget text or own scientific
calculations. Counts match reference positive-repetition counting and per-row
integer truncation; average load uses present recorded values, including partial
rows; max moment uses current calculated row outputs. Metrics and moments use
recorded source units. Unit/display policy integration with final settings remains
on the plan. Missing inputs and blocked metric calculation remain distinct.

The original 300-ms summary polling timer is replaced by updates on load,
calculation, edits, reset and language changes. QVariantAnimation retains the
original 750/700-ms OutCubic drawing transitions. Identical targets retain their
animation progress; color-only changes repaint. Missing/stale results stop the
animation and clear immediately. These changes prevent repaint chains and stale
results without adding background/concurrency infrastructure.

## Status and localization corrections

PARTIAL results remain visibly Incomplete even when complete rows contribute
positive damage. Complete zero-damage inputs have no modeled probability; absence
shows a dash/unavailable label rather than inventing a low-risk probability.
Invalid/review outcomes clear all result colors and scales. Gauge values preserve
the original bounded probability display (<5 maps to 0, >90 to 100); damage above
2 uses the original >2.0 caption. All scientific formulas/gates remain unchanged.

English/Spanish captions, legend and tooltips are provided. Spanish unavailable
risk uses "No disp." with the full "No disponible" tooltip to fit the original
header width. The task-tab captions still require localization when the remaining
views are connected. Menu/settings exceptions remain governed by final-targets.

## Verification and limits

Five focused regressions cover card/grid coherence, typed metrics, immediate stale
clearing, unchanged animation progress, incomplete/reset state, empty/metric-review
outcomes, localized captions/assets/tooltips, target-size bounds, scale limits,
invalid numeric/color rejection, and stopping animations. All 632 tests and quality
gates pass; combined coverage is 96.86%. Original/new sidebar drawing and populated
card construction are inspected at identical dimensions. Full empty, complete,
partial, reset, Spanish and 100-row bottom-scroll states are inspected natively.

Independent extracted-wheel checks exercise the connected panels and packaged
icons with partial calculation, Save/reopen and actual Settings Cancel. Evidence is
`f77_validation.json`; captures are `artifacts/main-panels/`; reproduction scripts
are archived under `docs/reference/`. All reference and lock hashes remain intact.
No VTK render, Windows/macOS compatibility, full menu or full application parity
is claimed. The hidden development harness ownership remains transitional.

## F78 follow-up

The former unavailable left viewport is now the actual packaged VTK avatar in the
integrated CLI. View controls are enabled and risk display is connected. Earlier
F77 verification remains historical; see [native renderer](vtk_body_renderer.md)
for current evidence and limits.
