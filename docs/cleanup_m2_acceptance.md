# M2 acceptance — guided upgrade and self-contained fixtures

**M2 complete: 3/6 cleanup milestones, 50%.** M3 remains unstarted and requires
owner instruction. The fixed six-part scope, formulas, UI architecture and approved
dependency baseline are unchanged. User acceptance remains held through M4/M5.

## Delivered workflow

Open, positional CLI project launch and Recent Projects share the same upgrade
detection. Earlier files show localized EN/ES explanation, Migrate/Cancel and a
copyable command for the separate removable tool. Cancel starts no process. Migrate
resolves current edits and publishes only to an owned temporary directory. Expected
launch/conversion failures remain visible with technical details and CLI guidance;
the current workspace remains open and there is no automatic retry.

After successful conversion, the existing assessment picker selects native data.
Cancellation removes temporary output without activating or remembering it.
Accepted conversion opens an unsaved native project. First Save chooses an absent
destination and confirms prefilled original name/description; original date,
language and default units survive GUI display changes. Cancel/conflict/publication
failure retains temporary data for retry. Closing/switching asks Save/Discard/Cancel
even if the current assessment is clean. Successful first Save activates the whole
permanent copy, then releases temporary backing; only that permanent path enters
Recent Projects. Discard releases/removes temporary backing. Native reopen bypasses
the converter. Original files remain unchanged.

This reuses ordinary New-project pre-save restrictions: management/PLOT/JROT/export
enable after Save. The existing header says no project loaded before first Save;
the localized bottom message explicitly identifies the upgraded copy and requests
Save. That bounded choice and compact long-name field behavior are recorded for
later owner review, not silently redesigned. A crash before first Save can lose
temporary output; the preserved original can be migrated again.

CLI utility conversion still publishes directly to its explicit --output path.
The application wheel excludes conversion code; supply the optional tool separately
or expose a forwarding ergotools-migrate command on PATH. Native use needs neither
converter nor original database/image folders. Application/domain code does not
read original schemas or embed original result archives.

## Fixtures

`test_projects/originals` contains 27 byte-identical original descriptors/database/
image files from all four supplied samples, with internal companion names intact.
`test_projects/native` contains the two supported comprehensive native projects.
Each has 194 source/result versions and four embedded plant images; comparative
has seven rotation schemes, integrated has five. M1R recalculated values are
unchanged. Original copies and native fixtures ship in the source archive, not
the runtime application wheel.

Each native file was copied alone into an otherwise empty temporary directory.
All metadata, hierarchy, workers/jobs/ownership, authored risk profiles, assessment
inputs/results, plant images/marker positions and rotation schemes matched exactly.
No original sidecars were copied. The earlier JROT schema and blank-title test3
remain unsupported; organization is not a claim that these were converted.

## Validation

Required full gate: **1,264 tests passed, 96.39% execution coverage**, Ruff/format,
strict mypy (247 modules), architecture (zero violations), wheel and sdist passed.
Focused M2 and existing workspace checks passed 35 tests before the final gate.
Regressions cover real modal buttons, consent/cancellation, process/source failure,
temporary recency, first Save cancel/conflict/failure, clean converted close consent,
cleanup, original preservation, literal command quoting and native reopen.

The extracted wheel ran real external conversion, first Save and native reopen in
both languages with converter imports blocked in the application. All 16 native
captures were inspected: default/expanded consent, errors, temporary/populated main,
prefilled first Save and permanent/populated main, including full VTK/cards/bottom
controls. Existing PLOT/JROT numerical/parity evidence remains valid; no changes
to those windows or calculators were made. Reference 500-file hashes and approved
lock remain unchanged. Final edits are documentation/guide text only; executable
AST matches the functional/native-tested wheel and final package bytes are verified.

Read [validation](cleanup_m2_validation.json), [fixture evidence](../artifacts/cleanup-m2-fixtures.json),
[native evidence](../artifacts/cleanup-m2-native/verification.json),
[package evidence](../artifacts/cleanup-m2-package.json), [fixture guide](../test_projects/README.md)
and [documentation inventory](cleanup_documentation_inventory.json). Per-symbol
semantic review remains explicitly pending where not performed; no claim that
test coverage proves complete documentation. No new milestone or schema repair.
