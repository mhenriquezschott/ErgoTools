"""Apply explicitly historical row outputs using existing assessment controls.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Sequence

from PyQt5.QtWidgets import QLabel

from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.domain.assessments.document import AssessmentKind, assessment_kind
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color


def historical_number(value: float | None, places: int) -> str:
    """Format recorded numbers without inferring absent values or recalculating.

    Args:
        value: Observed metric, or None for missing evidence; formatting never changes
            storage.
        places: Number of decimal places used for display only; the stored value is
            untouched.

    Returns:
        Display-rounded number or an em dash for absent recorded output; no
        recomputation occurs.
    """
    return "—" if value is None else f"{value:.{places}f}"


def historical_damage_color(result: HistoricalAssessmentResult) -> str | None:
    """Preserve recorded totals while matching fresh Save/reopen palette shades.

    Saved summaries retain calculator precision; the labels apply display rounding.
    Retained row damages preserve the palette operand without recalculating inputs. Add
    in row order, as the original tool does; Python's sum can round differently.
    Incomplete saved row evidence uses its matching saved summary.

    Args:
        result: Matching saved result cache in recorded source units; not a second
            calculation or migration archive.

    Returns:
        Original continuous palette color using matching saved row operands when
        complete, or None without cumulative damage.
    """
    if result.damage is None:
        return None
    damage = result.damage
    if result.calculation_status is not None and result.tasks:
        total = 0.0
        for row in result.tasks:
            if row.damage is None:
                break
            total += row.damage
        else:
            if total == 0:
                return None
            damage = total
    return {
        AssessmentKind.LIFFT: lifft_damage_color,
        AssessmentKind.DUET: duet_damage_color,
        AssessmentKind.TST: tst_damage_color,
    }[assessment_kind(result.source)](damage)


def show_historical_rows(
    outputs: Sequence[Sequence[QLabel]],
    result: HistoricalAssessmentResult,
    precision: DisplayPrecision | None = None,
) -> None:
    """Project original row evidence, keeping moments in original result units.

    Args:
        precision: Optional project decimal counts; None keeps diagnostic defaults.
        outputs: Existing row output labels in tool-specific moment/damage/percentage
            order.
        result: Matching saved result cache in recorded source units; not a second
            calculation or migration archive.

    Returns:
        None.
    """
    for labels, row in zip(outputs, result.tasks, strict=True):
        values: tuple[float | None, ...] = (row.moment, row.damage, row.share_percent)
        if assessment_kind(result.source) is AssessmentKind.DUET:
            values = values[1:]
        places = (
            (1, 4 if assessment_kind(result.source) is AssessmentKind.LIFFT else 5, 1)
            if len(labels) == 3
            else (5, 1)
        )
        if precision is not None:
            places = (
                (precision.moment, precision.damage, precision.contribution)
                if len(labels) == 3
                else (precision.damage, precision.contribution)
            )
        for label, value, decimals in zip(labels, values, places, strict=True):
            label.setText(historical_number(value, decimals))

        if row.damage is not None and row.share_percent:
            color = {
                AssessmentKind.LIFFT: lifft_damage_color,
                AssessmentKind.DUET: duet_damage_color,
                AssessmentKind.TST: tst_damage_color,
            }[assessment_kind(result.source)](row.damage)
            labels[0 if len(labels) == 2 else 1].setStyleSheet(
                "background-color: " + color
            )
