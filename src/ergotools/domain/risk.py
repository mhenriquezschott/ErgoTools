"""Classify outcome percentages using the existing ErgoTools gauge thresholds.

This is a presentation-category policy, not a scientific probability model. It does not
replace tool-specific continuous colors or calculate damage.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from enum import StrEnum


class RiskBand(StrEnum):
    """Stable, language-independent identifiers for existing outcome categories."""

    # At most 25 percent, inclusive.
    LOW = "low"
    # Above 25 through 37.5 percent, inclusive upper boundary.
    MODERATE = "moderate"
    # Above 37.5 through 50 percent, inclusive upper boundary.
    MODERATE_HIGH = "moderate_high"
    # Above 50 percent, including finite out-of-range high values.
    HIGH = "high"


def classify_probability(probability_percent: float) -> RiskBand:
    """Classify a finite outcome percentage with inclusive upper boundaries.

    Args:
        probability_percent: Outcome probability in percentage points, not 0-1. Finite
            values outside 0-100 are classified as the nearest endpoint, matching the
            working application's threshold behavior.

    Returns:
        The existing category: low through 25, moderate through 37.5, moderate-high
        through 50, otherwise high.

    Raises:
        ValueError: If the value is NaN or infinite. Missing results must be represented
            separately, never converted to a low-risk measurement.
    """
    if not math.isfinite(probability_percent):
        raise ValueError("Outcome probability must be finite.")
    if probability_percent <= 25.0:
        return RiskBand.LOW
    if probability_percent <= 37.5:
        return RiskBand.MODERATE
    if probability_percent <= 50.0:
        return RiskBand.MODERATE_HIGH
    return RiskBand.HIGH
