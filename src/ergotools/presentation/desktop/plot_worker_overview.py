"""Original PLOT worker selector, details and results composed with visual settings.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_results import PlotWorkerResult
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.worker_details import display_body_measurement
from ergotools.presentation.desktop.plot_marker_item import (
    MarkerAppearance,
    PlotMarkerItem,
)
from ergotools.presentation.desktop.plot_marker_layer import (
    MarkerKey,
    PlotMarkerLayer,
    plot_damage_color,
)
from ergotools.presentation.desktop.plot_worker_controls import PlotWorkerControls
from ergotools.presentation.desktop.plot_worker_picker import PlotWorkerPicker
from ergotools.presentation.desktop.plot_worker_preview import PlotWorkerPreview


class PlotWorkerOverview(QScrollArea):
    """Compose original worker regions using stable saved assignment identities."""

    def __init__(
        self,
        layer: PlotMarkerLayer,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        system: MeasurementSystem = MeasurementSystem.METRIC,
        show_success: Callable[[str], None] | None = None,
    ) -> None:
        """Build source geometry; scientific evaluation and storage stay outside UI.

        Args:
            layer: Existing PLOT marker/history owner; this view borrows its selection
                and save operations.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            system: Measurement display policy; conversions preserve canonical
                source/body units.
            show_success: Optional success-message callback after an explicit successful
                persistence operation.

        Returns:
            None.
        """
        super().__init__()
        self.layer = layer
        self.language = language
        self.system = system
        self.selected_id: int | None = None
        self._preferred_id: int | None = None
        self.letter = "All"
        self.by_name = False
        self._pulse_item: PlotMarkerItem | None = None
        self._pulses = 0
        self.timer = QTimer(self)
        self.timer.setInterval(190)
        self.timer.timeout.connect(self.advance_locate)
        self.setObjectName("workerOverviewScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QGroupBox()
        panel.setMinimumHeight(590)
        self.setWidget(panel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 14, 10, 10)
        layout.setSpacing(5)
        selector = QHBoxLayout()
        selector.setSpacing(7)
        self.combo = QComboBox(panel)
        self.combo.setToolTip(
            self.text(
                "Select a worker assignment to inspect or edit on the layout.",
                "Seleccione una asignación de trabajador para ver o editar "
                "en el plano.",
            )
        )
        selector.addWidget(self.combo, 1)
        self.order_button = QPushButton(panel)
        self.search_button = QPushButton(panel)
        for button, asset, english, spanish in (
            (
                self.order_button,
                "alphabet_order",
                "Change worker ordering.",
                "Cambiar el orden de los trabajadores.",
            ),
            (
                self.search_button,
                "search",
                "Search for a worker.",
                "Buscar un trabajador.",
            ),
        ):
            button.setFixedSize(36, 36)
            button.setIcon(icons[asset])
            button.setIconSize(QSize(24, 24))
            button.setToolTip(self.text(english, spanish))
            selector.addWidget(button)
        self.search_button.clicked.connect(self.search)
        self.order_button.clicked.connect(self.toggle_order)
        self.icons = icons
        layout.addLayout(selector)
        alphabet = QHBoxLayout()
        alphabet.setContentsMargins(0, 0, 0, 0)
        alphabet.setSpacing(1)
        group = QButtonGroup(self)
        group.setExclusive(True)
        self.letters: dict[str, QPushButton] = {}
        for letter in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(
                self.text("All", "Todos") if letter == "All" else letter, panel
            )
            button.setObjectName("plotAlphabetButton")
            button.setFixedHeight(20)
            button.setMinimumWidth(26 if letter == "All" else 12)
            button.setMaximumWidth(26 if letter == "All" else 15)
            button.setCheckable(True)
            button.setChecked(letter == "All")
            button.setToolTip(
                self.text("Show every worker", "Mostrar todos los trabajadores")
                if letter == "All"
                else self.text(
                    f"Show last names beginning with {letter}",
                    f"Mostrar apellidos que comienzan con {letter}",
                )
            )
            button.clicked.connect(
                lambda _checked, value=letter: self.set_letter(value)
            )
            group.addButton(button)
            self.letters[letter] = button
            alphabet.addWidget(button)
        layout.addLayout(alphabet)
        self.context = QLabel(panel)
        self.context.setObjectName("workerAssignmentContext")
        self.context.setTextFormat(Qt.TextFormat.PlainText)
        self.context.setWordWrap(True)
        self.context.setMinimumHeight(39)
        layout.addWidget(self.context)
        navigation = QHBoxLayout()
        navigation.setSpacing(5)
        self.navigation: list[QPushButton] = []
        for asset, english, spanish in (
            ("first", "Select the first worker.", "Seleccionar el primer trabajador."),
            (
                "previous",
                "Select the previous worker.",
                "Seleccionar el trabajador anterior.",
            ),
            ("next", "Select the next worker.", "Seleccionar el siguiente trabajador."),
            ("last", "Select the last worker.", "Seleccionar el último trabajador."),
        ):
            button = QPushButton(panel)
            button.setIcon(icons[asset])
            button.setIconSize(QSize(20, 20))
            button.setMinimumWidth(38)
            button.setToolTip(self.text(english, spanish))
            navigation.addWidget(button, 1)
            self.navigation.append(button)
        self.navigation[0].clicked.connect(lambda: self.navigate(0))
        self.navigation[1].clicked.connect(
            lambda: self.navigate(self.combo.currentIndex() - 1)
        )
        self.navigation[2].clicked.connect(
            lambda: self.navigate(self.combo.currentIndex() + 1)
        )
        self.navigation[3].clicked.connect(
            lambda: self.navigate(self.combo.count() - 1)
        )
        layout.addLayout(navigation)
        layout.addSpacing(8)
        details = QGroupBox(self.text("Worker details", "Datos del trabajador"), panel)
        details.setObjectName("workerSubgroup")
        details.setMinimumHeight(82)
        grid = QGridLayout(details)
        grid.setContentsMargins(10, 12, 10, 10)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        self.values: dict[str, QLabel] = {}
        self.body_labels: dict[str, QLabel] = {}
        for row, keys in enumerate((("age", "sex"), ("weight", "height"))):
            for column, key in enumerate(keys):
                label = QLabel(details)
                label.setAlignment(
                    Qt.Alignment(Qt.AlignmentFlag.AlignRight)
                    | Qt.AlignmentFlag.AlignVCenter
                )
                self.body_labels[key] = label
                value = QLabel(details)
                value.setTextFormat(Qt.TextFormat.PlainText)
                self.values[key] = value
                grid.addWidget(label, row, column * 2)
                grid.addWidget(value, row, column * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        layout.addWidget(details)
        assessment = QGroupBox(
            self.text("Assessment result", "Resultado de evaluación"), panel
        )
        assessment.setObjectName("workerSubgroup")
        assessment.setMinimumHeight(244)
        grid = QGridLayout(assessment)
        grid.setContentsMargins(10, 12, 10, 10)
        grid.setHorizontalSpacing(8)
        for index, (key, english, spanish) in enumerate(
            (
                ("tool", "Tool", "Herramienta"),
                ("damage", "Cumulative damage", "Daño acumulado"),
                ("risk", "Outcome probability", "Probabilidad"),
                ("job", "Job", "Puesto"),
                ("job_risk", "Job risk", "Riesgo del puesto"),
                ("difference", "Difference", "Diferencia"),
            )
        ):
            grid.addWidget(QLabel(self.text(english, spanish), assessment), index, 0)
            value = QLabel(assessment)
            value.setTextFormat(Qt.TextFormat.PlainText)
            value.setWordWrap(key in ("job", "difference"))
            self.values[key] = value
            grid.addWidget(value, index, 1)
        grid.setColumnStretch(1, 1)
        self.preview = PlotWorkerPreview(language)
        self.locate_button = QPushButton(self.text("Locate", "Localizar"), assessment)
        self.locate_button.setObjectName("locateWorkerButton")
        self.locate_button.setIcon(icons["locate"])
        self.locate_button.setIconSize(QSize(22, 22))
        self.locate_button.setToolTip(
            self.text(
                "Blink the selected worker's blue frame on the plant layout.",
                "Parpadear el marco azul del trabajador seleccionado en el plano.",
            )
        )
        self.locate_button.clicked.connect(self.locate)
        actions = QWidget(assessment)
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 2, 0, 0)
        actions_layout.setSpacing(10)
        actions_layout.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignLeft)
        actions_layout.addWidget(self.locate_button, 1, Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(actions, 6, 0, 1, 2)
        layout.addWidget(assessment)
        layout.addStretch(1)
        self.controls = PlotWorkerControls(
            layer, icons, language=language, show_success=show_success
        )
        layout.addWidget(self.controls)
        self.combo.currentIndexChanged.connect(self.selection_changed)
        layer.changed.connect(self.refresh)
        layer.selection_changed.connect(self.marker_selected)
        self.refresh()

    def text(self, english: str, spanish: str) -> str:
        """Translate interface text without interpreting saved labels.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def rows(self) -> tuple[PlotWorkerResult, ...]:
        """Return current results in reference binary ID/last-name order.

        Args:
            None.

        Returns:
            Current saved worker-result rows in reference binary ID/surname order, or an
            empty tuple without results.
        """
        if self.layer.results is None:
            return ()
        rows = self.layer.results.workers
        return tuple(
            sorted(
                rows,
                key=lambda row: (
                    (row.worker.last_name or "")
                    if self.by_name
                    else row.worker.worker_id,
                    row.assessment.assignment_id,
                ),
            )
        )

    def refresh(self) -> None:
        """Project dataset selection while preserving stable ownership and edits.

        Args:
            None.

        Returns:
            None.
        """
        self.stop_locate()
        rows = self.rows()
        initials = {(row.worker.last_name or "").strip()[:1].upper() for row in rows}
        if self.letter != "All" and self.letter not in initials:
            self.letter = "All"
        for letter, button in self.letters.items():
            button.setEnabled(letter == "All" or letter in initials)
            button.setChecked(letter == self.letter)
        previous = self.combo.blockSignals(True)
        self.combo.clear()
        for row in rows:
            if self.letter != "All" and not (
                row.worker.last_name or ""
            ).strip().upper().startswith(self.letter):
                continue
            worker = row.worker
            caption = (
                f"{worker.worker_id} ({worker.last_name}, {worker.first_name})"
                if worker.last_name and worker.first_name
                else worker.worker_id
            )
            self.combo.addItem(caption, row.assessment.assignment_id)
        preferred = (
            self.selected_id if self.selected_id is not None else self._preferred_id
        )
        index = self.combo.findData(preferred)
        self.combo.setCurrentIndex(
            index if index >= 0 else (0 if self.combo.count() else -1)
        )
        self.combo.blockSignals(previous)
        identity = self.combo.currentData()
        old_identity = self.selected_id
        self.selected_id = int(identity) if identity is not None else None
        if self.selected_id is not None:
            self._preferred_id = self.selected_id
            if self.controls.identity != self.selected_id:
                self.controls.select(("worker", self.selected_id))
            row = next(
                row for row in rows if row.assessment.assignment_id == self.selected_id
            )
            self.show_row(row)
        else:
            self.context.setText(
                self.text(
                    "No worker results match the current filters.",
                    "No hay resultados que coincidan con los filtros actuales.",
                )
            )
            for value in self.values.values():
                value.setText("\u2013")
            self.preview.appearance = None
            self.preview.update()
        for button in self.navigation:
            button.setEnabled(self.selected_id is not None)
        self.order_button.setEnabled(bool(rows))
        self.search_button.setEnabled(bool(rows))
        self.combo.setEnabled(bool(rows))
        self.locate_button.setEnabled(
            self.selected_id is not None
            and ("worker", self.selected_id) in self.layer.items
            and self.layer.items["worker", self.selected_id].isVisible()
        )
        self.set_body_labels()
        if old_identity != self.selected_id or not self.timer.isActive():
            for key, item in self.layer.items.items():
                if key[0] == "worker":
                    item.setSelected(key[1] == self.selected_id)

    def set_body_labels(self) -> None:
        """Expose kg/cm or lb/in captions without converting saved metadata.

        Args:
            None.

        Returns:
            None.
        """
        metric = self.system is MeasurementSystem.METRIC
        self.body_labels["age"].setText(self.text("Age:", "Edad:"))
        self.body_labels["sex"].setText(self.text("Sex:", "Sexo:"))
        self.body_labels["weight"].setText(
            self.text("Weight", "Peso") + (" (kg):" if metric else " (lb):")
        )
        self.body_labels["height"].setText(
            self.text("Height", "Estatura") + (" (cm):" if metric else " (in):")
        )

    def show_row(self, row: PlotWorkerResult) -> None:
        """Display saved evidence; missing and scientific-review risk stay absent.

        Args:
            row: Saved typed result row carrying exact source/assignment ownership and
                optional evidence.

        Returns:
            None.
        """
        place = row.assessment.owner.workplace
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[row.assessment.kind]
        self.context.setText(
            f"{place.plant_name}  \u203a  {place.section_name}  \u203a  "
            f"{place.line_name}  \u203a  {place.station_id}   •   "
            f"{self.text('Shift', 'Turno')} {place.shift_id}   •   {tool}"
        )
        details = row.worker.details
        missing = self.text("Not available", "No disponible")
        self.values["age"].setText(
            str(self.layer.current_year - int(details.birth_date[:4]))
            if details and details.birth_date
            else "N/A"
        )
        sex = details.sex if details else None
        self.values["sex"].setText(
            self.text(sex, "Mujer" if sex == "Female" else "Hombre") if sex else "N/A"
        )
        for key, value in (
            ("weight", details.weight_kg if details else None),
            ("height", details.height_cm if details else None),
        ):
            display = display_body_measurement(value, self.system, mass=key == "weight")
            self.values[key].setText(f"{display:g}" if display is not None else "N/A")
        self.values["tool"].setText(tool)
        damage = row.assessment.total_damage
        probability = row.assessment.probability
        risk = probability * 100 if probability is not None else None
        self.values["damage"].setText(
            f"{damage:.4f}" if damage is not None else missing
        )
        self.values["risk"].setText(f"{risk:.1f}%" if risk is not None else missing)
        job = row.job
        self.values["job"].setText(
            f"{job.job_id} - {job.name}"
            if job and job.name
            else job.job_id
            if job
            else self.text("Not classified", "Sin clasificar")
        )
        evidence = row.job_risk
        job_risk = evidence.measurement.probability_percent if evidence else None
        self.values["job_risk"].setText(
            f"{job_risk:.1f}%" if job_risk is not None else missing
        )
        difference = (
            risk - job_risk if risk is not None and job_risk is not None else None
        )
        direction = (
            self.text("above", "por encima del")
            if difference is not None and difference > 0
            else self.text("below", "por debajo del")
            if difference is not None and difference < 0
            else self.text("equal to", "igual al")
        )
        self.values["difference"].setText(
            (
                f"{difference:+.1f} pp ({direction} {self.text('Job', 'puesto')})"
                if difference
                else self.text("0.0 pp (equal to Job)", "0.0 pp (igual al puesto)")
            )
            if difference is not None
            else missing
        )
        self.values["job_risk"].setToolTip(
            self.text(
                "Current Job risk values", "Valores actuales de riesgo del trabajo"
            )
        )
        self.preview.appearance = MarkerAppearance(
            "circle" if sex == "Female" else "triangle" if sex == "Male" else "hexagon",
            plot_damage_color(row.assessment.kind, damage),
            plot_damage_color(
                row.assessment.kind,
                evidence.measurement.cumulative_damage if evidence else None,
            ),
            self.layer.results is not None
            and self.layer.results.selection.risk_view is PlotRiskView.COMPARISON,
            job_risk,
        )
        self.preview.update()

    def selection_changed(self, index: int) -> None:
        """Select once; notify map callbacks only when an item exists.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        if index >= 0:
            self.selected_id = int(self.combo.itemData(index))
            marker = self.layer.items.get(("worker", self.selected_id))
            if marker is not None:
                self.layer.select(marker)
            else:
                self.refresh()

    def marker_selected(self, key: MarkerKey) -> None:
        """Reveal the full alphabet when selecting a marker outside its filter.

        Args:
            key: Typed worker/station marker identity; captions and scene positions are
                not storage keys.

        Returns:
            None.
        """
        if key[0] == "worker":
            self.selected_id = key[1]
            if self.combo.findData(key[1]) < 0:
                self.letter = "All"
            self.refresh()

    def navigate(self, index: int) -> None:
        """Clamp original first/previous/next/last navigation.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        if self.combo.count():
            self.combo.setCurrentIndex(max(0, min(index, self.combo.count() - 1)))

    def set_letter(self, letter: str) -> None:
        """Filter the selector alone; saved map results are unchanged.

        Args:
            letter: Surname initial filter, or the reference All sentinel to remove that
                filter.

        Returns:
            None.
        """
        self.letter = letter
        self.refresh()

    def toggle_order(self) -> None:
        """Toggle reference ordering without reloading/writing saved assessments.

        Args:
            None.

        Returns:
            None.
        """
        self.by_name = not self.by_name
        self.order_button.setIcon(
            self.icons["number_order" if self.by_name else "alphabet_order"]
        )
        self.refresh()

    def locate(self) -> None:
        """Pulse an existing visible selected marker; do not create hidden geometry.

        Args:
            None.

        Returns:
            None.
        """
        self.stop_locate()
        marker = (
            self.layer.items.get(("worker", self.selected_id))
            if self.selected_id is not None
            else None
        )
        if marker is not None and marker.isVisible():
            self._pulse_item = marker
            self._pulses = 10
            self.layer.canvas.ensureVisible(marker)
            marker.setSelected(True)
            self.timer.start()

    def stop_locate(self) -> None:
        """Release pulse item before selection, scene rebuild or close.

        Args:
            None.

        Returns:
            None.
        """
        self.timer.stop()
        if self._pulse_item is not None:
            self._pulse_item.setSelected(True)
        self._pulse_item = None
        self._pulses = 0

    def advance_locate(self) -> None:
        """Advance the source 190 ms pulse and finish with the blue frame visible.

        Args:
            None.

        Returns:
            None.
        """
        marker = self._pulse_item
        if marker is None or self._pulses <= 0:
            self.stop_locate()
            return
        marker.setSelected(not marker.isSelected())
        self._pulses -= 1
        if self._pulses == 0:
            self.stop_locate()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Stop native animation when this overview is explicitly closed.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        self.stop_locate()
        super().closeEvent(event)

    def search(self) -> None:
        """Open the original modal picker; Cancel preserves selection and edits.

        Args:
            None.

        Returns:
            None.
        """
        rows = self.rows()
        if not rows:
            return
        dialog = PlotWorkerPicker(rows, self.icons, language=self.language, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            identity = dialog.selected_assignment_id
            if identity is not None:
                marker = self.layer.items.get(("worker", identity))
                if marker is not None:
                    self.layer.select(marker)
                else:
                    self.marker_selected(("worker", identity))
