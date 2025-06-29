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



class SectionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Section Management")
        self.setGeometry(200, 200, 800, 500)
        self.setupUI()

        # Get the Plant Name from the parent window
        if self.parent():
            plant_name = self.parent().plant_combo.currentText()
            self.plant_name_label.setText(f"{plant_name}")
        
        
        
        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadSections()

            # Get the current text from the plant_combo in the parent window
            section_combo_text = self.parent().section_combo.currentText()

            # Extract the ID from the text 
            section_name = section_combo_text.strip()

            index = self.name_combo.findText(section_name)
            if index != -1:
                self.name_combo.setCurrentIndex(index)

            



    def getSections(self, plant_name):
        """
        Retrieves all sections for a given plant from the database.

        Args:
            plant_name (str): The name of the plant to filter sections by.

        Returns:
            list: A list of strings.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing sections.")
            return
            
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve section data.")
            return

        # Ensure a valid plant name is provided
        if not plant_name:
            QMessageBox.warning(self, "Error", "No plant selected. Unable to retrieve sections.")
            return

        # Connect to the database and query the sections for the specified plant
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = "SELECT * FROM Section WHERE plant_name = ?"
            cursor.execute(query, (plant_name,))
            sections = cursor.fetchall()
            conn.close()

            # Format sections as <section name>(<location>, <capacity>)
            return [f"{row[1]}" for row in sections]  # Assuming name, location, and capacity are columns 1, 3, and 4
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve sections:\n{str(e)}")
            return []


    def loadSections(self):
        """
        Loads sections for the selected plant into the section combo box.
        """
        # Get the selected plant name from the parent window
        #plant_name = self.parent().plant_combo.currentText().strip()
        plant_name = self.plant_name_label.text().strip()
        #print("Plant Name:",plant_name)
        
        # Retrieve and populate sections for the selected plant
        sections_list = self.getSections(plant_name)
        if sections_list is not None:
            # Populate the section combo box
            self.name_combo.clear()
            self.name_combo.addItems(sections_list)


    def setupUI(self):
        layout = QVBoxLayout()

        # Form layout for input controls
        form_layout = QGridLayout()

        # Plant Name (non-editable, bold)
        plant_name_label = QLabel("Plant:")
        bold_font = QFont()
        bold_font.setBold(True)
        plant_name_label.setFont(bold_font)
        self.plant_name_label = QLabel("")
        self.plant_name_label.setFont(bold_font)
        form_layout.addWidget(plant_name_label, 0, 0)
        form_layout.addWidget(self.plant_name_label, 0, 1)

        # Section Name
        form_layout.addWidget(QLabel("Section Name (ID):"), 1, 0)
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)  # Allow new entries
        self.name_combo.currentIndexChanged.connect(self.loadSectionDetails)
        form_layout.addWidget(self.name_combo, 1, 1)

        # Description
        form_layout.addWidget(QLabel("Description:"), 2, 0)
        self.description_text = QTextEdit()
        form_layout.addWidget(self.description_text, 2, 1)

        # Location
        form_layout.addWidget(QLabel("Location:"), 3, 0)
        self.location_input = QLineEdit()
        form_layout.addWidget(self.location_input, 3, 1)

        # Capacity
        form_layout.addWidget(QLabel("Capacity:"), 4, 0)
        self.capacity_input = QLineEdit()
        form_layout.addWidget(self.capacity_input, 4, 1)

        # Area
        form_layout.addWidget(QLabel("Area (ft²):"), 5, 0)
        self.area_input = QLineEdit()
        form_layout.addWidget(self.area_input, 5, 1)

        # Creation Date
        form_layout.addWidget(QLabel("Creation Date:"), 6, 0)
        self.creation_date_input = QDateEdit()
        self.creation_date_input.setCalendarPopup(True)
        self.creation_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.creation_date_input, 6, 1)

        layout.addLayout(form_layout)

        # Navigation and operation buttons
        button_layout = QHBoxLayout()

        self.first_button = QPushButton("|<")
        self.first_button.setFont(bold_font)
        self.first_button.clicked.connect(self.firstSection)

        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousSection)

        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)
        self.new_button.clicked.connect(self.newSection)

        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)
        self.save_button.clicked.connect(self.saveSection)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)
        self.delete_button.clicked.connect(self.deleteSection)

        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)
        self.search_button.clicked.connect(self.searchSection)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)
        self.cancel_button.clicked.connect(self.cancelSection)

        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)
        self.close_button.clicked.connect(self.closeSection)

        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextSection)

        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastSection)

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


    def newSection(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving sections.")
            return

        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save section.")
            return

        # Clear input fields
        self.name_combo.blockSignals(True)  # Temporarily block signals
        self.name_combo.setCurrentIndex(-1)  # Clear the combo box selection
        self.name_combo.setEditText("")  # Clear the text
        self.name_combo.blockSignals(False)  # Re-enable signals

        self.description_text.clear()
        self.location_input.clear()
        self.capacity_input.clear()
        self.area_input.clear()
        self.creation_date_input.setDate(QDate.currentDate())  # Default to current date

        # Disable navigation and management buttons
        self.first_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.last_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.search_button.setEnabled(False)

        # Set focus on the name combo box
        self.name_combo.setFocus()


    def saveSection(self):    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving sections.")
            return

        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save section.")
            return

        # Connect to the database
        database_path = self.parent().projectdatabasePath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Validate Section Name
        section_name = self.name_combo.currentText().strip()
        if not section_name:
            QMessageBox.warning(self, "Validation Error", "Section Name is required.")
            return
        
        # Validate Section Name (No spaces allowed)
        section_name = self.name_combo.currentText().strip()
        if " " in section_name:
            QMessageBox.warning(self, "Validation Error", "Section Name cannot contain spaces.")
            return


        # Get Plant Name from the label
        plant_name = self.plant_name_label.text().strip()
        if not plant_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name is required.")
            return

        # Collect all fields
        description = self.description_text.toPlainText().strip()
        location = self.location_input.text().strip()
        capacity = float(self.capacity_input.text()) if self.capacity_input.text() else None
        area = float(self.area_input.text()) if self.area_input.text() else None
        creation_date = self.creation_date_input.date().toString("yyyy-MM-dd")

        # Insert or update the section
        #print("Plant Name:", plant_name)
        #print("Section Name:", section_name)
        
        try:
            cursor.execute('''
                INSERT INTO Section (
                    plant_name, name, description, location, capacity, area, creation_date
                ) VALUES (
                    :plant_name, :name, :description, :location, :capacity, :area, :creation_date
                )
                ON CONFLICT(plant_name, name) DO UPDATE SET
                    description = excluded.description,
                    location = excluded.location,
                    capacity = excluded.capacity,
                    area = excluded.area,
                    creation_date = excluded.creation_date
            ''', {
                'plant_name': plant_name,
                'name': section_name,
                'description': description,
                'location': location,
                'capacity': capacity,
                'area': area,
                'creation_date': creation_date
            })

            conn.commit()

            QMessageBox.information(self, "Success", f"Section '{section_name}' has been saved successfully.")

            # Enable navigation and other disabled buttons
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)

            current_text = self.name_combo.currentText()
            self.loadSections()  # Reload the section list
            index = self.name_combo.findText(current_text)
            if index != -1:
                self.name_combo.setCurrentIndex(index)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the section:\n{str(e)}")
        finally:
            conn.close()

    def deleteSection(self):
        """
        Handles the Delete button click event for the Section window.
        Deletes the selected section from the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting sections.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete section.")
            return
    
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                      "Are you sure you want to delete this section?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
    
        # Get the selected Section Name
        section_name = self.name_combo.currentText()
        if not section_name:
            QMessageBox.warning(self, "Error", "No Section Name selected. Unable to delete.")
            return
    
        # Get Plant Name from the label
        plant_name = self.plant_name_label.text().strip()
        if not plant_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name is required.")
            return
    
        try:
            # Connect to the database
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            # TODO: warning the user if tool data exist
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Delete the section from the database
            cursor.execute("DELETE FROM Section WHERE plant_name = ? AND name = ?", (plant_name, section_name))
            conn.commit()
    
            # Check if the section was successfully deleted
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Section '{section_name}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Section '{section_name}' has been deleted successfully.")
    
            # TODO: other delete code if needed..

            # Refresh the Section Name combo box
            self.name_combo.removeItem(self.name_combo.currentIndex())

            # Reset the Section Name combo box to the first index if items exist
            if self.name_combo.count() > 0:
                self.name_combo.setCurrentIndex(0)
                self.loadSectionDetails()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the section: {e}")
        finally:
            conn.close()

    def searchSection(self):
        """
        Handles the Search button click event for the Section window.
        Allows the user to search for a section by its name within the selected plant.
        """
        # Validate that the project file and database are created
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before searching.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to perform search.")
            return
    
        # Get Plant Name from the label
        plant_name = self.plant_name_label.text().strip()
        if not plant_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name is required.")
            return
    
        # Create the search dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Section")
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)
    
        # Name Search
        name_layout = QHBoxLayout()
        name_label = QLabel("Search by Section Name:")
        name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
    
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
    
        # Function to handle the OK button click
        def performSearch():
            section_name = ""
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            try:
                # Search by Section Name
                if name_input.text().strip():
                    cursor.execute("SELECT name FROM Section WHERE plant_name = ? AND name = ?", 
                                   (plant_name, name_input.text().strip()))
                    result = cursor.fetchone()
                    if result:
                        section_name = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search section:\n{str(e)}")
            finally:
                conn.close()
    
            if section_name:
                # Set the section name in the combo box and trigger the index change event
                index = self.name_combo.findText(section_name)
                if index != -1:
                    self.name_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Section name not found in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No section found with the given criteria.")
    
            dialog.accept()

        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)

        # Show the dialog
        dialog.exec_()

    def cancelSection(self):
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
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(0)
            self.loadSectionDetails()
    
        # TODO: other cancel code if needed..


   
    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
        
    # Custom handler for the Close button
    def closeSection(self):
        self.saveVars()
        self.close()  # Trigger the close event


    def saveVars(self):
        # Extract values from controls in the worker window
        section_name = self.name_combo.currentText().strip() 
        self.parent().editSectionName = section_name
    
    # Navigation Handlers
    def firstSection(self):
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(0)
            
    def previousSection(self):
        current_index = self.name_combo.currentIndex()
        if current_index > 0:
            self.name_combo.setCurrentIndex(current_index - 1)
    
    def nextSection(self):
        current_index = self.name_combo.currentIndex()
        if current_index < self.name_combo.count() - 1:
            self.name_combo.setCurrentIndex(current_index + 1)
      
    def lastSection(self):
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(self.name_combo.count() - 1)
            
 
    
    def loadSectionDetails(self):
        # Get the selected section name
        selected_section_name = self.name_combo.currentText()
        selected_plant_name = self.parent().plant_combo.currentText()
    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving sections.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to load section details.")
            return
    
        if not selected_section_name:
            return

        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
    
        try:
            # Fetch section details
            cursor.execute("SELECT * FROM Section WHERE name = ? AND plant_name = ?", (selected_section_name, selected_plant_name))
            section_data = cursor.fetchone()

            # Replace None from DB with an empty string in the section_data tuple
            if section_data:
                section_data = tuple("" if value is None else value for value in section_data)
    
            if section_data:
                # Map section_data to controls
                self.name_combo.setCurrentText(section_data[1])  # Section Name
                self.description_text.setPlainText(section_data[2])  # Description
                self.location_input.setText(section_data[3])  # Location
                self.capacity_input.setText(str(section_data[4]))  # Capacity
                self.area_input.setText(str(section_data[5]))  # Area
                self.creation_date_input.setDate(QDate.fromString(section_data[6], "yyyy-MM-dd"))  # Creation Date
            else:
                QMessageBox.warning(self, "Error", f"No data found for Section: {selected_section_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load section details: {str(e)}")

        finally:
            conn.close()

       
       
