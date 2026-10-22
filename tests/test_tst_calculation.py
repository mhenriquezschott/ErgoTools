"""TST reference parity at arm/direction boundaries and explicit numeric guards.

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
    calculate_tst_task,
    probability_from_damage,
)
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color
from ergotools.presentation.desktop.theme.upper_limb_colors import UPPER_LIMB_COLORS
from ergotools.presentation.localization import Language, Translator


class TstCalculationTests(unittest.TestCase):
    """Preserve unrounded model moments, five-place damage and exact display colors."""

    def test_all_frozen_task_cases_match_reference(self) -> None:
        """Match 1,650 task outputs across both systems and all three directions.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (
                Path(__file__).parent / "fixtures/tst_calculation_reference.json"
            ).read_text()
        )
        for r in fixture["records"]:
            with self.subTest(record=r):
                result = calculate_tst_task(
                    TstTask(
                        "a",
                        TstDirection(r["direction"]),
                        r["lever_arm"],
                        r["load"],
                        r["repetitions"],
                    ),
                    MeasurementSystem(r["system"]),
                )
                self.assertEqual(result.model_moment_ft_lbf, r["model_moment"])
                self.assertEqual(result.displayed_moment, r["display_moment"])
                self.assertEqual(result.cumulative_damage, r["damage"])
                self.assertEqual(tst_damage_color(result.cumulative_damage), r["color"])
        self.assertEqual(UPPER_LIMB_COLORS, tuple(fixture["color_table"]))

    def test_probability_and_color_thresholds_match_reference(self) -> None:
        """Preserve risk arithmetic and adjacent-float threshold colors.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (
                Path(__file__).parent / "fixtures/tst_calculation_reference.json"
            ).read_text()
        )
        for r in fixture["probabilities"]:
            self.assertTrue(
                math.isclose(
                    probability_from_damage(r["damage"]),
                    r["probability"],
                    rel_tol=1e-14,
                    abs_tol=1e-15,
                )
            )
            self.assertEqual(tst_damage_color(r["damage"]), r["color"])

    def test_damage_uses_unrounded_model_moment(self) -> None:
        """Display rounding must not feed back into the fatigue calculation.

        Args:
            None.

        Returns:
            None.
        """
        result = calculate_tst_task(
            TstTask("a", TstDirection.HANDLING_LOADS, 12, 10, 1e8),
            MeasurementSystem.IMPERIAL,
        )
        self.assertNotEqual(result.model_moment_ft_lbf, result.displayed_moment)
        incorrectly_rounded = round(
            (
                1.0
                / (
                    10
                    ** ((101.25 - 100 * (result.displayed_moment * 12 / 681)) / 14.83)
                )
            )
            * 1e8,
            5,
        )
        self.assertNotEqual(result.cumulative_damage, incorrectly_rounded)

    def test_direction_is_explicit_and_missing_is_not_handling_loads(self) -> None:
        """Reject raw or unsupported direction selectors explicitly.

        Args:
            None.

        Returns:
            None.
        """
        for direction, code in (
            (None, "validation.required"),
            ("0", "validation.tst_direction"),
            ("3", "validation.tst_direction"),
            (0, "validation.tst_direction"),
            (True, "validation.tst_direction"),
        ):
            with self.assertRaises(DraftError) as caught:
                calculate_tst_task(
                    TstTask("a", direction, 12, 10, 100), MeasurementSystem.IMPERIAL
                )
            self.assertEqual(caught.exception.issue.code, code)
            self.assertEqual(caught.exception.issue.field, "direction")

    def test_missing_negative_boolean_and_nonfinite_numeric_inputs(self) -> None:
        """All numeric fields retain task/field-specific issue context.

        Args:
            None.

        Returns:
            None.
        """
        for field in ("lever_arm", "load", "repetitions"):
            for value, code in (
                (None, "validation.required"),
                (-1, "validation.nonnegative"),
                (True, "validation.number"),
                (math.inf, "validation.nonfinite"),
                (math.nan, "validation.nonfinite"),
            ):
                values = dict(lever_arm=12, load=10, repetitions=100)
                values[field] = value
                with self.assertRaises(DraftError) as caught:
                    calculate_tst_task(
                        TstTask("a", TstDirection.HORIZONTAL, **values),
                        MeasurementSystem.IMPERIAL,
                    )
                self.assertEqual(
                    (
                        caught.exception.issue.code,
                        caught.exception.issue.field,
                        caught.exception.issue.task_id,
                    ),
                    (code, field, "a"),
                )

    def test_overflow_and_zero_denominator_become_structured_errors(self) -> None:
        """Reject nonfinite moments/damage and exponential denominator underflow.

        Args:
            None.

        Returns:
            None.
        """
        for arm, load, rep, field in (
            (1e308, 1e308, 1, "moment"),
            (12, 10000, 1, "damage"),
            (12, 100, 1e308, "damage"),
            (12, 10000, 0, "damage"),
        ):
            with self.assertRaises(DraftError) as caught:
                calculate_tst_task(
                    TstTask("a", TstDirection.HANDLING_LOADS, arm, load, rep),
                    MeasurementSystem.IMPERIAL,
                )
            self.assertEqual(caught.exception.issue.code, "validation.overflow")
            self.assertEqual(caught.exception.issue.field, field)

    def test_zero_repetitions_and_horizontal_absolute_moment(self) -> None:
        """Preserve complete zeros and direction-specific arm contribution.

        Args:
            None.

        Returns:
            None.
        """
        zero = calculate_tst_task(
            TstTask("a", TstDirection.HANDLING_LOADS, 12, 10, 0),
            MeasurementSystem.IMPERIAL,
        )
        self.assertEqual(zero.cumulative_damage, 0)
        horizontal = calculate_tst_task(
            TstTask("a", TstDirection.HORIZONTAL, 12, 0, 100),
            MeasurementSystem.IMPERIAL,
        )
        self.assertGreater(horizontal.model_moment_ft_lbf, 0)
        downward = calculate_tst_task(
            TstTask("a", TstDirection.DOWNWARD, 12, 0, 100), MeasurementSystem.IMPERIAL
        )
        self.assertEqual(downward.model_moment_ft_lbf, 0)
        self.assertEqual(tst_damage_color(0), "#2aff00")

    def test_invalid_probability_color_units_and_immutable_identity(self) -> None:
        """No nonfinite display values, silent unit fallback or source mutation.

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
                tst_damage_color(damage)
        task = TstTask("a", TstDirection.DOWNWARD, 12, 10, 100)
        with self.assertRaises(ValueError):
            calculate_tst_task(task, "unknown")
        result = calculate_tst_task(task, MeasurementSystem.IMPERIAL)
        with self.assertRaises(FrozenInstanceError):
            task.load = 20
        with self.assertRaises(FrozenInstanceError):
            result.cumulative_damage = 0
        self.assertEqual(result.task_id, "a")
        with self.assertRaises(DraftError):
            TstTask(" ")
        for language in Language:
            self.assertTrue(Translator(language).text("validation.tst_direction"))
