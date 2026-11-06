"""Keep light ErgoTools panels readable when native desktop defaults are dark.

Use actual Qt widgets and a controlled dark application palette. No OS theme is
changed. Native chooser exclusions and application-palette preservation are verified
separately from real macOS acceptance, which remains an owner deployment check.
"""

import gc
from collections.abc import Iterator
from pathlib import Path

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFontDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.presentation.desktop.assessment_location_browser import (
    AssessmentLocation,
)
from ergotools.presentation.desktop.assessment_tool_tabs import (
    AssessmentResultTabs,
    assessment_tool_icon,
)
from ergotools.presentation.desktop.theme.dialogs import install_dialog_theme
from ergotools.presentation.desktop.theme.job_management import JOB_MANAGEMENT_STYLE
from ergotools.presentation.desktop.theme.organization import ORGANIZATION_STYLE

# Qt widget ownership is process-scoped; each probe restores the original palette.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def dark_palette() -> Iterator[QPalette]:
    """Supply dark native colors while retaining the original application palette.

    Args:
        None.

    Yields:
        Dark application palette; restored after widgets are released by each test.
    """
    original = QPalette(_APP.palette())
    dark = QPalette(original)
    for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            dark.setColor(group, role, QColor("#FFFFFF"))
        for role in (QPalette.Window, QPalette.Base, QPalette.Button):
            dark.setColor(group, role, QColor("#242424"))
    _APP.setPalette(dark)
    install_dialog_theme(_APP)
    yield dark
    _APP.setPalette(original)
    _APP.processEvents()


def test_owned_forms_inherit_readable_colors_without_replacing_result_styles(
    dark_palette: QPalette,
) -> None:
    """Child labels, inputs and combo text stay readable under a dark native theme.

    Args:
        dark_palette: Controlled native defaults, restored by the fixture.

    Returns:
        None; no application-wide palette change and no override of explicit colors.
    """
    gc.collect()
    dialog = QDialog()
    dialog.setStyleSheet(JOB_MANAGEMENT_STYLE)
    layout = QFormLayout(dialog)
    entry = QLineEdit("Recorded value")
    entry.setStyleSheet("background:white;")
    combo = QComboBox()
    combo.setEditable(True)
    combo.addItem("Worker W01")
    combo.setStyleSheet("background:white;")
    layout.addRow("Task name", entry)
    layout.addRow("Worker", combo)
    colored = QLabel("High result")
    colored.setStyleSheet("background:#FF3B30;color:white;")
    layout.addRow(colored)
    dialog.show()
    _APP.processEvents()
    assert entry.palette().color(QPalette.Text) == QColor("#1B2933")
    assert combo.palette().color(QPalette.Text) == QColor("#1B2933")
    editor = combo.lineEdit()
    assert editor is not None
    assert editor.palette().color(QPalette.Text) == QColor("#1B2933")
    assert dialog.palette().color(QPalette.WindowText) == QColor("#1B2933")
    assert colored.palette().color(QPalette.WindowText) == QColor("white")
    assert _APP.palette().color(QPalette.Text) == dark_palette.color(QPalette.Text)
    QCoreApplication.sendEvent(dialog, QEvent(QEvent.Type.ApplicationPaletteChange))
    assert entry.palette().color(QPalette.Text) == QColor("#1B2933")
    dialog.close()
    dialog.deleteLater()
    _APP.processEvents()


@pytest.mark.parametrize("chooser_type", [QFileDialog, QColorDialog, QFontDialog])
def test_native_choosers_keep_system_palette(
    dark_palette: QPalette, chooser_type: type[QDialog]
) -> None:
    """Do not force light colors or application styling onto system choosers.

    Args:
        dark_palette: Controlled dark OS-like palette.
        chooser_type: Native file, color or font selector family.

    Returns:
        None; event observation is transparent and the chooser retains native text.
    """
    dialog = chooser_type()
    before = QPalette(dialog.palette())
    dialog.ensurePolished()
    QCoreApplication.sendEvent(dialog, QEvent(QEvent.Type.ApplicationPaletteChange))
    assert dialog.palette().color(QPalette.Text) == before.color(QPalette.Text)
    assert dialog.palette().color(QPalette.Text) == dark_palette.color(QPalette.Text)
    dialog.deleteLater()
    _APP.processEvents()


def test_main_window_text_uses_owned_light_palette(
    dark_palette: QPalette, tmp_path: Path
) -> None:
    """Exercise the real integrated window instead of a test-defined fake subclass.

    Args:
        dark_palette: Controlled dark native application defaults.
        tmp_path: Private settings path; no personal files/projects are opened.

    Returns:
        None; worker and repolished workplace selectors retain readable foregrounds.
    """
    window = create_window(
        tmp_path / "settings.json", original_controls=True, original_navigation=True
    )
    window.show()
    _APP.processEvents()
    assert window.palette().color(QPalette.WindowText) == QColor("#1B2933")
    # With no loaded project this selector is intentionally disabled/gray; it
    # must still contrast against the light panel rather than inherit white text.
    assert (
        window.main_navigation.workers.palette().color(QPalette.Text).lightness() < 170
    )
    browser = window.main_navigation.location_browser
    row = AssessmentLocation(
        "source",
        1,
        WorkplaceContext("Plant", "Packing", "Line A", "ST01", "1"),
        "",
        13.2,
    )
    for identity in (row.document_id, None, row.document_id):
        browser.update_rows((row,), identity, Language.ENGLISH, "LiFFT")
        _APP.processEvents()
        for combo in browser.combos:
            assert combo.palette().color(QPalette.Active, QPalette.Text) == QColor(
                "#1B2933"
            )
    assert _APP.palette().color(QPalette.Text) == dark_palette.color(QPalette.Text)
    window.close()
    window.deleteLater()
    _APP.processEvents()


def test_result_tabs_keep_complete_captions_and_icons(dark_palette: QPalette) -> None:
    """Measure all short tool captions without relying on native mini-tab metrics.

    Args:
        dark_palette: Native palette whose selected text would otherwise be inherited.

    Returns:
        None; icon/text widths fit, captions do not elide and scrolling stays available.
    """
    tabs = AssessmentResultTabs()
    icons = load_icons()
    for kind in AssessmentKind:
        tabs.addTab(QWidget(), assessment_tool_icon(icons, kind), kind.value.upper())
    tabs.resize(500, 160)
    tabs.show()
    _APP.processEvents()
    bar = tabs.tabBar()
    assert bar is not None
    font = QFont(bar.font())
    font.setPixelSize(12)
    font.setBold(True)
    assert bar.elideMode() == Qt.TextElideMode.ElideNone
    assert bar.usesScrollButtons() and tabs.iconSize() == QSize(24, 24)
    for i in range(tabs.count()):
        assert bar.tabRect(i).width() >= (
            QFontMetrics(font).horizontalAdvance(tabs.tabText(i)) + 24 + 8
        )
    tabs.close()
    tabs.deleteLater()
    _APP.processEvents()


def test_organization_tree_and_editors_have_explicit_dark_text(
    dark_palette: QPalette,
) -> None:
    """Keep unselected hierarchy names readable beside a selected plant.

    Args:
        dark_palette: Native dark defaults; the application palette remains unchanged.

    Returns:
        None; real tree/editor controls keep their source text and dark foregrounds.
    """
    dialog = QDialog()
    dialog.setStyleSheet(ORGANIZATION_STYLE)
    layout = QFormLayout(dialog)
    tree = QTreeWidget()
    tree.setHeaderLabels(["Location hierarchy", "Type"])
    first = QTreeWidgetItem(["Riverside Plant", "Plant"])
    other = QTreeWidgetItem(["Workflow Plant", "Plant"])
    tree.addTopLevelItems([first, other])
    tree.setCurrentItem(first)
    entry = QLineEdit("Packing")
    layout.addRow(tree)
    layout.addRow("Section name", entry)
    dialog.show()
    _APP.processEvents()
    assert tree.palette().color(QPalette.Text) == QColor("#1B2933")
    assert entry.palette().color(QPalette.Text) == QColor("#1B2933")
    assert other.text(0) == "Workflow Plant" and not other.isSelected()
    assert _APP.palette().color(QPalette.Text) == dark_palette.color(QPalette.Text)
    dialog.close()
    dialog.deleteLater()
    _APP.processEvents()
