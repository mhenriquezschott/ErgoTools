# Editing projected input units — F24, 2026-09-29

`edit_display_input` adds an explicit application boundary for one deliberately edited arm or force value in a LiFFT/TST unit projection. The entered value is converted from display units back to the assessment's recorded units and applied through the existing model-specific replacement command. One successful edit is one undo step. No dependency, schema or UI changed.

## Preservation and validation

The caller supplies the actual active session, its displayed projection, stable task identity, explicit field and parsed unrounded value. Source/session/revision freshness is checked before reading or mutating a task. Stale, foreign, reloaded or branched projections fail with a localized `validation.stale_view` issue. Missing tasks and invalid quantities fail explicitly; DUET has no dimensional source fields and is rejected.

Only `lever_arm` or `load` is converted. Units, row order, task identity, direction, repetitions and the other numeric field are retained exactly. None explicitly clears the selected field; finite signed values remain editable for subsequent input validation. Booleans, nonfinite or nonnumeric values, overflow and nonzero conversion underflow are rejected before mutation.

Re-entering the exact unrounded projected value is a no-op. This comparison runs after numeric validation, so True cannot masquerade as a displayed 1. It runs before reverse conversion, preventing needless floating-point drift in original values and preserving the redo branch. Callers must submit only deliberately changed fields; parsing all rounded screen fields on focus loss would lose this contract and must not be done in the future UI.

The new operation executes immediately in the existing synchronous owner-thread session. There is no buffered command retaining an old projection. Undo restores exact source snapshots, redo restores the converted edit, and new edits after undo follow the session's normal branch rules. Stored units are never replaced with view units.

## Freshness, storage and evaluation

Successful edits invalidate previous projections and cached evaluations through existing source/revision checks. Saving marks clean only after commit; a real SQLite trigger failure leaves both the earlier saved source and edited history usable for retry. Reopening preserves the converted field and untouched precision without changing project defaults.

Evaluation still uses recorded source units. Editing through an imperial projection of metric source cannot bypass metric scientific review, and TST direction review stays enforced. No result formulas or constants changed.

A source snapshot cannot detect a view-only preference change. The caller must pass the projection currently shown when interpreting input; the desktop presenter must replace its projection when display units change. GUI ownership/event wiring, localized numeric parsing, rendered rounding and deliberate number reinterpretation remain pending. This slice does not claim a complete desktop unit-switch workflow.

## Evidence

Eight new tests cover both models, both source/display unit choices and both editable fields; no-op precision and redo retention; clearing/missing/signed values; stale/foreign/reloaded/branched views; numeric and conversion failures; evaluation freshness and scientific gates; plus real SQL rollback/retry and file reopening. All 259 tests pass. Overall combined coverage is 99.59%; the new module has 100% statement/branch coverage. Ruff/format, strict mypy (70 files), architecture and builds pass. Independent wheel and original-tree evidence is recorded in `f24_validation.json`.

Next: locale-aware numeric input boundaries with explicit decimal conventions independent of interface language and measurement units. GUI integration will require visible controls and visual verification after the approved runtime dependencies are available.

## F25 follow-up

[Explicit decimal input](numeric_input.md) now parses and formats dimensional editor values and routes deliberate text changes through this edit boundary. Presenter-owned display context and GUI wiring remain pending.
