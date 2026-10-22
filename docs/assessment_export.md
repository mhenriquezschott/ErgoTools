# F91 — saved assessment summaries to CSV

Project > Export selected tool to CSV and the original Export toolbar action
export saved current versions of the selected tool for all workers. Export never
commits pending editor text, saves the active project, changes units/preferences,
switches source or modifies Undo history. Save first to include current edits.
No-data, Cancel and failures retain the current editor. The existing styled file
chooser has a CSV filter/suffix; menu/toolbar reuse the packaged Export asset.

Read-only application rows carry exact document/assignment/worker/workplace
ownership. Current versions on closed assignments remain under their original
owner; older noncurrent versions are excluded. A separately owned project
connection supplies saved data, and existing evaluators derive summaries.
LiFFT/DUET use their established completed-row grid calculation: unused slots
retain completed-row totals with explicit partial status. Invalid inputs and
scientific review gates have absent results, never fabricated zero risk.
Metric LiFFT and ST direction/metric review gates remain unchanged.

The writer emits reference-compatible UTF-8 BOM, standard CSV quoting and CRLF.
It closes a same-directory temporary file before exclusive publication. Existing
destinations, including files created during publication, cannot be overwritten.
Ordinary failures remove temporary files. Hard-link filesystem support is
required; power-loss durability and Windows/macOS acceptance remain uncertified.

## Reference comparison and recorded differences

The working reference main.py exportToCSV reads saved WorkerStationShiftErgoTool
summaries for the selected tool across all workers. Its first eleven English
headers and workplace/worker ordering are retained. The new format stores source
data rather than that legacy cached-summary table, so export derives results from
saved sources through the same migrated calculation boundary as the grids.

Project/assessment/assignment IDs, version, assignment-active flag, evaluation
status and issue keys are appended to distinguish historical ownership and
unavailable/partial results. No context is trimmed or merged. CSV headers and
machine identifiers remain stable across UI languages; UI captions/messages are
localized. Unit uses recorded source enum IDs (project defaults for unit-independent
DUET). Display-unit preferences do not rewrite exported source units.

Damage retains full model float precision instead of reading a four-decimal UI
label. Probability Outcome is model probability multiplied by 100 and rounded to
one decimal, without the legacy display-bound clipping to 0/100. None exports as
an empty cell. These documented data-format changes are not changes to formulas
or final legacy CSV parity. Consumers should read status/issue columns before
treating a row as complete. PLOT/JROT/legacy import/report exports are not included.

## Evidence and next workflow

Eight focused cases cover three-tool scope and pending preservation, toolbar
Cancel/failure, saved ownership, metric review, invalid source, Unicode/quoting,
no-data and blank-slot partial totals. Existing navigation regression now expects
Export enabled only in supported projects. Visual error checking exposed inherited
harness word wrapping in the integrated status bar; keeping it on one line avoids
compressing the avatar caption. Error status geometry is checked.

The required native gate passes with 711 tests, 96.63% combined coverage, strict
mypy on 144 source files, lint/format, architecture and both builds. Native
English/Spanish populated/disabled menus, selected CSV picker, all three pending
editor/Export routes, no-data and existing-target error states were inspected.
Avatar, cards, headers, captions and bottom controls remain visible at 1550 by
1015. VTK framebuffers use the existing composed capture method.

An isolated extracted wheel verifies three-tool saved CSV scope, closed-assignment
identity, unchanged pending/source/settings, scientific gates and native cleanup.
All 500 reference hashes and the approved lock remain unchanged. Only synthetic
projects were used. Evidence: f91_validation.json, artifacts/f91-check.log,
artifacts/summary-export/ and archived reference/f91-capture.py.txt,
f91-picker-capture.py.txt and f91-verify.py.txt.

Next is the original worker-transfer workflow. Full Settings/localization,
View/Help, project-details/legacy sidecars, scientific review, remaining renderer
features, PLOT/JROT and final copied-project/platform acceptance remain. The former
67% estimate remains withdrawn; overall percentage and finish date are unvalidated.
