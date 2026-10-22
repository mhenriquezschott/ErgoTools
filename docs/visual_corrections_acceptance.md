> Historical acceptance: its assessment-version menu descriptions are superseded by
> [owner-directed version removal](single_assessment_ownership.md). Those actions no longer exist.

# Owner-requested popup/PLOT visual corrections — 2026-10-12

## Scope and implementation

Fix only the reported main Worker dropdown contrast and PLOT Apply Filters styling.
No milestone/points/dependency/formula or risk-palette change. Reference source is
read-only throughout. Borrowed native fixtures are copied to /tmp for visual review.

The current reference main.py uses ErgoComboItemDelegate plus explicit popup palette
roles and view-specific selected/hover styles. The new worker selector had only the
ancestor stylesheet, allowing the native combo delegate to paint white text over white.
A small documented presentation component, combo_popup.py, ports that reference
palette/painting policy. Its Qt-owned delegate copies paint options and preserves the
original enabled/focus flags; selected/hover rows use white on #087E91, normal rows use
#1B2933 on white. Installation adds no navigation callbacks or storage access.

PLOT already contains the original #applyfilter_button stylesheet (#087E91 background,
white text/border). Its Apply control was missing that widget name and fell back to the
ordinary white button style. Restoring the original object name reconnects the existing
style and makes the existing white filter_apply_light icon visible. Clear remains white.
No layout, filtering behavior, icons, assessment data or saved numbers change.

## Color verification

All 313 original LiFFT/DUET/ST palette entries match exactly. Direct comparison against
the three current read-only reference calculators passes 10,014 damage samples per tool
(30,042 total), including zero, logarithmically distributed finite positive values and
adjacent floating values at damage thresholds. The original categorical gauge bands
remain 25/37.5/50 percent with colors #19B83F/#F5C400/#FF8A19/#FF3B30.
Continuous assessment-result colors and categorical gauge bands are separate existing
policies. Neither is changed by the navigation/button fixes.
Evidence: artifacts/risk_palette_visual_fix.json and risk_palette_verification.txt.

## Assessment-related Project menu actions

- New assessment: choose a worker, then a classified context for the active tool.
  Saved opens existing data; New opens an editable preview, created only on explicit
  first Save. Selecting it does not move/copy the worker's other assessments.
- Assessment context: choose which assignment/workplace assessment to view for the
  current worker/tool. Lists Saved/New and exact Plant/Section/Line/Station/Shift/Job.
- New blank version: create another empty version for the same saved assignment/tool.
  Existing versions remain; the new version is noncurrent until explicitly selected.
- Set current version: choose the version marked current for that assignment/tool.
  This changes which saved version is used as current; it is not Undo/Redo, deletion,
  reassignment or a project file switch.

## Documentation and validation

Semantically reviewed the new popup component and the four changed maintained files:
Qt ownership, paint-option immutability, no event/state mutation, borrowed style naming,
rendered hover/keyboard contrast, actual Apply/Clear button pixels and proper cleanup.
All procedures document purpose, Args/Returns and module architectural responsibility.
Renewed only these five file hashes; unchanged reviews remain untouched.
Focused tests include rendered worker popup and PLOT button regressions, all worker
navigation/filter cases and existing original scientific/color reference cases.
Native English/Spanish captures cover normal, selected, hovered and keyboard popup
states; main workspace/VTK/results/context/footer; PLOT default, hovered Apply and
1800×1200 enlargement. Normal PLOT is 1460×1060. No reference/project writes occur.
Final gate counts and visual inspection are recorded in visual_corrections_validation.json.

Final acceptance: **1295 tests passed, zero failures/skips; 95.97% combined coverage**. Ruff/format, strict mypy (252), architecture, naming, complete documentation structure/review and wheel/source builds pass. Fourteen native captures inspected. Existing Spanish minimum-width tab/text fit limits remain historical; no unrelated redesign added.
