"""Saved JROT schemes with exact worker, placement and Job ownership.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass
from enum import StrEnum

from ergotools.domain.assessments.context import WorkplaceContext, _require_identity
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.work_hierarchy import WorkHierarchy


class RotationMode(StrEnum):
    """Reference scheme provenance, independent of the current display tool."""

    # Scheme saved from manual/current assignments.
    MANUAL = "manual"
    # Scheme records optimization for one explicit primary tool.
    SINGLE_TOOL = "single_tool"
    # Scheme records multi-tool optimization with no single primary tool.
    ALL_TOOLS = "all_tools"


@dataclass(frozen=True, slots=True)
class RotationWorkerLink:
    """Worker identity and optional original assignment, including closed history.

    Attributes:
        worker_id: Literal saved worker identity; names never establish ownership.
        assignment_id: Optional exact original assignment ID; None is allowed in
            organization-wide schemes.
    """

    worker_id: str
    assignment_id: int | None = None

    def __post_init__(self) -> None:
        """Require exact text identity and a typed assignment ID when present.

        Args:
            None. Dataclass construction supplies the fields documented on
            RotationWorkerLink.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Rotation assignment identity requires an integer.
        """
        _require_identity(self.worker_id)
        if self.assignment_id is not None and type(self.assignment_id) is not int:
            raise ValueError("Rotation assignment identity requires an integer.")


@dataclass(frozen=True, slots=True)
class RotationTarget:
    """Exact Job/placement identity referencing current Job values.

    Attributes:
        job_id: Literal saved job identity, independent of the displayed job name.
        placement_id: Exact job-placement identity; None means an unclassified
            assignment or an unplaced rotation target.
    """

    job_id: str
    placement_id: int | None = None

    def __post_init__(self) -> None:
        """Reject implicit numeric identities before catalog validation.

        Args:
            None. Dataclass construction supplies the fields documented on
            RotationTarget.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Rotation target identities require integers.
        """
        _require_identity(self.job_id)
        if self.placement_id is not None and type(self.placement_id) is not int:
            raise ValueError("Rotation placement identity requires an integer.")

    @property
    def key(self) -> str:
        """Return an unambiguous opaque solver key without label sanitization.

        Args:
            None.

        Returns:
            Length-prefixed Job/placement identity; consumers must treat it as
            opaque, never as a display label.
        """
        return f"{len(self.job_id)}:{self.job_id}:{self.placement_id}"


@dataclass(frozen=True, slots=True)
class RotationScheme:
    """Complete manual/current rotation; saving does not imply solver feasibility.

    Scope is empty for organization-wide schemes or contains exact station/shift
    contexts for one shift. Existing links may be inactive historical records. Risk
    coefficients are read from each Job's single current risk set.

    Attributes:
        project_id: Nonblank saved project identity, never derived from a file name.
        scheme_id: Nonblank immutable saved rotation-scheme identity.
        name: Saved display name; identity is held separately and domain operations
            define trimming policy.
        workers: Ordered worker links with optional original assignment identities,
            including closed history.
        targets: Unique Job/placement identities; risk numbers are not stored here.
        current: Immutable schedule rows in original worker order; each row has the same
            positive block count.
        scope: Empty for organization-wide schemes, otherwise unique exact station/shift
            contexts sharing one shift.
        mode: Recorded manual/single-tool/all-tools provenance, independent of the
            current display tool.
        primary_kind: Selected optimized model only for single-tool provenance; None for
            manual or multi-tool.
        description: Optional saved description; None is distinct from an empty string.
    """

    project_id: str
    scheme_id: str
    name: str
    workers: tuple[RotationWorkerLink, ...]
    targets: tuple[RotationTarget, ...]
    current: tuple[WorkerRotation, ...]
    scope: tuple[WorkplaceContext, ...] = ()
    mode: RotationMode = RotationMode.MANUAL
    primary_kind: AssessmentKind | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """Reject incomplete shape, ambiguous identities and unsupported provenance.

        Args:
            None. Dataclass construction supplies the fields documented on
            RotationScheme.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: Scheme identities, time blocks or scope are inconsistent.
                Invalid rotation optimization provenance or description. Scheme
                collections require immutable typed records.
        """
        _require_identity(self.project_id, self.scheme_id, self.name)
        for values, kind in (
            (self.workers, RotationWorkerLink),
            (self.targets, RotationTarget),
            (self.current, WorkerRotation),
            (self.scope, WorkplaceContext),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(value, kind) for value in values
            ):
                raise ValueError("Scheme collections require immutable typed records.")
        if (
            not self.workers
            or not self.targets
            or not self.current
            or len({worker.worker_id for worker in self.workers}) != len(self.workers)
            or tuple(row.worker_id for row in self.current)
            != tuple(worker.worker_id for worker in self.workers)
            or len({len(row.target_keys) for row in self.current}) != 1
            or len({(target.job_id, target.placement_id) for target in self.targets})
            != len(self.targets)
            or {key for row in self.current for key in row.target_keys}
            != {target.key for target in self.targets}
            or len(set(self.scope)) != len(self.scope)
            or len({context.shift_id for context in self.scope}) > 1
        ):
            raise ValueError(
                "Scheme identities, time blocks or scope are inconsistent."
            )
        if (
            not isinstance(self.mode, RotationMode)
            or (self.mode == RotationMode.SINGLE_TOOL)
            != isinstance(self.primary_kind, AssessmentKind)
            or (self.mode != RotationMode.SINGLE_TOOL and self.primary_kind is not None)
            or (self.description is not None and not isinstance(self.description, str))
        ):
            raise ValueError("Invalid rotation optimization provenance or description.")

    def validate_references(
        self, hierarchy: WorkHierarchy, jobs: JobCatalog, risks: JobRiskCatalog
    ) -> None:
        """Validate project membership and historical assignment/workplace ownership.

        Activity is intentionally not required: saved schemes retain original closed
        assignments and placements. Current Job values may be absent; solver preparation
        separately rejects missing measurements for the selected tools.

        Args:
            hierarchy: Complete project hierarchy, including empty parents and
                independent shifts.
            jobs: Immutable job, placement and assignment catalog for the same project.
            risks: Current Job risks validated against the same project and real Jobs.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: Rotation belongs to a different project. Rotation assignment
                does not belong to the worker. Rotation worker assignment is outside its
                scope. Rotation Job is missing. Rotation
                placement does not belong to its job. Rotation target is outside its
                scope.
        """
        if not (
            self.project_id
            == hierarchy.work.project_id
            == jobs.project_id
            == risks.project_id
        ):
            raise ValueError("Rotation belongs to a different project.")
        self.validate_hierarchy(hierarchy)
        assignments = {item.assignment_id: item for item in jobs.assignments}
        placements = {item.placement_id: item for item in jobs.placements}
        job_ids = {job.job_id for job in jobs.jobs}
        for worker in self.workers:
            assignment = (
                assignments.get(worker.assignment_id)
                if worker.assignment_id is not None
                else None
            )
            if worker.assignment_id is not None and (
                assignment is None or assignment.worker.worker_id != worker.worker_id
            ):
                raise ValueError("Rotation assignment does not belong to the worker.")
            if self.scope and (
                assignment is None or assignment.worker.workplace not in self.scope
            ):
                raise ValueError("Rotation worker assignment is outside its scope.")
        for target in self.targets:
            if target.job_id not in job_ids:
                raise ValueError("Rotation target requires a real Job.")
            placement = (
                placements.get(target.placement_id)
                if target.placement_id is not None
                else None
            )
            if target.placement_id is not None and (
                placement is None or placement.job_id != target.job_id
            ):
                raise ValueError("Rotation placement does not belong to its job.")
            if self.scope and (
                placement is None or placement.workplace not in self.scope
            ):
                raise ValueError("Rotation target is outside its scope.")

    def validate_job_change(self, current: JobCatalog, replacement: JobCatalog) -> None:
        """Protect referenced identities while allowing assignment closure/activity.

        Reassignment creates a successor; it must not rewrite this scheme's original
        worker/workplace/placement. Notes and end dates may still change.

        Args:
            current: Previously saved job/assignment catalog whose referenced identities
                must be preserved.
            replacement: Proposed immutable replacement catalog; referenced ownership
                cannot be rewritten.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: Rotation references the original worker assignment. Rotation
                references the original job placement.
            KeyError: The baseline catalog lacks an already referenced assignment or
                placement; validate the baseline before comparing edits.
        """
        before = {item.assignment_id: item for item in current.assignments}
        after = {item.assignment_id: item for item in replacement.assignments}
        for worker in self.workers:
            if worker.assignment_id is not None:
                old = before[worker.assignment_id]
                new = after.get(worker.assignment_id)
                if new is None or (old.worker, old.placement_id) != (
                    new.worker,
                    new.placement_id,
                ):
                    raise ValueError(
                        "Rotation references the original worker assignment."
                    )
        old_placements = {item.placement_id: item for item in current.placements}
        new_placements = {item.placement_id: item for item in replacement.placements}
        for target in self.targets:
            if target.placement_id is not None:
                old_place = old_placements[target.placement_id]
                new_place = new_placements.get(target.placement_id)
                if new_place is None or (old_place.job_id, old_place.workplace) != (
                    new_place.job_id,
                    new_place.workplace,
                ):
                    raise ValueError("Rotation references the original job placement.")

    def validate_hierarchy(self, hierarchy: WorkHierarchy) -> None:
        """Protect saved workers/scope without reading Job or risk catalogs.

        Args:
            hierarchy: Complete project hierarchy, including empty parents and
                independent shifts.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: Rotation belongs to a different project. Rotation scope
                references a missing workplace. Rotation references a missing worker.
        """
        if self.project_id != hierarchy.work.project_id:
            raise ValueError("Rotation belongs to a different project.")
        contexts = {
            station.at_shift(shift)
            for station in hierarchy.work.stations
            for shift in hierarchy.work.shifts
        }
        if not set(self.scope) <= contexts:
            raise ValueError("Rotation scope references a missing workplace.")
        worker_ids = {worker.worker_id for worker in hierarchy.work.workers}
        if any(worker.worker_id not in worker_ids for worker in self.workers):
            raise ValueError("Rotation references a missing worker.")
