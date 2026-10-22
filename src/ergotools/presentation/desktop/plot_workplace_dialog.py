"""Original PLOT workplace-scope picker without SQL or global window lookup.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.plot_scope import PlotScope, hierarchy_paths
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE

# Original plant/section/line/station path levels; independent shift selection is
# separate.
_ENTITIES = ("Plant", "Section", "Line", "Station")
# Spanish plant/section/line/station path headings in original hierarchy order.
_SPANISH = ("Planta", "Sección", "Línea", "Estación")


class PlotWorkplaceDialog(QDialog):
    """Retain reference controls, one-plant checks and explicit modal acceptance."""

    def __init__(
        self,
        hierarchy: WorkHierarchy,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        initial: PlotScope | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Build a source-derived scope picker from an immutable saved hierarchy.

        Args:
            hierarchy: Immutable saved workplace/shift catalog used to build the local
                selection tree.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            initial: Initial exact PLOT scope, or None for an unselected scope.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        if initial is not None:
            initial.validate(hierarchy)
        self.hierarchy = hierarchy
        self.language = language
        self._updating_checks = False
        self.selection: PlotScope | None = None
        self._paths: tuple[tuple[str, ...], ...] = ()
        self.setWindowTitle(
            self.text("Filter by Workplace", "Filtrar por lugar de trabajo")
        )
        self.setMinimumSize(570, 540)
        self.setObjectName("plotWorkplaceDialog")
        self.setStyleSheet(PLOT_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel(self.text("Workplace scope", "Ámbito del lugar de trabajo"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        description = QLabel(
            self.text(
                "Choose one plant, then check one or more sections, lines, "
                "or stations. "
                "A checked higher level includes every location beneath it.",
                "Elija una planta y marque secciones, líneas o estaciones. "
                "Un nivel superior marcado incluye todos los lugares debajo de él.",
            )
        )
        description.setWordWrap(True)
        description.setObjectName("supportingText")
        layout.addWidget(description)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(
            [
                self.text("Include", "Incluir"),
                self.text("Workplace hierarchy", "Jerarquía del lugar de trabajo"),
                self.text("Scope", "Ámbito"),
            ]
        )
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(22, 22))
        header = self.tree.header()
        assert header is not None
        header.setStretchLastSection(False)
        for column, mode in enumerate(
            (
                QHeaderView.ResizeMode.ResizeToContents,
                QHeaderView.ResizeMode.Stretch,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        ):
            header.setSectionResizeMode(column, mode)
        self.tree.setToolTip(
            self.text(
                "Expand the hierarchy and use the Include checkboxes. "
                "Selections are limited to one plant.",
                "Expanda la jerarquía y marque Incluir. "
                "El ámbito se limita a una planta.",
            )
        )
        self.items: dict[tuple[str, ...], QTreeWidgetItem] = {}
        self._updating_checks = True
        for path in hierarchy_paths(hierarchy):
            depth = len(path) - 1
            item = QTreeWidgetItem(
                ["", path[-1], self.text(_ENTITIES[depth], _SPANISH[depth])]
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setIcon(1, icons[_ENTITIES[depth].lower()])
            if len(path) == 1:
                self.tree.addTopLevelItem(item)
            else:
                self.items[path[:-1]].addChild(item)
            self.items[path] = item
        if initial is not None:
            for path in initial.paths:
                self.items[path].setCheckState(0, Qt.CheckState.Checked)
        self._updating_checks = False
        self.tree.collapseAll()
        if self.items:
            path = initial.paths[0] if initial is not None else next(iter(self.items))
            self.tree.setCurrentItem(self.items[path])
        self.tree.itemChanged.connect(self.check_changed)
        self.tree.itemDoubleClicked.connect(self.toggle_check)
        layout.addWidget(self.tree, 1)
        row = QHBoxLayout()
        row.addWidget(QLabel(self.text("Shift", "Turno")))
        self.shift_combo = QComboBox()
        self.shift_combo.addItem(self.text("All", "Todos"), None)
        for shift in sorted(hierarchy.work.shifts):
            self.shift_combo.addItem(shift, shift)
        if initial is not None:
            self.shift_combo.setCurrentIndex(self.shift_combo.findData(initial.shift))
        self.shift_combo.setToolTip(
            self.text(
                "Choose a shift or include every shift in the selected workplace.",
                "Elija un turno o incluya todos los turnos del ámbito seleccionado.",
            )
        )
        self.shift_combo.currentIndexChanged.connect(self.refresh_summary)
        row.addWidget(self.shift_combo, 1)
        layout.addLayout(row)
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextFormat(Qt.TextFormat.PlainText)
        self.path_label.setObjectName("contextSummary")
        layout.addWidget(self.path_label)
        buttons = QDialogButtonBox()
        use_button = buttons.addButton(QDialogButtonBox.StandardButton.Ok)
        cancel = buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        assert use_button is not None and cancel is not None
        self.use_button = use_button
        self.use_button.setText(self.text("Use workplaces", "Usar lugares de trabajo"))
        self.use_button.setIcon(icons["station"])
        self.use_button.setIconSize(QSize(24, 24))
        cancel.setText(self.text("Cancel", "Cancelar"))
        cancel.setIcon(icons["cancel"])
        cancel.setIconSize(QSize(22, 22))
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.refresh_summary()

    def text(self, english: str, spanish: str) -> str:
        """Translate owned captions while preserving literal record identities.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def toggle_check(self, item: QTreeWidgetItem, column: int) -> None:
        """Retain double-click checking without changing tree-selection intent.

        Args:
            item: Borrowed live Qt item carrying typed owner data; the method does not
                take ownership.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            None.
        """
        item.setCheckState(
            0,
            Qt.CheckState.Unchecked
            if item.checkState(0) == Qt.CheckState.Checked
            else Qt.CheckState.Checked,
        )

    def check_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Keep one plant and avoid simultaneously checked ancestors/descendants.

        Args:
            item: Borrowed live Qt item carrying typed owner data; the method does not
                take ownership.
            column: Zero-based table/tree column; derived columns remain protected where
                specified.

        Returns:
            None.
        """
        if self._updating_checks or column != 0:
            return
        if item.checkState(0) == Qt.CheckState.Checked:
            path = next(
                path for path, candidate in self.items.items() if candidate is item
            )
            self._updating_checks = True
            try:
                for other, candidate in self.items.items():
                    if other != path and (
                        other[0] != path[0]
                        or other[: len(path)] == path
                        or path[: len(other)] == other
                    ):
                        candidate.setCheckState(0, Qt.CheckState.Unchecked)
            finally:
                self._updating_checks = False
        self.refresh_summary()

    def refresh_summary(self) -> None:
        """Update the original path summary and availability once per user change.

        Args:
            None.

        Returns:
            None.
        """
        paths = tuple(
            path
            for path, item in self.items.items()
            if item.checkState(0) == Qt.CheckState.Checked
        )
        self._paths = PlotScope(paths).paths if paths else ()
        self.use_button.setEnabled(bool(self._paths))
        if not self._paths:
            self.path_label.setText(
                self.text(
                    "Check at least one workplace scope.",
                    "Marque al menos un ámbito de trabajo.",
                )
            )
            return
        descriptions = [
            " \u203a ".join(path[1:])
            if len(path) > 1
            else self.text("All locations", "Todos los lugares")
            for path in self._paths
        ]
        shift = self.shift_combo.currentText() or self.text("All", "Todos")
        self.path_label.setText(
            f"{self.text('Plant', 'Planta')}: {self._paths[0][0]}  |  "
            f"{self.text('Included', 'Incluidos')}: {'; '.join(descriptions)}  |  "
            f"{self.text('Shift', 'Turno')}: {shift}"
        )

    def accept_selection(self) -> None:
        """Return an immutable validated choice only after explicit acceptance.

        Args:
            None.

        Returns:
            None.
        """
        if self._paths:
            scope = PlotScope(self._paths, self.shift_combo.currentData())
            scope.validate(self.hierarchy)
            self.selection = scope
            self.accept()
