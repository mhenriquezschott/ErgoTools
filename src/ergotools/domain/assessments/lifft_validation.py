"""Shared LiFFT input validation for calculation and assessment preparation.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.assessments.validation import (
    validate_nonnegative_input as validate_lifft_input,
)

__all__ = ["lifft_draft_issues", "validate_lifft_input"]


def lifft_draft_issues(draft: LifftDraft) -> tuple[InputIssue, ...]:
    """Collect all input issues in task/field order without calculating or mutating.

    An empty draft needs a task; a complete all-zero task is valid input. A clean result
    does not certify scientific validity or guarantee finite arithmetic.

    Args:
        draft: Ordered immutable source tasks; this operation neither edits nor
            evaluates them.

    Returns:
        All numeric issues in task/field order, or a tasks-required issue for an empty
        draft.
    """
    if not draft.tasks:
        return (InputIssue("validation.tasks_required", "tasks"),)
    issues: list[InputIssue] = []
    for task in draft.tasks:
        for field, value in (
            ("lever_arm", task.lever_arm),
            ("load", task.load),
            ("repetitions", task.repetitions),
        ):
            try:
                validate_lifft_input(value, field, task.task_id)
            except DraftError as error:
                issues.append(error.issue)
    return tuple(issues)
