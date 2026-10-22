"""Reviewed reference main-window stylesheet for original-layout ports.

Presentation theme layer. Integrated main workspace: brand/toolbar, avatar panel,
assessment tabs, context, result cards, footer and shared controls.

This data-only module retains the original application palette, font declarations, pixel
spacing and object-name/dynamic-property selectors. Desktop hosts set stable widget
object names and apply the stylesheet; translated captions and literal user data do not
participate in selector identity. It constructs no widgets and owns no event/signal,
persistence, solver or scientific behavior. Preserve exact stylesheet bytes during
documentation changes.
"""

# Original Qt stylesheet for integrated main workspace: brand/toolbar, avatar panel,
# assessment tabs, context, result cards, footer and shared controls.
MAIN_WORKSPACE_STYLE = """
            QPushButton#contextModeButton {
                min-height: 30px; padding: 0 10px; border-radius: 0;
                border: 1px solid #9EB0BE; color: #405462;
            }
            QPushButton#contextModeButton:checked {
                background: #DDF3F5; color: #087E91;
                border: 2px solid #08A9B5; font-weight: 700;
            }
            QMainWindow, QWidget#mainWorkspace {
                background: #F4F7F9;
                color: #1B2933;
                font: 12px "Segoe UI";
               
            }
            QFrame#brandHeader { background: #073E68; border-radius: 7px; }
            QLabel#brandName { color: white; font-size: 36px; font-weight: 700; }
            QLabel#projectName {
                color: #D9EDF5;
                font-size: 16px;
                font-weight: 700;
               
            }
            QToolBar#mainToolbar {
                background: white;
                border: 0;
                border-radius: 6px;
                padding: 5px 7px;
                spacing: 3px;
               
            }
            QToolBar#mainToolbar QToolButton {
                color: #0B326C;
                min-width: 56px;
                padding: 6px 5px;
                border: 0;
               
            }
            QToolBar#mainToolbar QToolButton:hover {
                background: #EAF7F8;
                border-radius: 5px;
               
            }
            QToolBar#mainToolbar::separator {
                background: #D5DEE5;
                width: 1px;
                margin: 8px 6px;
               
            }
            QFrame#contextBar, QFrame#workspacePanel, QFrame#resultsSidebar {
                background: white;
                border: 1px solid #D5DEE5;
                border-radius: 7px;
               
            }
            QFrame#bodyRegionPanel {
                background: #092D45;
                border: 1px solid #174963;
                border-radius: 7px;
                color: white;
               
            }
            QFrame#bodyRegionPanel QLabel {
                color: white;
                background: transparent;
                border: 0;
               
            }
            QLabel#bodyRegionTitle, QLabel#bodySectionTitle {
                color: white;
                font-weight: 700;
               
            }
            QLabel#bodyRiskLabel { color: white; font-size: 11px; }
            QLabel#bodyRiskRange { color: white; font-size: 10px; }
            QFrame#activeRegionPanel { background: #092D45; border: 0; }
            QLabel#activeRegionName {
                background: #092D45;
                color: white;
                font-size: 14px;
                font-weight: 700;
               
            }
            QLabel#activeRegionCaption {
                background: #092D45;
                color: #66C7FF;
                font-size: 12px;
                font-weight: 600;
               
            }
            QLabel#bodyInfoIcon {
                border: 2px solid #D7E6EE;
                border-radius: 9px;
                font-weight: 700;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
               
            }
            QLabel#activeRegionName {
                color: white;
                font-size: 16px;
                font-weight: 700;
               
            }
            QLabel#activeRegionCaption { color: #42B8E8; font-weight: 600; }
            QFrame#bodyPanelDivider { background: #376077; border: 0; }
            QWidget#vtkWorkspace { background: #092D45; border: 0; }
            QToolButton#modelViewButton {
                color: white;
                background: transparent;
                border: 0;
                padding: 4px 1px;
                font-size: 10px;
               
            }
            QToolButton#modelViewButton:hover {
                background: #174963;
                border-radius: 4px;
               
            }
            QLabel#contextLabel, QLabel#panelTitle, QLabel#summaryTitle {
                color: #0B326C;
                font-weight: 600;
               
            }
            QLabel#dialogTitle {
                color: #0B326C;
                font-size: 20px;
                font-weight: 700;
               
            }
            QLabel#contextArrow { color: #08A9B5; font-weight: 700; }
            QLabel#contextSummary {
                color: #405462;
                font-size: 12px;
                font-weight: 600;
               
            }
            QPushButton#contextToggleButton {
                text-align: left; color: #0B326C;
                background: transparent;
                border: 0;
                padding: 0 4px;
                font-weight: 700;
            }
            QPushButton#contextToggleButton:hover {
                color: #087E91;
                background: #EDF7F8;
               
            }
            QLabel#supportingText { color: #405462; font-size: 12px; }
            QFrame#resultsSidebar QLabel { font-size: 13px; }
            QFrame#resultsSidebar QLabel#summaryTitle {
                font-size: 14px;
                font-weight: 700;
               
            }
            QLabel#riskOutcome {
                color: #304652;
                font-size: 13px;
                font-weight: 650;
               
            }
            QComboBox, QLineEdit {
                min-height: 30px;
                background: white;
                border: 1px solid #BCC9D3;
                border-radius: 5px;
                padding: 0 8px;
               
            }
            QComboBox:focus, QLineEdit:focus { border: 2px solid #08A9B5; }
            QComboBox QAbstractItemView {
                background: white; color: #1B2933; border: 1px solid #9EB0BE;
                selection-background-color: #087E91; selection-color: white;
                outline: 0; padding: 3px;
            }
            QComboBox QAbstractItemView::item:selected,
            QComboBox QAbstractItemView::item:hover {
                background: #087E91;
                color: white;
               
            }
            QPushButton {
                min-height: 32px;
                background: white;
                color: #0B326C;
                border: 1px solid #9EB0BE;
                border-radius: 5px;
                padding: 0 12px;
                font-weight: 600;
               
            }
            QPushButton:hover { background: #EDF7F8; border-color: #08A9B5; }
            QPushButton#compactButton { padding: 0 9px; }
            QPushButton#mainAlphabetButton {
                min-width: 18px;
                max-width: 18px;
                min-height: 27px;
                max-height: 27px;
                padding: 0; border: 0; background: transparent; color: #173544;
                font-size: 11px; font-weight: 850;
            }
            QPushButton#mainAlphabetButton:hover {
                background: #DDF3F5;
                color: #0B326C;
                font-size: 16px;
               
            }
            QPushButton#mainAlphabetButton:checked {
                background: #0B326C;
                color: white;
                border-radius: 4px;
                font-size: 11px;
               
            }
            QPushButton#mainAlphabetButton[currentInitial="true"] {
                color: #001C2B;
                font-weight: 900;
                font-size: 13px;
               
            }
            QPushButton#mainAlphabetButton:checked[currentInitial="true"] {
                color: white;
               
            }
            QPushButton#mainAlphabetButton:disabled {
                color: #C7D0D7;
                font-weight: 600;
                font-size: 10px;
               
            }
            QPushButton#primaryOutlineButton { border: 2px solid #08A9B5; }
            QPushButton#calculateButton {
                background: #087E91;
                color: white;
                border-color: #087E91;
               
            }
            QPushButton#calculateButton:hover { background: #096D7C; }
            QPushButton#clearAssessmentButton { color: #0B326C; }
            QTabWidget#assessmentTabs::pane { border: 0; background: white; }
            QTabWidget#assessmentTabs QTabBar::tab {
                min-height: 41px;
                padding: 9px 4px;
                color: #5F6F7A;
                border: 0;
                font-size: 13px;
                font-weight: 600;
               
            }
            QTabWidget#assessmentTabs QTabBar::tab:selected {
                color: #087E91;
                font-weight: 600;
                border-bottom: 3px solid #08A9B5;
               
            }
            QScrollArea, QScrollArea QWidget {
                background: white;
                border-color: #D5DEE5;
               
            }
            QFrame#summaryCard {
                background: white;
                border: 1px solid #D5DEE5;
                border-radius: 6px;
               
            }
            QLabel#metricValue {
                color: #F97316;
                font-size: 20px;
                font-weight: 600;
               
            }
            QLabel#riskSeverity { font-size: 11px; font-weight: 700; }
            QLabel#metricSmallValue {
                color: #0B326C;
                font-size: 14px;
                font-weight: 750;
               
            }
            QLabel#readyStatus {
                color: #C17B00;
                font-size: 15px;
                font-weight: 800;
               
            }
            QLabel#readyStatus[ready="true"] { color: #16813A; }
            QProgressBar {
                min-height: 8px;
                max-height: 8px;
                border: 0;
                background: #DCE4E9;
                border-radius: 4px;
               
            }
            QProgressBar::chunk { background: #08A9B5; border-radius: 4px; }
            QFrame#workspaceFooter {
                background: #F4F7F9;
                border: 0;
                color: #5F6F7A;
               
            }
            QFrame#workspaceFooter QLabel {
                background: transparent;
                color: #344B5A;
                font-size: 13px;
                font-weight: 600;
               
            }
            QStatusBar { background: #F4F7F9; color: #5F6F7A; border: 0; }
            QStatusBar::item { border: 0; }
            QGroupBox {
                color: #0B326C;
                border: 1px solid #D5DEE5;
                border-radius: 5px;
                margin-top: 8px;
               
            }
            QSlider::groove:horizontal {
                height: 5px;
                background: #D5DEE5;
                border-radius: 2px;
               
            }
            QSlider::handle:horizontal {
                width: 14px;
                margin: -5px 0;
                background: #08A9B5;
                border-radius: 7px;
               
            }
            QToolTip {
                background: #1B2933;
                color: white;
                border: 1px solid #0B326C;
                padding: 6px;
               
            }
        
"""
