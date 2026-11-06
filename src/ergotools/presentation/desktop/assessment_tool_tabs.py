"""Shared full-caption assessment tabs with measured bold text and icon padding."""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QFontMetrics, QIcon
from PyQt5.QtWidgets import QSizePolicy, QTabBar, QTabWidget

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.presentation.desktop.theme.main_workspace import ASSESSMENT_TAB_STYLE


def assessment_tool_icon(icons: Mapping[str, QIcon], kind: AssessmentKind) -> QIcon:
    """Resolve the same packaged tool identity used in the main assessment tabs.

    Args:
        icons: Host-injected processed application icons.
        kind: Stable calculator tool identity.

    Returns:
        Shared LiFFT, DUET or Shoulder icon, without generating another asset.

    Raises:
        KeyError: The host did not provide a required application icon.
    """
    return icons["shoulder" if kind is AssessmentKind.TST else kind.value]


def assessment_tool_title(kind: AssessmentKind) -> str:
    """Read the full branded tool caption used in the main assessment interface.

    Args:
        kind: Canonical calculator identity, independent of selected UI language.

    Returns:
        Full English branded name, including its familiar abbreviation.
    """
    return {
        AssessmentKind.LIFFT: "Lifting Fatigue Failure Tool (LiFFT)",
        AssessmentKind.DUET: "Distal Upper Extremity Tool (DUET)",
        AssessmentKind.TST: "The Shoulder Tool (ST)",
    }[kind]


class AssessmentToolTabs(QTabWidget):
    """Keep the familiar tool captions intact even when the tab strip must scroll."""

    def __init__(self) -> None:
        """Install one measured bar before hosts add their assessment editors.

        Args:
            None.

        Returns:
            None; no data or tool-selection history is owned here.
        """
        super().__init__()
        self.setTabBar(AssessmentToolTabBar())
        self.setObjectName("assessmentTabs")
        self.setStyleSheet(ASSESSMENT_TAB_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.setIconSize(QSize(32, 32))
        bar = self.tabBar()
        assert bar is not None
        bar.setElideMode(Qt.TextElideMode.ElideNone)
        bar.setUsesScrollButtons(True)
        bar.setExpanding(False)


class AssessmentToolTabBar(QTabBar):
    """Reserve styled caption/icon space across native Qt platform styles."""

    def __init__(self, caption_pixel_size: int = 13) -> None:
        """Match the host theme while retaining full captions via strip scrolling.

        Args:
            caption_pixel_size: Actual theme text size in logical pixels.

        Returns:
            None; this bar owns geometry only, never tool selection or history.
        """
        super().__init__()
        self.caption_pixel_size = caption_pixel_size
        self.setElideMode(Qt.TextElideMode.ElideNone)
        self.setUsesScrollButtons(True)
        self.setExpanding(False)

    def tabSizeHint(self, index: int) -> QSize:  # noqa: N802 — Qt override
        """Reserve full caption/icon geometry, including closing parentheses.

        Args:
            index: Existing tab whose literal caption is measured.

        Returns:
            Native height and a width accommodating the host theme's bold caption.
        """
        size = super().tabSizeHint(index)
        font = QFont(self.font())
        font.setPixelSize(self.caption_pixel_size)
        font.setBold(True)
        icon = self.iconSize().width() + 8 if not self.tabIcon(index).isNull() else 0
        width = QFontMetrics(font).horizontalAdvance(self.tabText(index)) + icon + 28
        return QSize(max(size.width(), width), size.height())


class AssessmentResultTabs(QTabWidget):
    """Show readable result/summary tabs instead of native miniature segments."""

    def __init__(self) -> None:
        """Compose the common readable tool-result or Worker/Job summary selector.

        Args:
            None.

        Returns:
            None; the host retains tab contents, selected-tool history and results.
        """
        super().__init__()
        self.setObjectName("assessmentResultTabs")
        self.setTabBar(AssessmentToolTabBar(12))
        self.setIconSize(QSize(24, 24))
        self.setStyleSheet(
            "#assessmentResultTabs::tab-bar {alignment:left;}"
            "#assessmentResultTabs::pane {background:white;border:1px solid #D5DEE5;}"
            "#assessmentResultTabs QTabBar::tab {background:#EDF2F5;color:#405866;"
            "font-size:12px;font-weight:600;min-height:28px;padding:3px 10px;"
            "border:1px solid #BCC9D3;}"
            "#assessmentResultTabs QTabBar::tab:selected {background:#DDF3F5;"
            "color:#087E91;border-bottom:3px solid #08A9B5;}"
            "#assessmentResultTabs QTabBar::tab:hover:!selected {background:#EAF7F8;}"
        )
