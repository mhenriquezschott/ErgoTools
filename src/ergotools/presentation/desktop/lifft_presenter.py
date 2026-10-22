"""Widget-independent LiFFT desktop coordination over existing application ports.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from dataclasses import replace
from typing import Literal
from uuid import uuid4

from ergotools.application.assessments.evaluation import AssessmentEvaluator
from ergotools.application.assessments.lifft_commands import (
    AddLifftTask,
    RemoveLifftTask,
    ReplaceLifftInputs,
    ReplaceLifftTask,
    SetLifftTaskCount,
)
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.model_units import MeasurementSystem, project_model_input
from ergotools.presentation.edit_context import AssessmentEditor, EditContext
from ergotools.presentation.numeric_input import DecimalConvention, parse_input_number


class LifftPresenter:
    """Coordinate a single active LiFFT source without owning widgets or storage."""

    def __init__(self, workspace: ProjectWorkspace[AssessmentDraft]) -> None:
        """Receive project ownership and start independent display preferences.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.

        Returns:
            None.
        """
        self.workspace = workspace
        self.editor = AssessmentEditor()
        self.evaluator = AssessmentEvaluator()
        self.system = MeasurementSystem.IMPERIAL
        self.convention = DecimalConvention.POINT

    def source(self) -> LifftDraft | None:
        """Return active LiFFT source; unsupported models fail before display.

        Args:
            None.

        Returns:
            Committed LiFFT draft in its stored source units, or None without an active
            source; another tool is rejected.

        Raises:
            ValueError: This screen supports LiFFT assessments only.
        """
        active = self.workspace.active
        if active is None:
            return None
        if not isinstance(active.state, LifftDraft):
            raise ValueError("This screen supports LiFFT assessments only.")
        return active.state

    def bind(self) -> EditContext | None:
        """Replace the input context after rendering or a preference change.

        Args:
            None.

        Returns:
            Fresh source/preference-bound edit context projecting arm/load values into
            display units, or None with no active source.

        Raises:
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        self.editor.clear()
        active = self.workspace.active
        self.source()
        return (
            self.editor.bind(active, self.system, self.convention)
            if active is not None
            else None
        )

    def commit(
        self,
        context: EditContext,
        task_id: str,
        field: Literal["lever_arm", "load", "repetitions"],
        text: str,
    ) -> bool:
        """Commit one deliberate field, keeping failed input and history intact.

        Args:
            context: Exact current source/display interpretation captured when the
                grid was bound; stale interpretations fail before mutation.
            task_id: Stable task identity from the bound source, independent of row
                position.
            field: Typed input field identity to commit, or the line editor being
                inspected.
            text: Literal control text or user input; interpretation follows this
                method's stated policy.

        Returns:
            True only when the deliberate field edit records a changed canonical source
            value; False for exact re-entry without a change.

        Raises:
            RuntimeError: No assessment is open.
            DraftError: Input parsing, task identity or the exact bound source/display
                context fails validation; pending text is preserved.
        """
        active = self.workspace.active
        if field != "repetitions":
            return self.editor.submit(active, context, task_id, field, text)
        if active is None or self.editor.current(active) is not context:
            raise DraftError(InputIssue("validation.stale_editor", "source", task_id))
        source = self.source()
        if source is None:
            raise RuntimeError("No assessment is open.")
        task = source.tasks[source.task_index(task_id)]
        value = parse_input_number(text, context.convention, field, task_id)
        changed = active.execute(
            LifftProjectEdit(
                ReplaceLifftTask(
                    active.document, task, replace(task, repetitions=value)
                )
            )
        )
        if changed:
            self.editor.clear()
        return changed

    def add(self) -> str:
        """Append one unfinished task as one undo step and return its identity.

        Args:
            None.

        Returns:
            Fresh stable identity of the appended unfinished task, recorded as one undo
            operation.

        Raises:
            RuntimeError: No assessment is open.
        """
        active = self.workspace.active
        source = self.source()
        if active is None or source is None:
            raise RuntimeError("No assessment is open.")
        task_id = uuid4().hex
        active.execute(
            LifftProjectEdit(
                AddLifftTask(active.document, LifftTask(task_id), len(source.tasks))
            )
        )
        return task_id

    def set_task_count(self, count: int) -> None:
        """Resize only this assessment, retaining the prefix and appending blank rows.

        Args:
            count: Accepted task count, an integer from 1 through 100; booleans are
                rejected.

        Returns:
            None.

        Raises:
            DraftError: Input parsing, task identity or the exact bound source/display
                context fails validation; pending text is preserved.
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        source = self.source()
        active = self.workspace.active
        if source is None or active is None:
            return
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or not 1 <= count <= 100
        ):
            raise DraftError(InputIssue("validation.position", "tasks"))
        if count == len(source.tasks):
            return
        tasks = source.tasks[:count] + tuple(
            LifftTask(uuid4().hex) for _ in range(max(0, count - len(source.tasks)))
        )
        active.execute(
            LifftProjectEdit(SetLifftTaskCount(active.document, source, tasks))
        )
        self.evaluator.clear()

    def remove(self, task_id: str) -> None:
        """Remove only the selected snapshot; undo restores its position/values.

        Args:
            task_id: Stable task identity from the bound source, independent of row
                position.

        Returns:
            None.

        Raises:
            RuntimeError: No assessment is open.
        """
        active = self.workspace.active
        source = self.source()
        if active is None or source is None:
            raise RuntimeError("No assessment is open.")
        task = source.tasks[source.task_index(task_id)]
        active.execute(LifftProjectEdit(RemoveLifftTask(active.document, task)))

    def commit_grid(
        self,
        context: EditContext,
        rows: tuple[tuple[str, str, str, str], ...],
        *,
        cell: tuple[str, int] | None = None,
    ) -> bool:
        """Accept one completed cell or an explicit grid as one atomic source edit.

        Rows contain task ID, lever arm, load and repetitions in displayed units.
        Invalid text leaves source and context unchanged. Exact re-entry preserves
        canonical values without round-trip conversion. No calculation or I/O occurs.

        Args:
            context: Exact current source/display interpretation captured when the
                grid was bound; stale interpretations fail before mutation.
            rows: Rows of stable task ID, arm/load/repetition text in the bound display
                units.
            cell: Optional task ID and input-column selection:
                (1 arm, 2 load, 3 repetitions).
                None parses all rows for explicit bulk acceptance. A cell accepts only
                that value, retaining every other canonical input even when its widget
                contains unfinished text. Unknown coordinates are rejected.

        Returns:
            True only when one parsed replacement changed the committed source; False
            for no active source/no change where supported.

        Raises:
            DraftError: Input parsing, task identity or the exact bound source/display
                context fails validation; pending text is preserved.
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        replacement = self.parse_grid(context, rows, cell=cell)
        active = self.workspace.active
        source = self.source()
        assert active is not None and source is not None
        changed = active.execute(
            LifftProjectEdit(ReplaceLifftInputs(active.document, source, replacement))
        )
        if changed:
            self.editor.clear()
        return changed

    def parse_grid(
        self,
        context: EditContext,
        rows: tuple[tuple[str, str, str, str], ...],
        *,
        cell: tuple[str, int] | None = None,
    ) -> LifftDraft:
        """Validate the bound grid and return its canonical source without mutation.

        Uses the same identity, decimal and unit rules as commit_grid. Missing
        values remain None; input parsing does not calculate or publish results.

        Args:
            context: Current source/display binding; stale bindings are rejected.
            rows: Stable task identities and displayed input values in grid order.
            cell: Optional task ID and input-column selection:
                (1 arm, 2 load, 3 repetitions).
                None parses all rows for explicit bulk acceptance. A cell accepts only
                that value, retaining every other canonical input even when its widget
                contains unfinished text. Unknown coordinates are rejected.

        Returns:
            Fully parsed immutable draft, retaining exact unchanged source values.

        Raises:
            DraftError: Invalid input, task identity or stale display/source binding.
            ValueError: Active source belongs to a different ergonomic tool.
        """
        active = self.workspace.active
        source = self.source()
        if (
            active is None
            or source is None
            or self.editor.current(active) is not context
        ):
            raise DraftError(InputIssue("validation.stale_editor", "source"))
        if tuple(row[0] for row in rows) != tuple(t.task_id for t in source.tasks):
            raise DraftError(InputIssue("validation.identity", "source"))
        if cell is not None and (
            type(cell[1]) is not int
            or cell
            not in {
                (task.task_id, column)
                for task in source.tasks
                for column in range(1, 4)
            }
        ):
            raise DraftError(InputIssue("validation.identity", "source"))
        tasks = []
        for task, projected, row in zip(
            source.tasks, context.view.tasks, rows, strict=True
        ):
            values = {}
            for column, (field, text) in enumerate(
                zip(("lever_arm", "load", "repetitions"), row[1:], strict=True), start=1
            ):
                if cell is not None and cell != (task.task_id, column):
                    values[field] = getattr(task, field)
                    continue
                value = parse_input_number(
                    text, context.convention, field, task.task_id
                )
                if value == getattr(projected, field):
                    value = getattr(task, field)
                elif field != "repetitions":
                    value = project_model_input(
                        value, field, task.task_id, context.view.system, source.system
                    )
                values[field] = value
            tasks.append(LifftTask(task.task_id, **values))
        return replace(source, tasks=tuple(tasks))

    def reset_grid(self) -> bool:
        """Clear all task inputs as one undo step; retain grid size and identities.

        Args:
            None.

        Returns:
            True when resetting inputs recorded a source change; False for
            absent/unchanged source.

        Raises:
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        active = self.workspace.active
        source = self.source()
        if active is None or source is None:
            return False
        changed = active.execute(
            LifftProjectEdit(
                ReplaceLifftInputs(
                    active.document,
                    source,
                    replace(
                        source, tasks=tuple(LifftTask(t.task_id) for t in source.tasks)
                    ),
                )
            )
        )
        if changed:
            self.editor.clear()
        return changed
