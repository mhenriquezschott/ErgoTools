"""Actual-method DUET parity and shared aggregation regression boundaries.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import math
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from ergotools.domain.assessments.duet import (
    DuetTask,
    DuetTaskResult,
    calculate_duet_task,
)
from ergotools.domain.assessments.duet_summary import summarize_duet_tasks
from ergotools.domain.assessments.validation import DraftError
from ergotools.presentation.desktop.theme.assessment_probability import (
    format_assessment_probability,
)
from ergotools.presentation.desktop.theme.duet_summary import display_duet_summary


class DuetSummaryTests(unittest.TestCase):
    """Keep DUET probability/palette separate while sharing total/share arithmetic."""

    def test_actual_reference_method_outputs_match(self) -> None:
        """Match all 63 captured summaries, including row and total precision.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/duet_summary_reference.json").read_text()
        )
        for record in fixture["records"]:
            with self.subTest(record=record):
                tasks = tuple(
                    calculate_duet_task(DuetTask(str(i), *inputs))
                    for i, inputs in enumerate(record["inputs"])
                )
                summary = summarize_duet_tasks(tasks)
                display = display_duet_summary(summary)
                self.assertEqual(summary.total_damage, record["total"])
                self.assertEqual(
                    [c.percentage for c in summary.contributions],
                    record["contributions"],
                )
                self.assertEqual(display.damage_text, record["damage_text"])
                self.assertEqual(display.probability_text, record["probability_text"])
                self.assertEqual(display.color, record["color"])
                self.assertEqual(list(display.task_colors), record["task_colors"])
                self.assertEqual(
                    list(display.task_damage_texts), record["task_damage_text"]
                )

    def test_zero_and_empty_summaries_clear_display_state(self) -> None:
        """Replacing a positive result supplies explicit zero shares/cleared colors.

        Args:
            None.

        Returns:
            None.
        """
        prior = display_duet_summary(summarize_duet_tasks((DuetTaskResult("a", 1),)))
        self.assertIsNotNone(prior.color)
        for tasks in ((), (DuetTaskResult("a", 0),)):
            summary = summarize_duet_tasks(tasks)
            display = display_duet_summary(summary)
            self.assertIsNone(summary.probability)
            self.assertIsNone(display.color)
            self.assertEqual(display.damage_text, "0.0")
            self.assertEqual(display.probability_text, "0.0")
            self.assertEqual(display.task_colors, tuple(None for _ in tasks))
            self.assertEqual(display.contribution_texts, tuple("0.0" for _ in tasks))

    def test_damage_precision_is_not_lost_before_aggregation(self) -> None:
        """A total label may round to zero while the model still evaluates damage.

        Args:
            None.

        Returns:
            None.
        """
        summary = summarize_duet_tasks((DuetTaskResult("a", 0.00001),))
        display = display_duet_summary(summary)
        self.assertEqual(summary.total_damage, 0.00001)
        self.assertIsNotNone(summary.probability)
        self.assertEqual(display.damage_text, "0.0000")
        self.assertEqual(display.task_damage_texts, ("0.00001",))
        self.assertNotEqual(display.probability_text, "0.0")

    def test_row_order_and_rounded_contributions_are_preserved(self) -> None:
        """Do not compensate summation or distribute percentage rounding residuals.

        Args:
            None.

        Returns:
            None.
        """
        ordered = summarize_duet_tasks(
            tuple(DuetTaskResult(str(i), d) for i, d in enumerate((1e16, 1, 1)))
        )
        self.assertEqual(ordered.total_damage, 1e16)
        self.assertNotEqual(ordered.total_damage, math.fsum((1e16, 1, 1)))
        equal = summarize_duet_tasks(tuple(DuetTaskResult(str(i), 1) for i in range(3)))
        self.assertEqual([c.percentage for c in equal.contributions], [33.3] * 3)

    def test_invalid_results_cannot_produce_partial_summaries(self) -> None:
        """Reject invalid IDs, damage and total overflow at the result boundary.

        Args:
            None.

        Returns:
            None.
        """
        cases = (
            ((DuetTaskResult(" ", 1),), "validation.required"),
            ((DuetTaskResult("a", 1), DuetTaskResult("a", 2)), "validation.duplicate"),
            ((DuetTaskResult("a", -1),), "validation.nonnegative"),
            ((DuetTaskResult("a", True),), "validation.number"),
            ((DuetTaskResult("a", math.inf),), "validation.nonfinite"),
            ((DuetTaskResult("a", math.nan),), "validation.nonfinite"),
            (
                (DuetTaskResult("a", 1e308), DuetTaskResult("b", 1e308)),
                "validation.overflow",
            ),
        )
        for tasks, code in cases:
            with self.assertRaises(DraftError) as caught:
                summarize_duet_tasks(tasks)
            self.assertEqual(caught.exception.issue.code, code)

    def test_display_bounds_and_immutability(self) -> None:
        """Keep round-before-bound policy and immutable model/display snapshots.

        Args:
            None.

        Returns:
            None.
        """
        for probability, expected in (
            (None, "0.0"),
            (0.0494, "< 5"),
            (0.0496, "5.0"),
            (0.9004, "90.0"),
            (0.9006, "> 90"),
        ):
            self.assertEqual(format_assessment_probability(probability), expected)
        summary = summarize_duet_tasks((DuetTaskResult("a", 1),))
        with self.assertRaises(FrozenInstanceError):
            summary.total_damage = 0
        with self.assertRaises(FrozenInstanceError):
            summary.contributions[0].percentage = 0
        with self.assertRaises(FrozenInstanceError):
            display_duet_summary(summary).color = "red"
