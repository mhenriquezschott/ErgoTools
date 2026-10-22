"""Assessment input validation and source freshness across real session operations.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import math
import sqlite3
import unittest
from dataclasses import FrozenInstanceError, replace

from ergotools.application.assessments.lifft_commands import ReplaceLifftTask
from ergotools.application.assessments.lifft_preparation import prepare_lifft
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import DraftError, LifftDraft, LifftTask
from ergotools.domain.assessments.lifft_validation import validate_lifft_input
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.lifft_store import LifftSqliteStore
from ergotools.presentation.localization import Language, Translator


class LifftPreparationTests(unittest.TestCase):
    """Reject incomplete source and stale reuse without mutating drafts or storage."""

    def setUp(self) -> None:
        """Create an independent loaded session for each scenario.

        Args:
            None.

        Returns:
            None.
        """
        self.task = LifftTask("a", 12, 100, 100)
        self.draft = LifftDraft(MeasurementSystem.IMPERIAL, (self.task,))
        self.session = DocumentSession(
            DocumentKey("p", "d"), self.draft, persisted=True
        )

    def test_collects_all_issues_in_task_and_field_order(self) -> None:
        """One invalid field must not hide later rows' missing or invalid values.

        Args:
            None.

        Returns:
            None.
        """
        draft = replace(
            self.draft,
            tasks=(LifftTask("a", None, -1, True), LifftTask("b", 0, None, None)),
        )
        session = DocumentSession(self.session.document, draft)
        prepared = prepare_lifft(session)
        self.assertFalse(prepared.has_valid_inputs)
        self.assertEqual(
            [(i.task_id, i.field, i.code) for i in prepared.issues],
            [
                ("a", "lever_arm", "validation.required"),
                ("a", "load", "validation.nonnegative"),
                ("a", "repetitions", "validation.number"),
                ("b", "load", "validation.required"),
                ("b", "repetitions", "validation.required"),
            ],
        )
        self.assertIs(prepared.source, draft)
        self.assertIsNone(draft.tasks[0].lever_arm)
        self.assertEqual(session.revision, 0)
        self.assertTrue(session.is_dirty)

    def test_empty_is_incomplete_but_zero_and_fractional_inputs_are_present(
        self,
    ) -> None:
        """Do not conflate absent tasks/inputs with complete zero-damage inputs.

        Args:
            None.

        Returns:
            None.
        """
        empty = prepare_lifft(
            DocumentSession(self.session.document, replace(self.draft, tasks=()))
        )
        self.assertFalse(empty.has_valid_inputs)
        self.assertEqual(empty.issues[0].code, "validation.tasks_required")
        for system in MeasurementSystem:
            draft = LifftDraft(system, (LifftTask("zero", 0, 0, 0.5),))
            ready = prepare_lifft(DocumentSession(self.session.document, draft))
            self.assertTrue(ready.has_valid_inputs)
            self.assertEqual(ready.source.system, system)

    def test_edit_undo_redo_and_branch_control_freshness(self) -> None:
        """Exact restored revisions can reuse a preparation; new branches cannot.

        Args:
            None.

        Returns:
            None.
        """
        original = prepare_lifft(self.session)
        changed = replace(self.task, load=200)
        self.session.execute(
            ReplaceLifftTask(self.session.document, self.task, changed)
        )
        edited = prepare_lifft(self.session)
        self.assertFalse(original.is_current(self.session))
        self.assertTrue(edited.is_current(self.session))
        self.session.undo()
        self.assertTrue(original.is_current(self.session))
        self.assertFalse(edited.is_current(self.session))
        self.session.redo()
        self.assertTrue(edited.is_current(self.session))
        self.session.undo()
        self.session.execute(
            ReplaceLifftTask(self.session.document, self.task, changed)
        )
        self.assertEqual(self.session.state, edited.source)
        self.assertFalse(edited.is_current(self.session))

    def test_noop_and_failed_edit_preserve_preparation(self) -> None:
        """Unchanged source must not become stale merely because an edit was tried.

        Args:
            None.

        Returns:
            None.
        """
        prepared = prepare_lifft(self.session)
        self.assertFalse(
            self.session.execute(
                ReplaceLifftTask(self.session.document, self.task, self.task)
            )
        )
        with self.assertRaises(DraftError):
            self.session.execute(
                ReplaceLifftTask(
                    self.session.document, replace(self.task, load=7), self.task
                )
            )
        self.assertTrue(prepared.is_current(self.session))
        self.assertFalse(self.session.is_dirty)

    def test_save_preserves_freshness_but_reload_does_not(self) -> None:
        """Real SQLite persistence cannot turn a new session into the old origin.

        Args:
            None.

        Returns:
            None.
        """
        connection = sqlite3.connect(":memory:")
        try:
            store = LifftSqliteStore.create(connection)
            prepared = prepare_lifft(self.session)
            self.session.save(store)
            self.assertTrue(prepared.is_current(self.session))
            loaded = DocumentSession(
                self.session.document, store.load(self.session.document), persisted=True
            )
            self.assertEqual(loaded.state, prepared.source)
            self.assertEqual(loaded.revision, prepared.revision)
            self.assertFalse(prepared.is_current(loaded))
            self.assertTrue(prepare_lifft(loaded).is_current(loaded))
        finally:
            connection.close()

    def test_close_and_another_session_with_identical_source_are_not_current(
        self,
    ) -> None:
        """Session identity prevents reuse even if a caller shares the same snapshot.

        Args:
            None.

        Returns:
            None.
        """
        prepared = prepare_lifft(self.session)
        other = DocumentSession(self.session.document, self.draft)
        self.assertFalse(prepared.is_current(other))
        self.assertFalse(prepared.is_current(None))

    def test_preparation_is_read_only_and_immutable(self) -> None:
        """Preparation does not mark dirty, create history or rewrite source.

        Args:
            None.

        Returns:
            None.
        """
        prepared = prepare_lifft(self.session)
        self.assertTrue(prepared.has_valid_inputs)
        self.assertFalse(self.session.is_dirty)
        self.assertIsNone(self.session.undo_label_key)
        with self.assertRaises(FrozenInstanceError):
            prepared.revision = 99
        self.assertIs(self.session.state, self.draft)

    def test_shared_numeric_boundary_reports_unsupported_values(self) -> None:
        """Share numeric checks and structured issue identity across both callers.

        Args:
            None.

        Returns:
            None.
        """
        for value, code in (
            (None, "validation.required"),
            (False, "validation.number"),
            (-1, "validation.nonnegative"),
            (math.nan, "validation.nonfinite"),
            (math.inf, "validation.nonfinite"),
            (10**400, "validation.number"),
            (object(), "validation.number"),
            ("bad", "validation.number"),
        ):
            with self.assertRaises(DraftError) as caught:
                validate_lifft_input(value, "load", "a")
            self.assertEqual(caught.exception.issue.code, code)
            self.assertEqual(caught.exception.issue.field, "load")
            self.assertEqual(caught.exception.issue.task_id, "a")
        self.assertEqual(validate_lifft_input(0.5, "repetitions", "a"), 0.5)

    def test_empty_assessment_issue_is_localized_in_both_languages(self) -> None:
        """The new preparation issue has English and Spanish display messages.

        Args:
            None.

        Returns:
            None.
        """
        for language in Language:
            self.assertTrue(Translator(language).text("validation.tasks_required"))
