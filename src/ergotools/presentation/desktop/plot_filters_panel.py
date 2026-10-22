"""Original PLOT filter grid with disclosure, unit projection and Apply/Clear intent.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Mapping

from PyQt5.QtCore import QLocale, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_history import PlotFilterState
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import (
    PlotDemographics,
    PlotFilterSelection,
    PlotRiskView,
    paired_range,
)
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.domain.worker_details import (
    display_body_measurement,
    store_body_measurement,
)
from ergotools.presentation.desktop.plot_filter_controls import (
    PlotToolControls,
    PlotWorkplaceControls,
)
from ergotools.presentation.desktop.plot_map_panel import PlotMapPanel
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE


class PlotFiltersPanel(QGroupBox):
    """Compose the original grid and publish immutable filters after explicit Apply."""

    history_changed = pyqtSignal()

    def __init__(
        self,
        hierarchy: WorkHierarchy,
        map_panel: PlotMapPanel,
        icons: Mapping[str, QIcon],
        apply_selection: Callable[[PlotFilterSelection], bool],
        *,
        system: MeasurementSystem = MeasurementSystem.METRIC,
        decimal_convention: DecimalConvention = DecimalConvention.POINT,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build controls without applying results or accepting assessment edits.

        Args:
            hierarchy: Immutable saved workplace/shift catalog used to build the local
                selection tree.
            map_panel: Owned map component providing scope acceptance and local error
                presentation.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            apply_selection: Callback publishing a complete immutable filter selection
                only on success.
            system: Measurement display policy; conversions preserve canonical
                source/body units.
            decimal_convention: Numeric-input policy independent of UI language and
                measurement units.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.

        Raises:
            ValueError: Invalid PLOT measurement system.
        """
        super().__init__(parent)
        if not isinstance(system, MeasurementSystem):
            raise ValueError("Invalid PLOT measurement system.")
        self.hierarchy = hierarchy
        self.map_panel = map_panel
        self.apply_selection = apply_selection
        self.system = system
        self.language = language
        self.applied: PlotFilterSelection | None = None
        self._projecting = False
        self._history_suppressed = False
        self._canonical_bounds: dict[tuple[str, int], float | None] = {}
        self.risk_view = PlotRiskView.INDIVIDUAL
        self.setTitle(self.text("Filters", "Filtros"))
        self.setStyleSheet(PLOT_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.tools = PlotToolControls(
            icons, self.tool_selected, language=language, parent=self
        )
        self.workplace = PlotWorkplaceControls(
            hierarchy, icons, map_panel.set_scope, language=language, parent=self
        )
        self.workplace.scope_changed.connect(self.notify_history)
        self.risk_group = QGroupBox(self.text("Risk view", "Vista de riesgo"), self)
        risk_row = QHBoxLayout(self.risk_group)
        risk_row.setContentsMargins(8, 12, 8, 12)
        risk_row.setSpacing(0)
        self.risk_buttons: dict[PlotRiskView, QToolButton] = {}
        for mode, english, spanish in (
            (PlotRiskView.INDIVIDUAL, "Individual", "Individual"),
            (PlotRiskView.JOB, "Job", "Puesto"),
            (PlotRiskView.COMPARISON, "Comparison", "Comparación"),
        ):
            button = QToolButton(self.risk_group)
            button.setObjectName("plotRiskViewButton")
            button.setText(self.text(english, spanish))
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            tooltips = {
                PlotRiskView.INDIVIDUAL: (
                    "Show each Worker's individual assessment risk.",
                    "Mostrar el riesgo de la evaluación individual de cada trabajador.",
                ),
                PlotRiskView.JOB: (
                    "Show current Job risk at each positioned Station.",
                    "Mostrar el riesgo actual del trabajo en "
                    "cada estación posicionada.",
                ),
                PlotRiskView.COMPARISON: (
                    "Compare the individual worker symbol with "
                    "its filled Job-risk square.",
                    "Comparar el símbolo individual con su "
                    "cuadrado de riesgo del puesto.",
                ),
            }
            button.setToolTip(self.text(*tooltips[mode]))
            button.clicked.connect(
                lambda checked, selected=mode: self.select_risk(selected)
            )
            risk_row.addWidget(button, 1)
            self.risk_buttons[mode] = button
        self.risk_buttons[self.risk_view].setChecked(True)
        self.demographics = QGroupBox(
            self.text("Worker demographics", "Datos demográficos"), self
        )
        self.demographics.setCheckable(True)
        self.demographics.setChecked(False)
        self.demographics.setToolTip(
            self.text(
                "Enable demographic filtering for workers shown on the layout.",
                "Activar filtros demográficos para los trabajadores del plano.",
            )
        )
        self.fields_container = QWidget(self.demographics)
        fields_row = QHBoxLayout(self.fields_container)
        fields_row.setContentsMargins(0, 0, 0, 0)
        fields_row.setSpacing(12)
        self.sex = QComboBox()
        self.sex.setMinimumWidth(112)
        for english, spanish, value in (
            ("Both", "Ambos", None),
            ("Female", "Femenino", "Female"),
            ("Male", "Masculino", "Male"),
        ):
            self.sex.addItem(self.text(english, spanish), value)
        self.sex.setToolTip(
            self.text("Filter workers by sex.", "Filtrar trabajadores por sexo.")
        )
        sex_column = QVBoxLayout()
        sex_column.setSpacing(3)
        caption = QLabel(self.text("Sex :", "Sexo :"))
        caption.setObjectName("demographicFieldTitle")
        sex_column.addWidget(caption)
        sex_column.addWidget(self.sex)
        fields_row.addLayout(sex_column, 1)
        self.ranges: dict[str, tuple[QDoubleSpinBox, QDoubleSpinBox]] = {}
        self.range_titles: dict[str, QLabel] = {}
        for key, english, spanish, decimals in (
            ("age", "Age range", "Edad", 0),
            ("weight", "Weight range", "Peso", 1),
            ("height", "Height range", "Estatura", 1),
        ):
            column = QVBoxLayout()
            column.setSpacing(3)
            label = QLabel(self.text(english, spanish))
            label.setObjectName("demographicFieldTitle")
            self.range_titles[key] = label
            column.addWidget(label)
            row = QHBoxLayout()
            row.setSpacing(5)
            fields = []
            for index in range(2):
                if index:
                    to = QLabel(self.text("to", "a"))
                    to.setObjectName("rangeFieldLabel")
                    to.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    row.addWidget(to)
                spin = QDoubleSpinBox(self.fields_container)
                spin.setRange(-1, 1000)
                spin.setDecimals(decimals)
                spin.setSingleStep(1 if decimals == 0 else 0.1)
                spin.setSpecialValueText("\u2013")
                spin.setValue(-1)
                spin.setKeyboardTracking(False)
                spin.setMinimumWidth(68)
                spin.setToolTip(
                    self.text(
                        f"{'Minimum' if index == 0 else 'Maximum'} worker {key}.",
                        f"{spanish}: {'mínimo' if index == 0 else 'máximo'}.",
                    )
                )
                self._canonical_bounds[key, index] = None
                spin.valueChanged.connect(
                    lambda value, field_key=key, position=index: self.bound_changed(
                        field_key, position, value
                    )
                )
                row.addWidget(spin, 1)
                fields.append(spin)
            self.ranges[key] = (fields[0], fields[1])
            column.addLayout(row)
            fields_row.addLayout(column, 1)
        demographics_layout = QVBoxLayout(self.demographics)
        demographics_layout.setContentsMargins(10, 10, 10, 8)
        demographics_layout.addWidget(self.fields_container)
        self.demographics.toggled.connect(self.disclose)
        actions = QWidget(self)
        actions.setObjectName("filterActions")
        actions.setFixedWidth(164)
        action_column = QVBoxLayout(actions)
        action_column.setContentsMargins(0, 0, 0, 0)
        action_column.setSpacing(10)
        self.clear_button = QPushButton(self.text("Clear Filters", "Limpiar filtros"))
        self.apply_button = QPushButton(self.text("Apply Filters", "Aplicar filtros"))
        self.apply_button.setObjectName("applyfilter_button")
        for button, icon in (
            (self.clear_button, "filter_reset"),
            (self.apply_button, "filter_apply_light"),
        ):
            button.setIcon(icons[icon])
            button.setIconSize(QSize(32, 32))
            button.setFixedHeight(58)
            action_column.addWidget(button)
        self.clear_button.setToolTip(
            self.text(
                "Reset every filter to its default value.",
                "Restablecer los filtros a sus valores iniciales.",
            )
        )
        self.apply_button.setToolTip(
            self.text(
                "Apply the selected filters to the plant layout and summaries.",
                "Aplicar los filtros al plano y a los resúmenes.",
            )
        )
        self.clear_button.clicked.connect(self.clear_filters)
        self.apply_button.clicked.connect(self.apply_filters)
        grid = QGridLayout(self)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(9)
        grid.setVerticalSpacing(8)
        grid.addWidget(self.tools, 0, 0)
        grid.addWidget(self.workplace, 0, 1)
        grid.addWidget(self.risk_group, 1, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.demographics, 1, 1, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(actions, 0, 2, 2, 1)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 3)
        self._set_suffixes()
        self.set_decimal_convention(decimal_convention)
        self.disclose(False)

    def text(self, english: str, spanish: str) -> str:
        """Translate controls while stored identities stay literal.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def tool_selected(self, kind: AssessmentKind) -> None:
        """Record selected tool intent; Apply still controls result publication.

        Args:
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.

        Returns:
            None.
        """
        self.notify_history()

    def select_risk(self, mode: PlotRiskView) -> None:
        """Select one risk view without fabricating a result dataset.

        Args:
            mode: Typed individual/job/comparison risk view; no risk is computed by
                selecting it.

        Returns:
            None.

        Raises:
            ValueError: Invalid PLOT risk view.
        """
        if not isinstance(mode, PlotRiskView):
            raise ValueError("Invalid PLOT risk view.")
        self.risk_view = mode
        self.risk_buttons[mode].setChecked(True)

    def disclose(self, expanded: bool) -> None:
        """Move peer regions together, preserving original 201/229-pixel disclosure.

        Args:
            expanded: True reveals optional detail controls; False collapses them
                without clearing values.

        Returns:
            None.
        """
        self.fields_container.setVisible(expanded)
        self.demographics.setFixedHeight(96 if expanded else 68)
        self.risk_group.setFixedHeight(96 if expanded else 68)
        self.setFixedHeight(229 if expanded else 201)

    def _set_suffixes(self) -> None:
        """Keep units in headings so narrow source fields show complete numbers.

        Args:
            None.

        Returns:
            None.
        """
        imperial = self.system is MeasurementSystem.IMPERIAL
        for key, english, spanish, unit in (
            ("weight", "Weight range", "Peso", "lb" if imperial else "kg"),
            ("height", "Height range", "Estatura", "in" if imperial else "cm"),
        ):
            self.range_titles[key].setText(f"{self.text(english, spanish)} ({unit})")

    def bound_changed(self, key: str, index: int, value: float) -> None:
        """Accept edits once; display projection never rounds canonical bounds.

        Args:
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.
            index: Zero-based combo/tab/directory position within the current local
                selection.
            value: Observed metric, or None for missing evidence; formatting never
                changes storage.

        Returns:
            None.
        """
        if self._projecting:
            return
        field = self.ranges[key][index]
        value_or_none = None if value == field.minimum() else value
        self._canonical_bounds[key, index] = (
            value_or_none
            if key == "age"
            else store_body_measurement(
                value_or_none, self.system, mass=key == "weight"
            )
        )

    def set_decimal_convention(self, convention: DecimalConvention) -> None:
        """Change native decimal input independently of language, without grouping.

        Args:
            convention: Point/comma input convention, independent of UI language and
                source units.

        Returns:
            None.

        Raises:
            ValueError: Invalid PLOT decimal convention.
        """
        if not isinstance(convention, DecimalConvention):
            raise ValueError("Invalid PLOT decimal convention.")
        locale = QLocale("de_DE" if convention is DecimalConvention.COMMA else "C")
        locale.setNumberOptions(
            QLocale.NumberOptions(QLocale.NumberOption.OmitGroupSeparator)
            | QLocale.NumberOption.RejectGroupSeparator
        )
        self._projecting = True
        try:
            for fields in self.ranges.values():
                for field in fields:
                    field.setLocale(locale)
        finally:
            self._projecting = False

    def set_system(self, system: MeasurementSystem) -> None:
        """Project bounds without cumulative rounding or clamping large values.

        Args:
            system: Measurement display policy; conversions preserve canonical
                source/body units.

        Returns:
            None.

        Raises:
            ValueError: Invalid PLOT measurement system.
        """
        if not isinstance(system, MeasurementSystem):
            raise ValueError("Invalid PLOT measurement system.")
        if system is self.system:
            return
        self._projecting = True
        try:
            for key in ("weight", "height"):
                for index, field in enumerate(self.ranges[key]):
                    converted = display_body_measurement(
                        self._canonical_bounds[key, index], system, mass=key == "weight"
                    )
                    if converted is not None:
                        field.setMaximum(max(1000.0, converted))
                        field.setValue(converted)
            self.system = system
            self._set_suffixes()
        finally:
            self._projecting = False

    def selection(self) -> PlotFilterSelection:
        """Freeze edited bounds; incomplete or reversed ranges remain ignored.

        Args:
            None.

        Returns:
            Immutable current scope/tool/risk/filter intent; incomplete or reversed
            demographic ranges are ignored.

        Raises:
            ValueError: Choose a workplace before applying PLOT filters.
        """
        if self.workplace.scope is None:
            raise ValueError("Choose a workplace before applying PLOT filters.")
        bounds = {
            key: paired_range(
                self._canonical_bounds[key, 0], self._canonical_bounds[key, 1]
            )
            for key in self.ranges
        }
        return PlotFilterSelection(
            self.workplace.scope,
            self.tools.selected,
            self.risk_view,
            PlotDemographics(
                self.demographics.isChecked(),
                self.sex.currentData(),
                bounds["age"],
                bounds["weight"],
                bounds["height"],
            ),
        )

    def apply_filters(self) -> None:
        """Publish successful Apply; errors retain applied filters and edited inputs.

        Args:
            None.

        Returns:
            None.
        """
        try:
            selection = self.selection()
            if self.apply_selection(selection):
                self.applied = selection
                self.notify_history()
        except Exception:
            logging.getLogger(__name__).exception("Unable to apply PLOT filters")
            self.map_panel.show_error(
                self.text(
                    "Filters could not be applied. Previous results have been kept.",
                    "No se pudieron aplicar los filtros. Se "
                    "conservaron los resultados anteriores.",
                )
            )

    def _clear_filters(self) -> None:
        """Restore defaults after map consent, without automatically applying.

        Args:
            None.

        Returns:
            None.
        """
        if self.hierarchy.plants:
            shifts = self.hierarchy.work.shifts
            shift = "1" if "1" in shifts else shifts[0] if shifts else None
            if not self.workplace.set_scope(
                PlotScope(((self.hierarchy.plants[0],),), shift)
            ):
                return
        self.tools.select_tool(AssessmentKind.LIFFT)
        self.select_risk(PlotRiskView.INDIVIDUAL)
        self.sex.setCurrentIndex(0)
        for fields in self.ranges.values():
            for field in fields:
                field.setValue(field.minimum())
        self.demographics.setChecked(False)

    def notify_history(self) -> None:
        """Publish one accepted control operation, never a replay projection.

        Args:
            None.

        Returns:
            None.
        """
        if not self._projecting and not self._history_suppressed:
            self.history_changed.emit()

    def clear_filters(self) -> None:
        """Group a successful Clear into one reversible configuration change.

        Args:
            None.

        Returns:
            None.
        """
        self._history_suppressed = True
        try:
            self._clear_filters()
        finally:
            self._history_suppressed = False
        self.notify_history()

    def snapshot(self) -> PlotFilterState:
        """Retain every canonical bound even when disabled, unpaired or reversed.

        Args:
            None.

        Returns:
            Immutable full control state, retaining disabled, unpaired or reversed
            canonical kg/cm bounds for Undo/Redo.

        Raises:
            ValueError: Choose a workplace before recording PLOT filters.
        """
        if self.workplace.scope is None:
            raise ValueError("Choose a workplace before recording PLOT filters.")
        return PlotFilterState(
            self.workplace.scope,
            self.tools.selected,
            self.risk_view,
            self.demographics.isChecked(),
            self.sex.currentData(),
            tuple(
                self._canonical_bounds.get((key, i))
                for key in ("age", "weight", "height")
                for i in (0, 1)
            ),
        )

    def restore(self, state: PlotFilterState) -> None:
        """Project a history snapshot exactly, with no Apply, I/O or new command.

        Canonical kg/cm values remain exact through display rounding and unit changes.
        The caller loads the scope/results before invoking this method.

        Args:
            state: Immutable source/view snapshot to project without recording another
                edit.

        Returns:
            None.
        """
        self._projecting = True
        try:
            self.workplace.scope = state.scope
            self.workplace.refresh_values()
            self.tools.selected = state.tool
            self.tools.buttons[state.tool].setChecked(True)
            self.select_risk(state.risk_view)
            self.sex.setCurrentIndex(self.sex.findData(state.sex))
            self.demographics.setChecked(state.enabled)
            for offset, key in enumerate(("age", "weight", "height")):
                for index, field in enumerate(self.ranges[key]):
                    value = state.bounds[offset * 2 + index]
                    self._canonical_bounds[key, index] = value
                    displayed = (
                        value
                        if key == "age"
                        else display_body_measurement(
                            value, self.system, mass=key == "weight"
                        )
                    )
                    field.setMaximum(max(1000.0, displayed or 0))
                    field.setValue(field.minimum() if displayed is None else displayed)
        finally:
            self._projecting = False
