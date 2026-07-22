import os
import sqlite3

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QRadioButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)


class WorkerTransferDialog(QDialog):
    """Copy or move selected tool assessments to a worker and workplace."""

    TOOL_METADATA = {
        "LiFFT": ("Lifting Fatigue Failure Tool", "lifft.png", "LifftResults"),
        "DUET": ("Distal Upper Extremity Tool", "duet.png", "DuetResults"),
        "ST": ("Shoulder Tool", "shoulder.png", "TstResults"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.database_path = parent.projectdatabasePath
        self.icon_root = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "assets", "ui-icons"
        ))
        self.source_key = self.currentSourceKey()
        self.workers = []
        self.selected_worker_id = None
        self.selected_station_path = None
        self.active_letter = None
        self.alphabet_buttons = {}
        self.setObjectName("workerTransferDialog")
        self.setWindowTitle("Transfer Assessment Data")
        self.resize(1280, 720)
        self.setMinimumSize(1080, 640)
        self.setStyleSheet(self.styleSheetText())
        self.buildUi()
        self.loadData()

    def styleSheetText(self):
        return """
            QDialog#workerTransferDialog { background: #F4F7F9; color: #1B2933; font: 12px "Segoe UI"; }
            QFrame#transferPanel { background: white; border: 1px solid #D5DEE5; border-radius: 7px; }
            QLabel#dialogTitle { color: #0B326C; font-size: 20px; font-weight: 700; }
            QLabel#panelTitle { color: #0B326C; font-size: 14px; font-weight: 700; }
            QLabel#supportingText { color: #405462; font-size: 12px; }
            QLabel#sourceWorker { color: #0B326C; font-size: 16px; font-weight: 700; }
            QLabel#contextPath { color: #405462; font-weight: 600; }
            QLabel#previewBox { background: #EAF7F8; color: #164655; border: 1px solid #B6DDE1; border-radius: 5px; padding: 9px; }
            QLabel#emptyTools { background: #F4F7F9; color: #5F6F7A; border: 1px solid #D5DEE5; border-radius: 5px; padding: 14px; font-weight: 600; }
            QLineEdit, QComboBox { min-height: 32px; background: white; border: 1px solid #BCC9D3; border-radius: 5px; padding: 0 8px; }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #08A9B5; }
            QComboBox QAbstractItemView { background: white; color: #1B2933; selection-background-color: #087E91; selection-color: white; }
            QTableWidget, QTreeWidget { background: white; color: #1B2933; border: 1px solid #BCC9D3; border-radius: 5px; alternate-background-color: #F7FAFB; gridline-color: #E3E9ED; }
            QTableWidget::item:selected, QTreeWidget::item:selected { background: #087E91; color: white; }
            QTreeWidget::item { min-height: 29px; padding: 2px 4px; }
            QHeaderView::section { background: #EAF2F6; color: #0B326C; border: 0; border-bottom: 1px solid #BCC9D3; padding: 7px 5px; font-weight: 700; }
            QPushButton { min-height: 34px; background: white; color: #0B326C; border: 1px solid #9EB0BE; border-radius: 5px; padding: 0 12px; font-weight: 650; }
            QPushButton:hover { background: #EDF7F8; border-color: #08A9B5; }
            QPushButton#primaryButton { background: #087E91; color: white; border: 1px solid #087E91; }
            QPushButton#primaryButton:hover { background: #096D7C; }
            QPushButton#primaryButton:disabled { background: #DCE4E9; color: #8796A0; border-color: #C7D1D8; }
            QPushButton#alphabetButton { min-width: 20px; max-width: 20px; min-height: 29px; max-height: 29px; padding: 0; border: 0; background: transparent; color: #5F6F7A; font-size: 10px; }
            QPushButton#alphabetButton:hover { background: #DDF3F5; color: #0B326C; font-size: 15px; }
            QPushButton#alphabetButton:checked { background: #0B326C; color: white; border-radius: 4px; font-weight: 700; }
            QPushButton#alphabetButton:disabled { color: #CBD4DA; }
            QRadioButton { min-height: 38px; padding: 0 10px; color: #0B326C; font-weight: 700; border: 1px solid #BCC9D3; border-radius: 5px; background: white; }
            QRadioButton:checked { color: white; background: #0B326C; border-color: #0B326C; }
            QRadioButton { spacing: 0; }
            QRadioButton::indicator { image: none; width: 0; height: 0; }
            QCheckBox { color: #1B2933; font-weight: 600; spacing: 8px; }
            QCheckBox::indicator { width: 17px; height: 17px; }
            QToolTip { background: #1B2933; color: white; border: 1px solid #0B326C; padding: 6px; }
        """

    def currentSourceKey(self):
        worker_text = self.main_window.workerComboBox.currentText()
        return (
            worker_text.split(" ", 1)[0] if worker_text else "",
            self.main_window.plant_combo.currentText().strip(),
            self.main_window.section_combo.currentText().strip(),
            self.main_window.line_combo.currentText().strip(),
            self.main_window.station_combo.currentText().strip(),
            self.main_window.shift_combo.currentText().strip(),
        )

    def panel(self, title, supporting=None):
        frame = QFrame()
        frame.setObjectName("transferPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        layout.addWidget(title_label)
        if supporting:
            help_label = QLabel(supporting)
            help_label.setObjectName("supportingText")
            help_label.setWordWrap(True)
            layout.addWidget(help_label)
        return frame, layout

    def buildUi(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)
        title = QLabel("Transfer assessment data")
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        subtitle = QLabel("Reuse selected ergonomic assessments for another worker, workplace, or shift.")
        subtitle.setObjectName("supportingText")
        root.addWidget(subtitle)

        columns = QHBoxLayout()
        columns.setSpacing(12)
        source_panel, source_layout = self.panel(
            "1. Source", "The active worker and workplace in the main window are used as the source."
        )
        source_panel.setMinimumWidth(275)
        source_panel.setMaximumWidth(320)
        source_worker_row = QHBoxLayout()
        worker_icon = QLabel()
        worker_icon.setPixmap(QIcon(os.path.join(self.icon_root, "worker.png")).pixmap(QSize(28, 28)))
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
        available_label = QLabel("Available tools")
        available_label.setObjectName("panelTitle")
        source_layout.addWidget(available_label)
        self.tool_table = QTableWidget(0, 2)
        self.tool_table.setHorizontalHeaderLabels(["Include", "Assessment tool"])
        self.tool_table.verticalHeader().hide()
        self.tool_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.tool_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tool_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tool_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tool_table.setToolTip("Select the assessment tools to copy or move.")
        source_layout.addWidget(self.tool_table, 1)
        self.empty_tools_label = QLabel(
            "No saved assessment data exists for this worker and workplace.\n\n"
            "Return to the main window and select a source context that contains tool data."
        )
        self.empty_tools_label.setObjectName("emptyTools")
        self.empty_tools_label.setWordWrap(True)
        self.empty_tools_label.setAlignment(Qt.AlignCenter)
        self.empty_tools_label.hide()
        source_layout.addWidget(self.empty_tools_label, 1)
        columns.addWidget(source_panel)

        operation_panel, operation_layout = self.panel(
            "2. Operation", "Copy keeps the source data. Move removes it after the destination is created."
        )
        operation_panel.setMinimumWidth(220)
        operation_panel.setMaximumWidth(255)
        self.copy_radio = QRadioButton("Copy data")
        self.move_radio = QRadioButton("Move data")
        self.copy_radio.setChecked(True)
        self.copy_radio.setToolTip("Create the selected assessments at the destination and keep the originals.")
        self.move_radio.setToolTip("Create the selected assessments at the destination and remove the originals.")
        operation_group = QButtonGroup(self)
        operation_group.addButton(self.copy_radio)
        operation_group.addButton(self.move_radio)
        operation_layout.addWidget(self.copy_radio)
        operation_layout.addWidget(self.move_radio)
        operation_layout.addStretch(1)
        operation_note = QLabel("Move is completed as one database transaction. If any selected destination conflicts, nothing is changed.")
        operation_note.setObjectName("supportingText")
        operation_note.setWordWrap(True)
        operation_layout.addWidget(operation_note)
        columns.addWidget(operation_panel)

        destination_panel, destination_layout = self.panel(
            "3. Destination", "Choose a worker, then select the station and shift that should receive the assessment."
        )
        search_row = QHBoxLayout()
        self.worker_search = QLineEdit()
        self.worker_search.setPlaceholderText("Search worker ID or name")
        self.worker_search.setClearButtonEnabled(True)
        self.worker_search.addAction(QIcon(os.path.join(self.icon_root, "search.png")), QLineEdit.LeadingPosition)
        self.worker_search.setToolTip("Filter destination workers while typing.")
        self.worker_search.textChanged.connect(self.filterWorkers)
        search_row.addWidget(self.worker_search)
        destination_layout.addLayout(search_row)
        alphabet = QHBoxLayout()
        alphabet.setSpacing(0)
        alphabet.addWidget(QLabel("Last name"))
        alphabet.addSpacing(5)
        self.alphabet_group = QButtonGroup(self)
        self.alphabet_group.setExclusive(True)
        for value in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(value)
            button.setObjectName("alphabetButton")
            button.setCheckable(True)
            button.setChecked(value == "All")
            button.setToolTip("Show all workers" if value == "All" else f"Show last names beginning with {value}")
            button.clicked.connect(lambda checked, letter=value: self.setAlphabet(letter))
            self.alphabet_group.addButton(button)
            self.alphabet_buttons[value] = button
            alphabet.addWidget(button)
        alphabet.addStretch(1)
        destination_layout.addLayout(alphabet)

        destination_split = QHBoxLayout()
        self.worker_table = QTableWidget(0, 3)
        self.worker_table.setHorizontalHeaderLabels(["Worker ID", "Last name", "First name"])
        self.worker_table.verticalHeader().hide()
        self.worker_table.setAlternatingRowColors(True)
        self.worker_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.worker_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.worker_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.worker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.worker_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.worker_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.worker_table.itemSelectionChanged.connect(self.workerSelectionChanged)
        self.worker_table.setToolTip("Select the worker who should receive the assessment data.")
        destination_split.addWidget(self.worker_table, 1)

        workplace_column = QVBoxLayout()
        workplace_label = QLabel("Workplace and shift")
        workplace_label.setObjectName("panelTitle")
        workplace_column.addWidget(workplace_label)
        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderLabels(["Workplace hierarchy", "Type"])
        self.workplace_tree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        self.workplace_tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.workplace_tree.setColumnWidth(0, 218)
        self.workplace_tree.setColumnWidth(1, 72)
        self.workplace_tree.setAlternatingRowColors(True)
        self.workplace_tree.currentItemChanged.connect(self.workplaceSelectionChanged)
        self.workplace_tree.setToolTip("Expand the hierarchy and select the destination station.")
        workplace_column.addWidget(self.workplace_tree, 1)
        shift_row = QHBoxLayout()
        shift_icon = QLabel()
        shift_icon.setPixmap(QIcon(os.path.join(self.icon_root, "shift.png")).pixmap(QSize(22, 22)))
        shift_row.addWidget(shift_icon)
        shift_row.addWidget(QLabel("Shift"))
        self.shift_combo = QComboBox()
        self.shift_combo.setToolTip("Select the destination work shift.")
        self.shift_combo.currentTextChanged.connect(self.updatePreview)
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
        cancel.setIcon(QIcon(os.path.join(self.icon_root, "cancel.png")))
        cancel.setIconSize(QSize(22, 22))
        cancel.setToolTip("Close without changing assessment data.")
        self.transfer_button = buttons.button(QDialogButtonBox.Ok)
        self.transfer_button.setText("Transfer selected tools")
        self.transfer_button.setObjectName("primaryButton")
        self.transfer_button.setIcon(QIcon(os.path.join(self.icon_root, "transferworkerdata-light.png")))
        self.transfer_button.setIconSize(QSize(26, 26))
        self.transfer_button.setToolTip("Perform the selected copy or move operation.")
        buttons.accepted.connect(self.performTransfer)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self.copy_radio.toggled.connect(self.updatePreview)
        self.move_radio.toggled.connect(self.updatePreview)

    def loadData(self):
        with sqlite3.connect(self.database_path) as conn:
            self.workers = [tuple("" if value is None else str(value) for value in row) for row in conn.execute(
                "SELECT id, last_name, first_name FROM Worker ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE, id"
            )]
            self.populateWorkplaceTree(conn)
            self.shift_combo.addItems([str(row[0]) for row in conn.execute("SELECT id FROM Shift ORDER BY id")])
            available = [row[0] for row in conn.execute(
                """SELECT tool_id FROM WorkerStationShiftErgoTool
                   WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=?
                   AND station_id=? AND shift_id=? ORDER BY tool_id""", self.source_key
            )]
        source_worker = self.main_window.workerComboBox.currentText() or self.source_key[0]
        self.source_worker_label.setText(source_worker)
        self.source_path_label.setText(
            "Plant: {}\nSection: {}\nLine: {}\nStation: {}\nShift: {}".format(*self.source_key[1:])
        )
        self.populateTools(available)
        initials = {row[1][:1].upper() for row in self.workers if row[1] and row[1][0].isalpha()}
        for value, button in self.alphabet_buttons.items():
            button.setEnabled(value == "All" or value in initials)
        self.filterWorkers()
        self.selectInitialDestination()
        self.updatePreview()

    def populateTools(self, available):
        self.tool_table.setRowCount(len(available))
        for row, tool_id in enumerate(available):
            metadata = self.TOOL_METADATA.get(tool_id, (tool_id, "transferworkerdata.png", ""))
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.setToolTip(f"Include {metadata[0]} in this operation.")
            checkbox.stateChanged.connect(self.updatePreview)
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(10, 0, 0, 0)
            holder_layout.addWidget(checkbox)
            holder_layout.addStretch(1)
            self.tool_table.setCellWidget(row, 0, holder)
            item = QTableWidgetItem(QIcon(os.path.join(self.icon_root, metadata[1])), tool_id)
            item.setData(Qt.UserRole, tool_id)
            item.setToolTip(metadata[0])
            self.tool_table.setItem(row, 1, item)
            self.tool_table.setRowHeight(row, 44)
        if not available:
            self.tool_table.hide()
            self.empty_tools_label.show()

    def populateWorkplaceTree(self, conn):
        for (plant,) in conn.execute("SELECT name FROM Plant ORDER BY name COLLATE NOCASE"):
            plant_item = self.addTreeItem(None, plant, "Plant", (plant,))
            for (section,) in conn.execute(
                "SELECT name FROM Section WHERE plant_name=? ORDER BY name COLLATE NOCASE", (plant,)
            ):
                section_item = self.addTreeItem(plant_item, section, "Section", (plant, section))
                for (line,) in conn.execute(
                    "SELECT name FROM Line WHERE plant_name=? AND section_name=? ORDER BY name COLLATE NOCASE",
                    (plant, section),
                ):
                    line_item = self.addTreeItem(section_item, line, "Line", (plant, section, line))
                    for (station,) in conn.execute(
                        """SELECT id FROM Station WHERE plant_name=? AND section_name=? AND line_name=?
                           ORDER BY id COLLATE NOCASE""", (plant, section, line)
                    ):
                        self.addTreeItem(line_item, station, "Station", (plant, section, line, station))
        self.workplace_tree.collapseAll()

    def addTreeItem(self, parent, text, entity, path):
        item = QTreeWidgetItem([str(text), entity])
        item.setData(0, Qt.UserRole, tuple(str(value) for value in path))
        item.setIcon(0, QIcon(os.path.join(self.icon_root, entity.lower() + ".png")))
        item.setToolTip(0, f"{entity}: {text}")
        (self.workplace_tree.addTopLevelItem if parent is None else parent.addChild)(item)
        return item

    def setAlphabet(self, value):
        self.active_letter = None if value == "All" else value
        self.filterWorkers()

    def filterWorkers(self, *args):
        query = self.worker_search.text().strip().casefold()
        rows = [row for row in self.workers if (
            (not query or query in " ".join(row).casefold()) and
            (not self.active_letter or row[1].upper().startswith(self.active_letter))
        )]
        self.worker_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, value in enumerate(row):
                item = QTableWidgetItem(value or "-")
                item.setToolTip(value or "Not provided")
                if column == 0:
                    item.setData(Qt.UserRole, row[0])
                self.worker_table.setItem(row_index, column, item)
            self.worker_table.setRowHeight(row_index, 34)
        self.worker_table.clearSelection()
        self.selected_worker_id = None
        self.updatePreview()

    def selectInitialDestination(self):
        source_worker = self.source_key[0]
        fallback = 0
        for row in range(self.worker_table.rowCount()):
            if self.worker_table.item(row, 0).data(Qt.UserRole) != source_worker:
                fallback = row
                break
        if self.worker_table.rowCount():
            self.worker_table.selectRow(fallback)
        source_path = self.source_key[1:5]
        iterator = [self.workplace_tree.topLevelItem(i) for i in range(self.workplace_tree.topLevelItemCount())]
        while iterator:
            item = iterator.pop(0)
            if item.text(1) == "Station" and tuple(item.data(0, Qt.UserRole)) == source_path:
                self.workplace_tree.setCurrentItem(item)
                ancestor = item.parent()
                while ancestor:
                    ancestor.setExpanded(True)
                    ancestor = ancestor.parent()
                break
            iterator.extend(item.child(i) for i in range(item.childCount()))
        self.shift_combo.setCurrentText(self.source_key[5])

    def workerSelectionChanged(self):
        selected = self.worker_table.selectionModel().selectedRows()
        self.selected_worker_id = self.worker_table.item(selected[0].row(), 0).data(Qt.UserRole) if selected else None
        self.updatePreview()

    def workplaceSelectionChanged(self, item, previous=None):
        self.selected_station_path = (
            tuple(item.data(0, Qt.UserRole)) if item and item.text(1) == "Station" else None
        )
        self.updatePreview()

    def selectedTools(self):
        tools = []
        for row in range(self.tool_table.rowCount()):
            item = self.tool_table.item(row, 1)
            holder = self.tool_table.cellWidget(row, 0)
            checkbox = holder.findChild(QCheckBox) if holder else None
            if item and checkbox and checkbox.isChecked():
                tools.append(item.data(Qt.UserRole))
        return tools

    def destinationKey(self):
        if not self.selected_worker_id or not self.selected_station_path or not self.shift_combo.currentText():
            return None
        return (self.selected_worker_id,) + self.selected_station_path + (self.shift_combo.currentText(),)

    def updatePreview(self, *args):
        tools = self.selectedTools() if hasattr(self, "tool_table") else []
        destination = self.destinationKey() if hasattr(self, "worker_table") else None
        mode = "Copy" if getattr(self, "copy_radio", None) and self.copy_radio.isChecked() else "Move"
        if not tools:
            message = "Select at least one available assessment tool."
        elif not self.selected_worker_id:
            message = "Select a destination worker."
        elif not self.selected_station_path:
            message = "Select a destination station from the workplace hierarchy."
        else:
            message = (
                f"{mode} {len(tools)} selected tool{'s' if len(tools) != 1 else ''} to "
                f"{destination[0]} at {' > '.join(destination[1:5])}, shift {destination[5]}."
            )
        self.preview_label.setText("Transfer preview: " + message)
        self.transfer_button.setEnabled(bool(tools and destination and destination != self.source_key))

    def performTransfer(self):
        tools = self.selectedTools()
        destination = self.destinationKey()
        if not tools or not destination:
            QMessageBox.warning(self, "Incomplete destination", "Select tools, a destination worker, station, and shift.")
            return
        if destination == self.source_key:
            QMessageBox.warning(self, "Same destination", "The source and destination contexts are identical.")
            return
        with sqlite3.connect(self.database_path) as conn:
            conflicts = [tool_id for tool_id in tools if conn.execute(
                """SELECT 1 FROM WorkerStationShiftErgoTool WHERE worker_id=? AND plant_name=?
                   AND section_name=? AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?""",
                destination + (tool_id,),
            ).fetchone()]
        if conflicts:
            names = ", ".join(self.TOOL_METADATA.get(tool, (tool, "", ""))[0] for tool in conflicts)
            QMessageBox.warning(
                self, "Destination already contains data",
                f"The destination already contains: {names}. No data was changed."
            )
            return
        mode = "copy" if self.copy_radio.isChecked() else "move"
        reply = QMessageBox.question(
            self, f"Confirm {mode}",
            f"{mode.title()} {len(tools)} selected assessment tool(s) to the chosen worker and workplace?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys=ON")
                for tool_id in tools:
                    self.copyTableRows(conn, "WorkerStationShiftErgoTool", self.source_key, destination, tool_id)
                    results_table = self.TOOL_METADATA[tool_id][2]
                    self.copyTableRows(conn, results_table, self.source_key, destination, tool_id, multiple=True)
                if self.move_radio.isChecked():
                    for tool_id in tools:
                        conn.execute(
                            """DELETE FROM WorkerStationShiftErgoTool WHERE worker_id=? AND plant_name=?
                               AND section_name=? AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?""",
                            self.source_key + (tool_id,),
                        )
        except sqlite3.Error as error:
            QMessageBox.critical(self, "Transfer failed", f"No data was changed.\n\n{error}")
            return
        QMessageBox.information(
            self, "Transfer complete",
            f"Selected assessment data was successfully {'copied' if mode == 'copy' else 'moved'} to the destination."
        )
        self.accept()

    @staticmethod
    def copyTableRows(conn, table, source, destination, tool_id, multiple=False):
        cursor = conn.execute(
            f"""SELECT * FROM {table} WHERE worker_id=? AND plant_name=? AND section_name=?
                AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?""",
            source + (tool_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            return
        columns = [description[0] for description in cursor.description]
        replacements = dict(zip(
            ("worker_id", "plant_name", "section_name", "line_name", "station_id", "shift_id"),
            destination,
        ))
        insert = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
        for row in rows:
            values = list(row)
            for column, value in replacements.items():
                values[columns.index(column)] = value
            conn.execute(insert, values)
