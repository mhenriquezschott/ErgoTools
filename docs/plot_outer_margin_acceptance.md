# PLOT outer inset aligned with JROT

Owner request, 2026-10-17: PLOT's groups/frames sit too close to its window edges.
The root now uses JROT's 10 logical pixel inset on every side, replacing 2/8/2/8.
Initial/minimum window dimensions add 16 pixels horizontally and 4 vertically to
preserve interior allocation. Default size is 1476×1124; live content minima still
apply. No other layout, workflow, history, gauge, solver or data changes.

Final native Linux gate: **1,379 passed, zero failures/skips; 95.40% coverage**.
Standards/types (262)/documentation (423)/review/build checks pass. The one changed
module was substantively reviewed and matches the rebuilt wheel. Eight EN/ES
native captures at minimum/enlarged sizes with demographics on/off were inspected,
including full-size header/margin checks. Every top-level panel has exactly ten
pixels at left/right; the minimum panel remains 1407 pixels wide before and after.
Existing rail bounds and no plant-image scrollbars are verified. Both maintained
fixtures retain this round's starting bytes; reference and approved lock untouched.

A separate minimum-size chart-label overlap was reproduced when switching straight
to Comparison after opening, in both the preceding accepted wheel and this change.
The x-axis label can meet/overlap the chart selector; enlarging provides room.
This is not a margin regression or newly accepted chart fit. It is recorded for
owner review without silently adding a chart correction to this spacing request.
See review_register.md and the baseline/current capture manifests for reproduction.

Migration/cleanup stay 100%; no new milestone. Next: owner visual/testing feedback.
Windows/macOS native testing remains deferred.

[Validation](../artifacts/plot_outer_margin_validation.json),
[visual record](../artifacts/plot_outer_margin_review/validation.json).
