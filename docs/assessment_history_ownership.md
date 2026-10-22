# Historical assessment ownership — F44

The reference IndividualAssessment table scopes version identity to
(worker_assignment_id, tool_id, version), with positive versions and at most one
is_current row per assignment/tool. Different assignments at the same workplace
can each retain a current assessment. Assignment activity is not an assessment
ownership constraint.

AssignmentAssessment and AssessmentHistory now express this in the pure domain:
document identity, assignment ID, explicit model, version, status and currentness.
The document ID maps to the modern source-document identity; legacy assessment
integer IDs are not automatically converted or imported. Collection order is
retained and duplicate documents/version keys/current owners are rejected.

Reference status values are draft, complete and superseded. SQL does not couple
status with currentness, so the model allows a superseded current row, a complete
noncurrent row, zero current rows and version gaps. These are storage contracts,
not approval to publish results or bypass scientific validation.

validate_jobs requires exact project and assignment membership, including inactive
assignments. current_for resolves only the supplied assignment/model; it never
falls back to another assignment at the same worker/workplace. After reassignment,
the prior assessment remains owned by the closed row and the new row initially
has no current assessment. Distinct histories may coexist at that workplace.

Nine frozen cases execute the actual reference table and unique-index SQL under
Python 3.10.18 against synthetic in-memory data. Foreign keys are not enabled in
that isolated constraint capture; assignment membership is separately tested
against the typed job catalog. Additional tests cover reassignment/removal,
foreign projects, malformed types, ordering and absent current versions.

This checkpoint does not change persistence or existing context bindings. Source
existence/model validation, atomic assessment creation plus assignment ownership,
protection against deleting or repurposing referenced assignment rows, current
version transitions and legacy import remain repository/application work.
Persisted worker/workplace bindings must not silently become historical links.
No final historical parity or UI integration is claimed yet.

Validation: 435 tests pass (4 new, including nine reference cases); combined
coverage 98.94%, new module 100%. Ruff/format, strict mypy (97 files), architecture,
builds and isolated-wheel ownership checks pass. All 500 reference files and the
approved dependency lock remain unchanged. See f44_validation.json and archived
capture/verification scripts. No schema, dependency, scientific or UI changes.
