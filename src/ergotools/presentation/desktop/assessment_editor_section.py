"""Reusable assessment section and action row for Main and Job editor hosts.

Presentation layer. Compose the shared grid (or tabbed grids), supplied result view
and actions. Hosts connect commands, supply task-count controls, and
own validation, calculation, history and saving. No source state or repository lives
in these layout components.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid
from ergotools.presentation.desktop.tool_result_summary import ToolResultSummary


class AssessmentActionRow(QHBoxLayout):
    """Shared equal-width Clear/Calculate actions around optional middle controls."""

    def __init__(
        self,
        icons: Mapping[str, QIcon],
        *,
        tasks: bool = False,
        middle: tuple[QWidget, ...] = (),
    ) -> None:
        """Build native actions without binding any application command.

        Args:
            icons: Packaged action assets supplied by the host.
            tasks: Add compact row-count buttons between Clear and Calculate.
            middle: Job task-count controls or other explicitly supplied middle widgets.

        Returns:
            None; hosts supply localized captions, tooltips and callbacks.
        """
        super().__init__()
        self.clear_button = QPushButton()
        self.clear_button.setObjectName("clearAssessmentButton")
        self.clear_button.setIcon(icons["delete"])
        self.clear_button.setIconSize(QSize(26, 26))
        self.calculate_button = QPushButton()
        self.calculate_button.setObjectName("calculateButton")
        self.calculate_button.setIcon(icons["calculate_light"])
        self.calculate_button.setIconSize(QSize(28, 28))
        self.add_task_button: QPushButton | None = None
        self.remove_task_button: QPushButton | None = None
        self.addWidget(self.clear_button, 1)
        if tasks:
            self.add_task_button = QPushButton("+ Task")
            self.remove_task_button = QPushButton("- Task")
            for button in (self.add_task_button, self.remove_task_button):
                button.setFixedHeight(40)
                self.addWidget(button)
        for widget in middle:
            self.addWidget(widget)
        self.addWidget(self.calculate_button, 1)
        for button in (self.clear_button, self.calculate_button):
            button.setMinimumHeight(40)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def settle(self) -> None:
        """Retain established action heights after Qt stylesheet polishing.

        Args:
            None.

        Returns:
            None; geometry only, without command execution or source changes.
        """
        for button in (
            self.clear_button,
            self.add_task_button,
            self.remove_task_button,
            self.calculate_button,
        ):
            if button is not None:
                button.setFixedHeight(40)


class AssessmentEditorSection(QWidget):
    """Compose common task content, result summary and action-row organization."""

    def __init__(
        self,
        content: QWidget,
        summary: QWidget | QLayout,
        actions: AssessmentActionRow,
        *,
        status: QWidget | None = None,
        spacing: int = 6,
        parent: QWidget | None = None,
    ) -> None:
        """Adopt supplied views while preserving host-specific source ownership.

        Args:
            content: Shared task grid or host-owned tabs containing those grids.
            summary: Existing shared totals layout or a direct-result summary wrapper.
            actions: Shared Clear/Calculate row with configured middle controls.
            status: Optional Job calculation/input-state message below the task area.
            spacing: Established host layout spacing in pixels.
            parent: Optional native owner; layout insertion can supply ownership later.

        Returns:
            None; layout adoption creates no task, calculation or history action.
        """
        super().__init__(parent)
        self.content = content
        self.summary = summary
        self.action_row = actions
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)
        layout.addWidget(content, 1)
        if status is not None:
            layout.addWidget(status)
        if isinstance(summary, QLayout):
            layout.addLayout(summary)
        else:
            layout.addWidget(summary)
        layout.addLayout(actions)
        if isinstance(content, AssessmentTaskGrid):
            content.geometry_changed.connect(self.align_summary)

    def align_summary(self) -> None:
        """Follow settled shared-grid columns without touching scientific values.

        Args:
            None.

        Returns:
            None; Job's tabbed summary remains bound by its existing host callback.
        """
        self.action_row.settle()
        if isinstance(self.content, AssessmentTaskGrid) and isinstance(
            self.summary, ToolResultSummary
        ):
            outputs = self.content.outputs
            self.summary.align_to(outputs[0][-2] if outputs else None, self)
