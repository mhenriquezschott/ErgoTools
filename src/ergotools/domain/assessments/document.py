"""Explicit supported source types for multi-assessment project documents.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from enum import StrEnum

from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft

type AssessmentDraft = LifftDraft | DuetDraft | TstDraft


class AssessmentKind(StrEnum):
    """Stable model identity for catalogs, independent of display language."""

    # Stable LiFFT model key for stored ownership and dispatch.
    LIFFT = "lifft"
    # Stable DUET model key for stored ownership and dispatch.
    DUET = "duet"
    # Stable Shoulder Tool key; the visible UI uses ST branding.
    TST = "tst"


def assessment_kind(source: AssessmentDraft) -> AssessmentKind:
    """Identify a supported source without inferring its model from task content.

    Args:
        source: Immutable assessment source; the draft type establishes the model.

    Returns:
        Supported model identity determined from the draft type, without inspecting task
        values.

    Raises:
        ValueError: Unsupported assessment source type.
    """
    if isinstance(source, LifftDraft):
        return AssessmentKind.LIFFT
    if isinstance(source, DuetDraft):
        return AssessmentKind.DUET
    if isinstance(source, TstDraft):
        return AssessmentKind.TST
    raise ValueError("Unsupported assessment source type.")


def task_has_data(task: LifftTask | DuetTask | TstTask) -> bool:
    """Distinguish entered rows from unused default grid capacity.

    Args:
        task: Immutable source row, before any model/ST-direction projection.

    Returns:
        True for any entered numeric value, including zero, or a nondefault selector.
        DUET's default scale zero and ST's default direction alone are unused slots.
        A changed selector with missing measurements is a started, incomplete row.
        No validation, calculation or source mutation occurs here.
    """
    if isinstance(task, DuetTask):
        return task.repetitions is not None or task.omni_res_scale not in (None, 0)
    return (
        isinstance(task, TstTask) and task.direction is not TstDirection.HANDLING_LOADS
    ) or any(
        value is not None for value in (task.lever_arm, task.load, task.repetitions)
    )
