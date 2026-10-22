# First runnable LiFFT desktop preview — F28, 2026-09-29

**Owner clarification (2026-09-30): this is a temporary development harness. Its layout and Apply/Discard workflow are not the final UI target. The final application must retain the existing integrated UI/workflows; see [final targets](final_targets.md).**

Launch from the new project root:

```bash
.venv/bin/python -m ergotools.bootstrap
```

Optional `--settings /path/to/settings.json` chooses the separate recent-project settings file. The default is `.cache/desktop_settings.json` under the launch directory. Start from this project to keep preview data local. Choose new temporary `.sqlite` projects; this preview does not import legacy operational files. New never overwrites an existing file.

## Implemented scope

A Qt view, widget-independent LiFFT presenter and composition root connect the tested source/history, unit projection, numeric input, evaluation and workspace adapters. Domain/application remain Qt-free. Asset bytes are injected from packaged resources; the window does not locate the reference checkout or open SQL connections.

The screen supports new/open/save, selection among saved LiFFT documents, add/remove task, one-field arm/load/repetition editing, undo/redo, source/display units, independent decimal convention and English/Spanish application labels. It displays current aggregate damage/probability, input issues and metric scientific-review status. Results clear when source changes; changing display units does not rewrite source. Repetition edits use the existing atomic task replacement command.

Pending text has an explicit policy: Apply or Discard before changing selection, units, decimal convention, language, history, project or calculation. The controls are disabled while pending, and close is rejected with a visible instruction. Invalid input remains visible for correction. Blank explicitly clears a field. Dirty committed source uses Save/Discard/Cancel on close/switch. Errors retain edits; adapter exceptions are logged and shown without raw data. Detached connection cleanup is retried before exit.

The read-only task table displays original/full-precision projected inputs. Full text is also available as a tooltip and in the editor. There are no derived per-task moment/damage/contribution columns yet. Large values may scroll/elide in cells; source precision is retained. Toolbar history works; keyboard history shortcuts remain pending. Reset-all is not exposed; row removal is undoable.

## Approved environment

The owner approved the exact Qt proposal with “ok go.” Added only Linux desktop-extra pins PyQt5 5.15.11, PyQt5-Qt5 5.15.17 and PyQt5-sip 12.17.0; all prior locked versions remain identical. Python remains 3.13.14. The runtime reports PyQt 5.15.11, Qt runtime 5.15.17 and SIP package 12.17.0. PyQt's compiled `QT_VERSION_STR` reports 5.15.14; this differs from the loaded runtime and is recorded rather than misreported as an installation mismatch.

Recreate the approved environment with the existing manager using `uv sync --locked --extra desktop --python 3.13.14`, with project-local cache/install paths as documented in development.md. No VTK, WebEngine, solver, pytest-qt, fonts or system libraries were installed. Linux is the only desktop-extra target approved/tested so far.

## Visual verification

Qt offscreen and native XCB rendering both work. The host exposes a 2560×1440 desktop; Segoe UI resolves to Cantarell. No font installation was made. The audited navy/teal palette, panel borders, focus treatment and processed icons were applied. Redo remains a text action because a processed Redo icon is absent. File dialog filesystem navigation uses Qt's built-in folder/drive symbols where no project asset exists; Save/Open/Cancel use project assets. Selection actions use styled text instead of unrelated stock icons.

Actual native screenshots were captured and inspected at 1200×780 and 960×680: empty, populated (25 rows), selected/scrolled, Spanish metric display with decimal comma, invalid pending input, expanded unit dropdown and metric review. New-file, source-unit and dirty-close dialogs were inspected too. A clipped Spanish field selector was found, widened to 190px and recaptured. Adjacent result cards and bottom editor/status controls fit at both tested sizes. No avatar exists in this slice, so no VTK acceptance is claimed.

Evidence images are under `artifacts/desktop/`: native-empty.png, native-populated.png, spanish-small.png, spanish-expanded.png, spanish-invalid.png, metric-review.png, file-dialog.png, units-dialog.png and dirty-dialog.png. Qt filesystem column/navigation chrome still uses the host's framework language; full Spanish Qt chrome, accessibility, high-DPI scaling and native Windows/macOS checks remain pending. Localized application labels and action buttons were checked; this is not complete application localization acceptance.

## Tests and limits

All 288 tests pass, including eleven new tests with actual Qt keyboard/button/dialog events and temporary SQLite projects. These cover pending-text protection, invalid retry/discard, repetitions, empty input, history, independent units/language/decimal, current/cleared results, review gates, add/remove, new/open/cancel, catalog filtering, save/reopen, dirty choices, failed save and cleanup retry. Ruff/format, strict mypy (78 files), architecture and package builds pass. Overall combined coverage is 98.50%; see `f28_validation.json` for exact evidence and independent wheel smoke.

This runnable development preview is not the replacement application. Remaining work includes per-task result presentation, keyboard/accessibility behavior, settings preference restoration, complete Qt localization, worker/job context, DUET/TST desktop views, scientific direction/metric review, legacy migration, avatar/VTK, PLOT/JROT and release packaging. Save As and reset-all remain separate policy/workflow slices. Next: finish per-task result presentation and keyboard/accessibility behavior without weakening scientific gates, then extend the desktop to other supported sources.
