# Standard Shift time entry — verified, 2026-10-19

Owner approves the proposed standard hour/minute editor with keyboard/arrow entry,
confirms 00-23 hours / 00-59 minutes and legitimate overnight shifts, and agrees to
try explicit following-day intent. Existing organization Optional details/tree
preservation remains required and continues to pass.

## Behavior and ownership

Plant/Shift clocks now share OptionalTimeEdit, a small adapter around Qt QTimeEdit.
Qt owns clock sections, colon, keyboard parsing, zero padding and stepping. Type
8:30 or 0830 for 08:30; 8: becomes 08:00 with the minute section selected for entry.
Hours/minutes stay within native clock bounds. Valid keyboard paste uses Qt clock
parsing; invalid paste is inert. Native arrows edit the selected section. Ctrl+A
then Delete/Backspace clears an optional value. Not set / Sin especificar represents
None, distinct from valid midnight 00:00. Merely focusing an absent clock supplies
no value. Malformed loaded text remains available for correction; parseable short
hours display canonically and a later accepted record edit writes HH:mm.

Shift adds Ends the following day / Termina al día siguiente. Same-day complete
pairs require end > start. Following-day pairs require end <= start, representing
one daily interval up to 24 hours; equal clocks mean 24 hours only with that option.
This existing clock-only representation/one-cycle bound was reported during work.
Loaded overnight pairs infer the checked option. Unknown/partial optional pairs
disable it without manufacturing clocks. The draft baseline includes intent so an
inconsistent choice cannot silently close/save. Invalid pairs retain form/private/
durable data and show localized guidance. Plant shares the clock input component;
Shift's day-pair ordering rule is not imposed on Plant metadata.

The option adds no stored day field, table/column, schema/codec version or alternate
assessment. Start/end remain existing optional organization clock attributes. The
adapter's absence/invalid flags belong only to its Qt view. Standard QTimeEdit focus
routes keyboard Undo/Redo to its internal line editor; mouse history still accepts
and replays one record through the existing shared cursor. Other date/spin controls
retain their policy. Optional panels and branch expansion remain preserved.

## Validation

Required native Linux bash tools/check.sh: **1,876 passed, zero failures/skips,
94.52% coverage**; Ruff/format, strict types (266), architecture, naming, complete
documentation/review and wheel/source builds pass. Native focused checks: 176
passed. Independent wheel: **181 passed / 78 subtests**; all 244 package Python
files and both guides equal reviewed source, converter excluded. Final gate wheel
hash equals the independently tested build.

Tests cover native keyboard/sections, short hours/compact entry, paste rejection,
readonly controls, stepping, nullable midnight, repeated clear/deduplicated signals,
legacy correction, all existing organization metadata/view/history tests, EN/ES
same-day/overnight/optional/equal-time pairs, failure preservation, exact shared
Undo/Redo, main Save and reopen with inferred day intent. Existing worker-management
and global save/regression tests pass. Maintained fixtures were updated as test
code in place; no new permanent native projects were created.

Twenty-six final native EN/ES captures inspected under the installed application
and menu theme: loaded clocks, short hour/minute entry, same-day error including
minimum size, night-shift pending/Undo/Redo/private Save/reopen, unspecified/midnight,
minimum controls and both scrolled Plant clocks. New unchecked/checked day control
is visible and footer/labels fit. Exploratory arrow probes found outer QSS spinner
borders suppressed native glyphs on this Qt style; final code retains Qt's native
frame/arrows and the existing field height/font. No custom arrow painting, icons
or dependencies were added. Only final captures listed in visual_validation count.
Both updated Help paragraphs rendered and visually inspected.

Seven maintained files substantively reviewed, including the new component and its
focused test module. Inventory: 433 files / 3,039 functions / 413 classes /
316 constants, zero pending/gaps. In-code, architecture, single-Save, database-purpose
and bilingual user documentation updated; obsolete plain-time caption/tooltip keys
removed. Owner workflow, both maintained comprehensive fixtures and uv.lock retain
their starting hashes. No reference, scientific formula, dependency or project data
changes. Linux migration/cleanup remains 100%; Windows/macOS acceptance deferred.

Evidence: [validation](../artifacts/shift_time_editor/validation.json),
[visuals/protections](../artifacts/shift_time_editor/visual_validation.json),
[package](../artifacts/shift_time_editor/package.json),
[documentation review](../artifacts/shift_time_editor/documentation_review.json).

## Next owner check

Restart and open shift 1. Try 8:30, 0830 and 8: with subsequent minutes; use arrows
on the selected section. Try 22:00 to 06:00 with Ends the following day, and verify
Undo/Redo without closing Optional details. Ctrl+A/Delete should show Not set, not
00:00. Restore desired test-project times before main Save. Await owner feedback
before continuing workplace associations. No new milestone was introduced.
