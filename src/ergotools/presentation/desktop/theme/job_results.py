"""Shared Job task, result-card and copy-preview colors from existing tool palettes.

Presentation theme layer. Delegate to the established continuous damage mappings;
do not classify, recalculate, round or change any stored measurement.
"""

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color

# Existing continuous damage palettes, keyed by stable tool rather than UI labels.
_COLORS = {
    AssessmentKind.LIFFT: lifft_damage_color,
    AssessmentKind.DUET: duet_damage_color,
    AssessmentKind.TST: tst_damage_color,
}


def job_damage_color(kind: AssessmentKind, damage: float | None) -> str:
    """Resolve the same damage shade used by the main assessment controls.

    Args:
        kind: Exact LiFFT/DUET/ST identity.
        damage: Dimensionless task/aggregate damage, or None when unavailable.

    Returns:
        Original palette color, or the existing neutral missing-result color.

    Raises:
        ValueError: Damage is negative or nonfinite.
    """
    return "#D9E1E6" if damage is None else _COLORS[kind](damage)
