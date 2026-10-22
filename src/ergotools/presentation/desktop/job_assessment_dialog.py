"""Select a current worker calculation to copy into a Job without association.

Presentation layer. Borrow read-only workspace capabilities; list standalone and real
workplace assessments for one explicit tool. No calculator, ownership mutation, SQL or
source recalculation occurs. The Job host owns replacement consent and shared history.
"""

from collections.abc import Mapping
from contextlib import suppress

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.presentation.desktop.style import WORKSPACE_STYLE
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


class JobAssessmentDialog(QDialog):
    """Return an independent current source/result copy, never an assessment link."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        kind: AssessmentKind,
        icons: Mapping[str, QIcon],
        language: Language,
        parent: QWidget | None = None,
        *,
        convention: DecimalConvention = DecimalConvention.POINT,
    ) -> None:
        """Read eligible assessments without navigating the main assessment editor.

        Args:
            workspace: Borrowed open project; no repository lifetime is transferred.
            kind: Exact Job tool to populate; other tools cannot be selected.
            icons: Existing processed application icons.
            language: UI wording only; worker/workplace data remain literal.
            parent: Owning Job Management dialog.
            convention: Application decimal mark, independent of interface language.

        Returns:
            None; acceptance is read-only and creates no Job or worker record.
        """
        super().__init__(parent)
        self.workspace = workspace
        self.kind = kind
        self.language = language
        self.convention = convention
        self.selected: JobRiskMeasurement | None = None
        self.setWindowTitle(
            self.text("Use worker assessment", "Usar evaluación de trabajador")
        )
        self.setStyleSheet(WORKSPACE_STYLE)
        apply_dialog_theme(self)
        self.resize(1000, 560)
        self.setMinimumSize(800, 480)
        layout = QVBoxLayout(self)
        title = QLabel(
            self.text("Use worker assessment", "Usar evaluación de trabajador")
        )
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        intro = QLabel(
            self.text(
                (
                    "Copy tasks and calculated values for this tool. The worker "
                    "assessment remains unchanged and independent."
                ),
                (
                    "Copiar tareas y valores calculados de esta herramienta. La "
                    "evaluación del trabajador permanece independiente y sin "
                    "cambios."
                ),
            )
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            self.text("Search worker or workplace", "Buscar trabajador o lugar")
        )
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            [
                self.text("Worker", "Trabajador"),
                self.text("Assessment context", "Contexto de evaluación"),
                self.text("Damage", "Daño"),
                self.text("Probability (%)", "Probabilidad (%)"),
                self.text("State", "Estado"),
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)
        footer = QHBoxLayout()
        footer.addStretch()
        self.cancel_button = QPushButton(self.text("Cancel", "Cancelar"))
        self.cancel_button.setIcon(icons["cancel"])
        self.cancel_button.clicked.connect(self.reject)
        self.use_button = QPushButton(
            self.text("Use assessment values", "Usar valores de evaluación")
        )
        self.use_button.setIcon(icons["worker"])
        self.use_button.setObjectName("primaryOutlineButton")
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self._use_selection)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.use_button)
        layout.addLayout(footer)
        hierarchy = workspace.read_hierarchy().hierarchy.work
        workers = {worker.worker_id: worker for worker in hierarchy.workers}
        catalog = workspace.read_jobs().jobs
        assignments = {a.assignment_id: a for a in catalog.assignments}
        placements = {p.placement_id: p for p in catalog.placements}
        jobs = {job.job_id: job for job in catalog.jobs}
        for entry in workspace.read_history().history.entries:
            if entry.kind is not kind:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            worker = workers[entry.worker_id]
            context = self.text("Standalone assessment", "Evaluación independiente")
            if entry.assignment_id is not None:
                place = assignments[entry.assignment_id].worker.workplace
                context = " > ".join(
                    (
                        place.plant_name,
                        place.section_name,
                        place.line_name,
                        place.station_id,
                        place.shift_id,
                    )
                )
                assignment = assignments[entry.assignment_id]
                placement = (
                    placements.get(assignment.placement_id)
                    if assignment.placement_id is not None
                    else None
                )
                job_caption = (
                    self.text("No Job", "Sin trabajo")
                    if placement is None
                    else self.text("Job", "Trabajo")
                    + ": "
                    + placement.job_id
                    + " - "
                    + jobs[placement.job_id].name
                )
                context = job_caption + " | " + context
            measurement = None
            # Uncalculated/stale sources remain visible but cannot be copied.
            with suppress(ValueError):
                measurement = workspace.job_measurement_from_assessment(
                    entry.document_id
                )
            values = (
                worker.worker_id
                + (
                    " | "
                    + ", ".join(
                        part for part in (worker.last_name, worker.first_name) if part
                    )
                    if worker.last_name or worker.first_name
                    else ""
                ),
                context,
                f"{measurement.cumulative_damage:.8g}".replace(".", convention.value)
                if measurement
                else "—",
                f"{measurement.probability_percent:.4g}".replace(".", convention.value)
                if measurement
                else "—",
                self.text("Ready", "Disponible")
                if measurement
                else self.text("Calculate first", "Calcular primero"),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                tooltip = value
                if column == 1:
                    tooltip += (
                        "\n"
                        + self.text("Assessment", "Evaluación")
                        + ": "
                        + entry.document_id
                    )
                    if entry.assignment_id is not None:
                        assignment = assignments[entry.assignment_id]
                        tooltip += (
                            "\n"
                            + self.text("Assignment", "Asignación")
                            + f": {assignment.assignment_id} | "
                            + (
                                self.text("Active", "Activa")
                                if assignment.active
                                else self.text("Previous", "Anterior")
                            )
                        )
                item.setToolTip(tooltip)
                item.setData(Qt.ItemDataRole.UserRole, entry.document_id)
                item.setData(Qt.ItemDataRole.UserRole + 1, measurement is not None)
                self.table.setItem(row, column, item)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.itemDoubleClicked.connect(self._use_selection)

    def text(self, english: str, spanish: str) -> str:
        """Resolve static UI wording without translating stored source data.

        Args:
            english: English interface text.
            spanish: Spanish interface text.

        Returns:
            Wording for the selected application language.
        """
        return spanish if self.language is Language.SPANISH else english

    def _filter(self, text: str) -> None:
        """Filter visible rows without changing selection eligibility or any source.

        Args:
            text: Literal search substring compared case-insensitively.

        Returns:
            None; a hidden selection cannot be accepted.
        """
        for row in range(self.table.rowCount()):
            cells = [self.table.item(row, c) for c in (0, 1)]
            self.table.setRowHidden(
                row,
                not any(
                    cell is not None and text.casefold() in cell.text().casefold()
                    for cell in cells
                ),
            )
        self._selection_changed()

    def _selection_changed(self) -> None:
        """Enable copying only for a visible current complete calculation.

        Args:
            None.

        Returns:
            None; missing/stale result rows cannot be accepted.
        """
        row = self.table.currentRow()
        item = self.table.item(row, 0)
        self.use_button.setEnabled(
            row >= 0
            and not self.table.isRowHidden(row)
            and item is not None
            and bool(item.data(Qt.ItemDataRole.UserRole + 1))
        )

    def _use_selection(self) -> None:
        """Recheck the exact result before returning a detached copy to the Job host.

        Args:
            None.

        Returns:
            None; failure or unavailable selection leaves the picker open.
        """
        if not self.use_button.isEnabled():
            return
        item = self.table.item(self.table.currentRow(), 0)
        assert item is not None
        try:
            self.selected = self.workspace.job_measurement_from_assessment(
                str(item.data(Qt.ItemDataRole.UserRole))
            )
        except ValueError:
            self.selected = None
            self.use_button.setEnabled(False)
            return
        self.accept()
