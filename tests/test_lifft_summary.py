"""Reference assessment aggregation and failure boundaries without GUI dependencies.

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

from ergotools.domain.assessments.lifft import LifftTaskResult, calculate_lifft_task
from ergotools.domain.assessments.lifft_draft import DraftError, LifftTask
from ergotools.domain.assessments.lifft_summary import summarize_lifft_tasks
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.theme.lifft_summary import (
    display_lifft_summary,
    format_lifft_probability,
)

# Explicit imperial source enum used by independent result-boundary fixtures.
IMPERIAL = MeasurementSystem.IMPERIAL


def result(task_id: str, damage: float) -> LifftTaskResult:
    """Make a calculated-result boundary value without coupling to lookup inputs.

    Args:
        task_id: Stable synthetic task identity, independent of the displayed row
            number.
        damage: Dimensionless damage boundary input (or deliberate invalid text) for the
            stated scenario.

    Returns:
        Synthetic LiFFT task result with the requested identity/damage for independent
        aggregation boundary tests.
    """
    return LifftTaskResult(task_id, IMPERIAL, 0, 0, damage)


class LifftSummaryTests(unittest.TestCase):
    """Preserve totals, shares and display rules with explicit absence and errors."""

    def test_actual_reference_assessment_outputs(self) -> None:
        """Compare sixty captures from the actual original assessment method.

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
        for record in fixture["records"]:
            with self.subTest(record=record):
                system = MeasurementSystem(record["system"])
                tasks = tuple(
                    calculate_lifft_task(LifftTask(str(i), *inputs), system)
                    for i, inputs in enumerate(record["inputs"])
                )
                summary = summarize_lifft_tasks(tasks, system)
                display = display_lifft_summary(summary)
                self.assertEqual(summary.total_damage, record["total"])
                self.assertEqual(
                    [c.percentage for c in summary.contributions],
                    record["contributions"],
                )
                self.assertEqual(display.probability_text, record["probability_text"])
                self.assertEqual(display.damage_text, record["damage_text"])
                self.assertEqual(display.color, record["color"])
                self.assertEqual(list(display.task_colors), record["task_colors"])

    def test_zero_result_clears_previously_populated_display_state(self) -> None:
        """Fresh display values explicitly replace old colors and percentages.

        Args:
            None.

        Returns:
            None.
        """
        previous = display_lifft_summary(
            summarize_lifft_tasks((result("a", 1),), IMPERIAL)
        )
        self.assertIsNotNone(previous.color)
        summary = summarize_lifft_tasks((result("a", 0),), IMPERIAL)
        current = display_lifft_summary(summary)
        self.assertIsNone(summary.probability)
        self.assertIsNone(current.color)
        self.assertEqual(current.task_colors, (None,))
        self.assertEqual(current.contribution_texts, ("0.0",))
        self.assertEqual(current.probability_text, "0.0")
        empty = summarize_lifft_tasks((), IMPERIAL)
        self.assertEqual(empty.contributions, ())
        self.assertIsNone(empty.probability)

    def test_rounded_contributions_need_not_sum_to_one_hundred(self) -> None:
        """Do not silently redistribute rounding residuals or reweight tasks.

        Args:
            None.

        Returns:
            None.
        """
        summary = summarize_lifft_tasks(
            tuple(result(str(i), 1) for i in range(3)), IMPERIAL
        )
        self.assertEqual([c.percentage for c in summary.contributions], [33.3] * 3)

    def test_row_order_addition_is_preserved(self) -> None:
        """Keep legacy += behavior across Python's newer sum implementation.

        Args:
            None.

        Returns:
            None.
        """
        tasks = (result("a", 1e16), result("b", 1), result("c", 1))
        summary = summarize_lifft_tasks(tasks, IMPERIAL)
        self.assertEqual(summary.total_damage, 1e16)
        self.assertNotEqual(summary.total_damage, math.fsum((1e16, 1, 1)))

    def test_probability_display_rounds_before_clamping(self) -> None:
        """Only rounded values strictly outside the display limits use bounds.

        Args:
            None.

        Returns:
            None.
        """
        for value, expected in (
            (None, "0.0"),
            (0, "< 5"),
            (0.0494, "< 5"),
            (0.0496, "5.0"),
            (0.05, "5.0"),
            (0.9, "90.0"),
            (0.9004, "90.0"),
            (0.9006, "> 90"),
            (1, "> 90"),
        ):
            self.assertEqual(format_lifft_probability(value), expected)
        for value in (math.nan, math.inf, -0.01, 1.01):
            with self.assertRaises(ValueError):
                format_lifft_probability(value)

    def test_invalid_damage_and_total_overflow_are_rejected(self) -> None:
        """Never publish a summary with negative/nonfinite damage or total.

        Args:
            None.

        Returns:
            None.
        """
        for damage, code in (
            (-1, "validation.nonnegative"),
            (True, "validation.number"),
            (math.nan, "validation.nonfinite"),
            (math.inf, "validation.nonfinite"),
        ):
            with self.assertRaises(DraftError) as caught:
                summarize_lifft_tasks((result("a", damage),), IMPERIAL)
            self.assertEqual(caught.exception.issue.code, code)
            self.assertEqual(caught.exception.issue.task_id, "a")
        with self.assertRaises(DraftError) as caught:
            summarize_lifft_tasks((result("a", 1e308), result("b", 1e308)), IMPERIAL)
        self.assertEqual(caught.exception.issue.field, "total_damage")

    def test_identity_and_unit_mismatches_are_rejected(self) -> None:
        """Only uniquely identified results from the same unit system aggregate.

        Args:
            None.

        Returns:
            None.
        """
        for tasks, system, code in (
            ((result(" ", 1),), IMPERIAL, "validation.required"),
            ((result("a", 1), result("a", 2)), IMPERIAL, "validation.duplicate"),
            ((result("a", 1),), MeasurementSystem.METRIC, "validation.unit"),
            ((), "imperial", "validation.unit"),
        ):
            with self.assertRaises(DraftError) as caught:
                summarize_lifft_tasks(tasks, system)
            self.assertEqual(caught.exception.issue.code, code)

    def test_result_and_display_are_immutable(self) -> None:
        """Returned snapshots cannot be altered by their consumers.

        Args:
            None.

        Returns:
            None.
        """
        summary = summarize_lifft_tasks((result("a", 1),), IMPERIAL)
        with self.assertRaises(FrozenInstanceError):
            summary.total_damage = 2
        with self.assertRaises(FrozenInstanceError):
            summary.contributions[0].percentage = 5
        with self.assertRaises(FrozenInstanceError):
            display_lifft_summary(summary).color = "red"
