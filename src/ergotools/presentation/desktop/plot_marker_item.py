"""Source-derived PLOT graphics geometry with owned movement and selection intent.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

from ergotools.domain.plot_positions import PlotPoint


@dataclass(frozen=True, slots=True)
class MarkerAppearance:
    """Original shapes/colors; absent comparison probability uses a dashed frame.

    Attributes:
        shape: Original worker circle/triangle/hexagon or job-square identity.
        color: Original continuous damage fill color.
        job_color: Original continuous job-damage frame color; missing comparison risk
            uses the original dashed frame.
        comparison: Whether to add the job-risk comparison frame.
        job_probability: Observed job probability percent, or None for an unavailable
            dashed frame.
        label: Literal marker label, separate from exact owner identity.
    """

    shape: Literal["circle", "triangle", "hexagon", "job"]
    color: str
    job_color: str = "#D9E1E6"
    comparison: bool = False
    job_probability: float | None = None
    label: str = ""


class PlotMarkerItem(QGraphicsObject):
    """Own one item; injected callbacks receive intent without SQL/global lookup."""

    def __init__(
        self,
        point: PlotPoint,
        appearance: MarkerAppearance,
        selected: Callable[["PlotMarkerItem"], None],
        moved: Callable[["PlotMarkerItem"], None],
        *,
        size: float = 50,
        scale: float = 1,
        view_scale: float = 1,
        offset: QPointF | None = None,
        anchored: bool = True,
        locked: bool = False,
        enabled: bool = True,
        context: Callable[["PlotMarkerItem", QPoint], None] | None = None,
    ) -> None:
        """Retain source dimensions and original-image position, not view pixels.

        Args:
            point: Marker anchor in original image pixels, independent of zoom and
                device-pixel ratio.
            appearance: Immutable source shape, risk colors and label used to paint this
                marker.
            selected: Selection callback receiving this marker once per accepted click.
            moved: Live marker whose completed gesture is being recorded once.
            size: Base marker side in original source pixels before symbol/view-scale
                projection.
            scale: Positive saved per-assignment symbol multiplier.
            view_scale: Positive fitted baseline used for initial symbol normalization,
                excluding interactive user zoom.
            offset: Display-only offset from the canonical original-image anchor; None
                means zero.
            anchored: Whether this marker has an explicit/inherited source anchor rather
                than an unplaced preview.
            locked: True prevents position changes while retaining marker selection.
            enabled: Whether the associated controls should accept user interaction.
            context: Optional right-click callback receiving this marker and global
                screen point.

        Returns:
            None.
        """
        super().__init__()
        self.appearance = appearance
        self.size = size
        self.marker_scale = scale
        self.anchored = anchored
        self.locked = locked
        self.selected_callback = selected
        self.context_callback = context
        self.moved_callback = moved
        self.offset = offset or QPointF()
        self.pending = False
        self.internal_scale = 1.0
        self._zoom_start: float | None = None
        self._zoom_scale = scale
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not locked)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setEnabled(enabled)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setZValue(4 if appearance.shape == "job" else 0)
        self.setPos(point.x + self.offset.x(), point.y + self.offset.y())
        self._saved_position = self.pos()
        self._saved_scale = scale
        self._drag_start = self.pos()
        self.set_view_scale(view_scale)

    def set_view_scale(self, scale: float) -> None:
        """Normalize initial size to image fit, without cancelling user magnification.

        Args:
            scale: Positive finite fitted baseline, excluding interactive user zoom.

        Returns:
            None.

        Raises:
            ValueError: PLOT view scale must be positive and finite.
        """
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("PLOT view scale must be positive and finite.")
        self.prepareGeometryChange()
        self.internal_scale = round(1 / scale, 2)
        self.update()

    def marker_rect(self) -> QRectF:
        """Return source dimensions normalized to the fitted image baseline.

        Args:
            None.

        Returns:
            Local symbol rectangle with marker scale and fitted-baseline normalization.
            User zoom scales this rectangle with the image, without renormalizing it.
        """
        side = self.size * self.internal_scale * self.marker_scale
        return QRectF(0, 0, side, side)

    def worker_path(self) -> QPainterPath:
        """Construct the original circle, triangle or 24-percent-inset hexagon.

        Args:
            None.

        Returns:
            Owned original circle/triangle/hexagon painter path inside the marker
            rectangle.
        """
        rect = self.marker_rect()
        if self.appearance.comparison:
            inset = rect.width() * 0.18
            rect = rect.adjusted(inset, inset, -inset, -inset)
        path = QPainterPath()
        if self.appearance.shape == "circle":
            path.addEllipse(rect)
        else:
            points = (
                (
                    QPointF(rect.center().x(), rect.top()),
                    QPointF(rect.right(), rect.bottom()),
                    QPointF(rect.left(), rect.bottom()),
                )
                if self.appearance.shape == "triangle"
                else (
                    QPointF(rect.left() + rect.width() * 0.24, rect.top()),
                    QPointF(rect.right() - rect.width() * 0.24, rect.top()),
                    QPointF(rect.right(), rect.center().y()),
                    QPointF(rect.right() - rect.width() * 0.24, rect.bottom()),
                    QPointF(rect.left() + rect.width() * 0.24, rect.bottom()),
                    QPointF(rect.left(), rect.center().y()),
                )
            )
            path.addPolygon(QPolygonF(points))
            path.closeSubpath()
        return path

    def boundingRect(self) -> QRectF:  # noqa: N802
        """Include the source selection margin so repaint/selection cannot clip.

        Args:
            None.

        Returns:
            Local marker bounds including the selection-frame repaint margin.
        """
        margin = (
            max(5, 5 * self.internal_scale)
            if self.appearance.shape == "job"
            else max(6, 6 * self.internal_scale)
        )
        return self.marker_rect().adjusted(-margin, -margin, margin, margin)

    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionGraphicsItem | None,
        widget: QWidget | None = None,
    ) -> None:
        """Paint original shapes/frame/text and selection without changing state.

        Args:
            painter: Qt painter active for this paint operation; optional overrides
                tolerate None.
            option: Qt style option supplied to the paint/editor delegate; it does not
                identify stored data.
            widget: Qt component to attach or inspect; lifetime remains with its owning
                window.

        Returns:
            None.
        """
        assert painter is not None
        rect = self.marker_rect()
        appearance = self.appearance
        job = appearance.shape == "job"
        if job or appearance.comparison:
            pen = QPen(
                QColor("#111111" if job else "#162C3A"),
                max(1, round(2 * self.internal_scale))
                if job
                else max(1, math.ceil(1.2 * self.internal_scale)),
            )
            if (job and (not self.anchored or appearance.job_probability is None)) or (
                not job and appearance.job_probability is None
            ):
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(
                QBrush(QColor(appearance.color if job else appearance.job_color))
            )
            painter.drawRect(rect)
        if not job and self.isSelected():
            self._paint_selection(painter, rect, job=False)
        if job:
            color = QColor(appearance.color)
            painter.setPen(
                QColor("#071B2D")
                if (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114)
                > 145
                else QColor("white")
            )
            font = QFont("Segoe UI")
            font.setBold(True)
            font.setPixelSize(max(8, round(11 * self.internal_scale)))
            # Fit ordinary IDs inside the unchanged Comparison frame. Full literal
            # identity remains in the tooltip when an unusually long ID needs elision.
            width = max(1.0, rect.width() - 2 * self.internal_scale)
            measured = QFontMetricsF(font).horizontalAdvance(appearance.label)
            if measured > width:
                font.setPixelSize(max(6, int(font.pixelSize() * width / measured)))
            painter.setFont(font)
            label = QFontMetricsF(font).elidedText(
                appearance.label, Qt.TextElideMode.ElideMiddle, width
            )
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)
        else:
            painter.setPen(
                QPen(QColor("#162C3A"), max(1, round(1.5 * self.internal_scale)))
            )
            painter.setBrush(QBrush(QColor(appearance.color)))
            path = self.worker_path()
            if appearance.shape == "circle":
                painter.drawEllipse(path.boundingRect())
            else:
                painter.drawPolygon(path.toFillPolygon())
        if job and self.isSelected():
            self._paint_selection(painter, rect, job=True)

    def _paint_selection(self, painter: QPainter, rect: QRectF, *, job: bool) -> None:
        """Preserve source paint order: worker border below shape, job border above.

        Args:
            painter: Qt painter active for this paint operation; optional overrides
                tolerate None.
            rect: Local drawing rectangle in Qt logical pixels.
            job: True selects job-placement geometry/metrics instead of
                individual-worker geometry/metrics.

        Returns:
            None.
        """
        painter.setPen(
            QPen(
                QColor("#0057D8") if job else QColor("blue"),
                max(2, round(3 * self.internal_scale))
                if job
                else min(4, math.ceil(self.internal_scale) + 2),
            )
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        gap = (
            max(3, 3 * self.internal_scale) if job else max(2, 2 * self.internal_scale)
        )
        painter.drawRect(rect.adjusted(-gap, -gap, gap, gap))

    def anchor_point(self) -> PlotPoint:
        """Return the original-image top-left point, excluding job display offset.

        Args:
            None.

        Returns:
            Canonical original-image anchor coordinates excluding the job's display-only
            offset.
        """
        return PlotPoint(
            self.pos().x() - self.offset.x(), self.pos().y() - self.offset.y()
        )

    def mark_saved(self) -> None:
        """Accept the current position/scale only after a successful external save.

        Args:
            None.

        Returns:
            None.
        """
        self._saved_position = self.pos()
        self._saved_scale = self.marker_scale
        self.pending = False
        self.anchored = True
        self.update()

    def cancel_edit(self) -> None:
        """Restore saved geometry with Qt notified before the bounding rect changes.

        Args:
            None.

        Returns:
            None.
        """
        self.prepareGeometryChange()
        self.marker_scale = self._saved_scale
        self.setPos(self._saved_position)
        self.pending = False
        self.update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:  # noqa: N802
        """Select once; Control-drag scales workers and Qt preserves the grab offset.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        assert event is not None
        self._drag_start = self.pos()
        self.selected_callback(self)
        if event.button() == Qt.MouseButton.RightButton and self.context_callback:
            self.context_callback(self, event.screenPos())
            event.accept()
            return
        if (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and self.appearance.shape != "job"
            and not self.locked
        ):
            self._zoom_start = event.scenePos().y()
            self._zoom_scale = self.marker_scale
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            event.accept()
            return
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:  # noqa: N802
        """Retain original Control-drag scaling; never mutate result dictionaries.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        assert event is not None
        if self._zoom_start is not None:
            factor = 1 - (event.scenePos().y() - self._zoom_start) / 100
            self.prepareGeometryChange()
            self.marker_scale = round(
                1 / max(0.1, min(self._zoom_scale * factor, 10)), 2
            )
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent | None) -> None:  # noqa: N802
        """Publish movement once on release, leaving persistence to the owner.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        assert event is not None
        zooming = self._zoom_start is not None
        self._zoom_start = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        if zooming:
            event.accept()
        else:
            super().mouseReleaseEvent(event)
        if self.pos() != self._drag_start or (
            zooming and self.marker_scale != self._zoom_scale
        ):
            self.pending = True
            self.moved_callback(self)
