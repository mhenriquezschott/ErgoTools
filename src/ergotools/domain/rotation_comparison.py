"""Frozen rotation comparisons without live catalogs, renderers or solver calls.

Domain layer. Indices use the accepted duration model. Deltas compare the same frozen
Job coefficients and timeline, never an old schedule with newly edited Job values.
"""

from dataclasses import dataclass, replace
from math import isfinite

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationRisk
from ergotools.domain.rotation_planning import RotationPlanningProblem
from ergotools.domain.rotation_scenario import (
    ROTATION_RUN_MODEL_VERSION,
    RotationInputs,
    RotationRun,
    complete_rotation_rows,
)


@dataclass(frozen=True, slots=True)
class IndexSummary:
    """Unrounded distribution of worker planning indices, not injury probabilities.

    Attributes:
        values: Exact worker-order indices from one complete staffed schedule.
    """

    values: tuple[float, ...]

    def __post_init__(self) -> None:
        """Require a nonempty immutable distribution of finite numeric indices.

        Args:
            None.

        Returns:
            None; no rounding, normalization or clamping is performed.

        Raises:
            ValueError: Distribution is empty, mutable or contains nonfinite values.
        """
        if (
            not isinstance(self.values, tuple)
            or not self.values
            or any(type(v) not in (int, float) or not isfinite(v) for v in self.values)
        ):
            raise ValueError("Indices require a nonempty finite numeric distribution.")

    @property
    def mean(self) -> float:
        """Read the population mean without display rounding.

        Args:
            None.

        Returns:
            Arithmetic mean of the nonempty worker index distribution.
        """
        return sum(self.values) / len(self.values)

    @property
    def worst(self) -> float:
        """Read the highest worker index.

        Args:
            None.

        Returns:
            Maximum weighted index in percentage points.
        """
        return max(self.values)

    @property
    def spread(self) -> float:
        """Read the distribution range without implying population-mean reduction.

        Args:
            None.

        Returns:
            Highest minus lowest worker index in percentage points.
        """
        return max(self.values) - min(self.values)


@dataclass(frozen=True, slots=True)
class ToolComparison:
    """Same-context before/after worker indices for one analyzed tool.

    Attributes:
        kind: Selected model, independent of whichever tab is displayed.
        before: None if no entered baseline/proposal exists; never inferred.
        after: Independently validated optimized arrangement indices.
        has_baseline: True identifies an entered or explicitly promoted baseline.
    """

    kind: AssessmentKind
    before: IndexSummary | None
    after: IndexSummary
    has_baseline: bool

    @property
    def changes(self) -> tuple[float, ...] | None:
        """Compare each worker without inventing a missing starting score.

        Args:
            None.

        Returns:
            After minus before; negative means a lower index. None stays missing.
        """
        if self.before is None:
            return None
        return tuple(
            a - b for a, b in zip(self.after.values, self.before.values, strict=True)
        )


def starting_indices(
    inputs: RotationInputs, risks: tuple[RotationRisk, ...], kind: AssessmentKind
) -> IndexSummary | None:
    """Evaluate a complete entered starting schedule without enforcing new rules.

    Args:
        inputs: Current or frozen dated/timed inputs with explicit schedules.
        risks: Available coefficients; the requested tool must be complete.
        kind: Selected tool to display independently of other missing tools.

    Returns:
        Baseline indices, otherwise proposed indices, or None if absent.

    Raises:
        ValueError: A present schedule, timing or requested coefficients are incomplete.
    """
    rows = inputs.baseline if inputs.baseline is not None else inputs.proposed
    if rows is None:
        return None
    if kind not in inputs.tools:
        raise ValueError("Select an analyzed tool before comparing its indices.")
    neutral = replace(
        inputs,
        tools=(kind,),
        baseline=None,
        proposed=None,
        rules=(),
        previous=None,
        following=None,
    )
    problem = RotationPlanningProblem(
        neutral, tuple(r for r in risks if r.kind is kind)
    )
    return IndexSummary(problem.scores(complete_rotation_rows(rows), kind))


def compare_rotation_run(run: RotationRun) -> tuple[ToolComparison, ...]:
    """Evaluate only the immutable context of a supported accepted or preview run.

    Args:
        run: Complete saved evidence, never live project Job measurements.

    Returns:
        Analyzed-tool-order distributions using the same coefficients on both sides.

    Raises:
        ValueError: Model is unsupported or schedule/rule evidence is invalid.
    """
    if run.contract_version != ROTATION_RUN_MODEL_VERSION:
        raise ValueError(
            "This saved model is read-only; weighted comparison is unavailable."
        )
    risks = tuple(
        RotationRisk(
            c.target_key, c.measurement.kind, c.measurement.probability_percent
        )
        for c in run.coefficients
        if c.measurement.probability_percent is not None
    )
    problem = RotationPlanningProblem(run.inputs, risks)
    problem.validate_schedule(run.arrangement)
    return tuple(
        ToolComparison(
            kind,
            starting_indices(run.inputs, risks, kind),
            IndexSummary(problem.scores(run.arrangement, kind)),
            run.inputs.baseline is not None,
        )
        for kind in run.inputs.tools
    )
