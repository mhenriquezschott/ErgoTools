"""Capture explicit mouse tab intent before normal Qt source selection runs.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QTabBar


class ToolTabFocus(QObject):
    """Observe accepted tab intent without consuming Qt's normal tab handling."""

    def __init__(self, tabs: QTabBar, begin: Callable[[], None]) -> None:
        """Observe the existing tab bar; programmatic changes bypass this filter.

        Args:
            tabs: Existing integrated tool tab bar to observe without consuming normal
                Qt selection.
            begin: Callback marking explicit mouse tab intent before dirty-source
                selection policy runs.

        Returns:
            None.
        """
        super().__init__(tabs)
        self._tabs = tabs
        self._begin = begin
        tabs.installEventFilter(self)

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Defer focus only for a left click on an enabled, different tab.

        Args:
            watched: QObject receiving the event; may be None in direct defensive calls.
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            True only when this filter explicitly consumes the event; otherwise the
            normal Qt base-filter result.
        """
        if (
            isinstance(event, QMouseEvent)
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            index = self._tabs.tabAt(event.pos())
            if (
                index >= 0
                and index != self._tabs.currentIndex()
                and self._tabs.isTabEnabled(index)
            ):
                self._begin()
        return super().eventFilter(watched, event)
