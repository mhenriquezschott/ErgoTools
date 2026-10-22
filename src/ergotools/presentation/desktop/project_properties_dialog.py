"""Read-only native project metadata in the current ErgoTools visual style.

Presentation layer: display supplied metadata/path only. Do not read SQLite, infer
creation timestamps, expose obsolete sidecar folders or modify project preferences.
Owned Qt fields support copying full paths and reading long descriptions without
expanding the dialog beyond its available screen.
"""

from collections.abc import Mapping
from pathlib import Path

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.presentation.desktop.style import WORKSPACE_STYLE

# Stable field identities and bilingual captions for the native single-file project.
_FIELDS = (
    ("name", "Project name", "Nombre del proyecto"),
    ("file", "Project file", "Archivo del proyecto"),
    ("location", "Location", "Ubicación"),
    ("created", "Created", "Creado"),
    ("language", "Project language", "Idioma del proyecto"),
    ("units", "Measurement system", "Sistema de medidas"),
)


class ProjectPropertiesDialog(QDialog):
    """Display applicable native details with copyable values and a bounded description.

    Attributes:
        fields: Read-only value controls indexed by stable metadata field identity.
        description: Read-only, scrollable plain text; markup is never interpreted.
        close_button: Standard themed Close action owned by this modal.
    """

    def __init__(
        self,
        metadata: ProjectMetadata,
        location: str,
        language: Language,
        *,
        parent: QWidget,
        icons: Mapping[str, QIcon] | None = None,
    ) -> None:
        """Build an owned metadata dialog without querying or changing the project.

        Args:
            metadata: Saved native project metadata; absent optional values stay
                explicitly unrecorded rather than being inferred from the filesystem.
            location: Full native project path, independent of the current directory.
            language: Interface language; saved names/descriptions remain literal.
            parent: Required Qt lifetime owner.
            icons: Processed application assets for the title and Close action;
                None supports isolated presentation tests without artwork.

        Returns:
            None; initial size is resizable, long values remain copyable and long
            descriptions scroll inside their field. No obsolete database/image/data
            sidecar folders or duplicate database filename/path are displayed.
        """
        super().__init__(parent)
        spanish = language is Language.SPANISH
        title = "Propiedades del proyecto" if spanish else "Project Properties"
        self.setWindowTitle(title)
        self.setMinimumSize(620, 460)
        self.resize(700, 500)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(
            WORKSPACE_STYLE + "QDialog { background: #F4F7F9; color: #1B2933; }"
            "QFrame#propertiesCard { background: white; border: 1px solid #D5DEE5;"
            " border-radius: 6px; }"
            "QLineEdit:read-only { background: #F4F7F9; color: #0B326C; }"
            "QPlainTextEdit { background: white; color: #1B2933;"
            " border: 1px solid #BCC9D3; border-radius: 5px; padding: 6px; }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)
        heading = QHBoxLayout()
        heading.setSpacing(12)
        if icons is not None:
            image = QLabel()
            image.setObjectName("propertiesIcon")
            image.setFixedSize(32, 32)
            image.setPixmap(icons["view"].pixmap(QSize(32, 32)))
            heading.addWidget(image)
        label = QLabel(title)
        label.setObjectName("propertiesHeading")
        label.setStyleSheet("color: #0B326C; font-size: 20px; font-weight: 700;")
        heading.addWidget(label, 1)
        root.addLayout(heading)
        card = QFrame()
        card.setObjectName("propertiesCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)
        missing = "Sin registro" if spanish else "Not recorded"
        metric = metadata.default_units is MeasurementSystem.METRIC
        values = {
            "name": metadata.title,
            "file": Path(location).name,
            "location": str(Path(location)),
            "created": metadata.created_at.isoformat(sep=" ")
            if metadata.created_at
            else missing,
            "language": (
                ("Español" if spanish else "Spanish")
                if metadata.language is Language.SPANISH
                else ("Inglés" if spanish else "English")
            )
            if metadata.language is not None
            else missing,
            "units": ("Métrico" if spanish else "Metric") if metric else "Imperial",
        }
        self.fields: dict[str, QLineEdit] = {}
        for key, english, translated in _FIELDS:
            field = QLineEdit(values[key])
            field.setReadOnly(True)
            field.setCursorPosition(0)
            field.setToolTip(values[key])
            caption = translated if spanish else english
            field.setAccessibleName(caption)
            field.setAccessibleDescription(values[key])
            self.fields[key] = field
            form.addRow(caption + ":", field)
        card_layout.addLayout(form)
        card_layout.addWidget(QLabel("Descripción:" if spanish else "Description:"))
        self.description = QPlainTextEdit(metadata.description or "")
        self.description.setReadOnly(True)
        self.description.setMinimumHeight(90)
        self.description.setAccessibleName("Descripción" if spanish else "Description")
        card_layout.addWidget(self.description, 1)
        root.addWidget(card, 1)
        footer = QHBoxLayout()
        footer.addStretch()
        self.close_button = QPushButton("Cerrar" if spanish else "Close")
        if icons is not None:
            self.close_button.setIcon(icons["close"])
            self.close_button.setIconSize(QSize(24, 24))
        self.close_button.clicked.connect(self.accept)
        footer.addWidget(self.close_button)
        root.addLayout(footer)
