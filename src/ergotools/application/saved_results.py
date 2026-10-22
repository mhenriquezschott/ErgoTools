"""Build and select the single authoritative source-bound assessment result.

Application layer: detach established grid evaluation outputs without save-time
rounding/clipping, and match them to exact inputs before reuse. Conversion and
interactive Calculate share this policy. Persistence is delegated through a port; this
module performs no SQL, UI formatting, filesystem access or formula changes.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluation,
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.historical_results import (
    HistoricalAssessmentResult,
    HistoricalTaskResult,
)
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet import DuetTaskResult
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft import LifftTaskResult
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst import TstTaskResult
from ergotools.domain.model_units import MeasurementSystem


@runtime_checkable
class SavedResultRepository(Protocol):
    """Atomically replace one version's inputs and sole calculated result."""

    def save_result(
        self, document: DocumentKey, result: HistoricalAssessmentResult
    ) -> None:
        """Replace matching inputs/result together, or roll back both.

        Args:
            document: Project-scoped assessment version identity.
            result: Successful complete/partial output bound to its exact source.

        Returns:
            None after commit; no extra original or prior result is retained.
        """
        ...

    def load_saved_result(
        self, document: DocumentKey
    ) -> HistoricalAssessmentResult | None:
        """Read this version's sole saved calculation without recalculating.

        Args:
            document: Project-scoped assessment version identity.

        Returns:
            Detached calculation, or None if not yet calculated/invalidated.
        """
        ...


def result_snapshot(
    evaluation: AssessmentEvaluation, units: MeasurementSystem
) -> HistoricalAssessmentResult | None:
    """Detach successful full/partial outputs from the editor's evaluation cache.

    Intrinsic model rounding stays unchanged. Formatting and gauge limits belong to
    presentation. Missing probability stays None rather than a zero-risk claim. No
    session, database or evaluation cache is modified.

    Args:
        evaluation: Complete or partial output of the established grid evaluator.
        units: Calculation units; independent of the current display preference.

    Returns:
        Detached result with the calculator's total/task precision and probability
        multiplied by 100 without rounding/clipping, or None for failed outcomes.
    """
    summary = evaluation.summary
    if summary is None or evaluation.status not in (
        EvaluationStatus.COMPLETE,
        EvaluationStatus.PARTIAL,
    ):
        return None
    calculated: tuple[LifftTaskResult | DuetTaskResult | TstTaskResult, ...] = (
        evaluation.task_results
    )
    tasks = tuple(
        HistoricalTaskResult(
            None if isinstance(task, DuetTaskResult) else task.displayed_moment,
            task.cumulative_damage,
            contribution.percentage,
        )
        for task, contribution in zip(calculated, summary.contributions, strict=True)
    )
    percent = None if summary.probability is None else summary.probability * 100
    return HistoricalAssessmentResult(
        evaluation.preparation.source,
        summary.total_damage,
        percent,
        tasks,
        units.value.title(),
        evaluation.status,
        tuple(issue.code for issue in evaluation.issues),
    )


def stored_result(
    repository: object, document: DocumentKey, source: object
) -> HistoricalAssessmentResult | None:
    """Select the sole saved result only when it matches the current inputs.

    Args:
        repository: Object optionally implementing the saved-result storage port.
        document: Project-scoped assessment version identity.
        source: Current immutable input snapshot to compare with the saved result.

    Returns:
        Matching result, or None for absent/stale output. No imported fallback,
        recalculation or persistence occurs here.
    """
    result = (
        repository.load_saved_result(document)
        if isinstance(repository, SavedResultRepository)
        else None
    )
    return result if result is not None and result.source == source else None


def calculate_saved_result(
    document: DocumentKey, source: AssessmentDraft, defaults: MeasurementSystem
) -> HistoricalAssessmentResult | None:
    """Evaluate persisted inputs using the same grid policy as interactive Calculate.

    No input, formula, session outside this call or database is modified. This is the
    external converter's calculation boundary, not a parallel calculator.

    Args:
        document: Project-scoped version identity, used only for evaluation binding.
        source: Exact saved task inputs, units and explicit ST direction convention.
        defaults: Project unit label for DUET's unit-independent input model only.

    Returns:
        Full-precision complete/partial result, or None for invalid/failed inputs.
        Missing inputs remain absent in source; established partial-grid behavior
        contributes only what that calculator can evaluate.

    Raises:
        ValueError: Source model or declared unit system is unsupported.
    """
    session: DocumentSession[AssessmentDraft] = DocumentSession(document, source)
    evaluator = AssessmentEvaluator()
    outcome = (
        evaluator.evaluate_lifft_grid(session)
        if isinstance(source, LifftDraft)
        else evaluator.evaluate_duet_grid(session)
        if isinstance(source, DuetDraft)
        else evaluator.evaluate_tst_grid(session)
    )
    units = defaults if isinstance(source, DuetDraft) else source.system
    return result_snapshot(outcome, units)


@dataclass(frozen=True, slots=True)
class ResultSave[State]:
    """Adapt a source session save to one atomic source/result repository commit.

    Attributes:
        repository: Borrowed atomic source/result persistence port; no connection
            ownership is transferred.
        result: Detached sole calculation bound to the exact source that the save
            adapter is allowed to commit.
    """

    repository: SavedResultRepository
    result: HistoricalAssessmentResult

    def save(self, document: DocumentKey, state: State) -> None:
        """Save matching inputs and the sole result through the atomic port.

        Args:
            document: Assessment version being saved.
            state: Exact session inputs captured with this calculation.

        Returns:
            None after the repository commit; session owns its clean marker.

        Raises:
            ValueError: Inputs differ from those used for this result.
        """
        if state != self.result.source:
            raise ValueError("Saved result does not match active source.")
        self.repository.save_result(document, self.result)
