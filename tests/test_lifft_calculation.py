"""Reference-runtime parity and explicit guards for the typed LiFFT task model.

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

from ergotools.domain.assessments.lifft import (
    calculate_lifft_task,
    probability_from_damage,
)
from ergotools.domain.assessments.lifft_data import DAMAGE_PER_CYCLE
from ergotools.domain.assessments.lifft_draft import DraftError, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.localization import Language, Translator


class LifftCalculationTests(unittest.TestCase):
    """Compare actual model outputs while keeping invalid-input differences explicit."""

    def test_all_frozen_task_outputs_match_the_reference(self) -> None:
        """Match 2,150 rounded moments, damages and exact colors in both systems.

        Args:
            None.

        Returns:
            None.
        """
        path = Path(__file__).parent / "fixtures" / "lifft_calculation_reference.json"
        fixture = json.loads(path.read_text())
        for record in fixture["records"]:
            with self.subTest(record=record):
                task = LifftTask(
                    "task", record["lever_arm"], record["load"], record["repetitions"]
                )
                result = calculate_lifft_task(task, MeasurementSystem(record["system"]))
                self.assertEqual(result.model_moment_ft_lbf, record["model_moment"])
                self.assertEqual(result.displayed_moment, record["display_moment"])
                self.assertEqual(result.cumulative_damage, record["damage"])
                self.assertEqual(
                    lifft_damage_color(result.cumulative_damage), record["color"]
                )
        self.assertEqual(
            DAMAGE_PER_CYCLE, tuple(float(v) for v in fixture["damage_table"])
        )

    def test_probability_and_color_edges_match_reference(self) -> None:
        """Compare positive-damage probability values and color threshold edges.

        Args:
            None.

        Returns:
            None.
        """
        path = Path(__file__).parent / "fixtures" / "lifft_calculation_reference.json"
        for record in json.loads(path.read_text())["probabilities"]:
            with self.subTest(record=record):
                self.assertTrue(
                    math.isclose(
                        probability_from_damage(record["damage"]),
                        record["probability"],
                        rel_tol=1e-14,
                        abs_tol=1e-15,
                    )
                )
                self.assertEqual(lifft_damage_color(record["damage"]), record["color"])

    def test_lookup_rounding_saturation_and_zero_are_preserved(self) -> None:
        """The table is indexed after one-decimal rounding, then capped at 200.

        Args:
            None.

        Returns:
            None.
        """
        for load, index in (
            (0, 0),
            (0.95, 0),
            (1, 1),
            (199.95, 199),
            (200, 200),
            (1000, 200),
        ):
            result = calculate_lifft_task(
                LifftTask("a", 12, load, 10000), MeasurementSystem.IMPERIAL
            )
            self.assertEqual(
                result.cumulative_damage, round(DAMAGE_PER_CYCLE[index] * 10000, 4)
            )

    def test_missing_and_negative_inputs_report_the_field(self) -> None:
        """Reject unsupported source values without an internal lookup error.

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
            ):
                values = dict(lever_arm=12, load=1, repetitions=1)
                values[field] = value
                with self.assertRaises(DraftError) as caught:
                    calculate_lifft_task(
                        LifftTask("a", **values), MeasurementSystem.IMPERIAL
                    )
                self.assertEqual(
                    (caught.exception.issue.code, caught.exception.issue.field),
                    (code, field),
                )

    def test_nonfinite_probability_and_color_inputs_are_rejected(self) -> None:
        """Never turn invalid probability/color inputs into plausible measurements.

        Args:
            None.

        Returns:
            None.
        """
        for damage in (math.nan, math.inf, -math.inf, -1):
            with self.assertRaises(ValueError):
                probability_from_damage(damage)
            with self.assertRaises(ValueError):
                lifft_damage_color(damage)
        with self.assertRaises(ValueError):
            probability_from_damage(0)
        self.assertEqual(lifft_damage_color(0), "#2eff00")

    def test_arithmetic_overflow_is_rejected(self) -> None:
        """Finite source values cannot produce infinite task output silently.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(DraftError) as caught:
            calculate_lifft_task(
                LifftTask("a", 1e308, 1e308, 1), MeasurementSystem.IMPERIAL
            )
        self.assertEqual(caught.exception.issue.field, "moment")
        with self.assertRaises(ValueError):
            calculate_lifft_task(
                LifftTask("a", 1e308, 100, 1), MeasurementSystem.METRIC
            )

    def test_result_is_immutable_and_source_is_not_rewritten(self) -> None:
        """Compute explicit result values without rewriting the source inputs.

        Args:
            None.

        Returns:
            None.
        """
        task = LifftTask("a", 30.48, 44.5, 100)
        result = calculate_lifft_task(task, MeasurementSystem.METRIC)
        self.assertEqual(task, LifftTask("a", 30.48, 44.5, 100))
        self.assertEqual(result.task_id, "a")
        self.assertEqual(result.system, MeasurementSystem.METRIC)
        with self.assertRaises(FrozenInstanceError):
            result.cumulative_damage = 0

    def test_new_validation_codes_have_both_translations(self) -> None:
        """Every added calculation guard exposes a presentable stable message key.

        Args:
            None.

        Returns:
            None.
        """
        for language in Language:
            for key in (
                "validation.number",
                "validation.nonnegative",
                "validation.overflow",
            ):
                self.assertTrue(Translator(language).text(key))
