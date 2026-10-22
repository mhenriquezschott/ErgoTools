"""CPU-backed Qt/native viewport capture for desktop visual verification only.

Native OpenGL widgets do not participate in Qt's raster paint engine. Render Qt controls
into owned image memory, then insert the separately captured native frame in its exact
logical viewport. No application refresh or layout is changed.

Developer tooling layer. Call these synchronous capture helpers on the GUI thread; they
create validation images rather than changing application state.
"""

import math

from PyQt5.QtCore import QPoint, QRect, QRectF, Qt
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QWidget


def render_widget(widget: QWidget) -> QImage:
    """Render visible Qt controls into an owned CPU image on the GUI thread.

    Native OpenGL content must be supplied separately. Device pixel ratio is retained so
    logical widget coordinates also work with fractional scaling. This synchronous
    operation paints only; it neither processes queued events nor commits editors or
    changes widget geometry.

    Args:
        widget: Live visible Qt widget owned by the GUI thread; its geometry is not
            changed.

    Returns:
        Detached CPU-backed image at the widget's retained device pixel ratio; native
        OpenGL pixels must be supplied separately.

    Raises:
        ValueError: The widget has no positive drawable area.
    """
    if widget.width() <= 0 or widget.height() <= 0:
        raise ValueError("Capture requires positive widget dimensions.")
    ratio = widget.devicePixelRatioF()
    image = QImage(
        math.ceil(widget.width() * ratio),
        math.ceil(widget.height() * ratio),
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    image.setDevicePixelRatio(ratio)
    image.fill(Qt.GlobalColor.transparent)
    widget.render(image, QPoint())
    return image


def composite_native_viewport(
    snapshot: QImage, viewport: QRect, frame: QImage
) -> QImage:
    """Insert a native frame into its logical bounds without changing other pixels.

    Return a detached CPU image; never mutate the captured Qt snapshot. Scale native
    framebuffer pixels to the exact logical viewport, independent of framebuffer/device
    pixel ratio. Clipping prevents painting adjacent controls.

    Args:
        snapshot: Owned raster capture of the surrounding Qt controls, including its
            device pixel ratio.
        viewport: Native widget bounds in logical coordinates relative to snapshot; must
            fit entirely inside it.
        frame: Nonempty separately captured native framebuffer image; rescaled only in
            the detached output.

    Returns:
        Detached composite with native pixels confined to the exact logical viewport;
        snapshot and frame are unchanged.

    Raises:
        ValueError: Images are empty or the viewport is empty/outside the snapshot.
    """
    if snapshot.isNull() or frame.isNull():
        raise ValueError("Capture requires nonempty Qt and native images.")
    ratio = snapshot.devicePixelRatio()
    bounds = QRectF(0, 0, snapshot.width() / ratio, snapshot.height() / ratio)
    if viewport.isEmpty() or not bounds.contains(QRectF(viewport)):
        raise ValueError("Native viewport must fit entirely inside the snapshot.")
    result = snapshot.copy()
    painter = QPainter(result)
    try:
        painter.setClipRect(viewport)
        painter.drawImage(QRectF(viewport), frame, QRectF(frame.rect()))
    finally:
        painter.end()
    return result
