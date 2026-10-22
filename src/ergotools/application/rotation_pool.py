"""JROT eligible choices and current Job values, without I/O.

Application layer. Prepare immutable analysis/history values through injected ports. Qt
controls, chart rendering, SQL transactions and user consent remain outside this module;
only explicitly supplied persistence callbacks can write.
"""

from dataclasses import dataclass
from typing import Protocol

from ergotools.application.rotation_scope import RotationScopeReader
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskValues
from ergotools.domain.rotation_scheme import (
    RotationScheme,
    RotationTarget,
    RotationWorkerLink,
)
from ergotools.domain.work_catalog import WorkerEntry


class RotationPoolReader(RotationScopeReader, Protocol):
    """Borrow the owning project's saved catalogs without writes or migration."""

    def load_job_risk(self) -> JobRiskCatalog:
        """Read immutable current values and their recorded measurement units.

        Borrow the owning project; no connection creation, writes or conversion.

        Args:
            None.

        Returns:
            Immutable saved current values and recorded measurements in their declared
            units.
        """
        ...


@dataclass(frozen=True, slots=True)
class RotationWorkerChoice:
    """Display record coupled to one exact worker/assignment link.

    Attributes:
        link: Stable worker and optional historical assignment identity.
        worker: Literal saved worker details used for display.
    """

    link: RotationWorkerLink
    worker: WorkerEntry


@dataclass(frozen=True, slots=True)
class RotationTargetChoice:
    """Display and current scientific values for an opaque rotation target.

    Attributes:
        target: Exact Job and optional placement identity.
        job_name: Literal saved job name; never a target identity.
        values: Exact referenced values including recorded measurement units.
        workplace: Exact placed workplace, or None for organization-wide targets.
    """

    target: RotationTarget
    job_name: str
    values: JobRiskValues
    workplace: WorkplaceContext | None = None


@dataclass(frozen=True, slots=True)
class RotationPool:
    """Immutable original-form choices; display captions never serve as identities.

    Attributes:
        project_id: Stable project ownership shared by every choice.
        workers: Eligible worker choices in case-insensitive worker-ID order.
        targets: Eligible or saved frozen target choices in deterministic schedule
            order.
    """

    project_id: str
    workers: tuple[RotationWorkerChoice, ...]
    targets: tuple[RotationTargetChoice, ...]


def rotation_pool(
    repository: RotationPoolReader,
    scope: tuple[WorkplaceContext, ...] = (),
    *,
    saved: RotationScheme | None = None,
) -> RotationPool:
    """Read original eligible choices or the selected scheme's frozen targets.

    Organization scope includes all workers, without assignment links. Workplace scope
    selects the lowest active assignment ID per worker, matching the source query. New
    targets require active Jobs with current values and, when scoped, active placements.
    Loading a saved scheme retains its Job/placement and closed worker-assignment links,
    while resolving current Job values. No measurement is converted or derived.

    Args:
        repository: Borrowed read-only hierarchy, jobs and risk-values catalogs from
            one project.
        scope: Unique exact workplaces in a single shift; empty selects
            organization-wide choices.
        saved: Optional saved scheme whose exact Job/placement and worker
            assignment links must be retained.

    Returns:
        Deterministically ordered eligible workers and targets, or the saved scheme's
        frozen target evidence.

    Raises:
        ValueError: Catalogs, scope or saved references have incompatible ownership or
            invalid membership.
        KeyError: A required saved values, worker, job or placement identity no longer
            exists.
    """
    hierarchy = repository.load_hierarchy()
    jobs = repository.load_jobs()
    risks = repository.load_job_risk()
    jobs.validate_hierarchy(hierarchy)
    risks.validate_jobs(jobs)
    contexts = set(hierarchy.work.available_workplaces())
    if (
        len(set(scope)) != len(scope)
        or not set(scope) <= contexts
        or len({place.shift_id for place in scope}) > 1
    ):
        raise ValueError("Rotation scope requires unique workplaces in one shift.")
    if saved is not None:
        saved.validate_references(hierarchy, jobs, risks)
        if scope != saved.scope:
            raise ValueError("Saved rotation and requested scope differ.")
    worker_records = {worker.worker_id: worker for worker in hierarchy.work.workers}
    links: dict[str, RotationWorkerLink] = {}
    if not scope:
        links = {key: RotationWorkerLink(key) for key in worker_records}
    else:
        for assignment in sorted(jobs.assignments, key=lambda item: item.assignment_id):
            if assignment.active and assignment.worker.workplace in scope:
                key = assignment.worker.worker_id
                links.setdefault(key, RotationWorkerLink(key, assignment.assignment_id))
    if saved is not None:
        links.update((link.worker_id, link) for link in saved.workers)
    workers = tuple(
        RotationWorkerChoice(links[key], worker_records[key])
        for key in sorted(links, key=str.casefold)
    )
    job_names = {job.job_id: job.name for job in jobs.jobs}
    placements = {place.placement_id: place for place in jobs.placements}
    if saved is not None:
        targets = saved.targets
    else:
        active_jobs = {job.job_id for job in jobs.jobs if job.active}
        current_values = sorted(
            (values for values in risks.values if values.job_id in active_jobs),
            key=lambda values: values.job_id.casefold(),
        )
        targets = (
            tuple(
                RotationTarget(values.job_id, place.placement_id)
                for values in current_values
                for place in sorted(
                    jobs.placements,
                    key=lambda place: (
                        place.workplace.plant_name.casefold(),
                        place.workplace.section_name.casefold(),
                        place.workplace.line_name.casefold(),
                        place.workplace.station_id.casefold(),
                        place.placement_id,
                    ),
                )
                if place.active
                and place.job_id == values.job_id
                and place.workplace in scope
            )
            if scope
            else tuple(RotationTarget(values.job_id) for values in current_values)
        )
    return RotationPool(
        hierarchy.work.project_id,
        workers,
        tuple(
            RotationTargetChoice(
                target,
                job_names[target.job_id],
                risks.for_job(target.job_id),
                placements[target.placement_id].workplace
                if target.placement_id is not None
                else None,
            )
            for target in targets
        ),
    )
