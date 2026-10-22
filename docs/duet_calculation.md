# DUET task calculation — F14

## Contract and compatibility

`domain.assessments.duet` defines frozen DuetTask and DuetTaskResult values, calculate_duet_task and probability_from_damage. Original source values and stable task identity are retained; None means unfinished input. The OMNI-Res selector is an integer from 0 through 10, dimensionless; repetitions retain the reference's fractional numeric support. There is no metric/imperial conversion in this model.

The active reference version 1.3.0 damage table has eleven unchanged entries. Task damage is round(table[index] * repetitions, 5). Scale zero has a nonzero per-cycle value (0.00000026); it must not be treated as no exposure. The coefficients and probability evaluation order remain predictor = 0.573 + 0.747 * math.log(damage, 10), then exp(predictor)/(1 + exp(predictor)). Probability accepts only positive finite damage on this API; the output is on the 0-1 scale. This is reference equivalence, not independent scientific validation.

The unchanged 105-entry palette is presentation-owned and distinct from LiFFT's palette. Damage below 0.00002 gets the first color, above 136 the last; otherwise the index is int(probability * 100). Task damage zero retains the reference first color. Assessment zero-total handling is separate and not integrated here. No icons or windows changed.

## Input differences and shared validation

The reference int(scale) truncates fractional values, accepts boolean values, and lets negative indices access the end of its table. Captured examples include -1 selecting the final entry, 1.9 selecting entry 1, 10.9 selecting entry 10, and 11 raising IndexError. The new typed API requires an actual integer 0-10, rejecting even 1.0 at this boundary. This matches the integer currentIndex from the existing eleven-choice UI; its legacy conversion to float was unnecessary. Parsing/import adapters must explicitly validate/convert external representations rather than rely on truncation. The new validation.omni_scale issue has English/Spanish messages.

Missing values, negative repetitions, booleans and nonfinite repetition counts produce structured issues. Finite nonnegative repetitions and lookup entries below one cannot overflow multiplication in the supported float range. The fixture covers repetitions up to 1e308. Task construction retains invalid fields for correction; calculation validates them. Blank task identity is rejected at construction.

InputIssue, DraftError and the finite-nonnegative numeric helper now live in `domain.assessments.validation`, independent of LiFFT or DUET. Existing LiFFT import locations intentionally re-export the same objects/function for compatibility. No numerical validation rule was silently changed by that move. LiFFT preparation and calculation continue to share the common helper. The helper accepts typed numeric inputs; it is not a locale-aware parser.

## Assessment call-site audit

`src/main.py:duetCalculateResults` uses the selector index and float repetitions, sums already-rounded task damage using row-order +=, and rounds task contributions to one decimal. Task labels show five decimals while the positive total label shows four. Probability display rounds to one decimal before strict `< 5` / `> 90` bounds. Missing repetitions warn but calculation continues with zero initialized rows. Zero totals use 0.0 labels; as in LiFFT, not all previous styles/row labels/actor states are explicitly cleared. The four forearm/hand actors share the total color. These are source observations; aggregation, incomplete-preview decisions and rendering have not yet been ported or visually tested.

## Reference evidence

Fixture: `tests/fixtures/duet_calculation_reference.json`. Reference pyDUET.py SHA-256: `53ac3bdfdaffcb6fa007505aac492af27d758987683cfc3a4bb8237bcf8c943f`. Original interpreter: `3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]`. The original standalone class was executed via runpy with -B, without importing Qt or accessing databases. Existing licensing is retained.

198 task cases cross all 11 scale choices with repetitions 0, 0.5, 1, 10, 100, 1000, 10000, 1e8 and 1e308, plus adjacent floating-point repetition values around damage targets 0.000005, 0.00002 and 136. Sixteen probability/color vectors include the smallest positive float, both threshold neighbors and extreme positive values. Unsupported-input observations are stored separately. Task damage/colors match exactly; probability comparisons use relative tolerance 1e-14 and absolute tolerance 1e-15. The complete capture harness is archived in `reference/f14-capture.py.txt` for reviewed regeneration, not production use.

Eight new tests cover reference outputs/table, probability/palette boundaries, invalid scales, missing/invalid repetitions, nonzero scale-zero damage, fractional repetitions, invalid probability/color values, identity/immutability and localization. All 166 tests pass, including every existing LiFFT regression. Combined coverage is 99.35%; new modules are 100%. Ruff/format, strict mypy (42 files), architecture and package builds pass. Independent verification is recorded in `f14_validation.json`.

## Remaining work

Next characterize DUET assessment summaries by executing the actual original method with inert UI stand-ins, then extract typed aggregation and presentation mappings. Whole DUET draft/history/storage, assessment coordination and GUI integration remain pending. Scientific validation and LiFFT's metric-moment review are still open. No dependency versions or original files changed.
