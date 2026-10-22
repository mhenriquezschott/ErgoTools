# Worker/workplace selection catalog — F33

WorkCatalog is an immutable, project-owned selection snapshot of WorkerEntry
identity/names, StationKey ancestry and independent shift IDs. It is deliberately
smaller than the full worker, plant or shift editing models. It retains input
order and exact strings, snapshots supplied collections, and rejects duplicate
identities or untyped records instead of silently hiding them.

## Audited reference behavior

`available_workplaces` in job_placement_repository selects every Station CROSS
JOIN Shift, ordered by plant, section, line, station and shift. It does not filter
job placements, worker assignments or worker availability. WorkCatalog reproduces
this rule with typed immutable WorkplaceContext values. Empty station or shift
sets produce no complete workplace; an empty worker set does not remove places.
Station IDs may repeat beneath different ancestors.

`getWorkers` in main selects worker ID, last name and first name, ordered by ID
or last name. Labels include both names only when both are nonempty; otherwise
the label is the exact worker ID. WorkerOrder and worker_options preserve binary,
null-first ordering and formatting. Each WorkerOption carries a separate ID, so
future selectors can use item data rather than parse labels. This avoids the
reference currentWorkerId split-at-first-space behavior for IDs containing spaces.
It is an explicit identity-handling improvement, not a change to displayed labels.

Equal last names preserve snapshot input order. The reference query has no
secondary ORDER BY key, so tie order is not guaranteed across database layouts;
fixtures establish parity for the captured layout only. Missing or empty names
remain valid, while blank IDs and non-string names fail the typed boundary.

The six main-window hierarchy helpers were also inspected. Plant/section/line/
station queries filter by complete ancestry but mostly have no explicit ORDER BY;
shifts are independent. Their catalogs include parents with no stations. Do not
reconstruct the complete hierarchy from this station-only selection snapshot:
empty plants/sections/lines must be retained in the later editing catalog.

## Ownership and integration

`worker_context(worker_id, workplace)` checks exact worker, station and shift
membership, then supplies the project's WorkerContext. It does not infer a job
assignment or a saved assessment. The existing workspace binding lookup remains
responsible for finding the tool document. Tests drive all three model selections
through this boundary and show that name changes preserve ownership.

No catalog is persisted or loaded from an operational database in this slice.
A later adapter must supply a complete snapshot for the intended project and
refresh it after catalog edits. A snapshot is not a freshness token; UI integration
must invalidate obsolete selection data. No full demographic, health, layout,
scheduling, worker editor or hierarchy editor is claimed.

## Evidence and next work

The actual reference getWorkers method plus WorkplaceKey/available_workplaces
were AST-extracted and run with the unchanged reference Python 3.10.18 on a tiny
temporary SQLite database. `reference/f33-capture.py.txt` records the capture;
`tests/fixtures/work_catalog_reference.json` freezes four populated/empty variants,
source hashes, worker IDs and labels. No real worker data was used.

337 tests pass, including twelve new cases covering reference parity, invalid
inputs, immutability and real-project catalog-to-workspace integration. Both new modules have 100% combined coverage. Full
standards/type/architecture/build gates pass; independent package/source/lock
verification is in `f33_validation.json`. No UI, schema or dependency changed.

Next: characterize the complete hierarchy record contract, including empty
parents, and design its persistence with referential constraints before connecting
selectors. Keep legacy import, assignment editing and final comprehensive copied
project validation as separate incremental integration work.
