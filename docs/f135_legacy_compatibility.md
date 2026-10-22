# F135 — preserve complete original project evidence

New-format twelve stores the exact original XML, a consistent read-only SQLite
snapshot and all referenced image bytes/names alongside the editable typed data.
Original cached results, task moments, raw selectors, timestamps, plant display
fields and schema objects remain recoverable after edits, backup and removal of
the copied source files. Next: connect an explicit converter, blocking source
conflicts and unresolved ST directions before destination creation. No reliable
overall completion percentage or finish date yet.

The format change is explicit: format eleven stays valid and has no archive;
format twelve requires valid source evidence on open. Version-one evidence tables
have SHA-256 integrity checks and ordered named image records, plus in-memory XML,
SQLite schema/integrity/foreign-key and image decoding checks. Creation-only
writers reject populated evidence. The archive does not replace editable records
or certify cached results as fresh calculations. Only existing referenced image
assets are archived, not arbitrary unrelated files in the source directory.

LegacyDescriptor retains the exact XML bytes it parsed. SQLite serialization uses
the already-open read transaction, retaining even unmapped tables/BLOB values and
committed WAL pages while excluding subsequent commits. The serialized snapshot
is logically faithful, not a promised byte-identical physical database copy. WAL
header bytes remain unchanged in the archive; only its in-memory validation copy
uses rollback-journal header flags because SQLite deserialize cannot attach WAL
sidecars. A real two-connection regression proves snapshot isolation and BLOB
preservation.

JROT saving now retains newer format versions rather than assigning eleven
unconditionally. Normal assessment edits, map/geometry saves, rotation saves,
project backup and source-independent reopening preserve the archive. Six archive
corruption cases reject open explicitly. No UI or scientific-model changes.

The extracted-wheel test archives all source data including 56 unresolved ST
sources while creating an explicitly marked 138-assessment LiFFT/DUET validation
subset. All four image bytes/names, catalogs, maps and rotation links round-trip;
actual rotation edits and backup retain format twelve and the complete archive.
This is not yet complete legacy conversion or comprehensive integrated UI parity.

Validation: 1068 tests pass; 96.55% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f135_validation.json and artifacts/f135-*.log.
