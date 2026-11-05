"""Shared readable workflow actions and title glyphs using existing packaged artwork.

Presentation only. Hosts retain callbacks, enablement, status text and history. These
helpers add no project/preference state and never discover assets from local paths.
"""

from collections.abc import Callable

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter
from PyQt5.QtWidgets import QAbstractButton, QSizePolicy, QToolButton


def set_action_icon(button: QAbstractButton, icon: QIcon, size: int = 28) -> None:
    """Fit a semantic icon beside existing action text without compressing its artwork.

    Args:
        button: Host-owned native action; callbacks and captions are retained.
        icon: Injected packaged or shared vector glyph.
        size: Logical square icon canvas; the artwork preserves its aspect ratio.

    Returns:
        None; layout only, without invoking the action.
    """
    button.setIcon(icon)
    button.setIconSize(QSize(size, size))
    button.setMinimumHeight(max(40, size + 12))


def stacked_action(text: str, callback: Callable[[], None], icon: QIcon) -> QToolButton:
    """Create a compact result action with a readable glyph above its caption.

    Args:
        text: Localized complete action caption and default tooltip.
        callback: Existing GUI-thread host operation.
        icon: Dedicated semantic glyph; no new artwork is drawn.

    Returns:
        Unparented button adopted by the host layout, preserving ordinary enabled state.
    """
    button = QToolButton()
    button.setText(text)
    button.setToolTip(text)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    button.setIcon(icon)
    button.setIconSize(QSize(44, 44))
    button.setMinimumHeight(82)
    button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    button.setStyleSheet(
        "QToolButton {background:white;color:#0B326C;border:1px solid #A9BED1;"
        "border-radius:4px;padding:6px 12px;font-weight:600;}"
        "QToolButton:hover {background:#EAF7F8;border-color:#08A9B5;}"
        "QToolButton:pressed {background:#DDF2F4;}"
        "QToolButton:disabled {color:#8898A5;background:#F4F7FA;border-color:#CBD6E2;}"
    )
    button.clicked.connect(callback)
    return button


def page_heading_icon(icon: QIcon) -> QIcon:
    """Render the drawer's same glyph in navy for a light page-heading background.

    Args:
        icon: Existing packaged step icon, possibly supplied as a light variant.

    Returns:
        Fresh navy icon preserving shape and alpha; drawer artwork is not modified.
    """
    pixmap = icon.pixmap(64, 64)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor("#0B326C"))
    painter.end()
    return QIcon(pixmap)
