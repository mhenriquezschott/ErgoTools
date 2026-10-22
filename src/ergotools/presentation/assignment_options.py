"""Classified context options derived from validated persisted job snapshots.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass

from ergotools.application.assessment_assignment import AssignmentSnapshot
from ergotools.domain.job_catalog import JobCatalog


@dataclass(frozen=True, slots=True)
class ClassifiedAssignment:
    """Display metadata for one exact eligible assignment; not a job editor.

    Attributes:
        assignment: Typed original project/worker/workplace assignment and placement
            eligibility.
        job_id: Stable literal job identity, independent of name.
        job_name: Optional literal job display name; never parsed as identity.
    """

    assignment: AssignmentSnapshot
    job_id: str | None
    job_name: str | None = None

    def __post_init__(self) -> None:
        """Require typed assignment and explicit job identity without label parsing.

        Args:
            None.

        Returns:
            None after validating the typed assignment and literal job display values.

        Raises:
            ValueError: Assignment is untyped, job identity is blank/nontext or optional
                name is nontext.
        """
        if not isinstance(self.assignment, AssignmentSnapshot):
            raise ValueError("Expected a typed assignment.")
        if self.job_id is not None and (
            not isinstance(self.job_id, str) or not self.job_id.strip()
        ):
            raise ValueError("Job identity must be nonblank text.")
        if self.job_name is not None and not isinstance(self.job_name, str):
            raise ValueError("Job name must be text or absent.")


def classified_assignments(
    catalog: JobCatalog, worker_id: str
) -> tuple[ClassifiedAssignment, ...]:
    """Project active assignment/placement pairs in reference workplace order.

    Job activity and date ranges are deliberately not eligibility filters here. Catalog
    validation has already established placement/job/context consistency.

    Args:
        catalog: Validated same-project jobs/placements/assignments snapshot.
        worker_id: Exact worker identity whose active classified contexts are requested.

    Returns:
        Active assignment/active-placement choices in original full-workplace order;
        inactive jobs and date ranges do not suppress eligibility.
    """
    jobs = {job.job_id: job for job in catalog.jobs}
    placements = {item.placement_id: item for item in catalog.placements}
    result = []
    for item in catalog.assignments:
        if item.worker.worker_id != worker_id or not item.active:
            continue
        placement = (
            placements.get(item.placement_id) if item.placement_id is not None else None
        )
        if placement is not None and not placement.active:
            continue
        job = jobs[placement.job_id] if placement is not None else None
        result.append(
            ClassifiedAssignment(
                AssignmentSnapshot(
                    item.worker,
                    item.assignment_id,
                    item.active,
                    item.placement_id,
                    placement.active if placement is not None else True,
                ),
                job.job_id if job is not None else None,
                job.name if job is not None else None,
            )
        )
    return tuple(
        sorted(
            result,
            key=lambda option: (
                option.assignment.worker.workplace.plant_name,
                option.assignment.worker.workplace.section_name,
                option.assignment.worker.workplace.line_name,
                option.assignment.worker.workplace.station_id,
                option.assignment.worker.workplace.shift_id,
            ),
        )
    )
