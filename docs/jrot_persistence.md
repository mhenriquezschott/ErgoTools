> Historical checkpoint: Job profile/version/evidence behavior below was explicitly
> superseded on 2026-10-20. Current Job values, calculators, copying and JROT policy are
> documented in the owner decision record
> and [current database inventory](database_tables.md). Removed APIs are not supported.

# JROT saved scheme workflow — F121, 2026-10-08

Frozen RotationScheme/RotationWorkerLink/RotationTarget records retain exact
project/scheme identity, editable name/description, ordered worker blocks,
original optional assignment IDs, exact job/placement/profile IDs, explicit
station/shift scope, manual/single-tool/all-tools provenance and primary tool.
Solver keys derive unambiguously from target identities rather than cell text.
Manual schemes require complete cells but may contain block collisions: Save
is not an optimization-feasibility or scientific approval operation.

The source mapping is rotation_repository.py list/load/save/delete and the active
rotation_layout.py save/load handlers. Source normalized records are represented
in this new format as version-one, strictly shaped JSON scheme payloads in an
owned SQLite table. Counts derive from complete rows instead of independent
potentially inconsistent metadata. Creation/update timestamps remain stored
alongside payloads. This is not a legacy .ergprj importer or schema copy.

The application RotationSchemeRepository port exposes ordered read, explicit
save and consent-owned delete. AssessmentProjectFile uses its existing connection;
no second handle, implicit editor save or optimization publication is introduced.
Read returns empty for full formats seven–ten without migration. Explicit Save
atomically adds missing details/map/geometry tables and scheme records, promoting
the project to format eleven only after commit. Existing sources, profile units,
maps and geometry survive. Failure rolls back schema, previous scheme and version;
unknown deletion raises KeyError. Older partial formats remain unsupported.
Opening/Save As validates and retains exact ownership. PLOT geometry saves now
preserve the higher project format instead of resetting it to ten.

Scope must contain one shift and exact existing workplaces. Links must belong
to their worker/job and scope. Saved inactive assignments and retired profiles
remain readable. New profile links require approved status; retired links can
only be retained from that same existing scheme. Newer current profiles do not
relink an old scheme. Approved/retired measurement immutability remains governed
by the existing risk store. No metric/imperial coefficient conversion is added;
source unit evidence stays with the referenced profile.

Referenced workers/scope cannot be deleted. Referenced assignment and placement
ownership cannot be rewritten or removed; ending an assignment or changing
activity/notes is permitted, so normal reassignment can retain its predecessor.
The actual Job Management deletion path also rejects rotation-referenced jobs
before removing profiles/placements. Deleting the scheme releases its links.
These guards cover concrete saved records, not speculative concurrent editors.
Hierarchy validation checks only its own links, avoiding recursive cross-catalog
reads during project open. Full reference validation is owned by the project.

Validation: 948 native tests pass (24 focused new cases), 96.81% coverage;
Ruff/format (446 files), strict mypy (202 source files), architecture and builds
pass. Focused cases cover formats seven–eleven, no-write reads, upsert/ordering,
reopen/copy/delete, initial and replacement rollback, old profile/assignment
retention, references/deletion protection, map/geometry/unit preservation, foreign
or malformed records and closed/transaction ownership. Independent extracted-wheel
actual persistence workflow passes. All 500 reference hashes and approved lock
are unchanged. Evidence: f121_validation.json, artifacts/f121-check.log and
artifacts/f121-wheel.log. No UI changed; no new visual captures were required.

Next: compose the original JROT layout and one-shift scope chooser into usable
edit/save/load/delete controls, then optimizer/comparison transfer and owned worker
cancel/close lifecycle. JROT main navigation remains disabled. Final legacy-format
compatibility, comprehensive copied-project integration and full visual/workflow
acceptance remain outstanding. No reliable overall percentage/date is established.
