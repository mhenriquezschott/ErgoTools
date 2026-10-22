"""Preserved LiFFT continuous display palette, separate from gauge categories.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

import math

from ergotools.domain.assessments.lifft import probability_from_damage

# Exact original LiFFT continuous palette, indexed by truncated 0-100 probability
# percent; duplicate colors are intentional.
_COLORS: tuple[str, ...] = (
    "#2eff00",
    "#37ff00",
    "#3fff00",
    "#48ff00",
    "#50ff00",
    "#59ff00",
    "#61ff00",
    "#6aff00",
    "#72ff00",
    "#7bff00",
    "#83ff00",
    "#8cff00",
    "#94ff00",
    "#9dff00",
    "#a5ff00",
    "#aeff00",
    "#b6ff00",
    "#bfff00",
    "#c7ff00",
    "#d0ff00",
    "#d8ff00",
    "#e1ff00",
    "#e9ff00",
    "#f2ff00",
    "#faff00",
    "#fffa00",
    "#fff600",
    "#fff600",
    "#fff200",
    "#ffee00",
    "#ffee00",
    "#ffe900",
    "#ffe500",
    "#ffe500",
    "#ffe100",
    "#ffdc00",
    "#ffdc00",
    "#ffd800",
    "#ffd400",
    "#ffd400",
    "#ffd000",
    "#ffc700",
    "#ffbb00",
    "#ffae00",
    "#ffa100",
    "#ff9400",
    "#ff8800",
    "#ff7b00",
    "#ff6e00",
    "#ff6100",
    "#ff5400",
    "#ff4800",
    "#ff3b00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
    "#ff2e00",
)


def lifft_damage_color(damage: float) -> str:
    """Map nonnegative finite damage to the reference palette without changing it.

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
    if damage < 0.0001:
        return _COLORS[0]
    if damage > 1:
        return _COLORS[-1]
    return _COLORS[int(probability_from_damage(damage) * 100)]
