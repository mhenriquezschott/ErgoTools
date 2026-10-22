# Worker edit Undo availability — 2026-10-18

Owner-reported correction to the unified Save workflow. After opening a saved project
with empty session history, editing Diego's weight from 65 to 85 left Undo disabled.
Close accepted the edit; reopening then exposed it to Undo. This was an availability
bug: history preparation could accept the pending form, but the disabled action could
not reach that preparation. Earlier coverage replayed accepted edits and missed the
still-open form interaction. The failing reproduction is retained in
`artifacts/worker_pending_undo_review/reproduction.log`.

The worker window now reports a valid pending existing-worker edit to its shared
history controls. Undo enables immediately and its mouse action accepts and reverses
that one edit while the window stays open. Redo restores it. Pending edits temporarily
disable project Redo without consuming its existing branch; returning to the loaded
values re-enables it. Invalid intermediate input stays unaccepted. Native text typing
Undo/Redo remains local. New workers still use Add worker/navigation/Close acceptance;
this correction does not turn partial new records into history entries.

The title buttons take mouse focus so replay uses the project action rather than the
previously focused text editor's typing stack. The existing shared project cursor,
validation, canonical unit conversion and removal-consent policy remain authoritative.
Value edits require no record-removal question. Close retains accepted changes in the
session; only main Save writes the project file. No schema, calculation, dependency,
backup, fixture or reference change is included. No additional milestone is created;
Linux migration/cleanup stay 100%, native Windows/macOS acceptance remains deferred.

## Evidence

Required native `bash tools/check.sh`: **1,406 passed, zero failures/skips, 94.29%
combined coverage**; standards/types (265), architecture/naming, documentation/review
and builds pass. Forty focused native tests and forty independent-wheel tests pass.
All 243 packaged Python files and both HTML guides match source. The inventory has
428 reviewed files/2,929 functions, with zero pending reviews or structural gaps.

Focused native checks cover the exact fresh reopen and real mouse/keyboard sequence
in English/Spanish and metric/imperial, native typing replay, invalid input, preserved
Redo and private-versus-durable content. Twelve native full-window captures were
inspected across pending/Undo/Redo states in all four language/unit combinations;
title controls, optional details and bottom controls fit. Unchanged UI retains the
prior unified-save visual evidence. Three changed maintained files received renewed
substantive documentation review and source-hash certification.

Actual final gate/package results are recorded in
`artifacts/worker_pending_undo_validation.json`; raw logs, captures, exact runtime
diff, review notes and protection hashes are in `artifacts/worker_pending_undo_review`.
The owner workflow project was not opened by these tests or modified. Both maintained
native fixture hashes and the approved lock remain unchanged. Prior reference-audit
exceptions remain historical; no reference writes were made. Root dist packages are
rebuilt; the frozen dist/linux delivery is not republished.

Restart the application to load the correction, reopen the workflow project, and
repeat the weight edit without closing Worker Management. Owner desktop acceptance
remains pending; resume the existing workflow test only after this check.
