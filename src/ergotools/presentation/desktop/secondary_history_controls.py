"""Shared compact icon/caption history controls for secondary ErgoTools windows.

Presentation only. QAction retains shortcuts, enablement, tooltips and replay ownership;
the main application's existing toolbar is deliberately outside this layout helper.
"""

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QHBoxLayout, QToolButton


def configure_history_button(button: QToolButton) -> None:
    """Apply the Job icon/caption treatment without changing its action or shortcuts.

    Args:
        button: Secondary-window owned control, already bound to its QAction.

    Returns:
        None; mouse focus leaves text editing, while keyboard typing stays native.
    """
    button.setObjectName("secondaryHistoryButton")
    button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    button.setIconSize(QSize(28, 28))
    button.setFixedSize(58, 58)
    button.setStyleSheet(
        "QToolButton { color: #0B326C; background: white; border: 0; "
        "border-radius: 5px; padding: 3px; font: 11px 'Segoe UI'; }"
        "QToolButton:hover { background: #EAF7F8; }"
        "QToolButton:disabled { color: #8998A3; }"
    )


def add_history_buttons(row: QHBoxLayout, undo: QToolButton, redo: QToolButton) -> None:
    """Place a neighboring pair in a title row, independently of its other spacing.

    Args:
        row: Existing window title layout, with its own title/stretch already present.
        undo: Window-owned Undo control.
        redo: Window-owned Redo control.

    Returns:
        None; no history state or main toolbar geometry is modified.
    """
    pair = QHBoxLayout()
    pair.setContentsMargins(0, 0, 0, 0)
    pair.setSpacing(1)
    for button in (undo, redo):
        configure_history_button(button)
        pair.addWidget(button)
    row.addLayout(pair)
