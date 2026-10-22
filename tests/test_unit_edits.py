"""Explicit display-unit edits preserve untouched source and transactional history.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
    prepare_assessment,
)
from ergotools.application.assessments.unit_edits import edit_display_input
from ergotools.application.assessments.unit_view import (
    AssessmentUnitView,
    prepare_unit_view,
)
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.presentation.localization import Language, Translator


class UnitEditTests(unittest.TestCase):
    """Exercise both models, unit directions, history and real storage failures."""

    def setUp(self) -> None:
        """Keep decimal source values and task order explicit in every workflow.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("p", "assessment")
        self.task = LifftTask("a", 12.3456789012345, 10.987654321, 100.25)
        self.draft = LifftDraft(MeasurementSystem.IMPERIAL, (self.task, LifftTask("b")))
        self.session = DocumentSession(self.key, self.draft, persisted=True)

    def test_both_models_units_and_fields_convert_only_the_named_value(self) -> None:
        """A deliberate field edit keeps source units and every other field exact.

        Args:
            None.

        Returns:
            None.
        """
        for system in MeasurementSystem:
            for target in MeasurementSystem:
                for model in ("lifft", "tst"):
                    task = (
                        self.task
                        if model == "lifft"
                        else TstTask(
                            "a",
                            TstDirection.HORIZONTAL,
                            self.task.lever_arm,
                            self.task.load,
                            self.task.repetitions,
                        )
                    )
                    source = (
                        LifftDraft(system, (task,))
                        if model == "lifft"
                        else TstDraft(system, (task,))
                    )
                    for field, factor in (("lever_arm", 2.54), ("load", 4.45)):
                        session = DocumentSession(self.key, source, persisted=True)
                        view = prepare_unit_view(session, target)
                        entered = 20.123
                        expected = (
                            entered
                            if target is system
                            else (
                                entered / factor
                                if target is MeasurementSystem.METRIC
                                else entered * factor
                            )
                        )
                        self.assertTrue(
                            edit_display_input(session, view, "a", field, entered)
                        )
                        self.assertEqual(
                            session.state.tasks[0], replace(task, **{field: expected})
                        )
                        self.assertIs(session.state.system, system)
                        self.assertTrue(session.is_dirty)
                        self.assertEqual(session.revision, 1)
                        self.assertFalse(view.is_current(session))
                        session.undo()
                        self.assertIs(session.state, source)
                        self.assertFalse(session.is_dirty)
                        session.redo()
                        self.assertEqual(
                            getattr(session.state.tasks[0], field), expected
                        )

    def test_reentered_exact_projection_preserves_source_precision_and_redo(
        self,
    ) -> None:
        """Unchanged displayed inputs never get multiplied/divided back into source.

        Args:
            None.

        Returns:
            None.
        """
        view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
        edit_display_input(self.session, view, "a", "load", 44.5)
        self.session.undo()
        redo_label = self.session.redo_label_key
        for field in ("lever_arm", "load"):
            self.assertFalse(
                edit_display_input(
                    self.session, view, "a", field, getattr(view.tasks[0], field)
                )
            )
            self.assertIs(self.session.state, self.draft)
            self.assertEqual(self.session.revision, 0)
            self.assertEqual(self.session.redo_label_key, redo_label)
        self.assertFalse(edit_display_input(self.session, view, "b", "load", None))
        self.assertTrue(self.session.redo())

    def test_clearing_signed_values_and_missing_source(self) -> None:
        """None clears exactly one field; signed finite values remain reviewable.

        Args:
            None.

        Returns:
            None.
        """
        for field in ("lever_arm", "load"):
            session = DocumentSession(self.key, self.draft)
            self.assertTrue(
                edit_display_input(
                    session,
                    prepare_unit_view(session, MeasurementSystem.METRIC),
                    "a",
                    field,
                    None,
                )
            )
            self.assertIsNone(getattr(session.state.tasks[0], field))
            self.assertTrue(
                edit_display_input(
                    session,
                    prepare_unit_view(session, MeasurementSystem.IMPERIAL),
                    "a",
                    field,
                    -1.25,
                )
            )
            self.assertEqual(getattr(session.state.tasks[0], field), -1.25)
            self.assertTrue(prepare_assessment(session).issues)
        view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
        edit_display_input(self.session, view, "b", "load", 4.45)
        self.assertEqual(self.session.state.tasks[1], LifftTask("b", None, 1, None))
        self.assertIs(self.session.state.tasks[0], self.task)

    def test_stale_foreign_reloaded_and_branched_views_are_rejected(self) -> None:
        """No old projection may overwrite a newer source or another session.

        Args:
            None.

        Returns:
            None.
        """
        view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
        edit_display_input(self.session, view, "a", "load", 44.5)
        changed_view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
        for active in (
            self.session,
            DocumentSession(self.key, self.draft),
            DocumentSession(DocumentKey("other", "assessment"), self.draft),
        ):
            before = active.state
            with self.assertRaises(DraftError) as caught:
                edit_display_input(active, view, "a", "load", 89)
            self.assertEqual(caught.exception.issue.code, "validation.stale_view")
            self.assertIs(active.state, before)
        self.session.undo()
        self.assertTrue(edit_display_input(self.session, view, "a", "load", 89))
        with self.assertRaises(DraftError):
            edit_display_input(self.session, changed_view, "a", "load", 44.5)
        for language in Language:
            self.assertTrue(Translator(language).text("validation.stale_view"))

    def test_invalid_numeric_edits_preserve_history_and_results(self) -> None:
        """Bad values fail before mutation, including boolean equality and overflow.

        Args:
            None.

        Returns:
            None.
        """
        source = LifftDraft(MeasurementSystem.METRIC, (LifftTask("a", 2.54, 4.45, 1),))
        session = DocumentSession(self.key, source, persisted=True)
        view = prepare_unit_view(session, MeasurementSystem.IMPERIAL)
        for value in (True, "1", float("nan"), float("inf"), 10**400, 1e308):
            with self.assertRaises(DraftError):
                edit_display_input(session, view, "a", "load", value)
            self.assertIs(session.state, source)
            self.assertFalse(session.is_dirty)
            self.assertIsNone(session.undo_label_key)
        imperial = DocumentSession(self.key, self.draft, persisted=True)
        with self.assertRaises(DraftError):
            edit_display_input(
                imperial,
                prepare_unit_view(imperial, MeasurementSystem.METRIC),
                "a",
                "load",
                5e-324,
            )
        self.assertIs(imperial.state, self.draft)

    def test_unknown_task_field_or_unitless_source_fails_explicitly(self) -> None:
        """No guessed fields, row-index identity or DUET force conversion.

        Args:
            None.

        Returns:
            None.
        """
        view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
        with self.assertRaises(DraftError) as caught:
            edit_display_input(self.session, view, "absent", "load", 1)
        self.assertEqual(caught.exception.issue.code, "validation.missing_task")
        for field in ("repetitions", "direction", "system", "mass"):
            with self.assertRaises(ValueError):
                edit_display_input(self.session, view, "a", field, 1)
        session = DocumentSession(self.key, DuetDraft())
        unitless = AssessmentUnitView(
            prepare_assessment(session), MeasurementSystem.METRIC, ()
        )
        with self.assertRaises(ValueError):
            edit_display_input(session, unitless, "a", "load", 1)

    def test_evaluation_freshness_and_scientific_gates_follow_source(self) -> None:
        """Editing invalidates results; displaying imperial never removes review.

        Args:
            None.

        Returns:
            None.
        """
        for source, status in (
            (
                LifftDraft(MeasurementSystem.IMPERIAL, (self.task,)),
                EvaluationStatus.COMPLETE,
            ),
            (
                LifftDraft(MeasurementSystem.METRIC, (self.task,)),
                EvaluationStatus.COMPLETE,
            ),
            (
                TstDraft(
                    MeasurementSystem.METRIC,
                    (TstTask("a", TstDirection.DOWNWARD, 12, 10, 100),),
                ),
                EvaluationStatus.COMPLETE,
            ),
        ):
            session = DocumentSession(self.key, source, persisted=True)
            evaluator = AssessmentEvaluator()
            prior = evaluator.evaluate(session)
            edit_display_input(
                session,
                prepare_unit_view(session, MeasurementSystem.IMPERIAL),
                "a",
                "load",
                5,
            )
            self.assertIsNone(evaluator.current(session))
            self.assertEqual(evaluator.evaluate(session).status, status)
            session.undo()
            self.assertEqual(evaluator.evaluate(session).summary, prior.summary)

    def test_failed_save_retry_and_reopen_preserve_converted_source(self) -> None:
        """Failed saves retain the previous disk state and the edited history.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "edit.sqlite"
            meta = ProjectMetadata("p", "Units", MeasurementSystem.METRIC)
            with AssessmentProjectFile.create_with_document(
                path, meta, self.key.document_id, self.draft
            ):
                pass
            with closing(sqlite3.connect(path)) as connection:
                store = AssessmentSqliteStore(connection)
                edit_display_input(
                    self.session,
                    prepare_unit_view(self.session, MeasurementSystem.METRIC),
                    "a",
                    "load",
                    44.5,
                )
                connection.execute(
                    "CREATE TRIGGER reject_update BEFORE UPDATE ON draft_documents "
                    "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    self.session.save(store)
                self.assertTrue(self.session.is_dirty)
                self.assertEqual(store.load(self.key), self.draft)
                self.assertFalse(connection.in_transaction)
                connection.execute("DROP TRIGGER reject_update")
                self.session.save(store)
                self.assertFalse(self.session.is_dirty)
            with AssessmentProjectFile.open(path) as project:
                loaded = project.load(self.key)
                self.assertEqual(loaded, self.session.state)
                self.assertEqual(loaded.tasks[0].load, 10)
                self.assertEqual(loaded.tasks[0].lever_arm, self.task.lever_arm)
                self.assertEqual(loaded.system, MeasurementSystem.IMPERIAL)
                self.assertEqual(project.metadata, meta)
