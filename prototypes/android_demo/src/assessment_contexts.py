"""Portable mobile context/reuse adapter over existing ownership and transfer APIs.

No schema or calculator changes. Mutations affect only the tablet workspace and are
wrapped by the caller's shared project history. Exact source/result checks protect
confirmation intent; native transactions own assignment/assessment atomicity.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path
from uuid import uuid4

from assessment_tools import new_source

from ergotools.application.session import DocumentKey
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessment_transfer import StandaloneDestination, TransferRequest
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def workplace_label(workplace: WorkplaceContext | None) -> str:
    """Describe exact ancestry and shift without confusing location with a filter.

    Args:
        workplace: Existing station/shift or None for standalone ownership.

    Returns:
        Full readable context label.
    """
    if workplace is None:
        return "Standalone assessment"
    return (
        f"{workplace.plant_name} / {workplace.section_name} / "
        f"{workplace.line_name} / {workplace.station_id} · "
        f"Shift {workplace.shift_id}"
    )


def read_contexts(path: Path) -> dict:
    """Detach a complete read-only worker/tool/context catalog with exact saved results.

    Args:
        path: Private tablet working file or disposable test native file.

    Returns:
        Hierarchy, jobs/history and source projections; closed ownership stays visible.
    """
    with AssessmentProjectFile.open(path) as project:
        hierarchy, jobs, history = (
            project.load_hierarchy(),
            project.load_jobs(),
            project.load_history(),
        )
        workers = {w.worker_id: w for w in hierarchy.work.workers}
        assignments = {a.assignment_id: a for a in jobs.assignments}
        placements = {p.placement_id: p for p in jobs.placements}
        job_names = {j.job_id: f"{j.job_id} · {j.name}" for j in jobs.jobs}
        records = []
        for owner in history.entries:
            assignment = assignments.get(owner.assignment_id)
            workplace = assignment.worker.workplace if assignment else None
            placement = placements.get(assignment.placement_id) if assignment else None
            key = DocumentKey(project.metadata.project_id, owner.document_id)
            records.append(
                {
                    "document": key,
                    "owner": owner,
                    "worker": workers[owner.worker_id],
                    "source": project.load(key),
                    "result": project.load_saved_result(key),
                    "units": project.metadata.default_units,
                    "workplace": workplace,
                    "context": workplace_label(workplace)
                    + (
                        " · Closed assignment"
                        if assignment and not assignment.active
                        else ""
                    ),
                    "active": assignment is None or assignment.active,
                    "job": job_names[placement.job_id]
                    if placement
                    else "No Job assigned",
                }
            )
        return {
            "hierarchy": hierarchy,
            "jobs": jobs,
            "history": history,
            "records": tuple(records),
        }


def destination_record(
    catalog: dict,
    worker_id: str,
    kind: AssessmentKind,
    workplace: WorkplaceContext | None,
) -> dict | None:
    """Find an exact active destination, keeping closed owners separate.

    Args:
        catalog: Detached read_contexts snapshot.
        worker_id: Exact destination worker.
        kind: Current tool only.
        workplace: Exact station/shift, or standalone.

    Returns:
        Existing target projection or None; absence never creates data.
    """
    return next(
        (
            r
            for r in catalog["records"]
            if r["worker"].worker_id == worker_id
            and r["owner"].kind is kind
            and r["workplace"] == workplace
            and r["active"]
        ),
        None,
    )


def check_expected(actual: dict | None, expected: dict | None) -> None:
    """Reject stale replacement/deletion consent without altering native bytes.

    Args:
        actual: Current exact record or None.
        expected: Record shown/confirmed, including source, owner and result.

    Returns:
        None when both absence or exact source-bound snapshots agree.

    Raises:
        ValueError: The intended source/destination changed since selection.
    """
    fields = ("document", "owner", "source", "result", "job", "active")
    if (actual is None) != (expected is None) or (
        actual is not None and any(actual[k] != expected[k] for k in fields)
    ):
        raise ValueError(
            "Assessment changed. Review the destination and confirm again."
        )


def create_assessment(
    path: Path,
    worker_id: str,
    kind: AssessmentKind,
    workplace: WorkplaceContext | None,
    *,
    expected: dict | None = None,
) -> str:
    """Create one blank assessment or replace exactly the explicitly confirmed target.

    Args:
        path: Private native workspace.
        worker_id: Saved worker identity.
        kind: Current tool, independent of other tool ownership.
        workplace: Existing station/shift or None for standalone.
        expected: Existing target confirmed for replacement; None requires absence.

    Returns:
        Resulting document ID; optional Job/assignment is retained on replacement.
    """
    catalog = read_contexts(path)
    actual = destination_record(catalog, worker_id, kind, workplace)
    check_expected(actual, expected)
    identity = actual["document"].document_id if actual else uuid4().hex
    with AssessmentProjectFile.open(path) as project:
        units = project.metadata.default_units
        source = new_source(kind, units, uuid4().hex)
        if actual:
            source = replace(actual["source"], tasks=source.tasks)
        project.begin_editing(lambda label: None)
        if workplace is None:
            if actual:
                project.save(actual["document"], source)
            else:
                project.create_historical_assessment(
                    AssignmentAssessment(identity, None, kind, worker_id), source
                )
        else:
            owner = next(
                (
                    a
                    for a in catalog["jobs"].assignments
                    if a.active
                    and a.worker.worker_id == worker_id
                    and a.worker.workplace == workplace
                ),
                None,
            )
            project.add_workplace_assessment(
                worker_id,
                workplace,
                owner.placement_id if owner else None,
                identity,
                source,
                effective_date=date.today(),
                expected_document_id=identity if actual else None,
            )
        project.commit_editing()
    return identity


def delete_assessment(path: Path, expected: dict) -> None:
    """Delete one confirmed source/owner, leaving assignments and other tools intact.

    Args:
        path: Private native workspace.
        expected: Exact selected record shown before confirmation.

    Returns:
        None; caller records one reversible native-byte project history action.
    """
    catalog = read_contexts(path)
    actual = next(
        (r for r in catalog["records"] if r["document"] == expected["document"]), None
    )
    check_expected(actual, expected)
    if actual is None:
        raise ValueError("Select an existing assessment.")
    with AssessmentProjectFile.open(path) as project:
        project.begin_editing(lambda label: None)
        project.delete_historical_assessment(
            project.load_history(), actual["document"].document_id
        )
        project.commit_editing()


def transfer_assessment(
    path: Path,
    source: dict,
    worker_id: str,
    workplace: WorkplaceContext | None,
    *,
    move: bool = False,
    expected: dict | None = None,
) -> str:
    """Copy/move the current tool using the existing atomic native transfer planner.

    Args:
        path: Private working project.
        source: Exact source projection selected before the destination dialog.
        worker_id: Existing target worker, same or different.
        workplace: Real station/shift destination, or standalone.
        move: Remove the source only after successful destination creation/replacement.
        expected: Exact existing destination confirmed for replacement.

    Returns:
        Independent new destination document identity with exact copied source/result.
    """
    catalog = read_contexts(path)
    actual_source = next(
        (r for r in catalog["records"] if r["document"] == source["document"]), None
    )
    check_expected(actual_source, source)
    if actual_source is None:
        raise ValueError("Source assessment no longer exists.")
    kind = source["owner"].kind
    check_expected(destination_record(catalog, worker_id, kind, workplace), expected)
    destination = (
        StandaloneDestination(catalog["history"].project_id, worker_id)
        if workplace is None
        else catalog["hierarchy"].work.worker_context(worker_id, workplace)
    )
    request = TransferRequest(
        source["owner"].assignment_id,
        destination,
        (kind,),
        move,
        source["worker"].worker_id,
        expected is not None,
    )
    identity = uuid4().hex
    with AssessmentProjectFile.open(path) as project:
        project.begin_editing(lambda label: None)
        project.transfer_assessments(
            catalog["jobs"], catalog["history"], request, {kind: identity}
        )
        project.commit_editing()
    return identity
