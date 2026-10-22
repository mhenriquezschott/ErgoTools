"""Saved current assessments for the reference worker/tool data browser.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass

from ergotools.domain.assessment_history import AssessmentHistory
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog


@dataclass(frozen=True, slots=True)
class SavedToolOption:
    """Exact saved source ownership independent of table sorting and captions.

    Attributes:
        assignment_id: Original workplace assignment, or None for standalone data.
        document_id: Exact current saved source identity.
        workplace: Original full workplace, or None for standalone worker data.
        kind: Scientific model identity.
        job_id: Referenced placement job, or None for unclassified ownership.
    """

    assignment_id: int | None
    document_id: str
    workplace: WorkplaceContext | None
    kind: AssessmentKind
    job_id: str | None


def saved_tool_options(
    jobs: JobCatalog,
    history: AssessmentHistory,
    worker_id: str,
    kind: AssessmentKind,
) -> tuple[SavedToolOption, ...]:
    """List saved assessments for this worker/tool, including closed owners.

    Historical assignments remain browsable without reassignment or promotion. Missing
    saved assessments are omitted; this operation never creates sources.

    Args:
        jobs: Validated same-project assignment/placement catalog.
        history: Saved assignment/tool ownership; validated against jobs
            before projection.
        worker_id: Exact selected worker identity.
        kind: Exact selected scientific tool.

    Returns:
        Saved assessment options in history order, retaining closed assignments and
        their original workplace ownership.

    Raises:
        ValueError: History/project/assignment membership is inconsistent.
    """
    history.validate_jobs(jobs)
    assignments = {a.assignment_id: a for a in jobs.assignments}
    placements = {p.placement_id: p for p in jobs.placements}
    result = []
    for entry in history.entries:
        assignment = (
            assignments.get(entry.assignment_id)
            if entry.assignment_id is not None
            else None
        )
        if entry.kind is not kind:
            continue
        if entry.worker_id != worker_id:
            continue
        placement = (
            placements.get(assignment.placement_id)
            if assignment is not None and assignment.placement_id is not None
            else None
        )
        result.append(
            SavedToolOption(
                entry.assignment_id,
                entry.document_id,
                assignment.worker.workplace if assignment is not None else None,
                entry.kind,
                placement.job_id if placement is not None else None,
            )
        )
    return tuple(result)
