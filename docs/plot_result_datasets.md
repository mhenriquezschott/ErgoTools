# F105 — saved PLOT assessment datasets

PLOT Apply can now read actual saved project data through load_plot_results and
publish one complete PlotResults value. The original component API is exercised
with the real loader in tests. Production navigation remains disabled until the
complete PLOT workflow is composed; no markers or summary widgets are claimed.

## Source mapping and selection rules

The implementation follows plot_position_repository.py plot_worker_records
(lines 50-187) and plot_job_records (lines 190–270), and plant_layout.py getWorkers,
getWorkersAllTools and getJobRiskMarkers (around lines 5249–5660). These are the
active normalized implementations, not the retained transitional legacy method.

Worker rows require an active assignment and a current version. Assessment status
does not add a filter. Closed assignments and noncurrent versions remain saved
but stay outside PLOT. Ownership never falls back to a successor assignment.
Full hierarchy prefixes and an optional exact shift apply to both worker and job
rows. A literal saved shift All remains a literal identity; None means all shifts.

Demographic constraints apply only to workers. Job rows require active placements
and active jobs, independent of whether workers pass demographic constraints or
have an assessment for the selected tool. Assigned-worker counts include all active
assignments for that placement. Placement/date text does not imply additional date
filtering. Worker rows remain included when an associated job or placement is
inactive, matching the original left joins and assignment activity predicate.

Job evidence requires an active job and its current approved profile, with the
matching tool measurement. Draft, retired and noncurrent evidence is excluded.
A missing profile/tool measurement is None, not an invented zero. A recorded zero
is preserved; incomplete approved tool evidence remains explicitly incomplete.
Selected-tool and all-tool worker datasets come from the same scoped selection.
Worker-ID or binary last-name ordering is available. Ties use explicit worker,
assignment and model identities for deterministic output; original SQL did not
specify tie ordering.

## Evaluation, units and publication

The existing saved-assessment evaluator is shared with CSV export through
saved_assessment_summary. Ownership/project/model checks precede evaluation.
CSV keeps closed current assignments; PLOT excludes them before loading source.
This avoids using export's broader scope as a PLOT query.

Worker result damage is dimensionless and probability is 0-1. Job evidence
probability remains its recorded percent scale. Source units are preserved;
display settings cannot rewrite saved assessments or approved measurements.
LiFFT metric-moment and Shoulder Tool review gates remain enforced. Partial grid
totals retain explicit partial status; invalid/review outcomes retain None values.
Recalculated saved-source outcomes are a deliberate continuation of the migrated
evaluation policy, not certification of legacy cached results or scientific models.

The loader reads through a separately owned project connection, closed on success
or failure. It never sees the active editor, commits pending input, upgrades the
project or writes data. All selected sources are loaded/evaluated before returning;
errors propagate to the existing filter-panel error boundary. The caller publishes
only after successful return. No speculative synchronization or background-thread
infrastructure was introduced.

## Validation and remaining integration

Eight focused new cases cover all three tools, partial/review/invalid outcomes,
active/current ownership, full ancestry and literal shifts, demographic predicates,
job counts, inactive placements/jobs, profile absence/retirement, order, invalid
contracts and read failures. The actual Apply callback reads saved disk data while
a main assessment has invalid pending edits; edits, session identity and project
bytes remain unchanged. Failure retains previously applied selection/results.

828 native tests pass; combined coverage is 96.54%. Ruff/format, strict mypy over
171 source files, architecture and wheel/sdist pass on the approved baseline.
The extracted wheel passes 24 comparisons against read-only AST-extracted original
SQL functions using an isolated synthetic in-memory reference schema. Comparisons
cover worker/all-tool identities and job placement counts/profile selection for four
scopes, three tools and two demographic settings. Arbitrary numeric values in that
reference fixture characterize selection only, not scientific formula equivalence.

No layout, widget, asset or rendering code changed, so F104's visual inspection
remains applicable; no repeated screenshot run is claimed. Native tests exercised
the unchanged Apply/Clear controls with real project reads. All 500 reference
hashes and the approved dependency lock remain unchanged. Evidence:
f105_validation.json, artifacts/f105-check.log, artifacts/f105-focused.log,
artifacts/f105-wheel.log and reference/f105-verify.py.txt.

Next: original station/worker marker positions and anchoring, then rendering these
datasets and original worker/job summaries in the complete PLOT composition.
Positions are not guessed at (0,0), and result contracts do not fabricate geometry.
Parent close consent, remaining map actions, legacy import and final acceptance
remain. JROT remains CBC single-tool/HiGHS multi-tool/no GLPK; no solver changed.
Overall completion percentage and finish date remain unvalidated.
