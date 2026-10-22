"""Strict version-one DUET source format, independent of legacy project schemas.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import json

from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.infrastructure.draft_json import (
    DocumentFormatError,
    document_fields,
    document_number,
    document_text,
    unique_object,
)


def decode_duet(payload: str) -> DuetDraft:
    """Decode all source fields or reject the entire payload without partial data.

    Preserve missing values and finite signed repetitions for later correction. Scale
    must be an integer or null; out-of-range integers remain editable. Reject duplicate
    keys/IDs, unknown fields/versions, booleans and nonfinite data.

    Args:
        payload: Complete versioned source JSON text; null fields represent unfinished
            input, not zero.

    Returns:
        Complete immutable version-one unit-independent source with integer-or-null OMNI
        indices and signed finite repetitions.

    Raises:
        DocumentFormatError: JSON, version, fields, primitive types or task identities
            are malformed; out-of-range integer OMNI values remain editable.
    """
    try:
        data = document_fields(
            json.loads(payload, object_pairs_hook=unique_object),
            {"format", "version", "tasks"},
        )
        if data["format"] != "ergotools.duet-draft":
            raise DocumentFormatError("Unsupported document format.")
        if type(data["version"]) is not int or data["version"] != 1:
            raise DocumentFormatError("Unsupported document version.")
        if not isinstance(data["tasks"], list):
            raise DocumentFormatError("Tasks must be an array.")
        tasks = []
        for entry in data["tasks"]:
            task = document_fields(entry, {"task_id", "omni_res_scale", "repetitions"})
            scale = task["omni_res_scale"]
            if scale is not None and type(scale) is not int:
                raise DocumentFormatError("Scale must be an integer or null.")
            tasks.append(
                DuetTask(
                    document_text(task["task_id"]),
                    scale,
                    document_number(task["repetitions"]),
                )
            )
        return DuetDraft(tuple(tasks))
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise DocumentFormatError("Invalid DUET draft document.") from error


def encode_duet(draft: DuetDraft) -> str:
    """Serialize deterministically and validate before any storage write begins.

    Args:
        draft: Immutable source draft with original task identities, order and units; no
            calculations are serialized.

    Returns:
        Deterministic compact ASCII source JSON preserving unfinished fields and input
        order, validated before any write.

    Raises:
        DocumentFormatError: The generated source fails strict decoding.
        ValueError: JSON encoding rejects a nonfinite source number.
    """
    data = {
        "format": "ergotools.duet-draft",
        "version": 1,
        "tasks": [
            {
                "task_id": task.task_id,
                "omni_res_scale": task.omni_res_scale,
                "repetitions": task.repetitions,
            }
            for task in draft.tasks
        ],
    }
    payload = json.dumps(
        data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    decode_duet(payload)
    return payload
