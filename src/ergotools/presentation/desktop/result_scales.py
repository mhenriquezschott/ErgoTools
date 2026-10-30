"""Original Qt gauge/scale geometry, isolated from source and persistence.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

import math
from collections.abc import Callable, Mapping
from dataclasses import replace

from PyQt5.QtCore import QEasingCurve, QPointF, QRectF, Qt, QVariantAnimation
from PyQt5.QtGui import (
    QColor,
    QContextMenuEvent,
    QIcon,
    QPainter,
    QPaintEvent,
    QPen,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QActionGroup,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QMenu,
    QSizePolicy,
    QWidget,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.domain.language import Language
from ergotools.presentation.desktop.gauge_markers import paint_gauge_markers
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES

# Original gauge band bounds in percent plus shared category labels/colors; tuple order
# is low through high.
_BANDS = tuple(
    (start, end, appearance.english_label, appearance.color_hex, appearance.range_label)
    for (start, end), appearance in zip(
        ((0, 25), (25, 37.5), (37.5, 50), (50, 100)),
        RISK_APPEARANCES.values(),
        strict=True,
    )
)


class _AnimatedScale(QWidget):
    """Animate a displayed quantity without timers that poll source or other widgets."""

    def __init__(self, limit: float, duration: int) -> None:
        """Create one widget-owned animated display scale.

        Connect one valueChanged repaint callback without polling other widgets or
        source values.

        Args:
            limit: Upper drawing scale in the caller's quantity: percent for risk or
                dimensionless damage.
            duration: Qt animation duration in milliseconds.

        Returns:
            None; construct one widget-owned animation and initialize unavailable
            display state.
        """
        super().__init__()
        self.animation_enabled = True
        self.limit = limit
        self.display_value = 0.0
        self.target_value = 0.0
        self.has_value = False
        self.fill_color = QColor("#D9E1E6")
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self._advance)

    def set_animation_enabled(self, enabled: bool) -> None:
        """Apply a personal display preference and settle a disabled running scale.

        Args:
            enabled: True animates future changed targets; False displays targets now.

        Returns:
            None; source/calculated quantities and the current target are unchanged.
        """
        self.animation_enabled = enabled
        if not enabled:
            self.animation.stop()
            self.display_value = self.target_value
            self.update()

    def _advance(self, value: object) -> None:
        """GUI-thread signal callback only; never calculate or save source data.

        Args:
            value: Qt QVariantAnimation value; numeric int/float values update the
                displayed quantity, others are ignored.

        Returns:
            None after optionally updating display state and requesting a deferred
            repaint.
        """
        if isinstance(value, (float, int)):
            self.display_value = float(value)
            self.update()

    def clear(self) -> None:
        """Stop animation and immediately clear an unavailable/stale assessment.

        Args:
            None.

        Returns:
            None; stop animation, reset target/display to zero, mark unavailable and
            request repaint.
        """
        self.animation.stop()
        self.has_value = False
        self.target_value = self.display_value = 0.0
        self.fill_color = QColor("#D9E1E6")
        self.update()

    def set_value(self, value: float, color: str) -> None:
        """Set finite value and color; identical targets never restart animation.

        An unchanged target can still repaint a changed color without restarting
        animation. Stored result precision is untouched.

        Args:
            value: Finite result quantity in this scale's units; clamp only this drawing
                target to 0..limit.
            color: Valid Qt color string for the displayed band/fill.

        Returns:
            None after updating appearance and starting animation only when the target
            differs by at least 0.0001.

        Raises:
            ValueError: Quantity is nonfinite or color is invalid.
        """
        if not math.isfinite(value):
            raise ValueError("Scale value must be finite.")
        value = min(self.limit, max(0.0, value))
        candidate = QColor(color)
        if not candidate.isValid():
            raise ValueError("Scale color must be valid.")
        self.fill_color = candidate
        self.has_value = True
        if abs(value - self.target_value) < 0.0001:
            self.update()  # Same number with a new color still needs repainting.
            return
        self.target_value = value
        self.animation.stop()
        if not self.animation_enabled:
            self.display_value = value
            self.update()
            return
        self.animation.setStartValue(self.display_value)
        self.animation.setEndValue(value)
        self.animation.start()


class RiskGauge(_AnimatedScale):
    """Original risk display with personal, presentation-only marker options.

    marker_settings is immutable; the optional host callback owns persistence and
    applies accepted settings through set_marker_settings. marker_language follows
    the host UI. No menu action changes the result, needle or running animation.
    """

    def __init__(
        self,
        marker_settings: GaugeMarkerSettings | None = None,
        change_markers: Callable[[GaugeMarkerSettings], None] | None = None,
        *,
        compact: bool = False,
        dialog_icons: Mapping[str, QIcon] | None = None,
    ) -> None:
        """Retain reference geometry and add configurable external arc annotations.

        Args:
            marker_settings: Initial visibility/spacing, or None for defaults.
            compact: Use PLOT's compact profile, animation timing and unavailable state
                within the same control; False uses the main result-card profile.
                Compact height reserves label space without reducing its full radius.
            dialog_icons: Optional packaged settings/cancel icons for the shared prompt.
            change_markers: Optional host callback that persists accepted preferences
                before calling set_marker_settings. None applies local options only.

        Returns:
            None; own one profile-specific animated percent gauge and shared controls.
        """
        super().__init__(100.0 if compact else 100, 700 if compact else 750)
        self._compact = compact
        self._dialog_icons = dialog_icons
        self.marker_settings = marker_settings or GaugeMarkerSettings()
        self.marker_language = Language.ENGLISH
        self._change_markers = change_markers
        self.decimal_places = 1
        self.outcome_text = "Probability of high-risk\njob"
        if compact:
            self.setMinimumSize(250, 144)
            self.setMaximumWidth(310)
        else:
            self.setMinimumWidth(190)
            self.setFixedHeight(167)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_marker_settings(self, settings: GaugeMarkerSettings) -> None:
        """Apply appearance without changing the value or restarting its animation.

        Args:
            settings: Validated immutable personal gauge options.

        Returns:
            None; retain the options and request a deferred repaint.
        """
        self.marker_settings = settings
        self.update()

    def _request_markers(self, settings: GaugeMarkerSettings) -> None:
        """Route an explicit menu change through the injected persistence owner.

        Args:
            settings: Newly selected validated appearance options.

        Returns:
            None. Without a host, apply locally. With a host, only it applies changes;
            failed persistence can therefore leave the previous appearance intact.
        """
        if self._change_markers is None:
            self.set_marker_settings(settings)
        else:
            self._change_markers(settings)

    def marker_menu(self) -> QMenu:
        """Build an owned, localized menu from current options without applying them.

        Args:
            None.

        Returns:
            Caller-owned menu parented to this widget. Triggering its actions requests
            a visibility/interval change; closing it without selection changes nothing.
        """
        spanish = self.marker_language is Language.SPANISH
        menu = QMenu(self)
        for field, caption in (
            ("show_ticks", "Mostrar marcas" if spanish else "Show tick marks"),
            (
                "show_labels",
                "Mostrar límites de riesgo" if spanish else "Show risk-range limits",
            ),
        ):
            action = menu.addAction(caption)
            assert action is not None
            action.setObjectName(field)
            action.setCheckable(True)
            action.setChecked(getattr(self.marker_settings, field))
            action.triggered.connect(
                lambda checked, field=field: self._request_markers(
                    replace(self.marker_settings, **{field: checked})
                )
            )
        intervals = menu.addMenu("Intervalo de marcas" if spanish else "Tick interval")
        assert intervals is not None
        group = QActionGroup(intervals)
        group.setExclusive(True)
        for interval in (5, 10, 20, 25):
            action = intervals.addAction(f"{interval} %")
            assert action is not None
            action.setObjectName(f"interval_{interval}")
            action.setCheckable(True)
            action.setChecked(self.marker_settings.interval == interval)
            group.addAction(action)
            action.triggered.connect(
                lambda checked, interval=interval: self._request_markers(
                    replace(self.marker_settings, interval=interval)
                )
            )
        custom = intervals.addAction(
            "Otro intervalo…" if spanish else "Custom interval…"
        )
        assert custom is not None
        custom.setObjectName("custom_interval")
        custom.triggered.connect(self._custom_marker_interval)
        return menu

    def _custom_marker_interval(self) -> None:
        """Request an integer tick interval; cancelled input preserves current options.

        Args:
            None.

        Returns:
            None; accepted spacing is routed through the same host callback as presets.
            Both buttons are explicitly localized and the transient dialog is released.
        """
        spanish = self.marker_language is Language.SPANISH
        dialog = QInputDialog(self)
        apply_dialog_theme(dialog)
        dialog.setMinimumWidth(360)
        dialog.setWindowTitle("Intervalo de marcas" if spanish else "Tick interval")
        dialog.setLabelText("Puntos porcentuales" if spanish else "Percentage points")
        dialog.setInputMode(QInputDialog.InputMode.IntInput)
        dialog.setIntRange(1, 100)
        dialog.setIntValue(self.marker_settings.interval)
        dialog.setOkButtonText("Usar" if spanish else "Use")
        dialog.setCancelButtonText("Cancelar" if spanish else "Cancel")
        if self._dialog_icons is not None:
            buttons = dialog.findChild(QDialogButtonBox)
            if buttons is not None:
                for role, key in (
                    (QDialogButtonBox.Ok, "settings"),
                    (QDialogButtonBox.Cancel, "cancel"),
                ):
                    button = buttons.button(role)
                    if button is not None:
                        button.setIcon(self._dialog_icons[key])
        try:
            if dialog.exec() == QDialog.Accepted:
                self._request_markers(
                    replace(self.marker_settings, interval=dialog.intValue())
                )
        finally:
            dialog.deleteLater()

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:  # noqa: N802
        """Offer immediate marker controls for native right-click/keyboard menus.

        Args:
            event: Native context-menu request; None is ignored for diagnostics.

        Returns:
            None; dispose the transient menu after it closes, even without selection.
        """
        if event is None:
            return
        menu = self.marker_menu()
        try:
            menu.exec(event.globalPos())
        finally:
            menu.deleteLater()

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Draw the reviewed reference geometry, palette and needle/scale.

        Main/compact profiles share the same painter, bands, markers and menus.
        A small outer-label margin keeps decimals clear of tick lines; compact labels
        stay within PLOT result cards. No source refresh or persistence is emitted.

        Args:
            event: Qt paint notification, or None for diagnostic calls; exposed region
                does not change the complete drawing policy.

        Returns:
            None after painting categorical arcs, needle, one-decimal animated percent
            or unavailable dash, localized outcome caption and optional markers.
            Existing colors and scale mapping remain; geometry reserves label clearance.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(
            self.width() / 2.0,
            self.height() - 20.0 if self._compact else 98.0,
        )
        radius = (
            min(self.width() / 2.0 - 24.0, center.y() - 30.0, 72.0)
            if self._compact
            else min(self.width() / 2.0 - 16.0, 70.0)
        )
        arc_width = 15 if self._compact else 13
        arc_rect = QRectF(
            center.x() - radius, center.y() - radius, radius * 2, radius * 2
        )
        for start, end, _label, color, _range_text in _BANDS:
            painter.setPen(
                QPen(
                    QColor(color),
                    arc_width,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.FlatCap,
                )
            )
            painter.drawArc(
                arc_rect, int((180 - start * 1.8) * 16), -int((end - start) * 1.8 * 16)
            )
        paint_gauge_markers(
            painter,
            center,
            radius,
            arc_width,
            self.width(),
            (*(float(band[0]) for band in _BANDS), 100.0),
            self.marker_settings,
            self.marker_language,
        )
        if self.has_value or not self._compact:
            angle = math.radians(180.0 - self.display_value * 1.8)
            tip_radius = radius - (10 if self._compact else 9)
            tip = QPointF(
                center.x() + math.cos(angle) * tip_radius,
                center.y() - math.sin(angle) * tip_radius,
            )
            half_width = 5.0 if self._compact else 4.6
            perpendicular = QPointF(
                math.sin(angle) * half_width, math.cos(angle) * half_width
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#758590" if self._compact else "#87949D"))
            painter.drawPolygon(
                QPolygonF([center + perpendicular, tip, center - perpendicular])
            )
            painter.setBrush(QColor("#647580" if self._compact else "#6F7E88"))
            painter.drawEllipse(
                center, 5.5 if self._compact else 5.0, 5.5 if self._compact else 5.0
            )
        painter.setPen(QColor("#0B326C"))
        font = painter.font()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, center.y() - (25 if self._compact else 24), self.width(), 34),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.display_value:.{self.decimal_places}f}%"
            if self.has_value
            else ("N/A" if self._compact else "—"),
        )
        if not self._compact:
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(QColor("#304652"))
            painter.drawText(
                QRectF(4, 126, self.width() - 8, 36),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                self.outcome_text,
            )

    def set_probability(self, percent: float | None) -> None:
        """Accept PLOT probability/absence through the shared gauge value contract.

        Args:
            percent: Finite probability percentage or None for unavailable evidence.

        Returns:
            None; absence clears immediately; a repeated target retains animation time.

        Raises:
            ValueError: Boolean, nonnumeric or nonfinite probability is supplied.
        """
        if percent is None:
            self.clear()
        elif type(percent) not in (int, float) or not math.isfinite(percent):
            raise ValueError("PLOT gauge requires a finite percentage or absence.")
        else:
            self.set_value(float(percent), "#D9E1E6")


class DamageScale(_AnimatedScale):
    """Reviewed original DamageScale drawing with source-owned state."""

    def __init__(self) -> None:
        """Preserve the reference drawing size and animation duration.

        Args:
            None.

        Returns:
            None; configure the original 0-2 dimensionless scale and 700 ms animation
            with minimum 38-pixel height.
        """
        super().__init__(2, 700)
        self.setMinimumHeight(38)

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802
        """Draw the reviewed reference geometry, palette and needle/scale.

        Resize geometry follows current widget width. Rendering saturation above two
        never clamps saved cumulative damage.

        Args:
            event: Qt paint notification, or None for diagnostic calls; not used to
                change scientific state.

        Returns:
            None after drawing the original neutral track, bounded colored fill and
            fixed 0/1/>2 labels.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        left, right, y = (3.0, self.width() - 3.0, 11.0)
        painter.setPen(
            QPen(QColor("#D9DEE2"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawLine(QPointF(left, y), QPointF(right, y))
        progress_x = left + (right - left) * self.display_value / 2.0
        if progress_x > left:
            progress_x = max(progress_x, left + 4.0)
            painter.setPen(
                QPen(self.fill_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawLine(QPointF(left, y), QPointF(progress_x, y))
        painter.setPen(QColor("#506273"))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, 22, 34, 14),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "0",
        )
        painter.drawText(
            QRectF(self.width() / 2 - 18, 22, 36, 14), Qt.AlignmentFlag.AlignCenter, "1"
        )
        painter.drawText(
            QRectF(self.width() - 42, 22, 42, 14),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            ">2",
        )
