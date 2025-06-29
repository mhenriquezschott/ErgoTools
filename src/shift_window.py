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



class ShiftWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shift Management")
        self.setGeometry(200, 200, 800, 500)
        self.setupUI()

        # Get the Plant, Section, Line, and Station names from the parent window
        #if self.parent():
        #    plant_name = self.parent().plant_combo.currentText()
        #    section_name = self.parent().section_combo.currentText()
        #    line_name = self.parent().line_combo.currentText()
        #    station_id = self.parent().station_combo.currentText()
        #    self.plant_name_label.setText(f"{plant_name}")
        #    self.section_name_label.setText(f"{section_name}")
        #    self.line_name_label.setText(f"{line_name}")
        #    self.station_id_label.setText(f"{station_id}")
            
        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadShifts()

            # Get the current text from the plant_combo in the parent window
            shift_combo_text = self.parent().shift_combo.currentText()

            # Extract the ID from the text 
            shift_id = shift_combo_text.strip()

            index = self.id_combo.findText(shift_id)
            if index != -1:
                self.id_combo.setCurrentIndex(index)    
    
            
            

    def setupUI(self):
        layout = QVBoxLayout()

        # Form layout for input controls
        form_layout = QGridLayout()
        bold_font = QFont()
        bold_font.setBold(True)

        # Plant, Section, Line, and Station Name (non-editable, bold, aligned with "-")
        
        #header_layout = QHBoxLayout()
        
        #plant_label = QLabel("Plant:")
        #plant_label.setFont(bold_font)
        #self.plant_name_label = QLabel("")
        #self.plant_name_label.setFont(bold_font)

        #separator_label_1 = QLabel(" - ")
        #separator_label_1.setFont(bold_font)

        #section_label = QLabel("Section:")
        #section_label.setFont(bold_font)
        #self.section_name_label = QLabel("")
        #self.section_name_label.setFont(bold_font)

        #separator_label_2 = QLabel(" - ")
        #separator_label_2.setFont(bold_font)

        #line_label = QLabel("Line:")
        #line_label.setFont(bold_font)
        #self.line_name_label = QLabel("")
        #self.line_name_label.setFont(bold_font)

        #separator_label_3 = QLabel(" - ")
        #separator_label_3.setFont(bold_font)

        #station_label = QLabel("Station:")
        #station_label.setFont(bold_font)
        #self.station_id_label = QLabel("")
        #self.station_id_label.setFont(bold_font)

        #header_layout.addWidget(plant_label)
        #header_layout.addWidget(self.plant_name_label)
        #header_layout.addWidget(separator_label_1)
        #header_layout.addWidget(section_label)
        #header_layout.addWidget(self.section_name_label)
        #header_layout.addWidget(separator_label_2)
        #header_layout.addWidget(line_label)
        #header_layout.addWidget(self.line_name_label)
        #header_layout.addWidget(separator_label_3)
        #header_layout.addWidget(station_label)
        #header_layout.addWidget(self.station_id_label)
        #header_layout.addStretch()  # Push content to the left

        #form_layout.addLayout(header_layout, 0, 0, 1, 2)

        # Shift fields
        form_layout.addWidget(QLabel("Shift ID:"), 1, 0)
        self.id_combo = QComboBox()
        self.id_combo.setEditable(True)  # Allow new entries
        self.id_combo.currentIndexChanged.connect(self.loadShiftDetails)
        form_layout.addWidget(self.id_combo, 1, 1)
        form_layout.addWidget(QLabel("Description:"), 2, 0)
        self.description_text = QTextEdit()
        form_layout.addWidget(self.description_text, 2, 1)

        form_layout.addWidget(QLabel("Start Time:"), 3, 0)
        self.start_time_input = QTimeEdit()
        self.start_time_input.setTime(QTime(8, 0))  # Default 08:00 AM
        self.start_time_input.timeChanged.connect(self.calculateDuration)
        form_layout.addWidget(self.start_time_input, 3, 1)

        form_layout.addWidget(QLabel("End Time:"), 4, 0)
        self.end_time_input = QTimeEdit()
        self.end_time_input.setTime(QTime(17, 0))  # Default 05:00 PM
        self.end_time_input.timeChanged.connect(self.calculateDuration)
        form_layout.addWidget(self.end_time_input, 4, 1)

        form_layout.addWidget(QLabel("Duration (hrs):"), 5, 0)
        self.duration_label = QLabel("9.0")  # Auto-calculated
        form_layout.addWidget(self.duration_label, 5, 1)

        form_layout.addWidget(QLabel("Shift Type:"), 6, 0)
        self.shift_type_input = QLineEdit()
        form_layout.addWidget(self.shift_type_input, 6, 1)

        form_layout.addWidget(QLabel("Tasks Performed:"), 7, 0)
        self.tasks_performed_input = QTextEdit()
        form_layout.addWidget(self.tasks_performed_input, 7, 1)

        form_layout.addWidget(QLabel("Product Output:"), 8, 0)
        self.product_output_input = QLineEdit()
        form_layout.addWidget(self.product_output_input, 8, 1)

        form_layout.addWidget(QLabel("Downtime (hrs):"), 9, 0)
        self.downtime_input = QLineEdit()
        form_layout.addWidget(self.downtime_input, 9, 1)

        form_layout.addWidget(QLabel("Incidents Reported:"), 10, 0)
        self.incidents_input = QTextEdit()
        form_layout.addWidget(self.incidents_input, 10, 1)

        form_layout.addWidget(QLabel("Ergonomic Risk Events:"), 11, 0)
        self.ergonomic_risk_input = QTextEdit()
        form_layout.addWidget(self.ergonomic_risk_input, 11, 1)

        form_layout.addWidget(QLabel("Notes:"), 12, 0)
        self.notes_input = QTextEdit()
        form_layout.addWidget(self.notes_input, 12, 1)

        layout.addLayout(form_layout)

        # Navigation and operation buttons
        button_layout = QHBoxLayout()

        self.first_button = QPushButton("|<")
        self.first_button.setFont(bold_font)
        self.first_button.clicked.connect(self.firstShift)

        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousShift)

        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)
        self.new_button.clicked.connect(self.newShift)

        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)
        self.save_button.clicked.connect(self.saveShift)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)
        self.delete_button.clicked.connect(self.deleteShift)

        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)
        self.search_button.clicked.connect(self.searchShift)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)
        self.cancel_button.clicked.connect(self.cancelShift)

        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)
        self.close_button.clicked.connect(self.closeShift)

        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextShift)

        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastShift)

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

        layout.addStretch()  # Spacer before buttons
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def calculateDuration(self):
        """ Calculate and update duration based on start and end times. """
        start = self.start_time_input.time()
        end = self.end_time_input.time()
        duration = start.msecsTo(end) / (1000 * 60 * 60)  # Convert milliseconds to hours
        self.duration_label.setText(f"{duration:.2f}")


    def getShifts(self):
        """
        Retrieves all shifts from the database.
    
        Returns:
            list: A list of shift IDs.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing shifts.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve shift data.")
            return
    
        # Connect to the database and query all shifts
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = "SELECT id FROM Shift"
            cursor.execute(query)
            shifts = cursor.fetchall()
            conn.close()
    
            # Format shifts as <shift ID>
            return [str(row[0]) for row in shifts]  # Assuming shift ID is at column index 0
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve shifts:\n{str(e)}")
            return []

    def loadShifts(self):
        """
        Loads all shifts into the shift combo box.
        """
        # Retrieve and populate shifts
        shifts_list = self.getShifts()
        if shifts_list is not None:
            # Populate the shift combo box
            self.id_combo.clear()
            self.id_combo.addItems(shifts_list)

    
    def newShift(self):
        """
        Prepares the Shift Window for entering a new shift.
        Clears all inputs and disables navigation buttons.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving shifts.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save shift.")
            return
    
        # Clear input fields
        self.id_combo.blockSignals(True)  # Temporarily block signals
        self.id_combo.setCurrentIndex(-1)  # Clear the combo box selection
        self.id_combo.setEditText("")  # Clear the text
        self.id_combo.blockSignals(False)  # Re-enable signals
    
        self.description_text.clear()
        self.start_time_input.setTime(QTime(8, 0))  # Default to 8:00 AM
        self.end_time_input.setTime(QTime(17, 0))  # Default to 5:00 PM
        self.duration_label.setText("9.0")  # Reset duration
        self.shift_type_input.clear()
        self.tasks_performed_input.clear()
        self.product_output_input.clear()
        self.downtime_input.clear()
        self.incidents_input.clear()
        self.ergonomic_risk_input.clear()
        self.notes_input.clear()
    
        # Disable navigation and management buttons
        self.first_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.search_button.setEnabled(False)
    
        # Set focus on the ID combo box
        self.id_combo.setFocus()

    
    
    
    def saveShift(self):    
        """
        Saves or updates the shift data in the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving shifts.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save shift.")
            return
    
        # Connect to the database    
        database_path = self.parent().projectdatabasePath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
    
        # Validate Shift ID
        shift_id = self.id_combo.currentText().strip()
        if not shift_id:
            QMessageBox.warning(self, "Validation Error", "Shift ID is required.")
            return


        # Validate Station ID (No spaces allowed)
        shift_id = self.id_combo.currentText().strip()
        if " " in shift_id:
            QMessageBox.warning(self, "Validation Error", "Shift ID cannot contain spaces.")
            return
            
             
            # Validate Product Output
        product_output_text = self.product_output_input.text().strip()
        if not product_output_text:
            product_output = 0
        else:
            try:
                product_output = float(product_output_text)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Product Output must be a valid number.")
                return
    
        # Validate Downtime
        downtime_text = self.downtime_input.text().strip()
        if not downtime_text:
            downtime = 0
        else:
            try:
                downtime = float(downtime_text)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Downtime must be a valid number.")
                return


        # Collect all fields
        description = self.description_text.toPlainText().strip()
        start_time = self.start_time_input.time().toString("HH:mm")
        end_time = self.end_time_input.time().toString("HH:mm")
        shift_type = self.shift_type_input.text().strip()
        tasks_performed = self.tasks_performed_input.toPlainText().strip()
        incidents_reported = self.incidents_input.toPlainText().strip()
        ergonomic_risk_events = self.ergonomic_risk_input.toPlainText().strip()
        notes = self.notes_input.toPlainText().strip()

        # Insert or update the shift
        try:
            cursor.execute('''
                INSERT INTO Shift (
                    id, description, start_time, end_time, 
                    shift_type, tasks_performed, product_output, downtime, 
                    incidents_reported, ergonomic_risk_events, notes
                ) VALUES (
                    :id, :description, :start_time, :end_time, 
                    :shift_type, :tasks_performed, :product_output, :downtime, 
                    :incidents_reported, :ergonomic_risk_events, :notes
                )
                ON CONFLICT(id) DO UPDATE SET
                    description = excluded.description,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    shift_type = excluded.shift_type,
                    tasks_performed = excluded.tasks_performed,
                    product_output = excluded.product_output,
                    downtime = excluded.downtime,
                    incidents_reported = excluded.incidents_reported,
                    ergonomic_risk_events = excluded.ergonomic_risk_events,
                    notes = excluded.notes
            ''', {
                'id': shift_id,
                'description': description,
                'start_time': start_time,
                'end_time': end_time,
                'shift_type': shift_type,
                'tasks_performed': tasks_performed,
                'product_output': product_output,
                'downtime': downtime,
                'incidents_reported': incidents_reported,
                'ergonomic_risk_events': ergonomic_risk_events,
                'notes': notes
            })

            conn.commit()

            QMessageBox.information(self, "Success", f"Shift '{shift_id}' has been saved successfully.")

            # Enable navigation and other disabled buttons
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)
    
            current_text = self.id_combo.currentText()
            self.loadShifts()  # Reload the shift list
            index = self.id_combo.findText(current_text)
            if index != -1:
                self.id_combo.setCurrentIndex(index)
    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the shift:\n{str(e)}")
        finally:
            conn.close()

    
    def deleteShift(self):
        """
        Handles the Delete button click event for the Shift window.
        Deletes the selected shift from the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting shifts.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete shift.")
            return

        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     "Are you sure you want to delete this shift?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
    
        # Get the selected Shift ID
        shift_id = self.id_combo.currentText().strip()
        if not shift_id:
            QMessageBox.warning(self, "Error", "No Shift ID selected. Unable to delete.")
            return
    
        try:
            # Connect to the database
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            # TODO: warning the user if tool data exist
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
             
            # Delete the shift from the database
            cursor.execute("""
                DELETE FROM Shift 
                WHERE id = ?
            """, (shift_id,))
            conn.commit()

            # Check if the shift was successfully deleted
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Shift '{shift_id}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Shift '{shift_id}' has been deleted successfully.")

            # Refresh the Shift Name combo box
            self.id_combo.removeItem(self.id_combo.currentIndex())
    
            # Reset the Shift Name combo box to the first index if items exist    
            if self.id_combo.count() > 0:
                self.id_combo.setCurrentIndex(0)
                self.loadShiftDetails()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the shift: {e}")
        finally:
            conn.close()


    def searchShift(self):
        """
        Handles the Search button click event for the Shift window.
        Allows the user to search for a shift by its ID.
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
        dialog.setWindowTitle("Search Shift")
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)

        # Name Search
        name_layout = QHBoxLayout()
        name_label = QLabel("Search by Shift ID:")
        name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
    
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
    
        # Function to handle the OK button click
        def performSearch():
            shift_id = ""
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            try:
                # Search by Shift ID
                if name_input.text().strip():
                    cursor.execute("""
                        SELECT id FROM Shift 
                        WHERE id = ?
                    """, (name_input.text().strip(),))
                    result = cursor.fetchone()
                    if result:
                        shift_id = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search shift:\n{str(e)}")
            finally:
                conn.close()
    
            if shift_id:
                # Set the shift ID in the combo box and trigger the index change event
                index = self.id_combo.findText(shift_id)
                if index != -1:
                    self.id_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Shift ID not found in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No shift found with the given criteria.")
    
            dialog.accept()

        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)

        # Show the dialog
        dialog.exec_()

    
    def cancelShift(self):
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
            self.loadShiftDetails()
    
        # TODO: other cancel code if needed..
    
    
    
    
    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
        
    # Custom handler for the Close button
    def closeShift(self):
        self.saveVars()
        self.close()  # Trigger the close event

    def saveVars(self):
        # Extract values from controls in the worker window
        shift_id = self.id_combo.currentText().strip() 
        self.parent().editShiftName = shift_id
        
    # Navigation Handlers
    def firstShift(self):
        if self.id_combo.count() > 0:
            self.id_combo.setCurrentIndex(0)
            
    def previousShift(self):
        current_index = self.id_combo.currentIndex()
        if current_index > 0:
            self.id_combo.setCurrentIndex(current_index - 1)
    
    def nextShift(self):
        current_index = self.id_combo.currentIndex()
        if current_index < self.id_combo.count() - 1:
            self.id_combo.setCurrentIndex(current_index + 1)
      
    def lastShift(self):
        if self.id_combo.count() > 0:
            self.id_combo.setCurrentIndex(self.id_combo.count() - 1)


    def loadShiftDetails(self):
        """
        Loads the details of the selected shift into the UI controls.
        """
        # Get the selected shift ID
        selected_shift_id = self.id_combo.currentText().strip()
    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving shifts.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to load shift details.")
            return
    
        if not selected_shift_id:
            return

        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
    
        try:
            # Fetch shift details
            cursor.execute("""
                SELECT * FROM Shift WHERE id = ?
            """, (selected_shift_id,))
            shift_data = cursor.fetchone()
    
            # Replace None from DB with an empty string in the shift_data tuple
            if shift_data:
                shift_data = tuple("" if value is None else value for value in shift_data)
    
                if shift_data:
                    # Map shift_data to controls
                    self.id_combo.setCurrentText(shift_data[0])  # Shift ID
                    self.description_text.setPlainText(shift_data[1])  # Description
                    self.start_time_input.setTime(QTime.fromString(shift_data[2], "HH:mm"))  # Start Time
                    self.end_time_input.setTime(QTime.fromString(shift_data[3], "HH:mm"))  # End Time
                    self.shift_type_input.setText(shift_data[4])  # Shift Type
                    self.tasks_performed_input.setText(shift_data[5])  # Tasks Performed
                    self.product_output_input.setText(str(shift_data[6]))  # Product Output    
                    self.downtime_input.setText(str(shift_data[7]))  # Downtime
                    self.incidents_input.setText(shift_data[8])  # Incidents Reported
                    self.ergonomic_risk_input.setText(shift_data[9])  # Ergonomic Risk Events    
                    self.notes_input.setPlainText(shift_data[10])  # Notes

                else:
                    QMessageBox.warning(self, "Error", f"No data found for Shift: {selected_shift_id}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load shift details: {str(e)}")
    
        finally:
            conn.close()

