# Current JROT meeting project — 2026-10-21

`jrot_workflow_demo.ergprj` (under `native/` from the parent directory) is the owner's
explicitly requested clean format-19 example: six named/demographic workers, six Jobs,
18 calculated source/result sets with 36 task rows, two plants, four sections, eight
lines, 24 stations and two shifts. No worker assessments or saved rotations are seeded.
Use it with Developer Menu → JROT workflow prototype…. See docs/jrot_meeting_demo.md
for the walkthrough, shared placement meanings, fixture provenance and cleanup notes.
It is one new demonstration project; existing fixtures are unchanged. Descriptions of
older formats/profile storage below are historical, not the current schema contract.

---

# Current self-contained test projects

All three established files use native format 19 and open directly without migration.

| Project | Worker assessments/results | Jobs | JROT schemes |
|---|---:|---:|---:|
| workflow_4_workers.ergprj | 12 | 0 | 0 |
| comparative_risk_test.ergprj | 194 | 12 | 7 |
| integrated_test.ergprj | 194 | 12 | 5 |

The comprehensive fixtures retain four embedded plant images and PLOT geometry.
The four-worker workflow remains at its owner-approved testing bookmark; no later
interactive workflow step has been performed by maintenance.

Native19 removes Job profile/evidence/lifecycle storage and retains each Job's selected
current values. Existing migrated values are direct entries without invented task data.
New calculator/copy inputs and all matching task outputs persist independently per
Job/tool. Worker source/result payloads, organization, images and schedule arrangements
were compared exactly before updating these same files in place.

All three tools have usable worker calculations in workflow_4_workers. In the two
comprehensive fixtures, LiFFT worker calculations are complete while existing DUET/ST
worker results are marked partial. Those records stay untouched; Calculate is required
before using a partial/stale worker result for a Job copy. Existing complete direct Job
values remain available to PLOT/JROT.

From the project root:

```sh
bash tools/run.sh "test_projects/native/workflow_4_workers.ergprj"
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
bash tools/run.sh "test_projects/native/integrated_test.ergprj"
```

These are the maintained fixtures; future format updates replace them in place.
Use Save As for personal experiments. Original inputs remain separately in ../originals;
the native application does not need them. See ../../docs/job_management_simplification_decisions.md
and the final acceptance/evidence for the current Job change.
