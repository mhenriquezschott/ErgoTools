# F148 — comprehensive fresh-calculation integration

The copied comprehensive project now completes fresh Calculate, edit, undo/redo,
Save, CSV export and reopen across LiFFT, DUET and ST. All 194 sources evaluate
without mutation: 103 complete and 91 partial grids. The native integrated
scenario also saves/cancels/reopens a worker edit, opens PLOT, runs actual CBC and
HiGHS optimization, applies/saves a multi-tool rotation, and verifies backup,
archive retention and unchanged original inputs. G3 gains its usable-integration
gate: fixed-scope progress is 74/100 complete and 26/100 remaining.

This is a workflow integration checkpoint, not final original-application
acceptance. EN/ES packaged checks use independent disposable copies, real VTK,
minimum/enlarged windows, all tool calculations, invalid pending text and toolbar
export that does not commit pending edits. Saved edited sources export fresh
results matching the live typed summaries; unchanged sources retain recorded
provenance. Original direction conventions and source units survive reopen.
All seven stored rotation schemes survive; the targeted solver scenario uses
TEST-All-2x3 rather than repeating captures of every unchanged scheme.

The CSV follow-up fixes a concrete absence case: DUET's original missing/empty
unit label now remains absent instead of inheriting project defaults. A typed
optional archived label is kept separately from model units. The six focused
recorded-export cases cover missing/zero/precision, changed-source invalidation
and explicit/missing/empty DUET units. All required code gates run after this fix.
The ST module documentation now describes the implemented application orchestration.

Visual evidence: artifacts/batch-f145-f148 (13 captures per language, with real
VTK image composites), plus the corrected actual metric-source F145 captures and
F146 ST captures. Contact sheets were inspected. ST, PLOT and JROT populated
states are readable, but some LiFFT/DUET main-window captures show missing or
clipped labels/regions after switching/resizing; the final ES ST pending capture
also has missing regions. R007 now records the broader
observed states; these captures do not pass final visual acceptance. Expanded
assessment popup verification and R006 narrow Spanish JROT scope remain open.
No UI layout or original formulas were changed to conceal these issues.

A concrete remaining workflow difference is recorded as R008: original Save
writes calculated result labels even without source edits; the new source-based
export still selects archived evidence when the persisted source is unchanged.
Fresh saved-result provenance must close under existing B1/C4 final acceptance,
without overwriting the retained original archive. No additional scope is added.

Next batch is explicitly bounded to existing acceptance rows: main-window
rendering/resize issues, saved fresh-result provenance, original LiFFT/DUET parity,
and original ST/context parity. Final platform delivery and documentation remain
in the fixed ledger. No dependency changes or reference writes occurred.

Validation: 1104 tests; 96.45% coverage; required gates and wheel checks pass; 500 reference hashes/lock unchanged. See f148_validation.json.
