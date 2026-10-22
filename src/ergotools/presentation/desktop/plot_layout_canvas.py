"""Original PLOT image-space canvas with coalesced aspect-preserving resize fit.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QCloseEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QResizeEvent,
    QShowEvent,
)
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget

from ergotools.application.plot_layout import LoadedPlantLayout


class PlotLayoutCanvas(QGraphicsView):
    """Own decoded pixels and retain original image coordinates.

    Own decoded pixels and retain original image coordinates for the composed marker
    layer.
    """

    layout_replaced = pyqtSignal()
    fitted = pyqtSignal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the original map component; do not open files or global windows.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
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
        self._fit_timer.timeout.connect(self.fit_layout)
        self.replace_guard: Callable[[], bool] | None = None
        self.loaded_layout: LoadedPlantLayout | None = None
        self.background: QGraphicsPixmapItem | None = None
        self.zoom_pending = False
        self._opacity_index = 0

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
        self.cancel_zoom()
        if not pixmap.isNull():
            background = scene.addPixmap(pixmap)
            assert background is not None
            self.background = background
            background.setZValue(-1)
            scene.setSceneRect(background.sceneBoundingRect())
        else:
            scene.setSceneRect(0, 0, 0, 0)
            self.resetTransform()
        self.loaded_layout = layout
        self._fit_timer.start(0)

    def fit_layout(self) -> None:
        """Fit the complete image after layout without modifying pixel coordinates.

        Args:
            None.

        Returns:
            None.
        """
        scene = self.scene()
        if scene is not None and not scene.sceneRect().isEmpty():
            self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.fitted.emit(self.transform().m11())

    def begin_zoom(self) -> None:
        """Arm the source one-click 1.5x zoom without selecting or moving a marker.

        Args:
            None.

        Returns:
            None.
        """
        if self.background is not None:
            self.zoom_pending = True
            self.setCursor(Qt.CursorShape.CrossCursor)

    def cancel_zoom(self) -> None:
        """Return the map to its normal selection cursor without changing geometry.

        Args:
            None.

        Returns:
            None.
        """
        self.zoom_pending = False
        self.unsetCursor()

    def zoom_out(self) -> None:
        """Use the source 1/1.5 step and 1:1 floor; never enlarge a fitted small map.

        Args:
            None.

        Returns:
            None.
        """
        current = self.transform().m11()
        if current > 1.0:
            factor = max(1.0, current / 1.5) / current
            self.scale(factor, factor)

    def reset_view(self) -> None:
        """Restore the source fitted view without rereading results or losing edits.

        The legacy actual-size button reapplied filters as a transform workaround.
        Direct fit preserves the observed fitted view and unsaved marker intent.

        Args:
            None.

        Returns:
            None.
        """
        self._fit_timer.stop()
        self.cancel_zoom()
        self.fit_layout()

    def cycle_opacity(self) -> None:
        """Apply the actual source 90/80/70/100% sequence except to map pixels.

        Args:
            None.

        Returns:
            None.
        """
        levels = (0.9, 0.8, 0.7, 1.0)
        opacity = levels[self._opacity_index]
        self._opacity_index = (self._opacity_index + 1) % len(levels)
        scene = self.scene()
        if scene is not None:
            for item in scene.items():
                if item is not self.background:
                    item.setOpacity(opacity)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Consume an armed left zoom click; retain ordinary right-click menus.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        if (
            event is not None
            and self.zoom_pending
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
            self.scale(1.5, 1.5)
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
            self.cancel_zoom()
            event.accept()
            return
        super().mousePressEvent(event)

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
