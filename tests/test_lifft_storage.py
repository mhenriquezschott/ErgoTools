"""Round trips and real SQLite rollback tests using temporary databases only.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.lifft_serialization import (
    DocumentFormatError,
    decode_lifft,
    encode_lifft,
)
from ergotools.infrastructure.lifft_store import LifftSqliteStore, StoreFormatError


class SerializationTests(unittest.TestCase):
    """Require explicit versions, original units and unambiguous numeric fields."""

    def test_round_trip_units_order_missing_zero_and_unicode(self) -> None:
        """Preserve every source field independently of the display language.

        Args:
            None.

        Returns:
            None.
        """
        for system in MeasurementSystem:
            draft = LifftDraft(
                system,
                (
                    LifftTask("tarea-ñ", 0, None, 0.5),
                    LifftTask("second", -1.25, 1e20, 100),
                ),
            )
            payload = encode_lifft(draft)
            self.assertEqual(decode_lifft(payload), draft)
            self.assertEqual(encode_lifft(draft), payload)
        empty = LifftDraft(MeasurementSystem.IMPERIAL)
        self.assertEqual(decode_lifft(encode_lifft(empty)), empty)

    def test_integer_precision_is_not_lost_to_float_coercion(self) -> None:
        """A finite integer JSON input must survive without silent rounding.

        Args:
            None.

        Returns:
            None.
        """
        value = 2**53 + 1
        draft = LifftDraft(
            MeasurementSystem.METRIC, (LifftTask("precise", repetitions=value),)
        )
        self.assertEqual(decode_lifft(encode_lifft(draft)).tasks[0].repetitions, value)

    def test_reject_wrong_envelope_shapes_versions_and_fields(self) -> None:
        """Never silently adopt another format or invent missing data.

        Args:
            None.

        Returns:
            None.
        """
        base = json.loads(encode_lifft(LifftDraft(MeasurementSystem.METRIC)))
        cases = [[], None, {}, {**base, "extra": 1}]
        for field, values in {
            "format": ["other", None],
            "version": [2, True, 1.0, "1"],
            "system": ["unknown", None, " "],
            "tasks": [{}, None],
        }.items():
            cases.extend({**base, field: value} for value in values)
        for value in cases:
            with self.subTest(value=value), self.assertRaises(DocumentFormatError):
                decode_lifft(json.dumps(value))

    def test_reject_ambiguous_or_malformed_task_fields(self) -> None:
        """Numbers exclude booleans/strings; IDs and exact fields are mandatory.

        Args:
            None.

        Returns:
            None.
        """
        base = json.loads(
            encode_lifft(LifftDraft(MeasurementSystem.METRIC, (LifftTask("a"),)))
        )
        task = base["tasks"][0]
        cases = [None, {}, {**task, "extra": 1}]
        for field, values in {
            "task_id": ["", 1, None],
            "load": [True, "2", [], float("nan"), float("inf"), 10**400],
        }.items():
            cases.extend({**task, field: value} for value in values)
        for value in cases:
            with self.subTest(value=value), self.assertRaises(DocumentFormatError):
                decode_lifft(json.dumps({**base, "tasks": [value]}))
        with self.assertRaises(DocumentFormatError):
            decode_lifft(json.dumps({**base, "tasks": [task, task]}))

    def test_duplicate_members_and_invalid_json_are_rejected(self) -> None:
        """Duplicate member names must not overwrite earlier data during parsing.

        Args:
            None.

        Returns:
            None.
        """
        for payload in (
            '{"version":1,"version":2}',
            "{",
            "null",
            "[1]",
            "[" * 1100 + "0" + "]" * 1100,
        ):
            with (
                self.subTest(payload=payload[:30]),
                self.assertRaises(DocumentFormatError),
            ):
                decode_lifft(payload)

    def test_encoder_rejects_boolean_numeric_input(self) -> None:
        """Typed-model misuse cannot serialize an ambiguous boolean measurement.

        Args:
            None.

        Returns:
            None.
        """
        draft = LifftDraft(MeasurementSystem.METRIC, (LifftTask("a", True),))
        with self.assertRaises(DocumentFormatError):
            encode_lifft(draft)


class SqliteStoreTests(unittest.TestCase):
    """Exercise a real database, including failed writes after SQL has executed."""

    def setUp(self) -> None:
        """Create a separate temporary database with deterministic cleanup.

        Args:
            None.

        Returns:
            None.
        """
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "drafts.sqlite"
        self.connection = sqlite3.connect(self.path)
        self.addCleanup(self.connection.close)
        self.store = LifftSqliteStore.create(self.connection)
        self.key = DocumentKey("project", "lifft")
        self.initial = LifftDraft(
            MeasurementSystem.METRIC, (LifftTask("original", 1, 2, None),)
        )

    def test_committed_save_survives_reopen_and_remains_undoable(self) -> None:
        """Save through the session and read from a separate connection.

        Args:
            None.

        Returns:
            None.
        """
        session = DocumentSession(self.key, self.initial)
        session.save(self.store)
        self.assertFalse(session.is_dirty)
        session.execute(AddLifftTask(self.key, LifftTask("new", 0, 0, 0), 1))
        session.save(self.store)
        other = sqlite3.connect(self.path)
        self.addCleanup(other.close)
        self.assertEqual(LifftSqliteStore(other).load(self.key), session.state)
        self.assertTrue(session.undo())
        self.assertTrue(session.is_dirty)
        self.assertEqual(session.state, self.initial)
        self.assertTrue(session.redo())
        self.assertFalse(session.is_dirty)

    def test_write_failure_rolls_back_and_session_can_retry(self) -> None:
        """An AFTER UPDATE trigger failure rolls back the executed update.

        Args:
            None.

        Returns:
            None.
        """
        session = DocumentSession(self.key, self.initial)
        session.save(self.store)
        session.execute(AddLifftTask(self.key, LifftTask("new"), 1))
        self.connection.execute(
            "CREATE TRIGGER fail_save AFTER UPDATE ON draft_documents "
            "BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            session.save(self.store)
        self.assertTrue(session.is_dirty)
        self.assertFalse(self.connection.in_transaction)
        self.assertEqual(self.store.load(self.key), self.initial)
        self.connection.execute("DROP TRIGGER fail_save")
        session.save(self.store)
        self.assertFalse(session.is_dirty)
        self.assertEqual(self.store.load(self.key), session.state)

    def test_keys_are_parameterized_and_isolated(self) -> None:
        """Identical document IDs in different projects do not share records.

        Args:
            None.

        Returns:
            None.
        """
        keys = [
            self.key,
            DocumentKey("other", "lifft"),
            DocumentKey("project", "other"),
            DocumentKey("'; DROP TABLE x;--", "é"),
        ]
        for index, key in enumerate(keys):
            self.store.save(
                key, LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask(str(index)),))
            )
        for index, key in enumerate(keys):
            self.assertEqual(self.store.load(key).tasks[0].task_id, str(index))
        with self.assertRaises(KeyError):
            self.store.load(DocumentKey("absent", "absent"))

    def test_corrupt_payload_is_rejected_without_repair(self) -> None:
        """Loading malformed stored data neither defaults fields nor rewrites rows.

        Args:
            None.

        Returns:
            None.
        """
        self.store.save(self.key, self.initial)
        with self.connection:
            self.connection.execute(
                "UPDATE draft_documents SET payload=?", ('{"version":2}',)
            )
        with self.assertRaises(DocumentFormatError):
            self.store.load(self.key)
        self.assertEqual(
            self.connection.execute("SELECT payload FROM draft_documents").fetchone()[
                0
            ],
            '{"version":2}',
        )

    def test_nonempty_database_and_unknown_versions_are_never_adopted(self) -> None:
        """Schema creation refuses existing data and version mismatches block writes.

        Args:
            None.

        Returns:
            None.
        """
        self.store.save(self.key, self.initial)
        with self.assertRaises(StoreFormatError):
            LifftSqliteStore.create(self.connection)
        self.assertEqual(self.store.load(self.key), self.initial)
        with self.connection:
            self.connection.execute("UPDATE draft_metadata SET version=2")
        with self.assertRaises(StoreFormatError):
            LifftSqliteStore(self.connection)
        with self.assertRaises(StoreFormatError):
            self.store.save(self.key, self.initial)
        self.assertFalse(self.connection.in_transaction)

    def test_uninitialized_connection_is_read_only_rejected(self) -> None:
        """Construction never initializes or migrates an arbitrary database.

        Args:
            None.

        Returns:
            None.
        """
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        with self.assertRaises(StoreFormatError):
            LifftSqliteStore(connection)
        self.assertEqual(
            connection.execute("SELECT name FROM sqlite_master").fetchall(), []
        )

    def test_caller_transaction_is_not_committed_or_rolled_back(self) -> None:
        """Refuse shared active transactions before touching caller-owned work.

        Args:
            None.

        Returns:
            None.
        """
        self.connection.execute("BEGIN")
        self.connection.execute("UPDATE draft_metadata SET version=99")
        for action in (
            lambda: self.store.save(self.key, self.initial),
            lambda: self.store.load(self.key),
            lambda: LifftSqliteStore.create(self.connection),
        ):
            with self.assertRaises(RuntimeError):
                action()
        self.assertTrue(self.connection.in_transaction)
        self.assertEqual(
            self.connection.execute("SELECT version FROM draft_metadata").fetchone()[0],
            99,
        )
        self.connection.rollback()
        self.store.save(self.key, self.initial)

    def test_nondefault_connection_modes_are_rejected(self) -> None:
        """Do not promise atomic saves with incompatible transaction ownership.

        Args:
            None.

        Returns:
            None.
        """
        for options in ({"isolation_level": None}, {"autocommit": True}):
            connection = sqlite3.connect(":memory:", **options)
            self.addCleanup(connection.close)
            with self.assertRaises(RuntimeError):
                LifftSqliteStore.create(connection)
