"""Source-derived PLOT worker visual settings and atomic Save All workflow.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from dataclasses import replace

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotRiskView
from ergotools.domain.plot_positions import (
    PlotPoint,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.presentation.desktop.plot_marker_layer import MarkerKey, PlotMarkerLayer


class PlotWorkerControls(QGroupBox):
    """Own original worker controls; selection belongs to the composed overview."""

    def __init__(
        self,
        layer: PlotMarkerLayer,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        show_success: Callable[[str], None] | None = None,
    ) -> None:
        """Preserve source grids, dimensions, icons and immediate flag previews.

        Args:
            layer: Existing PLOT marker/history owner; this view borrows its selection
                and save operations.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            show_success: Optional success-message callback after an explicit successful
                persistence operation.

        Returns:
            None.
        """
        super().__init__()
        self.layer = layer
        self.language = language
        self.show_success = show_success or self.saved_message
        self.identity: int | None = None
        self._typed = False
        self.field_drafts: dict[int, tuple[str, str, str]] = {}
        self.setTitle(self.text("Visual controls", "Controles visuales"))
        self.setObjectName("workerSubgroup")
        self.setMinimumHeight(116)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(8)
        state = QHBoxLayout()
        state.setSpacing(12)
        self.visible = QCheckBox(self.text("Visible", "Visible"), self)
        self.enabled = QCheckBox(self.text("Enable", "Incluir"), self)
        self.locked = QCheckBox(self.text("Lock", "Bloquear"), self)
        for checkbox, english, spanish in (
            (
                self.visible,
                "Show or hide the selected worker marker.",
                "Mostrar u ocultar el marcador seleccionado.",
            ),
            (
                self.enabled,
                "Include or exclude the selected worker from layout summaries.",
                "Incluir o excluir al trabajador de los resúmenes.",
            ),
            (
                self.locked,
                "Prevent the selected worker marker from being moved.",
                "Evitar el movimiento del marcador seleccionado.",
            ),
        ):
            checkbox.setToolTip(self.text(english, spanish))
            state.addWidget(checkbox)
            checkbox.toggled.connect(self.preview_flags)
        state.addStretch(1)
        layout.addLayout(state)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(5)
        self.x_input = QLineEdit(self)
        self.y_input = QLineEdit(self)
        self.scale_input = QLineEdit(self)
        for index, (caption, field, english, spanish) in enumerate(
            (
                (
                    "X:",
                    self.x_input,
                    "Horizontal position of the selected worker marker.",
                    "Posición horizontal del marcador seleccionado.",
                ),
                (
                    "Y:",
                    self.y_input,
                    "Vertical position of the selected worker marker.",
                    "Posición vertical del marcador seleccionado.",
                ),
                (
                    self.text("Scale:", "Escala:"),
                    self.scale_input,
                    "Display scale of the selected worker marker.",
                    "Escala visual del marcador seleccionado.",
                ),
            )
        ):
            label = QLabel(caption, self)
            label.setAlignment(
                Qt.Alignment(Qt.AlignmentFlag.AlignRight)
                | Qt.AlignmentFlag.AlignVCenter
            )
            grid.addWidget(label, 0, index * 2)
            grid.addWidget(field, 0, index * 2 + 1)
            field.setMinimumWidth(44)
            field.setMaximumWidth(72)
            grid.setColumnStretch(index * 2 + 1, 1)
            field.setToolTip(self.text(english, spanish))
            field.textEdited.connect(self.field_edited)
        layout.addLayout(grid)
        save_row = QHBoxLayout()
        save_row.setSpacing(6)
        self.save_button = QPushButton(self.text("Save", "Guardar"), self)
        self.save_all_button = QPushButton(self.text("Save All", "Guardar todo"), self)
        self.all_scale_input = QLineEdit("1.0", self)
        self.all_scale_input.setFixedWidth(54)
        self.all_scale_input.setToolTip(
            self.text(
                "Scale applied when saving all worker markers.",
                "Escala aplicada al guardar todos los marcadores.",
            )
        )
        for button in (self.save_button, self.save_all_button):
            button.setIcon(icons["save"])
            button.setIconSize(QSize(20, 20))
        self.save_button.setToolTip(
            self.text(
                "Save the selected worker's layout settings.",
                "Guardar los ajustes del trabajador seleccionado.",
            )
        )
        self.save_all_button.setToolTip(
            self.text(
                "Save all worker positions and display settings.",
                "Guardar todas las posiciones y ajustes visuales.",
            )
        )
        save_row.addWidget(self.save_button, 1)
        save_row.addWidget(QLabel(self.text("Scale:", "Escala:"), self))
        save_row.addWidget(self.all_scale_input)
        save_row.addWidget(self.save_all_button, 1)
        layout.addLayout(save_row)
        self.save_button.clicked.connect(self.save)
        self.save_all_button.clicked.connect(self.save_all)
        layer.history_restored.connect(self.history_restored)
        layer.changed.connect(self.refresh)
        layer.selection_changed.connect(self.select)
        self.refresh()

    def text(self, english: str, spanish: str) -> str:
        """Translate captions while settings retain canonical pixels and flags.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def select(self, key: MarkerKey) -> None:
        """Accept assignment identity from overview or marker, including hidden ones.

        Args:
            key: Typed worker/station marker identity; captions and scene positions are
                not storage keys.

        Returns:
            None.
        """
        if key[0] == "worker":
            if self.identity is not None and self._typed:
                self.field_drafts[self.identity] = (
                    self.x_input.text(),
                    self.y_input.text(),
                    self.scale_input.text(),
                )
            self.identity = key[1]
            fields = self.field_drafts.get(self.identity)
            self._typed = fields is not None
            if fields is not None:
                for field, value in zip(
                    (self.x_input, self.y_input, self.scale_input), fields, strict=True
                ):
                    field.setText(value)
            self.refresh()

    def history_restored(self) -> None:
        """Release accepted field caches before projecting a source history value.

        Args:
            None.

        Returns:
            None.
        """
        self.field_drafts.clear()
        self._typed = False

    def refresh(self) -> None:
        """Project saved/draft values without emitting checkbox edits or writes.

        Args:
            None.

        Returns:
            None.
        """
        results = self.layer.results
        if results is None:
            self.field_drafts.clear()
            self._typed = False
        available = (
            self.identity is not None
            and results is not None
            and results.selection.risk_view is not PlotRiskView.JOB
            and any(
                row.assessment.assignment_id == self.identity for row in results.workers
            )
        )
        for control in (
            self.visible,
            self.enabled,
            self.locked,
            self.x_input,
            self.y_input,
            self.scale_input,
            self.save_button,
        ):
            control.setEnabled(available)
        self.save_all_button.setEnabled(
            results is not None
            and results.selection.risk_view is not PlotRiskView.JOB
            and bool(results.workers)
        )
        self.all_scale_input.setEnabled(self.save_all_button.isEnabled())
        marker = (
            self.layer.worker_settings(self.identity)
            if available and self.identity is not None
            else None
        )
        for checkbox, value in (
            (self.visible, marker.visible if marker else False),
            (self.enabled, marker.enabled if marker else False),
            (self.locked, marker.locked if marker else False),
        ):
            previous = checkbox.blockSignals(True)
            checkbox.setChecked(value)
            checkbox.blockSignals(previous)
        if not self._typed:
            point = marker.point if marker else None
            self.x_input.setText(f"{point.x:g}" if point else "")
            self.y_input.setText(f"{point.y:g}" if point else "")
            self.scale_input.setText(f"{marker.scale:.2f}" if marker else "")

    def preview_flags(self, _checked: bool) -> None:
        """Preview flags locally without accepting partially typed coordinates.

        Args:
            _checked: Checkbox signal value; the complete current flags are read from
                the controls.

        Returns:
            None.
        """
        if self.identity is not None and self.layer.results is not None:
            marker = self.layer.worker_settings(self.identity)
            self.layer.preview_worker(
                replace(
                    marker,
                    visible=self.visible.isChecked(),
                    enabled=self.enabled.isChecked(),
                    locked=self.locked.isChecked(),
                )
            )

    def field_edited(self, _text: str) -> None:
        """Retain partial typed values and guard Apply/map replacement until saved.

        Args:
            _text: Text-change signal payload; current controls provide the complete
                pending values.

        Returns:
            None.
        """
        if self.identity is not None:
            self._typed = True
            self.field_drafts[self.identity] = (
                self.x_input.text(),
                self.y_input.text(),
                self.scale_input.text(),
            )
            self.layer.worker_drafts[self.identity] = self.layer.worker_settings(
                self.identity
            )
            self.layer.changed.emit()

    def selected_settings(self) -> WorkerAssignmentMarker:
        """Validate explicit original-image X/Y and positive dimensionless scale.

        Args:
            None.

        Returns:
            Validated worker settings in original image pixels with positive
            dimensionless scale; unchanged display strings preserve exact canonical
            values.

        Raises:
            ValueError: There is no selected worker.
        """
        if self.identity is None:
            raise ValueError("There is no selected worker.")
        marker = self.layer.worker_settings(self.identity)
        # Display formatting must not become a second edit when saving a drag.
        # Only a field whose text differs from its projection replaces the source.
        point = marker.point
        x_text = self.x_input.text().strip()
        y_text = self.y_input.text().strip()
        scale_text = self.scale_input.text().strip()
        return replace(
            marker,
            point=PlotPoint(
                point.x
                if point is not None and x_text == f"{point.x:g}"
                else float(x_text),
                point.y
                if point is not None and y_text == f"{point.y:g}"
                else float(y_text),
            ),
            scale=marker.scale
            if scale_text == f"{marker.scale:.2f}"
            else float(scale_text),
            source=WorkerPositionSource.MANUAL,
        )

    def invalid_settings(self) -> None:
        """Report actionable finite/range validation through the owning UI boundary.

        Args:
            None.

        Returns:
            None.
        """
        self.layer.show_error(
            self.text(
                "Worker X and Y must be finite numbers and scale must be positive.",
                "X e Y deben ser números finitos y la escala debe ser positiva.",
            )
        )

    def save(self) -> None:
        """Commit the selected worker settings; preserve typed intent on failure.

        Args:
            None.

        Returns:
            None.
        """
        if self.identity is None or self.layer.results is None:
            return
        try:
            marker = self.selected_settings()
        except ValueError:
            self.invalid_settings()
            return
        if self.layer.save_workers((marker,)):
            self.field_drafts.pop(marker.assignment_id, None)
            self._typed = False
            self.refresh()
            self.show_success(
                self.text(
                    "Visual worker tool saved successfully.",
                    "Se guardaron los ajustes del trabajador.",
                )
            )

    def save_all(self) -> None:
        """Validate the full current-result batch before one atomic save operation.

        Args:
            None.

        Returns:
            None.
        """
        results = self.layer.results
        if results is None or not results.workers:
            return
        try:
            scale = float(self.all_scale_input.text().strip())
            markers = []
            for row in results.workers:
                identity = row.assessment.assignment_id
                fields = self.field_drafts.get(identity)
                marker = self.layer.worker_settings(identity)
                if fields is not None:
                    marker = replace(
                        marker,
                        point=PlotPoint(float(fields[0]), float(fields[1])),
                        scale=float(fields[2]),
                        source=WorkerPositionSource.MANUAL,
                    )
                marker = replace(marker, scale=scale)
                if marker.point is None:
                    raise ValueError("Position every unplaced worker before Save All.")
                markers.append(marker)
        except ValueError:
            self.layer.show_error(
                self.text(
                    "Every worker needs finite X/Y coordinates and a positive scale "
                    "before Save All.",
                    "Cada trabajador necesita coordenadas X/Y finitas y una escala "
                    "positiva para guardar todo.",
                )
            )
            return
        if self.layer.save_workers(tuple(markers)):
            self.field_drafts.clear()
            self._typed = False
            self.refresh()
            self.show_success(
                self.text(
                    "All visual worker tools saved successfully.",
                    "Se guardaron todos los ajustes de los trabajadores.",
                )
            )

    def saved_message(self, message: str) -> None:
        """Preserve the original successful-Save modal through an injected boundary.

        Args:
            message: Literal user-facing notification/error content.

        Returns:
            None.
        """
        QMessageBox.information(self, self.text("Success", "Correcto"), message)
