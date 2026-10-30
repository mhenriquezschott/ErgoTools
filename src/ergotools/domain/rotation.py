"""Immutable JROT schedules and probability inputs, independent of solvers/UI.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from ergotools.domain.assessments.document import AssessmentKind


class RotationBackend(StrEnum):
    """Owner-approved backend identity; there is no automatic fallback."""

    # Owner-approved single-tool solver; no automatic fallback.
    CBC = "cbc"
    # Owner-approved multi-tool solver; GLPK is not supported.
    HIGHS = "highs"


class RotationSolveStatus(StrEnum):
    """Solver termination evidence, subject to configured numeric/gap tolerances."""

    # Backend reports optimal under configured numeric/relative-gap tolerances.
    OPTIMAL = "optimal"
    # Validated incumbent accepted without an optimal termination report.
    FEASIBLE = "feasible"


@dataclass(frozen=True, slots=True)
class WorkerRotation:
    """One worker's ordered opaque target keys; keys are never display labels.

    Attributes:
        worker_id: Literal saved worker identity; names never establish ownership.
        target_keys: Ordered opaque target identities, one per time block; never display
            labels.
    """

    worker_id: str
    target_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject empty identities and mutable/incomplete target sequences.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkerRotation.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: A rotation requires a Worker and complete target keys.
        """
        if (
            not isinstance(self.worker_id, str)
            or not self.worker_id.strip()
            or not isinstance(self.target_keys, tuple)
            or not self.target_keys
            or any(
                not isinstance(key, str) or not key.strip() for key in self.target_keys
            )
        ):
            raise ValueError("A rotation requires a Worker and complete target keys.")


@dataclass(frozen=True, slots=True)
class RotationRisk:
    """Current Job probability in percent; zero is valid and absence is rejected.

    Target keys distinguish Job/placement identities through the calling
    repository. Percentages are dimensionless; source unit evidence stays with the
    current Job measurement and is not converted here. This value does not certify
    model validity.

    Attributes:
        target_key: Opaque Job/placement identity matching a scheduled target.
        kind: Stable assessment model identity; displayed tool names are localized
            separately.
        probability_percent: Recorded probability in percent (0-100), not the
            calculators' 0-1 scale; zero is present evidence.
    """

    target_key: str
    kind: AssessmentKind
    probability_percent: float

    def __post_init__(self) -> None:
        """Require a supported tool and finite percentage between zero and 100.

        Args:
            None. Dataclass construction supplies the fields documented on RotationRisk.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: A target requires a supported tool and finite percent risk.
        """
        if (
            not isinstance(self.target_key, str)
            or not self.target_key.strip()
            or not isinstance(self.kind, AssessmentKind)
            or type(self.probability_percent) not in (int, float)
            or not isfinite(self.probability_percent)
            or not 0 <= self.probability_percent <= 100
        ):
            raise ValueError(
                "A target requires a supported tool and finite percent risk."
            )


@dataclass(frozen=True, slots=True)
class RotationProblem:
    """Complete current schedule and frozen job risks for a bounded solve.

    Each solve stage receives time_limit_seconds, matching the reference. Current
    assignments may collide within a block; the optimizer must resolve those collisions
    while retaining overall target totals. No schedule is persisted.

    Attributes:
        current: Immutable schedule rows in original worker order; each row has the same
            positive block count.
        risks: Frozen model-specific target probabilities in percent; completeness is
            checked for the requested tool.
        time_limit_seconds: Finite positive wall-time bound for each solve stage,
            matching the reference policy.
    """

    current: tuple[WorkerRotation, ...]
    risks: tuple[RotationRisk, ...]
    time_limit_seconds: float = 60.0

    def __post_init__(self) -> None:
        """Reject incomplete/duplicate workers, inconsistent blocks and risk keys.

        Args:
            None. Dataclass construction supplies the fields documented on
            RotationProblem.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Workers must be unique with one target in every block. Risk keys
                must be unique and belong to scheduled targets. A solve stage requires a
                finite positive time limit.
        """
        if (
            not isinstance(self.current, tuple)
            or not self.current
            or any(not isinstance(row, WorkerRotation) for row in self.current)
            or len({row.worker_id for row in self.current}) != len(self.current)
            or len({len(row.target_keys) for row in self.current}) != 1
        ):
            raise ValueError("Workers must be unique with one target in every block.")
        if (
            not isinstance(self.risks, tuple)
            or any(not isinstance(risk, RotationRisk) for risk in self.risks)
            or len({(risk.kind, risk.target_key) for risk in self.risks})
            != len(self.risks)
            or any(risk.target_key not in self.target_keys for risk in self.risks)
        ):
            raise ValueError(
                "Risk keys must be unique and belong to scheduled targets."
            )
        if (
            type(self.time_limit_seconds) not in (int, float)
            or not isfinite(self.time_limit_seconds)
            or self.time_limit_seconds <= 0
        ):
            raise ValueError("A solve stage requires a finite positive time limit.")

    @property
    def num_blocks(self) -> int:
        """Return the common number of time blocks.

        Args:
            None.

        Returns:
            Common positive number of time blocks in the validated current schedule.
        """
        return len(self.current[0].target_keys)

    @property
    def target_keys(self) -> tuple[str, ...]:
        """Return stable sorted identities used in the current schedule.

        Args:
            None.

        Returns:
            Sorted unique opaque target identities present in the current schedule.
        """
        return tuple(sorted({key for row in self.current for key in row.target_keys}))

    def risk_by_target(self, kind: AssessmentKind) -> dict[str, float]:
        """Return complete percentage coefficients or reject a missing measurement.

        Raises:
            ValueError: A tool is unsupported or any scheduled target lacks risk.

        Args:
            kind: Stable assessment model identity, independent of translated tool
                names.

        Returns:
            Complete target-to-probability mapping in percent (0-100), ready for the
            selected tool's optimizer.
        """
        if not isinstance(kind, AssessmentKind):
            raise ValueError("A supported assessment tool is required.")
        risks = {
            risk.target_key: risk.probability_percent
            for risk in self.risks
            if risk.kind == kind
        }
        if set(risks) != set(self.target_keys):
            raise ValueError(
                "Every scheduled target requires the selected tool's risk."
            )
        return risks

    def validate_schedule(self, schedule: tuple[WorkerRotation, ...]) -> None:
        """Check all original assignment constraints independently of solver status.

        Raises:
            ValueError: Workers/blocks/target totals change or a block repeats a target.

        Args:
            schedule: Candidate rows in original worker order, with one opaque target
                key per time block.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.
        """
        if (
            tuple(row.worker_id for row in schedule)
            != tuple(row.worker_id for row in self.current)
            or any(len(row.target_keys) != self.num_blocks for row in schedule)
            or Counter(key for row in schedule for key in row.target_keys)
            != Counter(key for row in self.current for key in row.target_keys)
            or any(
                len({row.target_keys[block] for row in schedule}) != len(schedule)
                for block in range(self.num_blocks)
            )
        ):
            raise ValueError("The solver schedule violates rotation constraints.")


@dataclass(frozen=True, slots=True)
class RotationSolution:
    """Validated schedule with backend and ordered stage termination evidence.

    OPTIMAL records the backend's report under the reference 1% relative gap, not a
    claim of exact global optimality. FEASIBLE means an incumbent was accepted without
    an optimal report. Multi-tool results retain both stages.

    Attributes:
        schedule: Validated replacement rows preserving workers, block shape, target
            totals and per-block exclusivity.
        backend: Explicit solver identity: CBC for single-tool, HiGHS for multi-tool; no
            automatic fallback.
        stages: Ordered backend termination statuses; optimal is subject to the
            configured relative-gap tolerance.
    """

    schedule: tuple[WorkerRotation, ...]
    backend: RotationBackend
    stages: tuple[RotationSolveStatus, ...]
