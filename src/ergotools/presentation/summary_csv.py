"""Stable reference CSV columns with explicit migrated ownership/status metadata.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from ergotools.application.assessment_export import SummaryExportRow
from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.domain.assessments.document import AssessmentKind

# Stable original summary interchange columns plus exact ownership/status
# provenance; independent of UI language.
SUMMARY_HEADERS = (
    "Export DateTime",
    "Worker ID",
    "Plant",
    "Section",
    "Line",
    "Station",
    "Shift",
    "Tool ID",
    "Total Cumulative Damage",
    "Probability Outcome",
    "Unit",
    "Project ID",
    "Assessment ID",
    "Assignment ID",
    "Assignment Active",
    "Evaluation Status",
    "Issue Keys",
)


def summary_csv_table(
    rows: tuple[SummaryExportRow, ...], export_datetime: str
) -> tuple[tuple[str, ...], ...]:
    """Format machine-readable CSV values without files, Qt or locale side effects.

    Args:
        rows: Saved assessments or read-only evaluations of persisted inputs.
        export_datetime: Caller-supplied timestamp shared by every output row.

    Returns:
        Header and data rows retaining float precision; CSV escaping is external.

    Preserve reference column order; append identities/status to distinguish
    historical assignments and unavailable results. Probability is percent,
    saved and recomputed values retain calculator precision without gauge clipping.
    Damage and percent values use Python's round-trip float representation.
    Fixed English headers, point decimals and enum/status IDs
    remain stable across UI languages. CSV escaping belongs to the writer.
    """
    data = [SUMMARY_HEADERS]
    labels = {
        AssessmentKind.LIFFT: "LiFFT",
        AssessmentKind.DUET: "DUET",
        AssessmentKind.TST: "ST",
    }
    for row in rows:
        place = row.owner.workplace
        probability = (
            row.recorded_probability_percent
            if row.recorded_probability_percent is not None
            else None
            if row.probability is None
            else row.probability * 100
        )
        data.append(
            (
                export_datetime,
                row.owner.worker_id,
                place.plant_name if place is not None else "",
                place.section_name if place is not None else "",
                place.line_name if place is not None else "",
                place.station_id if place is not None else "",
                place.shift_id if place is not None else "",
                labels[row.kind],
                "" if row.total_damage is None else str(row.total_damage),
                "" if probability is None else str(probability),
                (row.recorded_unit_label or "")
                if row.status is EvaluationStatus.RECORDED
                else row.units.value.title(),
                row.document.project_id,
                row.document.document_id,
                str(row.assignment_id) if row.assignment_id is not None else "",
                "true" if row.assignment_active else "false",
                row.status.value,
                ";".join(row.issue_keys),
            )
        )
    return tuple(data)
