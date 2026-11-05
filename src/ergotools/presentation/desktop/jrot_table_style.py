"""Consistent readable headers and row spacing for guided rotation tables.

Presentation layer. Apply local geometry/typography only; risk cell colors, data,
selection, column ownership and project history remain with each table's host.
"""

from PyQt5.QtCore import QModelIndex, QSize, Qt
from PyQt5.QtWidgets import (
    QStyleOptionViewItem,
    QTableWidget,
    QTreeWidget,
)

from ergotools.presentation.desktop.table_presentation import ReadableCellDelegate


class RotationCatalogRowDelegate(ReadableCellDelegate):
    """Increase catalog row height while preserving measured text/icon/check width."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: N802 - Qt override
        """Retain the native width required for a complete identifier and its icons.

        Args:
            option: Host-native font, decoration and checkbox styling.
            index: Group or selectable leaf being measured.

        Returns:
            Native content width with a 36px leaf or 28px hierarchy-row minimum.
        """
        size = super().sizeHint(option, index)
        leaf = isinstance(index.data(Qt.ItemDataRole.UserRole), str)
        size.setHeight(max(size.height(), 36 if leaf else 28))
        return size


def style_rotation_table(table: QTableWidget | QTreeWidget) -> None:
    """Give rotation tables bold full-height headings and comfortable row minima.

    Args:
        table: Owned guided table or catalog tree; no global stylesheet is changed.

    Returns:
        None; content sizing and responsive width allocation remain host-owned.
    """
    header = (
        table.header() if isinstance(table, QTreeWidget) else table.horizontalHeader()
    )
    assert header is not None
    font = header.font()
    font.setBold(True)
    header.setFont(font)
    header.setMinimumHeight(42)
    header.setStyleSheet(
        "QHeaderView::section { background:#EAF3F7; color:#0B326C; "
        "font-weight:700; padding:6px; border:1px solid #D5DEE5; }"
    )
    table.setAlternatingRowColors(True)
    if isinstance(table, QTreeWidget):
        table.setItemDelegate(RotationCatalogRowDelegate(table))
    else:
        table.setItemDelegate(ReadableCellDelegate(table))
        vertical = table.verticalHeader()
        assert vertical is not None
        vertical.setFixedWidth(
            max(
                44,
                vertical.fontMetrics().horizontalAdvance(str(max(1, table.rowCount())))
                + 20,
            )
        )
        vertical.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        vertical.setMinimumSectionSize(36)
        vertical.setDefaultSectionSize(36)
