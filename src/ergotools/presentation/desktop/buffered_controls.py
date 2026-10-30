"""Keep static Qt controls visually stable while an adjacent layout animates.

Presentation only. One device-aware widget pixmap shields unchanged controls from
ancestor/native-viewport repaint churn. Live controls retain focus, signals and mouse
ownership; no inputs or selection are copied. The buffer lasts only for the motion.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QResizeEvent
from PyQt5.QtWidgets import QLabel, QWidget


class BufferedControls(QWidget):
    """Temporarily paint a stable control strip through a mouse-transparent overlay."""

    def __init__(self) -> None:
        """Own an initially hidden presentation buffer above the live child controls.

        Args:
            None.

        Returns:
            None; the host retains layout, actions and animation lifetime.
        """
        super().__init__()
        self.buffer = QLabel(self)
        self.buffer.setObjectName("staticControlsBuffer")
        self.buffer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.buffer.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.buffer.hide()

    def freeze(self) -> None:
        """Capture the settled live strip at its native device pixel ratio.

        Args:
            None.

        Returns:
            None; only visible presentation is buffered. Controls remain interactive.
        """
        self.buffer.hide()
        self.buffer.setPixmap(self.grab())
        self.buffer.setGeometry(self.rect())
        self.buffer.show()
        self.buffer.raise_()

    def thaw(self) -> None:
        """Restore live painting and release the short-lived pixmap.

        Args:
            None.

        Returns:
            None; selection, text, focus and control geometry remain unchanged.
        """
        self.buffer.hide()
        self.buffer.setPixmap(QPixmap())

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802 — Qt override
        """Return to live controls when an actual window resize changes the strip.

        Args:
            event: Native geometry change; None only releases the buffer.

        Returns:
            None; never stretch stale pixels or defer a user's window resize.
        """
        self.thaw()
        if event is not None:
            super().resizeEvent(event)
