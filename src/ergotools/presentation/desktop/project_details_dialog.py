"""Original Name/Description collection, separate from creation and storage.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


class ProjectDetailsDialog(QDialog):
    """Retain the original automatically sized Project Details form and field order."""

    def __init__(
        self,
        language: Language,
        *,
        parent: QWidget,
        name: str = "",
        description: str = "",
    ) -> None:
        """Collect literal text without writing files or accepting assessment edits.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.
            name: Literal project/scheme name or export-name stem; empty by default.
            description: Literal project/scheme description; empty by default.

        Returns:
            None.
        """
        super().__init__(parent)
        apply_dialog_theme(self)
        spanish = language is Language.SPANISH
        self.setWindowTitle("Detalles del proyecto" if spanish else "Project Details")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Nombre:" if spanish else "Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(name)
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Descripción:" if spanish else "Description:"))
        self.description_input = QTextEdit()
        self.description_input.setAcceptRichText(False)
        self.description_input.setPlainText(description)
        layout.addWidget(self.description_input)
        self.button_box = QDialogButtonBox()
        accept = self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        cancel = self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        assert accept is not None and cancel is not None
        accept.setText("Aceptar" if spanish else "OK")
        cancel.setText("Cancelar" if spanish else "Cancel")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
