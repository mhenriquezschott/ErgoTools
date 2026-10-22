"""Reference popup painting for readable main-window worker selection.

Presentation layer. Configure the owned Qt popup and delegate on the GUI thread.
Explicit palette roles and selected/hover painting avoid native theme delegates
rendering white text over a white background. This module owns no project state,
navigation signals, assessment colors or storage operations.
"""

from typing import cast

from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QColor, QPainter, QPalette
from PyQt5.QtWidgets import (
    QComboBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)


class ComboPopupDelegate(QStyledItemDelegate):
    """Paint reference teal selection without changing item text or worker identity."""

    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Supply explicit contrast for selected and mouse-hovered popup rows.

        Args:
            painter: Qt-owned painter for the item; None performs no painting.
            option: Borrowed Qt state/geometry; copy before changing its palette.
            index: Exact model item to paint; no selection or data mutation occurs.

        Returns:
            None after the standard styled delegate paints text over the reference
            teal background. Unhighlighted rows retain normal dark text on white.
        """
        if painter is None:
            return
        styled = QStyleOptionViewItem(option)
        if styled.state & (
            QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver
        ):
            # Qt flag overloads admit int in stubs; this operation retains State flags.
            styled.state = cast(
                QStyle.State, styled.state | QStyle.StateFlag.State_Selected
            )
            styled.palette.setColor(QPalette.Highlight, QColor("#087E91"))
            styled.palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
            painter.fillRect(styled.rect, QColor("#087E91"))
        super().paint(painter, styled, index)


def style_combo_popup(combo: QComboBox) -> None:
    """Install the reference palette, spacing and an owned contrast-safe delegate.

    Args:
        combo: Newly constructed main-window selector; Qt owns its popup and delegate.
            Configure once without connecting signals or changing current selection.

    Returns:
        None; selected/hovered rows use white text on teal, other rows dark on white.
        The combo retains the established surrounding application stylesheet.
    """
    view = combo.view()
    assert view is not None
    palette = view.palette()
    for role, value in (
        (QPalette.Base, "#FFFFFF"),
        (QPalette.Text, "#1B2933"),
        (QPalette.Highlight, "#087E91"),
        (QPalette.HighlightedText, "#FFFFFF"),
    ):
        palette.setColor(role, QColor(value))
    view.setPalette(palette)
    view.setItemDelegate(ComboPopupDelegate(view))
    view.setStyleSheet(
        "QAbstractItemView { background: white; color: #1B2933; outline: 0; }"
        "QAbstractItemView::item { min-height: 28px; padding: 2px 7px; }"
        "QAbstractItemView::item:selected, QAbstractItemView::item:hover "
        "{ background: #087E91; color: white; }"
    )
