"""Shared full-caption assessment tabs with measured bold text and icon padding."""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QFontMetrics, QIcon
from PyQt5.QtWidgets import QSizePolicy, QTabBar, QTabWidget

from ergotools.domain.assessments.document import AssessmentKind


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
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.setIconSize(QSize(32, 32))
        bar = self.tabBar()
        assert bar is not None
        bar.setElideMode(Qt.TextElideMode.ElideNone)
        bar.setUsesScrollButtons(True)
        bar.setExpanding(False)


class AssessmentToolTabBar(QTabBar):
    """Measure the styled semibold caption rather than Qt's unstyled text estimate."""

    def tabSizeHint(self, index: int) -> QSize:  # noqa: N802 — Qt override
        """Reserve full caption/icon geometry, including closing parentheses.

        Args:
            index: Existing tab whose literal caption is measured.

        Returns:
            Native height and a width accommodating bold 13-pixel theme text.
        """
        size = super().tabSizeHint(index)
        font = QFont(self.font())
        font.setPixelSize(13)
        font.setBold(True)
        icon = self.iconSize().width() + 8 if not self.tabIcon(index).isNull() else 0
        width = QFontMetrics(font).horizontalAdvance(self.tabText(index)) + icon + 28
        return QSize(max(size.width(), width), size.height())
