"""Focus-aware Qt actions over PLOT's application-owned source history.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QIcon, QKeyEvent, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QLineEdit,
    QToolButton,
    QWidget,
)

from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.secondary_history_controls import (
    configure_history_button,
)
from ergotools.presentation.localization import Translator


class PlotHistoryActions(QObject):
    """Adapt source history to title-row buttons and standard platform shortcuts.

    Line edits retain native typing history, even when it is empty. Unaccepted
    coordinate strings cannot be erased by an unrelated document Undo. Actions belong
    only to this modal window; no global application shortcut is installed.
    """

    def __init__(
        self,
        window: QWidget,
        layer: PlotMarkerLayer,
        icons: Mapping[str, QIcon],
        has_unaccepted_fields: Callable[[], bool],
        *,
        language: Language,
    ) -> None:
        """Connect the existing engine without adding a second Qt undo stack.

        Args:
            window: Qt window owning title-row actions and shortcuts.
            layer: Existing PLOT marker/history owner; this view borrows its selection
                and save operations.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            has_unaccepted_fields: Callback reporting typed coordinate text that
                document Undo must preserve.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        super().__init__(window)
        self.window = window
        self.layer = layer
        self.has_unaccepted_fields = has_unaccepted_fields
        self.translator = Translator(language)
        self.undo_action = QAction(icons["undo"], "", window)
        self.redo_action = QAction(icons["redo"], "", window)
        for action, standard in (
            (self.undo_action, QKeySequence.StandardKey.Undo),
            (self.redo_action, QKeySequence.StandardKey.Redo),
        ):
            action.setShortcuts(QKeySequence.keyBindings(standard))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            window.addAction(action)
        self.undo_button = QToolButton(window)
        self.redo_button = QToolButton(window)
        for button, action in (
            (self.undo_button, self.undo_action),
            (self.redo_button, self.redo_action),
        ):
            button.setDefaultAction(action)
            configure_history_button(button)
        self.undo_action.triggered.connect(lambda: self.replay(redo=False))
        self.redo_action.triggered.connect(lambda: self.replay(redo=True))
        layer.changed.connect(self.refresh)
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        app.focusChanged.connect(self.focus_changed)
        for field in window.findChildren(QLineEdit):
            field.installEventFilter(self)
            field.textChanged.connect(self.refresh)
            field.selectionChanged.connect(self.refresh)
        self.refresh()

    def focused_field(self) -> QLineEdit | None:
        """Resolve only this window's editable text controls.

        Args:
            None.

        Returns:
            Focused line editor owned by this window, or None when focus belongs
            elsewhere; caller borrows it.
        """
        field = QApplication.focusWidget()
        return (
            field
            if isinstance(field, QLineEdit) and self.window.isAncestorOf(field)
            else None
        )

    def focus_changed(self, _old: QWidget | None, _new: QWidget | None) -> None:
        """Refresh action ownership as focus moves between fields and map controls.

        Args:
            _old: Previously focused widget supplied by Qt; its contents are not
                inspected.
            _new: Newly focused widget supplied by Qt; refresh resolves actual focus
                ownership.

        Returns:
            None.
        """
        self.refresh()

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802
        """Keep typing shortcuts local even when that field's history is empty.

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
        """Project labels/enabled state; never evaluate, save or modify geometry.

        Args:
            None.

        Returns:
            None.
        """
        field = self.focused_field()
        history = self.layer.shared_history or self.layer.history
        blocked = self.has_unaccepted_fields()
        for action, verb, key in (
            (
                self.undo_action,
                "undo",
                history.session.undo_label_key if history else None,
            ),
            (
                self.redo_action,
                "redo",
                history.session.redo_label_key if history else None,
            ),
        ):
            label = self.translator.text(f"plot.history.{verb}")
            if field is not None:
                enabled = not field.isReadOnly() and (
                    field.isUndoAvailable()
                    if verb == "undo"
                    else field.isRedoAvailable()
                )
                if enabled:
                    label += " " + self.translator.text("plot.history.typing")
            else:
                enabled = key is not None and not blocked
                if key is not None:
                    label += " " + self.translator.text(key)
            action.setText(label)
            action.setIconText(self.translator.text(f"plot.history.{verb}"))
            action.setEnabled(enabled)
            action.setToolTip(
                self.translator.text("plot.history.pending_fields")
                if blocked and field is None
                else label
            )

    def replay(self, *, redo: bool) -> None:
        """Route to native text or active PLOT history; no persistence side effects.

        Args:
            redo: True replays the next operation; False restores the previous
                operation.

        Returns:
            None.
        """
        field = self.focused_field()
        if field is not None:
            if redo:
                field.redo()
            else:
                field.undo()
        elif not self.has_unaccepted_fields():
            if redo:
                self.layer.redo()
            else:
                self.layer.undo()
        self.refresh()
