"""One current risk measurement and optional task source per Job/tool.

Domain layer. Immutable values distinguish missing from zero and validate ownership,
units and task-model identity. No profiles, evidence lifecycle, Qt or SQL are retained.
Editing/calculation policy belongs to application services; storage owns transactions.
"""

from dataclasses import dataclass
from math import isfinite

from ergotools.domain.assessments.context import _require_identity
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.job_catalog import JobCatalog


@dataclass(frozen=True, slots=True)
class JobTaskResult:
    """Exact output for one source-positioned Job task; no alternate result set.

    Attributes:
        moment: Moment in source display units; None for DUET/blank rows.
        damage: Dimensionless task damage with intrinsic calculator precision.
        share_percent: Task contribution in 0-100 percent, or None if unavailable.
    """

    moment: float | None
    damage: float | None
    share_percent: float | None

    def __post_init__(self) -> None:
        """Validate finite nonnegative task outputs without rounding or recalculating.

        Args:
            None.

        Returns:
            None; missing values stay absent rather than becoming zero.

        Raises:
            ValueError: An output is nonnumeric, nonfinite, negative or outside percent.
        """
        for value in (self.moment, self.damage, self.share_percent):
            if value is not None and (
                type(value) not in (int, float) or not isfinite(value) or value < 0
            ):
                raise ValueError("Job task outputs must be finite nonnegative numbers.")
        if self.share_percent is not None and self.share_percent > 100:
            raise ValueError("Task contribution must not exceed 100 percent.")


@dataclass(frozen=True, slots=True)
class JobRiskMeasurement:
    """Single current tool input/output; an uncalculated source has absent outputs.

    Attributes:
        kind: LiFFT, DUET or ST identity, never a translated caption.
        cumulative_damage: Nonnegative dimensionless damage; None before calculation.
        probability_percent: Outcome probability in 0-100 percent, never a fraction.
        unit: Recorded calculation units; source units are never inferred from language.
        source: Optional independent calculator tasks. None means direct entry; changing
            tasks must invalidate outputs. Worker copies never carry ownership links.
        task_results: Exact per-task outputs in source order, empty before calculation.
    """

    kind: AssessmentKind
    cumulative_damage: float | None = None
    probability_percent: float | None = None
    unit: str | None = None
    source: AssessmentDraft | None = None
    task_results: tuple[JobTaskResult, ...] = ()

    def __post_init__(self) -> None:
        """Validate finite measurements, matching tools and retained task capacity.

        Args:
            None.

        Returns:
            None; never calculate or normalize scientific values during construction.

        Raises:
            ValueError: Tool, units, quantities or source model/capacity is invalid.
        """
        if not isinstance(self.kind, AssessmentKind):
            raise ValueError("Measurement requires a supported assessment kind.")
        for value in (self.cumulative_damage, self.probability_percent):
            if value is not None and (
                type(value) not in (int, float) or not isfinite(value) or value < 0
            ):
                raise ValueError("Risk values must be finite nonnegative numbers.")
        if self.probability_percent is not None and self.probability_percent > 100:
            raise ValueError("Probability percent must not exceed 100.")
        if self.unit is not None and not isinstance(self.unit, str):
            raise ValueError("Risk units require text or absence.")
        if self.source is not None and (
            assessment_kind(self.source) is not self.kind
            or not 1 <= len(self.source.tasks) <= 100
        ):
            raise ValueError(
                "Job calculator requires 1-100 tasks of the selected tool."
            )
        if (
            not isinstance(self.task_results, tuple)
            or any(not isinstance(row, JobTaskResult) for row in self.task_results)
            or (self.source is None and self.task_results)
            or (self.task_results and (not self.complete or self.source is None))
            or (
                self.source is not None
                and self.complete
                and len(self.task_results) != len(self.source.tasks)
            )
        ):
            raise ValueError(
                "Calculated Job task outputs must match the current source."
            )

    @property
    def complete(self) -> bool:
        """Report usable current outputs; missing values never become zero.

        Args:
            None.

        Returns:
            True when both current damage and probability exist, including exact zero.
        """
        return (
            self.cumulative_damage is not None and self.probability_percent is not None
        )


@dataclass(frozen=True, slots=True)
class JobRiskValues:
    """The single editable risk set belonging to a Job, with no separate identity.

    Attributes:
        job_id: Exact parent Job identity.
        measurements: At most one current source/output per tool. Empty means no risk.
    """

    job_id: str
    measurements: tuple[JobRiskMeasurement, ...] = ()

    def __post_init__(self) -> None:
        """Reject duplicate tools or mutable/untyped collections.

        Args:
            None.

        Returns:
            None; no provenance or alternate values are manufactured.

        Raises:
            ValueError: Parent identity, collection or tool uniqueness is invalid.
        """
        _require_identity(self.job_id)
        if (
            not isinstance(self.measurements, tuple)
            or any(
                not isinstance(item, JobRiskMeasurement) for item in self.measurements
            )
            or len({item.kind for item in self.measurements}) != len(self.measurements)
        ):
            raise ValueError("A Job requires at most one measurement per tool.")


@dataclass(frozen=True, slots=True)
class JobRiskCatalog:
    """Project-owned current Job values; identity is Job ID, not an artificial profile.

    Attributes:
        project_id: Exact project owning every Job.
        values: Nonempty risk sets in stable Job order, one per Job.
    """

    project_id: str
    values: tuple[JobRiskValues, ...] = ()

    def __post_init__(self) -> None:
        """Validate immutable unique populated Job sets.

        Args:
            None.

        Returns:
            None; absent Job measurements remain absent.

        Raises:
            ValueError: Collection type, duplicate Jobs or empty sets are invalid.
        """
        _require_identity(self.project_id)
        if (
            not isinstance(self.values, tuple)
            or any(
                not isinstance(item, JobRiskValues) or not item.measurements
                for item in self.values
            )
            or len({item.job_id for item in self.values}) != len(self.values)
        ):
            raise ValueError("Risk catalog requires unique populated Job sets.")
        object.__setattr__(
            self, "values", tuple(sorted(self.values, key=lambda item: item.job_id))
        )

    def for_job(self, job_id: str) -> JobRiskValues:
        """Return a Job's current risk set, or an empty value without inserting it.

        Args:
            job_id: Exact requested Job identity.

        Returns:
            Immutable current measurements or a nonpersisted empty set.
        """
        return next(
            (item for item in self.values if item.job_id == job_id),
            JobRiskValues(job_id),
        )

    def validate_jobs(self, jobs: JobCatalog) -> None:
        """Require the same project and real parent Jobs.

        Args:
            jobs: Complete immutable Job/placement/assignment catalog.

        Returns:
            None when every stored risk set has a real same-project parent.

        Raises:
            ValueError: Project ownership or Job membership differs.
        """
        if self.project_id != jobs.project_id or not {
            item.job_id for item in self.values
        } <= {job.job_id for job in jobs.jobs}:
            raise ValueError("Job risks require real Jobs in the same project.")
