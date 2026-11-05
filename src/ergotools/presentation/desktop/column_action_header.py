"""Reusable table-header actions aligned with their actual column geometry.

Presentation layer. Hosts own semantics and enablement; this header only positions
compact native buttons beneath measured icon/label rows, including horizontal scrolling.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import QIcon, QPainter, QResizeEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QStyle,
    QStyleOptionHeader,
    QToolButton,
    QWidget,
)


class ColumnActionHeader(QHeaderView):
    """Place compact actions inside selected header sections without a fake data row."""

    def __init__(
        self,
        parent: QWidget,
        actions: Mapping[int, tuple[tuple[str, str, Callable[[], None]], ...]],
    ) -> None:
        """Create column-aligned action rows controlled by the owning table/dialog.

        Args:
            parent: Existing table retaining native header ownership.
            actions: Logical column to caption, tooltip and callback tuples.

        Returns:
            None; callbacks run only on explicit button activation, never on layout.
        """
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setFixedHeight(68)
        self.setDefaultAlignment(
            Qt.AlignmentFlag(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        )
        self.hosts: dict[int, QWidget] = {}
        self.buttons: dict[int, tuple[QToolButton, ...]] = {}
        for column, choices in actions.items():
            host = QWidget(self.viewport())
            row = QHBoxLayout(host)
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(4)
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            buttons = []
            for caption, tooltip, callback in choices:
                button = QToolButton(host)
                button.setText(caption)
                button.setToolTip(tooltip)
                button.setAutoRaise(False)
                button.setStyleSheet(
                    "QToolButton {font-size:11px;padding:2px 6px;min-width:25px;}"
                )
                button.clicked.connect(callback)
                row.addWidget(button)
                buttons.append(button)
            self.hosts[column] = host
            self.buttons[column] = tuple(buttons)
        self.sectionMoved.connect(self.position_actions)
        self.sectionResized.connect(self.position_actions)
        self.geometriesChanged.connect(self.position_actions)

    def sectionSizeFromContents(self, logical_index: int) -> QSize:  # noqa: N802 — Qt override
        """Reserve complete single-line captions, visible icons and bulk controls.

        Args:
            logical_index: Model column whose header is being measured.

        Returns:
            Native section size widened for the icon/title row and action buttons.
            Sizing does not mutate model labels or restriction values.
        """
        size = super().sectionSizeFromContents(logical_index)
        model = self.model()
        if model is None:
            return size
        title = str(model.headerData(logical_index, self.orientation()) or "")
        icon = model.headerData(
            logical_index, self.orientation(), Qt.ItemDataRole.DecorationRole
        )
        width = self.fontMetrics().horizontalAdvance(title) + 24
        if isinstance(icon, QIcon) and not icon.isNull():
            width += self.iconSize().width() + 8
        host = self.hosts.get(logical_index)
        if host is not None:
            width = max(width, host.sizeHint().width() + 12)
        return QSize(max(size.width(), width), self.height())

    def paintSection(  # noqa: N802 — Qt override
        self, painter: QPainter | None, rect: QRect, logical_index: int
    ) -> None:
        """Paint a centered icon/title row above independent native action buttons.

        Args:
            painter: Qt-owned painter, never retained after this call.
            rect: Visible section rectangle in viewport coordinates.
            logical_index: Header model column; original labels remain accessible.

        Returns:
            None; native background/borders remain theme-owned. Icon and text share
            one 36px band instead of centering the icon over both header rows.
        """
        if painter is None or not rect.isValid():
            return
        model = self.model()
        if model is None:
            return
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.section = logical_index
        option.text = ""
        option.icon = QIcon()
        style = self.style()
        assert style is not None
        style.drawControl(QStyle.ControlElement.CE_Header, option, painter, self)
        title = str(model.headerData(logical_index, self.orientation()) or "")
        icon = model.headerData(
            logical_index, self.orientation(), Qt.ItemDataRole.DecorationRole
        )
        icon_width = (
            self.iconSize().width()
            if isinstance(icon, QIcon) and not icon.isNull()
            else 0
        )
        gap = 8 if icon_width else 0
        text_width = self.fontMetrics().horizontalAdvance(title)
        left = rect.x() + max(8, (rect.width() - icon_width - gap - text_width) // 2)
        painter.save()
        painter.setClipRect(rect.adjusted(4, 0, -4, 0))
        painter.setFont(self.font())
        painter.setPen(option.palette.color(option.palette.ButtonText))
        if isinstance(icon, QIcon) and icon_width:
            icon.paint(painter, QRect(left, rect.y() + 6, icon_width, 28))
        text_rect = QRect(
            left + icon_width + gap,
            rect.y() + 2,
            max(0, rect.right() - left - icon_width - gap - 6),
            36,
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, title)
        painter.restore()

    def position_actions(self) -> None:
        """Follow section moves/resizes/scrolling using logical viewport positions.

        Args:
            None.

        Returns:
            None; native column labels, sorting and model data remain unchanged.
        """
        for column, host in self.hosts.items():
            host.setGeometry(
                self.sectionViewportPosition(column) + 1,
                self.height() - 32,
                max(0, self.sectionSize(column) - 2),
                28,
            )
            host.setVisible(not self.isSectionHidden(column))

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802 — Qt override
        """Keep action rows aligned after a native header viewport resize.

        Args:
            event: Native resize event forwarded unchanged.

        Returns:
            None; no action is invoked or project value accepted.
        """
        super().resizeEvent(event)
        self.position_actions()
