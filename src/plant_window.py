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


class PlantWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plant Management")
        self.setGeometry(200, 200, 800, 600)
        self.setupUI()
        
        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadPlants()

            # Get the current text from the plant_combo in the parent window
            plant_combo_text = self.parent().plant_combo.currentText()

            # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
            plant_name = plant_combo_text.strip()

            index = self.name_combo.findText(plant_name)
            if index != -1:
                self.name_combo.setCurrentIndex(index)



    def setupUI(self):
        layout = QVBoxLayout()

        # Form layout for input controls
        form_layout = QGridLayout()

        # Name
        form_layout.addWidget(QLabel("Plant Name (ID):"), 0, 0)
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)  # Allow new entries
        self.name_combo.currentIndexChanged.connect(self.loadPlantDetails)
        form_layout.addWidget(self.name_combo, 0, 1)

        # Description
        form_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_text = QTextEdit()
        form_layout.addWidget(self.description_text, 1, 1)

        # Location
        form_layout.addWidget(QLabel("Location:"), 2, 0)
        self.location_input = QLineEdit()
        form_layout.addWidget(self.location_input, 2, 1)

        # Type of Plant
        form_layout.addWidget(QLabel("Type of Plant:"), 3, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Manufacturing", "Processing", "Assembly", "Other"])
        self.type_combo.setEditable(True)  # Allow the user to write in the combobox
        form_layout.addWidget(self.type_combo, 3, 1)

        # Area
        form_layout.addWidget(QLabel("Area (ft²):"), 4, 0)
        self.area_input = QLineEdit()
        form_layout.addWidget(self.area_input, 4, 1)

        # Number of Shifts
        form_layout.addWidget(QLabel("Number of Shifts:"), 5, 0)
        self.num_shifts_spin = QSpinBox()
        self.num_shifts_spin.setRange(0, 100)
        form_layout.addWidget(self.num_shifts_spin, 5, 1)

        # Start Time
        form_layout.addWidget(QLabel("Start Time:"), 6, 0)
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(8, 0))  # Default to 8:00 AM
        self.start_time.timeChanged.connect(self.calculateOperationalHours)  # Connect signal
        form_layout.addWidget(self.start_time, 6, 1)

        # End Time
        form_layout.addWidget(QLabel("End Time:"), 7, 0)
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(17, 0))  # Default to 5:00 PM
        self.end_time.timeChanged.connect(self.calculateOperationalHours)  # Connect signal
        form_layout.addWidget(self.end_time, 7, 1)

        # Operational Hours (calculated)
        form_layout.addWidget(QLabel("Operational Hours:"), 8, 0)
        self.operational_hours_label = QLabel("9.00")
        form_layout.addWidget(self.operational_hours_label, 8, 1)

        # Production Capacity
        form_layout.addWidget(QLabel("Production Capacity:"), 9, 0)
        self.production_capacity_input = QLineEdit()
        form_layout.addWidget(self.production_capacity_input, 9, 1)

        # Opening Date
        form_layout.addWidget(QLabel("Opening Date:"), 10, 0)
        self.opening_date = QDateEdit()
        self.opening_date.setCalendarPopup(True)
        self.opening_date.setDate(QDate.currentDate())
        self.opening_date.dateChanged.connect(self.calculateYearsOfOperation)  # Connect the signal
        form_layout.addWidget(self.opening_date, 10, 1)

        # Years of Operation (calculated)
        form_layout.addWidget(QLabel("Years of Operation:"), 11, 0)
        self.years_of_operation_label = QLabel("0")
        form_layout.addWidget(self.years_of_operation_label, 11, 1)

        layout.addLayout(form_layout)


        # Create bold font for button labels
        bold_font = QFont()
        bold_font.setBold(True)
        
        # Buttons for navigation and operations
        button_layout = QHBoxLayout()
        
        
        
        self.first_button = QPushButton("|<")
        self.first_button.setFont(bold_font)
        self.first_button.clicked.connect(self.firstPlant)

        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousPlant)

        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)
        self.new_button.clicked.connect(self.newPlant)

        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)
        self.save_button.clicked.connect(self.savePlant)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)
        self.delete_button.clicked.connect(self.deletePlant)

        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)
        self.search_button.clicked.connect(self.searchPlant)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)
        self.cancel_button.clicked.connect(self.cancelPlant)

        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)
        self.close_button.clicked.connect(self.closePlant)

        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextPlant)

        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastPlant)
        
        
        

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


        # Add layouts to the main layout
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Connect button signals (placeholder connections)
        self.close_button.clicked.connect(self.close)
 

    def calculateOperationalHours(self):
        # Get the start time and end time as QTime objects
        start_time = self.start_time.time()
        end_time = self.end_time.time()

        # Calculate the difference in minutes
        total_minutes = start_time.secsTo(end_time) // 60
        if total_minutes < 0:  # Handle overnight shifts
            total_minutes += 24 * 60

        # Calculate the operational hours
        operational_hours = total_minutes / 60.0

        # Update the label
        self.operational_hours_label.setText(f"{operational_hours:.2f}")


 
    def calculateYearsOfOperation(self):
        # Get the opening date
        opening_date = self.opening_date.date()
        
        # Get the current date
        current_date = QDate.currentDate()
        
        # Calculate the difference in years
        years_of_operation = opening_date.daysTo(current_date) // 365
        
        # Update the label
        self.years_of_operation_label.setText(str(years_of_operation))

    
    # Navigation Handlers
    def firstPlant(self):
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(0)
            
        

    def previousPlant(self):
        current_index = self.name_combo.currentIndex()
        if current_index > 0:
            self.name_combo.setCurrentIndex(current_index - 1)
        
     

    def nextPlant(self):
        current_index = self.name_combo.currentIndex()
        if current_index < self.name_combo.count() - 1:
            self.name_combo.setCurrentIndex(current_index + 1)
            
   
    def lastPlant(self):
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(self.name_combo.count() - 1)
            
 
    
    
    def newPlant(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving plants.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save plant.")
            return

        # Clear input fields
        self.name_combo.blockSignals(True)  # Temporarily block signals
        self.name_combo.setCurrentIndex(-1)  # Clear the combo box selection
        self.name_combo.setEditText("")  # Clear the text
        self.name_combo.blockSignals(False)  # Re-enable signals
    
        self.description_text.clear()
        self.location_input.clear()
        self.type_combo.setCurrentIndex(-1)
        self.area_input.clear()
        self.num_shifts_spin.setValue(1)  # Default to 1 shift
        self.start_time.setTime(QTime(8, 0))  # Default start time 8:00 AM
        self.end_time.setTime(QTime(17, 0))  # Default end time 5:00 PM
        self.operational_hours_label.setText("9.0")  # Default operational hours
        self.production_capacity_input.clear()
        self.opening_date.setDate(QDate.currentDate())  # Default to current date
        self.years_of_operation_label.setText("0")  # Default years of operation
    
        # Disable navigation and management buttons
        self.first_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.search_button.setEnabled(False)

        # Set focus on the name combo box
        self.name_combo.setFocus()
    
    
    
    def savePlant(self):    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving plants.")
            return

        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save plant.")
            return

        # Connect to the database
        database_path = self.parent().projectdatabasePath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Validate Plant Name
        plant_name = self.name_combo.currentText().strip()
        if not plant_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name is required.")
            return

        # Validate Plant Name (No spaces allowed)
        plant_name = self.name_combo.currentText().strip()
        if " " in plant_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name cannot contain spaces.")
            return
            
        # Collect all fields
        description = self.description_text.toPlainText().strip()
        location = self.location_input.text().strip()
        plant_type = self.type_combo.currentText() if self.type_combo.currentIndex() != -1 else None
        area = float(self.area_input.text()) if self.area_input.text() else None
        num_shifts = self.num_shifts_spin.value()
        start_time = self.start_time.time().toString("HH:mm:ss")
        end_time = self.end_time.time().toString("HH:mm:ss")
        operational_hours = float(self.operational_hours_label.text()) if self.operational_hours_label.text() else None
        production_capacity = float(self.production_capacity_input.text()) if self.production_capacity_input.text() else None
        opening_date = self.opening_date.date().toString("yyyy-MM-dd")
        years_of_operation = int(self.years_of_operation_label.text()) if self.years_of_operation_label.text().isdigit() else None

        # Insert or update the plant
        try:
            cursor.execute('''
                INSERT INTO Plant (
                    name, description, location, type, area, number_of_shifts, start_time,
                    end_time, operational_hours, production_capacity, opening_date, years_of_operation
                ) VALUES (
                    :name, :description, :location, :type, :area, :number_of_shifts, :start_time,
                    :end_time, :operational_hours, :production_capacity, :opening_date, :years_of_operation
                )
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    location = excluded.location,
                    type = excluded.type,
                    area = excluded.area,
                    number_of_shifts = excluded.number_of_shifts,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    operational_hours = excluded.operational_hours,
                    production_capacity = excluded.production_capacity,
                    opening_date = excluded.opening_date,
                    years_of_operation = excluded.years_of_operation
            ''', {
                'name': plant_name,
                'description': description,
                'location': location,
                'type': plant_type,
                'area': area,
                'number_of_shifts': num_shifts,
                'start_time': start_time,
                'end_time': end_time,
                'operational_hours': operational_hours,
                'production_capacity': production_capacity,
                'opening_date': opening_date,
                'years_of_operation': years_of_operation
            })

            conn.commit()

            QMessageBox.information(self, "Success", f"Plant '{plant_name}' has been saved successfully.")

            # Enable navigation and other disabled buttons
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)

            current_text = self.name_combo.currentText()
            self.loadPlants()  # Reload the plant list
            index = self.name_combo.findText(current_text)
            if index != -1:
                self.name_combo.setCurrentIndex(index)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the plant:\n{str(e)}")
        finally:
            conn.close()




    def deletePlant(self):
        """
        Handles the Delete button click event for the Plant window.
        Deletes the selected plant from the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting plants.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete plant.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                      "Are you sure you want to delete this plant?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
    
        # Get the selected Plant Name
        plant_name = self.name_combo.currentText()
        if not plant_name:
            QMessageBox.warning(self, "Error", "No Plant Name selected. Unable to delete.")
            return
    
        try:
            # Connect to the database
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            # TODO: warning the user if tool data exist
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
     
            # Delete the plant from the database
            cursor.execute("DELETE FROM Plant WHERE name = ?", (plant_name,))
            conn.commit()
    
            # Check if the plant was successfully deleted
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Plant Name '{plant_name}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Plant Name '{plant_name}' has been deleted successfully.")
            
            # TODO: other delete code if needed..
    
            # Refresh the Plant Name combo box
            self.name_combo.removeItem(self.name_combo.currentIndex())
    
            # Reset the Plant Name combo box to the first index if items exist
            if self.name_combo.count() > 0:
                self.name_combo.setCurrentIndex(0)    
                self.loadPlantDetails()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the plant: {e}")
        finally:
            conn.close()



    def searchPlant(self):
        """
        Handles the Search button click event for the Plant window.
        Allows the user to search for a plant by its name.
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
        dialog.setWindowTitle("Search Plant")
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)
    
        # Name Search
        name_layout = QHBoxLayout()
        name_label = QLabel("Search by Plant Name:")
        name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
    
        # Function to handle the OK button click
        def performSearch():
            plant_name = ""
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            try:
                # Search by Plant Name
                if name_input.text().strip():
                    cursor.execute("SELECT name FROM Plant WHERE name = ?", (name_input.text().strip(),))
                    result = cursor.fetchone()
                    if result:
                        plant_name = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search plant:\n{str(e)}")
            finally:
                conn.close()
    
            if plant_name:
                # Set the plant name in the combo box and trigger the index change event
                index = self.name_combo.findText(plant_name)
                if index != -1:
                    self.name_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Plant name not found in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No plant found with the given criteria.")
    
            dialog.accept()
    
        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)
    
        # Show the dialog
        dialog.exec_()

    
    
    
    def cancelPlant(self):
        """
        Handles the Cancel button click event.
        Enables navigation buttons and resets the Plant Name combo box to the first item if available.
        """
        # Enable navigation and other disabled buttons
        self.first_button.setEnabled(True)
        self.previous_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.last_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.search_button.setEnabled(True)
    
        # Reset the Plant Name combo box to the first index if items exist
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(0)
            self.loadPlantDetails()

        # TODO: other cancel code if needed..

    
    
    
    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
        
    # Custom handler for the Close button
    def closePlant(self):
        self.saveVars()
        self.close()  # Trigger the close event


    def saveVars(self):
        # Extract values from controls in the worker window
        plant_name = self.name_combo.currentText().strip() 
        self.parent().editPlantName = plant_name
 
    def getPlants(self):
        """
        Retrieves all plants from the database.

        Returns:
            list: A list of strings.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing plants.")
            return
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve plant data.")
            return

        # Connect to the database and query the plants
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = "SELECT * FROM Plant"
            cursor.execute(query)
            plants = cursor.fetchall()
            conn.close()

            # Format plants as <plant name>(<location>, <type>)
            return [f"{row[0]}" for row in plants]  # Assuming name, location, and type are columns 0, 2, and 3
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve plants:\n{str(e)}")
            return []


    def loadPlants(self):
        """
        Loads plants into the plant combo box.
        """
        plants_list = self.getPlants()
        if plants_list is not None:
            # Populate the plant combo box
            self.name_combo.clear()
            self.name_combo.addItems(plants_list)



    def loadPlantDetails(self):
        # Get the selected plant name
        selected_plant_name = self.name_combo.currentText()
    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving plants.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to load plant details.")
            return
    
        if not selected_plant_name:
            return
    
        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
    
        try:
            # Fetch plant details
            cursor.execute("SELECT * FROM Plant WHERE name = ?", (selected_plant_name,))
            plant_data = cursor.fetchone()
    
            # Replace None from DB with an empty string in the plant_data tuple
            if plant_data:
                plant_data = tuple("" if value is None else value for value in plant_data)
    
            if plant_data:
                # Map plant_data to controls
                self.name_combo.setCurrentText(plant_data[0])  # Name
                self.description_text.setPlainText(plant_data[1])  # Description
                self.location_input.setText(plant_data[2])  # Location
                self.type_combo.setCurrentText(plant_data[3])  # Type of Plant
                self.area_input.setText(str(plant_data[4]))  # Area
                self.num_shifts_spin.setValue(int(plant_data[5]) if plant_data[5] else 0)  # Number of Shifts
                self.start_time.setTime(QTime.fromString(plant_data[6], "HH:mm:ss"))  # Start Time
                self.end_time.setTime(QTime.fromString(plant_data[7], "HH:mm:ss"))  # End Time
                self.operational_hours_label.setText(str(plant_data[8]))  # Operational Hours
                self.production_capacity_input.setText(str(plant_data[9]))  # Production Capacity
                self.opening_date.setDate(QDate.fromString(plant_data[10], "yyyy-MM-dd"))  # Opening Date
                self.years_of_operation_label.setText(str(plant_data[11]))  # Years of Operation
            else:
                QMessageBox.warning(self, "Error", f"No data found for Plant: {selected_plant_name}")
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load plant details: {str(e)}")
    
        finally:
            conn.close()


