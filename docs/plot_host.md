# Original PLOT host composition — F116, 2026-10-07

`presentation.desktop.plot_window.PlotWindow` composes the reviewed components
from F103–F115. It is a modal dialog owned by the caller; project lifetime remains
with that caller. `PlotHostRepository` extends the existing saved-result read
port with saved job reading and explicit position commits. Image reader/writer,
validated importer and exact saved-assessment handoff are injected separately.
No concrete storage adapter, SQL, parent-variable lookup or reference-tree asset
path enters this composition. All icons come from the packaged processed set.

## Original source mapping

Reference `src/plant_layout.py`, `PlantLayoutWindow` sets the title, maximize flag,
1460×1060 initial size and 1300×1045 historical floor. Its
`configureResponsiveLayout` lines 2575–2624 define the two detail tabs, padded
worker tab glyph (82 pixels on a transparent 96-pixel canvas), icon size 24,
map/detail horizontal splitter, stretch factors 4:1 and initial sizes 1040:390.
The root uses margins 2/8/2/8 and spacing 8 with filters, middle and outcome in
that order. These source controls/layouts define the migrated host; screenshots
were used for inspection, not reconstruction. Original mode synchronization at
3135 selects Job Placement for job mode and Worker Overview otherwise.
`selectRiskViewMode` immediately applies a changed risk mode. Map selection
reveals the details tab. The source close/saveVars workflow hands a selected
saved worker assessment back to the parent; existing F112 exact ownership/editor
acceptance replaces copying mutable parent variables.

## Complete host workflows

Opening loads the default saved workplace and selected LiFFT rows without writes.
Apply reads a complete saved result before publishing it. Explicit marker Save
and image Save retain their existing component-owned transactions. Applying with
pending marker changes is rejected, keeping the current results and edited
controls; Save/Cancel remains available in those controls. Failed risk-mode Apply
restores the applied risk button so the controls agree with the map/outcome.
Job mode selects the job detail panel; individual/comparison select workers.
A real marker selection reveals the corresponding detail tab.

Closing a clean host needs no confirmation. Pending image or marker edits prompt
for explicit discard, defaulting to No; cancellation retains the window and edits.
Close never saves data. Owned worker/job locate timers and outcome animations stop
on accepted closure. Load into Tool first uses the layer's existing pending-marker
interlock, then the host's pending-image consent and the integrated editor's
injected acceptance. Only acceptance closes PLOT. Rejection, consent cancellation
or errors retain PLOT and its pending image. No multi-user assumptions or
speculative asynchronous infrastructure were added.

## Composition corrections and visual limits

The historical 1300-wide floor cannot contain the fixed-format outcome regions
already characterized in F115. The host now derives its width floor from the
actual root layout. At the native fixture the floor is approximately 1411 pixels;
the original 1460-pixel initial size remains. Worker details reserve their real
content width plus the vertical scrollbar and frame, instead of clipping controls
in a 390-pixel tab. Vertical scrolling retains access to the lower controls at the
minimum height. Workplace headings reserve their current font's text width.
The source rail's white bold title rule, originally applied separately, is now
included in the shared PLOT stylesheet. Palette, fonts, icons and layout order
remain source-derived; these are actual clipping/style corrections, not a redesign.
Localized long tab labels retain Qt's source scroll-button behavior.

Twenty-two native XCB captures record EN/ES initial, minimum, worker, expanded,
job, comparison, enlarged and empty states; scrolled bottom worker controls;
owned close-Cancel and read-error dialogs. Geometry records check the complete
root regions inside the actual window. Five focused native tests exercise real
buttons, failed reads, pending-marker Apply, close Yes/No, editor rejection/error,
pending-image consent, successful exact handoff and no implicit project writes.
The independent extracted wheel repeats actual host/mode/resize/modal/handoff
workflows with packaged assets and a separate temporary database. No full-host
source pixel equivalence is claimed by these composed-fixture checks. Previous
source component comparisons remain recorded at their own checkpoints.

## Remaining PLOT integration

Zoom, actual size, opacity, capture and export rail actions remain disabled.
Review/connect original saved-data deletion, then expose this host through the
main PLOT button and verify the actual integrated editor workflow end to end.
This checkpoint does not enable an incomplete production PLOT window. Legacy
project import/comprehensive copied-project validation and final application
visual/workflow parity remain later acceptance work. JROT follows PLOT with the
owner's CBC single-tool/HiGHS multi-tool/no-GLPK decision.

Evidence: `f116_validation.json`, `artifacts/f116-check.log`,
`artifacts/f116-wheel.log`, `artifacts/f116-capture.log` and
`artifacts/plot-host`. Reproducible capture/wheel/verification scripts are archived
as text in `docs/reference/f116-*.py.txt`; they do not become production tooling.
