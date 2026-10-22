"""Original live PLOT worker-result picker with stable assignment selection.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping
from html import escape

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_results import PlotWorkerResult
from ergotools.domain.language import Language
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE


class PlotWorkerPicker(QDialog):
    """Search current saved result rows without project queries or editor changes."""

    def __init__(
        self,
        rows: tuple[PlotWorkerResult, ...],
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Retain source geometry for the hierarchy, results, search and buttons.

        Args:
            rows: Immutable saved result/search rows retaining exact assignment
                ownership.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.rows = rows
        self.language = language
        self.scope_path: tuple[str, ...] = ()
        self.selected_assignment_id: int | None = None
        self.setWindowTitle(
            self.text("Select Worker Result", "Seleccionar resultado de trabajador")
        )
        self.resize(820, 500)
        self.setMinimumSize(680, 420)
        self.setStyleSheet(PLOT_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(10)
        title = QLabel(
            self.text("Select worker result", "Seleccionar resultado de trabajador")
        )
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            self.text(
                "Search within the workers and workplace assignments shown "
                "by the current filters.",
                "Busque entre los trabajadores y asignaciones de los filtros actuales.",
            )
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.text(
                "Search by worker ID, name, plant, section, line, station, or shift",
                "Buscar por ID, nombre, planta, sección, línea, estación o turno",
            )
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setToolTip(
            self.text(
                "Results update while you type.",
                "Los resultados se actualizan al escribir.",
            )
        )
        layout.addWidget(self.search_input)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderLabels(
            (self.text("Workplace", "Lugar de trabajo"),)
        )
        self.workplace_tree.setAlternatingRowColors(True)
        self.workplace_tree.setMinimumWidth(220)
        self.workplace_tree.setToolTip(
            self.text(
                "Select a workplace level to narrow the worker results.",
                "Seleccione un nivel para filtrar los resultados.",
            )
        )
        nodes: dict[tuple[str, ...], QTreeWidgetItem] = {}
        for row in rows:
            parent_item: QTreeWidgetItem | None = None
            path: tuple[str, ...] = ()
            for asset, value in zip(
                ("plant", "section", "line", "station"),
                self.workplace_path(row),
                strict=True,
            ):
                path = (*path, value)
                if path not in nodes:
                    item = QTreeWidgetItem((value,))
                    item.setData(0, Qt.ItemDataRole.UserRole, path)
                    item.setIcon(0, icons[asset])
                    if parent_item is None:
                        self.workplace_tree.addTopLevelItem(item)
                    else:
                        parent_item.addChild(item)
                    nodes[path] = item
                parent_item = nodes[path]
        self.workplace_tree.collapseAll()
        if self.workplace_tree.topLevelItemCount():
            self.workplace_tree.setCurrentItem(self.workplace_tree.topLevelItem(0))
        self.splitter.addWidget(self.workplace_tree)
        self.results = QTreeWidget()
        self.results.setColumnCount(4)
        self.results.setHeaderLabels(
            tuple(
                self.text(en, es)
                for en, es in (
                    ("Worker", "Trabajador"),
                    ("Name", "Nombre"),
                    ("Workplace", "Lugar de trabajo"),
                    ("Shift", "Turno"),
                )
            )
        )
        self.results.setRootIsDecorated(False)
        self.results.setAlternatingRowColors(True)
        self.results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        header = self.results.header()
        assert header is not None
        header.setStretchLastSection(False)
        for column in (0, 1, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.splitter.addWidget(self.results)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setSizes((230, 570))
        layout.addWidget(self.splitter, 1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButtons(QDialogButtonBox.StandardButton.Cancel)
            | QDialogButtonBox.StandardButton.Ok
        )
        select_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        assert select_button is not None and cancel_button is not None
        self.select_button = select_button
        self.cancel_button = cancel_button
        select_button.setText(self.text("Select Worker", "Seleccionar trabajador"))
        cancel_button.setText(self.text("&Cancel", "&Cancelar"))
        select_button.setIcon(icons["worker"])
        cancel_button.setIcon(icons["cancel"])
        for button in (select_button, cancel_button):
            button.setIconSize(QSize(22, 22))
        select_button.setToolTip(
            self.text(
                "Select this worker result on the plant layout.",
                "Seleccionar este resultado en el plano.",
            )
        )
        cancel_button.setToolTip(
            self.text(
                "Close without changing the selected worker.",
                "Cerrar sin cambiar el trabajador seleccionado.",
            )
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.search_input.textChanged.connect(self.populate)
        self.workplace_tree.currentItemChanged.connect(self.change_scope)
        self.results.itemDoubleClicked.connect(lambda *_args: self.accept_selection())
        self.results.currentItemChanged.connect(self.update_selection)
        self.populate()

    def text(self, english: str, spanish: str) -> str:
        """Translate captions independently of literal saved identities.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    @staticmethod
    def workplace_path(row: PlotWorkerResult) -> tuple[str, str, str, str]:
        """Return exact saved ancestry; repeated station labels remain distinct.

        Args:
            row: Saved typed result row carrying exact source/assignment ownership and
                optional evidence.

        Returns:
            Exact saved plant/section/line/station ancestry, excluding shift.
        """
        place = row.assessment.owner.workplace
        return place.plant_name, place.section_name, place.line_name, place.station_id

    def change_scope(self, item: QTreeWidgetItem | None) -> None:
        """Apply a hierarchy prefix only within this modal result snapshot.

        Args:
            item: Borrowed live tree/graphics item carrying typed owner data; None
                denotes no selection.

        Returns:
            None.
        """
        path = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else ()
        self.scope_path = (
            tuple(str(value) for value in path) if isinstance(path, tuple) else ()
        )
        self.populate()

    def populate(self) -> None:
        """Perform source substring search across ID/name/hierarchy/shift live.

        Args:
            None.

        Returns:
            None.
        """
        query = self.search_input.text().strip().casefold()
        self.results.clear()
        for row in self.rows:
            worker = row.worker
            name = ", ".join(
                value for value in (worker.last_name, worker.first_name) if value
            )
            path = self.workplace_path(row)
            workplace = " \u203a ".join(path)
            shift = row.assessment.owner.workplace.shift_id
            if self.scope_path and path[: len(self.scope_path)] != self.scope_path:
                continue
            if (
                query
                and query
                not in " ".join((worker.worker_id, name, workplace, shift)).casefold()
            ):
                continue
            item = QTreeWidgetItem((worker.worker_id, name, workplace, shift))
            item.setData(0, Qt.ItemDataRole.UserRole, row.assessment.assignment_id)
            for column, value in enumerate((worker.worker_id, name, workplace, shift)):
                item.setToolTip(column, "<qt>" + escape(value) + "</qt>")
            self.results.addTopLevelItem(item)
        if self.results.topLevelItemCount():
            self.results.setCurrentItem(self.results.topLevelItem(0))
        self.update_selection()

    def update_selection(self) -> None:
        """Disable acceptance when the live query has no selected result.

        Args:
            None.

        Returns:
            None.
        """
        self.select_button.setEnabled(self.results.currentItem() is not None)

    def accept_selection(self) -> None:
        """Publish one stable assignment ID; empty acceptance has no effect.

        Args:
            None.

        Returns:
            None.
        """
        item = self.results.currentItem()
        if item is not None:
            identity = item.data(0, Qt.ItemDataRole.UserRole)
            if type(identity) is int and any(
                row.assessment.assignment_id == identity for row in self.rows
            ):
                self.selected_assignment_id = identity
                self.accept()
