"""Original PLOT Job Placement overview with owned selection and explicit saves.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_results import PlotJobResult
from ergotools.domain.language import Language
from ergotools.domain.plot_positions import PlotPoint
from ergotools.presentation.desktop.plot_marker_item import PlotMarkerItem
from ergotools.presentation.desktop.plot_marker_layer import MarkerKey, PlotMarkerLayer


class PlotJobOverview(QScrollArea):
    """Port source placement controls; the injected layer owns geometry and storage."""

    def __init__(
        self,
        layer: PlotMarkerLayer,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
    ) -> None:
        """Build original grids/margins and connect one-way selection notifications.

        Args:
            layer: Existing PLOT marker/history owner; this view borrows its selection
                and save operations.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        super().__init__()
        self.layer = layer
        self.language = language
        self.selected_id: int | None = None
        self._editing_fields = False
        self._pulse_item: PlotMarkerItem | None = None
        self._pulses = 0
        self.timer = QTimer(self)
        self.timer.setInterval(190)
        self.timer.timeout.connect(self.advance_locate)
        self.setObjectName("jobOverviewScroll")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QWidget()
        panel.setObjectName("jobOverviewPanel")
        self.setWidget(panel)
        root = QVBoxLayout(panel)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)
        selector = QHBoxLayout()
        selector.setSpacing(7)
        self.combo = QComboBox(panel)
        self.combo.setToolTip(
            self.text(
                "Select a Job placement from the current map scope.",
                "Seleccione un puesto del ámbito actual del plano.",
            )
        )
        selector.addWidget(self.combo, 1)
        self.locate_button = QPushButton(panel)
        self.locate_button.setIcon(icons["locate"])
        self.locate_button.setIconSize(QSize(22, 22))
        self.locate_button.setFixedSize(36, 36)
        self.locate_button.setToolTip(
            self.text(
                "Locate the selected Job placement on the plant layout.",
                "Localizar el puesto seleccionado en el plano.",
            )
        )
        self.locate_button.clicked.connect(self.locate)
        selector.addWidget(self.locate_button)
        root.addLayout(selector)
        navigation = QHBoxLayout()
        navigation.setSpacing(5)
        self.navigation: list[QPushButton] = []
        for asset, english, spanish in (
            (
                "first",
                "Select the first Job placement.",
                "Seleccionar el primer puesto.",
            ),
            (
                "previous",
                "Select the previous Job placement.",
                "Seleccionar el puesto anterior.",
            ),
            (
                "next",
                "Select the next Job placement.",
                "Seleccionar el siguiente puesto.",
            ),
            ("last", "Select the last Job placement.", "Seleccionar el último puesto."),
        ):
            button = QPushButton(panel)
            button.setIcon(icons[asset])
            button.setIconSize(QSize(20, 20))
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
        root.addLayout(navigation)
        self.context = QLabel(panel)
        self.context.setObjectName("jobAssignmentContext")
        self.context.setTextFormat(Qt.TextFormat.PlainText)
        self.context.setWordWrap(True)
        self.context.setMinimumHeight(30)
        root.addWidget(self.context)
        self.values: dict[str, QLabel] = {}
        for title, fields in (
            (
                self.text("Job placement", "Puesto de trabajo"),
                (
                    ("job", "Job", "Puesto"),
                    ("workers", "Assigned workers", "Trabajadores asignados"),
                ),
            ),
            (
                self.text("Current Job risk", "Riesgo actual del puesto"),
                (
                    ("damage", "Cumulative damage", "Daño acumulado"),
                    ("risk", "Outcome probability", "Probabilidad"),
                ),
            ),
        ):
            group = QGroupBox(title, panel)
            group.setObjectName("workerSubgroup")
            grid = QGridLayout(group)
            grid.setContentsMargins(10, 10, 10, 8)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(4)
            for index, (key, english, spanish) in enumerate(fields):
                value = QLabel("\u2013", group)
                value.setTextFormat(Qt.TextFormat.PlainText)
                value.setWordWrap(True)
                self.values[key] = value
                grid.addWidget(QLabel(self.text(english, spanish), group), index, 0)
                grid.addWidget(value, index, 1)
            grid.setColumnStretch(1, 1)
            root.addWidget(group)
        group = QGroupBox(
            self.text("Station map position", "Posición de la estación"), panel
        )
        group.setObjectName("workerSubgroup")
        position = QVBoxLayout(group)
        position.setContentsMargins(10, 10, 10, 8)
        position.setSpacing(5)
        note = QLabel(
            self.text(
                "Shared by every Job placement at this Station.",
                "Compartida por todos los puestos de esta estación.",
            ),
            group,
        )
        note.setObjectName("jobPositionNote")
        note.setWordWrap(True)
        position.addWidget(note)
        coordinates = QHBoxLayout()
        self.x_input = QLineEdit(group)
        self.y_input = QLineEdit(group)
        for caption, field in (("X", self.x_input), ("Y", self.y_input)):
            coordinates.addWidget(QLabel(caption, group))
            coordinates.addWidget(field, 1)
            field.textEdited.connect(self.coordinate_edited)
        position.addLayout(coordinates)
        self.status = QLabel(group)
        self.status.setObjectName("jobPositionStatus")
        position.addWidget(self.status)
        actions = QHBoxLayout()
        self.cancel_button = QPushButton(
            self.text("Cancel movement", "Cancelar movimiento"), group
        )
        self.save_button = QPushButton(
            self.text("Save position", "Guardar posición"), group
        )
        for button, asset in (
            (self.cancel_button, "cancel"),
            (self.save_button, "save"),
        ):
            button.setIcon(icons[asset])
            button.setIconSize(QSize(20, 20))
            actions.addWidget(button)
        self.cancel_button.clicked.connect(self.cancel)
        self.save_button.clicked.connect(self.save)
        position.addLayout(actions)
        root.addWidget(group)
        root.addStretch(1)
        self.combo.currentIndexChanged.connect(self.selection_changed)
        layer.history_restored.connect(self.history_restored)
        layer.changed.connect(self.refresh)
        layer.selection_changed.connect(self.marker_selected)
        self.refresh()

    def text(self, english: str, spanish: str) -> str:
        """Translate captions independently of stored identity and pixel values.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def selected_marker(self) -> PlotMarkerItem | None:
        """Resolve the current item each time; rebuilt Qt items are never cached.

        Args:
            None.

        Returns:
            Current live job marker resolved by exact identity, or None when absent;
            never cache it across scene replacement.
        """
        return (
            self.layer.items.get(("job", self.selected_id))
            if self.selected_id is not None
            else None
        )

    @property
    def has_unaccepted_fields(self) -> bool:
        """Report local text that document history must not discard implicitly.

        Args:
            None.

        Returns:
            True when typed coordinate strings still require explicit Save/Cancel.
        """
        return self._editing_fields

    def history_restored(self) -> None:
        """Reproject accepted coordinates after document Undo/Redo or Cancel.

        Args:
            None.

        Returns:
            None.
        """
        self._editing_fields = False

    def refresh(self) -> None:
        """Project saved results and edit intent without recursive combo signals.

        Args:
            None.

        Returns:
            None.
        """
        self.stop_locate()
        rows = self.layer.results.jobs if self.layer.results is not None else ()
        previous = self.combo.blockSignals(True)
        self.combo.clear()
        for row in rows:
            place = row.placement.workplace
            self.combo.addItem(
                f"{row.job.job_id}  |  {place.station_id}  |  "
                f"{self.text('Shift', 'Turno')} {place.shift_id}",
                row.placement.placement_id,
            )
        index = self.combo.findData(self.selected_id)
        self.combo.setCurrentIndex(index if index >= 0 else (0 if rows else -1))
        self.combo.blockSignals(previous)
        if rows:
            self.selected_id = rows[self.combo.currentIndex()].placement.placement_id
            self.show_row(rows[self.combo.currentIndex()])
        else:
            self.context.setText(
                self.text(
                    "No Job placements match the current filters.",
                    "No hay puestos que coincidan con los filtros actuales.",
                )
            )
            for value in self.values.values():
                value.setText("\u2013")
        marker = self.selected_marker()
        pending = marker is not None and marker.pending
        if marker is not None:
            for key, item in self.layer.items.items():
                if key[0] == "job":
                    item.setSelected(item is marker)
        if not self._editing_fields:
            point = (
                marker.anchor_point()
                if marker is not None and (marker.pending or marker.anchored)
                else None
            )
            self.x_input.setText(f"{point.x:.1f}" if point else "")
            self.y_input.setText(f"{point.y:.1f}" if point else "")
        self.status.setText(
            self.text("Unsaved Station position", "Posición de estación sin guardar")
            if pending
            else self.text("Station anchor saved", "Posición de estación guardada")
            if marker is not None and marker.anchored
            else self.text("Station anchor not positioned", "Estación sin posición")
            if marker is not None
            else self.text("No position selected", "Ninguna posición seleccionada")
        )
        self.status.setProperty("pending", pending)
        self.status.setProperty(
            "saved", marker is not None and marker.anchored and not pending
        )
        style = self.status.style()
        assert style is not None
        style.unpolish(self.status)
        style.polish(self.status)
        for button in self.navigation:
            button.setEnabled(marker is not None and not pending)
        self.combo.setEnabled(marker is not None and not pending)
        self.locate_button.setEnabled(marker is not None)
        self.x_input.setEnabled(marker is not None)
        self.y_input.setEnabled(marker is not None)
        self.save_button.setEnabled(pending)
        self.cancel_button.setEnabled(pending)

    def show_row(self, row: PlotJobResult) -> None:
        """Display literal placement and optional current Job values; zero is valid.

        Args:
            row: Saved typed result row carrying exact source/assignment ownership and
                optional evidence.

        Returns:
            None.
        """
        place = row.placement.workplace
        self.context.setText(
            f"{place.plant_name}  \u203a  {place.section_name}  \u203a  "
            f"{place.line_name}  \u203a  {place.station_id}   •   "
            f"{self.text('Shift', 'Turno')} {place.shift_id}"
        )
        job_name = row.job.name or self.text("Unnamed Job", "Puesto sin nombre")
        self.values["job"].setText(f"{row.job.job_id} - {job_name}")
        self.values["workers"].setText(str(row.assigned_worker_count))
        evidence = row.risk
        missing = self.text("Not available", "No disponible")
        damage = evidence.measurement.cumulative_damage if evidence else None
        risk = evidence.measurement.probability_percent if evidence else None
        self.values["damage"].setText(
            f"{damage:.4f}" if damage is not None else missing
        )
        self.values["risk"].setText(f"{risk:.1f}%" if risk is not None else missing)

    def selection_changed(self, index: int) -> None:
        """Select one owner without sending feedback from marker notifications.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        if index < 0:
            return
        self.selected_id = int(self.combo.itemData(index))
        self._editing_fields = False
        marker = self.selected_marker()
        if marker is not None:
            self.layer.select(marker)
        self.refresh()

    def marker_selected(self, key: MarkerKey) -> None:
        """Accept marker selection and refresh only this overview.

        Args:
            key: Typed worker/station marker identity; captions and scene positions are
                not storage keys.

        Returns:
            None.
        """
        if key[0] == "job":
            self.selected_id = key[1]
            self._editing_fields = False
            self.refresh()

    def navigate(self, index: int) -> None:
        """Clamp source navigation and prevent selection while position is pending.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        marker = self.selected_marker()
        if marker is not None and not marker.pending:
            self.combo.setCurrentIndex(max(0, min(index, self.combo.count() - 1)))

    def coordinate_edited(self, _text: str) -> None:
        """Keep partially typed coordinates until explicit Save validates both.

        Args:
            _text: Text-change signal payload; current controls provide the complete
                pending values.

        Returns:
            None.
        """
        marker = self.selected_marker()
        if marker is not None:
            self._editing_fields = True
            marker.pending = True
            for peer in self.layer.items.values():
                if peer is not marker:
                    peer.setEnabled(False)
            self.layer.changed.emit()

    def save(self) -> None:
        """Validate finite original-image coordinates and commit through the layer.

        Args:
            None.

        Returns:
            None.
        """
        marker = self.selected_marker()
        if marker is None or self.selected_id is None:
            return
        try:
            current = marker.anchor_point()
            x_text = self.x_input.text().strip()
            y_text = self.y_input.text().strip()
            # Keep original pixels when only the rounded projection is unchanged.
            point = PlotPoint(
                current.x if x_text == f"{current.x:.1f}" else float(x_text),
                current.y if y_text == f"{current.y:.1f}" else float(y_text),
            )
        except ValueError:
            self.layer.show_error(
                self.text(
                    "Station X and Y must be valid finite numbers.",
                    "X e Y de la estación deben ser números finitos válidos.",
                )
            )
            return
        marker.setPos(point.x + marker.offset.x(), point.y + marker.offset.y())
        self.layer.moved(marker)
        if self.layer.save(("job", self.selected_id)):
            self._editing_fields = False
            self.refresh()

    def cancel(self) -> None:
        """Discard typed/moved position without writing or changing selected owner.

        Args:
            None.

        Returns:
            None.
        """
        if self.selected_id is not None and self.selected_marker() is not None:
            self._editing_fields = False
            self.layer.cancel(("job", self.selected_id))

    def locate(self) -> None:
        """Ensure visibility and pulse the source blue selection ten times.

        Args:
            None.

        Returns:
            None.
        """
        self.stop_locate()
        marker = self.selected_marker()
        if marker is not None:
            self._pulse_item = marker
            self._pulses = 10
            marker.setSelected(True)
            self.layer.canvas.ensureVisible(marker)
            self.timer.start()

    def stop_locate(self) -> None:
        """Stop before selection/dataset replacement can invalidate a Qt wrapper.

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
        """Advance one timer pulse and finish with the selected frame visible.

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
        """Stop locate animation when the containing overview is closed.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        self.stop_locate()
        super().closeEvent(event)
