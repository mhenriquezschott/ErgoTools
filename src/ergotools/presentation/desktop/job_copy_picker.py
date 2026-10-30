"""Read-only source browsing shared by worker-assessment and Job-value copies.

Presentation layer. Navigate immutable source identities with search, alphabet and
arrow controls; display context trees and existing colored results. An injected
resolver rechecks the selected source at acceptance. Browsing never writes, calculates,
associates or navigates the project. Explicit
subset Copy delegates evaluation to the established application calculator.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from PyQt5 import sip
from PyQt5.QtCore import QSignalBlocker, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.job_calculation import copy_job_tasks
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind, task_has_data
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.alphabet_navigation import AlphabetNavigation
from ergotools.presentation.desktop.job_result_panel import result_value_style
from ergotools.presentation.desktop.job_task_copy_details import JobTaskCopyDetails
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.theme.job_management import JOB_MANAGEMENT_STYLE
from ergotools.presentation.desktop.theme.job_results import job_damage_color


@dataclass(frozen=True, slots=True)
class CopyCandidate:
    """One source leaf, independent of localized captions and tree positions.

    Attributes:
        identity: Exact document or Job identity passed to the read-only resolver.
        path: Context labels, with parent hierarchy followed by the selectable leaf.
        job: Optional literal Job caption, never parsed for identity.
        shift: Literal recorded shift caption, empty for standalone/global values.
        measurement: Existing input/output, or None for an unavailable worker result.
    """

    identity: str
    path: tuple[str, ...]
    job: str
    shift: str
    measurement: JobRiskMeasurement | None


@dataclass(frozen=True, slots=True)
class CopySource:
    """One worker or Job shown in the source navigator.

    Attributes:
        identity: Stable worker/Job identifier, separate from visible names.
        caption: Literal surname/name or Job title, used for search and alphabet order.
        candidates: All eligible-tool contexts, including unavailable worker results.
    """

    identity: str
    caption: str
    candidates: tuple[CopyCandidate, ...]


class JobValuePicker(QDialog):
    """Browse sources and return one detached measurement through an explicit Copy."""

    def __init__(
        self,
        sources: tuple[CopySource, ...],
        kind: AssessmentKind,
        icons: Mapping[str, QIcon],
        language: Language,
        convention: DecimalConvention,
        resolve: Callable[[str], JobRiskMeasurement],
        *,
        worker_sources: bool,
        project_id: str,
        units: MeasurementSystem,
        parent: QWidget | None = None,
    ) -> None:
        """Build one source navigator and its context/result tree.

        Args:
            sources: Detached read-only worker/Job catalog in caller-defined order.
            kind: Exact ergonomic tool requested by the destination Job.
            icons: Packaged application icons for navigation and hierarchy nodes.
            language: UI wording, independent of saved names and parsing.
            convention: Decimal separator for display only.
            resolve: Recheck an exact selected identity; never mutate the source.
            worker_sources: True labels the navigator as workers; False as Jobs.
            project_id: Exact open project identity for detached subset evaluation.
            units: Project default units, without reinterpreting source quantities.
            parent: Job window retaining ownership of replacement consent/history.

        Returns:
            None; opening or browsing creates no record or project history action.
        """
        super().__init__(parent)
        self.kind = kind
        self._project_id = project_id
        self._units = units
        self.task_details: dict[str, JobTaskCopyDetails] = {}
        self._source_nodes: dict[str, QTreeWidgetItem] = {}
        self._selected_tasks: dict[str, tuple[str, ...]] = {}
        self.language = language
        self.convention = convention
        self._sources = sources
        self._resolve = resolve
        self._icons = icons
        self._letter: str | None = None
        self.selected: JobRiskMeasurement | None = None
        self.setObjectName("jobWindow")
        self.setStyleSheet(JOB_MANAGEMENT_STYLE)
        apply_dialog_theme(self)
        self.resize(1120, 740)
        self.setMinimumSize(960, 640)
        tool = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[kind]
        title = (
            self.text("Copy worker assessment", "Copiar evaluación de trabajador")
            if worker_sources
            else self.text("Copy from Job", "Copiar de trabajo")
        )
        self.setWindowTitle(f"{title} · {tool}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        heading = QLabel(self.windowTitle())
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)
        help_text = QLabel(
            self.text(
                "Choose a source and assessment context. "
                "Its inputs and results are copied independently.",
                "Seleccione un origen y contexto. Sus datos y resultados "
                "se copian de forma independiente.",
            )
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        navigator = QFrame()
        navigator.setObjectName("workspacePanel")
        navigation = QVBoxLayout(navigator)
        row = QHBoxLayout()
        row.addWidget(
            QLabel(
                self.text("Worker", "Trabajador")
                if worker_sources
                else self.text("Job", "Trabajo")
            )
        )
        self.source_combo = QComboBox()
        self.source_combo.setToolTip(
            self.text(
                "Choose the worker or Job whose assessment you want to inspect.",
                "Elegir el trabajador o trabajo cuya evaluación desea revisar.",
            )
        )
        source_column = QVBoxLayout()
        source_column.addWidget(self.source_combo)
        row.addLayout(source_column, 3)
        self.navigation_buttons: list[QPushButton] = []
        for icon, step, label in (
            ("first", -2, "First"),
            ("previous", -1, "Previous"),
            ("next", 1, "Next"),
            ("last", 2, "Last"),
        ):
            button = QPushButton()
            button.setIcon(icons[icon])
            button.setIconSize(QSize(22, 22))
            button.setFixedWidth(42)
            button.setToolTip(
                self.text(
                    label,
                    {
                        "First": "Primero",
                        "Previous": "Anterior",
                        "Next": "Siguiente",
                        "Last": "Último",
                    }[label],
                )
            )
            button.clicked.connect(lambda _checked, delta=step: self._navigate(delta))
            row.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
            self.navigation_buttons.append(button)
        self.search = QLineEdit()
        self.search.setToolTip(
            self.text(
                "Filter sources by ID or name.", "Filtrar orígenes por ID o nombre."
            )
        )
        self.search.setPlaceholderText(
            self.text("Search ID or name", "Buscar ID o nombre")
        )
        row.addWidget(self.search, 1, Qt.AlignmentFlag.AlignTop)
        navigation.addLayout(row)
        self.alphabet = AlphabetNavigation(self.text("All", "Todos"), self._set_letter)
        self.alphabet_buttons = self.alphabet.buttons
        for token, button in self.alphabet_buttons.items():
            button.setToolTip(
                self.text("Show all sources", "Mostrar todas las fuentes")
                if token == "All"
                else self.text(
                    "Show names beginning with ", "Mostrar nombres que empiezan con "
                )
                + token
            )
        source_column.addWidget(self.alphabet)
        layout.addWidget(navigator)
        self.tree = QTreeWidget()
        self.tree.setToolTip(
            self.text(
                "Expand an assessment to inspect read-only tasks and select rows "
                "to copy.",
                "Expandir una evaluación para revisar tareas y seleccionar las "
                "que desea copiar.",
            )
        )
        self.tree.setHeaderLabels(
            [
                self.text("Assessment context", "Contexto de evaluación"),
                self.text("Job", "Trabajo"),
                self.text("Shift", "Turno"),
                self.text("Source damage", "Daño del origen"),
                self.text("Probability (%)", "Probabilidad (%)"),
                self.text("State", "Estado"),
            ]
        )
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        layout.addWidget(self.tree, 1)
        preview = QFrame()
        preview.setObjectName("workspacePanel")
        preview_layout = QHBoxLayout(preview)
        self.source_summary = QLabel()
        self.source_summary.setWordWrap(True)
        preview_layout.addWidget(self.source_summary, 1)
        self.damage_preview = QLabel("—")
        self.probability_preview = QLabel("—")
        for label, caption in (
            (self.damage_preview, self.text("Source damage", "Daño del origen")),
            (
                self.probability_preview,
                self.text("Source probability (%)", "Probabilidad del origen (%)"),
            ),
        ):
            values = QVBoxLayout()
            values.addWidget(QLabel(caption))
            label.setMinimumWidth(130)
            values.addWidget(label)
            preview_layout.addLayout(values)
        layout.addWidget(preview)
        footer = QHBoxLayout()
        footer.addStretch(1)
        self.cancel_button = QPushButton(self.text("Cancel", "Cancelar"))
        self.cancel_button.setToolTip(
            self.text("Close without copying.", "Cerrar sin copiar.")
        )
        self.cancel_button.setIcon(icons["cancel"])
        self.cancel_button.clicked.connect(self.reject)
        self.use_button = QPushButton(self.text("Copy values", "Copiar valores"))
        self.use_button.setToolTip(
            self.text(
                "Copy the selected tasks/results into the destination tool; "
                "source data stays unchanged.",
                "Copiar tareas/resultados seleccionados a la herramienta de "
                "destino sin modificar el origen.",
            )
        )
        self.use_button.setObjectName("primaryOutlineButton")
        self.use_button.setIcon(
            icons["worker"] if worker_sources else icons["job_management"]
        )
        self.use_button.clicked.connect(self._use_selection)
        footer.addWidget(self.cancel_button)
        footer.addWidget(self.use_button)
        layout.addLayout(footer)
        self.search.textChanged.connect(self._filter_sources)
        self.source_combo.currentIndexChanged.connect(self._populate)
        self.tree.currentItemChanged.connect(self._selection_changed)
        self.tree.itemExpanded.connect(self._expand_source)
        self._filter_sources()

    def text(self, english: str, spanish: str) -> str:
        """Resolve interface wording without translating literal source identities.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Current-language wording.
        """
        return spanish if self.language is Language.SPANISH else english

    def _set_letter(self, letter: str) -> None:
        """Filter names alphabetically while preserving a surviving source choice.

        Args:
            letter: ASCII initial, or All to remove the alphabet filter.

        Returns:
            None; no source data changes.
        """
        self._letter = None if letter == "All" else letter
        self._filter_sources()

    def _filter_sources(self) -> None:
        """Rebuild visible identities from literal name/ID and alphabet filters.

        Args:
            None.

        Returns:
            None; an empty match clears selection and disables Copy/navigation.
        """
        previous = self.source_combo.currentData()
        self.alphabet.set_available(
            frozenset(source.caption[:1].upper() for source in self._sources),
            self._letter or "All",
        )
        query = self.search.text().casefold().strip()
        with QSignalBlocker(self.source_combo):
            self.source_combo.clear()
            for source in self._sources:
                if (
                    query
                    and query not in f"{source.identity} {source.caption}".casefold()
                ):
                    continue
                if self._letter and not source.caption.upper().startswith(self._letter):
                    continue
                self.source_combo.addItem(
                    f"{source.identity} · {source.caption}", source.identity
                )
            self.source_combo.setCurrentIndex(
                max(0, self.source_combo.findData(previous))
            )
        for button in self.navigation_buttons:
            button.setEnabled(self.source_combo.count() > 1)
        self._populate()

    def _navigate(self, step: int) -> None:
        """Navigate the filtered source list using the application's arrow analogy.

        Args:
            step: -2/2 selects first/last; -1/1 moves to the adjacent source.

        Returns:
            None; empty lists remain unselected.
        """
        count = self.source_combo.count()
        if count:
            index = (
                0
                if step == -2
                else count - 1
                if step == 2
                else min(count - 1, max(0, self.source_combo.currentIndex() + step))
            )
            self.source_combo.setCurrentIndex(index)

    def _populate(self) -> None:
        """Display standalone and real hierarchy contexts for the selected source.

        Args:
            None.

        Returns:
            None; ready zero values are selectable; unavailable values remain visible.
        """
        self.task_details.clear()
        self._source_nodes.clear()
        self.tree.clear()
        identity = self.source_combo.currentData()
        source = next((s for s in self._sources if s.identity == identity), None)
        nodes: dict[tuple[str, ...], QTreeWidgetItem] = {}
        first = None
        for candidate in source.candidates if source else ():
            parent = None
            for depth, caption in enumerate(candidate.path[:-1]):
                path = candidate.path[: depth + 1]
                if path not in nodes:
                    node = QTreeWidgetItem([caption])
                    node.setIcon(
                        0,
                        self._icons[
                            ("plant", "section", "line", "station")[min(depth, 3)]
                        ],
                    )
                    if parent is None:
                        self.tree.addTopLevelItem(node)
                    else:
                        parent.addChild(node)
                    nodes[path] = node
                parent = nodes[path]
            item = candidate.measurement
            state = (
                self.text("Calculate first", "Calcular primero")
                if item is None
                else self.text("Task inputs", "Datos de tareas")
                if item.source is not None
                else self.text("Direct result", "Resultado directo")
            )
            leaf = QTreeWidgetItem(
                [
                    candidate.path[-1],
                    candidate.job,
                    candidate.shift,
                    "—"
                    if item is None or item.cumulative_damage is None
                    else f"{item.cumulative_damage:.8g}".replace(
                        ".", self.convention.value
                    ),
                    "—"
                    if item is None or item.probability_percent is None
                    else f"{item.probability_percent:.1f}".replace(
                        ".", self.convention.value
                    ),
                    state,
                ]
            )
            leaf.setData(0, Qt.ItemDataRole.UserRole, candidate)
            self._source_nodes[candidate.identity] = leaf
            leaf.setToolTip(0, " > ".join(candidate.path))
            leaf.setIcon(
                0, self._icons["worker"] if parent is None else self._icons["station"]
            )
            if parent is None:
                self.tree.addTopLevelItem(leaf)
            else:
                parent.addChild(leaf)
            if item is not None and item.cumulative_damage is not None:
                color = QColor(job_damage_color(item.kind, item.cumulative_damage))
                foreground = QColor("#102A43" if color.lightnessF() > 0.5 else "white")
                for column in (3, 4):
                    leaf.setBackground(column, color)
                    leaf.setForeground(column, foreground)
            if item is not None and item.source is not None:
                child = QTreeWidgetItem(leaf)
                child.setFirstColumnSpanned(True)
                child.setSizeHint(0, QSize(0, 64))
            if first is None:
                first = leaf
        for node in nodes.values():
            node.setExpanded(True)
        if first is not None:
            self.tree.setCurrentItem(first)
        self._selection_changed()

    def _selection_changed(self) -> None:
        """Preview only the selected leaf; parent nodes cannot be copied.

        Args:
            None.

        Returns:
            None; absence clears previous preview values and Copy availability.
        """
        candidate = self._candidate(self.tree.currentItem())
        item = candidate.measurement if candidate is not None else None
        selected = self._task_ids(candidate) if candidate is not None else ()
        count = (
            sum(task_has_data(t) for t in item.source.tasks)
            if item and item.source
            else 0
        )
        self.use_button.setEnabled(
            item is not None and (item.source is None or bool(selected))
        )
        self.source_summary.setText(
            self.text(
                "Select an assessment to copy.",
                "Seleccione una evaluación para copiar.",
            )
            if not isinstance(candidate, CopyCandidate)
            else " > ".join(candidate.path)
            + (
                self.text(
                    f" · {len(selected)}/{count} tasks selected. "
                    "Subsets are recalculated on Copy.",
                    f" · {len(selected)}/{count} "
                    "tareas seleccionadas. "
                    "Las selecciones parciales se recalculan al copiar.",
                )
                if item is not None and item.source is not None
                else ""
            )
        )
        for label, value, digits in (
            (self.damage_preview, item.cumulative_damage if item else None, 4),
            (self.probability_preview, item.probability_percent if item else None, 1),
        ):
            label.setText(
                "—"
                if value is None
                else f"{value:.{digits}f}".replace(".", self.convention.value)
            )
            label.setToolTip("" if value is None else str(value))
            label.setStyleSheet(
                ""
                if value is None or item is None
                else result_value_style(
                    job_damage_color(item.kind, item.cumulative_damage)
                )
            )

    def _candidate(self, node: QTreeWidgetItem | None) -> CopyCandidate | None:
        """Resolve a source row or its embedded details without selecting parent groups.

        Args:
            node: Current tree row, including a detail child, or None.

        Returns:
            Exact source candidate, or None for grouping/empty rows.
        """
        while node is not None:
            candidate = node.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(candidate, CopyCandidate):
                return candidate
            node = node.parent()
        return None

    def _task_ids(self, candidate: CopyCandidate) -> tuple[str, ...]:
        """Read copy selection, defaulting to populated source rows only.

        Args:
            candidate: Immutable source snapshot whose tasks are being selected.

        Returns:
            Checked stable identities, or no task IDs for direct result values.
        """
        source = candidate.measurement.source if candidate.measurement else None
        return self._selected_tasks.get(
            candidate.identity,
            tuple(t.task_id for t in source.tasks if task_has_data(t))
            if source
            else (),
        )

    def _expand_source(self, node: QTreeWidgetItem) -> None:
        """Lazily create read-only selectable task details beneath their source row.

        Args:
            node: Expanded assessment/Job row or an ordinary hierarchy group.

        Returns:
            None; the tree owns detail widget lifetime and no values are copied.
        """
        candidate = node.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(candidate, CopyCandidate):
            return
        item = candidate.measurement
        if item is None or item.source is None:
            return
        self.tree.setCurrentItem(node)
        QTimer.singleShot(0, self._reveal_current_source)
        if candidate.identity in self.task_details:
            return
        details = JobTaskCopyDetails(
            item, self.language, self.convention, self._task_ids(candidate)
        )
        self.task_details[candidate.identity] = details
        details.activated.connect(lambda: self._activate_source(candidate.identity))
        details.selection_changed.connect(
            lambda ids, source=candidate: self._select_tasks(source, ids)
        )
        child = node.child(0)
        if child is not None:
            child.setSizeHint(0, QSize(0, details.preferred_height))
            self.tree.setItemWidget(child, 0, details)
        self.tree.setCurrentItem(node)

    def _reveal_current_source(self) -> None:
        """Keep the source row and its expanded task headers visible together.

        Args:
            None.

        Returns:
            None; retired dialogs/items are never captured by a queued callback.
        """
        if sip.isdeleted(self.tree):
            return
        node = self.tree.currentItem()
        if node is not None:
            self.tree.scrollToItem(node, QAbstractItemView.ScrollHint.PositionAtTop)

    def _activate_source(self, identity: str) -> None:
        """Keep Copy targeted to the source whose embedded preview is being used.

        Args:
            identity: Stable source identity; retired filtered rows are ignored.

        Returns:
            None; only tree selection changes, never a source or project value.
        """
        node = self._source_nodes.get(identity)
        if node is not None:
            self.tree.setCurrentItem(node)

    def _select_tasks(
        self, candidate: CopyCandidate, identities: tuple[str, ...]
    ) -> None:
        """Retain only copy-checkbox state and refresh availability/selection wording.

        Args:
            candidate: Source owning the immutable task identities.
            identities: Selected original rows, never edited source values.

        Returns:
            None; selection survives collapse/filtering while this dialog is open.
        """
        self._selected_tasks[candidate.identity] = identities
        self._activate_source(candidate.identity)
        self._selection_changed()

    def _use_selection(self) -> None:
        """Recheck the exact source before returning a detached measurement.

        Args:
            None.

        Returns:
            None; unavailable sources leave the dialog open without copying stale data.
        """
        candidate = self._candidate(self.tree.currentItem())
        if not self.use_button.isEnabled() or not isinstance(candidate, CopyCandidate):
            return
        try:
            value = self._resolve(candidate.identity)
            if value.source is not None:
                if (
                    candidate.measurement is None
                    or value.source != candidate.measurement.source
                ):
                    raise ValueError("Source tasks changed; reopen the source browser.")
                value = copy_job_tasks(
                    value,
                    self._task_ids(candidate),
                    project_id=self._project_id,
                    units=self._units,
                )
            self.selected = value
        except (ValueError, KeyError):
            self.selected = None
            self.use_button.setEnabled(False)
            self.source_summary.setText(
                self.text(
                    "Source unavailable; select another assessment.",
                    "Origen no disponible; seleccione otra evaluación.",
                )
            )
            return
        self.accept()
