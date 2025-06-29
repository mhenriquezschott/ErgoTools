import sys
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
                             QPushButton, QFrame, QGraphicsView, QGraphicsScene, QToolButton, QCheckBox, QGroupBox, QGridLayout, QStatusBar, QGraphicsPixmapItem, QMenu, QAction, QSpinBox, QGraphicsRectItem)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QCursor, QPen, QIcon, QBrush, QColor, QPolygonF, QFont, QPainter, QFontMetrics
from PyQt5.QtCore import Qt, QDate, QSize, QPointF, QRectF, pyqtSignal
from PyQt5.QtWidgets import QWidget, QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItem, QGraphicsPolygonItem

import random



class MultiSelectComboBox(QComboBox):

    itemCheckStateChanged = pyqtSignal() 
    def __init__(self, parent=None):
        super(MultiSelectComboBox, self).__init__(parent)
        self.setModel(QStandardItemModel(self))
        #self.view().pressed.connect(self.handleItemPressed)  # Keep 'pressed' for proper behavior
        self.view().clicked.connect(self.handleItemPressed)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setAlignment(Qt.AlignLeft)

    def handleItemPressed(self, index):
        """Handles item selection logic, including 'All' selection behavior."""
        item = self.model().itemFromIndex(index)
        if not item:
            return

        item_text = item.text()

        # **Manually Toggle Check State (Fixes Checkbox Click Issue)**
        new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        item.setCheckState(new_state)

        # **Handle "All" Selection Behavior**
        if item_text == "All":
            for i in range(self.count()):
                self.model().item(i).setCheckState(new_state)

        # **Ensure "All" is selected if all other items are checked**
        elif item_text != "All":
            all_selected = all(
                self.model().item(i).checkState() == Qt.Checked
                for i in range(1, self.count())  # Skip "All" index (assumed at 0)
            )
            self.model().item(0).setCheckState(Qt.Checked if all_selected else Qt.Unchecked)

        self.updateText()  # Update displayed text
        self.itemCheckStateChanged.emit()  # **Emit the signal when an item is checked/unchecked**
        

    def updateText(self):
        """Updates the display text based on selected items."""
        selected_items = [
            self.itemText(i) for i in range(self.count())
            if self.model().item(i).checkState() == Qt.Checked and self.itemText(i) != "All"
        ]
        #print("selected_items", selected_items)
        # **Show 'All' if all items are selected**
        if len(selected_items) == self.count() - 1:  # All except "All"
            self.lineEdit().setText("All")
        else:
            self.lineEdit().setText(", ".join(selected_items))

        # **Force UI Refresh**
        self.lineEdit().update()  # Ensure UI reflects changes

    def addSelectableItem(self, text):
        """Adds a single selectable item to the combo box."""
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addSelectableItems(self, items):
        """Adds multiple selectable items to the combo box."""
        for text in items:
            self.addSelectableItem(text)


