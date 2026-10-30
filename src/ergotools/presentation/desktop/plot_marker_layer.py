"""Original PLOT marker composition with injected save/error/selection operations.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from html import escape
from typing import Literal

from PyQt5.QtCore import QObject, QPoint, QPointF, pyqtSignal
from PyQt5.QtWidgets import QMenu

from ergotools.application.assessment_export import SummaryExportRow
from ergotools.application.plot_history import PlotPositionHistory
from ergotools.application.plot_results import PlotResults, PlotWorkerResult
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog
from ergotools.domain.language import Language
from ergotools.domain.plot_filters import PlotFilterSelection, PlotRiskView
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas
from ergotools.presentation.desktop.plot_marker_item import (
    MarkerAppearance,
    PlotMarkerItem,
)
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color

# Both tags identify a worker assignment; the tag selects its visual representation.
# A Job glyph is an occurrence at that assignment, never a Job placement identity.
type MarkerKey = tuple[Literal["worker", "job"], int]


def plot_damage_color(kind: AssessmentKind, damage: float | None) -> str:
    """Use source continuous palettes; absent/review results remain neutral.

    Args:
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.
        damage: Observed dimensionless cumulative damage, or None for unavailable
            evidence.

    Returns:
        Original tool-specific continuous palette color, or neutral gray when damage is
        absent.
    """
    if damage is None:
        return "#D9E1E6"
    return (
        lifft_damage_color(damage)
        if kind is AssessmentKind.LIFFT
        else duet_damage_color(damage)
        if kind is AssessmentKind.DUET
        else tst_damage_color(damage)
    )


class PlotMarkerLayer(QObject):
    """Own graphics items and edit intent independently of SQL and main-window state."""

    changed = pyqtSignal()
    selection_changed = pyqtSignal(tuple)
    history_restored = pyqtSignal()

    def __init__(
        self,
        canvas: PlotLayoutCanvas,
        jobs: JobCatalog,
        save_positions: Callable[[PlotPositions], None],
        show_error: Callable[[str], None],
        *,
        language: Language = Language.ENGLISH,
        current_year: int,
        on_select: Callable[[MarkerKey], None] | None = None,
        load_assessment: Callable[[SummaryExportRow], bool] | None = None,
    ) -> None:
        """Inject saved ownership and operations; creating a layer never writes.

        Args:
            canvas: Owned Qt canvas whose figure or scene is composed here; this adapter
                does not acquire repository ownership.
            jobs: Immutable job/placement/assignment catalog used to resolve marker
                ownership.
            save_positions: Explicit atomic persistence callback for validated immutable
                map positions.
            show_error: Callback displaying a localized map-operation failure without
                discarding edits.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            current_year: Explicit calendar year for demographic ages; keeps loaded
                projections deterministic.
            on_select: Optional notification receiving the selected marker's typed owner
                key.
            load_assessment: Optional host callback accepting the exact saved
                assessment; True completes handoff.

        Returns:
            None.
        """
        super().__init__(canvas)
        self.canvas = canvas
        self.jobs = jobs
        self.save_positions = save_positions
        self.show_error = show_error
        self.language = language
        self.current_year = current_year
        self.on_select = on_select
        self.load_assessment = load_assessment
        self.items: dict[MarkerKey, PlotMarkerItem] = {}
        self.results: PlotResults | None = None
        self.worker_drafts: dict[int, WorkerAssignmentMarker] = {}
        # Integrated Cancel movement restores only this view's latest selected move.
        self.movement_origins: dict[int, WorkerAssignmentMarker] = {}
        self.history: PlotPositionHistory | None = None
        self.shared_history: PlotPositionHistory | None = None
        self.project_editing = False
        self.replay_view: Callable[[bool], bool] | None = None
        self._histories: dict[PlotFilterSelection, PlotPositionHistory] = {}
        self._next_document_id = 1
        canvas.replace_guard = lambda: not self.pending
        canvas.layout_replaced.connect(self.clear)
        canvas.fitted.connect(self.set_view_scale)

    def text(self, english: str, spanish: str) -> str:
        """Translate owned captions while saved identities remain literal.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    @property
    def pending(self) -> bool:
        """Report unsaved marker intent without querying saved sources.

        Args:
            None.

        Returns:
            True when accepted history geometry or local worker/item previews differ
            from the saved baseline.
        """
        return (
            (self.history is not None and self.history.is_dirty)
            or bool(self.worker_drafts)
            or any(item.pending for item in self.items.values())
        )

    def clear(self) -> None:
        """Release items before scene clearing, avoiding deleted Qt wrappers.

        Args:
            None.

        Returns:
            None.
        """
        scene = self.canvas.scene()
        assert scene is not None
        for item in self.items.values():
            scene.removeItem(item)
            item.deleteLater()
        self.items.clear()
        self.worker_drafts.clear()
        self.movement_origins.clear()
        self.results = None
        self.history = None
        self.changed.emit()

    def set_results(self, results: PlotResults) -> None:
        """Render a complete same-plant dataset; reject replacing pending edits.

        Args:
            results: Complete saved PLOT projection matching the displayed plant and
                project.

        Returns:
            None.

        Raises:
            ValueError: Save or cancel PLOT marker edits before replacing results. PLOT
                results do not match the displayed plant. PLOT marker ownership belongs
                to another project.
        """
        if self.pending:
            raise ValueError(
                "Save or cancel PLOT marker edits before replacing results."
            )
        layout = self.canvas.loaded_layout
        if layout is None or layout.scope.plant != results.selection.scope.plant:
            raise ValueError("PLOT results do not match the displayed plant.")
        if results.positions.project_id != self.jobs.project_id:
            raise ValueError("PLOT marker ownership belongs to another project.")
        self.clear()
        self.results = results
        history = self.shared_history or self._histories.get(results.selection)
        # Another map document may have saved the same shared assignment/anchor.
        # Do not replay obsolete full snapshots over a different committed source.
        if history is None or (
            self.shared_history is None and history.saved != results.positions
        ):
            history = PlotPositionHistory(
                DocumentKey(self.jobs.project_id, f"plot-map-{self._next_document_id}"),
                results.positions,
            )
            self._next_document_id += 1
            self._histories[results.selection] = history
        if self.shared_history is not None:
            history.reload_positions(results.positions)
        self.history = history
        for worker_row in results.workers:
            identity = worker_row.assessment.assignment_id
            marker = results.positions.marker(identity)
            point = results.positions.worker_point(identity, self.jobs)
            # Every view projects the same assignment geometry; absent is never origin.
            if marker is None or not marker.visible or point is None:
                continue
            self._add_worker(worker_row, marker, point)
        self.changed.emit()

    def _add_worker(
        self,
        worker_row: PlotWorkerResult,
        marker: WorkerAssignmentMarker,
        point: PlotPoint,
    ) -> PlotMarkerItem:
        """Reuse source worker paint/tooltip composition for newly shown markers.

        Args:
            worker_row: Saved worker result containing exact assignment ownership and
                optional risk evidence.
            marker: Immutable worker-assignment visual settings, including canonical
                image coordinates.
            point: Marker anchor in original image pixels, independent of zoom and
                device-pixel ratio.

        Returns:
            New scene-owned worker marker carrying the exact saved assignment and risk
            appearance.
        """
        assert self.results is not None
        identity = marker.assignment_id
        details = worker_row.worker.details
        shape: Literal["circle", "triangle", "hexagon", "job"] = (
            "circle"
            if details is not None and details.sex == "Female"
            else "triangle"
            if details is not None and details.sex == "Male"
            else "hexagon"
        )
        evidence = worker_row.job_risk
        job_only = self.results.selection.risk_view is PlotRiskView.JOB
        appearance = MarkerAppearance(
            "job" if job_only else shape,
            plot_damage_color(
                worker_row.assessment.kind,
                evidence.measurement.cumulative_damage if evidence else None,
            )
            if job_only
            else plot_damage_color(
                worker_row.assessment.kind, worker_row.assessment.total_damage
            ),
            plot_damage_color(
                worker_row.assessment.kind,
                evidence.measurement.cumulative_damage if evidence else None,
            ),
            self.results.selection.risk_view is PlotRiskView.COMPARISON,
            evidence.measurement.probability_percent if evidence else None,
            worker_row.job.job_id.removeprefix("Job-") if worker_row.job else "—",
        )
        item = self.add_item(
            ("job" if job_only else "worker", identity),
            point,
            appearance,
            size=marker.size,
            scale=marker.scale,
            locked=marker.locked,
            enabled=marker.enabled,
        )
        place = worker_row.assessment.owner.workplace
        age = (
            str(self.current_year - int(details.birth_date[:4]))
            if details is not None and details.birth_date
            else "N/A"
        )
        risk = (
            f"{worker_row.assessment.probability * 100:.1f}%"
            if worker_row.assessment.probability is not None
            else self.text("Not available", "No disponible")
        )
        job_risk = (
            f"{evidence.measurement.probability_percent:.1f}%"
            if evidence is not None
            and evidence.measurement.probability_percent is not None
            else self.text("Not available", "No disponible")
        )
        job_name = (
            worker_row.job.job_id
            if worker_row.job
            else self.text("Not classified", "Sin clasificar")
        )
        damage = (
            str(worker_row.assessment.total_damage)
            if worker_row.assessment.total_damage is not None
            else self.text("Not available", "No disponible")
        )
        if job_only:
            job_id = worker_row.job.job_id if worker_row.job else "—"
            name = worker_row.job.name.strip() if worker_row.job else ""
            job_caption = f"{job_id} — {name}" if name and name != job_id else job_id
            self.tooltip(
                item,
                [
                    self.text(
                        f"Job: {job_caption}",
                        f"Trabajo: {job_caption}",
                    ),
                    self.text(
                        f"Job risk: {job_risk}", f"Riesgo del trabajo: {job_risk}"
                    ),
                    self.text(
                        f"Worker: {worker_row.worker.worker_id}",
                        f"Trabajador: {worker_row.worker.worker_id}",
                    ),
                    self.text(
                        f"Section: {place.section_name}",
                        f"Sección: {place.section_name}",
                    ),
                    self.text(f"Line: {place.line_name}", f"Línea: {place.line_name}"),
                    self.text(
                        f"Station: {place.station_id}", f"Estación: {place.station_id}"
                    ),
                    self.text(f"Shift: {place.shift_id}", f"Turno: {place.shift_id}"),
                ],
            )
        else:
            self.tooltip(
                item,
                [
                    f"ID: {worker_row.worker.worker_id}",
                    self.text(
                        f"Name: {worker_row.worker.first_name or ''} "
                        f"{worker_row.worker.last_name or ''}",
                        f"Nombre: {worker_row.worker.first_name or ''} "
                        f"{worker_row.worker.last_name or ''}",
                    ),
                    self.text(f"Age: {age}", f"Edad: {age}"),
                    self.text(
                        f"Section: {place.section_name}",
                        f"Sección: {place.section_name}",
                    ),
                    self.text(f"Line: {place.line_name}", f"Línea: {place.line_name}"),
                    self.text(
                        f"Station: {place.station_id}",
                        f"Estación: {place.station_id}",
                    ),
                    self.text(f"Shift: {place.shift_id}", f"Turno: {place.shift_id}"),
                    self.text(
                        f"Cumulative Damage: {damage}",
                        f"Daño acumulado: {damage}",
                    ),
                    self.text(f"Individual Risk: {risk}", f"Riesgo individual: {risk}"),
                    self.text(f"Job: {job_name}", f"Puesto: {job_name}"),
                    self.text(
                        f"Job Risk: {job_risk}", f"Riesgo del puesto: {job_risk}"
                    ),
                ],
            )
        return item

    def tooltip(self, item: PlotMarkerItem, lines: list[str]) -> None:
        """Escape literal saved labels in a native rich-text tooltip.

        Args:
            item: Borrowed live Qt item carrying typed owner data; the method does not
                take ownership.
            lines: Literal tooltip lines escaped before rich-text composition.

        Returns:
            None.
        """
        item.setToolTip("<qt>" + "<br>".join(escape(line) for line in lines) + "</qt>")

    def add_item(
        self,
        key: MarkerKey,
        point: PlotPoint,
        appearance: MarkerAppearance,
        *,
        size: float,
        scale: float = 1,
        offset: QPointF | None = None,
        anchored: bool = True,
        locked: bool = False,
        enabled: bool = True,
    ) -> PlotMarkerItem:
        """Create one typed item, preserving the background and scene rect.

        Args:
            key: Typed view/assignment marker identity; captions and scene positions are
                not storage keys.
            point: Marker anchor in original image pixels, independent of zoom and
                device-pixel ratio.
            appearance: Immutable source shape, risk colors and label used to paint this
                marker.
            size: Base marker side in original source pixels before symbol/view-scale
                projection.
            scale: Positive finite dimensionless marker/view scale, as specified by the
                owning method.
            offset: Display-only offset from the canonical original-image anchor; None
                means zero.
            anchored: Whether this marker has an explicit/inherited source anchor rather
                than an unplaced preview.
            locked: True prevents position changes while retaining marker selection.
            enabled: Whether the associated controls should accept user interaction.

        Returns:
            New scene-owned marker registered under the exact supplied owner key.
        """
        item = PlotMarkerItem(
            point,
            appearance,
            self.select,
            self.moved,
            size=size,
            scale=scale,
            view_scale=self.canvas.fitted_scale,
            offset=offset,
            anchored=anchored,
            locked=locked,
            enabled=enabled,
            context=self.show_worker_menu if key[0] == "worker" else None,
        )
        scene = self.canvas.scene()
        assert scene is not None
        item.setOpacity(self.canvas.marker_opacity)
        scene.addItem(item)
        self.items[key] = item
        return item

    def set_view_scale(self, scale: float) -> None:
        """Normalize symbols to fit; user zoom scales them with the image.

        Args:
            scale: Positive fitted baseline emitted by the canvas, excluding user zoom.

        Returns:
            None.
        """
        for item in self.items.values():
            item.set_view_scale(scale)

    def select(self, selected: PlotMarkerItem) -> None:
        """Select by owner identity without changing main assessments.

        Args:
            selected: Live marker selected by exact owner identity.

        Returns:
            None.
        """
        for key, item in self.items.items():
            item.setSelected(item is selected)
            if item is selected:
                self.selection_changed.emit(key)
                if self.on_select is not None:
                    self.on_select(key)

    def moved(self, moved: PlotMarkerItem) -> None:
        """Record a released gesture in the same assignment history for every view.

        Args:
            moved: Assignment glyph whose completed gesture updates shared map geometry.

        Returns:
            None.
        """
        key = next(key for key, item in self.items.items() if item is moved)
        assert self.history is not None
        previous = self.worker_settings(key[1])
        if self.project_editing and (
            moved.anchor_point() != previous.point
            or moved.marker_scale != previous.scale
        ):
            self.movement_origins[key[1]] = previous
        marker = replace(
            previous,
            point=moved.anchor_point(),
            scale=moved.marker_scale,
            source=WorkerPositionSource.MANUAL,
        )
        self.preview_worker(marker, label_key="plot.history.move")

    def save(self, key: MarkerKey) -> bool:
        """Commit selected intent; Undo after Save remains a purely local draft.

        Args:
            key: Typed view/assignment marker identity; captions and scene positions are
                not storage keys.

        Returns:
            True after selected intent is persisted; False on a handled persistence
            failure with drafts retained.

        Raises:
            ValueError: There are no PLOT results to save.
        """
        if self.results is None or self.history is None:
            raise ValueError("There are no PLOT results to save.")
        return self.save_workers((self.worker_settings(key[1]),))

    def cancel(self, key: MarkerKey) -> None:
        """Restore selected saved intent as an undoable edit, with no database I/O.

        Args:
            key: Typed view/assignment marker identity; captions and scene positions are
                not storage keys.

        Returns:
            None.
        """
        assert self.history is not None
        positions = self.history.state
        saved = self.history.saved
        marker = saved.marker(key[1])
        positions = replace(
            positions,
            workers=tuple(
                marker if p.assignment_id == key[1] and marker is not None else p
                for p in positions.workers
                if p.assignment_id != key[1] or marker is not None
            ),
        )
        if marker is not None and positions.marker(key[1]) is None:
            positions = replace(positions, workers=(*positions.workers, marker))
        self.history.edit(positions, "plot.history.cancel")
        self.worker_drafts.pop(key[1], None)
        self.restore_history()

    def undo(self) -> bool:
        """Restore one source operation without changing saved project records.

        Args:
            None.

        Returns:
            True when the source history moves back one operation; False at its
            boundary.
        """
        if self.replay_view is not None:
            return self.replay_view(False)
        if self.history is None or not self.history.session.undo():
            return False
        self.restore_history()
        return True

    def redo(self) -> bool:
        """Reapply one source operation; saving remains explicit.

        Args:
            None.

        Returns:
            True when the source history moves forward one operation; False at its
            boundary.
        """
        if self.replay_view is not None:
            return self.replay_view(True)
        if self.history is None or not self.history.session.redo():
            return False
        self.restore_history()
        return True

    def restore_history(self) -> None:
        """Project immutable geometry in place, retaining selected Qt item ownership.

        Args:
            None.

        Returns:
            None.
        """
        assert self.history is not None and self.results is not None
        self.worker_drafts.clear()
        self.history_restored.emit()
        for row in self.results.workers:
            identity = row.assessment.assignment_id
            marker = self.history.state.ensure_marker(identity, self.jobs).marker(
                identity
            )
            saved_marker = self.history.saved.ensure_marker(identity, self.jobs).marker(
                identity
            )
            assert marker is not None
            if marker != saved_marker:
                self.worker_drafts[identity] = marker
            self._project_worker(marker, pending=marker != saved_marker)
        self.changed.emit()

    def worker_settings(self, identity: int) -> WorkerAssignmentMarker:
        """Return saved/draft settings without creating a stored marker or origin.

        Args:
            identity: Saved assignment or placement integer identity, resolved within
                the current result set.

        Returns:
            Current saved/draft settings for the exact eligible assignment; no marker or
            origin is persisted by reading.

        Raises:
            ValueError: Worker is not in the current PLOT results.
        """
        results = self.results
        if results is None or not any(
            row.assessment.assignment_id == identity for row in results.workers
        ):
            raise ValueError("Worker is not in the current PLOT results.")
        draft = self.worker_drafts.get(identity)
        assert self.history is not None
        marker = draft or self.history.state.ensure_marker(identity, self.jobs).marker(
            identity
        )
        assert marker is not None
        return marker

    def preview_worker(
        self,
        marker: WorkerAssignmentMarker,
        *,
        label_key: str = "plot.history.settings",
    ) -> None:
        """Record validated flags/geometry; no persistence occurs during preview.

        Args:
            marker: Immutable worker-assignment visual settings, including canonical
                image coordinates.
            label_key: Stable localized command label recorded in the PLOT history
                timeline.

        Returns:
            None.

        Raises:
            ValueError: The assignment is outside the current result set.
        """
        self.worker_settings(marker.assignment_id)
        assert self.history is not None
        positions = self.history.state.ensure_marker(marker.assignment_id, self.jobs)
        positions = replace(
            positions,
            workers=tuple(
                marker if item.assignment_id == marker.assignment_id else item
                for item in positions.workers
            ),
        )
        self.history.edit(positions, label_key)
        self.worker_drafts[marker.assignment_id] = marker
        self._project_worker(marker, pending=True)
        self.changed.emit()

    def _project_worker(self, marker: WorkerAssignmentMarker, *, pending: bool) -> None:
        """Render a source value without recording a second history operation.

        Args:
            marker: Immutable worker-assignment visual settings, including canonical
                image coordinates.
            pending: Whether projected marker values differ from accepted saved intent.

        Returns:
            None.
        """
        assert self.results is not None
        key: MarkerKey = (
            "job" if self.results.selection.risk_view is PlotRiskView.JOB else "worker",
            marker.assignment_id,
        )
        item = self.items.get(key)
        if item is None and marker.visible and marker.point is not None:
            row = next(
                row
                for row in self.results.workers
                if row.assessment.assignment_id == marker.assignment_id
            )
            item = self._add_worker(row, marker, marker.point)
        if item is not None:
            item.prepareGeometryChange()
            item.marker_scale = marker.scale
            if marker.point is not None:
                item.setPos(marker.point.x, marker.point.y)
            item.locked = marker.locked
            item.setFlag(item.GraphicsItemFlag.ItemIsMovable, not marker.locked)
            item.setVisible(marker.visible and marker.point is not None)
            item.setEnabled(marker.enabled)
            item.pending = pending
            item.update()

    def save_workers(self, markers: tuple[WorkerAssignmentMarker, ...]) -> bool:
        """Commit a validated worker batch once, retaining all drafts on failure.

        Settings apply only to current result assignments. Save All is atomic and does
        not process Qt events inside the transaction. Every point must be
        explicit/inherited; unplaced workers cannot silently manufacture origin.

        Args:
            markers: Validated batch of worker settings committed in one atomic save.

        Returns:
            True after the complete batch is committed; False after a handled write
            failure with intent retained.

        Raises:
            ValueError: There are no worker settings to save. Duplicate worker settings
                in Save.
        """
        if self.results is None or not markers:
            raise ValueError("There are no worker settings to save.")
        if len({marker.assignment_id for marker in markers}) != len(markers):
            raise ValueError("Duplicate worker settings in Save.")
        assert self.history is not None
        positions = self.results.positions
        draft = self.history.state
        for marker in markers:
            self.worker_settings(marker.assignment_id)
            positions = positions.with_saved_marker(marker, self.jobs)
            draft = draft.with_saved_marker(marker, self.jobs)
        self.history.edit(
            draft, "plot.history.batch" if len(markers) > 1 else "plot.history.settings"
        )
        # Failed persistence keeps the entire validated batch available to undo/retry.
        for marker in markers:
            self.worker_drafts[marker.assignment_id] = marker
            self._project_worker(marker, pending=True)
        try:
            self.history.save(positions, self.save_positions)
        except Exception:
            logging.getLogger(__name__).exception("Unable to save PLOT worker settings")
            self.show_error(
                self.text(
                    "Worker settings could not be saved. Your edits have been kept.",
                    "No se pudieron guardar los ajustes. Se conservaron sus cambios.",
                )
            )
            return False
        self.results = replace(self.results, positions=positions)
        for marker in markers:
            # Publish committed settings without clearing other workers' intent.
            committed = positions.marker(marker.assignment_id)
            assert committed is not None
            self._project_worker(committed, pending=False)
            self.worker_drafts.pop(marker.assignment_id, None)
            key: MarkerKey = (
                "job"
                if self.results.selection.risk_view is PlotRiskView.JOB
                else "worker",
                marker.assignment_id,
            )
            item = self.items.get(key)
            if item is not None:
                item.mark_saved()
        for key, item in self.items.items():
            item.setEnabled(self.worker_settings(key[1]).enabled)
        self.changed.emit()
        return True

    def worker_menu(self, identity: int) -> QMenu:
        """Build the original worker actions; opening a menu performs no writes.

        Args:
            identity: Saved assignment or placement integer identity, resolved within
                the current result set.

        Returns:
            Owned styled menu over the captured worker identity; caller executes and
            releases it.
        """
        self.worker_settings(identity)
        menu = QMenu(self.canvas)
        menu.setStyleSheet(PLOT_STYLE)
        lock = menu.addAction(self.text("Lock", "Bloquear"))
        save = menu.addAction(self.text("Save", "Guardar"))
        load = menu.addAction(
            self.text("Load into Tool Window", "Cargar en la ventana de evaluación")
        )
        assert lock is not None and save is not None and load is not None
        save.setVisible(not self.project_editing)
        lock.triggered.connect(lambda: self.lock_worker(identity))

        def save_selected() -> None:
            """Save only this menu's captured worker assignment.

            Save only this menu's captured worker assignment and discard the boolean
            result at the Qt signal boundary.

            Args:
                None.

            Returns:
                None.
            """
            self.save(("worker", identity))

        def load_selected() -> None:
            """Request this menu's exact saved assessment handoff.

            Request this menu's exact saved assessment handoff; the layer/host retains
            its acceptance and dirty policy.

            Args:
                None.

            Returns:
                None.
            """
            self.load_worker(identity)

        save.triggered.connect(save_selected)
        load.setEnabled(self.load_assessment is not None)
        load.triggered.connect(load_selected)
        return menu

    def show_worker_menu(self, item: PlotMarkerItem, position: QPoint) -> None:
        """Run the source right-click menu and release its owned Qt instance.

        Args:
            item: Borrowed live Qt item carrying typed owner data; the method does not
                take ownership.
            position: Global screen point in Qt logical pixels for the context menu.

        Returns:
            None.
        """
        identity = next(key[1] for key, value in self.items.items() if value is item)
        menu = self.worker_menu(identity)
        try:
            menu.exec(position)
        finally:
            menu.close()
            menu.deleteLater()

    def lock_worker(self, identity: int) -> None:
        """Preview a lock; explicit Save persists it with this assignment's settings.

        Args:
            identity: Saved assignment or placement integer identity, resolved within
                the current result set.

        Returns:
            None.
        """
        self.preview_worker(replace(self.worker_settings(identity), locked=True))

    def load_worker(self, identity: int) -> bool:
        """Request exact saved assessment handoff without saving marker edits.

        Args:
            identity: Saved assignment or placement integer identity, resolved within
                the current result set.

        Returns:
            True only when the injected host accepts the exact saved assessment; False
            for rejected/unavailable/failed handoff.
        """
        self.worker_settings(identity)
        if self.load_assessment is None:
            return False
        if self.pending:
            self.show_error(
                self.text(
                    "Save or cancel PLOT marker edits before loading an assessment.",
                    "Guarde o cancele los cambios del mapa "
                    "antes de cargar una evaluación.",
                )
            )
            return False
        assert self.results is not None
        row = next(
            row
            for row in self.results.workers
            if row.assessment.assignment_id == identity
        )
        try:
            return self.load_assessment(row.assessment)
        except Exception:
            logging.getLogger(__name__).exception("Unable to load PLOT assessment")
            self.show_error(
                self.text(
                    "Assessment could not be loaded. The PLOT window remains open.",
                    "No se pudo cargar la evaluación. La ventana PLOT sigue abierta.",
                )
            )
            return False
