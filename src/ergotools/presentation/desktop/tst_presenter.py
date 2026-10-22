"""Widget-independent Shoulder Tool input and reference-calculation workflow.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from dataclasses import replace
from uuid import uuid4

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluation,
    AssessmentEvaluator,
)
from ergotools.application.assessments.project_edits import TstProjectEdit
from ergotools.application.assessments.tst_commands import (
    ReplaceTstInputs,
    SetTstTaskCount,
)
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.model_units import MeasurementSystem, project_model_input
from ergotools.presentation.edit_context import AssessmentEditor, EditContext
from ergotools.presentation.numeric_input import DecimalConvention, parse_input_number


class TstPresenter:
    """Own ST input interpretation/history; delegate calculation to the application."""

    def __init__(self, workspace: ProjectWorkspace[AssessmentDraft]) -> None:
        """Receive existing workspace ownership; default to imperial point display.

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

    def source(self) -> TstDraft | None:
        """Return only an active ST draft; reject another tool explicitly.

        Args:
            None.

        Returns:
            Committed ST draft with stored units/direction convention, or None without
            an active source; another tool is rejected.

        Raises:
            ValueError: ST controls require a Shoulder Tool assessment.
        """
        active = self.workspace.active
        if active is None:
            return None
        if not isinstance(active.state, TstDraft):
            raise ValueError("ST controls require a Shoulder Tool assessment.")
        return active.state

    def bind(self) -> EditContext | None:
        """Project source arm/load into display units without source/history changes.

        Args:
            None.

        Returns:
            Fresh source/preference-bound ST context with projected dimensional fields,
            or None with no active source.

        Raises:
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        self.editor.clear()
        self.source()
        active = self.workspace.active
        return (
            self.editor.bind(active, self.system, self.convention) if active else None
        )

    def commit_grid(
        self,
        context: EditContext,
        rows: tuple[tuple[str, TstDirection | None, str, str, str], ...],
        *,
        cell: tuple[str, int] | None = None,
    ) -> bool:
        """Accept one cell or an explicit grid, preserving exact untouched values.

        Direction retains the source convention and visible choice. Convert only changed
        dimensional inputs back to source cm/N or inches/lbf. Invalid text raises
        DraftError without losing pending text or modifying the document.

        Args:
            context: Exact current source/display interpretation captured when the
                grid was bound; stale interpretations fail before mutation.
            rows: Rows of stable task ID, original typed direction, arm/load/repetitions
                display text; dimensional values follow the bound context.
            cell: Optional task ID and input-column selection:
                (1 direction, 2 arm, 3 load, 4 repetitions).
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
        source = self.source()
        assert source is not None
        return self._replace(source, replacement)

    def parse_grid(
        self,
        context: EditContext,
        rows: tuple[tuple[str, TstDirection | None, str, str, str], ...],
        *,
        cell: tuple[str, int] | None = None,
    ) -> TstDraft:
        """Validate the bound grid and return its canonical source without mutation.

        Uses the same identity, decimal and unit rules as commit_grid. Missing
        values remain None; input parsing does not calculate or publish results.

        Args:
            context: Current source/display binding; stale bindings are rejected.
            rows: Stable task identities and displayed input values in grid order.
            cell: Optional task ID and input-column selection:
                (1 direction, 2 arm, 3 load, 4 repetitions).
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
        if tuple(row[0] for row in rows) != tuple(
            task.task_id for task in source.tasks
        ):
            raise DraftError(InputIssue("validation.identity", "source"))
        if cell is not None and (
            type(cell[1]) is not int
            or cell
            not in {
                (task.task_id, column)
                for task in source.tasks
                for column in range(1, 5)
            }
        ):
            raise DraftError(InputIssue("validation.identity", "source"))
        tasks = []
        for row, original, projected in zip(
            rows, source.tasks, context.view.tasks, strict=True
        ):
            direction = (
                row[1] if cell is None or cell == (row[0], 1) else original.direction
            )
            if direction is not None and not isinstance(direction, TstDirection):
                raise DraftError(
                    InputIssue("validation.direction", "direction", row[0])
                )
            values = {}
            for column, (field, text) in enumerate(
                zip(("lever_arm", "load", "repetitions"), row[2:], strict=True), start=2
            ):
                if cell is not None and cell != (row[0], column):
                    values[field] = getattr(original, field)
                    continue
                value = parse_input_number(text, context.convention, field, row[0])
                if value == getattr(projected, field):
                    value = getattr(original, field)
                elif field != "repetitions":
                    value = project_model_input(
                        value, field, row[0], context.view.system, source.system
                    )
                values[field] = value
            tasks.append(TstTask(row[0], direction, **values))
        return replace(source, tasks=tuple(tasks))

    def _replace(self, source: TstDraft, replacement: TstDraft) -> bool:
        """Record one complete input replacement in the active source history.

        Record one complete input replacement in the active source history and
        invalidate cached interpretation/results only after the command boundary.

        Args:
            source: Previously committed typed source used as the expected edit state.
            replacement: Fully parsed replacement source; applied as one reversible
                command.

        Returns:
            True when the active history accepted a changed replacement; False with no
            active source or no change.
        """
        active = self.workspace.active
        if active is None:
            return False
        changed = active.execute(
            TstProjectEdit(ReplaceTstInputs(active.document, source, replacement))
        )
        if changed:
            self.editor.clear()
        self.evaluator.clear()
        return changed

    def set_task_count(self, count: int) -> None:
        """Resize only this assessment; preserve retained rows, units and identities.

        Reject noninteger/out-of-range counts before creating identities or editing. The
        caller accepts valid pending text before resizing. Same-count requests do
        nothing; history restores truncated rows and the prior calculation snapshot.

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
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or not 1 <= count <= 100
        ):
            raise DraftError(InputIssue("validation.position", "tasks"))
        source = self.source()
        active = self.workspace.active
        if source is None or active is None:
            return
        if count == len(source.tasks):
            return
        tasks = source.tasks[:count] + tuple(
            TstTask(uuid4().hex, TstDirection.HANDLING_LOADS)
            for _ in range(max(0, count - len(source.tasks)))
        )
        active.execute(TstProjectEdit(SetTstTaskCount(active.document, source, tasks)))
        self.editor.clear()
        self.evaluator.clear()

    def reset_grid(self) -> bool:
        """Reset numeric inputs and select Handling Loads as one reversible edit.

        Args:
            None.

        Returns:
            True when resetting inputs recorded a source change; False for
            absent/unchanged source.

        Raises:
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        source = self.source()
        if source is None:
            return False
        return self._replace(
            source,
            replace(
                source,
                tasks=tuple(
                    TstTask(task.task_id, TstDirection.HANDLING_LOADS)
                    for task in source.tasks
                ),
            ),
        )

    def calculate(self) -> AssessmentEvaluation | None:
        """Calculate grid behavior using recorded units and direction convention.

        Args:
            None.

        Returns:
            Current grid evaluation, including incomplete status, or None when no
            assessment is active.

        Raises:
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        self.source()
        active = self.workspace.active
        return self.evaluator.evaluate_tst_grid(active) if active else None
