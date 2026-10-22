# Owner-reported PLOT/JROT/context layout corrections

2026-10-17. Owner authorizes these bounded UI corrections after visual testing:
restore larger PLOT gauges, separate standalone navigation from workplace hierarchy,
replace the extra PLOT/JROT Edit menu/history bar with title-row actions, and fix
PLOT demographic disclosure and flattened chart space without image scrollbars.
No migration milestone or extra implementation scope is introduced.

## Resulting behavior

- Main/PLOT still share `RiskGauge`. The compact PLOT profile reserves 144 pixels
  vertically and comparison columns reserve at least 210 horizontally, restoring
  the full 72-pixel arc radius instead of shrinking it for annotation margins.
  Comparison stack/cluster widths expand together, so both endpoint labels and
  captions fit. Risk limits, colors, classification, results and animation are
  unchanged; the previously recorded main animation endpoint issue stays separate.
- Select assessment context has a full-size Standalone assessment footer button,
  outside the hierarchy. It accepts unassigned navigation directly. Use assessment
  context requires a real workplace leaf, including when the tree is empty. The
  host retains pending-input and Save/Discard/Cancel resolution. Association-only
  dialogs have no standalone action. No artificial records or source copies.
- PLOT has a localized title row; JROT reuses its existing title/subtitle row.
  Undo/Redo icon buttons sit at the far right with existing action tooltips,
  shortcuts, focus/native typing behavior, solver interlocks and history engines.
  Neither window constructs the extra menu bar or full-width history toolbar.
  Existing PLOT/JROT Save controls remain unchanged.
- Plant View reserves the actual fixed rail height (556 logical pixels). The
  splitter cannot collapse its children. The root follows live minimum sizes,
  growing when demographics opens or wrapped explanations require extra room.
  No horizontal or vertical plant-image scrollbar is introduced.
- Tools Overview reserves at least 250 pixels for the chart. It propagates wrapped
  explanation/legend height at the current width after redraw and resize, preventing
  a chart/control overlap during risk-mode changes. Job mode still intentionally
  hides the worker chart selector. Existing plots/settings/data are unchanged.

## Evidence and limits

Final Linux XCB gate: **1,379 passed, zero failures/skips, 95.4% coverage**.
Strict types (262), standards/architecture/naming, both documentation gates (423
files), and wheel/source builds pass. All ten changed production modules and both
HTML guides match the rebuilt wheel. Independent extracted-wheel EN/ES PLOT,
JROT and context composition/geometry checks also pass.

[Final gate and package results](../artifacts/plot_layout_followup_validation.json),
[required check log](../artifacts/plot_layout_followup_final_check.log),
[substantive source reviews](../artifacts/plot_layout_followup_documentation_review.json).
Sixteen changed code/test files were reviewed against actual contracts; both
mandatory documentation gates remain enforced. Existing maintained tests were
updated in place for the approved UI contract; no duplicate test projects.

[Native visual record](../artifacts/plot_layout_followup_review/validation.json)
contains **42 inspected captures**: PLOT EN/ES, Individual/Job/Comparison,
demographics on/off, requested minimum/enlarged sizes and gauge details; JROT saved
minimum/enlarged and blank draft; context with empty/populated/selected hierarchy
and association-only pickers. All captures were inspected in contact sheets, with
full-size checks of chart/toolbar, enlarged gauge labels, context footer and JROT
bottom controls. Earlier intermediate screenshots/debug logs are superseded by
these final manifests. Visual checks use the actual production composition and
disposable native project copies; geometry checks also assert full rail containment,
visible chart/control separation and no plant-image scrollbars.

At the requested small size Qt grows the content window as required: measured
PLOT windows range from 1411×1098 through 1411×1185 across language/risk/disclosure
states. Enlarged captures use 1800×1250 or 1800×1266 as required by content. The
available native screen was 2560×1409. These results do not certify smaller desktop
work areas; the plant image intentionally has no scrollbar fallback. JROT keeps
its existing 1480×740 minimum. Windows/macOS native acceptance remains deferred.

Both maintained native fixture hashes match their own before/after capture values;
the actively used comparative project is not restored to a historical acceptance
hash. Original reference and approved dependency lock receive no writes. Native
schema stays 16 and personal preferences format 5. No dependency, formula,
calculation, database, solver or ownership behavior change was added.

Migration/cleanup stay 100%. Next: owner Linux visual/testing feedback; no additional
implementation milestone is active.
