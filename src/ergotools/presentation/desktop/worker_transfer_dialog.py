"""Original three-column transfer form over injected saved-data commands.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Mapping
from uuid import uuid4

from PyQt5.QtCore import QSignalBlocker, QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessment_transfer import TransferRequest, plan_transfer
from ergotools.domain.assessments.context import WorkerContext, WorkplaceContext
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.presentation.desktop.theme.worker_transfer import WORKER_TRANSFER_STYLE
from ergotools.presentation.desktop.worker_transfer_text import transfer_text
from ergotools.presentation.worker_options import WorkerOrder, worker_options

# Module-scoped diagnostic logger; adapters log technical failures while views retain
# user input.
_LOG = logging.getLogger(__name__)
# Original transfer tool order, branded captions and packaged icon keys.
TOOLS = {
    AssessmentKind.LIFFT: ("LiFFT", "lifft"),
    AssessmentKind.DUET: ("DUET", "duet"),
    AssessmentKind.TST: ("ST", "shoulder"),
}


class WorkerTransferDialog(QDialog):
    """Own modal selections; no SQL, global window lookup or implicit source save."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        source_assignment_id: int,
        icons: Mapping[str, QIcon],
        resolve_move: Callable[[TransferRequest], CloseChoice | None],
        *,
        language: Language,
        parent: QWidget,
    ) -> None:
        """Receive exact source ownership and an explicit dirty-move resolver.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.
            source_assignment_id: Exact saved source assignment whose selected tool
                versions may be copied/moved.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            resolve_move: Host callback resolving dirty consent for a move affecting the
                active assessment.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        super().__init__(parent)
        self.workspace = workspace
        self.icons = icons
        self.language = language
        self.resolve_move = resolve_move
        self.jobs = workspace.read_jobs()
        self.history = workspace.read_history()
        self.hierarchy = workspace.read_hierarchy().hierarchy
        self.source_assignment_id = source_assignment_id
        self.source_owner = next(
            a.worker
            for a in self.jobs.jobs.assignments
            if a.assignment_id == source_assignment_id
        )
        self.selected_worker_id: str | None = None
        self.selected_station_path: tuple[str, str, str, str] | None = None
        self.active_letter: str | None = None
        self.alphabet_buttons: dict[str, QPushButton] = {}
        self.completed = False
        self.setObjectName("workerTransferDialog")
        self.setWindowTitle(self.text("Transfer Assessment Data"))
        self.resize(1280, 720)
        # The inherited 1080-pixel width clips the fixed alphabet/tree columns.
        self.setMinimumSize(1280, 640)
        self.setStyleSheet(WORKER_TRANSFER_STYLE)
        self._build_ui()
        self.load_data()

    def text(self, english: str) -> str:
        """Localize transfer commands and principal controls independently of units.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return transfer_text(english, self.language)

    @staticmethod
    def header(table: QTableWidget, *, vertical: bool = False) -> QHeaderView:
        """Require Qt's owned header before configuring reference sizing.

        Args:
            table: Owned Qt table to populate or delegate edits for; identity lives in
                item data.
            vertical: True requests the vertical table header; False requests the
                horizontal header.

        Returns:
            Borrowed existing horizontal/vertical Qt header requested by the caller.
        """
        header = table.verticalHeader() if vertical else table.horizontalHeader()
        assert header is not None
        return header

    def panel(
        self,
        title: str,
        supporting: str | None = None,
    ) -> tuple[QFrame, QVBoxLayout]:
        """Create a reference section with unchanged margins and spacing.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            supporting: Optional localized explanatory section text; None omits that
                label.

        Returns:
            Owned source-styled section frame and its vertical layout.
        """
        frame = QFrame()
        frame.setObjectName("transferPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        title_label = QLabel(self.text(title))
        title_label.setObjectName("panelTitle")
        layout.addWidget(title_label)
        if supporting:
            help_label = QLabel(self.text(supporting))
            help_label.setObjectName("supportingText")
            help_label.setWordWrap(True)
            layout.addWidget(help_label)
        return frame, layout

    def _build_ui(self) -> None:
        """Retain original source/operation/destination controls and proportions.

        Args:
            None.

        Returns:
            None.
        """
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)
        title = QLabel(self.text("Transfer assessment data"))
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        subtitle = QLabel(
            self.text(
                "Reuse selected ergonomic assessments for another w"
                "orker, workplace, or shift."
            )
        )
        subtitle.setObjectName("supportingText")
        root.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setSpacing(12)
        source_panel, source_layout = self.panel(
            "1. Source",
            "The active worker and workplace in the main window"
            " are used as the source.",
        )
        source_panel.setMinimumWidth(275)
        source_panel.setMaximumWidth(320)
        source_worker_row = QHBoxLayout()
        worker_icon = QLabel()
        worker_icon.setPixmap(self.icons["worker"].pixmap(QSize(28, 28)))
        source_worker_row.addWidget(worker_icon)
        self.source_worker_label = QLabel()
        self.source_worker_label.setObjectName("sourceWorker")
        self.source_worker_label.setWordWrap(True)
        source_worker_row.addWidget(self.source_worker_label, 1)
        source_layout.addLayout(source_worker_row)
        self.source_path_label = QLabel()
        self.source_path_label.setObjectName("contextPath")
        self.source_path_label.setWordWrap(True)
        source_layout.addWidget(self.source_path_label)
        source_layout.addSpacing(6)
        available_label = QLabel(self.text("Available tools"))
        available_label.setObjectName("panelTitle")
        source_layout.addWidget(available_label)
        self.tool_table = QTableWidget(0, 2)
        self.tool_table.setHorizontalHeaderLabels(["Include", "Assessment tool"])
        self.header(self.tool_table, vertical=True).hide()
        self.tool_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.tool_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.header(self.tool_table).setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.header(self.tool_table).setSectionResizeMode(1, QHeaderView.Stretch)
        self.tool_table.setToolTip(
            self.text("Select the assessment tools to copy or move.")
        )
        source_layout.addWidget(self.tool_table, 1)
        self.empty_tools_label = QLabel(
            self.text(
                "No saved assessment data exists for this worker and workplace.\n\n"
                "Return to the main window and select a source cont"
                "ext that contains tool data."
            )
        )
        self.empty_tools_label.setObjectName("emptyTools")
        self.empty_tools_label.setWordWrap(True)
        self.empty_tools_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_tools_label.hide()
        source_layout.addWidget(self.empty_tools_label, 1)
        columns.addWidget(source_panel)

        operation_panel, operation_layout = self.panel(
            "2. Operation",
            "Copy keeps the source data. Move removes it after "
            "the destination is created.",
        )
        operation_panel.setMinimumWidth(220)
        operation_panel.setMaximumWidth(255)
        self.copy_radio = QRadioButton(self.text("Copy data"))
        self.move_radio = QRadioButton(self.text("Move data"))
        self.copy_radio.setChecked(True)
        self.copy_radio.setToolTip(
            self.text(
                "Create the selected assessments at the destination "
                "and keep the originals."
            )
        )
        self.move_radio.setToolTip(
            self.text(
                "Create the selected assessments at the destination"
                " and remove the originals."
            )
        )
        operation_group = QButtonGroup(self)
        operation_group.addButton(self.copy_radio)
        operation_group.addButton(self.move_radio)
        operation_layout.addWidget(self.copy_radio)
        operation_layout.addWidget(self.move_radio)
        operation_layout.addStretch(1)
        operation_note = QLabel(
            self.text(
                "Move is completed as one database transaction. If "
                "any selected destination conflicts, nothing is cha"
                "nged."
            )
        )
        operation_note.setObjectName("supportingText")
        operation_note.setWordWrap(True)
        operation_layout.addWidget(operation_note)
        columns.addWidget(operation_panel)

        destination_panel, destination_layout = self.panel(
            "3. Destination",
            "Choose a worker, then select the station and shift"
            " that should receive the assessment.",
        )
        search_row = QHBoxLayout()
        self.worker_search = QLineEdit()
        self.worker_search.setPlaceholderText("Search worker ID or name")
        self.worker_search.setClearButtonEnabled(True)
        self.worker_search.addAction(self.icons["search"], QLineEdit.LeadingPosition)
        self.worker_search.setToolTip(
            self.text("Filter destination workers while typing.")
        )
        self.worker_search.textChanged.connect(self.filter_workers)
        search_row.addWidget(self.worker_search)
        destination_layout.addLayout(search_row)
        alphabet = QHBoxLayout()
        alphabet.setSpacing(0)
        alphabet.addWidget(QLabel(self.text("Last name")))
        alphabet.addSpacing(5)
        self.alphabet_group = QButtonGroup(self)
        self.alphabet_group.setExclusive(True)
        for value in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(self.text(value))
            if value == "All" and self.language is Language.SPANISH:
                button.setStyleSheet("min-width: 34px; max-width: 34px;")
            button.setObjectName("alphabetButton")
            button.setCheckable(True)
            button.setChecked(value == "All")
            button.setToolTip(
                self.text("Show all workers")
                if value == "All"
                else self.text("Show last names beginning with {letter}").format(
                    letter=value
                )
            )
            button.clicked.connect(
                lambda checked, letter=value: self.set_alphabet(letter)
            )
            self.alphabet_group.addButton(button)
            self.alphabet_buttons[value] = button
            alphabet.addWidget(button)
        alphabet.addStretch(1)
        destination_layout.addLayout(alphabet)

        destination_split = QHBoxLayout()
        self.worker_table = QTableWidget(0, 3)
        self.worker_table.setHorizontalHeaderLabels(
            ["Worker ID", "Last name", "First name"]
        )
        self.header(self.worker_table, vertical=True).hide()
        self.worker_table.setAlternatingRowColors(True)
        self.worker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.worker_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.worker_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.header(self.worker_table).setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.header(self.worker_table).setSectionResizeMode(1, QHeaderView.Stretch)
        self.header(self.worker_table).setSectionResizeMode(2, QHeaderView.Stretch)
        self.worker_table.itemSelectionChanged.connect(self.worker_selection_changed)
        self.worker_table.setToolTip(
            self.text("Select the worker who should receive the assessment data.")
        )
        destination_split.addWidget(self.worker_table, 1)

        workplace_column = QVBoxLayout()
        workplace_label = QLabel(self.text("Workplace and shift"))
        workplace_label.setObjectName("panelTitle")
        workplace_column.addWidget(workplace_label)
        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderLabels(["Workplace hierarchy", "Type"])
        tree_header = self.workplace_tree.header()
        assert tree_header is not None
        tree_header.setSectionResizeMode(0, QHeaderView.Fixed)
        tree_header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.workplace_tree.setColumnWidth(0, 218)
        self.workplace_tree.setColumnWidth(1, 72)
        self.workplace_tree.setAlternatingRowColors(True)
        self.workplace_tree.currentItemChanged.connect(self.workplace_selection_changed)
        self.workplace_tree.setToolTip(
            self.text("Expand the hierarchy and select the destination station.")
        )
        workplace_column.addWidget(self.workplace_tree, 1)
        shift_row = QHBoxLayout()
        shift_icon = QLabel()
        shift_icon.setPixmap(self.icons["shift"].pixmap(QSize(22, 22)))
        shift_row.addWidget(shift_icon)
        shift_row.addWidget(QLabel(self.text("Shift")))
        self.shift_combo = QComboBox()
        self.shift_combo.setToolTip(self.text("Select the destination work shift."))
        self.shift_combo.currentTextChanged.connect(self.update_preview)
        shift_row.addWidget(self.shift_combo, 1)
        workplace_column.addLayout(shift_row)
        destination_split.addLayout(workplace_column, 1)
        destination_layout.addLayout(destination_split, 1)
        columns.addWidget(destination_panel, 1)
        root.addLayout(columns, 1)

        self.preview_label = QLabel()
        self.preview_label.setObjectName("previewBox")
        self.preview_label.setWordWrap(True)
        root.addWidget(self.preview_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        cancel = buttons.button(QDialogButtonBox.Cancel)
        assert cancel is not None
        cancel.setText("&" + self.text("Cancel"))
        cancel.setIcon(self.icons["cancel"])
        cancel.setIconSize(QSize(22, 22))
        cancel.setToolTip(self.text("Close without changing assessment data."))
        transfer_button = buttons.button(QDialogButtonBox.Ok)
        assert transfer_button is not None
        self.transfer_button = transfer_button
        self.transfer_button.setText(self.text("Transfer selected tools"))
        self.transfer_button.setObjectName("primaryButton")
        self.transfer_button.setIcon(self.icons["transfer_worker_data_light"])
        self.transfer_button.setIconSize(QSize(26, 26))
        self.transfer_button.setToolTip(
            self.text("Perform the selected copy or move operation.")
        )
        self.buttons = buttons
        buttons.accepted.connect(self.perform_transfer)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.copy_radio.toggled.connect(self.update_preview)
        self.move_radio.toggled.connect(self.update_preview)

    def load_data(self) -> None:
        """Populate saved worker/hierarchy/current-source selections without edits.

        Args:
            None.

        Returns:
            None.
        """
        owner = self.source_owner
        place = owner.workplace
        self.source_worker_label.setText(
            next(
                option.label
                for option in worker_options(self.hierarchy.work, WorkerOrder.ID)
                if option.worker_id == owner.worker_id
            )
        )
        self.source_path_label.setText(
            "\n".join(
                f"{self.text(label)}: {value}"
                for label, value in zip(
                    ("Plant", "Section", "Line", "Station", "Shift"),
                    (
                        place.plant_name,
                        place.section_name,
                        place.line_name,
                        place.station_id,
                        place.shift_id,
                    ),
                    strict=True,
                )
            )
        )
        available = [
            kind
            for kind in TOOLS
            if self.history.history.current_for(self.source_assignment_id, kind)
            is not None
        ]
        available.sort(key=lambda kind: TOOLS[kind][0])
        self.tool_table.setRowCount(len(available))
        for row, kind in enumerate(available):
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            title = {
                AssessmentKind.LIFFT: "Lifting Fatigue Failure Tool",
                AssessmentKind.DUET: "Distal Upper Extremity Tool",
                AssessmentKind.TST: "Shoulder Tool",
            }[kind]
            title = self.text(title)
            checkbox.setToolTip(
                self.text("Include {tool} in this operation.").format(tool=title)
            )
            checkbox.stateChanged.connect(self.update_preview)
            holder = QWidget()
            layout = QHBoxLayout(holder)
            layout.setContentsMargins(10, 0, 0, 0)
            layout.addWidget(checkbox)
            layout.addStretch(1)
            self.tool_table.setCellWidget(row, 0, holder)
            label, icon = TOOLS[kind]
            item = QTableWidgetItem(self.icons[icon], label)
            item.setData(Qt.ItemDataRole.UserRole, kind)
            item.setToolTip(title)
            self.tool_table.setItem(row, 1, item)
            self.tool_table.setRowHeight(row, 44)
        self.tool_table.setVisible(bool(available))
        self.empty_tools_label.setVisible(not available)
        nodes: dict[tuple[str, ...], QTreeWidgetItem] = {}
        paths = (
            [(p,) for p in self.hierarchy.plants]
            + [(s.plant_name, s.section_name) for s in self.hierarchy.sections]
            + [
                (line.plant_name, line.section_name, line.line_name)
                for line in self.hierarchy.lines
            ]
            + [
                (s.plant_name, s.section_name, s.line_name, s.station_id)
                for s in self.hierarchy.work.stations
            ]
        )
        for path in paths:
            node = QTreeWidgetItem(
                [
                    path[-1],
                    self.text(("Plant", "Section", "Line", "Station")[len(path) - 1]),
                ]
            )
            node.setData(0, Qt.ItemDataRole.UserRole, path)
            node.setToolTip(0, f"{node.text(1)}: {path[-1]}")
            icon = ("plant", "section", "line", "station")[len(path) - 1]
            node.setIcon(0, self.icons[icon])
            if len(path) == 1:
                self.workplace_tree.addTopLevelItem(node)
            else:
                nodes[path[:-1]].addChild(node)
            nodes[path] = node
        self.workplace_tree.collapseAll()
        self.shift_combo.addItems(list(self.hierarchy.work.shifts))
        self.worker_search.setPlaceholderText(self.text("Search worker ID or name"))
        self.tool_table.setHorizontalHeaderLabels(
            [self.text("Include"), self.text("Assessment tool")]
        )
        self.worker_table.setHorizontalHeaderLabels(
            [self.text("Worker ID"), self.text("Last name"), self.text("First name")]
        )
        self.workplace_tree.setHeaderLabels(
            [self.text("Workplace hierarchy"), self.text("Type")]
        )
        initials = {
            (w.last_name or "")[:1].upper() for w in self.hierarchy.work.workers
        }
        for letter, button in self.alphabet_buttons.items():
            button.setEnabled(letter == "All" or letter in initials)
        self.filter_workers()
        for row in range(self.worker_table.rowCount()):
            candidate = self.worker_table.item(row, 0)
            if (
                candidate is not None
                and candidate.data(Qt.ItemDataRole.UserRole) != owner.worker_id
            ):
                self.worker_table.selectRow(row)
                break
        station = (
            place.plant_name,
            place.section_name,
            place.line_name,
            place.station_id,
        )
        if station in nodes:
            self.workplace_tree.setCurrentItem(nodes[station])
            ancestor = nodes[station].parent()
            while ancestor is not None:
                ancestor.setExpanded(True)
                ancestor = ancestor.parent()
        self.shift_combo.setCurrentText(place.shift_id)
        self.update_preview()

    def set_alphabet(self, letter: str) -> None:
        """Apply the original last-name filter without retaining hidden selection.

        Args:
            letter: Surname initial filter, or the reference All sentinel to remove that
                filter.

        Returns:
            None.
        """
        self.active_letter = None if letter == "All" else letter
        self.filter_workers()

    def filter_workers(self, *_: object) -> None:
        """Filter identifiers/names while preserving exact item identity.

        Args:
            _: Unused Qt signal payloads; current controls supply the operation's
                complete state.

        Returns:
            None.
        """
        query = self.worker_search.text().strip().casefold()
        rows = [
            worker
            for worker in self.hierarchy.work.workers
            if (
                not query
                or query
                in " ".join(
                    (worker.worker_id, worker.first_name or "", worker.last_name or "")
                ).casefold()
            )
            and (
                not self.active_letter
                or (worker.last_name or "").upper().startswith(self.active_letter)
            )
        ]
        rows.sort(
            key=lambda w: (
                (w.last_name or "").casefold(),
                (w.first_name or "").casefold(),
                w.worker_id,
            )
        )
        blocker = QSignalBlocker(self.worker_table)
        self.worker_table.setRowCount(len(rows))
        for row, worker in enumerate(rows):
            for column, value in enumerate(
                (worker.worker_id, worker.last_name or "-", worker.first_name or "-")
            ):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, worker.worker_id)
                item.setToolTip(value)
                self.worker_table.setItem(row, column, item)
            self.worker_table.setRowHeight(row, 34)
        self.worker_table.clearSelection()
        del blocker
        self.selected_worker_id = None
        self.update_preview()

    def worker_selection_changed(self) -> None:
        """Resolve a selected destination from item data, never displayed names.

        Args:
            None.

        Returns:
            None.
        """
        items = self.worker_table.selectedItems()
        self.selected_worker_id = (
            items[0].data(Qt.ItemDataRole.UserRole) if items else None
        )
        self.update_preview()

    def workplace_selection_changed(
        self,
        item: QTreeWidgetItem | None,
        previous: QTreeWidgetItem | None = None,
    ) -> None:
        """Only a station establishes a complete destination workplace.

        Args:
            item: Borrowed live tree/graphics item carrying typed owner data; None
                denotes no selection.
            previous: Previously selected Qt tree item; ignored when deriving the new
                exact context.

        Returns:
            None.
        """
        path = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        self.selected_station_path = (
            (path[0], path[1], path[2], path[3])
            if isinstance(path, tuple) and len(path) == 4
            else None
        )
        self.update_preview()

    def selected_tools(self) -> tuple[AssessmentKind, ...]:
        """Return selected typed tool identities in reference tool order.

        Args:
            None.

        Returns:
            Checked typed tool identities in original LiFFT/DUET/ST order.
        """
        tools = []
        for row in range(self.tool_table.rowCount()):
            holder = self.tool_table.cellWidget(row, 0)
            item = self.tool_table.item(row, 1)
            checkbox = holder.findChild(QCheckBox) if holder is not None else None
            if checkbox is not None and checkbox.isChecked() and item is not None:
                tools.append(AssessmentKind(item.data(Qt.ItemDataRole.UserRole)))
        return tuple(tools)

    def request(self) -> TransferRequest | None:
        """Build complete exact context; incomplete controls have no request.

        Args:
            None.

        Returns:
            Complete exact copy/move request, or None while destination/tool selection
            is incomplete.
        """
        if (
            self.selected_worker_id is None
            or self.selected_station_path is None
            or not self.shift_combo.currentText()
        ):
            return None
        destination = WorkerContext(
            self.source_owner.project_id,
            self.selected_worker_id,
            WorkplaceContext(
                *self.selected_station_path, self.shift_combo.currentText()
            ),
        )
        return TransferRequest(
            self.source_assignment_id,
            destination,
            self.selected_tools(),
            self.move_radio.isChecked(),
        )

    def update_preview(self, *_: object) -> None:
        """Keep original preview/button interlocks in sync, without recursion.

        Args:
            _: Unused Qt signal payloads; current controls supply the operation's
                complete state.

        Returns:
            None.
        """
        if not hasattr(self, "transfer_button"):
            return
        request = self.request()
        valid = bool(
            request and request.kinds and request.destination != self.source_owner
        )
        self.transfer_button.setEnabled(valid)
        kinds = self.selected_tools()
        if not kinds:
            message = self.text("Select at least one available assessment tool.")
        elif self.selected_worker_id is None:
            message = self.text("Select a destination worker.")
        elif request is None:
            message = self.text(
                "Select a destination station from the workplace hierarchy."
            )
        else:
            mode = self.text("Move" if request.move else "Copy")
            place = request.destination.workplace
            path = " > ".join(
                (
                    place.plant_name,
                    place.section_name,
                    place.line_name,
                    place.station_id,
                )
            )
            template = self.text(
                "{mode} {count} selected tools to {worker} at {path}, shift {shift}."
            )
            message = template.format(
                mode=mode,
                count=len(kinds),
                worker=request.destination.worker_id,
                path=path,
                shift=place.shift_id,
            )
        self.preview_label.setText(self.text("Transfer preview: ") + message)

    def perform_transfer(self) -> None:
        """Confirm and execute one atomic selection; failures retain the owned form.

        Args:
            None.

        Returns:
            None.
        """
        request = self.request()
        if request is None or not request.kinds:
            return
        identities = {kind: uuid4().hex for kind in request.kinds}
        try:
            plan_transfer(
                self.hierarchy.work,
                self.jobs.jobs,
                self.history.history,
                request,
                identities,
            )
        except (ValueError, KeyError) as error:
            _LOG.info("Assessment transfer rejected: %s", error)
            message = str(error)
            if self.language is Language.SPANISH and self.text(message) == message:
                message = (
                    "The selected data could not be transferred. "
                    "Reopen the form and check the destination."
                )
            self.show_warning(self.text(message))
            return
        if not self.confirm_transfer():
            return
        try:
            choice = self.resolve_move(request) if request.move else None
            # Accepted input may refresh main navigation. Reissue modal catalog
            # snapshots after the explicit dirty resolver, before the transaction.
            self.jobs = self.workspace.read_jobs()
            self.history = self.workspace.read_history()
            outcome = self.workspace.transfer_assessments(
                self.jobs, self.history, request, identities, choice=choice
            )
        except Exception:
            _LOG.exception("Assessment transfer failed")
            self.show_failure()
            return
        if outcome.completed:
            self.completed = True
            self.show_success()
            self.accept()

    def confirm_transfer(self) -> bool:
        """Ask explicit consent with owned translated buttons and No as default.

        Args:
            None.

        Returns:
            True only for explicit Yes to the displayed complete transfer preview.
        """
        return bool(
            self._message(
                QMessageBox.Question,
                "Confirm transfer",
                self.preview_label.text(),
                confirm=True,
            )
            == QMessageBox.Yes
        )

    def show_warning(self, message: str) -> None:
        """Report a rejected selection with no transfer writes.

        Args:
            message: Literal user-facing notification/error content.

        Returns:
            None.
        """
        self._message(QMessageBox.Warning, "Transfer failed", message)

    def show_failure(self) -> None:
        """Report a logged execution failure while retaining the form.

        Args:
            None.

        Returns:
            None.
        """
        self._message(
            QMessageBox.Critical, "Transfer failed", self.text("Transfer failed")
        )

    def show_success(self) -> None:
        """Acknowledge the completed transaction before accepting the form.

        Args:
            None.

        Returns:
            None.
        """
        self._message(
            QMessageBox.Information, "Transfer complete", self.text("Transfer complete")
        )

    def _message(
        self, icon: QMessageBox.Icon, title: str, message: str, *, confirm: bool = False
    ) -> int:
        """Execute an owned localized message dialog and release its Qt resources.

        Execute an owned localized message dialog and release its Qt resources after the
        user responds.

        Args:
            icon: Qt message severity icon.
            title: Localized message/window title; never used as a stored identifier.
            message: Literal user-facing notification/error content.
            confirm: True presents explicit Yes/No consent with No as the safe default.

        Returns:
            Qt standard-button/result integer chosen by the user; the temporary message
            instance is released.
        """
        dialog = QMessageBox(icon, self.text(title), message, parent=self)
        dialog.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No if confirm else QMessageBox.Ok
        )
        spanish = self.language is Language.SPANISH
        for role, english, translated in (
            (QMessageBox.Yes, "Yes", "Sí"),
            (QMessageBox.No, "No", "No"),
            (QMessageBox.Ok, "OK", "Aceptar"),
        ):
            button = dialog.button(role)
            if button is not None:
                button.setText("&" + (translated if spanish else english))
        if confirm:
            dialog.setDefaultButton(QMessageBox.No)
            dialog.setEscapeButton(QMessageBox.No)
        try:
            return dialog.exec_()
        finally:
            dialog.close()
            dialog.deleteLater()
