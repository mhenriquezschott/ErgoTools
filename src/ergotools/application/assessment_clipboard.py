"""Atomic spreadsheet-value preparation for worker and Job assessment grids.

Application layer. Parse tab-separated values using the shared numeric policy, retain
original measurements for unchanged projected values, and return one immutable source.
The desktop owns mapping/preview/clipboard access and the session owns one history edit.
No spreadsheet engine, SQL, formula evaluation, calculator or widget dependency exists.
"""

import csv
from dataclasses import replace
from io import StringIO

from ergotools.application.job_calculation import resize_job_source
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet import DuetTask
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem, project_model_input
from ergotools.domain.numeric_input import format_input_number, parse_input_number
from ergotools.domain.task_catalog import TaskDefinition

# Bound a clipboard preview before allocating native widgets; current capacity is 100.
MAX_CLIPBOARD_CHARACTERS = 1_000_000


class ClipboardRowError(ValueError):
    """First invalid target task row, retaining its structured numeric issue.

    Attributes:
        row_index: Zero-based destination task position, independent of source IDs.
        detail: Original field-specific parser issue or explicit choice/range error.
    """

    def __init__(self, row_index: int, detail: ValueError | DraftError) -> None:
        """Retain the failed row for localized preview feedback without source mutation.

        Args:
            row_index: Exact target row of the rejected batch cell.
            detail: Original validation issue; never a fabricated zero or partial row.

        Returns:
            None; ordinary ValueError clients can still reject the whole batch.
        """
        self.row_index = row_index
        self.detail = detail
        super().__init__(f"Task {row_index + 1}: {detail}")


def clipboard_rows(text: str) -> tuple[tuple[str, ...], ...]:
    """Parse Excel-style quoted tab/newline cells without executing formulas/macros.

    Args:
        text: Plain clipboard text; tabs separate columns, CRLF/LF separate rows.

    Returns:
        Nonempty rectangular rows preserving blank cells and literal text values.

    Raises:
        ValueError: Text is oversized, malformed, empty or nonrectangular.
    """
    if len(text) > MAX_CLIPBOARD_CHARACTERS:
        raise ValueError("Clipboard selection is too large.")
    try:
        rows = tuple(
            tuple(row)
            for row in csv.reader(StringIO(text), delimiter="\t", strict=True)
        )
    except csv.Error as error:
        raise ValueError("Clipboard cells have invalid quoting.") from error
    if (
        not rows
        or not rows[0]
        or len(rows) > 101
        or len(rows[0]) > 20
        or any(len(row) != len(rows[0]) for row in rows)
    ):
        raise ValueError("Paste a rectangular selection of at most 100 task rows.")
    return rows


def assessment_input_fields(source: AssessmentDraft) -> tuple[str, ...]:
    """Return editable clipboard column identities, excluding row IDs and results.

    Args:
        source: Exact tool source; direction conventions and units remain unchanged.

    Returns:
        Task name followed by numeric/selector inputs in shared-grid visual order.
    """
    if isinstance(source, DuetDraft):
        return ("task_name", "omni_res_scale", "repetitions")
    return (
        "task_name",
        *(("direction",) if isinstance(source, TstDraft) else ()),
        "lever_arm",
        "load",
        "repetitions",
    )


def _direction(text: str) -> TstDirection | None:
    """Map displayed ST choices or exact stored codes without changing conventions.

    Args:
        text: Plain source value, including established English/Spanish selector labels.

    Returns:
        Matching stored enum code or None for an explicitly blank selector cell.

    Raises:
        ValueError: Text is not a supported ST input choice.
    """
    token = " ".join(text.casefold().replace("/", " ").split())
    if token in ("", "please select ...", "please select", "seleccione ..."):
        return None
    aliases = {
        "0": TstDirection.HANDLING_LOADS,
        "handling load": TstDirection.HANDLING_LOADS,
        "handling loads": TstDirection.HANDLING_LOADS,
        "manipulación de cargas": TstDirection.HANDLING_LOADS,
        "1": TstDirection.DOWNWARD,
        "push pull downward": TstDirection.DOWNWARD,
        "push or pull downward": TstDirection.DOWNWARD,
        "empujar o tirar hacia abajo": TstDirection.DOWNWARD,
        "2": TstDirection.HORIZONTAL,
        "horizontal push pull": TstDirection.HORIZONTAL,
        "horizontal push or pull": TstDirection.HORIZONTAL,
        "empuje o tirón horizontal": TstDirection.HORIZONTAL,
    }
    if token not in aliases:
        raise ValueError("Choose an ST task type or code 0, 1 or 2.")
    return aliases[token]


def _paste_task[Task: (LifftTask, DuetTask, TstTask)](
    task: Task,
    cells: tuple[str, ...],
    fields: tuple[str | None, ...],
    convention: DecimalConvention,
    input_system: MeasurementSystem,
    source_system: MeasurementSystem,
) -> Task:
    """Validate one mapped row while preserving unmapped fields and exact quantities.

    Args:
        task: Original typed row; stable identity is never pasted from a spreadsheet.
        cells: Plain cell values aligned with the explicit mapping.
        fields: Allowed field or None to ignore a source column.
        convention: Explicit numeric decimal mark, independent of language/OS.
        input_system: Units declared for pasted arm/load values.
        source_system: Units of the preserved canonical source.

    Returns:
        Same typed row with only mapped fields replaced, including explicit blanks.

    Raises:
        ValueError: A choice/range is invalid or a spreadsheet formula is supplied.
        DraftError: Numeric grammar or unit projection fails before state changes.
    """
    name, definition_id = task.task_name, task.task_definition_id
    repetitions = task.repetitions
    arm = task.lever_arm if isinstance(task, (LifftTask, TstTask)) else None
    load = task.load if isinstance(task, (LifftTask, TstTask)) else None
    scale = task.omni_res_scale if isinstance(task, DuetTask) else None
    direction = task.direction if isinstance(task, TstTask) else None
    for field, text in zip(fields, cells, strict=True):
        if field is None:
            continue
        if text.lstrip().startswith("="):
            raise ValueError("Paste cell values, not spreadsheet formulas.")
        if field == "task_name":
            name = text if text.strip() else None
            # Exact re-entry retains an explicit reference; a different label is local.
            if name != task.task_name:
                definition_id = None
        elif field == "direction":
            direction = _direction(text)
        else:
            token = text.split(":", 1)[0] if field == "omni_res_scale" else text
            value = parse_input_number(token, convention, field, task.task_id)
            if value is not None and value < 0:
                raise ValueError("Task inputs must be nonnegative.")
            if field == "omni_res_scale":
                if value is not None and (int(value) != value or not 0 <= value <= 10):
                    raise ValueError("OMNI-Res must be a whole number from 0 to 10.")
                scale = int(value) if value is not None else None
            elif field in ("lever_arm", "load"):
                original = getattr(task, field)
                projected = project_model_input(
                    original, field, task.task_id, source_system, input_system
                )
                converted = (
                    original
                    if value == projected
                    else project_model_input(
                        value, field, task.task_id, input_system, source_system
                    )
                )
                if field == "lever_arm":
                    arm = converted
                else:
                    load = converted
            else:
                repetitions = value
    if isinstance(task, LifftTask):
        return replace(
            task,
            lever_arm=arm,
            load=load,
            repetitions=repetitions,
            task_name=name,
            task_definition_id=definition_id,
        )
    if isinstance(task, DuetTask):
        return replace(
            task,
            omni_res_scale=scale,
            repetitions=repetitions,
            task_name=name,
            task_definition_id=definition_id,
        )
    return replace(
        task,
        direction=direction,
        lever_arm=arm,
        load=load,
        repetitions=repetitions,
        task_name=name,
        task_definition_id=definition_id,
    )


def prepare_assessment_paste(
    source: AssessmentDraft,
    rows: tuple[tuple[str, ...], ...],
    fields: tuple[str | None, ...],
    *,
    start_row: int = 0,
    convention: DecimalConvention = DecimalConvention.POINT,
    input_system: MeasurementSystem = MeasurementSystem.METRIC,
) -> AssessmentDraft:
    """Prepare one all-or-nothing paste without recording edits or calculating.

    Args:
        source: Exact current source, retained unchanged if preparation fails.
        rows: Data rows only; caller explicitly handles the optional header row.
        fields: Per-column canonical field mapping; None ignores a derived/ID column.
        start_row: Existing zero-based target row, or current row count to append.
        convention: Explicit decimal convention selected in the preview.
        input_system: Declared pasted units; canonical source units are preserved.

    Returns:
        Fully validated replacement with up to 100 tasks and stable retained row IDs.

    Raises:
        ValueError: Mapping, rows, target, capacity or a field value is invalid.
        ClipboardRowError: A target row has invalid numeric/choice input.
    """
    allowed = assessment_input_fields(source)
    mapped = tuple(field for field in fields if field is not None)
    if (
        not rows
        or not mapped
        or len(set(mapped)) != len(mapped)
        or any(field not in allowed for field in mapped)
        or any(len(row) != len(fields) for row in rows)
        or not 0 <= start_row <= len(source.tasks)
        or start_row + len(rows) > 100
    ):
        raise ValueError("Paste mapping, target row or task capacity is invalid.")
    expanded = source
    while len(expanded.tasks) < start_row + len(rows):
        expanded = resize_job_source(expanded)
    system = (
        expanded.system
        if isinstance(expanded, (LifftDraft, TstDraft))
        else input_system
    )
    # Branches keep concrete task tuple types through immutable dataclass replacement.
    if isinstance(expanded, LifftDraft):
        tasks_l = list(expanded.tasks)
        for index, cells in enumerate(rows, start_row):
            try:
                tasks_l[index] = _paste_task(
                    tasks_l[index], cells, fields, convention, input_system, system
                )
            except (ValueError, DraftError) as error:
                raise ClipboardRowError(index, error) from error
        return replace(expanded, tasks=tuple(tasks_l))
    if isinstance(expanded, DuetDraft):
        tasks_d = list(expanded.tasks)
        for index, cells in enumerate(rows, start_row):
            try:
                tasks_d[index] = _paste_task(
                    tasks_d[index], cells, fields, convention, input_system, system
                )
            except (ValueError, DraftError) as error:
                raise ClipboardRowError(index, error) from error
        return replace(expanded, tasks=tuple(tasks_d))
    tasks_s = list(expanded.tasks)
    for index, cells in enumerate(rows, start_row):
        try:
            tasks_s[index] = _paste_task(
                tasks_s[index], cells, fields, convention, input_system, system
            )
        except (ValueError, DraftError) as error:
            raise ClipboardRowError(index, error) from error
    return replace(expanded, tasks=tuple(tasks_s))


def assessment_clipboard_text(
    source: AssessmentDraft,
    definitions: tuple[TaskDefinition, ...],
    convention: DecimalConvention,
    system: MeasurementSystem,
) -> str:
    """Export full-precision editable values with headers suitable for Excel paste.

    Args:
        source: Exact current source; row IDs and calculated columns are excluded.
        definitions: Current project names used to resolve explicit reusable references.
        convention: Desired decimal mark; numeric values are never display-rounded.
        system: Explicit output arm/load units, separate from canonical stored units.

    Returns:
        Quoted TSV text with task names/selector codes and exact editable values.
    """
    fields = assessment_input_fields(source)
    names = {d.definition_id: d.name for d in definitions}
    stream = StringIO()
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    headers = {
        "task_name": "Task name",
        "omni_res_scale": "OMNI-Res scale",
        "direction": "Task type",
        "repetitions": "Repetitions (per work day)",
        "lever_arm": "Lever arm (cm)"
        if system is MeasurementSystem.METRIC
        else "Lever arm (in)",
        "load": "Load (N)" if system is MeasurementSystem.METRIC else "Load (lbf)",
    }
    writer.writerow([headers[field] for field in fields])
    original_system = (
        source.system if isinstance(source, (LifftDraft, TstDraft)) else system
    )
    for task in source.tasks:
        row = []
        for field in fields:
            if field == "task_name":
                row.append(
                    names.get(task.task_definition_id or "", task.task_name or "")
                )
            elif field == "direction":
                row.append(
                    task.direction.value
                    if isinstance(task, TstTask) and task.direction is not None
                    else ""
                )
            else:
                value = getattr(task, field)
                if field in ("lever_arm", "load"):
                    value = project_model_input(
                        value, field, task.task_id, original_system, system
                    )
                row.append(format_input_number(value, convention))
        writer.writerow(row)
    return stream.getvalue()
