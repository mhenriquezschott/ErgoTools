"""Strict versioned interchange format for source TST drafts, not .ergprj.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import json

from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_draft import (
    TstDirectionConvention,
    TstDraft,
    TstTask,
)
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.draft_json import (
    DocumentFormatError as DocumentFormatError,
)
from ergotools.infrastructure.draft_json import document_fields as _fields
from ergotools.infrastructure.draft_json import document_number as _number
from ergotools.infrastructure.draft_json import document_text as _text
from ergotools.infrastructure.draft_json import unique_object as _object


def decode_tst(payload: str) -> TstDraft:
    """Decode a complete draft or raise DocumentFormatError without partial data.

    Reject unknown versions/fields, duplicate JSON members, booleans masquerading as
    numbers, nonfinite values, invalid units and duplicate task identities. Version one
    retains model IDs; version two explicitly records their source convention. Missing
    direction stays null. No defaulting, calculation, migration or source-unit
    conversion occurs.

    Args:
        payload: Complete versioned source JSON text; null fields represent unfinished
            input, not zero.

    Returns:
        Complete immutable ST source; version one uses model direction IDs, version two
        retains its explicit saved convention.

    Raises:
        DocumentFormatError: JSON, version, direction convention/codes, units, numeric
            values or task identities are malformed.
    """
    try:
        envelope = json.loads(payload, object_pairs_hook=_object)
        if not isinstance(envelope, dict):
            raise DocumentFormatError("Expected a TST draft object.")
        version = envelope.get("version")
        if type(version) is not int or version not in (1, 2):
            raise DocumentFormatError("Unsupported document version.")
        expected = {"format", "version", "system", "tasks"}
        if version == 2:
            expected.add("direction_convention")
        data = _fields(envelope, expected)
        if data["format"] != "ergotools.tst-draft":
            raise DocumentFormatError("Unsupported document format.")
        system = MeasurementSystem(_text(data["system"]))
        if not isinstance(data["tasks"], list):
            raise DocumentFormatError("Tasks must be an array.")
        tasks = []
        for entry in data["tasks"]:
            task = _fields(
                entry, {"task_id", "direction", "lever_arm", "load", "repetitions"}
            )
            tasks.append(
                TstTask(
                    _text(task["task_id"]),
                    None
                    if task["direction"] is None
                    else TstDirection(_text(task["direction"])),
                    _number(task["lever_arm"]),
                    _number(task["load"]),
                    _number(task["repetitions"]),
                )
            )
        convention = (
            TstDirectionConvention.MODEL_CODES
            if version == 1
            else TstDirectionConvention(_text(data["direction_convention"]))
        )
        return TstDraft(system, tuple(tasks), convention)
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise DocumentFormatError("Invalid TST draft document.") from error


def encode_tst(draft: TstDraft) -> str:
    """Encode deterministically and validate before storage can start a write.

    Args:
        draft: Immutable source draft with original task identities, order and units; no
            calculations are serialized.

    Returns:
        Validated compact ASCII source JSON; emit version two only when an explicit
        nonmodel direction convention is required.

    Raises:
        DocumentFormatError: A direction is not typed/absent or the generated source
            fails strict decoding.
        ValueError: JSON encoding rejects a nonfinite source number.
    """
    if any(
        task.direction is not None and not isinstance(task.direction, TstDirection)
        for task in draft.tasks
    ):
        raise DocumentFormatError("Direction must be a model enum or absent.")
    data = {
        "format": "ergotools.tst-draft",
        "version": 1,
        "system": draft.system.value,
        "tasks": [
            {
                "task_id": task.task_id,
                "direction": task.direction,
                "lever_arm": task.lever_arm,
                "load": task.load,
                "repetitions": task.repetitions,
            }
            for task in draft.tasks
        ],
    }
    if draft.direction_convention is not TstDirectionConvention.MODEL_CODES:
        data["version"] = 2
        data["direction_convention"] = draft.direction_convention.value
    payload = json.dumps(
        data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    decode_tst(payload)
    return payload
