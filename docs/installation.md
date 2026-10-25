# Install and launch ErgoTools

[Back to the README](../README.md#installation)

ErgoTools runs locally as a desktop application. Installation downloads Python and
libraries; ordinary assessments and optimization work offline afterwards. A graphical
session, working OpenGL driver, and a writable project folder are required.

| Platform | Setup | Validation |
| --- | --- | --- |
| Linux x86-64 | Locked desktop environment | Native GUI, VTK, CBC and HiGHS verified on Ubuntu 25.04 |
| Windows 10/11 x64 | Separate pinned trial requirements | Package resolution checked; native installation, GUI and solvers await testing |
| macOS 11+ Intel / Apple silicon | Separate pinned trial requirements | Package resolution checked for both architectures; native installation, GUI and solvers await testing |

Use **CPython 3.13.14** and **uv 0.11.25**. Python 3.10 instructions from older
branches do not apply to this codebase. Windows ARM64 is not a native trial target.
On Apple silicon, use an arm64 Terminal/Python throughout, without mixing Intel
packages. A virtual environment belongs to its installation path: recreate it if
you move the checkout.

## Get Git and uv

Install [Git](https://git-scm.com/downloads) and the pinned
[uv installer](https://docs.astral.sh/uv/getting-started/installation/).
If Git and uv are already available, skip their installers. On macOS, `git --version`
may offer Apple's Command Line Tools installation; finish that first.

**Windows — PowerShell:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.11.25/install.ps1 | iex"
```

**macOS / Linux — Terminal:**

```bash
curl -LsSf https://astral.sh/uv/0.11.25/install.sh | sh
```

Reopen the terminal after installation and check:

```text
git --version
uv --version
```

The commands below select the required Python explicitly; there is no need to
activate the environment or change the system Python. Run them in a normal user
terminal, in a folder you own.

## Linux

```bash
git clone --branch main --single-branch https://github.com/mhenriquezschott/ErgoTools.git
cd ErgoTools
uv python install 3.13.14
uv sync --locked --no-dev --extra desktop --python 3.13.14
bash tools/run.sh
```

Optional project argument:

```bash
bash tools/run.sh "test_projects/native/comparative_risk_test.ergprj"
```

The desktop needs the distribution's OpenGL and Qt/XCB system libraries. If startup
reports a missing shared library, use its exact name to identify the relevant OS
package; reinstalling Python libraries does not supply system X11 drivers.
See [independent Linux installation and recovery](linux_delivery.md) for wheel-based
delivery. A Git clone does not contain generated `dist/` packages.

## Windows trial

The project's `desktop` extra currently has Linux-only markers. Consequently,
`uv sync --extra desktop` alone does **not** install the Windows GUI. These steps
install the editable application first and then the explicit trial libraries:

```powershell
git clone --branch main --single-branch https://github.com/mhenriquezschott/ErgoTools.git
cd ErgoTools
uv python install 3.13.14
uv sync --locked --no-dev --python 3.13.14
uv pip install --python .venv\Scripts\python.exe --only-binary :all: -r tools\requirements_desktop_trial.txt
.\tools\run_windows.cmd
```

Check that each command succeeds before continuing. This uses PyQt5 **5.15.11**
with Qt **5.15.2**, explicitly approved for the Windows trial: Qt **5.15.17** has
[Linux/macOS wheels but no Windows wheel](https://pypi.org/project/PyQt5-Qt5/5.15.17/#files).
Other runtime versions match the Linux baseline. The separate
[trial file](../tools/requirements_desktop_trial.txt) leaves `uv.lock` and the Linux
environment intact. It requests wheels only; do not work around an unavailable
wheel by upgrading packages or compiling a different Qt.

### Desktop shortcut

In File Explorer, locate `ErgoTools\tools\run_windows.cmd`. On Windows 11, use
**Show more options → Send to → Desktop (create shortcut)**; on Windows 10,
use **Send to → Desktop (create shortcut)**. Rename the shortcut **ErgoTools**.
Double-click it to launch. Keep the script inside the checkout: a shortcut points
to it; a copied script on the desktop would look for the wrong environment.

The launcher selects this checkout's Python and needs no environment activation.
A console remains available for startup errors. You can also pass a quoted project
path from a terminal:

```powershell
.\tools\run_windows.cmd "C:\Users\YourName\Documents\ErgoTools projects\example.ergprj"
```

## macOS trial

```bash
git clone --branch main --single-branch https://github.com/mhenriquezschott/ErgoTools.git
cd ErgoTools
uv python install 3.13.14
uv sync --locked --no-dev --python 3.13.14
uv pip install --python .venv/bin/python --only-binary :all: -r tools/requirements_desktop_trial.txt
chmod +x tools/run_macos.command
./tools/run_macos.command
```

The trial uses the same exact library versions as Linux, including Qt **5.15.17**.
Package resolution has been checked for Intel and Apple silicon; that does not
establish successful native rendering or solver execution. Do not mix architectures
or install the older branch's Conda/requirements environment on top of this one.

### Desktop alias

In Finder, locate `ErgoTools/tools/run_macos.command`, choose **File → Make Alias**,
and move the **alias** to the Desktop. Rename it **ErgoTools**. Keep the original
`.command` file inside `tools`; double-click the alias to launch in Terminal.
This avoids a new Terminal command or environment activation at every launch.

If macOS blocks a downloaded executable, review it and use the normal per-item
**Open** / **Privacy & Security** approval. Do not disable Gatekeeper globally.
To keep a startup error visible, run the command in an already open Terminal.

```bash
./tools/run_macos.command "/Users/YourName/Documents/ErgoTools projects/example.ergprj"
```

## Update the code

Save your project and close ErgoTools first. From the checkout:

```bash
git pull --ff-only origin main
```

Your desktop shortcut/alias launches the updated editable source. It does not pull
code, install libraries or save a project by itself. Keep your own projects outside
the checkout so updates cannot replace example files you have edited.

If dependency metadata changed, repeat your platform's environment commands.
On Windows/macOS, repeat **both** `uv sync` and the trial `uv pip install` command:
`uv sync` removes libraries that are outside the Linux-marked desktop extra.
Do not run `uv sync` by itself there and expect the GUI dependencies to remain.
If Git reports local changes or a non-fast-forward update, stop and inspect them;
these instructions never reset local work.

## First-launch check

1. Launch without `--disable-vtk`; confirm the body model is visible and can rotate.
2. Open a personal copy of `comparative_risk_test.ergprj`. Review LiFFT, DUET and ST.
3. Open PLOT and check the plant image, charts and Individual/Job/Comparison views.
4. Open JROT; run a selected-tool solve (CBC), then an all-three solve (HiGHS).
5. Save As to a new file, close, reopen and verify its data. Check native file dialogs,
   language switching, units and display scaling on your machine.

These are the native Windows/macOS checks still to be performed. Report OS version,
CPU architecture, `uv --version`, Python version and the exact error if startup fails.
Use the platform checklist for the fuller acceptance review.
