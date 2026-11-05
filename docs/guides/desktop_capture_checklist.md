# ErgoTools Windows/macOS deployment and capture checklist

Companion to the **5 November 2026, 26-page Windows/macOS user guide**. This is a
native deployment trial: record what succeeds and what fails. The guide's reference
illustrations are not evidence that ErgoTools has passed on your computer.

## Before starting

1. Create a **free GitHub account**, verify its email and sign in to GitHub Desktop.
   You need the account for this guide's Desktop route and for reporting issues.
2. Use Windows 10/11 **x64** (prefer Windows 11), or a Mac with matching Intel/Apple
   silicon tools. GitHub Desktop requires macOS 12+. Windows ARM64 is not this trial.
3. Follow the PDF commands exactly, one at a time. Keep the clone on `main`, in a
   stable local folder such as `~/ErgoTools-code/ErgoTools`. Keep personal projects
   outside it. Do not copy a virtual environment from another computer.
4. Make `ErgoTools-test-evidence` in your home folder. Inside it, use `windows/` or
   `macos/`, with `screenshots/`, `logs/`, `diagnostics/` and `projects/` subfolders.
5. Use sample identities. Do not capture passwords, tokens, recovery codes, private
   email, real worker records or unrelated notifications. Account/setup screens
   should be captured before entering secrets, or sanitized afterward.

## How to capture and record results

- Save **original PNGs at native resolution**. Do not resize or annotate the originals.
  Leave enough surrounding UI to identify the window and action. For small controls,
  supply both a whole-window capture and a focused crop if helpful.
- Keep the OS's normal scaling. Record resolution, scaling percentage and monitors;
  do not change them merely to make a capture look better. If testing another scale,
  label the before/after pair and restart the app when appropriate.
- Use the filename IDs below, for example `W06-python-install.png`. Add `-error`
  when the action fails. Retain the **complete error as text**, not just a screenshot.
- For each ID record **Pass / Fail / Not run**, OS/build/architecture, date, exact
  action, expected/actual result and filenames. Keep the installed full commit SHA
  from GitHub Desktop **History > Copy SHA**, Python version and `uv --version`.
- An update may offer no changes. Record **Already up to date**; do not create a dummy
  commit, push anything, change branches or deliberately corrupt the installation.
- PDF page numbers below refer to this edition. Capture both the action and its
  visible result when these cannot fit in one image.

## Windows captures

**Core** items are the minimum useful set for rewriting the guide with tested Windows
screens. **Extra** items improve troubleshooting and feature coverage.

| ID / suggested PNG name | PDF page | Priority | Capture and expected result |
|---|---:|---|---|
| W01-system | 2, 15 | Core | Settings > System > About: Windows edition/build and x64 architecture. Hide device IDs/serials. Also capture Display with resolution and scale. |
| W02-account-desktop | 1, 4 | Core | GitHub Desktop installed and signed in; capture its ordinary repository view, not credentials. Note any browser authorization or installer steps that differed. |
| W03-repository-main | 5 | Core | Browser at `github.com/mhenriquezschott/ErgoTools`, repository name and `main` visible. |
| W04-clone-dialog | 6 | Core | Desktop > File > Clone Repository > URL, `https://github.com/mhenriquezschott/ErgoTools.git`, chosen local path. Then capture the completed clone with ErgoTools / main / clean Changes. |
| W05-uv-setup | 7 | Core | Normal PowerShell: installer command/result, then a newly opened PowerShell showing `uv --version`. No administrator shell is required. |
| W06-python-install | 8 | Core | Repository prompt, `uv python install 3.13.14` and result. Include the actual clone path or note it separately. |
| W07-environment-sync | 8 | Core | `uv sync --locked --no-dev --python 3.13.14` result. Preserve the full output in a text log if it scrolls. |
| W08-desktop-libraries | 8 | Core | Trial-requirements install command and result. This is separate from sync and installs the graphical libraries. |
| W09-first-launch | 8 | Core | PowerShell running `.\tools\run_windows.cmd`, followed by main ErgoTools with **3D avatar visible**. Note elapsed launch time, warnings or clipping. |
| W10-shortcut-create | 9 | Core | Explorer `tools` folder with `run_windows.cmd`; desktop shortcut creation dialog or Send to > Desktop route. Capture the resulting shortcut and its Properties target. |
| W11-shortcut-launch | 9 | Core | App closed first, then launched by that shortcut. Confirm it opens the same clone and project. Do not copy the launcher out of `tools`. |
| W12-fetch-pull | 13 | Core | Desktop showing ErgoTools/main, Fetch origin and, if offered, Pull origin. Capture clean completed state; note Already up to date if no update exists. |
| W13-refresh | 14 | Core | Run **both** environment commands after an update requiring dependencies, then use the same desktop shortcut successfully. Record skipped refresh if no relevant update is available. |
| W14-history | 15 | Core | Desktop History with latest local commit selected and Copy SHA context action; put the full SHA in the test notes. |
| W15-issue-search | 17 | Core | Browser repository Issues and search for an example symptom. No need to open an issue. |
| W16-issue-draft | 18–19, 22 | Core | New issue form with a clearly marked **unsubmitted training draft**, reproduction steps and a sanitized screenshot preview. Close/discard it afterward. Report a real bug only when intended. |
| W17-snipping | 20 | Extra | Windows + Shift + S / Snipping Tool selection and saved PNG. Capture any different Windows 11 save behavior. |
| W18-diagnostics | 24 | Core | ErgoTools > Edit > Settings > General, Display diagnostics report/folder controls; folder containing newest JSON. Include the JSON with the evidence. |
| W19-explicit-report | 23–24 | Extra | Close app, then launch from PowerShell with the explicit diagnostics folder command below. If startup fails, keep console text and any report produced. |
| W20-app-windows | 25 | Core | Main LiFFT/DUET/ST with populated test tasks, Job Management, Organization and PLOT. Show full windows, avatar, gauges, bottom controls and any scaling problems. |
| W21-project-roundtrip | 25 | Core | Open a bundled test project, **Save As** a copy under evidence/projects, close and reopen that copy. Note that data/results persist and the bundled file is unchanged. |
| W22-import | 14, 25 | Extra | Import a CSV/XLSX/XLSM: worksheet/range, column mapping, included/skipped rows and resulting tasks. Test accents using the sample below. |
| W23-optimization | 25 | Core | Run the known-answer check below and capture selected tools, matrix/indices, then keep/save/reopen and confirm the result persists. |

Windows commands copied from the guide (PowerShell in the repository):

```powershell
uv python install 3.13.14
uv sync --locked --no-dev --python 3.13.14
uv pip install --python .venv\Scripts\python.exe --only-binary :all: -r tools\requirements_desktop_trial.txt
.\tools\run_windows.cmd
```

Optional explicit report folder; close ErgoTools first:

```powershell
.\tools\run_windows.cmd --startup-diagnostics --diagnostics-dir "$HOME\ErgoTools-test-evidence\diagnostics"
```

## macOS captures

Use the same procedure, privacy rules and result record. These captures must come
from a real Mac; Linux renderings cannot substitute for Finder, Terminal or macOS.

| ID / suggested PNG name | PDF page | Priority | Capture and expected result |
|---|---:|---|---|
| M01-system | 2, 10, 15 | Core | About This Mac: macOS version and Intel/Apple silicon; System Settings > Displays: resolution/scaling and monitors. Hide serial number. |
| M02-account-desktop | 4 | Core | GitHub Desktop installed in Applications and signed in, using the matching processor download. No credential screens. |
| M03-clone | 5–6 | Core | Browser repository/main, Desktop URL clone dialog/local path and completed clone. |
| M04-uv | 10 | Core | Terminal installer command/result, reopened Terminal `uv --version`. |
| M05-environment | 11 | Core | Python install, locked sync and trial requirements install, with complete text logs. |
| M06-first-launch | 11 | Core | `chmod +x tools/run_macos.command`, launch and main app with real avatar. Note any security approval steps without bypassing organizational controls. |
| M07-alias | 12 | Core | Finder tools folder, Make Alias action, desktop alias, successful double-click launch. Retain the original launcher inside the clone. |
| M08-update | 13–15 | Core | Fetch/Pull or Already up to date, full local SHA, dependency refresh when needed and successful alias launch. |
| M09-issue-draft | 17–19, 22 | Core | Issues search and unsubmitted training draft with sanitized attachment. |
| M10-screenshot | 21 | Extra | Shift + Command + 4, or +5 options, saved screenshot file and actual PNG format. |
| M11-diagnostics | 24 | Core | Settings report/folder controls and JSON in `~/Library/Logs/ErgoTools`, or explicit folder below. |
| M12-app-checks | 25 | Core | Same main/Jobs/PLOT, project roundtrip and known-answer optimization checks as Windows; record each separately. |
| M13-import | 14, 25 | Extra | CSV/XLSX/XLSM range/mapping/skip rows and correct pasted tasks with accented names. |

macOS Terminal, in the repository:

```bash
uv python install 3.13.14
uv sync --locked --no-dev --python 3.13.14
uv pip install --python .venv/bin/python --only-binary :all: -r tools/requirements_desktop_trial.txt
chmod +x tools/run_macos.command
./tools/run_macos.command
```

Optional explicit report folder; close ErgoTools first:

```bash
./tools/run_macos.command --startup-diagnostics --diagnostics-dir "$HOME/ErgoTools-test-evidence/diagnostics"
```

## Application checks and known answer

Work on a **private Save As copy** of
`test_projects/native/jrot_workflow_optimization_test01.ergprj`.

- Main tools: confirm task inputs, results, anatomy and all controls are legible.
- Jobs/Organization/PLOT: open populated windows, resize normally and record any
  clipping, missing graphics or wrong cursor/display behavior.
- JROT: choose **Test 01 · Equal blocks — 3 workers / 3 Jobs**, LiFFT only,
  three 160-minute blocks and no worker restrictions. Run optimization.
  The job risks are 0%, 50% and 100%. A balanced optimum gives **50.00 for each
  worker**, because each receives each Job once across equal blocks. Each column
  must contain each Job exactly once. A different equally optimal ordering is valid.
- Keep the optimization result, Main Save, close/reopen the private project and
  verify the kept result. This checks both solver installation and persistence.
- Optionally run a populated multi-tool example with LiFFT/DUET/ST selected to
  exercise all-tool execution. Record tools, durations, restrictions and results;
  do not compare it against the single-tool answer above.

Optional UTF-8 CSV for import (save outside the code folder):

```csv
Task name,Lever arm (cm),Load (N),Repetitions
Empaque Ñ,30,49,100
Carga café,45,98.1,200
```

Map the four input columns to LiFFT, choose metric **cm / N**, exclude the header
and import into a private sample assessment. Names and input values should match,
including `Ñ` and `é`. Calculated columns must not be mapped as inputs. Then test
Undo and confirm the pasted rows/names are reversed after the removal warning.
For Excel files choose the actual sheet/range; macros are not run and formulas are
not recalculated by import. Keep the test workbook or a sanitized reproduction.

## What to return

Return the PNG folder, test notes with Pass/Fail/Not run per ID, full code SHA,
complete command/error logs, startup JSON and sanitized sample files needed to
reproduce failures. A ZIP of the evidence folder is convenient. Keep credentials,
virtual environments and confidential project data out of it.

Suggested result row:

| ID | Status | OS / scale | Code SHA | Action / actual result | Evidence |
|---|---|---|---|---|---|
| W09 | Not run | Windows 11 x64 / 125% | full SHA | First launch | W09-first-launch.png; logs/launch.txt |

Record any missing or outdated guide steps in the notes. The returned real OS
captures will replace reference illustrations in the next guide revision.
