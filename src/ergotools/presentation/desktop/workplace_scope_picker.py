"""Read-only hierarchy/Shift selection shared by guided entry and the scratch demo.

Presentation layer. Full ancestry and actual clock metadata remain visible. The caller
owns scope meaning and accepted data/history; Cancel changes nothing and no records,
sample entities or default Shifts are created by this selector.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.language import Language
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.workflow_action_style import set_action_icon


class WorkplaceScopePicker(QDialog):
    """Choose a real hierarchy prefix and recurring shift using familiar tree views."""

    def __init__(
        self,
        hierarchy: WorkHierarchy | None,
        icons: Mapping[str, QIcon],
        shifts: tuple[tuple[str, str, str, str], ...],
        initial_path: tuple[str, ...] | None,
        initial_shift: str,
        parent: QWidget,
        *,
        language: Language = Language.ENGLISH,
        lines_only: bool = False,
    ) -> None:
        """Build full-ancestry location rows and clock-described shift choices.

        Args:
            hierarchy: Detached project hierarchy, absent for a sample-only session.
            icons: Existing packaged Plant/Section/Line/Station/Shift artwork.
            shifts: ID, description, start and end strings; sample is explicitly named.
            initial_path: Selected Plant/Section/Line prefix, or all workplaces.
            initial_shift: Current exact recurring Shift identity.
            parent: Owning editor; this selector never writes project data.
            language: Caption language; names/keys remain literal.
            lines_only: True enables only Lines and the all-workplaces root.

        Returns:
            None; accepted path and shift remain scratch state.
        """
        super().__init__(parent)
        self.icons = icons
        self.language, self.lines_only = language, lines_only
        apply_dialog_theme(self)
        self.setWindowTitle(
            self.text("Choose workplace and shift", "Elegir lugar y turno")
        )
        self.resize(980, 650)
        self.setMinimumSize(820, 540)
        self.path = initial_path
        self.shift_id = initial_shift
        root = QVBoxLayout(self)
        title = QLabel(self.text("Workplace and shift", "Lugar de trabajo y turno"))
        title.setStyleSheet("color: #0B326C; font-size: 20px; font-weight: 700;")
        root.addWidget(title)
        note = QLabel(
            self.text(
                "Choose a Line and Shift. Stations are physical locations; Jobs "
                "are activities.",
                "Elija línea y turno. Las estaciones son lugares físicos; los "
                "trabajos son actividades.",
            )
        )
        note.setWordWrap(True)
        root.addWidget(note)
        body = QHBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [
                self.text("Workplace hierarchy", "Jerarquía laboral"),
                self.text("Type", "Tipo"),
            ]
        )
        self.tree.setIconSize(QSize(24, 24))
        all_item = QTreeWidgetItem(
            [
                self.text("All workplaces", "Todos los lugares"),
                self.text("Project", "Proyecto"),
            ]
        )
        self.tree.addTopLevelItem(all_item)
        self.tree.setCurrentItem(all_item)
        items: dict[tuple[str, ...], QTreeWidgetItem] = {}
        paths = (
            []
            if hierarchy is None
            else [(p,) for p in hierarchy.plants]
            + [(s.plant_name, s.section_name) for s in hierarchy.sections]
            + [
                (line.plant_name, line.section_name, line.line_name)
                for line in hierarchy.lines
            ]
            + [
                (s.plant_name, s.section_name, s.line_name, s.station_id)
                for s in hierarchy.work.stations
            ]
        )
        for path in paths:
            entity = ("Plant", "Section", "Line", "Station")[len(path) - 1]
            caption = self.text(
                entity,
                {
                    "Plant": "Planta",
                    "Section": "Sección",
                    "Line": "Línea",
                    "Station": "Estación",
                }[entity],
            )
            row = QTreeWidgetItem([path[-1], caption])
            row.setIcon(0, icons[entity.lower()])
            row.setData(0, Qt.ItemDataRole.UserRole, path)
            row.setToolTip(0, " / ".join(path))
            if len(path) == 1:
                self.tree.addTopLevelItem(row)
            else:
                items[path[:-1]].addChild(row)
            if len(path) == 4 or (lines_only and len(path) < 3):
                row.setFlags(Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled))
                row.setToolTip(
                    1,
                    self.text(
                        "Physical context only; select the parent Line.",
                        "Solo contexto físico; seleccione la línea superior.",
                    ),
                )
            items[path] = row
            if path == initial_path:
                self.tree.setCurrentItem(row)
        self.tree.expandToDepth(1)
        self.shift_tree = QTreeWidget()
        self.shift_tree.setHeaderLabels(
            [
                self.text("Shift", "Turno"),
                self.text("Start", "Inicio"),
                self.text("End", "Término"),
            ]
        )
        for key, description, start, end in shifts:
            row = QTreeWidgetItem([key + " · " + description, start, end])
            row.setIcon(0, icons["shift"])
            row.setData(0, Qt.ItemDataRole.UserRole, key)
            row.setToolTip(0, key + " · " + description)
            self.shift_tree.addTopLevelItem(row)
            if key == initial_shift:
                self.shift_tree.setCurrentItem(row)
        for tree in (self.tree, self.shift_tree):
            tree.setAlternatingRowColors(True)
            header = tree.header()
            assert header is not None
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            for column in range(1, tree.columnCount()):
                header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        body.addWidget(self.tree, 3)
        body.addWidget(self.shift_tree, 2)
        root.addLayout(body, 1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self._button(self.text("Cancel", "Cancelar"), self.reject))
        buttons.addWidget(
            self._button(
                self.text("Use workplace and shift", "Usar lugar y turno"),
                self.accept_selection,
                primary=True,
            )
        )
        root.addLayout(buttons)

    def accept_selection(self) -> None:
        """Return exact selected ancestry/shift without changing organization data.

        Args:
            None.

        Returns:
            None; both selections must be present before closing.
        """
        location, shift = self.tree.currentItem(), self.shift_tree.currentItem()
        if location is not None and shift is not None:
            self.path = location.data(0, Qt.ItemDataRole.UserRole)
            self.shift_id = str(shift.data(0, Qt.ItemDataRole.UserRole))
            self.accept()

    def text(self, english: str, spanish: str) -> str:
        """Choose owned captions while preserving saved record identities.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Current language text.
        """
        return spanish if self.language is Language.SPANISH else english

    def _button(
        self, caption: str, callback: Callable[[], None], *, primary: bool = False
    ) -> QPushButton:
        """Create an Enter-safe owned selector action.

        Args:
            caption: Localized button text.
            callback: Owned acceptance/cancellation callback.
            primary: True marks the accepting action in the common palette.

        Returns:
            Unparented button adopted by the action row.
        """
        button = QPushButton(caption)
        set_action_icon(button, self.icons["filter_apply" if primary else "cancel"])
        button.setAutoDefault(False)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        return button
