# M06 — complete

**89.00/100 overall; 6/12 complete; 15/26 earned, 11 points remaining.**
M06 receives its fixed 2.5 points after both acceptance items pass. M07 next;
not started. Original map/chart/export comparisons below remain valid; the
approved PLOT history gap is now implemented and independently verified.
CR004 removal was withdrawn; no requirement or milestone weight changed.

## M06.1 — original maps, marker workflows and approved history verified

Original code defines image pixel coordinates, fit/alignment and marker controls.
Reuse F142 active loadImageNew characterization: original image scene rectangle,
aspect-preserving fit, Top/Left alignment and hidden scrollbars agree for three
image aspect ratios at two sizes. Current frozen-original loader regressions pass.
Stored dormant Plant transforms remain archived, as the original active loader
does not apply them. No dormant scale/rotation/crop/mirror is activated.

Reuse F106 original station/worker persistence comparisons and F107 shape/paint,
selection, drag/scale and ownership comparisons. Current packaged checks exercise
actual viewport drag/Ctrl scale, read-only selection, preview/Save/Cancel, failure
retention/retry, shared station anchors, zero/fractional points, flags/lock/visibility,
Save All atomicity, absent geometry, map Open/Save and independent reopen. Worker
controls retain their original Save/Save All row; no Cancel button was invented.
The existing layer Cancel restores drafts; Job controls have actual Cancel movement.
Existing F112/F118 context-menu Lock/Save/Load and exact assessment handoff remain
covered by current integration checks. Map rail zoom/opacity/reset/capture retains
F117 source comparisons and current regressions. No new PLOT deletion action.

Current disposable comprehensive-project native scenario selects the real worker
marker, edits/discards through layer Cancel, edits/Save through its original button,
then edits/Cancel/Save a Job anchor through original controls. Saved worker points
remain unchanged by Job moves. Independent reopen verifies complete position
snapshot, exact plant image bytes and source archive; jobs and assessment history
remain unchanged. Original operational project/code are never written.

**Approved history implemented:** application-owned commands now provide marker
move/scale, worker flags/settings, accepted typed edits, batch edits and Cancel
history. Localized Edit actions/shortcuts route to the active PLOT document or
native typing history. One gesture is one source operation; Save is not an edit;
Undo after Save requires an explicit later Save to alter persisted geometry.
Failures retain intent, branching clears Redo, missing/zero anchors and station
order are preserved. See [contracts and retention evidence](plot_history.md).

The final wheel's native comprehensive-copy scenario verifies actual mouse moves,
Control scaling, menu actions, standard shortcuts, typed input, Save/Undo/Redo,
new-branch flags, write failure/retry, dirty-close rejection, job anchor Save and
independent reopen in English and Spanish. Archived assessment evidence, jobs,
assessment ownership and map image remain unchanged. Twelve changed-UI captures
were inspected, including expanded menus, selected/pending/saved and empty states
at 1460×1060, 1800×1200 and the calculated minimum size. Complete menu/filter/map/
tab/outcome/button bounds pass; scrollable details remain accessible. The already
recorded narrow Spanish tab scrolling belongs to M09's broader shared UI matrix.

## M06.2 — charts, settings, highlights and exports verified

Reuse F113 original chart series/arithmetic and source/native chart comparisons,
F114 graph/settings/legend/viewer controls, F115 highlight/detail/gauge comparisons,
F108 Job and F109/F110 Worker source controls. These are unchanged PLOT components,
so no repeated source reconstruction. Current original worker controls, Job panel,
Graph Settings and Tools Overview source captures were inspected individually.
Current Graph Settings default is **pixel-identical at 520×436** to the source
fixture. Existing documented corrections remain: independent viewer figure,
content-based chart margins/wrapping, strict finite input, safe atomic batch writes,
full station identity, missing-value/paired aggregation and explicit export provenance.

Native copied-data workflow verifies modal settings Close retains the chart and
Apply changes axis/text/grid/value settings. Expanded viewer owns its figure;
zoom/home/Close leaves embedded canvas and size intact. Populated/selected and
empty highlight dialogs, empty chart, chart sex groups, worker and Job selections,
and Spanish reopened host were inspected. Complete map/filter/tab/outcome/Apply/
Clear bounds pass at 1460×1060 and 1800×1200. Scrollable worker controls remain
reachable; Spanish tabs use Qt scrolling at narrow width. The broader localization/
resize matrix stays M09. This does not claim untested whole-app/OS acceptance.

Actual PNG/JPEG/SVG/PDF chart exports are produced, with 300-DPI PNG metadata.
Map PNG pixels exactly match the current canvas after normalizing decoded image
formats. The first audit compared differing QImage formats and failed in the
harness; correcting the audit's format comparison passed with no application change.
Both map and chart PNG exports were visually inspected. Current tests additionally
verify Cancel, encoder/write failure, suffixes and atomic CSV publication.

Six CSV exports cover LiFFT/DUET/ST and Metric/Imperial. **370 original normalized
row comparisons** verify owner/workplace/job identities, damage/probability precision,
missing/zero evidence and body-unit projection. F131 recovered sources 101/102/104
are explicitly separate from the original normalized rows (same M05 disposition).
Original retained CSV fields/order plus migrated exact assessment/status/body-unit
provenance remain F118's documented policy. No geometry draft enters saved CSV.

## Required evidence and scope

**Final full gate:** `artifacts/m06-history-check.log` records 1,168 tests,
96.37% combined coverage, lint, formatting, strict mypy, architecture and wheel/
source builds passing under the approved Python 3.13.14 baseline. **83 focused
PLOT tests pass from the final independent wheel**, using native XCB:
`artifacts/m06-history-wheel.log`. This supersedes the earlier unchanged M04 gate
for the changed code. The earlier 77-test original comparison and 370 CSV row
comparisons remain valid prior evidence for unchanged outputs.

**Final native gate:** `artifacts/m06-history-native-wheel.log` and
`artifacts/m06-history-native/verification.json`; 12 final captures inspected.
All 500 reference manifest hashes and the approved lock are unchanged. No Python
or dependency version changed. Original application/projects remain untouched;
all writes used disposable converted copies. Original map/chart/export and source
comparison details above are reused rather than repeated without cause.

The two actual integration failures found and fixed were exact geometry on Save
and station ordering; focused regressions protect both. Subsequent shared-display
focus/overlap harness corrections changed no product code. See m06_review.md for
retained failed-run logs and the final exclusive native acceptance.

Both M06.1 and M06.2 are verified. No remaining M06 item or owner answer. Proceed
only with the owner's next fixed milestone, M07; no extra scope was introduced.
