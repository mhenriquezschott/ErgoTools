# Historical creation through the workspace — F47

This advances the creation side of the documented worker/job assessment workflow.
ProjectWorkspace.create_assignment_assessment accepts an explicit
AssignmentAssessment and initial source. The optional HistoricalProject capability
provides non-mutating preflight and atomic source-plus-ownership creation.

Cancel or absent dirty consent performs no repository I/O. Preflight checks source
model/serialization, hierarchy and assignment membership, existing document IDs,
version uniqueness and current-owner conflicts before any requested old-source
save. It runs against one read snapshot. The workspace also rejects source revision
changes or nested transitions during preflight.

After preflight, an explicitly requested old-source save precedes creation.
Repository creation rechecks constraints inside its write transaction; preflight
is not a reservation and does not replace final validation. Creation failure leaves
the old session active, possibly clean if its separately requested save succeeded.
Successful creation activates a clean new document without changing project
ownership or recent-file settings. The operation does not modify assessment undo
history for the prior document.

Version, status and currentness are explicit inputs. Existing current assessments
are never silently demoted. Creating a noncurrent historical version still activates
that newly created document; later assignment-based selection resolves the saved
current version. Current-version switching, automatic version allocation and
active-assignment eligibility in the presenter remain separate work.

Three new integration scenarios cover multiple paths: dirty consent, model/owner/
version/current/ID rejection before old save, successful save/create, nested calls,
reentrant source edits, failed save, late creation failure and retry, unbound ID
collision and unsupported legacy adapters. All 451 tests pass; combined coverage
98.95%, workspace 100%. Ruff/format, strict mypy (99 files), architecture and builds
pass. Extracted-wheel creation and reopen also pass. All 500 original files and
the dependency lock remain unchanged; see f47_validation.json.

This is an application capability, not new desktop controls. Assignment-aware
presenter state, context-dialog host integration and current-version lifecycle
remain pending. No schema, dependency, formula or UI change occurred.
