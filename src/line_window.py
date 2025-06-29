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



class LineWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Line Management")
        self.setGeometry(200, 200, 800, 500)
        self.setupUI()

        # Get the Plant Name and Section Name from the parent window
        if self.parent():
            plant_name = self.parent().plant_combo.currentText()
            section_name = self.parent().section_combo.currentText()
            self.plant_name_label.setText(f"{plant_name}")
            self.section_name_label.setText(f"{section_name}")
        
        
        # Check if a project has been created from the parent window
        if self.parent().projectFileCreated:
            self.loadLines()

            # Get the current text from the plant_combo in the parent window
            line_combo_text = self.parent().line_combo.currentText()

            # Extract the ID from the text 
            line_name = line_combo_text.strip()

            index = self.name_combo.findText(line_name)
            if index != -1:
                self.name_combo.setCurrentIndex(index)
            
            
    def getLines(self, plant_name, section_name):
        """
        Retrieves all lines for a given plant and section from the database.
    
        Args:
            plant_name (str): The name of the plant to filter lines by.
            section_name (str): The name of the section to filter lines by.
    
        Returns:
            list: A list of strings.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing lines.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve line data.")
            return
    
        # Ensure valid plant and section names are provided
        if not plant_name or not section_name:
            QMessageBox.warning(self, "Error", "No plant or section selected. Unable to retrieve lines.")
            return

        # Connect to the database and query the lines for the specified plant and section
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            query = "SELECT * FROM Line WHERE plant_name = ? AND section_name = ?"
            cursor.execute(query, (plant_name, section_name))
            lines = cursor.fetchall()
            conn.close()

            # Format lines as <line name>(<description>, <location>)
            return [f"{row[2]}" for row in lines]  # Assuming name, description, and location are columns 2, 3, and 4
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve lines:\n{str(e)}")
            return []


    def loadLines(self):
        """
        Loads lines for the selected plant and section into the line combo box.
        """
        # Get the selected plant and section names from the labels in the Line window
        plant_name = self.plant_name_label.text().strip()
        section_name = self.section_name_label.text().strip()
    
        # Retrieve and populate lines for the selected plant and section
        lines_list = self.getLines(plant_name, section_name)
        if lines_list is not None:
            # Populate the line combo box
            self.name_combo.clear()
            self.name_combo.addItems(lines_list)


    def setupUI(self):
        layout = QVBoxLayout()

        # Form layout for input controls
        form_layout = QGridLayout()

        # Plant and Section Name (non-editable, bold, aligned with a "-")
        plant_section_layout = QHBoxLayout()
        bold_font = QFont()
        bold_font.setBold(True)

        plant_name_label = QLabel("Plant:")
        plant_name_label.setFont(bold_font)
        self.plant_name_label = QLabel("")
        self.plant_name_label.setFont(bold_font)
    
        separator_label = QLabel(" - ")
        separator_label.setFont(bold_font)
    
        section_name_label = QLabel("Section:")
        section_name_label.setFont(bold_font)
        self.section_name_label = QLabel("")
        self.section_name_label.setFont(bold_font)

        plant_section_layout.addWidget(plant_name_label)
        plant_section_layout.addWidget(self.plant_name_label)
        plant_section_layout.addWidget(separator_label)
        plant_section_layout.addWidget(section_name_label)
        plant_section_layout.addWidget(self.section_name_label)
        plant_section_layout.addStretch()  # Push content to the left

        form_layout.addLayout(plant_section_layout, 0, 0, 1, 2)


        # Line Name
        form_layout.addWidget(QLabel("Line Name (ID):"), 2, 0)
        self.name_combo = QComboBox()
        self.name_combo.setEditable(True)  # Allow new entries
        self.name_combo.currentIndexChanged.connect(self.loadLineDetails)
        form_layout.addWidget(self.name_combo, 2, 1)

        # Description
        form_layout.addWidget(QLabel("Description:"), 3, 0)
        self.description_text = QTextEdit()
        form_layout.addWidget(self.description_text, 3, 1)

        # Location
        form_layout.addWidget(QLabel("Location:"), 4, 0)
        self.location_input = QLineEdit()
        form_layout.addWidget(self.location_input, 4, 1)

        # Products
        form_layout.addWidget(QLabel("Products:"), 5, 0)
        self.products_input = QLineEdit()
        form_layout.addWidget(self.products_input, 5, 1)

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
        self.first_button.clicked.connect(self.firstLine)

        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousLine)

        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)
        self.new_button.clicked.connect(self.newLine)

        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)
        self.save_button.clicked.connect(self.saveLine)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)
        self.delete_button.clicked.connect(self.deleteLine)

        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)
        self.search_button.clicked.connect(self.searchLine)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)
        self.cancel_button.clicked.connect(self.cancelLine)

        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)
        self.close_button.clicked.connect(self.closeLine)

        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextLine)

        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastLine)

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

    def newLine(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving lines.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save line.")
            return
    
        # Clear input fields
        self.name_combo.blockSignals(True)  # Temporarily block signals
        self.name_combo.setCurrentIndex(-1)  # Clear the combo box selection
        self.name_combo.setEditText("")  # Clear the text
        self.name_combo.blockSignals(False)  # Re-enable signals
    
        self.description_text.clear()
        self.location_input.clear()
        self.products_input.clear()
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


    def saveLine(self):    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving lines.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save line.")
            return
    
        # Connect to the database    
        database_path = self.parent().projectdatabasePath
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Validate Line Name
        line_name = self.name_combo.currentText().strip()
        if not line_name:
            QMessageBox.warning(self, "Validation Error", "Line Name is required.")
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

        # Validate Line Name (No spaces allowed)
        line_name = self.name_combo.currentText().strip()
        if " " in line_name:
            QMessageBox.warning(self, "Validation Error", "Line Name cannot contain spaces.")
            return
            
            
        # Collect all fields
        description = self.description_text.toPlainText().strip()
        location = self.location_input.text().strip()
        products = self.products_input.text().strip()
        creation_date = self.creation_date_input.date().toString("yyyy-MM-dd")

        # Insert or update the line
        try:
            cursor.execute('''
                INSERT INTO Line (
                    plant_name, section_name, name, description, location, products, creation_date
                ) VALUES (
                    :plant_name, :section_name, :name, :description, :location, :products, :creation_date
                )
                ON CONFLICT(plant_name, section_name, name) DO UPDATE SET
                    description = excluded.description,
                    location = excluded.location,
                    products = excluded.products,
                    creation_date = excluded.creation_date
            ''', {
                'plant_name': plant_name,
                'section_name': section_name,
                'name': line_name,
                'description': description,
                'location': location,
                'products': products,
                'creation_date': creation_date
            })

            conn.commit()

            QMessageBox.information(self, "Success", f"Line '{line_name}' has been saved successfully.")

            # Enable navigation and other disabled buttons
            self.first_button.setEnabled(True)
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.last_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.search_button.setEnabled(True)

            current_text = self.name_combo.currentText()
            self.loadLines()  # Reload the line list
            index = self.name_combo.findText(current_text)
            if index != -1:
                self.name_combo.setCurrentIndex(index)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving the line:\n{str(e)}")
        finally:
            conn.close()



    def deleteLine(self):
        """
        Handles the Delete button click event for the Line window.
        Deletes the selected line from the database.
        """
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before deleting lines.")
            return

        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to delete line.")
            return

        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                      "Are you sure you want to delete this line?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Get the selected Line Name
        line_name = self.name_combo.currentText()
        if not line_name:
            QMessageBox.warning(self, "Error", "No Line Name selected. Unable to delete.")
            return

        # Get Plant Name and Section Name from the labels
        plant_name = self.plant_name_label.text().strip()
        section_name = self.section_name_label.text().strip()
        if not plant_name or not section_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name and Section Name are required.")
            return

        try:
            # Connect to the database
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            # TODO: warning the user if tool data exist
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            
            # Delete the line from the database
            cursor.execute("DELETE FROM Line WHERE plant_name = ? AND section_name = ? AND name = ?", (plant_name, section_name, line_name))
            conn.commit()

            # Check if the line was successfully deleted
            if cursor.rowcount == 0:
                QMessageBox.warning(self, "Error", f"Line '{line_name}' not found in the database.")
            else:
                QMessageBox.information(self, "Success", f"Line '{line_name}' has been deleted successfully.")

            # TODO: other delete code if needed..

            # Refresh the Line Name combo box
            self.name_combo.removeItem(self.name_combo.currentIndex())

            # Reset the Line Name combo box to the first index if items exist
            if self.name_combo.count() > 0:
                self.name_combo.setCurrentIndex(0)
                self.loadLineDetails()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the line: {e}")
        finally:
            conn.close()


    def searchLine(self):
        """
        Handles the Search button click event for the Line window.
        Allows the user to search for a line by its name within the selected plant and section.
        """
        # Validate that the project file and database are created
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before searching.")
            return
    
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to perform search.")
            return
    
        # Get Plant Name and Section Name from the labels
        plant_name = self.plant_name_label.text().strip()
        section_name = self.section_name_label.text().strip()
        if not plant_name or not section_name:
            QMessageBox.warning(self, "Validation Error", "Plant Name and Section Name are required.")
            return
    
        # Create the search dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Line")
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)

        # Name Search
        name_layout = QHBoxLayout()
        name_label = QLabel("Search by Line Name:")
        name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        # Function to handle the OK button click
        def performSearch():
            line_name = ""
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            try:
                # Search by Line Name
                if name_input.text().strip():
                    cursor.execute("SELECT name FROM Line WHERE plant_name = ? AND section_name = ? AND name = ?", 
                                   (plant_name, section_name, name_input.text().strip()))
                    result = cursor.fetchone()
                    if result:
                        line_name = result[0]
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search line:\n{str(e)}")
            finally:
                conn.close()

            if line_name:
                # Set the line name in the combo box and trigger the index change event
                index = self.name_combo.findText(line_name)
                if index != -1:
                    self.name_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, "Not Found", "Line name not found in combo box.")
            else:
                QMessageBox.information(self, "No Match", "No line found with the given criteria.")

            dialog.accept()

        # Connect buttons to actions
        button_box.accepted.connect(performSearch)
        button_box.rejected.connect(dialog.reject)

        # Show the dialog
        dialog.exec_()


    def cancelLine(self):
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
            self.loadLineDetails()
    
        # TODO: other cancel code if needed..

    # Override the closeEvent method to handle the window close event
    def closeEvent(self, event):
        self.saveVars()
        
    # Custom handler for the Close button
    def closeLine(self):
        self.saveVars()
        self.close()  # Trigger the close event


    def saveVars(self):
        # Extract values from controls in the worker window
        line_name = self.name_combo.currentText().strip() 
        self.parent().editLineName = line_name
        
        
    # Navigation Handlers
    def firstLine(self):
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(0)
            
    def previousLine(self):
        current_index = self.name_combo.currentIndex()
        if current_index > 0:
            self.name_combo.setCurrentIndex(current_index - 1)
    
    def nextLine(self):
        current_index = self.name_combo.currentIndex()
        if current_index < self.name_combo.count() - 1:
            self.name_combo.setCurrentIndex(current_index + 1)
      
    def lastLine(self):
        if self.name_combo.count() > 0:
            self.name_combo.setCurrentIndex(self.name_combo.count() - 1)


    def loadLineDetails(self):
        # Get the selected line name
        selected_line_name = self.name_combo.currentText()
        selected_section_name = self.section_name_label.text().strip()
        selected_plant_name = self.plant_name_label.text().strip()
    
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving lines.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to load line details.")
            return
    
        if not selected_line_name:
            return

        # Connect to the database
        conn = sqlite3.connect(self.parent().projectdatabasePath)
        cursor = conn.cursor()
    
        try:
            # Fetch line details
            cursor.execute("SELECT * FROM Line WHERE name = ? AND section_name = ? AND plant_name = ?", 
                           (selected_line_name, selected_section_name, selected_plant_name))
            line_data = cursor.fetchone()
    
            # Replace None from DB with an empty string in the line_data tuple
            if line_data:
                line_data = tuple("" if value is None else value for value in line_data)
    
                if line_data:
                    # Map line_data to controls
                    self.name_combo.setCurrentText(line_data[2])  # Line Name
                    self.description_text.setPlainText(line_data[3])  # Description
                    self.location_input.setText(line_data[4])  # Location
                    self.products_input.setText(line_data[5])  # Products
                    self.creation_date_input.setDate(QDate.fromString(line_data[6], "yyyy-MM-dd"))  # Creation Date
                else:
                    QMessageBox.warning(self, "Error", f"No data found for Line: {selected_line_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load line details: {str(e)}")

        finally:
            conn.close()


