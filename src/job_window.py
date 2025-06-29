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
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QFont, QPixmap, QRegExpValidator, QColor

from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import QRegularExpression, QRegExp

#from PySide2.QtWidgets import QSpacerItem, QSizePolicy

from pyLiFFT import LiFFT
from pyDUET import DUET
from pyTST import TST




class JobWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Job Management")
        self.setGeometry(200, 200, 800, 500)
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
        layout = QVBoxLayout()
        form_layout = QGridLayout()
        bold_font = QFont()
        bold_font.setBold(True)
    
        # --- Job Basic Info ---
        form_layout.addWidget(QLabel("Job ID:"), 0, 0)
        self.job_id_combo = QComboBox()
        self.job_id_combo.setEditable(True)  # Allow new job entries
        #self.job_id_combo.currentIndexChanged.connect(self.loadJobDetails)
        form_layout.addWidget(self.job_id_combo, 0, 1)
    
        form_layout.addWidget(QLabel("Job Name:"), 1, 0)
        self.job_name_input = QLineEdit()
        form_layout.addWidget(self.job_name_input, 1, 1)
    
        form_layout.addWidget(QLabel("Description:"), 2, 0)
        self.job_description_input = QTextEdit()
        form_layout.addWidget(self.job_description_input, 2, 1)
    
        
        form_layout.addWidget(QLabel("Risk Measurements:"), 3, 0)
        form_layout.addWidget(self.createRiskMeasurementTable(), 3, 1)
    
        
        self.job_id_combo.currentIndexChanged.connect(self.loadJobDetails)
        
        
        layout.addLayout(form_layout)
    
    
        # --- Navigation and Operation Buttons ---
        button_layout = QHBoxLayout()
    
        self.first_button = QPushButton("|<")
        self.first_button.setFont(bold_font)
        self.first_button.clicked.connect(self.firstJob)
    
        self.previous_button = QPushButton("<")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousJob)
    
        self.next_button = QPushButton(">")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextJob)
    
        self.last_button = QPushButton(">|")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastJob)
        
        self.new_button = QPushButton("New")
        self.new_button.setFont(bold_font)
        self.new_button.clicked.connect(self.newJob)
    
        self.save_button = QPushButton("Save")
        self.save_button.setFont(bold_font)
        self.save_button.clicked.connect(self.saveJob)
    
        self.delete_button = QPushButton("Delete")
        self.delete_button.setFont(bold_font)
        self.delete_button.clicked.connect(self.deleteJob)
    
        self.search_button = QPushButton("Search")
        self.search_button.setFont(bold_font)
        self.search_button.clicked.connect(self.searchJob)
    
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(bold_font)
        self.cancel_button.clicked.connect(self.cancelJob)
    
        self.close_button = QPushButton("Close")
        self.close_button.setFont(bold_font)
        self.close_button.clicked.connect(self.close)
    
       
    
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
    
        layout.addStretch()
        layout.addLayout(button_layout)
        self.setLayout(layout)


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
            color = tool_obj.colorFromDamageRisk(damage)
    
        
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
    
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
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
            conn = sqlite3.connect(self.parent().projectdatabasePath)
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

        # Clear the table values and colors (but keep headers, layout, formatting)
        for row in range(self.risk_table.rowCount()):
            for col in [1, 2]:  # Only Total Cumulative Damage and Probability Outcome
                item = self.risk_table.item(row, col)
                if item:
                    item.setText("0.0")
                    item.setBackground(QColor("#ffffff"))  # Reset to white background
    
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
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
    
        try:
            # Save or update Job table
            cursor.execute('''
                INSERT INTO Job (id, name, description)
                VALUES (:id, :name, :description)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description
            ''', {
                'id': job_id,
                'name': job_name,
                'description': job_description
            })

            # Save measurements from self.risk_table
            for row in range(3):  # 3 tools: LiFFT, DUET, ST
                tool = self.risk_table.item(row, 0).text().strip()
    
                damage_text = self.risk_table.item(row, 1).text().strip()
                prob_text = self.risk_table.item(row, 2).text().strip()
    
                try:
                    damage = float(damage_text) if damage_text else 0.0
                    probability = float(prob_text) if prob_text else 0.0
                except ValueError:
                    QMessageBox.warning(self, "Validation Error", f"{tool} fields must be numeric.")
                    return

                # Recalculate color using tool-specific function
                if tool == "LiFFT":
                    #from tools.lifft import LiFFT
                    lifft = LiFFT(self.parent().selectedMeasurementSystem, 0, 0, 0)
                    color = lifft.colorFromDamageRisk(damage)
                elif tool == "DUET":
                    #from tools.duet import DUET
                    duet = DUET(0, 0)
                    color = duet.colorFromDamageRisk(damage)
                elif tool == "ST":
                    #from tools.shoulder_tool import TST
                    tst = TST(self.parent().selectedMeasurementSystem, "", 0, 0, 0)
                    color = tst.colorFromDamageRisk(damage)
                else:
                    color = "#ffffff"
    
                cursor.execute('''
                    INSERT INTO JobMeasurement (job_id, tool_id, total_cumulative_damage, probability_outcome, color)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(job_id, tool_id) DO UPDATE SET
                        total_cumulative_damage = excluded.total_cumulative_damage,
                        probability_outcome = excluded.probability_outcome,
                        color = excluded.color
                ''', (job_id, tool, damage, probability, color))
    
            conn.commit()
    
            QMessageBox.information(self, "Success", f"Job '{job_id}' has been saved successfully.")
    
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
    
        except sqlite3.Error as e:
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
            conn = sqlite3.connect(self.parent().projectdatabasePath)
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
    
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
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
    
            # Disable signals to avoid triggering recomputation on setItem
            self.risk_table.blockSignals(True)

            tools = ["LiFFT", "DUET", "ST"]
            for row, tool in enumerate(tools):
                cursor.execute("""
                    SELECT total_cumulative_damage, probability_outcome
                    FROM JobMeasurement
                    WHERE job_id = ? AND tool_id = ?
                """, (selected_job_id, tool))
                measurement = cursor.fetchone()
    
                if measurement:
                    damage_val, prob_val = measurement
                    damage_val = float(damage_val) if damage_val is not None else 0.0
                    prob_val = float(prob_val) if prob_val is not None else 0.0
                else:
                    damage_val = 0.0
                    prob_val = 0.0
    
                # Update table cells
                self.risk_table.item(row, 1).setText(str(damage_val))
                self.risk_table.item(row, 2).setText(str(prob_val))
    
                # Recalculate risk and apply color based on tool
                if tool == "LiFFT":
                    tool_obj = LiFFT(self.parent().selectedMeasurementSystem, 0, 0, 0)
                elif tool == "DUET":
                    tool_obj = DUET(0, 0)
                elif tool == "ST":
                    tool_obj = TST(self.parent().selectedMeasurementSystem, "", 0, 0, 0)
                else:
                    continue
    
                # Color background of probability cell
                color = tool_obj.colorFromDamageRisk(damage_val)
                self.risk_table.item(row, 1).setBackground(QColor(color))
                self.risk_table.item(row, 2).setBackground(QColor(color))

            self.risk_table.blockSignals(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load job details:\n{str(e)}")
        finally:
            conn.close()




