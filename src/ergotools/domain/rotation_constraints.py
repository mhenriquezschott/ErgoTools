"""Typed hard planning restrictions and frozen, explicit neighboring-run boundaries.

Domain layer. Exact worker/position identities are never display labels. A boundary
is copied evidence from a selected accepted run, not an inferred recurring Shift or
wrap. Live-source freshness and temporal ownership are checked by application
preparation.
"""

from dataclasses import dataclass
from datetime import datetime

from ergotools.domain.assessments.context import _require_identity
from ergotools.domain.rotation import RotationRisk


@dataclass(frozen=True, slots=True)
class FixedPosition:
    """Require one worker at one exact Job position throughout productive blocks.

    Attributes:
        worker_id: Exact participating worker.
        target_key: Exact selected Job/placement key.
    """

    worker_id: str
    target_key: str

    def __post_init__(self) -> None:
        """Reject blank identities without inferring a Job from a label.

        Args:
            None.

        Returns:
            None after identity validation.

        Raises:
            ValueError: Worker/position identity is missing.
        """
        _require_identity(self.worker_id, self.target_key)


@dataclass(frozen=True, slots=True)
class ExcludedPosition:
    """Forbid one exact worker/position pair in every productive block.

    Attributes:
        worker_id: Exact participating worker.
        target_key: Exact selected Job/placement key.
    """

    worker_id: str
    target_key: str

    def __post_init__(self) -> None:
        """Reject blank identities; contradiction checks belong to complete preparation.

        Args:
            None.

        Returns:
            None after validating literal identities.

        Raises:
            ValueError: Worker/position identity is missing.
        """
        _require_identity(self.worker_id, self.target_key)


@dataclass(frozen=True, slots=True)
class NoAdjacentHigh:
    """Forbid adjacent High positions for one worker, including requested boundaries.

    Attributes:
        worker_id: Exact participant; within-rotation checking is always active.
        previous: Also check the selected previous run's last block.
        following: Also check the selected following run's first block.
    """

    worker_id: str
    previous: bool = False
    following: bool = False

    def __post_init__(self) -> None:
        """Require explicit Boolean boundary intentions rather than truthy coercion.

        Args:
            None.

        Returns:
            None; missing requested neighbors remain incomplete draft intentions.

        Raises:
            ValueError: Identity or flags are invalid.
        """
        _require_identity(self.worker_id)
        if type(self.previous) is not bool or type(self.following) is not bool:
            raise ValueError("Boundary checking options must be Boolean.")


# New rule types require explicit adapters and validation.
type RotationRule = FixedPosition | ExcludedPosition | NoAdjacentHigh


@dataclass(frozen=True, slots=True)
class BoundaryExposure:
    """Frozen neighboring position and tool risks for one worker.

    Attributes:
        worker_id: Neighbor participant; it may be absent from the current rotation.
        target_key: Neighbor's opaque position identity, not a current target
        reference.
        risks: Exact frozen run probabilities; missing tools are never filled from
        live data.
    """

    worker_id: str
    target_key: str
    risks: tuple[RotationRisk, ...]

    def __post_init__(self) -> None:
        """Validate immutable unique tool evidence bound to the neighbor position.

        Args:
            None.

        Returns:
            None; no probability or classification is inferred.

        Raises:
            ValueError: Evidence has malformed or duplicated identities/tools.
        """
        _require_identity(self.worker_id, self.target_key)
        if (
            not isinstance(self.risks, tuple)
            or not self.risks
            or any(
                not isinstance(r, RotationRisk) or r.target_key != self.target_key
                for r in self.risks
            )
            or len({r.kind for r in self.risks}) != len(self.risks)
        ):
            raise ValueError(
                "Neighbor boundary requires unique frozen position/tool risks."
            )


@dataclass(frozen=True, slots=True)
class RotationBoundary:
    """Explicit neighboring-run identity and frozen boundary evidence.

    Attributes:
        scenario_id: Selected same-project scenario; missing/deleted sources become
        stale.
        run_signature: Exact canonical accepted-run signature, not a name or save
        timestamp.
        start: Naive local start datetime of that run; no timezone/DST inference.
        end: Naive local end datetime, including next-day meaning.
        workers: Last block for a previous neighbor, first block for a following
        neighbor.
    """

    scenario_id: str
    run_signature: str
    start: datetime
    end: datetime
    workers: tuple[BoundaryExposure, ...]

    def __post_init__(self) -> None:
        """Reject malformed temporal/worker evidence without reading a project.

        Args:
            None.

        Returns:
            None; application preparation checks the current referenced run
            separately.

        Raises:
            ValueError: Signature, local clocks or boundary collection is invalid.
        """
        _require_identity(self.scenario_id, self.run_signature)
        if (
            len(self.run_signature) != 64
            or any(c not in "0123456789abcdef" for c in self.run_signature)
            or type(self.start) is not datetime
            or type(self.end) is not datetime
            or self.start.tzinfo is not None
            or self.end.tzinfo is not None
            or self.end <= self.start
            or self.start.second
            or self.start.microsecond
            or self.end.second
            or self.end.microsecond
            or not isinstance(self.workers, tuple)
            or not self.workers
            or any(not isinstance(w, BoundaryExposure) for w in self.workers)
            or len({w.worker_id for w in self.workers}) != len(self.workers)
        ):
            raise ValueError("Invalid fixed neighboring-run boundary context.")
