"""Paint optional annotations around the existing assessment probability arc.

Presentation layer. Probability-to-angle mapping matches the original semicircle;
the host supplies its actual risk-band boundaries, center, radius and pen width.
Painting touches no source, result, animation or persistence state. Invoke only on
the GUI thread while the caller's QPainter is active.
"""

import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFontMetricsF, QPainter, QPen

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.domain.language import Language


def marker_values(
    settings: GaugeMarkerSettings, boundaries: tuple[float, ...]
) -> tuple[tuple[float, bool], ...]:
    """Combine regular ticks with exact boundary ticks without duplicates.

    Args:
        settings: Validated visibility and integer percentage-point spacing.
        boundaries: Existing ordered risk limits on the gauge's 0-100 percent scale.

    Returns:
        Sorted (percentage, is_boundary) pairs, or an empty tuple when ticks are hidden.
        Boundary labels are handled independently by the painter.
    """
    if not settings.show_ticks:
        return ()
    values = set(range(0, 101, settings.interval)) | set(boundaries)
    return tuple((float(value), value in boundaries) for value in sorted(values))


def paint_gauge_markers(
    painter: QPainter,
    center: QPointF,
    radius: float,
    arc_width: float,
    width: int,
    boundaries: tuple[float, ...],
    settings: GaugeMarkerSettings,
    language: Language,
) -> None:
    """Draw outward ticks and range limits inside the unchanged gauge dimensions.

    Args:
        painter: Active borrowed painter; its pen/font/brush state is restored.
        center: Original semicircle center in logical widget pixels.
        radius: Original arc centerline radius in logical pixels.
        arc_width: Existing colored-arc pen width in logical pixels.
        width: Widget width used to keep endpoint labels within horizontal bounds.
        boundaries: Existing risk limits in percent, including zero and one hundred.
        settings: Personal visibility and tick-spacing options; values are not modified.
        language: Label decimal convention: Spanish comma or English point.

    Returns:
        None. Place labels five pixels farther outward than the initial marker layout;
        retain a top inset and place endpoints below the arc to avoid tick overlap.
    """
    painter.save()
    outer = radius + arc_width / 2 + 1.5
    painter.setPen(QPen(QColor("#6F7E88"), 1.0))
    for value, boundary in marker_values(settings, boundaries):
        angle = math.radians(180 - value * 1.8)
        length = 5.0 if boundary else 3.0
        painter.drawLine(
            QPointF(
                center.x() + math.cos(angle) * outer,
                center.y() - math.sin(angle) * outer,
            ),
            QPointF(
                center.x() + math.cos(angle) * (outer + length),
                center.y() - math.sin(angle) * (outer + length),
            ),
        )
    if settings.show_labels:
        font = painter.font()
        font.setPointSizeF(7.0)
        font.setBold(False)
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        for value in boundaries:
            text = f"{value:g}"
            if language is Language.SPANISH:
                text = text.replace(".", ",")
            angle = math.radians(180 - value * 1.8)
            distance = outer + 15
            label_width = metrics.horizontalAdvance(text) + 4
            x = center.x() + math.cos(angle) * distance - label_width / 2
            x = max(1.0, min(x, width - label_width - 1))
            y = center.y() - math.sin(angle) * distance - metrics.height() / 2
            y = max(1.0, y)
            if value in (0, 100):
                y = center.y() + 6
            painter.drawText(
                QRectF(x, y, label_width, metrics.height() + 2),
                Qt.AlignmentFlag.AlignCenter,
                text,
            )
    painter.restore()
