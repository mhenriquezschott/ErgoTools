# F94 — persisted decimal convention, 2026-10-06

Tools > Settings now includes an explicit decimal separator choice: 1.25 or 1,25.
Apply persists it independently of language and metric/imperial display units.
A fresh application restores the choice before binding assessment controls.
Language never selects a decimal mark implicitly. Cancel changes nothing.
The original toolbar Settings retains its task-count operation.

Pending input is validated using the previously active convention before Apply.
Invalid input retains the text and old preferences. A settings-write failure
retains the old display/decimal policy; valid input accepted before the failure
remains an ordinary source edit, matching the existing Settings contract.
Successful Apply rebinds all three tools without converting recorded source units
or source values. Comma changes editable numeric formatting/parsing only;
result formatting and machine-readable CSV retain their existing policies.
No grouping separators or automatic locale guessing were added.

DecimalConvention now belongs to the portable domain contract and remains
available through the existing numeric_input import for compatibility. Application
settings and numeric presentation share this typed enum without a reversed layer
dependency. No numeric algorithm, scientific gate or project schema changed.

User settings format version two requires decimal_convention with value '.' or
','. Strict version-one files remain readable and default to point without any
write during load. Only an explicit settings save publishes version two, preserving
language, units and recent history. Corrupt, duplicate-member, incomplete or future
formats are rejected instead of reset. An older migrated build that understands
only version one cannot read a saved version-two settings file. This change affects
only the new project's user-settings file, not the reference environment or project
files. Dependencies and their approved version ranges are unchanged.

Four focused cases cover all three tools' modal Cancel, invalid Apply, save failure,
old-convention validation, comma projection/input, preserved language/units/history
and fresh-window restoration; a separate case verifies read-only version-one load,
explicit upgrade and invalid convention rejection. Required gates pass 729 tests,
96.34% combined coverage, lint/format, strict mypy on 151 source files, architecture,
wheel and source builds. Native English/Spanish default/selected/expanded Settings
and all three integrated comma-input layouts were inspected at 1550 by 1015.
Avatar, cards, labels and bottom controls remain visible. The independent extracted
wheel verifies actual modal Apply, all three tools, persisted restart, recorded
source units and native renderer cleanup. All 500 reference hashes and the approved
lock remain unchanged. Only synthetic project/settings files were used.

Evidence: f94_validation.json, artifacts/f94-check.log, archived
reference/f94-capture.py.txt and reference/f94-verify.py.txt.
This completes decimal-setting persistence, not full localization or scientific
unit acceptance. Next: complete the remaining dialog/stock-control language review,
then the documented renderer View animation/preferences work. Project details /
sidecars, scientific gates, PLOT/JROT, legacy import and final copied-project /
platform acceptance remain. Overall completion percentage and finish date remain
unvalidated after withdrawal of the former 67% estimate.

F96 extends settings to version three for the original View camera policy; strict
versions one/two remain readable. Decimal persistence is retained. See
[camera animation](camera_animation.md) for current format compatibility.
