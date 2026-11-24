# Android tablet worker-assessment demo

Run and optional rebuild/stop commands are in
[the demo README](../prototypes/android_demo/README.md). This is a separate Flet
frontend, not a desktop Qt layout scaled down. Touch scrolling, numeric input,
local calculation and native project persistence are supported through project Home,
native Open/Save As, app-managed Save, recents, worker editing and shared history.
LiFFT, DUET and ST share touch task/result components with reusable names, clipboard
support and animated results. The demo includes workplace browsing, assessment reuse,
organization editing and personal display settings. It is isolated from the desktop
application and shares its calculation/storage core.

## Architecture and isolation

`demo_service.py` composes existing AssessmentEvaluator, result_snapshot,
DocumentSession and AssessmentProjectFile APIs. Calculation, source/result
precision, format-24 schema, worker demographics and standalone ownership are
unchanged. Save exercises begin_editing, SQLite checkpoint serialization/restore,
source-bound result storage and commit_editing, then closes/reopens the repository.
The mobile screen owns the controls, gauge and feedback only. No server is required.

Each build copies domain/application/infrastructure Python files byte-for-byte into
owned cache staging. This is packaging, not a maintained fork: future builds take
current shared files again. `source_manifest.json` records staged hashes; a digest
controls rebuilding. Desktop Qt/VTK/HiGHS are not imported or installed in the APK.
The desktop Python environment, root dependency lock, calculators, schema and
maintained native fixtures are not changed.

The initial compatibility test used private `files/data/tablet_sample.ergprj`,
which M01 leaves intact. Current project files are described below. It separately
writes `compatibility_probe.ergprj` and JSON runtime evidence from a fixed synthetic
vector on launch. Probe generation never overwrites the interactive sample. APK
updates use `adb install -r`, a stable package ID and the same signing setup, retaining
private data. Closing the emulator also retains its disk; the launcher never wipes it.
M01 imports/exports complete native bytes through Android’s system document picker;
content URIs are never opened as Python filesystem paths.

## Toolchain

Owner authorizes installing tools for this isolated test. Exact selected versions:
Flet/CLI/desktop 1.1.2; its Flutter 3.47.9; Flet python-build manifest 20261027,
Android Python 3.13.18; SDK command-line tools 12.0; Android 15/API35 Google APIs
x86_64 image; OpenJDK 21.0.9 already installed. Gradle installs its required SDK
platforms/build tools/CMake into the isolated SDK. Runtime/build pins are separate
from the desktop's approved Python 3.13.14 and root uv.lock.

An official Android Emulator 36.4.10 archive is installed separately at
`~/.cache/ergotools-android-demo/emulators/36.4.10/`:
`https://dl.google.com/android/repository/emulator-linux_x64-15004761.zip`.
Its published SHA-256 is
`58bfdf0572f06ec007a7287154cdc6b2ebfea947d07a1e26a0f6b5e1a39e9191`.
The archive hash was verified before extraction. The SDK's newer 37.2.13 is retained
for diagnosis, not used by the launcher. GPU mode, CPU acceleration and proxy removal
were isolated; 37 still hung before kernel boot. The same AVD boots with pinned 36,
KVM, SwiftShader GLES and Vulkan disabled. This records observed host compatibility,
not a general claim that emulator 37 fails on all Linux systems.

SDK: `~/.cache/ergotools-android-demo/sdk`; Flutter: `~/flutter/3.47.9`;
CLI environment: `<checkout>/tmp/android-demo-toolchain/venv`.
Flet, Dart and Gradle also create their ordinary user caches. SDK/runtime downloads
are substantial on first setup. Later APK builds use caches. No existing SDK or
personal emulator was replaced. The dedicated AVD resides below `~/.android/avd`.

## Rebuild and launch behavior

`run.sh` invokes the stdlib-only `manage.py` launcher. It stages current shared and
prototype files in a path without spaces, preserving Flutter's incremental build
cache. A build failure stops and points to build.log rather than opening stale code
as an updated app. The launcher reuses or cold-boots only the dedicated AVD, waits
for Android readiness, installs a changed/missing APK, then opens the stable package
`org.ergotools.tabletdemo`. Main desktop UI changes do not automatically redesign
mobile screens. Shared services and mobile frontend changes trigger a fresh APK.

Logs are `~/.cache/ergotools-android-demo/build.log` and `emulator.log`.
Runtime Python messages are available through the SDK adb logcat tag `flet.python`.
No passwords, personal projects or real worker information are included in the sample.
Prototype screenshot/evidence files are under artifacts/android_demo_20261109.

## Removal

Close only the demo with `run.sh --stop`. To remove the demo later, remove its
prototype folder, dedicated cache, dedicated AVD files named ErgoTools_Tablet_API35
and checkout-local tmp/android-demo-toolchain. Remove Flutter 3.47.9 only if nothing
else uses it. Ordinary shared .flet/.pub-cache/.gradle caches may be retained; do not
blindly remove them or the user's global .android directory/ADB keys. Desktop
ErgoTools and all project files remain independent.

## Acceptance and limits

The APK was installed and exercised on the actual Android emulator, not just a Linux
Flet window. Its Android Python calculation matches the desktop oracle exactly for
the documented vector. The native repository's editing/checkpoint/commit path works;
no Qt, VTK or HiGHS import appears in the Android process. A saved project was pulled
from Android, opened/edited by the unchanged desktop adapter and returned to Android;
the new 98.1 N input and 16.016181175764896 result were displayed after reopen.
Automatic APK replacement, app relaunch and emulator cold boot retain those edits.
The cached launch prints that both build and installation were skipped.
Three bridge regressions cover known results, invalid-input file preservation and
startup-probe isolation. Basic native screen/keyboard/scroll review supplements the
existing unchanged-code regression evidence. This does not certify DUET/ST, mobile
worker management, a mobile document picker, avatars, the full desktop workflow or
Play Store distribution. Those follow after this feasibility gate.

The frozen Linux CLI environment is recorded in
`prototypes/android_demo/requirements-toolchain.txt`. Recreating it uses:

```bash
uv venv --python .venv/bin/python tmp/android-demo-toolchain/venv
uv pip install --python tmp/android-demo-toolchain/venv/bin/python \
  -r prototypes/android_demo/requirements-toolchain.txt
```

SDK/Flutter/AVD setup is a one-time workstation installation; regular runs use the
launcher. Do not run desktop `uv sync` against this separate environment. Changes to
the desktop installation instructions are not needed for this optional prototype.

Offline acceptance also passed with guest Wi-Fi and mobile data disabled: startup
ran the real calculator/native storage probe and restored the interactive sample.
Final offline screen was inspected; numeric keyboard and scrolled result captures
are retained with the validation record.

## Project lifecycle

`project_session.py` owns `files/data/workspace.ergprj`, `projects.json` and saved
native files under `files/data/projects/<private-id>.ergprj`. The working file is
separate from the explicitly saved version. The JSON catalog is personal mobile
state, not a schema extension. Native source, result, hierarchy, Job and rotation
content remains complete. Save uses flushed sibling staging and atomic replacement.
Recent entries use private identities, file names, origins and save times. Identical
reimports reuse an existing saved entry; different content stays an independent copy.

At M01, `mobile_assessment.py` selected a worker-owned, one-task metric LiFFT source;
it preserves task identity/name/catalog reference and units through dataclass
replacement. Incomplete drafts save without results. Calculate uses the established
evaluator/result snapshot; the project-level Save remains explicit.
`mobile_ui.py` owns responsive home/forms/overview, native pickers and Android Back
confirmation. Invalid imports, file errors and picker cancellation are visible.
Save As uses `src_bytes`; Android opaque return identifiers are not passed to Path
for file I/O. Suggested export names remain in the tablet catalog when Android does
not return the actual name. Persistent in-place binding to an external document is
outside this milestone; the copy behavior is explicit in the UI.

M01 acceptance: 12 focused native-adapter regressions; required check.sh standards,
types, architecture, naming, reviewed desktop documentation and builds pass using
focused tests with reused unchanged desktop coverage. Prototype files receive a
manual contract/body review and Ruff checks; they are outside the desktop strict
mypy/hash-review inventory. Actual Android native picker export/reimport, cancellation,
new-project keyboard entry, Back Save/Discard/Cancel, invalid import protection,
draft restart recovery, explicit calculation/Save, and portrait/landscape screens
were checked. A private comprehensive project copy (28 workers, 194 assessments)
was imported/saved byte-identically. Evidence: artifacts/android_m01_20261109.
M01 acceptance is historical; subsequent accepted slices are described below.

## Worker management

`mobile_workers.py` contains portable native worker editing/search/unit contracts.
`worker_browser.py` owns touch form/navigation state; `touch_alphabet.py` is reusable
across future mobile pickers. Optional dates use DatePicker; numbers use decimal
keyboards and whole-candidate filtering, including empty text. Edits preserve
unmodified details and canonical body precision. Native ownership validation remains
authoritative for deleting referenced workers.

`mobile_history.py` supplies pure immutable byte replacement and saved-marker
adapters to the existing generic DocumentSession. ProjectSession.change records
successful native operations, ignores byte-identical no-ops and restores working
bytes on failures. Replay atomically replaces only the private workspace; saved
project bytes are unchanged. Project saving marks the current revision clean while
retaining history. New/open/discard reset chronology, app restart restores working
bytes without a persisted timeline. Workers and LiFFT use the same project history;
25 full-byte changes are retained, with native worker-data replay confirmations.
UI disclosure/filter state survives replay; subpage actions stay fixed during scroll.
The only additional persistent app state is selected_worker in the private JSON
catalog, not a native database column. No schema/dependency/formula change.

Validation includes M01 regressions, field-by-field native worker history, precise
imperial body conversion, hidden metadata, duplicate/stale edit rejection, protected
deletion, history limits/redo branching and the numeric filter's clear/partial states.
Actual Android creation, calendars, search, keyboard edits, confirmation/replay,
optional details, save/restart/export and portrait/landscape screens are inspected
with evidence under artifacts/android_m02_20261110. Core desktop checks/coverage are
reused unchanged, with the required gate on the focused prototype tests.


## LiFFT task editor

The M03 `lifft_tasks.py` (generalized as `assessment_tasks.py` in M04) reuses
the native ownership/task catalog APIs, LifftDraft/LifftTask,
AssessmentEvaluator.evaluate_lifft_grid and result_snapshot. New standalone sources
start with one blank task in project units; existing sources retain every row,
identity, name/reference and original units. Stale expected sources reject mutation.
Source/name/result writes commit together to the private workspace. No-op Calculate
leaves native bytes and history unchanged. Edits preserve untouched numeric precision.
Legacy literal names are not silently cataloged by an unrelated numeric edit; newly
entered or pasted names are reusable immediately, in the same compound Undo action.

`task_editor.py` owns task selection, checkboxes, per-field completion, task actions,
name search/alphabet and editable clipboard preview. Landscape uses list/input/result
columns; portrait stacks them. Removal confirms content loss and retains at least
one blank task. Clear keeps row count/identities and existing catalog definitions.
Only current LiFFT content changes; other workers/tools remain untouched. Creating
an assessment is explicit, undoable and rejected for duplicate native ownership.
Worker selection opens standalone first, otherwise an existing associated source;
M05 will provide complete context browsing.

`mobile_results.py` is a reusable presentation component with core risk bands,
10% gauge ticks, optional needle, total/damage bar, readiness and legend. Animation
updates needle/bar geometry only. Blank input has no result; unused blank rows are
ignored. Started missing rows show an explicit partial result/missing-field list;
invalid calculations clear stale result claims. Per-task results use core values.
Numeric field completion accepts one history change. Calculate verifies the same
policy; Save remains project-level.

Clipboard interchange supports Unicode TSV with three numeric input columns or
an optional name column first, no header/calculated outputs, decimal comma, blanks
and finite-value validation. Parsing is atomic, maximum 100 tasks; new identities
prevent aliases. Paste appends or replaces one wholly empty slot. Units must already
match the destination source; no automatic cross-unit conversion or XLSX import is
claimed. Full native-byte snapshots remain bounded to 25 actions; large-file mobile
memory benchmarking is outside this demo acceptance.

M03 evidence: artifacts/android_m03_20261110/validation.json. Focused native-adapter
regressions include known exact numerical vectors, partial/blank/invalid/stale input,
metric/imperial equivalence, precision, 100-row limit, task/name/result compound
history and no-op calculation. Android acceptance covers multi-task keyboard input,
real clipboard round trip, batch removal/history, name search, create/clear/replay,
Save/export/restart and inspected portrait/landscape layouts. Physical ARM devices
remain untested. Prototype bodies/contracts are manually reviewed/Ruff checked,
separately from the unchanged desktop strict-mypy/hash-review gate.


## Shared three-tool editor

`assessment_tools.py` owns tool branding, source field metadata, original selector
labels, typed blank-source construction and input summaries. It has no formulas,
persistence or Flet dependency. `assessment_tasks.py` replaces the LiFFT-only module;
all earlier callers/tests use this same shared implementation, not copied tool
editors. Its task/default helpers support all three models; the existing grid
calculators and source-bound result snapshots remain authoritative. DUET uses project
defaults for its result-unit label but has no physical input units. ST retains each
source’s explicit REFERENCE_UI or MODEL_CODES convention; new sources use the
established reference selector convention. No manual extra direction swap is added.

`TaskEditor` specializes only discrete selector/numeric input metadata and per-tool
labels. Rating/direction selection is one immediate auto-calculated history action.
All tools share names, checkboxes, clipboard, add/remove/clear, validation/readiness,
project actions and responsive layout. `ResultPanel` projects the actual tool title,
probability and five-place damage display without changing stored precision. Worker
selection and document ID remain explicit; tool switches never replace another
source. The native ownership constraint prevents duplicate standalone worker/tool
assessments. Navigation remains view state rather than a data Undo entry.

TSV column schemas are tool-specific: LiFFT arm/load/repetitions; DUET integer
OMNI-Res/repetitions; ST direction/arm/load/repetitions. An optional literal name can
precede these columns. ST direction codes 0/1/2 use the destination draft convention;
there is no clipboard cross-convention/unit inference. All rows/names/results paste
atomically; invalid discrete codes/nonfinite text reject before native writes.
Default OMNI 0 and Handling Loads with no measurements are unused blank rows.
Physical input precision and all untouched source fields/convention survive edits.

M04 acceptance is recorded in artifacts/android_m04_20261110/validation.json,
including known literal DUET and all-three-ST-direction results, both ST conventions,
metric/imperial equivalence, multi-tool native save/reopen, invalid/partial inputs,
compound catalog replay, no-op Calculate and batch removal. Android interactions
exercise real selectors, keyboard, shared history/clipboard, save/export/restart and
inspected portrait/landscape layouts. Full physical ARM-device and imperial UI
interaction acceptance remain outside this emulator demonstration. No root package,
reference, maintained fixture, desktop workflow, schema or formula changes.


## Workplace contexts and reuse

`assessment_contexts.py` detaches complete hierarchy/job/history and worker-owned
source/result projections. Full labels and exact identities stay separate. Active
destination lookup excludes closed owners. Before mutation, the adapter compares
source/owner/result/optional-Job state with the confirmed snapshot. Creation uses
create_historical_assessment or add_workplace_assessment; deletion uses the existing
historical delete API; Copy/Move delegates to TransferRequest/transfer_assessments.
No SQL, schema extension, calculator copy or extra result cache is introduced.

Transfer includes only the selected tool. Core transactions create/reuse active
assignments and retain optional Job data; standalone has no synthetic workplace.
Existing target replacement requires exact consent and same-source transfer rejects.
Saved calculation precision, units and ST convention are copied unchanged. Source,
destination, assignment and sole result are one private native-byte project action;
Move removes source only after destination succeeds. Delete leaves assignment intact;
Undo creation can restore the whole previous project including absence of a new owner.
Empty sources remain valid and source-bound stale-result safeguards stay authoritative.

`context_browser.py` composes reusable nested hierarchy controls, source cards/risk
badges, worker search/alphabet and one destination picker shared by Add and transfer.
Current worker/tool browser contains relevant saved contexts only; the destination
picker contains all real stations at its selected project shift. Standalone is first.
Closed history is marked and opens by exact document ID. Same-context tool switches
look for the same owner rather than silently selecting another location; absent closed
owner tools ask the user to choose a saved context instead of manufacturing ownership.

Focus is explicitly moved from search to the initiating action before confirmation.
This prevents Android dialog cancellation from restoring a search field offscreen and
scrolling away from the selected card. Expanded paths/filters remain local view state
through browser refresh/history. Source/record changes still use the shared project
Save/Undo/Redo; no per-dialog Save is introduced.

Portable tests cover all three tools, standalone/workplace directions, duplicate
station names across plants, shifts, exact-result copying, independent edits, replacement,
delete/replay/reopen, stale intent, optional Job and closed ownership. Synthetic final
publication failure verifies native bytes/history stay unchanged. Actual Android
acceptance and limits are recorded in artifacts/android_m05_20261110/validation.json.
Private fixtures only; no maintained desktop projects or dependencies changed.

## Display preferences and complete demonstration

`mobile_preferences.py` owns a validated immutable `TabletPreferences` value and an
atomic personal JSON store. Stable per-tool keys persist optional name/detail flags;
unsupported intervals, durations and coerced boolean values reject. A malformed file
is retained, safe defaults are used, and Home explains recovery through Settings.
Explicit Apply publishes personal preferences; no native source/result/history/dirty
marker is touched. Cancel/Back/Home discard the draft. Opening Settings first accepts
pending valid assessment inputs or retains an invalid editor with its explanation.

`tablet_settings.py` reuses `ResultPanel`/`BodyRegion`; landscape presents controls
beside the preview, narrow layouts stack them. Result previews use existing saved
source-bound values where possible; absent sources use an explicitly illustrative
40%/0.8 display example. Per-tool task layout uses read-only example fields, never
fake persisted assessment values. Needle, bar and body pulse switches are independent;
animation duration is presentation only. Generations cancel stale preview frames.

`body_region.py` draws a small local front/back silhouette through Flet Canvas.
Tool-to-region mapping and risk color follow the selected assessment; no VTK/network/
third-party rendering dependency or new anatomical calculation is introduced. The
editor exposes it through a collapsed disclosure to preserve initial input space.
Optional field hiding retains original names/data, input validation and clipboard
content; scientific inputs remain accessible and visible.

`demo_project.py` creates only a new caller-owned native destination, refusing existing
files. Existing native hierarchy/Job/assessment/transfer APIs create four fictional
workers, two plants, four stations, two shifts, two optional Jobs and nineteen sources:
twelve standalone, six populated workplace sources (one closed), one empty workplace
ST source. Eighteen calculated results match the unchanged grid evaluator exactly.
Home creates this sample inside an owned temporary folder, validates its complete
bytes before activation under a fresh private catalog identity, then deletes the
temporary file. Save/Discard/Cancel protects any previously active project.

Final M06 evidence is recorded in `artifacts/android_m06_20261110/validation.json`.
Earlier accepted M01–M05 checks remain valid for unchanged components. The required
root gate runs focused prototype regressions with unchanged desktop coverage reused;
prototype code is reviewed/linted separately, not claimed covered by desktop strict
mypy or the desktop reviewed-hash inventory. The fixed six-slice demo is complete;
production mobile packaging/physical-device acceptance remains separate future work.

## Current tablet design refinement — 2026-11-11

The tablet frontend has saved-assessment
previews, actual-model offline turntable anatomy, responsive gauge/legend/damage
visualization and hierarchy/Shift/timing editing through unchanged native APIs.
No Job, PLOT or JROT mobile editor is added. See [the tablet frontend guide](../prototypes/android_demo/README.md)
for current scope and supported controls.
