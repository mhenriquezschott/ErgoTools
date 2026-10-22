"""Original PLOT dialog composition over injected saved project capabilities.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.assessment_export import SummaryExportRow
from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.application.plot_access import PlotRepository
from ergotools.application.plot_history import PlotEditState
from ergotools.application.plot_layout import PlantLayoutReader, PlantLayoutWriter
from ergotools.application.plot_results import PlotResults, saved_plot_results
from ergotools.application.project_editing import ProjectEditingSession
from ergotools.application.session import DocumentSession
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.plant_layout_image import PlantLayoutImage
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.presentation.desktop.plot_filters_panel import PlotFiltersPanel
from ergotools.presentation.desktop.plot_history_actions import PlotHistoryActions
from ergotools.presentation.desktop.plot_job_overview import PlotJobOverview
from ergotools.presentation.desktop.plot_map_panel import PlotMapPanel
from ergotools.presentation.desktop.plot_marker_layer import PlotMarkerLayer
from ergotools.presentation.desktop.plot_outcome_panel import PlotOutcomePanel
from ergotools.presentation.desktop.plot_tools_overview import PlotToolsOverview
from ergotools.presentation.desktop.plot_worker_overview import PlotWorkerOverview
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE
from ergotools.presentation.plot_csv import plot_csv_table


class PlotWindow(QDialog):
    """Compose PLOT with one shared project Save or explicit diagnostic controls.

    The caller retains project lifetime. Integrated accepted geometry/images are
    staged privately; closing retains them without durable writes. Diagnostic
    workspaces retain their original local Save/discard policy. Assessment handoff
    closes this dialog only after its own pending-edit validation and
    map consent and the integrated editor's acceptance. Remaining map rail workflows use
    explicit save/export intent. Production navigation borrows the same workspace-owned
    project connection for the modal lifetime.
    """

    def __init__(
        self,
        repository: PlotRepository,
        reader: PlantLayoutReader,
        writer: PlantLayoutWriter,
        import_image: Callable[[str], PlantLayoutImage],
        icons: Mapping[str, QIcon],
        *,
        current_year: int,
        csv_writer: Callable[[str, tuple[tuple[str, ...], ...]], None] | None = None,
        system: MeasurementSystem = MeasurementSystem.METRIC,
        language: Language = Language.ENGLISH,
        load_assessment: Callable[[SummaryExportRow], bool] | None = None,
        parent: QWidget | None = None,
        editing: ProjectEditingSession | None = None,
        gauge_markers: GaugeMarkerSettings | None = None,
        change_gauge_markers: Callable[[GaugeMarkerSettings], None] | None = None,
    ) -> None:
        """Build the title-row actions and fitted PLOT regions without saving records.

        The root minimum constraint follows live child size hints. Expanding filters
        grows the window as needed, retaining the complete rail and chart controls
        without introducing plant-image scrollbars. Ten-pixel outer margins match
        JROT; the window size includes the added inset without shrinking content.

        Args:
            repository: Borrowed active-project capability; the caller retains
                connection lifetime.
            reader: Injected reader of embedded plant-layout image data.
            writer: Injected explicit plant-layout writer; preview/open actions do not
                call it.
            import_image: Injected validator returning decoded source image bytes and
                metadata for a chosen file.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            current_year: Explicit calendar year for demographic ages; keeps loaded
                projections deterministic.
            csv_writer: Optional file writer receiving a destination and complete CSV
                cells.
            system: Measurement display policy; conversions preserve canonical
                source/body units.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            load_assessment: Optional host callback accepting the exact saved
                assessment; True completes handoff.
            editing: Shared private project session; None retains diagnostic
                Save controls.
            gauge_markers: Initial shared main/PLOT risk-gauge options, or defaults.
            change_gauge_markers: Optional preference-save callback; local previews
                remain possible without a personal store.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.editing = editing
        self._accepting_plot = True
        self._plot_accept_failed = False
        self._save_gauge_markers = change_gauge_markers
        self.repository = repository
        self.language = language
        self.current_year = current_year
        self.system = system
        self.csv_writer = csv_writer
        self.load_assessment = load_assessment
        self._closure_accepted = False
        self._filter_results: dict[PlotFilterSelection, PlotResults] = {}
        self.setObjectName("plotDialog")
        self.setWindowTitle("Plant-Layout Organizational Tool (PLOT)")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.setMinimumSize(1316, 1049)
        self.resize(1476, 1124)
        self.setStyleSheet(PLOT_STYLE)
        hierarchy = repository.load_hierarchy()
        self.map_panel = PlotMapPanel(
            hierarchy, reader, writer, import_image, icons, language=language
        )
        self.layer = PlotMarkerLayer(
            self.map_panel.canvas,
            repository.load_jobs(),
            repository.save_plot_positions,
            self.map_panel.show_error,
            current_year=current_year,
            language=language,
            load_assessment=self.handoff if load_assessment is not None else None,
        )
        self.filters = PlotFiltersPanel(
            hierarchy,
            self.map_panel,
            icons,
            self.apply_selection,
            system=system,
            language=language,
        )
        self.tools = PlotToolsOverview(self.layer, icons, language=language)
        self.workers = PlotWorkerOverview(
            self.layer, icons, system=system, language=language
        )
        self.jobs = PlotJobOverview(self.layer, icons, language=language)
        self.overviews = QStackedWidget()
        self.overviews.addWidget(self.workers)
        self.overviews.addWidget(self.jobs)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("plotDetailsTabs")
        self.tabs.setIconSize(QSize(24, 24))
        self.tabs.addTab(
            self.tools,
            icons["plot"],
            self.text("Tools Overview", "Resumen de herramientas"),
        )
        # Retain the source worker glyph's 82/96 transparent visual padding.
        pixmap = QPixmap(96, 96)
        pixmap.fill(Qt.GlobalColor.transparent)
        source = icons["worker"].pixmap(QSize(82, 82))
        painter = QPainter(pixmap)
        painter.drawPixmap(
            (96 - source.width()) // 2, (96 - source.height()) // 2, source
        )
        painter.end()
        self.worker_icon = QIcon(pixmap)
        self.job_icon = icons["job_management"]
        self.tabs.addTab(self.overviews, self.worker_icon, "")
        self.tabs.setTabToolTip(
            0,
            self.text(
                "View aggregate charts and metrics for the current filters.",
                "Ver gráficos y métricas agregados de los filtros actuales.",
            ),
        )
        worker_panel = self.workers.widget()
        assert worker_panel is not None
        worker_scrollbar = self.workers.verticalScrollBar()
        assert worker_scrollbar is not None
        self.tabs.setMinimumWidth(
            max(
                390,
                worker_panel.minimumSizeHint().width()
                + worker_scrollbar.sizeHint().width()
                + 8,
            )
        )
        self.tabs.setMaximumWidth(500)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("plotMainSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.map_panel)
        self.splitter.addWidget(self.tabs)
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([1040, 390])
        self.outcome = PlotOutcomePanel(
            self.layer,
            icons,
            language=language,
            gauge_markers=gauge_markers,
            change_gauge_markers=self.change_gauge_markers,
        )
        self.history_actions: PlotHistoryActions | ProjectHistoryActions
        if editing is not None:
            self.history_actions = ProjectHistoryActions(
                self,
                editing,
                icons,
                language,
                prepare=self.accept_plot_fields,
                restored=self.restore_project_plot,
            )
        else:
            self.history_actions = PlotHistoryActions(
                self,
                self.layer,
                icons,
                lambda: (
                    bool(self.workers.controls.field_drafts)
                    or self.jobs.has_unaccepted_fields
                ),
                language=language,
            )

        root = QVBoxLayout(self)
        root.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        # Match JROT's ten-pixel outer inset; enlarge the initial/minimum
        # window by the added margins so panel content retains its space.
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        self.title_row = QHBoxLayout()
        self.title = QLabel(
            self.text(
                "Plant-Layout Organizational Tool (PLOT)",
                "Herramienta organizacional de distribución de planta (PLOT)",
            )
        )
        self.title.setObjectName("dialogTitle")
        self.title_row.addWidget(self.title)
        self.title_row.addStretch(1)
        self.title_row.addWidget(self.history_actions.undo_button)
        self.title_row.addWidget(self.history_actions.redo_button)
        root.addLayout(self.title_row)
        root.addWidget(self.filters)
        # Non-collapsible children propagate their live rail/chart minima through
        # this layout, including demographic disclosure and wrapped chart text.
        root.addWidget(self.splitter, 1)
        root.addWidget(self.outcome)
        self.setMinimumWidth(max(1316, root.minimumSize().width()))
        self.layer.changed.connect(self.sync_mode)
        self.layer.selection_changed.connect(self.reveal_selection)
        for button in self.filters.risk_buttons.values():
            button.clicked.connect(self.apply_risk_mode)
        self.map_panel.buttons["export"].clicked.connect(self.export_csv)
        self.sync_mode()
        if hierarchy.plants:
            self.filters.clear_filters()
            self.filters.apply_filters()
            if self.layer.history is not None:
                self.layer.shared_history = self.layer.history
                self.layer.shared_history.initialize_filters(
                    self.filters.snapshot(), self.filters.applied
                )
                self.layer.replay_view = self.replay_history
        self.filters.history_changed.connect(self.record_filter_history)

        self._accepting_plot = False
        self.layer.project_editing = editing is not None
        if editing is not None:
            self.map_panel.buttons["save"].hide()
            self.workers.controls.save_button.hide()
            self.workers.controls.save_all_button.setText(
                self.text("Apply to all", "Aplicar a todos")
            )
            self.workers.controls.save_all_button.setIcon(icons["filter_apply"])
            self.workers.controls.save_all_button.clicked.disconnect()
            self.workers.controls.save_all_button.clicked.connect(self.apply_plot_batch)
            self.workers.controls.show_success = lambda _message: None
            self.jobs.save_button.hide()
            for field in (
                self.workers.controls.x_input,
                self.workers.controls.y_input,
                self.workers.controls.scale_input,
                self.jobs.x_input,
                self.jobs.y_input,
            ):
                field.editingFinished.connect(self.accept_plot_field_edit)
            self.layer.changed.connect(self.accept_plot_state)
            self.map_panel.buttons["open"].clicked.connect(self.accept_plot_image)
            retained = editing.editor("plot.view")
            if isinstance(retained, PlotEditState):
                self.restore_project_plot()
            elif self.layer.history is not None:
                editing.seed_editor("plot.view", self.layer.history.session.state)

    def apply_plot_batch(self) -> None:
        """Accept the existing batch-layout operation as one shared history action.

        Args:
            None.

        Returns:
            None; existing coordinate/placement validation and atomic batch behavior
            are retained, without a local project Save or success modal.
        """
        if self.editing is None:
            return
        with self.editing.suspend():
            self.workers.controls.save_all()
        self.accept_plot_state()

    def accept_plot_image(self) -> None:
        """Accept an imported plant image into private project data.

        Args:
            None.

        Returns:
            None; import failures retain their existing form error and retry behavior.
        """
        if self.editing is None or self.map_panel.pending_image is None:
            return
        image = self.map_panel.pending_image
        scope = self.map_panel.scope
        if scope is None:
            return
        try:
            self.repository.save_plant_image(scope.plant, image)
        except Exception:
            logging.getLogger(__name__).exception("Unable to accept plant image")
            self._plot_accept_failed = True
            self.map_panel.show_error(
                self.text(
                    "The image could not be accepted. Its preview is kept for retry.",
                    "No se pudo aceptar la imagen. "
                    "Se conserva la vista previa para reintentar.",
                )
            )
            return
        self.map_panel.pending_image = None
        self.map_panel.buttons["save"].setEnabled(False)

    def accept_plot_field_edit(self) -> None:
        """Accept completed coordinate typing through the ordinary validation boundary.

        Args:
            None.

        Returns:
            None; invalid text remains pending for correction.
        """
        self.accept_plot_fields()

    def accept_plot_fields(self) -> bool:
        """Validate entered marker coordinates before accepting or closing the editor.

        Args:
            None.

        Returns:
            False for invalid fields, retaining their strings; True after accepting
            complete worker/station intent into the shared project session.
        """
        if self.editing is None or self._accepting_plot:
            return True
        self._plot_accept_failed = False
        controls = self.workers.controls
        try:
            for identity in tuple(controls.field_drafts):
                controls.select(("worker", identity))
                marker = controls.selected_settings()
                controls.field_drafts.pop(identity, None)
                self.layer.preview_worker(marker)
            if self.jobs.has_unaccepted_fields:
                self.jobs.save()
                if self.jobs.has_unaccepted_fields:
                    return False
            self.accept_plot_image()
            self.accept_plot_state()
            return not self._plot_accept_failed and self.map_panel.pending_image is None
        except ValueError:
            controls.invalid_settings()
            return False

    def accept_plot_state(self) -> None:
        """Stage accepted PLOT geometry and retain reversible analysis controls.

        Args:
            None.

        Returns:
            None; nested projection signals are suppressed and never create extra steps.
        """
        editing = self.editing
        history = self.layer.history or self.layer.shared_history
        if (
            editing is None
            or history is None
            or self._accepting_plot
            or editing.replaying
        ):
            return
        self._accepting_plot = True
        try:
            state = history.session.state
            with editing.suspend():
                if state.positions != self.repository.load_plot_positions():
                    history.save(state.positions, self.repository.save_plot_positions)
                self.layer.worker_drafts.clear()
                for item in self.layer.items.values():
                    item.pending = False
                    item.setEnabled(True)
            editing.set_editor("plot.view", state, "plot.edit")
            if self.map_panel.pending_image is None:
                self._plot_accept_failed = False
        except Exception:
            self._plot_accept_failed = True
            logging.getLogger(__name__).exception("Unable to accept PLOT changes")
            self.map_panel.show_error(
                self.text(
                    "PLOT changes could not be accepted. "
                    "Your edits are kept for retry.",
                    "No se pudieron aceptar los cambios de PLOT. "
                    "Se conservan para reintentar.",
                )
            )
        finally:
            self._accepting_plot = False

    def restore_project_plot(self) -> None:
        """Restore PLOT analysis and geometry from the shared project revision.

        Args:
            None.

        Returns:
            None; frozen result projections and exact filters are reused when available.
        """
        editing = self.editing
        if editing is None:
            return
        state = editing.editor("plot.view")
        if not isinstance(state, PlotEditState):
            state = None
        self._accepting_plot = True
        try:
            hierarchy = self.repository.load_hierarchy()
            self.layer.jobs = self.repository.load_jobs()
            self.map_panel.hierarchy = hierarchy
            self.filters.hierarchy = hierarchy
            self.filters.workplace.hierarchy = hierarchy
            self.layer.clear()
            self.map_panel.scope = None
            self.map_panel.pending_image = None
            self.filters.workplace.scope = None
            self.filters.applied = None
            if state is not None and state.filters is not None:
                try:
                    state.filters.scope.validate(hierarchy)
                except ValueError:
                    state = None
            if state is not None and state.filters is not None:
                state = replace(state, positions=self.repository.load_plot_positions())
                assert state.filters is not None
                self.filters.restore(state.filters)
                self.apply_selection(state.applied or state.filters.selection())
                history = self.layer.history
                if history is not None:
                    history.session = DocumentSession(
                        history.session.document, state, persisted=True
                    )
                    history.saved = self.repository.load_plot_positions()
                    self.layer.shared_history = history
                    self.layer.restore_history()
            elif hierarchy.plants:
                self.filters.clear_filters()
                self.filters.apply_filters()
            else:
                self.map_panel.canvas.set_layout(None)
                self.filters.workplace.refresh_values()
                self.map_panel.update_view_actions()
            self.workers.controls.history_restored()
            self.sync_mode()
        finally:
            self._accepting_plot = False

    def change_gauge_markers(self, settings: GaugeMarkerSettings) -> None:
        """Save an explicit appearance choice, then update every owned PLOT gauge.

        Args:
            settings: Shared immutable marker options selected in any gauge menu.

        Returns:
            None. Failed persistence is logged/reported and all previous appearances
            remain intact. No project, geometry, scope or solver data is written.
        """
        try:
            if self._save_gauge_markers is not None:
                self._save_gauge_markers(settings)
        except Exception:
            logging.getLogger(__name__).exception("Unable to save gauge preferences")
            QMessageBox.critical(
                self,
                self.text("Settings", "Configuración"),
                self.text(
                    "Unable to save gauge preferences.",
                    "No se pudo guardar la configuración del indicador.",
                ),
            )
            return
        for gauge in (
            self.outcome.gauge,
            self.outcome.individual_gauge,
            self.outcome.job_gauge,
        ):
            gauge.set_marker_settings(settings)

    def text(self, english: str, spanish: str) -> str:
        """Translate owned captions while leaving stored workplace names literal.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def apply_selection(self, selection: PlotFilterSelection) -> bool:
        """Publish complete saved results only after scope loading and edit checks.

        Failed reads retain the applied dataset. Pending marker edits require an
        explicit Save or Cancel in their existing controls before applying.

        Args:
            selection: Immutable exact PLOT scope/tool/risk/demographic choice to apply.

        Returns:
            True after complete results and scope are published; False retains the
            previous applied dataset.
        """
        if self.layer.pending:
            self.map_panel.show_error(
                self.text(
                    "Save or cancel PLOT marker edits before applying filters.",
                    "Guarde o cancele los cambios del mapa antes de aplicar filtros.",
                )
            )
            return False
        results = saved_plot_results(
            self.repository, selection, current_year=self.current_year
        )
        if not self.map_panel.set_scope(selection.scope):
            return False
        self.layer.set_results(results)
        self._filter_results[selection] = results
        return True

    def record_filter_history(self) -> None:
        """Record accepted tool/scope/Clear/Apply in the map's single timeline.

        Args:
            None.

        Returns:
            None.
        """
        history = self.layer.shared_history
        if history is not None and self.filters.workplace.scope is not None:
            results = self.layer.results
            history.edit_filters(
                self.filters.snapshot(), results.selection if results else None
            )
            self.history_actions.refresh()

    def replay_history(self, redo: bool) -> bool:
        """Restore controls/results/geometry without writes or duplicate commands.

        Results reuse immutable saved-data projections from this modal session. Scope
        image loading retains the existing failure/discard policy. Rejected scope
        changes roll back the history cursor, preserving the redo branch.

        Args:
            redo: True replays the next operation; False restores the previous
                operation.

        Returns:
            True after accepted replay projection; False at a boundary or rejected
            scope, with the history cursor restored.
        """
        history = self.layer.shared_history
        if history is None:
            return False
        before = history.session.state
        if not (history.session.redo() if redo else history.session.undo()):
            return False
        state = history.session.state
        if state.filters != before.filters or state.applied != before.applied:
            assert state.filters is not None
            guard = self.map_panel.canvas.replace_guard
            self.map_panel.canvas.replace_guard = lambda: True
            try:
                accepted = self.map_panel.set_scope(state.filters.scope)
            finally:
                self.map_panel.canvas.replace_guard = guard
            if not accepted:
                history.session.undo() if redo else history.session.redo()
                self.history_actions.refresh()
                return False
            self.layer.clear()
            if state.applied is not None:
                results = self._filter_results[state.applied]
                self.layer.set_results(replace(results, positions=history.saved))
            self.filters.restore(state.filters)
            self.filters.applied = state.applied
        if self.layer.results is not None:
            self.layer.history = history
            self.layer.restore_history()
        self.history_actions.refresh()
        return True

    def apply_risk_mode(self) -> None:
        """Keep source risk buttons' immediate Apply and restore mode on rejection.

        Args:
            None.

        Returns:
            None.
        """
        results = self.layer.results
        if (
            results is not None
            and results.selection.risk_view is self.filters.risk_view
        ):
            return
        self.filters.apply_filters()
        if self.layer.results is results and results is not None:
            self.filters.select_risk(results.selection.risk_view)

    def sync_mode(self) -> None:
        """Project applied mode into tabs without triggering another Apply.

        Args:
            None.

        Returns:
            None.
        """
        self.map_panel.buttons["export"].setEnabled(self.csv_writer is not None)
        results = self.layer.results
        job_view = (
            results is not None and results.selection.risk_view is PlotRiskView.JOB
        )
        self.overviews.setCurrentIndex(1 if job_view else 0)
        self.tabs.setTabText(
            1,
            self.text("Job Placement", "Ubicación de puestos")
            if job_view
            else self.text("Worker Overview", "Resumen de trabajadores"),
        )
        self.tabs.setTabIcon(1, self.job_icon if job_view else self.worker_icon)
        self.tabs.setTabToolTip(
            1,
            self.text(
                "Select and control a job placement on the plant layout.",
                "Seleccionar y controlar un puesto en el plano de la planta.",
            )
            if job_view
            else self.text(
                "Select and control an individual worker marker on the plant layout.",
                "Seleccionar y controlar un trabajador en el plano de la planta.",
            ),
        )

    def reveal_selection(self, _key: tuple[object, ...]) -> None:
        """Reveal the original detail tab after a real map marker selection.

        Args:
            _key: Marker-selection signal payload; the containing detail tab is revealed
                for any valid selection.

        Returns:
            None.
        """
        self.tabs.setCurrentIndex(1)

    def choose_csv(self) -> str:
        """Use the original dated CSV/All Files chooser and native overwrite consent.

        Args:
            None.

        Returns:
            Selected CSV destination, or an empty string after cancellation.
        """
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.text("Save Data as CSV", "Guardar datos como CSV"),
            f"WorkerStationShiftData_{datetime.now():%Y-%m-%d}.csv",
            self.text(
                "CSV Files (*.csv);;All Files (*)", "Archivos CSV (*.csv);;Todos (*)"
            ),
        )
        return path

    def export_csv(self) -> None:
        """Export applied saved workers while retaining pending edits.

        Args:
            None.

        Returns:
            None.
        """
        results = self.layer.results
        if results is None or not results.workers:
            self.map_panel.message(
                self.text("No Data", "Sin datos"),
                self.text("There is no data to export.", "No hay datos para exportar."),
                QMessageBox.Icon.Warning,
            )
            return
        if self.csv_writer is None:
            return
        path = self.choose_csv()
        if not path:
            return
        try:
            self.csv_writer(path, plot_csv_table(results, self.system))
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Unable to export PLOT CSV")
            self.map_panel.show_error(
                self.text(
                    "Data could not be exported. Choose a writable location.",
                    "No se pudieron exportar los datos. "
                    "Elija una ubicación con escritura.",
                )
            )
            return
        self.map_panel.message(
            self.text("Success", "Éxito"),
            self.text("Data successfully exported to:\n", "Datos exportados a:\n")
            + path,
            QMessageBox.Icon.Information,
        )

    def confirm_close(self) -> bool:
        """Require explicit discard consent only when image/marker edits exist.

        Args:
            None.

        Returns:
            True with no unsaved map intent or explicit discard consent; False retains
            the PLOT window.
        """
        if self.editing is not None:
            return self.accept_plot_fields()
        if self.map_panel.pending_image is None and not self.layer.pending:
            return True
        return (
            self.map_panel.message(
                self.text("Unsaved PLOT changes", "Cambios de PLOT sin guardar"),
                self.text(
                    "Discard unsaved PLOT changes and close this window?",
                    "¿Descartar los cambios de PLOT sin guardar y cerrar esta ventana?",
                ),
                QMessageBox.Icon.Question,
                question=True,
            )
            == QMessageBox.StandardButton.Yes
        )

    def handoff(self, row: SummaryExportRow) -> bool:
        """Close only after own consent and accepted exact saved editor selection.

        Cancellation, editor rejection and exceptions retain this window and its pending
        image. The marker layer reports exceptions through its error UI.

        Args:
            row: Saved typed result row carrying exact source/assignment ownership and
                optional evidence.

        Returns:
            True after both local discard consent and exact editor acceptance close
            PLOT; False retains this window.
        """
        if self.load_assessment is None or not self.confirm_close():
            return False
        if not self.load_assessment(row):
            return False
        self._closure_accepted = True
        self.close()
        return True

    def reject(self) -> None:
        """Apply the same edit consent to Escape as to the window close button.

        Args:
            None.

        Returns:
            None.
        """
        if not self._closure_accepted and not self.confirm_close():
            return
        self._closure_accepted = True
        self.workers.stop_locate()
        self.jobs.stop_locate()
        self.outcome.close()
        super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Stop owned animation/locate timers; never implicitly save project data.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        if event is None:
            return
        if not self._closure_accepted and not self.confirm_close():
            event.ignore()
            return
        self._closure_accepted = True
        super().closeEvent(event)
