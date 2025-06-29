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
    QComboBox, QPushButton, QTabWidget, QWidget, QGridLayout, QMessageBox, QDialogButtonBox, QTextEdit, QTimeEdit
)

from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QPixmap, QRegExpValidator

from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import QRegularExpression, QRegExp

#from PySide2.QtWidgets import QSpacerItem, QSizePolicy

class StationWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Station Management")
        self.setGeometry(200, 200, 800, 500)
        self.setupUI()

        # Get the Plant, Section, and Line names from the parent window
        if self.parent():
            plant_name = self.parent().plant_combo.currentText()
            section_name = self.parent().section_combo.currentText()
            line_name = self.parent().line_combo.currentText()
            self.plant_name_label.setText(f"{plant_name}")
            self.section_name_label.setText(f"{section_name}")
            self.line_name_label.setText(f"{line_name}")
            
        
        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadStations()

            # Get the current text from the plant_combo in the parent window
            station_combo_text = self.parent().station_combo.currentText()

            # Extract the ID from the text 
            station_id = station_combo_text.strip()

            index = self.id_combo.findText(station_id)
            if index != -1:
                self.id_combo.setCurrentIndex(index)
            

    def setupUI(self):
        layout = QVBoxLayout()

        # Form layout for input controls
        form_layout = QGridLayout()

        # Plant, Section, and Line Name (non-editable, bold, aligned with a "-")
        header_layout = QHBoxLayout()
        bold_font = QFont()
        bold_font.setBold(True)

        plant_name_label = QLabel("Plant:")
        plant_name_label.setFont(bold_font)
        self.plant_name_label = QLabel("")
        self.plant_name_label.setFont(bold_font)

        separator_label_1 = QLabel(" - ")
        separator_label_1.setFont(bold_font)

        section_name_label = QLabel("Section:")
        section_name_label.setFont(bold_font)
        self.section_name_label = QLabel("")
        self.section_name_label.setFont(bold_font)

        separator_label_2 = QLabel(" - ")
        separator_label_2.setFont(bold_font)

        line_name_label = QLabel("Line:")
        line_name_label.setFont(bold_font)
        self.line_name_label = QLabel("")
        self.line_name_label.setFont(bold_font)

        header_layout.addWidget(plant_name_label)
        header_layout.addWidget(self.plant_name_label)
        header_layout.addWidget(separator_label_1)
        header_layout.addWidget(section_name_label)
        header_layout.addWidget(self.section_name_label)
        header_layout.addWidget(separator_label_2)
        header_layout.addWidget(line_name_label)
        header_layout.addWidget(self.line_name_label)
        header_layout.addStretch()  # Push content to the left

        form_layout.addLayout(header_layout, 0, 0, 1, 2)

        # Station fields
        form_layout.addWidget(QLabel("Station ID:"), 1, 0)
        self.id_combo = QComboBox()
        self.id_combo.setEditable(True)  # Allow new entries
        self.id_combo.currentIndexChanged.connect(self.loadStationDetails)
        form_layout.addWidget(self.id_combo, 1, 1)

        form_layout.addWidget(QLabel("Location:"), 2, 0)
        self.location_input = QLineEdit()
        form_layout.addWidget(self.location_input, 2, 1)

        form_layout.addWidget(QLabel("Task Description:"), 3, 0)
        self.task_description_text = QTextEdit()
        form_layout.addWidget(self.task_description_text, 3, 1)

        form_layout.addWidget(QLabel("Equipment Used:"), 4, 0)
        self.equipment_used_input = QLineEdit()
        form_layout.addWidget(self.equipment_used_input, 4, 1)

        form_layout.addWidget(QLabel("Cycle Time (sec):"), 5, 0)
        self.cycle_time_input = QLineEdit()
        form_layout.addWidget(self.cycle_time_input, 5, 1)

        form_layout.addWidget(QLabel("Capacity:"), 6, 0)
        self.capacity_input = QLineEdit()
        form_layout.addWidget(self.capacity_input, 6, 1)

        form_layout.addWidget(QLabel("Ergonomic Risk Level:"), 7, 0)
        self.ergonomic_risk_input = QLineEdit()
        form_layout.addWidget(self.ergonomic_risk_input, 7, 1)

        form_layout.addWidget(QLabel("Performance Metric:"), 8, 0)
        self.performance_metric_input = QLineEdit()
        form_layout.addWidget(self.performance_metric_input, 8, 1)

        form_layout.addWidget(QLabel("Power Consumption (kWh):"), 9, 0)
        self.power_consumption_input = QLineEdit()
        form_layout.addWidget(self.power_consumption_input, 9, 1)

        form_layout.addWidget(QLabel("Materials Used:"), 10, 0)
        self.materials_used_input = QLineEdit()
        form_layout.addWidget(self.materials_used_input, 10, 1)

        layout.addLayout(form_layout)
        #layout.addStretch()
         
        # Navigation and operation buttons
        button_layout = QHBoxLayout()

        self.first_button = QPushButton("|<")
        self.first_button.setFont(bold_font)
        self.first_button.clicked.connect(self.firstStation)

        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousStation)

        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)
        self.new_button.clicked.connect(self.newStation)

        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)
        self.save_button.clicked.connect(self.saveStation)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)
        self.delete_button.clicked.connect(self.deleteStation)

        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)
        self.search_button.clicked.connect(self.searchStation)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)
        self.cancel_button.clicked.connect(self.cancelStation)

        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)
        self.close_button.clicked.connect(self.closeStation)

        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextStation)

        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastStation)

        # Add buttons to the layout
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

        # Add a vertical spacer before the buttons
        layout.addStretch()
        #TODO: Check why is not adding a space
        #layout.addStretch()
        # Add a vertical spacer before the buttons
        # Create a horizontal layout to hold the spacer
        #spacer_layout = QHBoxLayout()
 
        # Create the spacer item
        #spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add the spacer to the layout
        #spacer_layout.addItem(spacer)

        # Add the spacer layout to the main layout
        #layout.addLayout(spacer_layout)
        
        # Add layouts to the main layout
        layout.addLayout(button_layout)
        self.setLayout(layout)


    def getStations(self, plant_name, section_name, line_name):
        """
        Retrieves all stations for a given plant, section, and line from the database.

        Args:
            plant_name (str): The name of the plant to filter stations by.
            section_name (str): The name of the section to filter stations by.
            line_name (str): The name of the line to filter stations by.

        Returns:
            list: A list of strings.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing stations.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve station data.")
            return
    
        # Ensure valid plant, section, and line names are provided
        if not plant_name or not section_name or not line_name:
            QMessageBox.warning(self, "Error", "No plant, section, or line selected. Unable to retrieve stations.")
            return

        # Connect to the database and query the stations for the specified plant, section, and line
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = "SELECT * FROM Station WHERE plant_name = ? AND section_name = ? AND line_name = ?"
            cursor.execute(query, (plant_name, section_name, line_name))
            stations = cursor.fetchall()
            conn.close()

            # Format stations as <station name>
            return [f"{row[3]}" for row in stations]  # Assuming name is at column index 3
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve stations:\n{str(e)}")
            return []


    def loadStations(self):
        """
        Loads stations for the selected plant, section, and line into the station combo box.
        """
        # Get the selected plant, section, and line names from the labels in the Station window
        plant_name = self.plant_name_label.text().strip()
        section_name = self.section_name_label.text().strip()
        line_name = self.line_name_label.text().strip()
    
        # Retrieve and populate stations for the selected plant, section, and line
        stations_list = self.getStations(plant_name, section_name, line_name)
        if stations_list is not None:
            # Populate the station combo box
            self.id_combo.clear()
            self.id_combo.addItems(stations_list)


    # Navigation Handlers
    def firstStation(self):
        if self.id_combo.count() > 0:
            self.id_combo.setCurrentIndex(0)
            
    def previousStation(self):
        current_index = self.id_combo.currentIndex()
        if current_index > 0:
            self.id_combo.setCurrentIndex(current_index - 1)
    
    def nextStation(self):
        current_index = self.id_combo.currentIndex()
        if current_index < self.id_combo.count() - 1:
            self.id_combo.setCurrentIndex(current_index + 1)
      
    def lastStation(self):
        if self.id_combo.count() > 0:
            self.id_combo.setCurrentIndex(self.id_combo.count() - 1)

    def newStation(self):
        """
        Prepares the Station Window for entering a new Station.
        Clears all inputs and disables navigation buttons.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving stations.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save station.")
            return
    
        # Clear input fields
        self.id_combo.blockSignals(True)  # Temporarily block signals
        self.id_combo.setCurrentIndex(-1)  # Clear the combo box selection
        self.id_combo.setEditText("")  # Clear the text
        self.id_combo.blockSignals(False)  # Re-enable signals

        self.location_input.clear()
        self.task_description_text.clear()
        self.equipment_used_input.clear()
        self.cycle_time_input.clear()
        self.capacity_input.clear()
        self.ergonomic_risk_input.clear()
        self.performance_metric_input.clear()
        self.power_consumption_input.clear()
        self.materials_used_input.clear()

        # Disable navigation and management buttons
        self.first_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.search_button.setEnabled(False)
    
        # Set focus on the ID combo box
        self.id_combo.setFocus()

    def saveStation(self):    
        """
        Saves or updates the Station data in the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving stations.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save station.")
            return
    
        # Connect to the database    
        database_path = self.parent().projectdatabasePath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Validate Station ID
        station_id = self.id_combo.currentText().strip()
        if not station_id:
            QMessageBox.warning(self, "Validation Error", "Station ID is required.")
            return

        # Validate Station ID (No spaces allowed)
        station_id = self.id_combo.currentText().strip()
        if " " in station_id:
            QMessageBox.warning(self, "Validation Error", "Station Name cannot contain spaces.")
            return
            
            
        # Get Plant Name from the label
        plant_name = self.plant_name_label.text().strip()
        if not plant_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name is required.")
            return

        # Get Section Name from the label
        section_name = self.section_name_label.text().strip()
        if not section_name:
            QMessageBox.warning(self, "Validation Error", "Section Name is required.")
            return

        # Get Line Name from the label
        line_name = self.line_name_label.text().strip()
        if not line_name:
            QMessageBox.warning(self, "Validation Error", "Line Name is required.")
            return

        # Collect all fields
        location = self.location_input.text().strip()
        task_description = self.task_description_text.toPlainText().strip()
        equipment_used = self.equipment_used_input.text().strip()
        cycle_time = float(self.cycle_time_input.text()) if self.cycle_time_input.text() else None
        capacity = int(self.capacity_input.text()) if self.capacity_input.text() else None
        ergonomic_risk = float(self.ergonomic_risk_input.text()) if self.ergonomic_risk_input.text() else None
        performance_metric = self.performance_metric_input.text().strip()
        power_consumption = float(self.power_consumption_input.text()) if self.power_consumption_input.text() else None
        materials_used = self.materials_used_input.text().strip()

        # Insert or update the station
        try:
            cursor.execute('''
                INSERT INTO Station (
                    plant_name, section_name, line_name, id, location, task_description, equipment_used,
                    cycle_time, capacity, ergonomic_risk_level, performance_metric, power_consumption, materials_used
                ) VALUES (
                    :plant_name, :section_name, :line_name, :id, :location, :task_description, :equipment_used,
                    :cycle_time, :capacity, :ergonomic_risk_level, :performance_metric, :power_consumption, :materials_used
                )
                ON CONFLICT(plant_name, section_name, line_name, id) DO UPDATE SET
                    location = excluded.location,
                    task_description = excluded.task_description,
                    equipment_used = excluded.equipment_used,
                    cycle_time = excluded.cycle_time,
                    capacity = excluded.capacity,
                    ergonomic_risk_level = excluded.ergonomic_risk_level,
                    performance_metric = excluded.performance_metric,
                    power_consumption = excluded.power_consumption,
                    materials_used = excluded.materials_used
            ''', {
                'plant_name': plant_name,
                'section_name': section_name,
                'line_name': line_name,
                'id': station_id,
                'location': location,
                'task_description': task_description,
                'equipment_used': equipment_used,
                'cycle_time': cycle_time,
                'capacity': capacity,
                'ergonomic_risk_level': ergonomic_risk,
                'performance_metric': performance_metric,
                'power_consumption': power_consumption,
                'materials_used': materials_used
            })

            conn.commit()

            QMessageBox.information(self, "Success", f"Station '{station_id}' has been saved successfully.")

            # Enable navigation and other disabled buttons
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)

            current_text = self.id_combo.currentText()
            self.loadStations()  # Reload the station list
            index = self.id_combo.findText(current_text)
            if index != -1:
                self.id_combo.setCurrentIndex(index)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the station:\n{str(e)}")
        finally:
            conn.close()



    def deleteStation(self):
        """
        Handles the Delete button click event for the Station window.
        Deletes the selected station from the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting stations.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete station.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                  "Are you sure you want to delete this station?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
    
        # Get the selected Station Name
        station_id = self.id_combo.currentText().strip()
        if not station_id:
            QMessageBox.warning(self, "Error", "No Station ID selected. Unable to delete.")
            return
    
        # Get Plant Name, Section Name, and Line Name from the labels
        plant_name = self.plant_name_label.text().strip()
        section_name = self.section_name_label.text().strip()
        line_name = self.line_name_label.text().strip()
        if not plant_name or not section_name or not line_name:
            QMessageBox.warning(self, "Validation Error", "Plant, Section, and Line names are required.")
            return
    
        try:
            # Connect to the database
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            # TODO: warning the user if tool data exist
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            
            # Delete the station from the database
            cursor.execute("""
                DELETE FROM Station 
                WHERE plant_name = ? AND section_name = ? AND line_name = ? AND id = ?
            """, (plant_name, section_name, line_name, station_id))
            conn.commit()
    
            # Check if the station was successfully deleted
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Station '{station_id}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Station '{station_id}' has been deleted successfully.")
    
            # TODO: other delete code if needed..
    
            # Refresh the Station Name combo box
            self.id_combo.removeItem(self.id_combo.currentIndex())
    
            # Reset the Station Name combo box to the first index if items exist
            if self.id_combo.count() > 0:
                self.id_combo.setCurrentIndex(0)
                self.loadStationDetails()
    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the station: {e}")
        finally:
            conn.close()


    def searchStation(self):
        """
        Handles the Search button click event for the Station window.
        Allows the user to search for a station by its name within the selected plant, section, and line.
        """
        # Validate that the project file and database are created
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before searching.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to perform search.")
            return
    
        # Get Plant Name, Section Name, and Line Name from the labels
        plant_name = self.plant_name_label.text().strip()
        section_name = self.section_name_label.text().strip()
        line_name = self.line_name_label.text().strip()
        if not plant_name or not section_name or not line_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name, Section Name, and Line Name are required.")
            return
    
        # Create the search dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Station")
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)
    
        # Name Search
        name_layout = QHBoxLayout()
        name_label = QLabel("Search by Station ID:")
        name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
    
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
    
        # Function to handle the OK button click
        def performSearch():
            station_name = ""
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            try:
                # Search by Station Name
                if name_input.text().strip():
                    cursor.execute("""
                        SELECT id FROM Station 
                        WHERE plant_name = ? AND section_name = ? AND line_name = ? AND id = ?
                    """, (plant_name, section_name, line_name, name_input.text().strip()))
                    result = cursor.fetchone()
                    if result:
                        station_name = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search station:\n{str(e)}")
            finally:
                conn.close()
    
            if station_name:
                # Set the station name in the combo box and trigger the index change event
                index = self.id_combo.findText(station_name)
                if index != -1:
                    self.id_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Station name not found in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No station found with the given criteria.")
    
            dialog.accept()
    
        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)
    
        # Show the dialog
        dialog.exec_()


    def cancelStation(self):
        """
        Handles the Cancel button click event.
        Enables navigation buttons and resets the Section Name combo box to the first item if available.
        """
        # Enable navigation and other disabled buttons
        self.first_button.setEnabled(True)
        self.previous_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.last_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.search_button.setEnabled(True)
    
        # Reset the Section Name combo box to the first index if items exist
        if self.id_combo.count() > 0:
            self.id_combo.setCurrentIndex(0)
            self.loadStationDetails()
    
        # TODO: other cancel code if needed..

    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
        
    # Custom handler for the Close button
    def closeStation(self):
        self.saveVars()
        self.close()  # Trigger the close event


    def saveVars(self):
        # Extract values from controls in the worker window
        station_id = self.id_combo.currentText().strip() 
        self.parent().editStationName = station_id
    
    def loadStationDetails(self):
        # Get the selected station name
        selected_station_id = self.id_combo.currentText().strip()
        selected_line_name = self.line_name_label.text().strip()
        selected_section_name = self.section_name_label.text().strip()
        selected_plant_name = self.plant_name_label.text().strip()

        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving stations.")
            return

        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to load station details.")
            return
    
        if not selected_station_id:
            return
    
        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
    
        try:
            # Fetch station details
            cursor.execute("""
                SELECT * FROM Station 
                WHERE id = ? AND line_name = ? AND section_name = ? AND plant_name = ?
            """, (selected_station_id, selected_line_name, selected_section_name, selected_plant_name))
            station_data = cursor.fetchone()
    
            # Replace None from DB with an empty string in the station_data tuple
            if station_data:
                station_data = tuple("" if value is None else value for value in station_data)
    
                if station_data:
                    # Map station_data to controls
                    self.id_combo.setCurrentText(station_data[3])  # Station ID
                    self.location_input.setText(station_data[4])  # Location
                    self.task_description_text.setPlainText(station_data[5])  # Task Description
                    self.equipment_used_input.setText(station_data[6])  # Equipment Used
                    self.cycle_time_input.setText(str(station_data[7]))  # Cycle Time
                    self.capacity_input.setText(str(station_data[8]))  # Capacity
                    self.ergonomic_risk_input.setText(str(station_data[9]))  # Ergonomic Risk Level
                    self.performance_metric_input.setText(station_data[10])  # Performance Metric
                    self.power_consumption_input.setText(str(station_data[11]))  # Power Consumption
                    self.materials_used_input.setText(station_data[12])  # Materials Used
                else:
                    QMessageBox.warning(self, "Error", f"No data found for Station: {selected_station_id}")
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load station details: {str(e)}")
    
        finally:
            conn.close()




