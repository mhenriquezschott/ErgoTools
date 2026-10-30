"""Animated height disclosure without owning assessment state or persistence.

A clipped QWidget reveals its existing content. Repeated projections do not restart
motion; callers settle project changes immediately and animate explicit user actions.
"""

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class ExpandableSection(QWidget):
    """Reveal one content widget while allowing the containing layout to grow."""

    def __init__(self, content: QWidget) -> None:
        """Adopt existing content in an initially hidden, height-clipped container.

        Args:
            content: Existing presentation widget; no data is loaded or selected here.

        Returns:
            None; the section starts collapsed and owns its animation lifetime.
        """
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content)
        self.content = content
        self.animation = QPropertyAnimation(self, b"maximumHeight", self)
        self.animation.setDuration(190)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.animation.finished.connect(self._finished)
        self.expanded = False
        self._unconstrained_height = self.maximumHeight()
        self.setMaximumHeight(0)
        self.hide()

    def set_expanded(self, expanded: bool, *, animate: bool) -> None:
        """Reveal/collapse from the current height, including reversed motion.

        Args:
            expanded: Accepted disclosure state, independent of source selection.
            animate: True for explicit user motion; False settles immediately.

        Returns:
            None; animation changes layout height only and writes no preferences.
        """
        self.animation.stop()
        current = self.height() if not self.isHidden() else 0
        self.expanded = expanded
        target = self.content.sizeHint().height() if expanded else 0
        if not animate:
            self.setMaximumHeight(self._unconstrained_height if expanded else 0)
            self.setVisible(expanded)
            return
        self.setMaximumHeight(current)
        self.show()
        self.animation.setStartValue(current)
        self.animation.setEndValue(target)
        self.animation.start()

    def _finished(self) -> None:
        """Remove a collapsed section after the final frame without touching its data.

        Args:
            None.

        Returns:
            None; expansion releases the height cap; collapsed content hides.
        """
        if self.expanded:
            self.setMaximumHeight(self._unconstrained_height)
        else:
            self.hide()
