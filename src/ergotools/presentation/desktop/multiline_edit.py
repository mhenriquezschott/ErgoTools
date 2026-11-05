"""Compact plain-text form editor with field-completion semantics.

Presentation layer. Native text Undo/Redo remains local while focus departure notifies
the form to accept one completed field through its existing document/history port.
"""

from PyQt5.QtCore import QSignalBlocker, pyqtSignal
from PyQt5.QtGui import QFocusEvent
from PyQt5.QtWidgets import QPlainTextEdit


class MultilineEdit(QPlainTextEdit):
    """A two-line form field with the same completion signals as single-line inputs."""

    # User text edits advertise pending state; programmatic projection is blocked.
    textEdited = pyqtSignal(str)  # noqa: N815 - QLineEdit-compatible signal
    # Forms accept one completed edit when focus leaves, not on each keystroke.
    editingFinished = pyqtSignal()  # noqa: N815 - QLineEdit-compatible signal

    def __init__(self) -> None:
        """Own a compact native editor without an independent project writer.

        Args:
            None.

        Returns:
            None; ordinary text editing and selection remain native.
        """
        super().__init__()
        self.setFixedHeight(60)
        self.textChanged.connect(self._edited)

    def _edited(self) -> None:
        """Advertise pending user text without accepting a project change.

        Args:
            None.

        Returns:
            None; the form decides when to commit the completed value.
        """
        self.textEdited.emit(self.toPlainText())

    def text(self) -> str:
        """Read literal form text, including newline characters.

        Args:
            None.

        Returns:
            Plain text with no rich-text interpretation.
        """
        return self.toPlainText()

    def setText(self, text: str) -> None:  # noqa: N802 - form projection API
        """Project accepted text without advertising another user edit.

        Args:
            text: Literal stored description.

        Returns:
            None; native text history resets to the accepted projection.
        """
        with QSignalBlocker(self):
            self.setPlainText(text)

    def focusOutEvent(self, event: QFocusEvent | None) -> None:  # noqa: N802
        """Notify the owning form after native focus-departure processing.

        Args:
            event: Qt focus event, forwarded unchanged.

        Returns:
            None; no data is saved directly by this control.
        """
        super().focusOutEvent(event)
        self.editingFinished.emit()
