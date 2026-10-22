"""Verify native metadata, menu icon metrics and long-assessment edit locations.

Test layer: use isolated classified projects and actual Qt controls. Calculations,
reference assets and projects are never modified by the tests.
"""

from pathlib import Path

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel, QMenu, QPushButton, QStyle

from ergotools.application.settings import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.menu_icon_style import (
    MenuIconStyle,
    install_menu_icon_style,
)
from ergotools.presentation.desktop.project_properties_dialog import (
    ProjectPropertiesDialog,
)
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("row", [0, 24])
def test_fifty_task_undo_redo_returns_to_edit_scroll(
    window: LifftWindow,
    index: int,
    row: int,
) -> None:
    """Undo/Redo returns to the editing viewport even after the user scrolls elsewhere.

    Args:
        window: Fixture-owned integrated classified three-tool assessment.
        index: LiFFT, DUET or ST index; numeric input or selector edits are exercised.
        row: First or middle task in the fifty-task grid.

    Returns:
        None; assert exact source replay and horizontal/vertical offsets after queued
        layout/focus processing, using actual toolbar buttons and focused controls.
    """
    window.assessment_tabs.setCurrentIndex(index)
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(50)
    window.refresh()
    QTest.qWait(30)
    panel = window.secondary_panel() or window.task_panel
    area = panel.body_scroll
    horizontal, vertical = area.horizontalScrollBar(), area.verticalScrollBar()
    assert vertical.maximum() > 0
    vertical.setValue(0 if row == 0 else vertical.maximum() // 2)
    control = panel.inputs[row][0]
    control.setFocus()
    QTest.qWait(30)
    position = (horizontal.value(), vertical.value())
    active = window.presenter.workspace.active
    before = active.state
    if index == 0:
        control.setText("13")
        control.textEdited.emit("13")
        assert panel.commit_inputs()
        window.refresh()
    else:
        control.setCurrentIndex((control.currentIndex() + 1) % control.count())
    changed = active.state
    assert changed != before
    # Scroll away deliberately; replay must restore where this operation occurred.
    vertical.setValue(vertical.maximum() if row == 0 else 0)
    undo = window.main_navigation.toolbar.widgetForAction(
        window.main_navigation.toolbar_actions["undo"]
    )
    assert undo.isEnabled()
    QTest.mouseClick(undo, Qt.MouseButton.LeftButton)
    QTest.qWait(50)
    assert active.state is before
    assert (horizontal.value(), vertical.value()) == position
    vertical.setValue(vertical.maximum() if row == 0 else 0)
    redo = window.main_navigation.toolbar.widgetForAction(
        window.main_navigation.toolbar_actions["redo"]
    )
    assert redo.isEnabled()
    QTest.mouseClick(redo, Qt.MouseButton.LeftButton)
    QTest.qWait(50)
    assert active.state is changed
    assert (horizontal.value(), vertical.value()) == position


def test_menu_icon_metric_is_menu_only_and_install_is_idempotent(
    window: LifftWindow,
) -> None:
    """Use 25 logical-pixel menu icons without changing button icon metrics.

    Args:
        window: Fixture-owned integrated window installing the application's style.

    Returns:
        None; compare base/proxy metrics through Qt's stylesheet wrapper and
        ensure repeated setup never compounds.
    """
    app = QApplication.instance()
    style = app.style()
    proxy = app.findChild(MenuIconStyle)
    assert proxy is not None
    menu = QMenu(window)
    button = QPushButton(window)
    metric = QStyle.PixelMetric.PM_SmallIconSize
    assert style.pixelMetric(metric, None, menu) == 25
    # Qt5 stylesheet menu painting asks this metric without a widget.
    assert style.pixelMetric(metric) == 25
    assert style.pixelMetric(metric, None, button) == proxy.baseStyle().pixelMetric(
        metric, None, button
    )
    install_menu_icon_style(app)
    assert app.style() is style


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_properties_native_fields_long_plain_description_and_resize(
    window: LifftWindow,
    tmp_path: Path,
    language: Language,
) -> None:
    """Display applicable metadata, literal long descriptions and full copyable paths.

    Args:
        window: Qt owner and processed icon provider supplied by the fixture.
        tmp_path: Disposable project pathname; no file needs creating.
        language: English or Spanish interface; literal metadata is not translated.

    Returns:
        None; verify read-only values, missing optional metadata, no obsolete fields
        and usable resizing without unbounded description growth.
    """
    description = "<b>literal markup</b>\n" + "Long project description. " * 300
    path = tmp_path / "a long folder name" / "test.ergprj"
    metadata = ProjectMetadata(
        "p", "A project", MeasurementSystem.METRIC, description=description
    )
    dialog = ProjectPropertiesDialog(
        metadata, str(path), language, parent=window, icons=window.icons
    )
    try:
        dialog.show()
        QApplication.processEvents()
        assert set(dialog.fields) == {
            "name",
            "file",
            "location",
            "created",
            "language",
            "units",
        }
        assert (
            dialog.description.toPlainText() == description
            and dialog.description.isReadOnly()
        )
        assert dialog.fields["location"].text() == str(path)
        assert dialog.fields["location"].toolTip() == str(path)
        assert all(field.isReadOnly() for field in dialog.fields.values())
        assert dialog.fields["created"].text() == (
            "Sin registro" if language is Language.SPANISH else "Not recorded"
        )
        assert not dialog.close_button.icon().isNull()
        icon = dialog.findChild(QLabel, "propertiesIcon")
        heading = dialog.findChild(QLabel, "propertiesHeading")
        assert icon.geometry().right() < heading.geometry().left()
        dialog.resize(900, 650)
        QApplication.processEvents()
        assert dialog.description.isVisible() and dialog.close_button.isVisible()
        assert dialog.description.height() < dialog.height()
    finally:
        dialog.close()
        dialog.deleteLater()
