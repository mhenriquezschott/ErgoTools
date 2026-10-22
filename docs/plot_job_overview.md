# Original PLOT Job Placement overview — F108

The reviewed `plant_layout.py` methods `buildJobOverviewPanel`,
`jobOverviewSelectionChanged`, `setJobPositionPending` and position/Locate actions
are the source for this component. `PlotJobOverview` preserves their original
selector/navigation rows, grids, subgroup styling, 8-pixel root margins,
5-pixel spacing, scroll behavior, processed icons and X/Y/Cancel/Save controls.
It composes with the F107 marker layer in a native harness; production PLOT and
its full details-tab arrangement remain pending.

## Usable workflow

Saved Apply results populate active placements. Dropdown or first/previous/next/
last navigation selects a stable placement ID. Clicking a marker synchronizes the
selector without feeding combo changes back through the same signal. Details show
literal workplace identity, assigned-worker count and optional approved job
profile/tool evidence. Zero risk/damage remains valid; missing evidence stays
unavailable. Literal labels use plain text so saved markup is never interpreted.

X/Y are original-image pixels, independent of metric/imperial body units. Typing
marks pending intent without parsing intermediate keystrokes or moving the marker.
Save validates both fields as finite numbers, moves the selected display marker
with its fanout offset and invokes the existing transactional save operation.
Navigation locks during pending movement. Invalid/failed Save retains both the
fields and pending state for retry; Cancel restores the last saved coordinates.
Dragging an existing marker updates the overview. Accepted job saves refresh shared
station placements while preserving saved worker points. Locate ensures marker
visibility and pulses the original blue frame ten times at 190 ms.

## Code improvements

The overview receives the marker layer and packaged icons rather than reaching
into a global main window or querying SQL. Layer notifications carry selected
owner IDs and changed intent; combo publication blocks signals to prevent a
selection feedback loop. The overview resolves items by identity after save-driven
rebuilds. Locate stops on selection/dataset changes and explicit overview close,
releasing its temporary item reference before queued Qt deletion. No new project
format, dependency, scientific formula or unit policy is introduced.

Source float parsing allowed NaN/infinity; this component rejects them through
`PlotPoint` finite validation and reports a localized message through the injected
error boundary. Failed writes retain intent using F107's diagnostic logging and
localized error callback. Unlike the legacy Save path, it does not expose arbitrary
storage exception text to the user.

## Validation and limits

Three focused native cases cover English/Spanish selection/navigation, marker-to-
selector synchronization, missing versus zero evidence, real typed partial/invalid
input, pending navigation lock, failure/retry/Cancel, shared-anchor persistence,
drag-to-field refresh, Locate pulses/teardown, empty controls and literal markup.
851 baseline tests pass, 96.30% coverage. Ruff check/format, strict mypy (176 source
files), architecture and wheel/sdist builds pass. The isolated extracted wheel
verifies actual overview/packaged icons, Save/Cancel/retry and saved-project reopen.
All 500 reference hashes and the approved dependency lock remain unchanged.

Twenty-two native captures under `artifacts/plot-job-overview` include extracted
source-code empty/populated controls, English/Spanish empty/populated/unpositioned,
pending/failed-save/Cancel/saved/Locate/enlarged states, plus adjacent map
compositions at 1460×800 and 1920×1060. Review covered important states and clipping;
map containment assertions pass. English empty and populated 390×640 fixture
images match the original pixel-for-pixel. These are same-platform component
comparisons, not full PLOT/application or cross-platform acceptance. The failed-
save harness captures retained draft controls; it collects the injected error text
rather than claiming a new final-window error dialog has been integrated.

Evidence: `f108_validation.json`, `artifacts/f108-check.log`,
`artifacts/f108-wheel.log`, `artifacts/f108-native.log`; reproduction scripts:
`docs/reference/f108-capture.py.txt` and `f108-verify.py.txt`.

Next: original Worker Overview and its visibility/enable/lock/scale/position/Save
controls, marker context actions and Load Into Tool selection handoff; then
summaries and complete PLOT window composition. Production PLOT remains disabled.
Parent close consent, remaining map actions, intentional deletion composition,
comprehensive-copy validation and final acceptance remain. JROT follows PLOT:
CBC single-tool, HiGHS multi-tool, no GLPK. No reliable overall completion
percentage or finish date is claimed; the former 67% remains withdrawn.
