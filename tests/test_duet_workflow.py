"""DUET source editing, validation, strict persistence and real failure recovery.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ergotools.application.assessments.duet_commands import (
    AddDuetTask,
    RemoveDuetTask,
    ReplaceDuetTask,
)
from ergotools.application.assessments.duet_preparation import prepare_duet
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.validation import DraftError
from ergotools.infrastructure.draft_json import DocumentFormatError
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.duet_serialization import decode_duet, encode_duet
from ergotools.infrastructure.duet_store import DuetSqliteStore
from ergotools.infrastructure.lifft_store import LifftSqliteStore
from ergotools.presentation.localization import Language, Translator


class DuetWorkflowTests(unittest.TestCase):
    """Exercise source state and transaction boundaries without operational files."""

    def setUp(self) -> None:
        """Create an independent source session for each scenario.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("project", "assessment")
        self.task = DuetTask("a", 5, 100)
        self.draft = DuetDraft((self.task,))
        self.session = DocumentSession(self.key, self.draft, persisted=True)

    def test_add_replace_remove_and_undo_redo_preserve_source(self) -> None:
        """Each command is one reversible change retaining task identity and order.

        Args:
            None.

        Returns:
            None.
        """
        second = DuetTask("b", None, 0.5)
        self.session.execute(AddDuetTask(self.key, second, 0))
        self.assertEqual(self.session.state.tasks, (second, self.task))
        edited = replace(second, omni_res_scale=2)
        self.session.execute(ReplaceDuetTask(self.key, second, edited))
        self.session.execute(RemoveDuetTask(self.key, self.task))
        self.assertEqual(self.session.state.tasks, (edited,))
        self.session.undo()
        self.session.undo()
        self.assertEqual(self.session.state.tasks, (second, self.task))
        self.session.undo()
        self.assertEqual(self.session.state, self.draft)
        self.assertFalse(self.session.is_dirty)
        self.session.redo()
        self.assertTrue(self.session.is_dirty)

    def test_invalid_commands_preserve_history_and_dirty_state(self) -> None:
        """Reject position, duplicate, stale, absent, foreign and changed identities.

        Args:
            None.

        Returns:
            None.
        """
        cases = (
            AddDuetTask(self.key, DuetTask("b"), -1),
            AddDuetTask(self.key, DuetTask("b"), 2),
            AddDuetTask(self.key, self.task, 0),
            ReplaceDuetTask(self.key, replace(self.task, repetitions=2), self.task),
            ReplaceDuetTask(self.key, self.task, DuetTask("b")),
            RemoveDuetTask(self.key, DuetTask("missing")),
            RemoveDuetTask(DocumentKey("other", "assessment"), self.task),
        )
        for command in cases:
            with self.assertRaises(ValueError):
                self.session.execute(command)
            self.assertIs(self.session.state, self.draft)
            self.assertFalse(self.session.is_dirty)
            self.assertEqual(self.session.revision, 0)
        self.assertFalse(
            self.session.execute(ReplaceDuetTask(self.key, self.task, self.task))
        )

    def test_draft_snapshots_input_sequence_and_rejects_duplicate_ids(self) -> None:
        """External list edits cannot alter an owned draft.

        Args:
            None.

        Returns:
            None.
        """
        tasks = [self.task]
        draft = DuetDraft(tasks)
        tasks.clear()
        self.assertEqual(draft.tasks, (self.task,))
        with self.assertRaises(DraftError):
            DuetDraft((self.task, self.task))

    def test_preparation_collects_all_issues_without_zero_substitution(self) -> None:
        """Report incomplete/invalid fields in row order; zero remains present.

        Args:
            None.

        Returns:
            None.
        """
        draft = DuetDraft((DuetTask("a", None, None), DuetTask("b", 11, -1)))
        prepared = prepare_duet(DocumentSession(self.key, draft))
        self.assertFalse(prepared.has_valid_inputs)
        self.assertEqual(
            [(i.task_id, i.field) for i in prepared.issues],
            [
                ("a", "omni_res_scale"),
                ("a", "repetitions"),
                ("b", "omni_res_scale"),
                ("b", "repetitions"),
            ],
        )
        self.assertIs(prepared.source, draft)
        self.assertFalse(
            prepare_duet(DocumentSession(self.key, DuetDraft())).has_valid_inputs
        )
        self.assertTrue(
            prepare_duet(
                DocumentSession(self.key, DuetDraft((DuetTask("z", 0, 0),)))
            ).has_valid_inputs
        )

    def test_preparation_freshness_across_edits_branches_and_close(self) -> None:
        """Use session and revision identity instead of equal values alone.

        Args:
            None.

        Returns:
            None.
        """
        initial = prepare_duet(self.session)
        edited = replace(self.task, repetitions=200)
        self.session.execute(ReplaceDuetTask(self.key, self.task, edited))
        changed = prepare_duet(self.session)
        self.assertFalse(initial.is_current(self.session))
        self.session.undo()
        self.assertTrue(initial.is_current(self.session))
        self.session.redo()
        self.assertTrue(changed.is_current(self.session))
        self.session.undo()
        self.session.execute(ReplaceDuetTask(self.key, self.task, edited))
        self.assertFalse(changed.is_current(self.session))
        self.assertFalse(initial.is_current(None))
        self.assertFalse(initial.is_current(DocumentSession(self.key, self.draft)))

    def test_codec_roundtrips_original_missing_signed_and_precise_values(self) -> None:
        """Persist editable source, not computed totals or localized labels.

        Args:
            None.

        Returns:
            None.
        """
        draft = DuetDraft(
            (
                DuetTask("ñ", None, None),
                DuetTask("zero", 0, 0),
                DuetTask("review", -1, -0.5),
                DuetTask("precise", 10, 2**53 + 1),
            )
        )
        payload = encode_duet(draft)
        self.assertEqual(decode_duet(payload), draft)
        self.assertEqual(encode_duet(decode_duet(payload)), payload)
        self.assertEqual(decode_duet(encode_duet(DuetDraft())), DuetDraft())
        self.assertNotIn("cumulative_damage", json.loads(payload)["tasks"][0])

    def test_codec_rejects_ambiguous_or_unsupported_documents(self) -> None:
        """Reject corruption, unknown fields/versions and wrong model envelopes.

        Args:
            None.

        Returns:
            None.
        """
        base = json.loads(encode_duet(self.draft))
        cases = [
            None,
            [],
            {},
            {**base, "version": True},
            {**base, "version": 2},
            {**base, "version": 1.0},
            {**base, "format": "ergotools.lifft-draft"},
            {**base, "tasks": {}},
            {**base, "extra": 0},
        ]
        for case in cases:
            with self.assertRaises(DocumentFormatError):
                decode_duet(json.dumps(case))
        for payload in (
            '{"version":1,"version":1}',
            "{",
            "[" * 1100 + "0" + "]" * 1100,
        ):
            with self.assertRaises(DocumentFormatError):
                decode_duet(payload)

    def test_codec_rejects_invalid_task_shapes_and_numeric_types(self) -> None:
        """No booleans/fractions masquerade as scales or nonfinite stored numbers.

        Args:
            None.

        Returns:
            None.
        """
        base = json.loads(encode_duet(self.draft))
        task = base["tasks"][0]
        cases = [None, {}, {**task, "extra": 1}, {**task, "task_id": ""}]
        for field, values in {
            "omni_res_scale": [True, 1.0, "1", []],
            "repetitions": [True, "1", float("nan"), float("inf"), 10**400],
        }.items():
            cases.extend({**task, field: value} for value in values)
        for case in cases:
            with self.assertRaises(DocumentFormatError):
                decode_duet(json.dumps({**base, "tasks": [case]}))
        with self.assertRaises(DocumentFormatError):
            decode_duet(json.dumps({**base, "tasks": [task, task]}))
        with self.assertRaises(ValueError):
            encode_duet(DuetDraft((DuetTask("a", 1, float("nan")),)))

    def test_real_file_save_close_reopen_and_freshness(self) -> None:
        """Round-trip a new SQLite file using only the caller-owned connection.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "draft.sqlite"
            connection = sqlite3.connect(path)
            try:
                store = DuetSqliteStore.create(connection)
                prepared = prepare_duet(self.session)
                self.session.save(store)
                self.assertTrue(prepared.is_current(self.session))
                self.assertFalse(self.session.is_dirty)
            finally:
                connection.close()
            connection = sqlite3.connect(path)
            try:
                loaded = DuetSqliteStore(connection).load(self.key)
                reopened = DocumentSession(self.key, loaded, persisted=True)
                self.assertEqual(loaded, self.draft)
                self.assertFalse(prepared.is_current(reopened))
                self.assertTrue(prepare_duet(reopened).has_valid_inputs)
            finally:
                connection.close()

    def test_failed_sql_save_rolls_back_and_keeps_session_dirty_for_retry(self) -> None:
        """A real trigger failure retains the prior stored source and clean marker.

        Args:
            None.

        Returns:
            None.
        """
        connection = sqlite3.connect(":memory:")
        try:
            store = DuetSqliteStore.create(connection)
            self.session.save(store)
            self.session.execute(AddDuetTask(self.key, DuetTask("b", 3, 100), 1))
            connection.execute(
                "CREATE TRIGGER reject_update BEFORE UPDATE ON draft_documents "
                "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                self.session.save(store)
            self.assertTrue(self.session.is_dirty)
            self.assertFalse(connection.in_transaction)
            self.assertEqual(store.load(self.key), self.draft)
            connection.execute("DROP TRIGGER reject_update")
            self.session.save(store)
            self.assertFalse(self.session.is_dirty)
            self.assertEqual(store.load(self.key), self.session.state)
        finally:
            connection.close()

    def test_tool_formats_are_isolated_and_existing_schema_is_protected(self) -> None:
        """Neither adapter may adopt or overwrite the other model's database.

        Args:
            None.

        Returns:
            None.
        """
        for creator, other in (
            (DuetSqliteStore, LifftSqliteStore),
            (LifftSqliteStore, DuetSqliteStore),
        ):
            connection = sqlite3.connect(":memory:")
            try:
                creator.create(connection)
                with self.assertRaises(StoreFormatError):
                    other(connection)
                with self.assertRaises(StoreFormatError):
                    other.create(connection)
                creator(connection)
            finally:
                connection.close()

    def test_missing_documents_and_localized_command_labels(self) -> None:
        """Document identity scopes storage and all edit labels have translations.

        Args:
            None.

        Returns:
            None.
        """
        connection = sqlite3.connect(":memory:")
        try:
            store = DuetSqliteStore.create(connection)
            store.save(self.key, self.draft)
            with self.assertRaises(KeyError):
                store.load(DocumentKey("other", "assessment"))
        finally:
            connection.close()
        for language in Language:
            for command in (AddDuetTask, ReplaceDuetTask, RemoveDuetTask):
                self.assertTrue(Translator(language).text(command.label_key))
