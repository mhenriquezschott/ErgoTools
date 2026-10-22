"""Source-bound assessment evaluation using characterized model compatibility.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass, field, replace
from enum import StrEnum

from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
    task_has_data,
)
from ergotools.domain.assessments.duet import (
    DuetTask,
    DuetTaskResult,
    calculate_duet_task,
)
from ergotools.domain.assessments.duet_draft import DuetDraft, duet_draft_issues
from ergotools.domain.assessments.duet_summary import DuetSummary, summarize_duet_tasks
from ergotools.domain.assessments.lifft import LifftTaskResult, calculate_lifft_task
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.lifft_summary import (
    LifftSummary,
    summarize_lifft_tasks,
)
from ergotools.domain.assessments.lifft_validation import lifft_draft_issues
from ergotools.domain.assessments.tst import (
    TstDirection,
    TstTask,
    TstTaskResult,
    calculate_tst_task,
)
from ergotools.domain.assessments.tst_draft import TstDraft, tst_draft_issues
from ergotools.domain.assessments.tst_summary import TstSummary, summarize_tst_tasks
from ergotools.domain.assessments.validation import DraftError, InputIssue


class EvaluationStatus(StrEnum):
    """Explicit outcomes; an absent result must not be displayed as zero risk."""

    # Required entered-row inputs were present and model evaluation succeeded.
    COMPLETE = "complete"
    # Grid preview succeeded; genuinely started rows still lack required fields.
    PARTIAL = "partial"
    # Validation rejected source input; publish no calculated task results or summary.
    INVALID_INPUT = "invalid_input"
    # Explicit reserved review outcome, distinct from numeric or scientific validity.
    REVIEW_REQUIRED = "review_required"
    # Historical evidence status; current native result persistence accepts only
    # COMPLETE/PARTIAL.
    RECORDED = "recorded"  # Exported archived evidence; never a fresh evaluation.
    # Model arithmetic/validation produced a structured failure; publish no partial
    # outputs.
    CALCULATION_FAILED = "calculation_failed"


@dataclass(frozen=True, slots=True)
class AssessmentPreparation:
    """Mixed-session source snapshot and ordered validation issues.

    Retains the origin only for identity checks; release preparations on close.
    Completeness does not imply scientific validation or arithmetic success.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        revision: Captured session-local revision identity, not a persisted assessment
            version number.
        source: Exact immutable source object captured from the originating session.
        kind: Supported source model identity, independent of visible tab text.
        issues: Ordered structured input or calculation issues; absence is not silently
            converted to numeric zero.
        _session: Originating owner-thread session retained only for identity checks;
            release preparations on close.
    """

    document: DocumentKey
    revision: int
    source: AssessmentDraft
    kind: AssessmentKind
    issues: tuple[InputIssue, ...]
    _session: DocumentSession[AssessmentDraft] = field(repr=False, compare=False)

    def is_current(self, active: DocumentSession[AssessmentDraft] | None) -> bool:
        """Require the actual active session, captured revision and source identity.

        Args:
            active: Actual currently active session, or None after closing; equal values
                in another session do not match.

        Returns:
            True only for the exact originating active session, captured revision and
            original source object.
        """
        return (
            active is self._session
            and active.revision == self.revision
            and active.state is self.source
        )


def prepare_assessment(
    session: DocumentSession[AssessmentDraft],
) -> AssessmentPreparation:
    """Validate the mixed source without casts, history changes or calculation.

    Args:
        session: Caller-owned assessment session inspected synchronously on its owner
            thread.

    Returns:
        Immutable mixed-model source/preparation snapshot with complete ordered input
        issues, without editing history.

    Raises:
        ValueError: The session source has no supported assessment draft type.
    """
    source = session.state
    kind = assessment_kind(source)
    if isinstance(source, LifftDraft):
        issues = lifft_draft_issues(source)
    elif isinstance(source, DuetDraft):
        issues = duet_draft_issues(source)
    else:
        issues = tst_draft_issues(source)
    return AssessmentPreparation(
        session.document, session.revision, source, kind, issues, session
    )


@dataclass(frozen=True, slots=True)
class AssessmentEvaluation:
    """Source-bound full/partial result or explicit failure with structured issues.

    Failure/review outcomes have no task results or summary. Construct via the
    evaluator; this value does not certify scientific correctness of the models.

    Attributes:
        preparation: Exact source/session/revision provenance used to reject foreign or
            obsolete display/results.
        status: Explicit complete/partial/invalid/failure outcome; absence of results is
            distinct from zero risk.
        task_results: Ordered model-calculated rows, with their model-specific intrinsic
            rounding and source units.
        summary: Model-specific aggregate with dimensionless damage and optional 0-1
            probability, or None on failure.
        issues: Ordered structured input or calculation issues; absence is not silently
            converted to numeric zero.
    """

    preparation: AssessmentPreparation
    status: EvaluationStatus
    task_results: (
        tuple[LifftTaskResult, ...]
        | tuple[DuetTaskResult, ...]
        | tuple[TstTaskResult, ...]
    ) = ()
    summary: LifftSummary | DuetSummary | TstSummary | None = None
    issues: tuple[InputIssue, ...] = ()


class AssessmentEvaluator:
    """Own at most one evaluation, independent of persistence, widgets and language.

    Owner-thread synchronous use only. Views must query current(actual_active) before
    displaying results, and clear on project close/switch to release the retained
    origin. No automatic widget notification or background job exists.
    """

    def __init__(self) -> None:
        """Start with no cached result or retained session.

        Args:
            None.

        Returns:
            None. Initialize an empty single-outcome cache with no retained source
            session.
        """
        self._evaluation: AssessmentEvaluation | None = None

    def clear(self) -> None:
        """Release the cached source/session/result without editing the document.

        Args:
            None.

        Returns:
            None. Release the owned cached source/session/outcome; do not edit or save
            the assessment.
        """
        self._evaluation = None

    def current(
        self, active: DocumentSession[AssessmentDraft] | None
    ) -> AssessmentEvaluation | None:
        """Return an outcome only for its exact source; stale results remain hidden.

        Undo to the original revision can restore eligibility if no later evaluation
        replaced the cache. Save alone preserves it; equal-valued reloads do not.

        Args:
            active: Actual currently active session, or None after closing; equal values
                in another session do not match.

        Returns:
            Cached outcome only while its source preparation matches the actual active
            session/revision/object; otherwise None.
        """
        evaluation = self._evaluation
        return (
            evaluation
            if evaluation is not None and evaluation.preparation.is_current(active)
            else None
        )

    def evaluate(
        self, session: DocumentSession[AssessmentDraft]
    ) -> AssessmentEvaluation:
        """Evaluate valid tasks together; never return partial totals.

        Clear any old result before work, so even unexpected exceptions cannot expose it
        as current. LiFFT uses the characterized reference conversion in both unit
        systems, including its documented legacy moment-display expression. This is
        behavioral compatibility, not scientific certification. ST projects the
        explicitly recorded direction convention before calculation. Known numeric
        errors become issues; no formula or source quantity is rewritten. Unexpected
        programming errors propagate for diagnosis. No I/O is performed.

        Args:
            session: Caller-owned assessment session inspected synchronously on its
                owner thread.

        Returns:
            Source-bound COMPLETE or explicit invalid/calculation-failed outcome;
            missing input never produces a strict partial total.
        """
        return self._evaluate(session)

    def evaluate_lifft_grid(
        self, session: DocumentSession[AssessmentDraft]
    ) -> AssessmentEvaluation:
        """Calculate the reference grid's incomplete-row preview without source edits.

        Complete rows contribute damage. Arm/load without repetitions show only moment;
        other incomplete rows show zero outputs. Missing source values remain missing.
        Wholly unused slots do not affect completeness; started incomplete rows retain
        PARTIAL/required-field issues. Numeric and scientific-review failures suppress
        all outputs. Strict evaluate() is unchanged.

        Args:
            session: Caller-owned assessment session inspected synchronously on its
                owner thread.

        Returns:
            Source-bound complete/partial original LiFFT grid outcome, or explicit
            failure with no outputs.

        Raises:
            ValueError: The active session source is not LiFFT; no calculation is
                attempted.
        """
        if not isinstance(session.state, LifftDraft):
            raise ValueError("LiFFT grid evaluation requires a LiFFT source.")
        return self._evaluate(session, grid_kind=AssessmentKind.LIFFT)

    def evaluate_duet_grid(
        self, session: DocumentSession[AssessmentDraft]
    ) -> AssessmentEvaluation:
        """Preview complete DUET rows beside blank slots without editing source.

        Unused default rows are ignored for completeness. Started missing-input rows
        produce zero damage and explicit PARTIAL status.
        Invalid values block all outputs. Strict evaluate() remains unchanged.

        Args:
            session: Caller-owned assessment session inspected synchronously on its
                owner thread.

        Returns:
            Source-bound complete/partial original DUET grid outcome, or explicit
            failure with no outputs.

        Raises:
            ValueError: The active session source is not DUET; no calculation is
                attempted.
        """
        if not isinstance(session.state, DuetDraft):
            raise ValueError("DUET grid evaluation requires a DUET source.")
        return self._evaluate(session, grid_kind=AssessmentKind.DUET)

    def evaluate_tst_grid(
        self, session: DocumentSession[AssessmentDraft]
    ) -> AssessmentEvaluation:
        """Preview original ST complete/arm-load rows beside unfinished slots.

        Source direction codes are projected once through their recorded convention.
        Missing inputs remain absent in the source; zero placeholders exist only in
        local calculation inputs. Invalid fields reject all outputs atomically.

        Args:
            session: Caller-owned assessment session inspected synchronously on its
                owner thread.

        Returns:
            Source-bound complete/partial original ST grid outcome with its saved
            direction convention, or explicit failure.

        Raises:
            ValueError: The active session source is not ST; no calculation is
                attempted.
        """
        if not isinstance(session.state, TstDraft):
            raise ValueError("ST grid evaluation requires an ST source.")
        return self._evaluate(session, grid_kind=AssessmentKind.TST)

    def _evaluate(
        self,
        session: DocumentSession[AssessmentDraft],
        *,
        grid_kind: AssessmentKind | None = None,
    ) -> AssessmentEvaluation:
        """Evaluate one source and retain its full, partial or failed outcome.

        Clear the old cache before validation. Strict mode rejects every issue; grid
        preview ignores unused slots when at least one row is started, and accepts
        missing required fields on started rows only. All-blank sources remain without
        modeled probability and never become complete zero-risk results. Preview zeros
        are local calculator inputs and never become saved source data. Apply the
        recorded ST direction convention once. Catch DraftError as CALCULATION_FAILED;
        unexpected exceptions propagate with the old cache already released. No output
        is persisted here.

        Args:
            session: Caller-owned assessment session inspected synchronously on its
                owner thread.
            grid_kind: None requires complete input; an explicit model enables only that
                model's original incomplete-row preview policy.

        Returns:
            New cached source-bound outcome: all task results and summary, or an
            explicit failure without partial publication. Missing preview fields remain
            missing in the source.
        """
        self.clear()
        prepared = prepare_assessment(session)
        source = prepared.source
        if grid_kind is not None and any(task_has_data(task) for task in source.tasks):
            # Unused capacity is not an incomplete task. Keep strict preparation
            # unchanged and retain issues on genuinely started rows, including zeros.
            unused = {task.task_id for task in source.tasks if not task_has_data(task)}
            prepared = replace(
                prepared,
                issues=tuple(
                    issue
                    for issue in prepared.issues
                    if issue.code != "validation.required"
                    or issue.task_id not in unused
                ),
            )
        missing = tuple(i for i in prepared.issues if i.code == "validation.required")
        invalid = tuple(i for i in prepared.issues if i not in missing)
        if prepared.issues and (grid_kind is None or invalid or not source.tasks):
            result = AssessmentEvaluation(
                prepared, EvaluationStatus.INVALID_INPUT, issues=prepared.issues
            )
        else:
            try:
                if isinstance(source, LifftDraft):
                    lifft_tasks = tuple(
                        calculate_lifft_task(
                            _grid_task(task)
                            if grid_kind is AssessmentKind.LIFFT
                            else task,
                            source.system,
                        )
                        for task in source.tasks
                    )
                    result = AssessmentEvaluation(
                        prepared,
                        EvaluationStatus.PARTIAL
                        if missing
                        else EvaluationStatus.COMPLETE,
                        lifft_tasks,
                        summarize_lifft_tasks(lifft_tasks, source.system),
                        issues=missing,
                    )
                elif isinstance(source, TstDraft):
                    model_tasks = tuple(
                        source.model_task(t.task_id) for t in source.tasks
                    )
                    tst_tasks = tuple(
                        calculate_tst_task(
                            _tst_grid_task(task)
                            if grid_kind is AssessmentKind.TST
                            else task,
                            source.system,
                        )
                        for task in model_tasks
                    )
                    result = AssessmentEvaluation(
                        prepared,
                        EvaluationStatus.PARTIAL
                        if missing
                        else EvaluationStatus.COMPLETE,
                        tst_tasks,
                        summarize_tst_tasks(tst_tasks, source.system),
                        issues=missing,
                    )
                else:
                    duet_tasks = tuple(
                        calculate_duet_task(
                            DuetTask(task.task_id, 0, 0)
                            if grid_kind is AssessmentKind.DUET
                            and (
                                task.omni_res_scale is None or task.repetitions is None
                            )
                            else task
                        )
                        for task in source.tasks
                    )
                    result = AssessmentEvaluation(
                        prepared,
                        EvaluationStatus.PARTIAL
                        if missing
                        else EvaluationStatus.COMPLETE,
                        duet_tasks,
                        summarize_duet_tasks(duet_tasks),
                        issues=missing,
                    )
            except DraftError as error:
                result = AssessmentEvaluation(
                    prepared, EvaluationStatus.CALCULATION_FAILED, issues=(error.issue,)
                )
        self._evaluation = result
        return result


def _grid_task(task: LifftTask) -> LifftTask:
    """Project reference preview inputs locally; never replace the source task.

    A missing arm or load prevents moment calculation. Missing repetitions alone allow
    the reference rep=0 moment preview, contributing no cumulative damage. Complete
    inputs pass unchanged through the existing strict calculator.

    Args:
        task: Immutable original task; preview substitution is local and never fills
            saved source fields.

    Returns:
        Original complete LiFFT task, a local repetition-zero moment preview, or an
        all-zero local placeholder when arm/load are missing.
    """
    if task.lever_arm is None or task.load is None:
        return LifftTask(task.task_id, 0, 0, 0)
    return replace(task, repetitions=0) if task.repetitions is None else task


def _tst_grid_task(task: TstTask) -> TstTask:
    """Keep reference rep=0 moment previews local; never fill unfinished source.

    Args:
        task: Immutable original task; preview substitution is local and never fills
            saved source fields.

    Returns:
        Original complete ST task, a local repetition-zero moment preview, or a local
        handling-loads zero placeholder for missing direction/arm/load.
    """
    if task.direction is None or task.lever_arm is None or task.load is None:
        return TstTask(task.task_id, TstDirection.HANDLING_LOADS, 0, 0, 0)
    return replace(task, repetitions=0) if task.repetitions is None else task
