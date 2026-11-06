# ErgoTools installation command companion

Use with the [illustrated PDF guide](ergotools_installation_and_github_guide.pdf).
Run commands from the checkout folder, one block at a time. `$HOME` fills in your
own username. If your clone is somewhere else, replace the quoted checkout path
with its actual location (GitHub Desktop → Show in Explorer/Finder).
Do not copy a terminal prompt. Keep continuation characters at the ends of lines.

## Windows / PowerShell

Clone through GitHub Desktop → File → Clone Repository → URL:
`https://github.com/mhenriquezschott/ErgoTools.git`.
Suggested checkout: `$HOME\ErgoTools-code\ErgoTools`.

Install uv, then close and reopen PowerShell:

```powershell
powershell -ExecutionPolicy ByPass `
  -c "irm https://astral.sh/uv/0.11.25/install.ps1 | iex"
```
```powershell
cd "$HOME\ErgoTools-code\ErgoTools"
```
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

## macOS / Terminal

Clone through GitHub Desktop using the same URL. Install uv and open a new Terminal:

```bash
curl -LsSf https://astral.sh/uv/0.11.25/install.sh | sh
```
```bash
cd "$HOME/ErgoTools-code/ErgoTools"
```
```bash
uv python install 3.13.14
```

Finish the Apple Command Line Tools prompt if shown. If Python's patching failed
before those tools were installed, finish them and run:

```bash
uv python install 3.13.14 --reinstall
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

## Linux / terminal

```bash
mkdir -p "$HOME/ErgoTools-code"
git clone --branch main --single-branch \
  https://github.com/mhenriquezschott/ErgoTools.git \
  "$HOME/ErgoTools-code/ErgoTools"
```
```bash
curl -LsSf https://astral.sh/uv/0.11.25/install.sh | sh
```

Open a new terminal, then:

```bash
cd "$HOME/ErgoTools-code/ErgoTools"
```
```bash
uv python install 3.13.14
```
```bash
uv sync --locked --no-dev --extra desktop --python 3.13.14
```
```bash
bash tools/run.sh
```

## Updates

Save and close the app. Fetch/Pull main in GitHub Desktop, or run:

```bash
git pull --ff-only origin main
```

Then repeat the platform's sync and desktop-library commands above. On Windows/macOS,
**both** sync and pip steps are needed. Keep personal projects outside the checkout.

## Console evidence

Windows (PowerShell in checkout):

```powershell
$env:PYTHONFAULTHANDLER = "1"
.\tools\run_windows.cmd
```
macOS:

```bash
PYTHONFAULTHANDLER=1 ./tools/run_macos.command
```
Linux:

```bash
PYTHONFAULTHANDLER=1 bash tools/run.sh --startup-diagnostics
```

Keep the terminal open and copy its error text to `console.txt`. Review private
paths/identifiers before attaching a ZIP to a GitHub issue.
