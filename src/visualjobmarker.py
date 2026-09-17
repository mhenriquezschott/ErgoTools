"""Station-anchored Job risk marker used by PLOT Job Risk view."""

from __future__ import annotations

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import QGraphicsItem, QMessageBox

from database import database_session
from plot_position_repository import StationKey, set_station_position


class VisualJobMarker(QGraphicsItem):
    def __init__(self, scene, data, scale_factor, *, display_offset=(0.0, 0.0)):
        super().__init__()
        self.parent_scene = scene
        self.data = data
        self.station_key = StationKey(
            str(data["plant_name"]),
            str(data["section_name"]),
            str(data["line_name"]),
            str(data["station_id"]),
        )
        self.job_id = str(data["job_id"])
        self.job_name = str(data.get("job_name") or "")
        self.shift_id = str(data["shift_id"])
        self.assigned_worker_count = int(data.get("assigned_worker_count") or 0)
        self.probability_outcome = data.get("probability_outcome")
        self.profile_name = data.get("job_risk_profile_name")
        self.profile_version = data.get("job_risk_profile_version")
        self.color = QColor(data.get("color", "#9AA8B2"))
        self.size = 38.0
        self.scale_factor = float(scale_factor or 1.0)
        self.internal_scale = round(1.0 / self.scale_factor, 2)
        self.offset_x = float(display_offset[0])
        self.offset_y = float(display_offset[1])
        self.has_anchor = data.get("x") is not None and data.get("y") is not None
        anchor_x = float(data.get("x") or 18.0)
        anchor_y = float(data.get("y") or 18.0)
        self.setPos(anchor_x + self.offset_x, anchor_y + self.offset_y)
        self._start_position = self.pos()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCursor(Qt.OpenHandCursor)
        self.setZValue(4)
        self.setToolTip(self._tooltip())
        scene.addItem(self)

    def _tooltip(self):
        risk = (
            f"{float(self.probability_outcome):.1f}%"
            if self.probability_outcome is not None
            else "Not available"
        )
        profile = self.profile_name or "Not available"
        if self.profile_version is not None:
            profile += f" (v{self.profile_version})"
        return (
            f"Job: {self.job_id} - {self.job_name}\n"
            f"Station: {self.station_key.station_id}\n"
            f"Shift: {self.shift_id}\n"
            f"Assigned workers: {self.assigned_worker_count}\n"
            f"Job Risk: {risk}\n"
            f"Profile: {profile}\n"
            "Drag to set or move the Station position."
        )

    def boundingRect(self):
        margin = max(5.0, 5.0 * self.internal_scale)
        return self._markerRect().adjusted(-margin, -margin, margin, margin)

    def _markerRect(self):
        side = self.size * self.internal_scale
        return QRectF(0.0, 0.0, side, side)

    def paint(self, painter, option, widget=None):
        rect = self._markerRect()
        pen = QPen(QColor("#111111"), max(1, round(2 * self.internal_scale)))
        if not self.has_anchor:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.color))
        painter.drawRect(rect)
        painter.setPen(QColor("#071B2D") if self.color.lightness() > 145 else Qt.white)
        font = QFont("Segoe UI")
        font.setBold(True)
        font.setPixelSize(max(8, round(11 * self.internal_scale)))
        painter.setFont(font)
        marker_label = self.job_id.removeprefix("Job-")
        painter.drawText(rect, Qt.AlignCenter, marker_label)
        if self.isSelected():
            painter.setPen(QPen(QColor("#0057D8"), max(2, round(3 * self.internal_scale))))
            painter.setBrush(Qt.NoBrush)
            selection_gap = max(3.0, 3.0 * self.internal_scale)
            painter.drawRect(rect.adjusted(
                -selection_gap, -selection_gap, selection_gap, selection_gap
            ))

    def mousePressEvent(self, event):
        self._start_position = self.pos()
        self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setCursor(Qt.OpenHandCursor)
        if self.pos() == self._start_position:
            return
        plot_window = self.parent_scene.parent()
        database_path = getattr(plot_window.parent(), "projectdatabasePath", "")
        if not database_path:
            self.setPos(self._start_position)
            return
        anchor_x = float(self.pos().x()) - self.offset_x
        anchor_y = float(self.pos().y()) - self.offset_y
        try:
            with database_session(database_path) as connection:
                set_station_position(
                    connection,
                    self.station_key,
                    anchor_x,
                    anchor_y,
                    position_source="job",
                )
            self.has_anchor = True
            self.update()
            callback = getattr(plot_window, "jobMarkerPositionSaved", None)
            if callback is not None:
                callback(self.station_key, anchor_x, anchor_y)
        except Exception as error:
            self.setPos(self._start_position)
            QMessageBox.critical(
                plot_window,
                "Position not saved",
                f"The Station position could not be saved:\n{error}",
            )
