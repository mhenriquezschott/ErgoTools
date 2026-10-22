# CR006 disposition — approved and implemented

Owner answered yes on 2026-10-11. Exact saved/imported results now transfer
atomically; focused/full/packaged/native checks pass. The observed damage numbers
are different precisions of the same calculation: 0.98249 rounds to 0.9825.
No formula correction was needed. See m10_acceptance.md. Proposal below is the
historical pre-approval record; its pending wording is superseded here.

---

# CR006 — preserve saved results during assessment transfer

M10's copied-project scenario found a confirmed original-workflow mismatch.
Approval is requested before a bounded correction. Product and test source remain
unchanged. M10 earns no points yet: **94.50/100, 9/12 complete**.

## Observed behavior

The original `worker_transfer_window.py` copies both summary records and per-tool
result rows, replacing ownership columns only. The migrated adapter copies saved
task inputs and history but omits their results. Destination display/export then
calculates a replacement instead of retaining the saved observation.

Actual single-button probes on disposable projects confirm this independently
for freshly saved and imported assessments, with one transfer invocation each:

| Source | Tool | Saved damage | Destination damage | Other loss |
|---|---|---:|---:|---|
| Fresh Calculate/Save | DUET | 0.9825 | 0.98249 | Recorded 63.8% absent; Imperial label becomes Metric |
| Imported original | DUET | 0.0174 | 0.01743 | Recorded 32.3% absent; recorded status becomes partial |
| Imported original | ST | 0.0281 | 0.02813 | Recorded 36.0% absent; recorded status becomes partial |

Task inputs are identical. This is result/provenance loss, not an input-conversion
error. Evidence: `artifacts/m10-transfer-probe.json` and probe wheel log.

## Proposed bounded correction

1. In `infrastructure/assessment_project_file.py`, capture each source-bound saved
   result (or its archived recorded result) before any Move deletion. Persist the
   result with destination inputs/history in the existing atomic transaction.
   Preserve exact totals, probability, task outputs, units and recorded/fresh
   status. If there is no stored result, preserve that absence.
2. In `infrastructure/saved_result_store.py`, retain existing fresh-result version
   1 decoding/validation and support an explicitly versioned recorded-copy payload
   for archived results. Recorded results can lack a fresh-calculation status or
   unit label. Preserve those original values rather than inventing them. Keep
   source binding, finite numeric validation and strict envelope validation.
   Reuse the existing result table; no dependency, calculation, UI or original
   archive changes. Existing projects stay readable; older intermediate builds
   are not promised forward compatibility with the new recorded-copy envelope.
3. Add focused regressions for Copy/Move of all three tools, fresh and archived
   results, absent-result behavior, reopen/export equality and rollback on a
   result-write failure. Then run the required code-slice gate, rebuild once and
   finish the fixed M10 scenario on a fresh disposable comprehensive copy.

This is one bounded correction pass within M10, with **zero added milestones or
points**. No renderer, solver, localization or broader storage redesign. If another
repair is discovered, report it separately before implementing it. M11 remains
unstarted. The owner may approve this repair or explicitly accept the mismatch;
no acceptance exception is assumed.

Approval is required by AGENTS.md's owner scope rule: “No new defect repair may
be disguised as extending an existing milestone.”
