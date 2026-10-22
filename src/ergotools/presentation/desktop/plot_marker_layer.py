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
    StationPosition,
    StationPositionSource,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.work_catalog import StationKey
from ergotools.presentation.desktop.plot_layout_canvas import PlotLayoutCanvas
from ergotools.presentation.desktop.plot_marker_item import (
    MarkerAppearance,
    PlotMarkerItem,
)
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color

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
        if results.selection.risk_view is PlotRiskView.JOB:
            counts: dict[StationKey, int] = {}
            for row in results.jobs:
                place = row.placement.workplace
                station = StationKey(
                    place.plant_name,
                    place.section_name,
                    place.line_name,
                    place.station_id,
                )
                anchor = results.positions.station_position(station)
                index = counts.get(station, 0)
                counts[station] = index + 1
                evidence = row.risk
                unavailable = self.text("Not available", "No disponible")
                risk = (
                    f"{evidence.measurement.probability_percent:.1f}%"
                    if evidence is not None
                    and evidence.measurement.probability_percent is not None
                    else unavailable
                )
                item = self.add_item(
                    ("job", row.placement.placement_id),
                    anchor.point if anchor is not None else PlotPoint(18, 18),
                    MarkerAppearance(
                        "job",
                        plot_damage_color(
                            results.selection.tool,
                            evidence.measurement.cumulative_damage
                            if evidence
                            else None,
                        ),
                        label=row.job.job_id.removeprefix("Job-"),
                    ),
                    size=38,
                    offset=QPointF((index % 3) * 9, (index // 3) * 9),
                    anchored=anchor is not None,
                )
                self.tooltip(
                    item,
                    [
                        self.text(
                            f"Job: {row.job.job_id} - {row.job.name}",
                            f"Puesto: {row.job.job_id} - {row.job.name}",
                        ),
                        self.text(
                            f"Station: {station.station_id}",
                            f"Estación: {station.station_id}",
                        ),
                        self.text(
                            f"Shift: {place.shift_id}", f"Turno: {place.shift_id}"
                        ),
                        self.text(
                            f"Assigned workers: {row.assigned_worker_count}",
                            f"Trabajadores asignados: {row.assigned_worker_count}",
                        ),
                        self.text(f"Job Risk: {risk}", f"Riesgo del puesto: {risk}"),
                        self.text(
                            "Drag to set or move the Station position.",
                            "Arrastre para establecer o mover "
                            "la posición de la estación.",
                        ),
                    ],
                )
        else:
            for worker_row in results.workers:
                identity = worker_row.assessment.assignment_id
                marker = results.positions.marker(identity)
                point = results.positions.worker_point(identity, self.jobs)
                # Creation/visibility belongs to the original worker position controls.
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
        item = self.add_item(
            ("worker", identity),
            point,
            MarkerAppearance(
                shape,
                plot_damage_color(
                    worker_row.assessment.kind,
                    worker_row.assessment.total_damage,
                ),
                plot_damage_color(
                    worker_row.assessment.kind,
                    evidence.measurement.cumulative_damage if evidence else None,
                ),
                self.results.selection.risk_view is PlotRiskView.COMPARISON,
                evidence.measurement.probability_percent if evidence else None,
            ),
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
                self.text(f"Job Risk: {job_risk}", f"Riesgo del puesto: {job_risk}"),
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
            key: Typed worker/station marker identity; captions and scene positions are
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
            view_scale=self.canvas.transform().m11(),
            offset=offset,
            anchored=anchored,
            locked=locked,
            enabled=enabled,
            context=self.show_worker_menu if key[0] == "worker" else None,
        )
        scene = self.canvas.scene()
        assert scene is not None
        scene.addItem(item)
        self.items[key] = item
        return item

    def set_view_scale(self, scale: float) -> None:
        """Resize symbols after fit without moving their original-image coordinates.

        Args:
            scale: Positive finite dimensionless marker/view scale, as specified by the
                owning method.

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
        """Record one released gesture; job previews lock peers as in the source.

        Args:
            moved: Live marker whose completed gesture is being recorded once.

        Returns:
            None.
        """
        key = next(key for key, item in self.items.items() if item is moved)
        assert self.history is not None
        if key[0] == "worker":
            marker = replace(
                self.worker_settings(key[1]),
                point=moved.anchor_point(),
                scale=moved.marker_scale,
                source=WorkerPositionSource.MANUAL,
            )
            self.preview_worker(marker, label_key="plot.history.move")
        else:
            self.history.edit(
                self.history.state.with_station(
                    StationPosition(
                        self.job_station(key[1]),
                        moved.anchor_point(),
                        StationPositionSource.JOB,
                    )
                ),
                "plot.history.move",
            )
            moved.pending = True
            for item in self.items.values():
                if item is not moved:
                    item.setEnabled(False)
            self.changed.emit()

    def job_station(self, identity: int) -> StationKey:
        """Resolve the exact station shared by a selected job placement.

        Args:
            identity: Saved assignment or placement integer identity, resolved within
                the current result set.

        Returns:
            Exact complete station ancestry shared by the specified job placement.
        """
        assert self.results is not None
        row = next(
            row for row in self.results.jobs if row.placement.placement_id == identity
        )
        place = row.placement.workplace
        return StationKey(
            place.plant_name, place.section_name, place.line_name, place.station_id
        )

    def save(self, key: MarkerKey) -> bool:
        """Commit selected intent; Undo after Save remains a purely local draft.

        Args:
            key: Typed worker/station marker identity; captions and scene positions are
                not storage keys.

        Returns:
            True after selected intent is persisted; False on a handled persistence
            failure with drafts retained.

        Raises:
            ValueError: There are no PLOT results to save.
        """
        if self.results is None or self.history is None:
            raise ValueError("There are no PLOT results to save.")
        if key[0] == "worker":
            return self.save_workers((self.worker_settings(key[1]),))
        station = self.job_station(key[1])
        # Typed job coordinates are accepted only by Save, like the original UI.
        item = self.items[key]
        desired = self.history.state.station_position(station)
        if desired is not None and desired.point != item.anchor_point():
            self.moved(item)
            desired = self.history.state.station_position(station)
        positions = self.results.positions
        if desired is None:
            positions = replace(
                positions,
                stations=tuple(p for p in positions.stations if p.station != station),
            )
        else:
            # Preserve station order: reordering an unchanged source is not an edit.
            positions = positions.with_station(desired)
        try:
            self.history.save(positions, self.save_positions)
        except Exception:
            logging.getLogger(__name__).exception("Unable to save PLOT marker position")
            self.show_error(
                self.text(
                    "Position could not be saved. Your edits have been kept.",
                    "No se pudo guardar la posición. Se conservaron sus cambios.",
                )
            )
            return False
        updated = replace(self.results, positions=positions)
        self.clear()
        self.set_results(updated)
        self.select(self.items[key])
        self.changed.emit()
        return True

    def cancel(self, key: MarkerKey) -> None:
        """Restore selected saved intent as an undoable edit, with no database I/O.

        Args:
            key: Typed worker/station marker identity; captions and scene positions are
                not storage keys.

        Returns:
            None.
        """
        assert self.history is not None
        positions = self.history.state
        saved = self.history.saved
        if key[0] == "worker":
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
        else:
            station = self.job_station(key[1])
            anchor = saved.station_position(station)
            positions = replace(
                positions,
                stations=tuple(
                    anchor if p.station == station and anchor is not None else p
                    for p in positions.stations
                    if p.station != station or anchor is not None
                ),
            )
            if anchor is not None and positions.station_position(station) is None:
                positions = positions.with_station(anchor)
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
        if self.results.selection.risk_view is PlotRiskView.JOB:
            pending_station: StationKey | None = None
            for key, item in self.items.items():
                station = self.job_station(key[1])
                anchor = self.history.state.station_position(station)
                saved = self.history.saved.station_position(station)
                point = anchor.point if anchor is not None else PlotPoint(18, 18)
                item.setPos(point.x + item.offset.x(), point.y + item.offset.y())
                item.anchored = anchor is not None
                item.pending = anchor != saved
                if item.pending:
                    pending_station = station
                item.setEnabled(True)
                item.update()
            if pending_station is not None:
                for key, item in self.items.items():
                    item.setEnabled(self.job_station(key[1]) == pending_station)
        else:
            for row in self.results.workers:
                identity = row.assessment.assignment_id
                marker = self.history.state.ensure_marker(identity, self.jobs).marker(
                    identity
                )
                saved_marker = self.history.saved.ensure_marker(
                    identity, self.jobs
                ).marker(identity)
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
            ValueError: Worker visual controls require a worker risk view.
        """
        self.worker_settings(marker.assignment_id)
        if self.results is None or self.results.selection.risk_view is PlotRiskView.JOB:
            raise ValueError("Worker visual controls require a worker risk view.")
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
        item = self.items.get(("worker", marker.assignment_id))
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
        if (
            self.results is None
            or not markers
            or self.results.selection.risk_view is PlotRiskView.JOB
        ):
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
            item = self.items.get(("worker", marker.assignment_id))
            if item is not None:
                item.mark_saved()
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
