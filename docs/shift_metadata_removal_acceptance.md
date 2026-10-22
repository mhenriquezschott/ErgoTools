# Recurring Shift metadata correction — 2026-10-19

The owner explicitly requested removing Incidents reported and Ergonomic risk events
because a Shift describes a recurring schedule rather than a particular date.
Both editors and their unused English/Spanish localization entries are removed.
`OrganizationRecord` rejects both names, even with empty values. No replacement
incident tables, event infrastructure or dependencies are introduced.

## Native storage and conversion

Native format **17** retains the existing SQL tables/keys and hierarchy envelope.
The reduced field contract changes the allowed Shift attribute pairs inside
`work_catalog`; formats through 16 are not silently decoded as current projects.
The existing removable external converter handles earlier full native formats 8–16.
It filters exactly these two Shift fields before strict native validation, inside
its private transaction, and publishes exclusively to a separate output. Unknown
remaining fields still fail. Format-14/15/16 source/result payloads are retained
exactly, without recalculation. Original XML conversion selects only maintained
organization fields; frozen original schemas and files remain unchanged.

Under this explicit field-removal instruction, old populated values are removed too;
regressions exercise populated and empty cases. No values are hidden in archives.

## Maintained project update

The two maintained fixtures and `workflow_4_workers.ergprj` were updated at their
existing paths. The owner saved and closed the live workflow project before its
update. All five Shift records contained only null values for the removed fields:
four pairs in each maintained fixture, two in the workflow file. There was no
populated incident information to discard. Private conversion output was validated
before the bounded fixture update; no parallel maintained projects or backups exist.

Full database comparisons show changes only to project format metadata and the two
removed attribute pairs in `work_catalog`. Every other table/row, exact task/result
payload, image and rotation timestamp is unchanged. Integrity/FK checks and direct
native reopening pass. See [fixture evidence](../artifacts/shift_metadata_removal/fixture_migration.json).

## Verification

Focused regression: **181 passed**. New tests cover domain/UI rejection in EN/ES,
format-14/15/16 empty/populated conversion, source byte immutability, exact unrelated
rows, conversion dispatch, missing transaction and rejection/rollback of unrelated
invalid fields. Existing maintained native tests were updated in place to expect
format 17; no duplicate test projects were introduced.

Twelve native XCB form captures inspected: EN/ES expanded top, pending Notes,
Undo, collapsed, minimum-size reopened bottom and new empty Shift. Existing clocks,
following-day option, view preservation and bottom controls remain usable; Notes is
fully visible when scrolled to the bottom. Both changed packaged Help sections
were rendered and inspected. See [visual evidence](../artifacts/shift_metadata_removal/visual_validation.json).

Required native Linux gate: **1,885 passed, zero failures/skips, 94.50% coverage**;
standards/format/types (266), architecture/naming/documentation and wheel/sdist
builds pass. Independent wheel: **220 passed / 78 subtests**, all 244 package Python
files and both guides equal reviewed source; converter excluded. Final wheel equals
the tested wheel. The final return-doc correction retained identical executable AST
and passed the renewed documentation checks. Gate/package results are recorded in
[validation](../artifacts/shift_metadata_removal/validation.json).
All sixteen changed maintained files received substantive contract/documentation
review; the independent reviewed hashes and generated symbol inventory were renewed.

Approved Linux migration and cleanup remain **100% complete**. This is a bounded
owner-requested correction, not a new milestone. Windows/macOS acceptance remains
deferred. Reference application, original fixtures, calculations and lock remain
unchanged. Next: restart ErgoTools, open the existing workflow project and obtain
owner feedback before resuming the four-worker workplace association tests.
