"""Original PLOT Job-only assignment overview with owned selection and explicit saves.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import (
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

from ergotools.application.plot_results import PlotWorkerResult
from ergotools.domain.language import Language
from ergotools.domain.plot_positions import PlotPoint
from ergotools.presentation.desktop.plot_marker_item import PlotMarkerItem
from ergotools.presentation.desktop.plot_marker_layer import (
    MarkerKey,
    PlotMarkerLayer,
    plot_damage_color,
)
from ergotools.presentation.desktop.plot_result_selector import PlotResultSelector


class PlotJobOverview(QScrollArea):
    """Inspect Job risks at shared assignment positions; the layer owns all geometry."""

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
        self.selector = PlotResultSelector(
            icons, job_view=True, language=language, parent=panel
        )
        selector.addWidget(self.selector, 1)
        self.locate_button = QPushButton(self.text("Locate", "Localizar"), panel)
        self.locate_button.setObjectName("locateJobButton")
        self.locate_button.setIcon(icons["locate"])
        self.locate_button.setIconSize(QSize(22, 22))
        self.locate_button.setToolTip(
            self.text(
                "Locate the selected Job occurrence on the plant layout.",
                "Localizar el trabajo seleccionado en el plano.",
            )
        )
        self.locate_button.clicked.connect(self.locate)
        root.addLayout(selector)
        navigation = QHBoxLayout()
        navigation.setSpacing(5)
        self.navigation: list[QPushButton] = []
        for asset, english, spanish in (
            (
                "first",
                "Select the first Job occurrence.",
                "Seleccionar el primer trabajo.",
            ),
            (
                "previous",
                "Select the previous Job occurrence.",
                "Seleccionar el trabajo anterior.",
            ),
            (
                "next",
                "Select the next Job occurrence.",
                "Seleccionar el siguiente trabajo.",
            ),
            (
                "last",
                "Select the last Job occurrence.",
                "Seleccionar el último trabajo.",
            ),
        ):
            button = QPushButton(panel)
            button.setIcon(icons[asset])
            button.setIconSize(QSize(20, 20))
            button.setToolTip(self.text(english, spanish))
            navigation.addWidget(button, 1)
            self.navigation.append(button)
        self.navigation[0].clicked.connect(lambda: self.navigate(0))
        self.navigation[1].clicked.connect(
            lambda: self.navigate(self.selector.current_index - 1)
        )
        self.navigation[2].clicked.connect(
            lambda: self.navigate(self.selector.current_index + 1)
        )
        self.navigation[3].clicked.connect(
            lambda: self.navigate(len(self.selector.rows) - 1)
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
                self.text("Job occurrence", "Ubicación del trabajo"),
                (
                    ("job", "Job", "Trabajo"),
                    ("occurrences", "Squares on map", "Cuadrados en el mapa"),
                ),
            ),
            (
                self.text("Current Job risk", "Riesgo actual del trabajo"),
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
            if any(key == "risk" for key, _english, _spanish in fields):
                grid.addWidget(self.locate_button, len(fields), 0, 1, 2)
            root.addWidget(group)
        group = QGroupBox(
            self.text("Assignment map position", "Posición de la asignación"), panel
        )
        group.setObjectName("workerSubgroup")
        position = QVBoxLayout(group)
        position.setContentsMargins(10, 10, 10, 8)
        position.setSpacing(5)
        note = QLabel(
            self.text(
                "Same assignment position in Individual, Job and Comparison views.",
                "La misma posición en las vistas Individual, Trabajo y Comparación.",
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
        self.cancel_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.cancel_button.setToolTip(
            self.text(
                "Restore the last move of this square. Undo/Redo reverses this action.",
                "Restaurar el último movimiento; la acción es reversible.",
            )
        )
        self.cancel_button.clicked.connect(self.cancel)
        self.save_button.clicked.connect(self.save)
        position.addLayout(actions)
        self.movement_hint = QLabel(
            self.text(
                "Cancel restores this square's last move in this view. Undo/Redo also "
                "restores accepted changes.",
                "Cancelar restaura el último movimiento en esta vista. "
                "Deshacer/Rehacer también restaura cambios aceptados.",
            ),
            group,
        )
        self.movement_hint.setWordWrap(True)
        position.addWidget(self.movement_hint)
        root.addWidget(group)
        root.addStretch(1)
        self.selector.selection_changed.connect(self.selection_changed)
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
        rows = self.layer.results.workers if self.layer.results is not None else ()
        self.selector.set_rows(rows, self.selected_id)
        self.selected_id = self.selector.selected_id
        if rows:
            row = self.selector.row_for_id(self.selected_id)
            assert row is not None
            self.show_row(row)
        else:
            self.context.setText(
                self.text(
                    "No assignment results match the current filters.",
                    "No hay asignaciones que coincidan con los filtros actuales.",
                )
            )
            for value in self.values.values():
                value.setText("\u2013")
                value.setStyleSheet("")
        marker = self.selected_marker()
        pending = marker is not None and (marker.pending or self._editing_fields)
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
        accepted_caption = (
            self.text("Map position accepted", "Posición del mapa aceptada")
            if self.layer.project_editing
            else self.text("Map position saved", "Posición del mapa guardada")
        )
        self.status.setText(
            self.text("Unsaved map position", "Posición del mapa sin guardar")
            if pending
            else accepted_caption
            if marker is not None and marker.anchored
            else self.text("Map position not set", "Posición del mapa no definida")
            if marker is not None
            else self.text(
                "Assignment not shown on map", "Asignación no visible en el mapa"
            )
            if self.selected_id is not None
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
            button.setEnabled(bool(rows) and not pending)
        self.selector.setEnabled(bool(rows) and not pending)
        self.locate_button.setEnabled(marker is not None)
        self.x_input.setEnabled(marker is not None)
        self.y_input.setEnabled(marker is not None)
        self.save_button.setEnabled(pending)
        self.cancel_button.setEnabled(
            pending
            or self._editing_fields
            or self.selected_id in self.layer.movement_origins
        )

    def show_row(self, row: PlotWorkerResult) -> None:
        """Display the Job risk at this assignment; never substitute individual risk.

        Args:
            row: Exact map assignment with its optional current Job measurement.

        Returns:
            None; missing Jobs/risks stay explicit and coordinates share other views.
        """
        place = row.assessment.owner.workplace
        self.context.setText(
            f"{place.plant_name} \u203a {place.section_name} \u203a "
            f"{place.line_name} \u203a "
            f"{place.station_id} · {self.text('Shift', 'Turno')} {place.shift_id}\n"
            + self.text(
                f"Worker: {row.worker.worker_id}",
                f"Trabajador: {row.worker.worker_id}",
            )
        )
        job_name = (
            f"{row.job.job_id} — {row.job.name}"
            if row.job
            else self.text("No Job", "Sin trabajo")
        )
        self.values["job"].setText(job_name)
        results = self.layer.results
        count = (
            sum(
                peer.job == row.job
                and (row.job is not None or peer.assessment.owner.workplace == place)
                and ("job", peer.assessment.assignment_id) in self.layer.items
                and self.layer.items["job", peer.assessment.assignment_id].isVisible()
                for peer in results.workers
            )
            if results is not None
            else 0
        )
        self.values["occurrences"].setText(str(count))
        evidence = row.job_risk
        missing = self.text("Not available", "No disponible")
        damage = evidence.measurement.cumulative_damage if evidence else None
        risk = evidence.measurement.probability_percent if evidence else None
        self.values["damage"].setText(
            f"{damage:.4f}" if damage is not None else missing
        )
        self.values["risk"].setText(f"{risk:.1f}%" if risk is not None else missing)
        color = plot_damage_color(row.assessment.kind, damage)
        for key in ("damage", "risk"):
            self.values[key].setStyleSheet(
                f"background: {color}; color: #071B2D; "
                "padding: 3px; border-radius: 3px;"
            )

    def selection_changed(self, identity: int) -> None:
        """Select an exact map assignment from the workplace/Job hierarchy.

        Args:
            identity: Stable assignment ID chosen by the shared selector.

        Returns:
            None; no position or assessment data is modified.
        """
        if self.selector.row_for_id(identity) is None:
            return
        self.selected_id = identity
        self._editing_fields = False
        marker = self.selected_marker()
        if marker is not None:
            self.layer.select(marker)
        self.refresh()

    def marker_selected(self, key: MarkerKey) -> None:
        """Accept marker selection and refresh only this overview.

        Args:
            key: Typed view/assignment marker identity; captions and scene positions are
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
        if marker is None or not marker.pending:
            self.selector.navigate(index)

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
                    "Map X and Y must be valid finite numbers.",
                    "X e Y del mapa deben ser números finitos válidos.",
                )
            )
            return
        marker.setPos(point.x + marker.offset.x(), point.y + marker.offset.y())
        self.layer.moved(marker)
        if self.layer.save(("job", self.selected_id)):
            self._editing_fields = False
            self.refresh()

    def cancel(self) -> None:
        """Restore the last integrated move or discard an unaccepted coordinate draft.

        Args:
            None.

        Returns:
            None; accepted restoration is reversible in shared history. Diagnostic
            explicit-save windows retain their saved-position cancellation behavior.
        """
        if self.selected_id is None or self.selected_marker() is None:
            return
        if self.layer.project_editing:
            if self._editing_fields:
                self._editing_fields = False
                self.layer.restore_history()
                self.refresh()
                self.movement_hint.setText(
                    self.text(
                        "Coordinate draft cancelled; accepted position retained.",
                        "Coordenadas canceladas; posición aceptada conservada.",
                    )
                )
                return
            original = self.layer.movement_origins.pop(self.selected_id, None)
            if original is not None:
                self.layer.preview_worker(original, label_key="plot.history.cancel")
                self.movement_hint.setText(
                    self.text(
                        "Previous position restored. Undo can restore the move.",
                        "Posición restaurada. Deshacer recupera el movimiento.",
                    )
                )
        else:
            self._editing_fields = False
            self.layer.cancel(("job", self.selected_id))

    def locate(self) -> None:
        """Center the selected Job square at current zoom and pulse its blue frame.

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
            self.layer.canvas.locate_item(marker)
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
