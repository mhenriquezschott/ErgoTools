# Legacy evidence reconciliation — F131

The comprehensive copy now has a conflict-free recovery plan for all 194 original
assessment summaries and 3,577 task rows: 191 exact old/current matches plus three
recovered records/45 rows on their existing assignments 101, 102 and 104. Next:
PLOT companion images/geometry and saved JROT provenance, then explicit conversion.
No source or destination records are written by this read-only recovery plan.

Source review: schema_migrations.py v5 completion/ownership mapping and original
main.py task persistence. Full worker/plant/section/line/station/shift/tool keys
join old tables to versioned history. Matching current versions must agree on
recorded units, cached totals/probability and every ordered input/result task field;
otherwise a concrete conflict blocks complete conversion. Missing current history,
unknown owners and orphan tasks are never silently replaced or discarded.

A genuinely missing record is recovered only with one exact existing active
assignment. No successor assignment is invented. Full-context/tool UUID-based
document IDs remain deterministic across row order; task IDs/gaps and immutable
raw source rows remain intact. Lifecycle follows the source v5 condition (any
positive repetitions -> complete), which grants no scientific approval and does
not mark evidence fresh. ST raw selectors remain unresolved as in F130.

Focused fixtures check deterministic recovery, closed/active owner distinction,
no duplicate import, task-cache disagreement, absent owner and source foreign-key
failure. Copied comprehensive source bytes remain unchanged. Independent wheel
checks reproduce 191 exact matches, three recovered owners and 45 recovered rows.
No UI changed. The owner has been asked how ST displayed directions versus swapped
legacy formula indices should be handled before that conversion can proceed;
independent PLOT/JROT compatibility work continues meanwhile.
Overall percentage and finish date remain unvalidated.

Validation: 1034 tests pass; 96.71% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f131_validation.json and artifacts/f131-*.log.
