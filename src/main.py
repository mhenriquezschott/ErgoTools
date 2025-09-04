
import sys
import vtk
import sqlite3
import datetime
import os
import subprocess
import csv
from vtk.util.numpy_support import numpy_to_vtk
import numpy as np
from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtCore import Qt, QTimer, QLocale
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont, QPixmap
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, QLineEdit,
                             QFrame, QWidget, QComboBox, QDateTimeEdit, QMessageBox, QAction, QDialog, QFileDialog, QSpinBox)
import math
from pyLiFFT import LiFFT
from pyDUET import DUET
from pyTST import TST

class ErgoTools(QtWidgets.QMainWindow):
    
    def retranslateUI(self):
        # control panel
        self.upButton.setText(QtWidgets.QApplication.translate('App', 'Up'))
        self.downButton.setText(QtWidgets.QApplication.translate('App', 'Down'))
        self.leftButton.setText(QtWidgets.QApplication.translate('App', 'Left'))
        self.rightButton.setText(QtWidgets.QApplication.translate('App', 'Right'))
        self.zoomLabel.setText(QtWidgets.QApplication.translate("App", "Zoom:"))
        self.rotationLabel.setText(QtWidgets.QApplication.translate("App", "Rotation:"))
        self.axisGroup.setTitle(QtWidgets.QApplication.translate("App", "Rotation Axis"))
  
        # Main window 
        self.setWindowTitle(QtWidgets.QApplication.translate("App", "Fatigue Failure Risk Assessment Tools"))
    
        # Updating the menu bar items
        self.file_menu.setTitle(QtWidgets.QApplication.translate('App', 'File'))
        self.export_csv_action.setText(QtWidgets.QApplication.translate('App', 'Export selected tool to CSV format'))
        self.exit_action.setText(QtWidgets.QApplication.translate('App', 'Exit'))
        self.help_menu.setTitle(QtWidgets.QApplication.translate('App', 'Help'))
        self.user_guide_action.setText(QtWidgets.QApplication.translate('App', 'User Guide'))
        self.about_action.setText(QtWidgets.QApplication.translate('App', 'About'))
    
        # showAuthorsDialog
        self.authorsDialog.setWindowTitle(QtWidgets.QApplication.translate("App", "Authors"))
        self.authorsLabel.setText(QtWidgets.QApplication.translate("App", "Ivan Nail, Ph.D."))

        # setupTopWidgets
        self.userIDLabel.setText(QtWidgets.QApplication.translate("App", "User ID:"))
        self.loadButton.setText(QtWidgets.QApplication.translate("App", "Load"))
        self.saveButton.setText(QtWidgets.QApplication.translate("App", "Save"))
        self.languageLabel.setText(QtWidgets.QApplication.translate("App", "Language:"))
        self.unitLabel.setText(QtWidgets.QApplication.translate("App", "Unit:"))
 
        # updateUnitsLabels 
        if self.unitComboBox.currentText() == QtWidgets.QApplication.translate("App", "English"):
            self.lifft_headers_labels[1].setText(QtWidgets.QApplication.translate("App", "Lever Arm (inch)"))
            self.lifft_headers_labels[2].setText(QtWidgets.QApplication.translate("App", "Load (lb)"))
            self.lifft_headers_labels[3].setText(QtWidgets.QApplication.translate("App", "Moment (ft.lb)"))
        
            self.tst_headers_labels[2].setText(QtWidgets.QApplication.translate("App", "Lever Arm (inch)"))  # Change to inch
            self.tst_headers_labels[3].setText(QtWidgets.QApplication.translate("App", "Load (lb)"))         # Change to lb
            self.tst_headers_labels[4].setText(QtWidgets.QApplication.translate("App", "Moment (ft.lb)"))    # Change to ft.lb
    
        elif self.unitComboBox.currentText() == QtWidgets.QApplication.translate("App", "Metric"):
            self.lifft_headers_labels[1].setText(QtWidgets.QApplication.translate("App", "Lever Arm (cm)"))    # Change back to cm
            self.lifft_headers_labels[2].setText(QtWidgets.QApplication.translate("App", "Load (N)"))          # Change back to N
            self.lifft_headers_labels[3].setText(QtWidgets.QApplication.translate("App", "Moment (N.m)"))      # Change back to N.m

            self.tst_headers_labels[2].setText(QtWidgets.QApplication.translate("App", "Lever Arm (cm)"))    # Change back to cm
            self.tst_headers_labels[3].setText(QtWidgets.QApplication.translate("App", "Load (N)"))          # Change back to N
            self.tst_headers_labels[4].setText(QtWidgets.QApplication.translate("App", "Moment (N.m)"))      # Change back to N.m
    
        # setupLiFFTTab
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.lifft_tab), QtWidgets.QApplication.translate("App", "Lifting Fatigue Failure Tool (LiFFT)"))
        self.lifft_headers_labels[0].setText(QtWidgets.QApplication.translate("App", "Task #"))
        self.lifft_headers_labels[4].setText(QtWidgets.QApplication.translate("App", "Repetitions (per work day)"))
        self.lifft_headers_labels[5].setText(QtWidgets.QApplication.translate("App", "Damage (cumulative)"))
        self.lifft_headers_labels[6].setText(QtWidgets.QApplication.translate("App", "% Total (damage)"))
    
        self.lifft_total_damage_label.setText(QtWidgets.QApplication.translate("App", "Total Cumulative Damage:"))
        self.lifft_probability_label.setText(QtWidgets.QApplication.translate("App", "Probability of High Risk Job * (%):"))
    
        self.lifft_reset_button.setText(QtWidgets.QApplication.translate("App", "Reset"))
        self.lifft_calculate_button.setText(QtWidgets.QApplication.translate("App", "Calculate"))


        # setupDUETTab
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.duet_tab), QtWidgets.QApplication.translate("App", "Distal Upper Extremity Tool (DUET)"))
    
        # Column headers translations
        self.duet_headers_labels[0].setText(QtWidgets.QApplication.translate("App", "Task #"))
        self.duet_headers_labels[1].setText(QtWidgets.QApplication.translate("App", "OMNI-Res Scale"))
        self.duet_headers_labels[2].setText(QtWidgets.QApplication.translate("App", "Repetitions (per work day)"))
        self.duet_headers_labels[3].setText(QtWidgets.QApplication.translate("App", "Damage (cumulative)"))
        self.duet_headers_labels[4].setText(QtWidgets.QApplication.translate("App", "% Total (damage)"))
    
        # Bottom row labels translations
        self.duet_total_damage_label.setText(QtWidgets.QApplication.translate("App", "Total Cumulative Damage:"))
        self.duet_probability_label.setText(QtWidgets.QApplication.translate("App", "Probability of Distal Upper Extremity Outcome (%):"))
    
        # Buttons translations
        self.duet_reset_button.setText(QtWidgets.QApplication.translate("App", "Reset"))
        self.duet_calculate_button.setText(QtWidgets.QApplication.translate("App", "Calculate"))
   

        # setupTSTTab
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tst_tab), QtWidgets.QApplication.translate("App", "Shoulder Tool (ST)"))
    
        # Column headers translations
        self.tst_headers_labels[0].setText(QtWidgets.QApplication.translate("App", "Task #"))
        self.tst_headers_labels[1].setText(QtWidgets.QApplication.translate("App", "Type of Task"))
        self.tst_headers_labels[5].setText(QtWidgets.QApplication.translate("App", "Repetitions (per work day)"))
        self.tst_headers_labels[6].setText(QtWidgets.QApplication.translate("App", "Damage (cumulative)"))
        self.tst_headers_labels[7].setText(QtWidgets.QApplication.translate("App", "% Total (damage)"))
    
        # Bottom row labels translations
        self.tst_total_damage_label.setText(QtWidgets.QApplication.translate("App", "Total Cumulative Damage:"))
        self.tst_probability_label.setText(QtWidgets.QApplication.translate("App", "Probability of Shoulder Outcome (%):"))
    
        # Buttons translations
        self.tst_reset_button.setText(QtWidgets.QApplication.translate("App", "Reset"))
        self.tst_calculate_button.setText(QtWidgets.QApplication.translate("App", "Calculate"))

        # Number of Tasks Label
        self.numTasksLabel.setText(QtWidgets.QApplication.translate("App", "N° of Tasks:"))
        
        # "Set Tasks" Button
        self.setTasksButton.setText(QtWidgets.QApplication.translate("App", "Set Tasks"))


  
  
    
  
  
  
  
  
  
  
    # ------------------------- INIT -----------------------------------------
    # ------------------------------------------------------------------------   
    
        
    def __init__(self, parent=None):
        super(ErgoTools, self).__init__(parent)
        
        self.databasePath = "../data/ergotools_data.db"
        self.setupDatabase()
        self.isAnimationAllowed = False  # Add a flag to control when animation is allowed
        
        self.num_task = 10
        
        self.setupUI()
        self.setupMenuBar()  # Setup the menu bar
        self.setupStatusBar()  # Setup the status bar
        self.setupAnimationTimers()
        self.isAnimationAllowed = True
        self.setupLocale()
        

       
        
    def setupLocale(self):
        # Get the system's current locale
        system_locale = QLocale.system()
        
        # Get the language of the system's locale
        system_language = system_locale.language()

        # Check if the language is English or Spanish
        if system_language == QLocale.English: #
            self.languageComboBox.setCurrentIndex(0) # english
        elif system_language == QLocale.Spanish:
            self.languageComboBox.setCurrentIndex(1) # spanish
        else:
            print("System language is neither English nor Spanish.")

        
    def setupMenuBar(self):
        # Get the menu bar
        self.menu_bar = self.menuBar()

        # Creating the "File" menu
        #self.file_menu = self.menu_bar.addMenu('&File')
        self.file_menu = self.menu_bar.addMenu('File')

        # Export to CSV action
        #self.export_csv_action = QAction('Export selected tool to &CSV format', self)
        self.export_csv_action = QAction('Export selected tool to CSV format', self)
        self.export_csv_action.triggered.connect(self.exportToCSV)
        self.file_menu.addAction(self.export_csv_action)

        # Adding a separator
        self.file_menu.addSeparator()

        # Creating the "Exit" action
        #self.exit_action = QAction('&Exit', self)
        self.exit_action = QAction('Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(self.close)  # Assuming self.close() is your method to close the application
        self.file_menu.addAction(self.exit_action)

        # Creating the "Help" menu
        #self.help_menu = self.menu_bar.addMenu('&Help')
        self.help_menu = self.menu_bar.addMenu('Help')

        # User Guide action
        #self.user_guide_action = QAction('&User Guide', self)
        self.user_guide_action = QAction('User Guide', self)
        self.user_guide_action.triggered.connect(self.openHelpPDF)
        self.help_menu.addAction(self.user_guide_action)

        # About action
        #self.about_action = QAction('&About', self)
        self.about_action = QAction('About', self)
        self.authorsDialog = QDialog(self)
        self.authorsDialog.setWindowTitle("Authors")
        self.authorsLabel = QLabel("Ivan Nail, Ph.D.")
        self.about_action.triggered.connect(self.showAuthorsDialog)
        self.help_menu.addAction(self.about_action)
    
    def exportToCSV(self):
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)

        # Validation
        valid, userid, datetime = self.validateInputsForSave()
        if not valid:
            return

        if currentTabIndex == 0:  # LiFFT Tool
            # Prepare data for CSV
            csv_data = []
            headers = ["UserID", "DateTime", "Task ID", "Lever Arm", "Load", "Moment", "Repetitions", "Cumulative Damage", "Percentage Total", "Total Cumulative Damage", "Probability High Risk", "Unit"]
            csv_data.append(headers)

            for i in range(self.num_task):
                task_data = [
                    userid,
                    datetime,
                    str(i + 1),  # Task ID
                    self.lifft_lever_arm_inputs[i].text(),
                    self.lifft_load_inputs[i].text(),
                    self.lifft_output_labels_matrix[i][3].text(),
                    self.lifft_repetitions_inputs[i].text(),
                    self.lifft_output_labels_matrix[i][5].text(),
                    self.lifft_output_labels_matrix[i][6].text(),
                    self.lifft_total_damage_value_label.text(),
                    self.lifft_probability_value_label.text(),
                    self.unitComboBox.currentText(),
                ]
                csv_data.append(task_data)

            # File save dialog
            suggested_filename = f"LiFFT_{userid}_{datetime.replace(':', '-')}.csv"
            filepath, _ = QFileDialog.getSaveFileName(self, "Save CSV", suggested_filename, "CSV files (*.csv)")
        
            if not filepath:
                # User canceled save
                return

            # Write data to CSV
            try:
                with open(filepath, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(csv_data)
                #QMessageBox.information(self, "Export Successful", "LiFFT data exported successfully to CSV.")
                QMessageBox.information(self, "Export Successful" if self.languageComboBox.currentIndex() == 0 else "Exportación Exitosa", "LiFFT data exported successfully to CSV." if self.languageComboBox.currentIndex() == 0 else "Los datos de LiFFT se han exportado correctamente a CSV.")

            except Exception as e:
                #QMessageBox.critical(self, "Export Error", f"An error occurred while exporting to CSV: {e}")
                QMessageBox.critical(self, "Export Error" if self.languageComboBox.currentIndex() == 0 else "Error de Exportación", f"An error occurred while exporting to CSV: {e}" if self.languageComboBox.currentIndex() == 0 else f"Ocurrió un error al exportar a CSV: {e}")

        
        
        elif currentTabIndex == 1:  # DUET
            # Prepare data for CSV
            csv_data_duet = []
            headers_duet = ["UserID", "DateTime", "Task ID", "OMNI-Res Scale", "Repetitions", "Cumulative Damage", "Percentage Total", "Total Cumulative Damage", "Probability Distal Upper Extremity Outcome", "Unit"]
            csv_data_duet.append(headers_duet)

            for i in range(self.num_task):
                omni_res_scale = self.omnires_dropdowns[i].currentText()
                repetitions = self.duet_repetitions_inputs[i].text()
                cumulative_damage = self.duet_output_labels_matrix[i][3].text()  # Assuming cumulative damage is at index 3
                percentage_total = self.duet_output_labels_matrix[i][4].text()  # Assuming percentage total is at index 4
                # Note: Adjust indices based on actual placement in your output labels matrix
                task_data_duet = [
                    userid,
                    datetime,
                    str(i + 1),  # Task ID
                    omni_res_scale,
                    repetitions,
                    cumulative_damage,
                    percentage_total,
                    self.duet_total_damage_value_label.text(),
                    self.duet_probability_value_label.text(),
                    self.unitComboBox.currentText(),
                ]
                csv_data_duet.append(task_data_duet)
            
            # File save dialog for DUET data
            suggested_filename_duet = f"DUET_{userid}_{datetime.replace(':', '-')}.csv"
            filepath_duet, _ = QFileDialog.getSaveFileName(self, "Save DUET CSV", suggested_filename_duet, "CSV files (*.csv)")
    
            if not filepath_duet:
                # User canceled save
                return

            # Write DUET data to CSV
            try:
                with open(filepath_duet, 'w', newline='', encoding='utf-8') as file_duet:
                    writer_duet = csv.writer(file_duet)
                    writer_duet.writerows(csv_data_duet)
                #QMessageBox.information(self, "Export Successful", "DUET data exported successfully to CSV.")
                QMessageBox.information(self, "Export Successful" if self.languageComboBox.currentIndex() == 0 else "Exportación Exitosa", "DUET data exported successfully to CSV." if self.languageComboBox.currentIndex() == 0 else "Los datos de DUET se exportaron exitosamente a CSV.")

            except Exception as e:
                #QMessageBox.critical(self, "Export Error", f"An error occurred while exporting DUET to CSV: {e}")
                QMessageBox.critical(self, "Export Error" if self.languageComboBox.currentIndex() == 0 else "Error de Exportación", f"An error occurred while exporting DUET to CSV: {e}" if self.languageComboBox.currentIndex() == 0 else f"Ocurrió un error al exportar los datos de DUET a CSV: {e}")

            
        elif currentTabIndex == 2:  # ST
            # Prepare data for CSV
            csv_data_st = []
            headers_st = ["UserID", "DateTime", "Task ID", "Type of Task", "Lever Arm", "Load", "Moment", "Repetitions", "Cumulative Damage", "Percentage Total", "Total Cumulative Damage", "Probability Shoulder Outcome", "Unit"]
            csv_data_st.append(headers_st)

            for i in range(self.num_task):
                type_of_task = self.tst_type_of_task_dropdowns[i].currentText()
                lever_arm = self.tst_lever_arm_inputs[i].text()
                load = self.tst_load_inputs[i].text()
                moment = self.tst_output_labels_matrix[i][4].text()  # Assuming moment is at index 4
                repetitions = self.tst_repetitions_inputs[i].text()
                cumulative_damage = self.tst_output_labels_matrix[i][6].text()  # Assuming cumulative damage is at index 6
                percentage_total = self.tst_output_labels_matrix[i][7].text()  # Assuming percentage total is at index 7
                task_data_st = [
                    userid,
                    datetime,
                    str(i + 1),  # Task ID
                    type_of_task,
                    lever_arm,
                    load,
                    moment,
                    repetitions,
                    cumulative_damage,
                    percentage_total,
                    self.tst_total_damage_value_label.text(),
                    self.tst_probability_value_label.text(),
                    self.unitComboBox.currentText(),
                ]
                csv_data_st.append(task_data_st)

            # File save dialog for ST data
            suggested_filename_st = f"TST_{userid}_{datetime.replace(':', '-')}.csv"
            filepath_st, _ = QFileDialog.getSaveFileName(self, "Save The Shoulder Tool CSV", suggested_filename_st, "CSV files (*.csv)")

            if not filepath_st:
                # User canceled save
                return

            # Write ST data to CSV
            try:
                with open(filepath_st, 'w', newline='', encoding='utf-8') as file_st:
                    writer_st = csv.writer(file_st)
                    writer_st.writerows(csv_data_st)
                #QMessageBox.information(self, "Export Successful", "The Shoulder Tool data exported successfully to CSV.")
                QMessageBox.information(self, "Export Successful" if self.languageComboBox.currentIndex() == 0 else "Exportación Exitosa", "The Shoulder Tool data exported successfully to CSV." if self.languageComboBox.currentIndex() == 0 else "Los datos de The Shoulder Tool se exportaron correctamente a CSV.")

            except Exception as e:
                #QMessageBox.critical(self, "Export Error", f"An error occurred while exporting ST to CSV: {e}")
                QMessageBox.critical(self, "Export Error" if self.languageComboBox.currentIndex() == 0 else "Error de Exportación", f"An error occurred while exporting ST to CSV: {e}" if self.languageComboBox.currentIndex() == 0 else f"Ocurrió un error al exportar los datos de ST a CSV: {e}")

        
    
    # Method to show authors dialog
    def showAuthorsDialog(self):
        #self.authorsDialog = QDialog(self)
        #self.authorsDialog.setWindowTitle("Authors")

        # Layout for the dialog
        layout = QVBoxLayout()
    
        # Add a label with some text
        self.authorsLabel = QLabel("Ivan Nail, Ph.D.")
        layout.addWidget(self.authorsLabel)
    
        # Add a central logo if you have one
        logo_label = QLabel()
        logo_path = '../assets/ergologo01.png'
        pixmap = QPixmap(logo_path)  # Replace with your logo's path
        if pixmap.isNull():
            print("Failed to load the image:", logo_path)
            return
        
        #logo_label.setPixmap(pixmap)
        logo_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))  # Optional: Scale the image
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Set the layout and size
        self.authorsDialog.setLayout(layout)
        self.authorsDialog.setFixedSize(500, 400)  # Adjust size as needed
        self.authorsDialog.exec_()

    # Method to open help PDF
    def openHelpPDF(self): # Get the directory of the current script
        dir_path = os.path.dirname(os.path.realpath(__file__))
        help_pdf_path = os.path.join(dir_path, '../assets', 'ergohelp01.pdf')

        # Check if the file exists
        if not os.path.exists(help_pdf_path):
            #QMessageBox.critical(self, "File Not Found", f"Could not find the help file: {help_pdf_path}")
            QMessageBox.critical(self, "File Not Found" if self.languageComboBox.currentIndex() == 0 else "Archivo No Encontrado", f"Could not find the help file: {help_pdf_path}" if self.languageComboBox.currentIndex() == 0 else f"No se pudo encontrar el archivo de ayuda: {help_pdf_path}")
            return

        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', help_pdf_path], check=True)
        elif sys.platform == 'win32':  # Windows
            os.startfile(help_pdf_path)
        else:  # Linux variants
            subprocess.run(['xdg-open', help_pdf_path], check=True)
        
    def setupAnimationTimers(self):
        self.animationTimer = QTimer(self)  # Timer for smooth transitions
        self.animationTimer.timeout.connect(self.updateRotation)
        self.targetRotation = 0
        self.currentRotation = 0

    def setupStatusBar(self):
        # Create or retrieve the status bar
        statusBar = self.statusBar()
        
        # Display a default message
        statusBar.showMessage("Ready", 5000)  # Message displayed for 5 seconds


    def setupDatabase(self):
        # Connect to the SQLite database (it will be created if it doesn't exist)
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()
        
        # Create the table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lifft_results (
            userid TEXT NOT NULL,
            datetime TEXT NOT NULL,
            task_id INTEGER NOT NULL,
            lever_arm REAL,
            load REAL,
            moment REAL,
            repetitions INTEGER,
            cumulative_damage REAL,
            percentage_total REAL,
            total_cumulative_damage REAL,
            probability_high_risk REAL,
            unit TEXT,
            PRIMARY KEY (userid, datetime, task_id)
        )
        ''')
        
        # Create the duet_results table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS duet_results (
            userid TEXT NOT NULL,
            datetime TEXT NOT NULL,
            task_id INTEGER NOT NULL,
            omni_res_scale INTEGER,
            repetitions INTEGER,
            cumulative_damage REAL,
            percentage_total REAL,
            total_cumulative_damage REAL,
            probability_distal_upper_extremity_outcome REAL,
            unit TEXT,
            PRIMARY KEY (userid, datetime, task_id)
        )
        ''')
    
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tst_results (
            userid TEXT NOT NULL,
            datetime TEXT NOT NULL,
            task_id INTEGER NOT NULL,
            type_of_task INTEGER,  
            lever_arm REAL,
            load REAL,
            moment REAL,
            repetitions INTEGER,
            cumulative_damage REAL,
            percentage_total REAL,
            total_cumulative_damage REAL,
            probability_shoulder_outcome REAL,
            unit TEXT,
            PRIMARY KEY (userid, datetime, task_id)
        )
        ''')
    
    
        conn.commit()
        conn.close()

    
    def changeLanguage(self, index):
        lang = self.languageComboBox.itemData(index)
        if lang:
            if self.translator.load(lang):
                QtWidgets.QApplication.instance().installTranslator(self.translator)
        else:
            QtWidgets.QApplication.instance().removeTranslator(self.translator)
        #print(index)
        
        
        if index == 0: # english
            #print("english")
            self.file_menu.setTitle('&File')
            self.export_csv_action.setText('Export selected tool to &CSV format')
            self.exit_action.setText('&Exit')
            self.help_menu.setTitle('&Help')
            self.user_guide_action.setText('&User Guide')
            self.about_action.setText('&About')
 
            
            self.omnires_dropdowns = []
            task_types = ["0: Extremely Easy", "1:", "2: Easy", "3:", "4: Somewhat Easy", "5:", "6: Somewhat Hard", "7:", "8: Hard", "9:", "10: Extremely Hard"]
            for row in range(self.num_task):
                # Difficulty Rating dropdown
                omnires_dropdown = QComboBox()
                omnires_dropdown.addItems(task_types)
                self.duet_tab_layout.removeWidget(omnires_dropdown)
                self.duet_tab_layout.addWidget(omnires_dropdown, row + 1, 1)
                self.omnires_dropdowns.append(omnires_dropdown)
                
            
            self.tst_type_of_task_dropdowns = []
            task_types = ["Handling Loads", "Push or Pull Downward", "Horizontal Push or Pull"]
            for row in range(self.num_task):
                # Type of Task dropdown
                type_of_task_dropdown = QComboBox()
                type_of_task_dropdown.addItems(task_types)
                self.tst_tab_layout.removeWidget(type_of_task_dropdown)
                self.tst_tab_layout.addWidget(type_of_task_dropdown, row + 1, 1)
                self.tst_type_of_task_dropdowns.append(type_of_task_dropdown)
           
           
            self.unitComboBox.setItemText(0, "English")
            self.unitComboBox.setItemText(1, "Metric")
            #self.unitComboBox = []
            #self.unitComboBox.addItems(["English", "Metric"])
            #self.topLayout.removeWidget(self.unitComboBox)
            #self.topLayout.addWidget(self.unitComboBox)
            
            self.languageComboBox.setItemText(0, "English")
            self.languageComboBox.setItemText(1, "Spanish")
            #self.languageComboBox.currentIndexChanged.disconnect(changeLanguage)
            #self.translator = QtCore.QTranslator(self)
            #self.languageCombo = QtWidgets.QComboBox()
            #self.languageComboBox.clear = []
            #options = [('Ingles', ''), ('Español', 'eng-esp')]
            #for text, lang in options:
            #    self.languageComboBox.addItem(text, lang)
            #self.topLayout.remove(self.languageComboBox)
            #self.topLayout.addWidget(self.languageComboBox)
             
            # Define language options and their corresponding file identifiers
            #self.languageCombo.currentIndexChanged.connect(self.changeLanguage)
          
            #self.lifft_probability_label.setText = "Probability of High Risk\nJob * (%):"
            
        elif index == 1: # spanish
            #print("spanish")
            self.file_menu.setTitle('&Archivo')
            self.export_csv_action.setText('Exportar herramienta seleccionada a formato &CSV')
            self.exit_action.setText('&Salir')
            self.help_menu.setTitle('&Ayuda')
            self.user_guide_action.setText('&Guía de Usuario')
            self.about_action.setText('&Acerca de')
            
           
            self.omnires_dropdowns = []
            task_types = ["0: Extremadamente fácil", "1:", "2: Fácil", "3:", "4: Algo fácil", "5:", "6: Algo difícil", "7:", "8: Difícil", "9:", "10: Extremadamente difícil"]
            for row in range(self.num_task):
                # Difficulty Rating dropdown
                omnires_dropdown = QComboBox()
                omnires_dropdown.addItems(task_types)
                self.duet_tab_layout.removeWidget(omnires_dropdown)
                self.duet_tab_layout.addWidget(omnires_dropdown, row + 1, 1)
                self.omnires_dropdowns.append(omnires_dropdown)
            

            
            self.tst_type_of_task_dropdowns = []
            task_types = ["Manipulación de cargas", "Empujar o Tirar hacia abajo", "Empuje o Tirón Horizontal"] 
            for row in range(self.num_task):
                # Type of Task dropdown
                type_of_task_dropdown = QComboBox()
                type_of_task_dropdown.addItems(task_types)
                self.tst_tab_layout.removeWidget(type_of_task_dropdown)
                self.tst_tab_layout.addWidget(type_of_task_dropdown, row + 1, 1)
                self.tst_type_of_task_dropdowns.append(type_of_task_dropdown)
            
            
            self.unitComboBox.setItemText(0, "Ingles")
            self.unitComboBox.setItemText(1, "Métrico")
            #self.unitComboBox = []
            #self.unitComboBox.addItems(["Ingles", "Métrico"])
            #self.topLayout.removeWidget(self.unitComboBox)
            #self.topLayout.addWidget(self.unitComboBox)

            self.languageComboBox.setItemText(0, "Ingles")
            self.languageComboBox.setItemText(1, "Español")
            #self.languageComboBox.currentIndexChanged.disconnect(self.changeLanguage)
            #self.translator = QtCore.QTranslator(self)
            #self.languageCombo = QtWidgets.QComboBox()
            #self.languageComboBox = []
            #options = [('English', ''), ('Spanish', 'eng-esp')]
            #for text, lang in options:
                #self.languageComboBox.addItem(text, lang)
            #opLayout.remove(self.languageComboBox)
            #self.topLayout.addWidget(self.languageComboBox) 
            
            
            # Define language options and their corresponding file identifiers
            #self.languageCombo.currentIndexChanged.connect(self.changeLanguage)
            
            
            #self.lifft_probability_label.setText = "Probabilidad de Resultado de Extremidad\nSuperior Distal (%):"
            

        #print(index)
        #self.file_menu.setTitle(QtWidgets.QApplication.translate('App', '&File'))
        #self.export_csv_action.setText(QtWidgets.QApplication.translate('App', 'Export selected tool to &CSV format'))
        #self.exit_action.setText(QtWidgets.QApplication.translate('App', '&Exit'))
        #self.help_menu.setTitle(QtWidgets.QApplication.translate('App', '&Help'))
        #self.user_guide_action.setText(QtWidgets.QApplication.translate('App', '&User Guide'))
        #self.about_action.setText(QtWidgets.QApplication.translate('App', '&About'))
        
        if self.unitComboBox.currentIndex() == 0: #"English":
            if self.languageComboBox.currentIndex() == 0: #"English":
                self.lifft_headers_labels[1].setText("Lever Arm (inch)")  # Change to inch
                self.lifft_headers_labels[2].setText("Load (lb)")         # Change to lb
                self.lifft_headers_labels[3].setText("Moment (ft.lb)")    # Change to ft.lb
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
                self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

                self.tst_headers_labels[2].setText("Lever Arm (inch)")  # Change to inch
                self.tst_headers_labels[3].setText("Load (lb)")         # Change to lb
                self.tst_headers_labels[4].setText("Moment (ft.lb)")    # Change to ft.lb
            
            elif self.languageComboBox.currentIndex() == 1: #"Spanish"  :
                self.lifft_headers_labels[1].setText("Brazo de Palanca (pulgadas)")  # Change to inch
                self.lifft_headers_labels[2].setText("Carga (libras)")         # Change to lb
                self.lifft_headers_labels[3].setText("Momento (ft.lb)")    # Change to ft.lb
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
                self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

                self.tst_headers_labels[2].setText("Brazo de Palanca (pulgadas)")  # Change to inch
                self.tst_headers_labels[3].setText("Carga (libras)")         # Change to lb
                self.tst_headers_labels[4].setText("Momento (ft.lb)")    # Change to ft.lb
            
            self.unit = "english"
            
        elif self.unitComboBox.currentIndex() == 1: #"Metric":
            if self.languageComboBox.currentIndex() == 0: #"English":
                self.lifft_headers_labels[1].setText("Lever Arm (cm)")    # Change back to cm
                self.lifft_headers_labels[2].setText("Load (N)")          # Change back to N
                self.lifft_headers_labels[3].setText("Moment (N.m)")      # Change back to N.m
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "cm", "N", "N.m"
                self.lifft_color_english, self.lifft_color_metric = "color: #808080;" , "color: #337ab7; font-weight:bold;"
        
                self.tst_headers_labels[2].setText("Lever Arm (cm)")    # Change back to cm
                self.tst_headers_labels[3].setText("Load (N)")          # Change back to N
                self.tst_headers_labels[4].setText("Moment (N.m)")      # Change back to N.m
            
            elif self.languageComboBox.currentIndex() == 1: #"Spanish"  :
                self.lifft_headers_labels[1].setText("Brazo de Palanca (cm)")  # Change to inch
                self.lifft_headers_labels[2].setText("Carga (N)")         # Change to lb
                self.lifft_headers_labels[3].setText("Momento (N.m)")    # Change to ft.lb
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
                self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

                self.tst_headers_labels[2].setText("Brazo de Palanca (cm)")  # Change to inch
                self.tst_headers_labels[3].setText("Carga (N)")         # Change to lb
                self.tst_headers_labels[4].setText("Momento (N.m)")    # Change to ft.lb    
        
    
        self.retranslateUI()
        self.repaint() 



    def setupUI(self):
        # Main window central widget and vertical layout
        centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(centralWidget)
        mainLayout = QtWidgets.QVBoxLayout(centralWidget)

        # Setup top widgets first
        self.setupTopWidgets()
        mainLayout.addWidget(self.topContainer)  # Add the top layout container at the beginning
        
        # Horizontal layout for the content area
        contentLayout = QtWidgets.QHBoxLayout()
        
        # Left side layout for the 3D model and controls
        self.leftLayout = QtWidgets.QVBoxLayout()
        
        # VTK widget for 3D model visualization
        self.vtkWidget = QVTKRenderWindowInteractor()
        self.leftLayout.addWidget(self.vtkWidget)
        
        # Setup renderer for VTK widget
        self.setupRenderer()
        
        # Setup renderer for Pain Visualization Sphere widget
        #self.addPainVisualizationSphere()

        # Model control panel (zoom, rotation, movement)
        self.setupControlPanel()

        # Wrap left layout content in a container
        leftContainer = QtWidgets.QWidget()
        leftContainer.setLayout(self.leftLayout)
        contentLayout.addWidget(leftContainer)

        # Right side tab widget for tests input
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.currentChanged.connect(self.onTabChange)  # Connect the signal to your method

        self.setupTabWidgets()
        contentLayout.addWidget(self.tabWidget)

        # Adding the content layout to the main vertical layout
        mainLayout.addLayout(contentLayout)
        
        # Resize the window to ensure all tabs are visible
        #self.resize(1280, 800)  # Adjust the width (1200) and height (800) as necessary


    def setupTopWidgets(self):
        # Initialize the top container and layout
        self.topContainer = QtWidgets.QWidget()
        self.topLayout = QtWidgets.QHBoxLayout(self.topContainer)


        bold_font = QFont()
        bold_font.setBold(True)
       
        # User ID Label and Textbox
        self.userIDLabel = QtWidgets.QLabel("User ID:")
        self.userIDLabel.setFont(bold_font)
        self.userIDTextbox = QtWidgets.QLineEdit()

        # DateTime Control
        self.dateTimeControl = QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.dateTimeControl.setDisplayFormat("yyyy-MM-dd HH:mm")

        # Load Button
        self.loadButton = QtWidgets.QPushButton("Load")
        self.loadButton.clicked.connect(self.loadButtonClicked)

        # Save Button
        self.saveButton = QtWidgets.QPushButton("Save")
        self.saveButton.clicked.connect(self.saveButtonClicked)

        
        # Number of Tasks Label
        self.numTasksLabel = QLabel("N° of Tasks:")
        self.numTasksLabel.setFont(bold_font)  # Assuming you have a bold QFont object already defined as 'bold_font'

        # Number of Tasks SpinBox for integer entry 
        self.numTasksSpinBox = QSpinBox()
        self.numTasksSpinBox.setMinimum(1)  # Minimum value
        self.numTasksSpinBox.setMaximum(20)  # Maximum value
        self.numTasksSpinBox.setValue(10)  # Default value 
        self.numTasksSpinBox.setSingleStep(1)  # Step for increase or decrease

        # "Set Tasks" Button
        self.setTasksButton = QPushButton("Set Tasks")
        self.setTasksButton.clicked.connect(self.setTasksButtonClicked)  # Method to handle button click



        # Language Label and ComboBox
        self.languageLabel = QtWidgets.QLabel("Language:")
        self.languageLabel.setFont(bold_font)
        self.translator = QtCore.QTranslator(self)
        self.languageComboBox = QtWidgets.QComboBox()
        # Define language options and their corresponding file identifiers
        options = [('English', ''), ('Spanish', 'eng-esp')]
        for text, lang in options:
            self.languageComboBox.addItem(text, lang)
          
        self.languageComboBox.currentIndexChanged.connect(self.changeLanguage)
          
        # Unit Label and ComboBox
        self.unitLabel = QtWidgets.QLabel("Unit:")
        self.unitLabel.setFont(bold_font)
        self.unitComboBox = QtWidgets.QComboBox()
        self.unitComboBox.addItems(["English", "Metric"])
        self.unitComboBox.setCurrentIndex(1)  # Set "Metric" as default
        # Connect unitComboBox.currentIndexChanged signal to the appropriate slot
        self.unitComboBox.currentIndexChanged.connect(self.updateUnits)
        
        # Init unit..TODO: to be remove...
        self.unit = ""
        if self.unitComboBox.currentIndex() == 0: #"English":
            self.unit = "english"
            self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
            self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"
        elif self.unitComboBox.currentIndex() == 1: #"Metric":
            self.unit = "metric"
            self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "cm", "N", "N.m"
            self.lifft_color_english, self.lifft_color_metric = "color: #808080;" , "color: #337ab7; font-weight:bold;"

        
        # Add widgets to the top layout
        self.topLayout.addWidget(self.userIDLabel)
        self.topLayout.addWidget(self.userIDTextbox)
        self.topLayout.addWidget(self.dateTimeControl)
        self.topLayout.addWidget(self.loadButton)
        self.topLayout.addWidget(self.saveButton)
        self.topLayout.addWidget(self.numTasksLabel)
        self.topLayout.addWidget(self.numTasksSpinBox)
        self.topLayout.addWidget(self.setTasksButton)
        self.topLayout.addStretch()  # This pushes everything to the left
        
        self.topLayout.addWidget(self.languageLabel)
        self.topLayout.addWidget(self.languageComboBox)
        
        self.topLayout.addWidget(self.unitLabel)
        self.topLayout.addWidget(self.unitComboBox)
  


    def setTasksButtonClicked(self):
        # Implementation for what happens when the "Set Tasks" button is clicked
        self.num_task  = self.numTasksSpinBox.value()
        current_language_index = self.languageComboBox.currentIndex()
        #self.lifftResetForm()
        #self.duetResetForm()
        #self.tstResetForm()
        self.resetAllPatchs()
        self.tabWidget.removeTab(0)
        self.tabWidget.removeTab(0) # previous "0" reduce the total amount, so allways removing 0 so end up remoging the 3 of them 
        self.tabWidget.removeTab(0)
        
        
    
        self.setupTabWidgets()
        
        #self.languageComboBox.setCurrentIndex(current_language_index)
        self.changeLanguage(current_language_index)
        
        # Optionally, clear any warning messages
        self.statusBar().showMessage("")
        
        
        #self.repaint() 
    
    def resetAllPatchs(self):
        self.lowerBackActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftForeArmActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftHandActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightForeArmActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightHandActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftShoulderActor.VisibilityOff()
        self.leftShoulderActor.VisibilityOff()
        self.leftForeArmActor.VisibilityOff()
        self.leftHandActor.VisibilityOff()
        self.rightForeArmActor.VisibilityOff()
        self.rightHandActor.VisibilityOff()
        self.lowerBackActor.VisibilityOff()
        # Re-render the scene to update the view
        self.vtkWidget.GetRenderWindow().Render()
        
    def updateUnits(self, index):
        self.updateUnitsLabels()
        #self.lifftResetForm() # TODO: ..or convert data?,...or don't do anything..


    def updateUnitsLabels(self):
        # Check the current text of the lifft_unit_switcher to determine the unit system
        if self.unitComboBox.currentIndex() == 0: #"English":
            if self.languageComboBox.currentIndex() == 0: #"English":
                self.lifft_headers_labels[1].setText("Lever Arm (inch)")  # Change to inch
                self.lifft_headers_labels[2].setText("Load (lb)")         # Change to lb
                self.lifft_headers_labels[3].setText("Moment (ft.lb)")    # Change to ft.lb
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
                self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

                self.tst_headers_labels[2].setText("Lever Arm (inch)")  # Change to inch
                self.tst_headers_labels[3].setText("Load (lb)")         # Change to lb
                self.tst_headers_labels[4].setText("Moment (ft.lb)")    # Change to ft.lb
            
            elif self.languageComboBox.currentIndex() == 1: #"Spanish"  :
                self.lifft_headers_labels[1].setText("Brazo de Palanca (pulgadas)")  # Change to inch
                self.lifft_headers_labels[2].setText("Carga (libras)")         # Change to lb
                self.lifft_headers_labels[3].setText("Momento (ft.lb)")    # Change to ft.lb
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
                self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

                self.tst_headers_labels[2].setText("Brazo de Palanca (pulgadas)")  # Change to inch
                self.tst_headers_labels[3].setText("Carga (libras)")         # Change to lb
                self.tst_headers_labels[4].setText("Momento (ft.lb)")    # Change to ft.lb
            
            self.unit = "english"
            
        elif self.unitComboBox.currentIndex() == 1: #"Metric":
            if self.languageComboBox.currentIndex() == 0: #"English":
                self.lifft_headers_labels[1].setText("Lever Arm (cm)")    # Change back to cm
                self.lifft_headers_labels[2].setText("Load (N)")          # Change back to N
                self.lifft_headers_labels[3].setText("Moment (N.m)")      # Change back to N.m
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "cm", "N", "N.m"
                self.lifft_color_english, self.lifft_color_metric = "color: #808080;" , "color: #337ab7; font-weight:bold;"
        
                self.tst_headers_labels[2].setText("Lever Arm (cm)")    # Change back to cm
                self.tst_headers_labels[3].setText("Load (N)")          # Change back to N
                self.tst_headers_labels[4].setText("Moment (N.m)")      # Change back to N.m
            
            elif self.languageComboBox.currentIndex() == 1: #"Spanish"  :
                self.lifft_headers_labels[1].setText("Brazo de Palanca (cm)")  # Change to inch
                self.lifft_headers_labels[2].setText("Carga (N)")         # Change to lb
                self.lifft_headers_labels[3].setText("Momento (N.m)")    # Change to ft.lb
                self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
                self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

                self.tst_headers_labels[2].setText("Brazo de Palanca (cm)")  # Change to inch
                self.tst_headers_labels[3].setText("Carga (N)")         # Change to lb
                self.tst_headers_labels[4].setText("Momento (N.m)")    # Change to ft.lb    
            self.unit = "metric"
            
    def lifftResetForm(self):
        
        for row in range(len(self.lifft_damage)):
            self.lifft_output_labels_matrix[row][5].setStyleSheet("background-color: none;")
                
        self.lifft_total_damage_value_label.setStyleSheet("background-color: none;")
        self.lifft_probability_value_label.setStyleSheet("background-color: none;")
        

        # Clear all input fields and reset output labels to "0.0"
    
        # Clear input fields
        for input_field in self.lifft_lever_arm_inputs + self.lifft_load_inputs + self.lifft_repetitions_inputs:
            input_field.setText('')
    
        #print("Here3?\n")
        
        # Reset output labels to "0.0"
        for row in range(0, self.num_task):  # Assuming tasks rows are from 1 to 10
            for col in [3, 5, 6]:  # Columns for "Moment (N.m)", "Damage (cumulative)", and "% Total (damage)"
                if self.lifft_output_labels_matrix[row][col] is not None:
                    self.lifft_output_labels_matrix[row][col].setText("0.0")
        
        
        #print("Here4?\n")
        
        self.lifft_total_damage_value_label.setText("0.0")
        self.lifft_probability_value_label.setText("0.0")
        
        self.lowerBackActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.lowerBackActor.VisibilityOff()
        # Re-render the scene to update the view
        self.vtkWidget.GetRenderWindow().Render()

        # Optionally, clear any warning messages
        self.statusBar().showMessage("")
    
    
    
    def lifftCalculateResults(self):
        
        # Step 0: Validate inputs
        
        # Reset warning label at the beginning of the calculation
        self.statusBar().showMessage("")
    
        # Combine all input arrays for easier iteration
        all_inputs = self.lifft_lever_arm_inputs + self.lifft_load_inputs + self.lifft_repetitions_inputs
    
        # Check if any input is empty
        if any(input_field.text().strip() == '' for input_field in all_inputs):
            #self.statusBar().showMessage("Warning: Incomplete Input")
            self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")

            #return  # Exit the function early if any input is incomplete
        
        
        # Step 1: Call calcs...
        #-----------------------------------------------------------------------------------
        for i in range(self.num_task):
            self.lifft_moment[i] = 0.0
            self.lifft_damage[i][0] = 0.0
            self.lifft_damage[i][1] = 'none'   # firs item is the value, second is the color
            self.lifft_percent[i] = 0.0

        self.lifft_total_damage = 0
        self.lifft_total_risk = 0
        self.lifft_total_risk_color = 'none'
        
        
        for row in range(self.num_task):
            #d = data['form-' + str(i) + '-distance']
            #l = data['form-'+str(i)+'-load']
            #r = data['form-'+str(i)+'-rep']
            
            try:
                d = float(self.lifft_lever_arm_inputs[row].text())
            except ValueError:
                d = ''

            try:
                l = float(self.lifft_load_inputs[row].text())
            except ValueError:
                l = ''
             
            try:
                r = float(self.lifft_repetitions_inputs[row].text())
            except ValueError:
                r = ''
                 
            if d != '' and l != '' and r != '':
                lifft = LiFFT(self.unit, float(d), float(l), float(r))
                self.lifft_moment[row], self.lifft_damage[row][0], self.lifft_damage[row][1] = lifft.calculate()
                self.lifft_total_damage += self.lifft_damage[row][0]
            elif l != '' and d != '':
                model = LiFFT(self.unit, float(d), float(l), rep=0)
                self.lifft_moment[row], self.lifft_damage[row][0], self.lifft_damage[row][1] = model.calculate()
                #self.statusBar().showMessage("Warning: Incomplete Input") 
                self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")

            
            self.lifft_output_labels_matrix[row][3].setText(f"{float(self.lifft_moment[row]):.1f}")    
            self.lifft_output_labels_matrix[row][5].setText(f"{float(self.lifft_damage[row][0]):.4f}")
            
            
            
                   
        #total_damage = sum(damage)
        if self.lifft_total_damage != 0:
            #print("len lifft=" + str(len(self.lifft_damage)) + "\n")
            for j in range(len(self.lifft_damage)):
                self.lifft_percent[j] = round(self.lifft_damage[j][0] / self.lifft_total_damage * 100, 1)
                if self.lifft_percent[j] == 0:
                    self.lifft_damage[j][1] = 'none'
                    
                lifft_color_code = self.lifft_damage[j][1]  # Retrieve the color code from the matrix
                # Set the background color of the QLabel in the desired column, e.g., column 5
                self.lifft_output_labels_matrix[j][5].setStyleSheet(f"background-color: {lifft_color_code};")
                self.lifft_output_labels_matrix[j][6].setText(str(self.lifft_percent[j]))
                

            self.lifft_total_risk = round(lifft.riskFromDamage(self.lifft_total_damage) * 100, 1)
            if self.lifft_total_risk < 5:
                self.lifft_total_risk = "< 5"
            elif self.lifft_total_risk > 90:
                self.lifft_total_risk = "> 90"

            self.lifft_total_risk_color = lifft.colorFromDamageRisk(self.lifft_total_damage)

            self.lifft_total_damage_value_label.setText(f"{float(self.lifft_total_damage):.4f}")
            
            try:
                # Try to convert to float and format
                formatted_value = f"{float(self.lifft_total_risk):.1f}"
            except ValueError:
                # If conversion fails, use the string directly
               formatted_value = self.lifft_total_risk

            self.lifft_probability_value_label.setText(formatted_value)
            #self.lifft_probability_value_label.setText(f"{float(self.lifft_total_risk):.1f}")
            
            self.lifft_total_damage_value_label.setStyleSheet(f"background-color: {self.lifft_total_risk_color};")
            self.lifft_probability_value_label.setStyleSheet(f"background-color: {self.lifft_total_risk_color};")
            
            # Check if the color is valid and not 'none' or 'None'
            if self.lifft_total_risk_color and self.lifft_total_risk_color.lower() != 'none' and self.lifft_total_risk_color.lower() != 'None':
                # Assuming self.lifft_total_risk_color is a string like '#RRGGBB'
                # Convert hexadecimal color to a tuple of RGB values (0 to 1 range)
                color = self.hexColorToRGB(self.lifft_total_risk_color)
        
                # Set the color to the lower back actor
                self.lowerBackActor.GetProperty().SetColor(color)
        
                # Make the actor visible
                self.lowerBackActor.VisibilityOn()
        
                # Re-render the scene to update the view
                self.vtkWidget.GetRenderWindow().Render()
            else:
                # If the color is not valid, make the actor invisible or handle as needed
                self.lowerBackActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                self.lowerBackActor.VisibilityOff()
                self.vtkWidget.GetRenderWindow().Render()
        
        
        else:
            for j in range(len(self.lifft_damage)):
                self.lifft_damage[j][1] = 'none'

            self.lifft_total_risk = 0
            self.lifft_total_risk_color = 'none' 
            
            self.lifft_total_damage_value_label.setText("0.0")   
            self.lifft_probability_value_label.setText("0.0")    
        #--------------------------------------------------------------------------------    
        
        
    def hexColorToRGB(self, hexColor):
        """Convert a hexadecimal color string to a tuple of RGB values."""
        hexColor = hexColor.lstrip('#')
        lv = len(hexColor)
        return tuple(int(hexColor[i:i + lv // 3], 16) / 255.0 for i in range(0, lv, lv // 3))
    
    
    
    # Reset form method
    def duetResetForm(self):
        for row in range(len(self.duet_damage)):
            self.duet_output_labels_matrix[row][3].setStyleSheet("background-color: none;")
                
        self.duet_total_damage_value_label.setStyleSheet("background-color: none;")
        self.duet_probability_value_label.setStyleSheet("background-color: none;")
               


        # Clear all input fields and reset output labels to "0.0"
    
        # Clear input fields
        for input_field in self.duet_repetitions_inputs:
            input_field.setText('')
    
        # Reset output labels to "0.0"
        for row in range(0, self.num_task):  # Assuming tasks rows are from 1 to 10
            for col in [3, 4]:  # Columns for "Moment (N.m)", "Damage (cumulative)", and "% Total (damage)"
                if self.duet_output_labels_matrix[row][col] is not None:
                    self.duet_output_labels_matrix[row][col].setText("0.0")
        
        for combobox in self.omnires_dropdowns:
            combobox.setCurrentIndex(0)
        
        self.duet_total_damage_value_label.setText("0.0")
        self.duet_probability_value_label.setText("0.0")
        
        self.leftForeArmActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftHandActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightForeArmActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightHandActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftForeArmActor.VisibilityOff()
        self.leftHandActor.VisibilityOff()
        self.rightForeArmActor.VisibilityOff()
        self.rightHandActor.VisibilityOff()
        
        # Re-render the scene to update the view
        self.vtkWidget.GetRenderWindow().Render()

        # Optionally, clear any warning messages
        self.statusBar().showMessage("")
        

    # Calculate results method
    def duetCalculateResults(self):
        # Step 0: Validate inputs
        
        # Reset warning label at the beginning of the calculation
        self.statusBar().showMessage("")
    
        # Combine all input arrays for easier iteration
        all_inputs = self.duet_repetitions_inputs
    
        # Check if any input is empty
        if any(input_field.text().strip() == '' for input_field in all_inputs):
            #self.statusBar().showMessage("Warning: Incomplete Input")
            self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")

            #return  # Exit the function early if any input is incomplete
        
        
        # Step 1: Call calcs...
        #-----------------------------------------------------------------------------------
        
        for i in range(self.num_task):
            #self.duet_moment[i] = 0.0
            self.duet_damage[i][0] = 0.0
            self.duet_damage[i][1] = 'none'   # firs item is the value, second is the color
            self.duet_percent[i] = 0.0

        self.duet_total_damage = 0
        self.duet_total_risk = 0
        self.duet_total_risk_color = 'none'
        
        
        for row in range(self.num_task):
            #d = data['form-' + str(i) + '-distance']
            #l = data['form-'+str(i)+'-load']
            #r = data['form-'+str(i)+'-rep']
            
            try:
                scale = self.omnires_dropdowns[row].currentIndex()
                #print("scale:"+str(scale)+"\n")
            except ValueError:
                scale = ''

            try:
                rep = float(self.duet_repetitions_inputs[row].text())
                #print("rep:"+str(rep)+"\n")
            except ValueError:
                rep = ''
            
            
            if rep != '':
                duet = DUET(float(scale), float(rep))
                self.duet_damage[row][0], self.duet_damage[row][1] = duet.calculate()

                self.duet_total_damage += self.duet_damage[row][0]
            else:
                #self.statusBar().showMessage("Warning: Incomplete Input")
                self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
 
                        
            self.duet_output_labels_matrix[row][3].setText(f"{float(self.duet_damage[row][0]):.5f}")
            
            
            
                   
        #total_damage = sum(damage)
        if self.duet_total_damage != 0:
            #print("len duet_damage=" + str(len(self.duet_damage)) + "\n")
            for j in range(len(self.duet_damage)):
                self.duet_percent[j] = round(self.duet_damage[j][0] / self.duet_total_damage * 100, 1)
                if self.duet_percent[j] == 0:
                    self.duet_damage[j][1] = 'none'
                    
                    
                duet_color_code = self.duet_damage[j][1]  # Retrieve the color code from the matrix
                # Set the background color of the QLabel in the desired column, e.g., column 5
                self.duet_output_labels_matrix[j][3].setStyleSheet(f"background-color: {duet_color_code};")
                self.duet_output_labels_matrix[j][4].setText(str(self.duet_percent[j]))
                

            self.duet_total_risk = round(duet.riskFromDamage(self.duet_total_damage) * 100, 1)
            if self.duet_total_risk < 5:
                self.duet_total_risk = "< 5"
            elif self.duet_total_risk > 90:
                self.duet_total_risk = "> 90"

            self.duet_total_risk_color = duet.colorFromDamageRisk(self.duet_total_damage)

            self.duet_total_damage_value_label.setText(f"{float(self.duet_total_damage):.4f}")
            
            try:
                # Try to convert to float and format
                formatted_value = f"{float(self.duet_total_risk):.1f}"
            except ValueError:
                # If conversion fails, use the string directly
               formatted_value = self.duet_total_risk

            self.duet_probability_value_label.setText(formatted_value)
            
            self.duet_total_damage_value_label.setStyleSheet(f"background-color: {self.duet_total_risk_color};")
            self.duet_probability_value_label.setStyleSheet(f"background-color: {self.duet_total_risk_color};")
            
            
            
            # Check if the color is valid and not 'none' or 'None'
            if self.duet_total_risk_color and self.duet_total_risk_color.lower() != 'none' and self.duet_total_risk_color.lower() != 'None':
                # Assuming self.duet_total_risk_color is a string like '#RRGGBB'
                # Convert hexadecimal color to a tuple of RGB values (0 to 1 range)
                color = self.hexColorToRGB(self.duet_total_risk_color)
        
                # Set the color to the lower back actor
                self.leftForeArmActor.GetProperty().SetColor(color)
                self.leftHandActor.GetProperty().SetColor(color)
                self.rightForeArmActor.GetProperty().SetColor(color)
                self.rightHandActor.GetProperty().SetColor(color)
        
                
                
                # Make the actor visible
                self.leftForeArmActor.VisibilityOn()
                self.leftHandActor.VisibilityOn()
                self.rightForeArmActor.VisibilityOn()
                self.rightHandActor.VisibilityOn()
        
                # Re-render the scene to update the view
                self.vtkWidget.GetRenderWindow().Render()
            else:
                # If the color is not valid, make the actor invisible or handle as needed
                self.leftForeArmActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                self.leftHandActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                self.rightForeArmActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                self.rightHandActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                
                self.leftForeArmActor.VisibilityOff()
                self.leftHandActor.VisibilityOff()
                self.rightForeArmActor.VisibilityOff()
                self.rightHandActor.VisibilityOff()
                
                self.vtkWidget.GetRenderWindow().Render()
        
        
        else:
            for j in range(len(self.duet_damage)):
                self.duet_damage[j][1] = 'none'

            self.duet_total_risk = 0
            self.duet_total_risk_color = 'none' 
            
            self.duet_total_damage_value_label.setText("0.0")   
            self.duet_probability_value_label.setText("0.0")    
       
       #--------------------------------------------------------------------------------
    
    
    def tstResetForm(self):
        for row in range(len(self.tst_damage)):
            self.tst_output_labels_matrix[row][6].setStyleSheet("background-color: none;")
                
        self.tst_total_damage_value_label.setStyleSheet("background-color: none;")
        self.tst_probability_value_label.setStyleSheet("background-color: none;")
               


        # Clear all input fields and reset output labels to "0.0"
    
        # Clear input fields
        for input_field in self.tst_lever_arm_inputs + self.tst_load_inputs + self.tst_repetitions_inputs:
            input_field.setText('')
    
    
        # Reset output labels to "0.0"
        for row in range(0, self.num_task):  # Assuming tasks rows are from 1 to 10
            for col in [4, 6, 7]:  # Columns for "Moment (N.m)", "Damage (cumulative)", and "% Total (damage)"
                if self.tst_output_labels_matrix[row][col] is not None:
                    self.tst_output_labels_matrix[row][col].setText("0.0")
        
        for combobox in self.tst_type_of_task_dropdowns:
            combobox.setCurrentIndex(0)
        
        self.tst_total_damage_value_label.setText("0.0")
        self.tst_probability_value_label.setText("0.0")
        
        self.leftShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftShoulderActor.VisibilityOff()
        self.leftShoulderActor.VisibilityOff()
        
        # Re-render the scene to update the view
        self.vtkWidget.GetRenderWindow().Render()

        # Optionally, clear any warning messages
        self.statusBar().showMessage("")
        
    
    
    def tstCalculateResults(self):
        # Step 0: Validate inputs
        
        # Reset warning label at the beginning of the calculation
        self.statusBar().showMessage("")
    
        # Combine all input arrays for easier iteration
        all_inputs = self.tst_lever_arm_inputs + self.tst_load_inputs + self.tst_repetitions_inputs
    
        # Check if any input is empty
        if any(input_field.text().strip() == '' for input_field in all_inputs):
            #self.statusBar().showMessage("Warning: Incomplete Input")
            self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")

            #return  # Exit the function early if any input is incomplete
        
        
        # Step 1: Call calcs...
        #-----------------------------------------------------------------------------------
        for i in range(self.num_task):
            self.tst_moment[i] = 0.0
            self.tst_damage[i][0] = 0.0
            self.tst_damage[i][1] = 'none'   # firs item is the value, second is the color
            self.tst_percent[i] = 0.0

        self.tst_total_damage = 0
        self.tst_total_risk = 0
        self.tst_total_risk_color = 'none'
        
        
        for row in range(self.num_task):
            #d = data['form-' + str(i) + '-distance']
            #l = data['form-'+str(i)+'-load']
            #r = data['form-'+str(i)+'-rep']
            
            #TODO: Check this...
            try:
                dire = self.tst_type_of_task_dropdowns[row].currentIndex()
                if (dire==2):
                	dire = 1
                elif (dire==1):
                	dire = 2
            except ValueError:
                dire = ''
                
            #print("Dire="+str(dire))
            
            
            try:
                d = float(self.tst_lever_arm_inputs[row].text())
            except ValueError:
                d = ''

            try:
                l = float(self.tst_load_inputs[row].text())
            except ValueError:
                l = ''
             
            try:
                r = float(self.tst_repetitions_inputs[row].text())
            except ValueError:
                r = ''
            
            
            
            if d != '' and l != '' and r != '':
                tst = TST(self.unit, str(dire), d, l, r)
                self.tst_moment[row], self.tst_damage[row][0], self.tst_damage[row][1] = tst.calculate()
                self.tst_total_damage += self.tst_damage[row][0]
            elif l != '' and d != '':
                model = TST(self.unit, str(dire), d, l, rep=0)
                self.tst_moment[row], self.tst_damage[row][0], self.tst_damage[row][1] = model.calculate()
                #self.statusBar().showMessage("Warning: Incomplete Input")
                self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
 
            
            self.tst_output_labels_matrix[row][4].setText(f"{float(self.tst_moment[row]):.1f}")    
            self.tst_output_labels_matrix[row][6].setText(f"{float(self.tst_damage[row][0]):.5f}")
            
            
            
                   
        #total_damage = sum(damage)
        if self.tst_total_damage != 0:
            #print("len tst=" + str(len(self.tst_damage)) + "\n")
            for j in range(len(self.tst_damage)):
                self.tst_percent[j] = round(self.tst_damage[j][0] / self.tst_total_damage * 100, 1)
                if self.tst_percent[j] == 0:
                    self.tst_damage[j][1] = 'none'
                    
                tst_color_code = self.tst_damage[j][1]  # Retrieve the color code from the matrix
                # Set the background color of the QLabel in the desired column, e.g., column 5
                self.tst_output_labels_matrix[j][6].setStyleSheet(f"background-color: {tst_color_code};")
                self.tst_output_labels_matrix[j][7].setText(str(self.tst_percent[j]))
                

            self.tst_total_risk = round(tst.riskFromDamage(self.tst_total_damage) * 100, 1)
            if self.tst_total_risk < 5:
                self.tst_total_risk = "< 5"
            elif self.tst_total_risk > 90:
                self.tst_total_risk = "> 90"

            self.tst_total_risk_color = tst.colorFromDamageRisk(self.tst_total_damage)

            self.tst_total_damage_value_label.setText(f"{float(self.tst_total_damage):.4f}")
            
            try:
                # Try to convert to float and format
                formatted_value = f"{float(self.tst_total_risk):.1f}"
            except ValueError:
                # If conversion fails, use the string directly
               formatted_value = self.tst_total_risk

            self.tst_probability_value_label.setText(formatted_value)
            #self.tst_probability_value_label.setText(f"{float(self.tst_total_risk):.1f}")
            
            self.tst_total_damage_value_label.setStyleSheet(f"background-color: {self.tst_total_risk_color};")
            self.tst_probability_value_label.setStyleSheet(f"background-color: {self.tst_total_risk_color};")
            
            # Check if the color is valid and not 'none' or 'None'
            if self.tst_total_risk_color and self.tst_total_risk_color.lower() != 'none' and self.tst_total_risk_color.lower() != 'None':
                # Assuming self.tst_total_risk_color is a string like '#RRGGBB'
                # Convert hexadecimal color to a tuple of RGB values (0 to 1 range)
                color = self.hexColorToRGB(self.tst_total_risk_color)
        
                # Set the color to the lower back actor
                self.leftShoulderActor.GetProperty().SetColor(color)
                self.rightShoulderActor.GetProperty().SetColor(color)
        
                # Make the actor visible
                self.leftShoulderActor.VisibilityOn()
                self.rightShoulderActor.VisibilityOn()
        
                # Re-render the scene to update the view
                self.vtkWidget.GetRenderWindow().Render()
            else:
                # If the color is not valid, make the actor invisible or handle as needed
                self.leftShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                self.rightShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
                self.leftShoulderActor.VisibilityOff()
                self.rightShoulderActor.VisibilityOff()
                self.vtkWidget.GetRenderWindow().Render()
        
        
        else:
            for j in range(len(self.tst_damage)):
                self.tst_damage[j][1] = 'none'

            self.tst_total_risk = 0
            self.tst_total_risk_color = 'none' 
            
            self.tst_total_damage_value_label.setText("0.0")   
            self.tst_probability_value_label.setText("0.0")    
        #------------------------------------------------------------------------------------
        
        
        
        
        
    def saveButtonClicked(self):
        #self.disableButtonsAndShowStatus("Busy with database operations...")
        self.disableButtonsAndShowStatus("Busy with database operations..." if self.languageComboBox.currentIndex() == 0 else "Ocupado con operaciones de base de datos...")

        try:
            self.saveData()
        finally:
            self.enableButtonsAndClearStatus()

    def loadButtonClicked(self):
        #self.disableButtonsAndShowStatus("Busy with database operations...")
        self.disableButtonsAndShowStatus("Busy with database operations..." if self.languageComboBox.currentIndex() == 0 else "Ocupado con operaciones de base de datos...")

        try:
            self.loadData()
        finally:
            self.enableButtonsAndClearStatus()

        

    def disableButtonsAndShowStatus(self, message):
        # Assuming saveButton and loadButton are the QPushButton instances
        self.saveButton.setDisabled(True)
        self.loadButton.setDisabled(True)
        self.statusBar().showMessage(message)

    def enableButtonsAndClearStatus(self):
        self.saveButton.setEnabled(True)
        self.loadButton.setEnabled(True)
        self.statusBar().clearMessage()

    
    def validateInput(self):
        # Example validation for UserID and DateTime; adjust according to your UI elements
        userid = self.userIDTextbox.text().strip()
        datetime = self.dateTimeControl.dateTime().toString("yyyy-MM-dd HH:mm")
        if not userid or not datetime:
            return False
        return True
    
    def checkForExistingLiFFTData(self, userid, datetime):
        # Assuming userid and datetime are the inputs to this method
        query = '''SELECT COUNT(*) FROM lifft_results WHERE userid=? AND datetime=?'''
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()
        cursor.execute(query, (userid, datetime))
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0

    
            
    def loadData(self):
        
        if not self.validateInput():
            #QMessageBox.warning(self, "Validation Error", "Please ensure all required fields are filled correctly.")
            QMessageBox.warning(self, "Validation Error" if self.languageComboBox.currentIndex() == 0 else "Error de Validación", 
                    "Please ensure all required fields are filled correctly." if self.languageComboBox.currentIndex() == 0 else "Por favor, asegúrese de que todos los campos requeridos estén correctamente completados.")

            #QMessageBox.information, QMessageBox.warning, QMessageBox.critial
            return
            
            
        userid = self.userIDTextbox.text().strip()
        datetime = self.dateTimeControl.dateTime().toString("yyyy-MM-dd HH:mm")

        
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)

        # Connect to the database
        try:
            conn = sqlite3.connect(self.databasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            #print(f"An error occurred: {e}")
            #QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            QMessageBox.critical(self, "Database Error" if self.languageComboBox.currentIndex() == 0 else "Error de Base de Datos", 
                     f"An error occurred: {e}" if self.languageComboBox.currentIndex() == 0 else f"Se produjo un error: {e}")

            return


        if currentTabIndex == 0: # LiFFT
    
            
            # Query to fetch data for the given userid and datetime
            query = '''SELECT task_id, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total, 
                       total_cumulative_damage, probability_high_risk, unit
                       FROM lifft_results WHERE userid=? AND datetime=? ORDER BY task_id'''
            cursor.execute(query, (userid, datetime))

            # Fetch all matching records
            tasks = cursor.fetchall()

            if not tasks:
                # No tasks found; possibly show a message or handle accordingly
                #QMessageBox.information(self, "No Data Found", "No records found on the LiFFT tool for the given User ID and Date+Time.")
                QMessageBox.information(self, "No Data Found" if self.languageComboBox.currentIndex() == 0 else "No Se Encontraron Datos", "No records found on the LiFFT tool for the given User ID and Date+Time." if self.languageComboBox.currentIndex() == 0 else "No se encontraron registros en la herramienta LiFFT para el ID de usuario y Fecha+Hora dados.")

                self.lifftResetForm()
                return
            
            # Clear any previous data in the LiFFT form
            #self.lifftResetForm()
            
            
            
            self.tabWidget.removeTab(0)
            self.num_task = len(tasks)
            #self.numTasksSpinBox.setValue(self.num_task)
            self.setupLiFFTTab()
            self.tabWidget.removeTab(1)
            self.setupDUETTab()
            self.tabWidget.removeTab(2)
            self.setupTSTTab()
            self.tabWidget.setCurrentIndex(0)
            
            
            self.total_cumulative_damage, self.probability_high_risk, self.loadunit = '', '', ''
            # Assuming the widgets in the LiFFT tab are indexed from 0 to num_task-1
            for task in tasks:
                task_id, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total, self.total_cumulative_damage, self.probability_high_risk, self.loadunit = task
                
                index = task_id - 1  # Adjusting task_id to match list indexing

                # Populate the input fields
                self.lifft_lever_arm_inputs[index].setText(str(lever_arm))
                self.lifft_load_inputs[index].setText(str(load))
                self.lifft_repetitions_inputs[index].setText(str(repetitions))

                # Populate the output labels
                self.lifft_output_labels_matrix[index][3].setText(str(moment))  # Example for moment
                self.lifft_output_labels_matrix[index][5].setText(str(cumulative_damage))  # For cumulative damage
                self.lifft_output_labels_matrix[index][6].setText(str(percentage_total))  # For percentage of total damage


           
            self.lifft_total_damage_value_label.setText(f"{float(self.total_cumulative_damage):.4f}")
            
            try:
                # Try to convert to float and format
                formatted_value = f"{float(self.probability_high_risk):.1f}"
            except ValueError:
                # If conversion fails, use the string directly
               formatted_value = self.probability_high_risk

            self.lifft_probability_value_label.setText(formatted_value)
            
            self.unit = self.loadunit
            # Block signals to prevent the currentIndexChanged signal from being emitted
            self.unitComboBox.blockSignals(True)
            if self.unit:
                textToSet = self.unit
            else:
                if self.languageComboBox.currentIndex() == 0: # english
                    textToSet = "Metric"  
                elif self.languageComboBox.currentIndex() == 1: # spanish
                    textToSet = "Métrico" 
                        
            index = self.unitComboBox.findText(textToSet, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.unitComboBox.setCurrentIndex(index)

            # Unblock signals after setting the text
            self.unitComboBox.blockSignals(False)
            self.updateUnitsLabels()




            # Calculate results even if in db to set proper colors...
            self.lifftCalculateResults()
            #QMessageBox.information(self, "Data Found", "Records found and loaded into the LiFFT tool.")
            QMessageBox.information(self, "Data Found" if self.languageComboBox.currentIndex() == 0 else "Datos Encontrados", "Records found and loaded into the LiFFT tool." if self.languageComboBox.currentIndex() == 0 else "Registros encontrados y cargados en la herramienta LiFFT.")


        
        elif currentTabIndex == 1: # DUET
            # Query to fetch data for the given userid and datetime
            query_duet = '''SELECT task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total,
                   total_cumulative_damage, probability_distal_upper_extremity_outcome, unit
                   FROM duet_results WHERE userid=? AND datetime=? ORDER BY task_id'''
            cursor.execute(query_duet, (userid, datetime))

            # Fetch all matching records
            tasks_duet = cursor.fetchall()

            if not tasks_duet:
                # No tasks found; possibly show a message or handle accordingly
                #QMessageBox.information(self, "No Data Found", "No records found on the DUET tool for the given User ID and Date+Time.")
                QMessageBox.information(self, "No Data Found" if self.languageComboBox.currentIndex() == 0 else "No se encontraron datos", "No records found on the DUET tool for the given User ID and Date+Time." if self.languageComboBox.currentIndex() == 0 else "No se encontraron registros en la herramienta DUET para el ID de usuario y Fecha/Hora dados.")

                self.duetResetForm()
                return

            # Clear any previous data in the DUET form
            #self.duetResetForm()
            
            self.tabWidget.removeTab(1)
            self.num_task = len(tasks_duet)
            #self.numTasksSpinBox.setValue(self.num_task)
            self.setupDUETTab()
            self.tabWidget.removeTab(0)
            self.setupLiFFTTab()
            self.tabWidget.removeTab(2)
            self.setupTSTTab()
            self.tabWidget.setCurrentIndex(1)

            self.total_cumulative_damage_duet, self.probability_distal_upper_extremity_outcome, self.unit_duet = '', '', ''
            # Assuming the widgets in the DUET tab are indexed from 0 to num_task-1
            for task in tasks_duet:
                task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total, self.total_cumulative_damage_duet, self.probability_distal_upper_extremity_outcome, self.unit_duet = task

                index = task_id - 1  # Adjusting task_id to match list indexing

                # Populate the combo box and input fields
                self.omnires_dropdowns[index].setCurrentIndex(omni_res_scale)
                self.duet_repetitions_inputs[index].setText(str(repetitions))

                # Populate the output labels
                self.duet_output_labels_matrix[index][3].setText(str(cumulative_damage))  # For cumulative damage
                self.duet_output_labels_matrix[index][4].setText(str(percentage_total))  # For percentage of total damage

            self.duet_total_damage_value_label.setText(f"{float(self.total_cumulative_damage_duet):.4f}")

            try:
                # Try to convert to float and format
                formatted_value = f"{float(self.probability_distal_upper_extremity_outcome):.1f}"
            except ValueError:
                # If conversion fails, use the string directly
                formatted_value = self.probability_distal_upper_extremity_outcome

            self.duet_probability_value_label.setText(formatted_value)
    
            # Optional: Trigger any DUET-specific calculations or UI updates
            self.duetCalculateResults()
            #QMessageBox.information(self, "Data Found", "Records found and loaded into the DUET tool.")
            QMessageBox.information(self, "Data Found" if self.languageComboBox.currentIndex() == 0 else "Datos Encontrados", "Records found and loaded into the DUET tool." if self.languageComboBox.currentIndex() == 0 else "Registros encontrados y cargados en la herramienta DUET.")

       
       
        elif currentTabIndex == 2: # ST
            # Query to fetch data for the given userid and datetime specific to the ST tool
            query_st = '''SELECT task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total, 
                  total_cumulative_damage, probability_shoulder_outcome, unit
                  FROM tst_results WHERE userid=? AND datetime=? ORDER BY task_id'''
            cursor.execute(query_st, (userid, datetime))

            # Fetch all matching records
            tasks_st = cursor.fetchall()

            if not tasks_st:
                # No tasks found; possibly show a message or handle accordingly
                #QMessageBox.information(self, "No Data Found", "No records found on The Shouler Tool for the given User ID and Date+Time.")
                QMessageBox.information(self, "No Data Found" if self.languageComboBox.currentIndex() == 0 else "No Se Encontraron Datos", "No records found on The Shoulder Tool for the given User ID and Date+Time." if self.languageComboBox.currentIndex() == 0 else "No se encontraron registros en la herramienta The Shoulder Tool para el ID de usuario y la fecha/hora dados.")

                self.tstResetForm()
                return

            # Clear any previous data in the ST form
            #self.tstResetForm()

            self.tabWidget.removeTab(2)
            self.num_task = len(tasks_st)
            #self.numTasksSpinBox.setValue(self.num_task)
            self.setupTSTTab()
            self.tabWidget.removeTab(0)
            self.setupLiFFTTab()
            self.tabWidget.removeTab(1)
            self.setupDUETTab()
            self.tabWidget.setCurrentIndex(2)
            
            
            self.total_cumulative_damage_st, self.probability_shoulder_outcome, self.unit_st = '', '', ''
            # Assuming the widgets in the ST tab are indexed from 0 to num_task-1
            for task in tasks_st:
                task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total,   self.total_cumulative_damage_st, self.probability_shoulder_outcome, self.unit_st = task
            
                index = task_id - 1  # Adjusting task_id to match list indexing
            
                # Populate the Type of Task dropdown, Lever Arm, Load, and Repetitions input fields
                self.tst_type_of_task_dropdowns[index].setCurrentIndex(type_of_task)
                self.tst_lever_arm_inputs[index].setText(str(lever_arm))
                self.tst_load_inputs[index].setText(str(load))
                self.tst_repetitions_inputs[index].setText(str(repetitions))
            
                # Populate the output labels for Moment, Cumulative Damage, and Percentage of Total Damage
                self.tst_output_labels_matrix[index][4].setText(str(moment))
                self.tst_output_labels_matrix[index][6].setText(str(cumulative_damage))
                self.tst_output_labels_matrix[index][7].setText(str(percentage_total))
            
            self.tst_total_damage_value_label.setText(f"{float(self.total_cumulative_damage_st):.4f}")

            try:
                # Try to convert to float and format
                formatted_value = f"{float(self.probability_shoulder_outcome):.1f}"
            except ValueError:
                # If conversion fails, use the string directly
                formatted_value = self.probability_shoulder_outcome

            self.tst_probability_value_label.setText(formatted_value)

            self.unit = self.unit_st
            # Block signals to prevent the currentIndexChanged signal from being emitted
            self.unitComboBox.blockSignals(True)
            if self.unit:
                textToSet = self.unit
            else:
                if self.languageComboBox.currentIndex == 0: # english
                    textToSet = "Metric"
                elif self.languageComboBox.currentIndex == 1: # english 
                    textToSet = "Métrico" 
                        
            index = self.unitComboBox.findText(textToSet, QtCore.Qt.MatchFixedString)
            if index >= 0:
                self.unitComboBox.setCurrentIndex(index)

            # Unblock signals after setting the text
            self.unitComboBox.blockSignals(False)
            self.updateUnitsLabels()

 
            # Optional: Trigger any ST-specific calculations or UI updates
            self.tstCalculateResults()
            #QMessageBox.information(self, "Data Found", "Records found and loaded into The Shoulder Tool.")
            QMessageBox.information(self, "Data Found" if self.languageComboBox.currentIndex() == 0 else "Datos Encontrados", "Records found and loaded into The Shoulder Tool." if self.languageComboBox.currentIndex() == 0 else "Registros encontrados y cargados en la herramienta The Shoulder Tool.")

            
            
        
        if conn:
            conn.close()
         
    

    def anyLiFFTTaskDataPresent(self):
        for lever_arm_input, load_input, repetitions_input in zip(self.lifft_lever_arm_inputs, self.lifft_load_inputs,     
            self.lifft_repetitions_inputs):
            if lever_arm_input.text() or load_input.text() or repetitions_input.text():
                return True
        return False
    
    def anyDUETTaskDataPresent(self):
        for repetitions_input in self.duet_repetitions_inputs:
            if repetitions_input.text():
                return True
        #for dropdown, repetitions_input in zip(self.omnires_dropdowns, self.duet_repetitions_inputs):
        #    if dropdown.currentIndex() != -1 or repetitions_input.text():
        #        return True
        return False
    
    def anySTTaskDataPresent(self):
        for lever_arm_input, load_input, repetitions_input in zip(self.tst_lever_arm_inputs, self.tst_load_inputs,  self.tst_repetitions_inputs):
            if lever_arm_input.text() or load_input.text() or repetitions_input.text():
                return True
        return False
        
    def checkForExistingLiFFTData(self, userid, datetime):
        # Assuming userid and datetime are the inputs to this method
        query = '''SELECT COUNT(*) FROM lifft_results WHERE userid=? AND datetime=?'''
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()
        cursor.execute(query, (userid, datetime))
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0
    
    def checkForExistingDUETData(self, userid, datetime):
        query = '''SELECT COUNT(*) FROM duet_results WHERE userid=? AND datetime=?'''
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()
        cursor.execute(query, (userid, datetime))
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0
    
    def checkForExistingSTData(self, userid, datetime):
        query = '''SELECT COUNT(*) FROM tst_results WHERE userid=? AND datetime=?'''
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()
        cursor.execute(query, (userid, datetime))
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0
    
    def validateInputsForSave(self):
        userid = self.userIDTextbox.text().strip()
        datetime = self.dateTimeControl.dateTime().toString("yyyy-MM-dd HH:mm")
    
        if not userid or not datetime:
            #QMessageBox.warning(self, "Validation Error", "User ID and Date+Time cannot be blank.")
            QMessageBox.warning(self, "Validation Error" if self.languageComboBox.currentIndex() == 0 else "Error de Validación", "User ID and Date+Time cannot be blank." if self.languageComboBox.currentIndex() == 0 else "El ID de usuario y la Fecha+Hora no pueden estar en blanco.")

            return False, None, None

        #if not self.isLiFFTTabSelected():
        #    QMessageBox.warning(self, "Wrong Tab", "Please select the LiFFT tab before saving.")
        #    return False, None, None
    
        return True, userid, datetime
    
    def saveData(self): #, userid, datetime):
    
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
        #print(currentTabIndex)
        
        # Connect to the database
        valid, userid, datetime = self.validateInputsForSave()
        if not valid:
            return


        try:
            conn = sqlite3.connect(self.databasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            #print(f"An error occurred: {e}")
            #QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            QMessageBox.critical(self, "Database Error" if self.languageComboBox.currentIndex() == 0 else "Error de Base de Datos", f"An error occurred: {e}" if self.languageComboBox.currentIndex() == 0 else f"Se produjo un error: {e}")

            return
    
        if currentTabIndex == 0: # LiFFT
        
            if self.checkForExistingLiFFTData(userid, datetime):
                #reply = QMessageBox.question(self, 'Message',
                #                     "Data will be update, are you sure?", QMessageBox.Yes |
                #                     QMessageBox.No, QMessageBox.No)
                #reply = QMessageBox.question(self,'Message' if self.languageComboBox.currentIndex() == 0 else 'Mensaje', "Data will be updated, are you sure?" if self.languageComboBox.currentIndex() == 0 else "Los datos serán actualizados, ¿está seguro?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                reply = QMessageBox.question(self, 'Data Exists' if self.languageComboBox.currentIndex() == 0 else 'Datos Existentes', "Existing LiFFT data found for this User ID and Date/Time. Update the data?" if self.languageComboBox.currentIndex() == 0 else "Se encontraron datos de LiFFT existentes para este ID de usuario y fecha/hora. ¿Actualizar los datos?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                

                if reply == QMessageBox.No:
                    return
                
            
            
            if not self.anyLiFFTTaskDataPresent():
                #QMessageBox.warning(self, "No Data", "At least one task must have data to save.")
                QMessageBox.warning(self, "No Data" if self.languageComboBox.currentIndex() == 0 else "Sin Datos", "At least one task must have data to save LiFFT." if self.languageComboBox.currentIndex() == 0 else "Al menos una tarea debe tener datos para guardar LiFFT.")

                return
    
        
            try:
                # Delete existing records for the given userid and datetime
                delete_query = '''DELETE FROM lifft_results WHERE userid=? AND datetime=?'''
                cursor.execute(delete_query, (userid, datetime))
        
                # Insert new records for each task
                insert_query = '''INSERT INTO lifft_results (userid, datetime, task_id, lever_arm, load, moment, repetitions,     
                    cumulative_damage, percentage_total, total_cumulative_damage, probability_high_risk, unit) VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        
                for i in range(self.num_task):
                    task_id = i + 1  # Task ID, assuming it starts from 1
                    lever_arm = self.lifft_lever_arm_inputs[i].text()
                    load = self.lifft_load_inputs[i].text()
                    moment = self.lifft_output_labels_matrix[i][3].text()  # Assuming moment is calculated and displayed
                    repetitions = self.lifft_repetitions_inputs[i].text()
                    cumulative_damage = self.lifft_output_labels_matrix[i][5].text()  # Assuming it's calculated/displayed
                    percentage_total = self.lifft_output_labels_matrix[i][6].text()  # Assuming it's calculated/displayed
                    total_cumulative_damage = self.lifft_total_damage_value_label.text()
                    probability_high_risk = self.lifft_probability_value_label.text()
                    unit = self.unitComboBox.currentText()
                    # Convert inputs to appropriate types as needed, e.g., float or int
            
                    cursor.execute(insert_query, (userid, datetime, task_id, lever_arm, load, moment, repetitions,   
                        cumulative_damage, percentage_total, total_cumulative_damage, probability_high_risk, unit))
        
                conn.commit()
                #QMessageBox.information(self, "Success", "LiFFT data saved successfully.")
                QMessageBox.information(self, "Success" if self.languageComboBox.currentIndex() == 0 else "Éxito", "LiFFT data saved successfully." if self.languageComboBox.currentIndex() == 0 else "Datos de LiFFT guardados exitosamente.")

            except Exception as e:
                #QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
                QMessageBox.critical(self, "Database Error" if self.languageComboBox.currentIndex() == 0 else "Error de Base de Datos", f"An error occurred: {e}" if self.languageComboBox.currentIndex() == 0 else f"Ocurrió un error: {e}")

            finally:
                conn.close()
                
        elif currentTabIndex == 1: # DUET
            # Check if data already in the db
            if self.checkForExistingDUETData(userid, datetime):
                #reply = QMessageBox.question(self, 'Data Exists',
                #                         "Existing DUET data found for this User ID and Date/Time. Update the data?",
                #                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                reply = QMessageBox.question(self, 'Data Exists' if self.languageComboBox.currentIndex() == 0 else 'Datos Existentes', "Existing DUET data found for this User ID and Date/Time. Update the data?" if self.languageComboBox.currentIndex() == 0 else "Se encontraron datos de DUET existentes para este ID de usuario y fecha/hora. ¿Actualizar los datos?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                    
            # Check for tasks present in the UI        
            if not self.anyDUETTaskDataPresent():
                #QMessageBox.warning(self, "No Data", "At least one task must have data to save for DUET.")
                QMessageBox.warning(self, "No Data" if self.languageComboBox.currentIndex() == 0 else "Sin Datos", "At least one task must have data to save for DUET." if self.languageComboBox.currentIndex() == 0 else "Al menos una tarea debe tener datos para guardar DUET.")
                return
        
            try:
                # Existing database connection setup...

                # Check and possibly alert for existing data, similar to LiFFT logic...
                # Delete existing records for DUET, analogous to LiFFT
                delete_query_duet = '''DELETE FROM duet_results WHERE userid=? AND datetime=?'''
                cursor.execute(delete_query_duet, (userid, datetime))
                
                # Insert new records for each task in DUET
                insert_query_duet = '''INSERT INTO duet_results (userid, datetime, task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total, total_cumulative_damage, probability_distal_upper_extremity_outcome, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

                for i in range(self.num_task):
                    task_id = i + 1
                    omni_res_scale = self.omnires_dropdowns[i].currentIndex()
                    repetitions = self.duet_repetitions_inputs[i].text()
                    # Assuming cumulative damage and percentage total are calculated/displayed similar to LiFFT
                    cumulative_damage = self.duet_output_labels_matrix[i][3].text()
                    percentage_total = self.duet_output_labels_matrix[i][4].text()
                    total_cumulative_damage = self.duet_total_damage_value_label.text()
                    probability_outcome = self.duet_probability_value_label.text()
                    unit = self.unitComboBox.currentText()

                    cursor.execute(insert_query_duet, (userid, datetime, task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total, total_cumulative_damage, probability_outcome, unit))
                conn.commit()
                #QMessageBox.information(self, "Success", "DUET data saved successfully.")
                QMessageBox.information(self, "Success" if self.languageComboBox.currentIndex() == 0 else "Éxito", "DUET data saved successfully." if self.languageComboBox.currentIndex() == 0 else "Datos de DUET guardados exitosamente.")

            except Exception as e:
                #QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
                QMessageBox.critical(self, "Database Error" if self.languageComboBox.currentIndex() == 0 else "Error de Base de Datos", f"An error occurred: {e}" if self.languageComboBox.currentIndex() == 0 else f"Ocurrió un error: {e}")
            finally:
                if conn:
                    conn.close()
                
                
        elif currentTabIndex == 2: # ST
            # Check if data already exists in the database for ST
            if self.checkForExistingSTData(userid, datetime):
                #reply = QMessageBox.question(self, 'Data Exists',
                #                             "Existing Shoulder Tool data found for this User ID and Date/Time. Update the data?",
                #                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                reply = QMessageBox.question(self, 'Data Exists' if self.languageComboBox.currentIndex() == 0 else 'Datos Existentes', "Existing Shoulder Tool data found for this User ID and Date/Time. Update the data?" if self.languageComboBox.currentIndex() == 0 else "Se encontraron datos The Shoulder Tool existentes para este ID de usuario y fecha/hora. ¿Actualizar los datos?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            # Check if any ST task data is present
            if not self.anySTTaskDataPresent():
                #QMessageBox.warning(self, "No Data", "At least one task must have data to save for The Shoulder Tool.")
                QMessageBox.warning(self, "No Data" if self.languageComboBox.currentIndex() == 0 else "Sin Datos", "At least one task must have data to save The Shoulder Tool." if self.languageComboBox.currentIndex() == 0 else "Al menos una tarea debe tener datos para guardar The Shoulder Tool.")
                return

            try:
                # Delete existing ST records for the given userid and datetime
                delete_query_st = '''DELETE FROM tst_results WHERE userid=? AND datetime=?'''
                cursor.execute(delete_query_st, (userid, datetime))

                # Insert new records for each ST task
                insert_query_st = '''INSERT INTO tst_results (userid, datetime, task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total, total_cumulative_damage, probability_shoulder_outcome, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

                for i in range(self.num_task):
                    task_id = i + 1
                    type_of_task = self.tst_type_of_task_dropdowns[i].currentIndex()
                    lever_arm = self.tst_lever_arm_inputs[i].text()
                    load = self.tst_load_inputs[i].text()
                    moment = self.tst_output_labels_matrix[i][4].text()  # Moment is a calculated field
                    repetitions = self.tst_repetitions_inputs[i].text()
                    cumulative_damage = self.tst_output_labels_matrix[i][6].text()
                    percentage_total = self.tst_output_labels_matrix[i][7].text()
                    total_cumulative_damage = self.tst_total_damage_value_label.text()
                    probability_outcome = self.tst_probability_value_label.text()
                    unit = self.unitComboBox.currentText()

                    cursor.execute(insert_query_st, (userid, datetime, task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total, total_cumulative_damage, probability_outcome, unit))

                conn.commit()
                #QMessageBox.information(self, "Success", "Shoulder Tool data saved successfully.")
                QMessageBox.information(self, "Success" if self.languageComboBox.currentIndex() == 0 else "Éxito", "Shoulder Tool data saved successfully." if self.languageComboBox.currentIndex() == 0 else "Datos de Shoulder Tool guardados exitosamente.")

                
            except Exception as e:
                #QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
                QMessageBox.critical(self, "Database Error" if self.languageComboBox.currentIndex() == 0 else "Error de Base de Datos", f"An error occurred: {e}" if self.languageComboBox.currentIndex() == 0 else f"Ocurrió un error: {e}")
            finally:
                if conn:
                    conn.close()
        

                
    def dateTimeChanged(self):
        # Handle date-time control change
        #print("Date-Time changed to:", self.dateTimeControl.dateTime().toString("yyyy-MM-dd HH:mm"))
        pass
        
        



    def setupControlPanel(self):
        # Control panel layout
        controlLayout = QtWidgets.QGridLayout()
        
        # Directional buttons
        self.upButton = QtWidgets.QPushButton("Up")
        self.downButton = QtWidgets.QPushButton("Down")
        self.leftButton = QtWidgets.QPushButton("Left")
        self.rightButton = QtWidgets.QPushButton("Right")
        self.zoomLabel = QtWidgets.QLabel("Zoom:")
        self.rotationLabel = QtWidgets.QLabel("Rotation:")
        #self.axisGroup = QtWidgets.QLabel("Rotation Axis:")
        #self.zoomLabel.setText(QtWidgets.QApplication.translate("App", "Zoom:"))
        #self.rotationLabel.setText(QtWidgets.QApplication.translate("App", "Rotation:"))
        #self.axisGroup.setTitle(QtWidgets.QApplication.translate("App", "Rotation Axis"))
   
        # Add buttons to layout
        controlLayout.addWidget(self.upButton, 0, 1)
        controlLayout.addWidget(self.downButton, 2, 1)
        controlLayout.addWidget(self.leftButton, 1, 0)
        controlLayout.addWidget(self.rightButton, 1, 2)
        
        # Slider for zoom
        self.zoomSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.zoomSlider.setMinimum(1)
        self.zoomSlider.setMaximum(100)
        self.zoomSlider.setValue(75)
        #controlLayout.addWidget(QtWidgets.QLabel("Zoom:"), 3, 0)
        controlLayout.addWidget(self.zoomLabel, 3, 0)
        controlLayout.addWidget(self.zoomSlider, 3, 1, 1, 2)
        
        # Slider for rotation
        self.rotationSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.rotationSlider.setMinimum(0)
        self.rotationSlider.setMaximum(360)
        controlLayout.addWidget(self.rotationLabel, 4, 0)
        controlLayout.addWidget(self.rotationSlider, 4, 1, 1, 2)
        
        # Radio buttons for axis selection
        self.axisGroup = QtWidgets.QGroupBox("Rotation Axis")
        self.axisLayout = QtWidgets.QHBoxLayout()
        self.xRadio = QtWidgets.QRadioButton("X")
        self.yRadio = QtWidgets.QRadioButton("Y")
        self.zRadio = QtWidgets.QRadioButton("Z")
        self.zRadio.setChecked(True)  # Default rotation around Z-axis
        self.axisLayout.addWidget(self.xRadio)
        self.axisLayout.addWidget(self.yRadio)
        self.axisLayout.addWidget(self.zRadio)
        self.axisGroup.setLayout(self.axisLayout)
        controlLayout.addWidget(self.axisGroup, 5, 0, 1, 3)
        
        # Add control panel to the left layout
        self.leftLayout.addLayout(controlLayout)

	
        # Connect signals
        self.controlPanelconnectSignals()



    def setupTabWidgets(self):
        
        #------------------------------------------------------------------------
        
        self.setupLiFFTTab()
        
        #------------------------------------------------------------------------
        

        #------------------------------------------------------------------------
        
        self.setupDUETTab()
        
        #------------------------------------------------------------------------
              

        #------------------------------------------------------------------------
        
        self.setupTSTTab()
        
        #------------------------------------------------------------------------
        
        
    def setupLiFFTTab(self):
        # Validator for double input
        lifft_double_validator = QDoubleValidator()
        
        # Create bold font for labels that need emphasis
        lifft_bold_font = QFont()
        lifft_bold_font.setBold(True)

        # Main layout
        lifft_main_layout = QVBoxLayout()

        # Frame to hold everything
        lifft_frame = QFrame()
        lifft_frame.setFrameShape(QFrame.StyledPanel)

        # Calculation variables...
        #self.num_task = 20
        self.lifft_damage, self.lifft_percent, self.lifft_moment = [], [], []
        for i in range(self.num_task):
            self.lifft_moment.append(0.0)
            self.lifft_damage.append([0.0, 'none'])   # firs item is the value, second is the color
            self.lifft_percent.append(0.0)

        self.lifft_total_damage = 0
        self.lifft_total_risk = 0
        self.lifft_total_risk_color = 'none'
    
        # Tab widget
        #lifft_tab_widget = QTabWidget()

        # First tab for LiFFT
        self.lifft_tab = QWidget()
        self.lifft_tab_layout = QGridLayout()
        self.lifft_tab.setLayout(self.lifft_tab_layout)

        # Column headers
        lifft_headers = ["Task #", "Lever Arm (cm)", "Load (N)", "Moment (N.m)", "Repetitions (per work day)", "Damage (cumulative)", "% Total (damage)"]
        self.lifft_headers_labels = []
        for col, header in enumerate(lifft_headers):
            lifft_header_label = QLabel(header)
            lifft_header_label.setFont(lifft_bold_font)
            lifft_header_label.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_header_label, 0, col)
            self.lifft_headers_labels.append(lifft_header_label)

        # Task number column
        for row in range(0, self.num_task):
            lifft_task_label = QLabel(str(row+1))
            lifft_task_label.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_task_label, row + 1, 0)

        # Input fields with validation
        self.lifft_lever_arm_inputs = []
        self.lifft_load_inputs = []
        self.lifft_repetitions_inputs = []
        for row in range(0, self.num_task):
            # Lever Arm (cm) input
            lifft_lever_arm_input = QLineEdit()
            lifft_lever_arm_input.setValidator(lifft_double_validator)
            lifft_lever_arm_input.setAlignment(Qt.AlignCenter)
            #self.lifft_tab_layout.removeWidget(lifft_lever_arm_input)
            self.lifft_tab_layout.addWidget(lifft_lever_arm_input, row + 1, 1)
            self.lifft_lever_arm_inputs.append(lifft_lever_arm_input)

            # Load (N) input
            lifft_load_input = QLineEdit()
            lifft_load_input.setValidator(lifft_double_validator)
            lifft_load_input.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_load_input, row + 1, 2)
            self.lifft_load_inputs.append(lifft_load_input)
            
            # Repetitions input
            lifft_repetitions_input = QLineEdit()
            lifft_repetitions_input.setValidator(QIntValidator())
            lifft_repetitions_input.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_repetitions_input, row + 1, 4)
            self.lifft_repetitions_inputs.append(lifft_repetitions_input)

        # Initialize a 2D list (matrix) to hold the output labels
        self.lifft_output_labels_matrix = [[None for _ in range(7)] for _ in range(self.num_task+1)]

        # Output labels for Moment, Damage, and % Total
        #print("num_task:" + str(self.num_task) + "\n")
        for row in range(0, self.num_task):
            for col in [3, 5, 6]:  # Only these columns have output labels
                lifft_label = QLabel("0.0")
                lifft_label.setAlignment(Qt.AlignCenter)
                self.lifft_tab_layout.addWidget(lifft_label, row + 1, col)
                self.lifft_output_labels_matrix[row][col] = lifft_label

        # Bottom row labels and values beneath the 'Damage' column
        self.lifft_total_damage_label = QLabel("Total Cumulative Damage:")
        self.lifft_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lifft_total_damage_label.setFont(lifft_bold_font)
        self.lifft_tab_layout.addWidget(self.lifft_total_damage_label, self.num_task + 1, 4, 1, 1)
        self.lifft_total_damage_value_label = QLabel("0.0")
        self.lifft_total_damage_value_label.setFont(lifft_bold_font)
        self.lifft_total_damage_value_label.setAlignment(Qt.AlignCenter)
        self.lifft_tab_layout.addWidget(self.lifft_total_damage_value_label, self.num_task + 1, 5)

        self.lifft_probability_label = QLabel("Probability of High Risk Job * (%):")
        self.lifft_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        #self.lifft_probability_label.setAlignment(Qt.AlignLeft)
        self.lifft_probability_label.setFont(lifft_bold_font)
        self.lifft_tab_layout.addWidget(self.lifft_probability_label, self.num_task + 2, 4, 1, 1)
        self.lifft_probability_value_label = QLabel("0.0")
        self.lifft_probability_value_label.setFont(lifft_bold_font)
        self.lifft_probability_value_label.setAlignment(Qt.AlignCenter)
        self.lifft_tab_layout.addWidget(self.lifft_probability_value_label, self.num_task + 2, 5)

        # Add LiFFT tab to tab widget
        #lifft_tab_widget.addTab(lifft_tab, "LiFFT")
        #self.tabWidget.addTab(lifft_tab, "LiFFT")
        #self.tabWidget.addTab(self.lifft_tab, "Lifting Fatigue Failure Tool (LiFFT)")
        self.tabWidget.insertTab(0, self.lifft_tab, "Lifting Fatigue Failure Tool (LiFFT)")
    
        # Buttons
        lifft_buttons_layout = QHBoxLayout()
        self.lifft_reset_button = QPushButton("Reset")
        self.lifft_calculate_button = QPushButton("Calculate")
        lifft_buttons_layout.addWidget(self.lifft_reset_button)
        lifft_buttons_layout.addWidget(self.lifft_calculate_button)
        
        self.lifft_tab_layout.addLayout(lifft_buttons_layout, self.num_task + 3, 0, 1, 7)  # Adjust grid position as necessary
        
        # Connect the buttons to methods
        self.lifft_reset_button.clicked.connect(self.lifftResetForm)
        self.lifft_calculate_button.clicked.connect(self.lifftCalculateResults)

    
    
    
    def setupDUETTab(self):
        # Validator for double input
        duet_double_validator = QDoubleValidator()
        
        # Create bold font for labels that need emphasis
        duet_bold_font = QFont()
        duet_bold_font.setBold(True)

        # Main layout
        duet_main_layout = QVBoxLayout()

        # Frame to hold everything
        duet_frame = QFrame()
        duet_frame.setFrameShape(QFrame.StyledPanel)

        # Calculation variables...
        self.duet_damage, self.duet_percent = [], []
        for i in range(self.num_task):
            self.duet_damage.append([0.0, 'none'])   # first item is the value, second is the color
            self.duet_percent.append(0.0)

        self.duet_total_damage = 0
        self.duet_total_risk = 0
        self.duet_total_risk_color = 'none'

        # Tab widget
        self.duet_tab = QWidget()
        self.duet_tab_layout = QGridLayout()
        self.duet_tab.setLayout(self.duet_tab_layout)

        # Column headers
        duet_headers = ["Task #", "OMNI-Res Scale", "Repetitions (per work day)", "Damage (cumulative)", "% Total (damage)"]
        self.duet_headers_labels = []
        for col, header in enumerate(duet_headers):
            duet_header_label = QLabel(header)
            duet_header_label.setFont(duet_bold_font)
            duet_header_label.setAlignment(Qt.AlignCenter)
            self.duet_tab_layout.addWidget(duet_header_label, 0, col)
            self.duet_headers_labels.append(duet_header_label)

        # Task number column and Difficulty Rating dropdown
        self.omnires_dropdowns = []
        self.duet_repetitions_inputs = []
        for row in range(self.num_task):
            # Task Number
            duet_task_label = QLabel(str(row+1))
            duet_task_label.setAlignment(Qt.AlignCenter)
            self.duet_tab_layout.addWidget(duet_task_label, row + 1, 0)
            
            # Difficulty Rating dropdown
            omnires_dropdown = QComboBox()
            omnires_dropdown.addItem("0: Extremely Easy")
            omnires_dropdown.addItem("1:")
            omnires_dropdown.addItem("2: Easy")
            omnires_dropdown.addItem("3:")
            omnires_dropdown.addItem("4: Somewhat Easy")
            omnires_dropdown.addItem("5:")
            omnires_dropdown.addItem("6: Somewhat Hard")
            omnires_dropdown.addItem("7:")
            omnires_dropdown.addItem("8: Hard")
            omnires_dropdown.addItem("9:")
            omnires_dropdown.addItem("10: Extremely Hard")
            
            self.duet_tab_layout.addWidget(omnires_dropdown, row + 1, 1)
            self.omnires_dropdowns.append(omnires_dropdown)
            
            
            
            # Repetitions input
            duet_repetitions_input = QLineEdit()
            duet_repetitions_input.setValidator(QIntValidator())
            duet_repetitions_input.setAlignment(Qt.AlignCenter)
            self.duet_tab_layout.addWidget(duet_repetitions_input, row + 1, 2)
            self.duet_repetitions_inputs.append(duet_repetitions_input)

        # Initialize a 2D list (matrix) to hold the output labels
        self.duet_output_labels_matrix = [[None for _ in range(5)] for _ in range(self.num_task + 1)]

        # Output labels for Damage, and % Total
        for row in range(self.num_task):
            for col in [3, 4]:  # Only these columns have output labels
                duet_label = QLabel("0.0")
                duet_label.setAlignment(Qt.AlignCenter)
                self.duet_tab_layout.addWidget(duet_label, row + 1, col)
                self.duet_output_labels_matrix[row][col] = duet_label

        # Bottom row labels and values beneath the 'Damage' column
        self.duet_total_damage_label = QLabel("Total Cumulative Damage:")
        self.duet_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.duet_total_damage_label.setFont(duet_bold_font)
        self.duet_tab_layout.addWidget(self.duet_total_damage_label, self.num_task + 1, 2, 1, 1)
        self.duet_total_damage_value_label = QLabel("0.0")
        self.duet_total_damage_value_label.setFont(duet_bold_font)
        self.duet_total_damage_value_label.setAlignment(Qt.AlignCenter)
        self.duet_tab_layout.addWidget(self.duet_total_damage_value_label, self.num_task + 1, 3)

        # Probability of High Risk label and value for DUET (immediately below the previous)
        self.duet_probability_label = QLabel("Probability of Distal Upper Extremity Outcome (%):")
        self.duet_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.duet_probability_label.setFont(duet_bold_font)
        self.duet_tab_layout.addWidget(self.duet_probability_label, self.num_task + 2, 2, 1, 1)  # Adjusted to column 2
        self.duet_probability_value_label = QLabel("0.0")
        self.duet_probability_value_label.setFont(duet_bold_font)
        self.duet_probability_value_label.setAlignment(Qt.AlignCenter)
        self.duet_tab_layout.addWidget(self.duet_probability_value_label, self.num_task + 2, 3)  # Adjusted to column 3


        #self.tabWidget.addTab(self.duet_tab, "Distal Upper Extremity Tool (DUET)")
        self.tabWidget.insertTab(1, self.duet_tab, "Distal Upper Extremity Tool (DUET)")
        #self.tabWidget.addTab(duet_tab, "DUET")
        
        # Buttons
        duet_buttons_layout = QHBoxLayout()
        self.duet_reset_button = QPushButton("Reset")
        self.duet_calculate_button = QPushButton("Calculate")
        duet_buttons_layout.addWidget(self.duet_reset_button)
        duet_buttons_layout.addWidget(self.duet_calculate_button)
        
        self.duet_tab_layout.addLayout(duet_buttons_layout, self.num_task + 3, 0, 1, 5)  # Adjust grid position as necessary
        
        # Connect the buttons to methods
        self.duet_reset_button.clicked.connect(self.duetResetForm)
        self.duet_calculate_button.clicked.connect(self.duetCalculateResults)
        
        


    def setupTSTTab(self):
        # Validator for double input
        tst_double_validator = QDoubleValidator()

        # Create bold font for labels that need emphasis
        tst_bold_font = QFont()
        tst_bold_font.setBold(True)

        # Main layout
        tst_main_layout = QVBoxLayout()

        # Frame to hold everything
        tst_frame = QFrame()
        tst_frame.setFrameShape(QFrame.StyledPanel)

        # Calculation variables...
        self.tst_lever_arm, self.tst_load, self.tst_moment, self.tst_repetitions, self.tst_damage, self.tst_percent = [], [], [], [], [], []
        for i in range(self.num_task):
            self.tst_lever_arm.append(0.0)
            self.tst_load.append(0.0)
            self.tst_moment.append(0.0)
            self.tst_repetitions.append(0)
            self.tst_damage.append([0.0, 'none'])
            self.tst_percent.append(0.0)

        #self.tst_total_cumulative_damage = 0
        #self.tst_probability_of_outcome = 0
        self.tst_total_damage = 0
        self.tst_total_risk = 0
        self.tst_total_risk_color = 'none'

        # Tab widget
        self.tst_tab = QWidget()
        self.tst_tab_layout = QGridLayout()
        self.tst_tab.setLayout(self.tst_tab_layout)

        # Column headers
        tst_headers = ["Task #", "Type of Task", "Lever Arm (cm)", "Load (N)", "Moment (N.m)", "Repetitions (per work day)", "Damage (cumulative)", "% Total (damage)"]
        self.tst_headers_labels = []
        for col, header in enumerate(tst_headers):
            tst_header_label = QLabel(header)
            tst_header_label.setFont(tst_bold_font)
            tst_header_label.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_header_label, 0, col)
            self.tst_headers_labels.append(tst_header_label)

        # Task number column and Type of Task dropdown
        self.tst_type_of_task_dropdowns = []
        task_types = ["Handling Loads", "Push or Pull Downward", "Horizontal Push or Pull"]
        for row in range(self.num_task):
            # Task Number
            tst_task_label = QLabel(str(row+1))
            tst_task_label.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_task_label, row + 1, 0)
            
        for row in range(self.num_task):
            # Type of Task dropdown
            type_of_task_dropdown = QComboBox()
            type_of_task_dropdown.addItems(task_types)
            self.tst_tab_layout.addWidget(type_of_task_dropdown, row + 1, 1)
            self.tst_type_of_task_dropdowns.append(type_of_task_dropdown)
        
        
        self.tst_lever_arm_inputs = []
        self.tst_load_inputs = []
        self.tst_repetitions_inputs = []
        for row in range(self.num_task):
            # Lever Arm (cm) input
            tst_lever_arm_input = QLineEdit()
            tst_lever_arm_input.setValidator(tst_double_validator)
            tst_lever_arm_input.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_lever_arm_input, row + 1, 2)
            self.tst_lever_arm_inputs.append(tst_lever_arm_input)

            # Load (N) input
            tst_load_input = QLineEdit()
            tst_load_input.setValidator(tst_double_validator)
            tst_load_input.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_load_input, row + 1, 3)
            self.tst_load_inputs.append(tst_load_input)
            
            # Repetitions input
            tst_repetitions_input = QLineEdit()
            tst_repetitions_input.setValidator(tst_double_validator)
            tst_repetitions_input.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_repetitions_input, row + 1, 5)
            self.tst_repetitions_inputs.append(tst_repetitions_input)

            
            
            

        # Initialize a 2D list (matrix) to hold the output labels for Moment, Damage, and % Total
        self.tst_output_labels_matrix = [[None for _ in range(8)] for _ in range(self.num_task + 1)]

        # Output labels for Moment, Damage, and % Total
        for row in range(self.num_task):
            for col in [4, 6, 7]:  # Columns for output labels
                tst_label = QLabel("0.0")
                tst_label.setAlignment(Qt.AlignCenter)
                self.tst_tab_layout.addWidget(tst_label, row + 1, col)
                self.tst_output_labels_matrix[row][col] = tst_label

        # Bottom row labels and values beneath the 'Damage' column
        self.tst_total_damage_label = QLabel("Total Cumulative Damage:")
        self.tst_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tst_total_damage_label.setFont(tst_bold_font)
        self.tst_tab_layout.addWidget(self.tst_total_damage_label, self.num_task + 1, 5, 1, 1)  # Adjusted to column 6 for TST
        self.tst_total_damage_value_label = QLabel("0.0")
        self.tst_total_damage_value_label.setFont(tst_bold_font)
        self.tst_total_damage_value_label.setAlignment(Qt.AlignCenter)
        self.tst_tab_layout.addWidget(self.tst_total_damage_value_label, self.num_task + 1, 6)  # Adjusted to column 7 for TST

        # Probability of Shoulder Outcome label and value for TST (immediately below the previous)
        self.tst_probability_label = QLabel("Probability of Shoulder Outcome (%):")
        self.tst_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tst_probability_label.setFont(tst_bold_font)
        self.tst_tab_layout.addWidget(self.tst_probability_label, self.num_task + 2, 5, 1, 1)  # Adjusted to column 6 for TST
        self.tst_probability_value_label = QLabel("0.0")
        self.tst_probability_value_label.setFont(tst_bold_font)
        self.tst_probability_value_label.setAlignment(Qt.AlignCenter)
        self.tst_tab_layout.addWidget(self.tst_probability_value_label, self.num_task + 2, 6)  # Adjusted to column 7 for TST

        #self.tabWidget.addTab(self.tst_tab, "Shoulder Tool (ST)")
        self.tabWidget.insertTab(2, self.tst_tab, "Shoulder Tool (ST)")
        #self.tabWidget.addTab(tst_tab, "TST")

        # Buttons
        tst_buttons_layout = QHBoxLayout()
        self.tst_reset_button = QPushButton("Reset")
        self.tst_calculate_button = QPushButton("Calculate")
        tst_buttons_layout.addWidget(self.tst_reset_button)
        tst_buttons_layout.addWidget(self.tst_calculate_button)

        self.tst_tab_layout.addLayout(tst_buttons_layout, self.num_task + 3, 0, 1, 8)  # Span across the entire grid width for TST

        # Connect the buttons to methods
        self.tst_reset_button.clicked.connect(self.tstResetForm)
        self.tst_calculate_button.clicked.connect(self.tstCalculateResults)

    
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    
    
    
    
    
    
    
    
    #---------------------------------------------------------------------------------
    #                       RENDER!!!!!!!!!!!!!!!!!!!!!!!
    #---------------------------------------------------------------------------------
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def setupRenderer(self):
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        # Load all STL models for the scene
        self.setupActors()

        # Reset the camera to fit all actors in view
        self.renderer.ResetCamera()
        
        self.initialCameraSettings = {'position': None, 'focalPoint': None, 'viewUp': None}
        self.storeInitialCameraSettings()
        
        # Initialize lastAngle for rotation control
        self.lastAngle = {'x': -90, 'y': 0, 'z': -45}  # Using a dictionary to store last angles for each axis

        
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def storeInitialCameraSettings(self):
        camera = self.renderer.GetActiveCamera()
        self.initialCameraSettings['position'] = camera.GetPosition()
        self.initialCameraSettings['focalPoint'] = camera.GetFocalPoint()
        self.initialCameraSettings['viewUp'] = camera.GetViewUp()
    
    
    def setupActors(self):
        # Define the base path for model files
        base_path = "../models/"
        
        # Load the main human model
        self.humanActor = self.loadModel(base_path + "JardeDummy.stl")
        
        
        # Load the lower back model
        #self.lowerBackActor = self.loadModel(base_path + "lowerback01.stl")
        #self.lowerBackActor.SetPosition(75, 295, 1060)
        self.lowerBackActor = self.loadModel(base_path + "lowerback03.stl")
        self.lowerBackActor.SetPosition(284, 293, 1010)
        #self.lowerBackActor.GetProperty().SetColor(0.0, 1.0, 0.0)
        self.lowerBackActor.VisibilityOff()  # Make invisible if needed
 

        # Load the forearm models
        self.leftForeArmActor = self.loadModel(base_path + "leftforearm02.stl")
        self.leftForeArmActor.SetPosition(264.7, 57.9, 851.6)
        self.leftHandActor = self.loadModel(base_path + "lefthand02.stl")
        self.leftHandActor.SetPosition(369, -42, 694)
        #self.leftForeArmActor.GetProperty().SetColor(0.0, 1.0, 0.0)
        #self.leftHandActor.GetProperty().SetColor(0.0, 1.0, 0.0)
        self.leftForeArmActor.VisibilityOff()  # Make invisible if needed
        self.leftHandActor.VisibilityOff()  # Make invisible if needed
	
        self.rightForeArmActor = self.loadModel(base_path + "rightforearm02.stl")
        self.rightForeArmActor.SetPosition(264.7, 535, 851.6)
        self.rightHandActor = self.loadModel(base_path + "righthand02.stl")
        self.rightHandActor.SetPosition(222, 545, 703)
        self.rightForeArmActor.VisibilityOff()  # Make invisible if needed
        self.rightHandActor.VisibilityOff()  # Make invisible if needed
        
        
        # Load shoulder models
        self.leftShoulderActor = self.loadModel(base_path + "leftshoulder03.stl")
        self.leftShoulderActor.SetPosition(247, 105, 1110)
        #self.leftShoulderActor.GetProperty().SetColor(0.0, 1.0, 0.0)
        self.leftShoulderActor.VisibilityOff()  # Make invisible if needed
	
        self.rightShoulderActor = self.loadModel(base_path + "rightshoulder03.stl")
        self.rightShoulderActor.SetPosition(247, 495, 1110)
        #self.rightShoulderActor.GetProperty().SetColor(0.0, 1.0, 0.0)
        self.rightShoulderActor.VisibilityOff()  # Make invisible if needed
        
        
        
        # ...Initial pose...
        #self.humanActor.SetUserTransform(vtk.vtkTransform().RotateX(-90))  # Rotate to stand up
        transform = vtk.vtkTransform()
        transform.RotateX(-90)  # Rotate -90 degrees around the X-axis
        self.humanActor.SetUserTransform(transform) 
        self.lowerBackActor.SetUserTransform(transform) 
        self.leftForeArmActor.SetUserTransform(transform) 
        self.leftHandActor.SetUserTransform(transform) 
        self.rightForeArmActor.SetUserTransform(transform) 
        self.rightHandActor.SetUserTransform(transform) 
        self.leftShoulderActor.SetUserTransform(transform) 
        self.rightShoulderActor.SetUserTransform(transform) 
        
        #self.humanActor.SetUserTransform(vtk.vtkTransform().RotateX(-90))
        # Continue from the previous transform
        transform.RotateZ(-45)  # Rotate -45 degrees around the Y-axis to show the back
        self.humanActor.SetUserTransform(transform) 
        self.lowerBackActor.SetUserTransform(transform) 
        self.leftForeArmActor.SetUserTransform(transform) 
        self.leftHandActor.SetUserTransform(transform) 
        self.rightForeArmActor.SetUserTransform(transform) 
        self.rightHandActor.SetUserTransform(transform) 
        self.leftShoulderActor.SetUserTransform(transform) 
        self.rightShoulderActor.SetUserTransform(transform) 
        
        
        # Add actors to the scene...
        self.renderer.AddActor(self.humanActor)
        self.renderer.AddActor(self.lowerBackActor)
        self.renderer.AddActor(self.leftForeArmActor)
        self.renderer.AddActor(self.leftHandActor)
        self.renderer.AddActor(self.rightForeArmActor)
        self.renderer.AddActor(self.rightHandActor)
        self.renderer.AddActor(self.leftShoulderActor)
        self.renderer.AddActor(self.rightShoulderActor)
         
        
        
        # TODO: Add additional body part actors as needed


    def loadModel(self, file_path):
        # Load an STL file and return its actor
        reader = vtk.vtkSTLReader()
        reader.SetFileName(file_path)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        return actor
        
    def onTabChange(self, index):
        if hasattr(self, 'animationTimer') and self.isAnimationAllowed:
            self.tabIndex = index  # Store the new tab index
            self.animationPhase = 1  # Start with resetting the view
            self.resetView()  # Reset view settings before starting animation
            self.animationTimer.start(16)  # Approx. 60 FPS
    
    def resetView(self):
        # Reset parameters for the initial view
        self.targetAzimuth = 0
        self.targetElevation = 0
        self.currentAzimuth = 0
        self.currentElevation = 0

    def setNewTargetPosition(self):
        # Define target positions based on the currently selected tab
        if self.tabIndex == 0:  # First tab LiFFT
            self.targetAzimuth = -30  # Example values
            self.targetElevation = -15
        elif self.tabIndex == 1:  # DUET
            self.targetAzimuth = 45
            self.targetElevation = 20
        elif self.tabIndex == 2:  # Shoulder Tool
            self.targetAzimuth = 90
            self.targetElevation = 0

    def positionReached(self, target, current):
        return abs(target - current) < 1

    def updateCameraPosition(self):
        camera = self.renderer.GetActiveCamera()
        if self.animationPhase == 1:
            # Incremental rotation towards reset view
            if not self.positionReached(0, self.currentAzimuth) or not self.positionReached(0, self.currentElevation):
                camera.Azimuth(-self.currentAzimuth / 10)
                camera.Elevation(-self.currentElevation / 10)
                self.currentAzimuth -= self.currentAzimuth / 10
                self.currentElevation -= self.currentElevation / 10
            else:
                self.animationPhase = 2  # Switch to moving towards the new target position
                self.setNewTargetPosition()
        elif self.animationPhase == 2:
            # Perform incremental rotation towards the target angle
            azimuthStep = (self.targetAzimuth - self.currentAzimuth) / 10
            elevationStep = (self.targetElevation - self.currentElevation) / 10
            camera.Azimuth(azimuthStep)
            camera.Elevation(elevationStep)
            self.currentAzimuth += azimuthStep
            self.currentElevation += elevationStep
            if self.positionReached(self.targetAzimuth, self.currentAzimuth) and self.positionReached(self.targetElevation, self.currentElevation):
                self.animationTimer.stop()  # Stop the timer when the target position is reached
            
                
    def updateRotation(self):
        self.updateCameraPosition()
        self.renderer.GetRenderWindow().Render()
        QtWidgets.QApplication.processEvents()  # Keep the UI responsive
        
        
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
     
     
     
     
     



    def controlPanelconnectSignals(self):
        # Connect the control signals to their respective slots
        #self.upButton.clicked.connect(lambda: self.moveModel(0, 10, 0))
        #self.downButton.clicked.connect(lambda: self.moveModel(0, -10, 0))
        #self.leftButton.clicked.connect(lambda: self.moveModel(-10, 0, 0))
        #self.rightButton.clicked.connect(lambda: self.moveModel(10, 0, 0))
        
        self.upButton.clicked.connect(self.moveCameraUp)
        self.downButton.clicked.connect(self.moveCameraDown)
        self.leftButton.clicked.connect(self.moveCameraLeft)
        self.rightButton.clicked.connect(self.moveCameraRight)
    
        self.zoomSlider.valueChanged.connect(self.adjustZoom)
        self.rotationSlider.valueChanged.connect(self.adjustRotation)


    def moveCamera(self, direction):
        camera = self.renderer.GetActiveCamera()
        position = camera.GetPosition()
        focalPoint = camera.GetFocalPoint()
        up = camera.GetViewUp()

        # Calculate camera's viewing direction
        viewDirection = np.array(focalPoint) - np.array(position)
        viewDirection = viewDirection / np.linalg.norm(viewDirection)

        # Calculate the right vector using cross product of view direction and up vector
        right = np.cross(viewDirection, up)
        right = right / np.linalg.norm(right)

        # Calculate the actual up vector (perpendicular to both view and right vectors)
        actualUp = np.cross(right, viewDirection)
        actualUp = actualUp / np.linalg.norm(actualUp)

        # Movement speed
        speed = 10

        # Determine movement vector based on direction parameter
        if direction == "up":
            movement = -actualUp * speed
        elif direction == "down":
            movement = actualUp * speed
        elif direction == "left":
            movement = right * speed
        elif direction == "right":
            movement = -right * speed

        # Update position and focal point
        newPosition = np.array(position) + movement
        newFocalPoint = np.array(focalPoint) + movement

        camera.SetPosition(newPosition.tolist())
        camera.SetFocalPoint(newFocalPoint.tolist())

        # Re-render the window to update the view
        self.vtkWidget.GetRenderWindow().Render()

    # Example usage
    def moveCameraUp(self):
        self.moveCamera("up")

    def moveCameraDown(self):
        self.moveCamera("down")
 
    def moveCameraLeft(self):
        self.moveCamera("left")

    def moveCameraRight(self):
        self.moveCamera("right")


    def adjustZoom(self, value):
        # Assuming value ranges from 1 to 100 with 75 as the initial zoom level (1.5x zoom)
        # Adjust the formula to map 75 to a zoom factor of 1.5 and allow for a wider range
        if value > 75:
            # When slider is above 75, increase zoom exponentially up to a max zoom factor (e.g., 5x)
            zoom_factor = 1.5 + (value - 75) / 25 * 3.5  # Adjust as needed
        elif value < 75:
            # When slider is below 75, decrease zoom, down to a min zoom factor (e.g., 0.5x)
            zoom_factor = 1.5 - (75 - value) / 75 * 1  # Adjust as needed
        else:
            # Default zoom factor when the slider is at 75
            zoom_factor = 1.5

        # Ensure zoom_factor is within reasonable limits (for safety, though it should already be constrained)
        zoom_factor = max(0.5, min(5.0, zoom_factor))

        #print("v:", value)
        #print("zf:", zoom_factor)
    
        # Reset camera to initial settings before applying zoom to ensure consistency
        camera = self.renderer.GetActiveCamera()
        self.renderer.ResetCamera()

        # Apply zoom
        camera.Zoom(zoom_factor)

        # Re-render
        self.vtkWidget.GetRenderWindow().Render()


    def adjustRotation(self, angle):
        # Determine the selected axis and get the last angle for that axis
        if self.xRadio.isChecked():
            axis = (1, 0, 0)
            axisKey = 'x'
        elif self.yRadio.isChecked():
            axis = (0, 1, 0)
            axisKey = 'y'
        else:  # Default to Z if nothing else is selected or Z is selected
            axis = (0, 0, 1)
            axisKey = 'z'

        # Calculate the rotation angle difference from the last angle to achieve incremental rotation
        angleDifference = angle - self.lastAngle[axisKey]
        self.lastAngle[axisKey] = angle  # Update the lastAngle for the next call

        camera = self.renderer.GetActiveCamera()
        focalPoint = camera.GetFocalPoint()

        # Apply rotation around the chosen axis at the focal point
        transform = vtk.vtkTransform()
        transform.PostMultiply()  # Ensure the transform is applied after the existing transformations
        transform.Translate(-focalPoint[0], -focalPoint[1], -focalPoint[2])  # Move to origin
        transform.RotateWXYZ(angleDifference, *axis)  # Rotate around the axis
        transform.Translate(focalPoint[0], focalPoint[1], focalPoint[2])  # Move back to original position

        # Update the camera's position and view up vector based on the transform
        newPosition = transform.TransformPoint(camera.GetPosition())
        newViewUp = transform.TransformVector(camera.GetViewUp())

        camera.SetPosition(newPosition)
        camera.SetViewUp(newViewUp)

        # Re-render the window to update the view
        self.vtkWidget.GetRenderWindow().Render()


        




if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ErgoTools()
    window.setWindowTitle("Fatigue Failure Risk Assessment Tools")
    #window.setGeometry(100, 100, 1030, 619)  # Adjust the size as needed to match the UI

    window.show()
    sys.exit(app.exec_())

