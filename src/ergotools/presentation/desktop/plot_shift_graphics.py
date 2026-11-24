"""Read-only PLOT Shift View glyphs and a compact seekable shift timeline.

Presentation layer. Image-pixel graphics have no movement flags, mutation callbacks
or saved coordinates. Timeline seeking changes only the player's local clock.
"""

from dataclasses import replace
from itertools import pairwise

from PyQt5.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from ergotools.application.shift_playback import ShiftPlayback
from ergotools.domain.plot_positions import PlotPoint
from ergotools.presentation.desktop.plot_marker_item import (
    MarkerAppearance,
    PlotMarkerItem,
)


def shift_color(value: float) -> QColor:
    """Interpolate the shared green/yellow/orange/red visual palette.

    Args:
        value: Schedule index or Job probability in percent.

    Returns:
        Continuous display color; never a changed risk threshold or saved result.
    """
    stops = (
        (0.0, "#16b83e"),
        (25.0, "#16b83e"),
        (37.5, "#f3c800"),
        (50.0, "#ff8c16"),
        (75.0, "#ff3934"),
        (100.0, "#c82035"),
    )
    for (a, ca), (b, cb) in pairwise(stops):
        if value <= b:
            fraction = max(0.0, (value - a) / (b - a))
            left, right = QColor(ca), QColor(cb)
            red = round(left.red() + (right.red() - left.red()) * fraction)
            green = round(left.green() + (right.green() - left.green()) * fraction)
            blue = round(left.blue() + (right.blue() - left.blue()) * fraction)
            return QColor(red, green, blue)
    return QColor(stops[-1][1])


def contrast_ink(color: QColor) -> QColor:
    """Choose readable text against a risk-colored fill.

    Args:
        color: Actual display fill, not an uncolored risk label.

    Returns:
        White on dark fills, otherwise the software's dark navy.
    """
    luminance = sum(
        weight * (channel / 255) ** 2.2
        for weight, channel in (
            (0.2126, color.red()),
            (0.7152, color.green()),
            (0.0722, color.blue()),
        )
    )
    return QColor("white" if luminance < 0.18 else "#092d47")


class ShiftGlyph(PlotMarkerItem):
    """Reuse ordinary map anchors, shapes, IDs and selection without movement.

    Attributes:
        label: Literal worker/Job ID.
        job: True selects a fixed square; False a worker.
        picked: Selection intent carrying the worker ID, never an edit.
    """

    picked = pyqtSignal(str)

    def __init__(
        self,
        label: str,
        job: bool,
        sex: str | None = None,
        *,
        size: float = 30,
        scale: float = 1,
        view_scale: float = 1,
    ) -> None:
        """Build a selectable worker using the ordinary top-left anchor contract.

        Args:
            label: Literal worker/Job ID.
            job: True paints an inert fixed destination.
            sex: Existing Male/Female/unspecified shape analogy.
            size: Same source symbol size as the baseline assignment marker.
            scale: Same saved per-assignment symbol multiplier.
            view_scale: Canvas fit scale, excluding interactive zoom.

        Returns:
            None; no mutation/context-menu callback is installed.
        """
        super().__init__(
            PlotPoint(0, 0),
            MarkerAppearance(
                "job"
                if job
                else "circle"
                if sex == "Female"
                else "triangle"
                if sex == "Male"
                else "hexagon",
                "#DDE8EF",
                job_probability=0,
                label="" if job else label,
            ),
            self.selected_intent,
            self.ignore_move,
            size=size,
            scale=scale,
            view_scale=view_scale,
            locked=True,
        )
        self.label, self.job = label, job
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, not job)
        self.setAcceptedMouseButtons(
            Qt.MouseButtons(
                Qt.MouseButton.NoButton if job else Qt.MouseButton.LeftButton
            )
        )
        self.setCursor(
            Qt.CursorShape.ArrowCursor if job else Qt.CursorShape.PointingHandCursor
        )
        self.setZValue(3 if job else 5)

    def marker_rect(self) -> QRectF:
        """Frame a worker with a slightly larger fixed Job square at the same center.

        Args:
            None.

        Returns:
            Ordinary worker bounds or a fifteen-percent-outset Job frame.
        """
        rect = super().marker_rect()
        if getattr(self, "job", False):
            margin = rect.width() * 0.15
            return rect.adjusted(-margin, -margin, margin, margin)
        return rect

    @property
    def color(self) -> QColor:
        """Read the transient fill without touching saved assessment values.

        Args:
            None.

        Returns:
            Actual rendered fill color.
        """
        return QColor(self.appearance.color)

    @color.setter
    def color(self, color: QColor) -> None:
        """Replace only transient appearance.

        Args:
            color: Current Job risk or accumulated worker-index color.

        Returns:
            None.
        """
        self.appearance = replace(self.appearance, color=color.name())

    def selected_intent(self, item: PlotMarkerItem) -> None:
        """Publish worker selection while retaining read-only geometry.

        Args:
            item: This clicked map symbol.

        Returns:
            None; fixed Job destinations are never selectable.
        """
        if not self.job:
            self.picked.emit(self.label)

    def ignore_move(self, item: PlotMarkerItem) -> None:
        """Satisfy the shared glyph callback contract without accepting edits.

        Args:
            item: Inert glyph; movement is disabled at the Qt flag boundary.

        Returns:
            None.
        """

    def boundingRect(self) -> QRectF:  # noqa: N802
        """Include the Job caption below the ordinary symbol rectangle.

        Args:
            None.

        Returns:
            Local bounds; scene/image extents are never changed by captions.
        """
        rect = super().boundingRect()
        return rect.adjusted(0, 0, 0, 18 * self.internal_scale) if self.job else rect

    def paint(
        self, painter: QPainter | None, option: object, widget: QWidget | None = None
    ) -> None:
        """Paint ordinary shape geometry plus a separate fixed-Job caption.

        Args:
            painter: Active borrowed scene painter.
            option: Qt style option, unused by the shared renderer.
            widget: Optional viewport.

        Returns:
            None.
        """
        if painter is None:
            return
        super().paint(painter, None, widget)
        if self.job:
            rect = self.marker_rect()
            font = QFont("Sans")
            font.setPixelSize(max(8, round(10 * self.internal_scale)))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#0b3d60"))
            painter.drawText(
                QRectF(
                    rect.left() - 10 * self.internal_scale,
                    rect.bottom() + 2 * self.internal_scale,
                    rect.width() + 20 * self.internal_scale,
                    16 * self.internal_scale,
                ),
                Qt.AlignmentFlag.AlignCenter,
                self.label,
            )


class ShiftTimeline(QWidget):
    """Paint proportional work/break intervals and the current real shift clock."""

    seek = pyqtSignal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create a compact touch/mouse seek surface.

        Args:
            parent: Owning player.

        Returns:
            None.
        """
        super().__init__(parent)
        self.data: ShiftPlayback | None = None
        self.elapsed = 0.0
        self.setFixedHeight(74)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click the timeline to seek • Haga clic para buscar un momento")

    def paintEvent(self, event: object) -> None:  # noqa: N802 — Qt override
        """Draw the clock, intervals and a high-contrast progress needle.

        Args:
            event: Qt repaint request, unused.

        Returns:
            None.
        """
        if self.data is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        timing = self.data.timing
        width = self.width() - 20
        painter.setFont(QFont("Sans", 9, QFont.Weight.Bold))
        for block in timing.blocks():
            for piece in block.pieces:
                rect = QRectF(
                    10 + width * piece.start / timing.shift_minutes,
                    4,
                    width * (piece.end - piece.start) / timing.shift_minutes - 2,
                    43,
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#0b4266"))
                painter.drawRoundedRect(rect, 4, 4)
                painter.setPen(QColor("white"))
                begin = (self.data.start + piece.start) % 1440
                end = (self.data.start + piece.end) % 1440
                label = f"Block {block.index + 1}"
                if rect.width() >= 115:
                    label += (
                        f"\n{begin // 60:02}:{begin % 60:02} - "
                        f"{end // 60:02}:{end % 60:02}"
                    )
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)
        for pause in timing.breaks:
            rect = QRectF(
                10 + width * pause.interval.start / timing.shift_minutes,
                4,
                max(
                    4.0,
                    width
                    * (pause.interval.end - pause.interval.start)
                    / timing.shift_minutes
                    - 2,
                ),
                43,
            )
            painter.fillRect(rect, QColor("#f5d589"))
            painter.setPen(QColor("#684800"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Ⅱ")
        x = 10 + width * self.elapsed / timing.shift_minutes
        painter.setPen(QPen(QColor("#00bac9"), 3))
        painter.drawLine(QPointF(x, 0), QPointF(x, 49))
        painter.setPen(QColor("#0b3d60"))
        for minute, alignment in (
            (0, Qt.AlignmentFlag.AlignLeft),
            (timing.shift_minutes, Qt.AlignmentFlag.AlignRight),
        ):
            clock = (self.data.start + minute) % 1440
            painter.drawText(
                QRectF(10, 51, width, 20),
                alignment,
                f"{clock // 60:02}:{clock % 60:02}",
            )
        if timing.shift_minutes * 0.04 < self.elapsed < timing.shift_minutes * 0.96:
            clock = int(self.data.start + self.elapsed) % 1440
            painter.drawText(
                QRectF(max(60.0, min(self.width() - 130.0, x - 50)), 51, 100, 20),
                Qt.AlignmentFlag.AlignCenter,
                f"{clock // 60:02}:{clock % 60:02}",
            )
        painter.end()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Publish a clamped clock seek without changing project geometry.

        Args:
            event: Left-button timeline click.

        Returns:
            None.
        """
        if (
            event is not None
            and self.data is not None
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self.seek.emit(
                max(0.0, min(1.0, (event.x() - 10) / max(1, self.width() - 20)))
                * self.data.timing.shift_minutes
            )
