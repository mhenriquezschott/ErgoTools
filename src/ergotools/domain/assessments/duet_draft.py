"""Ordered DUET source drafts and complete input issues, without calculation.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.duet import DuetTask, validate_duet_scale
from ergotools.domain.assessments.validation import (
    DraftError,
    InputIssue,
    validate_nonnegative_input,
)

__all__ = ["DuetDraft", "DuetTask", "duet_draft_issues"]


@dataclass(frozen=True, slots=True)
class DuetDraft:
    """Immutable ordered tasks with distinct stable identities; no unit conversion.

    Attributes:
        tasks: Ordered immutable source tasks; absence remains None in individual
            fields.
    """

    tasks: tuple[DuetTask, ...] = ()

    def __post_init__(self) -> None:
        """Snapshot task order and reject duplicate identities before history use.

        Args:
            None. Dataclass construction supplies the fields documented on DuetDraft.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            tasks as immutable tuples on the new frozen instance.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
        """
        object.__setattr__(self, "tasks", tuple(self.tasks))
        seen: set[str] = set()
        for task in self.tasks:
            if task.task_id in seen:
                raise DraftError(
                    InputIssue("validation.duplicate", "task_id", task.task_id)
                )
            seen.add(task.task_id)

    def task_index(self, task_id: str) -> int:
        """Find a task by stable identity or raise a structured missing-task issue.

        Args:
            task_id: Stable task identity used for lookup or field-specific validation
                diagnostics.

        Returns:
            Zero-based position of the exact task ID in the saved source order.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
        """
        for index, task in enumerate(self.tasks):
            if task.task_id == task_id:
                return index
        raise DraftError(InputIssue("validation.missing_task", "task_id", task_id))


def duet_draft_issues(draft: DuetDraft) -> tuple[InputIssue, ...]:
    """Collect every scale/repetition issue in row order; empty drafts need a task.

    Args:
        draft: Ordered immutable source tasks; this operation neither edits nor
            evaluates them.

    Returns:
        All field issues in task order, or a tasks-required issue for an empty draft; no
        exception for invalid fields.
    """
    if not draft.tasks:
        return (InputIssue("validation.tasks_required", "tasks"),)
    issues: list[InputIssue] = []
    for task in draft.tasks:
        try:
            validate_duet_scale(task.omni_res_scale, task.task_id)
        except DraftError as error:
            issues.append(error.issue)
        try:
            validate_nonnegative_input(task.repetitions, "repetitions", task.task_id)
        except DraftError as error:
            issues.append(error.issue)
    return tuple(issues)
