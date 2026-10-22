"""Lifecycle behavior under cancellation, failed I/O and real SQLite storage.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
import unittest
from collections.abc import Callable

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.document_lifecycle import CloseChoice, DocumentLifecycle
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.lifft_store import LifftSqliteStore


class Repository:
    """Deterministic I/O probe with injectable failures and callbacks."""

    def __init__(self) -> None:
        """Keep storage, call history and fault injection separate.

        Args:
            None.

        Returns:
            None.
        """
        self.values: dict[DocumentKey, LifftDraft] = {}
        self.calls: list[str] = []
        self.fail_save = False
        self.on_load: Callable[[], object] | None = None

    def load(self, document: DocumentKey) -> LifftDraft:
        """Return a known snapshot, recording the read even if it fails.

        Args:
            document: Exact project/document key whose state is read or written in
                isolation.

        Returns:
            Known immutable LiFFT draft after the configured read callback runs;
            deliberately injected callback failures propagate to the caller.
        """
        self.calls.append("load")
        if self.on_load is not None:
            self.on_load()
        return self.values[document]

    def save(self, document: DocumentKey, state: LifftDraft) -> None:
        """Commit a draft only if the injected save failure is disabled.

        Args:
            document: Exact project/document key whose state is read or written in
                isolation.
            state: Immutable draft snapshot being validated, loaded or persisted by this
                test callback.

        Returns:
            None.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        self.calls.append("save")
        if self.fail_save:
            raise OSError("Injected save failure")
        self.values[document] = state


class LifecycleTests(unittest.TestCase):
    """Protect the active session until every requested transition succeeds."""

    def setUp(self) -> None:
        """Begin with an unsaved active assessment and a different stored target.

        Args:
            None.

        Returns:
            None.
        """
        self.repository = Repository()
        self.key = DocumentKey("project-a", "lifft")
        self.target = DocumentKey("project-b", "lifft")
        self.draft = LifftDraft(MeasurementSystem.METRIC)
        self.session = DocumentSession(self.key, self.draft)
        self.repository.values[self.target] = self.draft
        self.lifecycle = DocumentLifecycle(self.repository, self.session)

    def test_dirty_transition_requires_explicit_choice(self) -> None:
        """Missing intent and cancellation perform no I/O or session replacement.

        Args:
            None.

        Returns:
            None.
        """
        for choice in (None, CloseChoice.CANCEL):
            self.assertFalse(self.lifecycle.open(self.target, choice=choice))
            self.assertFalse(self.lifecycle.close(choice=choice))
            self.assertIs(self.lifecycle.active, self.session)
        self.assertEqual(self.repository.calls, [])

    def test_save_before_switch_commits_old_document_only(self) -> None:
        """Load validation precedes saving; the target starts clean with no history.

        Args:
            None.

        Returns:
            None.
        """
        self.assertTrue(self.lifecycle.open(self.target, choice=CloseChoice.SAVE))
        self.assertEqual(self.repository.calls, ["load", "save"])
        self.assertEqual(self.repository.values[self.key], self.draft)
        self.assertFalse(self.session.is_dirty)
        active = self.lifecycle.active
        self.assertIsNotNone(active)
        self.assertEqual(active.document, self.target)
        self.assertFalse(active.is_dirty)
        self.assertIsNone(active.undo_label_key)

    def test_discard_switch_does_not_write_or_delete_storage(self) -> None:
        """Discard releases the old in-memory draft after a successful target load.

        Args:
            None.

        Returns:
            None.
        """
        self.assertTrue(self.lifecycle.open(self.target, choice=CloseChoice.DISCARD))
        self.assertEqual(self.repository.calls, ["load"])
        self.assertNotIn(self.key, self.repository.values)
        self.assertTrue(self.session.is_dirty)

    def test_load_failure_keeps_exact_session_and_history(self) -> None:
        """An unreadable target cannot trigger either save or discard.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(AddLifftTask(self.key, LifftTask("task"), 0))
        missing = DocumentKey("missing", "document")
        for choice in (CloseChoice.SAVE, CloseChoice.DISCARD):
            with self.assertRaises(KeyError):
                self.lifecycle.open(missing, choice=choice)
            self.assertIs(self.lifecycle.active, self.session)
            self.assertEqual(self.session.revision, 1)
            self.assertTrue(self.session.is_dirty)
        self.assertEqual(self.repository.calls, ["load", "load"])
        self.assertTrue(self.session.undo())

    def test_save_failure_blocks_switch_and_close_with_retry(self) -> None:
        """A failed save preserves active state and releases the operation guard.

        Args:
            None.

        Returns:
            None.
        """
        self.repository.fail_save = True
        with self.assertRaises(OSError):
            self.lifecycle.open(self.target, choice=CloseChoice.SAVE)
        with self.assertRaises(OSError):
            self.lifecycle.close(choice=CloseChoice.SAVE)
        self.assertIs(self.lifecycle.active, self.session)
        self.assertTrue(self.session.is_dirty)
        self.repository.fail_save = False
        self.assertTrue(self.lifecycle.close(choice=CloseChoice.SAVE))
        self.assertIsNone(self.lifecycle.active)
        self.assertEqual(self.repository.values[self.key], self.draft)

    def test_discard_close_never_touches_storage(self) -> None:
        """Closing a discarded new draft only releases the active reference.

        Args:
            None.

        Returns:
            None.
        """
        self.assertTrue(self.lifecycle.close(choice=CloseChoice.DISCARD))
        self.assertIsNone(self.lifecycle.active)
        self.assertEqual(self.repository.calls, [])

    def test_clean_and_empty_lifecycles_do_not_need_dirty_consent(self) -> None:
        """Clean switches and idempotent closes avoid unnecessary writes.

        Args:
            None.

        Returns:
            None.
        """
        self.session.save(self.repository)
        self.repository.calls.clear()
        self.assertTrue(self.lifecycle.open(self.target))
        self.assertTrue(self.lifecycle.close())
        self.assertTrue(self.lifecycle.close())
        self.assertEqual(self.repository.calls, ["load"])
        self.assertTrue(self.lifecycle.open(self.key))
        self.assertFalse(self.lifecycle.active.is_dirty)

    def test_same_document_open_keeps_unsaved_history(self) -> None:
        """Repeated selection must not reload over pending edits.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(AddLifftTask(self.key, LifftTask("task"), 0))
        self.assertTrue(self.lifecycle.open(self.key))
        self.assertIs(self.lifecycle.active, self.session)
        self.assertEqual(self.session.revision, 1)
        self.assertEqual(self.repository.calls, [])

    def test_unknown_choices_are_rejected_without_io(self) -> None:
        """A bad dialog adapter cannot implicitly select discard.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(ValueError):
            self.lifecycle.close(choice="discard")
        self.assertEqual(self.repository.calls, [])
        self.assertIs(self.lifecycle.active, self.session)

    def test_nested_lifecycle_operation_is_rejected(self) -> None:
        """A loader cannot recursively close the draft it is replacing.

        Args:
            None.

        Returns:
            None.
        """
        self.repository.on_load = lambda: self.lifecycle.close(
            choice=CloseChoice.DISCARD
        )
        with self.assertRaises(RuntimeError):
            self.lifecycle.open(self.target, choice=CloseChoice.DISCARD)
        self.assertIs(self.lifecycle.active, self.session)
        self.repository.on_load = None
        self.assertTrue(self.lifecycle.open(self.target, choice=CloseChoice.DISCARD))

    def test_edit_during_load_prevents_discarding_new_revision(self) -> None:
        """Reject the transition if an adapter callback changes the active draft.

        Args:
            None.

        Returns:
            None.
        """
        self.repository.on_load = lambda: self.session.execute(
            AddLifftTask(self.key, LifftTask("late"), 0)
        )
        with self.assertRaises(RuntimeError):
            self.lifecycle.open(self.target, choice=CloseChoice.DISCARD)
        self.assertIs(self.lifecycle.active, self.session)
        self.assertEqual(self.session.state.tasks[0].task_id, "late")
        self.assertEqual(self.repository.calls, ["load"])

    def test_sqlite_save_close_reopen_preserves_source(self) -> None:
        """Exercise the coordinator against a real transient database adapter.

        Args:
            None.

        Returns:
            None.
        """
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        store = LifftSqliteStore.create(connection)
        lifecycle = DocumentLifecycle(store, self.session)
        self.session.execute(AddLifftTask(self.key, LifftTask("real", 1, 0, None), 0))
        self.assertTrue(lifecycle.close(choice=CloseChoice.SAVE))
        self.assertTrue(lifecycle.open(self.key))
        self.assertEqual(lifecycle.active.state, self.session.state)
        self.assertFalse(lifecycle.active.is_dirty)
        self.assertIsNone(lifecycle.active.undo_label_key)
