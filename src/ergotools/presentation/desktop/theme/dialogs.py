"""Theme ErgoTools-owned forms/prompts while preserving system chooser defaults.

Presentation layer. A scoped owned-window palette and stylesheet supply common colors,
typography and controls. Existing per-dialog styles retain Qt local priority.
Ordinary prompts share the theme; file/color/font choosers retain platform defaults.
Window-manager decorations remain owned by the desktop. No project, preference
or filesystem operations occur here.
"""

from functools import cache

from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFontDialog,
    QInputDialog,
    QMessageBox,
    QWidget,
)

# Explicit roles for light application panels; never installed on QApplication or
# native file/color/font choosers. Disabled text remains visibly distinct.
_OWNED_PALETTE_COLORS = (
    (QPalette.ColorRole.Window, "#F4F7F9"),
    (QPalette.ColorRole.Base, "#FFFFFF"),
    (QPalette.ColorRole.AlternateBase, "#F5F8FA"),
    (QPalette.ColorRole.Button, "#FFFFFF"),
    (QPalette.ColorRole.WindowText, "#1B2933"),
    (QPalette.ColorRole.Text, "#1B2933"),
    (QPalette.ColorRole.ButtonText, "#0B326C"),
    (QPalette.ColorRole.PlaceholderText, "#6B7785"),
    (QPalette.ColorRole.Highlight, "#087E91"),
    (QPalette.ColorRole.HighlightedText, "#FFFFFF"),
    (QPalette.ColorRole.ToolTipBase, "#1B2933"),
    (QPalette.ColorRole.ToolTipText, "#FFFFFF"),
    (QPalette.ColorRole.Mid, "#BCC9D3"),
    (QPalette.ColorRole.Dark, "#9AA9B5"),
    (QPalette.ColorRole.Light, "#FFFFFF"),
)


def apply_owned_window_palette(widget: QWidget) -> None:
    """Resolve light-panel foregrounds independently of the desktop dark palette.

    Args:
        widget: Control inside an application-owned form or ordinary app prompt.

    Returns:
        None; child controls inherit explicit roles, while widget-specific result
        colors/styles keep priority. QApplication and native chooser palettes
        stay intact.
    """
    palette = owned_light_palette()
    if palette != widget.palette():
        widget.setPalette(palette)


@cache
def owned_light_palette() -> QPalette:
    """Build shared light defaults once; Qt copies them for individual controls.

    Args:
        None; called only after the GUI application exists.

    Returns:
        Read-only palette template. Do not mutate the returned object; widget palette
        setters copy its implicitly shared data. Explicit local styles retain priority.
    """
    palette = QPalette()
    for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
        for role, color in _OWNED_PALETTE_COLORS:
            palette.setColor(group, role, QColor(color))
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, QColor("#89969E"))
    return palette


class OwnedWindowPalette(QObject):
    """Correct owned-form colors before painting and OS theme changes."""

    def close(self) -> None:
        """Detach before Qt destroys native windows during application shutdown.

        Args:
            None.

        Returns:
            None; the application retains ownership until QObject cleanup.
        """
        app = self.parent()
        if isinstance(app, QApplication):
            app.removeEventFilter(self)
            app.setProperty("ergotoolsOwnedPaletteInstalled", False)

    def eventFilter(  # noqa: N802 -- Qt override
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        """Apply owned-window colors without intercepting events or native choosers.

        Args:
            watched: Qt object receiving its normal event.
            event: Polish/show/application-palette notification, or an unrelated event.

        Returns:
            False; Qt always continues normal processing. No descendant searches,
            file operations or native-style replacement occur.
        """
        if (
            event is not None
            and event.type()
            in (
                QEvent.Type.Polish,
                QEvent.Type.Show,
                QEvent.Type.ApplicationPaletteChange,
            )
            and isinstance(watched, QWidget)
            and (watched.isWindow() or event.type() == QEvent.Type.Polish)
            and not isinstance(
                watched.window(), (QFileDialog, QColorDialog, QFontDialog)
            )
            and (
                type(watched.window()).__module__.startswith(
                    "ergotools.presentation.desktop."
                )
                or type(watched.window()) is QDialog
                or isinstance(watched.window(), (QMessageBox, QInputDialog))
            )
        ):
            # Child defaults precede explicit stylesheet result/selection colors.
            apply_owned_window_palette(watched)
        return False


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
        app: Existing GUI-thread application. Qt owns stylesheet propagation; the
            parent-owned filter observes polish/show events without descendant searches.

    Returns:
        None. Repeated construction is idempotent. Ordinary app prompts use the common
        theme; system file/color/font selectors keep platform-native/default appearance.
    """
    if app.property("ergotoolsOwnedPaletteInstalled") is not True:
        palette_filter = OwnedWindowPalette(app)
        app.installEventFilter(palette_filter)
        app.aboutToQuit.connect(palette_filter.close)
        app.setProperty("ergotoolsOwnedPaletteInstalled", True)
    if app.property("ergotoolsDialogThemeInstalled") is True:
        return
    app.setStyleSheet(app.styleSheet() + APPLICATION_DIALOG_STYLE)
    app.setProperty("ergotoolsDialogThemeInstalled", True)
