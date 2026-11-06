# Install and launch ErgoTools

[Back to the README](../README.md#installation) · [Illustrated PDF guide](guides/ergotools_installation_and_github_guide.pdf) · [Copyable commands](guides/installation_commands.md)

ErgoTools runs locally on Windows, macOS and Linux. Use Python **3.13.14** and
**uv 0.11.25** with the repository’s pinned libraries. A graphical desktop,
working OpenGL drivers and a writable project folder are required.

| Platform | Prepare |
| --- | --- |
| Windows | Windows 10/11 x64, PowerShell |
| macOS | Intel or Apple silicon; use matching architecture throughout. GitHub Desktop requires macOS 12+. |
| Linux | x86-64 graphical desktop, Git, curl and Qt/XCB/OpenGL system libraries |

Create a [GitHub account](https://github.com/signup) for GitHub Desktop and bug
reports. [GitHub Desktop](https://desktop.github.com/download/) can clone/update
Windows and macOS checkouts without a separate command-line Git installation.
For the terminal route below, install [Git](https://git-scm.com/downloads).

## Clone the code

In GitHub Desktop: **File → Clone Repository → URL**, enter
`https://github.com/mhenriquezschott/ErgoTools.git`, select a stable local folder,
and clone. Confirm the branch is **main**. Use **Show in Explorer/Finder** to find
the checkout. Run installation commands from that folder.

Alternatively, in a terminal:

```bash
git clone --branch main --single-branch https://github.com/mhenriquezschott/ErgoTools.git
cd ErgoTools
```

Keep your own `.ergprj` files outside this checkout. A `.venv` belongs to its
installation location; recreate it if the checkout moves.

## Windows

Install uv in a normal PowerShell window:

```powershell
powershell -ExecutionPolicy ByPass `
  -c "irm https://astral.sh/uv/0.11.25/install.ps1 | iex"
```

Close and reopen PowerShell. Enter the checkout folder (`cd "your actual path"`),
then run each block in order:

```powershell
uv python install 3.13.14
```
```powershell
uv sync --locked --no-dev --python 3.13.14
```
```powershell
uv pip install --only-binary :all: `
  --python .venv\Scripts\python.exe `
  -r tools\requirements_desktop_trial.txt
```
```powershell
.\tools\run_windows.cmd
```

The Windows libraries use PyQt5 5.15.11 and Qt 5.15.2; Qt 5.15.17 has no Windows
wheel. Keep the provided versions.

In Explorer, right-click `tools/run_windows.cmd` → **Show more options → Send to →
Desktop (create shortcut)**. Rename the shortcut **ErgoTools**. Keep the original
script inside `tools`; copying just the script to the Desktop breaks its environment
lookup. The shortcut continues to work after code updates in the same checkout.

## macOS

Install uv in Terminal:

```bash
curl -LsSf https://astral.sh/uv/0.11.25/install.sh | sh
```

Open a new Terminal, enter the checkout folder, then run:

```bash
uv python install 3.13.14
```
```bash
uv sync --locked --no-dev --python 3.13.14
```
```bash
uv pip install --only-binary :all: \
  --python .venv/bin/python \
  -r tools/requirements_desktop_trial.txt
```
```bash
chmod +x tools/run_macos.command
./tools/run_macos.command
```

Finish Apple’s Command Line Tools installation if prompted. The full Xcode app is
not required. If uv reports a Python library-patching error before those tools were
available, complete the tools installation and run `uv python install 3.13.14 --reinstall`,
then repeat the environment commands. A normal rerun can simply say “already installed.”

In Finder, right-click `tools/run_macos.command` → **Make Alias**. Move only the
alias to the Desktop and rename it **ErgoTools**. Keep the original launcher in
`tools`; double-click the alias to start the app in Terminal.

## Linux

Install uv, then reopen your terminal:

```bash
curl -LsSf https://astral.sh/uv/0.11.25/install.sh | sh
```

From the checkout:

```bash
uv python install 3.13.14
```
```bash
uv sync --locked --no-dev --extra desktop --python 3.13.14
```
```bash
bash tools/run.sh
```

Install your distribution’s Qt/XCB/OpenGL system libraries if a missing shared-library
error identifies one. The [PDF guide](guides/ergotools_installation_and_github_guide.pdf)
includes an optional application-menu launcher. See [Linux delivery](linux_delivery.md)
for independent wheel installation and recovery.

## Update

Save your projects and close ErgoTools. In GitHub Desktop use **Fetch origin**, then
**Pull origin** if offered. Or, from the checkout:

```bash
git pull --ff-only origin main
```

Repeat your platform’s environment commands before launching. On Windows/macOS,
run **both** `uv sync` and the desktop requirements command, in that order: sync can
remove GUI libraries outside its core selection. Linux uses `--extra desktop`.
The desktop shortcut/alias keeps working; it launches code but does not download updates.
If Git reports local changes or a non-fast-forward update, inspect them before proceeding.

## Check the installation

1. Open a personal copy of a bundled sample from `test_projects/native`.
2. Check the 3D anatomy and task inputs for LiFFT, DUET and ST.
3. Open PLOT and check the plant image, charts and view modes.
4. Run a fresh single-tool and multi-tool optimization in JROT.
5. Save your copy outside the checkout, reopen it and check a known input/result.

Microsoft Excel is not needed for importing CSV, TSV, XLSX or XLSM cell values.
Workbook formulas are not evaluated; use stored cell values. Older `.xls` files
must be converted to a supported format.

## Report a problem

Use [GitHub Issues](https://github.com/mhenriquezschott/ErgoTools/issues), or
GitHub Desktop → **Repository → Create Issue on GitHub** to open that page in your
browser. Include the commit (Desktop History → Copy SHA), OS, display scaling,
reproduction steps and screenshots.

Windows/macOS launch logs are enabled by default; Linux can enable them with
`bash tools/run.sh --startup-diagnostics`.

| OS | Diagnostic folder |
| --- | --- |
| Windows | `%LOCALAPPDATA%\ErgoTools\diagnostics` (Explorer address bar) |
| macOS | `~/Library/Logs/ErgoTools` (Finder → Go → Go to Folder) |
| Linux | `$XDG_STATE_HOME/ergotools/diagnostics`, or `~/.local/state/ergotools/diagnostics` |

Settings → General → Display diagnostics → **Open report folder** opens the folder.
Choose the report from the failing launch. Review paths/identifiers before sharing,
ZIP the `.jsonl` file and matching rotated sibling when present, and attach that ZIP.
The [guide](guides/ergotools_installation_and_github_guide.pdf) covers screenshots,
console capture and attachment steps. See [display diagnostics](settings_previews_and_diagnostics.md)
for technical details.
