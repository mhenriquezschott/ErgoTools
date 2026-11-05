"""Original Worker Management palette and control treatment.

Presentation theme layer. Worker Management cards, demographics, calendar, table,
navigation, optional fields and notification/action states.

This data-only module retains the original application palette, font declarations,
pixel spacing and object-name/dynamic-property selectors. AlphabetNavigation owns the
shared letter-strip appearance, including availability and hover styling. Desktop
hosts set stable widget object names and apply the stylesheet; translated captions
and literal user data do not participate in selector identity. It constructs no
widgets and owns no event/signal, persistence, solver or scientific behavior.
Preserve exact stylesheet bytes during documentation changes.
"""

# Original Qt stylesheet for worker Management cards, demographics, calendar, table,
# navigation, optional fields and notification/action states.
WORKER_MANAGEMENT_STYLE = """
            QDialog#workerManagementDialog {
                background: #F4F7F9;
                color: #1B2933;
                font-family: Inter, "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QLabel#dialogTitle {
                color: #0B326C;
                font-size: 22px;
                font-weight: 600;
            }
            QLabel#dialogSubtitle, QLabel#supportingText {
                color: #5F6F7A;
            }
            QLabel#sectionTitle {
                color: #0B326C;
                font-size: 16px;
                font-weight: 600;
            }
            QLabel#eyebrow {
                color: #5F6F7A;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#calculatedValue {
                background: #EAF7F8;
                border: 1px solid #B8E1E4;
                border-radius: 6px;
                color: #0B326C;
                font-weight: 600;
                padding: 7px 10px;
            }
            QFrame#card {
                background: #FFFFFF;
                border: 1px solid #D5DEE5;
                border-radius: 8px;
            }
            QFrame#divider {
                color: #D5DEE5;
                background: #D5DEE5;
                max-height: 1px;
            }
            QFrame#notificationArea {
                border-radius: 6px;
                border: 1px solid #B8E1E4;
                background: #EAF7F8;
            }
            QFrame#notificationArea[severity="warning"] {
                border-color: #E4A11B;
                background: #FFF7E6;
            }
            QFrame#notificationArea[severity="error"] {
                border-color: #C93C3C;
                background: #FFF0F0;
            }
            QLabel#notificationLabel {
                color: #1B2933;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QComboBox, QDateEdit, QSpinBox {
                min-height: 34px;
                background: #FFFFFF;
                border: 1px solid #BCC9D3;
                border-radius: 6px;
                padding: 0 9px;
                selection-background-color: #08A9B5;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
                border: 2px solid #08A9B5;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #E8F3F6;
                border-bottom: 1px solid #C6D5DD;
            }
            QCalendarWidget QToolButton {
                color: #0B326C;
                background: transparent;
                border: 0;
                border-radius: 4px;
                padding: 5px 8px;
                font-weight: 600;
            }
            QCalendarWidget QToolButton:hover {
                background: #D6ECEF;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background: #FFFFFF;
                alternate-background-color: #F4F7F9;
                color: #1B2933;
                selection-background-color: #087E91;
                selection-color: #FFFFFF;
                outline: 0;
            }
            QTableWidget {
                background: #FFFFFF;
                alternate-background-color: #F7FAFC;
                border: 1px solid #D5DEE5;
                border-radius: 6px;
                gridline-color: #E6ECF0;
                outline: 0;
            }
            QTableWidget::item {
                padding: 8px 6px;
            }
            QTableWidget::item:selected {
                background: #DDF3F5;
                color: #0B326C;
            }
            QHeaderView::section {
                background: #EDF3F6;
                color: #0B326C;
                border: 0;
                border-bottom: 1px solid #D5DEE5;
                padding: 9px 6px;
                font-weight: 600;
            }
            QTabWidget#detailsTabs::pane {
                border: 0;
                border-top: 1px solid #D5DEE5;
                top: -1px;
            }
            QTabWidget#detailsTabs QTabBar::tab {
                background: #EDF3F6;
                color: #405866;
                border: 1px solid #CAD5DD;
                padding: 9px 16px;
                min-width: 180px;
                font-weight: 600;
            }
            QTabWidget#detailsTabs QTabBar::tab:selected {
                background: #FFFFFF;
                color: #087E91;
                border-bottom: 2px solid #08A9B5;
            }
            QPushButton {
                min-height: 42px;
                background: #FFFFFF;
                color: #0B326C;
                border: 1px solid #9EB0BE;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #EDF7F8;
                border-color: #08A9B5;
            }
            QPushButton#primaryButton {
                background: #0B326C;
                color: #FFFFFF;
                border-color: #0B326C;
            }
            QPushButton#primaryButton:hover {
                background: #12447F;
            }
            QPushButton#primaryOutlineButton {
                background: #FFFFFF;
                color: #0B326C;
                border: 2px solid #08A9B5;
            }
            QPushButton#primaryOutlineButton:hover {
                background: #EAF7F8;
            }
            QPushButton#dangerButton {
                color: #C93C3C;
                border-color: #D86A6A;
            }
            QPushButton#dangerButton:hover {
                background: #FFF1F1;
            }
            QPushButton#navButton {
                min-height: 30px;
                padding: 0;
            }
            QPushButton#pageButton {
                min-height: 30px;
                padding: 0 7px;
                font-size: 12px;
            }
            QLabel#pageLabel {
                color: #5F6F7A;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#recordNavigationLabel {
                color: #5F6F7A;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#alphabetLabel {
                color: #5F6F7A;
                font-size: 11px;
                font-weight: 600;
                padding-right: 4px;
            }
            
            
            
            
            QPushButton:disabled {
                background: #EEF2F4;
                color: #9AA7B0;
                border-color: #D5DEE5;
            }
            QToolButton#optionalToggle {
                min-height: 38px;
                background: #F4F7F9;
                color: #0B326C;
                border: 1px solid #D5DEE5;
                border-radius: 6px;
                padding: 0 10px;
                font-weight: 600;
                text-align: left;
            }
            QToolButton#optionalToggle:hover {
                border-color: #08A9B5;
                background: #EDF7F8;
            }
            QTabWidget#detailsTabs::pane {
                border: 0;
            }
            QScrollArea#detailsScroll, QWidget#detailsContent {
                background: #FFFFFF;
                border: 0;
            }
            QScrollBar:vertical {
                background: #EDF3F6;
                width: 9px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #9EB0BE;
                border-radius: 4px;
                min-height: 28px;
            }
            QToolTip {
                background: #1B2933;
                color: #FFFFFF;
                border: 1px solid #0B326C;
                padding: 6px;
            }
        """


# Shared workplace-first picker uses the established worker palette and packaged icons.
# Native tree/field semantics remain with Qt; selectors never use translated text.
WORKER_MANAGEMENT_STYLE += """
QDialog#workplaceAssignmentDialog { background: #F4F7F9; color: #1B2933; }
QTreeWidget#workplaceTree { background: white; color: #1B2933;
    border: 1px solid #BCC9D3; border-radius: 5px; }
QTreeWidget#workplaceTree::item { min-height: 30px; padding: 2px 5px; }
QTreeWidget#workplaceTree::item:selected { background: #DDF3F5; color: #0B326C; }
QTreeWidget#workplaceTree QHeaderView::section { background: #EDF3F6;
    color: #0B326C; padding: 8px; border: 0; font-weight: 600; }
"""
