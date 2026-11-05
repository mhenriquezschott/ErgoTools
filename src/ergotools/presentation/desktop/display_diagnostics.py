"""Read-only Qt startup/display observations through an injected report callback.

Presentation layer. Watches native top-level geometry, fonts, screen changes and Qt
messages without altering DPI attributes, scaling or window sizes. Timers coalesce
layout churn; bounded snapshots contain control geometry, never field text or images.
"""

import sys
from collections.abc import Callable, Mapping

from PyQt5 import sip
from PyQt5.QtCore import (
    PYQT_VERSION_STR,
    QT_VERSION_STR,
    QCoreApplication,
    QEvent,
    QMessageLogContext,
    QObject,
    QRect,
    Qt,
    QTimer,
    QtMsgType,
    qInstallMessageHandler,
    qVersion,
)
from PyQt5.QtGui import QGuiApplication, QScreen
from PyQt5.QtWidgets import QApplication, QWidget


def rectangle(value: QRect) -> dict[str, int]:
    """Encode logical-pixel geometry without mixing in physical screen pixels.

    Args:
        value: Qt rectangle in the documented caller's coordinate system.

    Returns:
        Plain x/y/width/height values, preserving negative multi-monitor origins.
    """
    return {
        "x": value.x(),
        "y": value.y(),
        "width": value.width(),
        "height": value.height(),
    }


class DisplayDiagnostics(QObject):
    """Observe Qt messages and top-level layout transitions for one launch only."""

    def __init__(
        self,
        record: Callable[[str, Mapping[str, object]], None],
        native: Callable[[int | None], dict[str, object]],
    ) -> None:
        """Install message capture before QApplication starts loading platform plugins.

        Args:
            record: Thread-safe, fail-soft infrastructure report sink.
            native: Read-only native OS DPI probe supplied by composition.

        Returns:
            None; callbacks never change rendering or scaling policy.
        """
        super().__init__()
        self.record, self.native = record, native
        self.app: QApplication | None = None
        self.closed = False
        self.pending: dict[int, QWidget] = {}
        self.screens: list[QScreen] = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.flush)
        self.previous_handler = qInstallMessageHandler(self.message)
        self.record(
            "qt_before_application",
            {
                "qt_compile": QT_VERSION_STR,
                "qt_runtime": qVersion(),
                "pyqt": PYQT_VERSION_STR,
                "native": self.native(None),
            },
        )

    def message(
        self, kind: QtMsgType, context: QMessageLogContext, text: str | None
    ) -> None:
        """Record Qt/plugin warnings while preserving the previous message destination.

        Args:
            kind: Original Qt message severity.
            context: Original source/category context, without local variable values.
            text: Original diagnostic message.

        Returns:
            None; Qt retains fatal-message handling after this callback returns.
        """
        if not self.closed:
            self.record(
                "qt_message",
                {
                    "severity": int(kind),
                    "category": context.category,
                    "message": text,
                    "file": context.file,
                    "line": context.line,
                },
            )
        if self.previous_handler is not None:
            self.previous_handler(kind, context, text)
        else:
            print(text, file=sys.stderr)

    def attach(self, app: QApplication) -> None:
        """Attach display observation after QApplication chooses its actual backend.

        Args:
            app: Existing GUI application owned by bootstrap.

        Returns:
            None; screen listeners and event filter live only until close.
        """
        self.app = app
        app.installEventFilter(self)
        app.screenAdded.connect(self.screen_added)
        app.screenRemoved.connect(self.screen_removed)
        style = app.style()
        self.record(
            "qt_application",
            {
                "platform": QGuiApplication.platformName(),
                "style": style.objectName() if style else None,
                "library_paths": QCoreApplication.libraryPaths(),
                "high_dpi_scaling": QCoreApplication.testAttribute(
                    Qt.ApplicationAttribute.AA_EnableHighDpiScaling
                ),
                "high_dpi_pixmaps": QCoreApplication.testAttribute(
                    Qt.ApplicationAttribute.AA_UseHighDpiPixmaps
                ),
                "disable_high_dpi_scaling": QCoreApplication.testAttribute(
                    Qt.ApplicationAttribute.AA_DisableHighDpiScaling
                ),
                "rounding_policy": int(
                    QGuiApplication.highDpiScaleFactorRoundingPolicy()
                ),
                "font": app.font().toString(),
                "native": self.native(None),
            },
        )
        for screen in app.screens():
            self.screen_added(screen)

    def screen_added(self, screen: QScreen) -> None:
        """Subscribe once to a real attached screen and record its current metrics.

        Args:
            screen: Screen supplied by Qt; identity/units remain Qt-owned.

        Returns:
            None; listeners are disconnected on removal or observer close.
        """
        if self.closed or screen in self.screens:
            return
        self.screens.append(screen)
        screen.geometryChanged.connect(self.screen_changed)
        screen.availableGeometryChanged.connect(self.screen_changed)
        screen.logicalDotsPerInchChanged.connect(self.screen_changed)
        screen.physicalDotsPerInchChanged.connect(self.screen_changed)
        self.screen_changed()

    def screen_removed(self, screen: QScreen) -> None:
        """Forget a removed monitor without retaining dead native screen wrappers.

        Args:
            screen: Removed screen, whose native lifetime may end after this signal.

        Returns:
            None; remaining screen metrics are recorded anew.
        """
        if screen in self.screens:
            self.screens.remove(screen)
        self.record("screen_removed", {"remaining": len(self.screens)})
        self.screen_changed()

    def screen_changed(self) -> None:
        """Capture Qt screen metrics with explicit logical/physical coordinate units.

        Args:
            None.

        Returns:
            None; no pixel ratio is used to resize the application.
        """
        if self.closed:
            return
        values = []
        for screen in self.screens:
            if sip.isdeleted(screen):
                continue
            values.append(
                {
                    "name": screen.name(),
                    "manufacturer": screen.manufacturer(),
                    "model": screen.model(),
                    "geometry_logical": rectangle(screen.geometry()),
                    "available_logical": rectangle(screen.availableGeometry()),
                    "virtual_logical": rectangle(screen.virtualGeometry()),
                    "device_pixel_ratio": screen.devicePixelRatio(),
                    "logical_dpi": [
                        screen.logicalDotsPerInchX(),
                        screen.logicalDotsPerInchY(),
                    ],
                    "physical_dpi": [
                        screen.physicalDotsPerInchX(),
                        screen.physicalDotsPerInchY(),
                    ],
                    "physical_mm": [
                        screen.physicalSize().width(),
                        screen.physicalSize().height(),
                    ],
                    "depth": screen.depth(),
                    "refresh_hz": screen.refreshRate(),
                    "primary": screen is QGuiApplication.primaryScreen(),
                }
            )
        self.record("screens", {"screens": values})

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 — Qt override
        """Coalesce shown/moved/resized top-level windows without consuming events.

        Args:
            watched: Native object observed through QApplication's filter.
            event: Original event, always forwarded unchanged.

        Returns:
            False; diagnostics never interfere with input, sizing or native handling.
        """
        if (
            not self.closed
            and isinstance(watched, QWidget)
            and watched.isWindow()
            and event is not None
            and event.type()
            in (
                QEvent.Type.Show,
                QEvent.Type.Resize,
                QEvent.Type.Move,
                QEvent.Type.WindowStateChange,
            )
        ):
            self.pending[id(watched)] = watched
            if not self.timer.isActive():
                self.timer.start()
        return False

    def flush(self) -> None:
        """Record settled top-level and bounded child geometry after layout churn.

        Args:
            None.

        Returns:
            None; deleted/hidden windows are skipped and no window title/text is read.
        """
        pending, self.pending = self.pending, {}
        if self.closed:
            return
        for widget in pending.values():
            if sip.isdeleted(widget) or not widget.isVisible():
                continue
            handle = widget.windowHandle()
            screen = handle.screen() if handle else None
            children = widget.findChildren(QWidget)
            self.record(
                "window_layout",
                {
                    "class": type(widget).__name__,
                    "object": widget.objectName(),
                    "geometry_logical": rectangle(widget.geometry()),
                    "frame_logical": rectangle(widget.frameGeometry()),
                    "minimum": [widget.minimumWidth(), widget.minimumHeight()],
                    "size_hint": [
                        widget.sizeHint().width(),
                        widget.sizeHint().height(),
                    ],
                    "device_pixel_ratio": widget.devicePixelRatioF(),
                    "screen": screen.name() if screen else None,
                    "font": widget.font().toString(),
                    "fits_screen_width": widget.frameGeometry().width()
                    <= screen.availableGeometry().width()
                    if screen
                    else None,
                    "fits_screen_height": widget.frameGeometry().height()
                    <= screen.availableGeometry().height()
                    if screen
                    else None,
                    "native": self.native(int(handle.winId()) if handle else None),
                    "children_total": len(children),
                    "children": [
                        {
                            "class": type(c).__name__,
                            "object": c.objectName(),
                            "geometry_logical": rectangle(c.geometry()),
                            "visible": c.isVisible(),
                            "font": c.font().toString(),
                            "minimum": [c.minimumWidth(), c.minimumHeight()],
                            "size_hint": [c.sizeHint().width(), c.sizeHint().height()],
                        }
                        for c in children[:80]
                    ],
                },
            )

    def close(self) -> None:
        """Stop capture and restore the prior Qt message handler without closing Qt.

        Args:
            None.

        Returns:
            None; no queued callback can append window observations after close.
        """
        if self.closed:
            return
        self.flush()
        self.closed = True
        self.timer.stop()
        self.pending.clear()
        qInstallMessageHandler(self.previous_handler)
        if self.app is not None:
            self.app.removeEventFilter(self)
            self.app.screenAdded.disconnect(self.screen_added)
            self.app.screenRemoved.disconnect(self.screen_removed)
        for screen in self.screens:
            if not sip.isdeleted(screen):
                screen.geometryChanged.disconnect(self.screen_changed)
                screen.availableGeometryChanged.disconnect(self.screen_changed)
                screen.logicalDotsPerInchChanged.disconnect(self.screen_changed)
                screen.physicalDotsPerInchChanged.disconnect(self.screen_changed)
        self.screens.clear()
