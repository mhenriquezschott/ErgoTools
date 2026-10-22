"""Stateless LiFFT summary text/colors preserving the assessment display policy.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.lifft_summary import LifftSummary
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.presentation.desktop.theme.assessment_probability import (
    format_assessment_probability as format_lifft_probability,
)
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color

__all__ = ["LifftSummaryDisplay", "display_lifft_summary", "format_lifft_probability"]


@dataclass(frozen=True, slots=True)
class LifftSummaryDisplay:
    """Complete immutable original decimal-point output snapshot.

    Optional project precision overrides decimal defaults without changing colors.
    None colors instruct the integrated host to clear stale styling; input decimal
    conventions are handled separately.

    Attributes:
        damage_text: Original four-decimal positive total or 0.0 zero-total text.
        probability_text: Original one-decimal bounded probability percent text.
        color: Original total damage color, or None to clear zero-total styling.
        task_colors: Source-order colors, None for rounded-zero task contribution.
        contribution_texts: Source-order original rounded percent share texts.
    """

    damage_text: str
    probability_text: str
    color: str | None
    task_colors: tuple[str | None, ...]
    contribution_texts: tuple[str, ...]


def display_lifft_summary(
    summary: LifftSummary, precision: DisplayPrecision | None = None
) -> LifftSummaryDisplay:
    """Derive all display state afresh from a summary produced by the domain API.

    Preserve suppression of task color when its rounded contribution is zero. Explicitly
    clear all colors/shares on zero totals rather than retaining stale widget state as
    the reference method can do. No widgets or assets are changed.

    Args:
        precision: Project display decimals; None retains original diagnostic
            formatting.
        summary: Complete validated domain-produced model summary; scientific quantities
            retain their recorded units and precision.

    Returns:
        Complete immutable original-formatted text/color snapshot, with explicit
        clearing instructions for unavailable/zero styling.

    Raises:
        ValueError: A summary supplies invalid damage or probability to the display
            helpers.
    """
    damage_places = precision.damage if precision else 4
    return LifftSummaryDisplay(
        f"{summary.total_damage:.{damage_places}f}" if summary.total_damage else "0.0",
        format_lifft_probability(
            summary.probability, precision.probability if precision else 1
        ),
        lifft_damage_color(summary.total_damage) if summary.total_damage else None,
        tuple(
            lifft_damage_color(task.cumulative_damage) if task.percentage else None
            for task in summary.contributions
        ),
        tuple(
            f"{task.percentage:.{precision.contribution}f}"
            if precision
            else str(task.percentage)
            for task in summary.contributions
        ),
    )
