"""Named rotation plans and immutable accepted-run context, independent of solving.

Domain layer. Drafts may be incomplete; old dates/timings remain unknown. A run
freezes its complete planning inputs, Job source/results and displayed labels.
Renaming a plan cannot change that run; editing its scientific inputs makes it stale
rather than silently combining an old solution with new coefficients. This module
never runs an optimizer.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from ergotools.domain.assessments.context import WorkplaceContext, _require_identity
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.rotation import (
    RotationBackend,
    RotationSolveStatus,
    WorkerRotation,
)
from ergotools.domain.rotation_constraints import (
    ExcludedPosition,
    FixedPosition,
    NoAdjacentHigh,
    RotationBoundary,
    RotationRule,
)
from ergotools.domain.rotation_scheme import (
    RotationMode,
    RotationTarget,
    RotationWorkerLink,
)
from ergotools.domain.rotation_timing import RotationTiming
from ergotools.domain.work_hierarchy import LineKey, WorkHierarchy

# Current planning-contract identity. Unknown positive versions remain readable
# evidence but cannot be accepted as current supported results.
ROTATION_RUN_MODEL_VERSION = 2


@dataclass(frozen=True, slots=True)
class RotationDraftRow:
    """One incomplete entered row, distinct from no observed schedule.

    Attributes:
        worker_id: Exact participating worker identity.
        target_keys: Position IDs or None for unfinished cells; never fake Jobs.
    """

    worker_id: str
    target_keys: tuple[str | None, ...]

    def __post_init__(self) -> None:
        """Require typed positive horizon while retaining explicit unentered cells.

        Args:
            None.

        Returns:
            None; partial rows are editable data, never solver-ready assignments.

        Raises:
            ValueError: Worker, collection or present target identity is invalid.
        """
        _require_identity(self.worker_id)
        if (
            not isinstance(self.target_keys, tuple)
            or not self.target_keys
            or any(
                k is not None and (not isinstance(k, str) or not k.strip())
                for k in self.target_keys
            )
        ):
            raise ValueError(
                "Draft schedule cells require a position identity or None."
            )


def complete_rotation_rows(
    rows: tuple[WorkerRotation | RotationDraftRow, ...],
) -> tuple[WorkerRotation, ...]:
    """Require complete entered cells before producing any solver-ready rows.

    Args:
        rows: Immutable complete/incomplete entered schedule, not an absent baseline.

    Returns:
        Complete rows with original order/identities; no assignments are guessed.

    Raises:
        ValueError: A row is unfinished or has an unsupported type.
    """
    complete = []
    for row in rows:
        if not isinstance(row, WorkerRotation | RotationDraftRow) or any(
            k is None for k in row.target_keys
        ):
            raise ValueError("Complete every entered schedule cell before optimizing.")
        complete.append(
            WorkerRotation(
                row.worker_id, tuple(k for k in row.target_keys if k is not None)
            )
        )
    return tuple(complete)


@dataclass(frozen=True, slots=True)
class RotationInputs:
    """Independent scenario draft; no live link to a Shift timing template.

    Attributes:
        planned_date: Local start date; None for an unresolved older rotation.
        line: Optional exact Plant/Section/Line identity for guided workplace entry.
        shift_id: Optional existing project-wide Shift identity.
        start_minute: Copied local clock origin, 0-1439; paired with timing.
        timing: Copied relative work/break plan; None remains explicitly untimed.
        workers: Ordered participating workers with optional original assignment
        links.
        targets: Unique participating Job/placement positions.
        tools: Ordered nonempty selected tool subset, without duplicate models.
        baseline: Existing observed or explicitly promoted reference rows, or None.
            Automatic feasibility generation never populates this field.
        proposed: Optional full/partial proposed rows, separate from observation.
        scope: Exact station/shift scope retained from current workplace selections.
        rules: Typed active hard restrictions; incomplete boundary intentions may
        remain.
        previous: Explicit frozen previous-run last-block context, or none.
        following: Explicit frozen following-run first-block context, or none.
    """

    planned_date: date | None = None
    line: LineKey | None = None
    shift_id: str | None = None
    start_minute: int | None = None
    timing: RotationTiming | None = None
    workers: tuple[RotationWorkerLink, ...] = ()
    targets: tuple[RotationTarget, ...] = ()
    tools: tuple[AssessmentKind, ...] = tuple(AssessmentKind)
    baseline: tuple[WorkerRotation | RotationDraftRow, ...] | None = None
    proposed: tuple[WorkerRotation | RotationDraftRow, ...] | None = None
    scope: tuple[WorkplaceContext, ...] = ()
    rules: tuple[RotationRule, ...] = ()
    previous: RotationBoundary | None = None
    following: RotationBoundary | None = None

    def __post_init__(self) -> None:
        """Reject malformed types, identities and partial copied clock pairs.

        Args:
            None.

        Returns:
            None; structurally valid incomplete drafts remain representable.

        Raises:
            ValueError: Dates, clocks, collections, identity or schedule shape is
                invalid.
        """
        if self.planned_date is not None and type(self.planned_date) is not date:
            raise ValueError("Rotation date must be a local calendar date or unknown.")
        if self.line is not None and not isinstance(self.line, LineKey):
            raise ValueError("Rotation Line requires its complete hierarchy identity.")
        if self.shift_id is not None:
            _require_identity(self.shift_id)
        if (self.start_minute is None) != (self.timing is None) or (
            self.start_minute is not None
            and (
                type(self.start_minute) is not int
                or not 0 <= self.start_minute < 1440
                or not isinstance(self.timing, RotationTiming)
            )
        ):
            raise ValueError(
                "Rotation clock and timing must be a complete copied pair."
            )
        for values, kind in (
            (self.workers, RotationWorkerLink),
            (self.targets, RotationTarget),
            (self.tools, AssessmentKind),
            (self.scope, WorkplaceContext),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(v, kind) for v in values
            ):
                raise ValueError(
                    "Rotation collections require immutable typed records."
                )
        if (
            not self.tools
            or len(set(self.tools)) != len(self.tools)
            or len({w.worker_id for w in self.workers}) != len(self.workers)
            or len({t.key for t in self.targets}) != len(self.targets)
            or len(set(self.scope)) != len(self.scope)
            or len({c.shift_id for c in self.scope}) > 1
            or (self.scope and self.shift_id not in (None, self.scope[0].shift_id))
        ):
            raise ValueError("Rotation participant, tool or scope identities disagree.")
        if (
            not isinstance(self.rules, tuple)
            or any(
                type(r) not in (FixedPosition, ExcludedPosition, NoAdjacentHigh)
                for r in self.rules
            )
            or len(set(self.rules)) != len(self.rules)
            or any(
                r.worker_id not in {w.worker_id for w in self.workers}
                for r in self.rules
            )
            or any(
                isinstance(r, (FixedPosition, ExcludedPosition))
                and r.target_key not in {t.key for t in self.targets}
                for r in self.rules
            )
            or any(
                v is not None and not isinstance(v, RotationBoundary)
                for v in (self.previous, self.following)
            )
        ):
            raise ValueError(
                "Unsupported or incompatible active rotation restrictions."
            )
        for field in ("baseline", "proposed"):
            rows = getattr(self, field)
            if rows is not None:
                self.validate_schedule(rows)
                # Canonical complete rows retain the existing solver/domain record.
                if all(k is not None for row in rows for k in row.target_keys):
                    object.__setattr__(self, field, complete_rotation_rows(rows))

    def validate_schedule(
        self, rows: tuple[WorkerRotation | RotationDraftRow, ...]
    ) -> None:
        """Check schedule identities/horizon without claiming staffing feasibility.

        Args:
            rows: Ordered entered rows for every worker; explicit None cells may remain.

        Returns:
            None for valid shape; drafts may still need staffing/rule validation.

        Raises:
            ValueError: Worker order, target ownership or block count differs.
        """
        if rows == () and not self.workers:
            return
        if (
            not isinstance(rows, tuple)
            or not rows
            or any(not isinstance(r, WorkerRotation | RotationDraftRow) for r in rows)
            or tuple(r.worker_id for r in rows)
            != tuple(w.worker_id for w in self.workers)
            or len({len(r.target_keys) for r in rows}) != 1
            or any(
                k is not None and k not in {t.key for t in self.targets}
                for r in rows
                for k in r.target_keys
            )
            or (
                self.timing is not None
                and len(rows[0].target_keys) != len(self.timing.block_minutes)
            )
        ):
            raise ValueError(
                "Rotation schedule does not match its participants or timing."
            )

    def validate_references(self, hierarchy: WorkHierarchy, jobs: JobCatalog) -> None:
        """Protect current draft references without re-reading copied clocks or risks.

        Args:
            hierarchy: Proposed same-project hierarchy, including inactive parents.
            jobs: Proposed complete Job/placement/assignment catalog.

        Returns:
            None; Shift template edits cannot mutate copied timing.

        Raises:
            ValueError: Referenced workers, Line, Shift, placement or scope is missing.
        """
        if jobs.project_id != hierarchy.work.project_id:
            raise ValueError("Rotation catalogs belong to different projects.")
        if self.line is not None and self.line not in hierarchy.lines:
            raise ValueError("Rotation references a missing Line.")
        if self.shift_id is not None and self.shift_id not in hierarchy.work.shifts:
            raise ValueError("Rotation references a missing Shift.")
        contexts = {
            s.at_shift(shift)
            for s in hierarchy.work.stations
            for shift in hierarchy.work.shifts
        }
        if not set(self.scope) <= contexts:
            raise ValueError("Rotation references a missing workplace.")
        worker_ids = {w.worker_id for w in hierarchy.work.workers}
        assignments = {a.assignment_id: a for a in jobs.assignments}
        placements = {p.placement_id: p for p in jobs.placements}
        job_ids = {j.job_id for j in jobs.jobs}
        for worker in self.workers:
            assignment = (
                assignments.get(worker.assignment_id)
                if worker.assignment_id is not None
                else None
            )
            if worker.worker_id not in worker_ids or (
                worker.assignment_id is not None
                and (
                    assignment is None
                    or assignment.worker.worker_id != worker.worker_id
                    or (self.scope and assignment.worker.workplace not in self.scope)
                )
            ):
                raise ValueError(
                    "Rotation references a missing or incompatible worker."
                )
        for target in self.targets:
            placement = (
                placements.get(target.placement_id)
                if target.placement_id is not None
                else None
            )
            if target.job_id not in job_ids or (
                target.placement_id is not None
                and (
                    placement is None
                    or placement.job_id != target.job_id
                    or (self.scope and placement.workplace not in self.scope)
                )
            ):
                raise ValueError("Rotation references a missing or incompatible Job.")


@dataclass(frozen=True, slots=True)
class RotationCoefficient:
    """Frozen Job input/result and label for one target/model at solve time.

    Attributes:
        target_key: Exact participating position identity.
        job_name: Literal displayed Job label frozen independently of later renames.
        measurement: Complete source-bound Job values; source may be absent for direct
            entry.
        task_names: Frozen displayed task labels, independent of reusable catalog
            renames.
    """

    target_key: str
    job_name: str
    measurement: JobRiskMeasurement
    task_names: tuple[str | None, ...] = ()

    def __post_init__(self) -> None:
        """Require explicit complete coefficient evidence without recalculating it.

        Args:
            None.

        Returns:
            None; zero probability remains valid, missing probability is rejected.

        Raises:
            ValueError: Identity, label or measurement is incomplete.
        """
        _require_identity(self.target_key, self.job_name)
        if (
            not isinstance(self.measurement, JobRiskMeasurement)
            or not self.measurement.complete
        ):
            raise ValueError("Run coefficients require complete Job values.")
        if (
            not isinstance(self.task_names, tuple)
            or len(self.task_names)
            != (
                len(self.measurement.source.tasks)
                if self.measurement.source is not None
                else 0
            )
            or any(
                n is not None and (not isinstance(n, str) or not n.strip())
                for n in self.task_names
            )
        ):
            raise ValueError("Frozen task labels must match the Job source rows.")


@dataclass(frozen=True, slots=True)
class RotationRun:
    """Immutable accepted result context; construction does not prove optimality.

    Attributes:
        inputs: Complete copied planning inputs used for this accepted run.
        coefficients: Exact selected-tool Job sources/results and labels.
        arrangement: Accepted worker/position matrix, separate from observed baseline.
        backend: Recorded solver provenance, including historical one-pass records.
            New guided runs use HiGHS with two passes; original single-tool
            results may retain one pass.
        stages: Actual pass statuses. Historical single-tool runs retain one pass;
            new optimizations record two. Numeric/gap qualifications still apply.
        settings: Explicit solver/model settings as unique key/value text, not
            instructions.
        completed_at: Aware UTC timestamp, independent of the rotation's local date.
        contract_version: Positive planning-model version; this is not a DB format
            version.
        worker_labels: Ordered literal labels used for the participating worker IDs.
    """

    inputs: RotationInputs
    coefficients: tuple[RotationCoefficient, ...]
    arrangement: tuple[WorkerRotation, ...]
    backend: RotationBackend
    stages: tuple[RotationSolveStatus, ...]
    settings: tuple[tuple[str, str], ...]
    completed_at: datetime
    contract_version: int
    worker_labels: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject incomplete context and unstaffed matrices without solving.

        Args:
            None.

        Returns:
            None; every saved outcome can retain its original displayed evidence.

        Raises:
            ValueError: Context, coefficients, timestamp or arrangement is inconsistent.
        """
        if not isinstance(self.inputs, RotationInputs):
            raise ValueError("Run requires typed planning inputs.")
        if not self.arrangement:
            raise ValueError("An accepted run requires participating workers.")
        self.inputs.validate_schedule(self.arrangement)
        complete_rotation_rows(self.arrangement)
        for entered in (self.inputs.baseline, self.inputs.proposed):
            if entered is not None:
                complete_rotation_rows(entered)
        if (
            self.inputs.planned_date is None
            or self.inputs.timing is None
            or len(self.inputs.workers) != len(self.inputs.targets)
            or any(
                set(r.target_keys[b] for r in self.arrangement)
                != {t.key for t in self.inputs.targets}
                for b in range(len(self.arrangement[0].target_keys))
            )
            or any(not isinstance(row, WorkerRotation) for row in self.arrangement)
            or not isinstance(self.coefficients, tuple)
            or any(not isinstance(c, RotationCoefficient) for c in self.coefficients)
            or len(self.coefficients)
            != len(self.inputs.targets) * len(self.inputs.tools)
            or {(c.target_key, c.measurement.kind) for c in self.coefficients}
            != {(t.key, k) for t in self.inputs.targets for k in self.inputs.tools}
            or not isinstance(self.backend, RotationBackend)
            or (
                len(self.inputs.tools) > 1 and self.backend is not RotationBackend.HIGHS
            )
            or not isinstance(self.stages, tuple)
            or len(self.stages) not in ((1, 2) if len(self.inputs.tools) == 1 else (2,))
            or any(not isinstance(s, RotationSolveStatus) for s in self.stages)
            or not isinstance(self.completed_at, datetime)
            or self.completed_at.utcoffset() != timedelta(0)
            or type(self.contract_version) is not int
            or self.contract_version < 1
            or not isinstance(self.worker_labels, tuple)
            or len(self.worker_labels) != len(self.inputs.workers)
            or any(not isinstance(s, str) or not s.strip() for s in self.worker_labels)
            or not isinstance(self.settings, tuple)
            or not self.settings
            or any(
                not isinstance(pair, tuple)
                or len(pair) != 2
                or any(not isinstance(v, str) or not v.strip() for v in pair)
                for pair in self.settings
            )
            or len({p[0] for p in self.settings}) != len(self.settings)
        ):
            raise ValueError(
                "Run requires a complete timed, staffed and frozen context."
            )


@dataclass(frozen=True, slots=True)
class RotationScenario:
    """One independent named plan with an optional retained accepted run.

    Attributes:
        project_id: Stable owning project identity.
        scenario_id: Immutable scenario identity, never inferred from its name.
        name: Editable nonblank display label; repeated names do not merge records.
        inputs: Current independent planning inputs, possibly incomplete.
        description: Optional literal user text.
        source_scenario_id: Optional duplicate-source identity. It remains meaningful
            after deletion, so this is provenance rather than a live foreign key.
        run: Last accepted immutable result; may be stale relative to edited current
            inputs.
        legacy_mode: Retained older scheme provenance, never a fabricated accepted run.
        legacy_primary_kind: Retained primary model only for older single-tool
            provenance.
    """

    project_id: str
    scenario_id: str
    name: str
    inputs: RotationInputs
    description: str | None = None
    source_scenario_id: str | None = None
    run: RotationRun | None = None
    legacy_mode: RotationMode | None = None
    legacy_primary_kind: AssessmentKind | None = None

    def __post_init__(self) -> None:
        """Validate current data while retaining unknown dates and prior evidence.

        Args:
            None.

        Returns:
            None; draft edits and immutable run evidence remain separate.

        Raises:
            ValueError: Identity, description, duplicate provenance or run type is
                invalid.
        """
        _require_identity(self.project_id, self.scenario_id, self.name)
        if (
            not isinstance(self.inputs, RotationInputs)
            or (self.description is not None and not isinstance(self.description, str))
            or (self.run is not None and not isinstance(self.run, RotationRun))
        ):
            raise ValueError("Invalid rotation scenario data.")
        if self.legacy_primary_kind is not None and not isinstance(
            self.legacy_primary_kind, AssessmentKind
        ):
            raise ValueError("Invalid retained older rotation primary tool.")
        if (
            self.legacy_mode is not None
            and not isinstance(self.legacy_mode, RotationMode)
        ) or (
            (self.legacy_mode is RotationMode.SINGLE_TOOL)
            != isinstance(self.legacy_primary_kind, AssessmentKind)
        ):
            raise ValueError("Invalid retained older rotation provenance.")
        if self.source_scenario_id is not None:
            _require_identity(self.source_scenario_id)
            if self.source_scenario_id == self.scenario_id:
                raise ValueError("A rotation cannot be its own duplicate source.")

    @property
    def run_matches_inputs(self) -> bool:
        """Compare current planning inputs with retained run context.

        Args:
            None.

        Returns:
            True only for an existing run of these exact current planning inputs.
        """
        return self.run is not None and self.run.inputs == self.inputs
