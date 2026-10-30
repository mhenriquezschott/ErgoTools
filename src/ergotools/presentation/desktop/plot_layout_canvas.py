"""Original PLOT image-space canvas with coalesced aspect-preserving resize fit.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable
from math import isfinite
from typing import Literal

from PyQt5.QtCore import QPoint, QPointF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QCloseEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QResizeEvent,
    QShowEvent,
    QWheelEvent,
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from ergotools.application.plot_history import MAX_PLOT_ZOOM, PlotNavigationState
from ergotools.application.plot_layout import LoadedPlantLayout
from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_navigation_icons import zoom_cursor


class PlotLayoutCanvas(QGraphicsView):
    """Own decoded pixels and retain original image coordinates.

    Own decoded pixels and retain original image coordinates for the composed marker
    layer.
    """

    layout_replaced = pyqtSignal()
    # Fitted baseline excludes user magnification, so markers zoom with the image.
    fitted = pyqtSignal(float)
    # Cursor choice is transient; completed image gestures enter view history.
    navigation_changed = pyqtSignal(str)
    # One completed view gesture, with immutable before/after snapshots.
    view_edited = pyqtSignal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the original map component; do not open files or global windows.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        viewport = self.viewport()
        horizontal = self.horizontalScrollBar()
        vertical = self.verticalScrollBar()
        assert viewport is not None and horizontal is not None and vertical is not None
        self._viewport = viewport
        self._horizontal_bar = horizontal
        self._vertical_bar = vertical
        self.setObjectName("plantlayout_image")
        self.setMinimumSize(900, 580)
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(
            QPainter.RenderHints(QPainter.RenderHint.Antialiasing)
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setAlignment(
            Qt.Alignment(Qt.AlignmentFlag.AlignTop) | Qt.AlignmentFlag.AlignLeft
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._fit_timer = QTimer(self)
        self._fit_timer.setSingleShot(True)
        self._fit_timer.timeout.connect(self.refit_layout)
        self.replace_guard: Callable[[], bool] | None = None
        self.loaded_layout: LoadedPlantLayout | None = None
        self.background: QGraphicsPixmapItem | None = None
        self.navigation_mode: Literal["select", "zoom_in", "zoom_out", "pan"] = "select"
        self.language = Language.ENGLISH
        self._fit_scale: float | None = None
        self._zoom_ratio = 1.0
        self._view_center: QPointF | None = None
        self._pan_start: QPoint | None = None
        self._pan_scroll = QPoint()
        self._pan_before: PlotNavigationState | None = None
        self.marker_opacity = 1.0
        self._opacity_index = 0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

    def set_layout(self, layout: LoadedPlantLayout | None) -> None:
        """Decode before replacing the map; invalid pixels retain the previous scope.

        An absent saved image clears the previous plant's map. Scene coordinates remain
        original image pixels, matching the reference worker/job positions.

        Args:
            layout: Decoded saved/preview image and exact plant scope; None after
                project replay removes its organization. Absent pixels clear the map.

        Returns:
            None.

        Raises:
            ValueError: Save or cancel PLOT marker edits before replacing the map. The
                saved plant layout image cannot be decoded.
        """
        if self.replace_guard is not None and not self.replace_guard():
            raise ValueError(
                "Save or cancel PLOT marker edits before replacing the map."
            )
        pixmap = QPixmap()
        if (
            layout is not None
            and layout.image is not None
            and not pixmap.loadFromData(layout.image)
        ):
            raise ValueError("The saved plant layout image cannot be decoded.")
        scene = self.scene()
        assert scene is not None
        self.layout_replaced.emit()
        scene.clear()
        self.background = None
        self.cancel_navigation()
        if not pixmap.isNull():
            background = scene.addPixmap(pixmap)
            assert background is not None
            self.background = background
            background.setZValue(-1)
            scene.setSceneRect(background.sceneBoundingRect())
        else:
            scene.setSceneRect(0, 0, 0, 0)
            self.resetTransform()
        self.marker_opacity = 1.0
        self._opacity_index = 0
        self.loaded_layout = layout
        self._fit_scale = None
        self._zoom_ratio = 1.0
        self._view_center = None
        self._fit_timer.start(0)

    @property
    def fitted_scale(self) -> float:
        """Expose the unzoomed fit used to normalize initial marker dimensions.

        Args:
            None.

        Returns:
            Positive image-fit scale, excluding user zoom; current transform before fit.
        """
        return self._fit_scale or self.transform().m11()

    @property
    def zoom_pending(self) -> bool:
        """Report a persistent magnifier tool.

        Args:
            None.

        Returns:
            True for either magnifier; pan and selection are not pending zoom.
        """
        return self.navigation_mode in ("zoom_in", "zoom_out")

    @property
    def can_zoom_out(self) -> bool:
        """Allow zooming out to the fitted image, even when fit is below 1:1.

        Args:
            None.

        Returns:
            True when the current transform exceeds this viewport's fitted scale.
        """
        return (
            self._fit_scale is not None
            and self.transform().m11() > self._fit_scale * 1.000001
        )

    def fit_layout(self) -> None:
        """Reset to the entire image without changing any original-pixel geometry.

        Args:
            None.

        Returns:
            None; previous zoom/pan is discarded only by this explicit fit operation.
        """
        self._zoom_ratio = 1.0
        self._view_center = None
        self.refit_layout()

    def refit_layout(self) -> None:
        """Recompute fit for the viewport while preserving user zoom and scene center.

        Args:
            None.

        Returns:
            None; ordinary resizing does not unexpectedly reset a magnified map.
        """
        scene = self.scene()
        if self.background is None or scene is None or scene.sceneRect().isEmpty():
            return
        center = self._view_center
        self.resetTransform()
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_scale = self.transform().m11()
        if self._zoom_ratio > 1:
            self.scale(self._zoom_ratio, self._zoom_ratio)
            if center is not None:
                self.centerOn(center)
        self._view_center = self.mapToScene(self._viewport.rect().center())
        if not self.can_zoom_out and self.navigation_mode in ("zoom_out", "pan"):
            self.cancel_navigation()
        self.fitted.emit(self.fitted_scale)

    def set_navigation_mode(
        self, mode: Literal["select", "zoom_in", "zoom_out", "pan"]
    ) -> None:
        """Apply an explicit local mode with cursor, focus and scene-drag ownership.

        Args:
            mode: Selection, persistent magnifier, or pan. Missing pixels or a fitted
                view with no pan/zoom-out range forces ordinary selection.

        Returns:
            None; navigation never selects/moves markers or writes project data.
        """
        if self.background is None or (
            mode in ("zoom_out", "pan") and not self.can_zoom_out
        ):
            mode = "select"
        changed = mode != self.navigation_mode
        self.navigation_mode = mode
        self._pan_start = None
        self.setInteractive(mode == "select")
        if mode in ("zoom_in", "zoom_out"):
            cursor = zoom_cursor(out=mode == "zoom_out")
            self.setCursor(cursor)
            self._viewport.setCursor(cursor)
        elif mode == "pan":
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self._viewport.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.unsetCursor()
            self._viewport.unsetCursor()
        if mode != "select":
            self.setFocus(Qt.FocusReason.MouseFocusReason)
        if changed:
            self.navigation_changed.emit(mode)

    def begin_zoom(self) -> None:
        """Select persistent zoom-in; repeated image clicks retain the magnifier.

        Args:
            None.

        Returns:
            None; Select or Escape restores ordinary marker selection.
        """
        self.set_navigation_mode("zoom_in")

    def zoom_out(self) -> None:
        """Select persistent zoom-out, using fitted scale as its floor.

        Args:
            None.

        Returns:
            None; every subsequent image click zooms until another tool is selected.
        """
        self.set_navigation_mode("zoom_out")

    def begin_pan(self) -> None:
        """Select persistent hand-drag mode without enabling marker movement.

        Args:
            None.

        Returns:
            None; middle-button dragging also pans without entering this mode.
        """
        self.set_navigation_mode("pan")

    def cancel_navigation(self) -> None:
        """Disarm navigation and restore normal marker selection without refitting.

        Args:
            None.

        Returns:
            None; pan/zoom already performed stays as a local view choice.
        """
        self.set_navigation_mode("select")

    def apply_zoom(self, factor: float, position: QPoint) -> None:
        """Zoom at a viewport point with a fitted floor and a 400% fit ceiling.

        Args:
            factor: Positive multiplicative view step supplied by a gesture.
            position: Viewport-pixel target, independent of original image coordinates.

        Returns:
            None; original image points, marker geometry and data history stay exact.
        """
        if self.background is None or not isfinite(factor) or factor <= 0:
            return
        self._fit_timer.stop()
        if self._fit_scale is None:
            self.refit_layout()
        before_view = self.navigation_snapshot()
        assert self._fit_scale is not None
        current = self.transform().m11()
        target = max(
            self._fit_scale, min(self._fit_scale * MAX_PLOT_ZOOM, current * factor)
        )
        before = self.mapToScene(position)
        self.scale(target / current, target / current)
        after = self.mapToScene(position)
        delta = after - before
        self.translate(delta.x(), delta.y())
        self._zoom_ratio = min(MAX_PLOT_ZOOM, target / self._fit_scale)
        self._view_center = self.mapToScene(self._viewport.rect().center())
        if not self.can_zoom_out and self.navigation_mode in ("zoom_out", "pan"):
            self.cancel_navigation()
        self.fitted.emit(self.fitted_scale)
        self.publish_view_edit(before_view)

    def navigation_snapshot(self) -> PlotNavigationState | None:
        """Capture widget-free view data for a completed user gesture.

        Args:
            None.

        Returns:
            Current plant view, or None when no image is loaded.
        """
        if self.background is None or self.loaded_layout is None:
            return None
        center = self.mapToScene(self._viewport.rect().center())
        return PlotNavigationState(
            self.loaded_layout.scope.plant,
            self._zoom_ratio,
            (center.x(), center.y()),
            self.marker_opacity,
        )

    def publish_view_edit(self, before: PlotNavigationState | None) -> None:
        """Publish exactly one changed user gesture; automatic fitting is excluded.

        Args:
            before: View captured before zoom, hand drag, Fit or opacity adjustment.

        Returns:
            None; clamped zoom and stationary drags add no history action.
        """
        after = self.navigation_snapshot()
        if before is not None and after is not None and after != before:
            self.view_edited.emit(before, after)

    def restore_navigation(self, state: PlotNavigationState | None) -> None:
        """Project a history view without emitting another edit or moving markers.

        Args:
            state: Retained view; another plant or None leaves its normal fitted view.

        Returns:
            None; scene center uses original image pixels and opacity affects markers.
        """
        if (
            state is None
            or self.loaded_layout is None
            or self.background is None
            or state.plant != self.loaded_layout.scope.plant
        ):
            return
        self._fit_timer.stop()
        self._zoom_ratio = state.zoom
        self._view_center = QPointF(*state.center)
        self.refit_layout()
        self.centerOn(QPointF(*state.center))
        self._view_center = self.mapToScene(self._viewport.rect().center())
        self.marker_opacity = state.opacity
        self._opacity_index = ((0.9, 0.8, 0.7, 1.0).index(state.opacity) + 1) % 4
        scene = self.scene()
        assert scene is not None
        for item in scene.items():
            if item is not self.background:
                item.setOpacity(state.opacity)

    def locate_item(self, item: QGraphicsItem) -> None:
        """Center a mapped assignment within image bounds, preserving magnification.

        Args:
            item: Borrowed scene item belonging to this canvas.

        Returns:
            None; Qt clamps near image edges. The recentering joins view history,
            while assignment geometry and the current cursor tool are unchanged.
        """
        before = self.navigation_snapshot()
        self.centerOn(item.sceneBoundingRect().center())
        self._view_center = self.mapToScene(self._viewport.rect().center())
        self.publish_view_edit(before)

    def reset_view(self) -> None:
        """Fit the complete image while retaining the active cursor tool.

        Args:
            None.

        Returns:
            None; this is Fit image, not a misleading promise of native 1:1 pixels.
        """
        before = self.navigation_snapshot()
        self._fit_timer.stop()
        self.fit_layout()
        self.publish_view_edit(before)

    def cycle_opacity(self) -> None:
        """Apply the actual source 90/80/70/100% sequence except to map pixels.

        Args:
            None.

        Returns:
            None.
        """
        before = self.navigation_snapshot()
        levels = (0.9, 0.8, 0.7, 1.0)
        opacity = levels[self._opacity_index]
        self.marker_opacity = opacity
        self._opacity_index = (self._opacity_index + 1) % len(levels)
        scene = self.scene()
        if scene is not None:
            for item in scene.items():
                if item is not self.background:
                    item.setOpacity(opacity)
        self.publish_view_edit(before)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Consume image navigation gestures before any graphics-item selection/drag.

        Args:
            event: Native viewport mouse event; None is handled by the Qt base.

        Returns:
            None; magnifiers stay active and cannot move the marker below them.
        """
        if event is not None and self.background is not None:
            if (
                event.button() == Qt.MouseButton.MiddleButton and self.can_zoom_out
            ) or (
                self.navigation_mode == "pan"
                and event.button() == Qt.MouseButton.LeftButton
            ):
                self._pan_before = self.navigation_snapshot()
                self._pan_start = event.pos()
                self._pan_scroll = QPoint(
                    self._horizontal_bar.value(), self._vertical_bar.value()
                )
                self._viewport.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
            if self.zoom_pending and event.button() == Qt.MouseButton.LeftButton:
                if self.background.sceneBoundingRect().contains(
                    self.mapToScene(event.pos())
                ):
                    self.apply_zoom(
                        1.5 if self.navigation_mode == "zoom_in" else 1 / 1.5,
                        event.pos(),
                    )
                event.accept()
                return
            if (
                self.navigation_mode != "select"
                and event.button() == Qt.MouseButton.RightButton
            ):
                self.cancel_navigation()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Pan using hidden scroll offsets while leaving marker coordinates untouched.

        Args:
            event: Native viewport move; normal selection delegates to Qt.

        Returns:
            None; no scrollbars become visible and no item receives this drag.
        """
        if event is not None and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._horizontal_bar.setValue(self._pan_scroll.x() - delta.x())
            self._vertical_bar.setValue(self._pan_scroll.y() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Finish hand/middle dragging without generating a marker-release operation.

        Args:
            event: Native release matching the retained navigation press.

        Returns:
            None; the selected navigation cursor and local scene center are retained.
        """
        if event is not None and self._pan_start is not None:
            self._pan_start = None
            self._view_center = self.mapToScene(self._viewport.rect().center())
            self.publish_view_edit(self._pan_before)
            self._pan_before = None
            if self.navigation_mode == "pan":
                self._viewport.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self._viewport.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """Let Escape cancel navigation before the containing dialog can close.

        Args:
            event: Native focused key event; ordinary typing delegates to Qt.

        Returns:
            None; a later Escape in selection mode keeps normal dialog behavior.
        """
        if (
            event is not None
            and event.key() == Qt.Key.Key_Escape
            and self.navigation_mode != "select"
        ):
            self.cancel_navigation()
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent | None) -> None:  # noqa: N802
        """Zoom at the pointer with the wheel without editing or selecting markers.

        Args:
            event: Native wheel input inside this map, not the side-panel scroll area.

        Returns:
            None; empty maps retain Qt's normal no-content behavior.
        """
        if event is not None and self.background is not None and event.angleDelta().y():
            self.apply_zoom(
                1.2 ** max(-10, min(10, event.angleDelta().y() / 120)),
                event.position().toPoint(),
            )
            event.accept()
            return
        super().wheelEvent(event)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        """Coalesce resize events into one owned Qt layout-pass callback.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        super().resizeEvent(event)
        self._fit_timer.start(0)

    def showEvent(self, event: QShowEvent | None) -> None:  # noqa: N802
        """Refit when the final viewport geometry becomes available.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        super().showEvent(event)
        self._fit_timer.start(0)

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Stop pending work when the component is closed.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        self._fit_timer.stop()
        super().closeEvent(event)
