# Complete selection hierarchy — F34

WorkHierarchy owns one WorkCatalog plus explicit plants, SectionKey values and
LineKey values. It retains parents without children instead of reconstructing
parents from stations. The existing WorkCatalog continues to own project,
workers, stations and independent shifts; its public API remains compatible.

Construction snapshots input collections and validates unique identities and
all parent references. A section needs its exact plant, a line its exact section,
and a station its exact line. Repeated names under different ancestors remain
valid. Orphans fail rather than being silently dropped or reparented. The snapshot
is immutable and cannot expose a partially validated hierarchy.

`sections_in`, `lines_in` and `stations_in` return children in supplied snapshot
order. A known empty parent returns an empty tuple. An unknown parent raises
KeyError, an explicit typed-boundary difference from the reference helpers'
empty/None results. Callers must represent incomplete selector state separately
and invalidate stale selections after a catalog refresh.

## Reference characterization

Reference main.py defines composite keys for sections, lines and stations, with
parent relationships using full ancestry. The getPlants/getSections/getLines/
getStations/getShifts methods were executed after AST extraction under unchanged
reference Python 3.10.18 against a synthetic temporary SQLite database. Eleven
captured query outputs cover empty plants, sections and lines; repeated branch
names; exact child filtering; independent shifts; and nonalphabetic input order.

The capture is `reference/f34-capture.py.txt`; frozen inputs, outputs and source
hash are in `tests/fixtures/work_hierarchy_reference.json`. The minimal fixture
has no indexes. Reference queries lack ORDER BY, so captured ordering is evidence
for that fixture, not a database-wide guarantee. The domain preserves the adapter's
snapshot order; eventual persistence must explicitly record or define ordering.
The alphabetically ordered complete workplace cross product remains the separate
WorkCatalog behavior characterized in F33.

## Validation and persistence requirements

353 tests pass, including sixteen new cases. The new module has 100% combined
statement/branch coverage. Ruff, formatting, strict mypy (86 files), architecture
and distribution builds pass. Package/reference/lock checks are recorded in
`f34_validation.json`. No UI, schema, dependency or operational data changed.

This is a complete *identity hierarchy*, not complete plant/worker/shift records.
Descriptions, PLOT geometry, scheduling details, demographic data and editors
remain outside this slice. No deletion cascade or legacy migration is implied.

The next persistence slice must preserve empty parents and ordering, validate all
relationships in one transaction, reject a catalog belonging to another project,
and prevent existing assessment bindings from becoming orphaned. Failed writes
must preserve the previous catalog and binding lookup. Older project versions
must not be silently migrated. Use small temporary projects and explicit format
capabilities before connecting selection widgets.
