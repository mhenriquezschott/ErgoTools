"""Original Job workplace layout connected to an injected, SQL-free presenter.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Iterator, Mapping

from PyQt5.QtCore import QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.work_catalog import StationKey
from ergotools.presentation.desktop.text import desktop_text
from ergotools.presentation.job_workplaces import JobWorkplaces, JobWorkplaceView

# Applicable rules from the original main workspace and Job Management theme.
_STYLE = """
QLabel#dialogTitle { color: #0B326C; font-size: 20px; font-weight: 700; }
QLabel#supportingText { color: #405462; font-size: 12px; }
QComboBox, QLineEdit { min-height: 30px; background: white;
 border: 1px solid #BCC9D3; border-radius: 5px; padding: 0 8px; }
QComboBox:focus, QLineEdit:focus { border: 2px solid #08A9B5; }
QComboBox QAbstractItemView { background: white; color: #1B2933;
 border: 1px solid #9EB0BE; selection-background-color: #087E91;
 selection-color: white; outline: 0; padding: 3px; }
QComboBox QAbstractItemView::item:selected,
QComboBox QAbstractItemView::item:hover { background: #087E91; color: white; }
QPushButton { min-height: 32px; background: white; color: #0B326C;
 border: 1px solid #9EB0BE; border-radius: 5px; padding: 0 12px; font-weight: 600; }
QPushButton:hover { background: #EDF7F8; border-color: #08A9B5; }
QPushButton#primaryOutlineButton { border: 2px solid #08A9B5; }
QHeaderView::section { background: #EAF1F5; color: #0B326C; border: 0;
 border-right: 1px solid #CAD5DD; border-bottom: 1px solid #CAD5DD;
 padding: 7px; font-weight: 700; }
QToolTip { background: #1B2933; color: white; border: 1px solid #0B326C;
 padding: 6px; }
"""


class JobWorkplaceDialog(QDialog):
    """Edit per-shift selections locally and persist once on explicit Save.

    The host loads the view and supplies processed icons and an optional remembered
    shift. Cancel performs no writes. Read preferred_shift after successful save to
    remember it without reaching into an unrelated parent window.
    """

    def __init__(
        self,
        presenter: JobWorkplaces,
        view: JobWorkplaceView,
        icons: Mapping[str, QIcon],
        *,
        preferred_shift: str | None = None,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build the original layout with typed data and no hidden database reads.

        Args:
            presenter: Injected tool/workplace coordinator; owns parsing and source
                commands, not these widgets.
            view: Immutable already-loaded job workplace view; no hidden storage reads
                are needed.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            preferred_shift: Remembered project shift identifier; None selects the
                dialog's available default.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.language = language
        self.presenter = presenter
        self.view = view
        self.preferred_shift: str | None = None
        self._displayed_shift: str | None = None
        self._selected = set(view.selected)
        self._saving = False
        self.setWindowTitle(self.text("placements_window").format(job=view.job_id))
        self.setObjectName("jobWorkplaceDialog")
        self.resize(840, 590)
        self.setMinimumSize(720, 500)
        self.setStyleSheet(_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel(self.text("placements_title"))
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        subtitle = QLabel(self.text("placements_job").format(job=view.job_id))
        subtitle.setObjectName("supportingText")
        layout.addWidget(subtitle)
        self.filter_input = QLineEdit()
        self.filter_input.setToolTip(
            "Filter the workplace hierarchy without changing selections."
            if language is Language.ENGLISH
            else "Filtrar la jerarquía sin cambiar las selecciones."
        )
        self.filter_input.setPlaceholderText(self.text("placements_filter"))
        layout.addWidget(self.filter_input)
        shifts = QHBoxLayout()
        shifts.addWidget(QLabel(self.text("placements_shift")))
        self.shift_combo = QComboBox()
        self.shift_combo.setToolTip(self.text("placements_shift_tip"))
        shifts.addWidget(self.shift_combo, 1)
        layout.addLayout(shifts)
        self.workplace_tree = QTreeWidget()
        tree = self.workplace_tree
        tree.setColumnCount(3)
        tree.setHeaderLabels(
            [
                self.text(key)
                for key in (
                    "placements_use",
                    "placements_hierarchy",
                    "placements_level",
                )
            ]
        )
        tree.setRootIsDecorated(True)
        tree.setAlternatingRowColors(True)
        tree.setIconSize(QSize(22, 22))
        tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        header = tree.header()
        assert header is not None
        header.setStretchLastSection(False)
        for column, mode in enumerate(
            (
                QHeaderView.ResizeToContents,
                QHeaderView.Stretch,
                QHeaderView.ResizeToContents,
            )
        ):
            header.setSectionResizeMode(column, mode)
        tree.setToolTip(self.text("placements_tree_tip"))
        layout.addWidget(tree, 1)
        self.assignment_status = QLabel()
        self.assignment_status.setObjectName("supportingText")
        layout.addWidget(self.assignment_status)
        actions = QHBoxLayout()
        self.clear_button = QPushButton(self.text("placements_clear"))
        self.clear_button.setIcon(icons["filter_reset"])
        self.clear_button.setToolTip(self.text("placements_clear_tip"))
        self.save_button = QPushButton(self.text("placements_save"))
        self.save_button.setToolTip(
            "Accept these Job workplaces; the main project Save stores them."
            if language is Language.ENGLISH
            else "Aceptar estos lugares; Guardar en la ventana principal los almacena."
        )
        self.save_button.setObjectName("primaryOutlineButton")
        self.save_button.setIcon(icons["save"])
        self.cancel_button = QPushButton(self.text("cancel"))
        self.cancel_button.setToolTip(
            "Close without accepting placement changes."
            if language is Language.ENGLISH
            else "Cerrar sin aceptar cambios de ubicación."
        )
        self.cancel_button.setIcon(icons["close"])
        actions.addWidget(self.clear_button)
        actions.addStretch(1)
        actions.addWidget(self.save_button)
        actions.addWidget(self.cancel_button)
        layout.addLayout(actions)
        self._populate(icons, preferred_shift)
        # Connect once, after construction. Rendering blocks emissions, so it
        # cannot recursively capture intermediate checkbox states.
        self.filter_input.textChanged.connect(self.apply_filter)
        self.shift_combo.currentTextChanged.connect(self.shift_changed)
        tree.itemChanged.connect(self.selection_changed)
        self.clear_button.clicked.connect(self.clear_assignments)
        self.save_button.clicked.connect(self.save_assignments)
        self.cancel_button.clicked.connect(self.reject)

    def text(self, key: str) -> str:
        """Resolve this dialog's language without mutating names or unit settings.

        Args:
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return desktop_text(key, self.language)

    def _populate(
        self, icons: Mapping[str, QIcon], preferred_shift: str | None
    ) -> None:
        """Build exact station paths and available shifts from the injected view.

        Build exact station paths and available shifts from the injected view, retaining
        a valid remembered shift.

        Args:
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            preferred_shift: Remembered project shift identifier; None selects the
                dialog's available default.

        Returns:
            None.
        """
        nodes: dict[tuple[str, ...], QTreeWidgetItem] = {}
        levels = ("Plant", "Section", "Line", "Station")
        for place in self.view.options:
            path = (
                place.plant_name,
                place.section_name,
                place.line_name,
                place.station_id,
            )
            parent = None
            for depth, value in enumerate(path, 1):
                partial = path[:depth]
                if partial not in nodes:
                    item = QTreeWidgetItem(
                        [
                            "",
                            value,
                            self.text("placements_" + levels[depth - 1].lower()),
                        ]
                    )
                    flags = item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                    if depth < 4:
                        flags |= Qt.ItemFlag.ItemIsAutoTristate
                    item.setFlags(flags)
                    item.setCheckState(0, Qt.CheckState.Unchecked)
                    item.setData(1, Qt.ItemDataRole.UserRole, partial)
                    item.setIcon(1, icons[levels[depth - 1].lower()])
                    item.setToolTip(1, " > ".join(partial))
                    if parent is None:
                        self.workplace_tree.addTopLevelItem(item)
                    else:
                        parent.addChild(item)
                    nodes[partial] = item
                parent = nodes[partial]
            assert parent is not None
            parent.setData(0, Qt.ItemDataRole.UserRole, StationKey(*path))
        self.workplace_tree.collapseAll()
        shifts = sorted({place.shift_id for place in self.view.options})
        self.shift_combo.addItems(shifts)
        selected_shifts = sorted({place.shift_id for place in self._selected})
        if preferred_shift is None and selected_shifts:
            preferred_shift = selected_shifts[0]
        if preferred_shift in shifts:
            self.shift_combo.setCurrentText(preferred_shift)
        self.shift_changed()

    def items(self) -> Iterator[QTreeWidgetItem]:
        """Traverse all nodes, including hidden and collapsed selections.

        Args:
            None.

        Yields:
            Every tree node, including hidden and collapsed nodes, in Qt iterator order.
        """
        iterator = QTreeWidgetItemIterator(self.workplace_tree)
        while (item := iterator.value()) is not None:
            yield item
            iterator += 1

    def _place(self, item: QTreeWidgetItem) -> WorkplaceContext:
        """Resolve the exact station and displayed shift.

        Resolve a station leaf into its exact workplace context at the displayed shift.

        Args:
            item: Borrowed live Qt item carrying typed owner data; the method does not
                take ownership.

        Returns:
            Exact station context combined with the currently displayed shift.
        """
        station = item.data(0, Qt.ItemDataRole.UserRole)
        assert isinstance(station, StationKey)
        assert self._displayed_shift is not None
        return station.at_shift(self._displayed_shift)

    def _checked(self) -> set[WorkplaceContext]:
        """Collect all checked station leaves for the displayed shift.

        Collect all checked station leaves for the displayed shift, including hidden or
        collapsed nodes.

        Args:
            None.

        Returns:
            Exact checked leaf contexts for the displayed shift; empty before a shift is
            selected.
        """
        if self._displayed_shift is None:
            return set()
        return {
            self._place(item)
            for item in self.items()
            if item.childCount() == 0 and item.checkState(0) == Qt.CheckState.Checked
        }

    def _capture(self) -> None:
        """Replace only the displayed shift's local placement intent.

        Replace only the displayed shift's local placement intent from the checked tree
        leaves.

        Args:
            None.

        Returns:
            None.
        """
        if self._displayed_shift is not None:
            self._selected = {
                place
                for place in self._selected
                if place.shift_id != self._displayed_shift
            } | self._checked()

    def _render(self) -> None:
        """Project local selections into leaf checkboxes under signal blocking.

        Project local selections into leaf checkboxes under signal blocking, then
        request one viewport repaint.

        Args:
            None.

        Returns:
            None.
        """
        with QSignalBlocker(self.workplace_tree):
            for item in self.items():
                if item.childCount() == 0:
                    place = self._place(item)
                    item.setCheckState(
                        0,
                        Qt.CheckState.Checked
                        if place in self._selected
                        else Qt.CheckState.Unchecked,
                    )
        viewport = self.workplace_tree.viewport()
        assert viewport is not None
        viewport.update()

    def shift_changed(self) -> None:
        """Capture the old shift before rendering the new selection once.

        Args:
            None.

        Returns:
            None.
        """
        self._capture()
        self._displayed_shift = self.shift_combo.currentText() or None
        if self._displayed_shift is not None:
            self._render()
        self._update_status()

    def selection_changed(self) -> None:
        """Capture checkbox intent without triggering another tree render.

        Args:
            None.

        Returns:
            None.
        """
        self._capture()
        self._update_status()

    def _update_status(self) -> None:
        """Show the displayed shift's checked placement count.

        Show the displayed shift's checked placement count without changing selection.

        Args:
            None.

        Returns:
            None.
        """
        if self._selected:
            self.assignment_status.setText(
                self.text("placements_count").format(
                    current=len(self._checked()),
                    shift=self._displayed_shift,
                    total=len(self._selected),
                )
            )
        else:
            self.assignment_status.setText(self.text("placements_neutral"))

    def apply_filter(self, text: str) -> None:
        """Filter visibility only; hidden checked stations remain selected.

        Args:
            text: Literal control text or user input; interpretation follows this
                method's stated policy.

        Returns:
            None.
        """
        query = text.strip().casefold()

        def visit(item: QTreeWidgetItem | None, ancestor_matches: bool = False) -> bool:
            """Recursively keep matching ancestry/descendants visible.

            Recursively keep matching ancestry/descendants visible and expand matching
            branches; checking state remains unchanged.

            Args:
                item: Borrowed live tree/graphics item carrying typed owner data; None
                    denotes no selection.
                ancestor_matches: True keeps descendants visible because an ancestor
                    matched the text filter.

            Returns:
                True when this node or an ancestor/descendant matches and the node
                should remain visible.
            """
            assert item is not None
            path = item.data(1, Qt.ItemDataRole.UserRole)
            own_match = not query or query in " ".join(path).casefold()
            descendant = False
            for index in range(item.childCount()):
                descendant = (
                    visit(item.child(index), ancestor_matches or own_match)
                    or descendant
                )
            visible = ancestor_matches or own_match or descendant
            item.setHidden(not visible)
            if query and descendant:
                item.setExpanded(True)
            return visible

        for index in range(self.workplace_tree.topLevelItemCount()):
            visit(self.workplace_tree.topLevelItem(index))

    def clear_assignments(self) -> None:
        """Clear the displayed shift, including stations hidden by the filter.

        Args:
            None.

        Returns:
            None.
        """
        if self._displayed_shift is not None:
            self._selected = {
                place
                for place in self._selected
                if place.shift_id != self._displayed_shift
            }
            self._render()
        self._update_status()

    def save_assignments(self) -> None:
        """Persist once, retain local selections on failure and accept on success.

        Args:
            None.

        Returns:
            None.
        """
        if self._saving:
            return
        self._saving = True
        try:
            self._capture()
            self.view = self.presenter.save(self.view, self._selected)
        except Exception as error:
            # UI recovery boundary: repository-specific errors remain below Qt.
            logging.getLogger(__name__).warning(
                "Workplace assignment save failed (%s).", type(error).__name__
            )
            QMessageBox.warning(
                self, self.text("placements_error_title"), self.text("placements_error")
            )
        else:
            self.preferred_shift = self._displayed_shift
            self.accept()
        finally:
            self._saving = False
