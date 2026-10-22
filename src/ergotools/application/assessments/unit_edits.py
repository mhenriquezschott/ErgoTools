"""Explicit single-field edits from display units into original assessment units.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import replace
from typing import Literal

from ergotools.application.assessments.lifft_commands import ReplaceLifftTask
from ergotools.application.assessments.project_edits import (
    LifftProjectEdit,
    TstProjectEdit,
)
from ergotools.application.assessments.tst_commands import ReplaceTstTask
from ergotools.application.assessments.unit_view import AssessmentUnitView
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.model_units import project_model_input


def edit_display_input(
    active: DocumentSession[AssessmentDraft],
    view: AssessmentUnitView,
    task_id: str,
    field: Literal["lever_arm", "load"],
    value: float | None,
) -> bool:
    """Apply one deliberately edited quantity as one source-history command.

    Only the named field is converted back to recorded units. All other fields, task
    identities, ordering and source units survive exactly. Signed finite values remain
    editable for review. No parsing, calculation or I/O occurs. The caller must use its
    currently displayed projection after a view-unit change; source freshness alone
    cannot identify obsolete display preferences.

    Args:
        active: Actual active session, used to reject stale or foreign projections.
        view: Projection whose units the caller used to parse the entered value.
        task_id: Stable task identity, never a row index.
        field: Dimensional source field explicitly edited by the user.
        value: Unrounded parsed display value; None explicitly clears this field.

    Returns:
        Whether source changed. Re-entering the exact projected value is a no-op,
        retaining original precision and any redo branch without round-trip drift.

    Raises:
        DraftError: Stale view, absent task or invalid/unrepresentable number.
        ValueError: Unsupported quantity or unitless assessment.
    """
    if not view.is_current(active):
        raise DraftError(InputIssue("validation.stale_view", "source", task_id))
    source = active.state
    if isinstance(source, DuetDraft):
        raise ValueError("DUET source has no dimensional inputs to edit.")
    if field not in ("lever_arm", "load"):
        raise ValueError("Unsupported model input quantity.")
    task = source.tasks[source.task_index(task_id)]
    original = task.lever_arm if field == "lever_arm" else task.load
    # Validate before equality: True must not compare equal to a displayed 1.
    entered = project_model_input(value, field, task_id, view.system, view.system)
    displayed = project_model_input(
        original, field, task_id, source.system, view.system
    )
    if entered == displayed:
        return False
    converted = project_model_input(entered, field, task_id, view.system, source.system)
    if isinstance(source, LifftDraft):
        expected = source.tasks[source.task_index(task_id)]
        replacement = (
            replace(expected, lever_arm=converted)
            if field == "lever_arm"
            else replace(expected, load=converted)
        )
        return active.execute(
            LifftProjectEdit(ReplaceLifftTask(active.document, expected, replacement))
        )
    expected_tst = source.tasks[source.task_index(task_id)]
    replacement_tst = (
        replace(expected_tst, lever_arm=converted)
        if field == "lever_arm"
        else replace(expected_tst, load=converted)
    )
    return active.execute(
        TstProjectEdit(ReplaceTstTask(active.document, expected_tst, replacement_tst))
    )
