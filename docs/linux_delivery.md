# Current owner-requested Job change — verified, 2026-10-20

Native format 19, one current Job/tool risk set, compact persistent calculators and
independent exact worker assessment copies are implemented. Root dist wheel/source
packages are rebuilt; the byte-identical wheel passes 181 focused tests outside source
with converter imports blocked. Required native Linux gate: 1984 passed, 94.33% coverage,
standards/types/documentation/builds pass. All three maintained native fixtures are
updated in place. See job_management_simplification_acceptance.md and its validation.

Use the current project launcher below or root dist packages. The frozen dist/linux
bundle further below is historical and does not contain this follow-up. No parallel
maintained fixtures are introduced. Windows/macOS acceptance remains deferred.

---

# ErgoTools Linux delivery

This is the integrated LiFFT/DUET/ST/PLOT/JROT desktop, validated on Ubuntu 25.04
x86-64 using XCB/XWayland and the approved Python 3.13.14 baseline. It contains
its own icons, avatar models, guides and calculation/storage code. The original
checkout is neither installed nor needed. Native Windows/macOS acceptance is
not included in this Linux delivery; see the platform review and M12 status.

## Run the existing new project

From the new project folder:

```bash
bash tools/run.sh
```

This launches the integrated application with VTK. Preferences now default to
Qt's per-user application configuration directory rather than the launch folder.
To reuse the prior development preferences explicitly:

```bash
bash tools/run.sh --settings "$PWD/.cache/desktop_settings.json"
```

The installed console command is `ergotools`; the equivalent module command is
`python -m ergotools.launcher`. `--disable-vtk` remains diagnostics only.
The old bootstrap and its preview flags remain diagnostic compatibility paths;
their historical help description does not define the delivered UI.

## Current development packages and frozen delivery bundle

The 2026-10-18 single-project-Save correction rebuilds and independently verifies the
wheel/source archive directly under `dist/`. The existing `dist/linux/` bundle remains
a frozen earlier delivery snapshot; regular `tools/check.sh` does not republish it.
Use `tools/run.sh` for the current workspace, or the verified current root `dist/`
wheel for an independent installation with the same approved requirements. Current
behavior/evidence is in [single project Save acceptance](single_project_save_acceptance.md).

## Install independently on Linux x86-64

Use the already approved uv 0.11.25 and exact Python/library baseline. These
instructions do not authorize upgrading versions. In a new writable installation
folder, copy the delivered wheel and runtime-linux-requirements.txt here, then:

```bash
uv python install 3.13.14 --install-dir "$PWD/python" --no-bin --no-registry
uv venv --python "$PWD/python/cpython-3.13.14-linux-x86_64-gnu/bin/python3.13" .venv
uv pip install --python .venv/bin/python --require-hashes -r runtime-linux-requirements.txt
uv pip install --python .venv/bin/python --no-deps ./ergotools-0.1.0.dev0-py3-none-any.whl
.venv/bin/ergotools
```

Initial installation can require network downloads. The requirement export
contains exact approved versions and distribution hashes, with no development
tools or editable source requirement. The clean test used a separately copied
approved interpreter and a fresh environment, downloaded only hash-approved
distributions, and ran the installed program with external networking disabled.
This delivery is not an offline wheelhouse or a self-contained OS image.
After installation, the application, both solvers and packaged guides operate
offline; a working native Qt/X11/OpenGL system remains necessary. Only this
tested Linux host is claimed, not every Linux distribution.

Do not move an already created virtual environment: recreate it at the new
location using these same pinned files. The installed script's absolute shebang
belongs to that environment. All Python/library and solver version changes need
explicit approval. Desktop dependency markers intentionally target Linux; do
not use this requirements file to assert Windows/macOS compatibility.

## Use and recovery

Launch from any folder; package assets do not depend on the current directory.
Use `--settings /absolute/path/settings.json` for a separate preference file.
The original-project Open workflow offers the external upgrade and opens a
temporary native copy until first Save. Original descriptor/database/images
remain unchanged outside the new file. Preserve original sidecars until conversion. Format-15 projects embed all images and a single native calculation per assessment; they contain
no original-schema archive. Earlier format-12/13 files need the external one-time upgrade.

Use the main Save before Backup to include accepted changes from all project editors.
Backup copies persisted data only. To restore, retain the current file separately,
Open a separately named backup and inspect workers/contexts, all assessment tools,
PLOT image/markers and JROT schemes before Save As. Undo histories/preferences
are not part of a project backup. Keep backups; project history can reverse accepted deletion only during the open project session.

The installed offline acceptance reopened a disposable copy of the comprehensive
converted original project, exercised Backup, matched complete SQL dumps and all
owned catalog/history/PLOT/JROT/native result data, and reopened the backup in Spanish.
CBC handles one tool; HiGHS handles all tools. GLPK is not included.

Current EN/ES Help ships inside the wheel. Full user, developer, architecture,
API and recovery documentation is in the source distribution's docs/ folder.
The migration evidence is in docs/m01_acceptance.md through m12_validation.json
as applicable. M12 is accepted for Linux; the owner explicitly deferred native
Windows/macOS acceptance, which remains unexecuted.

## Open a project from the command line

The original positional-project convention is supported:

```bash
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
```

From an independent installation, use `ergotools "/absolute/path/project.ergprj"`.
Quote paths containing spaces. Relative paths are relative to the terminal's
current directory, even when the launcher script lives elsewhere. The normal
original-project conversion dialogs still apply; native projects automatically load an available assessment;
startup does not automatically Save. Successful opens enter Project > Recent
projects (Proyecto > Proyectos recientes), up to ten paths, newest first.
Cancelled or failed opens are not added. Clear History removes only menu history.

The current comprehensive fixture contains assessments, PLOT and JROT data.
Use Save As for a personal review copy; the fixture needs no companion folders.
`test_projects/native/integrated_test.ergprj` is the second converted dataset.
Earlier M10 artifact files are historical checkpoints, not current fixtures.

Cleanup M1 separates old-project conversion into the removable
`tools/project_migration` utility. See its README and
[M1 acceptance](cleanup_m1_acceptance.md). The current installed wheel excludes
conversion code. Guided migration and separate original/native fixture organization
are accepted in M2; comprehensive per-symbol documentation completion is M4. All six cleanup milestones are now accepted for Linux; owner acceptance testing
can use the current native fixtures and final delivery package.

M1R supersedes M1's result policy: external conversion recalculates saved inputs;
native storage keeps one result per assessment with calculator precision.
UI formatting/gauge limits do not round stored values. The regenerated comprehensive
projects are in `test_projects/native`; see its README and cleanup_m1r_acceptance.md.
Historical artifacts/guides describe their earlier checkpoints and are not current
test datasets. M1/M1R/M2/M3/M4/M5 are accepted. Final inventory, package hashes and Linux
validation are recorded in cleanup_m5_acceptance.md and cleanup_m5_validation.json.

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
Cleanup M4/M5 are complete; the native fixtures are ready for owner testing.

## Final cleanup delivery — M5

All six cleanup milestones are accepted for Linux. The refreshed `dist/linux`
folder contains the current wheel/source archive, exact pinned runtime requirement
export, `INSTALL.md`, checksum list, both current single-file review projects and
an optional `tools/project_migration` directory. The main application wheel contains
no converter. The exported dependency file is unchanged from the approved M12
baseline; M5 refreshed only application code/documentation artifacts.

After the installation commands above, from that installation folder:

```sh
.venv/bin/ergotools "test_projects/native/comparative_risk_test.ergprj"
.venv/bin/ergotools "test_projects/native/integrated_test.ergprj"
```

Use Save As before experimenting with the supplied fixtures. Each has 194 saved
assessments/results and four embedded images; they contain seven and five
JROT schemes respectively. The 91 partial results in each reflect unfinished input
rows, not conversion errors. All 194 results in each match current evaluation.

The optional `ergotools-migrate` wrapper delegates to the separate utility using
this installation's `.venv`; it does not install dependencies. To enable in-app
Migrate discovery, add the delivery folder to PATH for that launch:

```sh
PATH="$PWD:$PATH" .venv/bin/ergotools
```

Or run the independent converter directly:

```sh
.venv/bin/python tools/project_migration/migrate_project.py "/path/original.ergprj" --output "/path/new_project.ergprj"
```

Remove the wrapper and `tools/project_migration` when old-project conversion is
no longer needed. Native Open/Save/Backup/PLOT/JROT continue without them. Keep
original source sidecars separately as reference evidence, never beside a native
project as a runtime requirement. See cleanup_m5_acceptance.md for exact final
checks, inventory, coverage limits and known sample-project limitations.

## Current optional organization contract

Native format 16 supports direct worker assessment ownership with an optional real
workplace assignment. Jobs are optional for PLOT Individual analysis; JROT All Jobs
remains independent of individual assessments and organization. New projects create
no artificial defaults or orphan assessment. Existing Default names are retained.
See [ownership, UI, migration and rollback](optional_assessment_context.md).


The owner-approved 2026-10-18 [single project Save](single_project_save.md) supersedes
older instructions to save inside management, PLOT or JROT windows. Main Save writes
all accepted content; Save As includes it, while Backup copies the last saved baseline.

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
