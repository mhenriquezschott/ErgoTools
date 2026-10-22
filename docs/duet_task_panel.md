# Original DUET task component — F79

This component comes from the reference `setupDUETTab`, control styling, sticky
header and DUET Calculate/Reset code. It preserves the five-column grid with
stretches (0,4,3,2,1), minima (48,250,220,150,105), eleven indexed OMNI-Res choices,
250px dropdown minimum and 280px repetition-input maximum. The hidden internal
header occupies its reference zero-height row; the hidden totals still reserve
two 30px rows above the original bottom controls. Processed packaged icons and
the common application stylesheet provide the original appearance.

`DuetTaskPanel` owns widgets and pending text. `DuetPresenter` owns grid parsing,
immutable source replacement, calculation and existing workspace/history calls.
Its dimensionless edit context retains the source and decimal convention; it
never uses LiFFT/TST dimensional conversions. `ReplaceDuetInputs` replaces all
reviewed fields atomically with preserved row identities. Failed parsing retains
the complete pending grid and unchanged source. Successful commit is one undo
step; Save uses the established transactional project workspace. Reset clears
even invalid pending text, restores rating zero and clears repetitions in one
reversible source change. No schema, scientific formula or dependency changed.

The explicit `evaluate_duet_grid` path matches the original handling of blank
slots: completed rows contribute rounded damage, missing rows have zero preview
damage, and PARTIAL status retains the missing-field issues. Missing source fields
remain None. Invalid numeric/scale values block all outputs. Strict evaluate()
continues rejecting missing fields. Zero-total probability remains absent.
Input edits clear old calculation colors; no label parsing or polling is used.
English/Spanish text, ratings and tooltips are separate from decimal parsing.
Translation retains pending data. Reference QIntValidator is replaced by the
existing parser so rejected input remains correctable and loaded fractional
repetition values retain reference calculator support; negative values are
retained as source input for correction but cannot produce calculated results.

## Verification and remaining integration

644 native tests pass; combined coverage 96.85%. Six new focused workflows
cover atomic edits/Undo/Redo/Save/reopen, retained invalid text/Reset, blank-row
partial vs strict results, translation/decimal/unit independence, clearing invalid
results/context rejection, missing vs zero rating and geometry. All standards,
typing, architecture and builds pass. Same-size original/new native component
captures include expanded popup, calculated/empty/error/localized/narrow/scroll
states. Scroll and bottom-control geometries match the original at 980×650.
The extracted wheel reproduces the synthetic workflow from another directory.
All 500 reference-file hashes and the approved dependency lock are unchanged.
Evidence: `f79_validation.json`; scripts: `docs/reference/f79-*.py.txt`.

This is an embeddable component, not a second finished application. No new launch
mode was introduced; the main preview's DUET tab remains disabled pending the
next integration slice. Tool/document selection, shared sidebar/avatar and DUET
worker/context routing are next; original ST controls follow. Delete and task-data
selection remain visibly disabled. Complete application/native-platform parity
and final comprehensive-project validation have not been claimed.
