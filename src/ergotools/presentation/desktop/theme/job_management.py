"""Applicable original main-workspace and Job Management stylesheet rules.

Presentation theme layer. Job metadata groups, main-style tool tabs, segmented input
modes, source-picker trees and result cards share focus/hover/disabled/danger states.

This data-only module retains the original application palette, font declarations, pixel
spacing and object-name/dynamic-property selectors. Desktop hosts set stable widget
object names and apply the stylesheet; translated captions and literal user data do not
participate in selector identity. It constructs no widgets and owns no event/signal,
persistence, solver or scientific behavior. Palette and geometry affect presentation
only; they never alter saved values.
"""

# Original Qt stylesheet for job Management cards, tool tabs and current risk tables,
# with focus/hover/disabled/danger states.
JOB_MANAGEMENT_STYLE = """
QFrame#contextBar, QFrame#workspacePanel, QFrame#resultsSidebar { background: white;
border: 1px solid #D5DEE5; border-radius: 7px; }
QLabel#contextLabel, QLabel#panelTitle, QLabel#summaryTitle { color: #0B326C;
font-weight: 600; }
QLabel#dialogTitle { color: #0B326C; font-size: 20px; font-weight: 700; }
QPushButton#contextToggleButton {
text-align: left; color: #0B326C;
background: transparent; border: 0; padding: 0 4px; font-weight: 700;
}
QPushButton#contextToggleButton:hover { color: #087E91; background: #EDF7F8; }
QLabel#supportingText { color: #405462; font-size: 12px; }
QComboBox, QLineEdit { min-height: 30px; background: white; border: 1px solid
#BCC9D3; border-radius: 5px; padding: 0 8px; }
QComboBox:focus, QLineEdit:focus { border: 2px solid #08A9B5; }
QComboBox QAbstractItemView {
background: white; color: #1B2933; border: 1px solid #9EB0BE;
selection-background-color: #087E91; selection-color: white;
outline: 0; padding: 3px;
}
QComboBox QAbstractItemView::item:selected,
QComboBox QAbstractItemView::item:hover { background: #087E91; color: white; }
QPushButton { min-height: 32px; background: white; color: #0B326C; border: 1px solid
#9EB0BE; border-radius: 5px; padding: 0 12px; font-weight: 600; }
QPushButton:hover { background: #EDF7F8; border-color: #08A9B5; }
QPushButton#compactButton { padding: 0 9px; }
QPushButton#mainAlphabetButton {
min-width: 18px; max-width: 18px; min-height: 27px; max-height: 27px;
padding: 0; border: 0; background: transparent; color: #173544;
font-size: 11px; font-weight: 850;
}
QPushButton#mainAlphabetButton:hover { background: #DDF3F5; color: #0B326C;
font-size: 16px; }
QPushButton#mainAlphabetButton:checked { background: #0B326C; color: white;
border-radius: 4px; font-size: 11px; }
QPushButton#mainAlphabetButton[currentInitial="true"] { color: #001C2B; font-weight:
900; font-size: 13px; }
QPushButton#mainAlphabetButton:checked[currentInitial="true"] { color: white; }
QPushButton#mainAlphabetButton:disabled { color: #C7D0D7; font-weight: 600;
font-size: 10px; }
QPushButton#primaryOutlineButton { border: 2px solid #08A9B5; }
QPushButton#calculateButton { background: #087E91; color: white; border-color:
#087E91; }
QPushButton#calculateButton:hover { background: #096D7C; }
QPushButton:disabled, QPushButton#calculateButton:disabled {
color: #6F7E88; background: #F2F5F7; border-color: #D5DEE5; }
QPushButton#resetButton { color: #0B326C; }
QToolTip { background: #1B2933; color: white; border: 1px solid #0B326C; padding:
6px; }
QDialog#jobWindow { background: #F4F7F9; color: #1B2933; font: 12px "Segoe UI"; }
QTextEdit { background: white; border: 1px solid #BCC9D3; border-radius: 5px;
padding: 6px; }
QTextEdit:focus { border: 2px solid #08A9B5; }
QTableWidget { background: white; alternate-background-color: #F5F8FA; border: 1px
solid #CAD5DD;
gridline-color: #D5DEE5; selection-background-color: #087E91; selection-color: white;
}
QHeaderView::section { background: #EAF1F5; color: #0B326C; border: 0; border-right:
1px solid #CAD5DD;
border-bottom: 1px solid #CAD5DD; padding: 7px; font-weight: 700; }
QPushButton#dangerButton { color: #C73737; border-color: #E0A2A2; }
QPushButton#dangerButton:hover { background: #FFF0F0; border-color: #C73737; }
QPushButton#primaryOutlineButton:disabled { color: #8998A3; background: #F2F5F7;
border: 1px solid #D5DEE5; }
QGroupBox { color: #0B326C; font-weight: 700; border: 1px solid #D5DEE5;
border-radius: 6px; margin-top: 9px; padding-top: 7px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QFrame#summaryCard { background: white; border: 1px solid #D5DEE5; border-radius: 6px; }
QTreeWidget { background: white; alternate-background-color: #F5F8FA;
border: 1px solid #CAD5DD; selection-background-color: #DDF3F5;
selection-color: #0B326C; }
QTreeWidget::item { min-height: 31px; }
QPushButton#copyAlphabetButton { padding: 0; min-height: 26px; border: 0;
background: transparent; font-size: 11px; }
QPushButton#copyAlphabetButton:checked { background: #0B326C; color: white; }
QPushButton#copyAlphabetButton:hover { background: #DDF3F5; }

QLabel#inputError { color: #B3261E; }
QComboBox:disabled, QDateEdit:disabled, QSpinBox:disabled {
color: #304652; background: #F2F5F7; border-color: #D5DEE5;
}

"""

# Local style overrides the main assessment area's fixed-width context-button rules.
JOB_INPUT_MODE_STYLE = """
QPushButton { padding: 0 16px; min-height: 32px;
 border: 1px solid #BCC9D3; border-radius: 0; color: #405462; }
QPushButton:checked { background: #DDF3F5; color: #008DA4;
 border-color: #00B3C4; }
QPushButton:hover { background: #EAF7F8; }
"""

# Project identity stays visible while the large Job editor covers its main owner.
JOB_MANAGEMENT_STYLE += """
QLabel#jobProjectBadge { background: transparent; color: #0B5274;
 border: 0; padding: 5px 10px; }
"""

# Job-specific heading sizes leave copy-picker and other dialog titles unchanged.
JOB_MANAGEMENT_STYLE += """
QLabel#jobManagementTitle { color: #0B326C; font-size: 22px; font-weight: 700; }
QLabel#jobAssessmentHeading { color: #0B326C; font-size: 14px; font-weight: 600; }
"""
