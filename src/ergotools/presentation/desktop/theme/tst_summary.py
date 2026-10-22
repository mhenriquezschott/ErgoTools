"""TST compatibility display policy, separate from scientific direction semantics.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_summary import TstSummary
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.presentation.desktop.theme.assessment_probability import (
    format_assessment_probability,
)
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color


def tst_direction_for_selection(index: int) -> TstDirection:
    """Preserve the original selector-to-calculation 0->0, 1->2, 2->1 mapping.

    The old downward/horizontal labels disagree with this mapping. Do not treat this
    adapter as scientific direction conversion or wire it into a new UI until reviewed.
    Raw model direction IDs bypass this selector adapter entirely.

    Owner-approved original compatibility mapping. Selector labels and internal model
    enum names differ; retain the original 1/2 swap exactly. Raw model direction IDs
    bypass this selector adapter. Do not apply this mapping twice.

    Args:
        index: Original visual selector index: 0 handling loads, 1 downward caption, 2
            horizontal caption; booleans are rejected.

    Returns:
        Original calculation branch: HANDLING_LOADS for 0, HORIZONTAL for 1 and DOWNWARD
            for 2.

    Raises:
        ValueError: Index is boolean, noninteger or outside 0..2.
    """
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= 2:
        raise ValueError("Unsupported TST selector index.")
    return (
        TstDirection.HANDLING_LOADS,
        TstDirection.HORIZONTAL,
        TstDirection.DOWNWARD,
    )[index]


@dataclass(frozen=True, slots=True)
class TstSummaryDisplay:
    """Complete immutable original decimal-point output snapshot.

    Optional project precision overrides decimal defaults without changing colors.
    None colors instruct the integrated host to clear stale styling; input decimal
    conventions are handled separately.

    Attributes:
        damage_text: Original four-decimal positive total or 0.0 zero-total text.
        probability_text: Original one-decimal bounded probability percent text.
        color: Original total damage color, or None to clear zero-total styling.
        task_moment_texts: Source-order one-decimal moments in recorded source units.
        task_damage_texts: Source-order five-decimal task damage texts.
        task_colors: Source-order colors, None for rounded-zero task contribution.
        contribution_texts: Source-order original rounded percent share texts.
    """

    damage_text: str
    probability_text: str
    color: str | None
    task_moment_texts: tuple[str, ...]
    task_damage_texts: tuple[str, ...]
    task_colors: tuple[str | None, ...]
    contribution_texts: tuple[str, ...]


def display_tst_summary(
    summary: TstSummary, precision: DisplayPrecision | None = None
) -> TstSummaryDisplay:
    """Format domain-produced summaries without updating widgets or shoulder actors.

    Project precision overrides only rendered decimal counts.
    Moments show one decimal, task damage five and positive total damage four. Zero
    total uses the reference 0.0 placeholders but explicitly clears styles and shares
    rather than retaining previous widget state. Rounded zero shares suppress task
    colors. Editable input decimal conventions are handled separately.

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
    moment_places = precision.moment if precision else 1
    return TstSummaryDisplay(
        f"{summary.total_damage:.{damage_places}f}" if summary.total_damage else "0.0",
        format_assessment_probability(
            summary.probability, precision.probability if precision else 1
        ),
        tst_damage_color(summary.total_damage) if summary.total_damage else None,
        tuple(f"{task.displayed_moment:.{moment_places}f}" for task in summary.tasks),
        tuple(f"{task.cumulative_damage:.{row_places}f}" for task in summary.tasks),
        tuple(
            tst_damage_color(task.cumulative_damage) if task.percentage else None
            for task in summary.contributions
        ),
        tuple(
            f"{task.percentage:.{precision.contribution}f}"
            if precision
            else str(task.percentage)
            for task in summary.contributions
        ),
    )
