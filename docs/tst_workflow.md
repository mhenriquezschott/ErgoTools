> Current owner-approved task-capacity and unused-row policy (2026-10-18)
> supersedes historical clear-on-count-change and unused-slot partial-status wording
> below. See [current behavior](task_grid_resize_acceptance.md).

# TST source workflow — F22, 2026-09-29

TST now participates in the new project's source editing, history, catalog and persistence workflows. This is backend integration, not a runnable desktop assessment or scientific approval. No interface or dependency changed.

## Source and history contracts

`TstDraft` owns original measurement units and an immutable ordered tuple of uniquely identified tasks. Missing fields remain `None`. Preparation collects all direction, arm, load and repetition errors in row/field order using the same validators as the isolated calculator. Invalid physical inputs can remain editable; finite signed values and fractional repetitions can be saved for review. Nonfinite values, booleans and invalid direction types cannot be saved.

`AddTstTask`, `ReplaceTstTask` and `RemoveTstTask` use document ownership, stable identities and expected snapshots. Failed commands preserve history and the clean marker. `TstProjectEdit` prevents applying these commands to another assessment model. Undo/redo restores exact original source, including units and directions, without rerunning calculations. Command labels and review issues have English/Spanish messages.

## Persistence and compatibility

The strict `ergotools.tst-draft` version-one JSON source format stores `system`, ordered tasks and explicit model direction IDs: `"0"` handling loads, `"1"` downward and `"2"` horizontal; null means unfinished. It never stores or converts UI selector indices. The reference selector swap documented in [F21](tst_summary.md) remains isolated and unresolved. This format must not be used to infer directions from legacy rows without that review.

The existing mixed envelope gains an explicit `tst` tag with the nested TST source. Project version two and the mixed database schema remain unchanged: their tagged payload design supports another source kind without table migration. Previous readers reject unknown tags rather than guessing. Version-one LiFFT projects still reject TST inserts/saves and are not automatically upgraded. These formats do not import original operational `.ergprj` databases.

TST uses the shared mixed store; a redundant standalone TST database adapter was not added. Transactional type-identity guards prevent replacement of any saved model with another. Duplicate insertion fails. Failed SQL writes roll back and preserve the previous saved source; sessions stay dirty until a successful retry. A separate reopened connection verifies saved model identity, directions and units.

## Evaluation gates

Input errors take precedence over review outcomes. Every otherwise valid TST source returns `REVIEW_REQUIRED` with `review.tst_direction`. Metric TST also returns `review.tst_metric_moment`. Both carry no task results or summary; there is no bypass flag. This blocks calculation even for a valid but numerically enormous task. Switching from a completed DUET assessment clears its cached result before creating a TST outcome.

Preparation/outcome freshness uses the exact active session, revision and source identity. Saving does not invalidate source identity; edits do. Undo can restore eligibility for a retained outcome. A reloaded equal-valued source belongs to a different session and cannot reuse the old result.

## Evidence and remaining work

Thirteen new workflow tests cover all directions/units, incomplete and malformed sources, exact round trips, stale/wrong-document/wrong-model edits, history, localization, review gates, real SQLite failure/retry, three-model reopening, duplicate/type protection, version-one rejection and workspace create/save/switch. Existing task/summary reference fixtures continue to run. Full gate and independent wheel/integrity evidence are recorded in `f22_validation.json`.

Scientific review of TST direction labels and metric conversion is still required. No GUI, unit-switch action, Save As, legacy import, native platform testing or visual acceptance is implied. The next source workflow is reference characterization of unit switching and its history/persistence semantics; implement conversion commands only after distinguishing input conversion from the disputed calculated moment display.
