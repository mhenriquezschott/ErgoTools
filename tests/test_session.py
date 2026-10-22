"""Exercise document history and save failure behavior using immutable drafts.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import unittest
from collections.abc import Callable
from dataclasses import dataclass, replace

from ergotools.application.session import DocumentKey, DocumentSession


@dataclass(frozen=True)
class Draft:
    """Small draft fixture; production assessment schemas are still pending."""

    title: str


@dataclass(frozen=True)
class Rename:
    """Pure command fixture with validation and an explicit owning document."""

    document: DocumentKey
    title: str
    label_key: str = "edit.rename"

    def apply(self, state: Draft) -> Draft:
        """Validate then return an immutable replacement without side effects.

        Args:
            state: Immutable draft snapshot being validated, loaded or persisted by this
                test callback.

        Returns:
            Immutable Draft replacement after validation; no repository write occurs.

        Raises:
            ValueError: The test double rejects invalid input or injects the stated
                controlled validation failure.
        """
        if not self.title:
            raise ValueError("Title required")
        return replace(state, title=self.title)


class MemoryStore:
    """Test adapter that can fail before committing any snapshot."""

    def __init__(self, *, fail: bool = False) -> None:
        """Start with no saved values and a controllable failure mode.

        Args:
            fail: True enables the controlled adapter failure; False permits the
                successful retry.

        Returns:
            None.
        """
        self.fail = fail
        self.saved: dict[DocumentKey, Draft] = {}

    def save(self, document: DocumentKey, state: Draft) -> None:
        """Record the immutable value or fail before touching stored state.

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
        if self.fail:
            raise OSError("Simulated write failure")
        self.saved[document] = state


class SessionTests(unittest.TestCase):
    """Protect dirty revisions, scoped commands and predictable undo/redo."""

    def setUp(self) -> None:
        """Create a fresh loaded document for each independent workflow.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("project-a", "document-a")
        self.session = DocumentSession(self.key, Draft("Original"), persisted=True)
        self.store = MemoryStore()

    def test_new_and_loaded_documents_have_distinct_save_states(self) -> None:
        """New drafts need saving even with no edits; loaded drafts start clean.

        Args:
            None.

        Returns:
            None.
        """
        self.assertFalse(self.session.is_dirty)
        new = DocumentSession(self.key, Draft("New"))
        self.assertTrue(new.is_dirty)
        new.save(self.store)
        self.assertFalse(new.is_dirty)
        self.assertEqual(self.store.saved[self.key], new.state)

    def test_edit_save_undo_redo_returns_to_clean_revision(self) -> None:
        """Saving adds no history entry; redo can return exactly to saved state.

        Args:
            None.

        Returns:
            None.
        """
        self.assertTrue(self.session.execute(Rename(self.key, "Edited")))
        self.assertTrue(self.session.is_dirty)
        self.assertEqual(self.session.undo_label_key, "edit.rename")
        self.session.save(self.store)
        saved_revision = self.session.revision
        self.assertFalse(self.session.is_dirty)
        self.assertTrue(self.session.undo())
        self.assertEqual(self.session.state.title, "Original")
        self.assertTrue(self.session.is_dirty)
        self.assertEqual(self.session.redo_label_key, "edit.rename")
        self.assertTrue(self.session.redo())
        self.assertEqual(self.session.revision, saved_revision)
        self.assertFalse(self.session.is_dirty)

    def test_undo_to_loaded_state_is_clean(self) -> None:
        """An unsaved edit is fully reversible back to the loaded revision.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(Rename(self.key, "Edited"))
        self.session.undo()
        self.assertFalse(self.session.is_dirty)

    def test_branch_cannot_reuse_a_saved_revision_number(self) -> None:
        """Editing after undo discards redo without accidentally marking clean.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(Rename(self.key, "Saved branch"))
        self.session.save(self.store)
        old_revision = self.session.revision
        self.session.undo()
        self.session.execute(Rename(self.key, "New branch"))
        self.assertGreater(self.session.revision, old_revision)
        self.assertTrue(self.session.is_dirty)
        self.assertIsNone(self.session.redo_label_key)
        self.assertFalse(self.session.redo())
        self.session.undo()
        self.assertTrue(self.session.is_dirty)

    def test_noop_preserves_redo_and_revision(self) -> None:
        """An unchanged form submission must not invalidate an undo branch.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(Rename(self.key, "Edited"))
        self.session.undo()
        self.assertFalse(self.session.execute(Rename(self.key, "Original")))
        self.assertEqual(self.session.revision, 0)
        self.assertFalse(self.session.is_dirty)
        self.assertTrue(self.session.redo())

    def test_failed_command_preserves_history_and_allows_retry(self) -> None:
        """Validation failure neither creates an edit nor discards redo.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(Rename(self.key, "Edited"))
        self.session.undo()
        with self.assertRaises(ValueError):
            self.session.execute(Rename(self.key, ""))
        self.assertEqual(self.session.state, Draft("Original"))
        self.assertFalse(self.session.is_dirty)
        self.assertTrue(self.session.redo())

    def test_failed_save_preserves_old_storage_and_clean_marker(self) -> None:
        """A failed write cannot make an unsaved revision appear durable.

        Args:
            None.

        Returns:
            None.
        """
        self.session.save(self.store)
        self.session.execute(Rename(self.key, "Edited"))
        self.store.fail = True
        with self.assertRaises(OSError):
            self.session.save(self.store)
        self.assertEqual(self.store.saved[self.key], Draft("Original"))
        self.assertTrue(self.session.is_dirty)
        self.session.undo()
        self.assertFalse(self.session.is_dirty)
        self.session.redo()
        self.store.fail = False
        self.session.save(self.store)
        self.assertFalse(self.session.is_dirty)

    def test_empty_history_actions_are_safe_noops(self) -> None:
        """Unavailable actions do not create dirty state or invalid cursors.

        Args:
            None.

        Returns:
            None.
        """
        self.assertIsNone(self.session.undo_label_key)
        self.assertIsNone(self.session.redo_label_key)
        self.assertFalse(self.session.undo())
        self.assertFalse(self.session.redo())
        self.assertFalse(self.session.is_dirty)

    def test_project_and_document_ownership_are_both_enforced(self) -> None:
        """Prevent cross-project and cross-document changes or history leaks.

        Args:
            None.

        Returns:
            None.
        """
        for key in (
            DocumentKey("other", "document-a"),
            DocumentKey("project-a", "other"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.session.execute(Rename(key, "Wrong target"))
        other = DocumentSession(DocumentKey("project-b", "document-a"), Draft("Other"))
        other.execute(Rename(other.document, "Other changed"))
        self.assertEqual(self.session.state, Draft("Original"))
        self.assertFalse(self.session.is_dirty)

    def test_blank_identifiers_and_action_keys_are_rejected(self) -> None:
        """Require stable identities and usable action-label keys.

        Args:
            None.

        Returns:
            None.
        """
        for project, document in (("", "a"), ("a", " ")):
            with self.assertRaises(ValueError):
                DocumentKey(project, document)
        with self.assertRaises(ValueError):
            self.session.execute(Rename(self.key, "Edited", " "))
        self.assertFalse(self.session.is_dirty)

    def test_save_reentrancy_cannot_change_the_snapshot(self) -> None:
        """An adapter callback cannot edit, undo, redo or save the active session.

        Args:
            None.

        Returns:
            None.
        """
        session = self.session
        store = self.store
        actions = (
            lambda: session.execute(Rename(self.key, "Unexpected")),
            session.undo,
            session.redo,
            lambda: session.save(store),
        )

        class ReentrantStore:
            """Adapter fixture attempting a forbidden recursive operation."""

            def __init__(self, action: Callable[[], object]) -> None:
                """Bind an action independently of loop-variable changes.

                Args:
                    action: Injected operation or named action selected for
                        reentrancy/dirty-consent testing.

                Returns:
                    None.
                """
                self.action = action

            def save(self, document: DocumentKey, state: Draft) -> None:
                """Attempt the selected operation before any persistence.

                Args:
                    document: Exact project/document key whose state is read or written
                        in isolation.
                    state: Immutable draft snapshot being validated, loaded or persisted
                        by this test callback.

                Returns:
                    None.
                """
                self.action()

        for action in actions:
            with self.assertRaises(RuntimeError):
                session.save(ReentrantStore(action))
            self.assertEqual(session.state, Draft("Original"))
            self.assertFalse(session.is_dirty)
        session.execute(Rename(self.key, "Retry"))
        session.save(store)
        self.assertFalse(session.is_dirty)

    def test_edit_reentrancy_is_rejected_without_losing_history(self) -> None:
        """A command callback cannot recursively modify its own history.

        Args:
            None.

        Returns:
            None.
        """
        session = self.session

        class RecursiveEdit:
            """Invalid command fixture attempting a nested edit operation."""

            document = session.document
            label_key = "edit.recursive"

            def apply(self, state: Draft) -> Draft:
                """Attempt undo while the outer command is being validated.

                Args:
                    state: Immutable draft snapshot being validated, loaded or persisted
                        by this test callback.

                Returns:
                    Immutable Draft replacement after validation; no repository write
                    occurs.
                """
                session.undo()
                return state

        with self.assertRaises(RuntimeError):
            session.execute(RecursiveEdit())
        self.assertEqual(session.revision, 0)
        self.assertFalse(session.is_dirty)
        self.assertTrue(session.execute(Rename(self.key, "Retry")))
