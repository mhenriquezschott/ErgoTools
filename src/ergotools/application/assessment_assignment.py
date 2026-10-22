"""Pure assignment lookup for an explicitly scoped assessment workplace.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from ergotools.domain.assessments.context import WorkerContext


@dataclass(frozen=True, slots=True)
class AssignmentSnapshot:
    """Assignment identity and eligibility copied from a repository snapshot.

    The adapter validates placement/context consistency and supplies exact booleans. Job
    activity and date ranges do not determine reference lookup eligibility.

    Attributes:
        worker: Exact project, worker and workplace ownership.
        assignment_id: Stable integer assignment identity; never a row position.
        active: Whether this assignment is active.
        job_placement_id: Exact linked placement identity, or None for unclassified
            ownership.
        placement_active: Whether that placement is active; does not imply job activity.
    """

    worker: WorkerContext
    assignment_id: int
    active: bool
    job_placement_id: int | None
    placement_active: bool

    def __post_init__(self) -> None:
        """Reject ambiguous flags and untyped database identities.

        Args:
            None.

        Returns:
            None; validate the constructed snapshot.

        Raises:
            ValueError: Worker context, integer identities or exact boolean activity
                flags are invalid.
        """
        if not isinstance(self.worker, WorkerContext):
            raise ValueError("Assignment requires a typed worker context.")
        if type(self.assignment_id) is not int or (
            self.job_placement_id is not None and type(self.job_placement_id) is not int
        ):
            raise ValueError("Assignment and placement IDs must be integers.")
        if type(self.active) is not bool or type(self.placement_active) is not bool:
            raise ValueError("Assignment activity flags must be booleans.")


def resolve_assessment_assignment(
    worker: WorkerContext, assignments: Iterable[AssignmentSnapshot]
) -> AssignmentSnapshot | None:
    """Find the eligible assignment for one exact project/worker/workplace.

    An inactive assignment, absent placement or inactive placement yields no match.
    Multiple active assignments for this owner raise ValueError, even when only one has
    an eligible placement: the reference schema forbids that state. Never choose an
    arbitrary row from corrupt or merged snapshots. This function performs no I/O and
    cannot change assessment ownership.

    Args:
        worker: Exact project, worker and workplace owner to resolve.
        assignments: Borrowed immutable assignment snapshots; consumed once without
            mutation.

    Returns:
        The sole active owner assignment when it has an active placement; otherwise
        None.

    Raises:
        ValueError: The owner is untyped or multiple active assignments match, even if
            only one placement is eligible.
    """
    if not isinstance(worker, WorkerContext):
        raise ValueError("Lookup requires a typed worker context.")
    selected: AssignmentSnapshot | None = None
    for assignment in assignments:
        if assignment.worker != worker or not assignment.active:
            continue
        if selected is not None:
            raise ValueError("Multiple active assignments for one worker context.")
        selected = assignment
    if (
        selected is None
        or selected.job_placement_id is None
        or not selected.placement_active
    ):
        return None
    return selected
