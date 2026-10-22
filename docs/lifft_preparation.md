# LiFFT input preparation and freshness — F13

## Implemented boundary

`application.assessments.lifft_preparation.prepare_lifft` captures the active immutable draft, document identity and session-local revision, and collects ordered input issues. The frozen LifftPreparation retains its originating session by identity. It performs no calculation, persistence, edit or history mutation. `has_valid_inputs` means that the source passed input checks, not scientific approval or guaranteed successful arithmetic.

`domain.assessments.lifft_validation.validate_lifft_input` is the existing task calculator's input guard extracted into a shared function. `lifft_draft_issues` uses that same function to report every issue in task order and lever-arm/load/repetitions field order. This prevents preparation and calculation from drifting into different numeric rules. Missing, boolean, negative and nonfinite inputs retain their established issue codes. Fractional and zero values remain accepted. An empty assessment reports `validation.tasks_required`, translated into English and Spanish. Existing reference numerical fixtures still pass unchanged.

Incomplete inputs are never silently replaced with zero, and preparation publishes no partial totals. This intentionally differs from the reference's incomplete-row calculation/zero-repetitions preview. A later UI may display an explicitly marked preview, but must not present it as a complete assessment. Complete zero inputs remain distinct from absent tasks/fields. The isolated F12 aggregator may still summarize an empty result tuple for callers; F13 rejects an empty source draft as incomplete for assessment preparation.

## Freshness contract

Call `prepared.is_current(actual_active_session)` before publishing or reusing derived work associated with that preparation. It requires the same session object, revision and source object. Passing None represents no active session. Saving without editing preserves freshness; edits invalidate it. Undo to the exact captured revision restores freshness, and redo restores the corresponding preparation. A new branch has a fresh revision even if its source equals an earlier draft. A reopened/reloaded session is different even if its document ID, revision zero and source values match. This prevents cross-session revision collisions.

These checks are available contracts, not automatic result-cache invalidation or a wired presenter. Callers must pass the actual active session, not retain and pass an obsolete session. The private reference keeps the origin session alive: retain only preparations needed by the active operation and discard them on close/switch. The immutable source/issues remain snapshots even as the origin session changes. This is a synchronous owner-thread contract, not background-task cancellation or synchronization.

Preparation does not certify arithmetic bounds: sufficiently large finite inputs may still overflow at calculation. Calculation preserves its own overflow guards. Structural draft validation and the typed input contract remain prerequisites; the shared numeric helper is not a general locale-aware text parser.

## Evidence and limits

Nine new tests cover ordered multiple issues, empty versus zero/fractional inputs in both unit systems, exact edit/undo/redo/branch identity, failed/no-op edits, real in-memory SQLite save/load, another session sharing the same snapshot, close, source/history immutability, numeric boundaries and both translations. 158 tests pass; combined coverage is 99.33%. The two new modules have 100% combined coverage. Ruff, formatting, strict mypy across 38 files, architecture and both builds pass. See `f13_validation.json` for isolated wheel, unchanged reference-tree and dependency-lock evidence.

No live model coordinator, result cache, GUI, background calculation or scientific validation was introduced. The metric-moment scientific-review gate remains open before full LiFFT workflow integration. The original environment and application remain unchanged.

## Next slice

Characterize the original DUET model and its assessment call sites before extracting the next pure calculator. Preserve the same input, reference-fixture and documentation standards. LiFFT view integration remains contingent on metric review and approved GUI dependencies; Save As, full localization, legacy migration and native packaging are still pending.


## F76 subsequent integration

The original-style grid now supports an explicitly marked incomplete-row preview
and the original task-count dialog. This supersedes earlier pending/full-row-only
statements about grid interaction above. Strict preparation and non-grid evaluation
remain unchanged. See [current workflow and limits](lifft_grid_workflow.md).
