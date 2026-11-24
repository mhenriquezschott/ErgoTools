# ErgoTools Android worker-assessment demo

The tablet demo provides project creation/opening/saving, touch worker management
and a shared multi-task LiFFT/DUET/ST editor. Calculations and native project storage use
the unchanged desktop core. The demo includes workplace browsing, assessment reuse and organization editing.

From the ErgoTools repository directory:

```bash
bash prototypes/android_demo/run.sh
```

The launcher detects shared-code or tablet-frontend changes, rebuilds if needed,
starts/reuses the dedicated tablet emulator, updates the APK automatically and opens
the app. With no changes it reuses the installed app. Updating retains the tablet's
saved test assessment. No manual Android installation or OS navigation is needed.
This is an automatic rebuild/update workflow, not live hot reload.

Optional commands:

```bash
bash prototypes/android_demo/run.sh --rebuild
bash prototypes/android_demo/run.sh --stop
```

## Open a project and assessment

1. First launch opens **Project home**. Choose **Explore sample project**, or use
   **Create project** to create an empty metric/imperial project.
2. **Save** stores the current project on this tablet and adds it to Recent projects.
   The button is disabled when the project has no changes.
3. With the sample, choose **Open / start assessment**. Its worker is W01, Elena Muñoz.
   Enter **30 cm**, **49 N**, **100 repetitions** and press **Calculate**: damage
   **0.0003**, probability **13.2%**. Calculation does not implicitly Save.
4. Press the project **Save** to retain the result. **Home** returns to the project
   overview; Android Back also returns home before exiting.
5. **Save As…** opens Android's system picker to write a complete `.ergprj` file.
   The exported file can be opened on desktop ErgoTools. **Open project…** imports
   a validated tablet copy; the external original stays unchanged. Save keeps the
   tablet copy; use Save As for an external file.
6. Switching/closing an unsaved project offers **Save / Discard / Cancel**.
   Accepted draft edits are also recovered after app restart. Temporary nonnumeric
   text is not an accepted numeric draft and can be lost on forced OS termination.

The home screen restores the active project and offers up to ten saved recent
projects. Empty projects can add and edit workers through **Workers**, then start
one standalone assessment per tool for the selected worker. Existing assessments
open with all their rows and original metric/imperial units (DUET is dimensionless). Other tools and complete
organization/Job/rotation data are preserved without truncation. Imported older unsupported formats show an error; no migration is run.
The previous feasibility-only `tablet_sample.ergprj` remains untouched in private
storage; M01 creates its explicit sample separately.

The current build targets the **x86_64 emulator**, not ARM tablets or Play Store
publication. It runs offline, with Python and SQLite inside the APK. Desktop-only
visual changes require their corresponding mobile UI implementation; changes to
shared logic/storage are included in subsequent automatic builds.

## Isolated setup on this Linux workstation

- CLI environment: `tmp/android-demo-toolchain/venv`, Flet/CLI 1.1.2.
- Flutter: `~/flutter/3.47.9`, required by that Flet release.
- SDK, source staging, APK and logs: `~/.cache/ergotools-android-demo/`.
- AVD: `ErgoTools_Tablet_API35`, Pixel Tablet / Android 15 / Google APIs x86_64.
- Emulator: separately pinned 36.4.10 under the dedicated cache. SDK emulator 37.2.13
  hangs before Android boot on this host; the same image boots with 36.4.10.
- ADB serial/port: `emulator-5580` / 5580. Commands never target real attached devices.
- Desktop Python stays 3.13.14 and its existing `.venv`/`uv.lock` stay unchanged.
  Flet's bundled Android Python is 3.13.18; Android SQLite is 3.53.4.

The launcher deliberately checks the installed setup rather than silently installing
SDKs or accepting tool licenses on every launch. Full setup/version and cleanup notes
are in [the Android demo guide](../../docs/mobile_android_demo.md).

## Workers and shared history

Open **Workers** from project Home. Use ID/name search, swipe the alphabet (only
available last-name initials are enabled), or switch between ID and name order.
Previous/Next follows the filtered list. Landscape uses list/details columns;
portrait stacks them. Project Save, Undo and Redo stay reachable while scrolling.

**Add worker** opens a creation form. Worker ID is required; names, sex, full birth
date, height/weight, hiring date and contact details are optional. Tap the form's
**Add worker** once to accept it. The birth calendar opens 18 years back, but no DOB
is saved until selected. Age is derived. Worker body values use project units
(cm/kg or in/lb); stored values retain the desktop canonical cm/kg convention.

For an existing worker, finish a field by moving to another control to accept its
change. Undo reverses each completed field independently. Add/delete undo/redo asks
for confirmation because it removes/restores a record. One project timeline is used
from Workers, Home and every assessment editor. It retains 25 actions during
the app session; history resets on opening a project or restarting the app. Save
retains the timeline and marks the current revision clean.

Expand **Employment and contact details** for hiring/contact data. The section stays
expanded during history replay. IDs of existing workers are fixed; deleting a worker
with assessments, assignments or protected rotation references is refused. No
associations are silently cascaded. Use project Save to retain all accepted edits.

Worker selection is remembered for assessment continuation. **Open / start
assessment** opens that worker’s standalone assessment, otherwise the first existing
workplace assessment. If none exists, an explicit **Start assessment** confirmation
creates one standalone assessment with one empty task. Choosing between workplace
assessments belongs to M05.


## LiFFT tasks and results

Landscape shows a task list, the active task’s inputs and a result card. Portrait
stacks these cards with touch scrolling; project Save/Undo/Redo stay at the top.
Tap a task to edit it. Names are optional; new accepted names enter the project’s
reusable catalog. **Use an existing task name…** offers search and the touch alphabet.
Numeric fields use the assessment’s units: cm/N or in/lbf, plus repetitions per work
day. Load is force, not kilograms of body mass.

Complete a field by tapping another control. The unchanged core recalculates the
whole assessment automatically. **Calculate** explicitly checks the same inputs.
Blank unused tasks do not make a result partial. Started rows missing inputs are
listed under **Still needed**; a partial result is labeled. Invalid inputs cannot
retain an older result. The gauge, damage bar, total and per-task details show the
accepted result; animation changes only the presentation.

- **+ Task** adds one blank row, up to 100. New assessments begin with one task.
- **- Task** removes checked rows, or the active row if none are checked. Removal
  warns when content is present; removing all rows leaves one empty task.
- **Select all / Select none** controls explicit task checkboxes. **Copy selected**
  copies checked tasks, otherwise the active task, using Android’s clipboard.
- **Paste tasks…** previews editable plain tab-separated inputs. Use three numeric
  columns (lever arm, load, repetitions), or an optional task-name column first.
  No header or calculated columns. Paste appends, except it replaces a single
  wholly empty slot. It uses the current assessment’s units without conversion.
- **Clear assessment** confirms before clearing this assessment’s inputs/results;
  it preserves the task count, ownership and reusable name catalog.

A completed input change is one Undo step. Paste includes its rows, newly reusable
names and results in one compound step. Structural replay and task-name removal
ask for confirmation. Save publishes the current project without clearing history.
A Calculate with unchanged inputs/results does not create a new Undo step.

Try two identical tasks of **30 cm / 49 N / 100 repetitions**: total damage
**0.0006**, probability **17.1%**. The original single task is **0.0003 / 13.2%**.
Undo the second task’s repetitions to see an explicit partial assessment, then Redo.

Clipboard support here is TSV input-only, not the desktop spreadsheet file importer.
Native portrait/landscape acceptance is on the dedicated Android emulator. Physical
ARM tablets, Play Store packaging and large-project memory performance are untested.


## DUET and ST

Choose **LiFFT / DUET / ST** on project Home, then **Open / start assessment**.
The same branded choices are available inside the task editor. Switching tools
accepts current inputs and opens the selected worker’s assessment for that tool;
if absent, creation asks for confirmation. Each worker/tool owns its independent
standalone source. Simply choosing a tool on Home never creates an assessment.

All tools share task list/detail layout, task names, checkboxes, add/remove/clear,
clipboard preview, automatic calculation, risk gauge/damage bar and project history.
DUET offers **OMNI-Res effort rating** with the same 0–10 descriptions as desktop,
plus repetitions. ST offers **Force direction** plus lever arm, load and repetitions.
New ST assessments use the desktop direction convention; imported source convention
and original units remain unchanged. A discrete selector is accepted/calculated as
one Undo action. Finish a numeric field by moving focus or the keyboard action;
hiding the keyboard alone may leave that field focused. Calculate/Save/navigation
also accept pending valid inputs.

Examples using one task and 100 repetitions:

| Tool | Inputs | Damage | Probability |
|---|---|---|---|
| DUET | OMNI-Res 6 | 0.01162 | 29.5% |
| ST | Handling Loads, 30 cm, 49 N | 0.00088 | 12.2% |
| ST | Push or Pull Downward, 30 cm, 49 N | 0.00010 | 5.5% |
| ST | Horizontal Push or Pull, 30 cm, 49 N | 0.00029 | 8.2% |

Clipboard column order, optional task name first:

- LiFFT: lever arm, load, repetitions.
- DUET: OMNI-Res integer 0–10, repetitions.
- ST: direction code 0/1/2, lever arm, load, repetitions.

ST codes mean the destination source’s recorded convention, matching its dropdown:
0 Handling Loads, 1 Downward, 2 Horizontal. Paste does not convert units or direction
conventions between source documents. Use inputs appropriate to the destination.
Calculated output columns never enter task input clipboard data. Save keeps all
three tools together in the same desktop-compatible native project.


## Choose assessment context and reuse data

Open **Assessments** from Home or the task editor. Select a worker using ID/name
search, the same touch alphabet as Workers, or the worker dropdown. Select the tool.
The browser shows that worker’s standalone source first, followed by expandable
**Plant → Section → Line → Station** branches containing only saved assessments.
Each card shows its full location/shift, optional Job, task count and colored saved
probability. **Open assessment** opens that exact source. Tool switching inside a
workplace editor keeps the same assignment; a missing tool asks before creating it.
Closed assignment sources are labeled explicitly and remain separate from active ones.

**Add assessment…** opens a real worker/shift/hierarchy picker. Choose standalone or
expand a plant, section and line and select a station. The shift choice applies to
station destinations. Existing source values are shown beside destinations. Adding
to an occupied context asks before replacing it with one empty task. New empty
assessments are valid saved drafts. The desktop must supply organization data; this
slice does not add a tablet organization or Job editor.

**Copy / Move…** is available on saved cards and in the task editor. It includes only
the current tool. Copy keeps the original and creates an independent destination;
Move removes the source only after successful destination creation. The destination
can be the same or another worker, standalone or any real station/shift. The identical
source location/worker is disabled. Existing destination data requires confirmation
before replacement. Source inputs, task names, original units/direction convention
and exact matching calculated results are retained without recalculation.

**Delete assessment** confirms before deleting one source and its result. The
workplace assignment, optional Job and other assessments remain. **Clear assessment**
inside the editor instead keeps the assessment and its row count, clearing inputs.
Undo/Redo restores complete source/result/assignment changes as one project action;
structural replay asks for confirmation. Browser filters and expanded paths stay in
view state; they do not alter calculation input. Project Save retains all changes.

For the current demonstration, Open **Tablet_contexts_M05.ergprj** in Android Downloads.
This is an independent private copy with two plants and Day/Night shifts. W01 has
standalone LiFFT/DUET/ST and LiFFT at Harbor Plant / Packing / Line A / ST01 / Day.
W02 starts with an empty standalone LiFFT source. Try copying the W01 workplace
assessment into W02’s standalone source, then Undo. Source files in Downloads and
maintained desktop test projects stay unchanged until an explicit external Save As.

## Complete sample and personal display settings

From Home choose **Open complete demo**. The usual Save/Discard/Cancel protection
runs first, then a fresh unsaved tablet copy is created. It contains four fictional
workers with demographics, all three tools, two plants/four stations, Day/Night shifts,
optional Job assignments, one empty workplace ST assessment and one closed ST
assignment. All eighteen populated sources use real core calculations; the remaining
source is an explicitly empty draft. Nothing is added to maintained desktop projects.

Try W01 for low values, W02 for high values, W03 for intermediate LiFFT/DUET values,
and W04 for varied tool results. **Assessments → W01 → ST** also contains the closed
Harbor / Packing / Line A / ST01 / Night source. W03/ST has an empty workplace draft
at Harbor / Packing / Line A / ST02 / Day. **Save** keeps your tablet copy;
**Save As** exports a complete desktop-compatible `.ergprj` file.

**Settings** is available on Home and subpages. It offers live gauge/range-label
previews, independent needle/bar/body animation switches and duration, an optional
expandable body-region illustration, and per-tool task-name/derived-detail visibility.
Required scientific inputs remain visible. Hiding names never removes them, changes
calculations or excludes them from copying. The task-display preview is explicitly
illustrative; the result preview uses a real saved result when available and is
labeled as an illustration otherwise.

**Preview animations** runs one finite transition. The body illustration has touch
Front/Back/Rotate controls and horizontal touch rotation. The current refinement uses
72 offline five-degree views rendered from the original desktop STL geometry with per-tool
depth-correct masks; Android does not load VTK.
It highlights lower back, hands/wrists or shoulders according to the selected tool.
An unavailable probability uses a neutral highlight, not a low-risk assertion.

**Apply settings** keeps personal choices across app restarts in private
`view_settings.json`. **Cancel**, Android Back and Home discard a settings draft.
Settings never enter project Undo/Redo or the native project file. Source edits
still share the existing project timeline and Save. The complete assessment workflow
requires no network once the app is installed; first build/toolchain setup does.

Physical Android devices, ARM packaging,
store distribution, PLOT/JROT mobile screens and Job editing are outside
this worker-assessment demonstration.

## Tablet design refinement

Home presents actual saved-assessment previews and direct entry to assessments,
workers and **Organization & shifts**. The result panel includes thick gauge bands,
readable scale labels and probability, an adaptive legend and an animated cumulative-
damage meter. Portrait puts task selection and anatomy access beside the inputs.

Organization supports the project hierarchy and typed metadata, calendars and
24-hour shift clocks. **Blocks & breaks** opens proportional timing with selectable
intervals, precise time pickers and touch Split/Draw/Move/Remove tools. These reuse
existing native validation and shared project Undo/Redo. An absent template remains
a preview until explicitly accepted or edited. Main Save stores accepted edits;
Save As exports the complete native project. Existing rotation timing copies remain
independent. No desktop core, schema or dependency changes are required.

See [the Android demo guide](../../docs/mobile_android_demo.md) for setup details and remaining physical-device limitations.

Result transitions start after the native result card is laid out on assessment/tool
loading. Separate gauge/bar/body switches and duration remain in Settings. The body
uses shaded multiplicative region colors, preserving contours, and gapless touch
rotation. Timing Draw and Move/resize show live validated geometry; release accepts
one change and an interrupted gesture leaves the project unchanged.

Front/Back and tool changes use a shared cancellable shortest-angle transition,
visiting every rendered view. Switching tools preserves the current angle before
turning; the needle animation never resets it. The LiFFT decal uses depth-aware
surface tolerance to avoid gaps where its source mesh intersects the display body.
