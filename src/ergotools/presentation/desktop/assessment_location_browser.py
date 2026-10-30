"""Compact current-tool assessment browser with exact source identities.

Presentation only: cascading saved paths never filter workers, create sources or move
ownership. The host resolves pending inputs and accepts navigation commands.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from PyQt5.QtCore import QSignalBlocker, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QToolButton,
    QWidget,
)

from ergotools.application.assessment_navigation import context_values
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.language import Language
from ergotools.domain.risk import classify_probability
from ergotools.presentation.desktop.combo_popup import style_combo_popup
from ergotools.presentation.desktop.context_value_label import ContextValueLabel
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES


@dataclass(frozen=True, slots=True)
class AssessmentLocation:
    """Saved source row; duplicate paths retain distinct assignment/document identities.

    Attributes:
        document_id: Exact saved source selected by the terminal dropdown.
        assignment_id: Exact historical or active workplace owner.
        workplace: Literal five-level saved location.
        detail: Optional assignment dates/status for historical disambiguation.
        probability: Saved probability on the 0-100 scale, or None when unavailable.
        job: Optional Job ID/name; classification is information, not editable.
    """

    document_id: str
    assignment_id: int
    workplace: WorkplaceContext
    detail: str
    probability: float | None
    job: tuple[str, str] | None = None


class AssessmentLocationBrowser(QGroupBox):
    """Five-level saved-assessment selector with no implicit ownership mutations."""

    # Exact document identity, never the display caption or a partial workplace path.
    selected = pyqtSignal(str)

    def __init__(self, icons: Mapping[str, QIcon]) -> None:
        """Build familiar hierarchy headings and compact cascading selectors.

        Args:
            icons: Injected packaged Plant/Section/Line/Station/Shift assets.

        Returns:
            None; no navigation occurs until a user changes a selector.
        """
        super().__init__()
        self.setMinimumWidth(0)
        self.setObjectName("assessmentLocationBrowser")
        self._rows: tuple[AssessmentLocation, ...] = ()
        self._language = Language.ENGLISH
        self._current: AssessmentLocation | None = None
        grid = QGridLayout(self)
        grid.setContentsMargins(10, 5, 10, 5)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(3)
        self.headings: list[QLabel] = []
        self.combos: list[QComboBox] = []
        for index, key in enumerate(("plant", "section", "line", "station", "shift")):
            heading = QWidget()
            row = QHBoxLayout(heading)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            glyph = QLabel()
            glyph.setPixmap(icons[key].pixmap(22, 22))
            glyph.setFixedSize(22, 22)
            label = QLabel()
            label.setObjectName("contextLabel")
            self.headings.append(label)
            row.addWidget(glyph)
            row.addWidget(label)
            row.addStretch()
            grid.addWidget(heading, 0, index)
            combo = QComboBox()
            combo.setMinimumWidth(0)
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            style_combo_popup(combo)
            combo.currentIndexChanged.connect(
                lambda _index, level=index: self._changed(level)
            )
            self.combos.append(combo)
            grid.addWidget(combo, 1, index)
            grid.setColumnStretch(index, (5, 4, 4, 4, 0)[index])
        grid.setColumnMinimumWidth(4, 100)
        job_title = QWidget()
        job_title_layout = QHBoxLayout(job_title)
        job_title_layout.setContentsMargins(0, 0, 0, 0)
        job_title_layout.setSpacing(4)
        glyph = QLabel()
        glyph.setPixmap(icons["job_management"].pixmap(22, 22))
        glyph.setFixedSize(22, 22)
        self.job_heading = QLabel()
        self.job_heading.setObjectName("contextLabel")
        job_title_layout.addWidget(glyph)
        job_title_layout.addWidget(self.job_heading)
        job_title_layout.addStretch()
        grid.addWidget(job_title, 0, 5)
        self.job_stack = QStackedWidget()
        self.job_stack.setMinimumWidth(0)
        self.job_value = ContextValueLabel()
        # Match the heading text after its 22px icon and 4px spacing.
        self.job_value.setContentsMargins(26, 0, 0, 0)
        self.job_combo = QComboBox()
        self.job_combo.setMinimumWidth(0)
        self.job_combo.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon
        )
        style_combo_popup(self.job_combo)
        self.job_combo.currentIndexChanged.connect(self._job_changed)
        self.job_stack.addWidget(self.job_value)
        self.job_stack.addWidget(self.job_combo)
        grid.addWidget(self.job_stack, 1, 5)
        grid.setColumnStretch(5, 4)
        self.add_button = QToolButton()
        self.add_button.setObjectName("workerActionButton")
        self.add_button.setIcon(icons["new"])
        self.add_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.add_button.setFixedHeight(32)
        grid.addWidget(self.add_button, 1, 6)
        self.delete_button = QToolButton()
        self.delete_button.setObjectName("workerActionButton")
        self.delete_button.setIcon(icons["delete"])
        self.delete_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.delete_button.setFixedHeight(32)
        grid.addWidget(self.delete_button, 1, 7)
        # The worker controls host this single-line status, outside the compact browser.
        self.summary = ContextValueLabel()
        self.summary.setParent(self)
        self.summary.hide()
        self.summary.setMinimumWidth(0)

    @property
    def assessment_count(self) -> int:
        """Expose current-tool workplace availability for the collapsed disclosure.

        Args:
            None.

        Returns:
            Number of saved source identities, independent of the active source.
        """
        return len(self._rows)

    @property
    def has_assessments(self) -> bool:
        """Report whether the current worker/tool has saved workplace sources.

        Args:
            None.

        Returns:
            True for a nonempty projected catalog; no project I/O occurs.
        """
        return bool(self._rows)

    def update_rows(
        self,
        rows: tuple[AssessmentLocation, ...],
        document_id: str | None,
        language: Language,
        tool: str,
        *,
        standalone_open: bool = True,
    ) -> None:
        """Project saved source choices without selecting or creating an assessment.

        Args:
            rows: Current worker/current tool workplace assessments only.
            document_id: Open source to highlight, or a standalone/unsaved identity.
            language: UI language; literal saved names remain unchanged.
            tool: Current tool caption for the summary.
            standalone_open: Whether the active view has no workplace owner.

        Returns:
            None; signals stay blocked during all programmatic population.
        """
        self._rows = tuple(
            sorted(
                rows,
                key=lambda r: (
                    tuple(v.casefold() for v in context_values(r.workplace)),
                    r.job or ("", ""),
                    r.assignment_id,
                    r.document_id,
                ),
            )
        )
        self._language = language
        spanish = language is Language.SPANISH
        self.setTitle("Evaluación" if spanish else "Assessment")
        self.add_button.setText("Añadir evaluación…" if spanish else "Add assessment…")
        self.add_button.setToolTip(
            "Crear una evaluación para este trabajador y herramienta en un lugar."
            if spanish
            else "Create an assessment for this worker and tool at a workplace."
        )
        self.delete_button.setText(
            "Eliminar evaluación…" if spanish else "Delete assessment…"
        )
        self.delete_button.setToolTip(
            "Eliminar una evaluación guardada; no elimina la asignación."
            if spanish
            else "Delete a saved assessment without removing its workplace assignment."
        )
        self.delete_button.setEnabled(bool(rows))
        self.job_heading.setText("Trabajo" if spanish else "Job")
        self._current = next(
            (r for r in self._rows if r.document_id == document_id), None
        )
        self._populate(0, self._current)
        self.setEnabled(True)
        if self._current is not None:
            path = " / ".join(context_values(self._current.workplace))
            message = (
                f"{tool} · "
                + ("Lugar seleccionado: " if spanish else "Workplace selected: ")
                + path
            )
        elif standalone_open:
            message = f"{tool} · " + (
                "Evaluación independiente seleccionada"
                if spanish
                else "Standalone selected"
            )
            message += f" · {len(rows)} " + (
                "evaluaciones en lugares disponibles"
                if spanish
                else "workplace assessments available"
            )
        else:
            message = f"{tool} · " + (
                "Vista previa del lugar sin guardar"
                if spanish
                else "Unsaved workplace preview"
            )
        self.summary.setText(message)
        self.summary.setToolTip(message)
        self._highlight()

    def _populate(self, level: int, current: AssessmentLocation | None = None) -> None:
        """Populate unique relevant paths, then resolve exact source in the Job cell.

        Args:
            level: First hierarchy selector to rebuild, from Plant zero to Shift four.
            current: Exact saved assessment to project without emitting selection.

        Returns:
            None; headings count actual entries and values retain literal identities.
        """
        spanish = self._language is Language.SPANISH
        labels = (
            ("Planta", "Sección", "Línea", "Estación", "Turno")
            if spanish
            else ("Plant", "Section", "Line", "Station", "Shift")
        )
        for depth in range(level, 5):
            combo = self.combos[depth]
            prefix = tuple(c.currentData() for c in self.combos[:depth])
            matches = tuple(
                r for r in self._rows if context_values(r.workplace)[:depth] == prefix
            )
            values = sorted(
                {context_values(r.workplace)[depth] for r in matches}, key=str.casefold
            )
            with QSignalBlocker(combo):
                combo.clear()
                combo.addItem("Seleccionar…" if spanish else "Select…", None)
                for value in values:
                    items = tuple(
                        r
                        for r in matches
                        if context_values(r.workplace)[depth] == value
                    )
                    caption = value
                    probability = None
                    if depth == 3:
                        caption, probability = self._station_caption(
                            value, items, current if current in items else None
                        )
                    combo.addItem(caption, value)
                    index = combo.count() - 1
                    combo.setItemData(
                        index,
                        value
                        + "\n"
                        + "\n".join(self._source_caption(r) for r in items),
                        Qt.ItemDataRole.ToolTipRole,
                    )
                    if probability is not None:
                        self._color_item(combo, index, probability)
                if current is not None:
                    combo.setCurrentIndex(
                        max(0, combo.findData(context_values(current.workplace)[depth]))
                    )
            if depth == 4:
                # Keep short shift IDs from consuming space needed by place/Job names.
                # Longer IDs get measured space without crowding the row.
                width = max(
                    (combo.fontMetrics().horizontalAdvance(v) for v in values),
                    default=0,
                )
                combo.setMinimumWidth(min(190, max(100, width + 30)))
            self.headings[depth].setText(f"{labels[depth]} ({len(values)})")
            combo.setEnabled(bool(values))
            combo.setToolTip(
                "Abrir datos existentes; no filtra trabajadores."
                if spanish
                else "Browse existing assessments; this does not filter workers."
            )
            self.headings[depth].setToolTip(
                "Opciones disponibles." if spanish else "Available entries."
            )
        self._populate_jobs(current)

    def _populate_jobs(self, current: AssessmentLocation | None) -> None:
        """Show Job information, using a selector only for ambiguous saved owners.

        Args:
            current: Exact source selected through this complete hierarchy path.

        Returns:
            None; the Job cell chooses saved sources without reclassifying Jobs.
        """
        spanish = self._language is Language.SPANISH
        path = tuple(c.currentData() for c in self.combos)
        matches = tuple(r for r in self._rows if context_values(r.workplace) == path)
        with QSignalBlocker(self.job_combo):
            self.job_combo.clear()
            used: set[str] = set()
            for row in matches:
                caption = (
                    " · ".join(row.job)
                    if row.job
                    else ("Sin trabajo asignado" if spanish else "No Job assigned")
                )
                if row.detail:
                    caption += " · " + row.detail
                if caption in used:
                    caption += f" · #{row.assignment_id}"
                used.add(caption)
                self.job_combo.addItem(caption, row.document_id)
                self.job_combo.setItemData(
                    self.job_combo.count() - 1,
                    self._source_caption(row),
                    Qt.ItemDataRole.ToolTipRole,
                )
            if current is not None:
                self.job_combo.setCurrentIndex(
                    self.job_combo.findData(current.document_id)
                )
        self.job_stack.setCurrentIndex(1 if len(matches) > 1 else 0)
        self.job_value.setText(self.job_combo.currentText() if matches else "—")
        self.job_value.setToolTip(
            self._source_caption(matches[0])
            if matches
            else ("Seleccione un lugar." if spanish else "Select a workplace.")
        )
        self.job_combo.setToolTip(
            "Elegir la evaluación guardada; no cambia el trabajo."
            if spanish
            else "Choose a saved assessment; this does not change its Job."
        )

    def _highlight(self) -> None:
        """Outline only the actual open workplace source, not an available placeholder.

        Args:
            None.

        Returns:
            None; highlight follows the accepted source, including history replay.
        """
        for widget in (self, *self.combos, self.job_combo):
            widget.setProperty("assessmentCurrent", self._current is not None)
            style = widget.style()
            assert style is not None
            style.unpolish(widget)
            style.polish(widget)
            widget.update()

    @staticmethod
    def _source_caption(row: AssessmentLocation) -> str:
        """Describe a source in a tooltip without changing its stored identity.

        Args:
            row: One saved source and its literal workplace/Job details.

        Returns:
            Full station, shift, available percentage and optional ownership details.
        """
        result = "—" if row.probability is None else f"{row.probability:.1f}%"
        return (
            f"{row.workplace.station_id} · {row.workplace.shift_id} · "
            f"{result} · {' · '.join(row.job) if row.job else ''} · {row.detail}"
        ).rstrip(" ·")

    @staticmethod
    def _station_caption(
        station: str,
        rows: tuple[AssessmentLocation, ...],
        selected: AssessmentLocation | None,
    ) -> tuple[str, float | None]:
        """Keep results beside Station without presenting an invented average.

        Args:
            station: Literal station identity; item data always retains this value.
            rows: Assessments at this station for all available shifts/owners.
            selected: Exact open source at this station, or None for other choices.

        Returns:
            Station caption and a single risk percentage for coloring when meaningful.
            The open station shows its selected assessment. Other stations with varying
            results show a range; missing results remain explicit and neutral.
        """
        if selected is not None:
            value = selected.probability
            return station + (" · —" if value is None else f" · {value:.1f}%"), value
        values = {row.probability for row in rows}
        if len(values) == 1:
            value = next(iter(values))
            return station + (" · —" if value is None else f" · {value:.1f}%"), value
        known = sorted(v for v in values if v is not None)
        suffix = (
            f"{known[0]:.1f}%"
            if len(known) == 1
            else f"{known[0]:.1f}\u2013{known[-1]:.1f}%"
            if known
            else "—"
        )
        if None in values and known:
            suffix += " / —"
        return f"{station} · {suffix}", None

    @staticmethod
    def _color_item(combo: QComboBox, index: int, probability: float) -> None:
        """Apply the existing gauge risk color to a Station dropdown item.

        Args:
            combo: Station selector being populated under signal blocking.
            index: Exact newly inserted item index.
            probability: Available percentage on the 0-100 scale.

        Returns:
            None; scientific values and selection remain unchanged.
        """
        color = RISK_APPEARANCES[classify_probability(probability)].color_hex
        combo.setItemData(index, QColor(color), Qt.ItemDataRole.BackgroundRole)
        combo.setItemData(index, QColor("#102A43"), Qt.ItemDataRole.ForegroundRole)

    def _changed(self, level: int) -> None:
        """Open the first saved descendant for an explicit hierarchy choice.

        Args:
            level: Changed Plant/Section/Line/Station/Shift selector.

        Returns:
            None; placeholders restore the open path without mislabeling the source.
        """
        if self.combos[level].currentData() is None:
            self._populate(0, self._current)
            return
        prefix = tuple(c.currentData() for c in self.combos[: level + 1])
        row = next(
            (
                r
                for r in self._rows
                if context_values(r.workplace)[: level + 1] == prefix
            ),
            None,
        )
        self._populate(level + 1, row)
        if row is not None:
            self.selected.emit(row.document_id)

    def _job_changed(self) -> None:
        """Select an exact saved source when several owners share the station/shift.

        Args:
            None.

        Returns:
            None; source IDs, not Job captions, establish identity.
        """
        identity = self.job_combo.currentData()
        if isinstance(identity, str):
            self.selected.emit(identity)
