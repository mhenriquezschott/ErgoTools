"""Exercise real LiFFT source drafts through the generic document history.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import math
import unittest
from dataclasses import FrozenInstanceError, replace

from ergotools.application.assessments.lifft_commands import (
    AddLifftTask,
    RemoveLifftTask,
    ReplaceLifftTask,
)
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import DraftError, LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.localization import Language, Translator


class LifftDraftTests(unittest.TestCase):
    """Protect task identity, incomplete data, units and reversible editing."""

    def setUp(self) -> None:
        """Load an immutable two-task assessment with an explicit metric system.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("project-a", "lifft-a")
        self.first = LifftTask("task-a", 25.4, 44.5, 100)
        self.second = LifftTask("task-b", 12.7, 22.25, None)
        self.initial = LifftDraft(MeasurementSystem.METRIC, (self.first, self.second))
        self.session = DocumentSession(self.key, self.initial, persisted=True)

    def test_missing_fields_remain_distinct_from_zero(self) -> None:
        """A partial draft must not silently acquire zero repetitions or results.

        Args:
            None.

        Returns:
            None.
        """
        issues = self.second.missing_inputs()
        self.assertEqual(len(issues), 1)
        self.assertEqual(
            (issues[0].code, issues[0].field, issues[0].task_id),
            ("validation.required", "repetitions", "task-b"),
        )
        self.assertEqual(LifftTask("zero", 0, 0, 0).missing_inputs(), ())
        self.assertEqual(
            [i.field for i in LifftTask("blank").missing_inputs()],
            ["lever_arm", "load", "repetitions"],
        )

    def test_nonfinite_values_have_structured_field_context(self) -> None:
        """Reject NaN/infinity in each field without logging the entered value.

        Args:
            None.

        Returns:
            None.
        """
        for field in ("lever_arm", "load", "repetitions"):
            for value in (math.nan, math.inf, -math.inf):
                with (
                    self.subTest(field=field, value=value),
                    self.assertRaises(DraftError) as caught,
                ):
                    replace(self.first, **{field: value})
                self.assertEqual(caught.exception.issue.code, "validation.nonfinite")
                self.assertEqual(caught.exception.issue.field, field)
                self.assertEqual(caught.exception.issue.task_id, "task-a")

    def test_draft_does_not_invent_physical_or_integer_limits(self) -> None:
        """Retain finite source data for model review rather than silently clamp it.

        Args:
            None.

        Returns:
            None.
        """
        task = LifftTask("review", -1, 1e12, 0.5)
        self.assertEqual((task.lever_arm, task.load, task.repetitions), (-1, 1e12, 0.5))
        self.assertEqual(task.missing_inputs(), ())

    def test_invalid_identity_units_and_duplicates_are_rejected(self) -> None:
        """Prevent ambiguous addressing and unsupported unit interpretation.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(DraftError) as caught:
            LifftTask(" ")
        self.assertEqual(caught.exception.issue.field, "task_id")
        with self.assertRaises(DraftError) as caught:
            LifftDraft("unknown")
        self.assertEqual(caught.exception.issue.code, "validation.unit")
        with self.assertRaises(DraftError) as caught:
            LifftDraft(MeasurementSystem.METRIC, (self.first, self.first))
        self.assertEqual(caught.exception.issue.code, "validation.duplicate")

    def test_snapshot_cannot_be_changed_through_input_collection(self) -> None:
        """Copy a boundary collection to a tuple and keep frozen task fields.

        Args:
            None.

        Returns:
            None.
        """
        source = [self.first]
        draft = LifftDraft(MeasurementSystem.IMPERIAL, source)
        source.clear()
        self.assertEqual(draft.tasks, (self.first,))
        with self.assertRaises(FrozenInstanceError):
            draft.tasks[0].load = 0

    def test_insert_edit_remove_undo_restores_exact_order_and_values(self) -> None:
        """Real assessment commands share one coherent document history.

        Args:
            None.

        Returns:
            None.
        """
        inserted = LifftTask("new")
        self.session.execute(AddLifftTask(self.key, inserted, 1))
        updated = replace(inserted, lever_arm=20, load=30, repetitions=40)
        self.session.execute(ReplaceLifftTask(self.key, inserted, updated))
        self.session.execute(RemoveLifftTask(self.key, self.first))
        self.assertEqual(self.session.state.tasks, (updated, self.second))
        self.assertEqual(self.session.state.system, MeasurementSystem.METRIC)
        for _ in range(3):
            self.assertTrue(self.session.undo())
        self.assertEqual(self.session.state, self.initial)
        self.assertFalse(self.session.is_dirty)
        for _ in range(3):
            self.assertTrue(self.session.redo())
        self.assertEqual(self.session.state.tasks, (updated, self.second))

    def test_insert_edges_and_invalid_positions(self) -> None:
        """Allow prepend/append while rejecting Python's negative slice semantics.

        Args:
            None.

        Returns:
            None.
        """
        empty = LifftDraft(MeasurementSystem.IMPERIAL)
        self.assertEqual(
            AddLifftTask(self.key, self.first, 0).apply(empty).tasks, (self.first,)
        )
        self.assertEqual(
            AddLifftTask(self.key, LifftTask("last"), 2)
            .apply(self.initial)
            .tasks[-1]
            .task_id,
            "last",
        )
        for index in (-1, 3):
            with self.assertRaises(DraftError) as caught:
                self.session.execute(AddLifftTask(self.key, LifftTask("new"), index))
            self.assertEqual(caught.exception.issue.code, "validation.position")
        self.assertFalse(self.session.is_dirty)

    def test_duplicate_insert_does_not_change_history(self) -> None:
        """Invalid insertion is atomic and leaves the loaded revision clean.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(DraftError):
            self.session.execute(AddLifftTask(self.key, self.first, 0))
        self.assertEqual(self.session.state, self.initial)
        self.assertIsNone(self.session.undo_label_key)

    def test_stale_edit_and_delete_preserve_current_data(self) -> None:
        """A previously displayed row cannot overwrite or delete newer fields.

        Args:
            None.

        Returns:
            None.
        """
        changed = replace(self.first, load=99)
        self.session.execute(ReplaceLifftTask(self.key, self.first, changed))
        for command in (
            ReplaceLifftTask(self.key, self.first, replace(self.first, load=1)),
            RemoveLifftTask(self.key, self.first),
        ):
            with self.assertRaises(DraftError) as caught:
                self.session.execute(command)
            self.assertEqual(caught.exception.issue.code, "validation.stale_task")
        self.assertEqual(self.session.state.tasks[0], changed)
        self.assertEqual(self.session.revision, 1)

    def test_absent_task_and_identity_changes_are_rejected(self) -> None:
        """Task identity cannot be reassigned through an edit operation.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(DraftError) as caught:
            self.session.execute(RemoveLifftTask(self.key, LifftTask("absent")))
        self.assertEqual(caught.exception.issue.code, "validation.missing_task")
        with self.assertRaises(DraftError) as caught:
            self.session.execute(ReplaceLifftTask(self.key, self.first, self.second))
        self.assertEqual(caught.exception.issue.code, "validation.identity")
        self.assertFalse(self.session.is_dirty)

    def test_unchanged_replacement_keeps_redo_branch(self) -> None:
        """Re-submitting an unchanged task must not erase reversible work.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(RemoveLifftTask(self.key, self.second))
        self.session.undo()
        self.assertFalse(
            self.session.execute(ReplaceLifftTask(self.key, self.first, self.first))
        )
        self.assertTrue(self.session.redo())

    def test_wrong_document_commands_are_rejected(self) -> None:
        """Assessment commands cannot be applied to another document's history.

        Args:
            None.

        Returns:
            None.
        """
        other = DocumentKey("project-b", "lifft-a")
        with self.assertRaises(ValueError):
            self.session.execute(RemoveLifftTask(other, self.first))
        self.assertFalse(self.session.is_dirty)

    def test_command_and_validation_catalogs_are_complete(self) -> None:
        """Every new action and issue code has an English and Spanish message.

        Args:
            None.

        Returns:
            None.
        """
        keys = {
            "edit.lifft.add_task",
            "edit.lifft.replace_task",
            "edit.lifft.remove_task",
            "validation.required",
            "validation.nonfinite",
            "validation.unit",
            "validation.duplicate",
            "validation.missing_task",
            "validation.stale_task",
            "validation.position",
            "validation.identity",
        }
        self.assertEqual(
            Translator(Language.ENGLISH).keys, Translator(Language.SPANISH).keys
        )
        for language in Language:
            translator = Translator(language)
            for key in keys:
                self.assertTrue(translator.text(key).strip())
            for command in (
                AddLifftTask(self.key, LifftTask("new"), 0),
                ReplaceLifftTask(self.key, self.first, self.first),
                RemoveLifftTask(self.key, self.first),
            ):
                self.assertTrue(translator.text(command.label_key))
        self.assertEqual(self.session.state, self.initial)
