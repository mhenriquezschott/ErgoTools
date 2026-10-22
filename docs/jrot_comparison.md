# Original JROT comparisons and HiGHS integration — F126, 2026-10-09

The F124/F125 JROT form now supports both original comparison workflows and
actual two-stage HiGHS all-tool optimization. Compare/Optimize All Tools are
usable when the scheduled profiles contain the required probabilities. Main
JROT navigation remains disabled until workspace/bootstrap composition is tested.
No dependencies, reference code or operational databases changed.

## Source mapping and preserved UI/workflows

Reviewed active reference: comparerotation_window.py CompareRotationWindow;
compareopallrotation_window.py CompareOpAllRotationWindow; rotation_layout.py
onCompareClicked, handleMultiToolOptimizationDone and onOptimizeAllClicked.
The inactive no-thread/standalone optimized windows were not adopted.

RotationComparisonDialog implements the two source layouts over immutable
current/optimized schemes and a frozen RotationPool, with a shared result renderer.
The single-tool comparison retains the original normal window, 1300x900 default,
960x650 minimum, title/subtitle and two stacked side-by-side comparison sections
for the other tools. The all-tool comparison retains 1400x1000 default, 1000x700
minimum, three tabs and the bottom Apply control with the packaged applyrotation
icon. Both retain root/section margins, panel headings, 50px rows, bold centered
headers, left/vertically centered worker text, damage palettes, averages and
source column policy: stretch through five columns; otherwise interactive
100px worker/average and 110px blocks with horizontal scrolling. The inherited
stylesheet controls the final Apply height, just as in the source.

CBC preview -> Compare shows that optimized schedule under the other tools,
without solving again or changing current assignments. HiGHS success opens the
original all-tool comparison; it does not populate/apply the main result until
Apply. Tabs inspect each tool's risks for the same schedule. The source Apply
uses the parent JROT tool, not the selected comparison tab: that behavior is
preserved. Apply fills the embedded optimized table and current rotation, closes
the comparison, and retains ALL_TOOLS provenance with no primary tool. Explicit
Save then persists it; preview/comparison/application perform no writes.

The source comparison tables were editable; migrated comparison cells are
read-only, so displayed results cannot diverge from the validated schedule.
Exact worker/assignment/profile/placement keys drive rendering/transfer rather
than parsing cell text. Missing displayed probabilities prevent a comparison or
all-tool solve rather than being silently shown as zero. Recorded unit strings
remain profile evidence and are not converted. The existing result renderer's
missing-unit caption policy is unchanged; no stored evidence is inferred.
EN/ES titles, subtitles, tab/column captions and Apply text are localized.
When comparing an applied all-tool result, the subtitle identifies all-tool
provenance rather than falsely claiming selected-tool optimization.

## Owned worker and comparison lifetime

The existing injected RotationOptimizer and one owned worker now route selected
runs to CBC/one stage and all-tool runs to HiGHS/two stages, validating backend,
stage status and every schedule constraint before GUI publication. The unchanged
F120 optimizer retains its objectives, occurrence/per-block constraints, 1% gap,
ceiling tolerance and per-stage time limit. Overlay elapsed budget is twice the
chosen limit for all-tool work. Cancel and Escape/window close retain ownership
until actual completion and suppress publication, as in F125; no forced thread
termination, solver fallback, GLPK or repository/widget access from the worker.

Comparison windows retain the source nonmodal interaction. The controller owns
and closes/replaces them when grid edits, applied scope/New/load, displayed tool,
transfer, another solve or parent closure makes their inputs obsolete. This is
specific to real interactions allowed by these source child windows; it adds no
multi-user/project-switch machinery. Repeated Compare replaces its prior child.
The all-tool Apply button emits intent to its owning controller; it never searches
parent widgets or concrete repositories. Manual editing resets applied provenance;
a tool-only repaint preserves it. Merely inspecting/closing a comparison does not
apply or save the result.

## Validation and next step

992 native tests pass, ten new focused cases; 96.71% combined coverage.
Ruff/format (469 files), strict mypy (215 source files), architecture,
wheel and sdist pass. Actual CBC comparison and HiGHS tabs/Apply/Save/reopen are
verified in EN/ES. Controlled all-tool workers check Cancel/close, error and wrong
backend; missing other-tool evidence blocks the action. Modeless comparison
ownership is checked through actual edit/scope/parent-close interactions.
The known sample yields 40% LiFFT, 40% DUET and 50% ST averages after optimization.
All data is synthetic; exact newer approved profile IDs and mixed unit evidence
survive reopen. Project bytes remain unchanged until explicit Save.

32 final native captures inspected: four source single/all minimum/enlarged
comparisons plus 28 EN/ES single-tool minimum/enlarged/selected, all three tabs
minimum/enlarged/selected, wide six-block grids, applied JROT form and all-tool
busy/cancelling states. English visible table rectangles, row/column dimensions,
text, tab and Apply rectangles match source-generated original controls at both
sizes. Whole-window pixel parity is not claimed: translations, selected/focused
cells and read-only behavior differ. Both panels, headings and bottom controls
remain visible; wide grids intentionally scroll like the original. No avatar/VTK
exists in the original comparison forms. A worker vertical-alignment mismatch
found during visual review was corrected and regression checked.

Independent extracted-wheel native actual CBC/other-tool comparison and
HiGHS/all tabs/Apply/explicit Save/reopen pass in EN/ES. All 500 reference hashes
and the approved lock are unchanged. Evidence: f126_validation.json,
artifacts/f126-check.log, artifacts/f126-focused.log, artifacts/f126-wheel.log
and artifacts/jrot-comparison; scripts archived as reference/f126-*.py.txt.

Next: wire the tested JROT form to the existing workspace-owned repository and
bootstrap solver composition, then enable/test actual main navigation. Continue
legacy-format compatibility, comprehensive copied-project integration and final
integrated UI/workflow/platform acceptance. Overall completion percentage and
finish date remain unvalidated; these component gates do not establish full parity.
