"""Code-native PLOT pan/fit glyphs and legible zoom cursors in the shared palette.

Presentation layer. Draw transparent Qt pixmaps at normalized icon/cursor sizes;
no external resources, package changes, scientific values or persistent state.
"""

from typing import Literal

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap, QPolygonF


def navigation_icon(kind: Literal["pan", "fit", "select"]) -> QIcon:
    """Draw the two navigation actions missing from the packaged icon set.

    Args:
        kind: Selection arrow, four-way pan arrows or fit-image frame identity.

    Returns:
        Transparent 96-pixel icon using the existing navy/teal line palette.
    """
    pixmap = QPixmap(96, 96)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#0B326C"), 3))
    if kind == "select":
        painter.setBrush(QColor("white"))
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(27, 13),
                    QPointF(27, 77),
                    QPointF(42, 61),
                    QPointF(55, 85),
                    QPointF(65, 79),
                    QPointF(52, 55),
                    QPointF(75, 53),
                ]
            )
        )
    elif kind == "pan":
        for start, end, wing1, wing2 in (
            ((48, 48), (48, 13), (38, 23), (58, 23)),
            ((48, 48), (48, 83), (38, 73), (58, 73)),
            ((48, 48), (13, 48), (23, 38), (23, 58)),
            ((48, 48), (83, 48), (73, 38), (73, 58)),
        ):
            painter.drawLine(QPointF(*start), QPointF(*end))
            painter.drawLine(QPointF(*end), QPointF(*wing1))
            painter.drawLine(QPointF(*end), QPointF(*wing2))
    else:
        painter.drawRect(QRectF(19, 27, 58, 42))
        painter.setPen(QPen(QColor("#008DA4"), 3))
        for x, y, sx, sy in (
            (11, 17, 1, 1),
            (85, 17, -1, 1),
            (11, 79, 1, -1),
            (85, 79, -1, -1),
        ):
            painter.drawLine(QPointF(x, y + sy * 12), QPointF(x, y))
            painter.drawLine(QPointF(x, y), QPointF(x + sx * 12, y))
    painter.end()
    return QIcon(pixmap)


def zoom_cursor(*, out: bool) -> QCursor:
    """Make a magnifier cursor that remains visible over bright/dark plant pixels.

    Args:
        out: True draws minus; False draws plus. The hotspot is the lens center.

    Returns:
        Native bitmap cursor; drawing does not change application-wide cursor state.
    """
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#0B326C"), 2))
    painter.setBrush(QColor("white"))
    painter.drawEllipse(QRectF(2, 2, 20, 20))
    painter.drawLine(QPointF(20, 20), QPointF(29, 29))
    painter.setPen(QPen(QColor("#008DA4"), 2))
    painter.drawLine(QPointF(7, 12), QPointF(17, 12))
    if not out:
        painter.drawLine(QPointF(12, 7), QPointF(12, 17))
    painter.end()
    return QCursor(pixmap, 12, 12)
