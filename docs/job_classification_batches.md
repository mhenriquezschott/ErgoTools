# Batch assignment classification — F43

classify_assignments accepts an immutable JobCatalog, one worker ID, typed
ClassificationRequest records and an explicit calendar date. It returns a complete
replacement catalog; commit once through workspace expected-value replacement.
A later validation failure publishes no partial result and does not mutate input.

Behavior matches update_worker_assignment_jobs in the reference repository:

- Each requested row must be active and belong to the specified worker.
- A non-null target requires an active placement and job in that exact workplace.
  This check occurs even when the requested placement is unchanged.
- Unchanged classification retains the source; an entirely unchanged batch returns
  the same catalog object.
- Classifying an unclassified row retains its identity and notes, filling an absent
  start date. Unlike the single-worker assignment entry point, this path does not
  replace its notes with classification text.
- Changing or removing an existing classification closes the old row, retains an
  existing end date, and creates an active successor. Removal creates an
  unclassified successor rather than erasing the former row.
- Successor notes exactly match the reference batch operation.

Intentional command-boundary differences: requests address distinct rows in the
original snapshot, never successors created earlier in the same batch. Duplicate
requests are rejected. Explicit successor IDs must be unused across the snapshot
and batch when a new row is needed. The host still owns ID allocation and business
date selection. A conflicting database commit requires refresh/recomputation.
Reversed resulting date ranges fail through domain validation.

Six frozen executions of the actual reference function cover unchanged,
unclassified, changed, pre-existing end-date, removal and unclassified no-op
behavior. Minimal synthetic SQL isolates that function; full schema invariants
remain covered by other fixtures. Further tests cover late failure, two workplaces,
duplicate successor IDs, inactive/foreign targets and typed-input rejection.
The packaged-wheel smoke commits and reloads classification removal.

All 431 tests pass (5 new), combined coverage 98.92%, new module 100%.
Ruff/format, strict mypy (96 files), architecture and builds pass. All 500 original
files and the dependency lock match their recorded hashes; see f43_validation.json.
No dependency, schema, scientific or UI change occurred.

Historical assignment rows are preserved, but assessment bindings still identify
worker/workplace/model, not historical assignment IDs. This does not establish
final historical-assessment parity. That ownership migration, integrated editing
and context-dialog host wiring remain pending.
