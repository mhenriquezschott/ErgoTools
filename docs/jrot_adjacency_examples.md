# When consecutive High Jobs are optimal

The workflow_4_workers project now includes Demo 11–14. Each uses three workers,
three Jobs and six blocks. The synthetic LiFFT coefficients are **0%, 5% and 55%**:
AJ01 Visual sorting, AJ02 Label inspection and AJ03 Container transfer. Only the
last Job is High under the current greater-than-50% rule. Worker assessments and
all earlier Jobs/rotations are retained. Each example has a kept result already saved.

| Demo | Timing | No consecutive High | Optimal maximum worker index |
|---|---|---|---:|
| 11 | Six equal 80-minute blocks | Off | 20.000 |
| 12 | Same equal blocks | On for all three workers | 20.000 |
| 13 | 120 / 20 / 20 / 20 / 140 / 160 minutes | Off | 20.000 |
| 14 | Same unequal blocks | On for all three workers | 20.625 |

Start with **Demo 13**, open **07 Optimization**, then select **Demo 14** and open
07 again. Both have the same Jobs, workers, baseline and timing. In Demo 13, V01's
saved real optimizer result has High in consecutive blocks 3 and 4. Demo 14 has no
worker with consecutive High. Its optimal indices are 20.625, 20 and 19.375. Existing
two-decimal displays show 20.62, 20.00 and 19.38; the saved values retain precision.
Step 03 shows the rule difference; 04 shows the same original baseline in both.

Demo 11/12 is the equal-duration comparison. Demo 11's actual CBC result has V01 on
High in blocks 3 and 4. Demo 12 separates High Jobs, and every worker still scores 20.
An unconstrained solver may choose another tied optimum with different ordering in a
future run. The unequal Demo 13 case is stronger: **every** unrestricted optimum
requires adjacency, so the contrast does not depend on which tied result is chosen.

Step 08 compares each result with its own baseline, not with the other Demo record.
All four baselines already have an optimal maximum of 20 but contain adjacent High.
Consequently, the constrained unequal result has a slightly higher maximum. The hard
restriction takes priority over improving the balancing objective. Rotation redistributes
exposure; it does not change the intrinsic risk of the 55% Job.

## Why these are proven optima

Each block staffs one worker at each of the three Jobs. The sum of Job coefficients
is 60, so the population mean is always 20. No maximum worker index can be below 20.
The unrestricted schedules and both equal-block schedules achieve 20 exactly.

For unequal timing, all durations are multiples of 20. A worker with index 20 must
satisfy `55 × High minutes + 5 × medium minutes = 20 × 480`. With the available
minutes, that forces High minutes 160 and medium minutes 160. The 160-minute final
block therefore occupies one worker's entire High allocation. Another worker needs
the 140-minute block plus one of the three 20-minute blocks. The remaining worker
needs the 120-minute first block plus two of those three short blocks. Every such
choice gives that worker adjacent High, either at the first boundary or between
short blocks. Thus an unrestricted maximum 20 is incompatible with the rule.

An independent enumeration of all **6^6 = 46,656** staffed schedules uses integer
arithmetic to prove the next restricted optimum is 20.625. Real CBC attains it and
passes the rule checks. Permanent regressions are in
`tests/test_rotation_adjacency_demonstration.py`. The equal-case test deliberately
allows alternative unconstrained ordering while requiring the restricted guarantee.
These are mathematical optimizer fixtures, not measured ergonomic assessments.

## Repeating the experiment

Review the kept results first. To rerun, use Run optimization in 07 and explicitly
Keep optimization result if wanted, then Main Save. To change a rule within one
rotation, use 03 Worker restrictions. A kept result remains frozen evidence until
replaced; a changed setup can make that old result stale. Each accepted edit remains
undoable. Create a duplicate when keeping separate experimental histories is useful.

For larger controlled fixed/excluded and duration examples, see
[Demo 15–20](jrot_rule_timing_examples.md): four workers, four Jobs and eight blocks.
