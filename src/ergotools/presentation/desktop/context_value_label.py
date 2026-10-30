"""Compact full-value workplace captions for the main assessment-context path.

Presentation layer. Preserve exact label text and full tooltip while painting a
single-line middle elision only when a hierarchy value exceeds its allocation.
This keeps long organization names from displacing the context-selection actions.
"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPainter, QPaintEvent
from PyQt5.QtWidgets import QLabel, QSizePolicy


class ContextValueLabel(QLabel):
    """Keep literal context values accessible in a width-adaptive icon/path cell."""

    def __init__(self) -> None:
        """Create a plain-text label with no content-dependent minimum width.

        Args:
            None.

        Returns:
            None; the host supplies both the full label and its descriptive tooltip.
        """
        super().__init__()
        self.setObjectName("contextSummary")
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumWidth(50)

    def sizeHint(self) -> QSize:  # noqa: N802 — Qt override
        """Offer the natural caption width, bounded for unusually long names.

        Args:
            None.

        Returns:
            Preferred cell size; actual width is shared with the other context cells.
        """
        return QSize(
            min(240, max(50, self.fontMetrics().horizontalAdvance(self.text()) + 2)),
            self.fontMetrics().height(),
        )

    def minimumSizeHint(self) -> QSize:  # noqa: N802 — Qt override
        """Keep text from imposing a window-wide hierarchy-name minimum.

        Args:
            None.

        Returns:
            Small readable cell minimum with a normal caption line height.
        """
        return QSize(50, self.fontMetrics().height())

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802 — Qt override
        """Draw a fitted literal caption without shortening the stored text.

        Args:
            event: Native paint notification; None is ignored defensively.

        Returns:
            None; full text/tooltip and assessment ownership remain unchanged.
        """
        if event is None:
            return
        painter = QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.setFont(self.font())
        painter.drawText(
            self.contentsRect(),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.fontMetrics().elidedText(
                self.text(), Qt.TextElideMode.ElideMiddle, self.contentsRect().width()
            ),
        )
