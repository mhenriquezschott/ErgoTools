"""Reusable clock timeline for explicit work blocks and shared breaks.

Presentation layer. Paint complete typed work/break timing at window scale. Visual
tools preview immutable proposals and emit only on release; Escape discards previews.
Hosts retain project history, acceptance and saving. No optimization runs here.
"""

from textwrap import fill

from PyQt5.QtCore import QEvent, QPoint, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QPolygon,
)
from PyQt5.QtWidgets import QWidget

from ergotools.application.rotation_segments import (
    move_timing_segment,
    resize_timing_boundary,
    segment_position,
    timing_segments,
)
from ergotools.application.rotation_timing import ShiftClock
from ergotools.application.rotation_timing_actions import (
    change_timing_break,
    draw_timing_break,
    join_timing_breaks,
    join_work_blocks,
    remove_work_block,
    split_work_block,
)
from ergotools.domain.language import Language
from ergotools.domain.rotation_timing import (
    RotationTiming,
)


def timing_action_cursor(tool: str) -> QCursor:
    """Draw distinct scissors, inward arrows or a removal cross over either bar color.

    Args:
        tool: Split, join or remove action; other names are rejected.

    Returns:
        Native bitmap cursor with a white visibility halo and central action hotspot.

    Raises:
        ValueError: The action has no custom cursor.
    """
    path = QPainterPath()
    if tool == "split":
        path.addEllipse(QRectF(2, 3, 8, 8))
        path.addEllipse(QRectF(2, 23, 8, 8))
        path.moveTo(9, 10)
        path.lineTo(29, 30)
        path.moveTo(9, 24)
        path.lineTo(29, 4)
    elif tool == "join":
        for start, tip, wing in ((3, 15, 10), (33, 21, 26)):
            path.moveTo(start, 17)
            path.lineTo(tip, 17)
            path.moveTo(wing, 11)
            path.lineTo(tip, 17)
            path.lineTo(wing, 23)
    elif tool == "remove":
        path.moveTo(8, 7)
        path.lineTo(28, 27)
        path.moveTo(8, 27)
        path.lineTo(28, 7)
    else:
        raise ValueError("Unsupported timing action cursor.")
    size = 31 if tool in ("split", "remove") else 36
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 36, size / 36)
    for color, width in (
        ("white", 5),
        ("#B52B35" if tool == "remove" else "#0B326C", 2),
    ):
        painter.setPen(
            QPen(QColor(color), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        )
        painter.drawPath(path)
    painter.end()
    return QCursor(pixmap, round(18 * size / 36), round(17 * size / 36))


class RotationTimeline(QWidget):
    """Scale relative minutes into work pieces without assigning work during breaks.

    Attributes:
        timing_changed: Complete proposed timing emitted once per completed gesture.
        snap_minutes: Positive minute increment used by pointer/keyboard gestures.
    """

    timing_changed = pyqtSignal(object)
    selection_changed = pyqtSignal(str, int)
    tool_changed = pyqtSignal(str)
    operation_error = pyqtSignal(str)

    def __init__(
        self, parent: QWidget | None = None, *, language: Language = Language.ENGLISH
    ) -> None:
        """Create an empty, keyboard-accessible drawing surface.

        Args:
            parent: Owner of this reusable widget and its native events.
            language: Localized tool and segment descriptions.

        Returns:
            None; no timing data or history is created.
        """
        super().__init__(parent)
        self.language = language
        self._hover_minute: int | None = None
        self._hover_segment: tuple[str, int] | None = None
        self.tool = "select"
        self.selection: tuple[str, int] | None = None
        self._gesture: tuple[str, int, int] | None = None
        self._gesture_error = ""
        self._origin_selection: tuple[str, int] | None = None
        self.timing: RotationTiming | None = None
        self.clock = ShiftClock(0, 1440)
        self.snap_minutes = 5
        self._drag_origin: RotationTiming | None = None
        self._boundary: int | None = None
        self._press_x = 0.0
        self._action_cursors = {
            tool: timing_action_cursor(tool) for tool in ("split", "join", "remove")
        }
        self.setMinimumSize(540, 170)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(
            self.text(
                "Rotation work and break timeline", "Cronograma de trabajo y descansos"
            )
        )

    def set_timing(self, timing: RotationTiming, clock: ShiftClock) -> None:
        """Project accepted/restored state, cancelling any obsolete drag preview.

        Args:
            timing: Complete relative-minute work/break plan.
            clock: Current Shift clock origin with the same elapsed span.

        Returns:
            None; no edit signal is emitted on projection.
        """
        self.timing, self.clock = timing, clock
        self._drag_origin = None
        self._gesture = None
        if self.selection is not None:
            kind, index = self.selection
            if index >= len(timing.breaks if kind == "break" else timing.block_minutes):
                self.selection = None
        if self._boundary is not None and self._boundary not in {
            i for i, _ in self._cuts()
        }:
            self._boundary = None
        self.update()

    def _x(self, minute: int) -> float:
        """Project a valid elapsed minute into the current drawable rectangle.

        Args:
            minute: Whole-minute offset in the displayed shift.

        Returns:
            Logical pixel X coordinate with fixed readable axis margins.
        """
        span = self.timing.shift_minutes if self.timing is not None else 1
        return 48 + minute / span * max(1, self.width() - 96)

    def _minute(self, x: float) -> int:
        """Project a pointer coordinate to clamped snapped elapsed minutes.

        Args:
            x: Logical widget pixel coordinate.

        Returns:
            Whole-minute shift offset using the selected snap interval.
        """
        span = self.timing.shift_minutes if self.timing is not None else 1
        value = (x - 48) / max(1, self.width() - 96) * span
        snapped = round(value / max(1, self.snap_minutes)) * max(1, self.snap_minutes)
        return min(span, max(0, snapped))

    def _cuts(self) -> tuple[tuple[int, int], ...]:
        """Read every interior work/break edge without creating phantom break work.

        Args:
            None.

        Returns:
            Interior segment boundary index and its shift-relative clock offset.
        """
        if self.timing is None:
            return ()
        values = timing_segments(self.timing)
        return tuple(
            (index, sum(s.minutes for s in values[:index]))
            for index in range(1, len(values))
        )

    def paintEvent(self, event: QPaintEvent | None) -> None:  # noqa: N802 — Qt override
        """Paint work pieces, pauses, clock ticks and accessible boundary handles.

        Args:
            event: Native paint region, or None for an explicit full repaint.

        Returns:
            None; painting never accepts timing or project data.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#F4F7F9"))
        timing = self.timing
        if timing is None:
            return
        selected_minute = self.selected_boundary_minute()
        selected_text = (
            self.clock.label(selected_minute) if selected_minute is not None else ""
        )
        selected_width = painter.fontMetrics().horizontalAdvance(selected_text) + 18
        selected_x = self._x(selected_minute) if selected_minute is not None else 0
        selected_label = QRectF(
            max(0, min(self.width() - selected_width, selected_x - selected_width / 2)),
            110,
            selected_width,
            24,
        )
        for index in range(5):
            minute = round(index * timing.shift_minutes / 4)
            x = self._x(minute)
            painter.setPen(QColor("#526E82"))
            painter.drawLine(QPoint(round(x), 26), QPoint(round(x), 108))
            tick_label = QRectF(x - 42, 110, 84, 24)
            if selected_minute is None or not tick_label.intersects(selected_label):
                painter.drawText(
                    tick_label, Qt.AlignmentFlag.AlignCenter, self.clock.label(minute)
                )
        for pause_index, pause in enumerate(timing.breaks):
            left, right = self._x(pause.interval.start), self._x(pause.interval.end)
            rectangle = QRectF(left, 35, right - left, 62)
            painter.fillRect(rectangle, QColor("#D5DEE5"))
            if self._hover_segment == ("break", pause_index):
                painter.setPen(QPen(QColor("#08A9B5"), 2))
                painter.drawRect(rectangle.adjusted(1, 1, -1, -1))
            if self.selection == ("break", pause_index):
                painter.setPen(QPen(QColor("#E79422"), 3))
                painter.drawRect(rectangle.adjusted(1, 1, -1, -1))
            if right - left > 36:
                painter.setPen(QColor("#355063"))
                painter.drawText(
                    QRectF(left, 35, right - left, 62),
                    Qt.AlignmentFlag.AlignCenter,
                    "||",
                )
        for block in timing.blocks():
            for piece in block.pieces:
                left, right = self._x(piece.start), self._x(piece.end)
                painter.fillRect(
                    QRectF(left, 35, right - left, 62),
                    QColor("#073E68"),
                )
                painter.setPen(QPen(QColor("#FFFFFF"), 1))
                painter.drawRect(QRectF(left, 35, right - left, 62))
                if self._hover_segment == ("block", block.index):
                    painter.setPen(QPen(QColor("#08A9B5"), 2))
                    painter.drawRect(QRectF(left + 1, 36, right - left - 2, 60))
                if self.selection == ("block", block.index):
                    painter.setPen(QPen(QColor("#E79422"), 3))
                    painter.drawRect(QRectF(left + 1, 36, right - left - 2, 60))
                if right - left > 30:
                    painter.setPen(QColor("white"))
                    painter.drawText(
                        QRectF(left, 35, right - left, 62),
                        Qt.AlignmentFlag.AlignCenter,
                        f"{block.index + 1}",
                    )
        for boundary, minute in self._cuts():
            x = round(self._x(minute))
            painter.setPen(
                QPen(QColor("#E79422" if boundary == self._boundary else "#08A9B5"), 3)
            )
            painter.drawLine(QPoint(x, 26), QPoint(x, 102))
            painter.setBrush(QColor("#0B326C"))
            painter.drawPolygon(
                QPolygon([QPoint(x - 6, 18), QPoint(x + 6, 18), QPoint(x, 27)])
            )

        if selected_minute is not None:
            painter.setPen(QPen(QColor("#E79422"), 1))
            painter.setBrush(QColor("#FFF6E8"))
            painter.drawRoundedRect(selected_label, 3, 3)
            painter.setPen(QColor("#0B326C"))
            painter.drawText(
                selected_label, Qt.AlignmentFlag.AlignCenter, selected_text
            )

        if self._hover_minute is not None and self.tool in ("split", "draw_break"):
            x = self._x(self._hover_minute)
            painter.setPen(QPen(QColor("#08A9B5"), 2, Qt.PenStyle.DashLine))
            painter.drawLine(QPoint(round(x), 20), QPoint(round(x), 136))
            label = QRectF(max(0, min(self.width() - 110, x - 55)), 140, 110, 24)
            painter.fillRect(label, QColor("#EAF7F8"))
            painter.setPen(QColor("#0B326C"))
            painter.drawText(
                label,
                Qt.AlignmentFlag.AlignCenter,
                self.clock.label(self._hover_minute),
            )

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802 — Qt override
        """Begin segment selection or one preview-only visual editing gesture.

        Args:
            event: Native pointer event in logical widget coordinates.

        Returns:
            None; no project change is emitted on press.
        """
        if (
            event is not None
            and event.button() == Qt.MouseButton.LeftButton
            and self.timing is not None
        ):
            self.setFocus()
            minute = self._minute(event.x())
            self._hover_minute = minute
            hit = self.segment_at(minute)
            if hit is not None:
                self.select_segment(*hit)
            cut = min(
                self._cuts(), key=lambda c: abs(self._x(c[1]) - event.x()), default=None
            )
            self._gesture_error = ""
            self._origin_selection = self.selection
            self._press_x = event.x()
            if (
                self.tool in ("select", "move")
                and cut is not None
                and abs(self._x(cut[1]) - event.x()) <= 10
            ):
                self._boundary = cut[0]
                self._gesture = None
                self._drag_origin = self.timing
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif self.tool == "move" and hit is not None:
                self._gesture = ("move:" + hit[0], hit[1], minute)
                self._drag_origin = self.timing
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            elif self.tool == "draw_break" and hit is not None and hit[0] == "block":
                self._gesture = ("draw", -1, minute)
                self._drag_origin = self.timing
            elif self.tool in ("split", "join", "remove") and hit is not None:
                self._gesture = (self.tool + ":" + hit[0], hit[1], minute)
                self._drag_origin = self.timing
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802 — Qt override
        """Preview snapped drag geometry or show context-specific clock information.

        Args:
            event: Native pointer event; None leaves state unchanged.

        Returns:
            None; a drag is still unaccepted until release.
        """
        if event is None or self.timing is None:
            return
        self._hover_minute = self._minute(event.x())
        self._hover_segment = self.segment_at(self._hover_minute)
        self.update()
        if self._drag_origin is not None:
            self.preview_at(event.x())
            self.setCursor(self.cursor_at(event.x(), dragging=True))
            return
        self.setCursor(self.cursor_at(event.x()))
        self.setToolTip(self.tooltip_at(event.x()))

    def selected_boundary_minute(self) -> int | None:
        """Read the selected edge's current clock offset, including drag previews.

        Args:
            None.

        Returns:
            Relative whole minute, or None when no valid interior edge is selected.
        """
        return next(
            (minute for index, minute in self._cuts() if index == self._boundary), None
        )

    def tooltip_at(self, x: float) -> str:
        """Describe the hovered interval or editable boundary and the current action.

        Args:
            x: Widget-local horizontal pointer position.

        Returns:
            Localized plain text with clock range, minutes and relevant instructions;
            empty text when no timing exists.
        """
        timing = self.timing
        hit = self.segment_at(self._minute(x))
        if timing is None or hit is None:
            return ""
        cut = next(
            (minute for _, minute in self._cuts() if abs(self._x(minute) - x) <= 10),
            None,
        )
        if cut is not None and self.tool in ("select", "move"):
            return (
                self.text("Boundary", "Límite")
                + f": {self.clock.label(cut)}\n"
                + fill(
                    self.text(
                        "Drag to resize the two neighboring intervals. Select, then "
                        "use Left/Right to adjust by the snap interval.",
                        "Arrastre para redimensionar los dos intervalos vecinos. "
                        "Seleccione y use Izquierda/Derecha para ajustar según el "
                        "intervalo de ajuste.",
                    ),
                    width=68,
                )
            )
        kind, index = hit
        if kind == "break":
            pause = timing.breaks[index]
            start, end = pause.interval.start, pause.interval.end
            title = self.text("Break", "Descanso") + f" {index + 1}"
            if pause.name:
                title += f" — {pause.name}"
        else:
            block = timing.blocks()[index]
            start, end = block.pieces[0].start, block.pieces[-1].end
            title = self.text("Work block", "Bloque de trabajo") + f" {index + 1}"
        details = (
            f"{title}\n{self.clock.label(start)} - {self.clock.label(end)}"
            f" · {end - start} min"
        )
        hints = {
            "select": self.text(
                "Click to select. Drag an edge to resize neighboring intervals.",
                "Haga clic para seleccionar. Arrastre un límite para redimensionar "
                "los intervalos vecinos.",
            ),
            "move": self.text(
                "Drag to move this interval; drag an edge to resize. Escape cancels "
                "the preview.",
                "Arrastre para mover este intervalo o su límite para "
                "redimensionarlo. Escape cancela la vista previa.",
            ),
            "split": self.text(
                "Click at the clock guide to split this work block.",
                "Haga clic en la guía horaria para dividir este bloque de trabajo.",
            )
            if kind == "block"
            else self.text(
                "Split applies to work blocks. Use Move / resize to adjust this break.",
                "Dividir se aplica a bloques de trabajo. Use Mover / redimensionar "
                "para ajustar este descanso.",
            ),
            "draw_break": self.text(
                "Drag across work to draw a break. A click adds up to 15 minutes.",
                "Arrastre sobre el trabajo para dibujar un descanso. Un clic añade "
                "hasta 15 minutos.",
            )
            if kind == "block"
            else self.text(
                "This is already a break. Use Move / resize to adjust it.",
                "Este intervalo ya es un descanso. Use Mover / redimensionar para "
                "ajustarlo.",
            ),
            "join": self.text(
                "Join adjacent work blocks at their shared boundary. A break between "
                "blocks prevents joining.",
                "Una bloques de trabajo contiguos en su límite compartido. Un descanso "
                "entre los bloques impide unirlos.",
            )
            if kind == "block"
            else self.text(
                "Click to join this break with a touching break. Separated breaks "
                "cannot be joined.",
                "Haga clic para unir este descanso con uno contiguo. No se pueden "
                "unir descansos separados.",
            ),
            "remove": self.text(
                "Click to remove this interval. Its time extends the immediate "
                "neighbors; at a shift edge, the sole neighbor absorbs it.",
                "Haga clic para eliminar este intervalo. Su tiempo amplía los "
                "vecinos inmediatos; en un extremo del turno, lo absorbe el único "
                "vecino.",
            ),
        }
        if self.tool == "remove" and kind == "block" and len(timing.block_minutes) == 1:
            return (
                details
                + "\n"
                + self.text(
                    "The last work block cannot be removed.",
                    "No se puede eliminar el último bloque de trabajo.",
                )
            )
        return details + "\n" + fill(hints[self.tool], width=68)

    def preview_at(self, x: float) -> None:
        """Project a visual tool or boundary drag, including final release position.

        Args:
            x: Last logical pointer coordinate, relative to this widget.

        Returns:
            None; tiny click jitter and an unchanged boundary retain the original mode.
        """
        origin = self._drag_origin
        if origin is not None and self._gesture is not None:
            self._preview_operation(x)
            return
        if origin is None or self._boundary is None:
            return
        if abs(x - self._press_x) < 2:
            self.timing = origin
        else:
            values = timing_segments(origin)
            before = sum(s.minutes for s in values[: self._boundary - 1]) + 1
            after = sum(s.minutes for s in values[: self._boundary + 1]) - 1
            candidate = resize_timing_boundary(
                origin, self._boundary, min(after, max(before, self._minute(x)))
            )
            self.timing = origin if candidate == origin else candidate
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802 — Qt override
        """Finish one gesture and emit one complete proposal only when it changed.

        Args:
            event: Native pointer release, or None for no action.

        Returns:
            None; host accepts or rejects the complete proposal through shared history.
        """
        if event is not None:
            self._hover_minute = self._minute(event.x())
        original = self._drag_origin
        origin_selection = self._origin_selection
        if original is not None and event is not None:
            self.preview_at(event.x())
        self._drag_origin = None
        self._gesture = None
        self.setCursor(
            self.cursor_at(event.x()) if event is not None else self.tool_cursor()
        )
        if original is not None and self._gesture_error:
            self.operation_error.emit(self._gesture_error)
        if original is not None and self.timing is not None and self.timing != original:
            proposed = self.timing
            self.timing_changed.emit(proposed)
            if self.timing != proposed:
                self.selection = origin_selection
            if self.selection is not None:
                self.selection_changed.emit(*self.selection)
            self.update()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802 — Qt override
        """Cancel, return to Select, remove a segment or nudge a selected boundary.

        Args:
            event: Native key; other keys retain standard QWidget handling.

        Returns:
            None; Escape emits no edit and each accepted arrow is one gesture.
        """
        if (
            event is not None
            and event.key() == Qt.Key.Key_Escape
            and self._drag_origin is not None
        ):
            self.timing, self._drag_origin = self._drag_origin, None
            self._gesture = None
            self._gesture_error = ""
            self.selection = self._origin_selection
            self.set_tool("select")
            if self.selection is not None:
                self.selection_changed.emit(*self.selection)
            self.update()
            event.accept()
            return
        if event is not None and event.key() == Qt.Key.Key_Escape:
            self.set_tool("select")
            event.accept()
            return
        if (
            event is not None
            and event.key() == Qt.Key.Key_Delete
            and self.selection is not None
            and self.timing is not None
        ):
            try:
                kind, index = self.selection
                candidate = (
                    change_timing_break(self.timing, index, None)
                    if kind == "break"
                    else remove_work_block(self.timing, index)
                )
                self.timing_changed.emit(candidate)
            except ValueError as error:
                self.operation_error.emit(str(error))
            event.accept()
            return
        if (
            event is not None
            and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right)
            and self.timing is not None
            and self._boundary is not None
        ):
            offset = sum(
                s.minutes for s in timing_segments(self.timing)[: self._boundary]
            )
            delta = self.snap_minutes * (-1 if event.key() == Qt.Key.Key_Left else 1)
            try:
                proposed = resize_timing_boundary(
                    self.timing, self._boundary, offset + delta
                )
            except ValueError:
                event.accept()
                return
            self.timing_changed.emit(proposed)
            event.accept()
            return
        super().keyPressEvent(event)

    def text(self, english: str, spanish: str) -> str:
        """Choose timeline captions without changing literal break names.

        Args:
            english: English text.
            spanish: Spanish text.

        Returns:
            Text in the timeline host language.
        """
        return spanish if self.language is Language.SPANISH else english

    def set_tool(self, tool: str) -> None:
        """Select a persistent visual tool, cancelling an unfinished gesture safely.

        Args:
            tool: select, split, draw_break, move, join or remove.

        Returns:
            None; changing tools creates no project-history edit.

        Raises:
            ValueError: Tool is unsupported.
        """
        if tool not in ("select", "split", "draw_break", "move", "join", "remove"):
            raise ValueError("Unsupported timing tool.")
        if self._drag_origin is not None:
            self.timing = self._drag_origin
            self.selection = self._origin_selection
        self._drag_origin, self._gesture = None, None
        self.tool = tool
        if tool not in ("select", "move"):
            self._boundary = None
        self.setCursor(self.tool_cursor())
        self.setToolTip(
            self.tooltip_at(self._x(self._hover_minute))
            if self._hover_minute is not None
            else ""
        )
        self.tool_changed.emit(tool)
        self.update()

    def tool_cursor(self) -> QCursor | Qt.CursorShape:
        """Read a cursor that identifies the selected persistent editing tool.

        Args:
            None.

        Returns:
            Scissors for Split, inward arrows for Join, red cross for Remove,
            crosshair for Draw break, or the ordinary selection arrow.
        """
        if self.tool in self._action_cursors:
            return self._action_cursors[self.tool]
        return (
            Qt.CursorShape.CrossCursor
            if self.tool == "draw_break"
            else Qt.CursorShape.ArrowCursor
        )

    def cursor_at(
        self, x: float, *, dragging: bool = False
    ) -> QCursor | Qt.CursorShape:
        """Distinguish pause movement, edge resizing and ordinary selection.

        Args:
            x: Local logical pointer position.
            dragging: True while a native gesture owns the pointer.

        Returns:
            Horizontal resize at editable edges, open/closed hand on break bodies,
            otherwise the selected tool's truthful cursor.
        """
        if dragging and self._drag_origin is not None:
            return (
                Qt.CursorShape.ClosedHandCursor
                if self._gesture is not None and self._gesture[0].startswith("move:")
                else Qt.CursorShape.SizeHorCursor
                if self._boundary is not None
                else self.tool_cursor()
            )
        if self.timing is not None and self.tool in ("select", "move"):
            if any(abs(self._x(minute) - x) <= 10 for _, minute in self._cuts()):
                return Qt.CursorShape.SizeHorCursor
            if self.tool == "move" and self.segment_at(self._minute(x)) is not None:
                return (
                    Qt.CursorShape.ClosedHandCursor
                    if dragging
                    else Qt.CursorShape.OpenHandCursor
                )
        return self.tool_cursor()

    def leaveEvent(self, event: QEvent | None) -> None:  # noqa: N802 — Qt override
        """Retire hover highlights and clock guides after leaving the timeline.

        Args:
            event: Native leave event; an active drag retains its preview.

        Returns:
            None; no timing or history change occurs.
        """
        if self._drag_origin is None:
            self._hover_minute = None
            self._hover_segment = None
            self.setToolTip("")
            self.update()
        super().leaveEvent(event)

    def segment_at(self, minute: int) -> tuple[str, int] | None:
        """Find the chronological work/break segment at a shift-relative minute.

        Args:
            minute: Whole-minute cursor position, including the final clock tick.

        Returns:
            Kind/index for a real segment; None before data is projected.
        """
        if self.timing is None:
            return None
        minute = min(self.timing.shift_minutes - 1, max(0, minute))
        for index, pause in enumerate(self.timing.breaks):
            if pause.interval.start <= minute < pause.interval.end:
                return "break", index
        for block in self.timing.blocks():
            if any(p.start <= minute < p.end for p in block.pieces):
                return "block", block.index
        return None

    def select_segment(self, kind: str, index: int) -> None:
        """Highlight a table/timeline selection without accepting any timing data.

        Args:
            kind: block or break.
            index: Zero-based chronological segment identity in this projection.

        Returns:
            None; hosts may synchronize their corresponding table row.
        """
        self.selection = kind, index
        self._boundary = None
        self.selection_changed.emit(kind, index)
        self.update()

    def _preview_operation(self, x: float) -> None:
        """Prepare edits against a frozen gesture origin, never cumulatively.

        Args:
            x: Latest snapped pointer position; final release is also projected.

        Returns:
            None; invalid proposals retain origin and report a release error.
        """
        origin, gesture = self._drag_origin, self._gesture
        if origin is None or gesture is None:
            return
        action, index, anchor = gesture
        minute = self._minute(x)
        self._gesture_error = ""
        try:
            if action == "draw":
                start, end = sorted((anchor, minute))
                if abs(x - self._press_x) < 2:
                    start, end = anchor, min(origin.shift_minutes, anchor + 15)
                candidate = draw_timing_break(origin, start, end)
                self.selection = (
                    "break",
                    next(
                        i
                        for i, pause in enumerate(candidate.breaks)
                        if pause.interval.start == start and pause.interval.end == end
                    ),
                )
            elif action in ("move:block", "move:break"):
                kind = "work" if action == "move:block" else "break"
                position = segment_position(origin, kind, index)
                start = (
                    sum(s.minutes for s in timing_segments(origin)[:position])
                    + minute
                    - anchor
                )
                candidate = move_timing_segment(origin, kind, index, start)
                intervals = candidate.blocks() if kind == "work" else candidate.breaks
                selected = min(
                    range(len(intervals)),
                    key=lambda i: abs(
                        (
                            candidate.blocks()[i].pieces[0].start
                            if kind == "work"
                            else candidate.breaks[i].interval.start
                        )
                        - start
                    ),
                )
                self.selection = ("block" if kind == "work" else "break", selected)
            elif action == "split:block":
                candidate = split_work_block(origin, minute)
            elif action == "join:block":
                cut = min(
                    ((b.index + 1, b.pieces[-1].end) for b in origin.blocks()[:-1]),
                    key=lambda c: abs(self._x(c[1]) - x),
                    default=None,
                )
                boundary = (
                    cut[0]
                    if cut is not None and abs(self._x(cut[1]) - x) <= 12
                    else min(index + 1, len(origin.block_minutes) - 1)
                )
                candidate = join_work_blocks(origin, boundary)
            elif action == "join:break":
                candidate = join_timing_breaks(origin, index)
                selected_interval = origin.breaks[index].interval
                self.selection = (
                    "break",
                    next(
                        i
                        for i, pause in enumerate(candidate.breaks)
                        if pause.interval.start <= selected_interval.start
                        and pause.interval.end >= selected_interval.end
                    ),
                )
            elif action == "remove:break":
                candidate = change_timing_break(origin, index, None)
            elif action == "remove:block":
                candidate = remove_work_block(origin, index)
            else:
                raise ValueError("Split inside a work block, not inside a break.")
            self.timing = candidate
        except ValueError as error:
            self.timing = origin
            self.selection = self._origin_selection
            self._gesture_error = str(error)
        self.update()
