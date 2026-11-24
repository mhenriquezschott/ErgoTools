# PLOT Shift View — developer preview

The owner authorizes a read-only desktop playback of complete baseline/optimized
rotations. Enable **Settings → General → Developer options** for this application
session, then open **PLOT → Shift View**. The option defaults off and resets on
restart. No new database tables, format, dependencies or calculator/optimizer rules
are introduced. The three ordinary PLOT modes retain their normal behavior.

## Try the complete example

Open `test_projects/native/shift_view_demo.ergprj`. It has twenty fictional named
workers with birth dates, sex and metric demographics; twenty Jobs and exact
station/shift placements; sixty calculated worker assessments; sixty calculated Job
tool measurements; two named tasks per source and six reusable task names.
No direct risk values are seeded. All values come from the existing calculators.
The original seed reused the comparison image and selected coordinates. The owner
has since supplied a dedicated 20-worker plant image and positioned every worker.
The maintained demo now uses that image, with positions aligned horizontally within
eight work cells. Worker identities and X coordinates are retained. Baseline block
one identifies the Job at each fixed mapped destination; workers need not be swapped
merely to improve the animation. The seed generator still creates its original
comparison-image example; it does not overwrite this customized maintained demo.

The 08:00–18:00 shift contains four 135-minute productive blocks, separated by three
20-minute breaks (540 working minutes / 60 break minutes). Both saved examples have
real retained three-tool optimization results:

1. **01 · Unrestricted balanced rotation** — no worker restrictions.
2. **02 · Avoid consecutive High Jobs** — every worker has No adjacent High enabled.

The baseline rotates each worker among similarly loaded Jobs in different map areas,
so high workloads remain concentrated and workers still visibly travel. Optimized
runs redistribute them; the constrained run independently passes all adjacency rules.
The baseline deliberately illustrates consecutive High exposures rather than being
forced to obey the later optimization restrictions.

The fixture's primary passes reported optimal under configured solver tolerances;
secondary balancing passes retained feasible incumbents at the 30-second per-pass
limit. This is not a claim of an exact unrestricted mathematical optimum. The
existing solver/model and acceptance policy are unchanged.

## Player controls

Choose a labeled **Rotation** and **Baseline / Optimized**. The shared ergonomic-tool
filter above the map selects the displayed tool; use Apply Filters as in normal
PLOT. The player reads
the latest project snapshot when entered, selected or reloaded. Baseline and optimized
are paired with the same retained run's frozen timing/coefficients; current Job edits
are not silently mixed into an older result. Changed drafts/data are identified.
A baseline without a retained run uses current calculated Job values.

The player replaces the bottom outcome/gauge region; it never adds a row above
the map or changes the map/sidebar geometry. Blocks show their start/end clocks.
**Play / Pause**, **Stop**, and clicking the timeline control playback.
**Previous / Next** jumps between work/break boundaries, keeping the current
Play/Pause state. **Reload** starts at the beginning and resumes only if playback
was already running; paused, stopped and ended playback stays paused.
Switching tool or baseline/optimized retains the shift minute; a running comparison
resumes. Changing preview speed preserves the clock and pauses. The initial settings
are two seconds per productive block and 1.2 seconds per break movement. Blocks retain
their real duration weights, regardless of preview pacing. Adjacent blocks without a
break receive a shorter zero-clock-time transition. Smoothstep easing accelerates and
decelerates movement; it is schematic movement, not a walking-route/time calculation.

Squares stay at fixed Job destinations and keep their selected-tool Job risk colors.
Worker shapes follow existing sex analogies (circle, triangle, hexagon if unspecified)
and carry short IDs, as do the ordinary map symbols. All modes use the same saved
top-left anchor and fitted symbol dimensions. Fixed Job frames surround those worker
positions; their captions sit below. No center/top-left coordinate conversion is
silently applied.

The right area has **Rotation exposure / Worker Overview** tabs. Exposure columns
reserve readable widths for both Now and Final; worker names use the remaining space
and retain full text in tooltips. Selecting a row or map worker synchronizes the blue
frame, table and worker selector. Worker Overview offers the shared alphabet,
ID/name search, navigation, demographics, current workplace/Job, colored accumulated
and final indices, and Locate. It contains no editable worker/map values. Locate
centers the moving symbol and blinks its blue selection frame without changing
its saved position. Clicking an already-selected exposure row clears both the row
and worker selection, including while playback continues.

Shared workplace/shift filters restrict fixed destinations and workers visiting them;
demographics restrict participants, independently of their individual assessments.
The full recorded rotation still supplies exposure history and its final divisor:
filtering never reruns the optimizer or recalculates a partial-population schedule.
No matching rotation gives an empty map with disabled playback. Incomplete mappings
show available destinations/participants and a bottom diagnostic, with playback and
seeking disabled. Missing metadata/timing can show known anchors neutrally without
inventing exposure values.

Map zoom, pan, opacity, selection and capture remain viewing actions. Editing controls
and marker dragging are unavailable in Shift View. Returning to normal modes restores
their original tabs/controls. A fixed shared bottom region preserves the exact
rail, canvas and sidebar rectangles and fitted image transform across mode changes.

To try different restrictions, close PLOT, open JROT, select either demo rotation,
change restrictions and run optimization. **Keep optimization result** accepts the
new run in the open project; Main Save stores it. Reopen PLOT → Shift View to see it.
Reload reads newly accepted results without launching any solver. Merely running a
preview without Keep does not replace a retained result.

## Index meaning and map ownership

At elapsed shift minute `t`, the displayed contribution is

`sum(completed productive minutes in each Job × that Job's risk percentage) / D`.

`D` is JROT's full averaging period: productive minutes if breaks are excluded,
otherwise full shift minutes. It is a partial contribution from zero to the final
JROT weighted index, not an average over only the time elapsed so far. Breaks add
neither exposure nor physiological recovery. This is separate from a worker's own
assessment and is not an injury-probability trajectory. No task calculation is
changed or repeated by playback.

Fixed destinations are inferred once from the mapped workers in baseline block one,
using exact Job-placement identities. The worker's baseline Job must match its mapped
assignment. The player requires complete timing, baseline staffing, selected-tool
risk values, one plant image and all destination points. It never fabricates a
missing station, coordinate or general-Job placement. Worker-owned map coordinates
remain untouched; animation uses separate inert scene items. Paired baseline and
optimized schedules always use the same destination map.

## Code and verification

- `application/shift_playback.py`: read-only preparation, weighted projection and
  preview pacing, independent of Qt/storage/solvers.
- `desktop/plot_shift_player.py`: local controls, timer and participant summary.
- `desktop/plot_shift_graphics.py`: inert scene glyphs and seekable timeline.
- `tools/create_shift_demo_project.py`: reproducible fixture creation with exclusive
  publication; it refuses existing destinations.
- `tests/test_shift_playback.py`: exact numeric examples, break/no-break timing,
  twenty-worker mappings/constraints, opt-in/native controls and byte-identical
  playback, including a real shared editing session staying clean.

This experimental mode has been exercised on Linux with a private Qt XCB display.
Native Windows/macOS acceptance of Shift View remains separate.

## Normal map layout tools

The compact Plant View rail contains Horizontal/Vertical alignment, Snap and Grid.
Right-click Grid to edit its spacing in original-image pixels. There is no extra
tools row above the image. Live mouse X/Y appears in Worker Overview → Visual
controls or Job Overview → Assignment map position, separately from the editable
assignment anchor fields. Comparison Worker Overview hides Visual controls.
Complete scale/coordinate edits and Visible/Enable/Lock changes use shared project
Undo/Redo, including when a valid numeric field still has focus. Drag an empty image area
with the Select cursor to draw a selection rectangle. Shift-click adds/removes an
icon. Each selected icon keeps its familiar blue frame; a dashed blue envelope joins
the selected group. Dragging selected workers moves them together. Locked workers
remain fixed and are excluded from alignment.

Horizontal shares selected centers' Y coordinate; Vertical shares X. Each alignment
or completed group drag is one chronological map edit; Undo/Redo restores the whole
batch through the existing project history. It never changes assessments or Job risks.
Snap rounds the dragged worker/group anchor to the nearest grid intersection;
a selected group keeps its internal spacing instead of snapping each member separately. Initial spacing follows
the selected icon's source-pixel size until the user chooses a spacing. The light dotted
grid appears only during a snapped drag unless Grid is explicitly enabled. Grid,
selection, spacing and cursor feedback are local view state; no schema or saved geometry
is added for them. The grid is bounded by the actual image and never creates image
scrollbars. Live feedback reports the mouse in original-image coordinates; the editable X/Y
fields report the actual assignment anchor after completed placement.

Placement tools (Horizontal/Vertical alignment, Snap and Grid) are grouped directly
below the opacity tool in the compact Plant View rail.
