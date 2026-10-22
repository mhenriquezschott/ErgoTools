# Original project Properties — F97, 2026-10-06

Project > Properties opens the owned read-only modal using the reference
`src/main.py:1163` implementation as its layout source. It retains 500 by 400
fixed dimensions, the 13 inline bold-caption rows in original order, and the
full-width Close button. The existing main-window stylesheet supplies the
button treatment. The original Properties action has no icon; none was invented.
English and Spanish captions are owned by this component.

The workspace exposes its connection's immutable ProjectMetadata without storage
I/O. The dialog receives that value and the current normalized location. Opening
or closing does not run the host's edit-acceptance/refresh wrapper: invalid pending
LiFFT/DUET/ST text, selected tool, source history and user preferences survive.
Each open creates a fresh owned dialog and schedules its deletion afterward.
No project disables the menu action, and direct calls return without showing a
window. Save As changes the next displayed location; Backup does not activate its
copy, under the already tested snapshot policy.

## Mapping and recorded differences

| Original row | Current new-format value |
|---|---|
| File | Current project filename |
| Project Name | Saved project title, independent of filename |
| Description, Date, Time | N/A: not stored in the current metadata |
| Database Name / Path | Current project filename / absolute location; SQLite is the project file |
| Project Path / Folder | Current parent directory / its name |
| Data Path, Images Path | N/A: no legacy per-project sidecar folders yet |
| Language | N/A: no project-scoped language; current user language is a separate preference |
| Measurement System | Saved project default, independent of current display units |

This completes access to available current-format details, **not legacy metadata
or XML-sidecar parity**. Do not substitute file modification time for creation
metadata, infer a project language from preferences, or create fictitious paths.
Original New Project metadata collection/persistence remains the next user
workflow. Later legacy import must preserve original descriptions, creation fields,
project language and sidecar relationships on copies of reference datasets.

Long values now elide in the middle instead of silently clipping the original
fixed-width label. A tooltip and accessible description retain the full value.
Record strings are HTML-escaped before adding the original bold caption, so names
such as `<b>Record & title</b>` remain literal. These are explicit invalid/clipping
corrections; no rearranged form, scrolling container or new editing workflow was
introduced. Existing remaining localization and F95 native message parity issues
are unchanged.

## Validation

Five focused cases in tests/test_project_properties.py exercise actual repeated
modal opens on all three tools with invalid pending input, saved-versus-display
units, full long/literal values, Spanish, unavailable legacy fields, current
Save As locations and Close availability. Required gates pass with 748 tests,
96.35% combined coverage, strict mypy over 154 source files, zero architecture
violations, Ruff check/format, and wheel/source builds.

Native xcb captures in artifacts/project-properties cover populated English/
Spanish dialogs, long strings, current/no-project menus and integrated VTK/cards/
bottom controls at 1550 by 1015 and enlargement to 1920 by 1200. The reference
method is extracted through AST without importing/running the reference app and
shown with the same parent stylesheet/DPI and synthetic metadata. This verifies
source-derived dialog layout, **not full reference-application acceptance**.
The initial capture harness incorrectly created a second QApplication; correcting
it to reuse the fixture application removed its teardown failure. An initial
strict-type check also identified the nullable Qt resize-event signature; the
production annotation is corrected without suppression.

An isolated extracted wheel opens actual modals on all three tools, preserves
pending/source/preferences, displays the active copied location in Spanish and
disables Properties after Close. All 500 reference hashes and the approved lock
are unchanged. See f97_validation.json, artifacts/f97-check.log and archived
reference/f97-capture.py.txt / reference/f97-verify.py.txt for reproducibility.
Overall completion percentage and finish date remain unvalidated; this checkpoint
adds a concrete project workflow rather than revising the former foundation-heavy
estimate.

## F98 superseding metadata rows

Format-eight projects created through the integrated New form now supply stored
Description, Date, Time and Language instead of N/A. The saved title drives the
main header as well. Missing older fields and sidecar paths remain N/A. Multiline
values display inline with their complete literal tooltip. See
[details, persistence and remaining lifecycle parity](project_details.md).
