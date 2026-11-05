# Known-answer JROT checks

Use `test_projects/native/workflow_4_workers.ergprj`. Existing workers, assessments,
organization, Jobs and Packing trial are preserved. The added validation data lives in
**Validation Plant → Packing studies → Known-answer line**. Workers V01 Elena Muñoz,
V02 Mateo Rojas and V03 Sofía Torres include sex and birth dates. VJ01 Visual inspection,
VJ02 Carton labeling and VJ03 Heavy transfer have intentionally synthetic direct reference
coefficients **0%, 50%, 100%**, respectively, in each tool. They are mathematical optimizer
fixtures, not task-derived measurements. Do not recalculate their direct damage fields;
changing those fields derives a different probability through the normal calculator.

Select a **Test …** rotation. Its setup, participants, baseline and restrictions are ready.
Leave the station-specific placement option off: these cases use one global position per
Job. Test 11 selects all three tools; other cases start with LiFFT. Open 03 to inspect or
change restrictions, 04 for baseline assignments, 06 for weighted baseline indices, then
07 to run. Keep optimization result explicitly retains the result without replacing the
baseline. Main Save stores it. Comparing before/after should retain the initial unequal
worker distribution. Equivalent Job/worker permutations are valid; compare the indices
and restrictions rather than expecting one particular arbitrary tie-breaking order.

| Rotation | Check | Expected maximum worker index |
|---|---|---:|
| Test 01 | Three workers, three Jobs, three equal 160-minute blocks | 50.00 |
| Test 02 | V01 fixed to inspection for every block | 83.33; V01 remains 0 |
| Test 03 | V01 excluded from heavy transfer | 66.67; V01 never receives VJ03 |
| Test 04 | No consecutive High for all three workers | 50.00; no adjacent VJ03 |
| Test 05 | Two workers, 0/100 Jobs; blocks 120 and 360 minutes | 75.00; worker indices 25 and 75 |
| Test 06 | Three workers/Jobs; blocks 60, 120 and 300 minutes | 62.50 |
| Test 07 | V01 fixed to High and forbidden consecutive High | Infeasible; keep no fabricated result |
| Test 08 | V01 ended the previous shift High | 50.00; V01 starts the current shift Low |
| Test 09 | V01 starts the next shift High | 50.00; V01 ends the current shift Low |
| Test 10 | Both neighboring shifts have V01 High at the boundary | 100.00; V01 must stay Low in both current blocks |
| Test 11 | Three equal blocks, all three tools with identical coefficients | 50.00 in every tool; one shared solved schedule |

Test 10 restricts only V01, so V02 can perform the two High blocks. This deliberately
shows how a hard restriction can worsen the best attainable maximum. Test 07 cannot
be fixed by a longer solve: its rules contradict each other across consecutive blocks.
The solver should explain infeasibility without overwriting any previously retained run.

**Test 90 · Boundary reference before/after** are genuine retained one-block reference
runs, used only by Tests 08–10. Their times are 07:00–08:00 and 12:00–13:00; current
boundary examples cover 08:00–12:00 with two equal blocks. They fix V01 to the High Job.
Do not replace these reference runs while checking the supplied boundary examples.
Ordinary within-shift restrictions need no previous/next link. If a reference's numerical
context changes, the dependent case must reject the stale boundary until reselected.

Before/after values use the same frozen coefficients and durations. The population mean
stays constant under full staffing; optimization redistributes exposure. Weighted indices
are schedule comparisons, not new individual injury probabilities. Current High thresholds
remain unchanged. The High Risk Notice identifies intrinsically High Jobs; rotation does
not change those Jobs' own coefficients.

Private preparation validates feasible cases with real CBC/HiGHS and exact exhaustive
assignment enumeration for the small internal cases, plus obvious independent boundary
endpoint checks. Existing permanent optimizer tests separately cover zero/all-High/equal
risks, odd/unequal blocks, staffing, all tool subsets, hard rules, thresholds and invalid or
missing neighboring context. User UI acceptance is still required.

The original file backup and exact preservation checks are recorded locally under
`artifacts/jrot_polish`. Restore only while ErgoTools is closed; do not overwrite newer
owner edits. No schema migration, calculator formula or solver implementation changes
are required by these examples.
