"""Ordered TST source drafts and complete input issues, without calculation.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass, replace
from enum import StrEnum

from ergotools.domain.assessments.tst import (
    TstDirection,
    TstTask,
    validate_tst_direction,
)
from ergotools.domain.assessments.validation import (
    DraftError,
    InputIssue,
    validate_nonnegative_input,
)
from ergotools.domain.model_units import MeasurementSystem

__all__ = ["TstDraft", "TstTask", "tst_draft_issues"]


class TstDirectionConvention(StrEnum):
    """Interpret saved direction codes without changing original labels or formulas.

    MODEL_CODES retains existing version-one new-format documents. REFERENCE_UI retains
    original dropdown positions; main.py swaps 1/2 before model invocation. This records
    compatibility, not a judgment about scientific direction names.
    """

    # Saved values already use calculator branch IDs; do not swap 1/2.
    MODEL_CODES = "model_codes"
    # Saved values are original selector positions; swap downward/horizontal at model
    # projection.
    REFERENCE_UI = "reference_ui"


@dataclass(frozen=True, slots=True)
class TstDraft:
    """Immutable ordered tasks with distinct stable identities and original units.

    Attributes:
        system: Explicit original arm/force system: cm/N or inches/lbf; independent of
            interface language.
        tasks: Ordered immutable source tasks; absence remains None in individual
            fields.
        direction_convention: Explicit interpretation of saved direction values; only
            reference UI codes swap model branches 1/2.
    """

    system: MeasurementSystem
    tasks: tuple[TstTask, ...] = ()
    direction_convention: TstDirectionConvention = TstDirectionConvention.MODEL_CODES

    def __post_init__(self) -> None:
        """Snapshot task order and reject duplicate identities before history use.

        Args:
            None. Dataclass construction supplies the fields documented on TstDraft.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            tasks as immutable tuples on the new frozen instance.

        Raises:
            DraftError: Source structure, completeness, numeric validity or task
                identity violates the constraints described above; issue retains
                field/task context.
            ValueError: ST source requires an explicit direction convention.
        """
        if not isinstance(self.system, MeasurementSystem):
            raise DraftError(InputIssue("validation.unit", "system"))
        if not isinstance(self.direction_convention, TstDirectionConvention):
            raise ValueError("ST source requires an explicit direction convention.")
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

    def model_task(self, task_id: str) -> TstTask:
        """Project one source task into the unchanged calculator's direction codes.

        This pure projection performs no evaluation or source mutation. Source labels,
        quantities, task identity and units stay unchanged. Reference downward selects
        model branch 2; horizontal selects branch 1. A missing direction remains
        missing. Unknown task identities raise DraftError.

        Args:
            task_id: Stable task identity used for lookup or field-specific validation
                diagnostics.

        Returns:
            A new task snapshot carrying calculator direction codes; the stored source
            remains unchanged.

        Raises:
            DraftError: The requested task identity is absent; no source or direction is
                changed.
        """
        task = self.tasks[self.task_index(task_id)]
        direction = task.direction
        if self.direction_convention is TstDirectionConvention.REFERENCE_UI:
            if direction is TstDirection.DOWNWARD:
                direction = TstDirection.HORIZONTAL
            elif direction is TstDirection.HORIZONTAL:
                direction = TstDirection.DOWNWARD
        return replace(task, direction=direction)


def tst_draft_issues(draft: TstDraft) -> tuple[InputIssue, ...]:
    """Collect every direction/numeric issue in row order; empty drafts need a task.

    Args:
        draft: Ordered immutable source tasks; this operation neither edits nor
            evaluates them.

    Returns:
        Direction and numeric issues in task/field order, or a tasks-required issue for
        an empty draft.
    """
    if not draft.tasks:
        return (InputIssue("validation.tasks_required", "tasks"),)
    issues: list[InputIssue] = []
    for task in draft.tasks:
        try:
            validate_tst_direction(task.direction, task.task_id)
        except DraftError as error:
            issues.append(error.issue)
        for field_name, value in (
            ("lever_arm", task.lever_arm),
            ("load", task.load),
            ("repetitions", task.repetitions),
        ):
            try:
                validate_nonnegative_input(value, field_name, task.task_id)
            except DraftError as error:
                issues.append(error.issue)
    return tuple(issues)
