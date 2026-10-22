# One assessment per assignment and ergonomic tool

Owner-approved correction: remove the unrequested New blank version and Set current
version feature completely, including frontend controls/handlers, application mutation
port/methods, domain version/status/currentness fields and database version storage.
New assessment and Assessment context keep their ordinary worker/job/workplace/tool
selection and first-Save workflow. Save updates the sole assessment. Job risk-profile
versions are a separate original feature used by JROT and remain unchanged.

## Database contract

assessment_ownership replaces assessment_history. Its only columns are document_id,
assignment_id, kind and insertion position. document_id is the primary identity;
(assignment_id, kind) is unique. assignment_id references worker_assignments with a
deferred foreign key so transactional catalog replacement cannot strand saved ownership.
The repository enables SQLite foreign keys; domain validation independently rejects
duplicate owners and storage validates the exact column contract. The empty historical
assessment_bindings table is removed from assignment-owned/full projects. It remains
only in diagnostic context-bound formats where actual binding functionality uses it.

No alternate assessments, superseded-value archive, version numbers, assessment lifecycle
status or current-version flag remain in current native storage. draft_documents holds
task inputs, saved_assessment_results holds the single source-bound calculation, and
assessment_ownership holds the worker assignment/tool relationship. Those are three
functional responsibilities, not three copies of the scientific result. Closed worker
assignments remain real owners of their assessments and are not assessment versions.

## Upgrade and data preservation

Format 15 identifies the schema change. The separate removable external tool handles
full earlier native formats 8–14. Normal Open offers the already existing external
conversion workflow; no legacy/version reader enters normal application code. Originals
are opened read-only and conversion happens in a private backup. Format-14 upgrades
preserve every retained task/result payload and all unrelated database rows, including
PLOT images/geometry, JROT schemes/timestamps, Job placements/profiles and worker data.
Older rounded result-envelope conversions retain the approved calculation policy.

The comparative input contains one additional empty LiFFT draft; only that verified
empty, noncurrent duplicate with no result is removed. A group containing competing
populated assessments is rejected before SQL changes; real data is never silently
selected, merged or discarded. A missing assignment, mixed ownership schema or populated
obsolete context bindings is rejected. Publication validates before exclusive creation;
an existing destination cannot be overwritten. Save As/Backup remain single-file native
operations and require no converter after upgrade.

Current converted fixtures: test_projects/native/comparative_risk_test.ergprj and
integrated_test.ergprj, each with 194 assessments/results. These standard files are
updated in place; no duplicate current folder or obsolete native fixtures remain. Use
`bash tools/run.sh test_projects/native/comparative_risk_test.ergprj` from the new root.

## Acceptance evidence

Independent tests compare complete row multisets and exact source/result bytes through
conversion, Save As snapshot, backup and reopen; verify schema columns/removed tables,
SQLite integrity/foreign keys and domain uniqueness; prove populated duplicates refuse
without mutation; drive all three tools in English/Spanish with absent version actions;
and prove direct duplicate/dangling writes roll back. See
artifacts/single_assessment_independent.log, artifacts/ownership_upgrade_preflight.json
and the final gate/native evidence recorded in STATUS when complete.

Removed tests specifically exercised the rejected version feature. Normal ownership,
closed-assignment isolation, failure/rollback, scientific, UI, PLOT/JROT and file-lifecycle
regressions remain; their obsolete version expectations were replaced by the unique-owner
contract rather than suppressing failures. No original golden calculations were changed.


## Final acceptance

The four requested correction areas (UI, core API/model, database schema, conversion/
workflow verification) are **4/4 complete (100%)**. This is a bounded owner-approved
correction, not an added migration milestone; fixed migration/cleanup ledgers remain
12/12 and 6/6. No dependency, calculation, risk palette or reference application changed.

Final required gate: **1,334 tests passed, zero failures/skips; 95.66% combined
coverage**. All standards/types/architecture/naming/documentation/source-review/build
checks pass (259 typed sources/tools; 417 maintained files; 55 changed files reviewed).
The lower suite count is deliberate: 13 tests specifically exercised the rejected
version feature; 10 independent acceptance cases replace it with the unique-assessment
contract. Original calculation golden fixtures were not changed.

Thirteen native English/Spanish captures were inspected: main LiFFT/DUET/ST, expanded
Project menus, PLOT/JROT, and diagnostic preview. The two version actions, buttons and
handlers are absent. All 194 task/result sources remain unchanged after browsing. Both
current test projects have exactly 194 assessments/results, all embedded images and
seven/five JROT schemes, respectively. SQL integrity/foreign-key checks pass, there are
17 required tables plus the optional stored-precision table documented in database_tables.md, and no assessment_history or
unused full-project assessment_bindings tables. File/codec and approved Job risk-profile
versions remain because their original functionality requires them.

Evidence: single_assessment_validation.json; artifacts/single_assessment_final_check.log;
artifacts/single_assessment_independent.log; artifacts/single_assessment_review/validation.json;
artifacts/single_assessment_reviewed_files.json and artifacts/ownership_upgrade_preflight.json.
Early regression logs retain outdated version expectations and the discovered file-picker
timer race. That test now inspects the same real owned dialog at exec with unchanged
extension/default-suffix assertions, avoiding global-modal/zero-delay timing; product
file-picker code is unchanged. No failures were suppressed.

Current files are under test_projects/native and open directly without conversion.
The obsolete native fixtures were replaced at their established paths. Opening a
separate old user project still offers the external upgrade workflow. Populated duplicates
require a specific data decision; the converter will not discard real input. Restart
running instances to load the corrected UI/model. Windows/macOS native acceptance stays
deferred as agreed. Local Linux delivery is rebuilt with the updated wheel, guides,
external removable tool, current projects and checksums.
