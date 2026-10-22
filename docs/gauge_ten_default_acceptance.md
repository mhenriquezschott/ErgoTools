# Ten-point gauge default and comparison text audit

Owner request, 2026-10-17: all shared risk gauges should initially show ticks every
ten percentage points, together with their range limits. Comparison title/subtitle
size was questioned; no text-size change was requested or made.

GaugeMarkerSettings now defaults to visible ticks, visible range labels and interval
10. Older personal settings without gauge fields derive the same validated defaults;
reading them does not write. Explicitly saved format-5 choices, including five-point
spacing or hidden ticks, remain unchanged. Main/PLOT/Settings consume the same value.
Current guides reflect the ten-point default; native schema and personal format stay
16 and 5. No dependencies, formulas, project data or reference writes.

The comparison stylesheet is identical to the earlier Linux delivery wheel: titles
13 px, risk subtitles 11 px, bottom captions 11 px. See
[font audit](../artifacts/gauge_comparison_font_audit.json). No font edits were made.

Focused regressions pass (47 tests). Final Linux gate: **1,379 passed,
zero failures/skips; 95.40% coverage**. Standards/types/documentation/reviews
and builds pass. Both changed production modules and the bilingual HTML guides
match the rebuilt wheel. Final required gate results are in
[validation](../artifacts/gauge_ten_default_validation.json). Six native EN/ES captures
of the main gauge, PLOT comparison and Settings were inspected; existing user files
were not used as write targets. Three changed source/test files were substantively
reviewed; mandatory documentation gates remain active.

The owner explicitly confirms application-wide persistence, superseding the interim
per-project answer. Options stay in personal settings format 5, shared across main,
PLOT and all projects and retained across restarts. Saving a project does not own
or reset these options. The in-progress project-storage changes were withdrawn;
exact source bytes match the tested wheel. No new table, columns, protocol or
project save-lifecycle change remains. Changing the fresh default does not overwrite
any existing saved choice. See artifacts/gauge_project_scope_withdrawal.json.

Migration/cleanup remain 100%; no milestone added. Next: owner testing feedback. Existing chart-fit/animation observations remain separate.
