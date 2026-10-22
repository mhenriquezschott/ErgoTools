"""Focus-aware JROT title-row actions over the existing application history engine.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from typing import TYPE_CHECKING

from PyQt5.QtCore import QEvent, QObject, QSize, Qt
from PyQt5.QtGui import QKeyEvent, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QLineEdit,
    QToolButton,
)

from ergotools.presentation.desktop.style import HISTORY_BUTTON_STYLE

if TYPE_CHECKING:
    from ergotools.presentation.desktop.rotation_dialog import RotationDialog


class RotationHistoryActions(QObject):
    """Keep typing undo local and disable source replay during an owned solve."""

    def __init__(self, view: "RotationDialog") -> None:
        """Install window-scoped standard shortcuts and styled title-row buttons.

        Args:
            view: Owning integrated window whose controls and existing command policy
                are reused.

        Returns:
            None.
        """
        super().__init__(view)
        self.view = view
        self.undo_action = QAction(view.icons["undo"], "", view)
        self.redo_action = QAction(view.icons["redo"], "", view)
        for action, key in (
            (self.undo_action, QKeySequence.StandardKey.Undo),
            (self.redo_action, QKeySequence.StandardKey.Redo),
        ):
            action.setShortcuts(QKeySequence.keyBindings(key))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            view.addAction(action)
        self.undo_button = QToolButton(view)
        self.redo_button = QToolButton(view)
        for button, action in (
            (self.undo_button, self.undo_action),
            (self.redo_button, self.redo_action),
        ):
            button.setObjectName("historyButton")
            button.setStyleSheet(HISTORY_BUTTON_STYLE)
            button.setDefaultAction(action)
            button.setIconSize(QSize(24, 24))
            button.setFixedSize(36, 36)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.undo_action.triggered.connect(lambda: self.replay(redo=False))
        self.redo_action.triggered.connect(lambda: self.replay(redo=True))
        for field in view.findChildren(QLineEdit):
            field.installEventFilter(self)
            field.textChanged.connect(self.refresh)
            field.selectionChanged.connect(self.refresh)
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        app.focusChanged.connect(self.refresh)
        view.title_row.addWidget(self.undo_button)
        view.title_row.addWidget(self.redo_button)
        self.refresh()

    def focused_field(self) -> QLineEdit | None:
        """Resolve native text ownership within this modal form only.

        Args:
            None.

        Returns:
            Focused line editor owned by this window, or None when focus belongs
            elsewhere; caller borrows it.
        """
        field = QApplication.focusWidget()
        # Editable QComboBox reports itself as focus owner, not its line edit.
        if isinstance(field, QComboBox) and field.isEditable():
            field = field.lineEdit()
        return (
            field
            if isinstance(field, QLineEdit) and self.view.isAncestorOf(field)
            else None
        )

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802
        """Claim native typing Undo/Redo even when its local stack is empty.

        Args:
            watched: QObject receiving the event; may be None in direct defensive calls.
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            True only when this filter explicitly consumes the event; otherwise the
            normal Qt base-filter result.
        """
        if (
            isinstance(watched, QLineEdit)
            and isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.ShortcutOverride
            and (
                event.matches(QKeySequence.StandardKey.Undo)
                or event.matches(QKeySequence.StandardKey.Redo)
            )
        ):
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def refresh(self) -> None:
        """Refresh enablement without changing the grid, preview or repository.

        Args:
            None.

        Returns:
            None.
        """
        field = self.focused_field()
        history = self.view.history
        if history is None:
            return
        busy = self.view.optimization is not None and self.view.optimization.busy
        for action, label, available in (
            (
                self.undo_action,
                self.view.text("Undo", "Deshacer"),
                history.undo_label_key is not None,
            ),
            (
                self.redo_action,
                self.view.text("Redo", "Rehacer"),
                history.redo_label_key is not None,
            ),
        ):
            if field is not None:
                available = not field.isReadOnly() and (
                    field.isUndoAvailable()
                    if action is self.undo_action
                    else field.isRedoAvailable()
                )
            action.setText(label)
            action.setToolTip(label)
            action.setEnabled(available and not busy)

    def replay(self, *, redo: bool) -> None:
        """Route native typing or one document replay; never save implicitly.

        Args:
            redo: True replays the next operation; False restores the previous
                operation.

        Returns:
            None.
        """
        if self.view.optimization is not None and self.view.optimization.busy:
            return
        field = self.focused_field()
        if field is not None:
            field.redo() if redo else field.undo()
        else:
            self.view.replay_history(redo=redo)
        self.refresh()
