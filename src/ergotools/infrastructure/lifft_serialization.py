"""Strict version-one interchange format for source LiFFT drafts, not .ergprj.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import json

from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.draft_json import (
    DocumentFormatError as DocumentFormatError,
)
from ergotools.infrastructure.draft_json import document_fields as _fields
from ergotools.infrastructure.draft_json import document_number as _number
from ergotools.infrastructure.draft_json import document_text as _text
from ergotools.infrastructure.draft_json import unique_object as _object


def decode_lifft(payload: str) -> LifftDraft:
    """Decode a complete draft or raise DocumentFormatError without partial data.

    Reject unknown versions/fields, duplicate JSON members, booleans masquerading as
    numbers, nonfinite values, invalid units and duplicate task identities. No
    defaulting, calculation, migration or source-unit conversion occurs.

    Args:
        payload: Complete versioned source JSON text; null fields represent unfinished
            input, not zero.

    Returns:
        Complete immutable version-one source draft with original cm/N or inch/lbf
        metadata and explicit missing values.

    Raises:
        DocumentFormatError: JSON, version, fields, units, number types or task
            identities are malformed; never return partial data.
    """
    try:
        data = _fields(
            json.loads(payload, object_pairs_hook=_object),
            {"format", "version", "system", "tasks"},
        )
        if data["format"] != "ergotools.lifft-draft":
            raise DocumentFormatError("Unsupported document format.")
        if type(data["version"]) is not int or data["version"] != 1:
            raise DocumentFormatError("Unsupported document version.")
        system = MeasurementSystem(_text(data["system"]))
        if not isinstance(data["tasks"], list):
            raise DocumentFormatError("Tasks must be an array.")
        tasks = []
        for entry in data["tasks"]:
            task = _fields(entry, {"task_id", "lever_arm", "load", "repetitions"})
            tasks.append(
                LifftTask(
                    _text(task["task_id"]),
                    _number(task["lever_arm"]),
                    _number(task["load"]),
                    _number(task["repetitions"]),
                )
            )
        return LifftDraft(system, tuple(tasks))
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise DocumentFormatError("Invalid LiFFT draft document.") from error


def encode_lifft(draft: LifftDraft) -> str:
    """Encode deterministically and validate before storage can start a write.

    Args:
        draft: Immutable source draft with original task identities, order and units; no
            calculations are serialized.

    Returns:
        Deterministic compact ASCII JSON validated by the same decoder before return; no
        derived values or writes.

    Raises:
        DocumentFormatError: The generated source fails strict decoding.
        ValueError: JSON encoding rejects a nonfinite source number.
    """
    data = {
        "format": "ergotools.lifft-draft",
        "version": 1,
        "system": draft.system.value,
        "tasks": [
            {
                "task_id": task.task_id,
                "lever_arm": task.lever_arm,
                "load": task.load,
                "repetitions": task.repetitions,
            }
            for task in draft.tasks
        ],
    }
    payload = json.dumps(
        data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    decode_lifft(payload)
    return payload
