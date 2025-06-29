import sys
import math
import pycountry
import locale 
import os
import time
import sqlite3

from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit, QSpinBox, 
    QComboBox, QPushButton, QTabWidget, QWidget, QGridLayout, QMessageBox, QDialogButtonBox
)

from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QPixmap, QRegExpValidator

from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import QRegularExpression, QRegExp


class WorkerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Workers Management")
        self.resize(600, 400)

        self.setupUI()

        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadWorkers(0)
            
            # Get the current text from the workerComboBox in the parent window
            worker_combo_text = self.parent().workerComboBox.currentText()

            # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
            worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""

            index = self.worker_id_combo.findText(worker_id)
            if index != -1:
                self.worker_id_combo.setCurrentIndex(index)


    def setupUI(self):
            
        # Create a bold font
        bold_font = QFont()
        bold_font.setBold(True)

        main_layout = QVBoxLayout(self)

        # Tab Widget
        self.tabWidget = QTabWidget()
        # Connect the tab widget's currentChanged signal to a handler
        self.tabWidget.currentChanged.connect(self.onTabChanged)

        main_layout.addWidget(self.tabWidget)
        

        # General Information Tab
        self.general_tab = QWidget()
        self.setupGeneralTab()
        self.tabWidget.addTab(self.general_tab, "General Information")


        # Head and Neck Tab
        self.head_neck_tab = QWidget()
        self.setupHeadNeckTab()
        #self.tabWidget.addTab(self.head_neck_tab, "Head and Neck")
        
        # Upper Body Measurements Tab
        self.upper_body_tab = QWidget()
        self.setupUpperBodyTab()
        #self.tabWidget.addTab(self.upper_body_tab, "Upper Body Measurements")

        # Lower Body Measurements Tab
        self.lower_body_tab = QWidget()
        self.setupLowerBodyTab()
        #self.tabWidget.addTab(self.lower_body_tab, "Lower Body Measurements")

        for i in range(1, self.tabWidget.count()):
            self.tabWidget.tabBar().setTabVisible(i, False)
    

        # Buttons
        button_layout = QHBoxLayout()
        
        self.first_button = QPushButton("|<")
        self.first_button.setFont(bold_font)  # Set bold font
        self.first_button.clicked.connect(self.firstWorker)
        
        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)  # Set bold font
        self.previous_button.clicked.connect(self.previousWorker)
        
        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)  # Set bold font
        self.new_button.clicked.connect(self.newWorker)
        
        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)  # Set bold font
        self.save_button.clicked.connect(self.saveWorker)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)  # Set bold font
        self.delete_button.clicked.connect(self.deleteWorker)
        
        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)  # Set bold font
        self.search_button.clicked.connect(self.searchWorker)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)  # Set bold font
        self.cancel_button.clicked.connect(self.cancelWorker)
        
        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)  # Set bold font
        self.close_button.clicked.connect(self.closeWorker)
        
        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)  # Set bold font
        self.next_button.clicked.connect(self.nextWorker)
        
        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)  # Set bold font
        self.last_button.clicked.connect(self.lastWorker)

        
        button_layout.addWidget(self.first_button)
        button_layout.addWidget(self.previous_button)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.last_button)
        
        main_layout.addLayout(button_layout)


    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
        
    # Custom handler for the Close button
    def closeWorker(self):
        self.saveVars()
        self.close()  # Trigger the close event


    def saveVars(self):
        # Extract values from controls in the worker window
        worker_id = self.worker_id_combo.currentText().strip() 
        last_name = self.last_name_input.text().strip()  
        first_name = self.first_name_input.text().strip() 
        # Set the parent's variables 
        self.parent().editWorkerWindowID = worker_id
        self.parent().editWorkerWindowLastName = last_name
        self.parent().editWorkerWindowFirstName = first_name


    def searchWorker(self):
    
        # Validate that the project file and database are created
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before searching.")
            return

        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to perform search.")
            return


        # Select the General Info tab
        self.tabWidget.setCurrentIndex(0)
        
        # Create the search dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Worker")
        dialog.setFixedSize(400, 200)
        layout = QVBoxLayout(dialog)

        # ID Search
        id_layout = QHBoxLayout()
        id_label = QLabel("Search by ID:")
        id_input = QLineEdit()
        id_layout.addWidget(id_label)
        id_layout.addWidget(id_input)
        layout.addLayout(id_layout)

        # Name Search
        name_layout = QHBoxLayout()
        name_label = QLabel("Search by Name:")
        first_name_input = QLineEdit()
        first_name_input.setPlaceholderText("First Name")
        last_name_input = QLineEdit()
        last_name_input.setPlaceholderText("Last Name")
        name_layout.addWidget(name_label)
        name_layout.addWidget(last_name_input)
        name_layout.addWidget(first_name_input)
        layout.addLayout(name_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        # Function to handle the OK button click
        def performSearch():
            worker_id = ""
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            try:
                # Search by ID if provided
                if id_input.text().strip():
                    cursor.execute("SELECT id FROM Worker WHERE id = ?", (id_input.text().strip(),))
                    result = cursor.fetchone()
                    if result:
                        worker_id = result[0]
                else:
                    # Search by First Name and Last Name if ID is not provided
                    first_name = first_name_input.text().strip()
                    last_name = last_name_input.text().strip()
                    if first_name and last_name:
                        cursor.execute("SELECT id FROM Worker WHERE first_name = ? AND last_name = ?", (first_name, last_name))
                        result = cursor.fetchone()
                        if result:
                            worker_id = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search worker:\n{str(e)}")
            finally:
                conn.close()

            if worker_id:
                # Set the worker ID in the combo box and trigger the index change event
                #print("Worker ID:", worker_id)
                index = self.worker_id_combo.findText(worker_id)
                if index != -1:
                    self.worker_id_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Worker ID not found in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No worker found with the given criteria.")

            dialog.accept()

        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)

        # Show the dialog
        dialog.exec_()



    def onTabChanged(self, index):
        if (index > 0):
            self.updateWorkerInfoLabels()


    def updateWorkerInfoLabels(self):
        #worker_id = self.worker_id_input.text().strip() if hasattr(self, 'worker_id_input') else ""
        #first_name = self.name_input.text().strip() if hasattr(self, 'name_input') else ""
        #last_name = self.last_name_input.text().strip() if hasattr(self, 'last_name_input') else ""

        worker_id = self.worker_id_combo.currentText().strip() 
        first_name = self.first_name_input.text().strip() 
        last_name = self.last_name_input.text().strip() 

        # Update Head and Neck Labels
        self.head_neck_id_label.setText(f"<b>ID:</b> {worker_id or ''}")
        self.head_neck_first_name_label.setText(f"<b>First Name:</b> {first_name or ''}")
        self.head_neck_last_name_label.setText(f"<b>Last Name:</b> {last_name or ''}")

        # Update Upper Body Labels
        self.upper_body_id_label.setText(f"<b>ID:</b> {worker_id or ''}")
        self.upper_body_first_name_label.setText(f"<b>First Name:</b> {first_name or ''}")
        self.upper_body_last_name_label.setText(f"<b>Last Name:</b> {last_name or ''}")

        # Update Lower Body Labels
        self.lower_body_id_label.setText(f"<b>ID:</b> {worker_id or ''}")
        self.lower_body_first_name_label.setText(f"<b>First Name:</b> {first_name or ''}")
        self.lower_body_last_name_label.setText(f"<b>Last Name:</b> {last_name or ''}")



    def deleteWorker(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting workers.")
            return
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete worker.")
            return

        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                      "Are you sure you want to delete this worker?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Get the selected Worker ID
        worker_id = self.worker_id_combo.currentText()
        if not worker_id:
            QMessageBox.warning(self, "Error", "No Worker ID selected. Unable to delete.")
            return

        try:
            # Connect to the database
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            # TODO: warning the user if tool data exist
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Delete the worker from the database
            cursor.execute("DELETE FROM Worker WHERE id = ?", (worker_id,))
            conn.commit()

            # Check if the worker was successfully deleted
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Worker ID '{worker_id}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Worker ID '{worker_id}' has been deleted successfully.")
            
            # TODO: other delete code if needed..

            # Refresh the Worker ID combo box
            self.worker_id_combo.removeItem(self.worker_id_combo.currentIndex())

            # Reset the Worker ID combo box to the first index if items exist
            if self.worker_id_combo.count() > 0:
                self.worker_id_combo.setCurrentIndex(0)
                self.loadWorkerDetails()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the worker: {e}")
        finally:
            conn.close()

    def newWorker(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
            
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save worker.")
            return
    
            
        # Clear inputs in the General tab
        #self.worker_id_combo.setCurrentIndex(-1)  # Clear selection in the combobox
        self.worker_id_combo.blockSignals(True)  # Temporarily block signals
        self.worker_id_combo.setEditText("")     # Set the text to ""
        self.worker_id_combo.blockSignals(False) # Re-enable signals

        self.first_name_input.clear()
        self.last_name_input.clear()
        self.dob_input.setDate(QDate.currentDate())
        self.age_label.setText("0")
        self.height_input.clear()
        self.weight_input.clear()
        self.address_input.clear()
        self.city_input.clear()
        self.zipcode_input.clear()
        self.country_combo.setCurrentIndex(-1)
        self.state_combo.setCurrentIndex(-1)
        self.date_of_hiring_input.setDate(QDate.currentDate())
        self.email_input.clear()

        # Clear inputs in the Head and Neck tab
        self.head_circumference_input.clear()
        self.neck_circumference_input.clear()
        self.head_length_input.clear()
        self.head_breadth_input.clear()
        self.head_height_input.clear()
        self.neck_length_input.clear()
        self.neck_angle_input.clear()
        self.head_angle_input.clear()
        self.head_volume_label.setText("Head Volume (cm³): 0.0")
        self.neck_stress_index_label.setText("Neck-Stress Index: 0.0")
        self.cervical_spine_alignment_label.setText("Cervical Spine Alignment: Neutral")
        self.neck_torque_label.setText("Neck Torque (N·m): 0.0")
        self.neck_head_ratio_label.setText("Neck-Head Ratio: 0.0")

        # Clear inputs in the Upper Body tab
        self.shoulder_width_input.clear()
        self.chest_circumference_input.clear()
        self.upper_arm_length_input.clear()
        self.forearm_length_input.clear()
        self.hand_length_input.clear()
        self.hand_breadth_input.clear()
        self.arm_span_input.clear()
        self.torso_length_input.clear()
        self.spinal_curvature_input.clear()
        self.shoulder_angle_input.clear()
        self.upper_limb_length_label.setText("Upper Limb Length (cm): 0.0")
        self.arm_hand_ratio_label.setText("Arm-Hand Ratio: 0.0")
        self.shoulder_to_hand_distance_label.setText("Shoulder-to-Hand Distance (cm): 0.0")
        self.arm_volume_label.setText("Arm Volume (cm³): 0.0")
        self.grip_strength_index_label.setText("Grip Strength Index: 0.0")
        self.torso_to_limb_ratio_label.setText("Torso-to-Limb Ratio: 0.0")
        self.postural_load_index_label.setText("Postural Load Index: 0.0")
        self.total_upper_body_volume_label.setText("Total Upper Body Volume (cm³): 0.0")

        # Clear inputs in the Lower Body tab
        self.hip_width_input.clear()
        self.waist_circumference_input.clear()
        self.thigh_circumference_input.clear()
        self.leg_length_input.clear()
        self.thigh_length_input.clear()
        self.lower_leg_length_input.clear()
        self.foot_length_input.clear()
        self.foot_breadth_input.clear()
        self.knee_height_input.clear()
        self.hip_angle_input.clear()
        self.knee_angle_input.clear()
        self.ankle_angle_input.clear()
        self.total_leg_length_label.setText("Total Leg Length (cm): 0.0")
        self.leg_proportion_index_label.setText("Leg Proportion Index: 0.0")
        self.foot_to_leg_ratio_label.setText("Foot-to-Leg Ratio: 0.0")
        self.lower_limb_volume_label.setText("Lower Limb Volume (cm³): 0.0")
        self.knee_torso_distance_label.setText("Knee-Torso Distance (cm): 0.0")
        self.step_length_label.setText("Step Length (cm): 0.0")
        self.postural_stability_index_label.setText("Postural Stability Index: 0.0")

        # TODO: Add clearing logic for any additional fields in other tabs as needed.

        # Disable navigation and management buttons
        self.first_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.search_button.setEnabled(False)

        #QMessageBox.information(self, "New Worker", "Ready to add a new worker.")
        self.tabWidget.setCurrentIndex(0)
        self.worker_id_combo.setFocus()
        

    def cancelWorker(self):
        """
        Handles the Cancel button click event. 
        Enables navigation buttons and resets the Worker ID combo box to the first item if available.
        """
        # Enable navigation and other disabled buttons
        self.first_button.setEnabled(True)
        self.previous_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.last_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.search_button.setEnabled(True)

        # Reset the Worker ID combo box to the first index if items exist
        if self.worker_id_combo.count() > 0:
            self.worker_id_combo.setCurrentIndex(0)
            self.loadWorkerDetails()

        # TODO: other cancel code if needed..


    # Navigation Handlers
    def firstWorker(self):
        if self.worker_id_combo.count() > 0:
            self.worker_id_combo.setCurrentIndex(0)
            
        if (self.tabWidget.currentIndex() > 0):
            self.updateWorkerInfoLabels()

    def previousWorker(self):
        current_index = self.worker_id_combo.currentIndex()
        if current_index > 0:
            self.worker_id_combo.setCurrentIndex(current_index - 1)
        
        if (self.tabWidget.currentIndex() > 0):
            self.updateWorkerInfoLabels()

    def nextWorker(self):
        current_index = self.worker_id_combo.currentIndex()
        if current_index < self.worker_id_combo.count() - 1:
            self.worker_id_combo.setCurrentIndex(current_index + 1)
            
        if (self.tabWidget.currentIndex() > 0):
            self.updateWorkerInfoLabels()

    def lastWorker(self):
        if self.worker_id_combo.count() > 0:
            self.worker_id_combo.setCurrentIndex(self.worker_id_combo.count() - 1)
            
        if (self.tabWidget.currentIndex() > 0):
            self.updateWorkerInfoLabels()

    def setupGeneralTab(self):
        layout = QGridLayout()

        # Worker ID
        layout.addWidget(QLabel("ID:"), 0, 0)
        self.worker_id_combo = QComboBox()
        self.worker_id_combo.setEditable(True)  # Allow the user to write in the combobox
        self.worker_id_combo.currentIndexChanged.connect(self.loadWorkerDetails)
        layout.addWidget(self.worker_id_combo, 0, 1)


        # Name
        layout.addWidget(QLabel("First Name:"), 1, 0)
        self.first_name_input = QLineEdit()
        layout.addWidget(self.first_name_input, 1, 1)

        # Last Name
        layout.addWidget(QLabel("Last Name:"), 2, 0)
        self.last_name_input = QLineEdit()
        layout.addWidget(self.last_name_input, 2, 1)

        # Date of Birth
        layout.addWidget(QLabel("Date of Birth:"), 3, 0)
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDate(QDate.currentDate())
        self.dob_input.dateChanged.connect(self.calculateAge)
        layout.addWidget(self.dob_input, 3, 1)

        # Age
        age_label = QLabel("Age:")
        layout.addWidget(age_label, 4, 0)
        self.age_label = QLabel("0")
        self.age_label.setFixedHeight(30)  # Set the desired height in pixels
        layout.addWidget(self.age_label, 4, 1)

        # Gender Combo Box
        gender_label = QLabel("Sex:")
        layout.addWidget(gender_label, 5, 0)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Female", "Male"])
        self.gender_combo.setCurrentIndex(0)  # Set default to Female
        self.gender_combo.setEditable(False)  # Keep it non-editable by default
        # self.gender_combo.setEditable(True)  # Uncomment this line to make it editable if needed
        layout.addWidget(self.gender_combo, 5, 1)
        

        # Height
        layout.addWidget(QLabel("Height (inch):"), 6, 0)
        self.height_input = QLineEdit()
        self.height_input.setValidator(QDoubleValidator(50.0, 300.0, 2))
        layout.addWidget(self.height_input, 6, 1)

        # Weight
        layout.addWidget(QLabel("Weight (lb):"), 7, 0)
        self.weight_input = QLineEdit()
        self.weight_input.setValidator(QDoubleValidator(10.0, 300.0, 2))
        layout.addWidget(self.weight_input, 7, 1)

        # Address
        layout.addWidget(QLabel("Address:"), 8, 0)
        self.address_input = QLineEdit()
        layout.addWidget(self.address_input, 8, 1)
        
        
        # City
        layout.addWidget(QLabel("City:"), 9, 0)
        self.city_input = QLineEdit()
        layout.addWidget(self.city_input, 9, 1)


        # State
        layout.addWidget(QLabel("State:"), 10, 0)
        self.state_combo = QComboBox()
        self.state_combo.addItem("Outside US")  # Default value
        self.state_combo.setEditable(True)  # Allow the user to write in the combobox
                

        layout.addWidget(self.state_combo, 10, 1)

        # Country
        layout.addWidget(QLabel("Country:"), 11, 0)
        self.country_combo = QComboBox()

        # Populate the country combobox using pycountry
        
        countries = sorted([country.name for country in pycountry.countries])
        self.country_combo.addItems(countries)
        self.country_combo.setEditable(True)  # Allow the user to write in the combobox
                
        # Get the system's country using locale and timezone
        
        # Retrieve the system's country from locale
        try:
            system_locale = locale.getdefaultlocale()
            country_code_from_locale = system_locale[0].split('_')[-1] if system_locale else None
        except Exception:
            country_code_from_locale = None

        # Fallback: Attempt to deduce the country using timezone
        try:
            timezone = time.tzname[0]
            country_code_from_timezone = timezone.split('/')[-1] if '/' in timezone else None
        except Exception:
            country_code_from_timezone = None

        # Combine the sources to find the system country
        system_country_code = country_code_from_locale or country_code_from_timezone
        system_country = next(
            (country.name for country in pycountry.countries if country.alpha_2 == system_country_code),
            None
        )

        # Set the detected country if valid
        if system_country and system_country in countries:
            self.country_combo.setCurrentText(system_country)

        # Connect the country combobox change event
        self.country_combo.currentIndexChanged.connect(self.populateStatesForUSA)
        
        layout.addWidget(self.country_combo, 11, 1)
        
        self.populateStatesForUSA()
        

        # Zip Code
        layout.addWidget(QLabel("Zip Code:"), 12, 0)
        self.zipcode_input = QLineEdit()
        #self.zip_code_input.setValidator(QRegExpValidator(QRegExp(r"^\d{5}(-\d{4})?$")))  # US ZIP Code validation
        # International ZIP code validation: Allows numbers (e.g., 5480000) and alphanumerics (e.g., A1A 1A1)
        zip_code_regex = QRegExp(r"^[A-Za-z0-9\- ]{3,10}$")
        self.zipcode_input.setValidator(QRegExpValidator(zip_code_regex))
        layout.addWidget(self.zipcode_input, 12, 1)

        # Email
        layout.addWidget(QLabel("Email:"), 13, 0)
        self.email_input = QLineEdit()
        # Set up an email validation pattern
        email_regex = QRegularExpression(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        email_validator = QRegularExpressionValidator(email_regex, self.email_input)
        self.email_input.setValidator(email_validator)
        layout.addWidget(self.email_input, 13, 1)

        # Date of Hiring
        layout.addWidget(QLabel("Date of Hiring:"), 14, 0)
        self.date_of_hiring_input = QDateEdit()
        self.date_of_hiring_input.setCalendarPopup(True)
        self.date_of_hiring_input.setDate(QDate.currentDate())
        self.date_of_hiring_input.setMinimumDate(QDate(1950, 1, 1))
        self.date_of_hiring_input.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.date_of_hiring_input, 14, 1)

	# Alternatively, align all widgets to the top
        #for row in range(layout.rowCount()):
        #    for col in range(layout.columnCount()):
        #        item = layout.itemAtPosition(row, col)
        #        if item:
        #            widget = item.widget()
        #            if widget:
        #                widget.setAlignment(Qt.AlignTop)
                        
        self.general_tab.setLayout(layout)
        
        


    def getWorkers(self, order_by):
        """
        Retrieves workers from the database in the specified order.
    
        Args:
            order_by (int): 0 for ordering by Worker ID, 1 for ordering by Last Name.
    
        Returns:
            list: A list of strings formatted as <worker id>(<last name>, <first name>).
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
            
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save worker.")
            return

        # Determine the order column
        order_column = "id" if order_by == 0 else "last_name"

        # Connect to the database and query the workers
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = f"SELECT id, last_name, first_name FROM Worker ORDER BY {order_column}"
            cursor.execute(query)
            workers = cursor.fetchall()
            conn.close()

            # Format workers as <worker id>(<last name>, <first name>)
            return [f"{row[0]}" for row in workers]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve workers:\n{str(e)}")
            return []



    def loadWorkers(self, order_by):
        # Order workers by id (order_by = 0)
        workers_list = self.getWorkers(order_by)
        # Populate the worker combobox
        self.worker_id_combo.clear()
        self.worker_id_combo.addItems(workers_list)
    
    
    
    
    def loadWorkerDetails(self):
        # Get the selected worker ID
        selected_worker_id = self.worker_id_combo.currentText()
        
        
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
            
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save worker.")
            return
            
        if not selected_worker_id:
        #    QMessageBox.warning(self, "Error", "No worker selected.")
            return
        
        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
        
        try:
            # Fetch general worker info
            #cursor.execute("SELECT * FROM Worker WHERE id = ?", (selected_worker_id,))
            #worker_data = cursor.fetchone()
            cursor.execute("SELECT * FROM Worker WHERE id = ?", (selected_worker_id,))
            worker_data = cursor.fetchone()

            # Replace None from DB with an empty string in the worker_data tuple
            if worker_data:
                worker_data = tuple("" if value is None else value for value in worker_data)

            
            if worker_data:
                # Map worker_data to controls
                self.worker_id_combo.setCurrentText(worker_data[0])  # Worker ID
                self.first_name_input.setText(worker_data[1])  # First Name
                self.last_name_input.setText(worker_data[2])  # Last Name
    
                # Reconstruct Date of Birth from Year, Month, Day
                dob_year = int(worker_data[3]) if worker_data[3] else QDate.currentDate().year()
                dob_month = int(worker_data[4]) if worker_data[4] else QDate.currentDate().month()
                dob_day = int(worker_data[5]) if worker_data[5] else QDate.currentDate().day()
                dob = QDate(dob_year, dob_month, dob_day)
                self.dob_input.setDate(dob)
    
                # Gender Mapping
                gender_value = worker_data[6] if worker_data[6] else "Female"  # Default to Female
                gender_index = self.gender_combo.findText(gender_value)  # Get index of "Female" or "Male"
                if gender_index != -1:
                    self.gender_combo.setCurrentIndex(gender_index)
    
                self.height_input.setText(str(worker_data[7]))  # Height
                self.weight_input.setText(str(worker_data[8]))  # Weight    
                self.address_input.setText(worker_data[9])  # Address
                self.email_input.setText(worker_data[10])  # Email
    
                # Reconstruct Date of Hiring from Year, Month, Day
                hiring_year = int(worker_data[11]) if worker_data[11] else QDate.currentDate().year()
                hiring_month = int(worker_data[12]) if worker_data[12] else QDate.currentDate().month()
                hiring_day = int(worker_data[13]) if worker_data[13] else QDate.currentDate().day()
                hiring_date = QDate(hiring_year, hiring_month, hiring_day)
                self.date_of_hiring_input.setDate(hiring_date)

                self.city_input.setText(worker_data[14])  # City
                #self.state_combo.setCurrentText(worker_data[15])  # State
                self.country_combo.setCurrentText(worker_data[16])  # Country
                self.zipcode_input.setText(worker_data[17])  # Zip Code

                # Example: Populate Head and Neck data
                self.head_circumference_input.setText(str(worker_data[18]))  # Head Circumference
                self.neck_circumference_input.setText(str(worker_data[19]))  # Neck Circumference
                self.head_length_input.setText(str(worker_data[20]))  # Head Length
                self.neck_angle_input.setText(str(worker_data[21]))  # Neck Angle

                # Example: Populate Upper Body data
                self.shoulder_width_input.setText(str(worker_data[23]))  # Shoulder Width
                self.chest_circumference_input.setText(str(worker_data[24]))  # Chest Circumference

                # Example: Populate Lower Body data
                self.hip_width_input.setText(str(worker_data[28]))  # Hip Width
                self.leg_length_input.setText(str(worker_data[29]))  # Leg Length

                # Ensure correct state selection after updating country
                self.populateStatesForUSA()
                self.state_combo.setCurrentText(worker_data[15])  # Adjusted index for state
            else:
                QMessageBox.warning(self, "Error", f"No data found for Worker ID: {selected_worker_id}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load worker details: {str(e)}")
        
        finally:
            conn.close()

    
    def loadWorkerDetailsOld(self):
        # Get the selected worker ID
        selected_worker_id = self.worker_id_combo.currentText()
        
        
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
            
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save worker.")
            return
            
        if not selected_worker_id:
        #    QMessageBox.warning(self, "Error", "No worker selected.")
            return
        
        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
        
        try:
            # Fetch general worker info
            #cursor.execute("SELECT * FROM Worker WHERE id = ?", (selected_worker_id,))
            #worker_data = cursor.fetchone()
            cursor.execute("SELECT * FROM Worker WHERE id = ?", (selected_worker_id,))
            worker_data = cursor.fetchone()

            # Replace None from DB with an empty string in the worker_data tuple
            if worker_data:
                worker_data = tuple("" if value is None else value for value in worker_data)

            
            if worker_data:
                # Map worker_data to controls
                self.worker_id_combo.setCurrentText(worker_data[0])
                self.first_name_input.setText(worker_data[1])
                self.last_name_input.setText(worker_data[2])
                self.dob_input.setDate(QDate.fromString(worker_data[3], "yyyy-MM-dd"))
                self.height_input.setText(str(worker_data[4]))
                self.weight_input.setText(str(worker_data[5]))
                self.address_input.setText(worker_data[6])
                self.email_input.setText(worker_data[7])
                self.date_of_hiring_input.setDate(QDate.fromString(worker_data[8], "yyyy-MM-dd"))
                self.city_input.setText(worker_data[9])
                
                #self.state_combo.setCurrentText(worker_data[10])
                self.country_combo.setCurrentText(worker_data[11])
                
                #print("state: ",worker_data[10])
                #print("country: ", worker_data[11])
                
                self.zipcode_input.setText(worker_data[12])
                
                # Example: Populate Head and Neck data
                self.head_circumference_input.setText(str(worker_data[13]))
                #self.head_circumference_input.setText("" if worker_data[13] is None else str(worker_data[13]))

                self.neck_circumference_input.setText(str(worker_data[14]))
                self.head_length_input.setText(str(worker_data[15]))
                self.neck_angle_input.setText(str(worker_data[16]))

                # Example: Populate Upper Body data
                self.shoulder_width_input.setText(str(worker_data[17]))
                self.chest_circumference_input.setText(str(worker_data[18]))

                # Example: Populate Lower Body data
                self.hip_width_input.setText(str(worker_data[19]))
                self.leg_length_input.setText(str(worker_data[20]))

                # TODO:Add more mappings as needed for remaining fields
                
                
                # TODO: check the behaviour of the state and country data loading each time a worker data change
                self.populateStatesForUSA()
                self.state_combo.setCurrentText(worker_data[10])
            else:
                QMessageBox.warning(self, "Error", f"No data found for Worker ID: {selected_worker_id}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load worker details: {str(e)}")
        
        finally:
            conn.close()
    
    
    
    
    def calculateAge(self):
        today = QDate.currentDate()
        dob = self.dob_input.date()
        age = today.year() - dob.year() - ((today.month(), today.day()) < (dob.month(), dob.day()))
        self.age_label.setText(str(age))

    # Function to populate states if "United States" is selected
    def populateStatesForUSA(self):
        if self.country_combo.currentText() == "United States":
            self.state_combo.clear()
            us_states = [
                "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
                "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
                "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
                "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
                "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
                "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
                "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
            ]
            self.state_combo.addItems(us_states)
        else:
            self.state_combo.clear()
            self.state_combo.addItem("Outside US")

    
    def setupHeadNeckTab(self):
        # Create the Head and Neck tab
        head_neck_tab = QWidget()
        head_neck_main_layout = QHBoxLayout()  # Main horizontal layout to split controls and image

        # Left Layout for Controls
        head_neck_layout = QVBoxLayout()

        bold_font = QFont()
        bold_font.setBold(True)
        
        
        # Add a section for displaying ID, First Name, and Last Name
        info_layout = QHBoxLayout()
        # ID Label
        self.head_neck_id_label = QLabel("ID: ")
        #self.head_neck_id_label.setFont(bold_font)
        self.head_neck_id_label.setFixedWidth(200)
        info_layout.addWidget(self.head_neck_id_label)

        # First Name Label
        self.head_neck_first_name_label = QLabel("First Name: ")
        #self.head_neck_first_name_label.setFont(bold_font)
        self.head_neck_first_name_label.setFixedWidth(200)
        info_layout.addWidget(self.head_neck_first_name_label)

        # Last Name Label
        self.head_neck_last_name_label = QLabel("Last Name: ")
        #self.head_neck_last_name_label.setFont(bold_font)
        self.head_neck_last_name_label.setFixedWidth(200)
        info_layout.addWidget(self.head_neck_last_name_label)

        head_neck_layout.addLayout(info_layout)



        # Section for Direct Measurements
        direct_measurements_label = QLabel("Direct Measurements")
        direct_measurements_label.setFont(bold_font)
        head_neck_layout.addWidget(direct_measurements_label)

        # Head Circumference
        head_circumference_layout = QHBoxLayout()
        head_circumference_label = QLabel("Head Circumference (50–65 cm):")
        self.head_circumference_input = QLineEdit()
        self.head_circumference_input.setValidator(QDoubleValidator(50.0, 65.0, 2))
        head_circumference_layout.addWidget(head_circumference_label)
        head_circumference_layout.addWidget(self.head_circumference_input)
        head_neck_layout.addLayout(head_circumference_layout)

        # Neck Circumference
        neck_circumference_layout = QHBoxLayout()
        neck_circumference_label = QLabel("Neck Circumference (30–45 cm):")
        self.neck_circumference_input = QLineEdit()
        self.neck_circumference_input.setValidator(QDoubleValidator(30.0, 45.0, 2))
        neck_circumference_layout.addWidget(neck_circumference_label)
        neck_circumference_layout.addWidget(self.neck_circumference_input)
        head_neck_layout.addLayout(neck_circumference_layout)

        # Head Length
        head_length_layout = QHBoxLayout()
        head_length_label = QLabel("Head Length (16–24 cm):")
        self.head_length_input = QLineEdit()
        self.head_length_input.setValidator(QDoubleValidator(16.0, 24.0, 2))
        head_length_layout.addWidget(head_length_label)
        head_length_layout.addWidget(self.head_length_input)
        head_neck_layout.addLayout(head_length_layout)

        # Head Breadth
        head_breadth_layout = QHBoxLayout()
        head_breadth_label = QLabel("Head Breadth (12–18 cm):")
        self.head_breadth_input = QLineEdit()
        self.head_breadth_input.setValidator(QDoubleValidator(12.0, 18.0, 2))
        head_breadth_layout.addWidget(head_breadth_label)
        head_breadth_layout.addWidget(self.head_breadth_input)
        head_neck_layout.addLayout(head_breadth_layout)

        # Head Height
        head_height_layout = QHBoxLayout()
        head_height_label = QLabel("Head Height (12–15 cm):")
        self.head_height_input = QLineEdit()
        self.head_height_input.setValidator(QDoubleValidator(12.0, 15.0, 2))
        head_height_layout.addWidget(head_height_label)
        head_height_layout.addWidget(self.head_height_input)
        head_neck_layout.addLayout(head_height_layout)

        # Neck Length
        neck_length_layout = QHBoxLayout()
        neck_length_label = QLabel("Neck Length (8–15 cm):")
        self.neck_length_input = QLineEdit()
        self.neck_length_input.setValidator(QDoubleValidator(8.0, 15.0, 2))
        neck_length_layout.addWidget(neck_length_label)
        neck_length_layout.addWidget(self.neck_length_input)
        head_neck_layout.addLayout(neck_length_layout)

        # Neck Angle
        neck_angle_layout = QHBoxLayout()
        neck_angle_label = QLabel("Neck Angle (0°–60° flexion, 0°–75° extension):")
        self.neck_angle_input = QLineEdit()
        self.neck_angle_input.setValidator(QDoubleValidator(0.0, 75.0, 1))
        neck_angle_layout.addWidget(neck_angle_label)
        neck_angle_layout.addWidget(self.neck_angle_input)
        head_neck_layout.addLayout(neck_angle_layout)

        # Head Angle
        head_angle_layout = QHBoxLayout()
        head_angle_label = QLabel("Head Angle (-30° to +30°):")
        self.head_angle_input = QLineEdit()
        self.head_angle_input.setValidator(QDoubleValidator(-30.0, 30.0, 1))
        head_angle_layout.addWidget(head_angle_label)
        head_angle_layout.addWidget(self.head_angle_input)
        head_neck_layout.addLayout(head_angle_layout)

        # Section for Calculated Measurements
        calculated_measurements_label = QLabel("Calculated Measurements")
        calculated_measurements_label.setFont(bold_font)
        head_neck_layout.addWidget(calculated_measurements_label)

        # Calculated Measurements (Display Only)
        self.head_volume_label = QLabel("Head Volume (cm³): 0.0")
        head_neck_layout.addWidget(self.head_volume_label)

        self.neck_stress_index_label = QLabel("Neck-Stress Index: 0.0")
        head_neck_layout.addWidget(self.neck_stress_index_label)

        self.cervical_spine_alignment_label = QLabel("Cervical Spine Alignment: Neutral")
        head_neck_layout.addWidget(self.cervical_spine_alignment_label)

        self.neck_torque_label = QLabel("Neck Torque (N·m): 0.0")
        head_neck_layout.addWidget(self.neck_torque_label)

        self.neck_head_ratio_label = QLabel("Neck-Head Ratio: 0.0")
        head_neck_layout.addWidget(self.neck_head_ratio_label)

        # Buttons for Calculate and Clean
        buttons_layout = QHBoxLayout()

        self.headneckcalculate_button = QPushButton("Calculate")
        self.headneckcalculate_button.clicked.connect(self.headneckCalculateMeasurements)
        buttons_layout.addWidget(self.headneckcalculate_button)

        self.headneckclean_button = QPushButton("Clean")
        self.headneckclean_button.clicked.connect(self.headneckCleanInputs)
        buttons_layout.addWidget(self.headneckclean_button)

        head_neck_layout.addLayout(buttons_layout)

        # Right Layout for the Image
        image_label = QLabel()
        image_path = "../images/headneckmeasurements01.png"
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            image_label.setText("Image not available")
        else:
            pixmap = pixmap.scaled(300, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)

        # Add layouts to the main layout
        head_neck_main_layout.addLayout(head_neck_layout)  # Add controls on the left
        head_neck_main_layout.addWidget(image_label)  # Add image on the right

        # Set the main layout for the tab
        head_neck_tab.setLayout(head_neck_main_layout)
        self.tabWidget.addTab(head_neck_tab, "Head and Neck")


       
    def headneckCleanInputs(self):
        # Clear all input fields in the Head and Neck tab
        self.head_circumference_input.clear()
        self.neck_circumference_input.clear()
        self.head_length_input.clear()
        self.head_breadth_input.clear()
        self.head_height_input.clear()
        self.neck_length_input.clear()
        self.neck_angle_input.clear()
        self.head_angle_input.clear()

        # Reset calculated measurements
        self.head_volume_label.setText("Head Volume (cm³): 0.0")
        self.neck_stress_index_label.setText("Neck-Stress Index: 0.0")
        self.cervical_spine_alignment_label.setText("Cervical Spine Alignment: Neutral")
        self.neck_torque_label.setText("Neck Torque (N·m): 0.0")
        self.neck_head_ratio_label.setText("Neck-Head Ratio: 0.0")

    def headneckCalculateMeasurements(self):
        try:
            # Gather input values
            head_circumference = float(self.head_circumference_input.text())
            neck_circumference = float(self.neck_circumference_input.text())
            head_length = float(self.head_length_input.text())
            head_breadth = float(self.head_breadth_input.text())
            head_height = float(self.head_height_input.text())
            neck_length = float(self.neck_length_input.text())
            neck_angle = float(self.neck_angle_input.text())
            head_angle = float(self.head_angle_input.text())

            # Perform calculations
            head_volume = (4/3) * 3.14159 * (head_circumference / (2 * 3.14159)) * (head_length / 2) * (head_breadth / 2)
            neck_stress_index = neck_circumference * neck_angle
            cervical_spine_alignment = "Neutral" if abs(neck_angle - head_angle) < 5 else "Misaligned"
            neck_torque = head_volume * 1.05 * (neck_angle / 90)  # Simplified example
            neck_head_ratio = neck_circumference / head_circumference

            # Update calculated measurements
            self.head_volume_label.setText(f"Head Volume (cm³): {head_volume:.2f}")
            self.neck_stress_index_label.setText(f"Neck-Stress Index: {neck_stress_index:.2f}")
            self.cervical_spine_alignment_label.setText(f"Cervical Spine Alignment: {cervical_spine_alignment}")
            self.neck_torque_label.setText(f"Neck Torque (N·m): {neck_torque:.2f}")
            self.neck_head_ratio_label.setText(f"Neck-Head Ratio: {neck_head_ratio:.2f}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred during calculation: {e}")

    
    def setupUpperBodyTab(self):
        # Create the Upper Body tab
        upper_body_tab = QWidget()
        upper_body_main_layout = QHBoxLayout()  # Main horizontal layout to split controls and image

        # Left Layout for Controls
        upper_body_layout = QVBoxLayout()

        bold_font = QFont()
        bold_font.setBold(True)

        # Add a section for displaying ID, First Name, and Last Name
        info_layout = QHBoxLayout()
        # ID Label
        self.upper_body_id_label = QLabel("ID: ")
        #self.upper_body_id_label.setFont(bold_font)
        self.upper_body_id_label.setFixedWidth(200)
        info_layout.addWidget(self.upper_body_id_label)

        # First Name Label
        self.upper_body_first_name_label = QLabel("First Name: ")
        #self.upper_body_first_name_label.setFont(bold_font)
        self.upper_body_first_name_label.setFixedWidth(200)
        info_layout.addWidget(self.upper_body_first_name_label)

        # Last Name Label
        self.upper_body_last_name_label = QLabel("Last Name: ")
        #self.upper_body_last_name_label.setFont(bold_font)
        self.upper_body_last_name_label.setFixedWidth(200)
        info_layout.addWidget(self.upper_body_last_name_label)

        upper_body_layout.addLayout(info_layout)
        
        
        # Section for Direct Measurements
        direct_measurements_label = QLabel("Direct Measurements")
        direct_measurements_label.setFont(bold_font)
        upper_body_layout.addWidget(direct_measurements_label)

        # Shoulder Width
        shoulder_width_layout = QHBoxLayout()
        shoulder_width_label = QLabel("Shoulder Width (30–50 cm):")
        self.shoulder_width_input = QLineEdit()
        self.shoulder_width_input.setValidator(QDoubleValidator(30.0, 50.0, 2))
        shoulder_width_layout.addWidget(shoulder_width_label)
        shoulder_width_layout.addWidget(self.shoulder_width_input)
        upper_body_layout.addLayout(shoulder_width_layout)

        # Chest Circumference
        chest_circumference_layout = QHBoxLayout()
        chest_circumference_label = QLabel("Chest Circumference (80–140 cm):")
        self.chest_circumference_input = QLineEdit()
        self.chest_circumference_input.setValidator(QDoubleValidator(80.0, 140.0, 2))
        chest_circumference_layout.addWidget(chest_circumference_label)
        chest_circumference_layout.addWidget(self.chest_circumference_input)
        upper_body_layout.addLayout(chest_circumference_layout)

        # Upper Arm Length
        upper_arm_length_layout = QHBoxLayout()
        upper_arm_length_label = QLabel("Upper Arm Length (25–40 cm):")
        self.upper_arm_length_input = QLineEdit()
        self.upper_arm_length_input.setValidator(QDoubleValidator(25.0, 40.0, 2))
        upper_arm_length_layout.addWidget(upper_arm_length_label)
        upper_arm_length_layout.addWidget(self.upper_arm_length_input)
        upper_body_layout.addLayout(upper_arm_length_layout)

        # Forearm Length
        forearm_length_layout = QHBoxLayout()
        forearm_length_label = QLabel("Forearm Length (20–35 cm):")
        self.forearm_length_input = QLineEdit()
        self.forearm_length_input.setValidator(QDoubleValidator(20.0, 35.0, 2))
        forearm_length_layout.addWidget(forearm_length_label)
        forearm_length_layout.addWidget(self.forearm_length_input)
        upper_body_layout.addLayout(forearm_length_layout)

        # Hand Length
        hand_length_layout = QHBoxLayout()
        hand_length_label = QLabel("Hand Length (15–25 cm):")
        self.hand_length_input = QLineEdit()
        self.hand_length_input.setValidator(QDoubleValidator(15.0, 25.0, 2))
        hand_length_layout.addWidget(hand_length_label)
        hand_length_layout.addWidget(self.hand_length_input)
        upper_body_layout.addLayout(hand_length_layout)

        # Hand Breadth
        hand_breadth_layout = QHBoxLayout()
        hand_breadth_label = QLabel("Hand Breadth (7–12 cm):")
        self.hand_breadth_input = QLineEdit()
        self.hand_breadth_input.setValidator(QDoubleValidator(7.0, 12.0, 2))
        hand_breadth_layout.addWidget(hand_breadth_label)
        hand_breadth_layout.addWidget(self.hand_breadth_input)
        upper_body_layout.addLayout(hand_breadth_layout)

        # Arm Span
        arm_span_layout = QHBoxLayout()
        arm_span_label = QLabel("Arm Span (140–200 cm):")
        self.arm_span_input = QLineEdit()
        self.arm_span_input.setValidator(QDoubleValidator(140.0, 200.0, 2))
        arm_span_layout.addWidget(arm_span_label)
        arm_span_layout.addWidget(self.arm_span_input)
        upper_body_layout.addLayout(arm_span_layout)

        # Torso Length
        torso_length_layout = QHBoxLayout()
        torso_length_label = QLabel("Torso Length (40–70 cm):")
        self.torso_length_input = QLineEdit()
        self.torso_length_input.setValidator(QDoubleValidator(40.0, 70.0, 2))
        torso_length_layout.addWidget(torso_length_label)
        torso_length_layout.addWidget(self.torso_length_input)
        upper_body_layout.addLayout(torso_length_layout)

        # Spinal Curvature
        spinal_curvature_layout = QHBoxLayout()
        spinal_curvature_label = QLabel("Spinal Curvature (Kyphosis 20°–60°, Lordosis 20°–50°):")
        self.spinal_curvature_input = QLineEdit()
        self.spinal_curvature_input.setValidator(QDoubleValidator(20.0, 60.0, 1))
        spinal_curvature_layout.addWidget(spinal_curvature_label)
        spinal_curvature_layout.addWidget(self.spinal_curvature_input)
        upper_body_layout.addLayout(spinal_curvature_layout)

        # Shoulder Angle
        shoulder_angle_layout = QHBoxLayout()
        shoulder_angle_label = QLabel("Shoulder Angle (0°–180° flexion, 0°–60° extension):")
        self.shoulder_angle_input = QLineEdit()
        self.shoulder_angle_input.setValidator(QDoubleValidator(0.0, 180.0, 1))
        shoulder_angle_layout.addWidget(shoulder_angle_label)
        shoulder_angle_layout.addWidget(self.shoulder_angle_input)
        upper_body_layout.addLayout(shoulder_angle_layout)

        # Sitting Height
        sitting_height_layout = QHBoxLayout()
        sitting_height_label = QLabel("Sitting Height (0–120 cm):")
        self.sitting_height_input = QLineEdit()
        self.sitting_height_input.setValidator(QDoubleValidator(0.0, 120.0, 1))
        sitting_height_layout.addWidget(sitting_height_label)
        sitting_height_layout.addWidget(self.sitting_height_input)
        upper_body_layout.addLayout(sitting_height_layout)


        # Section for Calculated Measurements
        calculated_measurements_label = QLabel("Calculated Measurements")
        calculated_measurements_label.setFont(bold_font)
        upper_body_layout.addWidget(calculated_measurements_label)

        # Upper Limb Length
        self.upper_limb_length_label = QLabel("Upper Limb Length (cm): 0.0")
        upper_body_layout.addWidget(self.upper_limb_length_label)

        # Arm-Hand Ratio
        self.arm_hand_ratio_label = QLabel("Arm-Hand Ratio: 0.0")
        upper_body_layout.addWidget(self.arm_hand_ratio_label)

        # Shoulder-to-Hand Distance
        self.shoulder_to_hand_distance_label = QLabel("Shoulder-to-Hand Distance (cm): 0.0")
        upper_body_layout.addWidget(self.shoulder_to_hand_distance_label)

        # Arm Volume
        self.arm_volume_label = QLabel("Arm Volume (cm): 0.0")
        upper_body_layout.addWidget(self.arm_volume_label)

        # Torso-to-Limb Ratio
        self.torso_to_limb_ratio_label = QLabel("Torso-to-Limb Ratio: 0.0")
        upper_body_layout.addWidget(self.torso_to_limb_ratio_label)

        # Grip Strength Index
        self.grip_strength_index_label = QLabel("Grip Strength Index: 0.0")
        upper_body_layout.addWidget(self.grip_strength_index_label)

        # Total Upper Body Volume
        self.total_upper_body_volume_label = QLabel("Total Upper Body Volume (cm³): 0.0")
        upper_body_layout.addWidget(self.total_upper_body_volume_label)

        # Postural Load Index
        self.postural_load_index_label = QLabel("Postural Load Index: 0.0")
        upper_body_layout.addWidget(self.postural_load_index_label)
        
        
        
        # Buttons for Calculate and Clean
        buttons_layout = QHBoxLayout()

        self.upperbodycalculate_button = QPushButton("Calculate")
        self.upperbodycalculate_button.clicked.connect(self.upperBodyCalculateMeasurements)
        buttons_layout.addWidget(self.upperbodycalculate_button)

        self.upperbodyclean_button = QPushButton("Clean")
        self.upperbodyclean_button.clicked.connect(self.upperBodyCleanInputs)
        buttons_layout.addWidget(self.upperbodyclean_button)

        upper_body_layout.addLayout(buttons_layout)

        # Right Layout for the Image
        image_label = QLabel()
        image_path = "../images/upperbodymeasurements01.png"
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            image_label.setText("Image not available")
        else:
            pixmap = pixmap.scaled(300, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)

        # Add layouts to the main layout
        upper_body_main_layout.addLayout(upper_body_layout)  # Add controls on the left
        upper_body_main_layout.addWidget(image_label)  # Add image on the right

        # Set the main layout for the tab
        upper_body_tab.setLayout(upper_body_main_layout)
        self.tabWidget.addTab(upper_body_tab, "Upper Body")

        
        
    def upperBodyCalculateMeasurements(self):
        try:
            # Fetch inputs and convert to float where necessary
            upper_arm_length = float(self.upper_arm_length_input.text())
            forearm_length = float(self.forearm_length_input.text())
            hand_length = float(self.hand_length_input.text())
            hand_breadth = float(self.hand_breadth_input.text())
            torso_length = float(self.torso_length_input.text())
            arm_span = float(self.arm_span_input.text())
            chest_circumference = float(self.chest_circumference_input.text())
            spinal_curvature = float(self.spinal_curvature_input.text())
            shoulder_angle = float(self.shoulder_angle_input.text())
            sitting_height = float(self.sitting_height_input.text() )

            # Calculations
            upper_limb_length = upper_arm_length + forearm_length + hand_length
            arm_hand_ratio = upper_arm_length / hand_length if hand_length > 0 else 0
            shoulder_to_hand_distance = upper_arm_length + forearm_length
            arm_volume = (
                3.14159 * ((upper_arm_length / 2) ** 2) * upper_arm_length +
                3.14159 * ((forearm_length / 2) ** 2) * forearm_length
            )  # Simplified cylindrical volume
            grip_strength_index = hand_length * hand_breadth
            torso_to_limb_ratio = torso_length / arm_span if arm_span > 0 else 0
            postural_load_index = (
                0.4 * spinal_curvature + 0.4 * shoulder_angle + 0.2 * sitting_height
            )  # Weighted sum approximation
            total_upper_body_volume = (
                3.14159 * (chest_circumference / (2 * 3.14159)) ** 2 * torso_length +
                arm_volume
            )  # Ellipsoidal and cylindrical combination
            # Arm Volume
            upper_arm_circumference = upper_arm_length * 0.4  # Assumption for approximation
            forearm_circumference = forearm_length * 0.3  # Assumption for approximation
            arm_volume = (
                3.14159 * ((upper_arm_circumference / (2 * 3.14159)) ** 2) * upper_arm_length +
                3.14159 * ((forearm_circumference / (2 * 3.14159)) ** 2) * forearm_length
            )
            
            # Update labels with calculated values
            self.upper_limb_length_label.setText(f"Upper Limb Length (cm): {upper_limb_length:.2f}")
            self.arm_hand_ratio_label.setText(f"Arm-Hand Ratio: {arm_hand_ratio:.2f}")
            self.shoulder_to_hand_distance_label.setText(f"Shoulder-to-Hand Distance (cm): {shoulder_to_hand_distance:.2f}")
            self.arm_volume_label.setText(f"Arm Volume (cm³): {arm_volume:.2f}")
            self.grip_strength_index_label.setText(f"Grip Strength Index: {grip_strength_index:.2f}")
            self.torso_to_limb_ratio_label.setText(f"Torso-to-Limb Ratio: {torso_to_limb_ratio:.2f}")
            self.postural_load_index_label.setText(f"Postural Load Index: {postural_load_index:.2f}")
            self.total_upper_body_volume_label.setText(f"Total Upper Body Volume (cm³): {total_upper_body_volume:.2f}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"An error occurred during calculation: {e}")

    def upperBodyCleanInputs(self):
        # Clear all input fields
        self.shoulder_width_input.clear()
        self.upper_arm_length_input.clear()
        self.forearm_length_input.clear()
        self.hand_length_input.clear()
        self.hand_breadth_input.clear()
        self.torso_length_input.clear()
        self.arm_span_input.clear()
        self.chest_circumference_input.clear()
        self.spinal_curvature_input.clear()
        self.shoulder_angle_input.clear()
        self.sitting_height_input.clear()

        # Reset calculated values
        self.upper_limb_length_label.setText("Upper Limb Length (cm): 0.0")
        self.arm_hand_ratio_label.setText("Arm-Hand Ratio: 0.0")
        self.shoulder_to_hand_distance_label.setText("Shoulder-to-Hand Distance (cm): 0.0")
        #self.sitting_height_label.setText("Sitting Height (0–120 cm):")
        self.grip_strength_index_label.setText("Grip Strength Index: 0.0")
        self.torso_to_limb_ratio_label.setText("Torso-to-Limb Ratio: 0.0")
        self.postural_load_index_label.setText("Postural Load Index: 0.0")
        self.total_upper_body_volume_label.setText("Total Upper Body Volume (cm³): 0.0")
    
        
        
        
    def setupLowerBodyTab(self):
        # Create the Upper Body tab
        lower_body_tab = QWidget()
        lower_body_main_layout = QHBoxLayout()  # Main horizontal layout to split controls and image

        # Left Layout for Controls
        lower_body_layout = QVBoxLayout()

        bold_font = QFont()
        bold_font.setBold(True)


        # Add a section for displaying ID, First Name, and Last Name
        info_layout = QHBoxLayout()
        # ID Label
        self.lower_body_id_label = QLabel("ID: ")
        #self.lower_body_id_label.setFont(bold_font)
        self.lower_body_id_label.setFixedWidth(200)
        info_layout.addWidget(self.lower_body_id_label)

        # First Name Label
        self.lower_body_first_name_label = QLabel("First Name: ")
        #self.lower_body_first_name_label.setFont(bold_font)
        self.lower_body_first_name_label.setFixedWidth(200)
        info_layout.addWidget(self.lower_body_first_name_label)

        # Last Name Label
        self.lower_body_last_name_label = QLabel("Last Name: ")
        #self.lower_body_last_name_label.setFont(bold_font)
        self.lower_body_last_name_label.setFixedWidth(200)
        info_layout.addWidget(self.lower_body_last_name_label)

        lower_body_layout.addLayout(info_layout)
        
        # Section for Direct Measurements
        direct_measurements_label = QLabel("Direct Measurements")
        direct_measurements_label.setFont(bold_font)
        lower_body_layout.addWidget(direct_measurements_label)


        ## Total Height
        #total_height_layout = QHBoxLayout()
        #total_height_label = QLabel("Total Height (25–300 cm):")
        #self.total_height_input = QLineEdit()
        #self.total_height_input.setValidator(QDoubleValidator(25.0, 300.0, 2))
        #total_height_layout.addWidget(total_height_label)
        #total_height_layout.addWidget(self.total_height_input)
        #lower_body_layout.addLayout(total_height_layout)

        # Hip Width (Biiliac Breadth)
        hip_width_layout = QHBoxLayout()
        hip_width_label = QLabel("Hip Width (25–40 cm):")
        self.hip_width_input = QLineEdit()
        self.hip_width_input.setValidator(QDoubleValidator(25.0, 40.0, 2))
        hip_width_layout.addWidget(hip_width_label)
        hip_width_layout.addWidget(self.hip_width_input)
        lower_body_layout.addLayout(hip_width_layout)

        # Waist Circumference
        waist_circumference_layout = QHBoxLayout()
        waist_circumference_label = QLabel("Waist Circumference (60–120 cm):")
        self.waist_circumference_input = QLineEdit()
        self.waist_circumference_input.setValidator(QDoubleValidator(60.0, 120.0, 2))
        waist_circumference_layout.addWidget(waist_circumference_label)
        waist_circumference_layout.addWidget(self.waist_circumference_input)
        lower_body_layout.addLayout(waist_circumference_layout)

        # Thigh Circumference
        thigh_circumference_layout = QHBoxLayout()
        thigh_circumference_label = QLabel("Thigh Circumference (40–80 cm):")
        self.thigh_circumference_input = QLineEdit()
        self.thigh_circumference_input.setValidator(QDoubleValidator(40.0, 80.0, 2))
        thigh_circumference_layout.addWidget(thigh_circumference_label)
        thigh_circumference_layout.addWidget(self.thigh_circumference_input)
        lower_body_layout.addLayout(thigh_circumference_layout)

        # Leg Length
        leg_length_layout = QHBoxLayout()
        leg_length_label = QLabel("Leg Length (70–120 cm):")
        self.leg_length_input = QLineEdit()
        self.leg_length_input.setValidator(QDoubleValidator(70.0, 120.0, 2))
        leg_length_layout.addWidget(leg_length_label)
        leg_length_layout.addWidget(self.leg_length_input)
        lower_body_layout.addLayout(leg_length_layout)

        # Thigh Length
        thigh_length_layout = QHBoxLayout()
        thigh_length_label = QLabel("Thigh Length (40–65 cm):")
        self.thigh_length_input = QLineEdit()
        self.thigh_length_input.setValidator(QDoubleValidator(40.0, 65.0, 2))
        thigh_length_layout.addWidget(thigh_length_label)
        thigh_length_layout.addWidget(self.thigh_length_input)
        lower_body_layout.addLayout(thigh_length_layout)

        # Lower Leg Length
        lower_leg_length_layout = QHBoxLayout()
        lower_leg_length_label = QLabel("Lower Leg Length (35–55 cm):")
        self.lower_leg_length_input = QLineEdit()
        self.lower_leg_length_input.setValidator(QDoubleValidator(35.0, 55.0, 2))
        lower_leg_length_layout.addWidget(lower_leg_length_label)
        lower_leg_length_layout.addWidget(self.lower_leg_length_input)
        lower_body_layout.addLayout(lower_leg_length_layout)

        # Foot Length
        foot_length_layout = QHBoxLayout()
        foot_length_label = QLabel("Foot Length (20–30 cm):")
        self.foot_length_input = QLineEdit()
        self.foot_length_input.setValidator(QDoubleValidator(20.0, 30.0, 2))
        foot_length_layout.addWidget(foot_length_label)
        foot_length_layout.addWidget(self.foot_length_input)
        lower_body_layout.addLayout(foot_length_layout)

        # Foot Breadth
        foot_breadth_layout = QHBoxLayout()
        foot_breadth_label = QLabel("Foot Breadth (8–12 cm):")
        self.foot_breadth_input = QLineEdit()
        self.foot_breadth_input.setValidator(QDoubleValidator(8.0, 12.0, 2))
        foot_breadth_layout.addWidget(foot_breadth_label)
        foot_breadth_layout.addWidget(self.foot_breadth_input)
        lower_body_layout.addLayout(foot_breadth_layout)

        # Knee Height (Sitting)
        knee_height_layout = QHBoxLayout()
        knee_height_label = QLabel("Knee Height (45–65 cm):")
        self.knee_height_input = QLineEdit()
        self.knee_height_input.setValidator(QDoubleValidator(45.0, 65.0, 2))
        knee_height_layout.addWidget(knee_height_label)
        knee_height_layout.addWidget(self.knee_height_input)
        lower_body_layout.addLayout(knee_height_layout)

        # Hip Angle
        hip_angle_layout = QHBoxLayout()
        hip_angle_label = QLabel("Hip Angle (90°–135°):")
        self.hip_angle_input = QLineEdit()
        self.hip_angle_input.setValidator(QDoubleValidator(90.0, 135.0, 1))
        hip_angle_layout.addWidget(hip_angle_label)
        hip_angle_layout.addWidget(self.hip_angle_input)
        lower_body_layout.addLayout(hip_angle_layout)

        # Knee Angle
        knee_angle_layout = QHBoxLayout()
        knee_angle_label = QLabel("Knee Angle (0°–135°):")
        self.knee_angle_input = QLineEdit()
        self.knee_angle_input.setValidator(QDoubleValidator(0.0, 135.0, 1))
        knee_angle_layout.addWidget(knee_angle_label)
        knee_angle_layout.addWidget(self.knee_angle_input)
        lower_body_layout.addLayout(knee_angle_layout)

        # Ankle Angle
        ankle_angle_layout = QHBoxLayout()
        ankle_angle_label = QLabel("Ankle Angle (0°–50° dorsiflexion, 0°–40° plantarflexion):")
        self.ankle_angle_input = QLineEdit()
        self.ankle_angle_input.setValidator(QDoubleValidator(0.0, 50.0, 1))
        ankle_angle_layout.addWidget(ankle_angle_label)
        ankle_angle_layout.addWidget(self.ankle_angle_input)
        lower_body_layout.addLayout(ankle_angle_layout)
        

        # Section for Calculated Measurements
        calculated_measurements_label = QLabel("Calculated Measurements")
        calculated_measurements_label.setFont(bold_font)
        lower_body_layout.addWidget(calculated_measurements_label)

        # Total Leg Length
        self.total_leg_length_label = QLabel("Total Leg Length (cm): 0.0")
        lower_body_layout.addWidget(self.total_leg_length_label)

        # Leg Proportion Index
        self.leg_proportion_index_label = QLabel("Leg Proportion Index: 0.0")
        lower_body_layout.addWidget(self.leg_proportion_index_label)

        # Foot-to-Leg Ratio
        self.foot_to_leg_ratio_label = QLabel("Foot-to-Leg Ratio: 0.0")
        lower_body_layout.addWidget(self.foot_to_leg_ratio_label)

        # Lower Limb Volume
        self.lower_limb_volume_label = QLabel("Lower Limb Volume (cm³): 0.0")
        lower_body_layout.addWidget(self.lower_limb_volume_label)

        # Knee-Torso Distance
        self.knee_torso_distance_label = QLabel("Knee-Torso Distance (cm): 0.0")
        lower_body_layout.addWidget(self.knee_torso_distance_label)

        # Step Length
        self.step_length_label = QLabel("Step Length (cm): 0.0")
        lower_body_layout.addWidget(self.step_length_label)

        # Postural Stability Index
        self.postural_stability_index_label = QLabel("Postural Stability Index: 0.0")
        lower_body_layout.addWidget(self.postural_stability_index_label)
                
        
        
        # Buttons for Calculate and Clean
        buttons_layout = QHBoxLayout()

        self.lowerbodycalculate_button = QPushButton("Calculate")
        self.lowerbodycalculate_button.clicked.connect(self.lowerBodyCalculateMeasurements)
        buttons_layout.addWidget(self.lowerbodycalculate_button)

        self.lowerbodyclean_button = QPushButton("Clean")
        self.lowerbodyclean_button.clicked.connect(self.lowerBodyCleanInputs)
        buttons_layout.addWidget(self.lowerbodyclean_button)

        lower_body_layout.addLayout(buttons_layout)

        # Right Layout for the Image
        image_label = QLabel()
        image_path = "../images/lowerbodymeasurements01.png"
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            image_label.setText("Image not available")
        else:
            pixmap = pixmap.scaled(300, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)

        # Add layouts to the main layout
        lower_body_main_layout.addLayout(lower_body_layout)  # Add controls on the left
        lower_body_main_layout.addWidget(image_label)  # Add image on the right

        # Set the main layout for the tab
        lower_body_tab.setLayout(lower_body_main_layout)
        self.tabWidget.addTab(lower_body_tab, "Lower Body")



    def lowerBodyCalculateMeasurements(self):
        try:
            # Retrieve input values and handle empty inputs
            thigh_length = float(self.thigh_length_input.text())
            lower_leg_length = float(self.lower_leg_length_input.text())
            leg_length = float(self.leg_length_input.text())
            total_height = float(self.height_input.text())
            foot_length = float(self.foot_length_input.text())
            foot_breadth = float(self.foot_breadth_input.text())
            thigh_circumference = float(self.thigh_circumference_input.text())
            knee_height = float(self.knee_height_input.text())
            hip_angle = math.radians(float(self.hip_angle_input.text()))  # Convert to radians
            ankle_angle = math.radians(float(self.ankle_angle_input.text()))  # Convert to radians
            knee_angle = math.radians(float(self.knee_angle_input.text()))  # Convert to radians

            # Total Leg Length
            total_leg_length = thigh_length + lower_leg_length
            self.total_leg_length_label.setText(f"Total Leg Length (cm): {total_leg_length:.2f}")

            # Leg Proportion Index
            leg_proportion_index = leg_length / total_height if total_height > 0 else 0
            self.leg_proportion_index_label.setText(f"Leg Proportion Index: {leg_proportion_index:.2f}")

            # Foot-to-Leg Ratio
            foot_to_leg_ratio = foot_length / leg_length if leg_length > 0 else 0
            self.foot_to_leg_ratio_label.setText(f"Foot-to-Leg Ratio: {foot_to_leg_ratio:.2f}")

            # Lower Limb Volume
            lower_limb_volume = (thigh_circumference ** 2 * thigh_length) + (foot_length * foot_breadth)
            self.lower_limb_volume_label.setText(f"Lower Limb Volume (cm³): {lower_limb_volume:.2f}")

            # Knee-Torso Distance
            knee_torso_distance = knee_height * math.sin(hip_angle)
            self.knee_torso_distance_label.setText(f"Knee-Torso Distance (cm): {knee_torso_distance:.2f}")

            # Step Length
            step_length = leg_length * math.sin(hip_angle)
            self.step_length_label.setText(f"Step Length (cm): {step_length:.2f}")

            # Postural Stability Index
            postural_stability_index = math.sin(ankle_angle) + math.sin(knee_angle) + math.sin(hip_angle)
            self.postural_stability_index_label.setText(f"Postural Stability Index: {postural_stability_index:.2f}")

        except ValueError as e:
            QMessageBox.warning(self, "Error", f"An error occurred during calculation: {e}")

   
    def lowerBodyCleanInputs(self):
        # Clear all input fields for direct measurements
        #self.total_height_input.clear()
        self.hip_width_input.clear()
        self.waist_circumference_input.clear()
        self.thigh_circumference_input.clear()
        self.leg_length_input.clear()
        self.thigh_length_input.clear()
        self.lower_leg_length_input.clear()
        self.foot_length_input.clear()
        self.foot_breadth_input.clear()
        self.knee_height_input.clear()
        self.hip_angle_input.clear()
        self.knee_angle_input.clear()
        self.ankle_angle_input.clear()

        # Reset all calculated measurement labels
        self.total_leg_length_label.setText("Total Leg Length (cm): 0.0")
        self.leg_proportion_index_label.setText("Leg Proportion Index: 0.0")
        self.foot_to_leg_ratio_label.setText("Foot-to-Leg Ratio: 0.0")
        self.lower_limb_volume_label.setText("Lower Limb Volume (cm³): 0.0")
        self.knee_torso_distance_label.setText("Knee-Torso Distance (cm): 0.0")
        self.step_length_label.setText("Step Length (cm): 0.0")
        self.postural_stability_index_label.setText("Postural Stability Index: 0.0")
   

    def saveWorker(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save worker.")
            return
    
        # Connect to the database
        database_path = self.parent().projectdatabasePath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
    
        # Validate Worker ID
        worker_id = self.worker_id_combo.currentText().strip()
        if not worker_id:
            QMessageBox.warning(self, "Validation Error", "Worker ID is required.")
            return
        
        #Validate Worker ID (No spaces allowed)
        worker_id = self.worker_id_combo.currentText().strip()
        if " " in worker_id:
            QMessageBox.warning(self, "Validation Error", "Worker ID cannot contain spaces.")
            return
    
        # Collect all fields
        # Validate First Name and Last Name
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()

        if (first_name and not last_name) or (last_name and not first_name):
            QMessageBox.warning(self, "Validation Error", "Both First Name and Last Name are required if one is entered.")
            return
    
        # If both are empty, keep them as blank
        first_name = first_name if first_name else ""
        last_name = last_name if last_name else ""

    
        # Extract Date of Birth
        dob = self.dob_input.date()
        year_of_birth = dob.year()
        month_of_birth = dob.month()
        day_of_birth = dob.day()
    
        # Extract Gender
        gender = self.gender_combo.currentText().strip()
    
        height = float(self.height_input.text()) if self.height_input.text() else None
        weight = float(self.weight_input.text()) if self.weight_input.text() else None
        address = self.address_input.text().strip()
        city = self.city_input.text().strip()
        state = self.state_combo.currentText() if self.state_combo.currentIndex() != -1 else None
        country = self.country_combo.currentText() if self.country_combo.currentIndex() != -1 else None
        zipcode = self.zipcode_input.text().strip()
        email = self.email_input.text().strip()
    
        # Extract Date of Hiring
        hiring_date = self.date_of_hiring_input.date()
        year_of_hiring = hiring_date.year()
        month_of_hiring = hiring_date.month()
        day_of_hiring = hiring_date.day()

        # TODO: Sample measurements (head and neck, upper body, lower body) - more can be added later
        head_circumference = float(self.head_circumference_input.text()) if self.head_circumference_input.text() else None
        neck_circumference = float(self.neck_circumference_input.text()) if self.neck_circumference_input.text() else None
        head_length = float(self.head_length_input.text()) if self.head_length_input.text() else None
        neck_angle = float(self.neck_angle_input.text()) if self.neck_angle_input.text() else None
    
        shoulder_width = float(self.shoulder_width_input.text()) if self.shoulder_width_input.text() else None   
        chest_circumference = float(self.chest_circumference_input.text()) if self.chest_circumference_input.text() else None   
   
        hip_width = float(self.hip_width_input.text()) if self.hip_width_input.text() else None   
        leg_length = float(self.leg_length_input.text()) if self.leg_length_input.text() else None   
   
    
        # Insert or update the worker
        try:
            cursor.execute('''
                INSERT INTO Worker (
                    id, first_name, last_name, year_of_birth, month_of_birth, day_of_birth, gender,
                    height, weight, address, email, year_of_hiring, month_of_hiring, day_of_hiring,
                    city, state, country, zipcode, head_circumference, neck_circumference, head_length, neck_angle, shoulder_width, chest_circumference, 
                    hip_width, leg_length
                ) VALUES (
                    :id, :first_name, :last_name, :year_of_birth, :month_of_birth, :day_of_birth, :gender,
                    :height, :weight, :address, :email, :year_of_hiring, :month_of_hiring, :day_of_hiring,
                    :city, :state, :country, :zipcode, :head_circumference, :neck_circumference, :head_length, :neck_angle, :shoulder_width, 
                    :chest_circumference, :hip_width, :leg_length
                )
                ON CONFLICT(id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    year_of_birth = excluded.year_of_birth,
                    month_of_birth = excluded.month_of_birth,
                    day_of_birth = excluded.day_of_birth,
                    gender = excluded.gender,
                    height = excluded.height,
                    weight = excluded.weight,
                    address = excluded.address,
                    email = excluded.email,
                    year_of_hiring = excluded.year_of_hiring,
                    month_of_hiring = excluded.month_of_hiring,
                    day_of_hiring = excluded.day_of_hiring,
                    city = excluded.city,
                    state = excluded.state,
                    country = excluded.country,
                    zipcode = excluded.zipcode,
                    head_circumference = excluded.head_circumference,
                    neck_circumference = excluded.neck_circumference,
                    head_length = excluded.head_length,
                    neck_angle = excluded.neck_angle,
                    shoulder_width = excluded.shoulder_width,
                    chest_circumference = excluded.chest_circumference,
                    hip_width = excluded.hip_width,
                    leg_length = excluded.leg_length
            ''', {
                'id': worker_id,
                'first_name': first_name,
                'last_name': last_name,
                'year_of_birth': year_of_birth,
                'month_of_birth': month_of_birth,
                'day_of_birth': day_of_birth,
                'gender': gender,
                'height': height,
                'weight': weight,
                'address': address,
                'email': email,
                'year_of_hiring': year_of_hiring,
                'month_of_hiring': month_of_hiring,
                'day_of_hiring': day_of_hiring,
                'city': city,
                'state': state,
                'country': country,
                'zipcode': zipcode,
                'head_circumference': head_circumference,
                'neck_circumference': neck_circumference,
                'head_length': head_length,
                'neck_angle': neck_angle,
                'shoulder_width': shoulder_width,
                'chest_circumference': chest_circumference,
                'hip_width': hip_width,
                'leg_length': leg_length
            })

            conn.commit()

            QMessageBox.information(self, "Success", f"Worker '{worker_id}' has been saved successfully.")

            # Enable navigation and other disabled buttons
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)

            current_text = self.worker_id_combo.currentText()
            self.loadWorkers(0)
            index = self.worker_id_combo.findText(current_text)
            if index != -1:
                self.worker_id_combo.setCurrentIndex(index)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the worker:\n{str(e)}")
        finally:
            conn.close()



        
                
            
            

