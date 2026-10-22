# F106 — station anchors and worker marker persistence

PLOT result datasets now carry validated project-owned geometry. Pure position
operations and explicit atomic persistence follow the original station/assignment
rules. This does not yet render markers, implement drag controls or enable the
production PLOT window.

## Original behavior and reviewed contracts

The source is plot_position_repository.py station_key_for_assignment,
station_position, initialize_station_position, set_station_position,
worker_assignment_marker, ensure_worker_assignment_marker and
save_worker_assignment_marker (around lines 296–530). The reviewed table
constraints are in schema_migrations.py _create_assignment_map_positions_v7.
VisualJobMarker.commitPosition and VisualWorkerTool.__saveData show how the
original UI invokes these operations; their drag/centering transforms remain
for the rendering slice.

Coordinates are original-image pixels, not metric/imperial body measurements or
scaled scene coordinates. Negative finite coordinates remain allowed. Station
identity includes plant/section/line/station; its anchor is shared across shifts
and placements. Worker identity is the exact assignment, shared across its tools,
including historical assignments. Display names never establish identity.

Ensuring a missing worker marker creates a hidden record: at the existing station
anchor when present, otherwise explicitly unplaced. Repeating Ensure retains
the existing marker. Saving a manual worker position initializes only a missing
station anchor, with worker provenance. Later worker moves keep that anchor.
Deliberate station/job moves update the anchor and leave stored worker points
unchanged, including inherited points. A worker without its own point can resolve
to a subsequently available anchor. No anchor/point remains None; the data model
does not manufacture a persisted origin.

Size and thickness are original pixels; scale is dimensionless. Size/scale must
be positive; thickness may be zero. Locked/visible/enabled are independent flags.
Unplaced requires absent coordinates; other provenance requires an actual point.
Typed validation rejects booleans as coordinates/sizes, nonfinite values, malformed
flags, partial coordinate pairs and duplicate geometry identities. These tighten
the reference function's permissive float/bool coercion while retaining valid
saved behavior.

## Storage, compatibility and ownership

Format ten adds project-owned station and assignment geometry. Explicit position
Save upgrades full seven/eight/nine projects atomically, creating absent details
and map storage when necessary. Reading older full projects returns empty geometry
without migration. Partial formats cannot save positions. Ordinary New remains
format eight; merely opening PLOT data does not upgrade it.

Schema, both geometry tables and metadata version commit together. Late failure
rolls back new tables, deleted/replaced records and version. The in-memory format
changes only after commit. Maps, assessment sources, profiles and project details
remain intact. Subsequent map Save retains ten instead of downgrading it to nine.
Reopen, Backup and Save As retain geometry; copied metadata edits retain ten.

Stored station/assignment membership is validated on read/open/write. Existing
geometry protects station identity and assignment ownership, including unassessed
assignments. Activity changes and closing assignments remain allowed; repurposing
or deleting referenced assignments is rejected until geometry is explicitly
removed. This adapter boundary differs from the reference SQL's deletion cascade.
Final organization/worker deletion workflows must compose intentional geometry
removal with their accepted deletion action to retain reference workflow parity;
no new user dialog or permanent restriction is introduced by this data slice.

The position store borrows the project's transaction. The application receives
geometry through its existing read-only result port; no Qt, SQL, renderer or active
editor is introduced into portable selection. Full-snapshot writes are synchronous
owner-thread operations, not a concurrency or autosave feature. Timestamps from
the original internal tables are not part of the current portable geometry API.

## Validation and remaining integration

Fifteen focused cases cover valid/invalid geometry, original movement semantics,
seven/eight/nine upgrades, reopen/copy/maps/results, schema and late SQL rollback,
referenced station/assignment guards, malformed/orphan records, partial formats
and transaction ownership. 843 native tests pass; combined coverage is 96.58%.
Ruff/format, strict mypy over 173 source files, architecture and wheel/sdist pass
on the approved baseline.

The extracted wheel passes six ordered state comparisons with read-only
AST-extracted original position functions and reviewed position-table creation
statements, using isolated synthetic data. It also verifies actual format-ten
save, dataset geometry, closed ownership, copies and reopen. No operational
project or reference module was imported. All 500 reference hashes and the
approved dependency lock remain unchanged.

No widget/layout/rendering code changed, so F104 visual evidence remains applicable;
no new visual acceptance is claimed. Evidence: f106_validation.json,
artifacts/f106-focused.log, artifacts/f106-check.log, artifacts/f106-wheel.log and
reference/f106-verify.py.txt. The permission review initially timed out before any
write; staging and a smaller authorized write succeeded.

Next: original worker/job marker rendering and move/save interactions, then worker/
job overviews and summaries in complete PLOT composition. Parent close consent,
remaining map actions, legacy import and final copied-project/platform validation
remain. JROT uses CBC single-tool/HiGHS multi-tool/no GLPK; no solver changed.
Overall completion percentage and finish date remain unvalidated.
