"""Shared read-only risk badge painting for assessment tables and hierarchy pickers.

Presentation only. Model roles supply already calculated display values/colors; the
standard selection in other columns remains independent of badge readability.
"""

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem


class AssessmentBadgeDelegate(QStyledItemDelegate):
    """Keep risk badges readable even while their hierarchy row is selected."""

    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Paint the supplied source-state badge without altering tree selection.

        Args:
            painter: Borrowed Qt painter, absent during defensive no-op calls.
            option: Qt-owned geometry/font; never modified.
            index: Read-only assessment cell with explicit background/foreground roles.

        Returns:
            None; native selection and risk colors stay independently visible.
        """
        if painter is None:
            return
        brush = index.data(Qt.ItemDataRole.BackgroundRole)
        if not isinstance(brush, QBrush):
            super().paint(painter, option, index)
            return
        painter.save()
        painter.fillRect(option.rect.adjusted(3, 3, -3, -3), brush)
        painter.setPen(QColor("#102A43"))
        painter.setFont(option.font)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        rect = option.rect.adjusted(8, 0, -8, 0)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            option.fontMetrics.elidedText(
                text, Qt.TextElideMode.ElideRight, rect.width()
            ),
        )
        painter.restore()
