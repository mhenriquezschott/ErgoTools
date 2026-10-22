"""Reviewed reference worker-transfer palette and component styling.

Presentation theme layer. Worker Transfer source/destination selection, saved-tool
tables, preview, mode segments and disabled actions.

This data-only module retains the original application palette, font declarations, pixel
spacing and object-name/dynamic-property selectors. Desktop hosts set stable widget
object names and apply the stylesheet; translated captions and literal user data do not
participate in selector identity. It constructs no widgets and owns no event/signal,
persistence, solver or scientific behavior. Preserve exact stylesheet bytes during
documentation changes.
"""

# Original Qt stylesheet for worker Transfer source/destination selection, saved-tool
# tables, preview, mode segments and disabled actions.
WORKER_TRANSFER_STYLE = """
            QDialog#workerTransferDialog { background: #F4F7F9;
 color: #1B2933;
 font: 12px "Segoe UI";
 }
            QFrame#transferPanel { background: white;
 border: 1px solid #D5DEE5;
 border-radius: 7px;
 }
            QLabel#dialogTitle { color: #0B326C;
 font-size: 20px;
 font-weight: 700;
 }
            QLabel#panelTitle { color: #0B326C;
 font-size: 14px;
 font-weight: 700;
 }
            QLabel#supportingText { color: #405462;
 font-size: 12px;
 }
            QLabel#sourceWorker { color: #0B326C;
 font-size: 16px;
 font-weight: 700;
 }
            QLabel#contextPath { color: #405462;
 font-weight: 600;
 }
            QLabel#previewBox { background: #EAF7F8;
 color: #164655;
 border: 1px solid #B6DDE1;
 border-radius: 5px;
 padding: 9px;
 }
            QLabel#emptyTools { background: #F4F7F9;
 color: #5F6F7A;
 border: 1px solid #D5DEE5;
 border-radius: 5px;
 padding: 14px;
 font-weight: 600;
 }
            QLineEdit, QComboBox { min-height: 32px;
 background: white;
 border: 1px solid #BCC9D3;
 border-radius: 5px;
 padding: 0 8px;
 }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #08A9B5;
 }
            QComboBox QAbstractItemView { background: white;
 color: #1B2933;
 selection-background-color: #087E91;
 selection-color: white;
 }
            QTableWidget, QTreeWidget { background: white;
 color: #1B2933;
 border: 1px solid #BCC9D3;
 border-radius: 5px;
 alternate-background-color: #F7FAFB;
 gridline-color: #E3E9ED;
 }
            QTableWidget::item:selected, QTreeWidget::item:selected {
 background: #087E91;
 color: white;
 }
            QTreeWidget::item { min-height: 29px;
 padding: 2px 4px;
 }
            QHeaderView::section { background: #EAF2F6;
 color: #0B326C;
 border: 0;
 border-bottom: 1px solid #BCC9D3;
 padding: 7px 5px;
 font-weight: 700;
 }
            QPushButton { min-height: 34px;
 background: white;
 color: #0B326C;
 border: 1px solid #9EB0BE;
 border-radius: 5px;
 padding: 0 12px;
 font-weight: 650;
 }
            QPushButton:hover { background: #EDF7F8;
 border-color: #08A9B5;
 }
            QPushButton#primaryButton { background: #087E91;
 color: white;
 border: 1px solid #087E91;
 }
            QPushButton#primaryButton:hover { background: #096D7C;
 }
            QPushButton#primaryButton:disabled { background: #DCE4E9;
 color: #8796A0;
 border-color: #C7D1D8;
 }
            QPushButton#alphabetButton { min-width: 20px;
 max-width: 20px;
 min-height: 29px;
 max-height: 29px;
 padding: 0;
 border: 0;
 background: transparent;
 color: #5F6F7A;
 font-size: 10px;
 }
            QPushButton#alphabetButton:hover { background: #DDF3F5;
 color: #0B326C;
 font-size: 15px;
 }
            QPushButton#alphabetButton:checked { background: #0B326C;
 color: white;
 border-radius: 4px;
 font-weight: 700;
 }
            QPushButton#alphabetButton:disabled { color: #CBD4DA;
 }
            QRadioButton { min-height: 38px;
 padding: 0 10px;
 color: #0B326C;
 font-weight: 700;
 border: 1px solid #BCC9D3;
 border-radius: 5px;
 background: white;
 }
            QRadioButton:checked { color: white;
 background: #0B326C;
 border-color: #0B326C;
 }
            QRadioButton { spacing: 0;
 }
            QRadioButton::indicator { image: none;
 width: 0;
 height: 0;
 }
            QCheckBox { color: #1B2933;
 font-weight: 600;
 spacing: 8px;
 }
            QCheckBox::indicator { width: 17px;
 height: 17px;
 }
            QToolTip { background: #1B2933;
 color: white;
 border: 1px solid #0B326C;
 padding: 6px;
 }
        """
