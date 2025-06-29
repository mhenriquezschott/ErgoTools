from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox, QSizePolicy, QCheckBox, QFrame, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QLocale, QTime, QDate, QStandardPaths, QSize

import sqlite3


class WorkerTransferDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transfer Worker Tool Data")
        self.setFixedSize(900, 110)  # Fixed window size

        # **Main Layout**
        main_layout = QVBoxLayout()

        # **Row Layout for Labels & Combos**
        row_layout = QHBoxLayout()

        # **Bold Font for Labels**
        bold_font = QFont()
        bold_font.setBold(True)

                # **Worker Row Layout (Separate from Other Filters)**
        worker_row_layout = QHBoxLayout()

        # **Worker Selection**
        self.worker_label = QLabel("Worker:")
        self.worker_label.setFont(bold_font)
        self.workerComboBox = QComboBox()  # Corrected name
        self.workerComboBox.setMinimumWidth(200)  # Increase width
        self.workerComboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.workerComboBox.currentIndexChanged.connect(self.onWorkerChanged)  # Connect event

        # **Add Widgets to Worker Row Layout**
        worker_row_layout.addWidget(self.worker_label)
        worker_row_layout.addWidget(self.workerComboBox)
        
        
        
        # Order Button
        self.orderButton = QtWidgets.QPushButton()
        self.orderButton.setIcon(QIcon("../images/alphaorder01.png"))
        self.orderButton.setFixedSize(30, 30)  # Square button
        self.orderButton.setIconSize(QtCore.QSize(25, 25))
        self.orderButton.clicked.connect(self.orderButtonClicked)
        worker_row_layout.addWidget(self.orderButton)

        # Search Button
        self.searchButton = QtWidgets.QPushButton()
        self.searchButton.setIcon(QIcon("../images/search_icon.png"))
        self.searchButton.setFixedSize(30, 30)  # Square button
        self.searchButton.setIconSize(QtCore.QSize(25, 25))
        self.searchButton.clicked.connect(self.searchWorkerClicked)
        worker_row_layout.addWidget(self.searchButton)

        
        
        
        
        
        
        
        worker_row_layout.addStretch()  # Push elements to the left



       


        # **Plant Selection**
        self.plant_label = QLabel("Plant:")
        self.plant_label.setFont(bold_font)
        self.plant_combo = QComboBox()
        self.plant_combo.setMinimumWidth(120)  # Increase width
        self.plant_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expand if needed
        self.plant_combo.currentIndexChanged.connect(self.onPlantChanged)  # Connect event

        # **Section Selection**
        self.section_label = QLabel("Section:")
        self.section_label.setFont(bold_font)
        self.section_combo = QComboBox()
        self.section_combo.setMinimumWidth(100)  # Increase width
        self.section_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.section_combo.currentIndexChanged.connect(self.onSectionChanged)  # Connect event

        # **Line Selection**
        self.line_label = QLabel("Line:")
        self.line_label.setFont(bold_font)
        self.line_combo = QComboBox()
        self.line_combo.setMinimumWidth(100)  # Increase width
        self.line_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.line_combo.currentIndexChanged.connect(self.onLineChanged)  # Connect event

        # **Station Selection**
        self.station_label = QLabel("Station:")
        self.station_label.setFont(bold_font)
        self.station_combo = QComboBox()
        self.station_combo.setMinimumWidth(50)  # Increase width
        self.station_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.station_combo.currentIndexChanged.connect(self.onStationChanged)  # Connect event

        # **Separator Between Station and Shift**
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.VLine)  # Vertical line
        self.separator.setFrameShadow(QFrame.Sunken)  # Slight shadow effect
        self.separator.setFixedWidth(10)  # Adjust width for visibility

        # **Shift Selection**
        self.shift_label = QLabel("Shift:")
        self.shift_label.setFont(bold_font)
        self.shift_combo = QComboBox()
        self.shift_combo.setMinimumWidth(20)  # Increase width
        self.shift_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.shift_combo.currentIndexChanged.connect(self.onShiftChanged)  # Connect event

        # **Add Widgets to Row Layout**
        row_layout.addWidget(self.plant_label)
        row_layout.addWidget(self.plant_combo)
        row_layout.addWidget(self.section_label)
        row_layout.addWidget(self.section_combo)
        row_layout.addWidget(self.line_label)
        row_layout.addWidget(self.line_combo)
        row_layout.addWidget(self.station_label)
        row_layout.addWidget(self.station_combo)
        row_layout.addWidget(self.separator) 
        row_layout.addWidget(self.shift_label)
        row_layout.addWidget(self.shift_combo)

        # **Buttons Layout**
        button_layout = QHBoxLayout()
        
        # **Cancel Button (Closes the Dialog)**
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)  # Close the dialog
        button_layout.addWidget(self.cancel_button)
        
        
        # **Copy Data Checkbox (Small Size, Enabled by Default)**
        self.copy_data_checkbox = QCheckBox("Copy Data")
        self.copy_data_checkbox.setChecked(True)  # Enabled by default
        self.copy_data_checkbox.setFixedSize(100, 25)  # Small checkbox size
        button_layout.addWidget(self.copy_data_checkbox)


        # **Transfer Button (Currently a Dummy Function)**
        self.transfer_button = QPushButton("Transfer")
        self.transfer_button.clicked.connect(self.onTransfer)
        button_layout.addWidget(self.transfer_button)

        # **Add Layouts to Main Layout**
        main_layout.addLayout(worker_row_layout)  # Add worker row layout first
        main_layout.addLayout(row_layout)  # Add the single row layout
        main_layout.addLayout(button_layout)  # Add the button layout

        # **Set Final Layout**
        self.setLayout(main_layout)
        
        self.loadWorkers(0)
        self.loadPlants()
        self.loadShifts()
        
        self.isNumberOrder = False  # Default state
        
        
    def onWorkerChanged(self):
        #selected_worker = self.worker_combo.currentText().strip()
        # Extract Worker ID if the format is "ID (LastName, FirstName)"
        #self.worker_id_label.setText(f"ID: {selected_worker.split(' ')[0]}" if selected_worker else "ID: ")
        return
        
        
        
    # **Handlers for ComboBox Changes (Dummy)**
    def onPlantChanged(self):
        self.loadSections()

    def onSectionChanged(self):
        self.loadLines()

    def onLineChanged(self):
        self.loadStations()

    def onStationChanged(self):
        return
        #print("Station changed:", self.station_combo.currentText())

    def onShiftChanged(self):
        return
        #print("Shift changed:", self.shift_combo.currentText())

    # **Transfer Button Handler **
    def onTransfer(self):
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            return 
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            return 

        # **Retrieve Source and Destination Worker IDs**
        parentWorkerComboText = self.parent().workerComboBox.currentText()
        parentWorkerID = parentWorkerComboText.split(" ")[0] if parentWorkerComboText else ""
    
        destinationWorkerComboText = self.workerComboBox.currentText()
        destinationWorkerID = destinationWorkerComboText.split(" ")[0] if destinationWorkerComboText else ""
    
        #if not destinationWorkerID or destinationWorkerID == parentWorkerID:
        #    QMessageBox.warning(self, "Invalid Transfer", "Cannot transfer data to the same worker.")
        #    return
    
        # **Retrieve Parent Worker Location Details**
        parentPlantName = self.parent().plant_combo.currentText().strip()
        parentSectionName = self.parent().section_combo.currentText().strip()
        parentLineName = self.parent().line_combo.currentText().strip()
        parentStationID = self.parent().station_combo.currentText().strip()
        parentShiftID = self.parent().shift_combo.currentText().strip()
    
        # **Retrieve Destination Location Details**
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
    
        # **Check if the destination worker already has data**
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
    
            cursor.execute('''
                SELECT COUNT(*) FROM WorkerStationShiftErgoTool
                WHERE worker_id=? AND plant_name=? AND section_name=? 
                AND line_name=? AND station_id=? AND shift_id=?
            ''', (destinationWorkerID, plant_name, section_name, line_name, station_id, shift_id))
    
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Transfer Not Allowed", "Tool data already exists for the destination worker at this location.")
                conn.close()
                return

            tools_to_transfer = ["LiFFT", "DUET", "ST"]
    
            for tool_id in tools_to_transfer:
                # **Check if tool data exists for the source worker**
                cursor.execute('''
                    SELECT * FROM WorkerStationShiftErgoTool
                    WHERE worker_id=? AND plant_name=? AND section_name=? 
                    AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
                ''', (parentWorkerID, parentPlantName, parentSectionName, parentLineName, parentStationID, parentShiftID, tool_id))
    
                source_record = cursor.fetchone()
    
                if not source_record:
                    continue  # Skip to the next tool if no data found
    
                # **Ask user if they want to transfer this tool**
                reply = QMessageBox.question(self, f'Transfer {tool_id} Data', 
                                             f"Do you want to transfer {tool_id} data?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    continue  # Skip transfer for this tool
    
                # **Copy WorkerStationShiftErgoTool Entry**
                columns = [desc[0] for desc in cursor.description]  # Extract column names
                values = list(source_record)  # Convert tuple to list
                values[columns.index("worker_id")] = destinationWorkerID  # Change worker ID
                values[columns.index("plant_name")] = plant_name
                values[columns.index("section_name")] = section_name
                values[columns.index("line_name")] = line_name
                values[columns.index("station_id")] = station_id
                values[columns.index("shift_id")] = shift_id
    
                insert_query = f'''
                    INSERT INTO WorkerStationShiftErgoTool ({', '.join(columns)}) 
                    VALUES ({', '.join(['?'] * len(columns))})
                '''
                cursor.execute(insert_query, values)
    
                # **Copy tool-specific results table**
                if tool_id == "LiFFT":
                    cursor.execute('''
                        SELECT * FROM LifftResults
                        WHERE worker_id=? AND plant_name=? AND section_name=? 
                        AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
                    ''', (parentWorkerID, parentPlantName, parentSectionName, parentLineName, parentStationID, parentShiftID, tool_id))
    
                    lifft_records = cursor.fetchall()
    
                    if lifft_records:
                        lifft_columns = [desc[0] for desc in cursor.description]
                        lifft_insert_query = f'''
                            INSERT INTO LifftResults ({', '.join(lifft_columns)}) 
                            VALUES ({', '.join(['?'] * len(lifft_columns))})
                        '''
                        for record in lifft_records:
                            new_values = list(record)
                            new_values[lifft_columns.index("worker_id")] = destinationWorkerID
                            new_values[lifft_columns.index("plant_name")] = plant_name
                            new_values[lifft_columns.index("section_name")] = section_name
                            new_values[lifft_columns.index("line_name")] = line_name
                            new_values[lifft_columns.index("station_id")] = station_id
                            new_values[lifft_columns.index("shift_id")] = shift_id
                            cursor.execute(lifft_insert_query, new_values)

                elif tool_id == "DUET":
                    cursor.execute('''
                        SELECT * FROM DuetResults
                        WHERE worker_id=? AND plant_name=? AND section_name=? 
                        AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
                    ''', (parentWorkerID, parentPlantName, parentSectionName, parentLineName, parentStationID, parentShiftID, tool_id))

                    duet_records = cursor.fetchall()

                    if duet_records:
                        duet_columns = [desc[0] for desc in cursor.description]
                        duet_insert_query = f'''
                            INSERT INTO DuetResults ({', '.join(duet_columns)}) 
                            VALUES ({', '.join(['?'] * len(duet_columns))})
                        '''
                        for record in duet_records:
                            new_values = list(record)
                            new_values[duet_columns.index("worker_id")] = destinationWorkerID
                            new_values[duet_columns.index("plant_name")] = plant_name
                            new_values[duet_columns.index("section_name")] = section_name
                            new_values[duet_columns.index("line_name")] = line_name
                            new_values[duet_columns.index("station_id")] = station_id
                            new_values[duet_columns.index("shift_id")] = shift_id
                            cursor.execute(duet_insert_query, new_values)

                elif tool_id == "ST":
                    cursor.execute('''
                        SELECT * FROM TstResults
                        WHERE worker_id=? AND plant_name=? AND section_name=? 
                        AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
                    ''', (parentWorkerID, parentPlantName, parentSectionName, parentLineName, parentStationID, parentShiftID, tool_id))
    
                    tst_records = cursor.fetchall()
    
                    if tst_records:
                        tst_columns = [desc[0] for desc in cursor.description]
                        tst_insert_query = f'''
                            INSERT INTO TstResults ({', '.join(tst_columns)}) 
                            VALUES ({', '.join(['?'] * len(tst_columns))})
                        '''
                        for record in tst_records:
                            new_values = list(record)
                            new_values[tst_columns.index("worker_id")] = destinationWorkerID
                            new_values[tst_columns.index("plant_name")] = plant_name
                            new_values[tst_columns.index("section_name")] = section_name
                            new_values[tst_columns.index("line_name")] = line_name
                            new_values[tst_columns.index("station_id")] = station_id
                            new_values[tst_columns.index("shift_id")] = shift_id
                            cursor.execute(tst_insert_query, new_values)

                conn.commit()

                # **Delete Source Data if Copy is NOT Checked**
                if not self.copy_data_checkbox.isChecked():
                    cursor.execute("PRAGMA foreign_keys = ON;")
                    cursor.execute('''
                        DELETE FROM WorkerStationShiftErgoTool 
                        WHERE worker_id=? AND plant_name=? AND section_name=? 
                        AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
                    ''', (parentWorkerID, parentPlantName, parentSectionName, 
                          parentLineName, parentStationID, parentShiftID, tool_id))
                    
                    conn.commit()


            conn.close()
            QMessageBox.information(self, "Transfer Successful", "Worker tool data successfully transferred.")
            #self.close()
    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred during transfer:\n{e}")
           
        
        
        

    def checkIfTransferLocationExists(self, worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id):
        """
        Checks if a record already exists in WorkerStationShiftErgoTool for the given worker and new location.
        
        Args:
            worker_id (str): The worker's unique ID.
            plant_name (str): Destination plant name.
            section_name (str): Destination section name.
            line_name (str): Destination line name.
            station_id (str): Destination station ID.
            shift_id (str): Destination shift ID.
            tool_id (str): The tool being transferred (e.g., "LiFFT", "DUET", "ST").
    
        Returns:
            bool: True if a record exists at the destination (transfer **not allowed**), False if safe to proceed.
        """
        try:
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()
            
            # Query to check if a record already exists in the target location
            cursor.execute('''
                SELECT * FROM WorkerStationShiftErgoTool
                WHERE worker_id=? AND plant_name=? AND section_name=? 
                AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
            ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id))
            
            result = cursor.fetchone()  # Expecting at most one row
            conn.close()
    
            # If result is not None, it means a record exists → Transfer **not possible**
            return result is not None

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return True  # Assume failure as a safety measure (preventing transfer)


    
    def getWorkers(self, order_by):
        """
        Retrieves workers from the database in the specified order.
    
        Args:
            order_by (int): 0 for ordering by Worker ID, 1 for ordering by Last Name.
    
        Returns:
            list: A list of strings formatted as <worker id>(<last name>, <first name>).
        """
        # Ensure a project file is created before accessing the database
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
    

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

            # TODO: format only if they have first and last name available
            # Format workers as <worker id>(<last name>, <first name>)
            #return [f"{row[0]} ({row[1]}, {row[2]})" for row in workers]
            
             # Format only if last name and first name are available
            return [
                f"{row[0]} ({row[1]}, {row[2]})" if row[1] and row[2] else str(row[0])
                for row in workers
            ]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve workers:\n{str(e)}")
            return []
    
    
    def loadWorkers(self, order_by):
        # Order workers by id (order_by = 0)
        workers_list = self.getWorkers(order_by)
        # Populate the worker combobox
        
        self.workerComboBox.blockSignals(True)  # Suspend signals
        
        self.workerComboBox.clear()
        self.workerComboBox.addItems(workers_list)
        
        self.workerComboBox.blockSignals(False)  # Suspend signals
        
        
    
    
    
    def getShifts(self):
        """
        Retrieves all shifts from the database.
    
        Returns:
            list: A list of shift IDs.
        """
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
    
        
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
            self.shift_combo.clear()
            self.shift_combo.addItems(shifts_list)
            
            
            
    def getPlants(self):
        """
        Retrieves all plants from the database.

        Returns:
            list: A list of strings formatted as <plant name>(<location>, <type>).
        """
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
    

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
            self.plant_combo.clear()
            self.plant_combo.addItems(plants_list)

    
    
    def getSections(self, plant_name):
        """
        Retrieves all sections for a given plant from the database.

        Args:
            plant_name (str): The name of the plant to filter sections by.

        Returns:
            list: A list of strings.
        """
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
            

        # Ensure a valid plant name is provided
        if not plant_name:
            #QMessageBox.warning(self, "Error", "No plant selected. Unable to retrieve sections.")
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
        plant_name = self.plant_combo.currentText().strip()
        #print("Plant Name:",plant_name)
        
        # Retrieve and populate sections for the selected plant
        sections_list = self.getSections(plant_name)
        if sections_list is not None:
            # Populate the section combo box
            self.section_combo.clear()
            self.section_combo.addItems(sections_list)

    
    
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
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
            
    
        # Ensure valid plant and section names are provided
        if not plant_name or not section_name:
            #QMessageBox.warning(self, "Error", "No plant or section selected. Unable to retrieve lines.")
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
        plant_name = self.plant_combo.currentText()
        section_name = self.section_combo.currentText()
    
        # Retrieve and populate lines for the selected plant and section
        lines_list = self.getLines(plant_name, section_name)
        if lines_list is not None:
            # Populate the line combo box
            self.line_combo.clear()
            self.line_combo.addItems(lines_list)
    
    
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
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []
            
    
        # Ensure valid plant, section, and line names are provided
        if not plant_name or not section_name or not line_name:
            #QMessageBox.warning(self, "Error", "No plant, section, or line selected. Unable to retrieve stations.")
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
        
        # Get the selected plant and section names from the labels in the Line window
        plant_name = self.plant_combo.currentText()
        section_name = self.section_combo.currentText()
        line_name = self.line_combo.currentText()
    
        # Retrieve and populate stations for the selected plant, section, and line
        stations_list = self.getStations(plant_name, section_name, line_name)
        
        #self.station_combo.blockSignals(True)  # Suspend signals
        if stations_list is not None:
            # Populate the station combo box
            self.station_combo.clear()
            self.station_combo.addItems(stations_list)
        
        #self.station_combo.blockSignals(False)  # Suspend signals



    def searchWorkerClicked(self):
        # Check if a project has been created from the parent window
        if not self.parent().projectFileCreated or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return 
        
        if not self.parent() or not hasattr(self.parent(), 'projectdatabasePath') or not self.parent().projectdatabasePath:
            #QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return 


        
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
            first_name = ""
            last_name = ""
            formatted_worker = ""
            
            conn = sqlite3.connect(self.parent().projectdatabasePath)
            cursor = conn.cursor()

            try:
                # Search by ID if provided
                if id_input.text().strip():
                    cursor.execute("SELECT id, first_name, last_name FROM Worker WHERE id = ?", (id_input.text().strip(),))
                    result = cursor.fetchone()
                    if result:
                        worker_id = result[0]
                        first_name = result[1]
                        last_name = result[2]

                    if first_name and last_name:
                        formatted_worker = f"{worker_id} ({last_name}, {first_name})"
                    else:
                        formatted_worker = worker_id

                        
                    
                    #formatted_worker = worker_id   
                    #formatted_worker = f"{worker_id} ({last_name}, {first_name})"
                else:
                    # Search by First Name and Last Name if ID is not provided
                    first_name = first_name_input.text().strip()
                    last_name = last_name_input.text().strip()
                    if first_name and last_name:
                        cursor.execute("SELECT id, first_name, last_name FROM Worker WHERE first_name = ? AND last_name = ?", (first_name, last_name))
                        result = cursor.fetchone()
                        if result:
                            worker_id = result[0]
                            first_name = result[1]
                            last_name = result[2]
                            
                            # Format the text as ID (Lastname, Firstname)
                            formatted_worker = f"{worker_id} ({last_name}, {first_name})"

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to search worker:\n{str(e)}")
            finally:
                conn.close()

            if formatted_worker:
                # Set the worker ID in the combo box and trigger the index change event
                index = self.workerComboBox.findText(formatted_worker)
                if index != -1:
                    self.workerComboBox.setCurrentIndex(index)
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

    
    # Handlers for the buttons
    def orderButtonClicked(self):
        self.setWorkerOrder()    
        
    
    def setWorkerOrder(self):
        #print("Is Numbered Order:", self.isNumberOrder)
        if not self.isNumberOrder:
            self.orderButton.setIcon(QIcon("../images/numberorder01.png"))
            self.loadWorkers(1)
        else:
            self.orderButton.setIcon(QIcon("../images/alphaorder01.png"))
            self.loadWorkers(0)
    
        self.isNumberOrder = not self.isNumberOrder  # Toggle the state


