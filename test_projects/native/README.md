# Native test projects

These projects use **native format 24** and open directly in ErgoTools. They contain
their own project data and assets; the original source projects are not needed at runtime.
Use the normal Tools → JROT entry for the guided rotation workflow.

| Project | Workers | Worker assessments/results | Jobs | Saved rotations |
|---|---:|---:|---:|---:|
| workflow_4_workers.ergprj | 7 | 12 | 10 | 34 |
| jrot_workflow_optimization_test01.ergprj | 7 | 12 | 10 | 35 |
| jrot_workflow_demo.ergprj | 6 | 0 | 6 | 0 |
| comparative_risk_test.ergprj | 28 | 194 | 12 | 7 |
| integrated_test.ergprj | 28 | 194 | 12 | 5 |

`workflow_4_workers.ergprj` retains the four original workflow workers, twelve
assessments and three operational Jobs, plus three synthetic reference workers and
three 0/50/100% Jobs and three 0/5/55% Jobs for optimizer checks. The filename is
retained for continuity. It includes Packing trial, the earlier Test rotations, ten
kept four-block Demo rotations and four kept six-block adjacency comparisons. There
are 34 saved rotations, 24 with kept results at this checkpoint.
Original owner-entered records and Test 01's saved result are preserved. See
[the original walkthrough](../../docs/jrot_walkthrough.md),
[earlier restriction cases](../../docs/jrot_restriction_examples.md) and
[new four-block cases with expected answers](../../docs/jrot_four_block_examples.md).
The current pre-update backup is in local artifacts/jrot_rule_timing_pairs; preserve
newer owner edits before considering rollback. Automated checks use private copies.

`jrot_workflow_demo.ergprj` provides a larger six-worker/six-Job organization example.
The two comprehensive fixtures include embedded plant images, PLOT geometry and saved
rotation data. Their existing DUET/ST worker results may retain partial status; calculate
again before copying a partial/stale assessment into a Job. Missing results are not zero.

From the project root:

```sh
bash tools/run.sh "test_projects/native/workflow_4_workers.ergprj"
bash tools/run.sh "test_projects/native/jrot_workflow_demo.ergprj"
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
bash tools/run.sh "test_projects/native/integrated_test.ergprj"
```

Use Save As for personal experiments. Maintained fixture updates require a saved/closed
application and preservation checks on private copies. Historical migration evidence
and original files remain separate; see [database documentation](../../docs/database_tables.md).

Demo 11–14 compares unrestricted and restricted optimal ordering; see
[expected answers and explanation](../../docs/jrot_adjacency_examples.md).

Demo 15–20 adds four-worker/eight-block fixed/excluded/timing pairs and AJ04 (25%).
See [the walkthrough and exact bounds](../../docs/jrot_rule_timing_examples.md).

The current JROT workflow test project is
`jrot_workflow_optimization_test01.ergprj`. **Demo 21 · Infeasible combined
restrictions** combines valid fixed Jobs and no-adjacent-High rules into a
cross-block impossibility. It should produce a clear warning and no optimized
matrix; clearing V03's adjacency restriction makes it solvable. See
[the example and checks](../../docs/jrot_infeasible_example.md). Existing records
and kept runs remain intact; the older four-workers file is not updated by this case.

## Shift View developer demo

`shift_view_demo.ergprj` contains 20 fictional workers, 20 positioned Job placements,
all three tools with named task inputs/results for Jobs and workers, and two retained
four-block baseline/optimized rotations. Day shift: 08:00–18:00, four 135-minute work
blocks and three 20-minute breaks. One example adds No adjacent High for all workers.
The owner supplied a dedicated 20-worker plant image and baseline placements,
now aligned horizontally within its eight work cells. The earlier seed used the
comparison image; its worker data was never copied. Enable the session Developer option, then PLOT → Shift
View. See [the playback guide](../../docs/plot_shift_view.md) for controls, weighted
index meaning and how to reoptimize in JROT. The existing native format is unchanged.
