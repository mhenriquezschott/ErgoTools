"""Original six-column saved tool-data browser with explicit selection identity.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.presentation.desktop.style import WORKSPACE_STYLE
from ergotools.presentation.saved_tool_options import SavedToolOption


class ToolDataDialog(QDialog):
    """Return a saved ownership choice without editing or loading project data."""

    def __init__(
        self,
        options: tuple[SavedToolOption, ...],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build the reference 800 by 400 scrollable table and Close/Load controls.

        Args:
            options: Immutable eligible saved selections; no storage access occurs while
                filtering the dialog.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.selected: SavedToolOption | None = None
        spanish = language is Language.SPANISH
        self.setWindowTitle(
            "Selección de datos de herramienta" if spanish else "Tool Data Selection"
        )
        self.resize(800, 400)
        self.setStyleSheet(WORKSPACE_STYLE)
        layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        table_layout = QVBoxLayout(container)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Planta", "Sección", "Línea", "Estación", "Turno", "Herramienta"]
            if spanish
            else ["Plant", "Section", "Line", "Station", "Shift", "Tool"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setRowCount(len(options))
        for row, option in enumerate(options):
            place = option.workplace
            tool = {
                AssessmentKind.LIFFT: "LiFFT",
                AssessmentKind.DUET: "DUET",
                AssessmentKind.TST: "ST",
            }[option.kind]
            values = (
                place.plant_name if place is not None else "—",
                place.section_name if place is not None else "—",
                place.line_name if place is not None else "—",
                place.station_id if place is not None else "—",
                place.shift_id if place is not None else "—",
                tool,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, option)
                item.setToolTip(
                    ("Asignación" if spanish else "Assignment")
                    + f": {option.assignment_id} | "
                    + ("Trabajo" if spanish else "Job")
                    + f": {option.job_id or '—'}"
                )
                self.table.setItem(row, column, item)
        # Styled bold headers need their painted font/padding before sizing.
        self.table.ensurePolished()
        header = self.table.horizontalHeader()
        assert header is not None
        header.ensurePolished()
        self.table.resizeColumnsToContents()
        metrics = QFontMetrics(header.font())
        for column in range(self.table.columnCount()):
            label = self.table.horizontalHeaderItem(column)
            assert label is not None
            self.table.setColumnWidth(
                column,
                max(
                    self.table.columnWidth(column),
                    metrics.horizontalAdvance(label.text()) + 24,
                ),
            )
        self.table.setSortingEnabled(True)
        table_layout.addWidget(self.table)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        buttons = QHBoxLayout()
        self.close_button = QPushButton("Cerrar" if spanish else "Close")
        self.load_button = QPushButton("Cargar" if spanish else "Load")
        buttons.addWidget(self.close_button)
        buttons.addStretch()
        buttons.addWidget(self.load_button)
        layout.addLayout(buttons)
        self.close_button.clicked.connect(self.reject)
        self.load_button.clicked.connect(self.load_selected)
        self.table.doubleClicked.connect(self.load_selected)
        self._selection_title = "Error de selección" if spanish else "Selection Error"
        self._selection_message = (
            "Seleccione una fila antes de continuar."
            if spanish
            else "Please select a row before proceeding."
        )

    def load_selected(self) -> None:
        """Accept the row's immutable identity; sorting cannot change its owner.

        Args:
            None.

        Returns:
            None.
        """
        item = self.table.item(self.table.currentRow(), 0)
        if item is None:
            QMessageBox.warning(self, self._selection_title, self._selection_message)
            return
        selected = item.data(Qt.ItemDataRole.UserRole)
        assert isinstance(selected, SavedToolOption)
        self.selected = selected
        self.accept()
