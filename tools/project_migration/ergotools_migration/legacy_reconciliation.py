"""Reconcile original summary/task tables with versioned history without writes.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

import json
from dataclasses import dataclass
from types import MappingProxyType
from uuid import NAMESPACE_URL, uuid5

from ergotools.domain.assessment_history import (
    AssessmentHistory,
    AssignmentAssessment,
)
from ergotools.domain.assessments.context import WorkerContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft

from .legacy_assessments import (
    LegacyAssessment,
    LegacyShoulderSource,
    read_legacy_task_source,
)
from .legacy_catalogs import LegacyCatalogs
from .legacy_project import LegacyProject, LegacyRow
from .legacy_values import (
    legacy_integer,
    legacy_keys,
    legacy_kind,
    optional_text,
)

# Original six-part worker/workplace SQL column order, including shift.
_CONTEXT_FIELDS = (
    "worker_id",
    "plant_name",
    "section_name",
    "line_name",
    "station_id",
    "shift_id",
)
# Exact older current-task table names by model for source/history reconciliation.
_TABLES = {
    AssessmentKind.LIFFT: "LifftResults",
    AssessmentKind.DUET: "DuetResults",
    AssessmentKind.TST: "TstResults",
}
# Original task comparison columns by model, including cached moment where present; no
# recalculation.
_INPUTS = {
    AssessmentKind.LIFFT: ("lever_arm", "load", "moment", "repetitions"),
    AssessmentKind.DUET: ("omni_res_scale", "repetitions"),
    AssessmentKind.TST: ("type_of_task", "lever_arm", "load", "moment", "repetitions"),
}


@dataclass(frozen=True, slots=True)
class LegacyConflict:
    """One concrete source disagreement that must block destination publication.

    Attributes:
        context: Exact worker, plant, section, line, station and shift identity tuple.
        kind: Stable supported assessment model identity.
        reason: Concrete reconciliation disagreement; publication must stop rather than
            silently repair it.
    """

    context: tuple[str, ...]
    kind: AssessmentKind
    reason: str


@dataclass(frozen=True, slots=True)
class LegacyRecoveredAssessment:
    """Unversioned source bound only to its unique existing active assignment.

    Attributes:
        ownership: Exact assignment/model/version/status/current record, including
            inactive historical owners.
        source: Typed LiFFT/DUET draft or raw ST selector source; no result is
            calculated by the reader.
        summary: Original unversioned summary row used for source/history
            reconciliation.
        original_tasks: Original row mappings retaining exact storage values, including
            blank line-edit strings.
    """

    ownership: AssignmentAssessment
    source: LifftDraft | DuetDraft | LegacyShoulderSource
    summary: LegacyRow
    original_tasks: tuple[LegacyRow, ...]


@dataclass(frozen=True, slots=True)
class LegacyReconciliation:
    """Read-only recovery plan; conflicts prohibit a complete import.

    Attributes:
        matched_summaries: Count of old summaries whose cached inputs/evidence match the
            unique current version.
        recovered: Unambiguous unversioned sources bound to their unique existing active
            assignment.
        conflicts: Concrete ambiguous or inconsistent source records; nonempty prevents
            conversion publication.
    """

    matched_summaries: int
    recovered: tuple[LegacyRecoveredAssessment, ...]
    conflicts: tuple[LegacyConflict, ...]


def _context(worker: WorkerContext) -> tuple[str, ...]:
    """Project ownership into the original six-column context order.

    Args:
        worker: Exact typed project/worker/workplace owner whose original context
            columns are needed.

    Returns:
        Worker ID followed by plant, section, line, station and shift IDs; project ID is
        validated separately.
    """
    place = worker.workplace
    return (
        worker.worker_id,
        place.plant_name,
        place.section_name,
        place.line_name,
        place.station_id,
        place.shift_id,
    )


def _key(row: LegacyRow) -> tuple[tuple[str, ...], AssessmentKind]:
    """Decode an original context/tool key for reconciling old and versioned tables.

    Args:
        row: Read-only original row mapping with exact version-eight schema column
            names.

    Returns:
        Exact six-column context tuple and supported assessment-model identity.

    Raises:
        KeyError: A required context or tool column is absent.
        ValueError: A context field is nontext or the original tool identity is
            unsupported.
    """
    return legacy_keys(row, *_CONTEXT_FIELDS), legacy_kind(row["tool_id"])


def _task_signature(
    rows: tuple[LegacyRow, ...], kind: AssessmentKind, index: str
) -> tuple[tuple[object, ...], ...]:
    """Compare original task/evidence columns without normalization.

    Args:
        rows: Original source rows in the caller-supplied task order, including gaps and
            blank fields.
        kind: Stable model identity already decoded from the original exact tool ID.
        index: Original task index column name: task_id in older tables or task_index in
            versioned tables.

    Returns:
        Ordered tuples of index, original inputs/moment and cached damage/share for
        exact equality comparison.

    Raises:
        KeyError: A required original index/input/evidence column is absent or the model
            is unsupported.
    """
    columns = (*_INPUTS[kind], "cumulative_damage", "percentage_total")
    return tuple((row[index], *(row[name] for name in columns)) for row in rows)


def reconcile_legacy_assessments(
    project: LegacyProject,
    catalogs: LegacyCatalogs,
    assessments: tuple[LegacyAssessment, ...],
) -> LegacyReconciliation:
    """Check old/versioned evidence and recover only unambiguous missing owners.

    Existing versioned history is authoritative only when the old current source agrees.
    Conflicting summaries/tasks, orphan old tasks, missing owners and ambiguous current
    versions are reported, never repaired or silently dropped. Recovered document IDs
    derive from full context/tool; no row-order numbering. Their original task IDs and
    raw storage values remain intact. No save occurs.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.
        catalogs: Validated source hierarchy/jobs/risks preserving exact original
            historical identities.
        assessments: Already read versioned sources and original cached evidence from
            this same source transaction.

    Returns:
        Matched count, unambiguous recovered sources and concrete conflicts; any
        conflict blocks destination publication.

    Raises:
        KeyError: Required original fields or referenced versioned assignment identities
            are missing.
        ValueError: Source model/index primitives or recovered history relationships are
            malformed.
        sqlite3.Error: Source snapshot reads fail; no output is published.
    """
    assignments = {a.assignment_id: a for a in catalogs.jobs.assignments}
    normalized: dict[
        tuple[tuple[str, ...], AssessmentKind], list[LegacyAssessment]
    ] = {}
    for assessment in assessments:
        assignment_id = assessment.ownership.assignment_id
        if assignment_id is None:
            raise ValueError("Original assessments require an explicit assignment.")
        assignment = assignments[assignment_id]
        key = (_context(assignment.worker), assessment.ownership.kind)
        normalized.setdefault(key, []).append(assessment)
    tasks: dict[tuple[tuple[str, ...], AssessmentKind], list[LegacyRow]] = {}
    for kind, table in _TABLES.items():
        for row in project.rows(table, order=(*_CONTEXT_FIELDS, "task_id")):
            key = _key(row)
            if key[1] is not kind or legacy_integer(row["task_id"]) < 0:
                raise ValueError("Old task has a wrong model or negative identity.")
            tasks.setdefault(key, []).append(row)
    conflicts = []
    recovered = []
    matched = 0
    for row in project.rows(
        "WorkerStationShiftErgoTool", order=(*_CONTEXT_FIELDS, "tool_id")
    ):
        key = _key(row)
        context, kind = key
        source_rows = tuple(tasks.pop(key, ()))
        existing = normalized.get(key, [])
        if existing:
            current = existing
            if len(current) != 1:
                conflicts.append(
                    LegacyConflict(context, kind, "No unique current history.")
                )
                continue
            saved = current[0]
            if (
                saved.unit != row["unit"]
                or saved.cumulative_damage != row["total_cumulative_damage"]
                or saved.probability_percent != row["probability_outcome"]
                or _task_signature(source_rows, kind, "task_id")
                != _task_signature(saved.original_tasks, kind, "task_index")
            ):
                conflicts.append(
                    LegacyConflict(context, kind, "Old/current evidence differs.")
                )
                continue
            matched += 1
            continue
        owners = [
            a
            for a in assignments.values()
            if a.active and _context(a.worker) == context
        ]
        if len(owners) != 1:
            conflicts.append(
                LegacyConflict(context, kind, "No unique active assignment.")
            )
            continue
        # Only the decoder's index spelling changes. The original rows are kept.
        decoded_rows = tuple(
            MappingProxyType(dict(task, task_index=task["task_id"]))
            for task in source_rows
        )
        source = read_legacy_task_source(kind, optional_text(row["unit"]), decoded_rows)
        identity = uuid5(
            NAMESPACE_URL, json.dumps((context, kind.value), ensure_ascii=True)
        )
        ownership = AssignmentAssessment(
            "legacy-unversioned-" + identity.hex,
            owners[0].assignment_id,
            kind,
            owners[0].worker.worker_id,
        )
        recovered.append(LegacyRecoveredAssessment(ownership, source, row, source_rows))
    conflicts.extend(
        LegacyConflict(context, kind, "Old task has no summary.")
        for context, kind in tasks
    )
    AssessmentHistory(
        catalogs.jobs.project_id,
        tuple(a.ownership for a in assessments) + tuple(a.ownership for a in recovered),
    ).validate_jobs(catalogs.jobs)
    return LegacyReconciliation(matched, tuple(recovered), tuple(conflicts))
