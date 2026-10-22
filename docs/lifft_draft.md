# F4 — LiFFT source draft and reversible task editing

Completed 2026-09-27 with the existing approved environment. This adds the first concrete assessment document to the generic F3 history. It is not a migrated LiFFT calculator or GUI.

## Reference and deliberate boundaries

Reference `src/main.py` around 5600 parses lever arm, load and repetitions with float(), using empty strings after parsing failures. When lever arm/load exist but repetitions do not, the existing preview calls LiFFT with rep=0. Around 7980–8006 the UI attaches QDoubleValidator to lever arm/load and QIntValidator to repetitions. No explicit physical bounds appear in those validator constructions. The reference starts with 15 task rows but adjusts row counts elsewhere; the new domain does not impose an arbitrary 15-task limit.

The new draft stores absent values as None. It never substitutes zero repetitions, calculates a preview, or stores derived damage/risk. That makes the difference between missing and entered zero explicit; a future presenter may implement the characterized preview behavior without corrupting source inputs. Structural nonfinite values are rejected, consistent with earlier typed API guards. Finite negative/large/fractional inputs are retained for review rather than clamped. `missing_inputs()` only checks presence: it is not a physical validator or permission to calculate. Integer-repetition UI behavior, physical bounds and locale text parsing must be decided and tested at the calculation/input boundary before UI integration.

This slice implements the accepted architecture's draft-editing requirements; the new commands are not claimed to reproduce an existing legacy undo system. Scientific constants and metric moment handling were not touched.

## Source ownership

`domain/assessments/lifft_draft.py` defines frozen task and draft values. Each task has a stable task ID and original numeric lever arm, load and repetitions. The owning draft's explicit MeasurementSystem determines inches/lbf or cm/N. Unit metadata belongs to the stored source, not current display language. There is deliberately no command that merely relabels units. Real unit switching will require conversion and round-trip acceptance later.

Tasks use a tuple snapshot, preserving order and preventing later changes to an input collection from modifying history. Duplicate/blank task IDs and unsupported measurement systems are rejected. Task IDs are opaque identities rather than row numbers; row positions can change without changing identity. Existing persisted task IDs and complete assignment/context identity still need explicit mapping in the persistence slice. Project/document scope is provided by DocumentSession/DocumentKey; this draft does not invent a legacy database identity mapping.

InputIssue carries a stable code, field name and optional task ID. DraftError exposes this structured context, while its technical exception text omits entered values. Catalogs supply generic localized messages; a future presenter must render field/task context appropriately. Spanish terminology requires first-UI review, as in F2.

## Commands and stale data

`application/assessments/lifft_commands.py` supplies AddLifftTask, ReplaceLifftTask and RemoveLifftTask. Each satisfies the generic EditCommand contract and includes the target DocumentKey and a localized action-label key. Insert takes a validated zero-based position. Replace preserves task identity/order. Replace and remove require the exact expected task snapshot and reject newer or absent values. Unrelated task changes do not invalidate an edit. This is a single-owner-session precondition, not concurrent database locking or a revision-token solution for asynchronous work.

All commands return new drafts without mutating inputs or performing I/O. Session undo restores original task values, missing fields, unit metadata and order. Equal-state replacements preserve redo. Failed duplicate/position/identity/stale edits preserve history and dirty state. Calculated results are absent, so stale derived results cannot be carried forward by these commands.

## Verification and remaining work

Thirteen new tests cover missing versus zero, field-specific nonfinite issues, finite data retention, invalid units/IDs/duplicates, immutable collection ownership, insert/edit/remove with full undo/redo, edge/invalid insertion positions, duplicate atomicity, stale replacement/removal, absent/changed identities, no-op redo retention, cross-project ownership and catalog completeness. All 56 project tests passed; combined coverage 98.51%, both new modules 100%. Ruff/format, strict mypy (22 source/tool files), architecture and builds passed. `f4_validation.json` records isolated package smoke, source integrity and lock verification.

Next: define a versioned serialization contract for this draft with round-trip and corrupt-input tests, then a transactional storage adapter that satisfies DocumentStore without accessing operational databases. Expand project open/close/save lifecycle and address Save As policy before implementing it. Add model input validation and characterization of full LiFFT formulas only after resolving the documented metric-moment review gate. GUI/VTK dependencies still need exact-version approval before installation. No interface changed or visual acceptance is claimed in F4.
