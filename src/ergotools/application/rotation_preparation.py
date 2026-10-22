"""Prepare solver inputs from exact scheduled current Job values.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from ergotools.application.rotation_pool import RotationPool
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation import RotationProblem, RotationRisk
from ergotools.domain.rotation_scheme import RotationScheme


def prepare_rotation_problem(
    scheme: RotationScheme,
    pool: RotationPool,
    kinds: tuple[AssessmentKind, ...],
    *,
    time_limit_seconds: float,
) -> RotationProblem:
    """Freeze scheduled probabilities in percent without conversion or writes.

    Zero is valid. Only scheduled targets require measurements; unused pool jobs do not
    block a solve. Job, placement and project identities must match.

    Args:
        scheme: Validated schedule with exact frozen targets and period assignments.
        pool: Same-project choices retaining current Job values and exact placement
            identities.
        kinds: Nonempty unique model identities required by the requested solve.
        time_limit_seconds: Solver time budget in seconds, validated by RotationProblem.

    Returns:
        Plain solver problem with scheduled target risks on the 0-100 percent scale; no
        measurement or schedule is changed.

    Raises:
        ValueError: Ownership, exact scheduled evidence, tool uniqueness, required
            probabilities or time budget is invalid.
    """
    if (
        scheme.project_id != pool.project_id
        or not kinds
        or len(set(kinds)) != len(kinds)
    ):
        raise ValueError("Optimization requires matching ownership and unique tools.")
    choices = {choice.target.key: choice for choice in pool.targets}
    risks = []
    for target in scheme.targets:
        choice = choices.get(target.key)
        if choice is None or choice.target != target:
            raise ValueError("Optimization requires the current scheduled Job values.")
        for kind in kinds:
            measurement = next(
                (item for item in choice.values.measurements if item.kind is kind),
                None,
            )
            if (
                measurement is None
                or not measurement.complete
                or measurement.probability_percent is None
            ):
                raise ValueError(
                    "Every scheduled target requires the selected tool's risk."
                )
            risks.append(
                RotationRisk(target.key, kind, measurement.probability_percent)
            )
    return RotationProblem(scheme.current, tuple(risks), time_limit_seconds)
