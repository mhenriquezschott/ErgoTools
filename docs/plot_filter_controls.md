# F103 — original PLOT workplace and tool controls

The original workplace/path blocks and ergonomic-tool buttons are now reviewed
components composed with F102's map in a temporary harness. Production PLOT is
still disabled. No result filtering or worker/job marker dataset is implied by
this UI selection slice.

## Source and behavior

PlotWorkplaceControls follows plant_layout.py configureResponsiveLayout, lines
1696–1780: 88-pixel group, original margins/spacing, plant icon, five path blocks,
processed next-arrow asset scaled to 14 by 24, entity icons, 118-pixel minimum
plant block and 132 by 52 Choose Workplace button. PlotToolControls follows the
original three exclusive icon/text buttons around lines 1800–1833, including the
28-pixel icons, group height and shared stylesheet. No controls were reconstructed
from screenshots or unrelated assets.

Choose Workplace uses the actual migrated modal picker and its initial immutable
selection. Cancel publishes nothing. An accepted choice validates against the
saved hierarchy and asks the map to accept it; only success updates path labels.
Declined pending-image discard or failed map load keeps labels and map consistent.
Repeating the same scope does not reload or prompt. The unselected component
shows a dash plant and All shifts instead of inventing the reference template's
shift 1. The eventual parent must explicitly restore the reference default scope
from available saved identities; this component does not infer one.

All/single/count path summaries match the source policy; full included paths are
available in tooltips. Actual shift names All/Todos remain stored identities and
are never translated into all-shifts semantics. Plain-text value labels elide long
names to fit the original block, with full accessibility text and escaped native
rich-text tooltips. This avoids expanding the whole window or interpreting names
containing <b> or & as formatting. Spanish count text may elide at the default
width; its complete value remains in the tooltip and fits at enlarged widths.

LiFFT/DUET/Shoulder buttons use AssessmentKind identities instead of string aliases.
Each new tool selection invokes one typed callback; repeated clicks do not repeat
notifications. It does not accept assessments, discard/reload map previews or
perform queries. The future Apply workflow owns filtered results and the applied
result-tool title independently of the selected tool.

## Validation and remaining composition

Eight focused cases cover actual modal acceptance/cancellation/prefill, failed
map acceptance, literal shifts, multi-station summaries, empty hierarchy, long
names/resize and exclusive typed tool notifications. Three composed main-tool
fixtures preserve pending invalid assessment input, state/settings and unsaved
map data during scope refusal/tool changes.

811 native tests pass, 96.48% combined statement/branch coverage. Ruff/format,
strict mypy over 167 source files, architecture and wheel/sdist pass. Native xcb
source-extracted workplace/tool regions were compared with English/Spanish empty,
expanded selected picker, composed selected/default/enlarged map states and long
literal values. Caption widths and full-image bounds were checked at 1460 by 820
and 1920 by 1080. The native tooltip widget was rendered for literal-text review;
its automatic hover timing was not a new acceptance claim. These composition
screenshots omit remaining original regions and are not final full-window parity.

Isolated-wheel checks cover actual Spanish picker/map/label agreement, literal
shift, Open/Save, duplicate tool intent and discard-No retention. All 500 reference
hashes and the approved lock remain unchanged. No new dependencies, assets,
project format, scientific calculation or VTK code changed. Evidence:
f103_validation.json, artifacts/f103-check.log and artifacts/plot-filters. Capture,
source-tool/tooltip and verification scripts are archived under reference/f103-*.txt.

Next: original risk-view and demographic filters with Apply/Clear, then connect
scoped worker/job results to markers and summaries while composing the complete
original PLOT window. Parent close consent and remaining map actions still need
integration. Units/localization, legacy sidecars, final copied comprehensive project
and platform acceptance remain required. JROT follows PLOT with CBC single-tool,
HiGHS multi-tool and GLPK excluded. Overall percentage and finish date remain
unvalidated; test coverage is not whole-application completion.
