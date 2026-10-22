"""Original JROT editable worker/time-block grid with exact evidence links.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QPoint,
    QSignalBlocker,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QIcon, QKeyEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QMenu,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ergotools.application.rotation_pool import RotationPool
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.presentation.desktop.rotation_display import (
    measurement_color,
    rotation_recommendation,
    rotation_text,
    target_labels,
    target_measurement,
)
from ergotools.presentation.desktop.theme.jrot import JROT_STYLE


class _ChoiceDelegate(QStyledItemDelegate):
    """Edit using opaque item data; never split displayed multiline captions."""

    def __init__(self, table: "RotationTable") -> None:
        """Bind the table-owned delegate whose combo choices use exact opaque item data.

        Args:
            table: Owned Qt table to populate or delegate edits for; identity lives in
                item data.

        Returns:
            None.
        """
        super().__init__(table)
        self.table = table

    # Qt virtual method names are required by the framework.
    def createEditor(  # noqa: N802
        self,
        parent: QWidget | None,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QWidget:
        """Exclude identities already selected in the same worker/block column.

        Args:
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.
            option: Qt style option supplied to the paint/editor delegate; it does not
                identify stored data.
            index: Exact Qt model index for the delegated cell.

        Returns:
            New Qt-owned combo editor offering exact eligible opaque keys for this cell.
        """
        editor = QComboBox(parent)
        # Use the same styled popup delegate as the migrated management forms.
        # The native menu delegate can paint selected text white on white.
        editor.setItemDelegate(QStyledItemDelegate(editor))
        for key, caption in self.table.choice_options(index.row(), index.column()):
            editor.addItem(caption, key)
        return editor

    def setEditorData(self, editor: QWidget | None, index: QModelIndex) -> None:  # noqa: N802
        """Select the exact current identity, including colliding captions.

        Args:
            editor: Qt-owned combo editor created for this cell; optional overrides
                tolerate None.
            index: Exact Qt model index for the delegated cell.

        Returns:
            None.
        """
        assert isinstance(editor, QComboBox)
        editor.setCurrentIndex(editor.findData(index.data(Qt.ItemDataRole.UserRole)))

    def setModelData(  # noqa: N802
        self,
        editor: QWidget | None,
        model: QAbstractItemModel | None,
        index: QModelIndex,
    ) -> None:
        """Commit one typed choice and one edit notification through the grid.

        Args:
            editor: Qt-owned combo editor created for this cell; optional overrides
                tolerate None.
            model: Qt delegate model parameter; typed commits are routed through the
                owning grid.
            index: Exact Qt model index for the delegated cell.

        Returns:
            None.
        """
        assert isinstance(editor, QComboBox)
        if editor.currentIndex() >= 0:
            self.table.set_choice(
                index.row(), index.column(), str(editor.currentData())
            )


class RotationTable(QTableWidget):
    """Original 60px rows and fixed worker/block/average columns, stretch advice.

    Loading or switching risk basis emits no edit notification. Each user edit updates
    only its row under QSignalBlocker and emits one changed signal. The caller owns
    repository writes, scope application and optimization lifecycle.
    """

    changed = pyqtSignal()

    def __init__(
        self,
        pool: RotationPool,
        *,
        workers: int = 1,
        blocks: int = 4,
        kind: AssessmentKind = AssessmentKind.LIFFT,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
        clear_icon: QIcon | None = None,
    ) -> None:
        """Build empty original cells using already-read immutable pool evidence.

        Args:
            clear_icon: Processed Delete asset from the owning JROT form, or None.
            pool: Immutable worker/target/current Job values against which grid choices
                and schedules are validated.
            workers: Requested worker-row count, an integer from 1 through 10.
            blocks: Requested editable time-block count, an integer from 2 through 10.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.

        Raises:
            ValueError: Unsupported rotation risk basis.
        """
        if not isinstance(kind, AssessmentKind):
            raise ValueError("Unsupported rotation risk basis.")
        super().__init__(parent)
        self._clear_icon = clear_icon
        self.pool = pool
        self.kind = kind
        self.language = language
        self._workers = {choice.link.worker_id: choice for choice in pool.workers}
        self._targets = {choice.target.key: choice for choice in pool.targets}
        self._labels = target_labels(pool.targets, language)
        self.setStyleSheet(JROT_STYLE)
        self.setItemDelegate(_ChoiceDelegate(self))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.reset_grid(workers, blocks)

    def _text(self, english: str, spanish: str) -> str:
        """Resolve this component's UI wording without translating saved user values.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI wording according to this component's catalog/fallback
            contract.
        """
        return rotation_text(english, spanish, self.language)

    @property
    def _tool_label(self) -> str:
        """Return the unchanged branded caption for the grid's current typed risk basis.

        Args:
            None.

        Returns:
            Unchanged LiFFT, DUET or ST branded caption for the current risk basis.
        """
        return {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[self.kind]

    @property
    def blocks(self) -> int:
        """Return the number of editable time blocks, excluding derived columns.

        Args:
            None.

        Returns:
            Number of editable time blocks, excluding worker identity, average and
            advice columns.
        """
        return self.columnCount() - 3

    def reset_grid(self, workers: int, blocks: int) -> None:
        """Start an empty grid with source bounds; no notifications or pool writes.

        Args:
            workers: Requested worker-row count, an integer from 1 through 10.
            blocks: Requested editable time-block count, an integer from 2 through 10.

        Returns:
            None.

        Raises:
            ValueError: Rotation requires 1-10 workers and 2-10 time blocks.
        """
        if (
            type(workers) is not int
            or type(blocks) is not int
            or not (1 <= workers <= 10 and 2 <= blocks <= 10)
        ):
            raise ValueError("Rotation requires 1-10 workers and 2-10 time blocks.")
        with QSignalBlocker(self):
            self.clear()
            self.setRowCount(workers)
            self.setColumnCount(blocks + 3)
            self.setHorizontalHeaderLabels(
                [
                    self._text("Worker", "Trab."),
                    *(
                        self._text(f"Time-Block\n{i + 1}", f"Bloque\n{i + 1}")
                        for i in range(blocks)
                    ),
                    self._text("Avg.", "Prom."),
                    self._text("Recommendation", "Recomendación"),
                ]
            )
            worker_header = self.horizontalHeaderItem(0)
            assert worker_header is not None
            worker_header.setToolTip(self._text("Worker", "Trabajador"))
            header = self.horizontalHeader()
            vertical = self.verticalHeader()
            assert header is not None and vertical is not None
            vertical.setDefaultSectionSize(60)
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            for column in range(blocks + 3):
                self.setColumnWidth(
                    column,
                    80 if column == 0 else (160 if column == blocks + 2 else 110),
                )
                for row in range(workers):
                    cell = QTableWidgetItem("")
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if column > blocks:
                        cell.setFlags(
                            Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled)
                            | Qt.ItemFlags(Qt.ItemFlag.ItemIsSelectable)
                        )
                    self.setItem(row, column, cell)
            header.setStretchLastSection(True)

    def _cell(self, row: int, column: int) -> QTableWidgetItem:
        """Require the existing cell at the requested zero-based table location.

        Args:
            row: Zero-based task/worker table row.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            Borrowed existing table cell at the validated zero-based coordinates.

        Raises:
            IndexError: The supplied zero-based row/column is outside the existing grid.
        """
        if not 0 <= row < self.rowCount() or not 0 <= column < self.columnCount():
            raise IndexError((row, column))
        cell = self.item(row, column)
        assert cell is not None
        return cell

    def choice_key(self, row: int, column: int) -> str | None:
        """Return stored identity; visible labels and tooltips are never parsed.

        Args:
            row: Zero-based task/worker table row.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            Stored opaque worker/target key, or None for an unchosen cell; displayed
            labels are never parsed.
        """
        value: object = self._cell(row, column).data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) else None

    def choice_options(self, row: int, column: int) -> tuple[tuple[str, str], ...]:
        """Supply available dropdown choices with source per-column exclusions.

        Args:
            row: Zero-based task/worker table row.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            Eligible opaque-key/caption pairs for this cell after per-column exclusions;
            empty for derived columns.
        """
        self._cell(row, column)
        if column > self.blocks:
            return ()
        used = {
            self.choice_key(other, column)
            for other in range(self.rowCount())
            if other != row
        }
        current = self.choice_key(row, column)
        if column == 0:
            choices = tuple((key, key) for key in self._workers)
        else:
            choices = tuple(
                (key, self._labels[key])
                for key, choice in self._targets.items()
                if key == current
                or (
                    (measurement := target_measurement(choice, self.kind)) is not None
                    and measurement.probability_percent is not None
                )
            )
        return tuple(
            choice
            for choice in choices
            if choice[0] not in used or choice[0] == current
        )

    def set_choice(self, row: int, column: int, key: str | None) -> None:
        """Apply or clear one eligible choice; reject duplicates before mutation.

        Saved manual collisions can be loaded, but dropdown editing follows the original
        unique-worker and unique-target-per-block restrictions.

        Args:
            row: Zero-based task/worker table row.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.

        Returns:
            None.

        Raises:
            ValueError: Derived rotation columns cannot be edited. Choice is unavailable
                or already used in this column.
        """
        cell = self._cell(row, column)
        if column > self.blocks:
            raise ValueError("Derived rotation columns cannot be edited.")
        if key is not None and key not in dict(self.choice_options(row, column)):
            raise ValueError("Choice is unavailable or already used in this column.")
        if self.choice_key(row, column) == key:
            return
        with QSignalBlocker(self):
            cell.setData(Qt.ItemDataRole.UserRole, key)
            self._render_row(row)
        self.changed.emit()

    def set_kind(self, kind: AssessmentKind) -> None:
        """Repaint recorded measurements without changing links or deriving values.

        Args:
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.

        Returns:
            None.

        Raises:
            ValueError: Unsupported rotation risk basis.
        """
        if not isinstance(kind, AssessmentKind):
            raise ValueError("Unsupported rotation risk basis.")
        self.kind = kind
        with QSignalBlocker(self):
            for row in range(self.rowCount()):
                self._render_row(row)

    def load_scheme(self, scheme: RotationScheme) -> None:
        """Load complete frozen links; validate before clearing existing edits.

        Args:
            scheme: Immutable complete saved or proposed rotation scheme with exact
                evidence links.

        Returns:
            None.

        Raises:
            ValueError: Rotation grid requires its exact saved evidence pool.
        """
        if (
            scheme.project_id != self.pool.project_id
            or any(
                link.worker_id not in self._workers
                or self._workers[link.worker_id].link != link
                for link in scheme.workers
            )
            or any(
                target.key not in self._targets
                or self._targets[target.key].target != target
                for target in scheme.targets
            )
        ):
            raise ValueError("Rotation grid requires its exact saved evidence pool.")
        self.reset_grid(len(scheme.workers), len(scheme.current[0].target_keys))
        with QSignalBlocker(self):
            for row, rotation in enumerate(scheme.current):
                for column, key in enumerate(
                    (rotation.worker_id, *rotation.target_keys)
                ):
                    self._cell(row, column).setData(Qt.ItemDataRole.UserRole, key)
                self._render_row(row)

    def restore_choices(self, cells: tuple[tuple[str | None, ...], ...]) -> None:
        """Restore a historical partial grid, retaining saved manual collisions.

        Validate all opaque keys before mutation. Replay does not emit changed or reread
        current Job values; the caller supplies the snapshot's pool.

        Args:
            cells: Historical partial opaque choices by worker row and worker/block
                column; None means unchosen.

        Returns:
            None.

        Raises:
            ValueError: Historical rotation cells require their exact pool.
        """
        if any(
            len(row) != self.blocks + 1
            or (row[0] is not None and row[0] not in self._workers)
            or any(key is not None and key not in self._targets for key in row[1:])
            for row in cells
        ):
            raise ValueError("Historical rotation cells require their exact pool.")
        with QSignalBlocker(self):
            self.setRowCount(len(cells))
            for row, values in enumerate(cells):
                for column, key in enumerate(values):
                    self._cell(row, column).setData(Qt.ItemDataRole.UserRole, key)
                self._render_row(row)

    def current_scheme(
        self,
        scheme_id: str,
        *,
        name: str | None = None,
        scope: tuple[WorkplaceContext, ...] = (),
        description: str | None = None,
    ) -> RotationScheme:
        """Build a complete manual scheme; never write or mark a draft as saved.

        Args:
            scheme_id: Exact proposed rotation scheme identifier, independent of
                displayed choice captions.
            name: Literal project/scheme name or export-name stem; None preserves the
                operation's stated default.
            scope: Exact typed workplace filter; no selection is reconstructed from
                displayed labels.
            description: Literal project/scheme description; None preserves absent
                optional metadata.

        Returns:
            Complete manual scheme preserving exact pool/Job links; no repository
            write or clean marker occurs.

        Raises:
            ValueError: A worker or block is empty or scheme ownership is invalid.
        """
        workers = []
        current = []
        keys: list[str] = []
        for row in range(self.rowCount()):
            worker = self.choice_key(row, 0)
            if worker is None:
                raise ValueError("Select a worker in every row.")
            blocks = tuple(
                self.choice_key(row, col) for col in range(1, self.blocks + 1)
            )
            if any(key is None for key in blocks):
                raise ValueError("Select a job in every time block.")
            selected = tuple(key for key in blocks if key is not None)
            workers.append(self._workers[worker].link)
            current.append(WorkerRotation(worker, selected))
            keys.extend(selected)
        return RotationScheme(
            self.pool.project_id,
            scheme_id,
            scheme_id if name is None else name,
            tuple(workers),
            tuple(self._targets[key].target for key in dict.fromkeys(keys)),
            tuple(current),
            scope,
            description=description,
        )

    def _render_row(self, row: int) -> None:
        """Render one row from opaque worker/target choices and current Job values.

        Render one row from opaque worker/target choices and current Job values,
        preserving original average/color/recommendation rules without saving.

        Args:
            row: Zero-based task/worker table row.

        Returns:
            None.
        """
        worker = self.choice_key(row, 0)
        cell = self._cell(row, 0)
        cell.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        cell.setText(worker or "")
        record = self._workers.get(worker) if worker is not None else None
        cell.setToolTip(
            " ".join(
                value
                for value in (record.worker.first_name, record.worker.last_name)
                if value
            )
            if record
            else ""
        )
        probabilities: list[float] = []
        colors: list[QColor] = []
        missing = False
        for column in range(1, self.blocks + 1):
            cell = self._cell(row, column)
            key = self.choice_key(row, column)
            cell.setToolTip("")
            cell.setBackground(QColor("white"))
            cell.setForeground(QColor("#1B2933"))
            if key is None:
                cell.setText("")
                continue
            choice = self._targets[key]
            measurement = target_measurement(choice, self.kind)
            probability = measurement.probability_percent if measurement else None
            if probability is None:
                missing = True
                cell.setText(
                    f"{self._labels[key]}\n{self._text('Unavailable', 'No disponible')}"
                )
                cell.setBackground(QColor("#F2F5F7"))
                cell.setForeground(QColor("#5F6F7A"))
            else:
                cell.setText(f"{self._labels[key]}\n{probability:.1f}%")
                color = QColor(
                    measurement_color(
                        self.kind,
                        measurement.cumulative_damage if measurement else None,
                    )
                )
                cell.setBackground(color)
                probabilities.append(probability)
                colors.append(color)
            cell.setToolTip(
                f"{self._tool_label} - {choice.job_name} "
                f"({measurement.cumulative_damage if measurement else None})\n"
                + f"{self._text('Units', 'Unidades')}: "
                + (measurement.unit or "Metric" if measurement else "—")
            )
        average = self._cell(row, self.blocks + 1)
        advice = self._cell(row, self.blocks + 2)
        advice.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        average.setBackground(QColor("white"))
        average.setForeground(QColor("#1B2933"))
        advice.setForeground(QColor("#1B2933"))
        average.setText("")
        advice.setText("")
        if missing:
            average.setText(self._text("Unavailable", "No disponible"))
            average.setBackground(QColor("#F2F5F7"))
            average.setForeground(QColor("#5F6F7A"))
            advice.setForeground(QColor("#5F6F7A"))
            advice.setText(
                self._text(
                    f"Unavailable: complete {self._tool_label} "
                    "Job risk data is required.",
                    "No disponible: se requieren datos de riesgo de "
                    f"{self._tool_label}.",
                )
            )
        elif len(probabilities) == self.blocks:
            average.setText(f"{round(sum(probabilities) / len(probabilities), 1)}%")
            average.setBackground(
                QColor(
                    sum(color.red() for color in colors) // len(colors),
                    sum(color.green() for color in colors) // len(colors),
                    sum(color.blue() for color in colors) // len(colors),
                )
            )
            advice.setText(rotation_recommendation(tuple(probabilities), self.language))
        advice.setToolTip(advice.text())

    def clear_selected(self) -> None:
        """Clear selected editable cells in one batch, preserving derived columns.

        Args:
            None.

        Returns:
            None.
        """
        affected = set()
        with QSignalBlocker(self):
            for cell in self.selectedItems():
                if (
                    cell.column() <= self.blocks
                    and self.choice_key(cell.row(), cell.column()) is not None
                ):
                    cell.setData(Qt.ItemDataRole.UserRole, None)
                    affected.add(cell.row())
            for row in affected:
                self._render_row(row)
        if affected:
            self.changed.emit()

    def _context_menu(self, position: QPoint) -> None:
        """Offer the original Clear action only.

        Offer the original Clear action only for editable worker/block cells at the
        requested viewport point.

        Args:
            position: Point in table viewport logical pixels; converted to global
                coordinates only when opening the menu.

        Returns:
            None.
        """
        index = self.indexAt(position)
        if not index.isValid() or index.column() > self.blocks:
            return
        menu = QMenu(self)
        action = menu.addAction(self._text("Clear Cell", "Vaciar celda"))
        assert action is not None
        if self._clear_icon is not None:
            action.setIcon(self._clear_icon)
        action.triggered.connect(
            lambda: self.set_choice(index.row(), index.column(), None)
        )
        viewport = self.viewport()
        assert viewport is not None
        menu.exec(viewport.mapToGlobal(position))

    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: N802
        """Keep the original Delete shortcut and ordinary table keyboard editing.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        if event is not None and event.key() == Qt.Key.Key_Delete:
            self.clear_selected()
            event.accept()
        else:
            super().keyPressEvent(event)
