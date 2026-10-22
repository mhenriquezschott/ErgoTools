"""Native Qt clock entry, optional midnight and localized form integration boundaries.

Tests create only owned widgets and private display clipboard values. Qt retains
section parsing/stepping; assertions distinguish absence from midnight and verify
that readonly/focus/paste operations cannot manufacture a clock value.
"""

from datetime import time

import pytest
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLineEdit

from ergotools.presentation.desktop.optional_time_edit import OptionalTimeEdit

# Retain the one QApplication required by real native clock controls.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("8:30", "08:30"),
        ("0830", "08:30"),
        ("00:00", "00:00"),
        ("23:59", "23:59"),
        ("1234", "12:34"),
        ("8:", "08:00"),
    ],
)
def test_standard_clock_keyboard_format_and_sections(typed: str, expected: str) -> None:
    """Qt supplies the colon, zero padding and section navigation for real typing.

    Args:
        typed: User keystrokes, including a short hour or compact four-digit entry.
        expected: Canonical clock after native section parsing.

    Returns:
        None; entry starts from unspecified and leaves minutes ready after a colon.
    """
    editor = OptionalTimeEdit("Not set")
    try:
        editor.show()
        _APP.setActiveWindow(editor)
        editor.setFocus()
        _APP.processEvents()
        assert editor.clock_text() == ""
        QTest.keyClicks(editor, typed)
        assert editor.clock_text() == expected
        assert editor.text() == expected
        if typed == "8:":
            assert editor.currentSection() == editor.MinuteSection
    finally:
        editor.close()
        editor.deleteLater()


@pytest.mark.parametrize("caption", ["Not set", "Sin especificar"])
def test_optional_clock_midnight_clear_step_and_focus(caption: str) -> None:
    """Missing values never reserve midnight or turn focus into a project value.

    Args:
        caption: English or Spanish unspecified caption.

    Returns:
        None; repeated clearing, midnight and native hour/minute stepping are distinct.
    """
    editor = OptionalTimeEdit(caption)
    try:
        editor.show()
        _APP.setActiveWindow(editor)
        editor.setFocus()
        _APP.processEvents()
        assert editor.text() == caption and editor.clock_text() == ""
        editor.clearFocus()
        _APP.processEvents()
        assert editor.clock_text() == ""
        for _ in range(2):
            editor.setTime(QTime(0, 0))
            assert editor.clock_text() == "00:00"
            editor.selectAll()
            QTest.keyClick(editor, Qt.Key.Key_Delete)
            assert editor.clock_text() == "" and editor.text() == caption
            editor.stepUp()
            assert editor.clock_text() == "01:00"
            editor.setCurrentSection(editor.MinuteSection)
            editor.stepUp()
            assert editor.clock_text() == "01:01"
            editor.clear()
        editor.setTime(time(8, 30))
        assert editor.clock_text() == "08:30"
        editor.setTime(QTime())
        assert editor.clock_text() == "08:30"
    finally:
        editor.close()
        editor.deleteLater()


@pytest.mark.parametrize("value", ["24:00", "12:60", "08:0", "not a time"])
def test_malformed_loaded_clock_is_retained_until_user_correction(value: str) -> None:
    """Bad historical text is not silently replaced by an internal default clock.

    Args:
        value: Invalid stored/programmatic value bypassing normal keyboard parsing.

    Returns:
        None; original text remains available and ordinary typing corrects the field.
    """
    editor = OptionalTimeEdit("Not set")
    try:
        editor.set_value(value)
        assert editor.clock_text() == value and not editor.is_acceptable()
        editor.show()
        _APP.setActiveWindow(editor)
        editor.setFocus()
        _APP.processEvents()
        QTest.keyClicks(editor, "8:30")
        assert editor.clock_text() == "08:30" and editor.is_acceptable()
        editor.set_value("8:30")
        assert editor.clock_text() == "08:30"
    finally:
        editor.close()
        editor.deleteLater()


@pytest.mark.parametrize(
    ("pasted", "expected"),
    [
        ("8:30", "08:30"),
        (" 23:59 ", "23:59"),
        ("00:00", "00:00"),
        ("24:00", ""),
        ("08:", ""),
        ("letters", ""),
    ],
)
def test_keyboard_paste_does_not_create_a_default_on_invalid_input(
    pasted: str, expected: str
) -> None:
    """Paste uses Qt clock parsing and leaves an absent value absent on rejection.

    Args:
        pasted: Private display clipboard text, including valid/invalid clocks.
        expected: Canonical optional value after Ctrl+V.

    Returns:
        None; invalid replacement of an existing valid clock is equally inert.
    """
    editor = OptionalTimeEdit("Not set")
    clipboard = _APP.clipboard()
    assert clipboard is not None
    previous = clipboard.text()
    try:
        editor.show()
        _APP.setActiveWindow(editor)
        editor.setFocus()
        _APP.processEvents()
        clipboard.setText(pasted)
        QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        assert editor.clock_text() == expected
        editor.set_value("09:15")
        clipboard.setText("invalid")
        QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        assert editor.clock_text() == "09:15"
    finally:
        clipboard.setText(previous)
        editor.close()
        editor.deleteLater()


def test_readonly_clock_and_duplicate_notifications_are_inert() -> None:
    """Readonly user events and repeated projections do not add value changes.

    Args:
        None.

    Returns:
        None; a provided midnight emits once and clearing it emits once.
    """
    editor = OptionalTimeEdit("Not set")
    changes = []
    try:
        editor.value_changed.connect(lambda: changes.append(editor.clock_text()))
        editor.set_value(None)
        editor.setReadOnly(True)
        editor.show()
        _APP.setActiveWindow(editor)
        editor.setFocus()
        _APP.processEvents()
        QTest.keyClicks(editor, "8:30")
        editor.stepBy(1)
        assert editor.clock_text() == "" and not changes
        editor.setReadOnly(False)
        editor.set_value("00:00")
        editor.set_value("00:00")
        assert changes == ["00:00"]
        editor.clear()
        editor.clear()
        assert changes == ["00:00", ""]
        assert editor.findChild(QLineEdit) is not None
    finally:
        editor.close()
        editor.deleteLater()
