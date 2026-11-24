"""Developer-only PLOT playback and static incomplete native rotation inspection.

Presentation layer. The player owns transient scene items, seek clock, preview
pacing and timers. It never persists marker movement or changes a rotation; reload
reads the latest retained JROT result through an injected read-only capability.
"""

from typing import TYPE_CHECKING

from PyQt5.QtCore import QElapsedTimer, QPointF, Qt, QTimer
from PyQt5.QtGui import QIcon, QMouseEvent
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.rotation_scenarios import own_run_is_current
from ergotools.application.shift_playback import (
    ShiftPlayback,
    ShiftPlaybackRepository,
    playback_stages,
    prepare_shift,
)
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.job_catalog import WorkerJobAssignment
from ergotools.domain.plot_filters import PlotFilterSelection
from ergotools.domain.plot_positions import WorkerAssignmentMarker
from ergotools.domain.rotation_scenario import RotationScenario
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.presentation.desktop.plot_shift_graphics import (
    ShiftGlyph,
    ShiftTimeline,
    contrast_ink,
    shift_color,
)
from ergotools.presentation.desktop.plot_shift_worker_overview import (
    ShiftWorkerOverview,
)

if TYPE_CHECKING:
    from ergotools.presentation.desktop.plot_window import PlotWindow


class ShiftExposureTable(QTableWidget):
    """Toggle an already selected participant row without enabling data edits."""

    def mousePressEvent(self, event: QMouseEvent | None) -> None:  # noqa: N802
        """Clear a repeated row click, otherwise keep native table selection.

        Args:
            event: Mouse press delivered to the read-only table viewport.

        Returns:
            None; selection-change signals synchronize the paired map glyph.
        """
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            selection = self.selectionModel()
            if (
                index.isValid()
                and selection is not None
                and selection.isRowSelected(index.row(), index.parent())
            ):
                self.setCurrentCell(-1, -1)
                self.clearSelection()
                event.accept()
                return
        super().mousePressEvent(event)


class PlotShiftPlayer(QGroupBox):
    """Own read-only playback controls, frozen data and transient scene items.

    Attributes:
        active: True only while the experimental mode is selected.
        data: Prepared single-plant playback, or None after incomplete selection.
        elapsed: Actual shift-relative clock minute, independent of playback speed.
        details: Separate right-side participant/index summary.
    """

    def __init__(
        self,
        window: "PlotWindow",
        repository: ShiftPlaybackRepository,
        icons: dict[str, QIcon],
    ) -> None:
        """Compose a compact player without loading rotations or modifying files.

        Args:
            window: Owning PLOT host and map scene.
            repository: Borrowed read-only project capability.
            icons: Existing software asset identities.

        Returns:
            None.
        """
        super().__init__(
            window.text("Shift playback", "Reproducción de turno"),
            window,
        )
        self.host, self.repository = window, repository
        self._tools_icon = window.tabs.tabIcon(0)
        self._exposure_icon = icons["jrot"]
        self.active = False
        self.visible_ids: set[str] = set()
        self.selected_worker: str | None = None
        self.filter_selection: PlotFilterSelection | None = None
        self.catalog_people: dict[str, WorkerEntry] = {}
        self.assignments: dict[str, WorkerJobAssignment] = {}
        self.target_places: dict[str, WorkplaceContext] = {}
        self.marker_settings: dict[str, WorkerAssignmentMarker] = {}
        self.data: ShiftPlayback | None = None
        self.scenarios: tuple[RotationScenario, ...] = ()
        self.elapsed = 0.0
        self.wall = 0.0
        self.glyphs: list[ShiftGlyph] = []
        self.people: list[ShiftGlyph] = []
        self.locate_timer = QTimer(self)
        self.locate_timer.setInterval(180)
        self.locate_timer.timeout.connect(self.pulse_worker)
        self._pulse_count = 0
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        window.layer.changed.connect(self.guard_history)
        window.map_panel.canvas.fitted.connect(self.resize_glyphs)
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        app.focusChanged.connect(self.guard_history)
        self.clock = QElapsedTimer()
        self.setObjectName("shiftPlayback")
        self.setStyleSheet(
            "QGroupBox#shiftPlayback {background:#edf7fa;border:1px solid "
            "#b9dbe1;border-radius:7px;margin-top:8px;} "
            "QGroupBox#shiftPlayback::title {color:#087f91;font-weight:bold;} "
            "QComboBox,QDoubleSpinBox {min-height:28px;} QPushButton {min-"
            "height:28px;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 6)
        layout.setSpacing(3)
        row = QHBoxLayout()
        row.addStretch(1)
        choices = QHBoxLayout()
        choices.addWidget(QLabel(window.text("Rotation", "Rotación")))
        self.rotation = QComboBox()
        self.rotation.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed
        )
        self.rotation.setMinimumWidth(220)
        self.rotation.setToolTip(
            window.text(
                (
                    "Choose a complete mapped JROT rotation. Reload reads newly kept "
                    "results."
                ),
                (
                    "Elija una rotación JROT completa y posicionada. Recargar lee los "
                    "resultados nuevos."
                ),
            )
        )
        self.variant = QComboBox()
        self.variant.addItems(
            [window.text("Baseline", "Inicial"), window.text("Optimized", "Optimizada")]
        )
        self.variant.setToolTip(
            window.text(
                "Compare paired schedules using the same fixed Job locations.",
                (
                    "Compare las programaciones con las mismas posiciones fijas de "
                    "trabajos."
                ),
            )
        )
        self.play = QPushButton(window.text("Play", "Reproducir"))
        self.play.setIcon(self.style_icon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play.clicked.connect(self.toggle)
        self.previous_button = QPushButton(window.text("Previous", "Anterior"))
        self.previous_button.setIcon(
            self.style_icon(QStyle.StandardPixmap.SP_MediaSkipBackward)
        )
        self.previous_button.setToolTip(
            window.text(
                "Jump to the previous work block or break; retain Play/Pause.",
                "Ir al bloque o descanso anterior; conservar reproducción o pausa.",
            )
        )
        self.previous_button.clicked.connect(lambda: self.jump_boundary(False))
        self.next_button = QPushButton(window.text("Next", "Siguiente"))
        self.next_button.setIcon(
            self.style_icon(QStyle.StandardPixmap.SP_MediaSkipForward)
        )
        self.next_button.setToolTip(
            window.text(
                "Jump to the next work block or break; retain Play/Pause.",
                "Ir al siguiente bloque o descanso; conservar reproducción o pausa.",
            )
        )
        self.next_button.clicked.connect(lambda: self.jump_boundary(True))
        self.stop_button = QPushButton(window.text("Stop", "Detener"))
        self.stop_button.setIcon(self.style_icon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop)
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.5, 20)
        self.speed.setSingleStep(0.5)
        self.speed.setValue(2)
        self.speed.setSuffix(window.text(" s/block", " s/bloque"))
        self.speed.setToolTip(
            window.text(
                (
                    "Playback seconds per work block. Real block minutes still "
                    "determine exposure."
                ),
                (
                    "Segundos de reproducción por bloque. Los minutos reales "
                    "determinan la exposición."
                ),
            )
        )
        self.motion = QDoubleSpinBox()
        self.motion.setRange(0.3, 5)
        self.motion.setSingleStep(0.1)
        self.motion.setValue(1.2)
        self.motion.setSuffix(window.text(" s/move", " s/mover"))
        self.motion.setToolTip(
            window.text(
                "Break transition duration; moves without a break take half this time.",
                "Duración del movimiento en descansos; sin descanso demora la mitad.",
            )
        )
        self.refresh_button = QPushButton(window.text("Reload", "Recargar"))
        self.refresh_button.setIcon(
            self.style_icon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.refresh_button.setToolTip(
            window.text(
                "Reload current rotation results and return to the beginning; "
                "keep playing only if already playing.",
                "Recargar resultados y volver al inicio; "
                "continuar solo si ya se estaba reproduciendo.",
            )
        )
        self.refresh_button.clicked.connect(self.reload)
        choices.addWidget(self.rotation, 1)
        choices.addWidget(self.variant)
        layout.addLayout(choices)
        for control, stretch in (
            (self.previous_button, 0),
            (self.play, 0),
            (self.next_button, 0),
            (self.stop_button, 0),
            (self.speed, 0),
            (self.motion, 0),
            (self.refresh_button, 0),
        ):
            control.setMaximumWidth(
                160 if control in (self.speed, self.motion) else 135
            )
            row.addWidget(control, stretch)
        row.addStretch(1)
        self.media_row = row
        self.timeline = ShiftTimeline(self)
        self.timeline.seek.connect(self.seek)
        layout.addWidget(self.timeline)
        layout.addLayout(row)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color:#0b4266;font-weight:bold;")
        layout.addWidget(self.status)
        self.details = QWidget()
        details_layout = QVBoxLayout(self.details)
        details_layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel(window.text("Rotation exposure", "Exposición de rotación"))
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#0b3d60")
        details_layout.addWidget(title)
        symbols = QLabel(
            window.text(
                "Fixed squares: Jobs · Moving shapes: workers",
                "Cuadrados fijos: trabajos · Símbolos móviles: trabajadores",
            )
        )
        symbols.setWordWrap(True)
        details_layout.addWidget(symbols)
        bands = QLabel(
            '<span style="color:#16b83e">●</span> 0-25 '
            '<span style="color:#d0a800">●</span> 25-37.5 '
            '<span style="color:#ff8c16">●</span> 37.5-50 '
            '<span style="color:#ff3934">●</span> &gt;50'
        )
        bands.setToolTip(
            window.text(
                "Shared risk ranges; colors vary continuously within the scale.",
                "Rangos compartidos; el color varía de forma continua en la escala.",
            )
        )
        details_layout.addWidget(bands)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        details_layout.addWidget(self.summary)
        self.table = ShiftExposureTable(0, 3)
        self.table.setHorizontalHeaderLabels(
            [
                window.text("Worker", "Trabajador"),
                window.text("Now", "Actual"),
                window.text("Final", "Final"),
            ]
        )
        self.table.setWordWrap(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vertical, horizontal = (
            self.table.verticalHeader(),
            self.table.horizontalHeader(),
        )
        assert vertical is not None and horizontal is not None
        vertical.setDefaultSectionSize(32)
        horizontal.setStretchLastSection(False)
        horizontal.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        horizontal.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        horizontal.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 76)
        self.table.setColumnWidth(2, 76)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )
        self.table.itemSelectionChanged.connect(self.table_selected)
        details_layout.addWidget(self.table, 1)
        self.problem = QLabel()
        self.problem.setWordWrap(True)
        self.problem.setStyleSheet(
            "color:#805000;background:#fff4da;padding:8px;"
            "border:1px solid #ead29a;border-radius:5px;"
        )
        self.problem.hide()
        details_layout.addWidget(self.problem)
        note = QLabel(
            window.text(
                (
                    "Worker color = accumulated schedule contribution over the full "
                    "JROT averaging period. Job squares stay fixed. This is not the "
                    "worker's individual assessment or an injury prediction. Breaks "
                    "add no exposure or recovery."
                ),
                (
                    "Color del trabajador = contribución acumulada al índice JROT. Los"
                    " cuadrados de trabajos permanecen fijos. No es la evaluación "
                    "individual ni una predicción de lesión. Los descansos no agregan "
                    "exposición ni recuperación."
                ),
            )
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "color:#35566c;padding:10px;background:#edf7fa;border:1px solid "
            "#cbdfe6;border-radius:6px;"
        )
        details_layout.addWidget(note)
        self.rotation.currentIndexChanged.connect(self.select)
        self.variant.currentIndexChanged.connect(self.switch_schedule)
        self.speed.valueChanged.connect(self.change_pacing)
        self.motion.valueChanged.connect(self.change_pacing)
        self.worker_overview = ShiftWorkerOverview(self)
        self.hide()
        self.details.hide()

    def style_icon(self, icon: QStyle.StandardPixmap) -> QIcon:
        """Read a standard media icon through the owned Qt style.

        Args:
            icon: Semantic Qt player icon identity.

        Returns:
            Native media glyph.
        """
        style = self.style()
        assert style is not None
        return style.standardIcon(icon)

    def guard_history(
        self, _old: QWidget | None = None, _new: QWidget | None = None
    ) -> None:
        """Keep document replay shortcuts disabled in this read-only mode.

        Args:
            _old: Optional former focus widget from QApplication.
            _new: Optional new focus widget; native text Undo remains independent.

        Returns:
            None; normal history refresh restores actions when leaving playback.
        """
        if self.active:
            self.host.history_actions.undo_action.setEnabled(False)
            self.host.history_actions.redo_action.setEnabled(False)

    def enter(self) -> None:
        """Activate an opt-in read-only surface after ordinary map edits are settled.

        Args:
            None.

        Returns:
            None; pending map edits retain the ordinary mode with an explanation.
        """
        if self.active:
            return
        if self.host.layer.pending or self.host.map_panel.pending_image is not None:
            self.host.map_panel.show_error(
                self.host.text(
                    "Finish map edits before Shift View.",
                    "Termine los cambios del mapa antes de Vista de turno.",
                )
            )
            self.host.filters.risk_buttons[self.host.filters.risk_view].setChecked(True)
            return
        self._ordinary_splitter = self.host.splitter.sizes()
        self.active = True
        self._ordinary_tab = self.host.tabs.currentIndex()
        self.host.outcome_stack.setCurrentWidget(self)
        self.host.tabs.removeTab(0)
        self.host.tabs.insertTab(
            0,
            self.details,
            self._exposure_icon,
            self.host.text("Rotation exposure", "Exposición de rotación"),
        )
        self.details.show()
        self.host.overviews.addWidget(self.worker_overview)
        self.host.overviews.setCurrentWidget(self.worker_overview)
        self.host.tabs.setTabText(
            1, self.host.text("Worker Overview", "Resumen de trabajadores")
        )
        self.host.tabs.setTabIcon(1, self.host.worker_icon)
        self.host.tabs.setCurrentIndex(0)
        self.host.map_panel.canvas.read_only = True
        self.host.map_tools.refresh()
        self.filter_selection = (
            self.host.filters.applied or self.host.filters.selection()
        )
        for key in ("open", "save", "export"):
            self.host.map_panel.buttons[key].setEnabled(False)
        self.guard_history()
        self.reload()
        self.host.splitter.setSizes(self._ordinary_splitter)

    def leave(self) -> None:
        """Stop playback and restore normal PLOT datasets and editing controls.

        Args:
            None.

        Returns:
            None; no player state is added to project history.
        """
        if not self.active:
            return
        self.active = False
        self.stop()
        self.clear_glyphs()
        self.hide()
        self.details.hide()
        self.host.tabs.removeTab(0)
        self.host.tabs.insertTab(
            0,
            self.host.tools,
            self._tools_icon,
            self.host.text("Tools Overview", "Resumen de herramientas"),
        )
        self.host.tools.show()
        self.host.overviews.removeWidget(self.worker_overview)
        self.worker_overview.hide()
        self.details.hide()
        self.host.outcome_stack.setCurrentWidget(self.host.outcome)
        self.host.map_panel.canvas.read_only = False
        self.host.map_tools.refresh()
        self.host.filters.apply_filters()
        self.host.map_panel.update_view_actions()
        self.host.filters.risk_buttons[self.host.filters.risk_view].setChecked(True)
        self.host.tabs.setCurrentIndex(self._ordinary_tab)
        self.host.history_actions.refresh()
        self.host.splitter.setSizes(self._ordinary_splitter)

    def reload(self) -> None:
        """Read the latest retained rotations without accepting or running a solve.

        Args:
            None.

        Returns:
            None; selected identity survives when still available.
        """
        running = self.timer.isActive()
        selected = self.rotation.currentData()
        self.scenarios = tuple(
            s
            for s in self.repository.load_rotation_scenarios()
            if self.rotation_matches(s)
        )
        self.rotation.blockSignals(True)
        self.rotation.clear()
        for scenario in self.scenarios:
            self.rotation.addItem(scenario.name, scenario.scenario_id)
        index = self.rotation.findData(selected)
        self.rotation.setCurrentIndex(max(0, index))
        self.rotation.blockSignals(False)
        self.rotation.setEnabled(bool(self.rotation.count()))
        self.select()
        if running and self.play.isEnabled():
            self.toggle()

    def switch_schedule(self) -> None:
        """Compare another variant/tool at the same shift minute.

        Args:
            None.

        Returns:
            None; playback resumes only if it was running before the switch.
        """
        elapsed, running = self.elapsed, self.timer.isActive()
        self.select()
        if self.data is not None:
            self.seek(elapsed)
            if running:
                self.toggle()

    def change_pacing(self) -> None:
        """Rebase preview seconds at the current real minute when speed changes.

        Args:
            None.

        Returns:
            None; retain the frame and pause for deliberate resume.
        """
        self.seek(self.elapsed)

    def clear_glyphs(self) -> None:
        """Release scene items before any scene/image replacement.

        Args:
            None.

        Returns:
            None.
        """
        self.locate_timer.stop()
        for item in self.glyphs:
            scene = item.scene()
            if scene is not None:
                scene.removeItem(item)
            item.deleteLater()
        self.glyphs.clear()
        self.people.clear()

    def select(self) -> None:
        """Prepare a fresh snapshot and restart the selected paired schedule.

        Args:
            None.

        Returns:
            None; incomplete data disables playback and shows its exact reason.
        """
        if not self.active:
            return
        self.pause()
        self.clear_glyphs()
        self.data = None
        self.problem.clear()
        self.problem.hide()
        self.timeline.data = None
        self.table.setRowCount(0)
        self.elapsed = self.wall = 0
        self.selected_worker = None
        try:
            scenario = next(
                (
                    s
                    for s in self.scenarios
                    if s.scenario_id == self.rotation.currentData()
                ),
                None,
            )
            if scenario is None:
                raise ValueError(
                    self.host.text(
                        "No rotations match the selected workplace and shift.",
                        "Ninguna rotación coincide con el lugar de trabajo y turno.",
                    )
                )
            self.data = prepare_shift(
                self.repository,
                scenario,
                self.filter_selection.tool
                if self.filter_selection
                else self.host.filters.tools.selected,
                self.variant.currentIndex() == 1,
                allow_partial=True,
            )
            if self.host.map_panel.canvas.background is None:
                raise ValueError("Load the plant layout image before playback.")
            for original_item in self.host.layer.items.values():
                original_item.hide()
            scene = self.host.map_panel.canvas.scene()
            assert scene is not None
            self.cache_catalogs(scenario)
            for destination in self.data.destinations:
                marker = self.marker_settings.get(destination.key)
                item = ShiftGlyph(
                    destination.job_id,
                    True,
                    size=marker.size if marker else 30,
                    scale=marker.scale if marker else 1,
                    view_scale=self.host.map_panel.canvas.fitted_scale,
                )
                item.color = shift_color(destination.risk)
                item.setPos(destination.point.x, destination.point.y)
                item.setToolTip(
                    f"{destination.job_id} · {destination.name}\n"
                    f"{self.host.text('Job risk', 'Riesgo del trabajo')}: "
                    f"{destination.risk:.1f}%"
                )
                item.setVisible(self.destination_visible(destination.key))
                scene.addItem(item)
                self.glyphs.append(item)
            self.table.setRowCount(len(self.data.rows))
            for index, (identity, name, sex) in enumerate(self.data.workers):
                assignment = self.assignment_for_worker(identity)
                marker = (
                    self.repository.load_plot_positions().marker(
                        assignment.assignment_id
                    )
                    if assignment
                    else None
                )
                item = ShiftGlyph(
                    identity,
                    False,
                    sex,
                    size=marker.size if marker else 30,
                    scale=marker.scale if marker else 1,
                    view_scale=self.host.map_panel.canvas.fitted_scale,
                )
                item.picked.connect(self.select_worker)
                scene.addItem(item)
                self.glyphs.append(item)
                self.people.append(item)
                self.table.setItem(index, 0, QTableWidgetItem(f"{identity} · {name}"))
                name_cell = self.table.item(index, 0)
                assert name_cell is not None
                name_cell.setData(Qt.ItemDataRole.UserRole, identity)
                name_cell.setToolTip(f"{identity} · {name}")
                for column in (1, 2):
                    cell = QTableWidgetItem("—")
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    font = cell.font()
                    font.setBold(True)
                    cell.setFont(font)
                    self.table.setItem(index, column, cell)
            self.timeline.data = self.data
            self.summary.setText(
                self.host.text(
                    "Read-only • Paired retained JROT values"
                    if self.data.recorded
                    else "Read-only • Current baseline Job values",
                    "Solo lectura • Valores JROT retenidos"
                    if self.data.recorded
                    else "Solo lectura • Valores actuales de trabajos",
                )
            )
            if scenario.run is not None and not own_run_is_current(
                scenario,
                self.repository.load_hierarchy(),
                self.repository.load_jobs(),
                self.repository.load_job_risk(),
            ):
                self.summary.setText(
                    self.host.text(
                        "Recorded pair • Current inputs changed",
                        "Par registrado • Los datos actuales cambiaron",
                    )
                )
            self.seek(0)
            self.select_worker(next(iter(sorted(self.visible_ids)), None))
            self.timeline.setEnabled(not self.data.issues)
            self.play.setEnabled(not self.data.issues and bool(self.visible_ids))
            self.stop_button.setEnabled(not self.data.issues and bool(self.visible_ids))
            if self.data.issues:
                self.problem.setText(
                    self.host.text(
                        "Playback unavailable: ", "Reproducción no disponible: "
                    )
                    + "\n".join(self.data.issues[:2])
                    + (
                        self.host.text(
                            f"\n{len(self.data.issues) - 2} more problems; "
                            "hover for details.",
                            f"\n{len(self.data.issues) - 2} problemas más; "
                            "ver detalles al pasar el cursor.",
                        )
                        if len(self.data.issues) > 2
                        else ""
                    )
                )
                self.problem.setToolTip("\n".join(self.data.issues))
                self.problem.show()
        except (ValueError, KeyError) as error:
            self.status.setText(str(error))
            self.problem.setText(str(error))
            self.problem.show()
            self.summary.setText(self.host.text("Read-only", "Solo lectura"))
            self.timeline.setEnabled(False)
            self.play.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.data = None
            self.show_available_static()
        self.timeline.update()
        for key in ("open", "save", "export"):
            self.host.map_panel.buttons[key].setEnabled(False)

    def pause(self) -> None:
        """Pause local wall time while keeping the exact current preview frame.

        Args:
            None.

        Returns:
            None.
        """
        self.timer.stop()
        self.play.setText(self.host.text("Play", "Reproducir"))
        self.play.setIcon(self.style_icon(QStyle.StandardPixmap.SP_MediaPlay))

    def stop(self) -> None:
        """Stop and return to the selected schedule's first work block.

        Args:
            None.

        Returns:
            None.
        """
        self.pause()
        self.wall = 0
        if self.active and self.data is not None:
            self.seek(0)

    def toggle(self) -> None:
        """Toggle finite playback; an ended schedule restarts from the beginning.

        Args:
            None.

        Returns:
            None.
        """
        if self.timer.isActive():
            self.pause()
        elif self.data is not None and not self.data.issues and self.visible_ids:
            duration = sum(
                s.seconds
                for s in playback_stages(
                    self.data, self.speed.value(), self.motion.value()
                )
            )
            if self.wall >= duration:
                self.wall = 0
            self.clock.start()
            self.timer.start()
            self.play.setText(self.host.text("Pause", "Pausar"))
            self.play.setIcon(self.style_icon(QStyle.StandardPixmap.SP_MediaPause))

    def seek(self, elapsed: float) -> None:
        """Pause at an exact real shift minute and synchronize the preview wall clock.

        Args:
            elapsed: Requested minute relative to shift start.

        Returns:
            None.
        """
        if self.data is None:
            return
        self.pause()
        self.elapsed = (
            0.0
            if self.data.issues
            else max(0.0, min(self.data.timing.shift_minutes, elapsed))
        )
        self.wall = 0
        for stage in playback_stages(
            self.data, self.speed.value(), self.motion.value()
        ):
            if stage.end > self.elapsed:
                self.wall += stage.seconds * max(
                    0.0,
                    (self.elapsed - stage.begin) / max(1.0, stage.end - stage.begin),
                )
                break
            self.wall += stage.seconds
        a, b, fraction = self.data.phase(self.elapsed)
        self.project(a, b, fraction)

    def tick(self) -> None:
        """Advance smooth local playback without touching any native project values.

        Args:
            None.

        Returns:
            None; the timer stops exactly at the shift end.
        """
        if self.data is None:
            self.pause()
            return
        self.wall += self.clock.restart() / 1000
        remaining = self.wall
        stages = playback_stages(self.data, self.speed.value(), self.motion.value())
        for stage in stages:
            if remaining < stage.seconds:
                fraction = remaining / stage.seconds
                self.elapsed = stage.begin + (stage.end - stage.begin) * fraction
                self.project(
                    stage.previous,
                    stage.following,
                    fraction * fraction * (3 - 2 * fraction),
                )
                return
            remaining -= stage.seconds
        self.elapsed = self.data.timing.shift_minutes
        last = len(self.data.timing.block_minutes) - 1
        self.project(last, last, 0)
        self.pause()

    def project(self, previous: int, following: int, fraction: float) -> None:
        """Render positions, accumulated colors and exact final reference indices.

        Args:
            previous: Current/source block.
            following: Destination block, equal during productive work.
            fraction: Smooth eased positional fraction; exposure uses real minutes.

        Returns:
            None; fixed Job squares never change position or risk color.
        """
        if self.data is None:
            return
        destinations = {d.key: d for d in self.data.destinations}
        visible_ids: set[str] = set()
        for index, (row, glyph) in enumerate(
            zip(self.data.rows, self.people, strict=True)
        ):
            a = destinations.get(row.target_keys[previous])
            b = destinations.get(row.target_keys[following])
            visible = (
                a is not None
                and b is not None
                and self.worker_visible(row.worker_id)
                and (self.destination_visible(a.key) or self.destination_visible(b.key))
            )
            glyph.setVisible(visible)
            self.table.setRowHidden(index, not visible)
            if not visible or a is None or b is None:
                continue
            visible_ids.add(row.worker_id)
            glyph.setPos(
                QPointF(
                    a.point.x + (b.point.x - a.point.x) * fraction,
                    a.point.y + (b.point.y - a.point.y) * fraction,
                )
            )
            if self.data.issues:
                continue
            score = self.data.index(index, self.elapsed)
            final = self.data.index(index, self.data.timing.shift_minutes)
            glyph.color = shift_color(score)
            glyph.update()
            glyph.setToolTip(
                f"{self.data.workers[index][0]} · {self.data.workers[index][1]}\n"
                f"{a.name} → {b.name}\n"
                f"Accumulated schedule index: {score:.2f}\nFinal: {final:.2f}"
            )
            for column, value in ((1, score), (2, final)):
                cell = self.table.item(index, column)
                assert cell is not None
                cell.setText(f"{value:.2f}")
                color = shift_color(value)
                cell.setBackground(color)
                cell.setForeground(contrast_ink(color))
        changed = visible_ids != self.visible_ids
        self.visible_ids = visible_ids
        if (
            self.selected_worker is not None
            and self.selected_worker not in self.visible_ids
        ):
            self.selected_worker = next(iter(sorted(self.visible_ids)), None)
            self.select_worker(self.selected_worker)
        if changed:
            self.worker_overview.refresh()
        self.worker_overview.show_details()
        self.previous_button.setEnabled(not self.data.issues and self.elapsed > 0)
        self.next_button.setEnabled(
            not self.data.issues and self.elapsed < self.data.timing.shift_minutes
        )
        self.timeline.elapsed = self.elapsed
        self.timeline.update()
        clock = int(self.data.start + self.elapsed) % 1440
        phase = (
            self.host.text("Moving to next Job", "Movimiento al siguiente trabajo")
            if previous != following
            else self.host.text(f"Block {previous + 1}", f"Bloque {previous + 1}")
        )
        self.status.setText(
            f"{self.data.plant} · {clock // 60:02}:{clock % 60:02} · "
            f"{phase} · {self.host.text('Read-only', 'Solo lectura')}"
        )

    def assignment_for_worker(self, worker_id: str) -> WorkerJobAssignment | None:
        """Resolve the selected rotation's exact participant assignment.

        Args:
            worker_id: Stable worker identity.

        Returns:
            Baseline assignment or None; never an invented placement.
        """
        return self.assignments.get(worker_id)

    def scope_matches(self, place: WorkplaceContext) -> bool:
        """Apply the ordinary workplace prefixes and shift to one fixed destination.

        Args:
            place: Exact station/shift ownership.

        Returns:
            True when the applied shared PLOT scope includes the destination.
        """
        if self.filter_selection is None:
            return False
        scope = self.filter_selection.scope
        path = (place.plant_name, place.section_name, place.line_name, place.station_id)
        return (scope.shift is None or scope.shift == place.shift_id) and any(
            path[: len(prefix)] == prefix for prefix in scope.paths
        )

    def rotation_matches(self, scenario: RotationScenario) -> bool:
        """Offer rotations having at least one real destination in the applied scope.

        Args:
            scenario: Current draft or retained named rotation.

        Returns:
            True for any matching exact placement or participant assignment. Unmapped
            general Jobs do not manufacture a plant association.
        """
        inputs = scenario.run.inputs if scenario.run else scenario.inputs
        jobs = self.repository.load_jobs()
        placements = {p.placement_id: p for p in jobs.placements}
        assignments = {a.assignment_id: a for a in jobs.assignments}
        return any(
            t.placement_id in placements
            and self.scope_matches(placements[t.placement_id].workplace)
            for t in inputs.targets
        ) or any(
            w.assignment_id in assignments
            and self.scope_matches(assignments[w.assignment_id].worker.workplace)
            for w in inputs.workers
        )

    def cache_catalogs(self, scenario: RotationScenario) -> None:
        """Freeze metadata for cheap frame updates and exact scope predicates.

        Args:
            scenario: Selected paired rotation snapshot.

        Returns:
            None; only local caches change, never project data.
        """
        self.catalog_people = {
            w.worker_id: w for w in self.repository.load_hierarchy().work.workers
        }
        jobs = self.repository.load_jobs()
        assignments = {a.assignment_id: a for a in jobs.assignments}
        placements = {p.placement_id: p for p in jobs.placements}
        inputs = scenario.run.inputs if scenario.run else scenario.inputs
        self.assignments = {
            w.worker_id: assignments[w.assignment_id]
            for w in inputs.workers
            if w.assignment_id in assignments
        }
        self.target_places = {
            t.key: placements[t.placement_id].workplace
            for t in inputs.targets
            if t.placement_id in placements
        }
        positions = self.repository.load_plot_positions()
        keys = (
            {row.worker_id: row.target_keys[0] for row in self.data.rows}
            if self.data
            else {}
        )
        self.marker_settings = {}
        for worker, assignment in self.assignments.items():
            marker = positions.marker(assignment.assignment_id)
            if marker and worker in keys:
                self.marker_settings[keys[worker]] = marker

    def destination_visible(self, key: str) -> bool:
        """Test a fixed destination against applied hierarchy/shift filters.

        Args:
            key: Exact rotation target key.

        Returns:
            True only for a known matching workplace.
        """
        place = self.target_places.get(key)
        return place is not None and self.scope_matches(place)

    def worker_visible(self, identity: str) -> bool:
        """Apply shared canonical demographics independently of worker assessments.

        Args:
            identity: Stable participant worker ID.

        Returns:
            Whether this participant passes the applied demographic predicate.
        """
        person = self.catalog_people.get(identity)
        return person is not None and (
            self.filter_selection is None
            or self.filter_selection.demographics.matches(
                person.details, current_year=self.host.current_year
            )
        )

    def apply_filters(self, selection: PlotFilterSelection) -> None:
        """Apply shared tool/workplace/demographic selection at the same shift minute.

        Args:
            selection: Ordinary PLOT applied filter snapshot.

        Returns:
            None; unavailable rotations show an empty state instead of switching plant.
        """
        elapsed, running = self.elapsed, self.timer.isActive()
        self.filter_selection = selection
        self.host.shift_button.setChecked(True)
        self.pause()
        self.reload()
        if self.data is not None:
            self.seek(elapsed)
            if running and self.play.isEnabled():
                self.toggle()

    def resize_glyphs(self, scale: float) -> None:
        """Normalize symbols exactly like ordinary PLOT after viewport resizing.

        Args:
            scale: New fitted image scale, excluding user magnification.

        Returns:
            None; canonical anchors and playback clock are unchanged.
        """
        for glyph in self.glyphs:
            glyph.set_view_scale(scale)

    def table_selected(self) -> None:
        """Link an exposure-table row to the blue worker frame.

        Args:
            None.

        Returns:
            None; selecting a row never starts movement or edits data.
        """
        selected = self.table.selectionModel()
        rows = selected.selectedRows() if selected is not None else []
        if not rows:
            self.select_worker(None)
            return
        cell = self.table.item(rows[0].row(), 0)
        if cell is not None:
            identity = cell.data(Qt.ItemDataRole.UserRole)
            if isinstance(identity, str):
                self.select_worker(identity)

    def select_worker(self, identity: str | None) -> None:
        """Synchronize worker selection across map, table and read-only overview.

        Args:
            identity: Visible worker ID, or None clears selection.

        Returns:
            None; worker remains immovable even when selected.
        """
        self.locate_timer.stop()
        self.selected_worker = identity
        for glyph in self.people:
            glyph.setSelected(glyph.label == identity and glyph.isVisible())
        self.table.blockSignals(True)
        row = -1
        for index in range(self.table.rowCount()):
            cell = self.table.item(index, 0)
            if cell is not None and cell.data(Qt.ItemDataRole.UserRole) == identity:
                row = index
                break
        if row >= 0:
            self.table.selectRow(row)
        else:
            self.table.setCurrentCell(-1, -1)
            self.table.clearSelection()
        self.table.blockSignals(False)
        self.worker_overview.refresh()
        self.host.map_panel.canvas._viewport.update()

    def locate_worker(self) -> None:
        """Center the selected moving worker using the existing map navigation.

        Args:
            None.

        Returns:
            None; viewing does not change assignment positions or project history.
        """
        glyph = next(
            (
                g
                for g in self.people
                if g.label == self.selected_worker and g.isVisible()
            ),
            None,
        )
        if glyph is not None:
            glyph.setSelected(True)
            self.host.map_panel.canvas.locate_item(glyph)
            self._pulse_count = 0
            self.locate_timer.start()

    def pulse_worker(self) -> None:
        """Blink the selected worker frame, retaining the final selected state.

        Args:
            None.

        Returns:
            None; teardown and selection changes stop this timer before glyph deletion.
        """
        self._pulse_count += 1
        for glyph in self.people:
            if glyph.label == self.selected_worker:
                glyph.setSelected(self._pulse_count % 2 == 0 or self._pulse_count >= 8)
        if self._pulse_count >= 8:
            self.locate_timer.stop()
        self.host.map_panel.canvas._viewport.update()

    def jump_boundary(self, forward: bool) -> None:
        """Seek to an adjacent block/break boundary without changing Play/Pause.

        Args:
            forward: True advances, False returns to the preceding boundary.

        Returns:
            None; unavailable or incomplete schedules remain inert.
        """
        if self.data is None or self.data.issues:
            return
        points = {0.0, float(self.data.timing.shift_minutes)}
        for block in self.data.timing.blocks():
            for piece in block.pieces:
                points.update((float(piece.start), float(piece.end)))
        for pause in self.data.timing.breaks:
            points.update((float(pause.interval.start), float(pause.interval.end)))
        candidates = sorted(
            p
            for p in points
            if (p > self.elapsed + 0.001 if forward else p < self.elapsed - 0.001)
        )
        if not candidates:
            return
        running = self.timer.isActive()
        self.seek(candidates[0] if forward else candidates[-1])
        if running and self.elapsed < self.data.timing.shift_minutes:
            self.toggle()

    def show_available_static(self) -> None:
        """Show known filtered anchors neutrally when timing/setup is incomplete.

        Args:
            None.

        Returns:
            None; absent rotation means an empty map, never unrelated workers.
        """
        for original in self.host.layer.items.values():
            original.hide()
        self.visible_ids.clear()
        scenario = next(
            (s for s in self.scenarios if s.scenario_id == self.rotation.currentData()),
            None,
        )
        if scenario is None:
            self.worker_overview.refresh()
            return
        self.cache_catalogs(scenario)
        scene = self.host.map_panel.canvas.scene()
        assert scene is not None
        positions = self.repository.load_plot_positions()
        for identity, assignment in self.assignments.items():
            if not self.worker_visible(identity) or not self.scope_matches(
                assignment.worker.workplace
            ):
                continue
            point = positions.worker_point(
                assignment.assignment_id, self.repository.load_jobs()
            )
            marker = positions.marker(assignment.assignment_id)
            if point is None:
                continue
            person = self.catalog_people[identity]
            glyph = ShiftGlyph(
                identity,
                False,
                person.details.sex if person.details else None,
                size=marker.size if marker else 30,
                scale=marker.scale if marker else 1,
                view_scale=self.host.map_panel.canvas.fitted_scale,
            )
            glyph.setPos(point.x, point.y)
            glyph.picked.connect(self.select_worker)
            glyph.setToolTip(
                self.host.text(
                    "Incomplete rotation: no exposure value calculated.",
                    "Rotación incompleta: no se calcula exposición.",
                )
            )
            scene.addItem(glyph)
            self.glyphs.append(glyph)
            self.people.append(glyph)
            self.visible_ids.add(identity)
            row = self.table.rowCount()
            self.table.insertRow(row)
            cell = QTableWidgetItem(
                f"{identity} · {person.first_name or ''} {person.last_name or ''}"
            )
            cell.setData(Qt.ItemDataRole.UserRole, identity)
            self.table.setItem(row, 0, cell)
            self.table.setItem(row, 1, QTableWidgetItem("—"))
            self.table.setItem(row, 2, QTableWidgetItem("—"))
        self.select_worker(next(iter(sorted(self.visible_ids)), None))
