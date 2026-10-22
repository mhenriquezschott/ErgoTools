# Original command-line project workflow restored

The owner identified this original behavior as missing after Linux closure and
reaffirmed the approved Recent Projects requirement. This is a bounded parity
correction, not an extra milestone, dependency or point increase. Linux scope
remains 100/100; Windows/macOS native acceptance remains explicitly deferred.

The original main.py accepts optional positional project_file and calls
openFilePath. The new launcher now accepts the same positional convention:

```bash
bash tools/run.sh "artifacts/m10-integration-final/run/M10-validated.ergprj"
```

Installed: `ergotools "/path/project.ergprj"`. Relative paths use the terminal's
working directory; quote spaces. Opening runs after show through the existing
Open conversion/assessment-selection/error policy. It never automatically Saves.
Conflicting Job Management diagnostic targets are rejected before creating a GUI.

Project > Recent projects / Proyecto > Proyectos recientes already existed;
no replacement menu was introduced. Up to ten successful Open/Save paths are
remembered newest first. Cancellation/failure does not add startup paths; the
existing missing-file/forget, clear-history and dirty-draft policies remain.
Clear History affects preferences only, not project files. Current per-user
launcher settings are separate from historical diagnostic project-local settings.

Eighteen focused source tests pass, including spaced relative paths, real project
Open, recent persistence, cancellation, missing file and conflicting diagnostics.
The required complete gate passes **1,232 tests, 96.51% coverage**, Ruff/format,
strict mypy (240 source/tool files), architecture and wheel/source builds.
The independent extracted wheel passes **34 tests and 77 subtests**, with all
application imports confined to that wheel; 237 Python files and both current
Help guides match source. Linux wheel/instructions/checksums are refreshed.

Native Linux XCB startup uses the real launcher, VTK and a disposable comprehensive
copy with a spaced path. The actual selection dialog is accepted automatically;
the application selects a real saved assessment and persists the recent path.
Five captures were inspected: empty Recent Projects, complete English/Spanish
main window with VTK/cards/bottom controls, and populated EN/ES Recent Projects.
Project bytes remain identical after startup/language/menu use. Prior conversion,
calculation, PLOT/JROT and larger-window evidence remains valid and reused.

All 500 reference-manifest files and the approved lock are unchanged. No reference
or operational project was edited. Earlier M12 hashes/counts describe its accepted
historical build; [current validation](cli_project_validation.json) identifies
the corrected delivery. Guides now explain both startup and Recent Projects.

Evidence: artifacts/cli-project-check.log, cli-project-wheel.log,
cli-project-package.json and cli-project-native/verification.json.

Current owner-approved history extension and delivery hashes: [analysis history acceptance](analysis_history_acceptance.md), [validation](analysis_history_validation.json). Earlier evidence remains historical.
