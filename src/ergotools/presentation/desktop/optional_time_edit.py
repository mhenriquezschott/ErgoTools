"""Optional 24-hour clock input using Qt's standard segmented time editor.

Presentation adapter. QTimeEdit owns keyboard parsing, section navigation, formatting
and stepping. This subclass only distinguishes an unspecified value from valid
midnight, retains malformed loaded text for correction, and exposes a value-change
notification to the owning form. No sentinel clock, date or UI flag is persisted.
"""

from datetime import datetime
from datetime import time as python_time
from typing import cast

from PyQt5.QtCore import QDateTime, Qt, QTime, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QKeySequence
from PyQt5.QtWidgets import QApplication, QTimeEdit, QWidget


class OptionalTimeEdit(QTimeEdit):
    """Standard hour/minute editor with an explicit optional-value boundary.

    Attributes:
        value_changed: Emitted when the optional canonical clock/raw invalid value
            changes; projection deduplicates notifications and never writes data.
    """

    value_changed = pyqtSignal()

    def __init__(self, not_set_text: str, parent: QWidget | None = None) -> None:
        """Create a nullable HH:mm editor without reserving a valid time as empty.

        Args:
            not_set_text: Localized display caption for an unspecified time.
            parent: Qt owner; None leaves top-level ownership to the caller.

        Returns:
            None; all actual clocks 00:00 through 23:59 remain usable.
        """
        self._empty = True
        self._invalid: str | None = None
        self._not_set_text = not_set_text
        self._projecting = True
        self._last_value = ""
        super().__init__(parent)
        self.setDisplayFormat("HH:mm")
        self.setKeyboardTracking(True)
        super().setTime(QTime(0, 0))
        self.timeChanged.connect(self._notify_value_changed)
        editor = self.lineEdit()
        assert editor is not None
        editor.textEdited.connect(self._text_edited)
        self._render_value()
        self._projecting = False

    def clock_text(self) -> str:
        """Read optional clock text without interpreting a hidden midnight as data.

        Args:
            None.

        Returns:
            Empty string for unspecified, original invalid text for correction, or
            canonical HH:mm for a valid Qt clock. This method performs no mutation.
        """
        if self._empty:
            return ""
        return (
            self._invalid
            if self._invalid is not None
            else self.time().toString("HH:mm")
        )

    def is_acceptable(self) -> bool:
        """Check the optional clock contract independently of its empty display label.

        Args:
            None.

        Returns:
            True for unspecified or valid clocks; False for malformed loaded text.
        """
        return self._invalid is None

    def set_value(self, value: str | None) -> None:
        """Project a stored clock, preserving invalid text rather than normalizing it.

        Args:
            value: None/empty for unspecified, a Qt-parseable HH:mm clock (short
                hours are zero-padded), or malformed historical text retained for
                explicit correction.

        Returns:
            None; valid midnight remains distinct from the unspecified state.
        """
        self._projecting = True
        try:
            self._empty = not value
            clock = QTime.fromString(value or "", "H:mm")
            valid = clock.isValid()
            self._invalid = value if value and not valid else None
            super().setTime(clock if valid else QTime(0, 0))
            self._render_value()
        finally:
            self._projecting = False
        self._notify_value_changed()

    def setTime(self, time: QTime | python_time) -> None:  # noqa: N802 — Qt public API
        """Retain Qt's explicit time setter while making midnight a provided value.

        Args:
            time: Qt or Python clock; invalid Qt values retain its no-change policy.

        Returns:
            None; application callers needing absence use set_value(None) or clear.
        """
        if isinstance(time, python_time):
            native = cast(python_time, time)
            clock = QTime(
                native.hour, native.minute, native.second, native.microsecond // 1000
            )
        else:
            clock = time
        if clock.isValid():
            self.set_value(clock.toString("HH:mm"))

    def clear(self) -> None:
        """Remove the optional value without changing any stored project directly.

        Args:
            None.

        Returns:
            None; the display returns to its localized unspecified caption.
        """
        self.set_value(None)

    def textFromDateTime(self, date_time: QDateTime | datetime) -> str:  # noqa: N802 — Qt override
        """Keep Qt reformatting from turning absence or invalid loaded text into data.

        Args:
            date_time: Internal Qt value used only when the optional clock is valid.

        Returns:
            Localized unspecified caption, retained invalid text, or Qt HH:mm output.
        """
        if self._empty:
            return self._not_set_text
        if self._invalid is not None:
            return self._invalid
        return super().textFromDateTime(date_time)

    def _render_value(self) -> None:
        """Refresh only the standard internal line editor, not the owning form.

        Args:
            None.

        Returns:
            None; projection does not create a native text edit or project command.
        """
        editor = self.lineEdit()
        assert editor is not None
        editor.setText(self.textFromDateTime(self.dateTime()))

    def _activate_clock(self) -> None:
        """Begin real clock entry when a user types or steps an unspecified value.

        Args:
            None.

        Returns:
            None; Qt receives its normal zero-padded sections with hours selected.
            Merely focusing or navigating the empty widget never provides a time.
        """
        if self._empty or self._invalid is not None:
            self._empty = False
            self._invalid = None
            super().setTime(QTime(0, 0))
            self._render_value()
            self.setSelectedSection(QTimeEdit.HourSection)

    def _text_edited(self, text: str) -> None:
        """Recognize native clearing/typing Undo without treating display text as time.

        Args:
            text: Qt's actual user-edited internal text, including native text replay.

        Returns:
            None; Qt continues to own clock parsing and section correction.
        """
        if self._projecting:
            return
        if not text or text == self._not_set_text:
            self.clear()
        self._notify_value_changed()

    def _notify_value_changed(self) -> None:
        """Notify the owner once for each optional-value change without saving it.

        Args:
            None.

        Returns:
            None; repeated native signals for the same clock are deduplicated.
        """
        if not self._projecting:
            value = self.clock_text()
            if value != self._last_value:
                self._last_value = value
                self.value_changed.emit()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802 — Qt override
        """Delegate clock typing to Qt and support clearing an optional whole value.

        Args:
            event: Native key event; None is tolerated for defensive direct calls.

        Returns:
            None; Ctrl+A then Delete/Backspace clears, digits activate hours, and
            keyboard paste uses Qt's clock parser and leaves minutes selected.
            Invalid paste cannot activate an unspecified value.
        """
        if event is None:
            return
        editor = self.lineEdit()
        assert editor is not None
        if not self.isReadOnly():
            if (
                event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)
                and editor.selectedText() == editor.text()
            ):
                self.clear()
                event.accept()
                return
            paste = event.matches(QKeySequence.StandardKey.Paste)
            if paste:
                clipboard = QApplication.clipboard()
                assert clipboard is not None
                clock = QTime.fromString(clipboard.text().strip(), "H:mm")
                if clock.isValid():
                    self.setTime(clock)
                    self.setSelectedSection(QTimeEdit.MinuteSection)
                event.accept()
                return
            if event.text().isdigit():
                self._activate_clock()
        super().keyPressEvent(event)
        self._notify_value_changed()

    def stepBy(self, steps: int) -> None:  # noqa: N802 — Qt override
        """Use native hour/minute stepping after activating a previously absent clock.

        Args:
            steps: Signed step count supplied by Qt's arrows, keyboard or wheel.

        Returns:
            None; readonly widgets remain unchanged and Qt enforces clock bounds.
        """
        if self.isReadOnly():
            return
        self._activate_clock()
        super().stepBy(steps)
        self._notify_value_changed()
