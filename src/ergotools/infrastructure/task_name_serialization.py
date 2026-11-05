"""Strict optional task-name fields shared by the three source interchange codecs.

Infrastructure layer. Unnamed source encodings remain byte-compatible. Named codec
versions require both explicit metadata members, including null for no reference;
unknown fields stay rejected by each owning codec. No catalog lookup or I/O occurs.
"""

from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.task_catalog import validate_task_label
from ergotools.infrastructure.draft_json import DocumentFormatError


def task_name_fields(draft: AssessmentDraft) -> bool:
    """Determine whether a source needs the named-task codec capability.

    Args:
        draft: Immutable LiFFT/DUET/ST source in original units and row order.

    Returns:
        True if any row carries an activity name or reusable definition reference.
    """
    return any(
        t.task_name is not None or t.task_definition_id is not None for t in draft.tasks
    )


def decode_task_name(
    data: dict[str, object], named: bool
) -> tuple[str | None, str | None]:
    """Read explicit optional metadata without coercion or fabricated definitions.

    Args:
        data: Strict row members validated by the owning tool codec.
        named: Whether that codec version requires task metadata members.

    Returns:
        Literal optional name and definition identity; both absent for unnamed codecs.

    Raises:
        DocumentFormatError: A metadata member has an invalid primitive or reference.
    """
    if not named:
        return None, None
    name, identity = data["task_name"], data["task_definition_id"]
    if (name is not None and not isinstance(name, str)) or (
        identity is not None and not isinstance(identity, str)
    ):
        raise DocumentFormatError("Task name/reference must be text or null.")
    try:
        validate_task_label(name, identity)
    except ValueError as error:
        raise DocumentFormatError("Invalid task name/reference.") from error
    return name, identity
