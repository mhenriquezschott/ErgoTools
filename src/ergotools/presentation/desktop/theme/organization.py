"""Original Organization Management styling.

Presentation theme layer. Organization hierarchy tree, exact-identity forms, optional
fields, tabs and action/notification states.

This data-only module retains the original application palette, font declarations, pixel
spacing and object-name/dynamic-property selectors. Desktop hosts set stable widget
object names and apply the stylesheet; translated captions and literal user data do not
participate in selector identity. It constructs no widgets and owns no event/signal,
persistence, solver or scientific behavior. Preserve exact stylesheet bytes during
documentation changes.
"""

# Original Qt stylesheet for organization hierarchy tree, exact-identity forms, optional
# fields, tabs and action/notification states.
ORGANIZATION_STYLE = (
    "\n            QDialog#organizationDialog { background: "
    '#F4F7F9; color: #1B2933; font: 13px "Segoe UI"; }'
    "\n            QLabel#dialogTitle { color: #0B326C; font-"
    "size: 22px; font-weight: 600; }\n            "
    "QLabel#dialogSubtitle { color: #5F6F7A; }\n            "
    "QLabel#sectionTitle { color: #0B326C; font-size: 16px; "
    "font-weight: 600; }\n            QLabel#eyebrow { color: "
    "#5F6F7A; font-size: 11px; font-weight: 600; }\n            "
    "QFrame#card { background: white; border: 1px solid "
    "#D5DEE5; border-radius: 8px; }\n            QTreeWidget { "
    "background: white; alternate-background-color: #F7FAFC; "
    "border: 1px solid #D5DEE5; }\n            QTreeWidget::item"
    " { min-height: 30px; padding: 2px 5px; }\n            "
    "QTreeWidget::item:selected { background: #DDF3F5; color: "
    "#0B326C; }\n            QHeaderView::section { background: "
    "#EDF3F6; color: #0B326C; border: 0; padding: 8px; font-"
    "weight: 600; }\n            QLineEdit, QTextEdit { "
    "background: white; border: 1px solid #BCC9D3; border-"
    "radius: 6px; padding: 7px 9px; }\n            "
    "QLineEdit:focus, QTextEdit:focus { border: 2px solid "
    "#08A9B5; }\n            QLineEdit:disabled { background: "
    "#EEF2F4; color: #687781; }\n            QPushButton { min-"
    "height: 42px; background: white; color: #0B326C; border: "
    "1px solid #9EB0BE; border-radius: 6px; padding: 0 15px; "
    "font-weight: 600; }\n            QPushButton:hover { "
    "background: #EDF7F8; border-color: #08A9B5; }\n            "
    "QPushButton#primaryButton { background: #0B326C; color: "
    "white; border-color: #0B326C; }\n            "
    "QPushButton#primaryOutlineButton { border: 2px solid "
    "#08A9B5; }\n            QPushButton#dangerButton { color: "
    "#C93C3C; border-color: #D86A6A; }\n            "
    "QLabel#notificationLabel { background: #EAF7F8; border: "
    "1px solid #B8E1E4; border-radius: 6px; padding: 9px 12px; "
    "}\n            QScrollArea, QScrollArea "
    "QWidget#qt_scrollarea_viewport, QWidget#formContent, "
    "QWidget#optionalContent {\n                background: "
    "white;\n                border: 0;\n            }"
    "\n            QToolButton#optionalToggle {\n                "
    "min-height: 38px; background: #F4F7F9; color: #0B326C;"
    "\n                border: 1px solid #D5DEE5; border-radius:"
    " 6px; padding: 0 10px;\n                font-weight: 600; "
    "text-align: left;\n            }\n            "
    "QToolButton#optionalToggle:hover { border-color: #08A9B5; "
    "background: #EDF7F8; }\n            QTabWidget::pane { "
    "border: 1px solid #D5DEE5; }\n            QTabBar::tab { "
    "padding: 8px 18px; color: #5F6F7A; }\n            "
    "QTabBar::tab:selected { color: #0B326C; font-weight: 600; "
    "border-bottom: 2px solid #08A9B5; }\n            QToolTip {"
    " background: #1B2933; color: white; border: 1px solid "
    "#0B326C; padding: 6px; }\n        "
)


# Keep Qt's native clock frame/arrows. Styling its outer border suppresses native
# glyphs on the approved desktop style; remove only the inner editor's duplicate
# field border. The new unchecked day indicator must remain visible.
ORGANIZATION_STYLE += """
QAbstractSpinBox QLineEdit { border: 0; padding: 0; background: transparent; }
QCheckBox#shiftEndsNextDay { color: #1B2933; spacing: 6px; }
QCheckBox#shiftEndsNextDay::indicator:unchecked { background: white;
    border: 1px solid #BCC9D3; border-radius: 2px; }
QCheckBox#shiftEndsNextDay:disabled { color: #89969E; }
"""
