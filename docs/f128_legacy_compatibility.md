# Legacy XML and read-only schema audit — F128

Original XML/SQLite version-eight projects now have a tested read-only adapter.
The comprehensive copied fixture passes integrity and reference checks: 30 tables,
28 workers, 191 historical assessments, 19 risk profiles and seven JROT schemes.
Next: typed organization/worker/job/risk catalogs, then historical task sources.
No destination conversion or integrated legacy-project UI acceptance is claimed.

Source mapping: reference main.py openFilePath and database_inventory.py resolve
DataPath + DatabaseName relative to the descriptor. DatabasePath is informational
and may be stale; original precedence is preserved. XML title/description/local
creation time/language/unit default map to ProjectMetadata with an explicit new
project ID, since the XML has none. Windows separators are normalized. Companion
paths must remain relative within the project copy; external paths require a
separate reviewed mapping. Unknown language/units, duplicate fields and malformed
metadata fail explicitly. Missing optional defaults match the original.

LegacyProject owns one query-only, mode=ro SQLite connection and read transaction,
checks schema version 8, integrity and foreign keys, and exposes immutable rows
and a schema/count inventory. It never imports legacy Python, invokes migrations,
repairs schema, recalculates results or writes the source. Earlier source schemas
remain explicitly unsupported until independently reviewed. This is a read port,
not permission to replace the operational project or an incomplete silent import.

The comprehensive descriptor and database were copied to a temporary directory.
Their original hashes and inventory are recorded in f128_legacy_audit.json. Focused
synthetic tests cover metadata/path errors, missing DB/no accidental creation,
unsupported version/no migration, immutable rows, denied writes and connection
closure. No application window changed, so no new screenshots were required.
Overall completion percentage and finish date remain unvalidated.

Validation: 1013 tests pass; 96.70% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f128_validation.json and artifacts/f128-*.log.
