from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QMessageBox, QScrollArea, QWidget
)

class ToolDataDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Tool Data Selection")
        self.resize(800, 400)  # Adjust width to fit content properly

        self.selected_row_data = None  # Store selected row data

        # **Main Layout**
        main_layout = QVBoxLayout(self)

        # **Scrollable Area for the Table**
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        container_widget = QWidget()
        table_layout = QVBoxLayout(container_widget)

        # **Table Widget**
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(6)  # Plant, Section, Line, Station, Shift, Tool
        self.tableWidget.setHorizontalHeaderLabels(["Plant", "Section", "Line", "Station", "Shift", "Tool"])
        self.tableWidget.setSelectionBehavior(QTableWidget.SelectRows)  # Select full rows
        self.tableWidget.setSelectionMode(QTableWidget.SingleSelection)  # One row at a time
        self.tableWidget.setSortingEnabled(True)  # Enable sorting

        # Enable horizontal scrolling for wide tables
        self.tableWidget.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.tableWidget.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        
        

        table_layout.addWidget(self.tableWidget)
        scroll_area.setWidget(container_widget)
        main_layout.addWidget(scroll_area)

        # **Populate Table with Data**
        if data:
            self.loadData(data)

        # **Buttons Layout (Close left, Load right)**
        button_layout = QHBoxLayout()
        self.closeButton = QPushButton("Close")
        self.loadButton = QPushButton("Load")
        
        button_layout.addWidget(self.closeButton)
        button_layout.addStretch()  # Pushes the "Load" button to the right
        button_layout.addWidget(self.loadButton)

        self.closeButton.clicked.connect(self.reject)  # Closes the dialog
        self.loadButton.clicked.connect(self.loadSelectedRow)  # Loads selected row data
        
        self.tableWidget.doubleClicked.connect(self.loadSelectedRow)

        main_layout.addLayout(button_layout)
        
        

    def loadData(self, data):
        """Populate the table with data from the database."""
        self.tableWidget.setRowCount(len(data))
    
        keys = ["plant_name", "section_name", "line_name", "station_id", "shift_id", "tool_id"]  # Column mapping
    
        for row_idx, row_data in enumerate(data):
            for col_idx, key in enumerate(keys):  # Use enumerate() for indexing
                item = QTableWidgetItem(str(row_data[key]))
                self.tableWidget.setItem(row_idx, col_idx, item)

        # Adjust column widths to fit content
        self.tableWidget.resizeColumnsToContents()

    def loadSelectedRow(self):
        """Store selected row data internally and close the dialog."""
        selected_row = self.tableWidget.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Selection Error", "Please select a row before proceeding.")
            return
        
        self.selected_row_data = {
            "plant_name": self.tableWidget.item(selected_row, 0).text(),
            "section_name": self.tableWidget.item(selected_row, 1).text(),
            "line_name": self.tableWidget.item(selected_row, 2).text(),
            "station_id": self.tableWidget.item(selected_row, 3).text(),
            "shift_id": self.tableWidget.item(selected_row, 4).text(),
            "tool_id": self.tableWidget.item(selected_row, 5).text(),
        }
        
        self.accept()  # Close the dialog

