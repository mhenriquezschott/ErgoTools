"""Map reviewed source catalogs to existing typed models without source writes.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from dataclasses import dataclass
from datetime import date

from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.job_risk import JobRiskCatalog, JobRiskMeasurement, JobRiskValues
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import (
    ORGANIZATION_FIELDS,
    OrganizationKind,
    OrganizationRecord,
)
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.domain.worker_details import WorkerDetails, store_body_measurement

from .legacy_project import LegacyProject, LegacyRow
from .legacy_values import (
    legacy_flag,
    legacy_integer,
    legacy_keys,
    legacy_kind,
    legacy_number,
    legacy_text,
    optional_integer,
    optional_text,
)

# Original five-part workplace column order, shared by placement/context decoding.
_ANCESTRY = ("plant_name", "section_name", "line_name", "station_id", "shift_id")


@dataclass(frozen=True, slots=True)
class LegacyCatalogs:
    """Validated source catalogs and selected current Job measurements.

    Attributes:
        hierarchy: Complete typed original organization and worker hierarchy.
        jobs: Typed original job/placement/assignment catalog retaining historical
            integer identities.
        risks: Uniquely selected current Job measurements, retaining exact units/values.
            Older profiles and evidence metadata are deliberately omitted.
    """

    hierarchy: WorkHierarchy
    jobs: JobCatalog
    risks: JobRiskCatalog


def _date(row: LegacyRow, suffix: str) -> str | None:
    """Build one ISO worker date from complete original year/month/day columns.

    Args:
        row: Read-only original row mapping with exact version-eight schema column
            names.
        suffix: Original split-date suffix, birth or hiring, identifying year/month/day
            columns.

    Returns:
        Canonical ISO date, or None only when every date part is absent; partial or
        invalid dates fail.

    Raises:
        KeyError: Required split-date columns are absent.
        ValueError: A date is partial, noninteger or not a valid calendar date.
    """
    parts = tuple(row[name + "_of_" + suffix] for name in ("year", "month", "day"))
    if all(value is None for value in parts):
        return None
    return date(*(legacy_integer(value) for value in parts)).isoformat()


def _worker(row: LegacyRow, system: MeasurementSystem) -> WorkerEntry:
    # Owner policy: interpret untagged legacy numbers using the project setting.
    # Normalize only the destination; original source files retain raw numbers.
    """Normalize original worker metadata using the approved project-unit policy.

    Args:
        row: Read-only original row mapping with exact version-eight schema column
            names.
        system: Declared project measurement system used by the owner-approved untagged
            body-value normalization.

    Returns:
        Typed worker entry with optional original text and canonical body length/mass in
        cm/kg.

    Raises:
        KeyError: Required worker columns are absent.
        ValueError: Worker metadata, dates, body numbers or the declared unit system are
            invalid.
    """
    return WorkerEntry(
        legacy_text(row["id"]),
        optional_text(row["first_name"]),
        optional_text(row["last_name"]),
        WorkerDetails(
            birth_date=_date(row, "birth"),
            hiring_date=_date(row, "hiring"),
            sex=optional_text(row["gender"]),
            height_cm=store_body_measurement(legacy_number(row["height"]), system),
            weight_kg=store_body_measurement(
                legacy_number(row["weight"]), system, mass=True
            ),
            address=optional_text(row["address"]),
            city=optional_text(row["city"]),
            region=optional_text(row["state"]),
            country=optional_text(row["country"]),
            postal_code=optional_text(row["zipcode"]),
            email=optional_text(row["email"]),
        ),
    )


def read_legacy_hierarchy(project: LegacyProject) -> WorkHierarchy:
    """Read complete ancestry, worker details and original organization attributes.

    Body numbers use the declared project system and normalize into cm/kg. This
    owner-approved legacy assumption cannot recover historical unit changes. Missing
    values remain None; partial dates, malformed fields and orphan identities raise
    ValueError/KeyError. Visual-only fields and unused legacy anthropometry remain in
    the read snapshot, not this domain projection; this function does not export or
    discard source records.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.

    Returns:
        Complete typed hierarchy with empty parents, workers and original optional
        organization fields.

    Raises:
        KeyError: Required entity or worker columns are absent.
        ValueError: Typed hierarchy, worker dates/measurements or exact ancestry are
            invalid.
        sqlite3.Error: The source snapshot cannot be queried.
    """
    rows = {kind: project.rows(kind.value) for kind in OrganizationKind}
    keys = {
        OrganizationKind.PLANT: ("name",),
        OrganizationKind.SECTION: ("plant_name", "name"),
        OrganizationKind.LINE: ("plant_name", "section_name", "name"),
        OrganizationKind.STATION: (*_ANCESTRY[:3], "id"),
        OrganizationKind.SHIFT: ("id",),
    }
    organization = tuple(
        OrganizationRecord(
            kind,
            legacy_keys(row, *keys[kind]),
            tuple(
                (
                    name,
                    legacy_number(row[name])
                    if field_type == "number"
                    else optional_text(row[name]),
                )
                for name, field_type in ORGANIZATION_FIELDS[kind.value]
            ),
        )
        for kind in OrganizationKind
        for row in rows[kind]
    )
    work = WorkCatalog(
        project.descriptor.metadata.project_id,
        tuple(
            _worker(row, project.descriptor.metadata.default_units)
            for row in project.rows("Worker", order=("id",))
        ),
        tuple(
            StationKey(*legacy_keys(row, *keys[OrganizationKind.STATION]))
            for row in rows[OrganizationKind.STATION]
        ),
        tuple(legacy_text(row["id"]) for row in rows[OrganizationKind.SHIFT]),
    )
    return WorkHierarchy(
        work,
        tuple(legacy_text(row["name"]) for row in rows[OrganizationKind.PLANT]),
        tuple(
            SectionKey(*legacy_keys(row, *keys[OrganizationKind.SECTION]))
            for row in rows[OrganizationKind.SECTION]
        ),
        tuple(
            LineKey(*legacy_keys(row, *keys[OrganizationKind.LINE]))
            for row in rows[OrganizationKind.LINE]
        ),
        organization,
    )


def read_legacy_catalogs(project: LegacyProject) -> LegacyCatalogs:
    """Read hierarchy, historical assignments and selected current Job values.

    Only uniquely selected prior Job values survive. Older profiles/evidence are
    discarded; retained units and missing quantities stay exact. No new connection
    and performs no save or inferred reassignment.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.

    Returns:
        Validated hierarchy, exact assignment IDs and selected current Job measurements.

    Raises:
        ValueError: Source values or cross-catalog relationships are invalid.
        KeyError: Required version-eight columns/foreign identities are missing.
    """
    hierarchy = read_legacy_hierarchy(project)
    project_id = hierarchy.work.project_id
    contexts = {
        legacy_integer(row["id"]): WorkplaceContext(*legacy_keys(row, *_ANCESTRY))
        for row in project.rows("WorkplaceContext", order=("id",))
    }
    jobs = JobCatalog(
        project_id,
        tuple(
            Job(
                legacy_text(row["id"]),
                legacy_text(row["name"]),
                legacy_flag(row["active"]),
                optional_text(row["description"]),
            )
            for row in project.rows("Job", order=("id",))
        ),
        tuple(
            JobPlacement(
                legacy_integer(row["id"]),
                legacy_text(row["job_id"]),
                contexts[legacy_integer(row["workplace_context_id"])],
                legacy_flag(row["active"]),
                notes=optional_text(row["notes"]),
            )
            for row in project.rows("JobPlacement", order=("id",))
        ),
        tuple(
            WorkerJobAssignment(
                legacy_integer(row["id"]),
                WorkerContext(
                    project_id,
                    legacy_text(row["worker_id"]),
                    contexts[legacy_integer(row["workplace_context_id"])],
                ),
                optional_integer(row["job_placement_id"]),
                legacy_flag(row["active"]),
                optional_text(row["started_at"]),
                optional_text(row["ended_at"]),
                optional_text(row["notes"]),
            )
            for row in project.rows("WorkerAssignment", order=("id",))
        ),
    )
    jobs.validate_hierarchy(hierarchy)
    selected = tuple(
        row
        for row in project.rows("JobRiskProfile", order=("id",))
        if legacy_flag(row["is_current"])
    )
    if len({row["job_id"] for row in selected}) != len(selected):
        raise ValueError("Multiple selected risk sets for the same Job.")
    selected_ids = {legacy_integer(row["id"]) for row in selected}
    measurements: dict[int, list[JobRiskMeasurement]] = {}
    for row in project.rows("JobRiskMeasurement", order=("profile_id", "tool_id")):
        if legacy_integer(row["profile_id"]) not in selected_ids:
            continue
        measurements.setdefault(legacy_integer(row["profile_id"]), []).append(
            JobRiskMeasurement(
                legacy_kind(row["tool_id"]),
                legacy_number(row["total_cumulative_damage"]),
                legacy_number(row["probability_outcome"]),
                optional_text(row["unit"]),
            )
        )
    risks = JobRiskCatalog(
        project_id,
        tuple(
            JobRiskValues(
                legacy_text(row["job_id"]),
                tuple(measurements.get(legacy_integer(row["id"]), ())),
            )
            for row in selected
            if measurements.get(legacy_integer(row["id"]))
        ),
    )
    risks.validate_jobs(jobs)
    return LegacyCatalogs(hierarchy, jobs, risks)
