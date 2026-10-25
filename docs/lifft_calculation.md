# LiFFT task calculation — F11

## Contract and preserved behavior

`domain.assessments.lifft.calculate_lifft_task` accepts an immutable LifftTask and an explicit MeasurementSystem, returning a frozen LifftTaskResult with source identity, system, model moment, displayed moment and cumulative damage. It does not mutate or save the draft. Functions and modules use snake_case, result classes use PascalCase, and the lookup constant uses UPPER_SNAKE_CASE. Public APIs have type annotations and documentation of units, rounding and errors.

The reference order is preserved: normalize cm/N with divisors 2.54 and 4.45; compute arm in inches / 12 * load in lbf; round moment to one decimal; truncate to the integer lookup index, capped at 200; multiply the original 201-entry damage table by repetitions; round damage to four decimals. Python floating-point rounding is preserved, including boundary behavior. Fractional repetitions remain supported.

The positive-damage probability uses the active reference expression: predictor = 1.7229 + 1.0239 * math.log(damage, 10), probability = exp(predictor) / (1 + exp(predictor)). No alternate logarithm or coefficient was substituted. Zero damage is outside this function's domain; summary behavior needs its own explicit policy.

Metric display still uses the isolated compatibility expression `(model_moment / 0.73756) * 9.81`, rounded to one decimal. Its scientific interpretation remains unresolved; the result is deliberately named `displayed_moment`. See the unit audit. This task API is isolated from application assessment workflows and the GUI pending that review.

The original 103-color palette and its damage thresholds live in presentation, separate from domain calculations and the four-category gauge palette. No icons or windows changed.

## Explicit invalid-input differences

Missing fields produce structured `validation.required` issues with task and field identity. Booleans, negative inputs and nonfinite values are rejected; arithmetic overflow is rejected before returning results. English and Spanish messages cover the added validation keys. The draft remains able to retain finite negative/fractional source values for review; calculation imposes the stricter boundary.

In the reference, negative arm/load can raise UnboundLocalError, negative repetitions can produce negative damage, and two negative inputs can produce a positive moment. These outcomes are captured as observations, not reproduced as accepted calculation behavior. Missing values do not silently become zero. Metric display overflow currently uses the existing conversion ValueError contract.

## Reference provenance and verification

Reference: `src/pyLiFFT.py` in the unchanged source tree, SHA-256 `c83295524a2abf2f928c7209f58381278e5b6e5e490c495dd19c0a703acb2efe`. Fixture runtime: `3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]`. New checks use the approved project-local Python 3.13.14. Existing project licensing is retained.

`tests/fixtures/lifft_calculation_reference.json` stores 2,150 actual task results, 13 positive-damage probability/color cases, invalid-input observations, and the original lookup/palette data. Capture invoked the original class directly with its original interpreter, without importing the new calculator.

To reproduce task inputs, use integer target moments 0 through 200 plus 0.04, 0.05, 0.06, 0.95, 0.99, 1.05, 1.25, 1.75, 198.95, 199.94, 199.95, 199.99, 200.01 and 250.0; deduplicate and sort. Cross these with repetitions 0, 1, 0.5, 100 and 10000, and both systems. Imperial arm/load are 12/target moment; metric arm/load are 30.48/target moment * 4.45. Capture calculate() outputs and the rounded normalized model moment. Probability inputs are 1e-12, 1e-8, nextafter(0.0001, 0), 0.0001, 0.001, 0.01, 0.1, 0.5, 1, nextafter(1, infinity), 10, 1e100 and 1e300.

All task outputs match exactly; probability comparisons allow relative tolerance 1e-14 and absolute tolerance 1e-15. Eight new tests also cover invalid fields, overflow, immutability, saturation and translations. The complete suite has 141 passing tests and 98.92% combined statement/branch coverage. The calculator module has 90% coverage; defensive conversion/nonfinite/damage-overflow paths are not all exercised through the already-validated draft type. Ruff, formatting, strict mypy and architecture checks pass. See `f11_validation.json` for package/reference/dependency verification.

## Remaining scope

Behavioral parity is not independent scientific validation. Whole-assessment aggregation, task contributions, zero-total summary behavior, displayed risk clamping, application result coordination and GUI integration remain pending. Next characterize these summary rules from actual reference call sites and define typed assessment results. Keep the metric review gate explicit before integrating the assessment workflow. No dependency change is needed for this task calculation slice.
