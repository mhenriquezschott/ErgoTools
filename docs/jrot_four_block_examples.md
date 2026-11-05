# Four-block restriction walkthrough examples

The maintained workflow_4_workers.ergprj includes Demo 01–10, in addition to the
original Test rotations and Packing trial. All new demos have three workers, three
Jobs and four blocks. They use LiFFT only to make constraints easy to see. No
neighboring-shift links are used. These synthetic 0/50/100% values are solver test
coefficients, not physical task recommendations.

V01 Elena Muñoz, V02 Mateo Rojas and V03 Sofía Torres start respectively on the
100%, 50% and 0% Job for all four baseline blocks. Every baseline deliberately
violates the new restriction being demonstrated. VJ01 is Visual inspection (0%),
VJ02 Carton labeling (50%, not High), VJ03 Heavy transfer (100%, High).

| Demo | Restriction | Block minutes | Expected optimized maximum worker index |
|---|---|---|---:|
| 01 | No consecutive High, all workers | 120 / 120 / 120 / 120 | 50.00 |
| 02 | Same | 30 / 60 / 90 / 300 | 62.50 |
| 03 | V01 fixed to inspection | Equal | 75.00 |
| 04 | Same | Very unequal | 81.25 |
| 05 | V01 excluded from transfer | Equal | 50.00 |
| 06 | Same | Very unequal | 62.50 |
| 07 | V01 fixed; V02/V03 no consecutive High | Equal | 75.00 |
| 08 | Same combined rules | Very unequal | 87.50 |
| 09 | V01 excluded; all no consecutive High | Equal | 50.00 |
| 10 | Same combined rules | Very unequal | 75.00 |

Choose Demo 01 first. Its kept result opens 08. Review 03 for rules, 04 for the bad
baseline, then 07 for the corrected arrangement. No worker has consecutive High
Jobs; each Job has exactly one worker per block. All worker indices become 50.
Demo 02 shows why the 300-minute final block limits balancing. Demo 03 keeps V01
on inspection throughout; Demo 05 never gives V01 transfer. Demos 07–10 combine
rules. Compare 04/08 and 06/10: adding a constraint can raise the best achievable
maximum. The population mean remains 50 because staffing and Job risks are fixed;
rotation redistributes exposure rather than reducing intrinsic Job risk.

Results are already kept and saved so inspection does not require another solve.
To experiment, edit 04 or the restrictions, run optimization in 07, inspect the
preview, explicitly Keep optimization result, then Main Save. The original baseline
changes only through its own editing/replacement actions. Generate initial proposal
belongs only to 04 and produces feasibility, not an optimized solution.

## Verification and recovery

Each of the ten cases uses real CBC plus an independent exhaustive 6^4 enumeration
of block staffing permutations. Literal rule checks and exact Fraction arithmetic
certify the optimal maximum, staffing and constraints without using MILP expressions
or production scoring as an oracle. Alternative tied schedules are valid. Permanent
regressions are in tests/test_rotation_four_block_restrictions.py. Existing multi-tool
HiGHS, infeasibility, thresholds and boundary tests remain in the suite.

Private preparation preserved every original rotation/result, last selection, schema,
and all 17 other database tables exactly. Only rotation_schemes gains the ten demos.
The exact pre-change file is retained locally at
artifacts/jrot_results_examples/workflow_before.ergprj. Before restoration, close the
application and preserve any newer owner edits; that backup predates them. Other
maintained projects remain untouched. Disposable private preparation/capture scripts
and copies can be removed after owner acceptance; the maintained demo records and
permanent tests remain.

For a controlled comparison where unrestricted optimal ordering contains adjacent
High Jobs, use the [six-block paired examples](jrot_adjacency_examples.md). The unequal
pair proves every unrestricted optimum violates adjacency and quantifies the trade-off.
