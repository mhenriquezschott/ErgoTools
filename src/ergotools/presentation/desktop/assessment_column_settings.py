"""Live shared-grid preview for optional personal assessment columns.

Presentation layer. Only visibility choices are collected; fixed sample tasks/results
are detached and never accepted into a project or personal preference payload.
"""

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.assessment_clipboard import (
    assessment_input_fields,
    prepare_assessment_paste,
)
from ergotools.application.assessment_columns import (
    AssessmentColumns,
    assessment_column_keys,
    optional_assessment_columns,
)
from ergotools.application.job_calculation import (
    blank_job_source,
    calculate_job_measurement,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid


class AssessmentColumnSettings(QWidget):
    """Hold per-tool visibility drafts with a read-only instance of the real grid."""

    def __init__(
        self,
        profiles: tuple[AssessmentColumns, ...],
        language: Language,
        units: MeasurementSystem,
        convention: DecimalConvention,
        parent: QWidget | None = None,
    ) -> None:
        """Build independent column choices and a live sample preview.

        Args:
            profiles: Previously accepted personal visibility choices.
            language: English/Spanish captions and grid headers.
            units: Sample display units, independent of projects.
            convention: Sample numeric display convention.
            parent: Owned Settings page.

        Returns:
            None; opening, toggling and previewing never accept project inputs.
        """
        super().__init__(parent)
        self.language, self.units, self.convention = language, units, convention
        self._drafts = {p.kind: p for p in profiles}
        self._grids: dict[AssessmentKind, AssessmentTaskGrid] = {}
        self.checks: dict[str, QCheckBox] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.addWidget(QLabel(self.text("Tool", "Herramienta")))
        self.tools = QComboBox()
        for name, kind in (
            ("LiFFT", AssessmentKind.LIFFT),
            ("DUET", AssessmentKind.DUET),
            ("ST", AssessmentKind.TST),
        ):
            self.tools.addItem(name, kind)
        self.tools.setToolTip(
            self.text(
                "Independent column visibility for each tool.",
                "Columnas independientes por herramienta.",
            )
        )
        bar.addWidget(self.tools)
        bar.addStretch(1)
        self.all_button = QPushButton(self.text("Show all", "Mostrar todas"))
        self.familiar_button = QPushButton(
            self.text("Hide task names", "Ocultar nombres")
        )
        self.all_button.setToolTip(
            self.text(
                "Restore all optional columns for this tool.",
                "Restaurar columnas opcionales de esta herramienta.",
            )
        )
        self.familiar_button.setToolTip(
            self.text(
                "Keep the familiar numeric layout, preserving saved task names.",
                "Conservar la vista numérica sin borrar nombres guardados.",
            )
        )
        self.all_button.clicked.connect(lambda: self.preset(False))
        self.familiar_button.clicked.connect(lambda: self.preset(True))
        bar.addWidget(self.all_button)
        bar.addWidget(self.familiar_button)
        root.addLayout(bar)
        choices = QGroupBox(self.text("Visible columns", "Columnas visibles"))
        self.choices = QGridLayout(choices)
        root.addWidget(choices)
        hint = QLabel(
            self.text(
                "Required inputs stay visible. Hiding a column "
                "preserves its data, calculations and copying.",
                "Las entradas obligatorias siguen visibles. "
                "Ocultar conserva datos, cálculos y copiado.",
            )
        )
        hint.setWordWrap(True)
        root.addWidget(hint)
        preview = QGroupBox(
            self.text("Live preview · sample data", "Vista previa · datos de ejemplo")
        )
        self.preview = QVBoxLayout(preview)
        root.addWidget(preview)
        root.addStretch(1)
        self.tools.currentIndexChanged.connect(self.show_tool)
        self.show_tool()

    def text(self, english: str, spanish: str) -> str:
        """Choose captions without translating saved task names.

        Args:
            english: English interface text.
            spanish: Spanish interface text.

        Returns:
            Caption in this Settings window's language.
        """
        return spanish if self.language is Language.SPANISH else english

    def show_tool(self) -> None:
        """Render this tool's required/optional choices and shared sample grid.

        Args:
            None.

        Returns:
            None; switches retain all tool drafts and temporary sample values.
        """
        while self.choices.count():
            item = self.choices.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        self.checks = {}
        kind = self.tools.currentData()
        hidden = self._drafts.get(kind, AssessmentColumns(kind)).hidden
        captions = {
            "task_number": ("Task number", "Número de tarea"),
            "task_name": ("Task name", "Nombre de tarea"),
            "lever_arm": ("Lever arm", "Brazo de palanca"),
            "load": ("Load", "Carga"),
            "moment": ("Moment", "Momento"),
            "direction": ("Task type", "Tipo de tarea"),
            "omni_res_scale": ("OMNI-RES", "OMNI-RES"),
            "repetitions": ("Repetitions", "Repeticiones"),
            "damage": ("Task damage", "Daño por tarea"),
            "share": ("% Total damage", "% Daño total"),
        }
        for index, key in enumerate(assessment_column_keys(kind)):
            optional = key in optional_assessment_columns(kind)
            box = QCheckBox(self.text(*captions[key]))
            box.setChecked(key not in hidden)
            box.setEnabled(optional)
            box.setToolTip(
                self.text(
                    "Show or hide this optional column.",
                    "Mostrar u ocultar esta columna opcional.",
                )
                if optional
                else self.text(
                    "Required input: always visible.",
                    "Entrada obligatoria: siempre visible.",
                )
            )
            box.toggled.connect(self.changed)
            self.checks[key] = box
            self.choices.addWidget(box, index // 4, index % 4)
        for grid in self._grids.values():
            grid.hide()
        if kind not in self._grids:
            grid = AssessmentTaskGrid(
                self.language,
                self.convention,
                kind=kind,
                system=self.units,
                read_only=True,
                compact=True,
            )
            grid.setFixedHeight(132)
            source = blank_job_source(kind, self.units)
            first_name = self.text("Packing", "Embalaje")
            last_name = self.text("Loading", "Carga")
            rows = (
                ((first_name, "4", "100"), (last_name, "8", "200"))
                if kind is AssessmentKind.DUET
                else (
                    (
                        (first_name, "Handling Load", "30", "49.05", "100"),
                        (last_name, "Handling Load", "45", "98.1", "200"),
                    )
                    if kind is AssessmentKind.TST
                    else (
                        (first_name, "30", "49.05", "100"),
                        (last_name, "45", "98.1", "200"),
                    )
                )
            )
            sample = prepare_assessment_paste(
                source,
                rows,
                assessment_input_fields(source),
                input_system=MeasurementSystem.METRIC,
            )
            result = calculate_job_measurement("preview", "preview", sample, self.units)
            grid.load_source(sample, result.task_results)
            self._grids[kind] = grid
            self.preview.addWidget(grid)
        self._grids[kind].set_column_preferences(self.profiles())
        self._grids[kind].show()

    def changed(self) -> None:
        """Collect optional visibility and update the same preview without data edits.

        Args:
            None.

        Returns:
            None; required controls are not eligible for preferences.
        """
        kind = self.tools.currentData()
        self._drafts[kind] = AssessmentColumns(
            kind,
            tuple(
                key
                for key in optional_assessment_columns(kind)
                if not self.checks[key].isChecked()
            ),
        )
        if kind in self._grids:
            self._grids[kind].set_column_preferences(self.profiles())

    def preset(self, hide_names: bool) -> None:
        """Apply a convenient current-tool view without changing other tools.

        Args:
            hide_names: True hides only names; False restores all optional columns.

        Returns:
            None; sample and real task values are retained.
        """
        kind = self.tools.currentData()
        previous = self._drafts.get(kind, AssessmentColumns(kind))
        hidden = (
            tuple(
                key
                for key in optional_assessment_columns(kind)
                if key in previous.hidden or key == "task_name"
            )
            if hide_names
            else ()
        )
        self._drafts[kind] = AssessmentColumns(kind, hidden)
        self.show_tool()

    def profiles(self) -> tuple[AssessmentColumns, ...]:
        """Read typed visibility drafts for explicit host Apply.

        Args:
            None.

        Returns:
            Stable per-tool choices; no sample task/result data is included.
        """
        return tuple(
            sorted(
                (p for p in self._drafts.values() if p.hidden),
                key=lambda p: p.kind.value,
            )
        )
