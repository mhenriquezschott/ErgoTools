"""Read-only multiselection of real workers or exact Job placement positions.

Presentation layer. Search/filter/check state is local until explicit acceptance. Full
hierarchy paths and result colors help distinguish repeated Jobs at different physical
positions. Hosts own all persistence, loss warnings and shared history.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from unicodedata import normalize

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
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

from ergotools.domain.language import Language
from ergotools.presentation.desktop.alphabet_navigation import AlphabetNavigation
from ergotools.presentation.desktop.jrot_table_style import style_rotation_table
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.workflow_action_style import set_action_icon


@dataclass(frozen=True, slots=True)
class JrotCatalogChoice:
    """Detached offered record retaining exact identity independently of display text.

    Attributes:
        key: Opaque current worker/position identity.
        values: Display text matching the picker columns.
        path: Full hierarchy grouping, empty for the global worker/Job catalogs.
        colors: Optional background per corresponding display column.
        in_scope: True if this record belongs to the host-selected Line.
    """

    key: str
    values: tuple[str, ...]
    path: tuple[str, ...] = ()
    colors: tuple[str | None, ...] = ()
    in_scope: bool = True


class JrotCatalogPicker(QDialog):
    """Searchable hierarchy-aware checked selection without project writes."""

    def __init__(
        self,
        title: str,
        headers: tuple[str, ...],
        choices: tuple[JrotCatalogChoice, ...],
        selected: tuple[str, ...],
        language: Language,
        parent: QWidget,
        *,
        icons: Mapping[str, QIcon],
        entity_icon: str,
        scope_label: str | None = None,
    ) -> None:
        """Build a local picker over current detached catalog rows.

        Args:
            title: Localized entity/position purpose.
            headers: Full visible column names.
            choices: Offered exact records; repeated captions never merge identities.
            selected: Initially checked offered keys.
            language: Caption language only.
            parent: Owning guided editor.
            icons: Current packaged entity/hierarchy icons.
            entity_icon: Stable worker or Job icon key for selectable leaves.
            scope_label: Selected Line caption; None omits the local scope filter.

        Returns:
            None; empty choices remain empty, and Cancel discards check changes.

        Raises:
            ValueError: Headers are empty or an offered row has another column count.
        """
        super().__init__(parent)
        if not headers or any(len(choice.values) != len(headers) for choice in choices):
            raise ValueError("Catalog rows must match the displayed columns.")
        self.language, self.choices = language, choices
        self.selected = selected
        self._letter = "All"
        self.nodes: dict[str, QTreeWidgetItem] = {}
        self.setWindowTitle(title)
        self.resize(940, 650)
        self.setMinimumSize(800, 520)
        apply_dialog_theme(self)
        root = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setStyleSheet("font-size:20px;font-weight:700;color:#0B326C;")
        root.addWidget(heading)
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            self.text("Search ID, name or workplace", "Buscar ID, nombre o lugar")
        )
        root.addWidget(self.search)
        self.scope_filter = QComboBox()
        self.scope_filter.addItem(
            self.text("Selected Line: ", "Línea seleccionada: ") + (scope_label or ""),
            True,
        )
        self.scope_filter.addItem(
            self.text("All project workers", "Todos los trabajadores del proyecto"),
            False,
        )
        self.scope_filter.setVisible(scope_label is not None)
        self.scope_filter.setCurrentIndex(0 if scope_label is not None else 1)
        self.scope_filter.setToolTip(
            self.text(
                "Filter by existing workplace assignments in the selected Line. "
                "Hidden checked workers remain selected.",
                "Filtrar por asignaciones existentes en la línea seleccionada. Las "
                "marcas ocultas se conservan.",
            )
        )
        root.addWidget(self.scope_filter)
        root.addWidget(
            QLabel(
                self.text(
                    "Last-name initial"
                    if entity_icon == "worker"
                    else "Job-name initial",
                    "Inicial del apellido"
                    if entity_icon == "worker"
                    else "Inicial del trabajo",
                )
            )
        )
        self.alphabet = AlphabetNavigation(
            self.text("All", "Todos"), self.select_letter
        )
        root.addWidget(self.alphabet)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(list(headers))
        self.tree.setIconSize(QSize(22, 22))
        style_rotation_table(self.tree)
        groups: dict[tuple[str, ...], QTreeWidgetItem] = {}
        self.groups = groups
        for choice in choices:
            parent_node: QTreeWidgetItem | None = None
            for depth, caption in enumerate(choice.path, 1):
                path = choice.path[:depth]
                if path not in groups:
                    group = QTreeWidgetItem([caption])
                    group.setIcon(
                        0,
                        icons[
                            ("plant", "section", "line", "station", "shift")[depth - 1]
                        ],
                    )
                    group.setFlags(Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled))
                    if parent_node is None:
                        self.tree.addTopLevelItem(group)
                    else:
                        parent_node.addChild(group)
                    groups[path] = group
                parent_node = groups[path]
            node = QTreeWidgetItem(list(choice.values))
            node.setIcon(0, icons[entity_icon])
            node.setFlags(node.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            node.setCheckState(
                0,
                Qt.CheckState.Checked
                if choice.key in selected
                else Qt.CheckState.Unchecked,
            )
            node.setData(0, Qt.ItemDataRole.UserRole, choice.key)
            for column, value in enumerate(choice.values):
                node.setToolTip(
                    column,
                    " / ".join(choice.path) + "\n" + headers[column] + ": " + value,
                )
                if column < len(choice.colors) and choice.colors[column]:
                    node.setBackground(column, QColor(choice.colors[column]))
            if parent_node is None:
                self.tree.addTopLevelItem(node)
            else:
                parent_node.addChild(node)
            self.nodes[choice.key] = node
        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        # Names/context absorb surplus width; risk/result columns remain content-sized.
        stretch = len(headers) - 1 if entity_icon == "worker" else 1
        header.setSectionResizeMode(min(stretch, len(headers) - 1), QHeaderView.Stretch)
        self.tree.expandAll()
        root.addWidget(self.tree, 1)
        actions = QHBoxLayout()
        for caption, checked in [
            (self.text("All visible", "Todos visibles"), True),
            (self.text("None", "Ninguno"), False),
        ]:
            button = QPushButton(caption)
            set_action_icon(button, icons["filter_apply" if checked else "cancel"], 24)
            button.setAutoDefault(False)
            button.setToolTip(
                self.text(
                    "Change checks for visible records only",
                    "Cambiar marcas solo de registros visibles",
                )
            )
            button.clicked.connect(
                lambda _checked=False, value=checked: self.check_visible(value)
            )
            actions.addWidget(button)
        self.count_label = QLabel()
        actions.addWidget(self.count_label)
        actions.addStretch(1)
        cancel = QPushButton(self.text("Cancel", "Cancelar"))
        set_action_icon(cancel, icons["cancel"])
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        accept = QPushButton(self.text("Use selection", "Usar selección"))
        set_action_icon(accept, icons["filter_apply"])
        accept.setAutoDefault(False)
        accept.clicked.connect(self.accept_selection)
        actions.addWidget(accept)
        root.addLayout(actions)
        self.search.textChanged.connect(self.filter_choices)
        self.scope_filter.currentIndexChanged.connect(
            lambda _index: self.filter_choices(self.search.text())
        )
        self.tree.itemChanged.connect(lambda *_args: self.update_count())
        self.filter_choices("")

    def text(self, english: str, spanish: str) -> str:
        """Resolve captions without translating record data.

        Args:
            english: English text.
            spanish: Spanish text.

        Returns:
            Current language caption.
        """
        return spanish if self.language is Language.SPANISH else english

    def filter_choices(self, text: str) -> None:
        """Filter leaves by complete ID/name/path, retaining all check states.

        Args:
            text: Literal case-insensitive search token.

        Returns:
            None; no source selection is accepted merely by filtering.
        """
        token = text.casefold()
        scoped = bool(self.scope_filter.currentData())
        offered = tuple(
            c
            for c in self.choices
            if (not scoped or c.in_scope)
            and token in " ".join((*c.path, *c.values)).casefold()
        )
        self.alphabet.set_available(
            frozenset(self.initial(c) for c in offered), self._letter
        )
        keys = {
            c.key
            for c in offered
            if self._letter == "All" or self.initial(c) == self._letter
        }
        for choice in self.choices:
            self.nodes[choice.key].setHidden(choice.key not in keys)
        for _path, node in sorted(self.groups.items(), key=lambda item: -len(item[0])):
            node.setHidden(
                all(
                    child.isHidden()
                    for i in range(node.childCount())
                    if (child := node.child(i)) is not None
                )
            )
        self.update_count()

    def initial(self, choice: JrotCatalogChoice) -> str:
        """Resolve an accented literal surname/Job caption to its alphabet initial.

        Args:
            choice: Detached offered record; the name is in column two, or the
                sole displayed column for single-column position pickers.

        Returns:
            Uppercase initial; no stored name or identity is normalized.
        """
        return (
            normalize(
                "NFKD", choice.values[1] if len(choice.values) > 1 else choice.values[0]
            )
            .encode("ascii", "ignore")
            .decode()
            .upper()[:1]
        )

    def select_letter(self, letter: str) -> None:
        """Filter visible records by initial without losing checks outside the filter.

        Args:
            letter: All or an enabled uppercase initial from the shared strip.

        Returns:
            None; only local picker visibility changes.
        """
        self._letter = letter
        self.filter_choices(self.search.text())

    def update_count(self) -> None:
        """Explain all retained checks, including those hidden by current filters.

        Args:
            None.

        Returns:
            None; accepting remains an explicit separate action.
        """
        checked = [
            n for n in self.nodes.values() if n.checkState(0) == Qt.CheckState.Checked
        ]
        hidden = sum(n.isHidden() for n in checked)
        self.count_label.setText(
            self.text(
                f"{len(checked)} selected · {hidden} hidden",
                f"{len(checked)} seleccionados · {hidden} ocultos",
            )
        )

    def check_visible(self, checked: bool) -> None:
        """Apply a local All/None action only to visible offered records.

        Args:
            checked: Desired local checkbox state.

        Returns:
            None; hidden choices retain their previous state.
        """
        for node in self.nodes.values():
            if not node.isHidden():
                node.setCheckState(
                    0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )

    def accept_selection(self) -> None:
        """Return checked keys in catalog order without inventing a default.

        Args:
            None.

        Returns:
            None; accepted empty selection is an explicit host-owned removal intent.
        """
        self.selected = tuple(
            c.key
            for c in self.choices
            if self.nodes[c.key].checkState(0) == Qt.CheckState.Checked
        )
        self.accept()
