"""JROT cell captions, continuous colors and unchanged row recommendations.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections import Counter

from ergotools.application.rotation_pool import RotationTargetChoice
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.language import Language
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color


def rotation_text(english: str, spanish: str, language: Language) -> str:
    """Select display text without changing saved identifiers or units.

    Args:
        english: English UI text; saved user values are never translated by this helper.
        spanish: Spanish UI text corresponding to the English caption.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        English or Spanish display text; source identifiers and units are untouched.
    """
    return spanish if language is Language.SPANISH else english


def target_labels(
    choices: tuple[RotationTargetChoice, ...], language: Language
) -> dict[str, str]:
    """Use original short labels and full ancestry when stations repeat.

    Args:
        choices: Frozen rotation target options including current Job measurements.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Opaque target-key to visible caption mapping, expanded to full ancestry when
        short station names collide.
    """
    short = {
        choice.target.key: choice.target.job_id
        + (f" - {choice.workplace.station_id}" if choice.workplace else "")
        for choice in choices
    }
    counts = Counter(short.values())
    result = {}
    for choice in choices:
        key = choice.target.key
        place = choice.workplace
        label = short[key]
        if counts[label] > 1 and place is not None:
            shift = rotation_text("Shift", "Turno", language)
            label = (
                f"{choice.target.job_id} @ {place.plant_name} / "
                f"{place.section_name} / {place.line_name} / "
                f"{place.station_id} / {shift} {place.shift_id}"
            )
        result[key] = label
    return result


def target_measurement(
    choice: RotationTargetChoice, kind: AssessmentKind
) -> JobRiskMeasurement | None:
    """Find recorded evidence, keeping missing values distinct from zero.

    Args:
        choice: Exact target/Job option whose recorded tool evidence is
            inspected.
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        Frozen measurement for the requested tool, or None when evidence is absent; zero
        remains valid.
    """
    return next(
        (
            item
            for item in choice.values.measurements
            if item.kind is kind and item.complete
        ),
        None,
    )


def measurement_color(kind: AssessmentKind, damage: float | None) -> str:
    """Preserve tool-specific damage colors; units are evidence, not conversions.

    Args:
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.
        damage: Observed dimensionless cumulative damage, or None for unavailable
            evidence.

    Returns:
        Original tool-specific continuous damage color, or neutral gray for unavailable
        evidence.
    """
    if damage is None:
        return "#D9E1E6"
    if kind is AssessmentKind.LIFFT:
        return lifft_damage_color(damage)
    if kind is AssessmentKind.DUET:
        return duet_damage_color(damage)
    return tst_damage_color(damage)


def rotation_recommendation(
    probabilities: tuple[float, ...], language: Language
) -> str:
    """Preserve the source thresholds and wording; values are probability percent.

    These are reference advisory rules, not a new scientific safety guarantee.

    Args:
        probabilities: Observed block probabilities in percent, retaining original
            recommendation thresholds.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Original localized advice derived from percentage thresholds, or empty text
        without probabilities.
    """
    if not probabilities:
        return ""
    average = sum(probabilities) / len(probabilities)
    if sum(value > 60 for value in probabilities) >= 2 and any(
        value < 20 for value in probabilities
    ):
        return rotation_text(
            "Redesign the high-risk jobs as the job rotation scheme is not safe.",
            "Rediseñe los trabajos de alto riesgo: "
            "el esquema de rotación no es seguro.",
            language,
        )
    if average > 50:
        return rotation_text(
            "Redesign at least one high-risk job, "
            "as the job rotation scheme is high-risk.",
            "Rediseñe al menos un trabajo de alto riesgo: "
            "la rotación es de alto riesgo.",
            language,
        )
    if 25 <= average <= 50:
        return rotation_text(
            "The job rotation scheme could be improved by redesigning the highest-risk "
            "job or adding more options for low-risk jobs.",
            "Mejore la rotación rediseñando el trabajo de mayor riesgo o agregando "
            "más opciones de bajo riesgo.",
            language,
        )
    return rotation_text(
        "This job rotation appears to be low risk.",
        "Esta rotación de trabajos parece ser de bajo riesgo.",
        language,
    )
