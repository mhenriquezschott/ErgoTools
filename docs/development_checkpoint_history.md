# Development and reproducibility

Run commands from the new project root. The approved environment is `.python/` plus `.venv/`; caches stay in `.cache/uv/`. Python is 3.13.14. Developer packages: Ruff 0.16.9, mypy 2.3.1, pytest 9.1.1, pytest-cov 7.1.0 and Hatchling 1.32.4. `uv.lock` records all resolved transitive versions and distribution hashes. The optional F28 Qt desktop packages are approved and installed as documented below; the explicitly approved F78 VTK runtime and its Matplotlib/NumPy dependencies are also installed; the approved F120 PuLP 3.2.2 and highspy 1.11.0 solver additions are installed. See [approval](dependency_proposal.md).

Using the existing uv 0.11.25 manager, recreate the approved environment only when necessary:

```bash
uv python install 3.13.14 --install-dir "$PWD/.python" --no-bin --no-registry --cache-dir "$PWD/.cache/uv"
UV_PYTHON_INSTALL_DIR="$PWD/.python" UV_CACHE_DIR="$PWD/.cache/uv" UV_LINK_MODE=copy uv sync --locked --python 3.13.14
bash tools/check.sh
```

The installed manager on the current machine is `/home/mhenriquez/.local/bin/uv`. The check script uses `.venv/bin/python`, fails on the first failing gate, writes ignored reports under `artifacts/`, and builds `dist/`. It never upgrades packages. Platform-specific environment creation and native GUI packaging are not yet validated on Windows/macOS.

Individual gates are `.venv/bin/python -m ruff check .`, `-m ruff format --check .`, `-m mypy`, `-m tools.check_architecture`, `-m pytest --cov`, and `-m hatchling build`. Use the project interpreter for every command. Do not present these results as tests of the original Python 3.10 baseline.

## Reference fixture

`tests/fixtures/risk_reference.json` records 1,013 values and exact reference labels/colors/ranges, the source SHA-256 and Python version. It was captured by loading only reference `src/risk_ranges.py` with runpy under `/home/mhenriquez/anaconda3/envs/ergotools/bin/python -B` (3.10.18). Inputs are the sorted unique union of `i / 10 for i in range(1001)`, -100, 1000 and `math.nextafter(x, d)` for x in 0,25,37.5,50,100 and d in negative/positive infinity. Each output uses risk_band(value) elements 2,3,4. Tests consume the frozen fixture without importing or locating the reference checkout. Regeneration requires deliberate reference review; do not overwrite expected outputs merely to obtain a pass.

## Distribution verification

The foundation wheel was extracted to a temporary directory, then imported with this same interpreter in isolated (`-I`) mode from that directory. Only that extraction was added to the test import path. Risk classification and SHA-256 of every packaged asset passed without the editable source package. This initial smoke check is recorded in `foundation_validation.json`; it is not yet an automated gate in check.sh. Add a reusable distribution smoke gate when release tooling expands.

Git is initialized independently but files remain uncommitted. Do not change global safe.directory settings if the mounted filesystem reports ownership differences; use a command-local `git -c safe.directory="$PWD" ...` after verifying the path. No remote, push or deployment is configured.

## F28 desktop environment

The owner approved PyQt5 5.15.11, PyQt5-Qt5 5.15.17 and PyQt5-sip 12.17.0 for this project. Reproduction now requires `uv sync --locked --extra desktop --python 3.13.14` with the project-local cache/install paths above. The exact versions are in uv.lock; all previous package versions remain fixed. Qt widget tests use the offscreen platform; native XCB visual checks are separate. Launch with `.venv/bin/python -m ergotools.bootstrap` from this root; see desktop_preview.md. This optional extra is Linux-only until another platform is reviewed.

## F68 Job Management preview

Run `.venv/bin/python -m ergotools.bootstrap --job-management-demo` from the new
project root. This opens or exclusively creates a separate persistent synthetic
project beside the selected preferences file (default `.cache/`). See
[job_management_preview.md](job_management_preview.md) for supported actions,
format requirements and remaining controls. It is not the final integrated app.

F70 adds `--job-language es` or `--job-language en` to either Job Management
preview command. Without it the preview uses saved language preferences; the
explicit option does not save a preference change. See
[job_management_language.md](job_management_language.md).

## F72 Worker Management

The default LiFFT preview exposes Worker Management for new-format-six/seven
projects. Open a compatible synthetic project and use the header button. The
existing Job Management demo supplies an empty format-seven project suitable for
creating workers; it has no organization/placements until those are populated.
See [worker_management.md](worker_management.md) for supported actions, canonical
body units, hierarchy payload compatibility and remaining parity work.

## F73 Organization Management and new projects

The default preview's New action now creates format-seven projects, enabling all
migrated management controls. Organization Management creates the empty location
hierarchy and shifts; Job Management places jobs there; Worker Management selects
an assignment and opens/creates its assessment. Existing older projects are not
implicitly upgraded. Hierarchy payload v3 reads v1/v2 but new saves require this
checkpoint or newer. See [organization_management.md](organization_management.md)
for the usable workflow and deliberate deletion/import/geometry limits.

## F74 Original LiFFT task controls

Use `.venv/bin/python -m ergotools.bootstrap --original-lifft-controls` to exercise
the migrated original task grid in the current harness. Without the flag the
previous preview remains available. The new component reuses saved tasks and
existing project/management controls; it is not the final main window.
See [lifft_task_panel.md](lifft_task_panel.md) for Calculate/Save/Reset behavior,
unit labels, disabled saved-assessment deletion and remaining parity work.


## F75 integrated navigation preview

`.venv/bin/python -m ergotools.bootstrap --integrated-preview` opens the shared
original main navigation around the task panel. This is an incremental integrated
preview; remaining tool views and model/result area are pending. See
[connected actions and limits](main_navigation.md). The existing
`--original-lifft-controls` component harness remains available. Native evidence
is in `artifacts/main-navigation/`; validation is in `f75_validation.json`.


## F76 grid workflow

In the integrated preview, Settings now opens the original task-count operation.
The grid calculates complete rows beside unused slots with an explicit incomplete
warning. See [workflow limits and verification](lifft_grid_workflow.md).
Native captures are in `artifacts/lifft-grid-workflow/`; evidence is
`f76_validation.json`. No environment recreation or dependency change is required.


## F77 three-panel integrated preview

The existing `--integrated-preview` now includes the original results sidebar and
left body-panel structure. The avatar viewport is explicitly unavailable pending
VTK adapter/version approval. See [workflow and validation](main_panels.md);
evidence is `f77_validation.json`, captures are `artifacts/main-panels/`.

## F78 native avatar

The integrated CLI enables the packaged VTK avatar and original Rotate/Zoom/Reset
View controls. `--disable-vtk` provides explicit renderer-free review. Follow
[vtk_body_renderer.md](vtk_body_renderer.md) for the native test command and capture
method; six VTK regressions require a native display. All exact approved additions
are in the existing Linux desktop extra and uv.lock; earlier versions are retained.

## F79 original DUET component

DUET task controls are migrated and tested as an embeddable component. The main
preview's DUET tab remains disabled until tool/document selection and shared
sidebar/avatar routing are connected in the next slice. No new launch mode or
permanent standalone window was added. See [scope](duet_task_panel.md) and
`f79_validation.json`; captures are in `artifacts/duet-task-panel/`.

## F80 integrated DUET

The existing `--integrated-preview` now enables the original DUET tab and shared
cards/avatar. Select existing tool data, or approve creation if that tool has no
assessment for the selected assignment. Native workflow checks and current limits
are documented in [duet_integration.md](duet_integration.md); evidence is
`f80_validation.json`. ST is next. Dependencies and launch commands are unchanged.

## F82 ST task component

The original ST component is migrated and native-tested with synthetic projects.
No new launch mode was added; main-preview ST remains disabled until integration.
See [scope and scientific gates](tst_task_panel.md) and `f82_validation.json`.

## F83 integrated ST

The existing `--integrated-preview` now enables all three assessment task tabs.
ST input/edit/history/Save/selection and native shoulder framing are connected;
Calculate retains the documented scientific review gates. See
[tst_integration.md](tst_integration.md) and `f83_validation.json`.
No environment or dependency change is required.

## F84 — task-count workflow validation

The existing Settings toolbar modal works for all three integrated task tabs.
Accepting 1–100 tasks clears only the active source; Cancel retains pending text.
`tests/test_task_count_integration.py` covers DUET/ST modal, history, units,
localization and Save/reopen. Run the documented native gate with
`QT_QPA_PLATFORM=xcb bash tools/check.sh`; no dependency changes are required.
F84 native captures and isolated-wheel evidence are described in
[task-count integration](task_count_integration.md).

## F85 — saved tool-data selection

In `--integrated-preview`, the grid button beside Reset browses saved data for the
active worker/tool in historical projects. Close preserves pending input; Load uses
existing Save/Discard/Cancel decisions. `tests/test_saved_tool_data.py` exercises
three-tool modal routing and sorting/ownership. Evidence and current Delete limits
are in [saved tool data](saved_tool_data.md) and `f85_validation.json`.

## F86 — Delete validation

The integrated task Delete buttons confirm immediate deletion of the open saved
version. No preserves pending text; Yes abandons it and clears the tool. Reset is
separate, and Delete cannot be undone. `tests/test_assessment_deletion.py` covers
modal routing, atomic rollback, exact scope, future insertion and empty projects.
See [behavior/limits](assessment_deletion.md) and `f86_validation.json`.

## F87 — menu recreation workflow

In the integrated preview, use Project > New assessment after Delete to choose an
eligible worker/assignment and explicitly create the selected tool's blank source.
Project/Edit menus expose existing assessment/history actions. Tests and current
Settings/menu/i18n limits are described in [assessment menus](assessment_menu.md)
and `f87_validation.json`.

## F88 — Tools > Settings

Use Tools > Settings for language/unit preferences. The toolbar Settings retains
original task count. Approved-environment native tests cover Cancel, invalid input,
write failure, source preservation and restart. See
[preferences scope](preferences_dialog.md) and `f88_validation.json`.

## F89 — recent-project and Close validation

Use Project > Recent projects to explicitly select an assessment in a saved
project, and Project > Close project for Save/Discard/Cancel before releasing it.
tests/test_recent_project_menu.py covers all three tools and failure/Cancel paths.
Native visual review additionally corrected empty-grid translated summary sizing.
See [behavior and current limits](recent_project_menu.md), f89_validation.json
and artifacts/f89-check.log. Next is Save As/backup.

## F90 — Save As/backup

Use Project > Save As to include validated current edits in a new file and activate
it. Backup saved project excludes unsaved edits and leaves the editor unchanged.
Existing destinations are rejected. tests/test_project_snapshots.py exercises
three-tool ownership/copy isolation, WAL, cancellation and filesystem failures.
See [behavior, visual evidence and limits](project_snapshots.md) and
f90_validation.json. Next is assessment export.

## F91 — selected-tool CSV

Export toolbar/Project menu uses saved current versions across all workers.
It preserves pending edits and includes closed-assignment identities. Status/issue
columns distinguish partial/review/invalid rows; Save first to include edits.
tests/test_summary_export.py covers scope, units, quoting, Cancel and errors.
See [CSV differences and limits](assessment_export.md) and f91_validation.json.
Next is the original worker-transfer workflow.

## F92 — Worker Transfer

The worker strip Transfer opens the original modal Copy/Move form. Copy uses saved
current data and preserves pending input; Move resolves dirty source consent before
removing selected current versions atomically. Existing destination tools reject
all writes. tests/test_assessment_transfer.py covers original-modal interlocks,
consent, three-tool preservation and rollback on the second insert. Native and
isolated-wheel checks use synthetic projects only. See
[behavior and language limits](assessment_transfer.md), f92_validation.json and
artifacts/f92-check.log. Next is remaining View/Help and preferences/language work.

## F93 — Help and About

Help menu/User Guide and Help toolbar use the packaged original PDF. About owns a
fresh original Authors dialog. tests/test_help_workflow.py covers all three tools,
repeated modal opens, invalid pending text, launcher/cache errors and partial-write
rejection. Automated checks control the viewer request; manually verify actual
viewer opening during platform acceptance. See [scope](help_workflow.md),
f93_validation.json and artifacts/f93-check.log. Next is preferences/localization
and decimal persistence; View camera animation remains renderer work.

## F94 — decimal persistence

Tools > Settings exposes independent point/comma choice. tests/test_decimal_preferences.py
covers old-convention input, Cancel/invalid Apply/save failure, all three tools,
restart and version-one read-only compatibility. Native and extracted-wheel
checks use synthetic projects only. See [compatibility and limits](decimal_preferences.md),
f94_validation.json and artifacts/f94-check.log. Next is remaining localization
review, then the original renderer View animation/preferences operation.

## F95 — localized Worker Transfer

Tests cover actual English/Spanish consent/conflicts, controls/tooltips and names
matching captions. Earlier atomic transfer regressions remain. Native and isolated-
wheel evidence use synthetic data. See [scope and native parity item](transfer_localization.md),
f95_validation.json and artifacts/f95-check.log. Next usable workflow: original
View camera animation/preferences; remaining locale/native-message gaps are recorded.

## F96 — original View animation

Use View > Animated body-region focus to enable region choreography or retain full
body. tests/test_camera_animation.py covers native mouse consent, stage targets,
manual/close cancellation, save failure, restart and old settings. Existing full-
avatar regressions select the full-body policy explicitly. Native/reference math
and independent-wheel evidence use synthetic fixtures. See [scope](camera_animation.md),
f96_validation.json and artifacts/f96-check.log. Next: original Properties/details.

## F97 — Project Properties

Project > Properties uses the original read-only 500 by 400 form. Five focused
cases cover all tools' pending input, saved defaults, repeated modal lifetime,
Spanish/long/literal values, absent legacy metadata, Save As locations and Close.
Native source-derived comparisons and isolated-wheel checks use synthetic data.
See [mapping and remaining parity](project_properties.md), f97_validation.json and
artifacts/f97-check.log. Next: original New Project metadata collection/persistence.

## F98 — project Name/Description

The integrated New path opens the original Project Details form. Twelve focused
cases cover native cancellation across tools, persistence/defaults/title,
copy/reopen, strict invalid records and unchanged old files. Full gates and native/
independent-wheel checks pass. See [workflow and format-eight limits](project_details.md),
f98_validation.json and artifacts/f98-check.log. Next: Save As prefilled details;
reference unsaved-New timing and legacy sidecars remain unfinished.

## F99 — Save As prefilled details

The integrated Save As form now prefills Name/Description and edits copy metadata.
Nine focused cases exercise three-tool Cancel and accepted source/copy isolation,
v8 replacement, SQL failure and identity/schema boundaries. Native source-derived
forms/Properties/integrated layout and independent-wheel checks pass. See
[compatibility and unfinished parity](save_as_details.md), f99_validation.json and
artifacts/f99-check.log. Next: original PLOT plant/layout selection and loading.

## F100 — original PLOT components

Fourteen focused cases characterize the original scope rules and read-only PNG/JPEG
map path, errors, resize and three-tool pending-edit isolation. Native component
comparisons and extracted-wheel checks pass; the complete PLOT window remains
unfinished and disabled. See plot_layout_components.md, f100_validation.json and
artifacts/f100-check.log. Next: persisted image import/save and original PLOT
window composition. Final full-window/platform/copied-project acceptance remains.

## F101 — explicit plant image persistence

Fourteen focused cases verify PNG/JPG import, preview/save, seven/eight/nine
compatibility, literal names, copy/reopen, real SQL rollback, invalid records and
three-tool pending isolation. Native unchanged-component captures and extracted-
wheel checks pass. See plant_image_persistence.md, f101_validation.json and
artifacts/f101-check.log. Next: original PLOT window/Open/Save integration. The
owner's CBC/HiGHS/no-GLPK JROT decision is documented; no solver dependency changed.

## F102 — original map Open/Save controls

Six new cases cover actual buttons, cancellation/errors/retry, scope consent,
localized native messages and three-tool pending isolation. Native source-region
comparisons and isolated-wheel controls/chooser/reopen checks pass. A visual error
check led to actionable localized messages and diagnostic logging. See
plot_map_controls.md, f102_validation.json and artifacts/f102-check.log. Next:
original workplace/tool filters and PLOT window composition; production remains
disabled until usable workflows are complete.

## F103 — workplace/tool regions

Eight focused cases verify actual modal intent, map/label consistency, literal and
long values, typed exclusive tools and three-tool pending isolation. Native source
comparisons/composition/resize and extracted-wheel checks pass. See
plot_filter_controls.md, f103_validation.json and artifacts/f103-check.log. Next:
original risk-view/demographic filters and Apply/Clear, then scoped result markers
and summaries. Production PLOT remains disabled until complete usable workflows.

## F104 — risk/demographics and Apply/Clear

Nine focused cases cover actual filter intent, source-compatible demographic
predicates, exact units, decimal convention, failure retention and three-tool
pending isolation. 820 tests and all required gates pass, with 96.53% coverage.
Native source/composition checks found and corrected clipped unit suffixes;
headings now carry units within the original grid. Extracted-wheel checks and
500 reference/lock hashes pass. See plot_demographic_filters.md and
f104_validation.json. Next: actual scoped assessment datasets and original
markers/summaries; production PLOT remains disabled pending complete workflows.

## F105 — actual saved PLOT result selection

Eight focused cases cover active/current ownership, hierarchy/shifts, demographics,
job counts/evidence, saved scientific gates and actual Apply with pending main
edits. 828 tests pass, 96.54% coverage; all required standards/build gates pass.
The extracted wheel matches 24 original source-SQL selections on synthetic data.
No UI layout changed; F104 visual evidence remains applicable. Reference/lock hashes
are unchanged. See plot_result_datasets.md and f105_validation.json. Next:
station/worker positions, markers and original summaries in full PLOT composition.

## F106 — station/worker positions

Fifteen focused cases cover anchor/marker semantics, exact pixel geometry, full
format upgrades, copy/reopen/map retention, SQL/schema rollback and ownership
guards. 843 tests pass, 96.58% coverage, with all required standards/build gates.
The extracted wheel matches six original position-operation states and verifies
saved geometry/results/copies. Reference/lock hashes remain unchanged. No UI
layout changed; existing visual evidence remains applicable. See
plot_position_persistence.md and f106_validation.json. Next: original markers
and move/save interactions, then overviews/summaries in complete PLOT composition.

## F107 — visible PLOT markers and position save intent

Five focused native cases cover rendering, actual mouse drag/Ctrl scale, visibility,
locks, shared station fanout, zero anchors, failure/retry/Cancel and replacement.
848 tests pass, 96.24% coverage, with all standards/build gates. Extracted-wheel
save/reopen and three source/native pixel comparisons pass; 21 captures cover
English/Spanish native states and enlargement. Reference/lock unchanged. See
plot_marker_rendering.md and f107_validation.json. Next: original worker/job
overviews and position controls, then summaries/full PLOT composition. Production
PLOT remains disabled and overall completion remains unvalidated.

## F108 — Job Placement overview workflow

Three focused cases cover selection, real typing, finite validation, navigation
locks, Save failure/retry/Cancel, zero/missing evidence, Locate and empty/literal
states. 851 tests pass, 96.30% coverage, all standards/build gates pass. Isolated
wheel overview/save/reopen and source/native empty/populated pixel comparisons
pass. Twenty-two native captures cover both languages and enlargement/map
containment; reference/lock unchanged. See plot_job_overview.md and
f108_validation.json. Next: original Worker Overview and visual/position controls,
then context handoff, summaries/full PLOT. Overall completion remains unvalidated.

## F109 — original worker visual settings and Save All

Three focused cases cover localized flag previews, actual typing, validation,
hidden/unplaced markers, single/batch save retry, atomic writer calls and empty/
job-mode controls. 854 tests pass, 96.31% coverage; all standards/build gates pass.
Extracted-wheel actual late SQL rollback/retry/reopen pass. Twenty-five native
captures verify controls and adjacent map resizing; original/populated controls
match pixel-for-pixel. Reference/lock unchanged. See f109_validation.json and
plot_worker_visual_controls.md. Next: surrounding Worker Overview, context
handoff and summaries/full PLOT. Overall completion remains unvalidated.

## F110 — Worker Overview composition

Three focused cases cover native selector/drafts, stable refresh, units, evidence
absence/zero, literal names and Locate/clear/close. 857 tests pass, 96.17% coverage;
all standards/build gates pass. Isolated wheel navigation/save/reopen passes;
three original preview captures match pixel-for-pixel. Native localized narrow/
enlarged panes and adjacent map were inspected; reference/lock unchanged. See
plot_worker_overview.md and f110_validation.json. Next: original search picker,
context handoff, summaries/full PLOT. Overall completion remains unvalidated.


## F111 — original worker search workflow

Three focused cases cover localized live search, exact hierarchy/literal shifts,
duplicate assignments, empty selection, double-click, literal tooltips and real
modal Cancel/Select with drafts and alphabet disclosure. 860 tests pass, 96.40%
coverage; all standards/build gates pass. Isolated wheel search/handoff/reopen
passes. Three original/native states match pixel-for-pixel; 25 native captures
were inspected. Reference/lock unchanged. See plot_worker_search.md and
f111_validation.json. Next: original marker context/Load Into Tool, summaries and
full PLOT. Production PLOT and overall completion remain unvalidated.


## F112 — original worker menu and integrated assessment handoff

Five focused cases cover localized menus, actual right-click, lock/save failure/
retry, pending-map block and integrated LiFFT/DUET/ST Cancel/Save/Discard with
exact ownership and recorded source preservation. 865 tests pass, 96.42% coverage;
all standards/build gates pass. Isolated wheel menu-to-editor/reopen passes. Two
source/native menus match pixel-for-pixel; localized menus and complete windows
with native VTK frames were inspected. Reference/lock unchanged. See
plot_context_actions.md and f112_validation.json. Next: summaries and full PLOT,
including parent consent/load-close composition. Production PLOT and overall
completion remain unvalidated.


## F113 — original summary calculations and figures

Five focused cases cover enabled membership, missing/zero evidence, population
deviation, paired comparison, absent metadata, units, placements and all localized
charts. 870 tests pass, 96.43% coverage; all standards/build gates pass. Isolated
wheel summary/render/no-write reopen passes. Three source/native chart fixtures
match pixel-for-pixel; the age difference is documented. Thirty-four native
captures were inspected; reference/lock unchanged. See plot_summaries.md and
f113_validation.json. Next: Tools Overview/legend/settings/viewer, then outcomes
and full PLOT. Production PLOT and overall completion remain unvalidated.


## F114 — Tools Overview, graph settings and expanded viewer

Seven focused cases cover native modal actions, saving with unfinished settings,
real click-to-expand, independent figure ownership/navigation, saved membership
vs previews, job-mode selector retention, empty clear, narrow label/title bounds,
300-DPI real file formats, suffix/Cancel and local failure handling. 877 tests
pass with 96.57% coverage; all standards/build gates pass. Extracted-wheel actual
modal/viewer/export/no-write reopen passes. Sixty-four native captures were
inspected; both source settings, three legends and focus-normalized complete
panel match pixel-for-pixel, with exact child geometry. The initial panel mismatch
was solely native focus, documented in the evidence. All reference hashes and
approved lock remain unchanged. See plot_graph_workflows.md and
f114_validation.json. Next: original outcome summary/gauges and full PLOT host,
including close/load consent and remaining map/deletion actions. Production PLOT
and overall completion remain unvalidated.


## F115 — outcome metrics, gauges and warning details

Six focused cases cover full station identity/strict threshold, saved enable vs
visibility/previews, missing/zero, actual localized warning dialog, literal names,
gauge easing/retargeting/endpoints, all modes, clear/closure and real minimum/text
bounds. 883 tests pass with 96.70% coverage; standards, architecture and builds
pass. Independent wheel modal/outcome/minimum/absence/no-write reopen passes.
Seventy-six native captures were inspected; 21 gauge fixtures and the normalized
source warning dialog match pixels exactly. Outcome width/height/wrapping changes
are documented actual clipping corrections. Reference/lock unchanged. See
plot_outcome_summary.md and f115_validation.json. Next: complete original PLOT
host, parent close/load consent and remaining map/deletion workflows. Production
PLOT and overall completion remain unvalidated.


## F116 — composed PLOT host

PlotWindow now owns the original filters/map/detail-tabs/outcome composition and
close/load consent. It remains unavailable in main navigation until remaining
map actions and deletion are connected. Native tests/captures instantiate it with
a temporary synthetic project; no operational database is used. See plot_host.md
for source mapping, actual minimum-size corrections and remaining integration.
F116 validation: 888 native tests, 96.87% combined coverage, strict mypy/standards,
architecture, wheel/sdist and independent extracted-wheel host workflows pass.
All 500 reference hashes and approved dependency lock remain unchanged.


## F117 — PLOT map view and capture workflows

The composed host now supports the original zoom/reset/opacity/capture rail
controls. Actual PNG export includes the current visible view; no project save
occurs. CSV remains disabled until its saved-worker dataset export is connected.
The source audit found no separate PLOT deletion UI; retain existing assessment
deletion in the integrated assessment screen. See plot_map_actions.md.
F117: 892 native tests, 96.88% coverage, strict standards/types, architecture,
builds, source algorithm comparisons and independent wheel map/capture checks
pass. Eighteen native artifacts inspected; reference and approved lock unchanged.
Next: CSV export and production PLOT navigation/editor integration, then JROT.


## F118 — usable PLOT in the integrated preview

Launch `.venv/bin/python -m ergotools.bootstrap --integrated-preview` in the new
project's approved environment. With an open migrated full project, the main PLOT
button now opens the original modal host. It supports map/marker/graph/outcome
workflows, saved worker CSV export and exact Load into Tool handoff. JROT remains
disabled. Only use synthetic projects or explicitly copied validation datasets.
See plot_integration.md for source mapping, CSV metadata/unit extension, original
project compatibility limits and composed VTK capture method.
F118: 898 native tests, 96.88% coverage, strict standards/types, architecture,
builds and independent wheel integrated modal/CSV/handoff pass. Reference and lock
unchanged. Next: source-based JROT characterization and exact solver dependency
proposal, retaining CBC single-tool/HiGHS multi-tool/no-GLPK.


## F119 JROT characterization — 2026-10-08

JROT exact solver approval is pending; see jrot_dependency_proposal.md. Package archives were statically inspected without executing or installing them. F118 remains the latest completed code gate; do not claim JROT functionality or compatibility from the F119 source/metadata review.


## F120 JROT optimizer — 2026-10-08

The existing locked desktop sync includes approved PuLP/CBC and highspy/HiGHS;
no extra environment or system solver installation is needed. Reproduce with the
project-local cache/install variables and `uv sync --locked --extra desktop
--python 3.13.14`. The minimal PuLP stub under typings is for development only.
Run the focused regressions with `.venv/bin/python -m pytest
tests/test_rotation_optimization.py`, and the required full gate with
`QT_QPA_PLATFORM=xcb bash tools/check.sh`. JROT UI is not yet enabled. See
jrot_optimization.md for real solve evidence and remaining integration work.


## F121 JROT saved schemes — 2026-10-08

JROT scheme persistence is available on full new-format projects; explicit first Save adds format eleven, while read is non-migrating. The form remains pending. Run focused tests/test_rotation_persistence.py with the approved interpreter; 948 native regressions and independent wheel persistence pass. See jrot_persistence.md and f121_validation.json.


## F122 original JROT scope chooser — 2026-10-08

The original JROT scope chooser is a tested component, not an enabled main feature. Native tests/test_rotation_scope.py checks controls, EN/ES, batching and no project writes. Capture comparison and independent wheel scripts are archived in docs/reference/f122-*.py.txt. 953 native tests pass. Containing scheme form integration is next.


## F123 original JROT worker/time-block grid — 2026-10-09

The original JROT worker/time-block grid is a tested component, not yet a main feature. tests/test_rotation_table.py covers actual dropdown delegates, EN/ES, units, historical pool links and a synthetic save/reopen/edit/delete workflow. Native component captures and independent wheel scripts are archived in docs/reference/f123-*.py.txt. 965 native tests pass; containing form controls are next.


## F124 original JROT scheme form — 2026-10-09

The original JROT form is directly testable as RotationDialog(repository, load_icons(), language=...), executed modally; main JROT remains disabled until optimization/comparison integration. tests/test_rotation_dialog.py verifies real buttons and native messages. Capture/wheel scripts are archived in docs/reference/f124-*.py.txt; 972 native tests pass. See jrot_form.md for exact workflow and pending actions.


## F125 selected-tool JROT optimization — 2026-10-09

Inject the approved PulpRotationOptimizer at composition to exercise selected-tool CBC in RotationDialog; manual-only callers remain valid. tests/test_rotation_solve.py covers actual CBC, preview/transfer/Save and owned cancellation/closure/failure. 982 native tests pass. Capture/wheel/evidence scripts are archived in docs/reference/f125-*.py.txt. See jrot_selected_optimization.md for bounded cancellation behavior and pending main integration.


## F126 JROT comparisons and HiGHS — 2026-10-09

992 native tests pass. tests/test_rotation_comparison.py exercises actual CBC/HiGHS comparisons, three tabs, Apply/Save/reopen, modeless child reset and all-tool cancellation/failures. Source geometry/native captures and independent wheel scripts are archived as docs/reference/f126-*.py.txt. Main JROT remains disabled pending workspace/bootstrap wiring; see jrot_comparison.md.


## F127 integrated main JROT — 2026-10-09

1003 native tests pass, 96.70% coverage. tests/test_rotation_integration.py
checks actual main-toolbar EN/ES CBC/HiGHS save/reopen, borrowed connection/format
upgrade, unfinished LiFFT/DUET/ST fields, capabilities, opener failure and safe
modal worker closure. Main JROT now enables on supported full projects. Native
main/VTK/JROT captures and extracted-wheel actual main-workflow scripts are
archived in docs/reference/f127-*.py.txt. See jrot_main_integration.md and
f127_validation.json. Legacy compatibility and comprehensive copied-project
validation are next; original operational files remain untouched.


## F128 legacy compatibility

Original XML/SQLite version-eight projects now have a tested read-only adapter.
The comprehensive copied fixture passes integrity and reference checks: 30 tables,
28 workers, 191 historical assessments, 19 risk profiles and seven JROT schemes.
Next: typed organization/worker/job/risk catalogs, then historical task sources.
No destination conversion or integrated legacy-project UI acceptance is claimed. See f128_legacy_compatibility.md and f128_validation.json for mapping, checks and remaining limits.


## F129 legacy compatibility

Original workers, organization, jobs, placements, assignments and every job-risk
profile version now map to existing immutable domain models. The comprehensive
copy validates all 28 workers, 12 jobs, 38 placements, 104 assignments, 19 profiles
and 56 measurements without source writes. Next: historical assessments/tasks and
cached evidence. Destination conversion and integrated legacy UI acceptance remain. See f129_legacy_compatibility.md and f129_validation.json for mapping, checks and remaining limits.


## F130 legacy compatibility

All 191 normalized historical assessments and 3,532 task rows in the comprehensive
copy now have a tested read-only compatibility mapping, with exact assignment/
version/current/status identity, units, source inputs, notes and cached evidence.
Next: reconcile three older records absent from normalized history, map PLOT/JROT
assets/provenance, and implement explicit atomic destination conversion before
integrated copied-project UI validation. Raw ST selector interpretation still
requires the documented scientific/UI decision; no implicit conversion is made. See f130_legacy_compatibility.md and f130_validation.json for mapping, checks and remaining limits.


## F131 legacy compatibility

The comprehensive copy now has a conflict-free recovery plan for all 194 original
assessment summaries and 3,577 task rows: 191 exact old/current matches plus three
recovered records/45 rows on their existing assignments 101, 102 and 104. Next:
PLOT companion images/geometry and saved JROT provenance, then explicit conversion.
No source or destination records are written by this read-only recovery plan. See f131_legacy_compatibility.md and f131_validation.json for mapping, checks and remaining limits.


## F132 legacy compatibility

The comprehensive copied project now maps all four exact plant images, 16 station
anchors and 100 assignment markers, with 191 raw assessment markers and original
plant display metadata retained. Next: saved JROT schemes/provenance, followed by
explicit destination conversion and integrated copied-project validation. See f132_legacy_compatibility.md and f132_validation.json for mapping, checks and remaining limits.


## F133 legacy compatibility

All seven original saved schemes now map to the established typed JROT models,
including 45 frozen target records, 179 assignment cells, exact scopes and original
manual/single-tool/all-tool provenance. Existing forms load every copied scheme in
EN/ES; actual CBC and HiGHS/Apply pass on the small saved source scheme. Next:
explicit atomic destination conversion with complete source evidence preservation,
then integrated copied-project validation. ST direction choice is still pending. See f133_legacy_compatibility.md and f133_validation.json for mapping, checks and remaining limits.


## F134 legacy compatibility

Complete typed snapshots now create a validated new-format project through a
hidden same-directory file and exclusive publication. Original approved/retired
profiles, historical ownership, PLOT images/positions and saved rotation links
survive exact read-back and reopen. Next: retain complete original XML/database
and image-name evidence; ST direction choice remains required before full source
conversion. Overall completion percentage and finish date remain unvalidated. See f134_legacy_compatibility.md and f134_validation.json for mapping, checks and remaining limits.


## F135 legacy compatibility

New-format twelve stores the exact original XML, a consistent read-only SQLite
snapshot and all referenced image bytes/names alongside the editable typed data.
Original cached results, task moments, raw selectors, timestamps, plant display
fields and schema objects remain recoverable after edits, backup and removal of
the copied source files. Next: connect an explicit converter, blocking source
conflicts and unresolved ST directions before destination creation. No reliable
overall completion percentage or finish date yet. See f135_legacy_compatibility.md and f135_validation.json for mapping, checks and remaining limits.


## F136 legacy compatibility

An explicit converter now takes an original XML project and publishes a separate
new-format-twelve repository with exact typed records and a complete source
archive. A small original-shaped project opens in the integrated application,
including recovered LiFFT, historical DUET, Worker Management, PLOT and saved
JROT. The comprehensive project currently blocks its 56 unresolved ST sources
before creating any destination. Next: review the original ST selector-to-model compatibility mapping,
then finish complete conversion and desktop Open integration. Overall percentage
and finish date remain unvalidated. See f136_legacy_compatibility.md and f136_validation.json for mapping, checks and remaining limits.


## F137 legacy compatibility

ST sources now record an explicit direction convention: existing version-one
new-format documents retain their model-code interpretation; imported original
UI sources retain their visible choices and the original 1/2 calculator swap.
All 1,650 frozen reference numerical vectors match through this mapping. No
scientific correction or owner direction answer is required for compatibility.
Next: convert all original assessments together, with source evidence intact.
Overall functional-parity percentage and finish date remain unvalidated. See f137_legacy_compatibility.md and f137_validation.json for mapping, checks and remaining limits.


## F138 legacy compatibility

The entire comprehensive project copy now converts into one new-format-twelve
file: 194 assessments/3,577 task rows, including all 56 ST sources, 28 workers,
12 jobs, 104 assignments, all 19 risk-profile versions, four maps/geometry and
seven saved JROT schemes. Reopen and backup retain exact typed records and the
complete source archive. Next: connect explicit conversion to desktop Open,
then exercise the converted copy through the integrated EN/ES workflows.
Overall full-parity percentage and finish date remain unvalidated. See f138_legacy_compatibility.md and f138_validation.json for mapping, checks and remaining limits.


## F139 legacy compatibility

The integrated main Open/recent workflow recognizes an original XML project,
asks for a separate converted-copy destination and then selects an assessment.
The destination alone enters recent history. Cancellation, existing-file and
missing-image failures retain the current workspace and unsaved source edits.
Next: comprehensive integrated copy validation. Full parity percentage and finish
date remain unvalidated. See f139_legacy_compatibility.md and f139_validation.json for mapping, checks and remaining limits.


## F140 legacy compatibility

The comprehensive project now opens through the integrated desktop as a separate
converted copy, with all 194 assessments/3,577 task rows and seven JROT schemes.
EN/ES native validation passes across LiFFT/DUET/ST, metric/imperial projection,
ST edit/undo/redo/save/reopen, Worker/Job/Organization Management, PLOT and real
CBC/HiGHS optimization followed by Apply/Save/backup. This completes the requested
F137–F140 four-milestone batch. Full-parity percentage/finish date remain unvalidated. See f140_legacy_compatibility.md and f140_validation.json for mapping, checks and remaining limits.


## F141 legacy compatibility

Converted projects now show original cached task outputs and totals in the
existing LiFFT/DUET/ST grids and result cards, explicitly marked Recorded /
Registrado. All 194 original/recovered sources are bound to their exact original
inputs. Editing hides historical evidence; undo can restore it, and saving an
edited source never makes the old result current. Fresh calculation gates remain.
Overall completion percentage and finish date remain unvalidated. See f141_legacy_compatibility.md and f141_validation.json for mapping, checks and remaining limits.


## F142 legacy compatibility

The original PLOT call path and active loadImageNew implementation were audited.
Stored Plant rotation/crop/mirror/other transform fields are not applied by that
loader. The migrated canvas matches its original pixel coordinates, scene bounds,
aspect-preserving fit, Top/Left alignment and hidden scrollbars, including resize.
Introducing dormant transforms would change the original behavior. They remain
archived for review rather than being activated. Next: readable assessment choices
and numeric inputs. Overall percentage/finish date remain unvalidated. See f142_legacy_compatibility.md and f142_validation.json for mapping, checks and remaining limits.


## F143 legacy compatibility

Integrated Open now offers tool, worker/name, complete workplace/shift and exact
version/assignment labels while keeping the stored document identity unchanged.
Narrow LiFFT/DUET/ST numeric inputs start at their leading digits, retaining full
precision and exact no-edit round trips. Existing recent-project Open, cancellation
and conversion behavior remain tested. Next: integrated comparison/visual checks
of this batch. Overall percentage and finish date remain unvalidated. See f143_legacy_compatibility.md and f143_validation.json for mapping, checks and remaining limits.


## F144 legacy compatibility

The F141–F144 batch completes historical result display, active-original PLOT
loader characterization, readable assessment selection and precise numeric
input display. Recorded outputs now use original tool palettes for task cells,
result cards and the avatar. Pending text immediately hides the previous recorded
outputs; repeated refreshes preserve the gauge animation target. Comprehensive
EN/ES workflows are validated on separate converted copies. Overall percentage
and finish date remain unvalidated; this is four milestones, not final acceptance. See f144_legacy_compatibility.md and f144_validation.json for mapping, checks and remaining limits.


## F145 implemented workflow

Fresh metric LiFFT now uses the characterized domain calculator through the
application service and reusable result presenter. Original normalization,
rounding and legacy moment-display arithmetic remain unchanged; this is behavioral
compatibility, not scientific certification. Missing/invalid inputs, source-unit
provenance, history and failure handling remain explicit. C1 gains usable-workflow
credit after frozen references, Calculate/Save/reopen and native checks pass. See f145_compatibility.md for evidence and limits.


## F146 implemented workflow

ST Calculate now runs the existing characterized calculator through the typed
application service, honoring each document's recorded direction convention.
The task grid, result cards, gauge and replaceable body renderer consume typed
results; calculation and unit policy stay outside Qt. C3 gains G3 usable-workflow
credit: overall fixed-scope progress is 73.25/100 (approximately 73%). See f146_compatibility.md for evidence and limits.


## F147 implemented workflow

Saved summary exports now preserve exact-source archived results with explicit
recorded status. The read-only application contract checks source equality before
using evidence; edited sources take the characterized fresh calculator path.
No calculation is run for an unchanged archived source. Per-assessment recorded
units are retained, including DUET's labels independent of project defaults.
This closes CSV compatibility within B1's existing G3 credit; no extra scope
points are claimed simply for completing another checkpoint. See f147_compatibility.md for evidence and limits.


## F148 implemented workflow

The copied comprehensive project now completes fresh Calculate, edit, undo/redo,
Save, CSV export and reopen across LiFFT, DUET and ST. All 194 sources evaluate
without mutation: 103 complete and 91 partial grids. The native integrated
scenario also saves/cancels/reopens a worker edit, opens PLOT, runs actual CBC and
HiGHS optimization, applies/saves a multi-tool rotation, and verifies backup,
archive retention and unchanged original inputs. G3 gains its usable-integration
gate: fixed-scope progress is 74/100 complete and 26/100 remaining. See f148_compatibility.md for evidence and limits.


## F149 implemented workflow

F149 verifies the reported main-window clipping without changing the application's
layout or behavior. Full-resolution F148 PNGs contain the labels and regions that
appeared absent in combined previews; R007 was not an established application
layout defect. The record is corrected rather than adding repaint callbacks.
The application wheel remains byte-for-byte identical to F148. Overall scope
progress remains 74/100 complete and 26/100 remaining; no final gate is awarded. See f149_compatibility.md for evidence and limits.


## F150 implemented workflow

Explicit Save now commits the current successful LiFFT/DUET/ST calculation with its unchanged or edited source in one SQLite transaction. Reopen/export prefer that exact-source saved result while the original archive remains separately readable and unchanged. Save As writes current results into the copy before adoption. Focused native pending-input and storage-failure regressions pass. Overall fixed-scope progress remains 74/100; final B1/C4 acceptance still needs its remaining lifecycle/navigation comparisons. See f150_compatibility.md for evidence and limits.


## F151 implemented workflow

LiFFT and DUET controls were compared by executing the original form-building methods in an isolated harness under the approved Qt baseline, without importing the original application's startup or touching its database. Headers, column/control types, DUET rating labels, button icons and matched parent-container captures now have direct source-based evidence. The measured DUET Calculate icon mismatch was corrected from 26 to the original 28 pixels. Overall scope progress remains 74/100; this checkpoint closes comparison subcriteria, not complete C1/C2 final acceptance. See f151_compatibility.md for evidence and limits.


## F152 implemented workflow

ST's Calculate icon now matches the original 28-pixel asset treatment. Original ST headers, column control types and direction selector labels are compared directly under the approved Qt baseline. The expanded Open assessment picker now uses the existing management/JROT styled delegate, fixing selected white text painted on a white background. EN/ES native selected/expanded states, all 194 captions, exact selection identity, modal behavior and cancellation pass. Overall scope remains 74/100; C3/C4 final workflow and full original-window acceptance are not claimed complete. See f152_compatibility.md for evidence and limits.


## F153 implemented workflow

Save during document/context/project transitions now uses the same atomic source/result persistence as explicit Save. An injected owner-thread result provider supplies only the active exact-source calculation after the target has been validated. No new background processing or modal ownership changes. All three tools pass switch Save, unchanged ownership/reopen, Save As success and retained-session failure acceptance. Current fixed-scope progress stays 74/100 while final lifecycle and original-window acceptance remains. See f153_compatibility.md for evidence and limits.


## F154 implemented workflow

Restored the original integrated inline totals for DUET and the original 13px/15px labels, risk backgrounds, rounded corners and luminance-based foreground for LiFFT and DUET. The original constructors hide totals, but refreshAssessmentSummary/styleToolResultSummary/alignToolSummary show them on the live result path. The previous empty-space interpretation was incomplete. A small typed, documented presentation component now owns those repeated controls; panels still own evaluation and exact-source historical selection. Progress remains 74/100; this bounded comparison does not claim complete-window G4 acceptance. See f154_compatibility.md for evidence and limits.


## F155 implemented workflow

Restored the original integrated ST inline totals using the same documented presentation component as LiFFT/DUET. Fixed an observed unit-label defect: switching display units projected ST inputs but also relabeled unchanged source-unit moments. The moment header now follows source/result units, matching the established LiFFT policy. The reference direction selectors and their calculator mapping remain unchanged. Current fixed-scope progress remains 74/100; full original-window and cross-feature final acceptance is still open. See f155_compatibility.md for evidence and limits.
