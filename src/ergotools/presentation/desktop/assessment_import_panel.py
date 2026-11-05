"""Reusable staged input import with source preview, field mapping and validation.

Presentation layer. Application preparation validates a complete immutable replacement.
Nothing is accepted into a project until the owning main/Job host accepts the dialog.
"""

import re
from collections.abc import Mapping
from dataclasses import replace

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.assessment_clipboard import (
    assessment_input_fields,
)
from ergotools.application.assessment_import import (
    ImportProfile,
    TabularFileReader,
    parse_import_text,
    prepare_import,
)
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    assessment_kind,
    task_has_data,
)
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_action_icons import (
    assessment_action_icon,
)
from ergotools.presentation.desktop.assessment_import_text import (
    assessment_import_error,
)
from ergotools.presentation.desktop.assessment_task_text import (
    task_field_caption,
)
from ergotools.presentation.desktop.import_row_header import ImportRowHeader
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.theme.main_workspace import MAIN_WORKSPACE_STYLE
from ergotools.presentation.desktop.workflow_action_style import set_action_icon


def clipboard_field(header: str) -> str | None:
    """Suggest a known editable field from explicit English/Spanish column headers.

    Args:
        header: Original first-row cell; numeric values are not interpreted as headers.

    Returns:
        Canonical field or None for unknown/derived/row-number headers.
    """
    token = " ".join(header.strip().casefold().replace("_", " ").split())
    aliases = {
        "task_name": ("task name", "nombre de tarea", "task description"),
        "lever_arm": ("lever arm", "brazo", "brazo de palanca"),
        "load": ("load", "carga"),
        "repetitions": (
            "repetition",
            "repetitions",
            "repeticion",
            "repetición",
            "repeticiones",
        ),
        "omni_res_scale": (
            "omni",
            "omni-res scale",
            "omni-res",
            "omni res scale",
            "escala omni-res",
        ),
        "direction": ("direction", "type of task", "task type", "tipo de tarea"),
    }
    return next(
        (
            field
            for field, names in aliases.items()
            if any(
                token == name
                or token.startswith(name + " (")
                or token.startswith(name + " /")
                for name in names
            )
        ),
        None,
    )


def clipboard_header_system(header: str, field: str | None) -> MeasurementSystem | None:
    """Read explicit dimensional header units without assuming mass is force.

    Args:
        header: Original source header; unit-free columns use the visible unit choice.
        field: Explicit mapped canonical destination, or None for ignored columns.

    Returns:
        Declared metric/imperial system for an arm/load column, otherwise None.

    Raises:
        ValueError: A dimensional header declares unsupported arm/force units.
    """
    if field not in ("lever_arm", "load"):
        return None
    units = re.findall(r"\(([^)]+)\)", header.casefold())
    if not units:
        return None
    token = units[-1].strip()
    metric = ("cm",) if field == "lever_arm" else ("n", "newton", "newtons")
    imperial = (
        ("in", "inch", "inches") if field == "lever_arm" else ("lb", "lbs", "lbf")
    )
    if token in metric:
        return MeasurementSystem.METRIC
    if token in imperial:
        return MeasurementSystem.IMPERIAL
    raise ValueError("Unsupported header units. Use cm/N or in/lbf.")


class AssessmentImportPanel(QWidget):
    """Stage source values and preferences without a project writer.

    Attributes:
        prepared: Emits after a complete immutable replacement validates.
        cancelled: Requests host-owned Cancel; Settings hosts hide these actions.
    """

    prepared = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(
        self,
        source: AssessmentDraft,
        text: str,
        language: Language,
        convention: DecimalConvention,
        system: MeasurementSystem,
        start_row: int,
        parent: QWidget | None = None,
        *,
        icons: Mapping[str, QIcon] | None = None,
        start_field: str = "task_name",
        profile: ImportProfile | None = None,
        file_reader: TabularFileReader | None = None,
        embedded: bool = False,
    ) -> None:
        """Build staged controls; file reads are explicit and project writes host-owned.

        Args:
            icons: Injected packaged action glyphs; no asset lookup or source writes.
            profile: Optional tool-specific remembered interpretation/mapping.
            file_reader: Injected bounded read-only CSV/TSV/XLSX capability.
            embedded: Hide target Apply/Cancel when embedded in personal Settings.
            source: Frozen canonical source captured after pending host edits commit.
            text: Plain clipboard selection with optional headers.
            language: Static English/Spanish interface captions.
            convention: Initial explicit decimal-mark choice.
            system: Initial pasted measurement system, shown for confirmation.
            start_row: Initial zero-based destination position.
            parent: Native owner; closing without Paste discards this preview.
            start_field: Last focused editable column, used only for headerless mapping.

        Returns:
            None; accepted replacement remains None until validation succeeds.

        Raises:
            ValueError: Initial text is malformed or exceeds finite preview bounds.
        """
        super().__init__(parent)
        self.icons = icons or {}
        self.source = source
        self.embedded = embedded
        self._profile = profile
        self.file_reader = file_reader
        self._path = ""
        self._base_rows: tuple[tuple[str, ...], ...] = ()
        self._updating = False
        self._active = True
        self._source_error = False
        self._invalid_cells: list[tuple[int, int]] = []
        self._excluded_rows: set[int] = set()
        self._preview_indices: tuple[int, ...] = ()
        self._row_snapshot: object = None
        self._has_source = bool(text.strip())
        initial_fields = (
            profile.fields
            if profile and profile.configured and profile.fields
            else assessment_input_fields(source)
        )
        labels = (
            profile.headers
            if profile and profile.headers
            else tuple(
                task_field_caption(field, language)
                if field
                else ("Ignorar" if language is Language.SPANISH else "Ignore")
                for field in initial_fields
            )
        )
        empty_row = tuple("" for _ in initial_fields)
        self.rows = (
            parse_import_text(text, profile.delimiter if profile else "auto")
            if text.strip()
            else (
                (empty_row,)
                if profile and profile.configured and not profile.header
                else (labels, empty_row)
            )
        )
        self.replacement: AssessmentDraft | None = None
        self.language = language
        self.start_field = start_field
        self.setWindowTitle(self.text("Import task data", "Importar datos de tareas"))
        self.setStyleSheet(MAIN_WORKSPACE_STYLE)
        apply_dialog_theme(self)
        self.resize(1100, 780)
        layout = QVBoxLayout(self)
        title = QLabel(self.text("Import task data", "Importar datos de tareas"))
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0B326C;")
        title.setVisible(not embedded)
        layout.addWidget(title)
        explanation = QLabel(
            self.text(
                "Map columns and confirm units. Paste replaces mapped cells together; "
                "Other fields remain. Cancel keeps your data; Undo reverses Paste.",
                "Asigne columnas y unidades. Solo cambian las celdas asignadas. "
                "Cancelar no cambia datos; Deshacer revierte todo el pegado.",
            )
        )
        if embedded:
            explanation.setText(
                self.text(
                    "Configure this tool's defaults. Preview data "
                    "stays temporary; Apply saves settings only.",
                    "Configure esta herramienta. La vista es "
                    "temporal; Aplicar guarda solo preferencias.",
                )
            )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.build_source_controls(layout, text)
        options = QGridLayout()
        self.header_option = QCheckBox(self.text("Header row", "Fila de encabezados"))
        self.header_option.setChecked(
            profile.header
            if profile and profile.configured
            else any(clipboard_field(cell) for cell in self.rows[0])
        )
        header_controls = QHBoxLayout()
        header_controls.addWidget(self.header_option)
        self.header_row = QSpinBox()
        self.header_row.setRange(1, max(1, len(self.rows)))
        self.header_row.setMaximumWidth(100)
        self.header_row.setToolTip(
            self.text(
                "Choose the source header row; preceding rows are "
                "skipped automatically.",
                "Elija la fila de encabezados; se omiten las filas anteriores.",
            )
        )
        self.header_row.valueChanged.connect(self.header_row_changed)
        header_controls.addWidget(self.header_row)
        header_controls.addStretch(1)
        options.addLayout(header_controls, 0, 0, 1, 2)
        options.addWidget(QLabel(self.text("Start at task", "Desde tarea")), 0, 2)
        self.start = QSpinBox()
        self.start.setRange(1, len(source.tasks) + 1)
        self.start.setValue(min(max(0, start_row), len(source.tasks)) + 1)
        options.addWidget(self.start, 0, 3)
        self.units = QComboBox()
        self.units.addItem("cm / N", MeasurementSystem.METRIC)
        self.units.addItem("in / lbf", MeasurementSystem.IMPERIAL)
        if profile and profile.configured:
            system = profile.units
        header_text = " ".join(self.rows[0]).casefold()
        if self.header_option.isChecked():
            if any(token in header_text for token in ("(in)", "inch", "lbf", "lbs")):
                system = MeasurementSystem.IMPERIAL
            elif any(token in header_text for token in ("(cm)", "(n)")):
                system = MeasurementSystem.METRIC
        self.units.setCurrentIndex(self.units.findData(system))
        self.units.setToolTip(
            self.text(
                "Units of pasted values; load is force, not mass.",
                "Unidades pegadas; la carga es fuerza, no masa.",
            )
        )
        options.addWidget(self.units, 1, 0)
        self.decimal = QComboBox()
        self.decimal.addItem("1.25", DecimalConvention.POINT)
        self.decimal.addItem("1,25", DecimalConvention.COMMA)
        self.decimal.setCurrentIndex(self.decimal.findData(convention))
        self.decimal.setToolTip(
            self.text(
                "Decimal separator in the pasted cells.",
                "Separador decimal de las celdas.",
            )
        )
        options.addWidget(self.decimal, 1, 1)
        self.thousands = QComboBox()
        for caption, value in [
            (self.text("No thousands separator", "Sin separador de miles"), ""),
            (self.text("Thousands: comma", "Miles: coma"), ","),
            (self.text("Thousands: point", "Miles: punto"), "."),
            (self.text("Thousands: space", "Miles: espacio"), " "),
        ]:
            self.thousands.addItem(caption, value)
        if profile:
            self.thousands.setCurrentIndex(self.thousands.findData(profile.thousands))
        self.thousands.setToolTip(
            self.text(
                "Explicit grouping only; decimal and thousands marks must differ.",
                "Agrupación explícita; decimales y miles deben usar marcas distintas.",
            )
        )
        options.addWidget(self.thousands, 1, 2, 1, 2)
        layout.addLayout(options)
        self.table = QTableWidget()
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        self.table.setToolTip(
            self.text(
                "Staging preview: edit values or select a "
                "rectangle; choose one destination per column.",
                "Vista de preparación: edite valores o "
                "seleccione un rectángulo; asigne cada columna.",
            )
        )
        layout.addWidget(self.table, 1)
        mapping_hint = QHBoxLayout()
        mapping_icon = QLabel()
        mapping_icon.setPixmap(self.icons.get("column_mapping", QIcon()).pixmap(28, 28))
        mapping_hint.addWidget(mapping_icon)
        mapping_label = QLabel(
            self.text(
                "Assign input columns above; tick only the rows you want to import.",
                "Asigne las columnas arriba y marque solo las filas "
                "que desea importar.",
            )
        )
        mapping_label.setWordWrap(True)
        mapping_hint.addWidget(mapping_label, 1)
        layout.addLayout(mapping_hint)
        self.preview_size = QLabel()
        self.preview_size.setWordWrap(True)
        layout.addWidget(self.preview_size)
        self.selection_button = QPushButton(
            self.text("Use selected cells", "Usar celdas seleccionadas")
        )
        self.selection_button.setToolTip(
            self.text(
                "Keep the selected rectangle and its column "
                "headers; original file stays unchanged.",
                "Conservar el rectángulo y sus encabezados; el "
                "archivo original no cambia.",
            )
        )
        self.selection_button.clicked.connect(self.use_selection)
        review_actions = QHBoxLayout()
        review_actions.addWidget(self.selection_button)
        self.exclude_empty_rows_button = QPushButton(
            self.text("Skip empty rows", "Omitir filas vacías")
        )
        self.exclude_empty_rows_button.setToolTip(
            self.text(
                "Skip rows with no mapped input values, such as "
                "merged-cell spacing. Blank cells within a kept task remain "
                "blank; the source file is unchanged.",
                "Quitar filas sin entradas asignadas, como espacios entre "
                "celdas combinadas. Los campos vacíos de una tarea se "
                "conservan; el archivo no cambia.",
            )
        )
        self.exclude_empty_rows_button.clicked.connect(self.exclude_empty_rows)
        review_actions.addWidget(self.exclude_empty_rows_button)
        self.validate_button = QPushButton(
            self.text("Validate preview", "Validar vista")
        )
        self.validate_button.setToolTip(
            self.text(
                "Check mapped values without applying them to an assessment.",
                "Comprobar los valores sin aplicarlos a una evaluación.",
            )
        )
        self.validate_button.clicked.connect(lambda: self.prepare(accept=False))
        review_actions.addWidget(self.validate_button)
        review_actions.addStretch(1)
        review_group = QGroupBox(self.text("Preview actions", "Acciones de la vista"))
        review_layout = QVBoxLayout(review_group)
        review_layout.setContentsMargins(10, 16, 10, 8)
        review_layout.setSpacing(4)
        review_layout.addLayout(review_actions)
        row_actions = QHBoxLayout()
        self.include_rows_button = QPushButton(
            self.text("Include selected rows", "Incluir filas seleccionadas")
        )
        self.exclude_rows_button = QPushButton(
            self.text("Skip selected rows", "Omitir filas seleccionadas")
        )
        self.include_all_button = QPushButton(self.text("Include all", "Incluir todas"))
        self.include_rows_button.clicked.connect(lambda: self.set_selected_rows(True))
        self.exclude_rows_button.clicked.connect(lambda: self.set_selected_rows(False))
        self.include_all_button.clicked.connect(self.include_all_rows)
        for control in (self.include_rows_button, self.exclude_rows_button):
            control.setToolTip(
                self.text(
                    "Select cells or row numbers in the preview, then include or skip "
                    "those rows. Ctrl selects separate ranges. "
                    "Source files stay unchanged.",
                    "Seleccione celdas o números de fila y luego incluya u omita esas "
                    "filas. Ctrl selecciona rangos separados. El archivo no cambia.",
                )
            )
        self.include_all_button.setToolTip(
            self.text(
                "Restore every staged data row without changing the column mapping.",
                "Restaurar todas las filas sin cambiar la asignación de columnas.",
            )
        )
        for button in (
            self.include_rows_button,
            self.exclude_rows_button,
            self.include_all_button,
        ):
            button.setAutoDefault(False)
            row_actions.addWidget(button)
        self.row_summary = QLabel()
        row_actions.addWidget(self.row_summary, 1)
        review_layout.addLayout(row_actions)
        layout.addWidget(review_group)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color: #AD302B;")
        status_row = QHBoxLayout()
        status_group = QGroupBox(self.text("Import status", "Estado de importación"))
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(10, 16, 10, 8)
        status_layout.addWidget(self.error)
        status_group.setStyleSheet(
            "QGroupBox {background:#EAF7F8;border:1px solid #B8DDE3;"
            "border-radius:4px;margin-top:8px;}"
        )
        status_row.addWidget(status_group, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        paste = buttons.button(QDialogButtonBox.Ok)
        assert paste is not None
        paste.setText(self.text("Paste", "Pegar"))
        paste.setObjectName("calculateButton")
        set_action_icon(paste, assessment_action_icon("paste", light=True), 28)
        cancel = buttons.button(QDialogButtonBox.Cancel)
        assert cancel is not None
        cancel.setText(self.text("Cancel", "Cancelar"))
        set_action_icon(cancel, self.icons.get("cancel", QIcon()), 28)
        buttons.accepted.connect(self.prepare)
        buttons.rejected.connect(self.cancelled.emit)
        buttons.setVisible(not embedded)
        status_row.addWidget(buttons)
        layout.addLayout(status_row)
        self.header_option.toggled.connect(self.render_preview)
        for control, name in (
            (self.selection_button, "select_cell_range"),
            (self.exclude_empty_rows_button, "remove_empty_rows"),
            (self.validate_button, "validate_import"),
            (self.open_file, "worksheet"),
            (self.read_range, "select_cell_range"),
            (self.update_preview, "refresh"),
            (self.include_rows_button, "include_rows"),
            (self.exclude_rows_button, "skip_rows"),
            (self.include_all_button, "include_all_rows"),
        ):
            set_action_icon(control, self.icons.get(name, QIcon()), 28)
        set_action_icon(self.clipboard_button, assessment_action_icon("paste"), 28)
        self.mappings: list[QComboBox] = []
        self.render_preview()
        self._base_rows = self.rows
        self.table.itemChanged.connect(self.preview_cell_changed)
        self.source_text.textChanged.connect(self.mark_source_stale)
        self.separator.currentTextChanged.connect(self.mark_source_stale)
        self.encoding.currentIndexChanged.connect(self.mark_source_stale)
        self.range_edit.textEdited.connect(self.mark_source_stale)
        self.validation_timer = QTimer(self)
        self.validation_timer.setSingleShot(True)
        self.validation_timer.setInterval(250)
        self.validation_timer.timeout.connect(
            lambda: self.prepare(accept=False, focus_error=False)
        )
        for control in (self.units, self.decimal, self.thousands):
            control.currentIndexChanged.connect(self.queue_validation)
        self.start.valueChanged.connect(self.queue_validation)
        for combo in self.mappings:
            combo.currentIndexChanged.connect(self.queue_validation)
        if profile:
            self.decimal.setCurrentIndex(self.decimal.findData(profile.decimal))
        for control in (
            self.header_option,
            self.start,
            self.units,
            self.decimal,
            self.thousands,
        ):
            control.setToolTip(
                control.toolTip()
                or self.text(
                    "Interpret the selected source; changes apply "
                    "only after validation.",
                    "Interpretar la selección; se aplica solo después de validar.",
                )
            )
        self.queue_validation()

    def text(self, english: str, spanish: str) -> str:
        """Choose an interface caption without translating source values.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Caption for the selected interface language.
        """
        return spanish if self.language is Language.SPANISH else english

    def row_label(self, row: int) -> str:
        """Return a stable original-preview row number or the All checkbox caption.

        Args:
            row: Table row, with zero reserved for column mapping.

        Returns:
            Original staged row number, independent of inclusion filtering.
        """
        return (
            self.text("Include", "Incluir")
            if row == 0
            else str(self._preview_indices[row - 1] + 1)
        )

    def row_included(self, row: int) -> bool:
        """Read current row/header checkbox state without changing staged cells.

        Args:
            row: Visible table row; zero represents all preview rows.

        Returns:
            True for included rows, or True for All only when no data rows are skipped.
        """
        return (
            all(i not in self._excluded_rows for i in self._preview_indices)
            if row == 0
            else self._preview_indices[row - 1] not in self._excluded_rows
        )

    def included_rows(self) -> tuple[tuple[str, ...], ...]:
        """Prepare the chosen header and included body in original source order.

        Args:
            None.

        Returns:
            Detached rows only; row choices are session data, never saved profiles.
        """
        body = tuple(
            self.rows[i] for i in self._preview_indices if i not in self._excluded_rows
        )
        return (
            (self.rows[self.header_row.value() - 1], *body)
            if self.header_option.isChecked()
            else body
        )

    def sync_row_inclusion(self) -> None:
        """Dim skipped rows without removing their editable staged data.

        Args:
            None.

        Returns:
            None; does not remove source rows or overwrite manual cell contents.
        """
        updating = self._updating
        self._updating = True
        for row, index in enumerate(self._preview_indices, 1):
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item is not None:
                    item.setForeground(
                        QColor("#7A858E" if index in self._excluded_rows else "#0B326C")
                    )
                    item.setBackground(
                        QBrush(QColor("#F0F1F2"))
                        if index in self._excluded_rows
                        else QBrush()
                    )
        self._updating = updating
        header = self.table.verticalHeader()
        if header is not None:
            viewport = header.viewport()
            if viewport is not None:
                viewport.update()
        if hasattr(self, "row_summary"):
            included = sum(i not in self._excluded_rows for i in self._preview_indices)
            self.row_summary.setText(
                self.text(
                    f"{included} included · "
                    f"{len(self._preview_indices) - included} skipped",
                    f"{included} incluidas · "
                    f"{len(self._preview_indices) - included} omitidas",
                )
            )

    def toggle_row(self, row: int) -> None:
        """Toggle one native row checkbox, or all data rows from its top checkbox.

        Args:
            row: Visible table row, zero selects the all-rows action.

        Returns:
            None; preview validation is refreshed without accepting project data.
        """
        indices = (
            self._preview_indices if row == 0 else (self._preview_indices[row - 1],)
        )
        include = not self.row_included(row)
        self._excluded_rows.difference_update(
            indices
        ) if include else self._excluded_rows.update(indices)
        self.sync_row_inclusion()
        self.queue_validation()

    def set_selected_rows(self, include: bool) -> None:
        """Include or skip every row touched by the current possibly disjoint selection.

        Args:
            include: True restores rows, False excludes them from importing.

        Returns:
            None; files and original staged row order remain unchanged.
        """
        indices = {
            self._preview_indices[i.row() - 1]
            for i in self.table.selectedIndexes()
            if i.row() > 0
        }
        self._excluded_rows.difference_update(
            indices
        ) if include else self._excluded_rows.update(indices)
        self.sync_row_inclusion()
        self.queue_validation()

    def include_all_rows(self) -> None:
        """Restore all preview body rows for review without resetting column mappings.

        Args:
            None.

        Returns:
            None; explicit validation still guards nonnumeric header/notes rows.
        """
        self._excluded_rows.clear()
        self.sync_row_inclusion()
        self.queue_validation()

    def header_row_changed(self) -> None:
        """Choose another header and initially skip its preceding explanatory rows.

        Args:
            None.

        Returns:
            None; preceding rows remain visible and can be explicitly included again.
        """
        self._excluded_rows.update(range(self.header_row.value() - 1))
        self._profile = None
        self.render_preview()
        self.queue_validation()

    def render_preview(self) -> None:
        """Rebuild staged rows and column mapping after header/range changes.

        Args:
            None.

        Returns:
            None; column suggestions are editable and no source is mutated.
        """
        if self.rows is not self._row_snapshot:
            self._excluded_rows.clear()
            self.header_row.blockSignals(True)
            self.header_row.setRange(1, max(1, len(self.rows)))
            self.header_row.setValue(1)
            self.header_row.blockSignals(False)
            self._row_snapshot = self.rows
        header = self.header_option.isChecked()
        self.header_row.setEnabled(header)
        header_index = self.header_row.value() - 1 if header else None
        self._preview_indices = tuple(
            i for i in range(len(self.rows)) if i != header_index
        )
        rows = tuple(self.rows[i] for i in self._preview_indices)
        fields = assessment_input_fields(self.source)
        offset = fields.index(self.start_field) if self.start_field in fields else 0
        self._updating = True
        self.table.clear()
        self.table.setColumnCount(len(self.rows[0]))
        self.table.setRowCount(len(rows) + 1)
        self.table.setHorizontalHeaderLabels(
            list(self.rows[header_index])
            if header_index is not None
            else [str(i + 1) for i in range(len(self.rows[0]))]
        )
        self.table.setVerticalHeaderLabels(
            [
                self.text("Map to", "Destino"),
                *(str(i + 1) for i in range(len(rows))),
            ]
        )
        self.mappings = []
        for column in range(len(self.rows[0])):
            combo = QComboBox()
            combo.addItem(self.text("Ignore column", "Ignorar columna"), None)
            for field in fields:
                combo.addItem(task_field_caption(field, self.language), field)
            suggested = (
                clipboard_field(self.rows[header_index][column])
                if header_index is not None
                else (
                    fields[column + offset] if column + offset < len(fields) else None
                )
            )
            if (
                header
                and suggested is None
                and self.rows[header_index if header_index is not None else 0][column]
                .strip()
                .casefold()
                in ("task #", "task number", "tarea #")
                and any(any(char.isalpha() for char in row[column]) for row in rows)
            ):
                suggested = "task_name"
            if (
                self._profile
                and self._profile.configured
                and len(self._profile.fields) == len(self.rows[0])
            ):
                suggested = self._profile.fields[column]
            combo.setCurrentIndex(max(0, combo.findData(suggested)))
            combo.currentIndexChanged.connect(self.queue_validation)
            combo.setToolTip(
                self.text(
                    "Destination input, or Ignore. Duplicate "
                    "destinations are rejected.",
                    "Entrada de destino o Ignorar. No se permiten destinos repetidos.",
                )
            )
            self.table.setCellWidget(0, column, combo)
            self.mappings.append(combo)
            for index, row in enumerate(rows, 1):
                item = QTableWidgetItem(row[column])
                item.setToolTip(row[column])
                self.table.setItem(index, column, item)
        if not isinstance(self.table.verticalHeader(), ImportRowHeader):
            row_header = ImportRowHeader(self.table, self.row_included, self.row_label)
            row_header.setToolTip(
                self.text(
                    "Tick rows to include. Untick unwanted rows; "
                    "source data stays unchanged.",
                    "Marque las filas que desea incluir; el origen no cambia.",
                )
            )
            row_header.toggled.connect(self.toggle_row)
            self.table.setVerticalHeader(row_header)
        self.sync_row_inclusion()
        header_view = self.table.horizontalHeader()
        assert header_view is not None
        header_view.setMinimumSectionSize(140)
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._updating = False
        if hasattr(self, "preview_size"):
            self.preview_size.setText(
                self.text(
                    f"{len(rows)} data rows · {len(self.rows[0])} columns"
                    " · Maximum 100 tasks per import",
                    f"{len(rows)} filas · {len(self.rows[0])} columnas"
                    " · Máximo 100 tareas por importación",
                )
            )
        if hasattr(self, "preview_size") and not self._has_source:
            self.preview_size.setText(
                self.text(
                    "Column layout only · Paste sample cells or "
                    "open a file to preview data",
                    "Solo estructura · Pegue celdas o abra un "
                    "archivo para revisar datos",
                )
            )

    def prepare(self, *, accept: bool = True, focus_error: bool = True) -> None:
        """Validate staged values and optionally request explicit host acceptance.

        Args:
            accept: False only updates diagnostics; True requests the modal Apply.
            focus_error: Reveal the first invalid row for explicit Validate/Paste.
                Background diagnostics keep the current viewport and selection.

        Returns:
            None; validation errors stay in this preview with no accepted replacement.
        """
        try:
            self._updating = True
            for row, column in self._invalid_cells:
                cell = self.table.item(row, column)
                if cell is not None:
                    cell.setBackground(QBrush())
                    cell.setToolTip(cell.text())
            self._invalid_cells.clear()
            self._updating = False
            self.sync_row_inclusion()
            self.replacement = None
            if not self._has_source:
                raise ValueError(
                    self.text(
                        "Choose a file or paste source data first.",
                        "Elija un archivo o pegue datos primero.",
                    )
                )
            if self._source_error:
                raise ValueError(
                    self.text(
                        "Correct the source error and update the preview first.",
                        "Corrija el origen y actualice la vista primero.",
                    )
                )
            import_rows = self.included_rows()
            if len(import_rows) <= int(self.header_option.isChecked()):
                raise ValueError(
                    self.text(
                        "Include at least one data row.",
                        "Incluya al menos una fila de datos.",
                    )
                )
            self.replacement = prepare_import(
                self.source, import_rows, self.profile(), self.start.value() - 1
            )
        except (ValueError, DraftError) as error:
            self.error.setStyleSheet("color:#AD302B;")
            from ergotools.application.assessment_clipboard import ClipboardRowError

            if isinstance(error, ClipboardRowError):
                self._updating = True
                included = [
                    i + 1
                    for i, n in enumerate(self._preview_indices)
                    if n not in self._excluded_rows
                ]
                offset = error.row_index - (self.start.value() - 1)
                row = included[offset] if 0 <= offset < len(included) else 1
                for column in range(self.table.columnCount()):
                    cell = self.table.item(row, column)
                    if cell is not None:
                        self._invalid_cells.append((row, column))
                        cell.setBackground(QColor("#FDE5E3"))
                        cell.setToolTip(assessment_import_error(error, self.language))
                self._updating = False
                if focus_error:
                    self.table.scrollToItem(self.table.item(row, 0))
            self.error.setText(assessment_import_error(error, self.language))
            return
        self.error.setStyleSheet("color:#0B326C;")
        self.error.setText(
            self.text(
                "Ready to import. Blank mapped cells replace "
                "existing values; other columns remain "
                "unchanged.",
                "Listo para importar. Los vacíos asignados "
                "reemplazan valores existentes; las otras "
                "columnas se conservan.",
            )
        )
        assert self.replacement is not None
        selected_tasks = self.replacement.tasks[
            self.start.value() - 1 : self.start.value()
            - 1
            + len(import_rows)
            - int(self.header_option.isChecked())
        ]
        required = tuple(
            field
            for field in assessment_input_fields(self.source)
            if field != "task_name"
        )
        incomplete = sum(
            task_has_data(task)
            and any(getattr(task, field) is None for field in required)
            for task in selected_tasks
        )
        if incomplete:
            self.error.setStyleSheet("color:#8A5C00;")
            self.error.setText(
                self.text(
                    f"{incomplete} started tasks have missing inputs. "
                    "They may be imported and completed later; "
                    "results remain incomplete.",
                    f"{incomplete} tareas iniciadas tienen datos faltantes. "
                    "Puede importarlas y completarlas después; "
                    "los resultados serán incompletos.",
                )
            )
        if accept:
            self.prepared.emit()

    def build_source_controls(self, layout: QVBoxLayout, text: str) -> None:
        """Build a compact source bar and editable Unicode clipboard staging area.

        Args:
            layout: Owned panel layout; shared by modal and embedded Settings hosts.
            text: Initial Unicode clipboard text, never persisted.

        Returns:
            None; file reads occur only after explicit source/sheet/range actions.
        """
        group = QGroupBox(self.text("Source data", "Datos de origen"))
        source = QGridLayout(group)
        self.open_file = QPushButton(self.text("Open file…", "Abrir archivo…"))
        self.open_file.setEnabled(self.file_reader is not None)
        self.open_file.setToolTip(
            self.text(
                "Read values from a file without modifying it.",
                "Leer valores sin modificar el archivo.",
            )
        )
        self.open_file.clicked.connect(self.choose_file)
        source.addWidget(self.open_file, 0, 0)
        self.sheet = QComboBox()
        self.sheet.setPlaceholderText(self.text("Worksheet", "Hoja"))
        self.sheet.setMinimumContentsLength(5)
        self.sheet.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.sheet.setEnabled(False)
        self.sheet.setToolTip(
            self.text(
                "Preview any worksheet; only the chosen range is imported.",
                "Revise cualquier hoja; solo se importa el rango elegido.",
            )
        )
        self.sheet.activated.connect(lambda: self.reload_file(True))
        source.addWidget(self.sheet, 0, 1)
        self.range_edit = QLineEdit()
        self.range_edit.setMinimumWidth(70)
        self.range_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.range_edit.setPlaceholderText(self.text("Range: B4:F25", "Rango: B4:F25"))
        self.range_edit.setToolTip(
            self.text(
                "A1 rectangle in the selected worksheet or "
                "current text table. Blank restores the source "
                "preview.",
                "Rectángulo A1 en la hoja o tabla de texto. "
                "Vacío restaura la vista de origen.",
            )
        )
        source.addWidget(self.range_edit, 0, 2)
        self.read_range = QPushButton(self.text("Show range", "Mostrar rango"))
        self.read_range.clicked.connect(self.load_range)
        source.addWidget(self.read_range, 0, 3)
        self.separator = QComboBox()
        self.separator.setEditable(True)
        for caption, value in [
            (self.text("Auto separator", "Separador: auto"), "auto"),
            (self.text("Tab", "Tabulación"), "\t"),
            (self.text("Comma", "Coma"), ","),
            (self.text("Semicolon", "Punto y coma"), ";"),
            (self.text("Pipe", "Barra vertical"), "|"),
        ]:
            self.separator.addItem(caption, value)
        self.separator.setToolTip(
            self.text(
                "Text columns: automatic, a listed separator, "
                "or type one custom character.",
                "Columnas de texto: automático, separador de "
                "lista o un carácter personalizado.",
            )
        )
        self.encoding = QComboBox()
        for caption, value in [
            (self.text("Auto encoding", "Codificación: auto"), "auto"),
            ("UTF-8", "utf-8-sig"),
            ("UTF-16", "utf-16"),
            ("Windows-1252", "cp1252"),
            ("ISO-8859-1", "iso8859-1"),
            ("ISO-8859-15", "iso8859-15"),
        ]:
            self.encoding.addItem(caption, value)
        self.encoding.setEnabled(False)
        self.encoding.setToolTip(
            self.text(
                "Text files only. Unicode clipboard and XLSX do"
                " not require decoding choices.",
                "Solo archivos de texto. El portapapeles "
                "Unicode y XLSX no requieren elegir "
                "codificación.",
            )
        )
        if self._profile:
            index = self.separator.findData(self._profile.delimiter)
            if index >= 0:
                self.separator.setCurrentIndex(index)
            else:
                self.separator.setEditText(self._profile.delimiter)
            self.encoding.setCurrentIndex(
                self.encoding.findData(self._profile.encoding)
            )
        source.addWidget(self.separator, 1, 0)
        source.addWidget(self.encoding, 1, 1)
        self.update_preview = QPushButton(
            self.text("Update preview", "Actualizar vista")
        )
        self.update_preview.setToolTip(
            self.text(
                "Re-read the file with these choices, or parse "
                "the staged clipboard text.",
                "Volver a leer el archivo o interpretar el "
                "texto preparado con estas opciones.",
            )
        )
        self.update_preview.clicked.connect(self.update_source)
        source.addWidget(self.update_preview, 1, 3)
        self.clipboard_button = QPushButton(
            self.text("Paste clipboard", "Pegar portapapeles")
        )
        self.clipboard_button.setToolTip(
            self.text(
                "Stage copied cells or delimited text, then review the preview.",
                "Preparar celdas copiadas o texto delimitado y revisar la vista.",
            )
        )
        self.clipboard_button.clicked.connect(self.read_clipboard)
        source.addWidget(self.clipboard_button, 1, 2)
        self.source_text = QPlainTextEdit(text)
        self.source_text.setMaximumHeight(85)
        self.source_text.setPlaceholderText(
            self.text(
                "Paste source text here, then Update preview—or open a file.",
                "Pegue texto aquí y actualice la vista, o abra un archivo.",
            )
        )
        self.source_text.setToolTip(
            self.text(
                "Temporary staging data. Never stored in application preferences.",
                "Datos temporales; nunca se guardan en las preferencias.",
            )
        )
        source.addWidget(self.source_text, 2, 0, 1, 4)
        self.source_notice = QLabel(
            self.text(
                "Clipboard text · Source file remains unchanged",
                "Texto del portapapeles · El archivo de origen no cambia",
            )
        )
        self.source_notice.setWordWrap(True)
        source.addWidget(self.source_notice, 3, 0, 1, 4)
        for button in (
            self.open_file,
            self.read_range,
            self.clipboard_button,
            self.update_preview,
        ):
            button.setStyleSheet("QPushButton {min-width:0;padding:4px 8px;}")
        if self.embedded:
            # Settings reflows these same controls into its narrower content pane.
            controls = (
                self.open_file,
                self.sheet,
                self.range_edit,
                self.read_range,
                self.separator,
                self.encoding,
                self.clipboard_button,
                self.update_preview,
            )
            for widget in (*controls, self.source_text, self.source_notice):
                source.removeWidget(widget)
            for index, widget in enumerate(controls):
                source.addWidget(widget, index // 2, index % 2)
            source.addWidget(self.source_text, 4, 0, 1, 2)
            source.addWidget(self.source_notice, 5, 0, 1, 2)
        layout.addWidget(group)

    def profile(self, *, mapping: bool = True) -> ImportProfile:
        """Collect interpretation choices without copying staged values.

        Args:
            mapping: False reads parsing only so invalid mappings can be replaced.

        Returns:
            Explicit configured profile for this tool, with no paths/ranges/source rows.

        Raises:
            ValueError: A separator, grouping choice or mapping is invalid.
        """
        separator = self.separator.currentData()
        if self.separator.currentText() != self.separator.itemText(
            self.separator.currentIndex()
        ):
            separator = self.separator.currentText()
        return ImportProfile(
            assessment_kind(self.source),
            delimiter=separator
            if isinstance(separator, str)
            else self.separator.currentText(),
            encoding=self.encoding.currentData(),
            decimal=self.decimal.currentData(),
            thousands=self.thousands.currentData(),
            units=self.units.currentData(),
            header=self.header_option.isChecked(),
            fields=tuple(combo.currentData() for combo in self.mappings)
            if mapping
            else (),
            configured=mapping,
            headers=self.rows[self.header_row.value() - 1]
            if mapping and self.header_option.isChecked()
            else (),
        )

    def choose_file(self) -> None:
        """Use the system selector and stage a supported file without destination edits.

        Args:
            None.

        Returns:
            None; Cancel retains the existing staged source and parsing choices.
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.text("Import task data", "Importar tareas"),
            "",
            "CSV / TSV / Excel (*.csv *.tsv *.txt *.xlsx *.xlsm)",
        )
        if path:
            self._path = path
            self.sheet.clear()
            self.range_edit.clear()
            self.reload_file(True)

    def reload_file(self, reset_range: bool = False) -> None:
        """Read one selected sheet/range with explicitly injected file capability.

        Args:
            reset_range: Clear the prior sheet's range when switching source/sheet.

        Returns:
            None; failures retain the prior preview and block applying it.
        """
        if not self._path or self.file_reader is None:
            return
        try:
            result = self.file_reader.read(
                self._path,
                self.profile(mapping=False),
                self.sheet.currentText(),
                "" if reset_range else self.range_edit.text().strip(),
            )
            # A sheet switch uses the newly selected exact name, not the first sheet.
            self._source_error = False
            self._has_source = True
            self._base_rows = result.rows
            self.rows = result.rows
            self.sheet.blockSignals(True)
            self.sheet.clear()
            for sheet_name in result.sheets:
                self.sheet.addItem(self.icons.get("worksheet", QIcon()), sheet_name)
            self.sheet.setCurrentText(result.sheet)
            self.sheet.blockSignals(False)
            self.sheet.setEnabled(bool(result.sheets))
            self.encoding.setEnabled(not bool(result.sheets))
            self.separator.setEnabled(not bool(result.sheets))
            self.range_edit.setText(result.cell_range)
            self.source_notice.setText(
                self._path
                + (
                    (" · " + result.sheet if result.sheet else "")
                    + (" · " + result.cell_range if result.cell_range else "")
                )
            )
            self.source_notice.setToolTip(self.source_notice.text())
            self.source_text.blockSignals(True)
            self.source_text.clear()
            self.source_text.blockSignals(False)
            self.header_option.setChecked(
                self._profile.header
                if self._profile
                and self._profile.configured
                and len(self._profile.fields) == len(self.rows[0])
                else any(clipboard_field(c) for c in self.rows[0])
            )
            self.render_preview()
            self.queue_validation()
            self.error.setText(
                self.text(
                    "Preview only. Select cells or an exact range; "
                    "only mapped inputs are applied. Formula cells "
                    "cannot be imported.",
                    "Solo vista previa. Elija celdas o un rango; se"
                    " aplican solo entradas asignadas. No se "
                    "importan fórmulas.",
                )
            )
        except (OSError, ValueError) as error:
            self._source_error = True
            if hasattr(self, "validation_timer"):
                self.validation_timer.stop()
            self.error.setText(assessment_import_error(error, self.language))

    def update_source(self) -> None:
        """Parse editable staged text, or reload a file with changed format choices.

        Args:
            None.

        Returns:
            None; no imported values enter the project until host acceptance.
        """
        if self.source_text.toPlainText().strip():
            try:
                rows = parse_import_text(
                    self.source_text.toPlainText(),
                    self.profile(mapping=False).delimiter,
                )
                self._path = ""
                self._source_error = False
                self._has_source = True
                self._base_rows = self.rows = rows
                self._profile = None
                self.sheet.clear()
                self.sheet.setEnabled(False)
                self.encoding.setEnabled(False)
                self.separator.setEnabled(True)
                self.range_edit.clear()
                self.header_option.setChecked(any(clipboard_field(c) for c in rows[0]))
                self.render_preview()
                self.error.clear()
                self.source_notice.setText(
                    self.text(
                        "Staged Unicode text · No file modified",
                        "Texto Unicode preparado · Ningún archivo modificado",
                    )
                )
            except ValueError as error:
                self._source_error = True
                self.error.setText(assessment_import_error(error, self.language))
        elif self._path:
            self.reload_file()

    def load_range(self) -> None:
        """Stage an A1 rectangle from the source, keeping original files untouched.

        Args:
            None.

        Returns:
            None; out-of-bounds/invalid ranges retain the prior preview.
        """
        if self._path:
            self.reload_file()
            return
        try:
            token = self.range_edit.text().strip().upper()
            rows = self._base_rows
            if token:
                match = re.fullmatch(r"([A-Z]+)([1-9]\d*):([A-Z]+)([1-9]\d*)", token)
                if match is None:
                    raise ValueError(
                        self.text(
                            "Use a range such as B4:F25.", "Use un rango como B4:F25."
                        )
                    )
                a, top, b, bottom = match.groups()
                left = self.column_number(a)
                right = self.column_number(b)
                first, last = int(top), int(bottom)
                if not (
                    1 <= left <= right <= len(rows[0])
                    and 1 <= first <= last <= len(rows)
                ):
                    raise ValueError(
                        self.text(
                            "Range is outside the source data.",
                            "El rango está fuera de los datos de origen.",
                        )
                    )
                rows = tuple(row[left - 1 : right] for row in rows[first - 1 : last])
            self.rows = rows
            self._source_error = False
            self._profile = None
            self.render_preview()
            self.error.clear()
        except ValueError as error:
            self.error.setText(str(error))

    @staticmethod
    def column_number(letters: str) -> int:
        """Convert validated A1 column letters without a spreadsheet dependency in Qt.

        Args:
            letters: Uppercase alphabetic source column.

        Returns:
            One-based column index.
        """
        result = 0
        for letter in letters:
            result = result * 26 + ord(letter) - ord("A") + 1
        return result

    def use_selection(self) -> None:
        """Keep a single selected preview rectangle and matching mapped headers.

        Args:
            None.

        Returns:
            None; disjoint selections require an explicit contiguous rectangle.
        """
        selections = self.table.selectedRanges()
        if len(selections) != 1 or selections[0].topRow() == 0:
            self.error.setText(
                self.text(
                    "Select one rectangle of data cells, excluding the mapping row.",
                    "Seleccione un rectángulo de datos sin la fila de asignación.",
                )
            )
            return
        area = selections[0]
        offset = int(self.header_option.isChecked())
        indices = self._preview_indices[area.topRow() - 1 : area.bottomRow()]
        columns = slice(area.leftColumn(), area.rightColumn() + 1)
        values = tuple(self.rows[i] for i in indices)
        if offset:
            values = (self.rows[self.header_row.value() - 1], *values)
        exclusions = {
            j + offset for j, i in enumerate(indices) if i in self._excluded_rows
        }
        candidate_rows = tuple(row[columns] for row in values)
        try:
            candidate_profile = replace(
                self.profile(mapping=False),
                fields=tuple(combo.currentData() for combo in self.mappings)[columns],
                headers=candidate_rows[0] if offset else (),
                configured=True,
            )
        except ValueError as error:
            self.error.setText(assessment_import_error(error, self.language))
            return
        self.rows = candidate_rows
        self._profile = candidate_profile
        self.render_preview()
        self._excluded_rows = exclusions
        self.sync_row_inclusion()
        self.error.clear()
        self.queue_validation()

    def exclude_empty_rows(self) -> None:
        """Skip empty mapped rows reversibly, retaining all staged source data.

        Args:
            None.

        Returns:
            None; named/incomplete tasks stay present and ignored formulas never
            keep otherwise empty spacer rows. No source file or assessment changes.
        """
        try:
            profile = self.profile()
        except ValueError as error:
            self.error.setText(assessment_import_error(error, self.language))
            return
        columns = tuple(
            i for i, field in enumerate(profile.fields) if field is not None
        )
        if not columns:
            self.error.setText(
                self.text(
                    "Map the input columns first.", "Asigne primero las columnas."
                )
            )
            return
        empty = {
            i
            for i in self._preview_indices
            if not any(self.rows[i][c].strip() for c in columns)
        }
        self._excluded_rows.update(empty)
        self.sync_row_inclusion()
        self.queue_validation()
        self.error.setText(
            self.text(
                f"Skipped {len(empty)} empty rows; Include all restores them.",
                f"Se omitieron {len(empty)} filas vacías; Incluir todas las restaura.",
            )
        )

    def preview_cell_changed(self, item: QTableWidgetItem) -> None:
        """Edit staged cells while retaining assessment and source-file ownership.

        Args:
            item: User-edited data cell; mapping row is owned by combos.

        Returns:
            None; source text/file remains available to restore the original preview.
        """
        if self._updating or item.row() == 0:
            return
        index = self._preview_indices[item.row() - 1]
        rows = [list(row) for row in self.rows]
        rows[index][item.column()] = item.text()
        self.rows = tuple(tuple(row) for row in rows)
        self._row_snapshot = self.rows
        self._has_source = True
        item.setToolTip(item.text())
        self.error.clear()
        self.queue_validation()

    def read_clipboard(self) -> None:
        """Stage Unicode clipboard contents without importing project data.

        Args:
            None.

        Returns:
            None; empty clipboard text retains the visible preview.
        """
        clipboard = QApplication.clipboard()
        if clipboard is not None and clipboard.text().strip():
            self.source_text.setPlainText(clipboard.text())
            self.update_source()

    def queue_validation(self) -> None:
        """Coalesce staged mapping/value diagnostics without accepting a project edit.

        Args:
            None.

        Returns:
            None; file failures keep their original actionable diagnostic.
        """
        if not self._active:
            return
        self.replacement = None
        if (
            hasattr(self, "validation_timer")
            and self._has_source
            and not self._source_error
        ):
            self.validation_timer.start()

    def mark_source_stale(self) -> None:
        """Require a new preview after text, delimiter, encoding or range edits.

        Args:
            None.

        Returns:
            None; existing rows remain inspectable but cannot be applied as new data.
        """
        if not self._active or self._updating or not self._has_source:
            return
        self._source_error = True
        self.replacement = None
        if hasattr(self, "validation_timer"):
            self.validation_timer.stop()
        self.error.setText(
            self.text(
                "Source choices changed. Update preview or Show"
                " range before importing.",
                "Cambió el origen. Actualice la vista o muestre"
                " el rango antes de importar.",
            )
        )

    def stop_validation(self) -> None:
        """Stop owned diagnostics when a modal/Settings host finishes its lifetime.

        Args:
            None.

        Returns:
            None; a validated accepted replacement remains available to its owner.
        """
        self._active = False
        self.validation_timer.stop()
