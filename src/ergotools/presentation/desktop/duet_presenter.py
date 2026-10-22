"""Widget-independent DUET grid edits and calculation over existing project ports.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from dataclasses import dataclass
from uuid import uuid4

from ergotools.application.assessments.duet_commands import (
    ReplaceDuetInputs,
    SetDuetTaskCount,
)
from ergotools.application.assessments.evaluation import (
    AssessmentEvaluation,
    AssessmentEvaluator,
    AssessmentPreparation,
    prepare_assessment,
)
from ergotools.application.assessments.project_edits import DuetProjectEdit
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.numeric_input import DecimalConvention, parse_input_number


@dataclass(frozen=True, slots=True)
class DuetEditContext:
    """Exact dimensionless source and decimal convention shown by the grid.

    Attributes:
        preparation: Exact bound source identity/revision used to reject stale grid
            commits.
        convention: Point/comma numeric-input convention captured when the grid was
            shown.
    """

    preparation: AssessmentPreparation
    convention: DecimalConvention


class DuetPresenter:
    """Coordinate dimensionless DUET inputs without widgets or file ownership."""

    def __init__(self, workspace: ProjectWorkspace[AssessmentDraft]) -> None:
        """Receive the existing workspace; keep parsing separate from UI language.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.

        Returns:
            None.
        """
        self.workspace = workspace
        self.context: DuetEditContext | None = None
        self.evaluator = AssessmentEvaluator()
        self.convention = DecimalConvention.POINT
        self.system = MeasurementSystem.IMPERIAL

    def source(self) -> DuetDraft | None:
        """Return active DUET source, rejecting a different model explicitly.

        Args:
            None.

        Returns:
            Committed dimensionless DUET draft, or None without an active source;
            another tool is rejected.

        Raises:
            ValueError: DUET controls require a DUET assessment.
        """
        active = self.workspace.active
        if active is None:
            return None
        if not isinstance(active.state, DuetDraft):
            raise ValueError("DUET controls require a DUET assessment.")
        return active.state

    def bind(self) -> DuetEditContext | None:
        """Bind dimensionless source without invoking dimensional unit conversion.

        Args:
            None.

        Returns:
            New dimensionless grid edit context with the current decimal convention, or
            None without an active source.

        Raises:
            ValueError: The active source belongs to a different ergonomic tool; no
                implicit reinterpretation occurs.
        """
        self.context = None
        self.source()
        active = self.workspace.active
        if active is not None:
            self.context = DuetEditContext(prepare_assessment(active), self.convention)
        return self.context

    def commit_grid(
        self,
        context: DuetEditContext,
        rows: tuple[tuple[str, int | None, str], ...],
        *,
        cell: tuple[str, int] | None = None,
    ) -> bool:
        """Accept one completed cell or an explicit grid without losing pending text.

        Args:
            context: Exact current source/display interpretation captured when the
                grid was bound; stale interpretations fail before mutation.
            rows: Rows of stable task ID, OMNI-Res scale and repetition text; DUET
                inputs are dimensionless.
            cell: Optional task ID and input-column selection:
                (1 rating, 2 repetitions).
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
        context: DuetEditContext,
        rows: tuple[tuple[str, int | None, str], ...],
        *,
        cell: tuple[str, int] | None = None,
    ) -> DuetDraft:
        """Validate the bound grid and return its canonical source without mutation.

        Uses the same identity, decimal and unit rules as commit_grid. Missing
        values remain None; input parsing does not calculate or publish results.

        Args:
            context: Current source/display binding; stale bindings are rejected.
            rows: Stable task identities and displayed input values in grid order.
            cell: Optional task ID and input-column selection:
                (1 rating, 2 repetitions).
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
            or (
                self.context is not context
                or not context.preparation.is_current(active)
            )
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
                for column in range(1, 3)
            }
        ):
            raise DraftError(InputIssue("validation.identity", "source"))
        tasks = tuple(
            DuetTask(
                identity,
                scale
                if cell is None or cell == (identity, 1)
                else original.omni_res_scale,
                parse_input_number(text, context.convention, "repetitions", identity)
                if cell is None or cell == (identity, 2)
                else original.repetitions,
            )
            for (identity, scale, text), original in zip(
                rows, source.tasks, strict=True
            )
        )
        return DuetDraft(tasks)

    def _replace(self, source: DuetDraft, replacement: DuetDraft) -> bool:
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
            DuetProjectEdit(ReplaceDuetInputs(active.document, source, replacement))
        )
        if changed:
            self.context = None
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
            DuetTask(uuid4().hex, 0) for _ in range(max(0, count - len(source.tasks)))
        )
        active.execute(
            DuetProjectEdit(SetDuetTaskCount(active.document, source, tasks))
        )
        self.context = None
        self.evaluator.clear()

    def reset_grid(self) -> bool:
        """Restore scale zero and blank repetitions in one reversible Reset.

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
            source, DuetDraft(tuple(DuetTask(t.task_id, 0) for t in source.tasks))
        )

    def calculate(self) -> AssessmentEvaluation | None:
        """Evaluate the committed grid, preserving incomplete preview status.

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
        return self.evaluator.evaluate_duet_grid(active) if active else None
