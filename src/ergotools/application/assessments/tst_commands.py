"""Pure TST draft commands for the application-owned undo/redo history.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass, replace
from typing import ClassVar

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import task_has_data
from ergotools.domain.assessments.tst_draft import (
    TstDraft,
    TstTask,
)
from ergotools.domain.assessments.validation import DraftError, InputIssue


def _expected_index(state: TstDraft, expected: TstTask) -> int:
    """Resolve a stable task identity and reject an obsolete expected row.

    Args:
        state: Current immutable source snapshot; successful edits return a replacement
            rather than mutating it.
        expected: Previously read exact task snapshot; compare all fields to reject
            stale edits.

    Returns:
        Zero-based source position of the expected stable task after exact row equality
        succeeds.

    Raises:
        DraftError: The stable task identity is absent or its complete current fields
            differ from expected.
    """
    index = state.task_index(expected.task_id)
    if state.tasks[index] != expected:
        raise DraftError(
            InputIssue("validation.stale_task", "task_id", expected.task_id)
        )
    return index


@dataclass(frozen=True, slots=True)
class AddTstTask:
    """Insert a stable task at an explicit zero-based position in one undo step.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        task: Typed stable-identity task to insert; calculation completeness is a
            separate rule.
        index: Zero-based insertion position, inclusive from zero through the current
            task count.
        label_key: Stable localization key describing the edit; None for the initial
            revision.
    """

    document: DocumentKey
    task: TstTask
    index: int
    label_key: ClassVar[str] = "edit.tst.add_task"

    def apply(self, state: TstDraft) -> TstDraft:
        """Validate position and uniqueness before constructing a new snapshot.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            DraftError: Insertion is outside 0..task count, or the resulting draft has
                duplicate task identities.
        """
        if not 0 <= self.index <= len(state.tasks):
            raise DraftError(
                InputIssue("validation.position", "index", self.task.task_id)
            )
        tasks = (*state.tasks[: self.index], self.task, *state.tasks[self.index :])
        return replace(state, tasks=tasks)


@dataclass(frozen=True, slots=True)
class ReplaceTstTask:
    """Replace all fields atomically while preserving task identity and position.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        expected: Exact previously read row or source snapshot whose equality is
            required before applying the edit.
        replacement: Proposed immutable row/grid retaining the ownership and unit
            identities required above.
        label_key: Stable localization key describing the edit; None for the initial
            revision.
    """

    document: DocumentKey
    expected: TstTask
    replacement: TstTask
    label_key: ClassVar[str] = "edit.tst.replace_task"

    def apply(self, state: TstDraft) -> TstDraft:
        """Reject stale fields or identity changes without mutating source state.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            DraftError: The expected task is absent/stale or the replacement changes its
                stable identity.
        """
        index = _expected_index(state, self.expected)
        if self.expected.task_id != self.replacement.task_id:
            raise DraftError(
                InputIssue("validation.identity", "task_id", self.expected.task_id)
            )
        tasks = (*state.tasks[:index], self.replacement, *state.tasks[index + 1 :])
        return replace(state, tasks=tasks)


@dataclass(frozen=True, slots=True)
class RemoveTstTask:
    """Remove a task only when its current fields match the expected snapshot.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        expected: Exact previously read row or source snapshot whose equality is
            required before applying the edit.
        label_key: Stable localization key describing the edit; None for the initial
            revision.
    """

    document: DocumentKey
    expected: TstTask
    label_key: ClassVar[str] = "edit.tst.remove_task"

    def apply(self, state: TstDraft) -> TstDraft:
        """Remove the matching task; history retains its exact value and position.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            DraftError: The expected stable task is absent or its current fields differ
                from the saved expected row.
        """
        index = _expected_index(state, self.expected)
        return replace(state, tasks=(*state.tasks[:index], *state.tasks[index + 1 :]))


@dataclass(frozen=True, slots=True)
class ReplaceTstInputs:
    """Replace a complete grid in one edit, retaining source units and task IDs.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        expected: Exact previously read row or source snapshot whose equality is
            required before applying the edit.
        replacement: Proposed immutable row/grid retaining the ownership and unit
            identities required above.
        label_key: Stable localization key describing the edit; None for the initial
            revision.
    """

    document: DocumentKey
    expected: TstDraft
    replacement: TstDraft
    label_key: ClassVar[str] = "edit.tst.replace_task"

    def apply(self, state: TstDraft) -> TstDraft:
        """Reject changed source, reordered identities or unit reinterpretation.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            DraftError: Source differs from expected, task identities/order change, or
                source units/direction convention are reinterpreted.
        """
        if state != self.expected:
            raise DraftError(InputIssue("validation.stale_task", "source"))
        if (
            state.system is not self.replacement.system
            or state.direction_convention is not self.replacement.direction_convention
            or tuple(task.task_id for task in state.tasks)
            != tuple(task.task_id for task in self.replacement.tasks)
        ):
            raise DraftError(InputIssue("validation.identity", "source"))
        return self.replacement


@dataclass(frozen=True, slots=True)
class SetTstTaskCount:
    """Resize this assessment to 1-100 rows, retaining its existing prefix.

    Attributes:
        document: Exact project/document owner of this command or captured preparation.
        expected: Exact previously read row or source snapshot whose equality is
            required before applying the edit.
        tasks: Exact retained prefix followed only by fresh default blank slots,
            or a shortened prefix. Counts are local to this assessment.
        label_key: Stable localization key describing the edit; None for the initial
            revision.
    """

    document: DocumentKey
    expected: TstDraft
    tasks: tuple[TstTask, ...]
    label_key: ClassVar[str] = "edit.tst.task_count"

    def apply(self, state: TstDraft) -> TstDraft:
        """Reject stale input, modified retained rows and nonblank appended slots.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            DraftError: Source differs from expected, count is outside 1-100, rows are
                not an unchanged prefix with blank appended slots, or IDs duplicate.
        """
        if state != self.expected:
            raise DraftError(InputIssue("validation.stale_task", "source"))
        retained = min(len(state.tasks), len(self.tasks))
        if (
            not 1 <= len(self.tasks) <= 100
            or self.tasks[:retained] != state.tasks[:retained]
            or any(task_has_data(task) for task in self.tasks[retained:])
        ):
            raise DraftError(InputIssue("validation.position", "tasks"))
        return replace(state, tasks=self.tasks)
