"""Reference output rows with source identity, unit gates and all-or-nothing display.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet import DuetTaskResult
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.lifft_results import present_lifft_results


class LifftResultDisplayTests(unittest.TestCase):
    """No widget or production dataset is needed to verify output associations."""

    def setUp(self) -> None:
        """Create a complete source whose task identities differ from row indices.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("p", "lifft")
        self.source = LifftDraft(
            MeasurementSystem.IMPERIAL,
            (LifftTask("stable-a", 12, 10, 100), LifftTask("stable-b", 30, 50, 200)),
        )
        self.session = DocumentSession(self.key, self.source, persisted=True)
        self.evaluator = AssessmentEvaluator()
        self.result = self.evaluator.evaluate(self.session)

    def test_reference_calculation_vectors_keep_output_precision(self) -> None:
        """Compare every imperial task fixture without enabling metric evaluation.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (
                Path(__file__).parent / "fixtures/lifft_calculation_reference.json"
            ).read_text()
        )
        count = 0
        for record in fixture["records"]:
            if record["system"] != "imperial":
                continue
            source = LifftDraft(
                MeasurementSystem.IMPERIAL,
                (
                    LifftTask(
                        "row",
                        record["lever_arm"],
                        record["load"],
                        record["repetitions"],
                    ),
                ),
            )
            session = DocumentSession(self.key, source)
            display = present_lifft_results(self.evaluator.evaluate(session), session)
            self.assertEqual(
                display.rows[0].moment_text, f"{record['display_moment']:.1f}"
            )
            self.assertEqual(display.rows[0].damage_text, f"{record['damage']:.4f}")
            count += 1
        self.assertEqual(count, 1075)

    def test_reference_summary_vectors_keep_order_contributions_and_colors(
        self,
    ) -> None:
        """Aggregate formatting and zero-color clearing match existing captures.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (
                Path(__file__).parent / "fixtures/lifft_summary_reference.json"
            ).read_text()
        )
        count = 0
        for record in fixture["records"]:
            if record["system"] != "imperial" or not record["inputs"]:
                continue
            source = LifftDraft(
                MeasurementSystem.IMPERIAL,
                tuple(
                    LifftTask(str(i), *values)
                    for i, values in enumerate(record["inputs"])
                ),
            )
            session = DocumentSession(self.key, source)
            display = present_lifft_results(self.evaluator.evaluate(session), session)
            self.assertEqual(
                [row.task_id for row in display.rows],
                [task.task_id for task in source.tasks],
            )
            self.assertEqual(
                [row.contribution_text for row in display.rows],
                [str(value) for value in record["contributions"]],
            )
            self.assertEqual([row.color for row in display.rows], record["task_colors"])
            self.assertEqual(display.summary.damage_text, record["damage_text"])
            self.assertEqual(
                display.summary.probability_text, record["probability_text"]
            )
            count += 1
        self.assertGreater(count, 20)

    def test_edit_reload_switch_and_undo_freshness(self) -> None:
        """Only the actual originating revision may display its output rows.

        Args:
            None.

        Returns:
            None.
        """
        expected = present_lifft_results(self.result, self.session)
        self.session.execute(
            LifftProjectEdit(AddLifftTask(self.key, LifftTask("new"), 2))
        )
        self.assertIsNone(present_lifft_results(self.result, self.session))
        self.session.undo()
        self.assertEqual(present_lifft_results(self.result, self.session), expected)
        for active in (
            None,
            DocumentSession(self.key, self.source),
            DocumentSession(DocumentKey("other", "lifft"), self.source),
        ):
            self.assertIsNone(present_lifft_results(self.result, active))
        with self.assertRaises(FrozenInstanceError):
            expected.rows[0].moment_text = "changed"

    def test_nonresults_other_models_and_metric_source_boundary(self) -> None:
        """No absent, invalid, failed or review-required outcome becomes zero risk.

        Args:
            None.

        Returns:
            None.
        """
        self.assertIsNone(present_lifft_results(None, self.session))
        for status in (
            EvaluationStatus.INVALID_INPUT,
            EvaluationStatus.REVIEW_REQUIRED,
            EvaluationStatus.CALCULATION_FAILED,
        ):
            self.assertIsNone(
                present_lifft_results(replace(self.result, status=status), self.session)
            )
        duet = DocumentSession(self.key, DuetDraft((DuetTask("a", 5, 100),)))
        self.assertIsNone(present_lifft_results(self.evaluator.evaluate(duet), duet))
        metric = DocumentSession(
            self.key, replace(self.source, system=MeasurementSystem.METRIC)
        )
        result = self.evaluator.evaluate(metric)
        display = present_lifft_results(result, metric)
        self.assertIsNotNone(display)
        self.assertEqual(display.system, MeasurementSystem.METRIC)
        self.assertIsNone(present_lifft_results(result, self.session))

    def test_malformed_complete_results_fail_without_partial_rows(self) -> None:
        """Reject missing/reordered/foreign outputs rather than matching by position.

        Args:
            None.

        Returns:
            None.
        """
        for result in (
            replace(self.result, summary=None),
            replace(
                self.result,
                summary=replace(self.result.summary, system=MeasurementSystem.METRIC),
            ),
            replace(self.result, task_results=self.result.task_results[:1]),
            replace(self.result, task_results=self.result.task_results[::-1]),
            replace(
                self.result,
                summary=replace(
                    self.result.summary,
                    contributions=self.result.summary.contributions[::-1],
                ),
            ),
            replace(
                self.result,
                task_results=(
                    replace(
                        self.result.task_results[0], system=MeasurementSystem.METRIC
                    ),
                    self.result.task_results[1],
                ),
            ),
            replace(
                self.result,
                task_results=(
                    DuetTaskResult("stable-a", 0.1),
                    self.result.task_results[1],
                ),
            ),
        ):
            with self.assertRaises(ValueError):
                present_lifft_results(result, self.session)
