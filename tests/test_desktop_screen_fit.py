"""Keep shared tab captions and complete PLOT results inside desktop work areas.

Use disposable native repositories and measured Qt geometry. These regressions
exercise taskbar/title-bar budgets, demographic disclosure, both languages and
all risk modes; they do not substitute for the owner's Windows visual retest.
"""

from pathlib import Path

import pytest
from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QApplication, QWidget

from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.assessment_tool_tabs import (
    AssessmentToolTabBar,
    AssessmentToolTabs,
    assessment_tool_title,
)
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from tests.test_plot_results import project as project
from tests.test_plot_window import host


@pytest.mark.parametrize("language", tuple(Language))
def test_plot_fits_windows_work_area_with_all_results(
    project: AssessmentProjectFile, tmp_path: Path, language: Language
) -> None:
    """Retain the full rail, charts and gauges within a 1920x1200 desktop budget.

    Args:
        project: Isolated native repository, never an operational project.
        tmp_path: Private map directory.
        language: English and longer Spanish explanations must both fit.

    Returns:
        None; the 1152-pixel work area includes a 40-pixel frame and full results.
    """
    window = host(project, tmp_path, language=language)
    window.fit_available_geometry(QRect(0, 0, 1920, 1152), 40)
    QApplication.processEvents()
    for button in (
        window.history_actions.undo_button,
        window.history_actions.redo_button,
    ):
        assert (
            button.width() >= button.fontMetrics().horizontalAdvance(button.text()) + 14
        )
    for mode in PlotRiskView:
        window.filters.risk_buttons[mode].click()
        for expanded in (True, False):
            window.filters.demographics.setChecked(expanded)
            QApplication.processEvents()
            QApplication.processEvents()
            assert window.height() + 40 <= 1152
            for panel in (window.filters, window.splitter, window.outcome):
                assert window.rect().contains(panel.geometry())
            rail = window.map_panel.rail
            for button in window.map_panel.buttons.values():
                if button.isVisible():
                    assert rail.rect().contains(
                        QRect(button.mapTo(rail, QPoint()), button.size())
                    )
            for gauge in (window.outcome.individual_gauge, window.outcome.job_gauge):
                assert gauge.height() >= 144
                assert gauge.parentWidget().rect().contains(gauge.geometry())
            assert window.tools.canvas.height() >= 220
            canvas = window.map_panel.canvas
            assert canvas.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
            assert canvas.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    window.fit_available_geometry(QRect(0, 0, 2400, 1600), 40)
    QApplication.processEvents()
    assert window.map_panel.buttons["open"].height() == 63
    assert window.tools.canvas.minimumHeight() == 250
    window.close()
    window.deleteLater()


def test_assessment_tabs_measure_full_styled_captions() -> None:
    """Use the shared measured bar for full titles, with scrolling if constrained.

    Args:
        None.

    Returns:
        None; each tab reserves icon plus bold themed text instead of truncating it.
    """
    tabs = AssessmentToolTabs()
    tabs.setStyleSheet(MAIN_WORKSPACE_STYLE)
    tabs.setIconSize(QSize(36, 36))
    icons = load_icons()
    for kind in AssessmentKind:
        asset = "shoulder" if kind is AssessmentKind.TST else kind.value
        tabs.addTab(QWidget(), icons[asset], assessment_tool_title(kind))
    tabs.resize(980, 200)
    tabs.show()
    QApplication.processEvents()
    bar = tabs.tabBar()
    assert isinstance(bar, AssessmentToolTabBar) and bar.usesScrollButtons()
    font = QFont(bar.font())
    font.setPixelSize(13)
    font.setBold(True)
    for index in range(tabs.count()):
        assert bar.tabRect(index).width() >= (
            QFontMetrics(font).horizontalAdvance(tabs.tabText(index)) + 36 + 8
        )
    tabs.close()
    tabs.deleteLater()
