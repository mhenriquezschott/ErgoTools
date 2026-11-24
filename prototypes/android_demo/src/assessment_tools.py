"""Mobile tool metadata and typed input projection; no formulas or persistence.

Share one touch editor across LiFFT/DUET/ST while retaining source units and ST's
recorded direction convention. Labels mirror desktop; evaluators remain in core.
"""

from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDirectionConvention, TstDraft
from ergotools.domain.model_units import MeasurementSystem

type AssessmentTask = LifftTask | DuetTask | TstTask

# Branding/assets copied from the desktop package, independent of stored model IDs.
TOOLS = {
    AssessmentKind.LIFFT: (
        "LiFFT",
        "Lifting Fatigue Failure Tool (LiFFT)",
        "lifft.png",
    ),
    AssessmentKind.DUET: ("DUET", "Distal Upper Extremity Tool (DUET)", "duet.png"),
    AssessmentKind.TST: ("ST", "The Shoulder Tool (ST)", "shoulder.png"),
}
# Same descriptive ratings as the desktop OMNI-Res selector; odd indices unnamed.
OMNI_LABELS = (
    "Extremely Easy",
    "",
    "Easy",
    "",
    "Somewhat Easy",
    "",
    "Somewhat Hard",
    "",
    "Hard",
    "",
    "Extremely Hard",
)
# Typed source IDs retain their original labels; the core projects convention once.
DIRECTION_LABELS = (
    (TstDirection.HANDLING_LOADS, "Handling Loads"),
    (TstDirection.DOWNWARD, "Push or Pull Downward"),
    (TstDirection.HORIZONTAL, "Horizontal Push or Pull"),
)


def numeric_fields(source: AssessmentDraft) -> tuple[str, ...]:
    """Return only editable numeric fields, excluding each tool's discrete selector.

    Args:
        source: Immutable native source in its original units/convention.

    Returns:
        Stable field names in source input order.
    """
    return (
        ("repetitions",)
        if isinstance(source, DuetDraft)
        else ("lever_arm", "load", "repetitions")
    )


def input_fields(source: AssessmentDraft) -> tuple[str, ...]:
    """Return all scientific inputs, including selectors, for completeness and clear.

    Args:
        source: Typed native draft.

    Returns:
        Ordered fields required for a complete task.
    """
    prefix = (
        ("omni_res_scale",)
        if isinstance(source, DuetDraft)
        else ("direction",)
        if isinstance(source, TstDraft)
        else ()
    )
    return (*prefix, *numeric_fields(source))


def source_units(source: AssessmentDraft) -> MeasurementSystem:
    """Resolve source units, using metric only as DUET's dimensionless result label.

    Args:
        source: Native draft; DUET has no physical measurements.

    Returns:
        Existing physical units or the conventional metric label for DUET.
    """
    return MeasurementSystem.METRIC if isinstance(source, DuetDraft) else source.system


def new_source(
    kind: AssessmentKind, units: MeasurementSystem, task_id: str
) -> AssessmentDraft:
    """Create one blank task using the same discrete defaults as desktop controls.

    Args:
        kind: Exact selected tool identity.
        units: Project defaults for LiFFT/ST only.
        task_id: New unique source-row identity.

    Returns:
        Typed draft; ST uses the established reference UI direction convention.
    """
    if kind is AssessmentKind.DUET:
        return DuetDraft((DuetTask(task_id, omni_res_scale=0),))
    if kind is AssessmentKind.TST:
        return TstDraft(
            units,
            (TstTask(task_id, TstDirection.HANDLING_LOADS),),
            TstDirectionConvention.REFERENCE_UI,
        )
    return LifftDraft(units, (LifftTask(task_id),))


def task_summary(source: AssessmentDraft, task: AssessmentTask) -> str:
    """Describe a complete task in current source units without recalculating it.

    Args:
        source: Current native draft.
        task: A complete row from that draft.

    Returns:
        Short readable input summary suitable for the task list.
    """
    if isinstance(source, DuetDraft):
        return f"OMNI-Res {task.omni_res_scale} · {task.repetitions:g} repetitions"
    prefix = (
        f"{dict(DIRECTION_LABELS)[task.direction]} · "
        if isinstance(source, TstDraft)
        else ""
    )
    return (
        f"{prefix}{task.lever_arm:g} · {task.load:g} · {task.repetitions:g} repetitions"
    )


def tool_name(source: AssessmentDraft) -> str:
    """Return public branding without exposing TST's historical storage key.

    Args:
        source: Native typed draft.

    Returns:
        LiFFT, DUET or ST.
    """
    return TOOLS[assessment_kind(source)][0]
