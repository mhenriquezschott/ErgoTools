"""Atomic ordered task-row removal for every assessment input host.

Application layer. Preserve retained task IDs, names, units and exact quantities;
empty editors retain one blank starter. Hosts own pending inputs, confirmation,
calculation, Undo and persistence. No Qt, storage or formula code is used here.
"""

from dataclasses import replace
from uuid import uuid4

from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet import DuetTask
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask


def remove_assessment_rows(
    source: AssessmentDraft, rows: tuple[int, ...]
) -> AssessmentDraft:
    """Remove distinct selected rows once, leaving the remaining rows in source order.

    Args:
        source: Frozen canonical input, never its rounded display projection.
        rows: Zero-based positions; duplicates are harmless, invalid indices rejected.

    Returns:
        Same-tool replacement, with one new blank starter if every row is removed.

    Raises:
        ValueError: No rows or an invalid/noninteger row is supplied.
    """
    if not rows or any(
        type(r) is not int or not 0 <= r < len(source.tasks) for r in rows
    ):
        raise ValueError("Select valid task rows to remove.")
    selected = set(rows)
    if isinstance(source, LifftDraft):
        tasks = tuple(t for i, t in enumerate(source.tasks) if i not in selected)
        return replace(source, tasks=tasks or (LifftTask(uuid4().hex),))
    if isinstance(source, DuetDraft):
        duet = tuple(t for i, t in enumerate(source.tasks) if i not in selected)
        return replace(source, tasks=duet or (DuetTask(uuid4().hex, 0),))
    shoulder = tuple(t for i, t in enumerate(source.tasks) if i not in selected)
    return replace(
        source, tasks=shoulder or (TstTask(uuid4().hex, TstDirection.HANDLING_LOADS),)
    )
