"""Original compact PLOT worker marker preview, independent of the map scene.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPaintEvent, QPen, QPolygonF
from PyQt5.QtWidgets import QWidget

from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_marker_item import MarkerAppearance


class PlotWorkerPreview(QWidget):
    """Paint source 72-pixel preview geometry without borrowing live graphics items."""

    def __init__(self, language: Language = Language.ENGLISH) -> None:
        """Retain source dimensions, selection and tooltips.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        super().__init__()
        self.language = language
        self.appearance: MarkerAppearance | None = None
        self.setFixedSize(72, 72)
        self.setToolTip(
            "La forma identifica el sexo; el color identifica el riesgo."
            if language is Language.SPANISH
            else "Marker shape identifies sex; color identifies the selected "
            "assessment risk."
        )

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Draw the original individual/comparison glyph and selected blue frame.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        appearance = self.appearance
        if appearance is None:
            painter.setPen(QColor("#758590"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Ningún\ntrabajador"
                if self.language is Language.SPANISH
                else "No worker\nselected",
            )
            return
        center = QPointF(self.width() / 2, self.height() / 2 + 1)
        extent = float(min(self.width(), self.height()))
        selection = extent - 10
        painter.setPen(QPen(QColor("blue"), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(
            QRectF(
                center.x() - selection / 2,
                center.y() - selection / 2,
                selection,
                selection,
            )
        )
        if appearance.comparison:
            side = extent - 20
            painter.setPen(QPen(QColor("#162C3A"), 2))
            painter.setBrush(QColor(appearance.job_color))
            painter.drawRect(
                QRectF(center.x() - side / 2, center.y() - side / 2, side, side)
            )
            size = side * 0.28
        else:
            size = (extent - 30) / 2
        painter.setPen(QPen(QColor("#162C3A"), 2))
        painter.setBrush(QColor(appearance.color))
        if appearance.shape == "circle":
            painter.drawEllipse(center, size, size)
        else:
            rect = QRectF(center.x() - size, center.y() - size, size * 2, size * 2)
            points = (
                (
                    QPointF(center.x(), center.y() - size),
                    QPointF(center.x() - size, center.y() + size * 0.8),
                    QPointF(center.x() + size, center.y() + size * 0.8),
                )
                if appearance.shape == "triangle"
                else (
                    QPointF(rect.left() + rect.width() * 0.24, rect.top()),
                    QPointF(rect.right() - rect.width() * 0.24, rect.top()),
                    QPointF(rect.right(), rect.center().y()),
                    QPointF(rect.right() - rect.width() * 0.24, rect.bottom()),
                    QPointF(rect.left() + rect.width() * 0.24, rect.bottom()),
                    QPointF(rect.left(), rect.center().y()),
                )
            )
            painter.drawPolygon(QPolygonF(points))
