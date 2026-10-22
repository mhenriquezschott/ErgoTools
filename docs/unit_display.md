# Source-preserving unit display — F23, 2026-09-29

The accepted plan (§5) explicitly corrects the original menu's relabeling behavior: switching display units must preserve physical exposure and results. The implementation now supplies a typed, source-bound projection for LiFFT/TST input rows. It does not yet wire a GUI menu or implement editing in projected units.

## Reference characterization

Original `setMetricSystem`/`setImperialSystem` call `updateUnits` and `setUnitSysText`. These set selection/header strings but do not convert input widgets or update recorded per-assessment unit metadata. The calculate-click handlers subsequently read the selected action, making unchanged numeric text liable to reinterpretation. Existing TODO comments acknowledge the unresolved conversion behavior.

`tests/fixtures/unit_switch_reference.json` contains 24 executions of those actual extracted methods with inert labels: both recorded unit choices for each dimensional tool, three tabs and both target units. Inputs and recorded units remain unchanged while headers change. Capture used original Python 3.10.18 with `-B`, no application import, Qt launch or database access. Source/AST hashes and the reproduction script `reference/f23-capture.py.txt` preserve provenance. This is method characterization, not visual acceptance or whole-menu signal testing.

## Implemented design

`project_model_input` centralizes arm/force display conversion beside the existing model normalization policy. Arm uses 2.54 cm/in; force uses the reference model's 4.45 N/lbf. These compatibility factors are not generic mass conversion or an approved correction to scientific constants. No calculated moment conversion is added. Same-unit values retain exact numeric identity; missing values stay absent; finite signed values remain reviewable. Invalid types, booleans, nonfinite inputs, overflow and nonzero underflow to zero produce structured errors. Unsupported quantities/units fail explicitly.

`prepare_unit_view` always derives immutable row projections from the original source, with original preparation, session and revision attached. It never projects from an earlier display, runs a calculator or rewrites a draft. Consequently repeated toggles cannot accumulate rounding drift, change persisted source bytes or alter existing calculation results. Repetitions and model directions are retained. Incomplete source issues remain available alongside projected input quantities; invalid dimensional numeric inputs fail the whole projection with no partial return. DUET has no dimensional source inputs and rejects this operation.

Display units are view state. Switching them is neither a document edit nor a change to project defaults, and does not create undo entries or mark clean documents dirty. Actual source edits remain undoable; they make old projections stale. Undo can restore the original projection's eligibility, while reload and cross-session use cannot. No view preference is persisted by this slice. The future desktop owner must replace/release projections on view changes and document close.

This intentionally supersedes F22's proposed source-conversion commands for ordinary display switching: multiplying and dividing stored floats could lose original precision and change values at model rounding thresholds. Preserving source and converting only the view satisfies the accepted preservation contract more directly. An explicit entered-number reinterpretation remains a different future command; it must never be an accidental side effect of changing labels.

## Review gates and remaining boundary

Evaluation always uses original source and its units. Showing a metric LiFFT/TST source in imperial units cannot bypass metric review; TST direction review also remains enforced. Existing results are not converted or relabeled by this API. Moment/result display remains subject to its existing scientific review and presentation policies.

Editing values entered in projected units, locale-aware numeric parsing, view preference persistence, translated unit labels, GUI wiring and visual testing are pending. A subsequent edit boundary must convert only deliberately edited quantities back to their recorded source units, preserve untouched source fields exactly, and reject stale projections. Original-source round trips, not approximate equality alone, must remain the acceptance criterion for repeated display toggles.

## Validation

Eleven new tests cover 24 menu captures, all 48 existing normalization vectors, repeated projections with exact source/result retention, both model types/units, missing/signed values, direction/repetition preservation, save/reopen/default isolation, source-history freshness, scientific review gates and numeric failures. All 251 tests pass; combined coverage is 99.59%, with projection and conversion modules at 100%. Ruff, formatting, strict mypy (69 files), architecture and builds pass. Independent wheel and original-file integrity evidence is in `f23_validation.json`. No dependency, schema or UI changed.

## F24 follow-up

[Projected-unit editing](unit_edits.md) now supplies the deliberate single-field edit boundary described above. Locale parsing, view preference persistence and GUI ownership remain pending; the F23 evidence and historical scope are unchanged.
