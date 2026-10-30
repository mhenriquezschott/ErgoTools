"""Width-adaptive alphabet navigation with a restrained in-place hover effect.

Presentation layer. A strip fills its parent's available width without fixed letter
sizes or layout changes on hover. The caller owns filtering and selection semantics.
"""

from collections.abc import Callable
from string import ascii_uppercase

from PyQt5.QtCore import QSignalBlocker
from PyQt5.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class AlphabetNavigation(QWidget):
    """Fit initials to the selector width with restrained in-place enlargement."""

    def __init__(self, all_caption: str, selected: Callable[[str], None]) -> None:
        """Construct an exclusive alphabet strip without imposing a fixed width.

        Args:
            all_caption: Localized All label; its stable identity remains All.
            selected: Host callback receiving All or an ASCII initial.

        Returns:
            None; construction invokes no filtering or project action.
        """
        super().__init__()
        self.setMinimumWidth(0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.buttons: dict[str, QPushButton] = {}
        self.group = QButtonGroup(self)
        for token in ("All", *ascii_uppercase):
            button = QPushButton(all_caption if token == "All" else token)
            button.setObjectName("copyAlphabetButton")
            button.setCheckable(True)
            button.setMinimumWidth(0)
            button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.group.addButton(button)
            button.clicked.connect(lambda _checked, value=token: selected(value))
            layout.addWidget(button, 3 if token == "All" else 1)
            self.buttons[token] = button
        self.buttons["All"].setChecked(True)
        self.setStyleSheet(
            "QPushButton#copyAlphabetButton { padding: 0; min-width: 0; } "
            "QPushButton#copyAlphabetButton:hover:enabled { font-size: 16px; "
            "background: #DDF3F5; color: #0B326C; }"
            "QPushButton#copyAlphabetButton:disabled { color: #C7D0D7; "
            "background: transparent; font-size: 11px; }"
        )

    def set_available(self, initials: frozenset[str], selected: str = "All") -> None:
        """Match source-catalog availability without filtering or changing selection.

        Args:
            initials: Available uppercase ASCII initials, independent of current filter.
            selected: Current alphabet filter, or All for the unfiltered catalog.

        Returns:
            None; empty initials disable letters while All remains a filter reset.
        """
        for token, button in self.buttons.items():
            with QSignalBlocker(button):
                button.setChecked(token == selected)
            button.setEnabled(token == "All" or token in initials)
