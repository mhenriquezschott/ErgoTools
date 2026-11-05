"""Responsive local-clock annotations shared by entered and solved rotation matrices.

Presentation layer. Uses the existing minute projection and ShiftClock formatter; no
clock data is inferred, saved or passed back to the planning model. Width checks never
expand columns or introduce a scrollbar merely to show a time annotation.
"""

from PyQt5.QtCore import QEvent, QObject, QTimer
from PyQt5.QtWidgets import QTableWidget

from ergotools.application.rotation_timing import ShiftClock
from ergotools.domain.rotation_scenario import RotationInputs


class RotationBlockHeaders(QObject):
    """Add full from/to labels when all block columns can display them comfortably."""

    def __init__(self, table: QTableWidget) -> None:
        """Observe the owned viewport and headers using one coalesced refresh.

        Args:
            table: Host-owned input or read-only schedule table.

        Returns:
            None; this helper owns no project state or column sizing policy.
        """
        super().__init__(table)
        self.table = table
        self.base: tuple[str, ...] = ()
        self.ranges: tuple[str, ...] = ()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh)
        header = table.horizontalHeader()
        assert header is not None
        header.sectionResized.connect(self.queue_refresh)
        header.geometriesChanged.connect(self.queue_refresh)
        viewport = table.viewport()
        assert viewport is not None
        viewport.installEventFilter(self)

    def bind(self, inputs: RotationInputs, count: int) -> None:
        """Capture current base headers and exact productive clock intervals.

        Args:
            inputs: Exact displayed draft or frozen result input, with optional clock.
            count: Number of block columns following the worker column.

        Returns:
            None; missing timing/origin leaves the original headings unchanged.
        """
        self.base = tuple(
            item.text() if (item := self.table.horizontalHeaderItem(i + 1)) else ""
            for i in range(count)
        )
        self.ranges = ()
        if inputs.timing is not None and inputs.start_minute is not None:
            clock = ShiftClock(inputs.start_minute, inputs.timing.shift_minutes)
            self.ranges = tuple(
                " / ".join(
                    f"{clock.label(piece.start)} - {clock.label(piece.end)}"
                    for piece in block.pieces
                )
                for block in inputs.timing.blocks()
            )[:count]
        self.queue_refresh()

    def queue_refresh(self) -> None:
        """Coalesce resize notifications without changing the table's content widths.

        Args:
            None.

        Returns:
            None; the table owns this timer through the helper's lifetime.
        """
        self.timer.start(0)

    def refresh(self) -> None:
        """Show time ranges only when every block has enough real available width.

        Args:
            None.

        Returns:
            None; full ranges remain in header tooltips even when visually omitted.
        """
        header = self.table.horizontalHeader()
        assert header is not None
        metrics = header.fontMetrics()
        viewport = self.table.viewport()
        show = (
            bool(self.ranges)
            and viewport is not None
            and sum(self.table.columnWidth(c) for c in range(self.table.columnCount()))
            <= viewport.width()
            and len(self.ranges) == len(self.base)
            and all(
                self.table.columnWidth(i + 1) >= metrics.horizontalAdvance(value) + 28
                for i, value in enumerate(self.ranges)
            )
        )
        for i, base in enumerate(self.base):
            item = self.table.horizontalHeaderItem(i + 1)
            if item is None:
                continue
            interval = self.ranges[i] if i < len(self.ranges) else ""
            text = base + ("\n" + interval if show else "")
            if item.text() != text:
                item.setText(text)
            item.setToolTip(base + ("\n" + interval if interval else ""))

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Refit annotations after the real viewport changes, including drawer motion.

        Args:
            watched: Native viewport owned by the table.
            event: Native event, forwarded unchanged.

        Returns:
            False after queuing resize work so native table behavior proceeds.
        """
        if event is not None and event.type() == QEvent.Type.Resize:
            self.queue_refresh()
        return super().eventFilter(watched, event)
