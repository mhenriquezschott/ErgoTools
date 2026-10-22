# PLOT worker visual settings — F109

This checkpoint migrates the original Worker Overview's Visual controls region,
not the complete Worker Overview. Reviewed `plant_layout.py` subgroup construction,
`visibleCheckChanged`, `enableCheckChanged`, `lockCheckChanged`, `saveVisualWorker`
and `saveAllVisualWorkers` define the layout/workflow. The surrounding worker
selector/alphabet/search/navigation, details, result/preview/Locate region and
Load Into Tool handoff remain the next composition work.

## Working controls

`PlotWorkerControls` retains the source subgroup title, 10/12/10/10 margins,
8-pixel vertical spacing, flag row, X:/Y:/Scale: grid, 44–72-pixel fields,
Save/Scale/Save All row, 54-pixel bulk scale field, icons and tooltips. It receives
assignment identity from the marker layer or future worker selector. Hidden and
unplaced workers can be selected through its owned API without fabricating a
stored position. Flag changes preview visibility, inclusion and lock locally;
Save accepts original-image coordinates and positive dimensionless scale.

Read/select creates no stored geometry. The layer retains immutable draft flags
separately from saved results. Showing a placed hidden worker creates its graphics
item through the existing worker shape/color/tooltip composition. Unplaced workers
remain absent until explicit X/Y placement; a newly saved worker initializes only
an absent station anchor. Positions are independent of metric/imperial body units.
Enable continues to mean inclusion/exclusion from later PLOT summaries; F107's
Qt enabled-item behavior is retained and summaries themselves remain pending.

Partial typed fields stay intact through flag projection and Save failure. Save
validates finite X/Y and positive finite scale before any write. Accepted writes
update saved geometry and graphics state without discarding other workers' draft
intent. Original success information dialogs are retained through an injectable
callback; errors use the existing localized error/diagnostic boundary. English
and Spanish captions are supported. Negative coordinates remain allowed.

## Save All improvements and explicit differences

The current selected-tool result assignments define the batch, including hidden
workers. Save All applies its bulk scale and preserves their current points/flags.
The selected worker's typed coordinate draft is validated/accepted rather than
silently ignored by bulk Save. All values are validated before one project-owned
transaction. The legacy loop performed individual writes and processed Qt events
between workers; the migrated path has neither partial commits nor event pumping
inside persistence. Failure retains saved data and every draft for retry.

An unplaced worker without actual/inherited coordinates causes the batch to be
rejected with a localized message. It must be positioned explicitly before Save
All; no arbitrary origin is manufactured. This is a deliberate guard, consistent
with F106's absence semantics, rather than a claim that final bulk unplaced-worker
UX has already been accepted. Selector/full-window composition must expose this
condition clearly. Source single-Save integer projection is improved to retain
saved fractional X/Y values; finite validation also rejects NaN/infinity and zero
or negative scales. Existing layer Cancel restores saved preview flags when used
by future parent discard consent; no new Cancel button was added to the source
worker controls.

## Evidence and remaining work

Three focused native cases cover both languages, actual typed fields, immediate
flag previews without writes, hidden/unplaced creation, positive/finite validation,
single/batch failure/retry, one writer call for Save All, shared-anchor inheritance,
preview discard and job-mode/empty controls. All 854 baseline tests pass, 96.31%
coverage; Ruff check/format, strict mypy (177 source files), architecture and
wheel/sdist builds pass. The isolated wheel checks the actual controls, saved
reopen and a late SQL trigger failure after the first worker insert: all batch
records roll back, drafts survive, retry succeeds. All 500 reference hashes and
the approved dependency lock remain unchanged.

Twenty-five native captures in `artifacts/plot-worker-controls` cover original
source-code controls, English/Spanish empty/populated/hidden/locked/invalid/failed/
saved/batch/success/enlarged states, plus adjacent map compositions at 1460×800 and
1920×1060. The populated English 390×170 controls fixture matches the source
pixel-for-pixel. Review covered fields/buttons and adjacent map containment.
A marker explicitly placed at a negative coordinate can lie outside the map;
no whole-window/final or cross-platform visual parity is claimed. The map-plus-
controls harness omits the still-pending worker overview regions intentionally.

See `f109_validation.json`, `artifacts/f109-check.log`, `artifacts/f109-wheel.log`,
`artifacts/f109-native.log`; capture and wheel verifier scripts are archived in
`docs/reference/f109-*.py.txt`.

Next: compose original worker selector/navigation/details/result/marker preview
and Locate with these controls, then marker context actions and Load Into Tool,
summaries and complete PLOT window. Production PLOT remains disabled. Parent
close consent, remaining map actions, intentional deletion composition and final
comprehensive-copy acceptance remain. JROT follows PLOT: CBC single-tool, HiGHS
multi-tool, no GLPK. Overall percentage/finish date remain unvalidated; the former
67% is not reused as a reliable whole-application measure.
