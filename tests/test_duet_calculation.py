"""Frozen DUET reference cases and explicit typed input-boundary behavior.

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
    calculate_duet_task,
    probability_from_damage,
)
from ergotools.domain.assessments.duet_data import DAMAGE_PER_CYCLE
from ergotools.domain.assessments.validation import DraftError
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.localization import Language, Translator


class DuetCalculationTests(unittest.TestCase):
    """Preserve selector-driven model outputs while rejecting invalid API inputs."""

    def test_frozen_task_outputs_and_lookup_match_reference(self) -> None:
        """Match all 198 five-decimal damages and exact task colors.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (
                Path(__file__).parent / "fixtures/duet_calculation_reference.json"
            ).read_text()
        )
        self.assertEqual(DAMAGE_PER_CYCLE, tuple(fixture["damage_table"]))
        for record in fixture["records"]:
            with self.subTest(record=record):
                result = calculate_duet_task(
                    DuetTask("a", record["scale"], record["repetitions"])
                )
                self.assertEqual(result.cumulative_damage, record["damage"])
                self.assertEqual(
                    duet_damage_color(result.cumulative_damage), record["color"]
                )

    def test_probability_and_palette_boundaries_match_reference(self) -> None:
        """Cover adjacent floats around both color thresholds and extreme damages.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (
                Path(__file__).parent / "fixtures/duet_calculation_reference.json"
            ).read_text()
        )
        for record in fixture["probabilities"]:
            self.assertTrue(
                math.isclose(
                    probability_from_damage(record["damage"]),
                    record["probability"],
                    rel_tol=1e-14,
                    abs_tol=1e-15,
                )
            )
            self.assertEqual(duet_damage_color(record["damage"]), record["color"])

    def test_scale_is_an_explicit_integer_selector(self) -> None:
        """Do not truncate fractions, accept booleans or use negative indexing.

        Args:
            None.

        Returns:
            None.
        """
        for scale in (-1, 11, 1.9, 10.9, 1.0, True, math.inf, math.nan, "1"):
            with self.assertRaises(DraftError) as caught:
                calculate_duet_task(DuetTask("a", scale, 100))
            self.assertEqual(caught.exception.issue.code, "validation.omni_scale")
            self.assertEqual(caught.exception.issue.field, "omni_res_scale")
            self.assertEqual(caught.exception.issue.task_id, "a")

    def test_missing_and_invalid_repetitions_report_precise_issues(self) -> None:
        """Distinguish unfinished tasks from zero repetitions or invalid numbers.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(DraftError) as caught:
            calculate_duet_task(DuetTask("a", None, 0))
        self.assertEqual(caught.exception.issue.field, "omni_res_scale")
        self.assertEqual(caught.exception.issue.code, "validation.required")
        for value, code in (
            (None, "validation.required"),
            (-1, "validation.nonnegative"),
            (True, "validation.number"),
            (math.nan, "validation.nonfinite"),
            (math.inf, "validation.nonfinite"),
        ):
            with self.assertRaises(DraftError) as caught:
                calculate_duet_task(DuetTask("a", 0, value))
            self.assertEqual(caught.exception.issue.code, code)
            self.assertEqual(caught.exception.issue.field, "repetitions")

    def test_zero_scale_is_not_zero_damage_and_fractional_repetitions_remain(
        self,
    ) -> None:
        """Scale zero has nonzero damage per cycle; zero repetitions null damage.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(
            calculate_duet_task(DuetTask("a", 0, 10000)).cumulative_damage, 0.0026
        )
        self.assertEqual(
            calculate_duet_task(DuetTask("a", 10, 0.5)).cumulative_damage, 0.00485
        )
        self.assertEqual(calculate_duet_task(DuetTask("a", 10, 0)).cumulative_damage, 0)
        self.assertEqual(duet_damage_color(0), "#2aff00")

    def test_nonpositive_probability_and_invalid_color_inputs_fail(self) -> None:
        """Never evaluate a logarithm at zero or publish nonfinite color output.

        Args:
            None.

        Returns:
            None.
        """
        for damage in (0, -1, math.inf, -math.inf, math.nan):
            with self.assertRaises(ValueError):
                probability_from_damage(damage)
        for damage in (-1, math.inf, -math.inf, math.nan):
            with self.assertRaises(ValueError):
                duet_damage_color(damage)

    def test_source_and_result_identity_are_immutable(self) -> None:
        """Preserve source values and task identity without side effects.

        Args:
            None.

        Returns:
            None.
        """
        task = DuetTask("a", 5, 100)
        result = calculate_duet_task(task)
        self.assertEqual(result.task_id, task.task_id)
        with self.assertRaises(FrozenInstanceError):
            task.repetitions = 1
        with self.assertRaises(FrozenInstanceError):
            result.cumulative_damage = 1
        with self.assertRaises(DraftError):
            DuetTask(" ", 5, 100)

    def test_scale_issue_has_both_translations(self) -> None:
        """Expose the new scale guard through both existing language catalogs.

        Args:
            None.

        Returns:
            None.
        """
        for language in Language:
            self.assertTrue(Translator(language).text("validation.omni_scale"))
