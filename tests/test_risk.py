"""Characterize categorical risk boundaries without importing the old application.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import math
import unittest
from pathlib import Path

from ergotools.domain.risk import RiskBand, classify_probability
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES


class RiskClassificationTests(unittest.TestCase):
    """Protect threshold edges and the frozen old-application display contract."""

    def test_reference_vectors_and_appearance(self) -> None:
        """Match reference results for frozen boundary and representative cases.

        Args:
            None.

        Returns:
            None.
        """
        fixture = Path(__file__).parent / "fixtures" / "risk_reference.json"
        records = json.loads(fixture.read_text(encoding="utf-8"))["records"]
        for record in records:
            with self.subTest(probability_percent=record["probability_percent"]):
                band = classify_probability(record["probability_percent"])
                appearance = RISK_APPEARANCES[band]
                self.assertEqual(appearance.english_label, record["label"])
                self.assertEqual(appearance.color_hex, record["color"])
                self.assertEqual(appearance.range_label, record["range"])

    def test_invalid_results_are_never_classified_as_measurements(self) -> None:
        """NaN and infinities must be rejected at the new typed API boundary.

        Args:
            None.

        Returns:
            None.
        """
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                classify_probability(value)

    def test_band_identifiers_are_independent_of_display_text(self) -> None:
        """Changing language must not change category identity or persisted keys.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(classify_probability(25.0).value, "low")
        self.assertEqual(
            classify_probability(math.nextafter(25.0, math.inf)), RiskBand.MODERATE
        )
        self.assertEqual(set(RISK_APPEARANCES), set(RiskBand))
