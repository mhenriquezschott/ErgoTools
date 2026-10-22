"""Actual TST assessment-method parity, including the legacy selector-index swap.

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

from ergotools.domain.assessments.tst import (
    TstDirection,
    TstTask,
    TstTaskResult,
    calculate_tst_task,
)
from ergotools.domain.assessments.tst_summary import summarize_tst_tasks
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.theme.tst_summary import (
    display_tst_summary,
    tst_direction_for_selection,
)

# Explicit imperial source enum used by independent result-boundary fixtures.
IMPERIAL = MeasurementSystem.IMPERIAL


def task_result(identity: str, damage: float) -> TstTaskResult:
    """Create a result-boundary value for validation/summation edge cases.

    Args:
        identity: Exact saved worker/task/scheme identity or deliberately malformed
            boundary value.
        damage: Dimensionless damage boundary input (or deliberate invalid text) for the
            stated scenario.

    Returns:
        Synthetic ST task result with exact identity/damage for independent aggregation
        boundary tests.
    """
    return TstTaskResult(identity, IMPERIAL, 0, 0, damage)


class TstSummaryTests(unittest.TestCase):
    """Separate reference UI mapping from direct model direction identities."""

    def test_all_actual_method_summary_cases_match(self) -> None:
        """Compare 70 exact moment/damage/share/text/color groups in both systems.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/tst_summary_reference.json").read_text()
        )
        for record in fixture["records"]:
            with self.subTest(record=record):
                system = MeasurementSystem(record["system"])
                tasks = tuple(
                    calculate_tst_task(
                        TstTask(str(i), tst_direction_for_selection(row[0]), *row[1:]),
                        system,
                    )
                    for i, row in enumerate(record["inputs"])
                )
                summary = summarize_tst_tasks(tasks, system)
                display = display_tst_summary(summary)
                self.assertEqual(summary.total_damage, record["total"])
                self.assertEqual(
                    [c.percentage for c in summary.contributions],
                    record["contributions"],
                )
                self.assertEqual(display.damage_text, record["damage_text"])
                self.assertEqual(display.probability_text, record["probability_text"])
                self.assertEqual(display.color, record["color"])
                self.assertEqual(
                    list(display.task_moment_texts), record["task_moment_text"]
                )
                self.assertEqual(
                    list(display.task_damage_texts), record["task_damage_text"]
                )
                self.assertEqual(list(display.task_colors), record["task_colors"])

    def test_selector_swap_is_explicit_and_invalid_indices_are_rejected(self) -> None:
        """Never silently reinterpret the reference's downward/horizontal index swap.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(
            [tst_direction_for_selection(i) for i in range(3)],
            [
                TstDirection.HANDLING_LOADS,
                TstDirection.HORIZONTAL,
                TstDirection.DOWNWARD,
            ],
        )
        for index in (-1, 3, True, 1.0, "1", None):
            with self.assertRaises(ValueError):
                tst_direction_for_selection(index)
        direct = calculate_tst_task(
            TstTask("a", TstDirection.DOWNWARD, 12, 0, 100), IMPERIAL
        )
        selected = calculate_tst_task(
            TstTask("a", tst_direction_for_selection(1), 12, 0, 100), IMPERIAL
        )
        self.assertEqual(direct.model_moment_ft_lbf, 0)
        self.assertGreater(selected.model_moment_ft_lbf, 0)

    def test_zero_empty_and_small_positive_totals_remain_distinct(self) -> None:
        """Clear zero colors and retain positive precision for probability.

        Args:
            None.

        Returns:
            None.
        """
        positive = display_tst_summary(
            summarize_tst_tasks((task_result("a", 1),), IMPERIAL)
        )
        self.assertIsNotNone(positive.color)
        for tasks in ((), (task_result("a", 0),)):
            summary = summarize_tst_tasks(tasks, IMPERIAL)
            display = display_tst_summary(summary)
            self.assertIsNone(summary.probability)
            self.assertIsNone(display.color)
            self.assertEqual(display.damage_text, "0.0")
            self.assertEqual(display.probability_text, "0.0")
            self.assertEqual(display.task_colors, tuple(None for _ in tasks))
            self.assertEqual(display.contribution_texts, tuple("0.0" for _ in tasks))
        small = summarize_tst_tasks((task_result("a", 0.00001),), IMPERIAL)
        self.assertIsNotNone(small.probability)
        self.assertEqual(display_tst_summary(small).damage_text, "0.0000")
        self.assertEqual(display_tst_summary(small).task_damage_texts, ("0.00001",))

    def test_wrong_units_and_invalid_results_are_rejected(self) -> None:
        """Keep unit ownership and shared ID/damage/overflow validation explicit.

        Args:
            None.

        Returns:
            None.
        """
        for tasks, system in (
            ((task_result("a", 1),), MeasurementSystem.METRIC),
            ((), "imperial"),
            ((task_result(" ", 1),), IMPERIAL),
            ((task_result("a", 1), task_result("a", 1)), IMPERIAL),
            ((task_result("a", -1),), IMPERIAL),
            ((task_result("a", math.inf),), IMPERIAL),
            ((task_result("a", True),), IMPERIAL),
            ((task_result("a", 1e308), task_result("b", 1e308)), IMPERIAL),
        ):
            with self.assertRaises(DraftError):
                summarize_tst_tasks(tasks, system)

    def test_summation_order_rounding_and_immutable_results(self) -> None:
        """Preserve += totals and rounded shares without redistributing residuals.

        Args:
            None.

        Returns:
            None.
        """
        ordered = summarize_tst_tasks(
            tuple(task_result(str(i), d) for i, d in enumerate((1e16, 1, 1))), IMPERIAL
        )
        self.assertEqual(ordered.total_damage, 1e16)
        equal = summarize_tst_tasks(
            tuple(task_result(str(i), 1) for i in range(3)), IMPERIAL
        )
        self.assertEqual([c.percentage for c in equal.contributions], [33.3] * 3)
        with self.assertRaises(FrozenInstanceError):
            equal.total_damage = 0
        with self.assertRaises(FrozenInstanceError):
            display_tst_summary(equal).color = "red"
