# TST task calculation — F20

## Preserved model behavior

The isolated domain TstTask/TstTaskResult and calculate_tst_task preserve the active reference TST 0.1.2 model. TstDirection values 0/1/2 mean the model formulas Handling Loads, Push or Pull Downward, and Horizontal Push or Pull. F21 corrected the initial UI-mapping claim: main.py swaps selector indices 1 and 2 before model invocation; see [the discrepancy audit](tst_summary.md). The old source comment mentioning a fourth direction is not implemented by the reference and is not adopted here.

Normalize arm/load to inches/lbf using the existing 2.54/4.45 compatibility divisors. For arms from 1.715 inclusive to 27 exclusive inches, arm moment is (-8.27 + 4.8223 * arm) / 12; at/above 27 it is 121.9 / 12; below 1.715 it is zero. Load moment uses load * arm / 12 in that order. Handling adds the arm term, downward uses load moment alone, horizontal uses abs(load moment - arm moment). Boundary behavior and the slight discontinuity at 27 are preserved.

Damage per cycle is 1 / (10 ** ((101.25 - 100 * (moment * 12 / 681)) / 14.83)). Unlike LiFFT, this moment is NOT rounded before damage calculation. Multiply by repetitions and round task damage to five decimals. Only displayed moment rounds to one decimal. The positive-damage probability retains predictor 0.864 + 0.928 * math.log(damage, 10), then exp(predictor)/(1+exp(predictor)), on the 0-1 scale.

Metric display uses the same isolated unresolved expression (moment / 0.73756) * 9.81 as the reference. This is compatibility characterization, not a validated physical conversion. No TST result is integrated into the mixed application evaluator yet. The scientific metric review gate must be enforced before such integration, as for LiFFT.

TST's 105-entry continuous palette was verified identical to DUET's and extracted into presentation.desktop.theme.upper_limb_colors. Each model retains its own probability function/color mapper. Thresholds remain damage < 0.00002 / > 136, otherwise palette[int(probability * 100)]. No UI or asset changed.

## Explicit input and error contracts

Original task values and task identity are immutable. None represents unfinished input. Only a TstDirection enum is accepted; raw selector representations require deliberate boundary conversion. Missing/unsupported direction, negative/boolean/nonfinite numbers and missing numeric fields raise structured DraftError. Fractional repetitions and zero remain supported. Invalid fields can exist in an editable task before calculation. Blank identity is rejected on construction. Direction messages exist in English/Spanish.

The reference can return negative damage for negative repetitions, negative moments for signed inputs, TypeError for direction 3 and ZeroDivisionError for very large moment. Those observations are captured separately. The new calculator rejects unsupported inputs, nonfinite moment/damage and an underflowed zero denominator with validation.overflow. It does not return partial output or short-circuit zero repetitions before evaluating moment/damage-per-cycle. Unsupported measurement systems still raise ValueError. No scientific constants, physical limits or alternative exponential approximation were introduced.

## Call-site audit and reference evidence

The active main.py method swaps selector indices 1 and 2, then uses that direction with selectedMeasurementSystem and float inputs. This mismatch with its visible labels requires review. It warns but continues on incomplete rows, with a zero-repetition preview when arm/load exist. It sums rounded damage in row order, displays task damage to five places and positive totals to four, rounds contributions to one place, and bounds rounded probability text with < 5 / > 90. Both shoulder actors use the total color. These are inspected source rules, not yet migrated/visually tested summary behavior.

Reference pyTST.py SHA-256: `1674be87b52b3013c5177a504a74efd1276711e09ed53a9e75b8e79999bc4099`. Runtime: `3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]`. `tests/fixtures/tst_calculation_reference.json` stores 1,650 actual task outputs, 16 probability/color cases and unsupported-input observations. Capture used the original standalone class under -B, without Qt, database access or bytecode writes. Existing licensing remains intact. The full harness is archived as `reference/f20-capture.py.txt` for deliberate reviewed reproduction.

Task inputs cross both systems, all directions, eleven arms including adjacent floats around 1.715/27, five loads (0, 0.5, 1, 10, 100), and five repetition counts (0, 0.5, 1, 100, 10000). Metric pairs use arm * 2.54 and load * 4.45. Exact unrounded model moments, displayed moments, damages and colors match. Probability tolerance is relative 1e-14 / absolute 1e-15. Eight new tests cover reference cases, unrounded damage order, missing/invalid inputs, overflow, direction semantics, immutability and translations. Earlier DUET palette/reference tests still pass.

222 tests pass; combined coverage 99.52%, new TST/palette modules 100%. Ruff/format, strict mypy (63 files), architecture and both builds pass. Independent package/reference/dependency evidence: f20_validation.json.

## Next work

Capture the actual TST assessment-summary method and extract typed totals/display mappings, followed by source draft/history/storage and mixed-project integration. Preserve the metric review gate. Scientific validation, GUI/VTK integration, other workflows, legacy migration and native packaging remain pending; no runnable replacement desktop app exists yet.
