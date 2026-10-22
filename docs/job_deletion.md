# Job deletion — F69

## Reference behavior and retained history rule

The original Job Management Delete button confirms the action and executes
`DELETE FROM Job`. Original schema constraints cascade to JobRiskProfile,
JobRiskMeasurement and JobPlacement. WorkerAssignment rows remain, with their
placement ID set to NULL. Existing IndividualAssessment rows remain attached to
those assignments. RotationTarget references restrict deletion of referenced
jobs, placements or profiles.

This was verified under the original Python 3.10.18 using extracted original
DDL and in-memory synthetic records. `tests/fixtures/job_deletion_reference.json`
records unassessed, assessed and rotation-referenced cases with source hashes.
The capture uses minimal identity-only stubs for external parent tables; it
checks the specified foreign keys, not every legacy migration or UI behavior.

The migrated history protection already requires an assessed assignment to retain
its classified job identity. Deletion therefore **refuses an assessment-linked
job**, with a readable message, leaving all records unchanged. This is a deliberate
stronger constraint than the original SET NULL behavior, not exact deletion parity.
No historical assessment source is removed, transferred or silently unclassified.
Other worker assignments retain their identity, context, dates and notes, becoming
unclassified when their job placement is deleted.

## Implementation

The existing management domain prepares remaining job/risk catalogs. The risk
store owns one transaction; assessment-history checks precede all deletion.
Measurements/profiles and placement/job rows are removed together; worker
assignment placement links are cleared. Any failure rolls everything back.
Job/risk snapshots are refreshed only on success; active assessment edits are
not saved or replaced. SQL stays in the infrastructure layer.

Risk-profile insert positions now append after the largest stored position.
Deletion can leave position gaps; using the surviving profile count would collide
with another stored position. Tests delete an earlier job/profile, then edit and
create a version of the surviving job to cover that actual sequence.

The Delete control is enabled for a selected existing job, uses the original
confirmation wording, and selects the first remaining job after success. Deleting
the last job produces an empty New job form. Typing a different ID into the
editable selector does not authorize deletion of a different record: the user
must select the saved job. A surviving job without profiles is labeled No profile.

## Validation and boundaries

587 tests pass, including 7 added cases and an extended last-job UI case. Checks
cover cascades, retained assignments, protected assessment links, missing jobs,
rollback at all four deletion stages, cancellation/confirmation, post-deletion
selection and profile creation after position gaps. Standards, strict typing,
architecture, package builds and isolated-wheel modal create/approve/delete/reopen
pass. Native Qt inspection covers the enabled control, confirmation, surviving-job
form, and protected-history message at the original minimum window size.

No schema, dependency or scientific formula change. Baseline original files and
dependency lock remain unchanged. The new format does not yet store JROT rotation
targets: their original RESTRICT behavior must be integrated before rotation
records or original comprehensive projects are admitted. This deletion operation
does not claim rotation-reference compatibility or import support. Full form
translation and final integrated application navigation remain outstanding.
