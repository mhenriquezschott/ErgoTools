"""Duration-weighted planning contract and independent hard-rule result validation.

Domain layer. Scores are time-weighted Job-risk indices, not individual injury
probabilities or dose/recovery calculations. Observations are optional and never
seeds invented by this model. Staffing/rules are validated independently of any
solver status.
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from math import isfinite

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.risk import RiskBand, classify_probability
from ergotools.domain.rotation import RotationRisk, WorkerRotation
from ergotools.domain.rotation_constraints import (
    ExcludedPosition,
    FixedPosition,
    NoAdjacentHigh,
)
from ergotools.domain.rotation_scenario import RotationInputs, complete_rotation_rows


def rotation_interval(inputs: RotationInputs) -> tuple[datetime, datetime]:
    """Resolve complete naive local start/end without guessing dates or DST offsets.

    Args:
        inputs: Accepted local date and independent copied clock/timing.

    Returns:
        Positive local daily interval, including overnight meaning.

    Raises:
        ValueError: Date, start or timing is unentered.
    """
    if (
        inputs.planned_date is None
        or inputs.start_minute is None
        or inputs.timing is None
    ):
        raise ValueError("Set the rotation date and complete copied timing first.")
    start = datetime.combine(inputs.planned_date, time()) + timedelta(
        minutes=inputs.start_minute
    )
    return start, start + timedelta(minutes=inputs.timing.shift_minutes)


def allowed_positions(inputs: RotationInputs) -> dict[str, frozenset[str]]:
    """Check rule consistency and static perfect staffing using exact identities.

    Args:
        inputs: Selected workers/positions and typed restrictions.

    Returns:
        Allowed positions per worker; no assignments or baseline are generated.

    Raises:
        ValueError: Rules conflict, counts differ, or no complete matching exists.
    """
    keys = {t.key for t in inputs.targets}
    if not inputs.workers or len(inputs.workers) != len(keys):
        raise ValueError("Select exactly one worker per Job position.")
    allowed = {w.worker_id: set(keys) for w in inputs.workers}
    fixed: dict[str, str] = {}
    for rule in inputs.rules:
        if isinstance(rule, FixedPosition):
            if rule.worker_id in fixed and fixed[rule.worker_id] != rule.target_key:
                raise ValueError("A worker cannot be fixed to different Job positions.")
            fixed[rule.worker_id] = rule.target_key
        elif isinstance(rule, ExcludedPosition):
            allowed[rule.worker_id].discard(rule.target_key)
    for worker, key in fixed.items():
        allowed[worker].intersection_update({key})
    matching: dict[str, str] = {}

    def augment(worker: str, visited: set[str]) -> bool:
        """Find one alternating staffing path without solver or project dependencies.

        Args:
            worker: Current unmatched exact participant.
            visited: Positions already visited by this augmentation.

        Returns:
            True if this worker can be matched while retaining other matches.
        """
        for key in sorted(allowed[worker] - visited):
            visited.add(key)
            if key not in matching or augment(matching[key], visited):
                matching[key] = worker
                return True
        return False

    if not all(augment(w.worker_id, set()) for w in inputs.workers):
        raise ValueError(
            "Fixed/excluded positions cannot staff every Job exactly once."
        )
    return {worker: frozenset(values) for worker, values in allowed.items()}


@dataclass(frozen=True, slots=True)
class RotationPlanningProblem:
    """Frozen solve inputs with explicit weights, tool subset and hard restrictions.

    Attributes:
        inputs: Dated/timed plan; observed/proposed rows remain explicit user data.
        risks: Available frozen selected-tool Job probabilities, never invented
        zeros.
        time_limit_seconds: Positive per-stage budget; multi-tool stages each
        receive it.
        generation: True solves feasibility only, not risk minimization.
    """

    inputs: RotationInputs
    risks: tuple[RotationRisk, ...]
    time_limit_seconds: float = 60.0
    generation: bool = False

    def __post_init__(self) -> None:
        """Validate planning context, staffing and selected-tool evidence.

        Args:
            None.

        Returns:
            None; static contradictions fail before invoking any backend.

        Raises:
            ValueError: Inputs, coefficients, neighboring contexts or budgets are
            invalid.
        """
        if (
            not isinstance(self.inputs, RotationInputs)
            or type(self.generation) is not bool
        ):
            raise ValueError(
                "Use typed planning inputs and an explicit generation mode."
            )
        start, end = rotation_interval(self.inputs)
        allowed_positions(self.inputs)
        if (
            type(self.time_limit_seconds) not in (float, int)
            or not isfinite(self.time_limit_seconds)
            or self.time_limit_seconds <= 0
        ):
            raise ValueError("A solve stage requires a finite positive time limit.")
        if (
            not isinstance(self.risks, tuple)
            or any(not isinstance(r, RotationRisk) for r in self.risks)
            or len({(r.target_key, r.kind) for r in self.risks}) != len(self.risks)
            or any(
                r.target_key not in self.target_keys or r.kind not in self.inputs.tools
                for r in self.risks
            )
        ):
            raise ValueError(
                "Planning coefficients must have unique selected position/tool keys."
            )
        needs_risks = not self.generation or any(
            isinstance(r, NoAdjacentHigh) for r in self.inputs.rules
        )
        if needs_risks:
            for kind in self.inputs.tools:
                self.risk_by_target(kind)
        if self.inputs.baseline is not None:
            self.validate_schedule(
                complete_rotation_rows(self.inputs.baseline), check_rules=False
            )
        if not self.generation and self.inputs.proposed is not None:
            self.validate_schedule(
                complete_rotation_rows(self.inputs.proposed), check_rules=False
            )
        for boundary, previous in (
            (self.inputs.previous, True),
            (self.inputs.following, False),
        ):
            requested = any(
                isinstance(r, NoAdjacentHigh)
                and (r.previous if previous else r.following)
                for r in self.inputs.rules
            )
            if requested and boundary is None:
                raise ValueError(
                    "Requested cross-shift boundary is not checked: select a "
                    "usable neighboring run."
                )
            if boundary is not None and (
                boundary.end > start if previous else boundary.start < end
            ):
                raise ValueError(
                    "Neighboring rotations overlap or have the wrong temporal order."
                )
            if requested and boundary is not None:
                for exposure in boundary.workers:
                    if exposure.worker_id in self.worker_ids and any(
                        isinstance(r, NoAdjacentHigh)
                        and r.worker_id == exposure.worker_id
                        and (r.previous if previous else r.following)
                        for r in self.inputs.rules
                    ):
                        self.boundary_high(exposure.worker_id, previous=previous)

    @property
    def worker_ids(self) -> tuple[str, ...]:
        """Read exact participant order without creating assignment rows.

        Args:
            None.

        Returns:
            Stable worker identities used by extraction and independent validation.
        """
        return tuple(w.worker_id for w in self.inputs.workers)

    @property
    def target_keys(self) -> tuple[str, ...]:
        """Read exact selected positions, including repeated Job placements.

        Args:
            None.

        Returns:
            Ordered unique opaque position identities.
        """
        return tuple(t.key for t in self.inputs.targets)

    @property
    def num_blocks(self) -> int:
        """Read positive productive block count from validated copied timing.

        Args:
            None.

        Returns:
            Number of assignment periods; breaks create no assignment slots.
        """
        assert self.inputs.timing is not None
        return len(self.inputs.timing.block_minutes)

    def risk_by_target(self, kind: AssessmentKind) -> dict[str, float]:
        """Require real complete probabilities for one selected analysis model.

        Args:
            kind: Selected scientific tool.

        Returns:
            Exact frozen percentages, with real zero retained.

        Raises:
            ValueError: A selected coefficient is unavailable or the tool is
            unselected.
        """
        values = {
            r.target_key: r.probability_percent for r in self.risks if r.kind is kind
        }
        if kind not in self.inputs.tools or set(values) != set(self.target_keys):
            raise ValueError(
                "Every selected Job requires complete selected-tool values."
            )
        return values

    def high_positions(self) -> frozenset[str]:
        """Classify High using any selected tool and the existing category boundaries.

        Args:
            None.

        Returns:
            Exact positions above the existing High threshold; 50 is not High.
        """
        risks = [self.risk_by_target(k) for k in self.inputs.tools]
        return frozenset(
            key
            for key in self.target_keys
            if any(classify_probability(r[key]) is RiskBand.HIGH for r in risks)
        )

    def boundary_high(self, worker: str, *, previous: bool) -> bool:
        """Read a frozen neighbor coefficient only for the same worker on both sides.

        Args:
            worker: Exact current worker identity.
            previous: True uses the previous last block; False the following first
            block.

        Returns:
            False for workers absent from that side; otherwise selected-tool High
            status.

        Raises:
            ValueError: A requested boundary or its matching-worker tool evidence is
            missing.
        """
        boundary = self.inputs.previous if previous else self.inputs.following
        if boundary is None:
            raise ValueError("Requested neighboring-run boundary is unavailable.")
        row = next((w for w in boundary.workers if w.worker_id == worker), None)
        if row is None:
            return False
        values = {r.kind: r.probability_percent for r in row.risks}
        if not set(self.inputs.tools) <= values.keys():
            raise ValueError(
                "Neighbor run lacks a selected tool; this boundary is not checked."
            )
        return any(
            classify_probability(values[k]) is RiskBand.HIGH for k in self.inputs.tools
        )

    def validate_schedule(
        self, schedule: tuple[WorkerRotation, ...], *, check_rules: bool = True
    ) -> None:
        """Independently verify staffing and all supported hard restrictions.

        Args:
            schedule: Complete candidate; no solver values or statuses are trusted.
            check_rules: False validates observation/proposal staffing, not new
            restrictions.

        Returns:
            None only for an exact feasible assignment under the requested checks.

        Raises:
            ValueError: Candidate shape, staffing or any active hard rule is
            violated.
        """
        if (
            not isinstance(schedule, tuple)
            or any(not isinstance(r, WorkerRotation) for r in schedule)
            or tuple(r.worker_id for r in schedule) != self.worker_ids
            or any(len(r.target_keys) != self.num_blocks for r in schedule)
            or any(
                {r.target_keys[b] for r in schedule} != set(self.target_keys)
                for b in range(self.num_blocks)
            )
        ):
            raise ValueError(
                "Schedule must staff every position exactly once in every block."
            )
        if not check_rules:
            return
        allowed = allowed_positions(self.inputs)
        high = (
            self.high_positions()
            if any(isinstance(r, NoAdjacentHigh) for r in self.inputs.rules)
            else frozenset()
        )
        for row in schedule:
            if any(key not in allowed[row.worker_id] for key in row.target_keys):
                raise ValueError("Schedule violates a fixed/excluded worker position.")
            for rule in self.inputs.rules:
                if (
                    not isinstance(rule, NoAdjacentHigh)
                    or rule.worker_id != row.worker_id
                ):
                    continue
                if any(
                    a in high and b in high
                    for a, b in zip(row.target_keys, row.target_keys[1:], strict=False)
                ):
                    raise ValueError("Schedule contains consecutive High positions.")
                if (
                    rule.previous
                    and self.boundary_high(row.worker_id, previous=True)
                    and row.target_keys[0] in high
                ) or (
                    rule.following
                    and self.boundary_high(row.worker_id, previous=False)
                    and row.target_keys[-1] in high
                ):
                    raise ValueError("Schedule violates a cross-shift High boundary.")

    def scores(
        self, schedule: tuple[WorkerRotation, ...], kind: AssessmentKind
    ) -> tuple[float, ...]:
        """Calculate weighted indices without a dose or recovery model.

        Args:
            schedule: Complete staffed schedule, possibly the observed
            rule-violating one.
            kind: Selected tool whose probabilities define this index.

        Returns:
            Unrounded worker indices in percentage points; breaks receive no
            assignments.
        """
        self.validate_schedule(schedule, check_rules=False)
        risks = self.risk_by_target(kind)
        assert self.inputs.timing is not None
        return tuple(
            sum(
                minutes * risks[key]
                for minutes, key in zip(
                    self.inputs.timing.block_minutes, row.target_keys, strict=True
                )
            )
            / self.inputs.timing.averaging_minutes
            for row in schedule
        )
