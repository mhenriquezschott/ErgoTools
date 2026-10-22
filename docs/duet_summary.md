# DUET assessment summaries — F15

## Implemented behavior

`summarize_duet_tasks` consumes ordered DuetTaskResult values and returns an immutable DuetSummary containing stable task contributions, total damage and optional model probability on the 0-1 scale. It does not recalculate inputs, persist results or control widgets. Source-draft completeness remains a separate pending DUET rule.

Totals use explicit row-order += on the five-decimal task damage, preserving the reference and avoiding the changed built-in sum behavior across Python versions. Contributions use round(task damage / total * 100, 1); rounding residuals are not redistributed. Empty/zero results yield zero shares and probability None, meaning the positive-damage model was not evaluated. Invalid/duplicate identities, boolean/negative/nonfinite damage and total overflow raise structured DraftError issues without returning partial summaries.

`display_duet_summary` provides immutable display state. Task damage text has five decimals, positive total text four, and zero total text is 0.0. A positive total of 0.00001 therefore displays 0.0000, but its probability still uses 0.00001. This reference precision difference is preserved and tested, not silently corrected. Probability rounds on the 0-100 scale before strict `< 5` / `> 90` bounds. None probability displays the legacy 0.0 placeholder without asserting zero risk. Task color is suppressed when its rounded share is zero. DUET uses its own unchanged probability expression and palette.

Zero summaries explicitly provide None colors and zero contribution strings so a future view can clear old state. The reference method leaves some previous row labels/styles/actor state untouched on zero recalculation. This is a documented intended stale-state correction; no live UI was modified or visually accepted. Decimal-point text is compatibility formatting, not full locale formatting. The caller must use summaries produced by the domain API.

## Standardization

LiFFT and DUET now share `domain.assessments.damage_summary` for identity/damage validation, sequential addition and rounded contributions. Models retain their own probability functions and metadata validation. LiFFT's unit checks occur before the shared helper; a multiply-invalid batch may now report a unit mismatch before an unrelated identity/damage issue. Valid outputs are unchanged. `LifftContribution` remains an import alias for the shared frozen DamageContribution class; its class name/repr is now DamageContribution. These result objects are not persisted by the source-draft codec.

Both assessment views share `presentation.desktop.theme.assessment_probability.format_assessment_probability`. The old format_lifft_probability import remains an explicit compatibility alias. This formatter is specific to these assessment displays; job/PLOT display policies must be audited separately. No generic model-probability abstraction or cross-tool merging was introduced.

## Reference evidence

Fixture: `tests/fixtures/duet_summary_reference.json`. Reference main.py SHA-256: `6e8a65a2ba7370b1dbda199110e3cfbe0b9f62d91ed9677ceea9f8483b3e2fc5`. Method AST SHA-256: `4d510a58236bd612c49d59fb417a3786467d69b68515ab7daf94500172921a54`. Reference runtime: `3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]`.

Capture extracted and compiled the unchanged actual duetCalculateResults method, using the original DUET class and inert selector/label/status/actor/render stand-ins. No Qt launch, database access or reference bytecode writes occurred. The archived harness `reference/f15-capture.py.txt` records exact inputs and capture details for deliberate reviewed regeneration. This is method-level characterization, not UI testing or scientific validation.

The 63 groups cover all eleven selector choices, empty/zero/round-to-zero cases, thirds, large totals, tiny shares, fractional repetitions and 21 deterministic multi-task groups. Tests compare exact totals, shares, summary text, row precision and all colors. Six new tests additionally cover zero clearing, rounding order, precision loss prevention before aggregation, invalid values/overflow and immutability. All 172 tests pass, including the 60 prior LiFFT summary fixtures. Combined coverage is 99.37%; new modules and modified LiFFT summary modules are 100%. Ruff/format, strict mypy (46 files), architecture and both builds pass. Independent package/reference/lock evidence: `f15_validation.json`.

## Remaining work

Next implement a DUET source draft and validated edit/history/preparation contracts, then versioned persistence. GUI/renderer coordination, full assessment integration, scientific review and the LiFFT metric-moment review gate remain pending. No runtime dependencies or original files changed.
