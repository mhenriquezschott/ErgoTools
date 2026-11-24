"""Mobile worker catalog use cases over unchanged domain and native repository APIs.

Preserve all nonedited demographic/contact details and relationship identities.
Worker IDs remain stable on edit. Deletion is restricted to unreferenced workers;
no assessment, assignment or rotation is silently cascaded by this frontend.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path
from unicodedata import normalize

from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.domain.worker_details import (
    WorkerDetails,
    display_body_measurement,
    store_body_measurement,
)
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile

# Flet 1.1.2 checks whole candidate text with hasMatch, not a character replacement
# filter. Anchors plus optional digits allow clearing and partial decimal entry.
BODY_INPUT_PATTERN = r"^[0-9]*(?:[.,][0-9]*)?$"


def initial(worker: WorkerEntry) -> str:
    """Map last name, first name or ID into a case/accent-independent initial.

    Args:
        worker: Existing typed worker entry.

    Returns:
        Latin initial, with accented Spanish characters normalized for browsing.
    """
    text = worker.last_name or worker.first_name or worker.worker_id
    return normalize("NFKD", text).upper()[0]


def age(worker: WorkerEntry, today: date | None = None) -> int | None:
    """Calculate current age from the optional saved full birth date.

    Args:
        worker: Canonical worker demographics.
        today: Explicit test date, otherwise device-local calendar date.

    Returns:
        Whole years, or None when no date is stored.
    """
    birth = worker.details.birth_date if worker.details else None
    if not birth:
        return None
    born, now = date.fromisoformat(birth), today or date.today()
    return now.year - born.year - ((now.month, now.day) < (born.month, born.day))


def filter_workers(
    workers: tuple[WorkerEntry, ...],
    query: str = "",
    letter: str = "All",
    *,
    by_id: bool = False,
) -> tuple[WorkerEntry, ...]:
    """Search IDs/names without losing Spanish accents or filtering unrelated data.

    Args:
        workers: Full immutable project worker catalog.
        query: Substring search, insensitive to case and accents.
        letter: Last-name initial or All.
        by_id: Sort by ID instead of last name/first name/ID.

    Returns:
        Ordered visible workers; no project mutation occurs.
    """

    def text(value: str) -> str:
        """Remove diacritics only for comparison, preserving saved literal names.

        Args:
            value: Search or catalog text.

        Returns:
            Casefolded comparison key.
        """
        return "".join(
            c for c in normalize("NFKD", value) if not 0x300 <= ord(c) <= 0x36F
        ).casefold()

    key = text(query.strip())
    offered = [
        w
        for w in workers
        if key in text(f"{w.worker_id} {w.first_name or ''} {w.last_name or ''}")
        and (letter == "All" or initial(w) == letter)
    ]
    return tuple(
        sorted(
            offered,
            key=lambda w: (
                (text(w.worker_id),)
                if by_id
                else (
                    text(w.last_name or w.first_name or w.worker_id),
                    text(w.first_name or ""),
                    text(w.worker_id),
                )
            ),
        )
    )


def load_workers(path: Path) -> tuple[tuple[WorkerEntry, ...], MeasurementSystem]:
    """Read catalog and body-display units without retaining a native connection.

    Args:
        path: Mobile private project workspace.

    Returns:
        Worker entries and project measurement system.
    """
    with AssessmentProjectFile.open(path) as project:
        return project.load_hierarchy().work.workers, project.metadata.default_units


def form_values(worker: WorkerEntry, system: MeasurementSystem) -> dict[str, str]:
    """Project editable fields while keeping canonical body precision available.

    Args:
        worker: Existing worker, including optional hidden details.
        system: Project display units for cm/kg or in/lb.

    Returns:
        Text fields, empty for absent values; no storage changes.
    """
    details = worker.details or WorkerDetails()
    result = {
        name: getattr(details, name) or ""
        for name in (
            "birth_date",
            "hiring_date",
            "sex",
            "address",
            "city",
            "region",
            "country",
            "postal_code",
            "email",
        )
    }
    for name, mass in (("height_cm", False), ("weight_kg", True)):
        value = display_body_measurement(getattr(details, name), system, mass=mass)
        result[name] = "" if value is None else format(value, ".15g")
    return {
        "worker_id": worker.worker_id,
        "first_name": worker.first_name or "",
        "last_name": worker.last_name or "",
        **result,
    }


def make_worker(
    values: dict[str, str],
    system: MeasurementSystem,
    previous: WorkerEntry | None = None,
) -> WorkerEntry:
    """Validate optional form values and preserve untouched canonical precision.

    Args:
        values: Complete shown form, dates as ISO strings, body values in display units.
        system: Explicit measurement system from the active native project.
        previous: Exact original worker; edit cannot change its stable ID.

    Returns:
        Typed validated worker entry. Future or inconsistent dates are rejected.
    """
    identity = values["worker_id"].strip()
    if not identity or any(c.isspace() for c in identity):
        raise ValueError("Worker ID is required and cannot contain spaces.")
    if previous and identity != previous.worker_id:
        raise ValueError("An existing worker ID cannot be changed.")
    old = previous.details if previous and previous.details else WorkerDetails()
    projected = form_values(previous, system) if previous else {}
    fields = {}
    for name in ("height_cm", "weight_kg"):
        raw = values.get(name, "").strip()
        fields[name] = (
            getattr(old, name)
            if previous and raw == projected[name]
            else store_body_measurement(
                float(raw.replace(",", ".")) if raw else None,
                system,
                mass=name == "weight_kg",
            )
        )
    for name in (
        "birth_date",
        "hiring_date",
        "sex",
        "address",
        "city",
        "region",
        "country",
        "postal_code",
        "email",
    ):
        fields[name] = values.get(name, getattr(old, name) or "").strip() or None
    details = replace(old, **fields)
    for value in (details.birth_date, details.hiring_date):
        if value and date.fromisoformat(value) > date.today():
            raise ValueError("Worker dates cannot be in the future.")
    if (
        details.birth_date
        and details.hiring_date
        and details.hiring_date < details.birth_date
    ):
        raise ValueError("Hiring date cannot be before date of birth.")
    return WorkerEntry(
        identity,
        values.get("first_name", "").strip() or None,
        values.get("last_name", "").strip() or None,
        details,
    )


def put_worker(
    path: Path, worker: WorkerEntry, *, expected: WorkerEntry | None = None
) -> None:
    """Add or edit one worker through guarded hierarchy/classification persistence.

    Args:
        path: Active private native file.
        worker: Fully validated next worker.
        expected: Exact previous entry for editing; None means creation only.

    Returns:
        None; duplicate IDs/stale forms or broken relationships raise atomically.
    """
    with AssessmentProjectFile.open(path) as project:
        hierarchy, jobs = project.load_hierarchy(), project.load_jobs()
        old = next(
            (w for w in hierarchy.work.workers if w.worker_id == worker.worker_id), None
        )
        if old != expected:
            raise ValueError(
                "Worker ID already exists or the worker changed. Refresh the form."
            )
        if old == worker:
            return
        workers = (
            (*hierarchy.work.workers, worker)
            if old is None
            else tuple(
                worker if w.worker_id == worker.worker_id else w
                for w in hierarchy.work.workers
            )
        )
        replacement = replace(hierarchy, work=replace(hierarchy.work, workers=workers))
        project.begin_editing(lambda label: None)
        project.replace_worker_catalogs(hierarchy, replacement, jobs, jobs)
        project.commit_editing()


def delete_worker(path: Path, identity: str) -> None:
    """Delete an unreferenced worker; native guards protect all retained contexts.

    Args:
        path: Active private native file.
        identity: Existing stable worker ID.

    Returns:
        None; referenced or missing workers are refused without cascading data loss.
    """
    with AssessmentProjectFile.open(path) as project:
        hierarchy, jobs = project.load_hierarchy(), project.load_jobs()
        if not any(w.worker_id == identity for w in hierarchy.work.workers):
            raise ValueError("This worker no longer exists.")
        if any(a.worker.worker_id == identity for a in jobs.assignments) or any(
            a.worker_id == identity for a in project.load_history().entries
        ):
            raise ValueError(
                "This worker has workplace assignments "
                "or assessments. Remove those "
                "associations before deleting the "
                "worker."
            )
        replacement = replace(
            hierarchy,
            work=replace(
                hierarchy.work,
                workers=tuple(
                    w for w in hierarchy.work.workers if w.worker_id != identity
                ),
            ),
        )
        project.begin_editing(lambda label: None)
        project.replace_worker_catalogs(hierarchy, replacement, jobs, jobs)
        project.commit_editing()
