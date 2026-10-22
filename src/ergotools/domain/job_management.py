"""Pure current Job risk/detail mutation, with no UI, storage or profile lifecycle."""

from dataclasses import replace

from ergotools.domain.job_catalog import Job, JobCatalog
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskValues


def save_job_details(
    jobs: JobCatalog,
    risk: JobRiskCatalog,
    job: Job,
    values: JobRiskValues | None,
) -> tuple[JobCatalog, JobRiskCatalog]:
    """Replace one Job and its current risks, preserving other Jobs and worker data.

    Args:
        jobs: Exact existing Job/assignment catalog.
        risk: Same-project current risk sets.
        job: Proposed Job identity/name/description; identity is stripped and validated.
        values: Replacement current risks; None preserves existing values. Empty removes
            this Job's risks without removing the Job or its placements.

    Returns:
        Immutable replacement Job and risk catalogs for one atomic repository write.

    Raises:
        ValueError: Job identity, risk ownership or project membership is invalid.
    """
    risk.validate_jobs(jobs)
    identity = job.job_id.strip()
    if not identity or " " in identity:
        raise ValueError("Job ID is required and cannot contain spaces.")
    saved_job = replace(
        job,
        job_id=identity,
        name=job.name.strip(),
        description=job.description.strip() if job.description is not None else None,
    )
    exists = any(item.job_id == identity for item in jobs.jobs)
    saved_jobs = replace(
        jobs,
        jobs=tuple(saved_job if item.job_id == identity else item for item in jobs.jobs)
        if exists
        else (*jobs.jobs, saved_job),
    )
    if values is None:
        return saved_jobs, risk
    if values.job_id != identity:
        raise ValueError("Risk values belong to another Job.")
    previous = risk.for_job(identity)
    replacement = tuple(
        values if item.job_id == identity else item
        for item in risk.values
        if item.job_id != identity or values.measurements
    )
    if not previous.measurements and values.measurements:
        replacement = (*replacement, values)
    return saved_jobs, replace(risk, values=replacement)


def delete_job(
    jobs: JobCatalog,
    risk: JobRiskCatalog,
    job_id: str,
) -> tuple[JobCatalog, JobRiskCatalog]:
    """Remove job-owned records and unclassify retained worker assignments.

    Match the original CASCADE on values/placements and SET NULL on worker assignment
    placement IDs. The repository must additionally protect assessment history (and
    rotation references when that schema is migrated) before writing. Raise ValueError
    for a missing job or inconsistent project relationships.

    Args:
        jobs: Immutable job, placement and assignment catalog for the same project.
        risk: Project-owned job-risk values whose ownership must match the job
            catalog.
        job_id: Exact job identity; display names never establish ownership.

    Returns:
        Replacement job/risk catalogs with owned values/placements removed and
        surviving assignments unclassified.

    Raises:
        ValueError: Select an existing job before deleting.
    """
    risk.validate_jobs(jobs)
    if not any(job.job_id == job_id for job in jobs.jobs):
        raise ValueError("Select an existing job before deleting.")
    removed = {item.placement_id for item in jobs.placements if item.job_id == job_id}
    saved_jobs = replace(
        jobs,
        jobs=tuple(job for job in jobs.jobs if job.job_id != job_id),
        placements=tuple(item for item in jobs.placements if item.job_id != job_id),
        assignments=tuple(
            replace(item, placement_id=None) if item.placement_id in removed else item
            for item in jobs.assignments
        ),
    )
    saved_risk = replace(
        risk, values=tuple(item for item in risk.values if item.job_id != job_id)
    )
    return saved_jobs, saved_risk
