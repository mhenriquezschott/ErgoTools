"""Original saved-worker PLOT CSV columns and explicit migrated provenance.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from datetime import date

from ergotools.application.plot_results import PlotResults
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.worker_details import WorkerDetails, display_body_measurement

# Stable original PLOT interchange columns plus explicit ownership/status/body-unit
# provenance; independent of UI language.
PLOT_HEADERS = (
    "worker_assignment_id",
    "worker_id",
    "plant_name",
    "section_name",
    "line_name",
    "station_id",
    "shift_id",
    "tool_id",
    "total_cumulative_damage",
    "probability_outcome",
    "unit",
    "first_name",
    "last_name",
    "year_of_birth",
    "month_of_birth",
    "day_of_birth",
    "gender",
    "worker_height",
    "worker_weight",
    "job_id",
    "job_name",
    "job_total_cumulative_damage",
    "job_probability_outcome",
    "job_unit",
    "project_id",
    "assessment_id",
    "evaluation_status",
    "issue_keys",
    "worker_body_unit",
)


def plot_csv_table(
    results: PlotResults, system: MeasurementSystem
) -> tuple[tuple[str, ...], ...]:
    """Format saved worker rows, never preview geometry or translated display text.

    Preserve the original retained columns/order and percentage probability scale.
    Append exact version/status and body-unit provenance. Missing values are empty; zero
    remains zero. Body lengths/masses project canonical cm/kg into the chosen display
    system with an explicit worker_body_unit column. CSV quoting/I/O belongs to the
    injected writer. Scientific review values remain unavailable.

    Args:
        results: Applied saved worker dataset; no unsaved preview or geometry is
            exported.
        system: Explicit display system for canonical body cm/kg projection; source
            assessment units remain unchanged.

    Returns:
        Fixed English machine header and complete text rows; None becomes empty while
        observed zero remains zero.

    Raises:
        ValueError: Saved ISO birth date or canonical body measurement projection is
            invalid.
    """
    labels = {
        AssessmentKind.LIFFT: "LiFFT",
        AssessmentKind.DUET: "DUET",
        AssessmentKind.TST: "ST",
    }
    table: list[tuple[str, ...]] = [PLOT_HEADERS]
    for row in results.workers:
        assessment = row.assessment
        place = assessment.owner.workplace
        details = row.worker.details or WorkerDetails()
        birthday = (
            date.fromisoformat(details.birth_date) if details.birth_date else None
        )
        evidence = row.job_risk
        values = (
            assessment.assignment_id,
            row.worker.worker_id,
            place.plant_name,
            place.section_name,
            place.line_name,
            place.station_id,
            place.shift_id,
            labels[assessment.kind],
            assessment.total_damage,
            None if assessment.probability is None else assessment.probability * 100,
            assessment.units.value.title(),
            row.worker.first_name,
            row.worker.last_name,
            birthday.year if birthday else None,
            birthday.month if birthday else None,
            birthday.day if birthday else None,
            details.sex,
            display_body_measurement(details.height_cm, system),
            display_body_measurement(details.weight_kg, system, mass=True),
            row.job.job_id if row.job else None,
            row.job.name if row.job else None,
            evidence.measurement.cumulative_damage if evidence else None,
            evidence.measurement.probability_percent if evidence else None,
            evidence.measurement.unit if evidence else None,
            assessment.document.project_id,
            assessment.document.document_id,
            assessment.status.value,
            ";".join(assessment.issue_keys),
            system.value.title(),
        )
        table.append(tuple("" if value is None else str(value) for value in values))
    return tuple(table)
