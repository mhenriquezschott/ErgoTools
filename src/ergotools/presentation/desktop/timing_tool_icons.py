"""Native vector timing tools using the shared application palette and proportions."""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF


def timing_tool_icon(tool: str) -> QIcon:
    """Draw the selected timeline action without loading external icon resources.

    Args:
        tool: select, split, draw_break, move, join or remove.

    Returns:
        Transparent padded icon matching ordinary secondary-window controls.

    Raises:
        ValueError: Tool is unsupported.
    """
    image = QPixmap(64, 64)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(2, 2)
    painter.setPen(QPen(QColor("#0B326C"), 1.7))
    if tool == "select":
        painter.drawPolygon(
            QPolygonF(
                [QPointF(8, 4), QPointF(25, 18), QPointF(17, 18), QPointF(13, 27)]
            )
        )
    elif tool == "split":
        painter.drawEllipse(QRectF(5, 19, 7, 7))
        painter.drawEllipse(QRectF(20, 19, 7, 7))
        painter.drawLine(QPointF(10, 21), QPointF(25, 5))
        painter.drawLine(QPointF(22, 21), QPointF(7, 5))
    elif tool == "draw_break":
        painter.fillRect(QRectF(6, 6, 6, 20), QColor("#526E82"))
        painter.fillRect(QRectF(20, 6, 6, 20), QColor("#526E82"))
    elif tool in ("move", "join"):
        painter.drawLine(QPointF(4, 16), QPointF(28, 16))
        for edge, sign in ((4, 1), (28, -1)):
            tip = edge if tool == "move" else 16
            painter.drawLine(QPointF(tip, 16), QPointF(tip + sign * 5, 11))
            painter.drawLine(QPointF(tip, 16), QPointF(tip + sign * 5, 21))
        if tool == "move":
            painter.drawLine(QPointF(16, 4), QPointF(16, 28))
            for tip, sign in ((4, 1), (28, -1)):
                painter.drawLine(QPointF(16, tip), QPointF(11, tip + sign * 5))
                painter.drawLine(QPointF(16, tip), QPointF(21, tip + sign * 5))
    elif tool == "remove":
        painter.setPen(QPen(QColor("#AD302B"), 2))
        painter.drawLine(QPointF(8, 8), QPointF(24, 24))
        painter.drawLine(QPointF(24, 8), QPointF(8, 24))
    else:
        painter.end()
        raise ValueError("Unsupported timing tool.")
    painter.end()
    return QIcon(image)
