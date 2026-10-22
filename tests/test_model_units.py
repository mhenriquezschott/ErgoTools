"""Protect reference conversion semantics without importing the old code.

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

from ergotools.domain.model_units import (
    MeasurementSystem,
    ModelLoad,
    model_moment_for_display,
    normalize_model_load,
)


class ModelUnitTests(unittest.TestCase):
    """Check model normalization, display stages and invalid boundary handling."""

    def test_reference_model_vectors(self) -> None:
        """Compare 48 captured LiFFT/Shoulder cases from reference Python 3.10.

        Args:
            None.

        Returns:
            None.
        """
        path = Path(__file__).parent / "fixtures" / "model_units_reference.json"
        for record in json.loads(path.read_text())["records"]:
            with self.subTest(record=record):
                system = MeasurementSystem(record["system"])
                actual = normalize_model_load(
                    record["lever_arm"], record["load"], system
                )
                self.assertEqual(actual.lever_arm_in, record["lever_arm_in"])
                self.assertEqual(actual.load_lbf, record["load_lbf"])
                self.assertEqual(
                    model_moment_for_display(record["model_moment_ft_lbf"], system),
                    record["display_moment"],
                )

    def test_force_is_not_body_mass(self) -> None:
        """Preserve 4.45 N per model lbf, with no kilogram interpretation.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(
            normalize_model_load(2.54, 4.45, MeasurementSystem.METRIC), ModelLoad(1, 1)
        )

    def test_normalization_retains_precision_and_signed_values(self) -> None:
        """Leave rounding and physical sign validation to the assessment layer.

        Args:
            None.

        Returns:
            None.
        """
        actual = normalize_model_load(-0.001, 0.001, MeasurementSystem.METRIC)
        self.assertEqual(actual.lever_arm_in, -0.001 / 2.54)
        self.assertEqual(actual.load_lbf, 0.001 / 4.45)
        with self.assertRaises(FrozenInstanceError):
            actual.load_lbf = 0

    def test_nonfinite_quantities_are_rejected(self) -> None:
        """Reject each nonfinite field before it can become a valid model result.

        Args:
            None.

        Returns:
            None.
        """
        for value in (math.nan, math.inf, -math.inf):
            for system in MeasurementSystem:
                with self.subTest(value=value, system=system):
                    with self.assertRaises(ValueError):
                        normalize_model_load(value, 1, system)
                    with self.assertRaises(ValueError):
                        normalize_model_load(1, value, system)
                    with self.assertRaises(ValueError):
                        model_moment_for_display(value, system)
            with self.assertRaises(ValueError):
                ModelLoad(1, value)

    def test_display_overflow_is_rejected(self) -> None:
        """A finite input must not overflow into an infinite displayed result.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(ValueError):
            model_moment_for_display(1e308, MeasurementSystem.METRIC)

    def test_unknown_system_never_defaults_to_imperial(self) -> None:
        """Reject malformed external values at runtime as well as in typed code.

        Args:
            None.

        Returns:
            None.
        """
        for function, args in (
            (normalize_model_load, (1, 1, "unknown")),
            (model_moment_for_display, (1, "unknown")),
        ):
            with self.subTest(function=function), self.assertRaises(ValueError):
                function(*args)

    def test_python_tie_rounding_is_preserved(self) -> None:
        """Retain one-decimal ties-to-even behavior at the display boundary.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(
            model_moment_for_display(1.25, MeasurementSystem.IMPERIAL), 1.2
        )
        self.assertEqual(
            model_moment_for_display(1.75, MeasurementSystem.IMPERIAL), 1.8
        )
