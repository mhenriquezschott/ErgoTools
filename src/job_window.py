import sys
import math
import pycountry
import locale 
import os
import time
import sqlite3

from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, QLocale, QTime, QDate, QStandardPaths

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit, QSpinBox, 
    QComboBox, QPushButton, QTabWidget, QWidget, QGridLayout, QMessageBox, QDialogButtonBox, QTextEdit, QTimeEdit, QTableWidget, QTableWidgetItem
)

from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QPixmap, QRegExpValidator, QColor, QIcon

from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import QRegularExpression, QRegExp

#from PySide2.QtWidgets import QSpacerItem, QSizePolicy

from pyLiFFT import LiFFT
from pyDUET import DUET
from pyTST import TST
from database import connect_database
from job_risk_repository import save_job_with_measurements
from job_risk_repository import (
    JobRiskProfileError,
    PROFILE_SOURCE_TYPES,
    approve_profile,
    create_draft_profile,
    job_profiles,
    make_profile_current,
    profile_measurements,
    retire_profile,
    save_draft_profile,
)
from risk_colors import job_risk_color




class JobWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Job Management")
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        self.setWindowIcon(QIcon(os.path.join(icon_root, "jobmanagement.png")))
        self.resize(1120, 740)
        self.setMinimumSize(980, 680)
        self.setObjectName("jobWindow")
        self.setupUI()

        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadJobs()

            # Get the current text from the plant_combo in the parent window
            job_combo_text = self.parent().job_combo.currentText()

            # Extract the ID from the text 
            job_id = job_combo_text.strip()

            index = self.job_id_combo.findText(job_id)
            if index != -1:
                self.job_id_combo.setCurrentIndex(index)    
    
            
            

    def setupUI(self):
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Job Management")
        title.setObjectName("dialogTitle")
        intro = QLabel("Define job-level risk measurements used by JROT rotation schemes.")
        intro.setObjectName("supportingText")
        layout.addWidget(title)
        layout.addWidget(intro)

        content = QHBoxLayout()
        content.setSpacing(14)
        browser_panel = QtWidgets.QFrame()
        browser_panel.setObjectName("workspacePanel")
        browser_panel.setMinimumWidth(280)
        browser_panel.setMaximumWidth(340)
        browser_layout = QVBoxLayout(browser_panel)
        browser_layout.setContentsMargins(14, 12, 14, 12)
        browser_layout.setSpacing(9)
        browser_title = QLabel("Jobs")
        browser_title.setObjectName("panelTitle")
        browser_layout.addWidget(browser_title)
        browser_layout.addWidget(QLabel("Job ID"))
        self.job_id_combo = QComboBox()
        self.job_id_combo.setEditable(True)
        self.job_id_combo.setToolTip("Select an existing job or enter an ID for a new job.")
        browser_layout.addWidget(self.job_id_combo)

        navigation = QHBoxLayout()
        navigation.setSpacing(6)
        nav_specs = (
            ("first_button", "first.png", self.firstJob, "First job"),
            ("previous_button", "previous.png", self.previousJob, "Previous job"),
            ("next_button", "next.png", self.nextJob, "Next job"),
            ("last_button", "last.png", self.lastJob, "Last job"),
        )
        for attr, icon, callback, tooltip in nav_specs:
            button = QPushButton()
            button.setIcon(QIcon(os.path.join(icon_root, icon)))
            button.setIconSize(QtCore.QSize(24, 24))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            setattr(self, attr, button)
            navigation.addWidget(button)
        browser_layout.addLayout(navigation)

        self.search_button = QPushButton("Search")
        self.search_button.setIcon(QIcon(os.path.join(icon_root, "search.png")))
        self.search_button.clicked.connect(self.searchJob)
        browser_layout.addWidget(self.search_button)
        browser_layout.addStretch(1)
        content.addWidget(browser_panel)

        details_panel = QtWidgets.QFrame()
        details_panel.setObjectName("workspacePanel")
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(16, 12, 16, 14)
        details_layout.setSpacing(10)
        details_title = QLabel("Job details")
        details_title.setObjectName("panelTitle")
        details_layout.addWidget(details_title)
        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(9)
        form_layout.addWidget(QLabel("Job name"), 0, 0)
        self.job_name_input = QLineEdit()
        self.job_name_input.setToolTip("Enter a descriptive name for this job.")
        form_layout.addWidget(self.job_name_input, 0, 1)
        form_layout.addWidget(QLabel("Description"), 1, 0, Qt.AlignTop)
        self.job_description_input = QTextEdit()
        self.job_description_input.setMaximumHeight(70)
        self.job_description_input.setPlaceholderText("Optional job description")
        form_layout.addWidget(self.job_description_input, 1, 1)
        form_layout.setColumnStretch(1, 1)
        details_layout.addLayout(form_layout)
        profile_header = QHBoxLayout()
        profile_header.setSpacing(8)
        profile_label = QLabel("Risk profile")
        profile_label.setObjectName("panelTitle")
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(245)
        self.profile_combo.setToolTip("Select a Job Risk Profile version.")
        self.profile_status_label = QLabel("No profile")
        self.profile_status_label.setObjectName("profileStatus")
        profile_header.addWidget(profile_label)
        profile_header.addWidget(self.profile_combo, 1)
        profile_header.addWidget(self.profile_status_label)
        details_layout.addLayout(profile_header)

        profile_actions = QHBoxLayout()
        profile_actions.setSpacing(7)
        self.new_profile_button = QPushButton("New version")
        self.new_profile_button.setIcon(QIcon(os.path.join(icon_root, "new.png")))
        self.new_profile_button.setToolTip("Create a draft by copying the selected profile.")
        self.approve_profile_button = QPushButton("Approve")
        self.approve_profile_button.setObjectName("primaryOutlineButton")
        self.approve_profile_button.setToolTip("Approve this draft and make it current.")
        self.current_profile_button = QPushButton("Use as current")
        self.current_profile_button.setToolTip("Use this approved historical profile in JROT.")
        self.retire_profile_button = QPushButton("Retire")
        self.retire_profile_button.setObjectName("dangerButton")
        self.retire_profile_button.setToolTip("Retire this profile without deleting its history.")
        for button in (
            self.new_profile_button,
            self.approve_profile_button,
            self.current_profile_button,
            self.retire_profile_button,
        ):
            button.setMinimumHeight(32)
            profile_actions.addWidget(button)
        profile_actions.addStretch(1)
        details_layout.addLayout(profile_actions)

        self.profile_tabs = QTabWidget()
        self.profile_tabs.setObjectName("profileTabs")
        measurement_tab = QWidget()
        measurement_layout = QVBoxLayout(measurement_tab)
        measurement_layout.setContentsMargins(8, 8, 8, 8)
        risk_help = QLabel("Cumulative damage and calculated outcome probability")
        risk_help.setObjectName("supportingText")
        measurement_layout.addWidget(risk_help)
        measurement_layout.addWidget(self.createRiskMeasurementTable(), 1)
        self.profile_tabs.addTab(measurement_tab, "Risk measurements")
        self.profile_tabs.addTab(self.createProfileEvidenceTab(), "Profile evidence")
        details_layout.addWidget(self.profile_tabs, 1)
        content.addWidget(details_panel, 1)
        layout.addLayout(content, 1)

        self.job_id_combo.currentIndexChanged.connect(self.loadJobDetails)
        self.profile_combo.currentIndexChanged.connect(self.loadSelectedProfile)
        self.new_profile_button.clicked.connect(self.newProfileVersion)
        self.approve_profile_button.clicked.connect(self.approveSelectedProfile)
        self.current_profile_button.clicked.connect(self.makeSelectedProfileCurrent)
        self.retire_profile_button.clicked.connect(self.retireSelectedProfile)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        command_specs = (
            ("new_button", "New job", "new.png", self.newJob, ""),
            ("save_button", "Save changes", "save.png", self.saveJob, "primaryOutlineButton"),
            ("delete_button", "Delete", "delete.png", self.deleteJob, "dangerButton"),
            ("cancel_button", "Cancel edit", "undo.png", self.cancelJob, ""),
        )
        for attr, text, icon, callback, object_name in command_specs:
            button = QPushButton(text)
            button.setIcon(QIcon(os.path.join(icon_root, icon)))
            button.setIconSize(QtCore.QSize(22, 22))
            button.clicked.connect(callback)
            if object_name:
                button.setObjectName(object_name)
            setattr(self, attr, button)
            button_layout.addWidget(button)
        self.close_button = QPushButton("Close")
        self.close_button.setIcon(QIcon(os.path.join(icon_root, "close.png")))
        self.close_button.setIconSize(QtCore.QSize(22, 22))
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        base = self.parent().mainWorkspaceStyleSheet() if hasattr(self.parent(), "mainWorkspaceStyleSheet") else ""
        self.setStyleSheet(base + """
            QDialog#jobWindow { background: #F4F7F9; color: #1B2933; font: 12px "Segoe UI"; }
            QTextEdit { background: white; border: 1px solid #BCC9D3; border-radius: 5px; padding: 6px; }
            QTextEdit:focus { border: 2px solid #08A9B5; }
            QTableWidget { background: white; alternate-background-color: #F5F8FA; border: 1px solid #CAD5DD;
                           gridline-color: #D5DEE5; selection-background-color: #087E91; selection-color: white; }
            QHeaderView::section { background: #EAF1F5; color: #0B326C; border: 0; border-right: 1px solid #CAD5DD;
                                   border-bottom: 1px solid #CAD5DD; padding: 7px; font-weight: 700; }
            QPushButton#dangerButton { color: #C73737; border-color: #E0A2A2; }
            QPushButton#dangerButton:hover { background: #FFF0F0; border-color: #C73737; }
            QPushButton#primaryOutlineButton:disabled { color: #8998A3; background: #F2F5F7;
                                                        border: 1px solid #D5DEE5; }
            QLabel#profileStatus { color: #405866; font-weight: 700; padding: 4px 7px;
                                   background: #EAF1F5; border: 1px solid #CAD5DD; border-radius: 4px; }
            QTabWidget#profileTabs::pane { border: 1px solid #CAD5DD; background: white; }
            QComboBox:disabled, QDateEdit:disabled, QSpinBox:disabled {
                color: #304652; background: #F2F5F7; border-color: #D5DEE5;
            }
        """)

    def createProfileEvidenceTab(self):
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        self.profile_name_input = QLineEdit()
        self.profile_source_combo = QComboBox()
        source_labels = {
            "expert": "Expert estimate",
            "external": "External assessment",
            "study": "Study",
            "aggregate": "Aggregated measurements",
            "imported": "Imported legacy data",
        }
        for source_type in PROFILE_SOURCE_TYPES:
            self.profile_source_combo.addItem(source_labels[source_type], source_type)
        self.profile_reference_input = QLineEdit()
        self.profile_reference_input.setPlaceholderText("Report, study, or dataset reference")
        self.profile_sample_size = QSpinBox()
        self.profile_sample_size.setRange(-1, 1000000)
        self.profile_sample_size.setSpecialValueText("Not specified")
        self.profile_sample_size.setValue(-1)
        self.profile_assessed_on = self.createOptionalDateEdit()
        self.profile_valid_from = self.createOptionalDateEdit()
        self.profile_valid_to = self.createOptionalDateEdit()
        self.profile_methodology_input = QTextEdit()
        self.profile_methodology_input.setMaximumHeight(72)
        self.profile_notes_input = QTextEdit()
        self.profile_notes_input.setMaximumHeight(72)

        layout.addWidget(QLabel("Profile name"), 0, 0)
        layout.addWidget(self.profile_name_input, 0, 1, 1, 3)
        layout.addWidget(QLabel("Source"), 1, 0)
        layout.addWidget(self.profile_source_combo, 1, 1)
        layout.addWidget(QLabel("Sample size"), 1, 2)
        layout.addWidget(self.profile_sample_size, 1, 3)
        layout.addWidget(QLabel("Source reference"), 2, 0)
        layout.addWidget(self.profile_reference_input, 2, 1, 1, 3)
        layout.addWidget(QLabel("Assessed on"), 3, 0)
        layout.addWidget(self.profile_assessed_on, 3, 1)
        layout.addWidget(QLabel("Valid from"), 3, 2)
        layout.addWidget(self.profile_valid_from, 3, 3)
        layout.addWidget(QLabel("Valid to"), 4, 2)
        layout.addWidget(self.profile_valid_to, 4, 3)
        layout.addWidget(QLabel("Methodology"), 5, 0, Qt.AlignTop)
        layout.addWidget(self.profile_methodology_input, 5, 1)
        layout.addWidget(QLabel("Notes"), 5, 2, Qt.AlignTop)
        layout.addWidget(self.profile_notes_input, 5, 3)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        return tab

    def createOptionalDateEdit(self):
        editor = QDateEdit()
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("dd MMM yyyy")
        editor.setMinimumDate(QDate(1900, 1, 1))
        editor.setSpecialValueText("Not set")
        editor.setDate(editor.minimumDate())
        return editor


    def createRiskMeasurementTable(self):
        self.risk_table = QTableWidget()
        self.risk_table.setRowCount(3)
        self.risk_table.setColumnCount(3)
        self.risk_table.setHorizontalHeaderLabels(["Tool", "Total\nCumulative Damage", "Probability\nOutcome (%)"])
    
        bold_font = QFont()
        bold_font.setBold(True)
        for i in range(3):
            self.risk_table.horizontalHeaderItem(i).setFont(bold_font)
            self.risk_table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)
    
        tools = ["LiFFT", "DUET", "ST"]
        for row, tool in enumerate(tools):
            
            tool_item = QTableWidgetItem(tool)
            tool_item.setFlags(Qt.ItemIsEnabled)
            tool_item.setTextAlignment(Qt.AlignCenter)
            bold_font = QFont()
            bold_font.setBold(True)
            tool_item.setFont(bold_font)
            self.risk_table.setItem(row, 0, tool_item)

    
            dmg_item = QTableWidgetItem("0.0")
            dmg_item.setTextAlignment(Qt.AlignCenter)
            self.risk_table.setItem(row, 1, dmg_item)
    
            prob_item = QTableWidgetItem("0.0")
            prob_item.setTextAlignment(Qt.AlignCenter)
            prob_item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.risk_table.setItem(row, 2, prob_item)
    
        self.risk_table.verticalHeader().setDefaultSectionSize(35)
        self.risk_table.cellChanged.connect(self.handleDamageEdit)
        
        
        # Stretch the 2nd and 3rd columns to fill remaining width
        header = self.risk_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # Tool name column stays fixed
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        
        return self.risk_table

    def optionalDateValue(self, editor):
        if editor.date() == editor.minimumDate():
            return None
        return editor.date().toString("yyyy-MM-dd")

    def setOptionalDateValue(self, editor, value):
        date = QDate.fromString(value or "", "yyyy-MM-dd")
        editor.setDate(date if date.isValid() else editor.minimumDate())

    def selectedProfile(self):
        profile_id = self.profile_combo.currentData()
        if profile_id is None:
            return None
        return next(
            (profile for profile in getattr(self, "profile_records", []) if profile["id"] == profile_id),
            None,
        )

    def loadProfiles(self, job_id, selected_profile_id=None):
        connection = connect_database(self.parent().projectdatabasePath, read_only=True)
        try:
            self.profile_records = job_profiles(connection, job_id)
        finally:
            connection.close()
        if selected_profile_id is None:
            selected_profile_id = next(
                (
                    profile["id"]
                    for profile in self.profile_records
                    if profile["status"] == "approved" and profile["is_current"]
                ),
                self.profile_records[0]["id"] if self.profile_records else None,
            )
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in self.profile_records:
            suffix = " | Current" if profile["is_current"] else ""
            self.profile_combo.addItem(
                f"v{profile['version']} | {profile['name']} | {profile['status'].title()}{suffix}",
                profile["id"],
            )
        index = self.profile_combo.findData(selected_profile_id)
        self.profile_combo.setCurrentIndex(index if index >= 0 else 0)
        self.profile_combo.blockSignals(False)
        self.loadSelectedProfile()

    def clearProfileControls(self):
        self.profile_records = []
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.blockSignals(False)
        self.profile_status_label.setText("New Job")
        self.profile_name_input.setText("Current job estimate")
        self.profile_source_combo.setCurrentIndex(0)
        self.profile_reference_input.clear()
        self.profile_methodology_input.clear()
        self.profile_notes_input.clear()
        self.profile_sample_size.setValue(-1)
        for editor in (
            self.profile_assessed_on,
            self.profile_valid_from,
            self.profile_valid_to,
        ):
            editor.setDate(editor.minimumDate())
        self.setProfileEditability(True, new_job=True)
        self.setMeasurementValues({})

    def setMeasurementValues(self, measurements):
        self.risk_table.blockSignals(True)
        for row, tool in enumerate(("LiFFT", "DUET", "ST")):
            measurement = measurements.get(tool)
            if measurement:
                damage = measurement.get("total_cumulative_damage")
                probability = measurement.get("probability_outcome")
                self.risk_table.item(row, 1).setText("" if damage is None else str(damage))
                self.risk_table.item(row, 2).setText("" if probability is None else str(probability))
                color = job_risk_color(
                    tool,
                    damage,
                    measurement.get("unit") or self.parent().selectedMeasurementSystem,
                )
            else:
                self.risk_table.item(row, 1).setText("")
                self.risk_table.item(row, 2).setText("")
                color = "#D9E1E6"
            self.risk_table.item(row, 1).setBackground(QColor(color))
            self.risk_table.item(row, 2).setBackground(QColor(color))
        self.risk_table.blockSignals(False)

    def setProfileEditability(self, editable, *, new_job=False):
        self.risk_table.setEnabled(True)
        for row in range(self.risk_table.rowCount()):
            for column in (1, 2):
                item = self.risk_table.item(row, column)
                flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
                if editable and column == 1:
                    flags |= Qt.ItemIsEditable
                item.setFlags(flags)
        for control in (self.profile_name_input, self.profile_reference_input):
            control.setReadOnly(not editable)
        for control in (self.profile_methodology_input, self.profile_notes_input):
            control.setReadOnly(not editable)
        for control in (
            self.profile_source_combo,
            self.profile_sample_size,
            self.profile_assessed_on,
            self.profile_valid_from,
            self.profile_valid_to,
        ):
            control.setEnabled(editable)
        profile = self.selectedProfile()
        self.new_profile_button.setEnabled(not new_job and profile is not None)
        self.approve_profile_button.setEnabled(bool(profile and profile["status"] == "draft"))
        self.current_profile_button.setEnabled(
            bool(profile and profile["status"] == "approved" and not profile["is_current"])
        )
        self.retire_profile_button.setEnabled(
            bool(profile and profile["status"] != "retired")
        )

    def loadSelectedProfile(self):
        profile = self.selectedProfile()
        if profile is None:
            return
        connection = connect_database(self.parent().projectdatabasePath, read_only=True)
        try:
            measurements = profile_measurements(connection, profile["id"])
        finally:
            connection.close()
        status = profile["status"].title()
        if profile["is_current"]:
            status += " | Current"
        self.profile_status_label.setText(status)
        self.profile_name_input.setText(profile["name"] or "")
        source_index = self.profile_source_combo.findData(profile["source_type"])
        self.profile_source_combo.setCurrentIndex(max(0, source_index))
        self.profile_reference_input.setText(profile["source_reference"] or "")
        self.profile_methodology_input.setPlainText(profile["methodology"] or "")
        self.profile_notes_input.setPlainText(profile["notes"] or "")
        self.profile_sample_size.setValue(
            profile["sample_size"] if profile["sample_size"] is not None else -1
        )
        self.setOptionalDateValue(self.profile_assessed_on, profile["assessed_on"])
        self.setOptionalDateValue(self.profile_valid_from, profile["valid_from"])
        self.setOptionalDateValue(self.profile_valid_to, profile["valid_to"])
        self.setMeasurementValues(measurements)
        self.setProfileEditability(profile["status"] == "draft")

    def measurementPayload(self):
        measurements = []
        for row, tool in enumerate(("LiFFT", "DUET", "ST")):
            damage_text = self.risk_table.item(row, 1).text().strip()
            probability_text = self.risk_table.item(row, 2).text().strip()
            try:
                damage = float(damage_text) if damage_text else None
                probability = float(probability_text) if probability_text else None
            except ValueError as error:
                raise JobRiskProfileError(f"{tool} measurements must be numeric.") from error
            if (damage is None) != (probability is None):
                raise JobRiskProfileError(
                    f"{tool} requires both cumulative damage and outcome probability."
                )
            measurements.append(
                {
                    "tool_id": tool,
                    "total_cumulative_damage": damage,
                    "probability_outcome": probability,
                    "unit": self.parent().selectedMeasurementSystem,
                }
            )
        return measurements

    def saveDraftControls(self, connection, profile_id):
        save_draft_profile(
            connection,
            profile_id,
            name=self.profile_name_input.text(),
            source_type=self.profile_source_combo.currentData(),
            source_reference=self.profile_reference_input.text().strip(),
            methodology=self.profile_methodology_input.toPlainText().strip(),
            sample_size=(
                self.profile_sample_size.value()
                if self.profile_sample_size.value() >= 0
                else None
            ),
            assessed_on=self.optionalDateValue(self.profile_assessed_on),
            valid_from=self.optionalDateValue(self.profile_valid_from),
            valid_to=self.optionalDateValue(self.profile_valid_to),
            notes=self.profile_notes_input.toPlainText().strip(),
            measurements=self.measurementPayload(),
        )

    def newProfileVersion(self):
        job_id = self.job_id_combo.currentText().strip()
        profile = self.selectedProfile()
        if not job_id or profile is None:
            QMessageBox.warning(self, "Risk Profile", "Save the Job before creating a profile version.")
            return
        connection = connect_database(self.parent().projectdatabasePath)
        try:
            profile_id = create_draft_profile(
                connection,
                job_id,
                copy_from_profile_id=profile["id"],
            )
            connection.commit()
        except (sqlite3.Error, JobRiskProfileError) as error:
            connection.rollback()
            QMessageBox.critical(self, "Risk Profile", str(error))
            return
        finally:
            connection.close()
        self.loadProfiles(job_id, profile_id)
        self.profile_tabs.setCurrentIndex(1)

    def approveSelectedProfile(self):
        profile = self.selectedProfile()
        if not profile or profile["status"] != "draft":
            return
        connection = connect_database(self.parent().projectdatabasePath)
        try:
            self.saveDraftControls(connection, profile["id"])
            approve_profile(connection, profile["id"])
            connection.commit()
        except (sqlite3.Error, JobRiskProfileError) as error:
            connection.rollback()
            QMessageBox.warning(self, "Profile Not Approved", str(error))
            return
        finally:
            connection.close()
        self.loadProfiles(profile["job_id"], profile["id"])

    def makeSelectedProfileCurrent(self):
        profile = self.selectedProfile()
        if not profile:
            return
        connection = connect_database(self.parent().projectdatabasePath)
        try:
            make_profile_current(connection, profile["id"])
            connection.commit()
        except (sqlite3.Error, JobRiskProfileError) as error:
            connection.rollback()
            QMessageBox.warning(self, "Risk Profile", str(error))
            return
        finally:
            connection.close()
        self.loadProfiles(profile["job_id"], profile["id"])

    def retireSelectedProfile(self):
        profile = self.selectedProfile()
        if not profile:
            return
        answer = QMessageBox.question(
            self,
            "Retire Risk Profile",
            f"Retire version {profile['version']} of this Job Risk Profile?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        connection = connect_database(self.parent().projectdatabasePath)
        try:
            retire_profile(connection, profile["id"])
            connection.commit()
        except (sqlite3.Error, JobRiskProfileError) as error:
            connection.rollback()
            QMessageBox.warning(self, "Risk Profile", str(error))
            return
        finally:
            connection.close()
        self.loadProfiles(profile["job_id"], profile["id"])




    def handleDamageEdit(self, row, col):
        if col != 1:
            return  # Only respond to cumulative damage edits
    
        tool = self.risk_table.item(row, 0).text()
        dmg_item = self.risk_table.item(row, 1)
        prob_item = self.risk_table.item(row, 2)
    
        try:
            damage = float(dmg_item.text())
        except ValueError:
            return
    
        if tool == "LiFFT":
            tool_obj = LiFFT(self.parent().selectedMeasurementSystem, 0, 0, 0)
        elif tool == "DUET":
            tool_obj = DUET(0, 0)
        elif tool == "ST":
            tool_obj = TST(self.parent().selectedMeasurementSystem, "", 0, 0, 0)
        else:
            return
    
        #risk = round(tool_obj.riskFromDamage(damage) * 100, 1)
        #color = tool_obj.colorFromDamageRisk(damage)
        
        if damage <= 0:
            risk = 0.0
            color = "#ffffff"
        else:
            risk = round(tool_obj.riskFromDamage(damage) * 100, 1)
            color = job_risk_color(tool, damage, self.parent().selectedMeasurementSystem)
    
        
        prob_item.setText(f"{risk}")
        prob_item.setBackground(QColor(color))
        dmg_item.setBackground(QColor(color))




    def deleteJob(self):
        """
        Handles the Delete button click event for the Job window.
        Deletes the selected job from the database, including its JobMeasurement entries.
        """
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting jobs.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete job.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     "Are you sure you want to delete this job?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Get selected Job ID
        job_id = self.job_id_combo.currentText().strip()
        if not job_id:
            QMessageBox.warning(self, "Error", "No Job ID selected. Unable to delete.")
            return
    
        conn = None
        try:
            conn = connect_database(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
    
            # Delete the job (JobMeasurement will cascade delete)
            cursor.execute("""
                DELETE FROM Job
                WHERE id = ?
            """, (job_id,))
            conn.commit()
    
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Job '{job_id}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Job '{job_id}' has been deleted successfully.")
    
            # Remove the job from the combo box and reset UI
            self.job_id_combo.removeItem(self.job_id_combo.currentIndex())
            if self.job_id_combo.count() > 0:
                self.job_id_combo.setCurrentIndex(0)
                self.loadJobDetails()
            else:
                # Clear input fields
                self.job_id_combo.blockSignals(True)
                self.job_id_combo.setCurrentIndex(-1)
                self.job_id_combo.setEditText("")
                self.job_id_combo.blockSignals(False)
            
                self.job_name_input.clear()
                self.job_description_input.clear()
            
                # Clear all rows in the risk_table
                for row in range(3):  # 3 tools
                    self.risk_table.blockSignals(True)
                    self.risk_table.item(row, 1).setText("0.0")
                    self.risk_table.item(row, 2).setText("0.0")
                    self.risk_table.item(row, 1).setBackground(QColor("#ffffff"))
                    self.risk_table.item(row, 2).setBackground(QColor("#ffffff"))
                    self.risk_table.blockSignals(False)
            
            
            
    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the job: {e}")
    
        finally:
            if conn is not None:
                conn.close()


    def cancelJob(self):
        """
        Handles the Cancel button click event.
        Enables navigation buttons and resets the Job ID combo box to the first item if available.
        """
        # Enable navigation and management buttons
        self.first_button.setEnabled(True)
        self.previous_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.last_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.search_button.setEnabled(True)
    
        # Reset the Job ID combo box to the first index if items exist
        if self.job_id_combo.count() > 0:
            self.job_id_combo.setCurrentIndex(0)
            self.loadJobDetails()

        # TODO: Add any additional cancel behavior here (e.g., status message, undo, etc.)



    def getJobs(self):
        """
        Retrieves all job IDs from the database.
    
        Returns:
            list: A list of job IDs (as strings), or None if error.
        """
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing jobs.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve job data.")
            return
    
        try:
            conn = connect_database(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = "SELECT id FROM Job"
            cursor.execute(query)
            jobs = cursor.fetchall()
            conn.close()

            return [str(row[0]) for row in jobs]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve jobs:\n{str(e)}")
            return []

    
    def loadJobs(self):
        """
        Loads all job IDs into the job combo box.
        """
        jobs_list = self.getJobs()
        if jobs_list is not None:
            self.job_id_combo.clear()
            self.job_id_combo.addItems(jobs_list)

    
    
    
    def firstJob(self):
        if self.job_id_combo.count() > 0:
            self.job_id_combo.setCurrentIndex(0)

    def previousJob(self):
        current_index = self.job_id_combo.currentIndex()
        if current_index > 0:
            self.job_id_combo.setCurrentIndex(current_index - 1)
    
    def nextJob(self):
        current_index = self.job_id_combo.currentIndex()
        if current_index < self.job_id_combo.count() - 1:
            self.job_id_combo.setCurrentIndex(current_index + 1)

    def lastJob(self):
        if self.job_id_combo.count() > 0:
            self.job_id_combo.setCurrentIndex(self.job_id_combo.count() - 1)



    # Custom handler for the Close button
    def closeJob(self):
        self.saveVars()
        self.close()  # Trigger the close event

    def saveVars(self):
        # Extract values from controls in the worker window
        job_id = self.job_id_combo.currentText().strip() 
        self.parent().editJobName = job_id
        # Override the closeEvent method to handle the window close event
        
    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
    
    
    
    def newJob(self):
        """
        Prepares the Job Window for entering a new job.
        Clears all inputs and disables navigation buttons.
        """
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing jobs.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to create new job.")
            return
    
        # Clear input fields
        self.job_id_combo.blockSignals(True)
        self.job_id_combo.setCurrentIndex(-1)
        self.job_id_combo.setEditText("")
        self.job_id_combo.blockSignals(False)
    
        self.job_name_input.clear()
        self.job_description_input.clear()
        self.clearProfileControls()
    
        # Disable navigation and management buttons
        self.first_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.search_button.setEnabled(False)
    
        # Set focus on the job ID field
        self.job_id_combo.setFocus()





    
    def saveJob(self):
        """
        Saves or updates the job data in the database,
        including its associated JobMeasurement values for LiFFT, DUET, and ST.
        """
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving jobs.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save job.")
            return
    
        job_id = self.job_id_combo.currentText().strip()
        if not job_id:
            QMessageBox.warning(self, "Validation Error", "Job ID is required.")
            return
    
        if " " in job_id:
            QMessageBox.warning(self, "Validation Error", "Job ID cannot contain spaces.")
            return

        job_name = self.job_name_input.text().strip()
        job_description = self.job_description_input.toPlainText().strip()
    
        database_path = self.parent().projectdatabasePath
        conn = connect_database(database_path)
        try:
            profile = self.selectedProfile()
            if profile and profile["status"] == "draft":
                conn.execute(
                    """
                    UPDATE Job
                    SET name = ?, description = ?, active = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (job_name, job_description, job_id),
                )
                self.saveDraftControls(conn, profile["id"])
                saved_profile_id = profile["id"]
                success_message = f"Draft profile v{profile['version']} saved."
            elif profile:
                conn.execute(
                    """
                    UPDATE Job
                    SET name = ?, description = ?, active = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (job_name, job_description, job_id),
                )
                saved_profile_id = profile["id"]
                success_message = f"Job '{job_id}' updated."
            else:
                measurements = [
                    measurement
                    for measurement in self.measurementPayload()
                    if measurement["total_cumulative_damage"] is not None
                ]
                if not measurements:
                    raise JobRiskProfileError(
                        "Enter at least one complete ergonomic-tool measurement."
                    )
                saved_profile_id = save_job_with_measurements(
                    conn,
                    job_id=job_id,
                    name=job_name,
                    description=job_description,
                    measurements=measurements,
                )
                success_message = f"Job '{job_id}' saved with an approved risk profile."
    
            conn.commit()
    
            QMessageBox.information(self, "Success", success_message)
    
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)

            current_text = self.job_id_combo.currentText()
            self.loadJobs()
            index = self.job_id_combo.findText(current_text)
            if index != -1:
                self.job_id_combo.setCurrentIndex(index)
            self.loadProfiles(job_id, saved_profile_id)
    
        except (sqlite3.Error, JobRiskProfileError) as e:
            conn.rollback()
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the job:\n{str(e)}")
    
        finally:
            conn.close()


    
    def searchJob(self):
        """
        Handles the Search button click event for the Job window.
        Allows the user to search for a job by its ID.
        """
        # Validate that the project file and database are created
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before searching.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to perform search.")
            return
    
        # Create the search dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Job")
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)
    
        # Job ID Search
        id_layout = QHBoxLayout()
        id_label = QLabel("Search by Job ID:")
        id_input = QLineEdit()
        id_layout.addWidget(id_label)
        id_layout.addWidget(id_input)
        layout.addLayout(id_layout)
    
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
    
        # Function to handle the OK button click
        def performSearch():
            job_id = ""
            conn = connect_database(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            try:
                # Search by Job ID
                if id_input.text().strip():
                    cursor.execute("""
                        SELECT id FROM Job 
                        WHERE id = ?
                    """, (id_input.text().strip(),))
                    result = cursor.fetchone()
                    if result:
                        job_id = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search job:\n{str(e)}")
            finally:
                conn.close()
    
            if job_id:
                # Set the job ID in the combo box and trigger the index change event
                index = self.job_id_combo.findText(job_id)
                if index != -1:
                    self.job_id_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Job ID found in database but not in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No job found with the given criteria.")
    
            dialog.accept()

        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)
    
        # Show the dialog
        dialog.exec_()

    
    
        
 
    def loadJobDetails(self):
        """
        Loads the details of the selected job into the UI controls,
        including JobMeasurement values for each ErgoTool.
        """
        selected_job_id = self.job_id_combo.currentText().strip()
    
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing jobs.")
            return

        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to load job details.")
            return

        if not selected_job_id:
            return

        conn = None
        try:
            conn = connect_database(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            # Load Job basic info
            cursor.execute("SELECT id, name, description FROM Job WHERE id = ?", (selected_job_id,))
            job_data = cursor.fetchone()
    
            if job_data:
                job_id, name, description = ("" if v is None else v for v in job_data)
                self.job_id_combo.setCurrentText(job_id)
                self.job_name_input.setText(name)
                self.job_description_input.setPlainText(description)
            else:
                QMessageBox.warning(self, "Error", f"No job data found for ID: {selected_job_id}")
                return
    
            conn.close()
            conn = None
            self.loadProfiles(selected_job_id)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load job details:\n{str(e)}")
        finally:
            if conn is not None:
                conn.close()
