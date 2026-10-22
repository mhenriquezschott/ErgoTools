# Original project details collection — F98, 2026-10-06

The integrated New workflow now collects Name and Description with the original
Project Details form from reference src/main.py:saveFile. The controls remain
Name QLabel/QLineEdit, Description QLabel/QTextEdit and the standard OK/Cancel
button box in a QVBoxLayout, with the original automatic sizing. English/Spanish
captions and standard-button text are owned by the form. The native standard
button treatment/ordering/icons are retained from the reference rather than
replaced with a new component. No designer asset or dependency was added.

The name is optional: whitespace-only input falls back to the destination stem,
consistent with the existing nonblank project-title contract. Accepted names are
trimmed; descriptions retain their literal Unicode, line breaks and whitespace.
The description editor disables rich-text input. Current display-unit policy and
language become the project's creation defaults, as in the reference save code.
Local creation date/time is captured at second precision; no timezone is invented.
The main header/status now shows the saved title rather than deriving a name from
the filename. Existing older projects also show their stored title.

## Cancellation and workflow limits

Cancel in the location picker or actual details form changes no project, task
text, source history or preferences. The host's New route now delays assessment
input parsing until after details acceptance. A regression exposed that the
DUET/ST toolbar route previously parsed invalid text before showing the form;
New is now explicitly exempt from that eager parsing in the shared dispatcher.
After acceptance, existing task/context validation and Save/Discard/Cancel consent
still apply. Invalid pending input retains the old project and creates no file.
A valid accepted grid edit remains an ordinary source edit if later dirty consent
is cancelled, consistent with the established transition policy. Existing files
are never replaced and initialization failures retain the old workspace owner.

The integrated preview still chooses a destination during New, whereas the
reference first resets an unsaved project and collects details at its first Save.
This slice adds the original metadata controls to the existing migrated lifecycle;
it does not claim exact parity for that unsaved-project timing. The standalone
harness retains its temporary unit prompt and filename-derived title. Original
Save As prefilled name/description editing is the next metadata workflow; its
current copy/Backup behavior preserves creation metadata unchanged. Sidecar folder
relationships and legacy XML import remain separate unfinished work.

## Format eight and old compatibility

ProjectMetadata now owns optional description, created_at and Language. None means
absent historical data; an empty description means explicitly accepted blank text.
The shared Language enum moves to domain.language, with application.settings
re-exporting the same identity so existing call sites and settings codecs retain
compatibility. Domain/application remain Qt/VTK/storage independent.

Bootstrap creates project format eight: the existing metadata, assessment,
hierarchy/job/history/risk schemas remain, plus one project_details record with
nullable description, canonical local ISO datetime and stable language code.
Parameter binding stores record text literally. Strict opening rejects malformed
language, timestamp, description type and row count. Older formats retain their
existing reader paths and absent optional values. Opening them performs no
migration/write; focused tests hash versions two through seven around read-only
open/close. Existing version-one readers also remain covered by the suite.
Writers targeting older formats reject populated optional fields before file
creation rather than silently discard them. Copy/Backup snapshot the complete
SQLite file; all details survive Save As, Backup and reopening.

Properties now displays stored description, date/time and project language when
available, even if current UI language/units differ. Missing old fields remain N/A.
The fixed inline description row displays line breaks as spaces, with complete
original text in its tooltip/accessibility value, preventing a multiline name/
description from pushing other rows out of the original 500 by 400 dialog.
No schema change occurs when opening or saving existing older projects.

## Evidence and remaining acceptance

Twelve focused cases cover actual Cancel on all three tools with invalid pending
input, native accepted Spanish text/metric defaults, creation timestamps, named
header/Properties, literal multiline preservation, blank-name fallback, declined
consent, exclusive destinations, old-format byte preservation, five malformed
storage cases and invalid portable values. Earlier New/organization regressions
now expect the format-eight bootstrap and remain functionally intact. An initial
test-only SQLite context omitted close; explicit closing fixed its ResourceWarning.

Required F98 gates pass: 760 tests, 96.35% combined coverage, Ruff check/format,
strict mypy over 156 source files, zero architecture violations and both builds.
Native xcb captures show the source-extracted reference form at the same style/DPI,
English/Spanish empty/populated/expanded states, persisted Properties and the
named integrated VTK/cards/bottom layout at 1550 by 1015 and 1920 by 1200.
These are source-derived/synthetic comparisons, not full reference-app acceptance.
An isolated extracted wheel validates actual three-tool Cancel isolation, creation,
Properties, snapshots and reopen. All 500 reference hashes and the approved lock
remain unchanged. Evidence is f98_validation.json, artifacts/f98-check.log and
archived reference/f98-capture.py.txt / reference/f98-verify.py.txt.

Overall percentage and finish date remain unvalidated. Final scientific gates,
PLOT/JROT, legacy import/sidecars, remaining localization/native-message parity,
unsaved-project workflow and copied comprehensive-project/platform acceptance
remain pending; this checkpoint is a concrete metadata workflow, not full parity.

## F99 superseding Save As behavior

Integrated full-project Save As now prefills the same form and accepts copy-only
name/description changes with fresh copy creation date/time/language/units. Backup
and direct save_as calls without metadata retain saved details unchanged. Original
file/source units/ownership remain intact. See [copy behavior](save_as_details.md).
