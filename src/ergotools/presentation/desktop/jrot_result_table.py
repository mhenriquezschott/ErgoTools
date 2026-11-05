"""Shared read-only guided matrices for previews, saved runs and comparisons.

Presentation layer. Exact supplied labels/coefficients own the display; no live lookup,
solver, document mutation or probability recomputation occurs in this widget.
"""

from collections.abc import Mapping

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QResizeEvent
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from ergotools.domain.language import Language
from ergotools.domain.risk import classify_probability
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scenario import RotationInputs
from ergotools.presentation.desktop.jrot_table_style import style_rotation_table
from ergotools.presentation.desktop.rotation_block_headers import RotationBlockHeaders
from ergotools.presentation.desktop.table_presentation import table_text_color
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES


def tool_caption(value: str) -> str:
    """Resolve persisted tool values to their branded display name.

    Args:
        value: LiFFT, DUET or ST stable enum value.

    Returns:
        Branded display name; unknown values remain explicit.
    """
    return {"lifft": "LiFFT", "duet": "DUET", "tst": "ST"}.get(value, value)


class JrotResultTable(QTableWidget):
    """Content-sized matrix using spare width for blocks and scrolling when needed."""

    def __init__(
        self,
        inputs: RotationInputs,
        rows: tuple[WorkerRotation, ...],
        labels: Mapping[str, str],
        workers: tuple[str, ...],
        risks: Mapping[str, float],
        scores: tuple[float, ...] | None,
        language: Language,
        parent: QWidget | None = None,
        *,
        compact: bool = False,
    ) -> None:
        """Project one exact schedule with frozen names, risks and optional indices.

        Args:
            inputs: Exact timing and position identities for these rows.
            rows: Complete schedule in worker order.
            labels: Job names indexed by exact position key.
            workers: Corresponding literal worker labels.
            risks: Available tool probabilities; absence is a dash, not zero.
            scores: Corresponding weighted indices, or None when unavailable.
            language: Owned header captions.
            parent: Optional Qt lifetime owner.
            compact: True displays Job IDs while tooltips retain complete names.

        Returns:
            None; cells and headers are read-only with complete value tooltips.
        """
        super().__init__(parent)
        style_rotation_table(self)
        self.widths: tuple[int, ...] = ()
        self.heights: tuple[int, ...] = ()
        spanish = language is Language.SPANISH
        blocks = len(rows[0].target_keys) if rows else 0
        self.setRowCount(len(rows))
        self.setColumnCount(blocks + 2)
        durations = inputs.timing.block_minutes if inputs.timing else ()
        self.setHorizontalHeaderLabels(
            [
                "Trabajador" if spanish else "Worker",
                *(
                    (f"Bloque {i + 1}" if spanish else f"Block {i + 1}")
                    + (f" · {durations[i]} min" if durations else "")
                    for i in range(blocks)
                ),
                "Índice ponderado" if spanish else "Weighted index",
            ]
        )
        targets = {t.key: t for t in inputs.targets}
        for index, row in enumerate(rows):
            self.setItem(index, 0, QTableWidgetItem(workers[index]))
            for column, key in enumerate(row.target_keys, 1):
                target = targets[key]
                name = labels.get(key, target.job_id)
                caption = target.job_id + (
                    " · " + name if name != target.job_id else ""
                )
                if target.placement_id is not None:
                    caption += f" · #{target.placement_id}"
                risk = risks.get(key)
                visible = target.job_id if compact else caption
                if compact and target.placement_id is not None:
                    visible += f" · #{target.placement_id}"
                item = QTableWidgetItem(
                    visible + "\n" + (f"{risk:.1f}%" if risk is not None else "—")
                )
                item.setToolTip(
                    caption + "\n" + (f"{risk:.1f}%" if risk is not None else "—")
                )
                if risk is not None:
                    item.setBackground(
                        QColor(RISK_APPEARANCES[classify_probability(risk)].color_hex)
                    )
                self.setItem(index, column, item)
            self.setItem(
                index,
                blocks + 1,
                QTableWidgetItem(f"{scores[index]:.2f}" if scores is not None else "—"),
            )
        for row_index in range(self.rowCount()):
            for column in range(self.columnCount()):
                cell = self.item(row_index, column)
                if cell is not None:
                    if not cell.toolTip():
                        cell.setToolTip(cell.text())
                    if column:
                        cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        font = cell.font()
                        font.setBold(True)
                        cell.setFont(font)
                        cell.setForeground(
                            table_text_color(cell.background().color())
                            if cell.background().style() != Qt.BrushStyle.NoBrush
                            else QColor("#082F49")
                        )
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        for row_index in range(self.rowCount()):
            self.setRowHeight(row_index, round(self.rowHeight(row_index) * 1.15))
        self.heights = tuple(self.rowHeight(i) for i in range(self.rowCount()))
        self.widths = tuple(self.columnWidth(i) for i in range(self.columnCount()))
        self.fit_columns()
        self.fit_rows()
        self.block_headers = RotationBlockHeaders(self)
        self.block_headers.bind(inputs, blocks)

    def fit_columns(self) -> None:
        """Allocate spare width across blocks without shrinking content minima.

        Args:
            None.

        Returns:
            None; overflow retains the standard horizontal scrollbar.
        """
        viewport = self.viewport()
        if viewport is None or not self.widths:
            return
        extra = max(0, viewport.width() - sum(self.widths))
        blocks = max(1, len(self.widths) - 2)
        for column, minimum in enumerate(self.widths):
            share = extra // blocks if 0 < column < len(self.widths) - 1 else 0
            self.setColumnWidth(column, minimum + share)

    def fit_rows(self) -> None:
        """Use spare height modestly without creating a vertical scrollbar.

        Args:
            None.

        Returns:
            None; content minima survive small viewports and enlarged rows can shrink.
        """
        viewport = self.viewport()
        if viewport is None or not self.heights:
            return
        extra = min(
            20, max(0, viewport.height() - sum(self.heights)) // len(self.heights)
        )
        for row, minimum in enumerate(self.heights):
            self.setRowHeight(row, minimum + extra)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        # Qt requires this virtual method spelling.
        """Refit the same matrix when the owner or animated drawer changes width.

        Args:
            event: Native resize payload, forwarded unchanged.

        Returns:
            None; no data or history is changed.
        """
        super().resizeEvent(event)
        self.fit_columns()
        self.fit_rows()
