"""Portable assessment task operations for the touch editor, using the core models.

Sources, reusable names and source-bound results commit together in a private native
editing session. No formula, unit conversion convention or schema is reimplemented.
Clipboard interchange is deliberately plain TSV in the assessment's current units.
"""

import csv
import io
import math
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from assessment_tools import AssessmentTask, input_fields, new_source, source_units

from ergotools.application.assessments.evaluation import AssessmentEvaluator
from ergotools.application.saved_results import result_snapshot
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
    task_has_data,
)
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile

# Same maximum as desktop task editors; a newly created mobile assessment starts at 1.
MAX_TASKS = 100


def blank_task(kind: AssessmentKind = AssessmentKind.LIFFT) -> AssessmentTask:
    """Give a new blank task a unique row identity, independent of its visible number.

    Args:
        kind: Selected tool; LiFFT is the compatibility default.

    Returns:
        Optional inputs remain absent; no result or task name is fabricated.
    """
    return new_source(kind, MeasurementSystem.METRIC, uuid4().hex).tasks[0]


def create_standalone(
    path: Path, worker_id: str, kind: AssessmentKind = AssessmentKind.LIFFT
) -> str:
    """Create exactly one worker-owned standalone assessment with one empty task.

    Args:
        path: Private project workspace.
        worker_id: Exact existing worker, never derived from a display label.
        kind: Tool with independent standalone ownership.

    Returns:
        New document ID; duplicate ownership is refused by the native adapter.
    """
    identity = uuid4().hex
    with AssessmentProjectFile.open(path) as project:
        if worker_id not in {
            w.worker_id for w in project.load_hierarchy().work.workers
        }:
            raise ValueError("Select an existing worker first.")
        project.begin_editing(lambda label: None)
        project.create_historical_assessment(
            AssignmentAssessment(identity, None, kind, worker_id),
            new_source(kind, project.metadata.default_units, uuid4().hex),
        )
        project.commit_editing()
    return identity


def preview(
    document: DocumentKey,
    draft: AssessmentDraft,
    defaults: MeasurementSystem = MeasurementSystem.METRIC,
) -> dict:
    """Evaluate the exact desktop grid policy without storing or altering source data.

    Args:
        document: Exact native source identity.
        draft: All source rows, including unused capacity and partial rows.
        defaults: Project result-unit label for dimensionless DUET sources only.

    Returns:
        Source-bound result, core issues and a plain-language readiness summary.
    """
    evaluator = AssessmentEvaluator()
    evaluate = {
        AssessmentKind.LIFFT: evaluator.evaluate_lifft_grid,
        AssessmentKind.DUET: evaluator.evaluate_duet_grid,
        AssessmentKind.TST: evaluator.evaluate_tst_grid,
    }[assessment_kind(draft)]
    outcome = evaluate(DocumentSession(document, draft))
    result = (
        result_snapshot(
            outcome,
            defaults
            if assessment_kind(draft) is AssessmentKind.DUET
            else source_units(draft),
        )
        if any(task_has_data(t) for t in draft.tasks)
        else None
    )
    missing = []
    for index, task in enumerate(draft.tasks, 1):
        if task_has_data(task):
            absent = [
                label
                for field, label in (
                    (field, field.replace("_", " ")) for field in input_fields(draft)
                )
                if getattr(task, field) is None
            ]
            if absent:
                missing.append(f"Task {index}: {', '.join(absent)}")
    message = (
        ("Still needed — " + "; ".join(missing))
        if missing
        else "Calculated from entered tasks. Blank unused rows are ignored."
        if result
        else "Enter task inputs to calculate."
    )
    if outcome.status.value in ("invalid_input", "calculation_failed"):
        message = "Check task inputs — " + "; ".join(
            f"{i.field}: {i.code}" for i in outcome.issues
        )
    return {
        "result": result,
        "message": message,
        "status": outcome.status.value,
        "issues": outcome.issues,
    }


def persist_source(
    path: Path, selected: dict, draft: AssessmentDraft, *, auto_calculate: bool = True
) -> dict:
    """Accept source/names/results together, retaining every other document.

    Args:
        path: Private native working file.
        selected: Previously loaded exact document/source projection.
        draft: Replacement rows; 1-100 for user operations, zero only for old imports.
        auto_calculate: Apply core grid evaluation, or clear results when False.

    Returns:
        Refreshed source, result and status, without publishing project Save.
    """
    if len(draft.tasks) > MAX_TASKS:
        raise ValueError("An assessment can have at most 100 tasks.")
    with AssessmentProjectFile.open(path) as project:
        if project.load(selected["document"]) != selected["source"]:
            raise ValueError("Assessment changed. Reopen it before editing.")
        previous = project.load_task_definitions()
        definitions = list(previous)
        named = []
        old_rows = {t.task_id: t for t in selected["source"].tasks}
        for task in draft.tasks:
            old = old_rows.get(task.task_id)
            if (
                task.task_name
                and not task.task_definition_id
                and (old is None or old.task_name != task.task_name)
            ):
                definition = next(
                    (
                        d
                        for d in definitions
                        if d.name.casefold() == task.task_name.casefold()
                    ),
                    None,
                )
                if definition is None:
                    definition = TaskDefinition(uuid4().hex, task.task_name)
                    definitions.append(definition)
                task = replace(task, task_definition_id=definition.definition_id)
            named.append(task)
        draft = replace(draft, tasks=tuple(named))
        evaluated = preview(
            selected["document"],
            draft,
            selected.get("units", project.metadata.default_units),
        )
        result = evaluated["result"] if auto_calculate else None
        if (
            draft == selected["source"]
            and tuple(definitions) == previous
            and project.load_saved_result(selected["document"]) == result
        ):
            return {
                **selected,
                "source": draft,
                "result": result,
                "readiness": evaluated,
            }
        project.begin_editing(lambda label: None)
        if tuple(definitions) != previous:
            project.replace_task_definitions(previous, tuple(definitions))
        if result is not None:
            project.save_result(selected["document"], result)
        else:
            project.save(selected["document"], draft)
        project.commit_editing()
    return {**selected, "source": draft, "result": result, "readiness": evaluated}


def remove_tasks(draft: AssessmentDraft, identities: set[str]) -> AssessmentDraft:
    """Remove exact rows, retaining one blank row when all are removed.

    Args:
        draft: Current source with stable task identities.
        identities: Checked task IDs, never visual row indices.

    Returns:
        Ordered replacement retaining all unselected rows and their exact inputs.
    """
    retained = tuple(t for t in draft.tasks if t.task_id not in identities)
    return replace(draft, tasks=retained or (blank_task(assessment_kind(draft)),))


def tasks_to_tsv(tasks: tuple, kind: AssessmentKind = AssessmentKind.LIFFT) -> str:
    """Copy selected tasks as tool-specific input-only tab-separated columns.

    Args:
        tasks: Selected source rows in source order, excluding calculated columns.
        kind: Selected tool determines input-only column order.

    Returns:
        Unicode TSV, current source units, blanks for missing numeric values.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t", lineterminator="\n")
    fields = input_fields(new_source(kind, MeasurementSystem.METRIC, "columns"))
    for task in tasks:
        writer.writerow(
            [
                task.task_name or "",
                *(
                    ""
                    if v is None
                    else str(v)
                    if isinstance(v, TstDirection)
                    else repr(v)
                    for v in (getattr(task, field) for field in fields)
                ),
            ]
        )
    return output.getvalue()


def tasks_from_tsv(text: str, kind: AssessmentKind = AssessmentKind.LIFFT) -> tuple:
    """Parse clipboard rows atomically with independent task identities.

    Args:
        text: TSV input fields, optionally preceded by a name. ST direction is 0/1/2.
        kind: Tool determines column schema and selector validation.

    Returns:
        Named immutable source rows; zero/negative/decimal values reach core validation.
    """
    result = []
    source = new_source(kind, MeasurementSystem.METRIC, "columns")
    fields = input_fields(source)
    for number, row in enumerate(csv.reader(io.StringIO(text), delimiter="\t"), 1):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) not in (len(fields), len(fields) + 1):
            raise ValueError(
                f"Row {number}: use {', '.join(fields)}, "
                "with an optional task-name column first."
            )
        name = row[0].strip() or None if len(row) == len(fields) + 1 else None
        try:
            values = {
                field: cell.strip()
                for field, cell in zip(fields, row[-len(fields) :], strict=True)
            }
            values["task_name"] = name or ""
            result.append(task_from_form(blank_task(kind), values, {}))
        except ValueError as error:
            raise ValueError(
                f"Row {number}: enter valid finite numeric inputs."
            ) from error
    if not result:
        raise ValueError("No task rows were found.")
    if len(result) > MAX_TASKS:
        raise ValueError("Paste at most 100 tasks at a time.")
    return tuple(result)


def task_form_values(task: AssessmentTask) -> dict[str, str]:
    """Project input text without asserting formatted numbers are storage precision.

    Args:
        task: Exact existing source row.

    Returns:
        Optional name, numeric strings and discrete source codes for this tool.
    """
    return {
        "task_name": task.task_name or "",
        **{
            k: ""
            if getattr(task, k) is None
            else str(getattr(task, k))
            if k == "direction"
            else format(getattr(task, k), ".15g")
            for k in ("omni_res_scale", "direction", "lever_arm", "load", "repetitions")
            if hasattr(task, k)
        },
    }


def task_from_form(
    task: AssessmentTask, values: dict[str, str], original: dict[str, str]
) -> AssessmentTask:
    """Retain exact untouched source precision when another field or name is edited.

    Args:
        task: Current accepted immutable row.
        values: Current entered text in the row's original source units.
        original: Text last displayed/accepted for each field.

    Returns:
        Replacement task with stable row identity and matching optional name reference.
    """
    fields = tuple(
        k
        for k in ("omni_res_scale", "direction", "lever_arm", "load", "repetitions")
        if hasattr(task, k)
    )
    changes = {}
    for field in fields:
        if values[field] == original.get(field):
            continue
        text = values[field].strip().replace(",", ".")
        if field == "direction":
            value = TstDirection(text) if text else None
        elif field == "omni_res_scale":
            value = int(text) if text else None
            if value is not None and not 0 <= value <= 10:
                raise ValueError("OMNI-Res must be an integer from 0 to 10.")
        else:
            value = float(text) if text else None
            if value is not None and not math.isfinite(value):
                raise ValueError("Enter a finite numeric input.")
        changes[field] = value
    name = (
        task.task_name
        if values["task_name"] == original.get("task_name")
        else values["task_name"].strip() or None
    )
    return replace(
        task,
        **changes,
        task_name=name,
        task_definition_id=task.task_definition_id if name == task.task_name else None,
    )
