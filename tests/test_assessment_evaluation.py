"""Mixed-source evaluation, review gates and result freshness across real sessions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

from ergotools.application.assessments.duet_commands import AddDuetTask
from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
    prepare_assessment,
)
from ergotools.application.assessments.project_edits import DuetProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class AssessmentEvaluationTests(unittest.TestCase):
    """Require complete source-bound outcomes; no silent partial or stale results."""

    def setUp(self) -> None:
        """Create an independently owned DUET session and evaluator.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("p", "assessment")
        self.source = DuetDraft((DuetTask("a", 5, 100),))
        self.session = DocumentSession(self.key, self.source, persisted=True)
        self.evaluator = AssessmentEvaluator()

    def test_complete_workflows_match_original_assessment_fixtures(self) -> None:
        """Compare all nonempty DUET/LiFFT summary groups in both unit systems.

        Args:
            None.

        Returns:
            None.
        """
        count = 0
        for name in ("duet", "lifft"):
            fixture = json.loads(
                (
                    Path(__file__).parent / f"fixtures/{name}_summary_reference.json"
                ).read_text()
            )
            for record in fixture["records"]:
                if not record["inputs"]:
                    continue
                if name == "duet":
                    source = DuetDraft(
                        tuple(
                            DuetTask(str(i), *values)
                            for i, values in enumerate(record["inputs"])
                        )
                    )
                else:
                    source = LifftDraft(
                        MeasurementSystem(record["system"]),
                        tuple(
                            LifftTask(str(i), *values)
                            for i, values in enumerate(record["inputs"])
                        ),
                    )
                session = DocumentSession(self.key, source)
                outcome = self.evaluator.evaluate(session)
                self.assertEqual(outcome.status, EvaluationStatus.COMPLETE)
                self.assertEqual(outcome.summary.total_damage, record["total"])
                self.assertEqual(
                    [c.percentage for c in outcome.summary.contributions],
                    record["contributions"],
                )
                self.assertEqual(len(outcome.task_results), len(source.tasks))
                self.assertIs(self.evaluator.current(session), outcome)
                count += 1
        self.assertEqual(count, 120)

    def test_invalid_sources_return_all_issues_without_partial_results(self) -> None:
        """Valid rows must not turn an incomplete assessment into a plausible total.

        Args:
            None.

        Returns:
            None.
        """
        for source in (
            DuetDraft(),
            LifftDraft(MeasurementSystem.IMPERIAL),
            DuetDraft((DuetTask("good", 5, 100), DuetTask("bad", None, -1))),
            LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("bad", None, -1, None),)),
        ):
            session = DocumentSession(self.key, source)
            outcome = self.evaluator.evaluate(session)
            self.assertEqual(outcome.status, EvaluationStatus.INVALID_INPUT)
            self.assertTrue(outcome.issues)
            self.assertEqual(outcome.task_results, ())
            self.assertIsNone(outcome.summary)
        self.assertEqual(len(outcome.issues), 3)

    def test_metric_compatibility_retains_invalid_input_guards(self) -> None:
        """Reference conversion is usable; missing metric inputs still fail closed.

        Args:
            None.

        Returns:
            None.
        """
        source = LifftDraft(
            MeasurementSystem.METRIC, (LifftTask("a", 30.48, 44.5, 100),)
        )
        session = DocumentSession(self.key, source, persisted=True)
        outcome = self.evaluator.evaluate(session)
        self.assertEqual(outcome.status, EvaluationStatus.COMPLETE)
        self.assertIsNotNone(outcome.summary)
        self.assertEqual(outcome.issues, ())
        self.assertIs(session.state, source)
        self.assertFalse(session.is_dirty)
        invalid = DocumentSession(
            self.key, LifftDraft(MeasurementSystem.METRIC, (LifftTask("a"),))
        )
        self.assertEqual(
            self.evaluator.evaluate(invalid).status, EvaluationStatus.INVALID_INPUT
        )

    def test_edit_undo_redo_new_branch_and_recomputation_control_cache(self) -> None:
        """Only the actual captured revision is eligible while it remains cached.

        Args:
            None.

        Returns:
            None.
        """
        self.assertIsNone(self.evaluator.current(self.session))
        original = self.evaluator.evaluate(self.session)
        command = DuetProjectEdit(AddDuetTask(self.key, DuetTask("b", 10, 100), 1))
        self.session.execute(command)
        self.assertIsNone(self.evaluator.current(self.session))
        self.session.undo()
        self.assertIs(self.evaluator.current(self.session), original)
        self.session.redo()
        changed = self.evaluator.evaluate(self.session)
        self.assertGreater(changed.summary.total_damage, original.summary.total_damage)
        self.session.undo()
        self.assertIsNone(self.evaluator.current(self.session))
        self.session.execute(command)
        self.assertEqual(self.session.state, changed.preparation.source)
        self.assertIsNone(self.evaluator.current(self.session))
        self.evaluator.clear()
        self.assertIsNone(self.evaluator.current(self.session))

    def test_known_overflow_discards_all_partial_task_results(self) -> None:
        """An error in a later row cannot expose an earlier row as a full result.

        Args:
            None.

        Returns:
            None.
        """
        for source in (
            LifftDraft(
                MeasurementSystem.IMPERIAL,
                (
                    LifftTask("good", 12, 100, 100),
                    LifftTask("overflow", 1e308, 1e308, 1),
                ),
            ),
            DuetDraft(tuple(DuetTask(str(i), 10, 1.7e308) for i in range(110))),
        ):
            outcome = self.evaluator.evaluate(DocumentSession(self.key, source))
            self.assertEqual(outcome.status, EvaluationStatus.CALCULATION_FAILED)
            self.assertEqual(outcome.issues[0].code, "validation.overflow")
            self.assertEqual(outcome.task_results, ())
            self.assertIsNone(outcome.summary)

    def test_unexpected_exception_clears_old_cache_and_propagates(self) -> None:
        """Do not hide implementation errors or retain a prior result after failure.

        Args:
            None.

        Returns:
            None.
        """
        self.evaluator.evaluate(self.session)
        with (
            patch(
                "ergotools.application.assessments.evaluation.calculate_duet_task",
                side_effect=RuntimeError("test"),
            ),
            self.assertRaises(RuntimeError),
        ):
            self.evaluator.evaluate(self.session)
        self.assertIsNone(self.evaluator.current(self.session))

    def test_evaluation_is_immutable_and_does_not_edit_or_mark_dirty(self) -> None:
        """Calculation has no source/history/persistence side effects.

        Args:
            None.

        Returns:
            None.
        """
        prepared = prepare_assessment(self.session)
        outcome = self.evaluator.evaluate(self.session)
        self.assertEqual(outcome.preparation.source, prepared.source)
        self.assertFalse(self.session.is_dirty)
        self.assertIsNone(self.session.undo_label_key)
        self.assertIs(self.session.state, self.source)
        with self.assertRaises(FrozenInstanceError):
            outcome.status = EvaluationStatus.INVALID_INPUT
        with self.assertRaises(FrozenInstanceError):
            outcome.preparation.revision = 99
        self.assertIsNone(self.evaluator.current(None))
        self.assertIsNone(
            self.evaluator.current(DocumentSession(self.key, self.source))
        )

    def test_zero_is_complete_with_absent_probability_not_incomplete(self) -> None:
        """Complete zero exposure has a summary but no evaluated model probability.

        Args:
            None.

        Returns:
            None.
        """
        outcome = self.evaluator.evaluate(
            DocumentSession(self.key, DuetDraft((DuetTask("a", 5, 0),)))
        )
        self.assertEqual(outcome.status, EvaluationStatus.COMPLETE)
        self.assertEqual(outcome.summary.total_damage, 0)
        self.assertIsNone(outcome.summary.probability)
        self.assertEqual(outcome.issues, ())

    def test_save_switch_and_reload_in_real_mixed_project(self) -> None:
        """Save preserves freshness; document switches and reloads invalidate it.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mixed.sqlite"
            with AssessmentProjectFile.create_with_document(
                path,
                ProjectMetadata("p", "Results", MeasurementSystem.METRIC),
                "assessment",
                self.source,
            ):
                pass
            workspace = ProjectWorkspace(
                lambda location: AssessmentProjectFile.open(Path(location)),
                JsonSettingsStore(Path(temporary) / "settings.json"),
            )
            try:
                workspace.switch(str(path), "assessment")
                outcome = self.evaluator.evaluate(workspace.active)
                workspace.save()
                self.assertIs(self.evaluator.current(workspace.active), outcome)
                workspace.create_assessment(
                    "lifft",
                    LifftDraft(
                        MeasurementSystem.IMPERIAL, (LifftTask("a", 12, 100, 100),)
                    ),
                )
                self.assertIsNone(self.evaluator.current(workspace.active))
                self.assertEqual(
                    self.evaluator.evaluate(workspace.active).status,
                    EvaluationStatus.COMPLETE,
                )
                workspace.switch(str(path), "assessment")
                self.assertIsNone(self.evaluator.current(workspace.active))
                self.evaluator.evaluate(workspace.active)
                workspace.close()
                self.assertIsNone(self.evaluator.current(workspace.active))
                workspace.switch(str(path), "assessment")
                self.assertIsNone(self.evaluator.current(workspace.active))
            finally:
                workspace.close(choice=CloseChoice.DISCARD)
                self.evaluator.clear()
