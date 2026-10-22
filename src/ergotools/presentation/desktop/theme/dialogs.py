"""Theme ErgoTools-owned forms/prompts while preserving system chooser defaults.

Presentation layer. One scoped application stylesheet supplies the common palette,
typography and controls. Existing per-dialog styles retain Qt local priority.
Ordinary prompts share the theme; file/color/font choosers retain platform defaults.
Window-manager decorations remain owned by the desktop. No project, preference
or filesystem operations occur here.
"""

from PyQt5.QtWidgets import QApplication, QDialog

# Shared navy/teal palette and logical-pixel spacing from the integrated application.
# Installed only on dialogs; specific local selectors retain priority.
# Keep checkbox/radio backgrounds native: transparent QSS removes their unchecked
# indicator outlines. Labels alone use transparent backgrounds. An explicit
# unchecked border also survives inherited dialog styles; checked ticks stay native.
DIALOG_STYLE = """
QDialog { background: #F4F7F9; color: #1B2933; font: 12px "Segoe UI"; }
QDialog QLabel { color: #1B2933; background: transparent; }
QDialog QCheckBox, QDialog QRadioButton { color: #1B2933; }
QDialog QCheckBox::indicator:unchecked { background: white;
    border: 1px solid #BCC9D3; border-radius: 2px; }
QDialog QCheckBox::indicator:unchecked:disabled { background: #F4F7F9;
    border-color: #D5DEE5; }
QDialog QPushButton { background: white; color: #0B326C; border: 1px solid #BCC9D3;
    border-radius: 5px; padding: 7px 10px; min-height: 26px; }
QDialog QToolButton { background: white; color: #0B326C; border: 1px solid #BCC9D3;
    border-radius: 4px; padding: 4px; }
QDialog QPushButton:hover { background: #EAF7F8; }
QDialog QPushButton:focus { border: 2px solid #08A9B5; }
QDialog QPushButton:disabled { color: #89969E; background: #F4F7F9; }
QDialog QLineEdit, QDialog QComboBox, QDialog QAbstractSpinBox {
    background: white; color: #1B2933; border: 1px solid #BCC9D3;
    border-radius: 5px; min-height: 28px; padding: 0 8px; }
QDialog QLineEdit:disabled, QDialog QComboBox:disabled,
QDialog QAbstractSpinBox:disabled {
    color: #89969E; background: #F4F7F9; }
QDialog QCheckBox:disabled, QDialog QRadioButton:disabled { color: #89969E; }
QDialog QTextEdit, QDialog QPlainTextEdit { background: white; color: #1B2933;
    border: 1px solid #BCC9D3; border-radius: 5px; }
QDialog QLineEdit:focus, QDialog QComboBox:focus, QDialog QAbstractSpinBox:focus {
    border: 2px solid #08A9B5; }
QDialog QAbstractItemView { background: white; color: #1B2933;
    border: 1px solid #D5DEE5; selection-background-color: #087E91;
    selection-color: white; }
QDialog QGroupBox { color: #0B326C; background: white; border: 1px solid #D5DEE5;
    border-radius: 5px; margin-top: 10px; padding-top: 8px; }
QDialog QGroupBox::title { subcontrol-origin: margin; left: 8px; font-weight: 700; }
QDialog QScrollArea { background: transparent; border: 0; }
QDialog QTabWidget::pane { background: white; border: 1px solid #D5DEE5; }
"""


# Exact base-dialog selectors cover ad-hoc app forms, while typed prompt selectors
# cover confirmations/input. System QFileDialog/QColorDialog/QFontDialog are excluded.
APPLICATION_DIALOG_STYLE = "\n".join(
    DIALOG_STYLE.replace("QDialog", selector)
    for selector in (".QDialog", "QMessageBox", "QInputDialog")
)


def apply_dialog_theme(dialog: QDialog) -> None:
    """Install the shared base once, preserving the dialog's explicit local selectors.

    Args:
        dialog: GUI-thread owned Qt dialog; no parent/window lookup is performed.

    Returns:
        None. Prefix detection makes explicit styling idempotent. Repeated calls
        preserve the same stylesheet and existing control ownership.
    """
    if dialog.property(
        "ergotoolsDialogThemeApplying"
    ) is True or dialog.styleSheet().startswith(DIALOG_STYLE):
        return
    dialog.setProperty("ergotoolsDialogTheme", True)
    dialog.setProperty("ergotoolsDialogThemeApplying", True)
    try:
        dialog.setStyleSheet(DIALOG_STYLE + dialog.styleSheet())
    finally:
        dialog.setProperty("ergotoolsDialogThemeApplying", False)


def install_dialog_theme(app: QApplication) -> None:
    """Install scoped styling for owned forms and ordinary application prompts.

    Args:
        app: Existing GUI-thread application. Qt owns stylesheet propagation; no event
            filters or window searches are installed.

    Returns:
        None. Repeated construction is idempotent. Ordinary app prompts use the common
        theme; system file/color/font selectors keep platform-native/default appearance.
    """
    if app.property("ergotoolsDialogThemeInstalled") is True:
        return
    app.setStyleSheet(app.styleSheet() + APPLICATION_DIALOG_STYLE)
    app.setProperty("ergotoolsDialogThemeInstalled", True)
