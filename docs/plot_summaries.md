# F113 — original PLOT summary calculations and charts

Source: `src/plant_layout.py`, `loadSummary`, `loadJobRiskSummary`,
`onSummaryPlotChanged`, `generateTotalWorkerRiskDistributionPlot`,
`generateWorkerRiskDistributionPlot`, `generateWorkerRiskByAgePlot`,
`clearSummaryForEmptyScope` and default graph styling. Reviewed source arithmetic,
series ordering, widths, fonts, colors and chart size are the starting point.

`summarize_plot` is a read-only application operation over `PlotResults`. It returns
immutable selected-tool worker totals, job-placement totals and all-tool chart
series. No query, Qt object, storage adapter, renderer or dependency enters the
calculation. Saved enable controls inclusion independently of marker visibility,
position or lock. Hidden/unplaced enabled assignments remain included. Worker
counts preserve the source assignment-row policy rather than deduplicating a worker
who holds different assignments. Sex/age grouping uses saved metadata and the
existing birth-year age policy; missing metadata stays absent. Ten-year age bins
span the source minimum/maximum, including intermediate empty categories.

Damage is dimensionless; individual probability converts from 0–1 to percent once,
while job evidence is already percent. Means use available observations only.
Error bars retain the source population (N) standard deviation, not sample
standard deviation or standard error. Observed zero remains valid. NaN/infinite,
boolean and out-of-range probability observations are rejected explicitly. Unit
labels never drive these dimensionless calculations or rewrite sources.

Selected-tool totals include total assignments, average known age, male/female
counts, available damage/risk averages and paired individual/job comparison.
Job totals preserve unique jobs, active placements, positioned/unpositioned
stations, available approved profiles, placement-weighted damage/risk and min/max
risk. The job chart retains sorted job IDs and active placement counts.

`summary_figure` owns new Matplotlib `Figure` instances directly, without pyplot
registry/global-window behavior or file I/O. It creates the original three worker
charts and placed-job horizontal chart, with English/Spanish titles, axes and
legends. Default risk axes, series colors, bar/error-bar styling, dimensions and
compact graph padding are retained. Explicit legend proxies keep the correct
series color even when a group has no bar. Empty scopes clear the chart using the
source centered message/hidden-axis presentation; unavailable age/risk evidence
also redraws instead of leaving a previous chart visible.

## Deliberate corrections

Missing/scientific-review evidence is excluded rather than treated as zero risk or
zero damage. Missing groups therefore have no zero-height bar/error-bar stroke;
category labels remain. Comparison differences average individual minus applicable
job risk for the same paired assignments. The source subtracted averages from
different populations when some workers lacked job evidence. Average age and
sex-specific absent observations return None rather than fabricated zero. Empty
messages use an actual newline rather than the source's literal escaped sequence.
These corrections preserve scientific gates and do not change any model formula.

## Validation and remaining composition

Five focused cases cover enabled membership across tools, missing/zero and absent
metadata, source population deviation, invalid probabilities/year, paired
comparison, unit independence, placement weighting/anchors/profiles and rendering
all localized populated/empty charts. The baseline gates pass: 870 tests, 96.43%
coverage (see exact evidence), Ruff/format, strict mypy on 182 source files,
architecture, wheel and sdist. The extracted wheel independently renders all
figures and verifies summaries, paired populations and unchanged saved
positions/history after reopening the synthetic project.

Thirty-four native Qt canvas captures were visually inspected: source/new chart
fixtures plus English/Spanish populated, empty, unavailable-age and enlarged
states. Tool, sex and job source fixtures match pixel-for-pixel at 310×230. The age
fixture differs at 61 pixels where the source draws zero-bar strokes for the empty
intermediate age bin; this is the documented missing-evidence correction. Both
languages fit at normal/enlarged sizes. No adjacent main-window UI, avatar, cards or
bottom controls changed in this slice. Standalone chart evidence does not establish
whole PLOT or final application visual parity.

Evidence: `f113_validation.json`, `artifacts/f113-check.log`,
`artifacts/f113-wheel.log`, `artifacts/f113-native.log`,
`artifacts/plot-summary-charts`, and `reference/f113-capture.py.txt` /
`reference/f113-verify.py.txt`. All 500 reference hashes and approved lock remain
unchanged. No dependency or reference-environment change was made.

Next: original Tools Overview panel, map symbol legend, graph settings and expanded
viewer, using these summary results/figures. Then outcomes and complete PLOT host
composition, parent close/load handling and remaining map/deletion actions.
Production PLOT remains disabled. JROT follows with CBC single-tool, HiGHS
multi-tool and no GLPK. Overall completion percentage and finish date remain
unvalidated.
