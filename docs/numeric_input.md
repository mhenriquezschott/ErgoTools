# Explicit decimal input — F25, 2026-09-29

The presentation boundary now parses editable numeric text under an explicit decimal-point or decimal-comma convention. This convention is independent of interface language, source units, display units and operating-system locale. No global locale changes, dependencies, settings schema or GUI controls were introduced.

## Grammar and precision

`DecimalConvention` selects one decimal separator. `parse_input_number` accepts ASCII digits, an optional leading sign, optional decimal fraction and optional signed scientific exponent. Surrounding whitespace is trimmed. Blank text returns None, not zero. Grouping separators, internal whitespace, an alternate decimal mark, units, underscores, partial tokens, Unicode digit/sign lookalikes, NaN and infinity are rejected with a field/task-specific issue. Trimmed input is limited to 256 characters.

There is no separator guessing: under comma convention `1,234` means 1.234; under point convention it is rejected. Thousands grouping is not supported. The future UI must make the active convention visible and preserve uncommitted text when preferences change; this API does not infer a regional locale from a language choice.

Whole-number tokens become Python integers and retain exact precision. Decimal/exponent tokens use the existing binary-float calculation contract without display rounding. Unrepresentable float overflow and nonzero underflow to zero fail explicitly. This does not claim arbitrary-precision decimal arithmetic or exact representation of every decimal fraction. Numeric/model range and scientific checks still belong to the domain/evaluation boundary.

`format_input_number` provides ungrouped, full-precision editor text using integer representation or float repr, adapted only for the separator. It preserves supported large integers, float round trips and negative floating zero. None becomes blank. Invalid/nonfinite numbers or values exceeding the editor text limit fail explicitly. Rounded result/report formatting remains separate; never initialize editable values by copying rounded report text.

## Integration and failure behavior

`edit_display_text` checks source freshness, parses one deliberately changed dimensional field, then invokes F24's unit-aware edit operation. Invalid input cannot become an absent value, mutate source, discard redo or invalidate an otherwise current result. Blank input explicitly clears that field and becomes an undoable edit. All successful changes keep the original source units and untouched values exact. Saving writes invariant numeric source through existing codecs; decimal-comma text never enters storage.

The wrapper currently covers arm/load edits for LiFFT/TST. The parser is reusable, but repetitions, OMNI-Res selector handling and other text fields still need their own presenter contracts. Imperial display/input over a metric source does not bypass scientific review. Editing TST directions is outside this numeric boundary.

No per-keystroke validator, grouping support, localized dates, regional locale discovery, preference persistence or full GUI integration is claimed. A presenter must own the current projection/convention and invalidate obsolete editors when either view preference changes. Source revision checks alone cannot distinguish two simultaneous display contexts. That presenter context is the next boundary before wiring widgets.

## Validation

Ten new tests cover both conventions, accepted/rejected grammar, extreme numbers, precise integer/float formatting, blank versus invalid input, both languages/models/source/display units, undo/redo, exact projection re-entry, stale-source precedence, cached result retention and save/reopen. All 269 tests pass; overall combined coverage is 99.61%, both new modules 100%. Ruff/format, strict mypy (72 files), architecture and distribution builds pass. Independent package smoke, dependency-lock and original-file integrity evidence are in `f25_validation.json`. GUI and scientific acceptance remain pending.

## F26 follow-up

[Presenter edit-context ownership](edit_context.md) now prevents obsolete display-unit/convention callbacks from submitting under a new interpretation. Concrete GUI lifecycle and pending-text behavior still require widget integration and visual testing.
