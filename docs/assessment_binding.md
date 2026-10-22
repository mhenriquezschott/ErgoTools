# Persisted assessment ownership — F31

The optional AssessmentBindings application port links an existing document to
one exact AssessmentContext. AssessmentBinding rejects cross-project ownership.
This association is metadata separate from task edit history: binding does not
save unsaved tasks, clear dirty state or add an undo command.

## Format and compatibility decision

`AssessmentProjectFile.create_contextual(path, metadata)` explicitly creates a
version-three project. It retains the mixed draft payload format and adds
`assessment_bindings`. Ordinary `create` and `create_with_document` still create
version two; the temporary desktop harness therefore keeps its existing format.
Opening versions one/two does not migrate or add tables. Their ownership APIs
raise StoreFormatError. The earlier LiFFT-only ProjectFile remains unchanged.

The table stores project/document IDs plus worker, plant, section, line, station,
shift and model. The document identity is its primary key; exact context has a
separate unique constraint. SQLite's default binary comparison preserves case
and whitespace. Identifiers are bound SQL parameters, including quotes and
non-ASCII text. Job IDs do not participate in assessment ownership.

## Transaction and lifecycle contract

- Bind only an already persisted draft with matching project and model.
- Validate the source and association under BEGIN IMMEDIATE on the dedicated
  connection; commit the association before returning.
- Repeating an identical binding is idempotent. A different binding for the same
  document raises ValueError; another document claiming an occupied context
  raises SQLite IntegrityError. Failed writes roll back and remain retryable.
- `assessment_binding` raises KeyError for a missing document and returns None
  for a saved but unbound document. `find_assessment` returns None for an absent
  exact context. Neither changes active selection, source state or history.
- Opening version three validates every stored association against its source,
  project, typed identifiers and model before returning the owned handle.
- Existing source saves preserve ownership and retain their model guard. Closed
  project handles reject all ownership operations.

Association and initial draft insertion are separate explicit transactions in
this slice. Failure to bind leaves an unbound saved draft, not a partial binding.
There is no combined create-and-bind workflow, rebind/unbind/delete API or implicit
relocation. Such lifecycle policies must be designed before UI integration.

## Evidence and limits

315 tests pass, including eleven additional cases. Temporary databases cover all
three tools, exact ownership isolation, idempotency, model mismatch, duplicate
contexts, reassignment rejection, injected SQL failure/retry, dirty-state/history
preservation, reopen, damaged associations, failed creation cleanup, closed
handles and byte-for-byte preservation of versions one/two. Both new modules
have 100% combined coverage. Standards, typing, architecture and builds pass;
`f31_validation.json` records independent wheel and reference integrity checks.

This schema is for new-format projects, not a legacy import. Worker/workplace
catalogs are not yet migrated, so their existence is not enforced. There are no
foreign-key cascades or deletion behavior: adapters validate source references,
and direct SQL writes remain unsupported outside deliberate corruption tests.
Single-owner/thread use is retained; multi-writer merging and power-loss recovery
are not certified. No UI or scientific formula changed. Next: application-level
context selection through the workspace with explicit dirty-choice handling,
then worker/workplace catalog integration using focused fixtures.
