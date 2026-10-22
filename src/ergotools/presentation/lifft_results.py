"""Source-bound LiFFT result rows for the integrated original-style UI.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluation,
    EvaluationStatus,
)
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.lifft import LifftTaskResult
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.lifft_summary import LifftSummary
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.theme.lifft_summary import (
    LifftSummaryDisplay,
    display_lifft_summary,
)


@dataclass(frozen=True, slots=True)
class LifftResultRow:
    """Stable source task identity and original display-formatted results.

    Attributes:
        task_id: Stable source row identity.
        moment_text: Original one-decimal recorded-unit moment.
        damage_text: Original four-decimal dimensionless task damage.
        contribution_text: Original percent contribution text.
        color: Original task fill color; None instructs the host to clear color.
    """

    task_id: str
    moment_text: str
    damage_text: str
    contribution_text: str
    color: str | None


@dataclass(frozen=True, slots=True)
class LifftResultDisplay:
    """Complete immutable LiFFT output snapshot.

    Replace rows and cards together; absence clears all stale numeric labels.

    Attributes:
        system: Recorded result unit system, independent of current display preference.
        rows: Original source-order formatted task results.
        summary: Original-formatted total/probability/cards and colors.
    """

    system: MeasurementSystem
    rows: tuple[LifftResultRow, ...]
    summary: LifftSummaryDisplay


def present_lifft_results(
    evaluation: AssessmentEvaluation | None,
    active: DocumentSession[AssessmentDraft] | None,
) -> LifftResultDisplay | None:
    """Present only complete current LiFFT results in original task order.

    No evaluation, normalization, display-unit conversion or source mutation occurs.
    Missing/stale/noncomplete/other-model outcomes return None, never zero values. Both
    recorded unit systems use the characterized reference display policy. Malformed
    complete LiFFT row identity, count, type or unit associations raise ValueError
    rather than silently zipping truncated/mismatched rows. Text preserves reference
    one/four-decimal precision and contribution formatting, independently of editable
    input conventions.

    Args:
        evaluation: Source-bound scientific outcome, or None when unavailable.
        active: Actual current source session, or None after close/switch.

    Returns:
        Complete original-formatted rows/cards only for a current complete LiFFT
        outcome; otherwise None, requiring the host to clear all outputs.

    Raises:
        ValueError: Complete LiFFT summary/rows/counts/order/model or unit associations
            are inconsistent.
    """
    if (
        evaluation is None
        or not evaluation.preparation.is_current(active)
        or evaluation.status is not EvaluationStatus.COMPLETE
    ):
        return None
    source = evaluation.preparation.source
    if not isinstance(source, LifftDraft):
        return None
    summary = evaluation.summary
    if not isinstance(summary, LifftSummary) or summary.system is not source.system:
        raise ValueError("LiFFT summary does not match its source units/model.")
    expected_ids = tuple(task.task_id for task in source.tasks)
    if (
        tuple(task.task_id for task in evaluation.task_results) != expected_ids
        or tuple(task.task_id for task in summary.contributions) != expected_ids
    ):
        raise ValueError(
            "LiFFT output identities/order must match the complete source."
        )
    display = display_lifft_summary(summary)
    rows = []
    for task, contribution, color in zip(
        evaluation.task_results,
        display.contribution_texts,
        display.task_colors,
        strict=True,
    ):
        if not isinstance(task, LifftTaskResult) or task.system is not source.system:
            raise ValueError("LiFFT task result has another model or unit system.")
        rows.append(
            LifftResultRow(
                task.task_id,
                f"{task.displayed_moment:.1f}",
                f"{task.cumulative_damage:.4f}",
                contribution,
                color,
            )
        )
    return LifftResultDisplay(source.system, tuple(rows), display)
