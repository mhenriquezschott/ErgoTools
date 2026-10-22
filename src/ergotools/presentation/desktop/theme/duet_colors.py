"""Reference DUET continuous palette and model-specific damage thresholds.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

import math

from ergotools.domain.assessments.duet import probability_from_damage
from ergotools.presentation.desktop.theme.upper_limb_colors import UPPER_LIMB_COLORS


def duet_damage_color(damage: float) -> str:
    """Map finite nonnegative damage to unchanged reference colors.

    This is a task/model display mapping, not a zero-total assessment policy.

    Args:
        damage: Finite nonnegative dimensionless cumulative damage; no source value is
            modified.

    Returns:
        Exact original continuous-palette color at the model's truncated percent index,
        with original low/high damage endpoint thresholds.

    Raises:
        ValueError: Damage is negative or nonfinite.
    """
    if not math.isfinite(damage) or damage < 0:
        raise ValueError("Damage must be finite and nonnegative.")
    if damage < 0.00002:
        return UPPER_LIMB_COLORS[0]
    if damage > 136:
        return UPPER_LIMB_COLORS[-1]
    return UPPER_LIMB_COLORS[int(probability_from_damage(damage) * 100)]
