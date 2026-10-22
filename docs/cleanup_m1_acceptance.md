> Historical M1 evidence: the dual-result policy and five-part percentage below
> are superseded by [M1R acceptance](cleanup_m1r_acceptance.md) and the current six-part ledger.

# Cleanup M1 acceptance — independent converter

M1 complete; follow-up **1/5, 20%**. M2–M5 remain unstarted. No new milestones,
dependencies, formulas or UI design changes. Owner testing remains on hold.

## Delivered boundaries

All original-format readers, reconciliation, recorded-output decoding and prior
converted format-12 upgrade live in `tools/project_migration/ergotools_migration`.
`migrate_project.py` is the optional external command-line boundary. Application
Open uses a process adapter, never converter imports. No compatibility shims or
duplicate old readers remain under `src/ergotools`. Negative architecture probes
reject both converter imports and unused reader files in the application package.

Native creation publishes format 13, with original recorded observations and
later saved outputs in separate versioned native result stores. Native storage
contains no original SQLite archive or old result schema. Recalculation cannot
overwrite original observations. All plant images/data/relationships are embedded.
Original XML/database/images and earlier converted input remain unchanged.

Formats 1–11 remain native-readable; format 12 requires the external upgrade.
The existing M1 Open destination workflow remains. Guided migration, explanation,
temporary unsaved first Save and permanent originals/native fixture folders are
M2, not claimed complete here. The wheel excludes the tool; an installed user must
retain/provide the external script to convert originals. Native use needs none.

## Verification

- Full isolated Linux XCB gate: **1,251 passed**, **96.45%**
  combined statement/branch coverage; no failing tests. Ruff, format, strict mypy
  (248 source/tool modules), architecture and wheel/source builds pass.
- Focused new external/architecture regressions: 18 tests, 17 subtests pass.
  Existing storage/lifecycle/export/transfer/desktop regressions are in the full
  gate. Failure cases include missing tool, existing destination, malformed input,
  archive corruption, identity conflicts, transaction ownership and no-overwrite.
- External comprehensive upgrade: 197 assessments, 194 recorded results,
  6 later saved calculations, 4 plant images, 7 rotation schemes.
- Independent wheel from unrelated directory with tool imports actively blocked:
  native Open, exact outputs/maps/schemes, Save As and Backup, integrated main,
  PLOT and JROT in English/Spanish. Six captures inspected; renderer, result cards,
  labels and bottom controls retain their accepted layout. Animated PLOT gauges
  were captured during interpolation; they are not scientific comparison values.
- All 500 recorded reference hashes and the approved dependency lock unchanged.
  Final source/wheel byte equality is recorded in the package report.

Functional/native checks precede final docstring-only refinements. Executable AST
identity against the tested wheel is checked before rebuilding; no redundant full
functional run is needed for comments/docstrings/guides. Final lint/format/types/
architecture/build checks pass. Coverage is executable-path coverage, not a test
pass percentage or documentation completeness score. Full documentation stays M4.

## Documentation accountability

The frozen pre-M1 audit is `cleanup_documentation_baseline.json`; the current
inventory includes **394 Python/stub files** and
**2624 functions**, with qualified
names, line ranges and source hashes. Each pending file/symbol/constant is explicit.
New M1 interfaces and changed native contracts have detailed documentation; moved
readers are not falsely certified as exhaustively reviewed. M4 must close every
pending item and enforce the agreed structure before M5 and owner testing.

Evidence: `artifacts/cleanup-m1-check.log`, `cleanup-m1-new-regressions.log`,
`cleanup-m1-package.json`, `cleanup-m1-native/verification.json`, six native PNGs,
`docs/cleanup_m1_validation.json`. Existing accepted parity evidence is retained.
Native Windows/macOS testing remains deferred as instructed.
