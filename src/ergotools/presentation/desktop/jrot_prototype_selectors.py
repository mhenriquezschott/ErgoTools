"""Disposable project-style selection windows for the developer JROT walkthrough.

Presentation only. Borrow detached catalogs and packaged icons; return local keys.
No production selector, repository, preferences, history or database is modified.
Remove this module with the prototype; it is not a new production management flow.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
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

from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.jrot_prototype_widgets import prototype_button
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


@dataclass(frozen=True, slots=True)
class PrototypeOption:
    """One detached selectable record, without ownership or mutation capability.

    Attributes:
        key: Exact local identity; never inferred from a displayed name.
        caption: Human-readable ID and name.
        details: Availability or demographic explanation shown beside the record.
        group: Visible source group separating project, sample and new input records.
    """

    key: str
    caption: str
    details: str
    group: str


class PrototypeRecordDialog(QDialog):
    """Search a grouped project-style tree instead of a crowded record dropdown."""

    def __init__(
        self,
        title: str,
        options: tuple[PrototypeOption, ...],
        initial: str,
        icon: QIcon,
        parent: QWidget,
    ) -> None:
        """Compose a themed, read-only record picker with explicit Use/Cancel.

        Args:
            title: English picker purpose.
            options: Detached choices with visible source/availability descriptions.
            initial: Current exact key, retained on Cancel.
            icon: Existing packaged entity artwork.
            parent: Prototype control owning this temporary modal.

        Returns:
            None; selection is returned only on explicit acceptance.
        """
        super().__init__(parent)
        apply_dialog_theme(self)
        self.setWindowTitle(title)
        self.resize(820, 560)
        self.setMinimumSize(650, 440)
        self.selection: str | None = None
        self.rows: list[QTreeWidgetItem] = []
        root = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setStyleSheet("color: #0B326C; font-size: 20px; font-weight: 700;")
        root.addWidget(heading)
        search = QLineEdit()
        search.setPlaceholderText("Search by ID, name or source")
        root.addWidget(search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID / name", "Data / source"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(24, 24))
        header = self.tree.header()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        groups: dict[str, QTreeWidgetItem] = {}
        for option in options:
            if option.group not in groups:
                group = QTreeWidgetItem([option.group])
                group.setFlags(Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled))
                self.tree.addTopLevelItem(group)
                groups[option.group] = group
            row = QTreeWidgetItem([option.caption, option.details])
            row.setData(0, Qt.ItemDataRole.UserRole, option.key)
            row.setIcon(0, icon)
            row.setToolTip(0, option.caption)
            row.setToolTip(1, option.details)
            groups[option.group].addChild(row)
            self.rows.append(row)
            if option.key == initial:
                self.tree.setCurrentItem(row)
        self.tree.expandAll()
        root.addWidget(self.tree, 1)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(prototype_button("Cancel", self.reject))
        self.use = prototype_button(
            "Use selection", self.accept_selection, primary=True
        )
        buttons.addWidget(self.use)
        root.addLayout(buttons)
        search.textChanged.connect(self.filter_records)
        self.tree.currentItemChanged.connect(self.refresh_selection)
        self.tree.itemDoubleClicked.connect(lambda: self.accept_selection())
        self.refresh_selection()

    def filter_records(self, text: str) -> None:
        """Filter literal captions/details while retaining record identities.

        Args:
            text: Case-insensitive search; an empty search restores all records.

        Returns:
            None; hidden records cannot be accepted accidentally.
        """
        token = text.casefold().strip()
        for row in self.rows:
            row.setHidden(token not in (row.text(0) + " " + row.text(1)).casefold())
        self.refresh_selection()

    def refresh_selection(self) -> None:
        """Enable Use only for an actual visible source record.

        Args:
            None.

        Returns:
            None; source group headings remain non-selectable.
        """
        row = self.tree.currentItem()
        self.use.setEnabled(
            row is not None
            and not row.isHidden()
            and isinstance(row.data(0, Qt.ItemDataRole.UserRole), str)
        )

    def accept_selection(self) -> None:
        """Return a selected key without importing or assigning any production data.

        Args:
            None.

        Returns:
            None; invalid selection leaves this modal open.
        """
        row = self.tree.currentItem()
        if self.use.isEnabled() and row is not None:
            self.selection = str(row.data(0, Qt.ItemDataRole.UserRole))
            self.accept()


class PrototypeRecordChoice(QPushButton):
    """Compact record summary opening the owned searchable tree picker."""

    chosen = pyqtSignal()

    def __init__(self, title: str, icon: QIcon) -> None:
        """Retain only the picker purpose and copied artwork until configured.

        Args:
            title: English dialog heading, such as Choose a worker.
            icon: Existing packaged entity icon.

        Returns:
            None; no project or global window is looked up.
        """
        super().__init__()
        self.title = title
        self.options: tuple[PrototypeOption, ...] = ()
        self.key = ""
        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setAutoDefault(False)
        self.clicked.connect(self.choose)

    def configure(self, options: tuple[PrototypeOption, ...], initial: str) -> None:
        """Populate a detached list and preserve a still-available selection.

        Args:
            options: Nonempty source records.
            initial: Desired key; falls back to the first record if no longer present.

        Returns:
            None; configuration does not emit a user selection signal.
        """
        self.options = options
        self.key = initial if any(o.key == initial for o in options) else options[0].key
        self.setText(self.option.caption + "  …")
        self.setToolTip(self.option.caption + "\n" + self.option.details)

    @property
    def option(self) -> PrototypeOption:
        """Return the exact selected source metadata.

        Args:
            None.

        Returns:
            Current immutable option; configure precedes access.
        """
        return next(o for o in self.options if o.key == self.key)

    def select_key(self, key: str) -> None:
        """Accept an existing key and notify the prototype host once.

        Args:
            key: Exact offered source identity.

        Returns:
            None; the host owns only scratch selection changes.

        Raises:
            ValueError: The key is not offered by this picker.
        """
        if not any(o.key == key for o in self.options):
            raise ValueError("Choose an offered record.")
        self.configure(self.options, key)
        self.chosen.emit()

    def choose(self) -> None:
        """Open the temporary record window and discard cancelled picker drafts.

        Args:
            None.

        Returns:
            None; explicit acceptance updates only this button's local key.
        """
        dialog = PrototypeRecordDialog(
            self.title, self.options, self.key, self.icon(), self
        )
        try:
            if dialog.exec() == QDialog.Accepted and dialog.selection is not None:
                self.select_key(dialog.selection)
        finally:
            dialog.deleteLater()


class PrototypeScopeDialog(QDialog):
    """Choose a real hierarchy prefix and recurring shift using familiar tree views."""

    def __init__(
        self,
        hierarchy: WorkHierarchy | None,
        icons: Mapping[str, QIcon],
        shifts: tuple[tuple[str, str, str, str], ...],
        initial_path: tuple[str, ...] | None,
        initial_shift: str,
        parent: QWidget,
    ) -> None:
        """Build full-ancestry location rows and clock-described shift choices.

        Args:
            hierarchy: Detached project hierarchy, absent for a sample-only session.
            icons: Existing packaged Plant/Section/Line/Station/Shift artwork.
            shifts: ID, description, start and end strings; sample is explicitly named.
            initial_path: Selected Plant/Section/Line prefix, or all workplaces.
            initial_shift: Current exact recurring Shift identity.
            parent: Prototype owner; this dialog never opens a production editor.

        Returns:
            None; accepted path and shift remain scratch state.
        """
        super().__init__(parent)
        apply_dialog_theme(self)
        self.setWindowTitle("Choose workplace and shift")
        self.resize(980, 650)
        self.setMinimumSize(820, 540)
        self.path = initial_path
        self.shift_id = initial_shift
        root = QVBoxLayout(self)
        title = QLabel("Workplace and shift")
        title.setStyleSheet("color: #0B326C; font-size: 20px; font-weight: 700;")
        root.addWidget(title)
        note = QLabel(
            "Choose a Plant, Section or Line. Stations show physical context; "
            "Jobs remain separate activities."
        )
        note.setWordWrap(True)
        root.addWidget(note)
        body = QHBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Workplace hierarchy", "Type"])
        self.tree.setIconSize(QSize(24, 24))
        all_item = QTreeWidgetItem(["All workplaces", "Project"])
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
            row = QTreeWidgetItem([path[-1], entity])
            row.setIcon(0, icons[entity.lower()])
            row.setData(0, Qt.ItemDataRole.UserRole, path)
            row.setToolTip(0, " / ".join(path))
            if len(path) == 1:
                self.tree.addTopLevelItem(row)
            else:
                items[path[:-1]].addChild(row)
            if len(path) == 4:
                row.setFlags(Qt.ItemFlags(Qt.ItemFlag.ItemIsEnabled))
                row.setToolTip(1, "Physical context only; select the parent Line.")
            items[path] = row
            if path == initial_path:
                self.tree.setCurrentItem(row)
        self.tree.expandToDepth(1)
        self.shift_tree = QTreeWidget()
        self.shift_tree.setHeaderLabels(["Shift", "Start", "End"])
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
        buttons.addWidget(prototype_button("Cancel", self.reject))
        buttons.addWidget(
            prototype_button(
                "Use workplace and shift", self.accept_selection, primary=True
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
