import os
import sqlite3

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QDoubleValidator, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QTabWidget, QTextEdit,
    QStyle, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)


ENTITY_FIELDS = {
    "Plant": [
        ("name", "Plant name", "line"), ("description", "Description", "text"),
        ("location", "Location", "line"), ("type", "Plant type", "line"),
        ("area", "Area", "number"), ("number_of_shifts", "Number of shifts", "number"),
        ("start_time", "Start time", "line"), ("end_time", "End time", "line"),
        ("operational_hours", "Operational hours", "number"),
        ("production_capacity", "Production capacity", "number"),
        ("opening_date", "Opening date", "line"),
        ("years_of_operation", "Years of operation", "number"),
    ],
    "Section": [
        ("name", "Section name", "line"), ("description", "Description", "text"),
        ("location", "Location", "line"), ("capacity", "Capacity", "number"),
        ("area", "Area", "number"), ("creation_date", "Creation date", "line"),
    ],
    "Line": [
        ("name", "Line name", "line"), ("description", "Description", "text"),
        ("location", "Location", "line"), ("products", "Products", "line"),
        ("creation_date", "Creation date", "line"),
    ],
    "Station": [
        ("id", "Station ID", "line"), ("location", "Location", "line"),
        ("task_description", "Task description", "text"),
        ("equipment_used", "Equipment used", "line"), ("cycle_time", "Cycle time (sec)", "number"),
        ("capacity", "Capacity", "number"), ("ergonomic_risk_level", "Ergonomic risk level", "number"),
        ("performance_metric", "Performance metric", "line"),
        ("power_consumption", "Power consumption (kWh)", "number"),
        ("materials_used", "Materials used", "line"), ("creation_date", "Creation date", "line"),
    ],
    "Shift": [
        ("id", "Shift ID", "line"), ("description", "Description", "text"),
        ("start_time", "Start time", "line"), ("end_time", "End time", "line"),
        ("shift_type", "Shift type", "line"), ("tasks_performed", "Tasks performed", "text"),
        ("product_output", "Product output", "number"), ("downtime", "Downtime (hrs)", "number"),
        ("incidents_reported", "Incidents reported", "text"),
        ("ergonomic_risk_events", "Ergonomic risk events", "text"), ("notes", "Notes", "text"),
    ],
}

PARENT_KEYS = {
    "Plant": [], "Section": ["plant_name"], "Line": ["plant_name", "section_name"],
    "Station": ["plant_name", "section_name", "line_name"], "Shift": [],
}
ID_FIELD = {"Plant": "name", "Section": "name", "Line": "name", "Station": "id", "Shift": "id"}
NEXT_ENTITY = {"Plant": "Section", "Section": "Line", "Line": "Station"}


class OrganizationWindow(QDialog):
    def __init__(self, parent=None, initial_entity="Plant"):
        super().__init__(parent)
        self.database_path = parent.projectdatabasePath
        self.current_entity = None
        self.current_keys = None
        self.new_parent_values = []
        self.editors = {}
        self.new_mode = False
        self.setWindowTitle("Organization Management")
        self.setObjectName("organizationDialog")
        self.setMinimumSize(1120, 740)
        self.resize(1180, 780)
        self.setStyleSheet(self.styleSheetText())
        self.icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        self.setupUI()
        self.refreshAll()
        self.selectInitialEntity(initial_entity)

    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        title = QLabel("Organization Management")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("Manage the workplace hierarchy and independent work shifts.")
        subtitle.setObjectName("dialogSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)
        directory = QFrame()
        directory.setObjectName("card")
        directory.setFixedWidth(410)
        directory_layout = QVBoxLayout(directory)
        directory_layout.setContentsMargins(15, 15, 15, 15)
        directory_heading = QLabel("Organization")
        directory_heading.setObjectName("sectionTitle")
        directory_layout.addWidget(directory_heading)
        self.directory_tabs = QTabWidget()
        self.directory_tabs.setIconSize(QSize(22, 22))
        self.location_tree = QTreeWidget()
        self.location_tree.setIconSize(QSize(22, 22))
        self.location_tree.setHeaderLabels(["Location hierarchy", "Type"])
        self.location_tree.header().setStretchLastSection(False)
        self.location_tree.header().setSectionResizeMode(0, self.location_tree.header().Stretch)
        self.location_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.location_tree.setToolTip("Expand the hierarchy and select a plant, section, line, or station to view its details.")
        self.location_tree.itemSelectionChanged.connect(self.locationSelected)
        self.shift_tree = QTreeWidget()
        self.shift_tree.setIconSize(QSize(22, 22))
        self.shift_tree.setHeaderLabels(["Shift", "Type"])
        self.shift_tree.header().setSectionResizeMode(0, self.shift_tree.header().Stretch)
        self.shift_tree.setToolTip("Select a shift to view or edit its independent schedule information.")
        self.shift_tree.itemSelectionChanged.connect(self.shiftSelected)
        self.directory_tabs.addTab(self.location_tree, QIcon(os.path.join(self.icon_root, "plant.png")), "Locations")
        self.directory_tabs.addTab(self.shift_tree, QIcon(os.path.join(self.icon_root, "shift.png")), "Shifts")
        self.directory_tabs.setTabToolTip(0, "Manage the Plant > Section > Line > Station hierarchy.")
        self.directory_tabs.setTabToolTip(1, "Manage shifts, which are independent from the location hierarchy.")
        self.directory_tabs.currentChanged.connect(self.directoryTabChanged)
        directory_layout.addWidget(self.directory_tabs, 1)
        tree_actions = QHBoxLayout()
        self.add_root_button = QPushButton("New plant")
        self.add_root_button.setIcon(QIcon(os.path.join(self.icon_root, "plant.png")))
        self.add_root_button.setIconSize(QSize(26, 26))
        self.add_root_button.setToolTip("Create a new top-level plant. On the Shifts tab, create a new shift.")
        self.add_root_button.clicked.connect(lambda: self.startNew("Plant", []))
        self.add_child_button = QPushButton("Add child")
        self.add_child_button.setIcon(QIcon(os.path.join(self.icon_root, "addchild.png")))
        self.add_child_button.setIconSize(QSize(26, 26))
        self.add_child_button.setToolTip("Add the next hierarchy level beneath the selected location.")
        self.add_child_button.setObjectName("primaryOutlineButton")
        self.add_child_button.clicked.connect(self.addChild)
        tree_actions.addWidget(self.add_root_button)
        tree_actions.addWidget(self.add_child_button)
        directory_layout.addLayout(tree_actions)
        body.addWidget(directory)

        details = QFrame()
        details.setObjectName("card")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(18, 16, 18, 16)
        header = QHBoxLayout()
        heading_box = QVBoxLayout()
        self.entity_title = QLabel("Select an item")
        self.entity_title.setObjectName("sectionTitle")
        self.breadcrumb = QLabel("Choose a location or shift to view its details.")
        self.breadcrumb.setObjectName("dialogSubtitle")
        self.breadcrumb.setWordWrap(True)
        heading_box.addWidget(self.entity_title)
        heading_box.addWidget(self.breadcrumb)
        header.addLayout(heading_box, 1)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setIcon(QIcon(os.path.join(self.icon_root, "delete.png")))
        self.delete_button.setIconSize(QSize(26, 26))
        self.delete_button.setToolTip("Delete the selected organization record after confirmation.")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.deleteEntity)
        header.addWidget(self.delete_button)
        details_layout.addLayout(header)
        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        self.form_scroll.setFrameShape(QFrame.NoFrame)
        self.form_content = QWidget()
        self.form_content.setObjectName("formContent")
        self.form_container_layout = QVBoxLayout(self.form_content)
        self.form_container_layout.setContentsMargins(0, 12, 8, 0)
        self.form_container_layout.setSpacing(10)
        required_label = QLabel("Required information")
        required_label.setObjectName("eyebrow")
        self.form_container_layout.addWidget(required_label)
        self.required_form = QFormLayout()
        self.required_form.setSpacing(10)
        self.required_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.form_container_layout.addLayout(self.required_form)
        self.optional_toggle = QToolButton()
        self.optional_toggle.setObjectName("optionalToggle")
        self.optional_toggle.setText("Optional details")
        self.optional_toggle.setCheckable(True)
        self.optional_toggle.setChecked(False)
        self.optional_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.optional_toggle.setArrowType(Qt.RightArrow)
        self.optional_toggle.setToolTip("Show or hide descriptive and operational fields.")
        self.optional_toggle.toggled.connect(self.setOptionalDetailsVisible)
        self.form_container_layout.addWidget(self.optional_toggle)
        self.optional_content = QWidget()
        self.optional_content.setObjectName("optionalContent")
        self.optional_form = QFormLayout(self.optional_content)
        self.optional_form.setContentsMargins(0, 2, 0, 0)
        self.optional_form.setSpacing(10)
        self.optional_form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.optional_content.hide()
        self.form_container_layout.addWidget(self.optional_content)
        self.form_container_layout.addStretch()
        self.form_scroll.setWidget(self.form_content)
        details_layout.addWidget(self.form_scroll, 1)
        self.note = QLabel("Note: Select an item to begin.")
        self.note.setObjectName("notificationLabel")
        self.note.setWordWrap(True)
        self.note.setToolTip("Validation, guidance, and save-result messages appear here.")
        details_layout.addWidget(self.note)
        body.addWidget(details, 1)
        layout.addLayout(body, 1)

        actions = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setIcon(QIcon(os.path.join(self.icon_root, "cancel.png")))
        self.cancel_button.setIconSize(QSize(26, 26))
        self.cancel_button.setToolTip("Discard unsaved field changes and reload the selected record.")
        self.cancel_button.clicked.connect(self.cancelEdit)
        self.save_button = QPushButton("Save changes")
        self.save_button.setIcon(QIcon(os.path.join(self.icon_root, "save.png")))
        self.save_button.setIconSize(QSize(26, 26))
        self.save_button.setToolTip("Save the required identifier and any optional organization details.")
        self.save_button.setObjectName("primaryOutlineButton")
        self.save_button.clicked.connect(self.saveEntity)
        close_button = QPushButton("Close")
        close_button.setIcon(QIcon(os.path.join(self.icon_root, "close.png")))
        close_button.setIconSize(QSize(26, 26))
        close_button.setToolTip("Close Organization Management and return to the assessment.")
        close_button.clicked.connect(self.accept)
        actions.addStretch()
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def query(self, sql, parameters=()):
        with sqlite3.connect(self.database_path) as conn:
            return conn.execute(sql, parameters).fetchall()

    def refreshAll(self):
        self.location_tree.blockSignals(True)
        self.location_tree.clear()
        plants = self.query("SELECT name FROM Plant ORDER BY name")
        for (plant,) in plants:
            plant_item = self.makeItem("Plant", [plant], plant)
            self.location_tree.addTopLevelItem(plant_item)
            for (section,) in self.query("SELECT name FROM Section WHERE plant_name = ? ORDER BY name", (plant,)):
                section_item = self.makeItem("Section", [plant, section], section)
                plant_item.addChild(section_item)
                for (line,) in self.query(
                    "SELECT name FROM Line WHERE plant_name = ? AND section_name = ? ORDER BY name", (plant, section)
                ):
                    line_item = self.makeItem("Line", [plant, section, line], line)
                    section_item.addChild(line_item)
                    for (station,) in self.query(
                        "SELECT id FROM Station WHERE plant_name = ? AND section_name = ? AND line_name = ? ORDER BY id",
                        (plant, section, line),
                    ):
                        line_item.addChild(self.makeItem("Station", [plant, section, line, station], station))
        self.location_tree.blockSignals(False)
        self.shift_tree.blockSignals(True)
        self.shift_tree.clear()
        for (shift_id,) in self.query("SELECT id FROM Shift ORDER BY id"):
            self.shift_tree.addTopLevelItem(self.makeItem("Shift", [shift_id], shift_id))
        self.shift_tree.blockSignals(False)

    def makeItem(self, entity, keys, text):
        item = QTreeWidgetItem([str(text), entity])
        item.setData(0, Qt.UserRole, (entity, keys))
        item.setIcon(0, QIcon(os.path.join(self.icon_root, entity.lower() + ".png")))
        item.setToolTip(0, f"Select this {entity.lower()} to view or edit its information.")
        return item

    def selectInitialEntity(self, entity):
        if entity == "Shift":
            self.directory_tabs.setCurrentIndex(1)
            selected_shift = self.parent().shift_combo.currentText().strip()
            if selected_shift:
                self.selectKeys("Shift", [selected_shift])
            elif self.shift_tree.topLevelItemCount():
                self.shift_tree.setCurrentItem(self.shift_tree.topLevelItem(0))
            else:
                self.startNew("Shift", [])
            return
        self.directory_tabs.setCurrentIndex(0)
        combo_names = {
            "Plant": ["plant_combo"],
            "Section": ["plant_combo", "section_combo"],
            "Line": ["plant_combo", "section_combo", "line_combo"],
            "Station": ["plant_combo", "section_combo", "line_combo", "station_combo"],
        }
        selected_keys = [getattr(self.parent(), name).currentText().strip() for name in combo_names[entity]]
        if all(selected_keys):
            self.selectKeys(entity, selected_keys)
            if self.location_tree.currentItem():
                self.collapseInitialTree()
                return
        match = self.findFirstItem(entity)
        if match:
            self.location_tree.setCurrentItem(match)
            self.collapseInitialTree()
        elif entity == "Plant":
            self.startNew("Plant", [])

    def findFirstItem(self, entity):
        iterator = self.location_tree.invisibleRootItem()
        stack = [iterator.child(i) for i in range(iterator.childCount())]
        while stack:
            item = stack.pop(0)
            data = item.data(0, Qt.UserRole)
            if data and data[0] == entity:
                return item
            stack[0:0] = [item.child(i) for i in range(item.childCount())]
        return None

    def collapseInitialTree(self):
        self.location_tree.blockSignals(True)
        self.location_tree.setCurrentItem(None)
        self.location_tree.clearSelection()
        self.location_tree.collapseAll()
        self.location_tree.blockSignals(False)

    def locationSelected(self):
        item = self.location_tree.currentItem()
        if item:
            self.loadEntity(*item.data(0, Qt.UserRole))

    def shiftSelected(self):
        item = self.shift_tree.currentItem()
        if item:
            self.loadEntity(*item.data(0, Qt.UserRole))

    def directoryTabChanged(self, index):
        is_shift = index == 1
        self.add_root_button.setText("New shift" if is_shift else "New plant")
        self.add_root_button.setIcon(QIcon(os.path.join(self.icon_root, "shift.png" if is_shift else "plant.png")))
        try:
            self.add_root_button.clicked.disconnect()
        except TypeError:
            pass
        self.add_root_button.clicked.connect(lambda: self.startNew("Shift" if is_shift else "Plant", []))
        self.add_child_button.setVisible(not is_shift)
        (self.shiftSelected if is_shift else self.locationSelected)()

    def clearForm(self):
        while self.required_form.rowCount():
            self.required_form.removeRow(0)
        while self.optional_form.rowCount():
            self.optional_form.removeRow(0)
        self.editors = {}

    def setOptionalDetailsVisible(self, expanded):
        self.optional_content.setVisible(expanded)
        self.optional_toggle.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)

    def loadEntity(self, entity, keys):
        where_columns = PARENT_KEYS[entity] + [ID_FIELD[entity]]
        row = self.query(
            f"SELECT {', '.join(name for name, _, _ in ENTITY_FIELDS[entity])} FROM {entity} "
            f"WHERE {' AND '.join(column + ' = ?' for column in where_columns)}", keys,
        )
        if not row:
            return
        self.buildForm(entity, keys[:-1], row[0], existing_keys=keys)

    def buildForm(self, entity, parent_values, values=None, existing_keys=None):
        self.clearForm()
        self.current_entity = entity
        self.current_keys = existing_keys
        self.new_parent_values = list(parent_values)
        self.new_mode = existing_keys is None
        self.optional_toggle.setChecked(False)
        self.entity_title.setText(("New " if self.new_mode else "Edit ") + entity.lower())
        path = parent_values + ([] if self.new_mode else [existing_keys[-1]])
        self.breadcrumb.setText("  >  ".join(str(value) for value in path) or "Top-level record")
        for index, (column, label, editor_type) in enumerate(ENTITY_FIELDS[entity]):
            editor = QTextEdit() if editor_type == "text" else QLineEdit()
            if editor_type == "text":
                editor.setMaximumHeight(76)
            elif editor_type == "number":
                editor.setValidator(QDoubleValidator(editor))
            value = values[index] if values else ""
            (editor.setPlainText if editor_type == "text" else editor.setText)("" if value is None else str(value))
            if not self.new_mode and column == ID_FIELD[entity]:
                editor.setEnabled(False)
                editor.setToolTip("Identifiers cannot be renamed because related records may depend on them.")
            else:
                editor.setToolTip(f"{label} for this {entity.lower()}.")
            target_form = self.required_form if column == ID_FIELD[entity] else self.optional_form
            target_form.addRow(label, editor)
            self.editors[column] = editor
        self.delete_button.setEnabled(not self.new_mode)
        self.note.setText("Note: Required identifiers must be unique within their parent location.")

    def editorValue(self, editor):
        return editor.toPlainText().strip() if isinstance(editor, QTextEdit) else editor.text().strip()

    def addChild(self):
        item = self.location_tree.currentItem()
        if item:
            entity, keys = item.data(0, Qt.UserRole)
        elif self.current_entity in NEXT_ENTITY and self.current_keys:
            entity, keys = self.current_entity, self.current_keys
        else:
            self.note.setText("Note: Select a plant, section, or line before adding a child location.")
            return
        child_entity = NEXT_ENTITY.get(entity)
        if not child_entity:
            self.note.setText("Note: Stations are the final level of the location hierarchy.")
            return
        self.startNew(child_entity, keys)

    def startNew(self, entity, parent_values):
        if entity in ("Section", "Line", "Station") and len(parent_values) != len(PARENT_KEYS[entity]):
            self.note.setText("Note: Select the parent location before creating this record.")
            return
        self.buildForm(entity, parent_values)

    def saveEntity(self):
        if not self.current_entity:
            return
        entity = self.current_entity
        fields = [field[0] for field in ENTITY_FIELDS[entity]]
        values = [self.editorValue(self.editors[field]) or None for field in fields]
        identifier = values[fields.index(ID_FIELD[entity])]
        if not identifier:
            self.note.setText(f"Note: {entity} identifier is required.")
            return
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                if self.new_mode:
                    parent_values = self.new_parent_values
                    columns = PARENT_KEYS[entity] + fields
                    conn.execute(
                        f"INSERT INTO {entity} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
                        parent_values + values,
                    )
                    saved_keys = parent_values + [identifier]
                else:
                    where_columns = PARENT_KEYS[entity] + [ID_FIELD[entity]]
                    conn.execute(
                        f"UPDATE {entity} SET {', '.join(field + ' = ?' for field in fields)} "
                        f"WHERE {' AND '.join(column + ' = ?' for column in where_columns)}",
                        values + self.current_keys,
                    )
                    saved_keys = self.current_keys
            self.setParentSelection(entity, saved_keys)
            self.refreshAll()
            self.selectKeys(entity, saved_keys)
            self.note.setText(f"Note: {entity} saved successfully.")
        except sqlite3.IntegrityError as error:
            self.note.setText(f"Note: Could not save. The identifier may already exist in this location. ({error})")
        except sqlite3.Error as error:
            self.note.setText(f"Note: Database error while saving: {error}")

    def deleteEntity(self):
        if not self.current_entity or not self.current_keys:
            return
        entity = self.current_entity
        reply = QMessageBox.question(
            self, f"Delete {entity}",
            f"Delete this {entity.lower()}? Related child records and assessments may also be deleted.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        where_columns = PARENT_KEYS[entity] + [ID_FIELD[entity]]
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    f"DELETE FROM {entity} WHERE {' AND '.join(column + ' = ?' for column in where_columns)}",
                    self.current_keys,
                )
            self.refreshAll()
            self.clearForm()
            self.current_entity = None
            self.current_keys = None
            self.entity_title.setText("Select an item")
            self.breadcrumb.setText("The record was deleted.")
            self.note.setText("Note: Deletion completed.")
        except sqlite3.Error as error:
            self.note.setText(f"Note: Database error while deleting: {error}")

    def cancelEdit(self):
        if self.current_keys:
            self.loadEntity(self.current_entity, self.current_keys)
        else:
            self.clearForm()
            self.entity_title.setText("Select an item")
            self.breadcrumb.setText("Choose a location or shift to view its details.")

    def selectKeys(self, entity, keys):
        tree = self.shift_tree if entity == "Shift" else self.location_tree
        iterator = tree.invisibleRootItem()
        stack = [iterator.child(i) for i in range(iterator.childCount())]
        while stack:
            item = stack.pop(0)
            if item.data(0, Qt.UserRole) == (entity, keys):
                tree.setCurrentItem(item)
                return
            stack.extend(item.child(i) for i in range(item.childCount()))

    def setParentSelection(self, entity, keys):
        attributes = {
            "Plant": "editPlantName", "Section": "editSectionName", "Line": "editLineName",
            "Station": "editStationName", "Shift": "editShiftName",
        }
        setattr(self.parent(), attributes[entity], keys[-1])

    def styleSheetText(self):
        return """
            QDialog#organizationDialog { background: #F4F7F9; color: #1B2933; font: 13px "Segoe UI"; }
            QLabel#dialogTitle { color: #0B326C; font-size: 22px; font-weight: 600; }
            QLabel#dialogSubtitle { color: #5F6F7A; }
            QLabel#sectionTitle { color: #0B326C; font-size: 16px; font-weight: 600; }
            QLabel#eyebrow { color: #5F6F7A; font-size: 11px; font-weight: 600; }
            QFrame#card { background: white; border: 1px solid #D5DEE5; border-radius: 8px; }
            QTreeWidget { background: white; alternate-background-color: #F7FAFC; border: 1px solid #D5DEE5; }
            QTreeWidget::item { min-height: 30px; padding: 2px 5px; }
            QTreeWidget::item:selected { background: #DDF3F5; color: #0B326C; }
            QHeaderView::section { background: #EDF3F6; color: #0B326C; border: 0; padding: 8px; font-weight: 600; }
            QLineEdit, QTextEdit { background: white; border: 1px solid #BCC9D3; border-radius: 6px; padding: 7px 9px; }
            QLineEdit:focus, QTextEdit:focus { border: 2px solid #08A9B5; }
            QLineEdit:disabled { background: #EEF2F4; color: #687781; }
            QPushButton { min-height: 42px; background: white; color: #0B326C; border: 1px solid #9EB0BE; border-radius: 6px; padding: 0 15px; font-weight: 600; }
            QPushButton:hover { background: #EDF7F8; border-color: #08A9B5; }
            QPushButton#primaryButton { background: #0B326C; color: white; border-color: #0B326C; }
            QPushButton#primaryOutlineButton { border: 2px solid #08A9B5; }
            QPushButton#dangerButton { color: #C93C3C; border-color: #D86A6A; }
            QLabel#notificationLabel { background: #EAF7F8; border: 1px solid #B8E1E4; border-radius: 6px; padding: 9px 12px; }
            QScrollArea, QScrollArea QWidget#qt_scrollarea_viewport, QWidget#formContent, QWidget#optionalContent {
                background: white;
                border: 0;
            }
            QToolButton#optionalToggle {
                min-height: 38px; background: #F4F7F9; color: #0B326C;
                border: 1px solid #D5DEE5; border-radius: 6px; padding: 0 10px;
                font-weight: 600; text-align: left;
            }
            QToolButton#optionalToggle:hover { border-color: #08A9B5; background: #EDF7F8; }
            QTabWidget::pane { border: 1px solid #D5DEE5; }
            QTabBar::tab { padding: 8px 18px; color: #5F6F7A; }
            QTabBar::tab:selected { color: #0B326C; font-weight: 600; border-bottom: 2px solid #08A9B5; }
            QToolTip { background: #1B2933; color: white; border: 1px solid #0B326C; padding: 6px; }
        """
