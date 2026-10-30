"""Static-strip buffering and read-only station assessment evidence contracts.

Native Qt tests use disposable catalogs only. Evidence must follow the selected shift
and retain honest missing/historical states; buffering must never own input or data.
"""

from dataclasses import replace

import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout

from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.presentation.desktop.buffered_controls import BufferedControls
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssessmentPreview,
    WorkplaceAssignmentDialog,
)
from tests.test_history_persistence import HIERARCHY, JOBS, STATION
from tests.test_main_navigation import window as window

# Keep one application across independent widget and integrated-window cases.
_APP = QApplication.instance() or QApplication([])


def test_buffer_keeps_live_controls_and_releases_on_resize() -> None:
    """The buffer is mouse-transparent and temporary; controls retain normal actions.

    Args:
        None.

    Returns:
        None; no duplicated widgets/state persist after thaw or window resizing.
    """
    strip = BufferedControls()
    layout = QVBoxLayout(strip)
    button = QPushButton("Live action")
    layout.addWidget(button)
    clicked: list[bool] = []
    button.clicked.connect(clicked.append)
    strip.resize(300, 65)
    strip.show()
    _APP.processEvents()
    try:
        strip.freeze()
        assert strip.buffer.isVisible() and not strip.buffer.pixmap().isNull()
        assert strip.buffer.testAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        assert strip.childAt(button.geometry().center()) is button
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        assert clicked == [False] and button.text() == "Live action"
        strip.resize(340, 65)
        _APP.processEvents()
        assert strip.buffer.isHidden() and strip.buffer.pixmap().isNull()
        strip.freeze()
        strip.thaw()
        assert strip.buffer.isHidden() and button.isVisible()
    finally:
        strip.close()
        strip.deleteLater()


def test_navigation_interrupts_buffer_and_summary_uses_available_width(
    window: LifftWindow,
) -> None:
    """Only static painting is buffered; new worker data becomes visible immediately.

    Args:
        window: Disposable integrated project with two assessed workers.

    Returns:
        None; the disclosure sits at the right edge and source changes settle motion.
    """
    nav = window.main_navigation
    nav.context_disclosure.click()
    QTest.qWait(35)
    assert nav.worker_controls.buffer.isVisible()
    right = (
        nav.context_disclosure.mapTo(window, QPoint()).x()
        + nav.context_disclosure.width()
    )
    assert (
        right
        == nav.standalone_button.mapTo(window, QPoint()).x()
        + nav.standalone_button.width()
    )
    assert nav.location_browser.summary.width() > 600
    window.navigate_worker("x")
    assert nav.worker_controls.buffer.isHidden()
    assert nav.workers.currentData() == "x"
    assert window.assessment_navigation.view.worker_id == "x"


@pytest.mark.parametrize("language", list(Language))
def test_picker_marks_saved_missing_and_historical_for_current_shift(
    language: Language,
) -> None:
    """Evidence badges distinguish calculated/blank/current/history without writes.

    Args:
        language: Both supported languages retain the same source-state identities.

    Returns:
        None; shift updates badges; ordinary assignment pickers keep two columns.
    """
    second, third = (
        replace(STATION, station_id="ST02"),
        replace(STATION, station_id="ST03"),
    )
    hierarchy = replace(
        HIERARCHY,
        work=replace(
            HIERARCHY.work,
            stations=(*HIERARCHY.work.stations, second, third),
            shifts=("Day", "Night"),
        ),
    )
    previews = (
        WorkplaceAssessmentPreview(STATION.at_shift("Day"), 40),
        WorkplaceAssessmentPreview(STATION.at_shift("Night"), None),
        WorkplaceAssessmentPreview(second.at_shift("Day"), 55, active=False),
    )
    dialog = WorkplaceAssignmentDialog(
        hierarchy,
        JOBS,
        "w",
        load_icons(),
        reuse_existing=True,
        assessments=previews,
        assessment_tool="LiFFT",
        language=language,
    )
    try:
        assert dialog.tree.columnCount() == 3
        dialog.select_workplace(STATION.at_shift("Day"))
        item = dialog._stations[STATION]
        assert "40.0%" in item.text(2)
        assert item.background(2).color().isValid()
        assert "LiFFT" in item.toolTip(2)
        assert (
            "Histórica" if language is Language.SPANISH else "Historical"
        ) in dialog._stations[second].text(2)
        assert dialog._stations[third].text(2) == (
            "Nueva" if language is Language.SPANISH else "New"
        )
        dialog.shift.setCurrentText("Night")
        assert item.text(2) == (
            "Guardada · Sin calcular"
            if language is Language.SPANISH
            else "Saved · Not calculated"
        )
        assert dialog._stations[second].text(2) == (
            "Nueva" if language is Language.SPANISH else "New"
        )
        dialog.shift.clear()
        assert not dialog.accept_button.isEnabled()
    finally:
        dialog.close()
        dialog.deleteLater()
    legacy = WorkplaceAssignmentDialog(hierarchy, JOBS, "w", load_icons())
    try:
        assert legacy.tree.columnCount() == 2
    finally:
        legacy.close()
        legacy.deleteLater()
