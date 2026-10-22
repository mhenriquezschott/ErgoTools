"""Owned original Set Number of Tasks form, with localized reference controls.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


class TaskCountDialog(QDialog):
    """Collect the active tool's row count; source changes belong to its presenter."""

    def __init__(self, language: Language, *, parent: QWidget) -> None:
        """Port openNumTasksDialog without database access or global window lookup.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        super().__init__(parent)
        apply_dialog_theme(self)
        spanish = language is Language.SPANISH
        self.setWindowTitle(
            "Establecer número de tareas" if spanish else "Set Number of Tasks"
        )
        layout = QVBoxLayout(self)
        label = QLabel("N° de tareas:" if spanish else "N° of Tasks:")
        font = QFont()
        font.setBold(True)
        label.setFont(font)
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(10)  # Preserve the reference dialog's initial value.
        layout.addWidget(label)
        layout.addWidget(self.count)
        buttons = QHBoxLayout()
        self.set_button = QPushButton("Establecer tareas" if spanish else "Set Tasks")
        self.cancel_button = QPushButton("Cancelar" if spanish else "Cancel")
        buttons.addWidget(self.set_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)
        self.set_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
