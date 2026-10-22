# Organization input cleanup — 2026-10-19

Owner-directed correction: optional Plant opening and Section/Line/Station creation
dates use calendars. Plant operational hours becomes a daily duration with native
hour/minute quantity controls. Remove Station task_description, equipment_used,
ergonomic_risk_level, performance_metric, power_consumption and materials_used from
form/domain/storage. Replace editable Plant number_of_shifts with a derived display.

## Field contracts and UI

`OptionalDateEdit` wraps standard Qt calendar/section entry, retaining canonical ISO
dates and an independent absent state. An unspecified popup begins at today, without
an inferred value merely from focus/opening. A real first click on today's unchanged
navigation anchor provides the date. Ctrl+A/Delete clears it; no valid date is used
as an empty sentinel. Valid Python/Qt explicit setters and native stepping are
supported. Existing organizational dates are all valid ISO values and are unchanged.

`OptionalDurationEdit` composes native hour/minute spin controls, accepting absence,
zero through 24 hours and whole minutes, with a full day distinct from zero. Existing
9.0 hours remains 9.0; 9h30min stores 9.5. There is no clock wrap or persisted UI flag.
Subminute, nonfinite or over-day retained values stop conversion rather than being
silently rounded/clamped. The retired-field data in these fixtures is empty/zero,
except the obsolete Plant count of 1 in the comprehensive fixtures.

Shifts are independent project-wide definitions. The owner explicitly clarified that
the calculated count must include only distinct shifts used by workplace assignments
or Jobs in that Plant. **Shifts in use** reads active Job placements and active worker
workplaces (including unclassified assignments), deduplicating shift IDs across
stations/Jobs/workers and excluding unrelated Plants and inactive links. Unused
project Shift definitions do not count. A Plant without usage therefore shows zero.
No new relationship/table is needed. The derived label is outside editable form
tokens and storage, so it does not add dirty states or history commands. The workspace
projection preserves existing hierarchy/Job snapshot authority. Job edits and shared
Undo/Redo refresh the label from current private project data.

All edited calendar/duration fields participate in the existing shared project
history and main Save. New native typing ownership is limited to the new adapters;
existing worker date/quantity behavior is unchanged. Organization tree expansion,
optional-details choice and mouse Undo behavior remain under their existing policy.
There are no new icons, dependencies, calculations or business tables.

## Format and fixture migration

Native format **18** gates the reduced metadata and stricter date/duration contract.
SQL tables/keys and the hierarchy JSON envelope are unchanged. The removable external
converter supports full native formats 8–17; its appropriately renamed organization
filter removes the explicitly retired fields inside a private transaction before
strict validation. Unknown retained fields/data still fail. Format-14/15/16/17
assessment input and result payloads remain exact; no recalculation is introduced.
Frozen original files/schemas remain unchanged; the original reader selects only
current domain fields. Runtime imports no old schema reader.

Both maintained fixtures and `workflow_4_workers.ergprj` were updated at their same
paths. No live process held these files when updated. A private output was validated
and fully compared before the bounded transactional in-place update. No parallel
fixtures or backups were made. Removed pairs: 136 in each comprehensive fixture and
13 in the workflow file. Dates and duration values are retained exactly; all unrelated
database tables/rows, source/result/image/scheme bytes and timestamps are exact.
Integrity/FK checks and direct native reopening pass. See
[fixture migration](../artifacts/organization_input_cleanup/fixture_migration.json).

## Validation

Required final native Linux gate: **1,925 passed, zero failures/skips,
94.46% coverage**; standards/format/types (268), architecture/naming/documentation
and wheel/sdist builds pass. Final count/input focused checks: 170. Independent
wheel: **260 passed / 78 subtests**, all 246 package Python files and both Help guides
equal reviewed source; converter excluded. The final wheel equals the tested wheel.
The earlier 1,923-test gate was superseded after the owner's count clarification;
unchanged date/duration and conversion evidence was reused. Final evidence is in
[validation](../artifacts/organization_input_cleanup/validation.json).
The new cases exercise domain rejection, real calendar first-click behavior,
absence/zero/full-day duration boundaries, invalid/lossy values, each location's
calendar Save/reopen/Undo/Redo, Plant usage deduplication/inactivity/other-Plant boundaries and live Job Undo/Redo, and empty/populated obsolete
conversion while preserving source bytes and unrelated rows.

Thirty native XCB captures inspected via contact sheets and full-size enlargements:
EN/ES all four populated calendars/native popups/new empty forms, Plant top/count
and duration/bottom, minimum Station and collapsed details. Both updated packaged
Help sections rendered and inspected. Existing scrollable Plant form exposes every
field; no changed labels or bottom controls are clipped. See
[visual evidence](../artifacts/organization_input_cleanup/visual_validation.json).

Twenty-two maintained files received substantive source-contract review and renewed
independent hashes/symbol inventory. Linux migration/cleanup remains **100%**; this
bounded owner correction adds no milestone. Windows/macOS remain deferred, not
passed. Next: owner reopens the workflow file, checks these input changes, and
resumes the agreed four-worker workplace association workflow when ready.
