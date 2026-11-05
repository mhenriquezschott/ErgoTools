# Rotation duration weights and solver comparison

## Demo 20: what the saved project contains

The maintained `jrot_workflow_optimization_test01.ergprj` was inspected on a private copy. Demo 20
has **no active worker restrictions**. Its productive blocks are
30 / 30 / 30 / 30 / 30 / 30 / 30 / 270 minutes, totaling 480. The retained result
uses all three tools and both optimization passes. Its LiFFT indices are:

| Worker | Weighted index |
|---|---:|
| V01 | 17.5 |
| V02 | 18.125 |
| V03 | 18.4375 |
| W04 | 30.9375 |

Equivalent optima may swap workers/intermediate values. The earlier 5.3125 minimum
belongs to a previously documented solution before secondary balancing. Results are
never silently replaced: rerun and explicitly Keep a new result when comparing engines.
The [rule and timing examples](jrot_rule_timing_examples.md) describe the paired cases.

## Block duration is a weight, not an exposure cap

Let `x[w,b,j]` be 1 when worker w performs Job j throughout productive block b,
otherwise 0; `d[b]` is its minutes and `r[j]` its selected tool's risk percentage.
The displayed weighted index is:

```
I[w] = sum_b sum_j (x[w,b,j] * d[b] * r[j]) / averaging_minutes
```

The existing `_planning_score` in
`src/ergotools/infrastructure/pulp_rotation_optimizer.py` constructs exactly this
expression:

```python
pulp.lpSum(
    variables[worker, b, key] * (minutes * risks[key])
    for b, minutes in enumerate(problem.inputs.timing.block_minutes)
    for key in problem.target_keys
) / problem.inputs.timing.averaging_minutes
```

For a worker with 60 minutes at 80% and 180 minutes at 0%, the index is
`(60*80 + 180*0)/240 = 20%`. An unweighted average of 40% would be incorrect.
Breaks receive no Job assignment; the chosen break-exclusion policy determines the
averaging denominator. These are comparison indices, not individual injury probabilities.

## Staffing makes the long High assignment unavoidable

For each block and Job, `_planning_model` enforces:

```python
pulp.lpSum(variables[w, b, key] for w in range(len(problem.worker_ids))) == 1
```

Each worker also receives exactly one Job in that block. Therefore **every Job must
be staffed during the 270-minute block**, including AJ03 at LiFFT 55%. Someone's
index is at least `270*55/480 = 30.9375`, even if all their short blocks are 0%.
The current solution attains that lower bound. With all four Jobs staffed, the mean
is conserved: `(0 + 5 + 25 + 55)/4 = 21.25`. The optimizer cannot raise the mean to
make the workers equal while keeping the same Jobs and complete staffing.

The primary objective minimizes the maximum index per tool (sum of these maxima for
multiple tools). The second pass reduces the sum of tool ranges while protecting the
first-pass ceilings. Neither pass prohibits a High Job just because a block is long.
No-adjacent-High, when enabled, prohibits High Jobs in consecutive blocks; it does not
limit the minutes of a single High assignment. Fixed/excluded rules restrict workers'
allowed Jobs, also without imposing a duration cap.

## Possible future changes: not implemented

- A maximum continuous High-exposure duration could forbid certain Job/block pairs.
  But banning AJ03 in the long block for every worker contradicts its mandatory
  staffing equation: the sum cannot simultaneously be 0 and 1.
- Splitting the 270-minute block into smaller productive blocks permits real worker
  changes within that interval while continuously staffing the Job.
- Allowing a Job to be inactive in selected blocks needs explicit availability/workload
  requirements, rather than silently removing staffing or changing exposure averages.
- A worker index cap below 30.9375 would make this exact example infeasible. A different
  objective alone cannot overcome the mandatory long-block contribution.

These examples change input scenarios, not scientific risk formulas or staffing rules.

## Current runtime

All optimization and proposal generation use HiGHS. Previously saved solver
attribution remains read-only provenance. See [HiGHS runtime](highs_only.md).
