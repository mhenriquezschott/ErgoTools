"""Native checkable import-row header without inserting fake source data columns.

Presentation layer. The panel owns row inclusion and source indices. This header
only paints native checkboxes/row numbers and emits click intent; source cells,
column mappings, file readers and project ownership stay unchanged.
"""

from collections.abc import Callable

from PyQt5.QtCore import QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QMouseEvent, QPainter
from PyQt5.QtWidgets import QHeaderView, QStyle, QStyleOptionButton, QWidget


class ImportRowHeader(QHeaderView):
    """Offer an obvious include checkbox next to each original source-row number."""

    toggled = pyqtSignal(int)

    def __init__(
        self, parent: QWidget, state: Callable[[int], bool], label: Callable[[int], str]
    ) -> None:
        """Borrow current row presentation without owning any import selection state.

        Args:
            parent: Existing table owning this vertical header.
            state: Current included state for a visible table row; row zero means All.
            label: Localized mapping-row label or original source-row number.

        Returns:
            None; clicks emit row intent for panel-owned validation and preview updates.
        """
        super().__init__(Qt.Orientation.Vertical, parent)
        self.included_state, self.label = state, label
        self.setFixedWidth(108)
        self.setMinimumSectionSize(34)
        self.setDefaultSectionSize(36)
        self.setSectionsClickable(True)
        self.setToolTip(
            "Tick rows to import; untick notes, extra headers or unwanted tasks."
        )

    def paintSection(self, painter: QPainter | None, rect: QRect, index: int) -> None:  # noqa: N802 — Qt override
        """Draw the native checkbox and stable row label with readable contrast.

        Args:
            painter: Qt-owned header painter.
            rect: Visible logical-pixel header rectangle.
            index: Visible table row, with zero reserved for the mapping controls.

        Returns:
            None; painting never changes data, mappings or inclusion.
        """
        if painter is None:
            return
        painter.save()
        painter.fillRect(
            rect, QColor("#EAF3F7" if self.included_state(index) else "#F0F1F2")
        )
        option = QStyleOptionButton()
        option.rect = QRect(rect.x() + 7, rect.center().y() - 9, 18, 18)
        option.state = QStyle.StateFlag(
            QStyle.StateFlag.State_Enabled
            | (
                QStyle.StateFlag.State_On
                if self.included_state(index)
                else QStyle.StateFlag.State_Off
            )
        )
        style = self.style()
        if style is not None:
            style.drawControl(QStyle.ControlElement.CE_CheckBox, option, painter, self)
        painter.setPen(QColor("#0B326C" if self.included_state(index) else "#73818B"))
        painter.drawText(
            rect.adjusted(31, 0, -3, 0),
            Qt.AlignmentFlag.AlignVCenter,
            self.label(index),
        )
        painter.restore()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802 — Qt override
        """Toggle a row checkbox while retaining normal header range-selection gestures.

        Args:
            event: Original native pointer event.

        Returns:
            None; clicking the number still permits ordinary table row selection.
        """
        if (
            event is not None
            and event.button() == Qt.MouseButton.LeftButton
            and event.x() < 30
        ):
            row = self.logicalIndexAt(event.pos())
            if row >= 0:
                self.toggled.emit(row)
            event.accept()
            return
        super().mousePressEvent(event)
