# F5 — versioned LiFFT serialization and transactional storage

Completed 2026-09-28 using Python's existing json/sqlite3 libraries. No dependencies changed. This is a new draft storage format; it neither reads nor migrates legacy .ergprj projects or operational databases.

## Payload version 1

`infrastructure/lifft_serialization.py` encodes a JSON object with exactly `format`, `version`, `system`, `tasks`. Format is `ergotools.lifft-draft`, version is integer 1, system is the original `imperial` or `metric` identifier. Ordered tasks contain exactly task_id, lever_arm, load and repetitions. Numeric fields are finite JSON numbers or null for missing. Zero, fractional and signed values remain explicit; decoding does not imply physical validity or calculate results. Integer numeric inputs retain their precision instead of being coerced to float. Integers too large for the domain's finite-number check are rejected.

The decoder rejects unknown versions/formats/units, missing/extra fields, duplicate JSON member names, duplicate task IDs, blank IDs, nonnumeric fields, boolean measurements, nonfinite values, malformed JSON and excessive parser recursion. It returns a complete immutable draft or raises DocumentFormatError; it never supplies guessed defaults or partial output. The encoder is deterministic for the same draft and validates its output before any database write. Display language and calculated results are not serialized. The format has no size quota yet and is not a hardened untrusted-file ingestion service.

## SQLite adapter version 1

`LifftSqliteStore` receives a caller-owned dedicated sqlite3 connection. The caller closes it. Default legacy transaction control and a non-None isolation_level are required; active caller transactions and incompatible autocommit modes are rejected before mutation. Constructors verify metadata without creating schema. Explicit `create(connection)` begins a transaction and requires an empty sqlite_master; it does not adopt an existing database. Initialization creates draft_metadata with format `ergotools.drafts`, version 1, plus draft_documents with primary key `(project_id, document_id)` and one JSON payload per document.

Save serializes/validates first, then uses BEGIN IMMEDIATE, verifies metadata and executes a parameterized upsert. SQLite commits the transaction before returning to DocumentSession, which then marks the revision clean. Errors propagate and the transaction context rolls back; a failed save leaves the session dirty and can be retried. Load looks up both identity components, validates the complete payload, and raises KeyError for missing documents. Unknown versions and corrupted payloads are never automatically repaired. The connection retains ownership of busy timeouts, journaling and durability settings: use a dedicated default connection. Power-loss recovery, filesystem behavior, read-only media and multiple concurrent writers are not certified by these tests. The current single-owner model has no optimistic concurrency token; do not share a writable document among independent sessions/processes without adding that policy.

## Example on a new test database

```python
import sqlite3
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.lifft_store import LifftSqliteStore

connection = sqlite3.connect(":memory:")
try:
    store = LifftSqliteStore.create(connection)
    key = DocumentKey("example-project", "lifft-document")
    session = DocumentSession(key, LifftDraft(MeasurementSystem.METRIC))
    session.save(store)
    restored = DocumentSession(key, store.load(key), persisted=True)
finally:
    connection.close()
```

Production paths, project metadata, assignment/context mappings, backup/migration and Save As semantics are deliberately not inferred from this example. A connection context manager commits/rolls back but does not close a connection; the owner must close it explicitly.

## Evidence and next steps

Fourteen new tests cover both unit systems, Unicode task IDs, order, missing/zero values, numeric precision, malformed versions/fields/types, duplicate keys/IDs, ambiguous booleans, nonfinite/overflow values, reopen from a second connection, session save/undo/redo, project/document isolation, SQL-like identifiers, corrupt payloads, unknown schema versions, refusal of nonempty/uninitialized databases, caller-transaction preservation and unsupported connection modes. An AFTER UPDATE trigger deliberately aborts an executed write; the prior draft remains intact, the session remains dirty, and retry succeeds after removing the test trigger. All database writes use temporary test databases or an isolated packaging-smoke database.

All 70 tests pass, total combined coverage 98.83%, both new production modules 100%. Ruff/format, strict mypy across 24 source/tool files, architecture and builds pass. `f5_validation.json` records isolated distribution and unchanged source/lock verification. This establishes rollback on an injected SQL error, not crash/power-loss durability or full project-format compatibility.

Next: application-level document load/open/close coordination and dirty-state decisions, then project lifecycle/settings/recent-file behavior. Confirm the previously documented Save As policy before implementing that workflow. Full assessment calculation still requires the metric-moment review gate; UI/scientific/VTK dependencies need exact-version approval. No GUI or legacy data migration occurred here.
