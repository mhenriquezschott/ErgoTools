"""Shared readable data-table presentation without data or document ownership.

Presentation layer. Numeric alignment, selection contrast and modest spare-space row
sizing are common to summary/review tables. Editors, risk thresholds and persistence
remain with their existing hosts. No value is inferred from formatting.
"""

import re

from PyQt5.QtCore import QModelIndex, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QPalette, QResizeEvent
from PyQt5.QtWidgets import (
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTreeWidget,
    QWidget,
)

# Whole numeric tokens: percentages, decimal commas and missing-value dashes.
_NUMBER = re.compile(r"(?:[+\u2212-]?\d+(?:[.,]\d+)?%?|—)")


def numeric_display(text: str) -> bool:
    """Identify a display token for alignment only, never parse a scientific input.

    Args:
        text: Already formatted cell text.

    Returns:
        True for one complete numeric or missing-value display token.
    """
    return _NUMBER.fullmatch(text.strip()) is not None


def table_text_color(background: QColor) -> QColor:
    """Choose light text on darker fills and navy on light/amber cells.

    Args:
        background: Actual painted opaque cell or selection color.

    Returns:
        Near-white for perceived brightness below 150/255; otherwise application navy.
        The threshold affects presentation only and is unrelated to risk classification.
    """
    brightness = (
        0.299 * background.red()
        + 0.587 * background.green()
        + 0.114 * background.blue()
    )
    return QColor("#FAFCFF" if brightness < 150 else "#082F49")


class ReadableCellDelegate(QStyledItemDelegate):
    """Draw numeric tokens centrally and keep text legible over colored selections."""

    def initStyleOption(  # noqa: N802 - Qt override
        self, option: QStyleOptionViewItem | None, index: QModelIndex
    ) -> None:
        """Apply shared contrast after native item foreground/background roles.

        Args:
            option: Qt-owned drawing option, or None as permitted by the binding.
            index: Read-only model cell.

        Returns:
            None; native selection and focus borders remain active.
        """
        if option is None:
            return
        super().initStyleOption(option, index)
        if numeric_display(option.text or ""):
            option.displayAlignment = Qt.AlignmentFlag.AlignCenter
            option.font.setBold(True)
        brush = QBrush(option.backgroundBrush)
        if brush.style() != Qt.BrushStyle.NoBrush:
            option.palette.setColor(
                QPalette.ColorRole.Text, table_text_color(brush.color())
            )
        option.palette.setColor(
            QPalette.ColorRole.HighlightedText,
            table_text_color(option.palette.color(QPalette.ColorRole.Highlight)),
        )


class AdaptiveTableWidget(QTableWidget):
    """Use spare table space without shrinking content or forcing extra scrollbars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Own a coalesced layout refresh after model or viewport geometry changes.

        Args:
            parent: Optional table lifetime owner.

        Returns:
            None; no application data or history is created.
        """
        super().__init__(parent)
        self.column_weights: tuple[int, ...] = ()
        self.column_minima: tuple[int, ...] = ()
        self._layout_timer = QTimer(self)
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self.fit_space)
        model = self.model()
        assert model is not None
        model.rowsInserted.connect(self.schedule_fit)
        model.modelReset.connect(self.schedule_fit)
        model.dataChanged.connect(self.schedule_fit)

    def schedule_fit(self) -> None:
        """Coalesce table rebuild notifications into one GUI-thread layout pass.

        Args:
            None.

        Returns:
            None; repeated cell updates do not cause repeated immediate resizing.
        """
        self._layout_timer.start(0)

    def set_column_weights(
        self, weights: tuple[int, ...], minima: tuple[int, ...]
    ) -> None:
        """Set explicit content-aware width priorities for the owning table.

        Args:
            weights: Nonnegative relative shares of spare width, one per column.
            minima: Readable minimum widths, one per column.

        Returns:
            None; a narrow viewport retains minima and ordinary horizontal scrolling.

        Raises:
            ValueError: Shapes differ from the model or a width/share is invalid.
        """
        if (
            len(weights) != self.columnCount()
            or len(minima) != self.columnCount()
            or any(w < 0 for w in weights)
            or any(m < 1 for m in minima)
        ):
            raise ValueError("Column layout must match the table.")
        self.column_weights, self.column_minima = weights, minima
        self.schedule_fit()

    def fit_space(self) -> None:
        """Expand rows moderately and distribute configured spare column width.

        Args:
            None.

        Returns:
            None; tall content retains its measured minimum and can scroll normally.
        """
        viewport = self.viewport()
        if viewport is None:
            return
        minima = tuple(max(42, self.sizeHintForRow(r)) for r in range(self.rowCount()))
        extra = (
            min(24, max(0, viewport.height() - sum(minima)) // len(minima))
            if minima
            else 0
        )
        for row, minimum in enumerate(minima):
            self.setRowHeight(row, minimum + extra)
        if len(self.column_minima) == self.columnCount() and self.column_minima:
            spare = max(0, viewport.width() - sum(self.column_minima))
            total = max(1, sum(self.column_weights))
            for column, minimum in enumerate(self.column_minima):
                self.setColumnWidth(
                    column, minimum + spare * self.column_weights[column] // total
                )

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        """Refit after a viewport change, including a drawer expansion.

        Args:
            event: Native resize event, forwarded unchanged.

        Returns:
            None; table selection and underlying values are preserved.
        """
        super().resizeEvent(event)
        if hasattr(self, "_layout_timer"):
            self.schedule_fit()


def install_readable_cells(table: QTableWidget | QTreeWidget) -> None:
    """Install shared numeric/contrast drawing on an owned data table or tree.

    Args:
        table: Host-owned view; editing and selection modes are untouched.

    Returns:
        None; the delegate is owned by its view.
    """
    table.setItemDelegate(ReadableCellDelegate(table))
