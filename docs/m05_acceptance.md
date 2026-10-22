# M05 complete — PLOT filters and risk results

**86.50/100 overall; 5/12 milestones complete; 12.50/26 remaining-baseline
points earned, 13.50 still to earn.** Fixed M05 earns 1.25 points. M06 next,
not started. One bounded comparison pass completed; no production correction
needed, no new feature/milestone, no dependency or reference changes.

## M05.1 — matched data and results

The current independent wheel was compared against AST-extracted original
`plot_worker_records` and `plot_job_records` functions. Original code was read,
not imported through application startup. Original database bytes were loaded
into an isolated in-memory connection; conversion used a disposable full copy.

48 cases cover four complete hierarchy/shift scopes, three tools and four
settings: no demographics, Female, Male plus age 20–60, and weight/height bounds.
Worker/assignment identity, all-tool identity, placement identity and active
assigned-worker counts match. Worker damage and probability match original saved
values at 1e-12 tolerance, preserving dimensionless damage and percent scaling.
Enabled assignment counts, age/sex/damage, available risk, paired Job comparison,
unique jobs, placements, positioned/unpositioned stations, approved profiles,
placement-weighted damage/risk and min/max pass independent expectations.
The comprehensive data includes a placement without selected-tool risk; it stays
missing. Existing focused tests verify missing worker observations and observed
zero independently, inclusive/incomplete/reversed bounds and canonical unit
projection. No missing values become invented zero observations.

The first raw comparison found 16 count/average differences, all explained by
three **already documented F131 recovered LiFFT sources** for V001 on assignments
101/102/104. The original normalized table omits them, while its old source table
retains them. Its raw all-shift LiFFT population is 97 versus converted 100;
this is preservation/reconciliation policy, not a new filter bug. That raw
comparison is retained in artifacts/m05/raw-comparison.json. For matched data,
only the in-memory original-query oracle represents those exact three archived
records on their existing owners. The final 48 cases have zero unexplained
differences. No operational/archive source bytes were changed or repaired.

F113's established paired-comparison rule is retained: average Individual minus
Job for the same paired assignments. Two cases differ from the original's
subtraction of unrelated population averages; both formulas are recorded in the
comparison JSON rather than claiming literal equality. Available-evidence means,
missing values, complete station ownership and zero handling remain the documented
F113/F115 migration policies. No scientific formula is changed.

## M05.2 — original controls and usable workflows

Reviewed original configureResponsiveLayout, demographic disclosure, resetFilters,
getWorkers and summary methods. Existing source-extracted F103/F104 filter and
F115 result/gauge/detail comparisons remain applicable because PLOT code has not
changed. Original expanded-filter and original/new outcome captures were inspected
individually alongside the current complete PLOT windows. The recorded F115
content-driven width/height/wrapping correction remains explicit; exact full-strip
pixel equality is not claimed. Gauge fixture equality and original assets/styles
remain covered by that source comparison.

Six current native images inspected: EN Individual/Job/Comparison at 1460×1060,
expanded workplace picker with Cancel, ES populated Female demographics and empty
worker results at 1800×1200. Native gauges were settled before capture. Complete
filter, map, tabs, outcome, Apply and Clear bounds pass; neighboring regions fit.
Actual risk buttons publish the selected mode. Apply filters Female rows correctly;
empty worker results clear the chart/summary and show N/A, while Job data remains
independent of worker demographics. Picker Cancel retains scope/results; Clear
then Apply restores workers. The converted project file is byte-identical before
and after the native scenario. Existing focused tests also verify accepted scope,
failed read retention and rejected Apply/close with pending edits.

## Validation and limits

**41 focused packaged tests pass**, covering results, filters, summary/outcome and
host workflow. No source/test changes: reuse the unchanged M04 full standards and
build gate, **1,162 tests and 96.44% coverage**, rather than rerunning it. Current
wheel and exact dependency lock are byte-identical to M04; all 500 reference
manifest hashes are unchanged. Archived M05 scripts reproduce comparison/native
checks with the approved interpreter and extracted package.

M06 owns final map/marker, chart/settings/details and export acceptance; M05 does
not claim those complete just because they are visible here. M09 owns the broader
shared localization/units/resize matrix. Windows/macOS VM testing remains deferred
under CR001 and is not reported as passed. No additional work is proposed.
