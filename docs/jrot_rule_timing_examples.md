# Clear excluded-Job, fixed-Job and block-duration comparisons

The maintained workflow_4_workers.ergprj includes **Demo 15–20**, each with **four
workers, four Jobs and eight blocks**. Participants are V01 Elena Muñoz, V02 Mateo
Rojas, V03 Sofía Torres and W04 Diego Soto. LiFFT coefficients are AJ01 Visual sorting
0%, AJ02 Label inspection 5%, AJ04 Carton inspection 25%, AJ03 Container transfer 55%.
They are synthetic reference values for optimizer testing. Each result is already kept
and saved. The two records in each pair retain identical baseline assignments.

| Compare in step 07 | What changes | Proven optimal maximum worker index |
|---|---|---:|
| Demo 15 → Demo 16 | V01 becomes excluded from the High Job, AJ03 | 21.25 → 21.875 |
| Demo 17 → Demo 18 | V01 becomes fixed to sorting, AJ01 | 21.25 → 28.75 |
| Demo 19 → Demo 20 | Eight equal 60-minute blocks become seven 30-minute blocks and one 270-minute block | 21.25 → 30.9375 |

## 1. Excluded Job: Demo 15 and 16

Open Demo 15 and select 07 Optimization. V01 receives the red 55% Job in blocks 4 and 7
in the kept result. Select Demo 16, return to 07 and inspect the same worker: there is
no AJ03 assignment anywhere in that row. Step 03 → Worker restrictions shows only
V01's excluded Job; the other workers remain unrestricted.

This contrast holds for **every** unrestricted optimum, independently of tied ordering.
All four unrestricted worker indices are 21.25, which V01 cannot achieve using only
0/5/25% Jobs in eight equal blocks. The excluded result's best maximum is 21.875;
V01 itself scores 20 in the stored result. Other workers absorb the High assignments.
Their exact tied ordering may change if the problem is solved again; V01's exclusion
must hold in every accepted result.

## 2. Fixed Job: Demo 17 and 18

Demo 17 is the unrestricted reference. V01 rotates between Jobs and receives High work.
In Demo 18, every V01 cell is AJ01 Visual sorting 0%. The remaining three workers still
rotate through the other Jobs. Step 03 shows V01 fixed to AJ01. This is not a manual
baseline assignment: the hard rule holds in every productive block of the result.

The baseline is identical between 17/18 and still has V01 rotating. The restricted
maximum 28.75 is higher than the unrestricted 21.25 because that original arrangement
is not feasible under the new fixed-Job rule. Keeping the result never rewrites the
baseline. Step 08 compares each result with its own baseline, not with the other record.

## 3. Different block durations: Demo 19 and 20

Demo 19 uses eight 60-minute blocks. Demo 20 uses **30 / 30 / 30 / 30 / 30 / 30 / 30 / 270
minutes**. The workers, Job values, rules and baseline assignment matrix are identical;
only block lengths change. No worker restriction is active in either timing example.

In Demo 20, locate the worker with the red 55% Job in the last, 270-minute block. In the
stored result this is V02; every other cell in that row is AJ01 at 0%. Other workers do
the High Job during the short blocks and lower-risk Jobs during the long block. A
future tied optimum may give the long High Job to another worker, but the compensation
pattern is necessary at the proven optimum.

**Every Job remains staffed in every block.** The model cannot move the High Job's
entire workload into short blocks or leave it unstaffed in the long block. It balances
who receives those assignments. The long High worker's seven zero-risk short blocks
are the visible consequence of time weighting.

The same baseline has maximum 21.25 with equal timing but 38.125 with unequal timing.
Optimizing the unequal instance lowers that 38.125 to 30.9375. Therefore compare before/
after within Demo 20 to see the improvement; comparing the optimal values of 19 and 20
shows the cost of changing the block structure. Existing two-decimal display formatting
shows the optimized maximum as 30.94; saved values retain their full precision.

## Independent bounds and verification

Each block's Job coefficients sum to 85, so the population mean is always 85/4=21.25.
Unrestricted real CBC solutions attain that bound. With eight equal blocks, a worker's
coefficient sum must be 170 to average 21.25. A worker without High can reach at most 160
below 170 using eight 0/5/25 values. If every worker were bounded by 170, the total could
be at most 160+3×170=670, below the required 680. Sums are multiples of 5, so the excluded
optimum is at least 175/8=21.875. The real solution attains it.

With V01 fixed to 0, the other three rows must carry all 680 points. Their sums remain
multiples of 5, forcing a maximum of at least ceil(680/15)×5=230, or 28.75 per worker.
The fixed result attains it. No unrestricted optimum can fix V01 to any one Job,
because none of the four Job values equals 21.25.

For unequal timing, someone must perform the 55% Job for 270 minutes, forcing a maximum
of at least 55×270/480=30.9375. The real optimizer attains that lower bound. As all other
Job values are positive except sorting, that worker must receive sorting in every
other block. Direct arithmetic from the stored matrix independently checks the scores,
all hard rules and complete staffing. Permanent real-CBC regressions are in
`tests/test_rotation_rule_timing_demonstrations.py`; no altered objective or solver is
used to force the demonstration.

Existing Jobs, workers, assessments, earlier rotations and remembered selection remain
unchanged. One new Job and six kept rotations were added after private-copy validation.

## All-tool data and secondary balancing — 2026-11-03

Owner-approved extension: Demo 15–20 now select all three tools and retain their
verified result. Every one-, two- and three-tool subset is supported. The four Jobs
in AJ01/AJ02/AJ04/AJ03 order use synthetic direct probabilities:

| Tool | AJ01 | AJ02 | AJ04 | AJ03 |
|---|---:|---:|---:|---:|
| LiFFT | 0 | 5 | 25 | 55 |
| DUET | 5 | 10 | 30 | 60 |
| ST | 10 | 14 | 30 | 54 |

The positive affine relationships preserve ordering and isolate restrictions/timing
across all seven subsets. They are controlled optimizer coefficients, not real worker
measurements or biomechanical input examples. Other tests cover conflicting tool
objectives. Existing LiFFT inputs/results and all six baselines are preserved.

Guided single-tool planning now also performs secondary balancing. First it minimizes
the maximum worker index; then it minimizes the worker range without increasing the
first-pass maximum beyond the established numerical tolerance. Multiple tools retain
their previous two-pass policy. Time limits apply to each pass; bounded feasible results
remain explicitly qualified. Original legacy adapter behavior is unchanged.

Demo 20's LiFFT maximum remains **30.9375** and its minimum becomes **17.5**.
One optimal vector is 17.5, 17.5, 19.0625 and 30.9375; equivalent optima can have
different intermediate values and worker ordering. Previously the same maximum could coexist
with 5.3125, 30.9375, 29.375 and 19.375. Perfect equality is impossible here: a High
Job must be staffed during the 270-minute block, and the minimum possible index for
that worker is 55×270/480 = 30.9375. The other three workers cannot all reach that
index because total exposure is conserved. Minimizing spread is secondary to keeping
that best maximum. Fixed/excluded restrictions can further prevent equalization.

No schema/model-version change: scoring, ownership, hard-rule interpretation and
existing serialized fields remain the same. Old one-pass single-tool results remain
readable and show a rerun suggestion; they are never relabeled as balanced. New run
settings record both objective names and actual pass statuses. Explicit Keep retains
results without replacing the baseline; Main Save persists them.
