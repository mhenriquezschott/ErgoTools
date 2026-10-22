# Comparison-gauge typography aligned with its legend

Owner request, 2026-10-17: match Individual average / Job average to Risk ranges,
and match the risk subtitles directly beneath those headings to the legend text.

The headings already share the same 13 px section-heading rule. Risk subtitles
increase from 11 px to 12 px and now share the exact compact-legend font-size rule.
Existing weights/colors, bottom captions, arc size, tick defaults, preferences and
all other layout/scientific behavior remain. One presentation stylesheet changes;
no dependency, database/project, formula, history or reference change.

Twelve native Linux XCB comparison-panel captures inspected: English/Spanish,
LiFFT/DUET/ST, minimum/enlarged sizes, including available and unavailable Job risks.
Actual Qt fonts confirm headings 13 px and risk subtitles/legend 12 px. Rich-text
subtitle widths fit their labels. Full-size EN/ES DUET checks and all capture contact
sheets show complete text with no new clipping. Capture checks use disposable native
project copies; both maintained native project hashes remain unchanged this round.

Final Linux gate: **1,379 passed, zero failures/skips, 95.40% coverage**.
Standards/types (262), documentation/review (423 files) and wheel/source builds pass.
The changed module matches the rebuilt wheel. See
[final validation](../artifacts/comparison_gauge_typography_validation.json),
[source review](../artifacts/comparison_gauge_typography_review.json) and
[native record](../artifacts/comparison_gauge_typography_review/validation.json).

Migration/cleanup stay 100%; no milestone added. Existing chart-fit/animation
observations remain separate; Windows/macOS native acceptance stays deferred.
Next: owner Linux visual feedback; no additional implementation is active.
