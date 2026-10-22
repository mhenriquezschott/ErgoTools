"""Stateless DUET assessment display values with explicit clearing instructions.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.duet_summary import DuetSummary
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.presentation.desktop.theme.assessment_probability import (
    format_assessment_probability,
)
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color


@dataclass(frozen=True, slots=True)
class DuetSummaryDisplay:
    """Complete immutable original decimal-point output snapshot.

    Optional project precision overrides decimal defaults without changing colors.
    None colors instruct the integrated host to clear stale styling; input decimal
    conventions are handled separately.

    Attributes:
        damage_text: Original four-decimal positive total or 0.0 zero-total text.
        probability_text: Original one-decimal bounded probability percent text.
        color: Original total damage color, or None to clear zero-total styling.
        task_damage_texts: Source-order five-decimal task damage texts.
        task_colors: Source-order colors, None for rounded-zero task contribution.
        contribution_texts: Source-order original rounded percent share texts.
    """

    damage_text: str
    probability_text: str
    color: str | None
    task_damage_texts: tuple[str, ...]
    task_colors: tuple[str | None, ...]
    contribution_texts: tuple[str, ...]


def display_duet_summary(
    summary: DuetSummary, precision: DisplayPrecision | None = None
) -> DuetSummaryDisplay:
    """Map a domain summary with five-decimal rows and four-decimal positive total.

    Project precision overrides only rendered decimal counts.
    Retain reference color suppression for zero rounded shares and bounded risk text,
    but clear stale styles/shares explicitly when the total becomes zero. This function
    changes no UI or VTK actor and assumes a domain-produced summary.

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
    row_places = precision.damage if precision else 5
    return DuetSummaryDisplay(
        f"{summary.total_damage:.{damage_places}f}" if summary.total_damage else "0.0",
        format_assessment_probability(
            summary.probability, precision.probability if precision else 1
        ),
        duet_damage_color(summary.total_damage) if summary.total_damage else None,
        tuple(
            f"{task.cumulative_damage:.{row_places}f}" for task in summary.contributions
        ),
        tuple(
            duet_damage_color(task.cumulative_damage) if task.percentage else None
            for task in summary.contributions
        ),
        tuple(
            f"{task.percentage:.{precision.contribution}f}"
            if precision
            else str(task.percentage)
            for task in summary.contributions
        ),
    )
