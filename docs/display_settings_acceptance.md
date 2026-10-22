# Display, Settings, avatar and icon acceptance

Owner-approved Linux follow-up: **4/4 requested corrections complete (100%)**.
No milestones, points or dependencies were added. The accepted migration and cleanup
ledgers remain 12/12 and 6/6. Native Windows/macOS acceptance remains deferred.

## User-visible behavior

- Numeric fields default to one display decimal for continuous inputs, moment,
  probability and contribution; damage/cumulative damage default to four. Repetition
  fields display whole numbers. Project Settings provides separate 0–8 decimal
  preferences for the five decimal groups. Decimal mark remains a user preference.
- Toolbar Settings and the Tools menu open the same themed window. It combines
  language/decimal mark/animated focus, project units/display precision, and the
  active assessment's task count. With no project open, project-specific controls
  are disabled. Apply persists preferences; the main Save continues saving assessments.
- Changing task count requires explicitly selecting Reset tasks and confirming a
  separate branded warning, with Cancel as default. Confirmed reset clears this
  assessment's inputs and is Undo-able. Cancel preserves edits, including invalid
  pending text. Confirmed reset can deliberately discard invalid text, as before.
- The avatar shows LiFFT, DUET and ST colors together where those assessments exist
  for the exact selected worker/assignment. Tab selection changes camera focus and
  sidebar content. Missing or invalid active results clear that region; other valid
  regions remain visible. Closing the project clears all regions.
- Appropriate processed icons are reused in menus, selectors, Job profile actions,
  graph Settings and JROT Clear cell. [Icon inventory](icon_inventory.md) lists
  missing dedicated assets. Redo and Retire remain text actions pending suitable icons.

## Precision and architecture guarantees

Display formatting does not round stored source data or calculated results. Numeric
editors retain exact original tokens when an unchanged field is committed alongside
another edit. Intentional retyping commits the entered value; native typing Undo
restores the original exact token. Unit changes do not accumulate rounding.
Fractional repetition sources remain exact although their display rounds to a whole
number. Formulas, intrinsic scientific rounding and original risk palettes are unchanged.

The domain owns validated immutable DisplayPrecision. The application uses an optional
project-preferences repository protocol; SQLite owns the optional display-settings
record in native format 14. Earlier native projects without that record use defaults.
Save As and Backup carry project preferences, images and data in the native project;
no original folders or migration utility are required. One authoritative calculated
result per assessment version remains the policy.

All-region colors cross the existing renderer port as plain body-region/RGB values.
The VTK adapter alone applies them to model actors. Sibling evaluation does not switch
active documents, write records, or import SQL/VTK into the domain/application layers.

## Verification and limits

Final approved-environment gate: **1,308 tests passed, zero failures/skips;
95.81% combined statement/branch coverage**. Ruff, formatting, strict types,
architecture, naming, structural documentation, substantive per-file review and wheel/
source builds pass. Coverage is executable path coverage, not a test pass percentage.
Forty-two changed/new maintained code files were individually reviewed and their
review hashes renewed; the full inventory reports no pending reviews.

Focused regressions cover exact-field retention through unit toggles/unrelated edits,
intentional typing/native Undo, per-project reopen/Save As/Backup precision,
reset confirmation/Cancel/Undo, existing invalid-text reset compatibility, same-owner
all-region overlays and native VTK actor visibility. Full-suite assertions now reflect
approved compact display and simultaneous overlays while retaining precise-data checks.

Native English/Spanish captures in artifacts/display_settings_review cover main
metric/imperial and tool states, enlarged workspace, populated/empty Settings,
selected reset controls, branded confirmation, affected menus/dialogs and JROT Clear
cell. Final confirmation captures supersede the earlier system-icon warning capture.
The final gauge and table both show the requested probability precision. A disposable
copy of the comprehensive project retained all **194 assessment sources and saved
results exactly**; its permanent fixture bytes remained unchanged.

The already-recorded Spanish main-window minimum-width text-fit limitation remains:
enlargement to 1800×1120 was inspected and fits. This follow-up does not silently add
an unrelated main-layout redesign. The new Settings controls and confirmation fit
in both languages. Dedicated icons are the only owner-supplied assets pending here.
Reference code/environment and permanent test projects were not edited. Approved
dependency versions and resource icon/model bytes remain unchanged.
