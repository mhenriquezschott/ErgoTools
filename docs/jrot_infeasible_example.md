# Combined restrictions with no feasible rotation

Open `test_projects/native/jrot_workflow_optimization_test01.ergprj` and select
**Demo 21 · Infeasible combined restrictions**. It has five workers, five existing
Jobs, six equal 80-minute blocks and complete values for all three tools. No
optimization result is stored for this intentionally infeasible example.

| Worker | Restriction |
|---|---|
| V01 · Elena Muñoz | No adjacent High |
| V02 · Mateo Rojas | No adjacent High |
| V03 · Sofía Torres | No adjacent High |
| W04 · Diego Soto | Fixed to AJ02 · Label inspection |
| W02 · Bruno Silva | Fixed to AJ04 · Carton inspection |

The remaining Jobs are AJ03 · Container transfer (High), VJ03 · Heavy transfer
(High), and AJ01 · Visual sorting (Low). Those classifications hold for every
nonempty tool subset. Static staffing works, no worker is both fixed and excluded
from the same Job, and every restriction is individually valid.

## Why the combination is impossible

The two fixed workers occupy the two other low/moderate Jobs in every block.
The three moving workers must therefore fill **two High Jobs in each column**.
Across any two adjacent columns, four High assignments are required. With No
adjacent High enabled for all three moving workers, each can take at most one
of those assignments: only three can be covered. Four required exceeds three
available. More solve time cannot repair this combination.

This is a cross-block infeasibility, beyond the simple fixed/excluded consistency
checks in the restriction editor. The illustrative baseline deliberately includes
adjacent High assignments; keeping it for reference does not mean it satisfies the
new optimization restrictions.

## Check the failure and recovery

1. Review the restrictions in step 03 and baseline in step 04.
2. In step 06 choose one tool, any pair, or all three.
3. In step 07 run optimization. Expect an explicit no-feasible-rotation dialog,
   a prominent notice and **no result matrix**. Step 08 must show the same
   unsuccessful outcome with no comparison values or enabled Report/Keep actions.
4. Return to step 03, open Worker restrictions and clear **No adjacent High for
   V03 only**. Keep both fixed Jobs and the other two adjacency restrictions.
5. Run again. A valid result should appear. V01 and V02 can alternate between a
   High Job and sorting; V03 can cover High work in neighboring blocks. No unique
   schedule is promised where equivalent optimal assignments exist.
6. Keep/Save only if desired. Undo can restore the restriction edit; a failed
   solve itself never replaces the baseline or a previously kept result.

The real adapter was checked for all seven tool subsets, both optimization and
feasibility generation: 14 infeasible cases and 14 corresponding feasible relaxed
cases. Timeout/no-incumbent paths are tested deterministically at either pass;
this example is a proof-of-infeasibility case, not a machine-dependent timeout demo.

## Data preservation and verification

Only the new rotation row is added to the owner-closed test project. Existing
workers, Jobs, sources, results, organization, images, prior rotations and remembered
selection are preserved exactly. Schema, calculator formulas and solver model are
unchanged. The project now has 35 rotations, including the previous 24 kept runs.
The older `workflow_4_workers.ergprj` copy is unchanged.

Preparation, SQL-row/schema checks, real solve outcomes and publication hashes are
under `artifacts/jrot_failures_20261115/`. The pre-update file is
`project_before.ergprj`; keep it for owner review, then remove the disposable
before/prepared copies when no longer needed. Restoring the whole backup after
later user edits would discard those edits; normally remove only Demo 21 through
JROT if the example is no longer wanted.

Twenty-seven new regression cases cover native infeasibility, one-/two-/three-tool
constraints, generation, timeout with/without valid incumbents in either pass,
English/Spanish warnings, prior kept results, refresh/navigation, context cleanup and retry. The
native EN/ES failure/recovery captures use private Xvfb/GLX, never the owner's
desktop. Controlled timeout captures are identified as such in their evidence.
