"""Preserve categorical gauge colors and English wording from the current UI.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ergotools.domain.risk import RiskBand


@dataclass(frozen=True, slots=True)
class RiskAppearance:
    """Original categorical gauge appearance; translation remains a separate adapter.

    Attributes:
        color_hex: Original categorical RGB hex color.
        message_key: Stable localization key for the category.
        english_label: Original English fallback label, independent of saved user data.
        range_label: Original visual percentage range caption, preserving strict
            category boundaries.
    """

    color_hex: str
    message_key: str
    english_label: str
    range_label: str


# Immutable original low/moderate/moderate-high/high categorical colors and
# translation/range labels in gauge order.
RISK_APPEARANCES: Mapping[RiskBand, RiskAppearance] = MappingProxyType(
    {
        RiskBand.LOW: RiskAppearance("#19B83F", "risk.low", "Low Risk", "0 - 25%"),
        RiskBand.MODERATE: RiskAppearance(
            "#F5C400", "risk.moderate", "Moderate Risk", "> 25% - 37.5%"
        ),
        RiskBand.MODERATE_HIGH: RiskAppearance(
            "#FF8A19", "risk.moderate_high", "Moderate High Risk", "> 37.5% - 50%"
        ),
        RiskBand.HIGH: RiskAppearance("#FF3B30", "risk.high", "High Risk", "> 50%"),
    }
)
