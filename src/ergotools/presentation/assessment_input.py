"""Text-to-edit boundary for dimensional assessment fields; no widget dependency.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from typing import Literal

from ergotools.application.assessments.unit_edits import edit_display_input
from ergotools.application.assessments.unit_view import AssessmentUnitView
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.presentation.numeric_input import DecimalConvention, parse_input_number


def edit_display_text(
    active: DocumentSession[AssessmentDraft],
    view: AssessmentUnitView,
    task_id: str,
    field: Literal["lever_arm", "load"],
    text: str,
    convention: DecimalConvention,
) -> bool:
    """Parse one deliberately changed field and execute its undoable source edit.

    Stale source is rejected before parsing. Invalid text never clears or rewrites
    source. Blank input explicitly clears the field; untouched editors must not be
    submitted. Caller owns the current projection and decimal convention, including what
    to do with uncommitted text when those preferences change. Language and measurement
    units never select the separator implicitly. No I/O occurs.

    Args:
        active: Current owner-thread assessment session receiving the Undo command.
        view: Exact current source-bound display-unit projection used to initialize the
            edited field.
        task_id: Stable source row identity.
        field: Dimensional lever_arm or load input to change.
        text: Deliberately edited complete text; blank explicitly clears, untouched
            editors must not submit.
        convention: Explicit point/comma decimal policy independent of language and
            measurement system.

    Returns:
        True for a recorded source edit; False when parsed source value is unchanged.

    Raises:
        DraftError: View is stale, text/field is invalid or numeric conversion fails.
        RuntimeError: Source command violates session owner-thread/reentrancy guards.
    """
    if not view.is_current(active):
        raise DraftError(InputIssue("validation.stale_view", "source", task_id))
    value = parse_input_number(text, convention, field, task_id)
    return edit_display_input(active, view, task_id, field, value)
