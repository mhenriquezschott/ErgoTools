# Hiring-date investigation — owner resolved, 2026-10-18

Owner resolution: the attempted hiring dates were in the future. The owner confirms
past-date selection works; the existing maximum-of-today rule explains the report.
No code correction is needed. Resume the four-worker workflow test.

The owner initially reported that selecting a new hiring date in the calendar is ignored until
another worker field (for example sex) has changed. Birth-date selection itself works.
The owner confirms a calendar day click but cannot identify one exact failing target.
After private-copy checks did not reproduce this, the owner explicitly authorized
checking the actual `test_projects/native/workflow_4_workers.ergprj`, allowing changes.

## Direct checks

The current integrated application opened that exact path on an isolated native XCB
Qt display with VTK enabled. Actual directory clicks selected W04 Diego. Twenty-seven
cases covered first hiring edits, prior birth-date changes and prior sex changes,
using current-month days 17/11/1, September 18, 2025-10-18, 2012-06-15, 2000-01-01,
1950-01-01 and tomorrow. Each valid date was accepted on its first calendar click;
future selection consistently respected the existing maximum of today. Changing sex
or birthday did not alter that policy. All 27 cases matched expectations. Cancel
returned to saved worker details between independent attempts; this matrix did not
write the saved project.

A separate direct-file sequence selected October 15, 2026 before any other edit,
clicked shared Undo (October 18), Redo (October 15), closed/reopened Worker Management,
used main Save, closed/reopened the project and checked the date again. All passed.
The date was then restored using the calendar and main Save to October 18, 2026.
Read-only full-table comparisons establish that every original database table row
was restored. The temporary saved change affected only `work_catalog`.

Six full-window captures were visually inspected: first hiring edits before/after
other demographic edits and pending/Undo/Redo states. Date text, history buttons and
bottom controls fit. These are investigation observations, not evidence that the
owner's reported refusal has been repaired.

## Project state and limitations

Original SHA-256:
`6f3f93e87c94c438151c8314b4faa6011c53ec0b45ca9e0029fec9e40177d27c`.
After authorized Save and original-data restoration:
`4acaaa7af1bcf02a1620813844a7396ed579db9bbcd4bdc525bcb093eee20937`.
Logical table rows are identical; SQLite publication can change file bytes. Do not
replace this live owner project from historical hashes or copies. Four workers remain;
Diego retains his original birth date, Male, 175 cm, 65 kg and 2026-10-18 hiring date.
No original reference or other maintained native fixture was changed.

No implementation change, speculative workaround or additional infrastructure was
introduced. No full regression gate was repeated for unchanged code. The previous
1,406-test/94.29% gate remains the accepted code evidence. Migration/cleanup remain
100%; Windows/macOS acceptance stays deferred. The direct checks have not established
the cause of the owner's different running-session behavior.

Next: resume standalone worker-assessment testing before adding real organization
and assignments. The hiring-date report is closed by the owner's clarification;
no source or date-policy change is authorized or necessary.

Raw native logs and JSON evidence are in
`artifacts/worker_hiring_date_investigation/`; `direct_project_probe.json` records
all 27 outcomes and `direct_save_reopen.json` records publication/restoration.
