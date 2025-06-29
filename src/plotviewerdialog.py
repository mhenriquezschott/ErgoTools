import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
                             QPushButton, QFrame, QGraphicsView, QGraphicsScene, QToolButton, QCheckBox, QGroupBox, QGridLayout, QStatusBar, QGraphicsPixmapItem, QMenu, QAction, QSpinBox, QGraphicsRectItem, QFileDialog)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QCursor, QPen, QIcon, QBrush, QColor, QPolygonF, QFont, QPainter, QFontMetrics, QTransform, QImage
from PyQt5.QtCore import Qt, QDate, QSize, QPointF, QRectF, QTimer
from PyQt5.QtWidgets import QWidget, QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem, QFileDialog, QGraphicsItem, QGraphicsPolygonItem, QGraphicsScene, QGraphicsPixmapItem
from PyQt5 import QtWidgets, QtCore 


from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


class PlotViewerDialog(QDialog):
    def __init__(self, fig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Expanded Plot View")
        self.setFixedSize(900, 650)  # Increased height to fit the toolbar

        self.fig = fig  # Store the Matplotlib figure

        # **Main Layout**
        layout = QVBoxLayout(self)

        # **Embed Figure in Dialog**
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)  # Add interactive toolbar

        layout.addWidget(self.toolbar)  # Add toolbar for zoom/pan
        layout.addWidget(self.canvas)  # Add canvas for displaying the plot

        # **Save Button**
        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self.savePlot)
        layout.addWidget(self.save_button)

    def savePlot(self):
        """Open file dialog to save the plot as an image."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)", options=options
        )
        if file_name:
            self.fig.savefig(file_name, dpi=300, bbox_inches='tight')  # Save at high resolution


class PlotViewerDialogW(QDialog):
    def __init__(self, fig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Expanded Plot View")
        self.setFixedSize(800, 600)  # Fixed size

        self.fig = fig  # Store figure reference

        # **Main Layout**
        layout = QVBoxLayout(self)

        # **Graphics View for Plot**
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setFixedSize(780, 500)  # Fixed size for plot display
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # **Convert Matplotlib Figure to QPixmap and Display**
        #self.updatePlotDisplay()

        # **Save Button**
        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self.savePlot)

        # **Add Widgets to Layout**
        layout.addWidget(self.graphics_view)
        layout.addWidget(self.save_button)
        
        QTimer.singleShot(0, self.updatePlotDisplay)
        

    def updatePlotDisplay(self):
        """Convert the Matplotlib figure to a QPixmap and update the QGraphicsView."""
        canvas = FigureCanvas(self.fig)
        canvas.draw()

        width, height = canvas.get_width_height()
        image = QImage(canvas.buffer_rgba(), width, height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)

        # **Clear previous items and add new pixmap**
        self.scene.clear()
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)

        # **Center the image in the QGraphicsView**
        self.scene.setSceneRect(0, 0, width, height)
        self.graphics_view.setRenderHint(QPainter.Antialiasing)  # Smooth rendering
        
        self.graphics_view.fitInView(pixmap_item, Qt.KeepAspectRatio)
        self.graphics_view.setAlignment(Qt.AlignCenter)

    def savePlot(self):
        """Open file dialog to save the plot as an image."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)", options=options)
        if file_name:
            self.fig.savefig(file_name, dpi=300, bbox_inches='tight')  # Save at high resolution

