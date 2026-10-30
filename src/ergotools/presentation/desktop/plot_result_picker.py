"""Searchable, read-only workplace trees for PLOT assignment and Job occurrences.

Presentation layer. The dialog consumes the already filtered immutable result rows;
selecting a leaf returns its assignment identity. It never queries or writes storage.
"""

from collections.abc import Mapping
from html import escape

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_results import PlotWorkerResult
from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_marker_layer import plot_damage_color
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE


class PlotResultPicker(QDialog):
    """Choose one exact assignment below its saved hierarchy, shift and optional Job."""

    def __init__(
        self,
        rows: tuple[PlotWorkerResult, ...],
        icons: Mapping[str, QIcon],
        *,
        job_view: bool = False,
        selected_id: int | None = None,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build a searchable tree from the caller's current applied scope only.

        Args:
            rows: Detached filtered assignments; repeated names stay distinct.
            icons: Packaged workplace, worker and Job icons, with no platform lookup.
            job_view: Show Job risks and group occurrences below their Job identities.
            selected_id: Exact assignment to reveal initially, if still in this scope.
            language: Interface language; stored names are literal plain text.
            parent: Dialog owner; cancelling never changes the host selection.

        Returns:
            None; only explicit leaf acceptance publishes selected_assignment_id.
        """
        super().__init__(parent)
        self.rows = rows
        self.icons = icons
        self.job_view = job_view
        self.language = language
        self.selected_assignment_id: int | None = None
        self._preferred = selected_id
        self.setStyleSheet(PLOT_STYLE)
        title = (
            self.text("Choose Job occurrence", "Elegir ubicación del trabajo")
            if job_view
            else self.text(
                "Choose worker assignment", "Elegir asignación de trabajador"
            )
        )
        self.setWindowTitle(title)
        self.resize(980, 630)
        self.setMinimumSize(760, 470)
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)
        hint = QLabel(
            self.text(
                (
                    "Search within the current filters. Expand a workplace "
                    "and select an "
                    "assignment; Jobs use the same map positions as Comparison."
                ),
                (
                    "Busque dentro de los filtros actuales. Expanda un lugar "
                    "y elija una "
                    "asignación; los trabajos usan las posiciones de Comparación."
                ),
            )
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.text(
                "Search ID, name, Job or workplace…",
                "Buscar ID, nombre, trabajo o lugar…",
            )
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setToolTip(self.search_input.placeholderText())
        layout.addWidget(self.search_input)
        self.tree = QTreeWidget()
        self.tree.setObjectName("plotResultTree")
        self.tree.setHeaderLabels(
            [
                self.text("Workplace / assignment", "Lugar / asignación"),
                self.text("Job", "Trabajo"),
                self.text("Risk (%)", "Riesgo (%)"),
            ]
        )
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setUniformRowHeights(True)
        self.tree.setIconSize(QSize(20, 20))
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        layout.addWidget(self.tree, 1)
        self.count_label = QLabel()
        layout.addWidget(self.count_label)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButtons(QDialogButtonBox.StandardButton.Ok)
            | QDialogButtonBox.StandardButton.Cancel
        )
        select = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        assert select is not None and cancel is not None
        self.select_button = select
        self.select_button.setText(self.text("Use selection", "Usar selección"))
        self.select_button.setIcon(icons["job_management" if job_view else "worker"])
        cancel.setText(self.text("Cancel", "Cancelar"))
        cancel.setIcon(icons["cancel"])
        self.select_button.setToolTip(
            self.text(
                "Select this assignment on the map.",
                "Seleccionar esta asignación en el mapa.",
            )
        )
        cancel.setToolTip(
            self.text(
                "Close without changing the map selection.",
                "Cerrar sin cambiar la selección del mapa.",
            )
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.search_input.textChanged.connect(self.populate)
        self.tree.currentItemChanged.connect(self.selection_changed)
        self.tree.itemDoubleClicked.connect(lambda *_args: self.accept_selection())
        self.populate()
        self.search_input.setFocus()

    def text(self, english: str, spanish: str) -> str:
        """Translate interface captions while retaining literal saved values.

        Args:
            english: English caption.
            spanish: Equivalent Spanish caption.

        Returns:
            The caption matching this dialog's language.
        """
        return spanish if self.language is Language.SPANISH else english

    def populate(self) -> None:
        """Filter complete ancestry and names, preserving exact assignment identities.

        Args:
            None; read the current search token without modifying any source row.

        Returns:
            None; branches remain non-accepting and missing risks never become zero.
        """
        current = self.tree.currentItem()
        preferred = (
            current.data(0, Qt.ItemDataRole.UserRole) if current else self._preferred
        )
        self.tree.clear()
        groups: dict[tuple[str, ...], QTreeWidgetItem] = {}
        leaves: list[QTreeWidgetItem] = []
        query = self.search_input.text().strip().casefold()
        for row in self.rows:
            place = row.assessment.owner.workplace
            name = " ".join(
                value
                for value in (row.worker.first_name, row.worker.last_name)
                if value
            )
            job = (
                f"{row.job.job_id} — {row.job.name}"
                if row.job
                else self.text("No Job", "Sin trabajo")
            )
            path: tuple[str, ...] = (
                place.plant_name,
                place.section_name,
                place.line_name,
                place.station_id,
                self.text(f"Shift {place.shift_id}", f"Turno {place.shift_id}"),
            )
            if (
                query
                and query
                not in " ".join((*path, name, row.worker.worker_id, job)).casefold()
            ):
                continue
            if self.job_view:
                path = (*path, job)
            parent: QTreeWidgetItem | None = None
            for depth, caption in enumerate(path):
                prefix = path[: depth + 1]
                node = groups.get(prefix)
                if node is None:
                    node = QTreeWidgetItem([caption])
                    node.setIcon(
                        0,
                        self.icons[
                            (
                                "plant",
                                "section",
                                "line",
                                "station",
                                "shift",
                                "job_management",
                            )[depth]
                        ],
                    )
                    node.setToolTip(
                        0, "<qt>" + escape(" \u203a ".join(prefix)) + "</qt>"
                    )
                    if parent is None:
                        self.tree.addTopLevelItem(node)
                    else:
                        parent.addChild(node)
                    groups[prefix] = node
                parent = node
            if self.job_view:
                measurement = row.job_risk.measurement if row.job_risk else None
                risk = measurement.probability_percent if measurement else None
                damage = measurement.cumulative_damage if measurement else None
            else:
                risk = (
                    row.assessment.probability * 100
                    if row.assessment.probability is not None
                    else None
                )
                damage = row.assessment.total_damage
            leaf = QTreeWidgetItem(
                [
                    f"{row.worker.worker_id} · {name}",
                    job,
                    f"{risk:.1f}" if risk is not None else "—",
                ]
            )
            leaf.setData(0, Qt.ItemDataRole.UserRole, row.assessment.assignment_id)
            leaf.setIcon(0, self.icons["worker"])
            color = QColor(plot_damage_color(row.assessment.kind, damage))
            leaf.setBackground(2, color)
            leaf.setForeground(
                2,
                QColor("#071B2D")
                if color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114
                > 145
                else QColor("white"),
            )
            leaf.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
            for column in range(3):
                leaf.setToolTip(column, "<qt>" + escape(leaf.text(column)) + "</qt>")
            assert parent is not None
            parent.addChild(leaf)
            leaves.append(leaf)
        self.tree.expandToDepth(5 if len(leaves) <= 200 else 1)
        selected = next(
            (
                leaf
                for leaf in leaves
                if leaf.data(0, Qt.ItemDataRole.UserRole) == preferred
            ),
            None,
        )
        if selected is None and leaves:
            selected = leaves[0]
        if selected is not None:
            ancestor = selected.parent()
            while ancestor is not None:
                ancestor.setExpanded(True)
                ancestor = ancestor.parent()
            self.tree.setCurrentItem(selected)
            self.tree.scrollToItem(selected)
        self.count_label.setText(
            self.text(
                f"{len(leaves)} matching assignments",
                f"{len(leaves)} asignaciones coincidentes",
            )
        )
        self.selection_changed()

    def selection_changed(self) -> None:
        """Allow acceptance only for a real leaf, never a hierarchy caption.

        Args:
            None; read the native current tree selection.

        Returns:
            None; selection changes remain local until Use selection is pressed.
        """
        item = self.tree.currentItem()
        self.select_button.setEnabled(
            item is not None and type(item.data(0, Qt.ItemDataRole.UserRole)) is int
        )

    def accept_selection(self) -> None:
        """Publish one validated assignment identity on explicit acceptance.

        Args:
            None.

        Returns:
            None; a branch or empty search leaves the dialog open.
        """
        item = self.tree.currentItem()
        identity = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if type(identity) is int and any(
            row.assessment.assignment_id == identity for row in self.rows
        ):
            self.selected_assignment_id = identity
            self.accept()
