"""Read historical version-eight sources and cached values for reconciliation.

Raw ST selector positions remain unchanged here; shoulder_source applies the original
UI/calculator convention before native evaluation. Cached values are comparison evidence
in memory, not a second saved native result.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from dataclasses import dataclass

from ergotools.domain.assessment_history import (
    AssessmentHistory,
    AssignmentAssessment,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem

from .legacy_catalogs import LegacyCatalogs
from .legacy_project import LegacyProject, LegacyRow
from .legacy_values import (
    legacy_integer,
    legacy_kind,
    legacy_number,
    optional_integer,
    optional_text,
)

# Exact version-eight historical task tables by model; never inferred from display
# captions.
_TASK_TABLES = {
    AssessmentKind.LIFFT: "LiFFTAssessmentTask",
    AssessmentKind.DUET: "DUETAssessmentTask",
    AssessmentKind.TST: "ShoulderAssessmentTask",
}


@dataclass(frozen=True, slots=True)
class LegacyShoulderTask:
    """Original selector position and source inputs before model-branch projection.

    Attributes:
        task_id: Stable decoded task identity derived from its original numeric task
            index.
        selector_index: Raw original ST dropdown position 0, 1 or 2, or None;
            shoulder_source applies the original branch convention later.
        lever_arm: Optional original arm length in the owning source's cm/in system.
        load: Optional original force in N/lbf, never body mass.
        repetitions: Optional original repetitions per day, retaining fractional counts.
    """

    task_id: str
    selector_index: int | None
    lever_arm: float | None
    load: float | None
    repetitions: float | None


@dataclass(frozen=True, slots=True)
class LegacyShoulderSource:
    """Original ST units and raw selector tasks before compatibility projection.

    Attributes:
        system: Explicit recorded source measurement system, independent of interface
            language.
        tasks: Ordered raw ST selector tasks; this reader neither remaps directions nor
            evaluates damage.
    """

    system: MeasurementSystem
    tasks: tuple[LegacyShoulderTask, ...]


@dataclass(frozen=True, slots=True)
class LegacyTaskEvidence:
    """Original cached task values; these are evidence, not fresh model results.

    Attributes:
        task_index: Original integer task-row index; gaps and ordering are retained.
        moment: Optional original cached display moment; absent for DUET and not a fresh
            calculation.
        cumulative_damage: Optional original cached dimensionless damage used only for
            source reconciliation.
        percentage_total: Optional original cached percent share (0-100 scale), not a
            regenerated contribution.
    """

    task_index: int
    moment: float | None
    cumulative_damage: float | None
    percentage_total: float | None


@dataclass(frozen=True, slots=True)
class LegacyAssessment:
    """Exact historical ownership, editable source and separately retained evidence.

    Original source ID is retained alongside a deterministic destination document ID.
    Cached totals, task moments/damage/shares, notes and assessed time are never
    overwritten by reading or confused with freshly calculated result freshness.

    Cached evidence exists in this read snapshot for reconciliation only. The native
    writer recalculates one result per valid source; it does not persist this cache.

    Attributes:
        source_id: Original integer IndividualAssessment identity alongside the
            deterministic native document ID.
        ownership: Exact assignment/model/version/status/current record, including
            inactive historical owners.
        source: Typed LiFFT/DUET draft or raw ST selector source; no result is
            calculated by the reader.
        unit: Optional original recorded unit label, independent of the project display
            default.
        cumulative_damage: Optional original cached dimensionless damage used only for
            source reconciliation.
        probability_percent: Optional original cached probability in percent; discarded
            when native results are recalculated.
        task_evidence: Read-only original task moment/damage/share records for
            reconciliation, never a second native result.
        assessed_at: Optional original assessment timestamp text, without timezone
            inference.
        notes: Optional original assessment note text.
        original_tasks: Original row mappings retaining exact storage values, including
            blank line-edit strings.
    """

    source_id: int
    ownership: AssignmentAssessment
    source: LifftDraft | DuetDraft | LegacyShoulderSource
    unit: str | None
    cumulative_damage: float | None
    probability_percent: float | None
    task_evidence: tuple[LegacyTaskEvidence, ...]
    assessed_at: str | None
    notes: str | None
    original_tasks: tuple[LegacyRow, ...]


def _input_number(value: object) -> float | None:
    # main.py saves untouched DUET/ST line edits as an exact empty string.
    # Normalize that UI absence only; original_tasks retains its storage value.
    """Decode an original numeric edit, treating only its exact empty string as absence.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Finite float or None for a missing value/exact empty edit; zero remains present.

    Raises:
        ValueError: A present storage value is not an accepted finite original number.
    """
    return None if value == "" else legacy_number(value)


def _system(unit: str | None) -> MeasurementSystem:
    """Resolve the explicitly recorded source arm/force measurement system.

    Args:
        unit: Recorded original Metric/Imperial label; LiFFT/ST sources require an
            explicit supported label.

    Returns:
        Explicit metric or imperial model-input system; no conversion occurs.

    Raises:
        ValueError: Recorded source units are absent or unsupported.
    """
    if unit not in ("Metric", "Imperial"):
        raise ValueError(
            "LiFFT/ST legacy source requires recorded Metric/Imperial units."
        )
    return MeasurementSystem.METRIC if unit == "Metric" else MeasurementSystem.IMPERIAL


def _selector(value: object) -> int | None:
    """Validate an original ST selector without remapping calculator branches.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Original index 0, 1 or 2, or None; the later shoulder mapper preserves the
        original branch convention.

    Raises:
        ValueError: A present selector is not an integer position 0, 1 or 2.
    """
    index = optional_integer(value)
    if index is not None and index not in (0, 1, 2):
        raise ValueError("Unknown original Shoulder Tool selector index.")
    return index


def read_legacy_task_source(
    kind: AssessmentKind, unit: str | None, rows: tuple[LegacyRow, ...]
) -> LifftDraft | DuetDraft | LegacyShoulderSource:
    """Decode original indexed task inputs; retain ST selectors without inference.

    Args:
        kind: Stable model identity already decoded from the original exact tool ID.
        unit: Recorded original Metric/Imperial label; LiFFT/ST sources require an
            explicit supported label.
        rows: Original source rows in the caller-supplied task order, including gaps and
            blank fields.

    Returns:
        Ordered LiFFT/DUET draft or raw ST selector source; this reader performs no
        evaluation or save.

    Raises:
        KeyError: Required task columns are absent.
        ValueError: Recorded units, primitive types, indices or draft identities are
            malformed.
    """
    if kind is AssessmentKind.LIFFT:
        return LifftDraft(
            _system(unit),
            tuple(
                LifftTask(
                    "legacy-task-" + str(legacy_integer(row["task_index"])),
                    _input_number(row["lever_arm"]),
                    _input_number(row["load"]),
                    _input_number(row["repetitions"]),
                )
                for row in rows
            ),
        )
    if kind is AssessmentKind.DUET:
        return DuetDraft(
            tuple(
                DuetTask(
                    "legacy-task-" + str(legacy_integer(row["task_index"])),
                    optional_integer(row["omni_res_scale"]),
                    _input_number(row["repetitions"]),
                )
                for row in rows
            )
        )
    return LegacyShoulderSource(
        _system(unit),
        tuple(
            LegacyShoulderTask(
                "legacy-task-" + str(legacy_integer(row["task_index"])),
                _selector(row["type_of_task"]),
                _input_number(row["lever_arm"]),
                _input_number(row["load"]),
                _input_number(row["repetitions"]),
            )
            for row in rows
        ),
    )


def read_legacy_assessments(
    project: LegacyProject, catalogs: LegacyCatalogs
) -> tuple[LegacyAssessment, ...]:
    """Read all historical versions, task rows and cached results on one snapshot.

    Keep task_index ordering/gaps and blank/zero rows. Bind to original assignment IDs,
    including closed owners. LiFFT/DUET sources use existing immutable drafts; ST
    retains raw selectors; shoulder_source applies the original UI branch mapping later.
    No calculation, approval, current-version selection or save occurs.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.
        catalogs: Validated source hierarchy/jobs/risks preserving exact original
            historical identities.

    Returns:
        Every saved historical assessment with exact assignment/version/current
        ownership, source rows and read-only cached evidence.

    Raises:
        ValueError: Unknown model/units, invalid ownership, or cross-model tasks.
        KeyError: Required version-eight schema fields are absent.
    """
    tasks: dict[tuple[int, AssessmentKind], list[LegacyRow]] = {}
    for kind, table in _TASK_TABLES.items():
        for row in project.rows(
            table, order=("individual_assessment_id", "task_index")
        ):
            if legacy_integer(row["task_index"]) < 0:
                raise ValueError("Legacy task indices cannot be negative.")
            key = (legacy_integer(row["individual_assessment_id"]), kind)
            tasks.setdefault(key, []).append(row)
    assessments = []
    for row in project.rows("IndividualAssessment", order=("id",)):
        identity = legacy_integer(row["id"])
        kind = legacy_kind(row["tool_id"])
        unit = optional_text(row["unit"])
        source_rows = tuple(tasks.pop((identity, kind), ()))
        ownership = AssignmentAssessment(
            "legacy-assessment-" + str(identity),
            legacy_integer(row["worker_assignment_id"]),
            kind,
            next(
                a.worker.worker_id
                for a in catalogs.jobs.assignments
                if a.assignment_id == legacy_integer(row["worker_assignment_id"])
            ),
        )
        assessments.append(
            LegacyAssessment(
                identity,
                ownership,
                read_legacy_task_source(kind, unit, source_rows),
                unit,
                legacy_number(row["total_cumulative_damage"]),
                legacy_number(row["probability_outcome"]),
                tuple(
                    LegacyTaskEvidence(
                        legacy_integer(task["task_index"]),
                        None
                        if kind is AssessmentKind.DUET
                        else legacy_number(task["moment"]),
                        legacy_number(task["cumulative_damage"]),
                        legacy_number(task["percentage_total"]),
                    )
                    for task in source_rows
                ),
                optional_text(row["assessed_at"]),
                optional_text(row["notes"]),
                source_rows,
            )
        )
    if tasks:
        raise ValueError(
            "Legacy task references a missing or different-model assessment."
        )
    history = AssessmentHistory(
        project.descriptor.metadata.project_id,
        tuple(assessment.ownership for assessment in assessments),
    )
    history.validate_jobs(catalogs.jobs)
    return tuple(assessments)
