"""Section-based preferences with owned drafts and explicit host Apply/Cancel.

Presentation layer. A left navigation tree selects one scrollable settings page.
All page controls remain alive while navigating, so tentative edits are retained;
only the host applies or persists accepted values. Scientific source values,
project lifetime and reset consent remain outside this dialog.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.settings import (
    DEFAULT_UNDO_LIMIT,
    MAX_UNDO_LIMIT,
    MIN_UNDO_LIMIT,
    Language,
)
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


class PreferencesDialog(QDialog):
    """Own five page drafts; section selection never applies or discards controls.

    section_items maps stable page identifiers to tree entries; pages owns their
    scroll areas. Existing language/units/precision/reset/gauge attributes remain the
    host's typed control boundary. Apply and Cancel remain visible outside page scroll.
    """

    def __init__(
        self,
        language: Language,
        units: MeasurementSystem,
        icons: Mapping[str, QIcon],
        *,
        parent: QWidget,
        convention: DecimalConvention = DecimalConvention.POINT,
        precision: DisplayPrecision | None = None,
        task_count: int | None = None,
        tool_name: str = "",
        assessment_context: str = "",
        project_open: bool = False,
        animated_focus: bool = True,
        gauge_markers: GaugeMarkerSettings | None = None,
        undo_limit: int = DEFAULT_UNDO_LIMIT,
        developer_enabled: bool = False,
    ) -> None:
        """Build General, Appearance, Project and Assessment sections with drafts.

        Args:
            language: Interface language; literal project/worker data is untouched.
            units: Initial display/default units; existing source units remain owned.
            icons: Existing packaged settings/cancel assets for footer actions.
            parent: GUI owner of this modal dialog.
            convention: Explicit point/comma input preference.
            precision: Project display decimals, or None for existing defaults.
            task_count: Active assessment count; None disables task-reset controls.
            tool_name: Active ergonomic tool caption, never an identity key.
            assessment_context: Host-projected project/worker/workplace identity;
                displayed literally and never used to locate or mutate a source.
            project_open: Enable project display controls only with an open project.
            animated_focus: Personal body-camera animation preference.
            undo_limit: Personal maximum shared Undo/Redo steps, 1-50.
            gauge_markers: Shared main/PLOT risk-gauge options, or None for defaults.
            developer_enabled: Window-session developer menu flag; never serialized.

        Returns:
            None; own controls only. Persistence/reset consent belong to the host.
        """
        super().__init__(parent)
        apply_dialog_theme(self)
        spanish = language is Language.SPANISH
        precision = precision or DisplayPrecision()
        gauge_markers = gauge_markers or GaugeMarkerSettings()
        self.setWindowTitle("Configuración" if spanish else "Settings")
        self.setMinimumSize(760, 480)
        self.resize(880, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(12)
        title = QLabel(
            "Configuración de ErgoTools" if spanish else "ErgoTools settings"
        )
        title.setStyleSheet("color: #0B326C; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)
        body = QHBoxLayout()
        body.setSpacing(14)
        self.sections = QTreeWidget()
        self.sections.setHeaderHidden(True)
        self.sections.setMinimumWidth(180)
        self.sections.setMaximumWidth(240)
        self.sections.setIndentation(14)
        self.sections.setStyleSheet(
            "QTreeWidget { border-radius: 5px; }"
            "QTreeWidget::item { min-height: 30px; padding: 3px 5px; }"
        )
        self.sections.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.pages = QStackedWidget()
        self.section_items: dict[str, QTreeWidgetItem] = {}
        body.addWidget(self.sections)
        body.addWidget(self.pages, 1)
        layout.addLayout(body, 1)
        general = self._add_page(
            "general",
            "General",
            "Preferencias personales de idioma, entrada numérica y Deshacer."
            if spanish
            else "Personal language, numeric-input and Undo preferences.",
        )
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.language = QComboBox()
        self.language.addItems(["English", "Español"])
        self.language.setCurrentIndex(list(Language).index(language))
        self.units = QComboBox()
        self.units.addItems(["Imperial", "Métrico" if spanish else "Metric"])
        self.units.setCurrentIndex(list(MeasurementSystem).index(units))
        self.decimal = QComboBox()
        self.decimal.addItems(["1.25", "1,25"])
        self.decimal.setCurrentIndex(list(DecimalConvention).index(convention))
        self.decimal.setToolTip(
            "Separador decimal para introducir números; no admite agrupación."
            if spanish
            else "Decimal mark for numeric input; grouping is unsupported."
        )
        form.addRow("Idioma" if spanish else "Language", self.language)
        form.addRow(
            "Separador decimal" if spanish else "Decimal separator", self.decimal
        )
        if not project_open:
            form.addRow(
                "Unidades predeterminadas" if spanish else "Default units", self.units
            )
        self.undo_limit = QSpinBox()
        self.undo_limit.setRange(MIN_UNDO_LIMIT, MAX_UNDO_LIMIT)
        self.undo_limit.setValue(undo_limit)
        self.undo_limit.setToolTip(
            "Compartido por la ventana principal, Trabajadores, PLOT y JROT."
            if spanish
            else "Shared by the main window, Workers, PLOT and JROT."
        )
        form.addRow("Pasos de deshacer" if spanish else "Undo steps", self.undo_limit)
        history_note = QLabel(
            "Reducir el límite elimina pasos anteriores y puede acortar Rehacer. "
            "No cambia los datos del proyecto."
            if spanish
            else "Lowering the limit discards older steps and may shorten Redo. "
            "It does not change project data."
        )
        history_note.setWordWrap(True)
        form.addRow(history_note)
        general.addLayout(form)
        developer = QGroupBox("Developer options")
        developer_layout = QVBoxLayout(developer)
        self.developer_option = QCheckBox("Enable Developer Menu for this session")
        self.developer_option.setChecked(developer_enabled)
        developer_layout.addWidget(self.developer_option)
        developer_note = QLabel(
            "Experimental previews only. This option resets on restart; "
            "prototype inputs are discarded when their window closes."
        )
        developer_note.setWordWrap(True)
        developer_layout.addWidget(developer_note)
        general.addWidget(developer)
        general.addStretch(1)
        appearance = QTreeWidgetItem(["Apariencia" if spanish else "Appearance"])
        appearance.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.sections.addTopLevelItem(appearance)
        gauges = self._add_page(
            "gauges",
            "Indicadores de riesgo" if spanish else "Risk gauges",
            "Opciones compartidas por la evaluación principal "
            "y todos los indicadores de PLOT."
            if spanish
            else "Shared appearance for the main assessment and every PLOT risk gauge.",
            appearance,
        )
        gauge_form = QFormLayout()
        gauge_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.gauge_ticks = QCheckBox("Mostrar marcas" if spanish else "Show tick marks")
        self.gauge_ticks.setChecked(gauge_markers.show_ticks)
        self.gauge_labels = QCheckBox(
            "Mostrar límites de riesgo" if spanish else "Show risk-range limits"
        )
        self.gauge_labels.setChecked(gauge_markers.show_labels)
        self.gauge_interval = QSpinBox()
        self.gauge_interval.setRange(1, 100)
        self.gauge_interval.setValue(gauge_markers.interval)
        self.gauge_interval.setToolTip(
            "Separación en puntos porcentuales; los límites de riesgo son exactos."
            if spanish
            else "Spacing in percentage points; risk-range limits remain exact."
        )
        gauge_form.addRow(self.gauge_ticks)
        gauge_form.addRow(self.gauge_labels)
        gauge_form.addRow(
            "Intervalo (puntos porcentuales)"
            if spanish
            else "Interval (percentage points)",
            self.gauge_interval,
        )
        gauges.addLayout(gauge_form)
        gauges.addStretch(1)
        avatar = self._add_page(
            "avatar",
            "Avatar",
            "Enfoque del cuerpo al cambiar de herramienta."
            if spanish
            else "Body-view focus when changing assessment tools.",
            appearance,
        )
        self.animated_focus = QCheckBox(
            "Animar enfoque del avatar" if spanish else "Animate avatar focus"
        )
        self.animated_focus.setChecked(animated_focus)
        avatar.addWidget(self.animated_focus)
        avatar.addStretch(1)
        project = self._add_page(
            "project",
            "Proyecto" if spanish else "Project",
            "Decimales y unidades de visualización; "
            "los valores guardados no se redondean."
            if spanish
            else "Display decimals and units; saved values are never rounded.",
        )
        project_group = QGroupBox("Visualización" if spanish else "Display")
        project_form = QFormLayout(project_group)
        project_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        if project_open:
            project_form.addRow("Unidades" if spanish else "Units", self.units)
        self.decimal_fields: dict[str, QSpinBox] = {}
        for key, en, es in (
            ("inputs", "Input values", "Valores de entrada"),
            ("moment", "Moment", "Momento"),
            ("probability", "Probability (%)", "Probabilidad (%)"),
            ("damage", "Task and cumulative damage", "Daño por tarea y acumulado"),
            ("contribution", "Damage contribution (%)", "Contribución al daño (%)"),
        ):
            spin = QSpinBox()
            spin.setRange(0, 8)
            spin.setValue(getattr(precision, key))
            spin.setToolTip(
                "Decimales de visualización; los valores guardados no se redondean."
                if spanish
                else "Display decimals only; saved values are never rounded."
            )
            self.decimal_fields[key] = spin
            project_form.addRow(es if spanish else en, spin)
        project_group.setEnabled(project_open)
        project.addWidget(project_group)
        project.addStretch(1)
        assessment = self._add_page(
            "assessment",
            "Evaluación" if spanish else "Assessment",
            "Cambie solo esta evaluación; las filas conservadas mantienen sus datos."
            if spanish
            else "Change only this assessment; retained rows keep their data.",
        )
        assessment_group = QGroupBox(
            ("Evaluación activa: " if spanish else "Active assessment: ") + tool_name
        )
        assessment_form = QFormLayout(assessment_group)
        self.assessment_context_label = QLabel(assessment_context)
        self.assessment_context_label.setWordWrap(True)
        self.assessment_context_label.setTextFormat(Qt.TextFormat.PlainText)
        assessment_form.addRow(self.assessment_context_label)
        self.reset_tasks = QCheckBox(
            "Cambiar número de tareas al aplicar"
            if spanish
            else "Change number of tasks on Apply"
        )
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(task_count or 15)
        self.count.setEnabled(False)
        self.reset_tasks.toggled.connect(self.count.setEnabled)
        assessment_form.addRow(self.reset_tasks)
        assessment_form.addRow(
            "Número de tareas" if spanish else "Number of tasks", self.count
        )
        warning = QLabel(
            "Aumentar añade filas vacías. Reducir conserva las primeras filas; "
            "eliminar datos requiere confirmación."
            if spanish
            else "Increasing adds blank rows. Reducing keeps the first rows; "
            "removing entered data requires confirmation."
        )
        warning.setWordWrap(True)
        assessment_form.addRow(warning)
        assessment_group.setEnabled(task_count is not None)
        assessment.addWidget(assessment_group)
        assessment.addStretch(1)
        note = QLabel(
            "Aplicar acepta los ajustes; Cancelar conserva la configuración anterior."
            if spanish
            else "Apply accepts settings; Cancel keeps the previous settings."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.cancel_button = QPushButton("Cancelar" if spanish else "Cancel")
        self.apply_button = QPushButton("Aplicar" if spanish else "Apply")
        for button, key in (
            (self.cancel_button, "cancel"),
            (self.apply_button, "settings"),
        ):
            button.setIcon(icons[key])
            button.setIconSize(QSize(24, 24))
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.accept)
        self.sections.expandAll()
        self.sections.currentItemChanged.connect(self._select_section)
        self.sections.setCurrentItem(self.section_items["general"])
        self._initial_developer = developer_enabled
        self._initial_ordinary = self._ordinary_values()

    def _ordinary_values(self) -> tuple[int | bool, ...]:
        """Capture existing preference drafts to distinguish a developer-only Apply.

        Args:
            None.

        Returns:
            Comparable existing values, including opt-in task-count controls; the
            runtime developer flag is intentionally excluded.
        """
        return (
            self.language.currentIndex(),
            self.units.currentIndex(),
            self.decimal.currentIndex(),
            self.undo_limit.value(),
            self.animated_focus.isChecked(),
            self.gauge_ticks.isChecked(),
            self.gauge_labels.isChecked(),
            self.gauge_interval.value(),
            self.reset_tasks.isChecked(),
            self.count.value(),
            *(spin.value() for spin in self.decimal_fields.values()),
        )

    def only_developer_changed(self) -> bool:
        """Identify session-only Apply without committing tasks or writing settings.

        Args:
            None.

        Returns:
            True only when the developer flag changed and all existing drafts match
            their initial values. Cancel remains owned by the dialog's normal result.
        """
        return (
            self.developer_option.isChecked() != self._initial_developer
            and self._ordinary_values() == self._initial_ordinary
        )

    def _add_page(
        self,
        key: str,
        title: str,
        description: str,
        parent: QTreeWidgetItem | None = None,
    ) -> QVBoxLayout:
        """Create one scrollable page and its stable navigation entry.

        Args:
            key: Unique internal page identity, independent of translated text.
            title: Localized page/tree caption.
            description: Localized purpose and persistence/safety context.
            parent: Optional tree category; None creates a top-level section.

        Returns:
            Owned page layout for controls. Page scroll never hides the footer actions.
        """
        page = QWidget()
        page.setObjectName("settingsPage")
        page.setStyleSheet("QWidget#settingsPage { background: white; }")
        root = QVBoxLayout(page)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(12)
        heading = QLabel(title)
        heading.setStyleSheet("color: #0B326C; font-size: 18px; font-weight: 700;")
        note = QLabel(description)
        note.setWordWrap(True)
        root.addWidget(heading)
        root.addWidget(note)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        index = self.pages.addWidget(scroll)
        item = QTreeWidgetItem([title])
        item.setData(0, Qt.ItemDataRole.UserRole, index)
        if parent is None:
            self.sections.addTopLevelItem(item)
        else:
            parent.addChild(item)
        self.section_items[key] = item
        return root

    def _select_section(
        self,
        current: QTreeWidgetItem | None,
        previous: QTreeWidgetItem | None,
    ) -> None:
        """Change only the visible page, retaining every draft value and enablement.

        Args:
            current: New navigation entry, or None if selection is cleared.
            previous: Prior entry supplied by Qt; no state is committed from it.

        Returns:
            None; valid leaf selection changes the stacked page without persistence.
        """
        if current is not None:
            index = current.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(index, int):
                self.pages.setCurrentIndex(index)
