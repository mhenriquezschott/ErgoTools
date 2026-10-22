# Worker birth-date calendar correction — 2026-10-18

Owner-requested correction during the four-worker acceptance workflow. Opening an
unspecified date of birth now browses the month eighteen years before today
(October 2008 on the acceptance date), instead of December 1899. The internal
minimum-date sentinel still means no birth date; browsing does not create a date,
age, storage write or hiring-age restriction. Saved birthdays retain normal Qt
selection/navigation. No domain, schema, dependency or reference change.

The existing WorkerManagementDialog event filter owns calendar opening as well as
directory resize behavior. The calendar show event changes only its visible page.
The changed method documentation and bilingual regression were substantively reviewed;
their exact review hashes and generated inventory are renewed.

Focused tests: 11 pass, including both EN/ES missing-date browsing, unchanged
missing birth date after Save, saved-date handling and another New worker.
Eight XCB widget captures (form and popup, blank/saved, EN/ES) inspected in
artifacts/worker_birth_calendar_review. The initial root-screen capture was black
under Wayland and was replaced with direct widget captures. Initial sandboxed XCB
startup was unavailable; actual display access was used for native verification.
Required final standards/test/build gate passes: 1,381 tests, zero
failures/skips, 95.40% coverage. Standards, strict types, architecture, naming,
documentation/review and wheel/sdist builds pass. The packaged changed module
is byte-identical to reviewed source. See artifacts/worker_birth_calendar_validation.json.

## Owner workflow checkpoint

The owner confirms empty Metric project Save/close/reopen through Recent Projects
and all four saved workers surviving another close/reopen. Read-only inspection of
workflow_4_workers.ergprj verifies four worker records and their demographics, zero
organization/assignments/Jobs/assessments, valid integrity/foreign keys and unchanged
file bytes. W04 Diego stores **85 kg**, whereas the suggested baseline was **65 kg**;
reported to the owner and left untouched. Hiring dates default to 2026-10-18.
Evidence: artifacts/owner_workflow_workers_checkpoint.json.

## Save-workflow review — proposal only

Current WorkerManagementDialog.save_worker calls
ProjectWorkspace.save_worker_catalogs, which validates and immediately commits worker
and classification catalogs together. Assignment creation/deletion have their own
persistence paths. Close does not retain uncommitted form text. Main workspace Save
currently handles active/retained assessment sources and returns False without an
active assessment. Removing the local Save button would therefore lose edits.

Recommended owner-requested simplification: project-session worker drafts survive
worker navigation and dialog closure; the existing main Save validates and commits
those drafts even without an assessment; project closing/switching offers
Save/Discard/Cancel, including failed-save retention. Defining how assignment,
delete and classification operations participate is required before implementation.
No unified-save code or other management/PLOT/JROT changes were implemented here.
Manual workflow testing remains paused at workers while the owner considers this.
Linux migration and cleanup remain complete at 100%; no new milestone.
