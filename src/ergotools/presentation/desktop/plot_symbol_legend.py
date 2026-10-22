"""Original neutral PLOT map-symbol key with owned, localized painting.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent, QPen, QPolygonF
from PyQt5.QtWidgets import QWidget

from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView


class PlotSymbolLegend(QWidget):
    """Preserve original neutral marker shapes separately from result colors."""

    def __init__(
        self, *, language: Language = Language.ENGLISH, parent: QWidget | None = None
    ) -> None:
        """Retain source 68-pixel legend region and mode-specific entries.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.language = language
        self.mode = PlotRiskView.INDIVIDUAL
        self.setFixedHeight(68)
        self.setMinimumWidth(300)
        self.setToolTip(
            self.text(
                "Marker shape identifies the mapped subject. Marker color "
                "identifies its risk range.",
                "La forma identifica al sujeto; el color indica su nivel de riesgo.",
            )
        )

    def text(self, english: str, spanish: str) -> str:
        """Translate legend labels without modifying risk or shape mapping.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def set_mode(self, mode: PlotRiskView) -> None:
        """Repaint the source job/worker/comparison legend without signals.

        Args:
            mode: Typed individual/job/comparison risk view; no risk is computed by
                selecting it.

        Returns:
            None.
        """
        self.mode = mode
        self.update()

    @staticmethod
    def draw_shape(
        painter: QPainter, shape: str, rect: QRectF, *, nested: bool = False
    ) -> None:
        """Draw source neutral geometry, including the nested comparison square.

        Args:
            painter: Qt painter active for this paint operation; optional overrides
                tolerate None.
            shape: Original marker geometry identity, such as circle, triangle or
                hexagon.
            rect: Local drawing rectangle in Qt logical pixels.
            nested: True adds the original outer comparison square around the individual
                symbol.

        Returns:
            None.
        """
        painter.setPen(QPen(QColor("#162C3A"), 1.5))
        painter.setBrush(QBrush(QColor("#EEF3F6")))
        if shape == "circle":
            painter.drawEllipse(rect)
        elif shape == "triangle":
            painter.drawPolygon(
                QPolygonF(
                    (
                        QPointF(rect.center().x(), rect.top()),
                        QPointF(rect.right(), rect.bottom()),
                        QPointF(rect.left(), rect.bottom()),
                    )
                )
            )
        elif shape == "hexagon":
            inset = rect.width() * 0.24
            painter.drawPolygon(
                QPolygonF(
                    (
                        QPointF(rect.left() + inset, rect.top()),
                        QPointF(rect.right() - inset, rect.top()),
                        QPointF(rect.right(), rect.center().y()),
                        QPointF(rect.right() - inset, rect.bottom()),
                        QPointF(rect.left() + inset, rect.bottom()),
                        QPointF(rect.left(), rect.center().y()),
                    )
                )
            )
        else:
            painter.drawRect(rect)
        if nested:
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(rect.adjusted(4, 4, -4, -4))

    def draw_entry(
        self,
        painter: QPainter,
        x: float,
        y: float,
        shape: str,
        label: str,
        *,
        nested: bool = False,
    ) -> float:
        """Place the source icon/text pair and return the next text-aware position.

        Args:
            painter: Qt painter active for this paint operation; optional overrides
                tolerate None.
            x: Horizontal placement in Qt logical drawing pixels.
            y: Vertical placement in Qt logical drawing pixels.
            shape: Original marker geometry identity, such as circle, triangle or
                hexagon.
            label: Visible label/legend caption; None omits an optional chart series
                label.
            nested: True adds the original outer comparison square around the individual
                symbol.

        Returns:
            Next horizontal position in Qt logical pixels after the marker, text and
            reference gap.
        """
        self.draw_shape(painter, shape, QRectF(x, y - 7, 14, 14), nested=nested)
        painter.drawText(QPointF(x + 20, y + 4), label)
        return x + 20 + painter.fontMetrics().horizontalAdvance(label) + 16

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Paint original legend entries within their fixed-format region.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(painter.font())
        font.setBold(True)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor("#0B326C"))
        painter.drawText(
            QRectF(0, 0, self.width(), 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.text("Map symbols", "Símbolos del mapa"),
        )
        font.setBold(False)
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(QColor("#304652"))
        if self.mode is PlotRiskView.JOB:
            self.draw_entry(
                painter,
                2,
                33,
                "square",
                self.text(
                    "Job placement (fill = Job risk)",
                    "Trabajo ubicado (color = riesgo)",
                ),
            )
            painter.setPen(QColor("#526777"))
            painter.drawText(
                QPointF(22, 58),
                self.text(
                    "One square per placement, not per worker",
                    "Un cuadrado por ubicación, no por trabajador",
                ),
            )
            return
        x = self.draw_entry(painter, 2, 33, "triangle", self.text("Male", "Hombre"))
        x = self.draw_entry(painter, x, 33, "circle", self.text("Female", "Mujer"))
        self.draw_entry(
            painter, x, 33, "hexagon", self.text("Sex not provided", "Sexo no indicado")
        )
        if self.mode is PlotRiskView.COMPARISON:
            self.draw_entry(
                painter,
                2,
                57,
                "square",
                self.text(
                    "Job outside / Individual inside",
                    "Trabajo fuera / Individuo dentro",
                ),
                nested=True,
            )
