"""Optional daily duration using native hour/minute spin controls.

Presentation adapter. A duration is not a clock: 24 hours is valid, and there is no
midnight wrap. Stored values remain decimal hours. An internal negative hour means
absence and is never serialized. Whole-minute conversion must be lossless; unknown
or subminute historical values fail instead of being rounded silently.
"""

import math

from PyQt5.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QHBoxLayout, QSpinBox, QWidget


class OptionalDurationEdit(QWidget):
    """Nullable daily duration with keyboard-accessible native quantity controls.

    Attributes:
        value_changed: Emitted when the optional duration changes outside projection.
        hours: Hour quantity, with a localized unspecified value below valid zero.
        minutes: Minute quantity; disabled for absence or a full 24-hour day.
    """

    value_changed = pyqtSignal()

    def __init__(self, not_set_text: str, parent: QWidget | None = None) -> None:
        """Compose native bounded hour/minute controls without clock/date semantics.

        Args:
            not_set_text: Localized caption for an unspecified duration.
            parent: Optional Qt owner.

        Returns:
            None. Minutes become available when a real hour quantity is provided.
        """
        super().__init__(parent)
        self._projecting = True
        self._last_value = ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.hours, self.minutes = QSpinBox(self), QSpinBox(self)
        self.hours.setRange(-1, 24)
        self.hours.setSpecialValueText(not_set_text)
        self.hours.setSuffix(" h")
        self.minutes.setRange(0, 59)
        self.minutes.setSuffix(" min")
        for editor in (self.hours, self.minutes):
            editor.setMinimumHeight(36)
            layout.addWidget(editor)
            editor.valueChanged.connect(self._changed)
        self.hours.setValue(-1)
        editor = self.hours.findChild(QWidget, "qt_spinbox_lineedit")
        assert editor is not None
        editor.installEventFilter(self)
        self.hours.installEventFilter(self)
        self._projecting = False
        self._changed()

    def duration_text(self) -> str:
        """Read the optional duration in canonical decimal hours for the form boundary.

        Args:
            None.

        Returns:
            Empty text for absence or decimal hours; 24 never wraps to zero.
        """
        return (
            ""
            if self.hours.value() < 0
            else str(self.hours.value() + self.minutes.value() / 60)
        )

    def set_value(self, value: float | None) -> None:
        """Project decimal hours only when the minute controls can retain them exactly.

        Args:
            value: None or a finite daily duration from 0 through 24 decimal hours.

        Returns:
            None. Projection emits at most one actual optional-value change.

        Raises:
            ValueError: Duration is outside one day or has subminute precision.
        """
        if value is not None and (not math.isfinite(value) or not 0 <= value <= 24):
            raise ValueError("Daily operational hours must be finite and within 0-24.")
        total = 0 if value is None else round(value * 60)
        if value is not None and (
            not math.isfinite(value) or not 0 <= value <= 24 or value != total / 60
        ):
            raise ValueError(
                "Daily operational hours require whole minutes from 0 to 24 hours."
            )
        self._projecting = True
        try:
            self.hours.setValue(-1 if value is None else total // 60)
            self.minutes.setValue(total % 60)
        finally:
            self._projecting = False
        self._changed()

    def clear(self) -> None:
        """Remove the optional duration while preserving zero as a valid quantity.

        Args:
            None.

        Returns:
            None. No project data is written by this control.
        """
        self.set_value(None)

    def _changed(self) -> None:
        """Constrain minute entry and notify once after a native quantity change.

        Args:
            None.

        Returns:
            None. Absence/full-day hours require zero minutes; projection is guarded.
        """
        if self._projecting:
            return
        self.minutes.setEnabled(0 <= self.hours.value() < 24)
        if not self.minutes.isEnabled() and self.minutes.value():
            self.minutes.setValue(0)
        value = self.duration_text()
        if value != self._last_value:
            self._last_value = value
            self.value_changed.emit()

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 — Qt override
        """Allow whole-value keyboard clearing on the native hour editor.

        Args:
            watched: Internal hour line editor installed by the constructor.
            event: Native event, including its existing keyboard selection.

        Returns:
            True only when Ctrl+A/Delete clears the optional duration; other native
            editing, navigation and stepping remain owned by Qt.
        """
        if (
            isinstance(event, QKeyEvent)
            and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace)
        ):
            editor = self.hours.lineEdit()
            if (
                editor is not None
                and bool(editor.selectedText())
                and editor.selectedText() in (editor.text(), self.hours.cleanText())
            ):
                self.clear()
                return True
        return super().eventFilter(watched, event)
