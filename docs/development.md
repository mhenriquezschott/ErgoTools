# Current JROT meeting prototype — 2026-10-21

Use test_projects/native/jrot_workflow_demo.ergprj and docs/jrot_meeting_demo.md for
the clean six-worker walkthrough. The isolated prototype owns new read-only pickers
and free review navigation; readiness gates calculations only. The reviewed removable
tools/create_jrot_demo_project.py builder uses current APIs and refuses an existing
output. No production/schema/dependency changes or prototype writes. Latest basic
native/package/visual evidence: jrot_prototype_meeting_validation.json.

---

# Session-only JROT developer prototype — 2026-10-20

Enable Settings → General → Enable Developer Menu for this session, Apply, then open
Developer Menu → JROT workflow prototype…. English/cm/N; inputs disappear on close.
No schema or production JROT change. See jrot_prototype.md for exact capabilities,
limitations and the owner-approved basic-test/native-inspection exception to a repeated
full gate. Hands-on production Job/workplace tests remain paused.

---

# Current owner-requested Job simplification — 2026-10-20

Native format 19 replaces Job profile/evidence storage with one current row per Job/tool.
Use existing application calculators; do not recreate formulas in the compact widgets.
Independent worker copies preserve exact task inputs and all matching calculated outputs.
The Job window borrows shared project history and the sole main Save. Retained closed
JROT drafts must refresh current Job numbers before staging, preventing stale optimization
provenance from being written back. See job_management_simplification_decisions.md and
database_tables.md. Historical format-18 notes below are superseded for current schema.

---

# Development and reproducibility

Use the new project exclusively. The reference tree, its Conda environment and
operational projects are read-only migration evidence. See [architecture](architecture.md),
[standards](coding_standards.md), [API contracts](api_contracts.md) and
[current cleanup ledger](cleanup_progress.json). Historical F instructions are archived in
[development checkpoint history](development_checkpoint_history.md); they do not
describe today's supported workflow.

## Run the current application

From the new project root:

```bash
bash tools/run.sh
```

The launcher selects the complete shared desktop and VTK renderer. Add
`--disable-vtk` only for isolated renderer-free checks. `--settings /path/file.json`
chooses a separate preference file; the diagnostic bootstrap defaults to `.cache/desktop_settings.json`, which is
project-local for diagnostic bootstrap. The delivered launcher instead uses Qt's
per-user AppConfigLocation. Preferences store language/units/decimal mark/recent paths and
camera animation independently of project data.

The no-flag LiFFT screen, `--original-lifft-controls`, `--job-management PATH`,
`--job-management-demo` and `--job-language en|es` remain diagnostic harnesses.
They are not alternate product UIs or final acceptance targets. Do not create
operational data in a demo. CLI `--help` documents exact retained options.

## Approved environment

Python **3.13.14**; Ruff **0.16.9**, mypy **2.3.1**, pytest **9.1.1**, pytest-cov
**7.1.0**, Hatchling **1.32.4**. Approved Linux desktop includes PyQt5 **5.15.11**,
Qt **5.15.17**, PyQt5-sip **12.17.0**, VTK **9.5.0**, Matplotlib **3.10.5**, NumPy
**2.2.6**, PuLP **3.2.2**, bundled CBC **2.10.3** and highspy/HiGHS **1.11.0**.
The complete exact transitive baseline and hashes are in uv.lock. CBC is for
single-tool optimization; HiGHS is for all-tool optimization. No GLPK.

Use the existing `.venv` normally. Recreate only when necessary, with the already
installed uv manager (0.11.25 on this machine) and approved versions:

```bash
uv python install 3.13.14 --install-dir "$PWD/.python" --no-bin --no-registry --cache-dir "$PWD/.cache/uv"
UV_PYTHON_INSTALL_DIR="$PWD/.python" UV_CACHE_DIR="$PWD/.cache/uv" UV_LINK_MODE=copy uv sync --locked --extra desktop --python 3.13.14
```

These commands may require network access for already approved distributions;
they are instructions, not a claim that clean/offline installation passed M12.
Do not upgrade uv, Python or any library as an incidental troubleshooting step.
Windows/macOS environments need actual target/version approval and VM validation.

## Verification and changes

```bash
QT_QPA_PLATFORM=xcb bash tools/check.sh
```

The gate runs Ruff, formatting, strict mypy, architecture/naming rules, complete
documentation structure and source-hash review inventory checks, pytest with
statement/branch coverage (minimum 90%), then wheel/sdist builds. Reports are in
artifacts/ and builds in dist/. Use a native Linux display for XCB/VTK checks;
offscreen runs verify Qt logic but do not establish native rendering parity.
Run focused regressions while developing and the required full gate once the
changed slice is ready. Reuse valid evidence; do not repeat checks without a
change/failure/unresolved criterion. Inspect changed UI states at original and
enlarged sizes. Screenshots verify code-derived layout, not a new design.

Use small synthetic fixtures first, and only disposable comprehensive copies for
integration. Frozen reference fixtures must not be regenerated merely to pass a
test. Original-source hashes and data preservation are recorded separately from
the new Python baseline. M10's accepted wheel passed full copied-project workflow
and original calculation comparisons; see m10_acceptance.md.

Build verification extracts the wheel and imports in isolated `-I` mode, with the
extraction taking precedence over src/. Verify every ergotools module is loaded
from that extraction. Assets are package-owned via importlib.resources; installed
code must not require the reference checkout or current directory for resources.

The mounted repository is independent and uncommitted; no push/deployment is
configured. For ownership warnings use command-local
`git -c safe.directory="$PWD" status`; do not modify global Git settings.

## Data and documentation

New-format projects own SQLite data, embedded image bytes and a single native
calculation per assessment version. Original files remain outside the native
project. Settings and transient Undo histories are separate. See recovery.md.
External guide launching uses Qt local URLs and an atomic platform cache; no
shell/browser process or network resource is required by the HTML guide.
User-guide Markdown and packaged EN/ES HTML are ordinary reviewed files, with no
new documentation framework. Keep their content synchronized; M11's source text
is archived in reference/m11-guide-source.py.txt.


## M12 delivery

Use [Linux delivery](linux_delivery.md) for an installed wheel and launcher, and
[platform review](platform_review.md) for executed versus deferred native checks.
The approved baseline remains exact; M12 changed entry-point metadata, not versions.

## Open a project from the command line

The original positional-project convention is supported:

```bash
bash tools/run.sh "artifacts/m10-integration-final/run/M10-validated.ergprj"
```

From an independent installation, use `ergotools "/absolute/path/project.ergprj"`.
Quote paths containing spaces. Relative paths are relative to the terminal's
current directory, even when the launcher script lives elsewhere. The normal
assessment-selection and original-project conversion dialogs still apply;
startup does not automatically Save. Successful opens enter Project > Recent
projects (Proyecto > Proyectos recientes), up to ten paths, newest first.
Cancelled or failed opens are not added. Clear History removes only menu history.

The comprehensive converted fixture above includes assessment, PLOT and JROT
data and integration-test edits. `M10-backup.ergprj` beside it is its saved backup.
Use Save As for a personal review copy. The similarly named XML original-project
descriptor in that folder is a copied conversion input, not the converted file.

## Analysis selections and keyboard history — owner-approved extension

Main assessments, PLOT and JROT use Edit > Undo/Redo and platform-standard
shortcuts (verified Linux desktop: Ctrl+Z and Ctrl+Shift+Z; use the
bindings displayed in the Edit menu on your platform). Focused text editors retain native
typing history, including when it is empty; modal dialogs do not replay the main
assessment history. Task-grid rebuilds retain document shortcuts without keeping
references to deleted input widgets.

PLOT uses one chronological session for marker edits and analysis configuration.
Apply records the accepted demographic setup, including its enabled flag, sex and
all canonical bounds. Disabled, unpaired and reversed bounds are retained exactly
even when they do not constrain the effective dataset. Tool selection, accepted
workplace selection, Clear and immediate risk-mode Apply are also reversible.
Tool selection still requires Apply to update results, preserving the existing
workflow. Undo restores both the selected controls and the applied dataset.
Replay reuses saved result projections from this modal session and reloads scope
images through existing consent/failure policy. Rejected scope restoration leaves
the history cursor unchanged. Geometry uses the same session and saved baseline;
analysis changes alone do not make saved map geometry dirty or write the project.

JROT history includes the displayed risk tool, All Jobs/workplace selection mode,
accepted pending workplace selections, applied scope/frozen pool, grid and applied
optimization provenance. Accepting the scope chooser and subsequently pressing
Apply are separate steps. Cancelled selection adds none. Undo of pending choices
does not rebuild them from current database records or change the applied pool.
Existing solver ownership disables replay until the owned solve finishes.

History supports multiple steps with no configured count limit, while the editing
session exists. A new accepted edit after Undo clears Redo; no-ops and rejected
operations retain it. Save is explicit and does not add a history entry. History
is not persisted across application/modal close or JROT scheme load/New/Cancel.
Confirmed deletions, transfers, file effects and management commits are not made
globally reversible by this extension.

All existing Save/Save All controls remain. Moving saving to the main UI and adding
arrow controls are later decisions; neither is implemented in this extension.

Cleanup M1 separates old-project conversion into the removable
`tools/project_migration` utility. See its README and
[M1 acceptance](cleanup_m1_acceptance.md). The current installed wheel excludes
conversion code. Guided migration and separate original/native fixture organization
are accepted in M2; comprehensive per-symbol documentation completion is M4. User acceptance
testing remains on hold until the six approved cleanup milestones close.

M1R supersedes M1's result policy: external conversion recalculates saved inputs;
native storage keeps one result per assessment with calculator precision.
UI formatting/gauge limits do not round stored values. The regenerated comprehensive
projects are in `test_projects/native`; see its README and cleanup_m1r_acceptance.md.
Historical artifacts/guides describe their earlier checkpoints and are not current
test datasets. M3–M5 remain unstarted; owner testing stays held through documentation.

## Guided original-project upgrade — cleanup M2

Opening an earlier project explains why it needs an upgrade and offers **Migrate**
or **Cancel** (English/Spanish). It also shows a copyable command for the separate
utility. Migrate runs that external process; no converter code enters the app.
Keep original database/image folders together until conversion succeeds. Missing
tools/assets, unsupported schemas or invalid data leave the current workspace open
and show the tool error. Cancel does not start conversion. No automatic retry.

The converted project opens in temporary native storage. Use the main **Save**
action, choose a new `.ergprj` file and confirm the prefilled project details.
Original date/language/default units are retained; current display units/language
do not reinterpret task data. Cancelled/failed first Save keeps the temporary copy
open for retry. Closing/switching asks Save/Discard/Cancel even when its current
assessment is clean. Discard removes the temporary copy. An application/system
crash before first Save can lose that temporary copy; the original remains intact.

Temporary files never enter Recent Projects. After first Save, only the permanent
native file is needed: it embeds every plant image and all supported data, including
PLOT/JROT relationships. The ordinary New-project pre-save restrictions are reused;
Save first before management/PLOT/JROT/export. During this temporary stage the
existing New-project header says no project loaded; the bottom message explicitly
identifies the upgraded copy and requests Save. No unrelated header redesign.

For command-line conversion instead of the GUI:

```sh
.venv/bin/python tools/project_migration/migrate_project.py "/path/original.ergprj" --output "/path/new_project.ergprj"
```

The CLI publishes directly to its explicit new destination. For installed-wheel
users, retain the separately supplied `tools/project_migration` folder and invoke
its script with the approved environment, or expose an `ergotools-migrate` wrapper
on PATH forwarding the same arguments. The app detects that optional command;
without a tool it still opens all current native projects. Do not reinstall or
upgrade dependencies to run the converter. See its README for supported formats.

Current fixtures: `test_projects/native/comparative_risk_test.ergprj` and
`test_projects/native/integrated_test.ergprj`. Originals and sidecars are separate
byte-identical reference copies in `test_projects/originals`. The two other original
samples still have documented schema/metadata limitations; no repair was added.
User acceptance stays held through cleanup M4/M5.

## Documentation review workflow

Keep file layer/scope and function purpose, Args, Returns/Yields, errors, units and
effects accurate during a change. Run the focused source checker before the full
gate; `python -m tools.check_documentation path/to/file.py` accepts selected files.
Use the project interpreter `.venv/bin/python`, including for tool commands.
After substantive review, explicitly record the changed file's reviewed SHA-256 in
`docs/cleanup_documentation_reviews.json`, then regenerate the inventory with
`.venv/bin/python -m tools.check_documentation_review --refresh-inventory`.
A refresh cannot approve unreviewed files. See coding_standards.md for the exact
policy; never waive the check by stamping current hashes without reviewing prose.


## Current display/Settings acceptance follow-up

See display_settings_acceptance.md and display_settings_validation.json. Focused
regressions are in tests/test_display_preferences.py and test_vtk_body_renderer.py;
existing tool integration tests now require simultaneous sibling overlays. Compact
input text is not evidence of source rounding: assert source_text and domain state.
When changing display precision, test unrelated-field edits, units, typing Undo,
reopen and snapshots. Native confirmation checks must inspect processed icons and
Cancel default. Keep the existing standards/documentation review gates mandatory.

## Current optional organization contract

Native format 16 supports direct worker assessment ownership with an optional real
workplace assignment. Jobs are optional for PLOT Individual analysis; JROT All Jobs
remains independent of individual assessments and organization. New projects create
no artificial defaults or orphan assessment. Existing Default names are retained.
See [ownership, UI, migration and rollback](optional_assessment_context.md).


## Assessment gauge marker verification

The owner-approved marker controls are documented in gauge_markers_acceptance.md.
Focused checks: tests/test_gauge_markers.py, test_settings.py, test_preferences_dialog.py,
test_camera_animation.py and test_decimal_preferences.py. Personal settings format 5
retains read support for versions 1-4; this is independent of native schema 16.
Test independent visibility, off-grid 37.5 boundaries, custom interval limits,
Cancel and failed persistence, restart, untouched source/needle animation and the
old gauge interior. Inspect native EN/ES menus, Settings with/without a project,
and integrated LiFFT/DUET/ST at metric/imperial display sizes before acceptance.
The existing integer/end-limit animation issue is separately recorded in the
review register; do not silently repair it as marker work or claim its endpoint
value/needle behavior visually passed.


## Shared gauge and Settings follow-up

Use tests/test_settings_navigation_theme.py for production main/PLOT composition,
shared persistence and failure retention, EN/ES section navigation and the system
chooser exception. RiskGauge owns both layout profiles; PlotRiskGauge must not
acquire another painter. Inspect Settings with/without a project in every section,
main LiFFT/DUET/ST, PLOT Individual/Job/Comparison, marker menus and owned interval
prompts. System file/color/font dialogs retain platform defaults: never force Qt
fallback or apply the application dialog helper to them. Automated checks assert
configuration at the chooser boundary; native Open/Cancel and Save selection remain
manual platform verification after restart. See settings_shared_gauge_acceptance.md.

## PLOT/JROT/context layout regressions

Use existing test_plot_window, test_plot_outcome, test_plot_history,
test_rotation_history, test_optional_assessment_context and test_main_navigation
scenarios. Inspect EN/ES Individual/Job/Comparison before and after demographic
expansion at minimum/enlarged sizes; verify the entire Plant View rail, plot axis
labels, graph selector/descriptions/legend/settings, outcome gauges and bottom edge.
Job mode intentionally hides the worker chart selector; do not assert its stale hidden
geometry against visible widgets. PLOT's QGraphicsView keeps both scrollbars off.
Verify title-row Undo/Redo clicking and native typing/shortcuts retain ownership,
including solver interlocks. Context tests must use the separate standalone button,
zero fake hierarchy rows for an organization-free worker and no standalone option in
association-only pickers. See plot_layout_followup_acceptance.md.


## Single project Save acceptance

The integrated composition enables ProjectWorkspace(unified_saving=True). Direct native
repositories and diagnostic harnesses retain their existing explicit-write contract.
Test accepted private data separately from the last saved .ergprj; main Save must work
without an active assessment. Tests may not seed the durable file behind an open private
session: use workspace ports and an explicit setup Save instead. Focused regressions
are test_unified_project_save.py and test_unified_analysis_save.py. Include real SQLite
commit failure/retry, Save As/Backup, removal consent cancellation, native typing and
closed-editor subscription teardown. See single_project_save.md for exact scope.

## Shift metadata follow-up — 2026-10-19

Current source and root `dist/` packages use native format 17. The recurring Shift
contract excludes `incidents_reported` and `ergonomic_risk_events`; earlier full
native formats 8–16 use the optional external conversion workflow. Formats 14–16
retain exact source/result payloads. The maintained native fixtures and four-worker
workflow were updated in place, with unrelated tables preserved exactly. Frozen
M5 `dist/linux` delivery evidence is historical and has not been republished here.
See [current acceptance](shift_metadata_removal_acceptance.md).

## Organization input cleanup — format 18, 2026-10-19

Current source/root dist packages use format 18. Optional organization dates use
standard calendars; daily operational duration uses hour/minute quantities while
retaining decimal-hour storage. Six Station attributes and the editable Plant shift
count are removed. Shifts in use is a Plant-specific read-only count of distinct shifts used by active
Job placements or worker workplace assignments; unused definitions do not count. Formats 8–17 use the existing external converter;
formats 14–17 retain exact tasks/results. Both maintained fixtures and the four-worker
workflow were updated in place, unrelated rows exact. Historical frozen dist/linux
acceptance is not republished here. See
[acceptance](organization_input_cleanup_acceptance.md).


## Workplace-first workflow — 2026-10-19

Use tests/test_workplace_assignment_workflow.py with the existing worker/optional-context
checks for workplace-first selection, optional Job filtering, existing-owner reuse,
rollback after assignment insertion, cancellation, shared replay and exact all-tool
result preservation. Use disposable copies for native English/Spanish UI verification;
never seed or modify the owner's open workflow project. Native format remains 18.


## Workplace assignment table sizing — 2026-10-19

The existing test_workplace_assignment_workflow module contains synthetic compact,
long-label, many-row and empty table cases in both languages. Verify full headers and
values, the selector's actual native edit-field width (not only its size hint), both
scroll directions, reachable Actions/last row and shrinking after clearing. Native
font/style differences may change whether a minimum-size viewport overflows; compare
actual columns with available space instead of forcing the same scrollbar everywhere.
Qt supplies arrow/text/cell geometry; do not replace it with equal-width columns or
font-specific padding guesses. No current project needs migration.


## Workplace table refinement regressions — 2026-10-19

In the existing workflow test module, assert that fitting columns exactly occupy the
viewport after show/resize/clear, and that widening expands Job without inflating
Station. Test the selector's actual text field and complete action-button rectangles
in both dimensions; table padding reduces embedded widget space. Native hover checks
use QHelpEvent for data/header/Job/action targets. Column descriptions are localized,
user values literal, and the table itself has no generic tooltip. The owned single-shot
fit timer coalesces viewport changes and must settle without creating history/Save
changes. Calendar/directory event filters remain independent. Use private copies only.


## Explicit assessment context creation — 2026-10-19

Worker/context regressions cover multiple assignments added before management closes,
no automatic assessment activation, exact Create/Open actions, all three tools in EN/ES,
cancellation, private state versus durable Save/reopen, shared removal consent and
Undo/Redo, same-Job consent and exact standalone input/result preservation. Use existing
synthetic workflow fixtures and private copies for native captures. Native format stays
18 and maintained test projects require no migration. See
explicit_context_creation_acceptance.md for the current bounded workflow correction.
