"""Retained diagnostic-editor stylesheet preserving audited ErgoTools palette.

Retained diagnostic-editor stylesheet preserving audited ErgoTools palette and controls.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

# Retained diagnostic-editor palette and controls; integrated navigation composes its
# own theme.
WORKSPACE_STYLE = """
QMainWindow, QWidget#workspace { background: #F4F7F9; color: #1B2933;
    font: 12px "Segoe UI"; }
QFrame#brand { background: #073E68; border-radius: 7px; }
QLabel#brandName { color: white; font-size: 30px; font-weight: 700; }
QLabel#subtitle { color: #D9EDF5; font-size: 15px; }
QFrame#panel { background: white; border: 1px solid #D5DEE5; border-radius: 7px; }
QLabel { color: #1B2933; background: transparent; }
QLabel#value { color: #F97316; font-size: 26px; font-weight: 600; }
QPushButton { background: white; color: #0B326C; border: 1px solid #BCC9D3;
    border-radius: 5px; padding: 7px 10px; min-height: 26px; }
QPushButton:hover { background: #EAF7F8; }
QPushButton:disabled { color: #89969E; background: #F4F7F9; }
QPushButton#calculate { background: #087E91; color: white; border-color: #087E91; }
QPushButton#calculate:hover { background: #096D7C; }
QPushButton#calculate:disabled { background: #E3E9ED; color: #89969E;
    border-color: #BCC9D3; }
QComboBox, QLineEdit { min-height: 30px; background: white; color: #1B2933;
    border: 1px solid #BCC9D3; border-radius: 5px; padding: 0 8px; }
QComboBox:focus, QLineEdit:focus { border: 2px solid #08A9B5; }
QComboBox QAbstractItemView { background: white; color: #1B2933;
    selection-background-color: #087E91; selection-color: white; }
QTableWidget { background: white; color: #1B2933; gridline-color: #E3E9ED;
    border: 1px solid #D5DEE5; selection-background-color: #087E91;
    selection-color: white; }
QHeaderView::section { background: #EDF7F8; color: #0B326C; padding: 9px 6px;
    border: 0; font-weight: 600; }
QMessageBox, QInputDialog { background: #F4F7F9; }
QToolTip { color: #1B2933; background: white; border: 1px solid #BCC9D3; }
"""


# Shared title-row history buttons use the established navy/teal palette.
# QAction remains the sole source of tooltips, shortcuts and enablement.
HISTORY_BUTTON_STYLE = """
QToolButton#historyButton { color: #003366; background: white;
    border: 1px solid #CBD9E5; border-radius: 4px; padding: 4px; }
QToolButton#historyButton:hover { background: #DCF3F5; border-color: #00B3C4; }
QToolButton#historyButton:disabled { color: #8A9BA8; }
"""
