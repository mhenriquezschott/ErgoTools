
import sys
import vtk
import sqlite3
import datetime
import os
import subprocess
import csv
import shutil
import argparse
import random
import xml.etree.ElementTree as ET
from vtk.util.numpy_support import numpy_to_vtk
import numpy as np
from PyQt5 import QtWidgets, QtCore 
from PyQt5.QtCore import Qt, QTimer, QLocale, QTime, QDate, QStandardPaths, QSize, QPointF, QRectF, QEasingCurve, QPropertyAnimation
from PyQt5.QtGui import QColor, QIntValidator, QDoubleValidator, QFont, QPainter, QPen, QPixmap, QIcon, QPolygonF, QPalette
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, QLineEdit,
                             QFrame, QWidget, QComboBox, QDateTimeEdit, QMessageBox, QAction, QDialog, QFileDialog, QInputDialog, QSpinBox, 	 
                             QTextEdit, QDialogButtonBox, QActionGroup, QProgressBar, QScrollArea, QToolBar, QSpacerItem, QSizePolicy, QStyle,
                             QTreeWidget, QTreeWidgetItem, QStyledItemDelegate, QStyleOptionViewItem,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QButtonGroup)
import math

import inspect

from pyLiFFT import LiFFT
from pyDUET import DUET
from pyTST import TST
from plant_layout import PlantLayoutWindow  # Import the Plant Layout window
from worker_window import WorkerWindow
from plant_window import PlantWindow
from section_window import SectionWindow
from line_window import LineWindow
from station_window import StationWindow
from shift_window import ShiftWindow
from organization_window import OrganizationWindow
from vtk_camera_director import VTKCameraDirector
from risk_ranges import RISK_BANDS, risk_band

from tooltransferdialog import ToolTransferDialog
from worker_transfer_window import WorkerTransferDialog
from tooldatadialog import ToolDataDialog


class VTKDisabledWidget(QtWidgets.QFrame):
    """Headless UI-review stand-in for QVTKRenderWindowInteractor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setMinimumSize(220, 420)

    def GetRenderWindow(self):
        return self

    def Render(self):
        pass


class VTKDisabledActor:
    """No-op actor used by the VTK-disabled project-data path."""

    def GetProperty(self):
        return self

    def SetColor(self, *args):
        pass

    def VisibilityOn(self):
        pass

    def VisibilityOff(self):
        pass


class RiskGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._display_value = 0.0
        self.target_value = 0.0
        self.outcome_text = "Probability of outcome"
        self.risk_color = QColor("#9EB0BE")
        self.animation = QPropertyAnimation(self, b"displayValue", self)
        self.animation.setDuration(750)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.setMinimumWidth(190)
        self.setFixedHeight(167)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    @QtCore.pyqtProperty(float)
    def displayValue(self):
        return self._display_value

    @displayValue.setter
    def displayValue(self, value):
        self._display_value = float(value)
        self.update()

    def setValue(self, value, color=None):
        value = min(100.0, max(0.0, float(value)))
        if color and color.lower() not in ("none", "transparent"):
            candidate = QColor(color)
            if candidate.isValid():
                self.risk_color = candidate
        if abs(value - self.target_value) < 0.001:
            return
        self.target_value = value
        self.animation.stop()
        self.animation.setStartValue(self._display_value)
        self.animation.setEndValue(value)
        self.animation.start()

    def setOutcomeText(self, text):
        if text != self.outcome_text:
            self.outcome_text = text
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = QPointF(self.width() / 2.0, 94.0)
        radius = min(self.width() / 2.0 - 16.0, 70.0)
        arc_rect = QRectF(center.x() - radius, center.y() - radius, radius * 2.0, radius * 2.0)
        for start, end, _label, color, _range_text in RISK_BANDS:
            pen = QPen(QColor(color), 13, Qt.SolidLine, Qt.FlatCap)
            painter.setPen(pen)
            painter.drawArc(arc_rect, int((180 - start * 1.8) * 16), -int((end - start) * 1.8 * 16))

        angle = math.radians(180.0 - self._display_value * 1.8)
        tip = QPointF(center.x() + math.cos(angle) * (radius - 9), center.y() - math.sin(angle) * (radius - 9))
        perpendicular = QPointF(math.sin(angle) * 4.6, math.cos(angle) * 4.6)
        needle = QPolygonF([center + perpendicular, tip, center - perpendicular])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#87949D"))
        painter.drawPolygon(needle)
        painter.setBrush(QColor("#6F7E88"))
        painter.drawEllipse(center, 5.0, 5.0)

        painter.setPen(QColor("#0B326C"))
        font = painter.font()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 70, self.width(), 34), Qt.AlignCenter, f"{self._display_value:.1f}%")

        caption_font = painter.font()
        caption_font.setPointSize(9)
        caption_font.setBold(True)
        painter.setFont(caption_font)
        painter.setPen(QColor("#304652"))
        painter.drawText(
            QRectF(4, 126, self.width() - 8, 36),
            Qt.AlignHCenter | Qt.AlignTop,
            self.outcome_text,
        )


class DamageScale(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._display_value = 0.0
        self.target_value = 0.0
        self.fill_color = QColor("#F97316")
        self.animation = QPropertyAnimation(self, b"displayValue", self)
        self.animation.setDuration(700)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.setMinimumHeight(38)

    @QtCore.pyqtProperty(float)
    def displayValue(self):
        return self._display_value

    @displayValue.setter
    def displayValue(self, value):
        self._display_value = float(value)
        self.update()

    def setValue(self, value, color=None):
        value = min(2.0, max(0.0, float(value)))
        if color:
            candidate = QColor(color)
            if candidate.isValid():
                self.fill_color = candidate
        if abs(value - self.target_value) < 0.0001:
            self.update()
            return
        self.target_value = value
        self.animation.stop()
        self.animation.setStartValue(self._display_value)
        self.animation.setEndValue(value)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        left, right, y = 3.0, self.width() - 3.0, 11.0
        painter.setPen(QPen(QColor("#D9DEE2"), 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(left, y), QPointF(right, y))
        progress_x = left + (right - left) * self._display_value / 2.0
        if progress_x > left:
            progress_x = max(progress_x, left + 4.0)
            painter.setPen(QPen(self.fill_color, 8, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(left, y), QPointF(progress_x, y))
        painter.setPen(QColor("#506273"))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(QRectF(0, 22, 34, 14), Qt.AlignLeft | Qt.AlignVCenter, "0")
        painter.drawText(QRectF(self.width() / 2 - 18, 22, 36, 14), Qt.AlignCenter, "1")
        painter.drawText(QRectF(self.width() - 42, 22, 42, 14), Qt.AlignRight | Qt.AlignVCenter, ">2")


class ErgoComboItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        styled_option = QStyleOptionViewItem(option)
        if styled_option.state & QStyle.State_Selected:
            styled_option.palette.setColor(QPalette.Highlight, QColor("#087E91"))
            styled_option.palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
            painter.fillRect(styled_option.rect, QColor("#087E91"))
        super().paint(painter, styled_option, index)


class AssessmentWorkplaceDialog(QDialog):
    """Select an existing station path and shift for the assessment context."""

    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.selected_path = None
        self.setObjectName("assessmentWorkplaceDialog")
        self.setWindowTitle("Assessment Workplace")
        self.setMinimumSize(560, 540)
        self.setStyleSheet(parent.mainWorkspaceStyleSheet() + """
            QDialog#assessmentWorkplaceDialog { background: #F4F7F9; color: #1B2933; }
            QDialog#assessmentWorkplaceDialog QTreeWidget {
                background: white; color: #1B2933; border: 1px solid #BCC9D3;
                border-radius: 5px; alternate-background-color: #F7FAFB;
            }
            QDialog#assessmentWorkplaceDialog QTreeWidget::item { min-height: 29px; padding: 2px 5px; }
            QDialog#assessmentWorkplaceDialog QTreeWidget::item:selected {
                background: #087E91; color: white;
            }
            QDialog#assessmentWorkplaceDialog QHeaderView::section {
                background: #EAF2F6; color: #0B326C; border: 0;
                border-bottom: 1px solid #BCC9D3; padding: 7px; font-weight: 700;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("Assessment workplace")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        description = QLabel("Select the station where this assessment applies, then choose its work shift.")
        description.setObjectName("supportingText")
        description.setWordWrap(True)
        layout.addWidget(description)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Workplace hierarchy", "Type"])
        self.tree.setColumnWidth(0, 390)
        self.tree.setToolTip("Expand the hierarchy and select a station for this assessment.")
        self.tree.currentItemChanged.connect(self.updateSelection)
        self.tree.itemDoubleClicked.connect(lambda *_: self.acceptSelection())
        layout.addWidget(self.tree, 1)
        shift_row = QHBoxLayout()
        shift_label = QLabel("Shift")
        shift_label.setObjectName("contextLabel")
        self.shift_combo = QComboBox()
        self.shift_combo.setToolTip("Select the shift associated with this assessment.")
        shift_row.addWidget(shift_label)
        shift_row.addWidget(self.shift_combo, 1)
        layout.addLayout(shift_row)
        self.path_label = QLabel("Select a station from the hierarchy.")
        self.path_label.setObjectName("contextSummary")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.accept_button = buttons.button(QDialogButtonBox.Ok)
        self.accept_button.setText("Use workplace")
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        self.accept_button.setIcon(QIcon(os.path.join(icon_root, "station.png")))
        self.accept_button.setIconSize(QSize(24, 24))
        self.accept_button.setObjectName("primaryOutlineButton")
        self.accept_button.setEnabled(False)
        buttons.button(QDialogButtonBox.Cancel).setIcon(QIcon(os.path.join(icon_root, "cancel.png")))
        buttons.button(QDialogButtonBox.Cancel).setIconSize(QSize(22, 22))
        buttons.accepted.connect(self.acceptSelection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.populate()

    def populate(self):
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        current = tuple(combo.currentText() for combo in (
            self.main_window.plant_combo, self.main_window.section_combo,
            self.main_window.line_combo, self.main_window.station_combo,
        ))
        current_item = None
        database = self.main_window.projectdatabasePath
        if database and os.path.exists(database):
            with sqlite3.connect(database) as conn:
                for (plant,) in conn.execute("SELECT name FROM Plant ORDER BY name"):
                    plant_item = self.addItem(None, plant, "Plant", (plant,), icon_root)
                    for (section,) in conn.execute(
                        "SELECT name FROM Section WHERE plant_name=? ORDER BY name", (plant,)
                    ):
                        section_item = self.addItem(plant_item, section, "Section", (plant, section), icon_root)
                        for (line,) in conn.execute(
                            "SELECT name FROM Line WHERE plant_name=? AND section_name=? ORDER BY name",
                            (plant, section),
                        ):
                            line_item = self.addItem(section_item, line, "Line", (plant, section, line), icon_root)
                            for (station,) in conn.execute(
                                "SELECT id FROM Station WHERE plant_name=? AND section_name=? AND line_name=? ORDER BY id",
                                (plant, section, line),
                            ):
                                station_item = self.addItem(
                                    line_item, station, "Station", (plant, section, line, station), icon_root
                                )
                                if station_item.data(0, Qt.UserRole) == current:
                                    current_item = station_item
                self.shift_combo.addItems([str(row[0]) for row in conn.execute("SELECT id FROM Shift ORDER BY id")])
        if not self.shift_combo.count():
            self.shift_combo.addItem(self.main_window.shift_combo.currentText() or "1")
        self.shift_combo.setCurrentText(self.main_window.shift_combo.currentText())
        self.tree.collapseAll()
        if current_item:
            ancestor = current_item.parent()
            while ancestor:
                ancestor.setExpanded(True)
                ancestor = ancestor.parent()
            self.tree.setCurrentItem(current_item)
            self.tree.scrollToItem(current_item)

    def addItem(self, parent, text, entity, path, icon_root):
        item = QTreeWidgetItem([str(text), entity])
        item.setData(0, Qt.UserRole, tuple(str(value) for value in path))
        item.setIcon(0, QIcon(os.path.join(icon_root, entity.lower() + ".png")))
        item.setToolTip(0, f"{entity}: {text}")
        (self.tree.addTopLevelItem if parent is None else parent.addChild)(item)
        return item

    def updateSelection(self, current, previous=None):
        is_station = bool(current and current.text(1) == "Station")
        self.accept_button.setEnabled(is_station)
        self.selected_path = current.data(0, Qt.UserRole) if is_station else None
        self.path_label.setText(
            "  >  ".join(self.selected_path) if self.selected_path else "Select a station from the hierarchy."
        )

    def acceptSelection(self):
        if not self.selected_path:
            QMessageBox.information(self, "Select a station", "Select a Station before continuing.")
            return
        self.accept()


class WorkerSearchDialog(QDialog):
    """Live worker directory filtered by surname and assessment workplace."""

    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.selected_worker_id = None
        self.active_letter = None
        self.active_workplace = ()
        self.worker_rows = []
        self.worker_contexts = {}
        self.alphabet_buttons = {}
        self.icon_root = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..", "assets", "ui-icons"
        ))
        self.setObjectName("workerSearchDialog")
        self.setWindowTitle("Find Worker")
        self.resize(1080, 650)
        self.setMinimumSize(900, 560)
        self.setStyleSheet(parent.mainWorkspaceStyleSheet() + """
            QDialog#workerSearchDialog { background: #F4F7F9; color: #1B2933; }
            QFrame#searchPanel { background: white; border: 1px solid #D5DEE5; border-radius: 7px; }
            QLabel#sectionTitle { color: #0B326C; font-size: 14px; font-weight: 700; }
            QLabel#resultCount { color: #405462; font-weight: 600; }
            QTreeWidget, QTableWidget {
                background: white; color: #1B2933; border: 1px solid #BCC9D3;
                border-radius: 5px; alternate-background-color: #F7FAFB; gridline-color: #E3E9ED;
            }
            QTreeWidget::item { min-height: 30px; padding: 2px 5px; }
            QTreeWidget::item:selected, QTableWidget::item:selected { background: #087E91; color: white; }
            QHeaderView::section {
                background: #EAF2F6; color: #0B326C; border: 0;
                border-bottom: 1px solid #BCC9D3; padding: 8px 6px; font-weight: 700;
            }
            QPushButton#alphabetButton {
                min-width: 22px; max-width: 22px; min-height: 30px; max-height: 30px;
                padding: 0; border: 0; background: transparent; color: #5F6F7A;
                font-size: 11px; font-weight: 650;
            }
            QPushButton#alphabetButton:hover { background: #DDF3F5; color: #0B326C; font-size: 17px; }
            QPushButton#alphabetButton:checked { background: #0B326C; color: white; border-radius: 4px; font-size: 12px; }
            QPushButton#alphabetButton:disabled { color: #C7D0D7; }
        """)
        self.buildUi()
        self.loadData()

    def buildUi(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)
        title = QLabel("Find a worker")
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        subtitle = QLabel(
            "Search by worker ID or name, then narrow the directory by last-name initial or assessment workplace."
        )
        subtitle.setObjectName("supportingText")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        content = QHBoxLayout()
        content.setSpacing(12)
        workplace_panel = QFrame()
        workplace_panel.setObjectName("searchPanel")
        workplace_panel.setFixedWidth(360)
        workplace_layout = QVBoxLayout(workplace_panel)
        workplace_layout.setContentsMargins(12, 12, 12, 12)
        workplace_title = QLabel("Assessment workplace")
        workplace_title.setObjectName("sectionTitle")
        workplace_title.setToolTip(
            "Filter workers by workplaces where they already have saved assessment data."
        )
        workplace_layout.addWidget(workplace_title)
        workplace_help = QLabel("Select any level to include all workplaces below it.")
        workplace_help.setObjectName("supportingText")
        workplace_help.setWordWrap(True)
        workplace_layout.addWidget(workplace_help)
        self.workplace_tree = QTreeWidget()
        self.workplace_tree.setHeaderLabels(["Workplace hierarchy", "Type"])
        self.workplace_tree.header().setSectionResizeMode(0, QHeaderView.Fixed)
        self.workplace_tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.workplace_tree.setColumnWidth(0, 245)
        self.workplace_tree.setColumnWidth(1, 82)
        self.workplace_tree.setAlternatingRowColors(True)
        self.workplace_tree.setToolTip(
            "Choose All workplaces, or expand the hierarchy to filter workers with assessments in that location."
        )
        self.workplace_tree.currentItemChanged.connect(self.workplaceChanged)
        workplace_layout.addWidget(self.workplace_tree, 1)
        content.addWidget(workplace_panel)

        directory_panel = QFrame()
        directory_panel.setObjectName("searchPanel")
        directory_layout = QVBoxLayout(directory_panel)
        directory_layout.setContentsMargins(12, 12, 12, 12)
        directory_layout.setSpacing(8)
        search_row = QHBoxLayout()
        directory_title = QLabel("Worker directory")
        directory_title.setObjectName("sectionTitle")
        search_row.addWidget(directory_title)
        search_row.addStretch(1)
        self.result_count = QLabel()
        self.result_count.setObjectName("resultCount")
        search_row.addWidget(self.result_count)
        directory_layout.addLayout(search_row)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search worker ID, first name, or last name")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(QIcon(os.path.join(self.icon_root, "search.png")), QLineEdit.LeadingPosition)
        self.search_input.setToolTip("Results update as you type. Partial names and IDs are supported.")
        self.search_input.textChanged.connect(self.applyFilters)
        directory_layout.addWidget(self.search_input)

        alphabet_row = QHBoxLayout()
        alphabet_row.setSpacing(1)
        alphabet_label = QLabel("Last name")
        alphabet_label.setObjectName("supportingText")
        alphabet_label.setToolTip("Filter workers by the first letter of their last name.")
        alphabet_row.addWidget(alphabet_label)
        alphabet_row.addSpacing(5)
        self.alphabet_group = QButtonGroup(self)
        self.alphabet_group.setExclusive(True)
        for value in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(value)
            button.setObjectName("alphabetButton")
            button.setCheckable(True)
            button.setChecked(value == "All")
            button.setToolTip("Show every last name" if value == "All" else f"Show last names beginning with {value}")
            button.clicked.connect(lambda checked, letter=value: self.setAlphabet(letter))
            self.alphabet_group.addButton(button)
            self.alphabet_buttons[value] = button
            alphabet_row.addWidget(button)
        alphabet_row.addStretch(1)
        directory_layout.addLayout(alphabet_row)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Worker ID", "Last name", "First name", "Sex", "Age", "Workplace"
        ])
        self.table.horizontalHeaderItem(5).setToolTip(
            "Workplaces where the worker has saved assessment data."
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(35)
        header = self.table.horizontalHeader()
        section_widths = (105, 108, 108, 74, 50)
        for column, width in enumerate(section_widths):
            header.setSectionResizeMode(column, QHeaderView.Fixed)
            self.table.setColumnWidth(column, width)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSortIndicator(1, Qt.AscendingOrder)
        self.table.setToolTip("Select a worker, then choose Use worker. Double-clicking also selects the worker.")
        self.table.itemSelectionChanged.connect(self.selectionChanged)
        self.table.itemDoubleClicked.connect(lambda *_: self.acceptSelection())
        directory_layout.addWidget(self.table, 1)
        content.addWidget(directory_panel, 1)
        root.addLayout(content, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        cancel_button.setIcon(QIcon(os.path.join(self.icon_root, "cancel.png")))
        cancel_button.setIconSize(QSize(22, 22))
        cancel_button.setToolTip("Close without changing the selected worker.")
        self.use_button = buttons.button(QDialogButtonBox.Ok)
        self.use_button.setText("Use worker")
        self.use_button.setObjectName("primaryOutlineButton")
        self.use_button.setIcon(QIcon(os.path.join(self.icon_root, "worker.png")))
        self.use_button.setIconSize(QSize(24, 24))
        self.use_button.setToolTip("Show the selected worker in the main assessment workspace.")
        self.use_button.setEnabled(False)
        buttons.accepted.connect(self.acceptSelection)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def loadData(self):
        current_year = QDate.currentDate().year()
        with sqlite3.connect(self.main_window.projectdatabasePath) as conn:
            workers = conn.execute(
                """SELECT id, last_name, first_name, gender, year_of_birth
                   FROM Worker ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE, id"""
            ).fetchall()
            contexts = conn.execute(
                """SELECT DISTINCT worker_id, plant_name, section_name, line_name, station_id
                   FROM WorkerStationShiftErgoTool"""
            ).fetchall()
            for worker_id, plant, section, line, station in contexts:
                self.worker_contexts.setdefault(str(worker_id), set()).add(tuple(
                    str(value) for value in (plant, section, line, station)
                ))
            self.populateWorkplaceTree(conn)
        self.worker_rows = []
        for worker_id, last_name, first_name, gender, year_of_birth in workers:
            try:
                age = str(max(0, current_year - int(year_of_birth))) if year_of_birth else "-"
            except (TypeError, ValueError):
                age = "-"
            self.worker_rows.append((
                str(worker_id), last_name or "", first_name or "", gender or "-", age
            ))
        available = {row[1][0].upper() for row in self.worker_rows if row[1] and row[1][0].isalpha()}
        for letter, button in self.alphabet_buttons.items():
            button.setEnabled(letter == "All" or letter in available)
        self.applyFilters()

    def populateWorkplaceTree(self, conn):
        all_item = QTreeWidgetItem(["All workplaces", "All"])
        all_item.setData(0, Qt.UserRole, ())
        all_item.setIcon(0, QIcon(os.path.join(self.icon_root, "plant.png")))
        self.workplace_tree.addTopLevelItem(all_item)
        for (plant,) in conn.execute("SELECT name FROM Plant ORDER BY name COLLATE NOCASE"):
            plant_item = self.addWorkplaceItem(None, plant, "Plant", (plant,))
            for (section,) in conn.execute(
                "SELECT name FROM Section WHERE plant_name=? ORDER BY name COLLATE NOCASE", (plant,)
            ):
                section_item = self.addWorkplaceItem(plant_item, section, "Section", (plant, section))
                for (line,) in conn.execute(
                    """SELECT name FROM Line WHERE plant_name=? AND section_name=?
                       ORDER BY name COLLATE NOCASE""", (plant, section)
                ):
                    line_item = self.addWorkplaceItem(section_item, line, "Line", (plant, section, line))
                    for (station,) in conn.execute(
                        """SELECT id FROM Station WHERE plant_name=? AND section_name=? AND line_name=?
                           ORDER BY id COLLATE NOCASE""", (plant, section, line)
                    ):
                        self.addWorkplaceItem(
                            line_item, station, "Station", (plant, section, line, station)
                        )
        self.workplace_tree.collapseAll()
        self.workplace_tree.setCurrentItem(all_item)

    def addWorkplaceItem(self, parent, text, entity, path):
        item = QTreeWidgetItem([str(text), entity])
        item.setData(0, Qt.UserRole, tuple(str(value) for value in path))
        item.setIcon(0, QIcon(os.path.join(self.icon_root, entity.lower() + ".png")))
        item.setToolTip(0, f"Filter by {entity.lower()}: {text}")
        (self.workplace_tree.addTopLevelItem if parent is None else parent.addChild)(item)
        return item

    def setAlphabet(self, letter):
        self.active_letter = None if letter == "All" else letter
        self.applyFilters()

    def workplaceChanged(self, item, previous=None):
        self.active_workplace = tuple(item.data(0, Qt.UserRole) or ()) if item else ()
        self.applyFilters()

    def applyFilters(self, *args):
        query = self.search_input.text().strip().casefold()
        filtered = []
        for row in self.worker_rows:
            worker_id, last_name, first_name, gender, age = row
            if query and query not in " ".join((worker_id, first_name, last_name)).casefold():
                continue
            if self.active_letter and not last_name.upper().startswith(self.active_letter):
                continue
            contexts = self.worker_contexts.get(worker_id, set())
            if self.active_workplace and not any(
                context[:len(self.active_workplace)] == self.active_workplace for context in contexts
            ):
                continue
            filtered.append(row)
        self.renderRows(filtered)

    def renderRows(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for row_index, (worker_id, last_name, first_name, gender, age) in enumerate(rows):
            contexts = sorted(self.worker_contexts.get(worker_id, set()))
            workplace = "; ".join(" > ".join(path) for path in contexts) if contexts else "No saved assessment workplace"
            values = (worker_id, last_name or "-", first_name or "-", gender, age, workplace)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.UserRole, worker_id)
                item.setToolTip(value)
                self.table.setItem(row_index, column, item)
        self.table.setSortingEnabled(True)
        self.table.sortItems(1, Qt.AscendingOrder)
        self.table.clearSelection()
        self.selected_worker_id = None
        self.use_button.setEnabled(False)
        count = len(rows)
        self.result_count.setText(f"{count} worker{'s' if count != 1 else ''}")

    def selectionChanged(self):
        selected = self.table.selectionModel().selectedRows()
        self.selected_worker_id = self.table.item(selected[0].row(), 0).data(Qt.UserRole) if selected else None
        self.use_button.setEnabled(bool(self.selected_worker_id))

    def acceptSelection(self):
        if self.selected_worker_id:
            self.accept()


class SyncedHeaderLayout(QGridLayout):
    """Sticky header whose column widths are synchronized to the task grid."""

    def __init__(self):
        super().__init__()
        self.next_column = 0

    def addSpacing(self, size):
        return

    def addWidget(self, widget, *args):
        if args:
            return super().addWidget(widget, *args)
        super().addWidget(widget, 0, self.next_column)
        self.next_column += 1


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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.lifft_tab), QtWidgets.QApplication.translate("App", "Lifting Fatigue Failure Tool (LiFFT)  "))
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
    
        
    def __init__(self, parent=None, disable_vtk=False):
        super(ErgoTools, self).__init__(parent)
        self.vtk_enabled = not disable_vtk
        
        self.databasePath = "../data/ergotools_data.db"
        #self.setupDatabase()
        self.isAnimationAllowed = False
        
        self.default_num_task = 15
        self.default_metric_sys = "Imperial"   
        self.num_task = self.default_num_task
        
        self.num_task_lift = self.num_task
        self.num_task_duet = self.num_task
        self.num_task_tst = self.num_task
        
       
        self.lifft_header_lever_arm_unit = "in"
        self.lifft_header_load_unit = "lb"
        self.lifft_header_moment_unit = "ft.lb"
        self.tst_header_lever_arm_unit = "in"
        self.tst_header_load_unit = "lb"
        self.tst_header_moment_unit = "ft.lb"   
 
       
        self.any_lifft_input_changed = False
        self.any_duet_input_changed = False
        self.any_tst_input_changed = False
       
        
        self.setupUI()
        self.setupMenuBar()  # Setup the menu bar
        self.setupStatusBar()  # Setup the status bar
        
        self.initProjectVars()
        
        self.setupLocale()
        
        self.setUnitText()
        
        
       
    def initProjectVars(self):
        # Make project-related paths accessible externally
        self.projectFilePath = ""  # The full path to the project file 
        self.projectFolderPath = ""  # The folder where the project resides
        self.projectFolderName = ""  # The project folder name
        self.projectName = ""  # The name of the project
        self.projectDescription = "" # The project description
        self.projectdatabasePath = ""  # The full path to the database
        self.projectdatabaseName = ""  # The database name
        self.dataFolder = ""  # The data folder
        self.imagesFolder = ""  # The images folder
        #self.selectedLanguage = ""
        #self.selectedMeasurementSystem = ""
        # Get the current language and measurement system
        self.selectedLanguage = "Spanish" if self.language_spanish_action.isChecked() else "English"
        self.selectedMeasurementSystem = "Metric" if self.metric_action.isChecked() else "Imperial"
        self.projectFileCreated = False
        self.isNumberOrder = True  # Default state
        
        self.previous_worker_index = self.workerComboBox.currentIndex()
        
        
       
    def setupLocale(self):
        # Get the system's current locale
        system_locale = QLocale.system()
        
        # Get the language of the system's locale
        system_language = system_locale.language()


        #TODO: check translation once the update is done...
        # Check if the language is English or Spanish
        #if system_language == QLocale.English: #
            #self.languageComboBox.setCurrentIndex(0) # english  
        #elif system_language == QLocale.Spanish:
            #self.languageComboBox.setCurrentIndex(1) # spanish
        #else:
        #    print("System language is neither English nor Spanish.")

        
    def setupMenuBar(self):
        # Get the menu bar
        self.menu_bar = self.menuBar()

        # Creating the "File" menu
        self.file_menu = self.menu_bar.addMenu('Project')

        # New and Open actions
        self.new_action = QAction('New...', self)
        self.new_action.triggered.connect(self.newFile)
        self.file_menu.addAction(self.new_action)

        self.open_action = QAction('Open...', self)
        self.open_action.triggered.connect(self.openFile)
        self.file_menu.addAction(self.open_action)

        self.file_menu.addSeparator()

        # Save and Save As actions
        self.save_action = QAction('Save...', self)
        self.save_action.triggered.connect(self.saveFile)
        self.file_menu.addAction(self.save_action)

        self.save_as_action = QAction('Save As...', self)
        self.save_as_action.triggered.connect(self.saveFileAs)
        self.file_menu.addAction(self.save_as_action)

        self.file_menu.addSeparator()

        # Export actions
        self.export_action = QAction('Export...', self)
        self.export_action.triggered.connect(self.exportFile)
        self.file_menu.addAction(self.export_action)

        self.export_as_action = QAction('Export As...', self)
        self.export_as_action.triggered.connect(self.exportFileAs)
        self.file_menu.addAction(self.export_as_action)

        self.export_action.setEnabled(False)
        self.export_as_action.setEnabled(False)

        self.export_csv_action = QAction('Export selected tool as CSV format', self) #TODO: move
        self.export_csv_action.triggered.connect(self.exportToCSV)
        self.file_menu.addAction(self.export_csv_action)

        self.file_menu.addSeparator()
        # Properties action
        self.properties_action = QAction('Properties', self)
        self.properties_action.triggered.connect(self.showPropertiesDialog)
        self.file_menu.addAction(self.properties_action) 

        self.file_menu.addSeparator()

        # Quit action
        self.exit_action = QAction('Quit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Quit application')
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # Creating the "Edit" menu
        self.edit_menu = self.menu_bar.addMenu('Edit')

        # Cut and Paste actions
        self.cut_action = QAction('Cut', self)
        self.cut_action.triggered.connect(self.cut)
        self.edit_menu.addAction(self.cut_action)

        self.paste_action = QAction('Paste', self)
        self.paste_action.triggered.connect(self.paste)
        self.edit_menu.addAction(self.paste_action)

        self.edit_menu.addSeparator()

        # Creating the "Preferences" submenu
        self.preferences_menu = self.edit_menu.addMenu('Preferences')


        # Number of Tasks submenu
        self.num_tasks_action = QAction('N° of Tasks', self)
        self.num_tasks_action.triggered.connect(self.openNumTasksDialog)
        self.preferences_menu.addAction(self.num_tasks_action)

        # Language submenu
        self.language_menu = self.preferences_menu.addMenu('Language')
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)

        self.language_spanish_action = QAction('Spanish', self, checkable=True)
        self.language_spanish_action.triggered.connect(self.setLanguageSpanish)
        self.language_english_action = QAction('English', self, checkable=True)
        self.language_english_action.triggered.connect(self.setLanguageEnglish)


        self.language_group.addAction(self.language_spanish_action)
        self.language_group.addAction(self.language_english_action)

        self.language_menu.addAction(self.language_spanish_action)
        self.language_menu.addAction(self.language_english_action)
        
        

        # Set the system language
        if QLocale.system().language() == QLocale.Spanish:
            self.language_spanish_action.setChecked(True)
        else:
            self.language_english_action.setChecked(True)

        self.language_english_action.setEnabled(True)
        self.language_spanish_action.setEnabled(False) 


        # Metric System submenu
        self.metric_system_menu = self.preferences_menu.addMenu('Measurement System')
        self.metric_system_group = QActionGroup(self)
        self.metric_system_group.setExclusive(True)

        self.metric_action = QAction('Metric', self, checkable=True)
        self.metric_action.triggered.connect(self.setMetricSystem)
        self.imperial_action = QAction('Imperial', self, checkable=True)
        self.imperial_action.triggered.connect(self.setImperialSystem)

        self.metric_system_group.addAction(self.metric_action)
        self.metric_system_group.addAction(self.imperial_action)

        self.metric_system_menu.addAction(self.metric_action)
        self.metric_system_menu.addAction(self.imperial_action)

        # Set default to Metric
        #self.metric_action.setChecked(True)
        self.imperial_action.setChecked(True)

        self.view_menu = self.menu_bar.addMenu('View')
        settings = QtCore.QSettings("ErgoTools", "ErgoTools")
        animation_enabled = settings.value("animated_body_region_focus", True, type=bool)
        self.camera_animation_action = QAction('Animated body-region focus', self, checkable=True)
        self.camera_animation_action.setChecked(animation_enabled)
        self.camera_animation_action.setStatusTip(
            "Animate the 3D camera toward the body region evaluated by each tool."
        )
        self.camera_animation_action.setToolTip(
            "Disable this option to keep the original full-body camera view for every tool."
        )
        self.camera_animation_action.setEnabled(self.vtk_enabled)
        self.camera_animation_action.toggled.connect(self.setCameraAnimationEnabled)
        self.view_menu.addAction(self.camera_animation_action)
        self.setCameraAnimationEnabled(animation_enabled)

        # Creating the "Tools" menu
        self.tools_menu = self.menu_bar.addMenu('Tools')

        # Plant Layout action
        self.plant_layout_action = QAction('Plant Layout', self)
        self.plant_layout_action.triggered.connect(self.openPlantLayout)
        self.tools_menu.addAction(self.plant_layout_action)

        # Creating the "Help" menu
        self.help_menu = self.menu_bar.addMenu('Help')

        # User Guide action
        self.user_guide_action = QAction('User Guide', self)
        self.user_guide_action.triggered.connect(self.openHelpPDF)
        self.help_menu.addAction(self.user_guide_action)

        # About action
        self.about_action = QAction('About', self)
        self.authorsDialog = QDialog(self)
        self.authorsDialog.setWindowTitle("Authors")
        self.authorsLabel = QLabel("Ivan Nail, Ph.D.")
        self.about_action.triggered.connect(self.showAuthorsDialog)
        self.help_menu.addAction(self.about_action)

    def cut(self):
        QMessageBox.information(self, "Edit Action", "Cut action triggered")

    def paste(self):
        QMessageBox.information(self, "Edit Action", "Paste action triggered")

    def setCameraAnimationEnabled(self, enabled):
        requested = bool(enabled)
        self.isAnimationAllowed = bool(requested and self.vtk_enabled)
        QtCore.QSettings("ErgoTools", "ErgoTools").setValue(
            "animated_body_region_focus", requested
        )
        if not self.vtk_enabled or not hasattr(self, "camera_director"):
            return
        if self.isAnimationAllowed:
            self.camera_director.apply(self.tabWidget.currentIndex())
        else:
            self.camera_director.applyFullBody()


    def showPropertiesDialog(self):
    
        # Ensure the project file is loaded or saved
        if not hasattr(self, 'projectFileCreated') or not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been loaded or saved.")
            return

        # Ensure the project file path is set
        if not hasattr(self, 'projectFilePath') or not self.projectFilePath:
            QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return

        # Read the XML file
        try:
            tree = ET.parse(self.projectFilePath)
            root = tree.getroot()

            # Extract data from the XML
            project_name = root.find('Name').text if root.find('Name') is not None else "N/A"
            description = root.find('Description').text if root.find('Description') is not None else "N/A"
            date = root.find('Date').text if root.find('Date') is not None else "N/A"
            time = root.find('Time').text if root.find('Time') is not None else "N/A"
            db_name = root.find('DatabaseName').text if root.find('DatabaseName') is not None else "N/A"
            db_path = root.find('DatabasePath').text if root.find('DatabasePath') is not None else "N/A"
            project_path = root.find('ProjectPath').text if root.find('ProjectPath') is not None else "N/A"
            project_folder = root.find('ProjectFolder').text if root.find('ProjectFolder') is not None else "N/A"
            data_path = root.find('DataPath').text if root.find('DataPath') is not None else "N/A"
            images_path = root.find('ImagesPath').text if root.find('ImagesPath') is not None else "N/A"
            language = root.find('Language').text if root.find('Language') is not None else "N/A"
            measurement_system = root.find('MeasurementSystem').text if root.find('MeasurementSystem') is not None else "N/A"

            # Create and show the dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Project Properties")
            dialog.setFixedSize(500, 400)

            layout = QVBoxLayout(dialog)

            # Add labels to display the information
            layout.addWidget(QLabel(f"<b>File:</b> {os.path.basename(self.projectFilePath)}"))
            layout.addWidget(QLabel(f"<b>Project Name:</b> {project_name}"))
            layout.addWidget(QLabel(f"<b>Description:</b> {description}"))
            layout.addWidget(QLabel(f"<b>Date:</b> {date}"))
            layout.addWidget(QLabel(f"<b>Time:</b> {time}"))
            layout.addWidget(QLabel(f"<b>Database Name:</b> {db_name}"))
            layout.addWidget(QLabel(f"<b>Database Path:</b> {db_path}"))
            layout.addWidget(QLabel(f"<b>Project Path:</b> {project_path}"))
            layout.addWidget(QLabel(f"<b>Project Folder:</b> {project_folder}"))
            layout.addWidget(QLabel(f"<b>Data Path:</b> {data_path}"))
            layout.addWidget(QLabel(f"<b>Images Path:</b> {images_path}"))
            layout.addWidget(QLabel(f"<b>Language:</b> {language}"))
            layout.addWidget(QLabel(f"<b>Measurement System:</b> {measurement_system}"))

            # Add a close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read project properties:\n{str(e)}")


    
    def openNumTasksDialog(self):
        self.num_tasks_dialog = QDialog(self)
        self.num_tasks_dialog.setWindowTitle('Set Number of Tasks')

        layout = QVBoxLayout(self.num_tasks_dialog)

        # Label and spinbox
        self.num_tasks_label = QLabel("N° of Tasks:")
        bold_font = QFont()
        bold_font.setBold(True)
        self.num_tasks_label.setFont(bold_font)

        
        
        self.num_tasks_spinbox = QSpinBox()
        self.num_tasks_spinbox.setRange(1, 100)
        self.num_tasks_spinbox.setValue(10)  # Default value
        layout.addWidget(self.num_tasks_label)
        layout.addWidget(self.num_tasks_spinbox)

        # Buttons
        button_layout = QHBoxLayout()
        self.num_tasks_set_button = QPushButton("Set Tasks")
        self.num_tasks_cancel_button = QPushButton("Cancel")

        button_layout.addWidget(self.num_tasks_set_button)
        button_layout.addWidget(self.num_tasks_cancel_button)

        layout.addLayout(button_layout)

        # Connect buttons
        self.num_tasks_set_button.clicked.connect(self.numTasksSetButtonClicked)
        self.num_tasks_cancel_button.clicked.connect(self.numTasksCancelButtonClicked)

        self.num_tasks_dialog.setLayout(layout)
        self.num_tasks_dialog.exec_()


    def numTasksSetButtonClicked(self):
        # Implementation for what happens when the "Set Tasks" menu is clicked
        
        
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
        
        
        num_tasks = self.num_tasks_spinbox.value()
        
        self.num_task = num_tasks  # Update the number of tasks
        
        #self.num_task  = self.numTasksSpinBox.value()
        #current_language_index = self.languageComboBox.currentIndex() #TODO: check this once the update is complete
        current_language_index = 0 #TODO: to make it work during the update
        
        #self.lifftResetForm()
        #self.duetResetForm()
        #self.tstResetForm()
        #self.resetAllPatchs()
        self.tabWidget.removeTab(currentTabIndex)
        if (currentTabIndex == 0):
            self.resetBackPatchs()
            self.num_task_lift = self.num_task
            self.setupLiFFTTab()
        elif (currentTabIndex == 1):
            self.resetArmPatchs()
            self.num_task_duet = self.num_task
            self.setupDUETTab()
        elif (currentTabIndex == 2):
            self.resetShoulderPatchs()
            self.num_task_tst = self.num_task
            self.setupTSTTab()    
        
        
        self.tabWidget.setCurrentIndex(currentTabIndex)
        
        #self.tabWidget.removeTab(0) # previous "0" reduce the total amount, so allways removing 0 so end up remoging the 3 of them 
        #self.tabWidget.removeTab(0)
        
        #self.setupTabWidgets()
        
        # self.changeLanguage(current_language_index) # TODO: Check what is need in terms of translation once is back working...
        
        # Optionally, clear any warning messages
        self.statusBar().showMessage("")
        
        
        #self.repaint() 
          
        QMessageBox.information(self, "N° of Tasks", f"Number of tasks set to {num_tasks}")
        self.num_tasks_dialog.accept()
        
        
    
    
    def numTasksSetButtonClickedW(self):
        # Implementation for what happens when the "Set Tasks" menu is clicked
        
        num_tasks = self.num_tasks_spinbox.value()
        
        self.num_task = num_tasks  # Update the number of tasks
        
        #self.num_task  = self.numTasksSpinBox.value()
        #current_language_index = self.languageComboBox.currentIndex() #TODO: check this once the update is complete
        current_language_index = 0 #TODO: to make it work during the update
        
        #self.lifftResetForm()
        #self.duetResetForm()
        #self.tstResetForm()
        self.resetAllPatchs()
        self.tabWidget.removeTab(0)
        self.tabWidget.removeTab(0) # previous "0" reduce the total amount, so allways removing 0 so end up remoging the 3 of them 
        self.tabWidget.removeTab(0)
        
        self.setupTabWidgets()
        
        # self.changeLanguage(current_language_index) # TODO: Check what is need in terms of translation once is back working...
        
        # Optionally, clear any warning messages
        self.statusBar().showMessage("")
        
        
        #self.repaint() 
          
        QMessageBox.information(self, "N° of Tasks", f"Number of tasks set to {num_tasks}")
        self.num_tasks_dialog.accept()
        
        
        
        
        

    def numTasksCancelButtonClicked(self):
        self.num_tasks_dialog.reject()


    def setUnitText(self):
        """Sets the unit text for headers, ensuring actions and labels exist before modification."""

        # **Validate if selectedMeasurementSystem actions exist**
        #if not hasattr(self, "selectedMeasurementSystem") or not isinstance(self.selectedMeasurementSystem, str):
        #    self.selectedMeasurementSystem = "imperial"  # Default to imperial if action doesn't exist
    
        # **Define measurement unit variables based on system**
        #system = self.selectedMeasurementSystem.lower()
        #if system not in ["metric", "imperial"]:
        #    system = "imperial"  # Default to imperial if invalid system
            
            
        #if hasattr(self, "unit_label"):
        #    self.unit_label.setText(f"Unit: {system.capitalize()}")
       
                 
       
        if not hasattr(self, "lifft_unit") or not (self.lifft_unit):
            self.lifft_unit = self.default_metric_sys
        system = self.lifft_unit.lower()
        if system not in ["metric", "imperial"]:
            system = self.default_metric_sys # Default to imperial if invalid system   
        self.lifft_header_lever_arm_unit = "cm" if system == "metric" else "in"
        self.lifft_header_load_unit = "N" if system == "metric" else "lb"
        self.lifft_header_moment_unit = "N.m" if system == "metric" else "ft.lb"
     
        if hasattr(self, "unit_label") and hasattr(self, "tabWidget"):
            if self.tabWidget.currentIndex() == 0:
                self.unit_label.setText(f"Unit: {system.capitalize()}")
        
         
         
        if hasattr(self, "unit_label") and hasattr(self, "tabWidget"):
            if self.tabWidget.currentIndex() == 1:
                system = self.default_metric_sys
                self.unit_label.setText(f"Unit: {system.capitalize()}") 
         
         
        if not hasattr(self, "tst_unit") or not (self.tst_unit):
            self.tst_unit = self.default_metric_sys
        system = self.tst_unit.lower()
        if system not in ["metric", "imperial"]:
            system = self.default_metric_sys # Default to imperial if invalid system       
        self.tst_header_lever_arm_unit = "cm" if system == "metric" else "in"
        self.tst_header_load_unit = "N" if system == "metric" else "lb"
        self.tst_header_moment_unit = "N.m" if system == "metric" else "ft.lb"   
        
        if hasattr(self, "unit_label") and hasattr(self, "tabWidget"):
            if self.tabWidget.currentIndex() == 2:
                self.unit_label.setText(f"Unit: {system.capitalize()}")
                
        # TODO: fix alignment issues!!
        
        # **Check and update main header labels**
        if hasattr(self, "lifft_headers_labels") and len(self.lifft_headers_labels) > 3:
            if self.lifft_headers_labels[1]:
                self.lifft_headers_labels[1].setText(f"Lever Arm ({self.lifft_header_lever_arm_unit})")
            if self.lifft_headers_labels[2]:
                self.lifft_headers_labels[2].setText(f"Load ({self.lifft_header_load_unit})")
            if self.lifft_headers_labels[3]:
                self.lifft_headers_labels[3].setText(f"Moment ({self.lifft_header_moment_unit})")

        # **Check and update fixed header labels**
        if hasattr(self, "lifft_headers_labels_fixed") and len(self.lifft_headers_labels_fixed) > 3:
            if self.lifft_headers_labels_fixed[1]:
                self.lifft_headers_labels_fixed[1].setText(f"Lever Arm ({self.lifft_header_lever_arm_unit})")
            if self.lifft_headers_labels_fixed[2]:
                self.lifft_headers_labels_fixed[2].setText(f"Load ({self.lifft_header_load_unit})")
            if self.lifft_headers_labels_fixed[3]:
                self.lifft_headers_labels_fixed[3].setText(f"Moment ({self.lifft_header_moment_unit})")
            
        
        
        # **Check and update main header labels**
        if hasattr(self, "tst_headers_labels") and len(self.tst_headers_labels) > 4:
            if self.tst_headers_labels[2]:
                self.tst_headers_labels[2].setText(f"Lever Arm ({self.tst_header_lever_arm_unit})")
            if self.tst_headers_labels[3]:
                self.tst_headers_labels[3].setText(f"Load ({self.tst_header_load_unit})")
            if self.tst_headers_labels[4]:
                self.tst_headers_labels[4].setText(f"Moment ({self.tst_header_moment_unit})")

        # **Check and update fixed header labels**    
        if hasattr(self, "tst_headers_labels_fixed") and len(self.tst_headers_labels_fixed) > 4:
            if self.tst_headers_labels_fixed[2]:
                self.tst_headers_labels_fixed[2].setText(f"Lever Arm ({self.tst_header_lever_arm_unit})")
            if self.tst_headers_labels_fixed[3]:
                self.tst_headers_labels_fixed[3].setText(f"Load ({self.tst_header_load_unit})")
            if self.tst_headers_labels_fixed[4]:
                self.tst_headers_labels_fixed[4].setText(f"Moment ({self.tst_header_moment_unit})")

        
    
    def setUnitSysText(self, system):
        """Sets the unit text for headers, ensuring actions and labels exist before modification."""
        system = system.lower()
        if system not in ["metric", "imperial"]:
            system = self.default_metric_sys # Default to imperial if invalid system   
        self.lifft_header_lever_arm_unit = "cm" if system == "metric" else "in"
        self.lifft_header_load_unit = "N" if system == "metric" else "lb"
        self.lifft_header_moment_unit = "N.m" if system == "metric" else "ft.lb"
     
        if hasattr(self, "unit_label") and hasattr(self, "tabWidget"):
            if self.tabWidget.currentIndex() == 0:
                self.unit_label.setText(f"Unit: {system.capitalize()}")
        
         
         
        if hasattr(self, "unit_label") and hasattr(self, "tabWidget"):
            if self.tabWidget.currentIndex() == 1:
                #system = self.default_metric_sys
                self.unit_label.setText(f"Unit: {system.capitalize()}") 
         
        self.tst_header_lever_arm_unit = "cm" if system == "metric" else "in"
        self.tst_header_load_unit = "N" if system == "metric" else "lb"
        self.tst_header_moment_unit = "N.m" if system == "metric" else "ft.lb"   
        
        if hasattr(self, "unit_label") and hasattr(self, "tabWidget"):
            if self.tabWidget.currentIndex() == 2:
                self.unit_label.setText(f"Unit: {system.capitalize()}")
                
        # TODO: fix alignment issues!!
        
        # **Check and update main header labels**
        if hasattr(self, "lifft_headers_labels") and len(self.lifft_headers_labels) > 3:
            if self.lifft_headers_labels[1]:
                self.lifft_headers_labels[1].setText(f"Lever Arm ({self.lifft_header_lever_arm_unit})")
            if self.lifft_headers_labels[2]:
                self.lifft_headers_labels[2].setText(f"Load ({self.lifft_header_load_unit})")
            if self.lifft_headers_labels[3]:
                self.lifft_headers_labels[3].setText(f"Moment ({self.lifft_header_moment_unit})")

        # **Check and update fixed header labels**
        if hasattr(self, "lifft_headers_labels_fixed") and len(self.lifft_headers_labels_fixed) > 3:
            if self.lifft_headers_labels_fixed[1]:
                self.lifft_headers_labels_fixed[1].setText(f"Lever Arm ({self.lifft_header_lever_arm_unit})")
            if self.lifft_headers_labels_fixed[2]:
                self.lifft_headers_labels_fixed[2].setText(f"Load ({self.lifft_header_load_unit})")
            if self.lifft_headers_labels_fixed[3]:
                self.lifft_headers_labels_fixed[3].setText(f"Moment ({self.lifft_header_moment_unit})")
            
        
        
        # **Check and update main header labels**
        if hasattr(self, "tst_headers_labels") and len(self.tst_headers_labels) > 4:
            if self.tst_headers_labels[2]:
                self.tst_headers_labels[2].setText(f"Lever Arm ({self.tst_header_lever_arm_unit})")
            if self.tst_headers_labels[3]:
                self.tst_headers_labels[3].setText(f"Load ({self.tst_header_load_unit})")
            if self.tst_headers_labels[4]:
                self.tst_headers_labels[4].setText(f"Moment ({self.tst_header_moment_unit})")

        # **Check and update fixed header labels**    
        if hasattr(self, "tst_headers_labels_fixed") and len(self.tst_headers_labels_fixed) > 4:
            if self.tst_headers_labels_fixed[2]:
                self.tst_headers_labels_fixed[2].setText(f"Lever Arm ({self.tst_header_lever_arm_unit})")
            if self.tst_headers_labels_fixed[3]:
                self.tst_headers_labels_fixed[3].setText(f"Load ({self.tst_header_load_unit})")
            if self.tst_headers_labels_fixed[4]:
                self.tst_headers_labels_fixed[4].setText(f"Moment ({self.tst_header_moment_unit})")

        
         
       
    
    def setLanguageSpanish(self):
        #QMessageBox.information(self, "Language Change", "Selected Language: Spanish")
        #lang = self.languageComboBox.itemData(index)
        #lang = 1
        #if lang:
        #    if self.translator.load(lang):
        #        QtWidgets.QApplication.instance().installTranslator(self.translator)
        #else:
        #    QtWidgets.QApplication.instance().removeTranslator(self.translator)
        
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
            omnires_dropdown.setMinimumWidth(225)
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
        
        self.languageComboBox.setItemText(0, "Ingles")
        self.languageComboBox.setItemText(1, "Español")       

        if self.unitComboBox.currentIndex() == 0: #"English":
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
            self.lifft_headers_labels[1].setText("Brazo de Palanca (cm)")  # Change to inch
            self.lifft_headers_labels[2].setText("Carga (N)")         # Change to lb
            self.lifft_headers_labels[3].setText("Momento (N.m)")    # Change to ft.lb
            self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
            self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

            self.tst_headers_labels[2].setText("Brazo de Palanca (cm)")  # Change to inch
            self.tst_headers_labels[3].setText("Carga (N)")         # Change to lb
            self.tst_headers_labels[4].setText("Momento (N.m)")    # Change to ft.lb    
            
            self.unit = "metric"
        
    
    
        self.selectedLanguage = "Spanish"
        
        self.retranslateUI()
        self.repaint() 



    def setLanguageEnglish(self):
        #QMessageBox.information(self, "Language Change", "Selected Language: English")
        
        #lang = self.languageComboBox.itemData(index)
        #lang = 0
        #if lang:
        #    if self.translator.load(lang):
        #        QtWidgets.QApplication.instance().installTranslator(self.translator)
        #else:
        #    QtWidgets.QApplication.instance().removeTranslator(self.translator)
       
       
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
            
        self.languageComboBox.setItemText(0, "English")
        self.languageComboBox.setItemText(1, "Spanish")
                
        if self.unitComboBox.currentIndex() == 0: #"English":
            self.lifft_headers_labels[1].setText("Lever Arm (inch)")  # Change to inch
            self.lifft_headers_labels[2].setText("Load (lb)")         # Change to lb
            self.lifft_headers_labels[3].setText("Moment (ft.lb)")    # Change to ft.lb
            self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
            self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"   

            self.tst_headers_labels[2].setText("Lever Arm (inch)")  # Change to inch
            self.tst_headers_labels[3].setText("Load (lb)")         # Change to lb
            self.tst_headers_labels[4].setText("Moment (ft.lb)")    # Change to ft.lb
            
            self.unit = "english"
            
        elif self.unitComboBox.currentIndex() == 1: #"Metric":
            self.lifft_headers_labels[1].setText("Lever Arm (cm)")    # Change back to cm
            self.lifft_headers_labels[2].setText("Load (N)")          # Change back to N
            self.lifft_headers_labels[3].setText("Moment (N.m)")      # Change back to N.m
            self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "cm", "N", "N.m"
            self.lifft_color_english, self.lifft_color_metric = "color: #808080;" , "color: #337ab7; font-weight:bold;"
        
            self.tst_headers_labels[2].setText("Lever Arm (cm)")    # Change back to cm
            self.tst_headers_labels[3].setText("Load (N)")          # Change back to N
            self.tst_headers_labels[4].setText("Moment (N.m)")      # Change back to N.m
            
            self.unit = "metric"
    
    
        # Get the current language and measurement system
        self.selectedLanguage = "English"
       
        self.retranslateUI()
        self.repaint() 













        

    def setMetricSystem(self):
        self.updateUnits(1) # Metric System
        #QMessageBox.information(self, "Metric System Change", "Selected Metric System: Metric")
        #print("Metric selected")
        self.setUnitSysText("Metric")

    def setImperialSystem(self):
        self.updateUnits(0) # English System
        #QMessageBox.information(self, "Metric System Change", "Selected Metric System: English")
        #print("Imperial selected")
        self.setUnitSysText("Imperial")

   


    
    def getCurrentLanguage(self):
        if self.language_spanish_action.isChecked():
            return 'Spanish'
        elif self.language_english_action.isChecked():
            return 'English'
        return None

    def getCurrentMetricSystem(self):
        if self.metric_action.isChecked():
            return 'Metric'
        elif self.imperial_action.isChecked():
            return 'English'
        return None
        
            
    def newFile(self):
        """
        Handle the 'New' menu action to reset the application state.
        """
        # Reset project-related variables
        #self.projectFilePath = None
        #self.projectFolderPath = None
        #self.projectFolderName = None
        #self.projectDescription = None
        #self.projectName = None
        #self.projectdatabasePath = None
        #self.projectdatabaseName = None
        #self.dataFolder = None
        #self.imagesFolder = None

        # Set projectFileCreated to False
        #self.projectFileCreated = False
        #print("self.imperial_action.isChecked():", self.imperial_action.isChecked())
        #self.metric_action.setChecked(False)
        #self.imperial_action.setChecked(True)
        #print("self.imperial_action.isChecked():", self.imperial_action.isChecked())
        #self.initProjectVars()
        #print("self.imperial_action.isChecked():", self.imperial_action.isChecked())
        #self.setUnitText()
        

 
        # **Suspend signals for all combo boxes**
        self.workerComboBox.blockSignals(True)
        self.plant_combo.blockSignals(True)
        self.section_combo.blockSignals(True)
        self.line_combo.blockSignals(True)
        self.station_combo.blockSignals(True)
        self.shift_combo.blockSignals(True)
        
        # **Clear and add default values**
        self.workerComboBox.clear()
        self.workerComboBox.addItems(["Default"])
        
        self.plant_combo.clear()
        self.plant_combo.addItems(["Default"])
        
        self.section_combo.clear()
        self.section_combo.addItems(["Default"])
        
        self.line_combo.clear()
        self.line_combo.addItems(["Default"])
        
        self.station_combo.clear()
        self.station_combo.addItems(["Default"])
        
        self.shift_combo.clear()
        self.shift_combo.addItems(["1"])
        
        # **Re-enable signals after modification**
        self.workerComboBox.blockSignals(False)
        self.plant_combo.blockSignals(False)
        self.section_combo.blockSignals(False)
        self.line_combo.blockSignals(False)
        self.station_combo.blockSignals(False)
        self.shift_combo.blockSignals(False)



        self.default_num_task = 15
        self.default_metric_sys = "Imperial"
        self.num_task  = self.default_num_task
        self.lifft_unit = self.default_metric_sys
        self.duet_unit = self.default_metric_sys
        self.tst_unit = self.default_metric_sys
        
        self.num_task_lift = self.num_task
        self.num_task_duet = self.num_task
        self.num_task_tst = self.num_task
        
        self.any_lifft_input_changed = False
        self.any_duet_input_changed = False
        self.any_tst_input_changed = False
        
        self.resetAll()


        self.metric_action.setChecked(False)
        self.imperial_action.setChecked(True)
        self.initProjectVars()
        
        self.setUnitText()

        
        
        # Display a message box or update the status bar to indicate the project has been reset
        QMessageBox.information(self, "New Project", "The project has been reset. You can start a new one.")



    def loadWorkers(self, order_by):
        # Order workers by id (order_by = 0)
        workers_list = self.getWorkers(order_by)
        # Populate the worker combobox
        
        self.worker_all_items = workers_list
        available_letters = {
            display.partition("(")[2].partition(",")[0].strip()[:1].upper()
            for display in workers_list if display.partition("(")[2].partition(",")[0].strip()
        }
        for value, button in getattr(self, "main_worker_alphabet_buttons", {}).items():
            button.setEnabled(value == "All" or value in available_letters)
        self.applyMainWorkerAlphabetFilter(
            getattr(self, "main_worker_alphabet_letter", None), preserve_selection=True
        )

    def applyMainWorkerAlphabetFilter(self, letter=None, preserve_selection=True):
        """Filter the main worker selector by last-name initial."""
        self.main_worker_alphabet_letter = letter
        if not hasattr(self, "workerComboBox"):
            return
        current_id = self.workerComboBox.currentText().split(" ", 1)[0] if preserve_selection else ""
        source = getattr(self, "worker_all_items", None)
        if source is None:
            source = [self.workerComboBox.itemText(index) for index in range(self.workerComboBox.count())]
            self.worker_all_items = source
        if letter:
            visible = []
            for display in source:
                surname = display.partition("(")[2].partition(",")[0].strip()
                if surname.upper().startswith(letter):
                    visible.append(display)
        else:
            visible = list(source)
        self.workerComboBox.blockSignals(True)
        self.workerComboBox.clear()
        self.workerComboBox.addItems(visible)
        index = next(
            (index for index, display in enumerate(visible) if display.split(" ", 1)[0] == current_id), -1
        )
        if index >= 0:
            self.workerComboBox.setCurrentIndex(index)
        elif visible:
            self.workerComboBox.setCurrentIndex(0)
        self.workerComboBox.blockSignals(False)

    def setMainWorkerAlphabetFilter(self, value):
        letter = None if value == "All" else value
        self.applyMainWorkerAlphabetFilter(letter)
        for candidate, button in self.main_worker_alphabet_buttons.items():
            button.blockSignals(True)
            button.setChecked(candidate == value)
            button.blockSignals(False)
        if self.workerComboBox.count():
            self.workerComboIndexChanged(self.workerComboBox.currentIndex())
        
        
    
    def getWorkers(self, order_by):
        """
        Retrieves workers from the database in the specified order.
    
        Args:
            order_by (int): 0 for ordering by Worker ID, 1 for ordering by Last Name.
    
        Returns:
            list: A list of strings formatted as <worker id>(<last name>, <first name>).
        """
        # Ensure a project file is created before accessing the database
        if not self.projectFileCreated or not self.projectdatabasePath:
            QMessageBox.warning(self, "Error", "No project file loaded or saved.")
            return []

        # Determine the order column
        order_column = "id" if order_by == 0 else "last_name"

        # Connect to the database and query the workers
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
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
       
       
       
    def getPlants(self):
        """
        Retrieves all plants from the database.

        Returns:
            list: A list of strings formatted as <plant name>(<location>, <type>).
        """
        # Check if a project has been created from the parent window
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing plants.")
            return
            
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve plant data.")
            return

        # Connect to the database and query the plants
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
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
        # Check if a project has been created from the parent window
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing sections.")
            return
            
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve section data.")
            return

        # Ensure a valid plant name is provided
        if not plant_name:
            #QMessageBox.warning(self, "Error", "No plant selected. Unable to retrieve sections.")
            return

        # Connect to the database and query the sections for the specified plant
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
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
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing lines.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve line data.")
            return
    
        # Ensure valid plant and section names are provided
        if not plant_name or not section_name:
            #QMessageBox.warning(self, "Error", "No plant or section selected. Unable to retrieve lines.")
            return

        # Connect to the database and query the lines for the specified plant and section
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
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
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing stations.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve station data.")
            return
    
        # Ensure valid plant, section, and line names are provided
        if not plant_name or not section_name or not line_name:
            #QMessageBox.warning(self, "Error", "No plant, section, or line selected. Unable to retrieve stations.")
            return

        # Connect to the database and query the stations for the specified plant, section, and line
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
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
    
    
    def getShifts(self):
        """
        Retrieves all shifts from the database.
    
        Returns:
            list: A list of shift IDs.
        """
        # Check if a project has been created from the parent window
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before managing shifts.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to retrieve shift data.")
            return
    
        # Connect to the database and query all shifts
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
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

    
    
    def openFile(self):
        # Open a file dialog to select a project file
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", os.path.expanduser("~/Documents"), "ErgoProj Files (*.ergprj)", options=options)

        self.openFilePath(file_path)
        

    def openFilePath(self, file_path):
        if not file_path:
            return

        # Read the XML file
        try:
        
            # Determine the project’s root folder based on the project file location.
            # os.path.abspath ensures an absolute path; os.path.dirname gives the folder.
            #project_root = os.path.dirname(os.path.abspath(file_path))
            #print("project_root:", project_root)
            
            #relative_db_path = "db"
            
            # Resolve the absolute path for the database folder:
            #db_path = os.path.normpath(os.path.join(project_root, relative_db_path))
            #print("Database folder absolute path:", db_path)
            
             
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract data from the XML
            self.projectFilePath = file_path
            self.projectFolderPath = os.path.dirname(file_path)
            self.projectFileCreated = True  # Indicate a project file has been loaded

            self.projectName = root.find('Name').text if root.find('Name') is not None else ""
            self.projectDescription = root.find('Description').text if root.find('Description') is not None else ""
            self.projectDate = root.find('Date').text if root.find('Date') is not None else ""
            self.projectTime = root.find('Time').text if root.find('Time') is not None else ""
            
            self.projectdatabaseName = root.find('DatabaseName').text if root.find('DatabaseName') is not None else ""
            
            
            
           # self.projectdatabasePath = os.path.normpath(os.path.join(self.projectFolderPath, root.find('DatabasePath').text) if root.find('DatabasePath') is not None else "")
            
            self.projectdatabasePath = os.path.normpath(os.path.join(self.projectFolderPath, root.find('DataPath').text, root.find('DatabaseName').text))
    
            
            
            
            
            self.projectFolderName = root.find('ProjectFolder').text if root.find('ProjectFolder') is not None else ""
            self.dataFolder = root.find('DataPath').text if root.find('DataPath') is not None else ""
            self.imagesFolder = root.find('ImagesPath').text if root.find('ImagesPath') is not None else ""
            self.selectedLanguage = root.find('Language').text if root.find('Language') is not None else "English"
            self.selectedMeasurementSystem = root.find('MeasurementSystem').text if root.find('MeasurementSystem') is not None else "Metric"


            #print(f"Project File Path: {self.projectFilePath}")
            #print(f"Project Folder Path: {self.projectFolderPath}")
            #print(f"Project Database Path: {self.projectdatabasePath}")



            self.default_metric_sys = self.selectedMeasurementSystem # Initial defaul is the project one..
            # Load workers into the combobox...
            self.isNumberOrder = True
            
            
            self.setWorkerOrder()  
            
            #self.loadWorkers(0)
            #self.orderButton.setIcon(QIcon("../images/alphaorder01.png"))
            
            self.loadPlants()
            #self.loadSections()
            #self.loadLines()
            #self.loadStations()
            self.loadShifts()
            
            
            
            self.loadToolsData()
            
            
            # Notify the user
            QMessageBox.information(self, "Project Opened", f"Project loaded successfully")

            self.projectFileCreated = True  # Boolean to indicate if the project file was created
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project file:\n{str(e)}")
            self.projectFileCreated = False
        
        #TODO: rest of the data load, right now only loading the project variables...  
    
    
    
    #def saveFileAs(self):
    #    QMessageBox.information(self, "Save Project As", "Save File As action triggered")

    def saveFileAs(self):
        # If there is no current project yet, fall back to normal Save
        if not self.projectFileCreated:
            self.saveFile()
            return

        # First save current tool data into the current project database
        #self.saveToolsData()
        
        
        # Ask for the new project file path
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        new_file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            os.path.expanduser("~/Documents"),
            "ErgoProj Files (*.ergprj)",
            options=options
        )

        if not new_file_path:
            return

        # Ensure the file has the correct extension
        if not new_file_path.endswith(".ergprj"):
            new_file_path += ".ergprj"

        # Avoid overwriting the same file path with unnecessary work
        current_project_path = os.path.normpath(self.projectFilePath) if self.projectFilePath else ""
        if os.path.normpath(new_file_path) == current_project_path:
            QMessageBox.information(self, "Save Project As", "The selected file is the same as the current project.")
            return

        # Ask optionally for a new project name and description, prefilled with current values
        description_dialog = QDialog(self)
        description_dialog.setWindowTitle("Project Details")
        description_layout = QVBoxLayout(description_dialog)

        name_label = QLabel("Name:")
        name_input = QLineEdit()
        name_input.setText(self.projectName if hasattr(self, "projectName") else "")
        description_layout.addWidget(name_label)
        description_layout.addWidget(name_input)
    
        description_label = QLabel("Description:")
        description_text_edit = QTextEdit()
        description_text_edit.setPlainText(self.projectDescription if hasattr(self, "projectDescription") else "")
        description_layout.addWidget(description_label)
        description_layout.addWidget(description_text_edit)
    
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(description_dialog.accept)
        button_box.rejected.connect(description_dialog.reject)
        description_layout.addWidget(button_box)
    
        if description_dialog.exec_() == QDialog.Accepted:
            project_name_input = name_input.text().strip()
            description = description_text_edit.toPlainText()
        else:
            return

        # New project naming
        new_project_folder = os.path.basename(new_file_path).replace(".ergprj", "")
        new_project_name = project_name_input
    
        # New folder structure
        new_project_folder_path = os.path.dirname(new_file_path)
        new_data_folder_name = new_project_folder + "_data"
        new_images_folder_name = new_project_folder + "_images"
    
        new_data_folder_path = os.path.join(new_project_folder_path, new_data_folder_name)
        new_images_folder_path = os.path.join(new_project_folder_path, new_images_folder_name)
    
        os.makedirs(new_data_folder_path, exist_ok=True)
        os.makedirs(new_images_folder_path, exist_ok=True)

        # New database path/name
        new_project_db_name = new_project_folder + "_data.db"
        new_project_db_path = os.path.join(new_data_folder_path, new_project_db_name)

        try:
            # Copy the CURRENT database, not the template database
            shutil.copyfile(self.projectdatabasePath, new_project_db_path)

            # Copy current images folder contents if it exists
            current_images_path = ""
            if hasattr(self, "projectFolderPath") and hasattr(self, "imagesFolder") and self.projectFolderPath and self.imagesFolder:
                current_images_path = os.path.join(self.projectFolderPath, self.imagesFolder)

            if current_images_path and os.path.isdir(current_images_path):
                for item_name in os.listdir(current_images_path):
                    src_item = os.path.join(current_images_path, item_name)
                    dst_item = os.path.join(new_images_folder_path, item_name)

                    if os.path.isdir(src_item):
                        if os.path.exists(dst_item):
                            shutil.rmtree(dst_item)
                        shutil.copytree(src_item, dst_item)
                    else:
                        shutil.copy2(src_item, dst_item)

            # Update project-related paths accessible externally
            self.projectFilePath = new_file_path
            self.projectFolderPath = new_project_folder_path
            self.projectRelFolderPath = os.path.join(new_project_folder, new_project_name)
            self.projectFolderName = new_project_folder
            self.projectDescription = description
            self.projectName = new_project_name
            self.projectdatabasePath = new_project_db_path
            self.projectdatabaseName = new_project_db_name
            self.dataFolder = new_data_folder_name
            self.imagesFolder = new_images_folder_name
    
            # Save current language and measurement system
            self.selectedLanguage = "Spanish" if self.language_spanish_action.isChecked() else "English"
            self.selectedMeasurementSystem = "Metric" if self.metric_action.isChecked() else "Imperial"
            self.default_metric_sys = self.selectedMeasurementSystem
    
            # Write the new XML project file
            root = ET.Element("ErgoProject")
    
            name_element = ET.SubElement(root, "Name")
            name_element.text = self.projectName
        
            description_element = ET.SubElement(root, "Description")
            description_element.text = self.projectDescription

            date_element = ET.SubElement(root, "Date")
            date_element.text = QDate.currentDate().toString("yyyy-MM-dd")
    
            time_element = ET.SubElement(root, "Time")
            time_element.text = QTime.currentTime().toString("HH:mm:ss")
    
            db_name_element = ET.SubElement(root, "DatabaseName")
            db_name_element.text = self.projectdatabaseName
    
            db_path_element = ET.SubElement(root, "DatabasePath")
            db_path_element.text = os.path.join(self.dataFolder, self.projectdatabaseName)
    
            folder_path_element = ET.SubElement(root, "ProjectPath")
            folder_path_element.text = self.projectRelFolderPath
    
            folder_name_element = ET.SubElement(root, "ProjectFolder")
            folder_name_element.text = self.projectFolderName
    
            data_folder_name_element = ET.SubElement(root, "DataPath")
            data_folder_name_element.text = self.dataFolder

            images_folder_name_element = ET.SubElement(root, "ImagesPath")
            images_folder_name_element.text = self.imagesFolder

            language_element = ET.SubElement(root, "Language")
            language_element.text = self.selectedLanguage
 
            measurement_system_element = ET.SubElement(root, "MeasurementSystem")
            measurement_system_element.text = self.selectedMeasurementSystem

            tree = ET.ElementTree(root)
            tree.write(self.projectFilePath)

            self.projectFileCreated = True

            QMessageBox.information(self, "Save Project As", f"Project saved successfully as:\n{self.projectFilePath}")
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project as:\n{str(e)}")
    

    def exportFile(self):
        QMessageBox.information(self, "Export Project", "Export Project action triggered")

    def exportFileAs(self):
        QMessageBox.information(self, "Export Project As", "Export Project As action triggered")
    
    
    def saveFile(self):
    
    
        # Check if a project has been created 
        if self.projectFileCreated:
            self.saveToolsData()
            return
    
             
        # Open a file dialog to get the project name and location
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", os.path.expanduser("~/Documents"), "ErgoProj Files (*.ergprj)", 
                                                   options=options)

        if not file_path:
            return

        # Ensure the file has the correct extension
        if not file_path.endswith('.ergprj'):
            file_path += '.ergprj'

        # Ask for an optional project name and description
        description_dialog = QDialog(self)
        description_dialog.setWindowTitle('Project Details')
        description_layout = QVBoxLayout(description_dialog)

        # Input for project name
        name_label = QLabel('Name:')
        name_input = QLineEdit()
        description_layout.addWidget(name_label)
        description_layout.addWidget(name_input)

        # Input for project description
        description_label = QLabel('Description:')
        description_text_edit = QTextEdit()
        description_layout.addWidget(description_label)
        description_layout.addWidget(description_text_edit)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(description_dialog.accept)
        button_box.rejected.connect(description_dialog.reject)
        description_layout.addWidget(button_box)

        # Execute the dialog and get inputs
        if description_dialog.exec_() == QDialog.Accepted:
            project_name_input = name_input.text() # or None
            description = description_text_edit.toPlainText()
        else:
            project_name_input = ""
            description = ""


        project_folder = os.path.basename(file_path).replace('.ergprj', '')
        project_name = project_name_input 
        

        # Create the project data folder
        #data_folder = os.path.join(os.path.dirname(file_path), project_name + '_data')
        data_folder_name = project_folder + '_data'
        data_folder = os.path.join(os.path.dirname(file_path), data_folder_name)
        os.makedirs(data_folder, exist_ok=True)
        
        images_folder_name = project_folder + '_images'
        images_folder = os.path.join(os.path.dirname(file_path), images_folder_name)
        os.makedirs(images_folder, exist_ok=True)
        
        # Copy the database to the new folder
        original_db_path = "../data/ergotools_data.db"
        #project_db_name = project_name + '_data.db'
        project_db_name = project_folder + '_data.db'
        project_db_path = os.path.join(data_folder, project_db_name)
        shutil.copyfile(original_db_path, project_db_path)

        # Make project-related paths accessible externally
        self.projectFilePath = file_path  # The full path to the project file 
        self.projectFolderPath = os.path.dirname(file_path)  # The folder where the project resides
        
        self.projectRelFolderPath = os.path.join(project_folder, project_name)
        
        self.projectFolderName = project_folder  # The project folder name
        self.projectDescription = description  # The project description
        self.projectName = project_name  # The name of the project
        self.projectdatabasePath = project_db_path  # The full path to the database
        self.projectdatabaseName = project_db_name  # The database name
        self.dataFolder = data_folder_name  # The data folder
        self.imagesFolder = images_folder_name  # The images folder


        # Get the current language and measurement system
        self.selectedLanguage = "Spanish" if self.language_spanish_action.isChecked() else "English"
        self.selectedMeasurementSystem = "Metric" if self.metric_action.isChecked() else "Imperial"
        
        self.default_metric_sys = self.selectedMeasurementSystem # Default is the new saved ...

        # Create the XML file
        root = ET.Element("ErgoProject")
        name_element = ET.SubElement(root, "Name")
        name_element.text = project_name
        description_element = ET.SubElement(root, "Description")
        description_element.text = description
        date_element = ET.SubElement(root, "Date")
        date_element.text = QDate.currentDate().toString("yyyy-MM-dd")
        time_element = ET.SubElement(root, "Time")
        time_element.text = QTime.currentTime().toString("HH:mm:ss")
        db_name_element = ET.SubElement(root, "DatabaseName")
        db_name_element.text = project_db_name
        
        db_path_element = ET.SubElement(root, "DatabasePath")
        #db_path_element.text = os.path.relpath(project_db_path, os.path.dirname(file_path))
        db_path_element.text = os.path.join(self.dataFolder, self.projectdatabaseName)
        
        folder_path_element = ET.SubElement(root, "ProjectPath")
        #folder_path_element.text = self.projectFolderPath
        folder_path_element.text = self.projectRelFolderPath
        
        folder_name_element = ET.SubElement(root, "ProjectFolder")
        folder_name_element.text = self.projectFolderName
        data_folder_name_element = ET.SubElement(root, "DataPath")
        data_folder_name_element.text = self.dataFolder
        images_folder_name_element = ET.SubElement(root, "ImagesPath")
        images_folder_name_element.text = self.imagesFolder
        language_element = ET.SubElement(root, "Language")
        language_element.text = self.selectedLanguage
        measurement_system_element = ET.SubElement(root, "MeasurementSystem")
        measurement_system_element.text = self.selectedMeasurementSystem

        tree = ET.ElementTree(root)
        tree.write(file_path)

        self.projectFileCreated = True  # Boolean to indicate if the project file was created


        QMessageBox.information(self, "Save Project", f"Project saved successfully:\n{file_path}")

        # TODO: if project file already created only sava data from tools, etc...after save the file it should also save the data!!!
        # TODO: if project fle already created, lanaguage and measurement system should be save to the project file...
    
   
    def openPlantLayout(self):
        #self.plant_layout_window = PlantLayoutWindow()
        #self.plant_layout_window.show()
        
        #plant_layout_dialog = PlantLayoutWindow(self)
        #plant_layout_dialog.exec_()  # Show the dialog as modal
        
        
        #Dialog = QtWidgets.QDialog()
        #ui = PlantLayoutWindow(self)
        #ui.setupUi(Dialog)
        ##Dialog.show()
        #Dialog.exec_()
        
        self.editToolID = ""
        self.editUnit = ""
        
        plant_layout_dialog = PlantLayoutWindow(self)
        plant_layout_dialog.exec_()  # Show the dialog as modal
        
        if not self.projectFileCreated:
            return
            
        self.loadEditVarsToUI()
        
        
        
    def loadEditVarsToUI(self):
        """Loads saved edit variables into the respective UI controls while managing signals and tab switching."""
    
        # **Validation: Ensure edit variables are not empty before proceeding**
        if not self.editWorkerID or not self.editShiftName or not self.editPlantName or not self.editSectionName or not self.editLineName or not    self.editStationName:
            return  # Exit the function if any required value is empty


        # **Switch to the correct tab in tabWidget based on editToolID**
        tool_tab_map = {"LiFFT": 0, "DUET": 1, "ST": 2}
        tab_index = tool_tab_map.get(self.editToolID, 0)  # Default to tab 0 if not found
        self.tabWidget.setCurrentIndex(tab_index)
        if self.vtk_enabled and hasattr(self, "camera_director"):
            QTimer.singleShot(0, lambda index=tab_index: self.onToolTabClicked(index))
    
        # **Block signals for all combo boxes before updating values**
        self.workerComboBox.blockSignals(True)
        self.shift_combo.blockSignals(True)
        self.plant_combo.blockSignals(True)
        self.section_combo.blockSignals(True)
        self.line_combo.blockSignals(True)
        self.station_combo.blockSignals(True)  # Station combo will be enabled later
    
        # **Set values in the combo boxes if they exist in the list**
        
        # Worker ComboBox
        index = self.workerComboBox.findText(self.editWorkerID)
        if index != -1:
            self.workerComboBox.setCurrentIndex(index)
    
        # Shift ComboBox
        index = self.shift_combo.findText(self.editShiftName)
        if index != -1:
            self.shift_combo.setCurrentIndex(index)
    
        # Plant ComboBox
        index = self.plant_combo.findText(self.editPlantName)
        if index != -1:
            self.plant_combo.setCurrentIndex(index)
    
        # Section ComboBox
        index = self.section_combo.findText(self.editSectionName)
        if index != -1:
            self.section_combo.setCurrentIndex(index)
    
        # Line ComboBox
        index = self.line_combo.findText(self.editLineName)
        if index != -1:
            self.line_combo.setCurrentIndex(index)
    
        index = self.station_combo.findText(self.editStationName)
        if index != -1:
            self.station_combo.setCurrentIndex(index)
    
           
        # **Re-enable signals for all other combo boxes**
        self.workerComboBox.blockSignals(False)
        self.shift_combo.blockSignals(False)
        self.plant_combo.blockSignals(False)
        self.section_combo.blockSignals(False)
        self.line_combo.blockSignals(False)
        self.station_combo.blockSignals(False)
        
        
        self.selectedMeasurementSystem = self.editUnit
        self.metric_action.setChecked(self.selectedMeasurementSystem == "Metric")
        self.imperial_action.setChecked(self.selectedMeasurementSystem == "Imperial")
            
        #print("UI combo boxes updated with saved edit variables.")
        self.loadToolsData()
        
    
    def exportToCSV(self):
        """Export one summary row per worker for the currently selected ergonomic tool."""
        if not hasattr(self, "projectdatabasePath") or not self.projectdatabasePath:
            QMessageBox.warning(
                self,
                "Export Error" if self.language_english_action.isChecked() else "Error de Exportación",
                "No project database is available."
                if self.language_english_action.isChecked()
                else "No hay una base de datos de proyecto disponible."
            )
            return
    
        current_tab_index = self.tabWidget.currentIndex()

        if current_tab_index == 0:
            tool_id = "LiFFT"
        elif current_tab_index == 1:
            tool_id = "DUET"
        elif current_tab_index == 2:
            tool_id = "ST"
        else:
            QMessageBox.warning(
                self,
                "Export Error" if self.language_english_action.isChecked() else "Error de Exportación",
                "Unknown tool tab selected."
                if self.language_english_action.isChecked()
                else "Se seleccionó una pestaña de herramienta desconocida."    
            )
            return

        export_datetime_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_datetime_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        headers = [
            "Export DateTime",
            "Worker ID",
            "Plant",
            "Section",
            "Line",
            "Station",
            "Shift",
            "Tool ID",
            "Total Cumulative Damage",
            "Probability Outcome",
            "Unit"
        ]
    
        csv_data = [headers]
    
        conn = None
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT
                    worker_id,
                    plant_name,
                    section_name,
                    line_name,
                    station_id,
                    shift_id,
                    tool_id,
                    total_cumulative_damage,
                    probability_outcome,
                    unit
                FROM WorkerStationShiftErgoTool
                WHERE tool_id = ?
                ORDER BY plant_name, section_name, line_name, station_id, shift_id, worker_id
            """
            cursor.execute(query, (tool_id,))
            rows = cursor.fetchall()

            if not rows:
                QMessageBox.information(
                    self,
                    "No Data" if self.language_english_action.isChecked() else "Sin Datos",
                    f"No summary records were found for {tool_id}."
                    if self.language_english_action.isChecked()
                    else f"No se encontraron registros resumen para {tool_id}."
                )
                return
    
            for row in rows:
                csv_data.append([
                    export_datetime_str,
                    str(row["worker_id"]).strip() if row["worker_id"] is not None else "",
                    str(row["plant_name"]).strip() if row["plant_name"] is not None else "",
                    str(row["section_name"]).strip() if row["section_name"] is not None else "",
                    str(row["line_name"]).strip() if row["line_name"] is not None else "",
                    str(row["station_id"]).strip() if row["station_id"] is not None else "",
                    str(row["shift_id"]).strip() if row["shift_id"] is not None else "",
                    str(row["tool_id"]).strip() if row["tool_id"] is not None else "",
                    row["total_cumulative_damage"] if row["total_cumulative_damage"] is not None else "",
                    row["probability_outcome"] if row["probability_outcome"] is not None else "",
                    str(row["unit"]).strip() if row["unit"] is not None else ""
                ])
    
            suggested_filename = f"{tool_id}_Summary_AllWorkers_{file_datetime_str}.csv"
            dialog_title = (
                f"Save {tool_id} Summary CSV"
                if self.language_english_action.isChecked()
                else f"Guardar CSV Resumen de {tool_id}"
            )

            filepath, _ = QFileDialog.getSaveFileName(
                self,
                dialog_title,
                suggested_filename,
                "CSV files (*.csv)"
            )

            if not filepath:
                return
    
            with open(filepath, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerows(csv_data)

            QMessageBox.information(
                self,
                "Export Successful" if self.language_english_action.isChecked() else "Exportación Exitosa",
                f"{tool_id} summary data exported successfully to CSV."
                if self.language_english_action.isChecked()
                else f"Los datos resumen de {tool_id} se exportaron correctamente a CSV."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error" if self.language_english_action.isChecked() else "Error de Exportación",
                f"An error occurred while exporting to CSV: {e}"
                if self.language_english_action.isChecked()
                else f"Ocurrió un error al exportar a CSV: {e}"
            )

        finally:
            if conn:
                conn.close()
            
            
    def exportToCSVOld(self):
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
        # Set the dialog window background color to white
        self.authorsDialog.setStyleSheet("background-color: white;")

        # Layout for the dialog
        layout = QVBoxLayout()

        # Add a label with formatted multiline text
        authorsText = (
            "<b>Developed by:</b><br><br>"
            "Dr. Mauricio Henriquez-Schott & Dr. Ivan Nail-Ulloa<br><br>"
            "Project funded by INES 52 R+D, through the Office of Research and Innovation of Universidad Austral de Chile, "
            "and the National Agency of Innovation and Development (ANID).<br><br>"
            "Based on the Fatigue Failure tools from Auburn University, led by Sean Gallagher, Richard Sesek, "
            "Mark Schall, Dania Bani Hani and Rong Huangfu.<br><br>"
            "Original tools can be found here:<br>"
            "<a href='https://eng.auburn.edu/occupational-safety-ergonomics-injury-prevention/research/research-2.html'>"
            "https://eng.auburn.edu/occupational-safety-ergonomics-injury-prevention/research/research-2.html</a>"
        )

        self.authorsLabel = QLabel(authorsText)
        self.authorsLabel.setWordWrap(True)
        self.authorsLabel.setTextFormat(Qt.RichText)
        self.authorsLabel.setOpenExternalLinks(True)  # Makes the link clickable
        layout.addWidget(self.authorsLabel)

        # Add a central logo
        logo_label = QLabel()
        logo_path = '../images/ergologomain01.png'
        pixmap = QPixmap(logo_path)  # Replace with your logo's path
        if pixmap.isNull():
            print("Failed to load the image:", logo_path)
            return

        # Scale the image and align it to the center
        logo_label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Set the layout and size
        self.authorsDialog.setLayout(layout)
        self.authorsDialog.setFixedSize(600, 700)  # Adjust size as needed
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
        
    def setupStatusBar(self):
        # Create or retrieve the status bar
        statusBar = self.statusBar()
        
        # Display a default message
        statusBar.showMessage("Ready", 5000)  # Message displayed for 5 seconds


    def setupDatabase(self):
        # Connect to the SQLite database (it will be created if it doesn't exist)
        conn = sqlite3.connect(self.databasePath)
        cursor = conn.cursor()

        # Drop all existing tables (optional - only if you want to clear everything)
        cursor.execute("PRAGMA foreign_keys=off;")  # Disable foreign key checks temporarily
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table_name in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name[0]};")
        cursor.execute("PRAGMA foreign_keys=on;")  # Re-enable foreign key checks

        # Create the "Worker" table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Worker (
            id TEXT PRIMARY KEY,                      -- Worker ID (alphanumeric)
            first_name TEXT,                          -- First Name
            last_name TEXT,                           -- Last Name
            year_of_birth INTEGER,                   -- Year of Birth
            month_of_birth INTEGER,                  -- Month of Birth
            day_of_birth INTEGER,                    -- Day of Birth
            gender TEXT,                             -- Gender (Male/Female)
            height REAL,                             -- Height (cm)
            weight REAL,                             -- Weight (kg)
            address TEXT,                            -- Address
            email TEXT,                              -- Email
            year_of_hiring INTEGER,                  -- Year of Hiring
            month_of_hiring INTEGER,                 -- Month of Hiring
            day_of_hiring INTEGER,                   -- Day of Hiring
            city TEXT,                               -- City
            state TEXT,                              -- State
            country TEXT,                            -- Country
            zipcode TEXT,                            -- Zip Code
    
            -- Head and Neck Measurements (examples)
            head_circumference REAL,                 -- Head Circumference (cm)
            neck_circumference REAL,                 -- Neck Circumference (cm)
            head_length REAL,                        -- Head Length (cm)
            neck_angle REAL,                         -- Neck Angle (degrees)
            head_angle REAL,                         -- Head Angle (degrees)
    
            -- Upper Body Measurements (examples)
            shoulder_width REAL,                     -- Shoulder Width (cm)
            chest_circumference REAL,                -- Chest Circumference (cm)
            upper_arm_length REAL,                   -- Upper Arm Length (cm)
            forearm_length REAL,                     -- Forearm Length (cm)
            hand_length REAL,                        -- Hand Length (cm)
    
            -- Lower Body Measurements (examples)
            hip_width REAL,                          -- Hip Width (cm)
            leg_length REAL,                         -- Leg Length (cm)
            thigh_length REAL,                       -- Thigh Length (cm)
            foot_length REAL,                        -- Foot Length (cm)
            knee_angle REAL                          -- Knee Angle (degrees)
    
            -- TODO: Add additional measurements from Head and Neck, Upper Body, and Lower Body tabs
        )
        ''')

        
        # Insert a "Default" entry into the Worker table with minimal values, including gender as "Female"
        cursor.execute('''
        INSERT OR IGNORE INTO Worker (
            id, gender
        ) VALUES (
            'Default', 'Female'  -- Worker ID (default to "Default"), Gender set to "Female"
        )
        ''')

        
        
        # Create the "Plant" table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Plant (
            name TEXT PRIMARY KEY,                    -- Plant Name
            description TEXT,                         -- Plant Description
            location TEXT,                            -- Location
            type TEXT,                                -- Type of Plant (e.g., Manufacturing, Processing)
            area REAL,                                -- Area (e.g., square feet)
            number_of_shifts INTEGER,                 -- Number of Shifts
            start_time TEXT,                          -- Start Time (ISO format)
            end_time TEXT,                            -- End Time (ISO format)
            operational_hours REAL,                   -- Calculated Operational Hours
            production_capacity REAL,                 -- Production Capacity
            opening_date TEXT,                        -- Opening Date (ISO format)
            years_of_operation INTEGER,               -- Calculated Years of Operation

            -- Visual elements
            image_name TEXT,                          -- Image Name
            image_path TEXT,                          -- Image Path
            x REAL,                                   -- X Coordinate
            y REAL,                                   -- Y Coordinate
            width REAL,                               -- Width
            height REAL,                              -- Height
            scale_x REAL,                             -- Scale X
            scale_y REAL,                             -- Scale Y
            crop_x REAL,                              -- Crop X
            crop_y REAL,                              -- Crop Y
            crop_width REAL,                          -- Crop Width
            crop_height REAL,                         -- Crop Height
            zoom REAL,                                -- Zoom Level
            rotation REAL,                            -- Rotation
            mirror_h INTEGER,                         -- Horizontal Mirror 
            mirror_V INTEGER                          -- Vertical Mirror
            orientation TEXT,                         -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                               -- Color
            brightness REAL,                          -- Brightness
            contrast REAL,                            -- Contrast
            saturation REAL,                          -- Saturation
            lock INTEGER,                             -- Lock State (0 or 1)
            visible INTEGER,                          -- Visibility (0 or 1)
            transparency REAL,                        -- Transparency (0.0–1.0)
            enable INTEGER                            -- Enable State (0 or 1)
        )
        ''')
        
        # Insert a "Default" entry into the Plant table with default values
        cursor.execute('''
        INSERT OR IGNORE INTO Plant (
            name,
            description,
            location,
            type,
            area,
            number_of_shifts,
            start_time,
            end_time,
            operational_hours,
            production_capacity,
            opening_date,
            years_of_operation
        ) VALUES (
            'Default',                     -- Name
            '',                            -- Description (empty by default)
            '',                            -- Location (empty by default)
            'Other',                       -- Type of Plant (default to "Other")
            NULL,                          -- Area (NULL by default)
            1,                             -- Number of Shifts (default to 1)
            '08:00:00',                    -- Start Time (default to 8:00 AM)
            '17:00:00',                    -- End Time (default to 5:00 PM)
            9.0,                           -- Operational Hours (default to 9.0)
            0,                             -- Production Capacity (default to 0)
            DATE('now'),                   -- Opening Date (default to current date)
            0                              -- Years of Operation (default to 0)
        )
        ''')

        
        
        
        
        
        # Create the "Section" table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Section (
            plant_name TEXT NOT NULL,                         -- Foreign key referencing Plant table
            name TEXT NOT NULL,                               -- Primary key for the Section table
            description TEXT,                                 -- Section description
            location TEXT,                                    -- Section location
            capacity REAL,                                    -- Section capacity
            area REAL,                                        -- Section area
            creation_date TEXT,                               -- Section creation date
    
            -- Visual elements
            x REAL,                                           -- X Coordinate
            y REAL,                                           -- Y Coordinate
            width REAL,                                       -- Width
            height REAL,                                      -- Height
            line_thickness REAL,                              -- Line Thickness
            scale_x REAL,                                     -- Scale X
            scale_y REAL,                                     -- Scale Y
            crop_x REAL,                                      -- Crop X
            crop_y REAL,                                      -- Crop Y
            crop_width REAL,                                  -- Crop Width
            crop_height REAL,                                 -- Crop Height
            zoom REAL,                                        -- Zoom Level
            rotation REAL,                                    -- Rotation
            mirror_h INTEGER,                                 -- Horizontal Mirror
            mirror_v INTEGER,                                 -- Vertical Mirror
            orientation TEXT,                                 -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                                       -- Color
            brightness REAL,                                  -- Brightness
            contrast REAL,                                    -- Contrast
            saturation REAL,                                  -- Saturation
            lock INTEGER,                                     -- Lock State (0 or 1)
            visible INTEGER,                                  -- Visibility (0 or 1)
            transparency REAL,                                -- Transparency (0.0–1.0)
            enable INTEGER,                                   -- Enable State (0 or 1)
        
            PRIMARY KEY (plant_name, name),                   -- Composite primary key (plant_name and section name)
            FOREIGN KEY (plant_name) REFERENCES Plant(name) ON DELETE CASCADE   -- Foreign key relationship with the Plant table
        )
        ''')
        
        # Insert a "Default" entry into the Section table with default values
        cursor.execute('''
        INSERT OR IGNORE INTO Section (
            plant_name,
            name,
            description,
            location,
            capacity,
            area,
            creation_date
        ) VALUES (
            'Default',                     -- Plant Name (default to "Default")
            'Default',                     -- Section Name (default to "Default")
            '',                            -- Description (empty by default)
            '',                            -- Location (empty by default)
            0,                             -- Capacity (NULL by default)
            0,                             -- Area (NULL by default)
            DATE('now')                    -- Creation Date (default to current date)
        )
        ''')

               
        
        # Create the "Line" table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Line (
            plant_name TEXT NOT NULL,                         -- Foreign key referencing Plant table
            section_name TEXT NOT NULL,                       -- Foreign key referencing Section table
            name TEXT NOT NULL,                               -- Primary key for the Line table
            description TEXT,                                 -- Line description
            location TEXT,                                    -- Line location
            products TEXT,                                    -- Products processed by the line
            creation_date TEXT,                               -- Line creation date
        
            -- Visual elements
            x REAL,                                           -- X Coordinate
            y REAL,                                           -- Y Coordinate
            width REAL,                                       -- Width
            height REAL,                                      -- Height
            line_thickness REAL,                              -- Line Thickness
            scale_x REAL,                                     -- Scale X
            scale_y REAL,                                     -- Scale Y
            crop_x REAL,                                      -- Crop X
            crop_y REAL,                                      -- Crop Y
            crop_width REAL,                                  -- Crop Width
            crop_height REAL,                                 -- Crop Height
            zoom REAL,                                        -- Zoom Level
            rotation REAL,                                    -- Rotation
            mirror_h INTEGER,                                 -- Horizontal Mirror
            mirror_v INTEGER,                                 -- Vertical Mirror
            orientation TEXT,                                 -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                                       -- Color
            brightness REAL,                                  -- Brightness
            contrast REAL,                                    -- Contrast
            saturation REAL,                                  -- Saturation
            lock INTEGER,                                     -- Lock State (0 or 1)
            visible INTEGER,                                  -- Visibility (0 or 1)
            transparency REAL,                                -- Transparency (0.0–1.0)
            enable INTEGER,                                   -- Enable State (0 or 1)
            
            -- PRIMARY KEY (plant_name, section_name, name),     -- Composite primary key (plant_name, section_name, line name)
            -- FOREIGN KEY (plant_name) REFERENCES Plant(name),  -- Foreign key relationship with the Plant table
            -- FOREIGN KEY (section_name) REFERENCES Section(name) -- Foreign key relationship with the Section table
            PRIMARY KEY (plant_name, section_name, name),     -- Composite primary key
            FOREIGN KEY (plant_name, section_name) REFERENCES Section (plant_name, name) ON DELETE CASCADE

        )
        ''')
        
        # Insert a "Default" entry into the Line table with default values
        cursor.execute('''
        INSERT OR IGNORE INTO Line (
            plant_name,
            section_name,
            name,
            description,
            location,
            products,
            creation_date
        ) VALUES (
            'Default',                     -- Plant Name (default to "Default")
            'Default',                     -- Section Name (default to "Default")
            'Default',                     -- Line Name (default to "Default")
            '',                            -- Description (empty by default)
            '',                            -- Location (empty by default)
            '',                            -- Products (empty by default)
            DATE('now')                    -- Creation Date (default to current date)
        )
        ''')
        
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Station (
            plant_name TEXT NOT NULL,                         -- Foreign key referencing Plant table
            section_name TEXT NOT NULL,                       -- Foreign key referencing Section table
            line_name TEXT NOT NULL,                          -- Foreign key referencing Line table
            id TEXT NOT NULL,                                 -- Primary key for the Station table
            location TEXT,                                    -- Workstation location
            task_description TEXT,                            -- Description of tasks performed
            equipment_used TEXT,                              -- Equipment used at the workstation
            cycle_time REAL,                                  -- Cycle time (in seconds)
            capacity INTEGER,                                 -- Workstation capacity
            ergonomic_risk_level REAL,                        -- Ergonomic risk level (0-100)
            performance_metric TEXT,                          -- Performance metric (e.g., efficiency %)
            power_consumption REAL,                           -- Power consumption (kW)
            materials_used TEXT,                              -- Materials processed or used at the workstation
            creation_date TEXT,                               -- Workstation creation date
            
            -- Visual elements
            x REAL,                                           -- X Coordinate
            y REAL,                                           -- Y Coordinate
            width REAL,                                       -- Width
            height REAL,                                      -- Height
            line_thickness REAL,                              -- Line Thickness
            scale_x REAL,                                     -- Scale X
            scale_y REAL,                                     -- Scale Y
            crop_x REAL,                                      -- Crop X
            crop_y REAL,                                      -- Crop Y
            crop_width REAL,                                  -- Crop Width
            crop_height REAL,                                 -- Crop Height
            zoom REAL,                                        -- Zoom Level
            rotation REAL,                                    -- Rotation
            mirror_h INTEGER,                                 -- Horizontal Mirror
            mirror_v INTEGER,                                 -- Vertical Mirror
            orientation TEXT,                                 -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                                       -- Color
            brightness REAL,                                  -- Brightness
            contrast REAL,                                    -- Contrast
            saturation REAL,                                  -- Saturation
            lock INTEGER,                                     -- Lock State (0 or 1)
            visible INTEGER,                                  -- Visibility (0 or 1)
            transparency REAL,                                -- Transparency (0.0–1.0)
            enable INTEGER,                                   -- Enable State (0 or 1)
        
            PRIMARY KEY (plant_name, section_name, line_name, id),   -- Composite primary key
            FOREIGN KEY (plant_name, section_name, line_name) 
            REFERENCES Line (plant_name, section_name, name) ON DELETE CASCADE     -- Foreign key relationship with the Line table
        )
        ''')
        
        
        # Insert a "Default" entry into the Station table with default values
        cursor.execute('''
        INSERT OR IGNORE INTO Station (
            plant_name,
            section_name,
            line_name,
            id,
            location,
            task_description,
            equipment_used,
            cycle_time,
            capacity,
            ergonomic_risk_level,
            performance_metric,
            power_consumption,
            materials_used,
            creation_date
        ) VALUES (
            'Default',                     -- Plant Name (default to "Default")
            'Default',                     -- Section Name (default to "Default")
            'Default',                     -- Line Name (default to "Default")
            'Default',                     -- Workstation ID (default to "Default")
            '',                            -- Location (empty by default)
            '',                            -- Task Description (empty by default)
            '',                            -- Equipment Used (empty by default)
            0.0,                           -- Cycle Time (default to 0.0)
            0,                             -- Capacity (default to 0)
            0.0,                           -- Ergonomic Risk Level (default to 0.0)
            '',                            -- Performance Metric (empty by default)
            0.0,                           -- Power Consumption (default to 0.0)
            '',                            -- Materials Used (empty by default)
            DATE('now')                    -- Creation Date (default to current date)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Shift (
            id TEXT NOT NULL PRIMARY KEY,         -- Primary key for the Shift table (independent)
            description TEXT,                     -- Shift description
            start_time TEXT,                      -- Shift start time (HH:MM format)
            end_time TEXT,                        -- Shift end time (HH:MM format)
            shift_type TEXT,                      -- Type of shift (e.g., Morning, Night)
            tasks_performed TEXT,                 -- List of tasks performed
            product_output REAL,                  -- Product output count
            downtime REAL,                         -- Downtime during the shift (in hours)
            incidents_reported TEXT,              -- List of reported incidents
            ergonomic_risk_events TEXT,           -- Ergonomic risk events reported
            notes TEXT                            -- Additional notes
        )
        ''')

        cursor.execute('''
        INSERT OR IGNORE INTO Shift (
            id,
            start_time,
            end_time
        ) VALUES (
            '1',           -- Shift ID (default to "1")
            '08:00',       -- Start Time (default to 8:00 AM)
            '17:00'        -- End Time (default to 5:00 PM)
        )
        ''')


        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ErgoTool (
            id TEXT NOT NULL PRIMARY KEY,   -- Primary key for the ergonomic tool (text format)
            name TEXT NOT NULL,             -- Name of the ergonomic tool
            description TEXT,               -- Description of the tool's purpose
            authors TEXT                    -- Authors or contributors of the tool
        )
        ''')
        
        cursor.executemany('''
        INSERT OR IGNORE INTO ErgoTool (id, name, description, authors) 
            VALUES (?, ?, ?, ?)
            ''', [
            ('LiFFT', 'Lifting Fatigue Failure Tool', '', ''),  # LiFFT tool
            ('DUET', 'Distal Upper Extremity Tool', '', ''),    # DUET tool
            ('ST', 'Shoulder Tool', '', '')         # Shoulder Tool (ST)
        ])

        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS WorkerStationShiftErgoTool (
            worker_id TEXT NOT NULL,               -- Foreign key referencing Worker table
            plant_name TEXT NOT NULL,              -- Foreign key referencing Station table
            section_name TEXT NOT NULL,            -- Foreign key referencing Station table
            line_name TEXT NOT NULL,               -- Foreign key referencing Station table
            station_id TEXT NOT NULL,              -- Foreign key referencing Station table
            shift_id TEXT NOT NULL,                -- Foreign key referencing Shift table
            tool_id TEXT NOT NULL,                 -- Foreign key referencing ErgoTool table
    
            total_cumulative_damage REAL,          -- Cumulative damage percentage
            probability_outcome REAL,              -- Probability of outcome
    
            -- Additional result fields
            result_3 REAL,
            result_4 REAL,
            result_5 REAL,
            result_6 REAL,
            result_7 REAL,
            result_8 REAL,
            result_9 REAL,
            unit TEXT,                             -- Measurement unit (Metric/Imperial)
    
            -- Visual elements
            x REAL,                                -- X Coordinate
            y REAL,                                -- Y Coordinate
            width REAL,                            -- Width
            height REAL,                           -- Height
            line_thickness REAL,                   -- Line Thickness
            scale_x REAL,                          -- Scale X
            scale_y REAL,                          -- Scale Y
            crop_x REAL,                           -- Crop X
            crop_y REAL,                           -- Crop Y
            crop_width REAL,                       -- Crop Width
            crop_height REAL,                      -- Crop Height
            zoom REAL,                             -- Zoom Level
            rotation REAL,                         -- Rotation
            mirror_h INTEGER,                      -- Horizontal Mirror
            mirror_v INTEGER,                      -- Vertical Mirror
            orientation TEXT,                      -- Orientation (e.g., Horizontal, Vertical)
            color TEXT,                            -- Color
            r INTEGER,                             -- Red value (0-255)
            g INTEGER,                             -- Green value (0-255)
            b INTEGER,                             -- Blue value (0-255)
            brightness REAL,                        -- Brightness
            contrast REAL,                          -- Contrast
            saturation REAL,                        -- Saturation
            lock INTEGER,                           -- Lock State (0 or 1)
            visible INTEGER,                        -- Visibility (0 or 1)
            transparency REAL,                      -- Transparency (0.0–1.0)
            enable INTEGER,                         -- Enable State (0 or 1)
    
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id),  
            FOREIGN KEY (worker_id) REFERENCES Worker (id) ON DELETE CASCADE,
            FOREIGN KEY (plant_name, section_name, line_name, station_id) REFERENCES Station (plant_name, section_name, line_name, id) ON DELETE CASCADE,
            FOREIGN KEY (shift_id) REFERENCES Shift (id) ON DELETE CASCADE,
            FOREIGN KEY (tool_id) REFERENCES ErgoTool (id) ON DELETE CASCADE
        )
        ''')

        
        # Create the updated LiFFT Results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS LifftResults (
            worker_id TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            plant_name TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            section_name TEXT NOT NULL,           -- Foreign key referencing WorkerStationShiftErgoTool
            line_name TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            station_id TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            shift_id TEXT NOT NULL,               -- Foreign key referencing WorkerStationShiftErgoTool
            tool_id TEXT NOT NULL,                -- Foreign key referencing WorkerStationShiftErgoTool
            task_id INTEGER NOT NULL,             -- Task identifier
    
            lever_arm REAL,                       -- Lever arm measurement
            load REAL,                            -- Load value
            moment REAL,                          -- Moment calculation
            repetitions INTEGER,                  -- Number of repetitions
            cumulative_damage REAL,               -- Cumulative damage percentage
            percentage_total REAL,                -- Total percentage of risk
    
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id),  
            FOREIGN KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) 
            REFERENCES WorkerStationShiftErgoTool (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) ON DELETE CASCADE
        )
        ''')

        
        
        # Create the updated DUET Results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS DuetResults (
            worker_id TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            plant_name TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            section_name TEXT NOT NULL,           -- Foreign key referencing WorkerStationShiftErgoTool
            line_name TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            station_id TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            shift_id TEXT NOT NULL,               -- Foreign key referencing WorkerStationShiftErgoTool
            tool_id TEXT NOT NULL,                -- Foreign key referencing WorkerStationShiftErgoTool
            task_id INTEGER NOT NULL,             -- Task identifier
        
            omni_res_scale INTEGER,               -- Omni resistance scale
            repetitions INTEGER,                  -- Number of repetitions
            cumulative_damage REAL,               -- Cumulative damage percentage
            percentage_total REAL,                -- Total percentage of risk
        
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id),  
            FOREIGN KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) 
            REFERENCES WorkerStationShiftErgoTool (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) ON DELETE CASCADE
        )        
        ''')

        # Create the updated TST Results table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TstResults (
            worker_id TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            plant_name TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            section_name TEXT NOT NULL,           -- Foreign key referencing WorkerStationShiftErgoTool
            line_name TEXT NOT NULL,              -- Foreign key referencing WorkerStationShiftErgoTool
            station_id TEXT NOT NULL,             -- Foreign key referencing WorkerStationShiftErgoTool
            shift_id TEXT NOT NULL,               -- Foreign key referencing WorkerStationShiftErgoTool
            tool_id TEXT NOT NULL,                -- Foreign key referencing WorkerStationShiftErgoTool
            task_id INTEGER NOT NULL,             -- Task identifier
        
            type_of_task INTEGER,                 -- Type of task
            lever_arm REAL,                       -- Lever arm measurement
            load REAL,                            -- Load value
            moment REAL,                          -- Moment calculation
            repetitions INTEGER,                  -- Number of repetitions
            cumulative_damage REAL,               -- Cumulative damage percentage
            percentage_total REAL,                -- Total percentage of risk
      
            PRIMARY KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id),  
            FOREIGN KEY (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) 
            REFERENCES WorkerStationShiftErgoTool (worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id) ON DELETE CASCADE
        )
        ''')

        

        # Commit changes and close the connection
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
        centralWidget = QtWidgets.QWidget(self)
        centralWidget.setObjectName("mainWorkspace")
        self.setCentralWidget(centralWidget)
        mainLayout = QtWidgets.QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(14, 10, 14, 8)
        mainLayout.setSpacing(10)

        self.setupNavigationButtons()
        self.setupTopWidgets()
        mainLayout.addWidget(self.topContainer)

        self.setupTabsTopControls()

        contentLayout = QtWidgets.QHBoxLayout()
        contentLayout.setSpacing(10)

        model_frame = QFrame()
        model_frame.setObjectName("bodyRegionPanel")
        model_frame.setMinimumWidth(240)
        model_frame.setMaximumWidth(285)
        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.setContentsMargins(14, 14, 14, 12)
        self.leftLayout.setSpacing(8)
        title_layout = QHBoxLayout()
        self.body_region_title = QLabel("LiFFT Body Region")
        self.body_region_title.setObjectName("bodyRegionTitle")
        title_layout.addWidget(self.body_region_title)
        title_layout.addStretch()
        self.leftLayout.addLayout(title_layout)
        self.vtkWidget = QVTKRenderWindowInteractor() if self.vtk_enabled else VTKDisabledWidget()
        self.vtkWidget.setObjectName("vtkWorkspace")
        self.vtkWidget.setMinimumHeight(315)
        self.leftLayout.addWidget(self.vtkWidget, 1)
        if self.vtk_enabled:
            self.setupRenderer()
        else:
            disabled_actor = VTKDisabledActor()
            for actor_name in (
                "humanActor",
                "lowerBackActor",
                "leftForeArmActor",
                "leftHandActor",
                "rightForeArmActor",
                "rightHandActor",
                "leftShoulderActor",
                "rightShoulderActor",
            ):
                setattr(self, actor_name, disabled_actor)
        self.setupControlPanel()
        model_frame.setLayout(self.leftLayout)
        contentLayout.addWidget(model_frame)

        tool_frame = QFrame()
        tool_frame.setObjectName("workspacePanel")
        tool_frame.setMinimumWidth(0)
        tool_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        tool_layout = QVBoxLayout(tool_frame)
        tool_layout.setContentsMargins(6, 6, 6, 6)
        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setObjectName("assessmentTabs")
        self.tabWidget.setIconSize(QSize(36, 36))
        self.tabWidget.tabBar().setElideMode(Qt.ElideNone)
        self.tabWidget.tabBar().setUsesScrollButtons(False)
        self.tabWidget.tabBar().setExpanding(False)
        self.tabWidget.setMinimumWidth(0)
        self.tabWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.tabWidget.currentChanged.connect(self.onTabChange)
        self.tabWidget.tabBarClicked.connect(self.onToolTabClicked)
        self.setupTabWidgets()
        tool_layout.addWidget(self.tabWidget)
        contentLayout.addWidget(tool_frame, 1)

        self.setupResultsSidebar()
        contentLayout.addWidget(self.results_sidebar)
        mainLayout.addLayout(contentLayout, 1)

        mainLayout.addWidget(self.location_context_frame)

        self.setupWorkspaceFooter()
        mainLayout.addWidget(self.workspace_footer)
        self.setStyleSheet(self.mainWorkspaceStyleSheet())
        self.summary_timer = QTimer(self)
        self.summary_timer.timeout.connect(self.refreshAssessmentSummary)
        self.summary_timer.start(300)

    def setupResultsSidebar(self):
        self.results_sidebar = QFrame()
        self.results_sidebar.setObjectName("resultsSidebar")
        self.results_sidebar.setMinimumWidth(230)
        self.results_sidebar.setMaximumWidth(260)
        layout = QVBoxLayout(self.results_sidebar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)

        risk_card = QFrame()
        risk_card.setObjectName("summaryCard")
        # Keep every vertical region deterministic.  The previous 240px card was
        # smaller than its contents, so Qt compressed different gaps on repaint.
        risk_card.setFixedHeight(235)
        risk_layout = QVBoxLayout(risk_card)
        risk_layout.setContentsMargins(10, 10, 10, 10)
        risk_layout.setSpacing(4)
        risk_header_widget = QWidget()
        self.risk_header_widget = risk_header_widget
        risk_header_widget.setFixedHeight(42)
        risk_header = QGridLayout(risk_header_widget)
        risk_header.setContentsMargins(0, 0, 0, 0)
        risk_header.setHorizontalSpacing(4)
        risk_header.setVerticalSpacing(0)
        self.individual_risk_title = QLabel("Individual LiFFT")
        self.individual_risk_title.setObjectName("summaryTitle")
        self.individual_risk_title.setToolTip(
            "Estimated individual probability for the adverse outcome calculated by the active ergonomic tool."
        )
        self.risk_level_title = QLabel("Risk Level")
        self.risk_level_title.setObjectName("summaryTitle")
        self.risk_severity_label = QLabel("Low")
        self.risk_severity_label.setObjectName("riskSeverity")
        self.risk_severity_label.setMinimumWidth(0)
        self.risk_severity_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        risk_header.addWidget(self.individual_risk_title, 0, 0, 1, 2)
        risk_header.addWidget(self.risk_level_title, 1, 0)
        risk_header.addWidget(self.risk_severity_label, 1, 1)
        risk_header.setColumnStretch(0, 1)
        self.risk_gauge = RiskGauge()
        risk_layout.addWidget(risk_header_widget)
        risk_layout.addWidget(self.risk_gauge)
        risk_layout.addStretch(1)
        layout.addWidget(risk_card)

        damage_card = QFrame()
        damage_card.setObjectName("summaryCard")
        damage_layout = QVBoxLayout(damage_card)
        damage_layout.setContentsMargins(8, 6, 8, 6)
        damage_layout.setSpacing(4)
        damage_title = QLabel("Cumulative damage")
        damage_title.setObjectName("summaryTitle")
        damage_title.setToolTip("Combined cumulative damage contribution from the entered tasks.")
        self.damage_value_label = QLabel("0.0000")
        self.damage_value_label.setObjectName("metricValue")
        self.damage_progress = DamageScale()
        self.damage_progress.setToolTip(
            "Cumulative damage scale: 0 at the left, 1 at the midpoint, and values above 2 capped at >2."
        )
        damage_layout.addWidget(damage_title)
        damage_layout.addWidget(self.damage_value_label)
        damage_layout.addWidget(self.damage_progress)
        layout.addWidget(damage_card)

        metrics_card = QFrame()
        metrics_card.setObjectName("summaryCard")
        metrics_layout = QGridLayout(metrics_card)
        metrics_layout.setContentsMargins(8, 6, 8, 6)
        metrics_layout.setHorizontalSpacing(6)
        metrics_layout.setVerticalSpacing(4)
        metrics_title = QLabel("Key metrics")
        metrics_title.setObjectName("summaryTitle")
        metrics_title.setToolTip("A live summary of the task data entered for the active tool.")
        metrics_layout.addWidget(metrics_title, 0, 0, 1, 2)
        self.metric_labels = {}
        for row, (key, label) in enumerate((
            ("tasks", "Tasks"), ("repetitions", "Repetitions"),
            ("average_load", "Average load"), ("max_moment", "Max moment"),
        ), start=1):
            metrics_layout.addWidget(QLabel(label), row, 0)
            value = QLabel("0")
            value.setAlignment(Qt.AlignRight)
            value.setObjectName("metricSmallValue")
            metrics_layout.addWidget(value, row, 1)
            self.metric_labels[key] = value
        layout.addWidget(metrics_card)

        status_card = QFrame()
        self.status_card = status_card
        status_card.setObjectName("summaryCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(8, 6, 8, 6)
        status_layout.setSpacing(3)
        status_title = QLabel("Status")
        status_title.setObjectName("summaryTitle")
        status_title.setToolTip("Indicates whether the active assessment contains data that can be evaluated.")
        self.assessment_status_label = QLabel("Ready")
        self.assessment_status_label.setObjectName("readyStatus")
        self.assessment_status_detail = QLabel("Select a context and enter task data.")
        self.assessment_status_detail.setObjectName("supportingText")
        self.assessment_status_detail.setWordWrap(True)
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.assessment_status_label)
        status_layout.addWidget(self.assessment_status_detail)
        layout.addWidget(status_card)
        layout.addStretch()

    def setupWorkspaceFooter(self):
        self.workspace_footer = QFrame()
        self.workspace_footer.setObjectName("workspaceFooter")
        footer_layout = QHBoxLayout(self.workspace_footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        self.footer_tool_label = QLabel("Tool: LiFFT")
        self.footer_tool_label.setMinimumWidth(115)
        self.footer_tool_label.setToolTip("The ergonomic assessment tool currently selected.")
        self.footer_unit_label = QLabel("Units: Imperial")
        self.footer_unit_label.setToolTip("The measurement system used by the current project.")
        self.footer_context_label = QLabel("No project loaded")
        self.footer_context_label.setToolTip("The project currently open in Ergo Tools.")
        footer_layout.addWidget(self.footer_tool_label)
        footer_layout.addWidget(self.footer_unit_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.footer_context_label)
        self.workspace_footer.setAutoFillBackground(True)

    def activeToolSummaryWidgets(self):
        index = self.tabWidget.currentIndex()
        if index == 0:
            return {
                "name": "LiFFT", "damage": self.lifft_total_damage_value_label,
                "probability": self.lifft_probability_value_label, "color": self.lifft_total_risk_color,
                "inputs": (self.lifft_lever_arm_inputs, self.lifft_load_inputs, self.lifft_repetitions_inputs),
                "moments": [row[3] for row in self.lifft_output_labels_matrix[:len(self.lifft_lever_arm_inputs)]],
            }
        if index == 1:
            return {
                "name": "DUET", "damage": self.duet_total_damage_value_label,
                "probability": self.duet_probability_value_label, "color": self.duet_total_risk_color,
                "inputs": ([], [], self.duet_repetitions_inputs), "moments": [],
            }
        return {
            "name": "Shoulder", "damage": self.tst_total_damage_value_label,
            "probability": self.tst_probability_value_label, "color": self.tst_total_risk_color,
            "inputs": (self.tst_lever_arm_inputs, self.tst_load_inputs, self.tst_repetitions_inputs),
            "moments": [row[4] for row in self.tst_output_labels_matrix[:len(self.tst_lever_arm_inputs)]],
        }

    @staticmethod
    def numericLabelValue(label):
        text = label.text().strip().replace("%", "")
        if text.startswith(">"):
            return 100.0
        if text.startswith("<"):
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0

    def refreshAssessmentSummary(self):
        if not hasattr(self, "tabWidget") or self.tabWidget.count() < 3:
            return
        self.syncStickyHeaders()
        summary = self.activeToolSummaryWidgets()
        self.individual_risk_title.setText(f"Individual {summary['name']}")
        self.styleAssessmentControls()
        lever_inputs, load_inputs, repetition_inputs = summary["inputs"]
        repetition_values = [float(field.text()) for field in repetition_inputs if field.text().strip()]
        task_count = sum(1 for value in repetition_values if value > 0)
        repetitions = sum(int(value) for value in repetition_values if value > 0)
        source_color = QColor(summary["color"])
        ready = bool(task_count and self.projectFileCreated and source_color.isValid())
        probability = self.numericLabelValue(summary["probability"])
        damage = self.numericLabelValue(summary["damage"])
        if not ready:
            probability = 0.0
            damage = 0.0
        display_color = source_color if ready else QColor("#D9E1E6")
        self.risk_gauge.setValue(probability, display_color.name())
        _start, _end, severity_name, severity_color, _range_text = risk_band(probability)
        if ready:
            severity = severity_name.removesuffix(" Risk")
            self.risk_severity_label.setText("● " + severity)
            self.risk_severity_label.setStyleSheet(f"color: {severity_color}; font-weight: 700;")
        else:
            self.risk_severity_label.setText("● Not available")
            self.risk_severity_label.setStyleSheet("color: #6F7E88; font-weight: 700;")
        outcome_text = {
            "LiFFT": "Probability of high-risk\njob",
            "DUET": "Probability of distal upper-\nextremity outcome",
            "Shoulder": "Probability of shoulder\noutcome",
        }[summary["name"]]
        region_context = {
            "LiFFT": ("LiFFT Body Region", "Lower Back"),
            "DUET": ("DUET Body Region", "Distal Upper Extremity"),
            "Shoulder": ("Shoulder Body Region", "Shoulders"),
        }[summary["name"]]
        self.body_region_title.setText(region_context[0])
        self.active_region_label.setText(region_context[1])
        self.body_risk_title.setText(f"{summary['name']} Individual Risk Score")
        self.risk_gauge.setOutcomeText(outcome_text)
        damage_color = display_color
        red = damage_color.redF()
        green = damage_color.greenF()
        blue = damage_color.blueF()
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        readable_damage_color = QColor("#102A43" if luminance > 0.58 else "#FFFFFF")
        self.damage_value_label.setText(">2.0" if damage > 2.0 else f"{damage:.4f}")
        self.damage_value_label.setStyleSheet(
            f"color: {readable_damage_color.name()}; background: {damage_color.name()}; "
            f"border: 1px solid {damage_color.darker(115).name()}; "
            "border-radius: 4px; padding: 7px 10px; font-size: 20px; font-weight: 700;"
        )
        self.damage_progress.setValue(damage, damage_color.name())
        self.styleToolResultSummary(summary, damage_color)
        loads = [float(field.text()) for field in load_inputs if field.text().strip()]
        moments = [self.numericLabelValue(label) for label in summary["moments"] if label]
        self.metric_labels["tasks"].setText(str(task_count))
        self.metric_labels["repetitions"].setText(f"{repetitions:,}")
        self.metric_labels["average_load"].setText(f"{sum(loads) / len(loads):.1f}" if loads else "-")
        self.metric_labels["max_moment"].setText(f"{max(moments):.1f}" if moments else "-")
        self.assessment_status_label.setText("Ready" if ready else "Incomplete")
        self.assessment_status_label.setProperty("ready", ready)
        self.assessment_status_label.style().unpolish(self.assessment_status_label)
        self.assessment_status_label.style().polish(self.assessment_status_label)
        self.assessment_status_detail.setText(
            "Assessment data is available." if ready else "Enter context and task data."
        )
        if self.projectFileCreated:
            project_text = self.projectName or os.path.splitext(os.path.basename(self.projectFilePath))[0] or "Untitled project"
        else:
            project_text = "No project loaded"
        self.project_header_label.setText(
            f"Current Project: {project_text}" + ("  •  Loaded" if self.projectFileCreated else "")
        )
        self.footer_tool_label.setText(f"Tool: {summary['name']}")
        units = getattr(self, "selectedMeasurementSystem", "Imperial")
        self.footer_unit_label.setText(f"Units: {units}")
        self.footer_context_label.setText(project_text)

    def styleToolResultSummary(self, summary, result_color):
        name = summary["name"]
        prefix = {"LiFFT": "lifft", "DUET": "duet", "Shoulder": "tst"}[name]
        damage_label = getattr(self, f"{prefix}_total_damage_label")
        probability_label = getattr(self, f"{prefix}_probability_label")
        damage_value = getattr(self, f"{prefix}_total_damage_value_label")
        probability_value = getattr(self, f"{prefix}_probability_value_label")
        for label in (damage_label, probability_label):
            label.setObjectName("toolResultName")
            label.setStyleSheet("color: #0B326C; font-size: 13px; font-weight: 700; padding-right: 8px;")
        luminance = (0.299 * result_color.red() + 0.587 * result_color.green() + 0.114 * result_color.blue())
        foreground = "#10212B" if luminance > 145 else "#FFFFFF"
        value_style = (
            f"background: {result_color.name()}; color: {foreground}; border-radius: 4px; "
            "font-size: 15px; font-weight: 800; padding: 5px 12px;"
        )
        for value in (damage_value, probability_value):
            value.setObjectName("toolResultValue")
            value.setMinimumHeight(30)
            value.setStyleSheet(value_style)
        self.alignToolSummary(prefix)

    def alignToolSummary(self, prefix):
        config = {
            "lifft": (self.lifft_tab, self.lifft_tab_layout, self.scroll_area, 5),
            "duet": (self.duet_tab, self.duet_tab_layout, self.scroll_area_duet, 3),
            "tst": (self.tst_tab, self.tst_tab_layout, self.scroll_area_tst, 6),
        }
        tab, grid, scroll, damage_column = config[prefix]
        layout = getattr(self, f"{prefix}_summary_layout", None)
        item = grid.itemAtPosition(1, damage_column)
        if not layout or not item or not item.widget():
            return
        name_labels = (
            getattr(self, f"{prefix}_total_damage_label"), getattr(self, f"{prefix}_probability_label"),
        )
        value_labels = (
            getattr(self, f"{prefix}_total_damage_value_label"), getattr(self, f"{prefix}_probability_value_label"),
        )
        label_width = max(label.sizeHint().width() for label in name_labels)
        damage_widget = item.widget()
        if not hasattr(self, "_summary_alignment_cache"):
            self._summary_alignment_cache = {}
        tab.setUpdatesEnabled(False)
        try:
            for widget in name_labels + value_labels:
                widget.show()
            layout.activate()
            for _ in range(4):
                current_value_x = value_labels[0].mapToGlobal(QtCore.QPoint(0, 0)).x()
                target_value_x = damage_widget.mapToGlobal(QtCore.QPoint(0, 0)).x()
                position_delta = target_value_x - current_value_x
                left_margin = max(0, layout.contentsMargins().left() + position_delta)
                available_width = max(0, layout.geometry().width())
                max_left_margin = max(
                    0, available_width - label_width - damage_widget.width() - layout.horizontalSpacing() - 4,
                )
                left_margin = min(left_margin, max_left_margin)
                alignment_key = (left_margin, label_width, damage_widget.width())
                if self._summary_alignment_cache.get(prefix) == alignment_key:
                    break
                self._summary_alignment_cache[prefix] = alignment_key
                for widget in name_labels + value_labels:
                    layout.removeWidget(widget)
                for column in range(layout.columnCount()):
                    layout.setColumnStretch(column, 0)
                    layout.setColumnMinimumWidth(column, 0)
                layout.setContentsMargins(left_margin, 5, 0, 5)
                for row, (label, value) in enumerate(zip(name_labels, value_labels)):
                    label.setFixedWidth(label_width)
                    value.setFixedWidth(damage_widget.width())
                    layout.addWidget(label, row, 0)
                    layout.addWidget(value, row, 1)
                layout.setColumnMinimumWidth(0, label_width)
                layout.setColumnMinimumWidth(1, damage_widget.width())
                layout.setColumnStretch(2, 1)
                layout.invalidate()
                layout.activate()
        finally:
            tab.setUpdatesEnabled(True)
            tab.update()

    def styleAssessmentControls(self):
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        for combo in self.findChildren(QComboBox):
            if combo.property("ergoPopupStyled"):
                continue
            view = combo.view()
            palette = view.palette()
            palette.setColor(QPalette.Base, QColor("#FFFFFF"))
            palette.setColor(QPalette.Text, QColor("#1B2933"))
            palette.setColor(QPalette.Highlight, QColor("#087E91"))
            palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
            view.setPalette(palette)
            view.setItemDelegate(ErgoComboItemDelegate(view))
            view.setStyleSheet(
                "QAbstractItemView { background: white; color: #1B2933; outline: 0; }"
                "QAbstractItemView::item { min-height: 28px; padding: 2px 7px; }"
                "QAbstractItemView::item:selected, QAbstractItemView::item:hover "
                "{ background: #087E91; color: white; }"
            )
            combo.setProperty("ergoPopupStyled", True)
        tools = (
            (0, "lifft", "lifft.png"), (1, "duet", "duet.png"), (2, "tst", "shoulder.png"),
        )
        for tab_index, prefix, tab_icon in tools:
            if tab_index < self.tabWidget.count():
                self.tabWidget.setTabIcon(tab_index, QIcon(os.path.join(icon_root, tab_icon)))
                self.tabWidget.setTabToolTip(tab_index, {
                    0: "LiFFT evaluates lower-back fatigue risk from lifting task demands.",
                    1: "DUET evaluates distal upper-extremity risk using OMNI-Res ratings and repetition exposure.",
                    2: "Shoulder Tool evaluates shoulder fatigue risk from task direction, load, and moment.",
                }[tab_index])
            calculate = getattr(self, f"{prefix}_calculate_button", None)
            reset = getattr(self, f"{prefix}_reset_button", None)
            delete = getattr(self, f"{prefix}_delete_button", None)
            if calculate:
                calculate.setObjectName("calculateButton")
                calculate.setIcon(QIcon(os.path.join(icon_root, "calculate-light.png")))
                calculate.setIconSize(QSize(28, 28))
                calculate.setToolTip("Calculate risk results from the task data currently shown.")
                calculate.style().unpolish(calculate)
                calculate.style().polish(calculate)
            if reset:
                reset.setObjectName("resetButton")
                reset.setIcon(QIcon(os.path.join(icon_root, "undo.png")))
                reset.setIconSize(QSize(26, 26))
                reset.setMaximumWidth(320)
                reset.setToolTip("Clear the active tool's task inputs and calculated results.")
                reset.style().unpolish(reset)
                reset.style().polish(reset)
            if delete:
                delete.setIcon(QIcon(os.path.join(icon_root, "delete.png")))
                delete.setIconSize(QSize(30, 30))
                delete.setFixedSize(40, 40)
                delete.setToolTip("Delete saved data for this tool and assessment context.")
            grid_button = getattr(self, f"{prefix}_grid_button", None)
            if grid_button:
                grid_button.setIcon(QIcon(os.path.join(icon_root, "bodyview.png")))
                grid_button.setIconSize(QSize(30, 30))
                grid_button.setFixedSize(40, 40)
                grid_button.setToolTip("Open the task-data grid view for the active tool.")
        header_tooltips = {
            "lifft_headers_labels_fixed": (
                "Task row number.", "Horizontal distance between the load and the lower back.",
                "Load handled during this task.", "Calculated lower-back moment.",
                "Task repetitions during one work day.", "Calculated cumulative damage for this task.",
                "This task's percentage of total cumulative damage.",
            ),
            "duet_headers_labels_fixed": (
                "Task row number.", "Perceived exertion rating on the OMNI-Resistance scale.",
                "Task repetitions during one work day.", "Calculated cumulative damage for this task.",
                "This task's percentage of total cumulative damage.",
            ),
            "tst_headers_labels_fixed": (
                "Task row number.", "Direction of the shoulder exertion.",
                "Horizontal distance used to calculate shoulder moment.", "Load handled during this task.",
                "Calculated shoulder moment.", "Task repetitions during one work day.",
                "Calculated cumulative damage for this task.", "This task's percentage of total cumulative damage.",
            ),
        }
        for labels_name, tooltips in header_tooltips.items():
            for label, tooltip in zip(getattr(self, labels_name, []), tooltips):
                label.setToolTip(tooltip)
        for fields, tooltip in (
            (getattr(self, "lifft_lever_arm_inputs", []), "Enter the lower-back lever arm for this lifting task."),
            (getattr(self, "lifft_load_inputs", []), "Enter the load handled during this lifting task."),
            (getattr(self, "lifft_repetitions_inputs", []), "Enter repetitions performed during one work day."),
            (getattr(self, "duet_repetitions_inputs", []), "Enter repetitions performed during one work day."),
            (getattr(self, "tst_lever_arm_inputs", []), "Enter the shoulder lever arm for this task."),
            (getattr(self, "tst_load_inputs", []), "Enter the load handled during this shoulder task."),
            (getattr(self, "tst_repetitions_inputs", []), "Enter repetitions performed during one work day."),
        ):
            for field in fields:
                field.setToolTip(tooltip)
        for field in getattr(self, "omnires_dropdowns", []):
            field.setMinimumWidth(250)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field.setToolTip("Select the OMNI-Resistance exertion rating for this task.")
        for field in getattr(self, "tst_type_of_task_dropdowns", []):
            field.setMinimumWidth(0)
            field.setMaximumWidth(220)
            field.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            field.setToolTip("Select the direction of force for this shoulder task.")

    def syncStickyHeaders(self):
        for grid_name, labels_name, body_name, header_widget_name in (
            ("lifft_tab_layout", "lifft_headers_labels_fixed", "scroll_area", "lifft_header_widget"),
            ("duet_tab_layout", "duet_headers_labels_fixed", "scroll_area_duet", "duet_header_widget"),
            ("tst_tab_layout", "tst_headers_labels_fixed", "scroll_area_tst", "tst_header_widget"),
        ):
            grid = getattr(self, grid_name, None)
            labels = getattr(self, labels_name, None)
            if not grid or not labels:
                continue
            for column, label in enumerate(labels):
                item = grid.itemAtPosition(1, column)
                if item and item.widget() and item.widget().width() > 0:
                    header_widget = getattr(self, header_widget_name, None)
                    if header_widget:
                        label.setFixedWidth(item.widget().width())
                        label.setFixedHeight(42)
                        label.setWordWrap(True)
                        margins = grid.getContentsMargins()
                        header_widget.layout().setContentsMargins(*margins)
                        header_widget.layout().setHorizontalSpacing(grid.horizontalSpacing())
            body = getattr(self, body_name, None)
            header_widget = getattr(self, header_widget_name, None)
            if body and header_widget:
                content_width = body.viewport().width() + body.horizontalScrollBar().maximum()
                header_widget.setFixedWidth(max(body.viewport().width(), content_width))

    def createStickyHeader(self, header_layout, prefix):
        header_widget = QWidget()
        header_widget.setObjectName("stickyHeader")
        header_widget.setLayout(header_layout)
        header_scroll = QScrollArea()
        header_scroll.setObjectName("stickyHeaderScroll")
        header_scroll.setFrameShape(QFrame.NoFrame)
        header_scroll.setWidgetResizable(False)
        header_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        header_scroll.setFixedHeight(42)
        header_scroll.setWidget(header_widget)
        setattr(self, f"{prefix}_header_widget", header_widget)
        setattr(self, f"{prefix}_header_scroll", header_scroll)
        return header_scroll

    def bindStickyHeader(self, prefix, body_scroll):
        header_scroll = getattr(self, f"{prefix}_header_scroll")
        body_scroll.horizontalScrollBar().valueChanged.connect(header_scroll.horizontalScrollBar().setValue)

    def mainWorkspaceStyleSheet(self):
        return """
            QMainWindow, QWidget#mainWorkspace { background: #F4F7F9; color: #1B2933; font: 12px "Segoe UI"; }
            QFrame#brandHeader { background: #073E68; border-radius: 7px; }
            QLabel#brandName { color: white; font-size: 36px; font-weight: 700; }
            QLabel#projectName { color: #D9EDF5; font-size: 16px; font-weight: 700; }
            QToolBar#mainToolbar { background: white; border: 0; border-radius: 6px; padding: 5px 7px; spacing: 3px; }
            QToolBar#mainToolbar QToolButton { color: #0B326C; min-width: 63px; padding: 6px 5px; border: 0; }
            QToolBar#mainToolbar QToolButton:hover { background: #EAF7F8; border-radius: 5px; }
            QToolBar#mainToolbar::separator { background: #D5DEE5; width: 1px; margin: 8px 6px; }
            QFrame#contextBar, QFrame#workspacePanel, QFrame#resultsSidebar { background: white; border: 1px solid #D5DEE5; border-radius: 7px; }
            QFrame#bodyRegionPanel { background: #092D45; border: 1px solid #174963; border-radius: 7px; color: white; }
            QFrame#bodyRegionPanel QLabel { color: white; background: transparent; border: 0; }
            QLabel#bodyRegionTitle, QLabel#bodySectionTitle { color: white; font-weight: 700; }
            QLabel#bodyRiskLabel { color: white; font-size: 11px; }
            QLabel#bodyRiskRange { color: white; font-size: 10px; }
            QFrame#activeRegionPanel { background: #092D45; border: 0; }
            QLabel#activeRegionName { background: #092D45; color: white; font-size: 14px; font-weight: 700; }
            QLabel#activeRegionCaption { background: #092D45; color: #66C7FF; font-size: 12px; font-weight: 600; }
            QLabel#bodyInfoIcon { border: 2px solid #D7E6EE; border-radius: 9px; font-weight: 700; min-width: 14px; max-width: 14px; min-height: 14px; max-height: 14px; }
            QLabel#activeRegionName { color: white; font-size: 16px; font-weight: 700; }
            QLabel#activeRegionCaption { color: #42B8E8; font-weight: 600; }
            QFrame#bodyPanelDivider { background: #376077; border: 0; }
            QWidget#vtkWorkspace { background: #092D45; border: 0; }
            QToolButton#modelViewButton { color: white; background: transparent; border: 0; padding: 4px 1px; font-size: 10px; }
            QToolButton#modelViewButton:hover { background: #174963; border-radius: 4px; }
            QLabel#contextLabel, QLabel#panelTitle, QLabel#summaryTitle { color: #0B326C; font-weight: 600; }
            QLabel#dialogTitle { color: #0B326C; font-size: 20px; font-weight: 700; }
            QLabel#contextArrow { color: #08A9B5; font-weight: 700; }
            QLabel#contextSummary { color: #405462; font-size: 12px; font-weight: 600; }
            QPushButton#contextToggleButton {
                text-align: left; color: #0B326C;
                background: transparent; border: 0; padding: 0 4px; font-weight: 700;
            }
            QPushButton#contextToggleButton:hover { color: #087E91; background: #EDF7F8; }
            QLabel#supportingText { color: #405462; font-size: 12px; }
            QFrame#resultsSidebar QLabel { font-size: 13px; }
            QFrame#resultsSidebar QLabel#summaryTitle { font-size: 14px; font-weight: 700; }
            QLabel#riskOutcome { color: #304652; font-size: 13px; font-weight: 650; }
            QComboBox, QLineEdit { min-height: 30px; background: white; border: 1px solid #BCC9D3; border-radius: 5px; padding: 0 8px; }
            QComboBox:focus, QLineEdit:focus { border: 2px solid #08A9B5; }
            QComboBox QAbstractItemView {
                background: white; color: #1B2933; border: 1px solid #9EB0BE;
                selection-background-color: #087E91; selection-color: white;
                outline: 0; padding: 3px;
            }
            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover { background: #087E91; color: white; }
            QPushButton { min-height: 32px; background: white; color: #0B326C; border: 1px solid #9EB0BE; border-radius: 5px; padding: 0 12px; font-weight: 600; }
            QPushButton:hover { background: #EDF7F8; border-color: #08A9B5; }
            QPushButton#compactButton { padding: 0 9px; }
            QPushButton#mainAlphabetButton {
                min-width: 18px; max-width: 18px; min-height: 27px; max-height: 27px;
                padding: 0; border: 0; background: transparent; color: #173544;
                font-size: 11px; font-weight: 850;
            }
            QPushButton#mainAlphabetButton:hover { background: #DDF3F5; color: #0B326C; font-size: 16px; }
            QPushButton#mainAlphabetButton:checked { background: #0B326C; color: white; border-radius: 4px; font-size: 11px; }
            QPushButton#mainAlphabetButton[currentInitial="true"] { color: #001C2B; font-weight: 900; font-size: 13px; }
            QPushButton#mainAlphabetButton:checked[currentInitial="true"] { color: white; }
            QPushButton#mainAlphabetButton:disabled { color: #C7D0D7; font-weight: 600; font-size: 10px; }
            QPushButton#primaryOutlineButton { border: 2px solid #08A9B5; }
            QPushButton#calculateButton { background: #087E91; color: white; border-color: #087E91; }
            QPushButton#calculateButton:hover { background: #096D7C; }
            QPushButton#resetButton { color: #0B326C; }
            QTabWidget#assessmentTabs::pane { border: 0; background: white; }
            QTabWidget#assessmentTabs QTabBar::tab { min-height: 41px; padding: 9px 4px; color: #5F6F7A; border: 0; font-size: 13px; font-weight: 600; }
            QTabWidget#assessmentTabs QTabBar::tab:selected { color: #087E91; font-weight: 600; border-bottom: 3px solid #08A9B5; }
            QScrollArea, QScrollArea QWidget { background: white; border-color: #D5DEE5; }
            QFrame#summaryCard { background: white; border: 1px solid #D5DEE5; border-radius: 6px; }
            QLabel#metricValue { color: #F97316; font-size: 20px; font-weight: 600; }
            QLabel#riskSeverity { font-size: 11px; font-weight: 700; }
            QLabel#metricSmallValue { color: #0B326C; font-size: 14px; font-weight: 750; }
            QLabel#readyStatus { color: #C17B00; font-size: 15px; font-weight: 800; }
            QLabel#readyStatus[ready="true"] { color: #16813A; }
            QProgressBar { min-height: 8px; max-height: 8px; border: 0; background: #DCE4E9; border-radius: 4px; }
            QProgressBar::chunk { background: #08A9B5; border-radius: 4px; }
            QFrame#workspaceFooter { background: #F4F7F9; border: 0; color: #5F6F7A; }
            QFrame#workspaceFooter QLabel { background: transparent; color: #344B5A; font-size: 13px; font-weight: 600; }
            QStatusBar { background: #F4F7F9; color: #5F6F7A; border: 0; }
            QStatusBar::item { border: 0; }
            QGroupBox { color: #0B326C; border: 1px solid #D5DEE5; border-radius: 5px; margin-top: 8px; }
            QSlider::groove:horizontal { height: 5px; background: #D5DEE5; border-radius: 2px; }
            QSlider::handle:horizontal { width: 14px; margin: -5px 0; background: #08A9B5; border-radius: 7px; }
            QToolTip { background: #1B2933; color: white; border: 1px solid #0B326C; padding: 6px; }
        """

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "results_sidebar"):
            self.results_sidebar.setVisible(event.size().width() >= 1450)

    def setupTabsTopControls(self):
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        self.location_context_frame = QFrame()
        self.location_context_frame.setObjectName("contextBar")
        self.tabstop_controls_layout = QVBoxLayout(self.location_context_frame)
        self.tabstop_controls_layout.setContentsMargins(14, 6, 12, 6)
        self.tabstop_controls_layout.setSpacing(6)

        context_disclosure_layout = QHBoxLayout()
        context_disclosure_layout.setContentsMargins(0, 0, 0, 0)

        self.context_toggle_button = QPushButton("Optional Plant Information  >")
        self.context_toggle_button.setObjectName("contextToggleButton")
        self.context_toggle_button.setCheckable(True)
        self.context_toggle_button.setChecked(False)
        self.context_toggle_button.setFixedWidth(280)
        self.context_toggle_button.setToolTip(
            "Show or hide the plant, section, line, station, and shift assessment context."
        )
        self.context_toggle_button.toggled.connect(self.setContextControlsExpanded)
        context_disclosure_layout.addWidget(self.context_toggle_button)
        context_disclosure_layout.addStretch(1)

        self.context_details_widget = QWidget()
        context_details_layout = QHBoxLayout(self.context_details_widget)
        context_details_layout.setContentsMargins(0, 0, 0, 0)
        context_details_layout.setSpacing(8)

        self.plant_combo = QComboBox()
        self.section_combo = QComboBox()
        self.line_combo = QComboBox()
        self.station_combo = QComboBox()
        self.shift_combo = QComboBox()
        self.context_labels = []
        combos = (
            ("Plant", self.plant_combo, self.plantComboIndexChanged),
            ("Section", self.section_combo, self.sectionComboIndexChanged),
            ("Line", self.line_combo, self.lineComboIndexChanged),
            ("Station", self.station_combo, self.stationComboIndexChanged),
            ("Shift", self.shift_combo, self.shiftComboIndexChanged),
        )
        for index, (label_text, combo, callback) in enumerate(combos):
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(os.path.join(
                os.path.dirname(__file__), "..", "assets", "ui-icons", label_text.lower() + ".png"
            )).pixmap(QSize(22, 22)))
            icon_label.setFixedSize(22, 22)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setToolTip(f"{label_text} level of the current assessment context.")
            label = QLabel(label_text)
            label.setObjectName("contextLabel")
            label.setContentsMargins(3, 0, 3, 0)
            label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            self.context_labels.append(label)
            combo.setMinimumWidth(85 if label_text != "Shift" else 70)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.currentIndexChanged.connect(callback)
            combo.setToolTip(f"Select the {label_text.lower()} for this assessment context.")
            context_details_layout.addWidget(icon_label)
            context_details_layout.addWidget(label)
            context_details_layout.addWidget(combo, 1)
            if index < len(combos) - 1:
                arrow = QLabel()
                arrow.setObjectName("contextArrow")
                arrow.setPixmap(QIcon(os.path.join(icon_root, "next.png")).pixmap(QSize(14, 14)))
                arrow.setFixedSize(16, 16)
                arrow.setAlignment(Qt.AlignCenter)
                arrow.setToolTip("Next workplace level")
                context_details_layout.addWidget(arrow)
        for combo, value in (
            (self.plant_combo, "Default"), (self.section_combo, "Default"),
            (self.line_combo, "Default"), (self.station_combo, "Default"), (self.shift_combo, "1"),
        ):
            combo.blockSignals(True)
            combo.addItem(value)
            combo.blockSignals(False)
            combo.currentTextChanged.connect(self.updateContextSummary)

        manage_button = QPushButton("Organization")
        manage_button.setObjectName("primaryOutlineButton")
        manage_button.setFixedWidth(210)
        manage_button.setIcon(QIcon(os.path.join(icon_root, "plant.png")))
        manage_button.setIconSize(QSize(26, 26))
        manage_button.setToolTip("Manage plants, sections, lines, stations, and shifts.")
        manage_button.clicked.connect(self.editOrganizationClicked)
        association_row = QHBoxLayout()
        association_row.setContentsMargins(0, 0, 0, 0)
        association_title = QLabel("Assessment workplace")
        association_title.setObjectName("contextLabel")
        association_title.setToolTip("Workplace and shift associated with the active tool assessment.")
        self.context_summary_widget = QWidget()
        self.context_summary_widget.setToolTip(
            "Plant, section, line, station, and shift for the active assessment."
        )
        context_summary_layout = QHBoxLayout(self.context_summary_widget)
        context_summary_layout.setContentsMargins(0, 0, 0, 0)
        context_summary_layout.setSpacing(5)
        self.context_summary_labels = []
        for index, level_name in enumerate(("Plant", "Section", "Line", "Station", "Shift")):
            value_label = QLabel()
            value_label.setObjectName("contextSummary")
            value_label.setToolTip(f"{level_name} associated with the active assessment.")
            self.context_summary_labels.append(value_label)
            context_summary_layout.addWidget(value_label)
            if index < 4:
                separator = QLabel()
                separator.setObjectName("contextArrow")
                separator.setPixmap(QIcon(os.path.join(icon_root, "next.png")).pixmap(QSize(14, 14)))
                separator.setFixedSize(16, 16)
                separator.setAlignment(Qt.AlignCenter)
                separator.setToolTip("Next workplace level")
                context_summary_layout.addWidget(separator)
        context_summary_layout.addStretch(1)
        association_row.addWidget(association_title)
        association_row.addWidget(self.context_summary_widget, 1)
        choose_button = QPushButton("Change workplace")
        choose_button.setObjectName("primaryOutlineButton")
        choose_button.setIcon(QIcon(os.path.join(icon_root, "station.png")))
        choose_button.setIconSize(QSize(24, 24))
        choose_button.setToolTip("Choose a station and shift from the workplace hierarchy.")
        choose_button.clicked.connect(self.openAssessmentWorkplaceDialog)
        association_row.addWidget(choose_button)
        manage_button.setText("Manage organization")
        association_row.addWidget(manage_button)
        self.tabstop_controls_layout.addLayout(association_row)
        self.context_details_widget.hide()
        self.context_toggle_button.hide()
        self.updateContextSummary()
        return

    def setContextControlsExpanded(self, expanded):
        detail_height = self.context_details_widget.sizeHint().height() + self.tabstop_controls_layout.spacing()
        if expanded:
            self._context_collapsed_window_height = self.height()
            target_height = self._context_collapsed_window_height + detail_height
        else:
            target_height = getattr(
                self, "_context_collapsed_window_height", self.height() - detail_height
            )

        self.context_details_widget.setVisible(expanded)
        self.context_toggle_button.setText(
            "Optional Plant Information  v" if expanded else "Optional Plant Information  >"
        )
        self.context_toggle_button.setToolTip(
            "Hide the optional assessment context."
            if expanded else
            "Show the optional plant, section, line, station, and shift assessment context."
        )
        # The application uses a fixed-size main window. Growing it with the
        # disclosure preserves the VTK viewport and result-card geometry.
        self.setFixedSize(self.width(), target_height)

    def updateContextSummary(self, *args):
        if not hasattr(self, "context_summary_labels"):
            return
        values = [combo.currentText() or fallback for combo, fallback in (
            (self.plant_combo, "Default"), (self.section_combo, "Default"),
            (self.line_combo, "Default"), (self.station_combo, "Default"), (self.shift_combo, "1"),
        )]
        for label, level_name, value in zip(
            self.context_summary_labels,
            ("Plant", "Section", "Line", "Station", "Shift"),
            values,
        ):
            label.setText(f"{level_name}: {value}")

    def openAssessmentWorkplaceDialog(self):
        dialog = AssessmentWorkplaceDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        plant, section, line, station = dialog.selected_path
        combos = (
            self.plant_combo, self.section_combo, self.line_combo,
            self.station_combo, self.shift_combo,
        )
        for combo in combos:
            combo.blockSignals(True)
        try:
            values = (
                (self.plant_combo, self.getPlants() or [], plant),
                (self.section_combo, self.getSections(plant) or [], section),
                (self.line_combo, self.getLines(plant, section) or [], line),
                (self.station_combo, self.getStations(plant, section, line) or [], station),
                (self.shift_combo, self.getShifts() or [], dialog.shift_combo.currentText()),
            )
            for combo, items, value in values:
                combo.clear()
                combo.addItems([str(item) for item in items])
                index = combo.findText(str(value))
                if index >= 0:
                    combo.setCurrentIndex(index)
        finally:
            for combo in combos:
                combo.blockSignals(False)
        self.loadToolsData()
        self.updateContextSummary()
        return

        # Row of controls outside the tabs area
        self.tabstop_controls_layout = QHBoxLayout()
        # Create bold font for labels that need emphasis
        bold_font = QFont()
        bold_font.setBold(True)
        
        
        # Add left spacing before the first control
        #left_spacer = QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        #top_controls_layout.addSpacerItem(left_spacer)

        # Create controls for Plant
        plant_label = QLabel("Plant:")
        plant_label.setFont(bold_font)  # Apply bold font
        self.plant_combo = QComboBox()
        self.plant_combo.setEditable(True)  # Allow the user to write in the combobox
        self.plant_combo.addItems(["Default"])  # Example items
        self.plant_combo.setFixedWidth(200)  # Set the fixed width for the combo box
        # Connect the combo box to an index change event
        self.plant_combo.currentIndexChanged.connect(self.plantComboIndexChanged)

        plant_edit_button = QPushButton()
        plant_edit_button.setIcon(QIcon("../images/edit_icon.png"))
        plant_edit_button.setFixedSize(30, 30)
        plant_edit_button.setIconSize(QtCore.QSize(25, 25))
        plant_edit_button.clicked.connect(self.editPlantClicked)
        
        # Add Plant controls to layout
        self.tabstop_controls_layout.addWidget(plant_label)
        self.tabstop_controls_layout.addWidget(self.plant_combo)
        self.tabstop_controls_layout.addWidget(plant_edit_button)

        self.tabstop_controls_layout.addStretch()  # Add a flexible stretch
        
        # Create controls for Section
        section_label = QLabel("Section:")
        section_label.setFont(bold_font)  # Apply bold font
        self.section_combo = QComboBox()
        self.section_combo.setEditable(True)  # Allow the user to write in the combobox
        self.section_combo.addItems(["Default"])  # Example items
        self.section_combo.setFixedWidth(100)  # Set the fixed width for the combo box
        # Connect the combo box to an index change event
        self.section_combo.currentIndexChanged.connect(self.sectionComboIndexChanged)
        section_edit_button = QPushButton()
        section_edit_button.setIcon(QIcon("../images/edit_icon.png"))
        section_edit_button.setFixedSize(30, 30)
        section_edit_button.setIconSize(QtCore.QSize(25, 25))
        section_edit_button.clicked.connect(self.editSectionClicked)

        # Add Section controls to layout
        self.tabstop_controls_layout.addWidget(section_label)
        self.tabstop_controls_layout.addWidget(self.section_combo)
        self.tabstop_controls_layout.addWidget(section_edit_button)

        self.tabstop_controls_layout.addStretch()  # Add a flexible stretch

        # Create controls for Line
        line_label = QLabel("Line:")
        line_label.setFont(bold_font)  # Apply bold font
        self.line_combo = QComboBox()
        self.line_combo.setEditable(True)  # Allow the user to write in the combobox
        self.line_combo.addItems(["Default"])  # Example items
        self.line_combo.setFixedWidth(100)  # Set the fixed width for the combo box
        # Connect the combo box to an index change event
        self.line_combo.currentIndexChanged.connect(self.lineComboIndexChanged)
        line_edit_button = QPushButton()
        line_edit_button.setIcon(QIcon("../images/edit_icon.png"))
        line_edit_button.setFixedSize(30, 30)
        line_edit_button.setIconSize(QtCore.QSize(25, 25))
        line_edit_button.clicked.connect(self.editLineClicked)

        # Add Line controls to layout
        self.tabstop_controls_layout.addWidget(line_label)
        self.tabstop_controls_layout.addWidget(self.line_combo)
        self.tabstop_controls_layout.addWidget(line_edit_button)

        self.tabstop_controls_layout.addStretch()  # Add a flexible stretch
        
        # Create controls for Station
        station_label = QLabel("Station:")
        station_label.setFont(bold_font)  # Apply bold font
        self.station_combo = QComboBox()
        self.station_combo.setEditable(True)  # Allow the user to write in the combobox
        self.station_combo.addItems(["Default"])  # Example items
        self.station_combo.setFixedWidth(100)  # Set the fixed width for the combo box
        # Connect the combo box to an index change event
        self.station_combo.currentIndexChanged.connect(self.stationComboIndexChanged)
        station_edit_button = QPushButton()
        station_edit_button.setIcon(QIcon("../images/edit_icon.png"))
        station_edit_button.setFixedSize(30, 30)
        station_edit_button.setIconSize(QtCore.QSize(25, 25))
        station_edit_button.clicked.connect(self.editStationClicked)

        # Add Station controls to layout
        self.tabstop_controls_layout.addWidget(station_label)
        self.tabstop_controls_layout.addWidget(self.station_combo)
        self.tabstop_controls_layout.addWidget(station_edit_button)

        self.tabstop_controls_layout.addStretch()  # Add a flexible stretch
        
        # Add vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)  # Vertical Line
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedWidth(10)  # Adjust width for better visibility

        self.tabstop_controls_layout.addWidget(separator)  # Insert separator between Station and Shift controls


        # Create controls for Shift
        shift_label = QLabel("Shift:")
        shift_label.setFont(bold_font)  # Apply bold font
        self.shift_combo = QComboBox()
        self.shift_combo.setEditable(True)  # Allow the user to write in the combobox
        self.shift_combo.addItems(["1"])  # Example items
        self.shift_combo.setFixedWidth(70)  # Set the fixed width for the combo box
        # Connect the combo box to an index change event
        self.shift_combo.currentIndexChanged.connect(self.shiftComboIndexChanged)
        shift_edit_button = QPushButton()
        shift_edit_button.setIcon(QIcon("../images/edit_icon.png"))
        shift_edit_button.setFixedSize(30, 30)
        shift_edit_button.setIconSize(QtCore.QSize(25, 25))
        shift_edit_button.clicked.connect(self.editShiftClicked)

        # Add Shift controls to layout
        self.tabstop_controls_layout.addWidget(shift_label)
        self.tabstop_controls_layout.addWidget(self.shift_combo)
        self.tabstop_controls_layout.addWidget(shift_edit_button)


        # Add spacing between groups
        #top_controls_layout.addStretch()

        # Add the top controls layout to the main layout
        #mainLayout.insertLayout(2, top_controls_layout)
        #mainLayout.addLayout(top_controls_layout)


   
    def setupNavigationButtons(self):
        # Navigation buttons layout
        self.navigationLayout = QtWidgets.QHBoxLayout()

        # Create bold font for button labels
        bold_font = QFont()
        bold_font.setBold(True)

        # First button
        self.first_button = QtWidgets.QPushButton("|<")
        self.first_button.setToolTip("First worker")
        self.first_button.setFont(bold_font)
        self.first_button.clicked.connect(self.firstButtonClicked)  
        self.navigationLayout.addWidget(self.first_button)

        # Previous button
        self.previous_button = QtWidgets.QPushButton("<")
        self.previous_button.setToolTip("Previous worker")
        self.previous_button.setFont(bold_font)
        self.previous_button.clicked.connect(self.previousButtonClicked)  
        self.navigationLayout.addWidget(self.previous_button)

        # Next button
        self.next_button = QtWidgets.QPushButton(">")
        self.next_button.setToolTip("Next worker")
        self.next_button.setFont(bold_font)
        self.next_button.clicked.connect(self.nextButtonClicked)  
        self.navigationLayout.addWidget(self.next_button)

        # Last button
        self.last_button = QtWidgets.QPushButton(">|")
        self.last_button.setToolTip("Last worker")
        self.last_button.setFont(bold_font)
        self.last_button.clicked.connect(self.lastButtonClicked)  
        self.navigationLayout.addWidget(self.last_button)
        for button in (self.first_button, self.previous_button, self.next_button, self.last_button):
            button.setObjectName("navButton")
            button.setFixedSize(38, 36)
            button.setText("")
            button.setIconSize(QSize(24, 24))
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        for button, icon_name in (
            (self.first_button, "first.png"), (self.previous_button, "previous.png"),
            (self.next_button, "next.png"), (self.last_button, "last.png"),
        ):
            button.setIcon(QIcon(os.path.join(icon_root, icon_name)))
    

    
    
    
    # Navigation Handlers
    def firstButtonClicked(self):
        if self.workerComboBox.count() > 0:
            self.workerComboBox.setCurrentIndex(0)
 
    def previousButtonClicked(self):
        current_index = self.workerComboBox.currentIndex()
        if current_index > 0:
            self.workerComboBox.setCurrentIndex(current_index - 1)
 
    def nextButtonClicked(self):
        current_index = self.workerComboBox.currentIndex()
        if current_index < self.workerComboBox.count() - 1:
            self.workerComboBox.setCurrentIndex(current_index + 1)
            
    def lastButtonClicked(self):
        if self.workerComboBox.count() > 0:
            self.workerComboBox.setCurrentIndex(self.workerComboBox.count() - 1)
 
 
 
    def setupTopWidgets(self):
        self.topContainer = QWidget()
        top_layout = QVBoxLayout(self.topContainer)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        header = QFrame()
        header.setObjectName("brandHeader")
        header.setFixedHeight(112)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 10, 8)
        brand_identity = QHBoxLayout()
        brand_identity.setSpacing(12)
        brand_logo = QLabel()
        brand_logo.setObjectName("brandLogo")
        brand_logo.setFixedSize(82, 82)
        brand_logo.setAlignment(Qt.AlignCenter)
        brand_logo.setToolTip("ErgoTools")
        logo_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons", "ergotools_logo.png")
        )
        brand_logo.setPixmap(
            QPixmap(logo_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        brand_box = QVBoxLayout()
        brand_box.setSpacing(2)
        brand = QLabel("ErgoTools")
        brand.setObjectName("brandName")
        self.project_header_label = QLabel("No project loaded")
        self.project_header_label.setObjectName("projectName")
        brand_box.addWidget(brand)
        brand_box.addWidget(self.project_header_label)
        brand_identity.addWidget(brand_logo)
        brand_identity.addLayout(brand_box)
        header_layout.addLayout(brand_identity, 1)

        self.toolbar = QToolBar()
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setFixedHeight(90)
        self.toolbar.setIconSize(QSize(38, 38))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        toolbar_actions = (
            ("new.png", "New", self.toolbarnewWorker), ("open.png", "Open", self.toolbaropenWorker),
            ("save.png", "Save", self.toolbarsaveWorker), ("plot.png", "Layout", self.toolbaropenLayout),
            ("export.png", "Export", self.exportToCSV), ("settings.png", "Settings", self.openNumTasksDialog),
            ("help.png", "Help", self.openHelpPDF),
        )
        for action_index, (icon_name, text, callback) in enumerate(toolbar_actions):
            action = QAction(QIcon(os.path.join(icon_root, icon_name)), text, self)
            action.setToolTip({
                "New": "Create a new project.", "Open": "Open an existing Ergo Tools project.",
                "Save": "Save the current project and assessment data.",
                "Layout": "Open the plant layout workspace.",
                "Export": "Export data from the selected ergonomic tool.",
                "Settings": "Configure the number of task rows and application options.",
                "Help": "Open the Ergo Tools user manual.",
            }[text])
            action.triggered.connect(callback)
            self.toolbar.addAction(action)
            self.toolbar.widgetForAction(action).setFixedHeight(75)
            if action_index in (2, 3, 4, 5):
                self.toolbar.addSeparator()
        header_layout.addWidget(self.toolbar)
        top_layout.addWidget(header)

        worker_bar = QFrame()
        worker_bar.setObjectName("contextBar")
        worker_bar_layout = QVBoxLayout(worker_bar)
        worker_bar_layout.setContentsMargins(14, 7, 12, 7)
        worker_bar_layout.setSpacing(2)
        worker_layout = QHBoxLayout()
        worker_layout.setContentsMargins(0, 0, 0, 0)
        worker_layout.setSpacing(8)
        worker_icon = QLabel()
        worker_icon.setPixmap(QIcon(os.path.join(icon_root, "worker.png")).pixmap(QSize(26, 26)))
        worker_icon.setFixedSize(28, 28)
        worker_icon.setAlignment(Qt.AlignCenter)
        worker_icon.setToolTip("Worker associated with the assessment currently shown.")
        worker_layout.addWidget(worker_icon)
        self.workerLabel = QLabel("Worker")
        self.workerLabel.setObjectName("contextLabel")
        worker_layout.addWidget(self.workerLabel)
        self.workerComboBox = QComboBox()
        self.workerComboBox.setMinimumWidth(280)
        self.workerComboBox.currentIndexChanged.connect(self.workerComboIndexChanged)
        self.workerComboBox.addItem("Default")
        self.workerComboBox.setToolTip("Select the worker whose assessment data you want to view or edit.")
        worker_layout.addWidget(self.workerComboBox, 1)
        self.orderButton = QPushButton("A-Z")
        self.orderButton.setIcon(QIcon(os.path.join(icon_root, "alphabetorder.png")))
        self.orderButton.setToolTip("Change worker ordering.")
        self.orderButton.clicked.connect(self.orderButtonClicked)
        self.editButton = QPushButton("Workers")
        self.editButton.setIcon(QIcon(os.path.join(icon_root, "workermanagement.png")))
        self.editButton.setToolTip("Open Worker Management.")
        self.editButton.clicked.connect(self.editWorkerClicked)
        self.searchButton = QPushButton("Search")
        self.searchButton.setIcon(QIcon(os.path.join(icon_root, "search.png")))
        self.searchButton.setToolTip("Find and select a worker by identifying information.")
        self.searchButton.clicked.connect(self.searchWorkerClicked)
        self.transferButton = QPushButton("Transfer")
        self.transferButton.setIcon(QIcon(os.path.join(icon_root, "transferworkerdata.png")))
        self.transferButton.setToolTip("Transfer worker assessment data to another context.")
        self.transferButton.clicked.connect(self.transferWorkerClicked)
        self.refreshButton = QPushButton("Refresh")
        self.refreshButton.setIcon(QIcon(os.path.join(icon_root, "refresh.png")))
        self.refreshButton.setToolTip("Reload workers and assessment context values from the project.")
        self.refreshButton.clicked.connect(self.refreshWorkerClicked)
        for button in (self.orderButton, self.editButton, self.searchButton, self.transferButton, self.refreshButton):
            button.setObjectName("compactButton")
            button.setIconSize(QSize(22, 22))
            worker_layout.addWidget(button)
        self.transferButton.setIconSize(QSize(30, 30))
        worker_layout.addSpacing(10)
        worker_layout.addLayout(self.navigationLayout)
        worker_bar_layout.addLayout(worker_layout)

        alphabet_layout = QHBoxLayout()
        alphabet_layout.setContentsMargins(100, 0, 0, 0)
        alphabet_layout.setSpacing(3)
        alphabet_label = QLabel("Last name")
        alphabet_label.setObjectName("supportingText")
        alphabet_label.setFixedWidth(68)
        alphabet_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        alphabet_label.setToolTip("Filter the worker selector by the first letter of the last name.")
        alphabet_layout.addWidget(alphabet_label)
        alphabet_layout.addSpacing(5)
        self.main_worker_alphabet_group = QButtonGroup(self)
        self.main_worker_alphabet_group.setExclusive(True)
        self.main_worker_alphabet_buttons = {}
        self.main_worker_alphabet_letter = None
        for value in ["All"] + [chr(code) for code in range(ord("A"), ord("Z") + 1)]:
            button = QPushButton(value)
            button.setObjectName("mainAlphabetButton")
            button.setCheckable(True)
            button.setChecked(value == "All")
            button.setToolTip("Show every worker" if value == "All" else f"Show last names beginning with {value}")
            button.clicked.connect(lambda checked, letter=value: self.setMainWorkerAlphabetFilter(letter))
            self.main_worker_alphabet_group.addButton(button)
            self.main_worker_alphabet_buttons[value] = button
            alphabet_layout.addWidget(button)
        alphabet_layout.addStretch(1)
        worker_bar_layout.addLayout(alphabet_layout)
        top_layout.addWidget(worker_bar)
        self.unit_label = QLabel("Unit: Imperial")
        self.unit = "imperial"
        return

        # Initialize the top container and layout
        self.topContainer = QtWidgets.QWidget()
        self.topLayout = QtWidgets.QVBoxLayout(self.topContainer)

        bold_font = QFont()
        bold_font.setBold(True)

        # Create the toolbar for small action buttons
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(40, 40))  # Slightly smaller icon size
        
        self.toolbar.setStyleSheet("""
            QToolBar {
                background: transparent;
                border-bottom: 1px solid #dcdcdc; 
            }
            QToolButton {
                border: none;
                background: transparent;
            }
            QToolButton:hover {
                border: 1px solid gray;
                background: #f0f0f0;
            }
            QToolButton:pressed {
                background: #d9d9d9;
            }
        """)
        
        #self.toolbar.setMaximumHeight(10)  # Adjust the width as needed
        #self.toolbar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)


        # Add Open Button
        open_action = QAction(QIcon("../images/open_icon01.png"), "New", self)
        open_action.triggered.connect(self.toolbaropenWorker)
        self.toolbar.addAction(open_action)

        # Add New Button
        new_action = QAction(QIcon("../images/new_icon01.png"), "New", self)
        new_action.triggered.connect(self.toolbarnewWorker)
        self.toolbar.addAction(new_action)

        # Add Save Button
        save_action = QAction(QIcon("../images/save_icon01.png"), "Save", self)
        save_action.triggered.connect(self.toolbarsaveWorker)
        self.toolbar.addAction(save_action)

        # Add Layout Viewer Button
        layout_action = QAction(QIcon("../images/layout_icon01.png"), "Layout", self)
        layout_action.triggered.connect(self.toolbaropenLayout)
        self.toolbar.addAction(layout_action)
        
        
        # **Create a Spacer Widget to Push Items to the Right**
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expands to take all available space
        self.toolbar.addWidget(spacer)  # This forces the next widget to be aligned right
        # **Unit Label on the Far Right**
        self.unit_label = QLabel("Unit: Imperial")
        self.unit_label.setFont(bold_font)
        self.unit_label.setStyleSheet("padding-right: 10px;")  # Add spacing on the right
        self.toolbar.addWidget(self.unit_label)  # Add the label at the rightmost position


        
        # Add toolbar to the layout
        self.topLayout.addWidget(self.toolbar)



        # Horizontal layout for worker controls
        worker_controls_layout = QHBoxLayout()

        # Worker Label
        self.workerLabel = QtWidgets.QLabel("Worker:")
        self.workerLabel.setFont(bold_font)
        worker_controls_layout.addWidget(self.workerLabel)

        # Worker ComboBox
        self.workerComboBox = QtWidgets.QComboBox()
        self.workerComboBox.setFixedWidth(400)
        self.workerComboBox.currentIndexChanged.connect(self.workerComboIndexChanged)
        self.workerComboBox.addItems(["Default"])  # Example items
        worker_controls_layout.addWidget(self.workerComboBox)

        # Order Button
        self.orderButton = QtWidgets.QPushButton()
        self.orderButton.setIcon(QIcon("../images/alphaorder01.png"))
        self.orderButton.setFixedSize(30, 30)  # Square button
        self.orderButton.setIconSize(QtCore.QSize(25, 25))
        self.orderButton.clicked.connect(self.orderButtonClicked)
        worker_controls_layout.addWidget(self.orderButton)

        # Edit Button
        self.editButton = QtWidgets.QPushButton()
        self.editButton.setIcon(QIcon("../images/edit_icon.png"))
        self.editButton.setFixedSize(30, 30)  # Square button
        self.editButton.setIconSize(QtCore.QSize(25, 25))
        self.editButton.clicked.connect(self.editWorkerClicked)
        worker_controls_layout.addWidget(self.editButton)
        
        # Search Button
        self.searchButton = QtWidgets.QPushButton()
        self.searchButton.setIcon(QIcon("../images/search_icon.png"))
        self.searchButton.setFixedSize(30, 30)  # Square button
        self.searchButton.setIconSize(QtCore.QSize(25, 25))
        self.searchButton.clicked.connect(self.searchWorkerClicked)
        worker_controls_layout.addWidget(self.searchButton)

        
        # Transfer Button
        self.transferButton = QtWidgets.QPushButton()
        self.transferButton.setIcon(QIcon("../images/transfer_icon01.png"))
        self.transferButton.setFixedSize(30, 30)  # Square button
        self.transferButton.setIconSize(QtCore.QSize(25, 25))
        self.transferButton.clicked.connect(self.transferWorkerClicked)
        worker_controls_layout.addWidget(self.transferButton)
        
        # Refresh Button
        self.refreshButton = QtWidgets.QPushButton()
        self.refreshButton.setIcon(QIcon("../images/refresh_icon.png"))
        self.refreshButton.setFixedSize(30, 30)  # Square button
        self.refreshButton.setIconSize(QtCore.QSize(25, 25))
        self.refreshButton.clicked.connect(self.refreshWorkerClicked)
        worker_controls_layout.addWidget(self.refreshButton)
        
        
        worker_controls_layout.addStretch()  # Push everything to the left
        
        #self.topLayout.addStretch()  # Push everything to the left
        # Add worker controls layout to the top layout
        self.topLayout.addLayout(worker_controls_layout)
        #self.topLayout.addStretch()  # Push everything to the left
        
        # Init unit..TODO: to be remove...check right place once update is done!
        self.unit = ""
        #if self.unitComboBox.currentIndex() == 0: #"English":
        #    self.unit = "english"
        #    self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "inch", "lb", "ft.lb"
        #    self.lifft_color_english, self.lifft_color_metric = "color: #337ab7; font-weight:bold;" , "color: #808080;"
        #elif self.unitComboBox.currentIndex() == 1: #"Metric":
        #    self.unit = "metric"
        #    self.lifft_leverarm_unit, self.lifft_load_unit, self.lifft_moment_unit = "cm", "N", "N.m"
        #    self.lifft_color_english, self.lifft_color_metric = "color: #808080;" , "color: #337ab7; font-weight:bold;"
        self.unit = "imperial" #TODO: to make it work during the update..



    def searchWorkerClicked(self):
        # Validate that the project file and database are created
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before searching.")
            return

        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to perform search.")
            return


        dialog = WorkerSearchDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        self.setMainWorkerAlphabetFilter("All")
        worker_id = dialog.selected_worker_id
        index = next(
            (candidate for candidate in range(self.workerComboBox.count())
             if self.workerComboBox.itemText(candidate).split(" ", 1)[0] == worker_id),
            -1,
        )
        if index >= 0:
            self.workerComboBox.setCurrentIndex(index)

    
    def toolbaropenWorker(self):
        self.openFile()

    def toolbarnewWorker(self):
        self.newFile()

    def toolbarsaveWorker(self):
        self.saveFile()

    def toolbaropenLayout(self):
        self.openPlantLayout()
            

    # Handlers for the buttons
    def orderButtonClicked(self):
        self.setWorkerOrder()    
        self.loadToolsData()
    
    def setWorkerOrder(self):
        #print("Is Numbered Order:", self.isNumberOrder)
        if not self.isNumberOrder:
            self.orderButton.setIcon(QIcon(os.path.join(
                os.path.dirname(__file__), "..", "assets", "ui-icons", "numberorder.png"
            )))
            self.orderButton.setText("ID")
            self.orderButton.setToolTip("Workers are ordered alphabetically. Click to order them by Worker ID.")
            self.loadWorkers(1)
        else:
            self.orderButton.setIcon(QIcon(os.path.join(
                os.path.dirname(__file__), "..", "assets", "ui-icons", "alphabetorder.png"
            )))
            self.orderButton.setText("A-Z")
            self.orderButton.setToolTip("Workers are ordered by Worker ID. Click to order them alphabetically.")
            self.loadWorkers(0)
    
        self.isNumberOrder = not self.isNumberOrder  # Toggle the state
        
    


    def editWorkerClicked(self):
        #QMessageBox.information(self, "Add Worker", "Add Worker button clicked.")
        
        
        self.editWorkerWindowID = ""
        self.editWorkerWindowLastName = ""
        self.editWorkerWindowFirstName = ""
        
        self.workers_window = WorkerWindow(self)
        self.workers_window.exec_()
        
        #self.loadWorkers(0)
        # Update the worker combobox based on the current order (numeric or alphabetic).
        # Determine the order parameter based on the self.isNumberOrder flag
        #order_by = 0 if self.isNumberOrder else 1

        # Call loadWorkers with the appropriate order
        #self.loadWorkers(order_by)
        # Load workers into the combobox...
        #self.isNumberOrder = True
        
        if self.projectFileCreated == True:
            #print("Number Order:", self.isNumberOrder) 
            if self.isNumberOrder:
                self.orderButton.setIcon(QIcon(os.path.join(
                    os.path.dirname(__file__), "..", "assets", "ui-icons", "numberorder.png"
                )))
                self.orderButton.setText("ID")
                self.orderButton.setToolTip("Workers are ordered alphabetically. Click to order them by Worker ID.")
                self.loadWorkers(1)
            else:
                self.orderButton.setIcon(QIcon(os.path.join(
                    os.path.dirname(__file__), "..", "assets", "ui-icons", "alphabetorder.png"
                )))
                self.orderButton.setText("A-Z")
                self.orderButton.setToolTip("Workers are ordered by Worker ID. Click to order them alphabetically.")
                self.loadWorkers(0)
            #self.setWorkerOrder()  
            
            # Format the text as ID (Lastname, Firstname)
            formatted_worker = f"{self.editWorkerWindowID} ({self.editWorkerWindowLastName}, {self.editWorkerWindowFirstName})"

            # Find the index of the formatted worker text in the combo box of the main window
            index = self.workerComboBox.findText(formatted_worker)

            #print("Here...:", self.workerComboBox.currentText())
            # TODO: check why is necesary...
            self.loadToolsData()
 
            # If the index is valid, set the combo box to that index
            if index != -1:
                self.workerComboBox.setCurrentIndex(index)
                
    
    
    
    #def removeWorkerClicked(self):
    #    QMessageBox.information(self, "Remove Worker", "Remove Worker button clicked.")

      
    def refreshWorkerClicked(self):
        self.loadToolsData()


    def transferWorkerClicked(self):
        dialog = WorkerTransferDialog(self)  # Pass the parent window (optional)
        result = dialog.exec_()  # Execute the dialog as a modal window
        self.loadToolsData()
        
        
    def setTasksButtonClicked(self):
        # Implementation for what happens when the "Set Tasks" button is clicked
        self.num_task  = self.numTasksSpinBox.value()
        self.resetAll()
    
    def resetAll(self):
        # TODO: Check to not reset the selected languaje and measurement system for each new...
        # current_language_index = self.languageComboBox.currentIndex()
        
        #self.lifftResetForm()
        #self.duetResetForm()
        #self.tstResetForm()
        self.resetAllPatchs()
        self.tabWidget.removeTab(0)
        self.tabWidget.removeTab(0) # previous "0" reduce the total amount, so allways removing 0 so end up remoging the 3 of them 
        self.tabWidget.removeTab(0)
        
        self.setupTabWidgets()
        
        # TODO: Check to not reset the selected languaje and measurement system for each new...
        #self.changeLanguage(current_language_index)
        
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
        self.rightShoulderActor.VisibilityOff()
        self.leftForeArmActor.VisibilityOff()
        self.leftHandActor.VisibilityOff()
        self.rightForeArmActor.VisibilityOff()
        self.rightHandActor.VisibilityOff()
        self.lowerBackActor.VisibilityOff()
        # Re-render the scene to update the view
        self.vtkWidget.GetRenderWindow().Render()
    
    
    def resetBackPatchs(self):
        self.lowerBackActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.lowerBackActor.VisibilityOff()
        self.vtkWidget.GetRenderWindow().Render()
    
    def resetArmPatchs(self):
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
    
    def resetShoulderPatchs(self):
        self.leftShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.rightShoulderActor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.leftShoulderActor.VisibilityOff()
        self.rightShoulderActor.VisibilityOff()
        self.vtkWidget.GetRenderWindow().Render()
        
    
    def updateUnits(self, index):
        #self.updateUnitsLabels(index)
        
        # Get the current language and measurement system
        if index == 0: #"Imperial":
            self.selectedMeasurementSystem = "Imperial"
        elif index == 1: #"Metric":   
            self.selectedMeasurementSystem = "Metric"	 
        
        self.setUnitText()
        #self.lifftResetForm() # TODO: ..or convert data?,...or don't do anything..


    def updateUnitsLabels(self, index):
        # Check the current text of the lifft_unit_switcher to determine the unit system
        if index == 0: #"English":
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
            
        elif index == 1: #"Metric":
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
            
    
    def updateUnitsLabelsOld(self):
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
            #self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
            self.statusBar().showMessage("Warning: Incomplete Input")
  
            #return  # Exit the function early if any input is incomplete
        
        
        # Step 1: Call calcs...
        #-----------------------------------------------------------------------------------
        #print("lifft calculations - self.num_task:", self.num_task)
        #print(f"Length of lifft_lever_arm_inputs: {len(self.lifft_lever_arm_inputs)}")
        #print(f"Length of lifft_load_inputs: {len(self.lifft_load_inputs)}")
        #print(f"Length of lifft_repetitions_inputs: {len(self.lifft_repetitions_inputs)}")


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
            #print(self.selectedMeasurementSystem)
            if d != '' and l != '' and r != '':
                lifft = LiFFT(self.selectedMeasurementSystem, float(d), float(l), float(r))
                self.lifft_moment[row], self.lifft_damage[row][0], self.lifft_damage[row][1] = lifft.calculate()
                self.lifft_total_damage += self.lifft_damage[row][0]
            elif l != '' and d != '':
                model = LiFFT(self.selectedMeasurementSystem, float(d), float(l), rep=0)
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
            #print("Color:",self.lifft_total_risk_color)
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
        #print("len:", len(self.duet_repetitions_inputs))
        # Check if any input is empty
        if any(input_field.text().strip() == '' for input_field in all_inputs):
            #self.statusBar().showMessage("Warning: Incomplete Input")
            #self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
            self.statusBar().showMessage("Warning: Incomplete Input") #TODO: check if need translate once the update is complete...
 
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
                #self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
                self.statusBar().showMessage("Warning: Incomplete Input") #TODO: check if need translate after the update--
 
                        
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
        #print("len:", len(self.tst_lever_arm_inputs))
        # Check if any input is empty
        if any(input_field.text().strip() == '' for input_field in all_inputs):
            #self.statusBar().showMessage("Warning: Incomplete Input")
            #self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
            self.statusBar().showMessage("Warning: Incomplete Input") #TODO: check if need translate after the update
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
            
            
            #print("Here!:", self.unit)
            
            if d != '' and l != '' and r != '':
                tst = TST(self.selectedMeasurementSystem, str(dire), d, l, r)
                self.tst_moment[row], self.tst_damage[row][0], self.tst_damage[row][1] = tst.calculate()
                self.tst_total_damage += self.tst_damage[row][0]
            elif l != '' and d != '':
                model = TST(self.selectedMeasurementSystem, str(dire), d, l, rep=0)
                self.tst_moment[row], self.tst_damage[row][0], self.tst_damage[row][1] = model.calculate()
                #self.statusBar().showMessage("Warning: Incomplete Input")
                #self.statusBar().showMessage("Warning: Incomplete Input" if self.languageComboBox.currentIndex() == 0 else "Advertencia: Entrada Incompleta")
                self.statusBar().showMessage("Warning: Incomplete Input") #TODO: check if need translate after the update
 
            
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
        ## Example validation for UserID and DateTime; adjust according to your UI elements
        #userid = self.userIDTextbox.text().strip()
        #datetime = self.dateTimeControl.dateTime().toString("yyyy-MM-dd HH:mm")
        #if not userid or not datetime:
        #    return False
            
        #self.validateInputsForSave()
        
        """
        Validates that all required combo boxes have valid selections.
        Displays an error message if any of the required fields are empty.
        """
        # List of required combo boxes
        required_fields = {
            "Worker ID": self.workerComboBox,
            "Plant": self.plant_combo,
            "Section": self.section_combo,
            "Line": self.line_combo,
            "Station": self.station_combo,
            "Shift": self.shift_combo
        }

        # Iterate over required fields and check for empty selections
        for field_name, combo in required_fields.items():
            if combo.currentText().strip() == "":
                #QMessageBox.warning(self, "Validation Error", f"{field_name} cannot be blank.")
                return False # Stop validation immediately if any field is empty

        
        return True
    
    
    def checkForExistingLiFFTData(self):
        """
        Checks if LiFFT data already exists in the LifftResults table for the given worker, 
        station, shift, tool, and task ID.
        
        Returns:
            bool: True if data exists, False otherwise.
        """
        # Validate required selections before proceeding
        self.validateInputsForSave()
    
        
        # Retrieve primary key data from UI elements
        #worker_id = self.workerComboBox.currentText().strip()
        worker_combo_text = self.workerComboBox.currentText()
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tool_id = ""
        tab_index = self.tabWidget.currentIndex()
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed
            
    
        # Ensure all required primary key values are present
        if not all([worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id]):
            QMessageBox.warning(
                self, 
                "Validation Error",
                "All primary key fields must be selected before checking for existing data." 
            )
            return False  # Prevent query execution if validation fails
    
        # Construct query to check for existing data in LifftResults
        query = '''
            SELECT COUNT(*) FROM LifftResults 
            WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
            AND station_id = ? AND shift_id = ? AND tool_id = ? 
        '''
    
        # Execute query
        conn = sqlite3.connect(self.projectdatabasePath)
        cursor = conn.cursor()
        cursor.execute(query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
        result = cursor.fetchone()
        conn.close()
    
        return result[0] > 0  # Returns True if at least one matching record exists, else False




    def workerComboIndexChanged(self, index):
        # If any LiFFT input has changed, prompt the user.
        if self.any_lifft_input_changed or self.any_duet_input_changed or self.any_tst_input_changed:
        
            # Revert the combo box to the previous index.
            self.workerComboBox.blockSignals(True)
            #print(self.previous_worker_index)
            self.workerComboBox.setCurrentIndex(self.previous_worker_index)
                
            self.workerComboBox.blockSignals(False)
                
            reply = QMessageBox.question(
                self,
                "Save Changes",
                "Input values have changed. Do you want to save them?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # User chose to save: call saveToolsData.
                #self.saveToolsData()
                #print(self.workerComboBox.currentText())
                
                # Reset the flag.
                self.any_lifft_input_changed = False
                self.any_duet_input_changed = False
                self.any_tst_input_changed = False
                # Revert the combo box to the previous index.
                #self.workerComboBox.blockSignals(True)
                #self.workerComboBox.setCurrentIndex(self.previous_worker_index)
                
                
                #print(self.workerComboBox.currentText())
                self.saveToolsData()
                
                self.workerComboBox.blockSignals(True)
                
                self.workerComboBox.setCurrentIndex(index)
                self.workerComboBox.blockSignals(False)
                
                # Optionally, you might want to return early.
                #return
            else:
                # User chose not to save: update the stored previous index.
                self.workerComboBox.blockSignals(True)
                self.workerComboBox.setCurrentIndex(index)
                self.workerComboBox.blockSignals(False)
                self.any_lifft_input_changed = False
                self.any_duet_input_changed = False
                self.any_tst_input_changed = False
                #self.previous_worker_index = index

        # Continue with normal processing.
        if hasattr(self, 'tabWidget') and self.tabWidget is not None:
            self.loadToolsData()
            self.previous_worker_index = index
        self.updateMainWorkerCurrentInitial()
            #print(self.previous_worker_index)

    def updateMainWorkerCurrentInitial(self):
        if not hasattr(self, "main_worker_alphabet_buttons"):
            return
        display = self.workerComboBox.currentText()
        surname = display.partition("(")[2].partition(",")[0].strip()
        initial = surname[:1].upper() if surname else ""
        for letter, button in self.main_worker_alphabet_buttons.items():
            button.setProperty("currentInitial", letter == initial)
            button.style().unpolish(button)
            button.style().polish(button)


    
    
    
    def workerComboIndexChangedW(self, index):
        #print("Here?")
        if hasattr(self, 'tabWidget') and self.tabWidget is not None:
            self.loadToolsData()
        #print("Here")
        #return
            
    
    
    def loadToolsData(self):
        ###################### TODO:  FIX ########################
        # TODO: temporary fix, this code is call recursive due to index change events in the comboboxes, it seems it have to do with clearing and adding    
        # items to the combos...some improvement stopping event signal in index change event in plant, section, line, station combos
        # also stopping signal when cleaning and adding items to workers combobox...
        
        stack_size = len(inspect.stack())

        if stack_size >= 6:  # Stop recursion at level 6
            #print(f"Exiting {inspect.stack()[1].function} at recursion level 6")
            return  # Quit function without further recursion
    
        #print(f"Call depth: {stack_size}, Function: {inspect.stack()[1].function}")
        
        ###################### TODO: FIX ########################
        
        

        # Check if a project has been created 
        if not hasattr(self, 'projectFileCreated') or not self.projectFileCreated:
            #QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            #QMessageBox.critical(self, "Error", "Database path is not set. Unable to save Data.")
            return
    
        #if not self.validateInput():
        #    return
            
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
        #print(currentTabIndex)
        
        #valid, userid, datetime = 0, 0, 0 #TODO: remove..
        
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        #worker_id = self.workerComboBox.currentText().strip()
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed

        self.selectedMeasurementSystem = self.default_metric_sys  # Start setting it as the project default..

        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            #print(f"An error occurred: {e}")
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

            return



        # Query LiFFT Tasks
        query = '''SELECT task_id, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total
                   FROM LifftResults 
                   WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
                   ORDER BY task_id'''
        cursor.execute(query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))

        # Fetch all matching records
        tasks_lifft = cursor.fetchall()

         # Query LiFFT unit
        cursor.execute('''
            SELECT total_cumulative_damage, probability_outcome, unit
            FROM WorkerStationShiftErgoTool
            WHERE worker_id=? AND plant_name=? AND section_name=? 
            AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
        ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
        # Fetch the result (expecting only one row)
        result = cursor.fetchone()
        # Assign values to variables, defaulting to 0 if result is None
        lifft_total_cumulative_damage, lifft_probability_outcome, self.lifft_unit = 0, 0, ""
        if result:
            lifft_total_cumulative_damage, lifft_probability_outcome, self.lifft_unit = result
        else:
            lifft_total_cumulative_damage, lifft_probability_outcome, self.lifft_unit = 0, 0, ""
            
        #print("Lifft unit:", lifft_unit) 




        # Query DUET Tasks
        query = '''
            SELECT task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total
            FROM DuetResults 
            WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                  AND station_id=? AND shift_id=? AND tool_id=?
            ORDER BY task_id
        '''
        cursor.execute(query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))

        # Fetch all matching records
        tasks_duet = cursor.fetchall()
            
  
  
        # Query DUET Unit
        cursor.execute('''
            SELECT total_cumulative_damage, probability_outcome, unit
            FROM WorkerStationShiftErgoTool
            WHERE worker_id=? AND plant_name=? AND section_name=? 
            AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
        ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
 
        # Fetch the result (expecting only one row)
        result = cursor.fetchone()

        # Assign values to variables, defaulting to 0 if result is None
        duet_total_cumulative_damage, duet_probability_outcome, self.duet_unit = 0, 0, ""
        if result:
            duet_total_cumulative_damage, duet_probability_outcome, self.duet_unit = result
        else:
            duet_total_cumulative_damage, duet_probability_outcome, self.duet_unit = 0, 0, ""
        
        
            
            
        # Query TST Tasks
        query = '''
            SELECT task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total
            FROM TstResults 
            WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                  AND station_id=? AND shift_id=? AND tool_id=?
            ORDER BY task_id
        '''
        cursor.execute(query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
        # Fetch all matching records
        tasks_tst = cursor.fetchall()

        # Query TST Unit
        cursor.execute('''
            SELECT total_cumulative_damage, probability_outcome, unit
            FROM WorkerStationShiftErgoTool
            WHERE worker_id=? AND plant_name=? AND section_name=? 
            AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
        ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))

        # Fetch the result (expecting only one row)
        result = cursor.fetchone()
        # Assign values to variables, defaulting to 0 if result is None
        tst_total_cumulative_damage, tst_probability_outcome, self.tst_unit = 0, 0, ""
        if result:
            tst_total_cumulative_damage, tst_probability_outcome, self.tst_unit = result
        else:
            tst_total_cumulative_damage, tst_probability_outcome, self.tst_unit = 0, 0, ""
            

        self.tabWidget.removeTab(0)
        if not tasks_lifft:
            self.num_task = self.default_num_task  
 
        else:
            self.num_task = len(tasks_lifft)
        self.num_task_lift = self.num_task    
        self.setupLiFFTTab()
        
               
        
        self.tabWidget.removeTab(1)
        if not tasks_duet:
            self.num_task = self.default_num_task  
 
        else:
            self.num_task = len(tasks_duet)
        self.num_task_duet = self.num_task
        self.setupDUETTab()
        
        
        
        self.tabWidget.removeTab(2)
        if not tasks_tst:
            self.num_task = self.default_num_task  
 
        else:
            self.num_task = len(tasks_tst)
        self.num_task_tst = self.num_task
        self.setupTSTTab()
        
        
        
        # Clean all colors patches 
        self.resetAllPatchs()
            
        
        
        # LiFFT Tasks...
        if tasks_lifft:
            for task in tasks_lifft:
                task_id, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total = task
                
                index = task_id - 1  # Adjusting task_id to match list indexing

                # Populate the input fields
                self.lifft_lever_arm_inputs[index].setText("" if lever_arm in [0, 0.0] else str(lever_arm))
                self.lifft_load_inputs[index].setText("" if load in [0, 0.0] else str(load))
                self.lifft_repetitions_inputs[index].setText("" if repetitions in [0, 0.0] else str(repetitions))

                # Populate the output labels
                self.lifft_output_labels_matrix[index][3].setText(str(moment))  # Example for moment
                self.lifft_output_labels_matrix[index][5].setText(str(cumulative_damage))  # For cumulative damage
                self.lifft_output_labels_matrix[index][6].setText(str(percentage_total))  # For percentage of total damage

        
        
        if not tasks_lifft:
            self.num_task = self.default_num_task  
        else:
            self.num_task = len(tasks_lifft)
        if self.lifft_unit:
            self.selectedMeasurementSystem = self.lifft_unit
        else:
            self.selectedMeasurementSystem = self.default_metric_sys
        if self.selectedMeasurementSystem in ["Metric", "Imperial"]:
            self.lifftCalculateResults()
        else:
            self.resetBackPatchs()
            
            
        # DUET Tasks...
        if tasks_duet:
            for task in tasks_duet:
                task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total = task

                index = task_id - 1  # Adjusting task_id to match list indexing

                # Populate the combo box and input fields
                self.omnires_dropdowns[index].setCurrentIndex(omni_res_scale)
                self.duet_repetitions_inputs[index].setText(str(repetitions))

                # Populate the output labels
                self.duet_output_labels_matrix[index][3].setText(str(cumulative_damage))  # For cumulative damage
                self.duet_output_labels_matrix[index][4].setText(str(percentage_total))  # For percentage of total damage

        
        if not tasks_duet:
            self.num_task = self.default_num_task  
        else:
            self.num_task = len(tasks_duet)
        if self.duet_unit:
            self.selectedMeasurementSystem = self.duet_unit
        else:
            self.selectedMeasurementSystem = self.default_metric_sys
        if self.selectedMeasurementSystem in ["Metric", "Imperial"]:
            self.duetCalculateResults()
        else:
            self.resetArmPatchs()
        
        # TST Tasks...
        if tasks_tst:
            for task in tasks_tst:
                task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total = task
            
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
        
        if not tasks_tst:
            self.num_task = self.default_num_task
        else:
            self.num_task = len(tasks_tst) 
        if self.tst_unit:
            self.selectedMeasurementSystem = self.tst_unit
        else:
            self.selectedMeasurementSystem = self.default_metric_sys
        if self.selectedMeasurementSystem in ["Metric", "Imperial"]:
            self.tstCalculateResults()
        else:
            self.resetShoulderPatchs()
        
        
        
        self.tabWidget.setCurrentIndex(currentTabIndex)
        
        if currentTabIndex == 0 and self.lifft_unit in ["Metric", "Imperial"]:
            self.selectedMeasurementSystem = self.lifft_unit
        elif currentTabIndex == 1 and self.duet_unit in ["Metric", "Imperial"]:
            self.selectedMeasurementSystem = self.duet_unit
        elif currentTabIndex == 2 and self.tst_unit in ["Metric", "Imperial"]:
            self.selectedMeasurementSystem = self.tst_unit
        else:
            self.selectedMeasurementSystem = self.default_metric_sys
    
        self.metric_action.setChecked(self.selectedMeasurementSystem.lower() == "metric")
        self.imperial_action.setChecked(self.selectedMeasurementSystem.lower() == "imperial")
    
        self.setUnitText()
        
        self.any_lifft_input_changed = False
        self.any_duet_input_changed = False
        self.any_tst_input_changed = False
    
             
         
    def setLiFFTColors(self, conn, worker_id, plant_name, section_name, line_name, station_id, shift_id):
        cursor = conn.cursor()
        # Execute query to fetch the color field from DUET if Exist to fill the avatar...
        cursor.execute('''
            SELECT color
            FROM WorkerStationShiftErgoTool
            WHERE worker_id=? AND plant_name=? AND section_name=? 
            AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
        ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
            
        # Fetch the result (expecting only one row)
        result = cursor.fetchone()
            
        # Assign the value to a variable, defaulting to None if result is None
        color_value = result[0] if result else None
            
        # Check if the color is valid and not 'none' or 'None'
        if color_value and color_value != 'none' and color_value != 'None':
            # Assuming self.lifft_total_risk_color is a string like '#RRGGBB'
            # Convert hexadecimal color to a tuple of RGB values (0 to 1 range)
            color = self.hexColorToRGB(color_value)
        
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
        
    
    def setDUETColors(self, conn, worker_id, plant_name, section_name, line_name, station_id, shift_id):
        cursor = conn.cursor()
        # Execute query to fetch the color field from DUET if Exist to fill the avatar...
        cursor.execute('''
            SELECT color
            FROM WorkerStationShiftErgoTool
            WHERE worker_id=? AND plant_name=? AND section_name=? 
            AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
        ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
            
        # Fetch the result (expecting only one row)
        result = cursor.fetchone()
            
        # Assign the value to a variable, defaulting to None if result is None
        color_value = result[0] if result else None
            
        # Check if the color is valid and not 'none' or 'None'
        if color_value and color_value.lower() != 'none' and color_value.lower() != 'None':
            # Convert hexadecimal color to a tuple of RGB values (0 to 1 range)
            color = self.hexColorToRGB(color_value)
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
    
    
    def setTSTColors(self, conn, worker_id, plant_name, section_name, line_name, station_id, shift_id):
        cursor = conn.cursor()
        # Execute query to fetch the color field from ST if Exist to fill the avatar...
        cursor.execute('''
            SELECT color
            FROM WorkerStationShiftErgoTool
            WHERE worker_id=? AND plant_name=? AND section_name=? 
            AND line_name=? AND station_id=? AND shift_id=? AND tool_id=?
        ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
            
        # Fetch the result (expecting only one row)
        result = cursor.fetchone()
            
        # Assign the value to a variable, defaulting to None if result is None
        color_value = result[0] if result else None
        
        # Check if the color is valid and not 'none' or 'None'
        if color_value and color_value != 'none' and color_value != 'None':
            # Assuming self.tst_total_risk_color is a string like '#RRGGBB'
            # Convert hexadecimal color to a tuple of RGB values (0 to 1 range)
            color = self.hexColorToRGB(color_value)
        
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
        
    
    
    def checkForExistingDUETData(self):
        """
        Checks if DUET data already exists in the LifftResults table for the given worker, 
        station, shift, tool, and task ID.
        
        Returns:
            bool: True if data exists, False otherwise.
        """
        # Validate required selections before proceeding
        self.validateInputsForSave()
    
        # Retrieve primary key data from UI elements
        #worker_id = self.workerComboBox.currentText().strip()
        worker_combo_text = self.workerComboBox.currentText()
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tool_id = ""
        tab_index = self.tabWidget.currentIndex()
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed
            
    
        # Ensure all required primary key values are present
        if not all([worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id]):
            QMessageBox.warning(
                self, 
                "Validation Error",
                "All primary key fields must be selected before checking for existing data." 
            )
            return False  # Prevent query execution if validation fails
    
        # Construct query to check for existing data in LifftResults
        query = '''
            SELECT COUNT(*) FROM DuetResults 
            WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
            AND station_id = ? AND shift_id = ? AND tool_id = ? 
        '''
    
        # Execute query
        conn = sqlite3.connect(self.projectdatabasePath)
        cursor = conn.cursor()
        cursor.execute(query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
        result = cursor.fetchone()
        conn.close()
    
        return result[0] > 0  # Returns True if at least one matching record exists, else False

    
    def checkForExistingSTData(self):
        """
        Checks if DUET data already exists in the LifftResults table for the given worker, 
        station, shift, tool, and task ID.
        
        Returns:
            bool: True if data exists, False otherwise.
        """
        # Validate required selections before proceeding
        self.validateInputsForSave()
    
        # Retrieve primary key data from UI elements
        #worker_id = self.workerComboBox.currentText().strip()
        worker_combo_text = self.workerComboBox.currentText()
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tool_id = ""
        tab_index = self.tabWidget.currentIndex()
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed
            
    
        # Ensure all required primary key values are present
        if not all([worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id]):
            QMessageBox.warning(
                self, 
                "Validation Error",
                "All primary key fields must be selected before checking for existing data." 
            )
            return False  # Prevent query execution if validation fails
    
        # Construct query to check for existing data in LifftResults
        query = '''
            SELECT COUNT(*) FROM TstResults 
            WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
            AND station_id = ? AND shift_id = ? AND tool_id = ? 
        '''
    
        # Execute query
        conn = sqlite3.connect(self.projectdatabasePath)
        cursor = conn.cursor()
        cursor.execute(query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
        result = cursor.fetchone()
        conn.close()
    
        return result[0] > 0  # Returns True if at least one matching record exists, else False

    
    
    
    def validateInputsForSaveOld(self):
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
        
        
    def validateInputsForSave(self):
        """
        Validates that all required combo boxes have valid selections.
        Displays an error message if any of the required fields are empty.
        """
        # List of required combo boxes
        required_fields = {
            "Worker ID": self.workerComboBox,
            "Plant": self.plant_combo,
            "Section": self.section_combo,
            "Line": self.line_combo,
            "Station": self.station_combo,
            "Shift": self.shift_combo
        }

        # Iterate over required fields and check for empty selections
        for field_name, combo in required_fields.items():
            if combo.currentText().strip() == "":
                QMessageBox.warning(self, "Validation Error", f"{field_name} cannot be blank.")
                return  # Stop validation immediately if any field is empty
    
    
    
    def saveToolsData(self): 
        # Check if a project has been created 
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded. Please create or load a project before saving workers.")
            return
    
        # Ensure the database path is accessible
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set. Unable to save Data.")
            return
    
        self.saveLiFFTToolData()
        self.saveDUETToolData()
        self.saveTSTToolData()
        
    
    def saveLiFFTToolData(self):
    
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
         
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        
        unit = self.selectedMeasurementSystem 
        
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed

        # Default values for other fields
        #x, y = 10, 10
        x = random.randint(10, 15)
        y = random.randint(10, 15)

        width, height = 50, 50
        line_thickness = 1
        scale_x, scale_y = 1, 1
        lock, transparency = 0, 0
        visible, enable = 0, 1      # TODO: by default visible should be 0, after the plant_layout is working...
        orientation = ""
        default_value = 0  # For all other numeric fields
         
        self.validateInputsForSave()
        
        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return
    
    
        # LiFFT..........................................................................................................................................
        total_cumulative_damage = float(self.lifft_total_damage_value_label.text().strip()) if self.lifft_total_damage_value_label.text().strip() else 0
        probability_text = self.lifft_probability_value_label.text().strip()
        if probability_text == "> 90":
            probability_outcome = 100
        elif probability_text == "< 5":
            probability_outcome = 0
        else:
            probability_outcome = float(probability_text) if probability_text else 0
            
        color = self.lifft_total_risk_color
        
        if self.checkForExistingLiFFTData():
            reply = QMessageBox.question(self, 'Data Exists', "Existing LiFFT data found for this Worker, Station and Shift. Update the data?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
               
        #if not self.anyLiFFTTaskDataPresent():
        #    QMessageBox.warning(self, "No Data", "At least one task must have data to save LiFFT.")
        #    return          
        
        if self.anyLiFFTTaskDataPresent():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Delete existing records for the given userid and datetime
                delete_query = '''
                    DELETE FROM LifftResults 
                    WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ? AND tool_id = ? 
                '''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
                conn.commit()
                
                
                
                # **Check if an entry with the same primary key exists**
                cursor.execute('''
                    SELECT x, y, width, height, line_thickness, scale_x, scale_y, lock, transparency, 
                           visible, enable, orientation 
                    FROM WorkerStationShiftErgoTool
                    WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                          AND station_id=? AND shift_id=? AND tool_id=?
                ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))

                existing_entry = cursor.fetchone()

                # **Store values if an entry exists**
                if existing_entry:
                    x, y, width, height, line_thickness, scale_x, scale_y, lock, transparency, visible, enable, orientation = existing_entry



                # Delete existing entry with the same primary key
                delete_query = '''DELETE FROM WorkerStationShiftErgoTool 
                                  WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                                  AND station_id=? AND shift_id=? AND tool_id=?'''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
                conn.commit()
                
                # Insert new entry
                insert_query = '''INSERT INTO WorkerStationShiftErgoTool (
                                    worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id,
                                    total_cumulative_damage, probability_outcome,
                                    result_3, result_4, result_5, result_6, result_7, result_8, result_9, unit,
                                    x, y, width, height, line_thickness, scale_x, scale_y, 
                                    crop_x, crop_y, crop_width, crop_height, zoom, rotation, 
                                    mirror_h, mirror_v, orientation, color, r, g, b, brightness, 
                                    contrast, saturation, lock, visible, transparency, enable
                                  ) VALUES (
                                    ?, ?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?
                                )'''
        
                cursor.execute(insert_query, (
                    worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT",
                    total_cumulative_damage, probability_outcome,
                    default_value, default_value, default_value, default_value, default_value, default_value, default_value, unit,
                    x, y, width, height, line_thickness, scale_x, scale_y, 
                    default_value, default_value, default_value, default_value, default_value, default_value, default_value, default_value, 
                    orientation, color, default_value, default_value, default_value, default_value, 
                    default_value, default_value, lock, visible, transparency, enable
                ))
                conn.commit()

                # Insert new records for each task in LifftResults
                insert_query = '''INSERT INTO LifftResults (
                                    worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id, 
                                    lever_arm, load, moment, repetitions, cumulative_damage, percentage_total
                                  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            
                for i in range(self.num_task_lift):
                    task_id = i + 1  # Task ID, starting from 1
                    lever_arm = self.lifft_lever_arm_inputs[i].text().strip()
                    load = self.lifft_load_inputs[i].text().strip()
                    moment = self.lifft_output_labels_matrix[i][3].text().strip()  # Moment value
                    repetitions = self.lifft_repetitions_inputs[i].text().strip()
                    cumulative_damage = self.lifft_output_labels_matrix[i][5].text().strip()
                    percentage_total = self.lifft_output_labels_matrix[i][6].text().strip()
            
                    # Convert numeric values to appropriate types
                    lever_arm = float(lever_arm) if lever_arm else 0
                    load = float(load) if load else 0
                    moment = float(moment) if moment else 0
                    repetitions = int(repetitions) if repetitions else 0
                    cumulative_damage = float(cumulative_damage) if cumulative_damage else 0
                    percentage_total = float(percentage_total) if percentage_total else 0
                
                    # Execute the insertion
                    cursor.execute(insert_query, (
                        worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT", task_id,
                        lever_arm, load, moment, repetitions, cumulative_damage, percentage_total
                    ))
                
                conn.commit()
                QMessageBox.information(self, "Success", "LiFFT data saved successfully.")
    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

            finally:
                if conn:
                    conn.close()
            
            
        
        
    def saveDUETToolData(self):        
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
         
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        
        unit = self.selectedMeasurementSystem 
        
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed

        # Default values for other fields
        #x, y = 10, 10
        x = random.randint(10, 15)
        y = random.randint(10, 15)

        width, height = 50, 50
        line_thickness = 1
        scale_x, scale_y = 1, 1
        lock, transparency = 0, 0
        visible, enable = 0, 1      # TODO: by default visible should be 0, after the plant_layout is working...
        orientation = ""
        default_value = 0  # For all other numeric fields
         
        self.validateInputsForSave()
        
        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return
        
        # DUET ........................................................................................................................................
        total_cumulative_damage = float(self.duet_total_damage_value_label.text().strip()) if self.duet_total_damage_value_label.text().strip() else 0
        probability_text = self.duet_probability_value_label.text().strip()
        if probability_text == "> 90":
            probability_outcome = 100
        elif probability_text == "< 5":
            probability_outcome = 0
        else:
            probability_outcome = float(probability_text) if probability_text else 0
        
        color = self.duet_total_risk_color         

        # Check if data already in the db
        if self.checkForExistingDUETData():
            reply = QMessageBox.question(self, 'Data Exists', "Existing DUET data found for this Worker, Station and Shift. Update the data?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
                    
        # Check for tasks present in the UI        
        #if not self.anyDUETTaskDataPresent():
        #    QMessageBox.warning(self, "No Data", "At least one task must have data to save for DUET." )
        #    return
        
        if self.anyDUETTaskDataPresent():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Delete existing records for the given userid and datetime
                delete_query = '''
                    DELETE FROM DuetResults 
                    WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ? AND tool_id = ? 
                '''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
                conn.commit()
                    
                
                # **Check if an entry with the same primary key exists**
                cursor.execute('''
                    SELECT x, y, width, height, line_thickness, scale_x, scale_y, lock, transparency, 
                           visible, enable, orientation 
                    FROM WorkerStationShiftErgoTool
                    WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                          AND station_id=? AND shift_id=? AND tool_id=?
                ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))

                existing_entry = cursor.fetchone()

                # **Store values if an entry exists**
                if existing_entry:
                    x, y, width, height, line_thickness, scale_x, scale_y, lock, transparency, visible, enable, orientation = existing_entry

                
                # Delete existing entry with the same primary key
                delete_query = '''DELETE FROM WorkerStationShiftErgoTool 
                                  WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                                  AND station_id=? AND shift_id=? AND tool_id=?'''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
        
                conn.commit()
                    
                # Insert new entry
                insert_query = '''INSERT INTO WorkerStationShiftErgoTool (
                                    worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id,
                                    total_cumulative_damage, probability_outcome,
                                    result_3, result_4, result_5, result_6, result_7, result_8, result_9, unit,
                                    x, y, width, height, line_thickness, scale_x, scale_y, 
                                    crop_x, crop_y, crop_width, crop_height, zoom, rotation, 
                                    mirror_h, mirror_v, orientation, color, r, g, b, brightness, 
                                    contrast, saturation, lock, visible, transparency, enable
                                  ) VALUES (
                                    ?, ?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?
                                  )'''
        
                cursor.execute(insert_query, (
                    worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET",
                    total_cumulative_damage, probability_outcome,
                    default_value, default_value, default_value, default_value, default_value, default_value, default_value, unit,
                    x, y, width, height, line_thickness, scale_x, scale_y, 
                    default_value, default_value, default_value, default_value, default_value, default_value, default_value, default_value, 
                    orientation, color, default_value, default_value, default_value, default_value, 
                    default_value, default_value, lock, visible, transparency, enable
                ))
                conn.commit()
                
                # Insert new records for each task in DUET
                insert_query_duet = '''INSERT INTO DuetResults (
                                    worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id, 
                                    omni_res_scale, repetitions, cumulative_damage, percentage_total
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

                for i in range(self.num_task_duet):
                    task_id = i + 1
                    omni_res_scale = self.omnires_dropdowns[i].currentIndex()
                    repetitions = self.duet_repetitions_inputs[i].text()
                    # Assuming cumulative damage and percentage total are calculated/displayed similar to LiFFT
                    cumulative_damage = self.duet_output_labels_matrix[i][3].text()
                    percentage_total = self.duet_output_labels_matrix[i][4].text()
                        
                    cursor.execute(insert_query_duet, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET", task_id, omni_res_scale, repetitions, cumulative_damage, percentage_total))
                conn.commit()
                QMessageBox.information(self, "Success", "DUET data saved successfully.")
    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            finally:
                if conn:
                    conn.close()                 

    
    
    def saveTSTToolData(self):        
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
         
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        
        unit = self.selectedMeasurementSystem 
        
        if tab_index == 0:
            tool_id = "LiFFT"
        elif tab_index == 1:
            tool_id = "DUET"
        elif tab_index == 2:
            tool_id = "ST"
        else:
            tool_id = ""  # Default case if needed

        # Default values for other fields
        #x, y = 10, 10
        x = random.randint(10, 15)
        y = random.randint(10, 15)

        width, height = 50, 50
        line_thickness = 1
        scale_x, scale_y = 1, 1
        lock, transparency = 0, 0
        visible, enable = 0, 1      # TODO: by default visible should be 0, after the plant_layout is working...
        orientation = ""
        default_value = 0  # For all other numeric fields
         
        self.validateInputsForSave()
        
        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return
            
        # TST..........................................................................................................................................
        total_cumulative_damage = float(self.tst_total_damage_value_label.text().strip()) if self.tst_total_damage_value_label.text().strip() else 0
        probability_text = self.tst_probability_value_label.text().strip()
        if probability_text == "> 90":
            probability_outcome = 100
        elif probability_text == "< 5":
            probability_outcome = 0
        else:
            probability_outcome = float(probability_text) if probability_text else 0
        
        color = self.tst_total_risk_color       
            
        # Check if data already exists in the database for ST
        if self.checkForExistingSTData():
            reply = QMessageBox.question(self, 'Data Exists', "Existing TST data found for this Worker, Station and Shift. Update the data?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Check if any ST task data is present
        #if not self.anySTTaskDataPresent():
        #    QMessageBox.warning(self, "No Data", "At least one task must have data to save for TST." )
        #    return
    
        if self.anySTTaskDataPresent():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Delete existing records for the given userid and datetime
                delete_query = '''
                    DELETE FROM TstResults 
                    WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ? AND tool_id = ? 
                '''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
                conn.commit()
                
                
                # **Check if an entry with the same primary key exists**
                cursor.execute('''
                    SELECT x, y, width, height, line_thickness, scale_x, scale_y, lock, transparency, 
                           visible, enable, orientation 
                    FROM WorkerStationShiftErgoTool
                    WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                          AND station_id=? AND shift_id=? AND tool_id=?
                ''', (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))

                existing_entry = cursor.fetchone()

                # **Store values if an entry exists**
                if existing_entry:
                    x, y, width, height, line_thickness, scale_x, scale_y, lock, transparency, visible, enable, orientation = existing_entry

                
                
                # Delete existing entry with the same primary key
                delete_query = '''DELETE FROM WorkerStationShiftErgoTool 
                                  WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                                  AND station_id=? AND shift_id=? AND tool_id=?'''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
    
                conn.commit()
                
                
                
                
                # Insert new entry
                insert_query = '''INSERT INTO WorkerStationShiftErgoTool (
                                    worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id,
                                    total_cumulative_damage, probability_outcome,
                                    result_3, result_4, result_5, result_6, result_7, result_8, result_9, unit,
                                    x, y, width, height, line_thickness, scale_x, scale_y, 
                                    crop_x, crop_y, crop_width, crop_height, zoom, rotation, 
                                    mirror_h, mirror_v, orientation, color, r, g, b, brightness, 
                                    contrast, saturation, lock, visible, transparency, enable
                                  ) VALUES (
                                    ?, ?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?,
                                    ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?, ?, ?, 
                                    ?, ?, ?, ?, ?, ?
                                  )'''
        
                cursor.execute(insert_query, (
                    worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST",
                    total_cumulative_damage, probability_outcome,
                    default_value, default_value, default_value, default_value, default_value, default_value, default_value, unit,
                    x, y, width, height, line_thickness, scale_x, scale_y, 
                    default_value, default_value, default_value, default_value, default_value, default_value, default_value, default_value, 
                    orientation, color, default_value, default_value, default_value, default_value, 
                    default_value, default_value, lock, visible, transparency, enable
                ))
        
                conn.commit()
                
                
                
                
                # Insert new records for each ST task
                insert_query_st = '''INSERT INTO TstResults (
                                  worker_id, plant_name, section_name, line_name, station_id, shift_id, tool_id, task_id, 
                                  type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total
                                  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

                for i in range(self.num_task_tst):
                    task_id = i + 1
                    type_of_task = self.tst_type_of_task_dropdowns[i].currentIndex()
                    lever_arm = self.tst_lever_arm_inputs[i].text()
                    load = self.tst_load_inputs[i].text()
                    moment = self.tst_output_labels_matrix[i][4].text()  # Moment is a calculated field
                    repetitions = self.tst_repetitions_inputs[i].text()
                    cumulative_damage = self.tst_output_labels_matrix[i][6].text()
                    percentage_total = self.tst_output_labels_matrix[i][7].text()
                    

                    cursor.execute(insert_query_st, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST", task_id, type_of_task, lever_arm, load, moment, repetitions, cumulative_damage, percentage_total))

                conn.commit()
                QMessageBox.information(self, "Success", "Shoulder Tool data saved successfully.")
                
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
                
            finally:
                if conn:
                    conn.close()
                
    
    
    
    
    
    
    
    
    
    

                
    def dateTimeChanged(self):
        # Handle date-time control change
        #print("Date-Time changed to:", self.dateTimeControl.dateTime().toString("yyyy-MM-dd HH:mm"))
        pass
        
        



    def setupControlPanel(self):
        active_region_frame = QFrame()
        active_region_frame.setObjectName("activeRegionPanel")
        active_region_frame.setFixedHeight(56)
        active_region_layout = QVBoxLayout(active_region_frame)
        active_region_layout.setContentsMargins(4, 2, 4, 2)
        active_region_layout.setSpacing(0)
        self.active_region_label = QLabel("Lower Back")
        self.active_region_label.setObjectName("activeRegionName")
        self.active_region_label.setAlignment(Qt.AlignCenter)
        self.active_region_label.setFixedHeight(28)
        active_caption = QLabel("Active Region")
        active_caption.setObjectName("activeRegionCaption")
        active_caption.setAlignment(Qt.AlignCenter)
        active_caption.setFixedHeight(22)
        active_region_layout.addWidget(self.active_region_label)
        active_region_layout.addWidget(active_caption)
        self.leftLayout.addWidget(active_region_frame)

        self.leftLayout.addWidget(self.bodyPanelDivider())
        self.body_risk_title = QLabel("LiFFT Individual Risk Score")
        self.body_risk_title.setObjectName("bodySectionTitle")
        self.leftLayout.addWidget(self.body_risk_title)
        for _start, _end, label, color, range_text in RISK_BANDS:
            row = QHBoxLayout()
            swatch = QLabel()
            swatch.setFixedSize(12, 12)
            swatch.setStyleSheet(f"background: {color}; border-radius: 6px;")
            row.addWidget(swatch)
            risk_label = QLabel(label)
            risk_label.setObjectName("bodyRiskLabel")
            row.addWidget(risk_label, 1)
            range_label = QLabel(range_text)
            range_label.setObjectName("bodyRiskRange")
            range_label.setAlignment(Qt.AlignRight)
            row.addWidget(range_label)
            self.leftLayout.addLayout(row)

        self.leftLayout.addWidget(self.bodyPanelDivider())
        controls = QHBoxLayout()
        controls.setSpacing(4)
        icon_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "ui-icons"))
        for text, icon_name, callback, tooltip in (
            ("Rotate", "3drotate-light.png", self.rotateModelView, "Rotate the model clockwise."),
            ("Zoom", "3dzoom-light.png", self.zoomModelView, "Zoom in on the active body region."),
            ("Reset View", "3dreset-light.png", self.resetModelView, "Restore the initial model view."),
        ):
            button = QtWidgets.QToolButton()
            button.setObjectName("modelViewButton")
            button.setText(text)
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setIcon(QIcon(os.path.join(icon_root, icon_name)))
            button.setIconSize(QSize(28, 28))
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            controls.addWidget(button, 1)
        self.leftLayout.addLayout(controls)

    def bodyPanelDivider(self):
        divider = QFrame()
        divider.setObjectName("bodyPanelDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        return divider

    def rotateModelView(self):
        if not self.vtk_enabled:
            return
        camera = self.renderer.GetActiveCamera()
        camera.Azimuth(20)
        self.renderer.ResetCameraClippingRange()
        self.vtkWidget.GetRenderWindow().Render()

    def zoomModelView(self):
        if not self.vtk_enabled:
            return
        self.renderer.GetActiveCamera().Zoom(1.15)
        self.renderer.ResetCameraClippingRange()
        self.vtkWidget.GetRenderWindow().Render()

    def resetModelView(self):
        if not self.vtk_enabled:
            return
        if hasattr(self, "camera_director"):
            if self.isAnimationAllowed:
                self.camera_director.apply(self.tabWidget.currentIndex())
            else:
                self.camera_director.applyFullBody()
            return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.initialCameraSettings['position'])
        camera.SetFocalPoint(self.initialCameraSettings['focalPoint'])
        camera.SetViewUp(self.initialCameraSettings['viewUp'])
        self.renderer.ResetCameraClippingRange()
        self.vtkWidget.GetRenderWindow().Render()



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
        
        
    
    
    def editOrganizationClicked(self):
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Project required", "Create or load a project before managing the organization.")
            return
        selections = [
            self.plant_combo.currentText(), self.section_combo.currentText(), self.line_combo.currentText(),
            self.station_combo.currentText(), self.shift_combo.currentText(),
        ]
        OrganizationWindow(self, "Plant").exec_()
        self.loadPlants()
        plant_index = self.plant_combo.findText(selections[0])
        if plant_index >= 0:
            self.plant_combo.setCurrentIndex(plant_index)
        self.loadSections()
        section_index = self.section_combo.findText(selections[1])
        if section_index >= 0:
            self.section_combo.setCurrentIndex(section_index)
        self.loadLines()
        line_index = self.line_combo.findText(selections[2])
        if line_index >= 0:
            self.line_combo.setCurrentIndex(line_index)
        self.loadStations()
        station_index = self.station_combo.findText(selections[3])
        if station_index >= 0:
            self.station_combo.setCurrentIndex(station_index)
        self.loadShifts()
        shift_index = self.shift_combo.findText(selections[4])
        if shift_index >= 0:
            self.shift_combo.setCurrentIndex(shift_index)


    def editPlantClicked(self):
        
        
        self.editPlantName = ""
        
        self.plant_window = OrganizationWindow(self, "Plant")
        self.plant_window.exec_()
 
        if not self.projectFileCreated:
            return

        self.loadPlants()
        
        # Find the index of the formatted worker text in the combo box of the main window
        index = self.plant_combo.findText(self.editPlantName)

        # If the index is valid, set the combo box to that index
        if index != -1:
            self.plant_combo.setCurrentIndex(index)
            
            
        

    

    
  

    def editSectionClicked(self):
        self.editSectionName = ""
        
        self.section_window = OrganizationWindow(self, "Section")
        self.section_window.exec_()
 
        if not self.projectFileCreated:
            return
         
        self.loadSections()
        
        # Find the index of the formatted worker text in the combo box of the main window
        index = self.section_combo.findText(self.editSectionName)

        # If the index is valid, set the combo box to that index
        if index != -1:
            self.section_combo.setCurrentIndex(index)     
        
       
    
    def editLineClicked(self):
        self.editLineName = ""
        
        self.line_window = OrganizationWindow(self, "Line")
        self.line_window.exec_()
 
        if not self.projectFileCreated:
            return
            
        self.loadLines()
        
        # Find the index of the formatted worker text in the combo box of the main window
        index = self.line_combo.findText(self.editLineName)

        # If the index is valid, set the combo box to that index
        if index != -1:
            self.line_combo.setCurrentIndex(index)   
    
    
    def editStationClicked(self):
        self.editStationName = ""
        
        self.station_window = OrganizationWindow(self, "Station")
        self.station_window.exec_()
 
        if not self.projectFileCreated:
            return
            
        self.loadStations()
        
        # Find the index of the formatted worker text in the combo box of the main window
        index = self.station_combo.findText(self.editStationName)

        # If the index is valid, set the combo box to that index
        if index != -1:
            self.station_combo.setCurrentIndex(index) 
            
            
    def editShiftClicked(self):
        self.editShiftName = ""
        
        self.shift_window = OrganizationWindow(self, "Shift")
        self.shift_window.exec_()
 
        if not self.projectFileCreated:
            return
            
        self.loadShifts()
        
        # Find the index of the formatted worker text in the combo box of the main window
        index = self.shift_combo.findText(self.editShiftName)

        # If the index is valid, set the combo box to that index
        if index != -1:
            self.shift_combo.setCurrentIndex(index)    
            
    
    def plantComboIndexChanged(self, index):
    
         self.section_combo.blockSignals(True)
         self.line_combo.blockSignals(True)
         self.station_combo.blockSignals(True)
            
         self.section_combo.clear()
         self.line_combo.clear()
         self.station_combo.clear()
         #self.shift_combo.clear()
         self.loadSections()
         self.loadLines()
         self.loadStations()
         #self.loadShifts()
         
         self.loadToolsData()
         
         self.section_combo.blockSignals(False)
         self.line_combo.blockSignals(False)
         self.station_combo.blockSignals(False)
         
    def sectionComboIndexChanged(self, index):
         #print("test")
         
         self.line_combo.blockSignals(True)
         self.station_combo.blockSignals(True)

         self.line_combo.clear()
         self.loadLines()
         self.station_combo.clear()
         self.loadStations()
         #self.shift_combo.clear()
         #self.loadShifts()
         self.loadToolsData()
         
         self.line_combo.blockSignals(False)
         self.station_combo.blockSignals(False)

    
    def lineComboIndexChanged(self, index):
    
         self.station_combo.blockSignals(True)

         self.station_combo.clear()
         self.loadStations()
         #self.shift_combo.clear()
         #self.loadShifts()
         self.loadToolsData()
         
         self.station_combo.blockSignals(False)

         
         
    def stationComboIndexChanged(self, index):
         #self.shift_combo.clear()
         #self.loadShifts()
         self.loadToolsData()
         #return
         
         
    
    def shiftComboIndexChanged(self, index):
         #self.shift_combo.clear()
         #self.loadShifts()
         self.loadToolsData()     
         #return
         
              
    
    
    def setupLiFFTTab(self):
        
        # Validator for double input
        lifft_double_validator = QDoubleValidator()
        
        # Create bold font for labels that need emphasis
        lifft_bold_font = QFont()
        lifft_bold_font.setBold(True)



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
        
        
        # Main layout for the LiFFT tab
        lifft_main_layout = QVBoxLayout()



        # **Duplicate Header (Fixed, Outside Scroll Area)**
        header_layout = SyncedHeaderLayout()
        #lifft_headers = ["Task #", "Lever Arm (cm)", "Load (N)", "Moment (N.m)", "Repetitions (per work day)", "Damage (cumulative)", "% Total (damage)"]
        
        lifft_headers = [
            "Task #", 
            f"Lever Arm ({self.lifft_header_lever_arm_unit})", 
            f"Load ({self.lifft_header_load_unit})", 
            f"Moment ({self.lifft_header_moment_unit})", 
            "Repetitions (per work day)", 
            "Damage (cumulative)", 
            "% Total (damage)"
        ]
        
        self.lifft_headers_labels_fixed = []
    
        for header in lifft_headers:
            lifft_header_label = QLabel(header)
            lifft_header_label.setFont(lifft_bold_font)
            lifft_header_label.setAlignment(Qt.AlignCenter)
            #lifft_header_label.setStyleSheet("border: 1px solid black; padding: 24px;")  # Optional styling
            #header_layout.addWidget(lifft_header_label)
            #self.lifft_headers_labels_fixed.append(lifft_header_label)
    
            if header == "Task #":
                header_layout.addSpacing(-60)  # Add space before this header
            elif header == f"Lever Arm ({self.lifft_header_lever_arm_unit})":
                header_layout.addSpacing(20)  # Add more space before this header      
            elif header == f"Load ({self.lifft_header_load_unit})":
                header_layout.addSpacing(80)  # Add more space before this header  
            elif header == f"Moment ({self.lifft_header_moment_unit})":
                header_layout.addSpacing(20)  # Add more space before this header  
            elif header == "Damage (cumulative)":
                header_layout.addSpacing(20)  # Add more space before this header  
            elif header == "Repetitions (per work day)":
                header_layout.addSpacing(20)  # Add more space before this header     
 
            # Add header label to layout
            header_layout.addWidget(lifft_header_label)
            self.lifft_headers_labels_fixed.append(lifft_header_label)
            
            #if header == "Task #":
            #    header_layout.addStretch(10)
             
    
    
        lifft_main_layout.addWidget(self.createStickyHeader(header_layout, "lifft"))




        
        # Add a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create a frame to hold all task controls
        self.scroll_frame = QFrame()
        scroll_frame_layout = QVBoxLayout()
        self.scroll_frame.setLayout(scroll_frame_layout)

        # Create grid layout for task controls
        self.lifft_tab_layout = QGridLayout()
        self.lifft_tab_layout.setAlignment(Qt.AlignTop)
        scroll_frame_layout.addLayout(self.lifft_tab_layout)

        # Add the frame to the scroll area
        self.scroll_area.setWidget(self.scroll_frame)
        self.bindStickyHeader("lifft", self.scroll_area)

        # Add the scroll area to the main layout
        lifft_main_layout.addWidget(self.scroll_area)

        # Column headers
        lifft_headers = ["Task #", f"Lever Arm ({self.lifft_header_lever_arm_unit})", f"Load ({self.lifft_header_load_unit})", f"Moment ({self.lifft_header_moment_unit})", "Repetitions (per work day)", "Damage (cumulative)", "% Total (damage)"]
        self.lifft_headers_labels = []
        for col, header in enumerate(lifft_headers):
            lifft_header_label = QLabel(header)
            lifft_header_label.setFont(lifft_bold_font)
            lifft_header_label.setAlignment(Qt.AlignCenter)
            lifft_header_label.setFixedHeight(0)  # Smallest visible height
            self.lifft_tab_layout.addWidget(lifft_header_label, 0, col)
            self.lifft_headers_labels.append(lifft_header_label)
            #lifft_header_label.setVisible(False)

        # Task number column
        for row in range(self.num_task):
            lifft_task_label = QLabel(str(row + 1))
            lifft_task_label.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_task_label, row + 1, 0)

        # Input fields with validation
        self.lifft_lever_arm_inputs = []
        self.lifft_load_inputs = []
        self.lifft_repetitions_inputs = []
        for row in range(self.num_task):
            # Lever Arm (cm) input
            lifft_lever_arm_input = QLineEdit()
            lifft_lever_arm_input.setValidator(lifft_double_validator)
            lifft_lever_arm_input.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_lever_arm_input, row + 1, 1)
            self.lifft_lever_arm_inputs.append(lifft_lever_arm_input)
            
             # Connect the textChanged signal to the common handler.
            lifft_lever_arm_input.textChanged.connect(self.lifftInputChanged)

            # Load (N) input
            lifft_load_input = QLineEdit()
            lifft_load_input.setValidator(lifft_double_validator)
            lifft_load_input.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_load_input, row + 1, 2)
            self.lifft_load_inputs.append(lifft_load_input)
            lifft_load_input.textChanged.connect(self.lifftInputChanged)
            
            # Repetitions input
            lifft_repetitions_input = QLineEdit()
            lifft_repetitions_input.setValidator(QIntValidator())
            lifft_repetitions_input.setAlignment(Qt.AlignCenter)
            self.lifft_tab_layout.addWidget(lifft_repetitions_input, row + 1, 4)
            self.lifft_repetitions_inputs.append(lifft_repetitions_input)
            lifft_repetitions_input.textChanged.connect(self.lifftInputChanged)

        # Initialize a 2D list (matrix) to hold the output labels
        self.lifft_output_labels_matrix = [[None for _ in range(7)] for _ in range(self.num_task + 1)]

        # Output labels for Moment, Damage, and % Total
        for row in range(self.num_task):
            for col in [3, 5, 6]:  # Only these columns have output labels
                lifft_label = QLabel("0.0")
                lifft_label.setAlignment(Qt.AlignCenter)
                self.lifft_tab_layout.addWidget(lifft_label, row + 1, col)
                self.lifft_output_labels_matrix[row][col] = lifft_label


        ## Bottom row labels and values beneath the 'Damage' column
        #self.lifft_total_damage_label = QLabel("Total Cumulative Damage:")
        #self.lifft_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        #self.lifft_total_damage_label.setFont(lifft_bold_font)
        #self.lifft_tab_layout.addWidget(self.lifft_total_damage_label, self.num_task + 1, 4, 1, 1)
        #self.lifft_total_damage_value_label = QLabel("0.0")
        #self.lifft_total_damage_value_label.setFont(lifft_bold_font)
        #self.lifft_total_damage_value_label.setAlignment(Qt.AlignCenter)
        #self.lifft_tab_layout.addWidget(self.lifft_total_damage_value_label, self.num_task + 1, 5)

        #self.lifft_probability_label = QLabel("Probability of High Risk Job * (%):")
        #self.lifft_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        #self.lifft_probability_label.setFont(lifft_bold_font)
        #self.lifft_tab_layout.addWidget(self.lifft_probability_label, self.num_task + 2, 4, 1, 1)
        #self.lifft_probability_value_label = QLabel("0.0")
        #self.lifft_probability_value_label.setFont(lifft_bold_font)
        #self.lifft_probability_value_label.setAlignment(Qt.AlignCenter)
        #self.lifft_tab_layout.addWidget(self.lifft_probability_value_label, self.num_task + 2, 5)
        
        
        
        
        # **Summary Grid Layout with 7 Columns & 2 Rows**
        summary_layout = QGridLayout()
        self.lifft_summary_layout = summary_layout
        summary_layout.setRowMinimumHeight(0, 30)
        summary_layout.setRowMinimumHeight(1, 30)
        
        # **Set Column Stretch for Precise Width Control**
        summary_layout.setColumnMinimumWidth(0, 50)  # Set fixed minimum width for the first column

        summary_layout.setColumnStretch(0, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(1, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(2, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(3, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(4, 2)  # Label Column
        summary_layout.setColumnStretch(5, 1)  # Value Column
        summary_layout.setColumnStretch(6, 1)  # Right spacer (empty)
        
        # **Row 1: Total Cumulative Damage**
        self.lifft_total_damage_label = QLabel("Total Cumulative Damage:")
        self.lifft_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lifft_total_damage_label.setFont(lifft_bold_font)
        
        #summary_layout.setSpacing(-60)  # Add space before this header
        summary_layout.addWidget(self.lifft_total_damage_label, 0, 4)  # Row 0, Col 4
        
        self.lifft_total_damage_value_label = QLabel("0.0")
        self.lifft_total_damage_value_label.setFont(lifft_bold_font)
        self.lifft_total_damage_value_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.lifft_total_damage_value_label, 0, 5)  # Row 0, Col 5
        
        # **Row 2: Probability of High-Risk Job**
        self.lifft_probability_label = QLabel("Probability of High Risk Job * (%):")
        self.lifft_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lifft_probability_label.setFont(lifft_bold_font)
        summary_layout.addWidget(self.lifft_probability_label, 1, 4)  # Row 1, Col 4
        
        self.lifft_probability_value_label = QLabel("0.0")
        self.lifft_probability_value_label.setFont(lifft_bold_font)
        self.lifft_probability_value_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.lifft_probability_value_label, 1, 5)  # Row 1, Col 
        
        # **Add the summary layout BEFORE the button layout**
        lifft_main_layout.addLayout(summary_layout)
        for widget in (
            self.lifft_total_damage_label, self.lifft_total_damage_value_label,
            self.lifft_probability_label, self.lifft_probability_value_label,
        ):
            widget.hide()

        

        ## **Buttons for LiFFT Tab**
        lifft_buttons_layout = QHBoxLayout()
        
        # **Left-aligned Reset Button (Expands to take available space)**
        self.lifft_reset_button = QPushButton("Reset")
        self.lifft_reset_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expanding left button
        lifft_buttons_layout.addWidget(self.lifft_reset_button)
        
        # **Small Delete Button (Fixed Size, Larger Icon)**
        self.lifft_delete_button = QPushButton()
        self.lifft_delete_button.setIcon(QIcon("../images/delete_icon01.png"))
        self.lifft_delete_button.setFixedSize(30, 30)  # Small square button
        self.lifft_delete_button.setIconSize(QSize(25, 25))  # Increase icon size
        lifft_buttons_layout.addWidget(self.lifft_delete_button)
        
        
        # **Small Grid Button (Fixed Size, Larger Icon)**
        self.lifft_grid_button = QPushButton()
        self.lifft_grid_button.setIcon(QIcon("../images/grid_icon01.png"))
        self.lifft_grid_button.setFixedSize(30, 30)  # Small square button
        self.lifft_grid_button.setIconSize(QSize(25, 25))  # Increase icon size
        lifft_buttons_layout.addWidget(self.lifft_grid_button)
        
        
        # **Right-aligned Calculate Button (Expands to take available space)**
        self.lifft_calculate_button = QPushButton("Calculate")
        self.lifft_calculate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expanding right button
        lifft_buttons_layout.addWidget(self.lifft_calculate_button)
        
        # **Add layout to main UI**
        lifft_main_layout.addLayout(lifft_buttons_layout)


        # Connect the buttons to methods
        self.lifft_reset_button.clicked.connect(self.lifftResetForm)
        self.lifft_calculate_button.clicked.connect(self.lifftCalculateResultsClicked)
        
        self.lifft_delete_button.clicked.connect(self.lifftDeleteAction)
        self.lifft_grid_button.clicked.connect(self.toolGridAction)

        # Create the LiFFT tab widget and set its layout
        self.lifft_tab = QWidget()
        self.lifft_tab.setLayout(lifft_main_layout)

        # Add LiFFT tab to the tab widget
        self.tabWidget.insertTab(0, self.lifft_tab, "Lifting Fatigue Failure Tool (LiFFT)  ")

        self.any_lifft_input_changed = False
        ##print("HERE")
        
        
    
    def lifftCalculateResultsClicked(self):
        self.selectedMeasurementSystem = "Metric" if self.metric_action.isChecked() else "Imperial"
        if self.selectedMeasurementSystem in ["Metric", "Imperial"]:
            self.num_task = len(self.lifft_lever_arm_inputs)
            self.lifftCalculateResults()
            
    
    def lifftDeleteAction(self):
        self.deleteLiFFTData()

    def lifftTransferAction(self):
        transfer_dialog = ToolTransferDialog(self) 
        transfer_dialog.exec_()  # Open it as a modal window
        self.loadToolsData()
        
    def toolGridAction(self):
        """
        Opens the Worker Data Dialog with data fetched from the database.
        """
        # **Validation: Ensure Project & Database Exists**
        if not self.projectFileCreated:
            QMessageBox.warning(self, "Error", "No project file has been created or loaded.")
            return
        
        if not hasattr(self, 'projectdatabasePath') or not self.projectdatabasePath:
            QMessageBox.critical(self, "Error", "Database path is not set.")
            return
    
        # **Get Worker ID from ComboBox**
        worker_combo_text = self.workerComboBox.currentText()
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
    
        # **Ensure Worker ID is Selected**
        if not worker_id:
            QMessageBox.warning(self, "Error", "Please select a worker first.")
            return

        # **Get Filters**
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
    
        unit = self.selectedMeasurementSystem  # Measurement System
    
        # **Determine Tool ID Based on Tab**
        tool_id = ["LiFFT", "DUET", "ST"][tab_index] if tab_index in [0, 1, 2] else ""
    
        # **Fetch Data from DB**
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            conn.row_factory = sqlite3.Row  # Enables dictionary-like access
            cursor = conn.cursor()
    
            query = """
                SELECT plant_name, section_name, line_name, station_id, shift_id, tool_id 
                FROM WorkerStationShiftErgoTool 
                WHERE worker_id = ? AND tool_id = ?
            """
            cursor.execute(query, (worker_id, tool_id))
            results = cursor.fetchall()
            conn.close()

            # Convert to list of dictionaries
            worker_data = [dict(row) for row in results]
    
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve worker data:\n{str(e)}")
            return

        # **Open Dialog with Data**
        dialog = ToolDataDialog(self, data=worker_data)
        if dialog.exec_() == QDialog.Accepted:
            # Store the selected data in variables
            self.selectedPlant = dialog.selected_row_data["plant_name"]
            self.selectedSection = dialog.selected_row_data["section_name"]
            self.selectedLine = dialog.selected_row_data["line_name"]
            self.selectedStation = dialog.selected_row_data["station_id"]
            self.selectedShift = dialog.selected_row_data["shift_id"]
            self.selectedTool = dialog.selected_row_data["tool_id"]
            
            
            # **Suspend signals**
            self.plant_combo.blockSignals(True)
            self.section_combo.blockSignals(True)
            self.line_combo.blockSignals(True)
            self.station_combo.blockSignals(True)
            self.shift_combo.blockSignals(True)

            # **Set new values**
            self.plant_combo.setCurrentText(self.selectedPlant)
            self.section_combo.setCurrentText(self.selectedSection)
            self.line_combo.setCurrentText(self.selectedLine)
            self.station_combo.setCurrentText(self.selectedStation)
            self.shift_combo.setCurrentText(self.selectedShift)

            # **Re-enable signals**
            self.plant_combo.blockSignals(False)
            self.section_combo.blockSignals(False)
            self.line_combo.blockSignals(False)
            self.station_combo.blockSignals(False)
            self.shift_combo.blockSignals(False)
    
            self.loadToolsData()
            #print("Selected Data:", self.selectedPlant, self.selectedSection, self.selectedLine, self.selectedStation, self.selectedShift, self.selectedTool)

    
    def lifftInputChanged(self, new_text):
        # Set the flag to True when any text is changed.
        self.any_lifft_input_changed = True
    
    
          
    def deleteLiFFTData(self):
        currentTabIndex = self.tabWidget.currentIndex()
        currentTabText = self.tabWidget.tabText(currentTabIndex)
         
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        
         
        self.validateInputsForSave()  # Also work for delete...
        
        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return
    
    
        if self.checkForExistingLiFFTData():
            reply = QMessageBox.question(self, 'Data Exists', "Existing LiFFT data found for this Worker, Station and Shift. Delete the data?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
               
        if self.anyLiFFTTaskDataPresent():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Delete existing records for the given userid and datetime
                delete_query = '''
                    DELETE FROM LifftResults 
                    WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ? AND tool_id = ? 
                '''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
                conn.commit()
                
                # Delete existing entry with the same primary key
                delete_query = '''DELETE FROM WorkerStationShiftErgoTool 
                                  WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                                  AND station_id=? AND shift_id=? AND tool_id=?'''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "LiFFT"))
                conn.commit()
             
                self.loadToolsData()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

            finally:
                if conn:
                    conn.close()   
           
    
    
    
    
    
    def setupDUETTab(self):
        # Validator for double input
        duet_double_validator = QDoubleValidator()

        # Create bold font for labels that need emphasis
        duet_bold_font = QFont()
        duet_bold_font.setBold(True)
    
    
        # Calculation variables...
        self.duet_damage, self.duet_percent = [], []
        for i in range(self.num_task):
            self.duet_damage.append([0.0, 'none'])   # first item is the value, second is the color
            self.duet_percent.append(0.0)

        self.duet_total_damage = 0
        self.duet_total_risk = 0
        self.duet_total_risk_color = 'none'

    
        # Main layout for the DUET tab
        duet_main_layout = QVBoxLayout()
    
        # **Duplicate Header (Fixed, Outside Scroll Area)**
        header_layout = SyncedHeaderLayout()
        duet_headers = ["Task #", "OMNI-Res Scale", "Repetitions (per work day)", "Damage (cumulative)", "% Total (damage)"]
        self.duet_headers_labels_fixed = []
    
        for header in duet_headers:
            duet_header_label = QLabel(header)
            duet_header_label.setFont(duet_bold_font)
            duet_header_label.setAlignment(Qt.AlignCenter)
    
            # Adjust spacing for better alignment
            if header == "Task #":
                header_layout.addSpacing(-80)  
            elif header == "OMNI-Res Scale":
                header_layout.addSpacing(-20)  
            elif header == "Repetitions (per work day)":
                header_layout.addSpacing(70)  
            elif header == "Damage (cumulative)":
                header_layout.addSpacing(430)  
            elif header == "% Total (damage)":
                header_layout.addSpacing(0)  

            header_layout.addWidget(duet_header_label)
            self.duet_headers_labels_fixed.append(duet_header_label)
            #if header == "Damage (cumulative)":
            #    header_layout.addSpacing(80)  

        duet_main_layout.addWidget(self.createStickyHeader(header_layout, "duet"))

        # **Add a scroll area**
        self.scroll_area_duet = QScrollArea()
        self.scroll_area_duet.setWidgetResizable(True)
    
        # Create a frame to hold all task controls
        self.scroll_frame_duet = QFrame()
        scroll_frame_layout = QVBoxLayout()
        self.scroll_frame_duet.setLayout(scroll_frame_layout)
    
        # Create grid layout for task controls
        self.duet_tab_layout = QGridLayout()
        self.duet_tab_layout.setAlignment(Qt.AlignTop)
        self.duet_tab_layout.setColumnStretch(0, 0)
        self.duet_tab_layout.setColumnStretch(1, 4)
        self.duet_tab_layout.setColumnStretch(2, 3)
        self.duet_tab_layout.setColumnStretch(3, 2)
        self.duet_tab_layout.setColumnStretch(4, 1)
        for column, width in enumerate((48, 250, 220, 150, 105)):
            self.duet_tab_layout.setColumnMinimumWidth(column, width)
        scroll_frame_layout.addLayout(self.duet_tab_layout)
    
        # Add the frame to the scroll area
        self.scroll_area_duet.setWidget(self.scroll_frame_duet)
        self.bindStickyHeader("duet", self.scroll_area_duet)
    
        # Add the scroll area to the main layout
        duet_main_layout.addWidget(self.scroll_area_duet)
    
        # **Column headers inside the scroll area**
        self.duet_headers_labels = []
        for col, header in enumerate(duet_headers):
            duet_header_label = QLabel(header)
            duet_header_label.setFont(duet_bold_font)
            duet_header_label.setAlignment(Qt.AlignCenter)
            duet_header_label.setWordWrap(True)
            duet_header_label.setFixedHeight(0)  # Smallest visible height
            duet_header_label.setMinimumWidth(0)
            duet_header_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.duet_tab_layout.addWidget(duet_header_label, 0, col)
            self.duet_headers_labels.append(duet_header_label)
    
        # **Task number column and Difficulty Rating dropdown**
        self.omnires_dropdowns = []
        self.duet_repetitions_inputs = []
        for row in range(self.num_task):
            # Task Number
            duet_task_label = QLabel(str(row+1))
            duet_task_label.setAlignment(Qt.AlignCenter)
            self.duet_tab_layout.addWidget(duet_task_label, row + 1, 0)
    
            # Difficulty Rating dropdown
            omnires_dropdown = QComboBox()
            omnires_dropdown.setMinimumWidth(250)
            omnires_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            omnires_dropdown.setMinimumContentsLength(19)
            omnires_dropdown.addItems([
                "0: Extremely Easy", "1:", "2: Easy", "3:", "4: Somewhat Easy", "5:",
                "6: Somewhat Hard", "7:", "8: Hard", "9:", "10: Extremely Hard"
            ])
            self.duet_tab_layout.addWidget(omnires_dropdown, row + 1, 1)
            self.omnires_dropdowns.append(omnires_dropdown)
            omnires_dropdown.currentIndexChanged.connect(self.duetDropdownChanged)

            # Repetitions input
            duet_repetitions_input = QLineEdit()
            duet_repetitions_input.setMaximumWidth(280)
            duet_repetitions_input.setValidator(QIntValidator())
            duet_repetitions_input.setAlignment(Qt.AlignCenter)
            self.duet_tab_layout.addWidget(duet_repetitions_input, row + 1, 2)
            self.duet_repetitions_inputs.append(duet_repetitions_input)
            duet_repetitions_input.textChanged.connect(self.duetInputChanged)

        # Initialize a 2D list (matrix) to hold the output labels
        self.duet_output_labels_matrix = [[None for _ in range(5)] for _ in range(self.num_task + 1)]
    
        # **Output labels for Damage and % Total**
        for row in range(self.num_task):
            for col in [3, 4]:  # Only these columns have output labels
                duet_label = QLabel("0.0")
                duet_label.setAlignment(Qt.AlignCenter)
                self.duet_tab_layout.addWidget(duet_label, row + 1, col)
                self.duet_output_labels_matrix[row][col] = duet_label
    
        
        # **Summary Grid Layout with 7 Columns & 2 Rows**
        summary_layout = QGridLayout()
        self.duet_summary_layout = summary_layout
        summary_layout.setRowMinimumHeight(0, 30)
        summary_layout.setRowMinimumHeight(1, 30)

        # **Set Column Stretch for Precise Width Control**
        summary_layout.setColumnMinimumWidth(0, 80)  # Fixed minimum width for the first column
        summary_layout.setColumnStretch(0, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(1, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(2, 1)  # Left spacer (empty)
        summary_layout.setColumnStretch(3, 2)  # Label Column
        summary_layout.setColumnStretch(4, 1)  # Value Column
        summary_layout.setColumnStretch(5, 1)  # Right spacer (empty)

        # **Row 1: Total Cumulative Damage**
        self.duet_total_damage_label = QLabel("Total Cumulative Damage:")
        self.duet_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.duet_total_damage_label.setFont(duet_bold_font)
        summary_layout.addWidget(self.duet_total_damage_label, 0, 3)  # Row 0, Col 3
        
        self.duet_total_damage_value_label = QLabel("0.0")
        self.duet_total_damage_value_label.setFont(duet_bold_font)
        self.duet_total_damage_value_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.duet_total_damage_value_label, 0, 4)  # Row 0, Col 4
        
        # **Row 2: Probability of High-Risk Job**
        self.duet_probability_label = QLabel("Probability of Distal Upper Extremity Outcome (%):")
        self.duet_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.duet_probability_label.setFont(duet_bold_font)
        summary_layout.addWidget(self.duet_probability_label, 1, 3)  # Row 1, Col 3
        
        self.duet_probability_value_label = QLabel("0.0")
        self.duet_probability_value_label.setFont(duet_bold_font)
        self.duet_probability_value_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.duet_probability_value_label, 1, 4)  # Row 1, Col 4
        
        # **Add the summary layout BEFORE the button layout**
        duet_main_layout.addLayout(summary_layout)
        for widget in (
            self.duet_total_damage_label, self.duet_total_damage_value_label,
            self.duet_probability_label, self.duet_probability_value_label,
        ):
            widget.hide()

        

        # **Buttons for DUET Tab**
        duet_buttons_layout = QHBoxLayout()

        # **Left-aligned Reset Button (Expands to take available space)**
        self.duet_reset_button = QPushButton("Reset")
        self.duet_reset_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expanding left button
        duet_buttons_layout.addWidget(self.duet_reset_button)
        
        # **Small Delete Button (Fixed Size, Larger Icon)**
        self.duet_delete_button = QPushButton()
        self.duet_delete_button.setIcon(QIcon("../images/delete_icon01.png"))
        self.duet_delete_button.setFixedSize(30, 30)  # Small square button
        self.duet_delete_button.setIconSize(QSize(25, 25))  # Increase icon size
        duet_buttons_layout.addWidget(self.duet_delete_button)
        
        # **Small Grid Button (Fixed Size, Larger Icon)**
        self.duet_grid_button = QPushButton()
        self.duet_grid_button.setIcon(QIcon("../images/grid_icon01.png"))
        self.duet_grid_button.setFixedSize(30, 30)  # Small square button
        self.duet_grid_button.setIconSize(QSize(25, 25))  # Increase icon size
        duet_buttons_layout.addWidget(self.duet_grid_button)
        
        # **Right-aligned Calculate Button (Expands to take available space)**
        self.duet_calculate_button = QPushButton("Calculate")
        self.duet_calculate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expanding right button
        duet_buttons_layout.addWidget(self.duet_calculate_button)
        
        # **Add layout to main UI**
        duet_main_layout.addLayout(duet_buttons_layout)


        # **Connect the buttons to methods**
        self.duet_reset_button.clicked.connect(self.duetResetForm)
        self.duet_grid_button.clicked.connect(self.toolGridAction)
        self.duet_calculate_button.clicked.connect(self.duetCalculateResultsClicked)
        
        self.duet_delete_button.clicked.connect(self.duetDeleteAction)

        # **Create the DUET tab widget and set its layout**
        self.duet_tab = QWidget()
        self.duet_tab.setLayout(duet_main_layout)

        # **Add DUET tab to the tab widget**
        self.tabWidget.insertTab(1, self.duet_tab, "Distal Upper Extremity Tool (DUET)")
        
        self.any_duet_input_changed = False

    
    def duetCalculateResultsClicked(self):
        self.selectedMeasurementSystem = "Metric" if self.metric_action.isChecked() else "Imperial"
        if self.selectedMeasurementSystem in ["Metric", "Imperial"]:
            #print("len(self.duet_repetitions_inputs):", len(self.duet_repetitions_inputs))
            self.num_task = len(self.duet_repetitions_inputs)
            self.duetCalculateResults()

    def duetDeleteAction(self):
        self.deleteDUETData()

    def duetTransferAction(self):
        transfer_dialog = ToolTransferDialog(self) 
        transfer_dialog.exec_()  # Open it as a modal window
        self.loadToolsData()
    
    
    def deleteDUETData(self):
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        
         
        self.validateInputsForSave()  # Also work for delete...
        
        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return
    
    
        if self.checkForExistingDUETData():
            reply = QMessageBox.question(self, 'Data Exists', "Existing DUET data found for this Worker, Station and Shift. Delete the data?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
               
        if self.anyDUETTaskDataPresent():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Delete existing records for the given userid and datetime
                delete_query = '''
                    DELETE FROM DuetResults 
                    WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ? AND tool_id = ? 
                '''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
                conn.commit()
                
                # Delete existing entry with the same primary key
                delete_query = '''DELETE FROM WorkerStationShiftErgoTool 
                                  WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                                  AND station_id=? AND shift_id=? AND tool_id=?'''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "DUET"))
                conn.commit()
             
                self.loadToolsData()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

            finally:
                if conn:
                    conn.close()   

    
    
    def duetDropdownChanged(self, index):
        self.any_duet_input_changed = True
        
    def duetInputChanged(self, new_text):
        self.any_duet_input_changed = True
    
    
    
    def setupTSTTab(self):
        # Validator for double input
        tst_double_validator = QDoubleValidator()
    
        # Create bold font for labels that need emphasis
        tst_bold_font = QFont()
        tst_bold_font.setBold(True)
    
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
        
        
        # **Main layout for the TST tab**
        tst_main_layout = QVBoxLayout()
    
        # **Duplicate Header (Fixed, Outside Scroll Area)**
        header_layout = SyncedHeaderLayout()
       
        tst_headers = [
            "Task #", 
            "Type of Task", 
            f"Lever Arm ({self.tst_header_lever_arm_unit})", 
            f"Load ({self.tst_header_load_unit})", 
            f"Moment ({self.tst_header_moment_unit})", 
            "Repetitions (per work day)", 
            "Damage (cumulative)", 
            "% Total (damage)"
        ]
                      
        self.tst_headers_labels_fixed = []
        for header in tst_headers:
            tst_header_label = QLabel(header)
            tst_header_label.setFont(tst_bold_font)
            tst_header_label.setAlignment(Qt.AlignCenter)
    
            # Custom spacing for better alignment
            if header == "Task #":
                header_layout.addSpacing(10)  
            elif header == "Type of Task":
                header_layout.addSpacing(40)   
            elif header == f"Lever Arm ({self.tst_header_lever_arm_unit})":
                header_layout.addSpacing(100)  
            elif header == f"Load ({self.tst_header_load_unit})":
                header_layout.addSpacing(60)  
            elif header == f"Moment ({self.tst_header_moment_unit})":
                header_layout.addSpacing(80)
                #tst_header_label.setAlignment(Qt.AlignRight)  
            elif header == "Repetitions (per work day)":
                header_layout.addSpacing(0)  
            elif header == "Damage (cumulative)":
                header_layout.addSpacing(20)  
    
            # Add header label to layout
            header_layout.addWidget(tst_header_label)    
            self.tst_headers_labels_fixed.append(tst_header_label)

        tst_main_layout.addWidget(self.createStickyHeader(header_layout, "tst"))


        # **Add a Scroll Area**
        self.scroll_area_tst = QScrollArea()
        self.scroll_area_tst.setWidgetResizable(True)
        self.scroll_area_tst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # **Create a frame to hold all task controls**
        self.scroll_frame_tst = QFrame()
        self.scroll_frame_tst.setMinimumWidth(0)
        self.scroll_frame_tst.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        scroll_frame_layout_tst = QVBoxLayout()
        scroll_frame_layout_tst.setContentsMargins(0, 0, 0, 0)
        self.scroll_frame_tst.setLayout(scroll_frame_layout_tst)

        # **Create grid layout for task controls**
        self.tst_tab_layout = QGridLayout()
        self.tst_tab_layout.setAlignment(Qt.AlignTop)
        self.tst_tab_layout.setContentsMargins(6, 0, 6, 0)
        self.tst_tab_layout.setColumnStretch(1, 3)
        self.tst_tab_layout.setColumnStretch(2, 2)
        self.tst_tab_layout.setColumnStretch(3, 1)
        self.tst_tab_layout.setColumnStretch(5, 3)
        self.tst_tab_layout.setColumnStretch(6, 2)
        for column, width in enumerate((55, 190, 95, 58, 80, 145, 115, 85)):
            self.tst_tab_layout.setColumnMinimumWidth(column, width)
        scroll_frame_layout_tst.addLayout(self.tst_tab_layout)

        # **Add the frame to the scroll area**
        self.scroll_area_tst.setWidget(self.scroll_frame_tst)
        self.bindStickyHeader("tst", self.scroll_area_tst)

        # **Add the scroll area to the main layout**
        tst_main_layout.addWidget(self.scroll_area_tst)


        # **Column headers (Inside Scroll Area)**
        self.tst_headers_labels = []
        for col, header in enumerate(tst_headers):
            tst_header_label = QLabel(header)
            tst_header_label.setFont(tst_bold_font)
            tst_header_label.setAlignment(Qt.AlignCenter)
            tst_header_label.setWordWrap(True)
            tst_header_label.setFixedHeight(0)  # Smallest visible height
            tst_header_label.setMinimumWidth(0)
            tst_header_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            self.tst_tab_layout.addWidget(tst_header_label, 0, col)
            self.tst_headers_labels.append(tst_header_label)

        # **Task number column and Type of Task dropdown**
        self.tst_type_of_task_dropdowns = []
        task_types = ["Handling Loads", "Push or Pull Downward", "Horizontal Push or Pull"]

        for row in range(self.num_task):
            # Task Number
            tst_task_label = QLabel(str(row+1))
            tst_task_label.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_task_label, row + 1, 0)
    
            # Type of Task dropdown
            type_of_task_dropdown = QComboBox()
            type_of_task_dropdown.setMinimumWidth(0)
            type_of_task_dropdown.setMaximumWidth(220)
            type_of_task_dropdown.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            type_of_task_dropdown.addItems(task_types)
            self.tst_tab_layout.addWidget(type_of_task_dropdown, row + 1, 1)
            self.tst_type_of_task_dropdowns.append(type_of_task_dropdown)
            type_of_task_dropdown.currentIndexChanged.connect(self.tstDropdownChanged)
    
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
            tst_lever_arm_input.textChanged.connect(self.tstInputChanged)


            # Load (N) input
            tst_load_input = QLineEdit()
            tst_load_input.setValidator(tst_double_validator)
            tst_load_input.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_load_input, row + 1, 3)
            self.tst_load_inputs.append(tst_load_input)
            tst_load_input.textChanged.connect(self.tstInputChanged)

            # Repetitions input
            tst_repetitions_input = QLineEdit()
            tst_repetitions_input.setValidator(tst_double_validator)
            tst_repetitions_input.setAlignment(Qt.AlignCenter)
            self.tst_tab_layout.addWidget(tst_repetitions_input, row + 1, 5)
            self.tst_repetitions_inputs.append(tst_repetitions_input)
            tst_repetitions_input.textChanged.connect(self.tstInputChanged)


        # **Output labels for Moment, Damage, and % Total**
        self.tst_output_labels_matrix = [[None for _ in range(8)] for _ in range(self.num_task + 1)]
    
        for row in range(self.num_task):
            for col in [4, 6, 7]:  # Columns for output labels
                tst_label = QLabel("0.0")
                tst_label.setAlignment(Qt.AlignCenter)
                self.tst_tab_layout.addWidget(tst_label, row + 1, col)
                self.tst_output_labels_matrix[row][col] = tst_label


        # **Summary Grid Layout (Outside Scroll Area)**
        summary_layout = QGridLayout()
        self.tst_summary_layout = summary_layout
        summary_layout.setRowMinimumHeight(0, 30)
        summary_layout.setRowMinimumHeight(1, 30)
        
        # **Set Column Stretch for Precise Width Control (8 Columns)**
        summary_layout.setColumnStretch(0, 1)  # Left spacer
        summary_layout.setColumnStretch(1, 1)  # Left spacer
        summary_layout.setColumnStretch(2, 1)  # Left spacer
        summary_layout.setColumnStretch(3, 1)  # Left spacer
        summary_layout.setColumnStretch(4, 1)  # Left spacer
        summary_layout.setColumnStretch(5, 2)  # Extra space before labels
        summary_layout.setColumnStretch(6, 2)  # Label Column
        summary_layout.setColumnStretch(7, 1)  # Value Column
        
        # **Row 1: Total Cumulative Damage**
        self.tst_total_damage_label = QLabel("Total Cumulative Damage:")
        self.tst_total_damage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tst_total_damage_label.setFont(tst_bold_font)
        summary_layout.addWidget(self.tst_total_damage_label, 0, 5)  # Row 0, Col 6
        
        self.tst_total_damage_value_label = QLabel("0.0")
        self.tst_total_damage_value_label.setFont(tst_bold_font)
        self.tst_total_damage_value_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.tst_total_damage_value_label, 0, 6)  # Row 0, Col 7
        
        # **Row 2: Probability of Shoulder Outcome**
        self.tst_probability_label = QLabel("Probability of Shoulder Outcome (%):")
        self.tst_probability_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.tst_probability_label.setFont(tst_bold_font)
        summary_layout.addWidget(self.tst_probability_label, 1, 5)  # Row 1, Col 6

        self.tst_probability_value_label = QLabel("0.0")
        self.tst_probability_value_label.setFont(tst_bold_font)
        self.tst_probability_value_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self.tst_probability_value_label, 1, 6)  # Row 1, Col 7
        
        # **Add the summary layout BEFORE the button layout**
        tst_main_layout.addLayout(summary_layout)
        for widget in (
            self.tst_total_damage_label, self.tst_total_damage_value_label,
            self.tst_probability_label, self.tst_probability_value_label,
        ):
            widget.hide()



        # **Buttons**
        tst_buttons_layout = QHBoxLayout()
        
        # **Left-aligned Reset Button (Expands to take available space)**
        self.tst_reset_button = QPushButton("Reset")
        self.tst_reset_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expanding left button
        tst_buttons_layout.addWidget(self.tst_reset_button)
        
        # **Small Delete Button (Fixed Size)**
        self.tst_delete_button = QPushButton()
        self.tst_delete_button.setIcon(QIcon("../images/delete_icon01.png"))
        self.tst_delete_button.setFixedSize(30, 30)  # Small square button (adjust as needed)
        self.tst_delete_button.setIconSize(QSize(25, 25))  # Increase icon size
        tst_buttons_layout.addWidget(self.tst_delete_button)
        
        # **Small Grid Button (Fixed Size, Larger Icon)**
        self.tst_grid_button = QPushButton()
        self.tst_grid_button.setIcon(QIcon("../images/grid_icon01.png"))
        self.tst_grid_button.setFixedSize(30, 30)  # Small square button
        self.tst_grid_button.setIconSize(QSize(25, 25))  # Increase icon size
        tst_buttons_layout.addWidget(self.tst_grid_button)
        
        # **Right-aligned Calculate Button (Expands to take available space)**
        self.tst_calculate_button = QPushButton("Calculate")
        self.tst_calculate_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Expanding right button
        tst_buttons_layout.addWidget(self.tst_calculate_button)
        
        # **Add layout to main UI**
        tst_main_layout.addLayout(tst_buttons_layout)

    
    
    
    
    
    
        # **Connect the buttons to methods**
        self.tst_reset_button.clicked.connect(self.tstResetForm)
        self.tst_calculate_button.clicked.connect(self.tstCalculateResultsClicked)
        
        self.tst_delete_button.clicked.connect(self.tstDeleteAction)
        self.tst_grid_button.clicked.connect(self.toolGridAction)

        # **Create the TST tab widget and set its layout**
        self.tst_tab = QWidget()
        self.tst_tab.setLayout(tst_main_layout)
    
        # **Add TST tab to the tab widget**
        self.tabWidget.insertTab(2, self.tst_tab, "Shoulder Tool (ST)")
        
        self.any_tst_input_changed = False


    def tstCalculateResultsClicked(self):
        self.selectedMeasurementSystem = "Metric" if self.metric_action.isChecked() else "Imperial"
        if self.selectedMeasurementSystem in ["Metric", "Imperial"]:
            self.num_task = len(self.tst_lever_arm_inputs)
            self.tstCalculateResults()

    
    def tstDeleteAction(self):
        self.deleteTSTData()
        
    def tstTransferAction(self):
        transfer_dialog = ToolTransferDialog(self) 
        transfer_dialog.exec_()  # Open it as a modal window
        self.loadToolsData()

    
    def deleteTSTData(self):
        # Retrieve primary key data from UI elements
        worker_combo_text = self.workerComboBox.currentText()
        # Extract the ID from the text (assuming the format is ID (Lastname, Firstname))
        worker_id = worker_combo_text.split(" ")[0] if worker_combo_text else ""
        
        plant_name = self.plant_combo.currentText().strip()
        section_name = self.section_combo.currentText().strip()
        line_name = self.line_combo.currentText().strip()
        station_id = self.station_combo.currentText().strip()
        shift_id = self.shift_combo.currentText().strip()
        tab_index = self.tabWidget.currentIndex()
        
         
        self.validateInputsForSave()  # Also work for delete...
        
        # Connect to the database
        try:
            conn = sqlite3.connect(self.projectdatabasePath)
            cursor = conn.cursor()
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            return
    
    
        if self.checkForExistingSTData():
            reply = QMessageBox.question(self, 'Data Exists', "Existing ST data found for this Worker, Station and Shift. Delete the data?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
               
        if self.anySTTaskDataPresent():
            try:
                cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Delete existing records for the given userid and datetime
                delete_query = '''
                    DELETE FROM TstResults 
                    WHERE worker_id = ? AND plant_name = ? AND section_name = ? AND line_name = ?
                    AND station_id = ? AND shift_id = ? AND tool_id = ? 
                '''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
                conn.commit()
                
                # Delete existing entry with the same primary key
                delete_query = '''DELETE FROM WorkerStationShiftErgoTool 
                                  WHERE worker_id=? AND plant_name=? AND section_name=? AND line_name=? 
                                  AND station_id=? AND shift_id=? AND tool_id=?'''
                cursor.execute(delete_query, (worker_id, plant_name, section_name, line_name, station_id, shift_id, "ST"))
                conn.commit()
             
                self.loadToolsData()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")

            finally:
                if conn:
                    conn.close()   

    
        
    def tstDropdownChanged(self, index):
        self.any_tst_input_changed = True
        
    def tstInputChanged(self, new_text):
        self.any_tst_input_changed = True
    
    
    # ----------------------------------------------------------------------------
    # ----------------------------------------------------------------------------
    
    
    
    
    
    
    
    
    #---------------------------------------------------------------------------------
    #                       RENDER!!!!!!!!!!!!!!!!!!!!!!!
    #---------------------------------------------------------------------------------
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def setupRenderer(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.035, 0.176, 0.271)
        self.renderer.SetBackground2(0.035, 0.176, 0.271)
        self.renderer.GradientBackgroundOff()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        # Load all STL models for the scene
        self.setupActors()

        # Reset the camera to fit all actors in view
        self.renderer.ResetCamera()
        self.camera_director = VTKCameraDirector(
            self.renderer, self.vtkWidget.GetRenderWindow(), self
        )
        self.camera_director.configure(self.humanActor, {
            0: [self.lowerBackActor],
            1: [
                self.leftForeArmActor, self.leftHandActor,
                self.rightForeArmActor, self.rightHandActor,
            ],
            2: [self.leftShoulderActor, self.rightShoulderActor],
        })
        self.camera_director.apply(0)

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
        if hasattr(self, "active_region_label"):
            title, region = {
                0: ("LiFFT Body Region", "Lower Back"),
                1: ("DUET Body Region", "Distal Upper Extremity"),
                2: ("Shoulder Body Region", "Shoulders"),
            }.get(index, ("Body Region", "Active Region"))
            self.body_region_title.setText(title)
            self.active_region_label.setText(region)

        #self.loadToolsData() #TODO: check for a way to fill the tab without rebuilding it..
         
        # Ensure the variables exist and have valid values before assigning
        lifft_unit = getattr(self, "lifft_unit", None)
        duet_unit = getattr(self, "duet_unit", None)
        tst_unit = getattr(self, "tst_unit", None)
        if index == 0 and lifft_unit in ["Metric", "Imperial"]:
            self.selectedMeasurementSystem = self.lifft_unit
        elif index == 1 and duet_unit in ["Metric", "Imperial"]:
            self.selectedMeasurementSystem = self.duet_unit
        elif index == 2 and tst_unit in ["Metric", "Imperial"]:
            self.selectedMeasurementSystem = self.tst_unit
        else:
            self.selectedMeasurementSystem = self.default_metric_sys
        
        if hasattr(self, "metric_action") and hasattr(self, "imperial_action"):
            self.metric_action.setChecked(self.selectedMeasurementSystem.lower() == "metric")
            self.imperial_action.setChecked(self.selectedMeasurementSystem.lower() == "imperial")

        self.unit_label.setText(f"Unit: {self.selectedMeasurementSystem}")

    def onToolTabClicked(self, index):
        """Animate only for a tool tab explicitly selected by the user."""
        if not self.vtk_enabled or not hasattr(self, "camera_director"):
            return
        if not self.isAnimationAllowed:
            self.camera_director.applyFullBody()
            return
        if self.camera_director.active_tool != index:
            self.camera_director.animateTo(index)
    
    
    def removeDuplicateTabs(self):
        """Removes duplicate tabs in the QTabWidget based on their title."""
        seen_titles = set()
        tabs_to_remove = []
    
        for index in range(self.tabWidget.count()):
            tab_title = self.tabWidget.tabText(index)
            if tab_title in seen_titles:
                tabs_to_remove.append(index)
            else:
                seen_titles.add(tab_title)

        # Remove tabs in reverse order to avoid shifting indices
        for index in reversed(tabs_to_remove):
            self.tabWidget.removeTab(index)
        
        
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
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fatigue Failure Risk Assessment Tools")
    parser.add_argument("project_file", nargs="?", help="Path to the .ergprj project file", default=None)
    parser.add_argument(
        "--disable-vtk",
        action="store_true",
        help="Skip the 3D renderer for headless UI review and screenshots",
    )
    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    window = ErgoTools(disable_vtk=args.disable_vtk)
    window.setWindowTitle("Fatigue Failure Risk Assessment Tools")

    # Set a fixed size for the main window
    window.setFixedSize(1550, 1015)  # Preserve the complete 3D model after adding the worker alphabet row.

    # If a project file path is provided, call the openFilePath function
    if args.project_file:
        window.openFilePath(args.project_file)

    window.show()
    sys.exit(app.exec_())    
    
    
