"""Nullable organization calendar backed by Qt's standard date editor.

Presentation layer. Dates serialize as ISO calendar dates; absence is independent of
all valid dates. Opening an unspecified calendar starts at today without making an
edit. Qt owns calendar navigation and segmented keyboard entry. No dates are inferred
from worker ages and no database access occurs here.
"""

from datetime import date as python_date
from datetime import datetime
from typing import cast

from PyQt5.QtCore import QDate, QDateTime, Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QDateEdit, QWidget


class OptionalDateEdit(QDateEdit):
    """Standard calendar with an explicit absent value and deduplicated notification.

    Attributes:
        value_changed: Emitted once when the optional ISO date actually changes.
    """

    value_changed = pyqtSignal()

    def __init__(self, not_set_text: str, parent: QWidget | None = None) -> None:
        """Create a calendar whose empty popup begins at the current date.

        Args:
            not_set_text: Localized caption displayed instead of an absent date.
            parent: Optional Qt widget owner.

        Returns:
            None. Merely focusing or opening the calendar does not provide a value.
        """
        self._empty = True
        self._projecting = True
        self._last_value = ""
        self._not_set_text = not_set_text
        super().__init__(parent)
        self.setDateRange(QDate(1, 1, 1), QDate(9999, 12, 31))
        self.setDisplayFormat("dd MMM yyyy")
        self.setCalendarPopup(True)
        super().setDate(QDate.currentDate())
        self.dateChanged.connect(self._date_changed)
        calendar = self.calendarWidget()
        assert calendar is not None
        calendar.clicked.connect(self._calendar_chosen)
        editor = self.lineEdit()
        assert editor is not None
        editor.textEdited.connect(self._text_edited)
        self._render_value()
        self._projecting = False

    def date_text(self) -> str:
        """Read the optional ISO date without changing the calendar or form.

        Args:
            None.

        Returns:
            Empty text for absence, otherwise a canonical yyyy-MM-dd calendar date.
        """
        return "" if self._empty else self.date().toString(Qt.DateFormat.ISODate)

    def set_value(self, value: str | None) -> None:
        """Project a validated saved ISO date or absence without creating a draft.

        Args:
            value: Canonical ISO date or None/empty text for unspecified.

        Returns:
            None. Today is only an empty calendar navigation anchor.

        Raises:
            ValueError: A provided date is invalid or not canonical ISO text.
        """
        day = QDate.fromString(value or "", Qt.DateFormat.ISODate)
        if value and (
            not day.isValid() or day.toString(Qt.DateFormat.ISODate) != value
        ):
            raise ValueError("Organization dates require ISO yyyy-MM-dd.")
        self._projecting = True
        try:
            self._empty = not value
            super().setDate(day if value else QDate.currentDate())
            self._render_value()
        finally:
            self._projecting = False
        self._notify()

    def setDate(self, date: QDate | python_date) -> None:  # noqa: N802 — Qt public API
        """Provide an explicit Qt/Python calendar date, including the navigation date.

        Args:
            date: Valid Qt or Python date; invalid Qt dates leave the value unchanged.

        Returns:
            None. Call clear or set_value(None) to provide absence.
        """
        if isinstance(date, python_date):
            native = cast(python_date, date)
            day = QDate(native.year, native.month, native.day)
        else:
            day = date
        if day.isValid():
            self.set_value(day.toString(Qt.DateFormat.ISODate))

    def clear(self) -> None:
        """Clear the optional calendar without reserving a real date as empty.

        Args:
            None.

        Returns:
            None. The form receives one value-change notification if needed.
        """
        self.set_value(None)

    def textFromDateTime(self, date_time: QDateTime | datetime) -> str:  # noqa: N802 — Qt override
        """Render absence separately from Qt's valid internal navigation anchor.

        Args:
            date_time: Native value supplied by Qt when rendering its date sections.

        Returns:
            Localized absence caption or Qt's normal localized date text.
        """
        return (
            self._not_set_text if self._empty else super().textFromDateTime(date_time)
        )

    def _render_value(self) -> None:
        """Refresh the internal text without creating a project mutation.

        Args:
            None.

        Returns:
            None. Qt keeps ownership of text editing and calendar sections.
        """
        editor = self.lineEdit()
        assert editor is not None
        editor.setText(self.textFromDateTime(self.dateTime()))

    def _text_edited(self, text: str) -> None:
        """Recognize native text Undo back to the unspecified calendar caption.

        Args:
            text: Actual user-edited internal text, including native typing replay.

        Returns:
            None. Qt owns date parsing; an empty/unspecified token clears absence.
        """
        if not self._projecting and (not text or text == self._not_set_text):
            self.clear()
        self._notify()

    def _notify(self) -> None:
        """Notify the form once per optional-date change outside projection.

        Args:
            None.

        Returns:
            None. Repeated Qt date/calendar signals are deduplicated.
        """
        value = self.date_text()
        if not self._projecting and value != self._last_value:
            self._last_value = value
            self.value_changed.emit()

    def _date_changed(self, day: QDate) -> None:
        """Accept a native section/calendar edit while ignoring programmatic projection.

        Args:
            day: New valid Qt date; the native widget already owns this value.

        Returns:
            None. The previously empty caption becomes a real calendar date.
        """
        if not self._projecting:
            self._empty = False
            self._render_value()
            self._notify()

    def _calendar_chosen(self, day: QDate) -> None:
        """Accept even a click on today's unchanged empty navigation anchor.

        Args:
            day: Actual calendar day clicked by the user, including the current date.

        Returns:
            None. Opening or dismissing the popup alone never invokes this handler.
        """
        if not self.isReadOnly():
            self.setDate(day)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802 — Qt override
        """Retain standard date entry and support Ctrl+A/Delete optional clearing.

        Args:
            event: Native key event, or None for a defensive direct call.

        Returns:
            None. Digits activate Qt's day section; navigation alone stays absent.
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
            if event.text().isdigit() and self._empty:
                self._empty = False
                self._render_value()
                self.setSelectedSection(QDateEdit.DaySection)
        super().keyPressEvent(event)
        self._notify()

    def stepBy(self, steps: int) -> None:  # noqa: N802 — Qt override
        """Delegate calendar section stepping while retaining optional read-only state.

        Args:
            steps: Signed native arrow, keyboard or wheel step count.

        Returns:
            None. A step provides a date; merely focusing the widget does not.
        """
        if self.isReadOnly():
            return
        self._empty = False
        super().stepBy(steps)
        self._render_value()
        self._notify()
