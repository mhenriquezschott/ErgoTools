# Atomic assessment creation and binding — F37

AssessmentProjectFile.create_bound_assessment inserts a new draft and its context
binding in one BEGIN IMMEDIATE transaction. It validates project/model identity,
encodes the source, checks document uniqueness, then validates and writes ownership.
Version-four catalog membership remains enforced; version three preserves its
catalog-independent behavior. Versions one/two reject the operation without migration.

Source insertion and binding now expose explicit transaction-composition helpers.
They require an active caller-owned transaction and never commit independently.
The project repository owns rollback/commit for the combined operation. Standalone
save/insert/bind retain their existing transaction ownership and semantics. Callers
of composition helpers must roll back on failure; these helpers are adapter-level
operations, not workspace APIs.

Any failure—including missing owners, occupied contexts or SQL errors on the second
write—removes both newly attempted records through rollback. Existing drafts and
bindings remain unchanged. Duplicate document IDs cannot be repurposed, and the
combined API is create-only, not idempotent. The older explicit separate insert/bind
APIs remain available; their documented possibility of an unbound draft is unchanged.

## Workspace behavior

create_assessment now accepts optional context. Without it, the previous unbound
creation workflow is unchanged. With context, a BoundAssessmentProject capability
is required; there is no fallback to two independent writes.

Cancel or missing dirty consent performs no repository I/O. Document-ID and occupied
context preflight precede a requested current save. Save then commits the old draft
before combined creation; Discard does not write it. The new clean session is
activated only after the combined transaction succeeds. If later creation fails,
the old session remains active and may now be clean because its separately requested
save succeeded. Model/source validation and catalog membership can still fail at
that later boundary. Old-save plus new-create is not one cross-document transaction.

No connection, recency or catalog-snapshot replacement is needed for successful
in-project creation. Catalog identity data remains unchanged, while subsequent
binding lookup can resolve the newly saved assessment.

## Evidence and remaining work

388 tests pass, including eleven additional cases. Tests exercise all three models
in versions three/four, model/ID/context conflicts, missing owners, real SQL aborts
at either insertion followed by retry, Save/Discard/Cancel, preflight ordering,
post-save creation failure, transaction-helper misuse, unavailable capabilities and
unchanged older formats. Shared draft/binding stores and workspace have 100%
combined coverage; full suite coverage is 98.77%. Standards, strict mypy (88 files),
architecture and distribution builds pass. Independent verification is recorded in
`f37_validation.json`.

No schema, dependency, default file format, UI or scientific behavior changed.
Only temporary synthetic databases were used. Next integrate catalog selection and
creation into reusable presentation/editor workflows, preserving reference layout
and dirty-text handling; complete worker/job record editing remains pending.
