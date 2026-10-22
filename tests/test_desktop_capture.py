"""Desktop capture preserves adjacent controls and device-independent geometry.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import pytest
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtWidgets import QApplication, QLabel

from tools.capture_desktop import composite_native_viewport, render_widget

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("ratio", [1.0, 1.5, 2.0])
def test_native_frame_cannot_overpaint_adjacent_controls(ratio: float) -> None:
    """A large native framebuffer stays inside its small logical viewport.

    Args:
        ratio: Explicit native screenshot/device scaling factor used to check capture
            geometry.

    Returns:
        None.
    """
    base = QImage(int(100 * ratio), int(80 * ratio), QImage.Format.Format_RGB32)
    base.setDevicePixelRatio(ratio)
    base.fill(QColor("white"))
    frame = QImage(400, 300, QImage.Format.Format_RGB32)
    frame.fill(QColor("red"))
    composed = composite_native_viewport(base, QRect(20, 10, 30, 20), frame)
    for y in range(base.height()):
        for x in range(base.width()):
            inside = 20 * ratio <= x < 50 * ratio and 10 * ratio <= y < 30 * ratio
            assert composed.pixelColor(x, y) == QColor("red" if inside else "white")
    assert base.pixelColor(int(25 * ratio), int(15 * ratio)) == QColor("white")
    assert composed.devicePixelRatio() == ratio
    for rect in (QRect(), QRect(-1, 0, 10, 10), QRect(90, 0, 20, 20)):
        with pytest.raises(ValueError, match="fit entirely"):
            composite_native_viewport(base, rect, frame)
    with pytest.raises(ValueError, match="nonempty"):
        composite_native_viewport(base, QRect(0, 0, 10, 10), QImage())
    with pytest.raises(ValueError, match="nonempty"):
        composite_native_viewport(QImage(), QRect(0, 0, 10, 10), frame)


def test_qt_capture_owns_pixels_without_changing_control_state() -> None:
    """An image remains stable after its source control text changes.

    Args:
        None.

    Returns:
        None.
    """
    label = QLabel("Visible caption")
    label.resize(200, 40)
    label.show()
    _APP.processEvents()
    try:
        before = label.geometry()
        image = render_widget(label)
        frozen = image.copy()
        label.setText("Changed caption")
        assert image == frozen and label.geometry() == before
        assert render_widget(label) != frozen
        label.resize(0, 0)
        with pytest.raises(ValueError, match="positive"):
            render_widget(label)
    finally:
        label.close()
