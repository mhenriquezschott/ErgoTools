"""Small native vector icons matching ErgoTools navy/teal action controls.

Presentation-only drawing. Called after QApplication exists; no raster generation,
external assets, project state or import-time I/O. Shared task/import/drawer controls
use the same geometry, padding and device-independent proportions.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF


def assessment_action_icon(action: str, light: bool = False) -> QIcon:
    """Draw a supported task/clipboard/pin glyph at a shared high-resolution size.

    Args:
        action: add_task, remove_task, copy, paste, import, pin or unpin.
        light: White strokes for a dark drawer; ordinary controls use navy/teal.

    Returns:
        Transparent high-resolution icon with the same visible padded bounds.

    Raises:
        ValueError: An unsupported semantic action is requested.
    """
    if action not in {
        "add_task",
        "remove_task",
        "copy",
        "paste",
        "import",
        "pin",
        "unpin",
    }:
        raise ValueError("Unsupported assessment action icon.")
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(2, 2)
    pen = QPen(QColor("white" if light else "#0B326C"), 1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    if action in ("pin", "unpin"):
        if action == "unpin":
            painter.translate(16, 16)
            painter.rotate(35)
            painter.translate(-16, -16)
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(10, 5),
                    QPointF(22, 5),
                    QPointF(20, 9),
                    QPointF(20, 15),
                    QPointF(24, 19),
                    QPointF(8, 19),
                    QPointF(12, 15),
                    QPointF(12, 9),
                ]
            )
        )
        painter.drawLine(QPointF(16, 19), QPointF(16, 28))
    else:
        if action == "copy":
            painter.drawRoundedRect(QRectF(7, 4, 17, 21), 2, 2)
        painter.drawRoundedRect(QRectF(4, 8, 18, 20), 2, 2)
        for y in (13, 17, 21):
            painter.drawLine(QPointF(8, y), QPointF(16, y))
        if action in ("paste", "import"):
            painter.drawRoundedRect(QRectF(9, 5, 8, 5), 1, 1)
        painter.setPen(QPen(QColor("white" if light else "#087E91"), 2))
        if action in ("add_task", "remove_task"):
            painter.drawLine(QPointF(21, 23), QPointF(30, 23))
            if action == "add_task":
                painter.drawLine(QPointF(25.5, 18.5), QPointF(25.5, 27.5))
        elif action == "import":
            painter.drawLine(QPointF(30, 16), QPointF(22, 16))
            painter.drawLine(QPointF(22, 16), QPointF(26, 12))
            painter.drawLine(QPointF(22, 16), QPointF(26, 20))
    painter.end()
    return QIcon(pixmap)


def drawer_step_icon(icon: QIcon) -> QIcon:
    """Tint an existing transparent application icon for the dark navigation drawer.

    Args:
        icon: Processed packaged icon with preserved transparent margins.

    Returns:
        White glyph retaining the original alpha, shape and padding.
    """
    pixmap = icon.pixmap(64, 64)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor("white"))
    painter.end()
    return QIcon(pixmap)
