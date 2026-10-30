"""Width-adaptive project caption that cannot displace main toolbar actions.

Presentation layer. Keep the exact QLabel text/accessibility and full tooltip, but paint
one or two fitted lines in the available brand area. Prefer the existing font, then a
small readable reduction, and only elide exceptionally long captions. No project data,
file names, branding geometry, history or persistence is changed by this component.
"""

from dataclasses import dataclass

from PyQt5.QtCore import QPointF, QSize, Qt
from PyQt5.QtGui import (
    QFont,
    QFontMetrics,
    QPainter,
    QPaintEvent,
    QTextLayout,
    QTextOption,
)
from PyQt5.QtWidgets import QLabel, QSizePolicy


@dataclass(frozen=True, slots=True)
class ProjectCaptionPresentation:
    """Read-only description of the fitted caption, separate from its full source.

    Attributes:
        text: Display-only text; QLabel.text retains the exact full caption.
        font_pixels: Chosen readable font size, without changing the ErgoTools heading.
        lines: Number of visible lines, at most two.
        elided: True only for the extreme-length middle-ellipsis fallback.
    """

    text: str
    font_pixels: int
    lines: int
    elided: bool


class ProjectCaption(QLabel):
    """Fit the project/state caption inside a content-independent layout allocation."""

    def __init__(self) -> None:
        """Create a plain-text caption that yields width to the complete toolbar.

        Args:
            None.

        Returns:
            None; no project state or rendering outside this label is changed.
        """
        super().__init__()
        self.setObjectName("projectName")
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def sizeHint(self) -> QSize:  # noqa: N802 — Qt override
        """Offer a neutral width and the original one-line vertical layout hint.

        Args:
            None.

        Returns:
            Content-independent width; caption length cannot widen the brand column.
        """
        return QSize(200, self.fontMetrics().height())

    def minimumSizeHint(self) -> QSize:  # noqa: N802 — Qt override
        """Allow horizontal fitting while retaining a readable line-height minimum.

        Args:
            None.

        Returns:
            Zero minimum width, so long metadata cannot squeeze toolbar actions.
        """
        return QSize(0, self.fontMetrics().height())

    def setText(self, text: str | None) -> None:  # noqa: N802 — Qt override
        """Retain exact metadata/status text and expose it unabridged on hover.

        Args:
            text: Localized caption with Loaded/Modified status; None clears the label.

        Returns:
            None; fitting affects paint only and never the stored label value.
        """
        super().setText(text)
        self.setToolTip(text or "")

    def presentation(self) -> ProjectCaptionPresentation:
        """Describe the current fitted display without accepting or shortening source.

        Args:
            None.

        Returns:
            Current paint-time caption, font and line count for the allocated size.
        """
        return self._fit()[0]

    def _layout(self, text: str, font: QFont) -> QTextLayout | None:
        """Prepare at most two lines that actually fit both allocated dimensions.

        Args:
            text: Full or display-elided plain text.
            font: Explicit candidate font, preserving the original weight/family.

        Returns:
            Completed layout, or None when two lines/available height are insufficient.
        """
        layout = QTextLayout(text, font)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        layout.beginLayout()
        height = 0.0
        fits = True
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(max(1, self.width()))
            line.setPosition(QPointF(0, height))
            height += line.height()
            if layout.lineCount() > 2 or height > self.height():
                fits = False
                break
        layout.endLayout()
        return layout if fits else None

    def _fit(self) -> tuple[ProjectCaptionPresentation, QTextLayout]:
        """Prefer full-size lines, then readable smaller text, then middle elision.

        Args:
            None.

        Returns:
            Display description and prepared Qt layout; full QLabel text is unchanged.
        """
        full = self.text()
        font = QFont(self.font())
        base = font.pixelSize()
        if base <= 0:
            base = max(12, round(font.pointSizeF() * self.logicalDpiY() / 72))
        for pixels in dict.fromkeys((base, max(12, base - 2), max(12, base - 4))):
            font.setPixelSize(pixels)
            layout = self._layout(full, font)
            if layout is not None:
                # Keep state words together instead of orphaning Modified on line two.
                if layout.lineCount() == 2 and "  •  " in full:
                    title, status = full.split("  •  ", 1)
                    formatted = title + "\u2028" + status
                    separated = self._layout(formatted, font)
                    if separated is not None:
                        return ProjectCaptionPresentation(
                            formatted, pixels, separated.lineCount(), False
                        ), separated
                return ProjectCaptionPresentation(
                    full, pixels, layout.lineCount(), False
                ), layout
        # Fit the native Unicode-aware middle ellipsis to the same two-line bounds.
        metrics = QFontMetrics(font)
        low, high = 0, max(1, self.width() * 2)
        text = ""
        layout = QTextLayout(text, font)
        while low <= high:
            budget = (low + high) // 2
            candidate = metrics.elidedText(full, Qt.TextElideMode.ElideMiddle, budget)
            proposed = self._layout(candidate, font)
            if proposed is not None:
                text, layout = candidate, proposed
                low = budget + 1
            else:
                high = budget - 1
        return ProjectCaptionPresentation(
            text, font.pixelSize(), layout.lineCount(), True
        ), layout

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802 — Qt override
        """Paint only the fitted plain text, leaving the brand and toolbar untouched.

        Args:
            event: Native repaint; None is ignored for defensive direct calls.

        Returns:
            None; label text/tooltip remain complete, including elided project names.
        """
        if event is None or self.width() <= 0 or self.height() <= 0:
            return
        _, layout = self._fit()
        painter = QPainter(self)
        painter.setPen(self.palette().color(self.foregroundRole()))
        layout.draw(
            painter,
            QPointF(0, max(0.0, (self.height() - layout.boundingRect().height()) / 2)),
        )
