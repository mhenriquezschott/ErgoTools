# F115 — original PLOT outcome summary, gauges and warning details

Reviewed reference: `src/plant_layout.py`, `PlotRiskGauge`,
`PlotHighlightDetailsDialog`, the outcome region in `configureResponsiveLayout`,
`updateOutcomeRiskLayout`, `loadSummary`, `loadJobRiskSummary`, `loadOutcome`,
`clearOutcomeForEmptyScope`, `setComparisonGaugeValue` and
`updateAppliedToolOutcomeTitle`; plus the source `risk_ranges.py`.

`PlotOutcomePanel` composes the original ten filtered-result cells, Highlights
row and View details button, categorical risk ranges, single gauge and two-column
comparison gauges. Source margins, grid spacing, widths, colors, typography,
processed icons, captions and risk-category thresholds are retained. English and
Spanish views use the existing risk catalog. The already packaged `view.png` is
now exposed through `load_icons`; no asset or dependency was added.

The panel consumes saved `PlotResults` and F113's immutable summaries. Individual
and Job views use the appropriate observed risk average; comparison shows the
individual average and available paired Job average. The existing F113 correction
keeps difference populations paired. Risk percentages and damage are dimensionless;
metric/imperial settings do not change them or rewrite source assessments. Age
retains the reference truncated integer display. Missing evidence displays an en
dash or N/A, rather than fabricated zero. An observed zero remains available.

`PlotRiskGauge` preserves the PLOT-specific arc, needle and text geometry. It
reuses the owned QVariant animation already used by assessment scales, with the
source 700-ms OutCubic easing. Floating endpoints keep integer inputs and the
100% boundary interpolatable. Identical targets do not restart animation; new
targets start from the currently displayed value. Missing results clear
immediately. Nonfinite/boolean inputs fail explicitly, and finite display values
clamp to the reference range. Closing the outcome panel stops owned animations.

`plot_highlights` is a read-only application operation, using stdlib and domain
contracts. It preserves the original strict >50% warning threshold, saved enabled
worker membership and active Job-placement membership. Hidden/unplaced enabled
workers remain eligible. Missing evidence is excluded. `StationHighlight` keeps
complete station identity, count, observed mean and maximum percentages.

`PlotHighlightDialog` retains the original 760 x 420 size, 720 x 390 minimum,
station/count/average/maximum columns, column resizing, severity backgrounds,
contrast calculation, selected-row treatment and processed Close button. Station
identities remain plain text, including literal markup characters. Duplicate
station IDs show their complete paths; each row also has a full-path tooltip.
Opening, selecting and closing details perform no project write.

## Deliberate corrections

- Source station-ID-only grouping merges equally named stations in different
  branches. Full plant/section/line/station grouping preserves their ownership.
  Ordinary unique station IDs retain their original short display.
- The original outcome group's declared 700-pixel minimum cannot contain its
  600-pixel summary region and 701-pixel risk cluster. Its 210-pixel fixed height
  also clips long risk headings and wrapped unavailable messages. The minimum
  width and height now follow actual content, retaining 700/210 as floors.
  Long headings/statuses wrap, and warning height follows its available width.
  The inspected fixture needs about 1355 pixels wide and 238 pixels high. This
  is a documented clipping correction, not an exact full-strip pixel match.
  Neighboring map/chart regions move and resize with the outcome strip.
- Unavailable worker evidence now has a clear neutral message and absent gauge;
  the source could attempt numeric arithmetic on missing outcomes.
- Resize reflow does not reload storage, recompute summaries, republish marker
  results or restart animation. Visual drafts likewise leave saved metrics alone;
  explicit successful Save publishes changed enabled membership.

## Acceptance and next integration

Six focused cases cover strict threshold and duplicate station ownership, missing
and observed-zero evidence, saved enable vs visibility/preview, actual modal
warning navigation/Close, literal identities, localized modes, gauge easing,
retargeting/identical targets, finite/clamped endpoints, clear/closure, complete
native child bounds and wrapped message height at the true minimum.

The baseline gate passes 883 tests with 96.70% combined coverage, Ruff/format
(423 files), strict mypy (192 source files), architecture, wheel and source archive.
The independent extracted-wheel workflow verifies actual localized modal details,
all three outcome modes, zero/absence, full station identity, minimum-size bounds,
wrapped unavailable messages, animation closure, the 100% endpoint and unchanged
positions/history after reopening the synthetic project.

Seventy-six native captures were visually inspected: 21 original/new gauge pairs
across all threshold boundaries, zero, missing and three widths; localized
individual/job/comparison, empty/unavailable and minimum states; details
populated/selected/empty/enlarged; and adjacent map/Tools Overview compositions.
All 21 gauge fixtures and the focus-normalized original warning dialog match
pixel-for-pixel. The outcome layout's width/height/wrapping corrections and changed
child geometry are recorded explicitly; full-strip equality is not claimed.
No main-window avatar, assessment cards or bottom controls changed. These composed
synthetic PLOT fixtures are not the final complete PLOT window.

All 500 reference hashes and approved dependency lock remain unchanged. Evidence:
`f115_validation.json`, `artifacts/f115-check.log`, `artifacts/f115-wheel.log`,
`artifacts/f115-capture.log`, `artifacts/plot-outcome`, and archived capture/wheel
scripts under `reference/`.

Next: compose the complete original PLOT host from the migrated map, filters,
worker/job overviews, chart and outcome regions. Connect parent close/load consent
and the remaining map/deletion actions into complete usable workflows. Production
PLOT stays disabled until those workflows pass. Then JROT: CBC single-tool,
HiGHS multi-tool, no GLPK. Overall completion percentage and finish date remain
unvalidated.
