"""Guided optional upgrade dialog in the desktop presentation layer.

Explains source preservation, external CLI use and explicit first Save in EN/ES.
Executes only the caller's owned conversion callback after Migrate; it neither opens
repositories nor chooses permanent paths. Styling is inherited from the integrated
desktop. Technical failures remain selectable text for diagnosis.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.presentation.desktop.text import desktop_text

# Conversion errors are logged locally; literal tool details are also shown for
# diagnosing missing tools or unsupported inputs without discarding the project.
_LOG = logging.getLogger(__name__)


class ProjectMigrationDialog(QDialog):
    """Collect consent and report a bounded external migration attempt."""

    def __init__(
        self,
        language: Language,
        command: str,
        migrate: Callable[[], bool],
        *,
        parent: QWidget,
    ) -> None:
        """Build localized controls without running the utility.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            command: Copyable external migration command with a separate output
                destination.
            migrate: Consented external conversion callback; False cancels activation.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        super().__init__(parent)
        self.language = language
        self._migrate = migrate
        self.setWindowTitle(desktop_text("migration_title", language))
        self.setMinimumWidth(600)
        self.resize(680, 430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.explanation = QLabel(desktop_text("migration_explanation", language))
        self.explanation.setWordWrap(True)
        layout.addWidget(self.explanation)
        label = QLabel(desktop_text("migration_cli", language))
        label.setWordWrap(True)
        layout.addWidget(label)
        self.command = QPlainTextEdit(command)
        self.command.setReadOnly(True)
        self.command.setStyleSheet(
            "QPlainTextEdit { background: white; color: #1B2933; "
            "border: 1px solid #BCC9D3; border-radius: 5px; padding: 8px; }"
        )
        self.command.setToolTip(desktop_text("migration_cli_tip", language))
        self.command.setAccessibleName(desktop_text("migration_cli", language))
        layout.addWidget(self.command)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setTextFormat(Qt.TextFormat.PlainText)
        self.error.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.error.hide()
        layout.addWidget(self.error)
        self.buttons = QDialogButtonBox()
        self.migrate_button = self.buttons.addButton(
            desktop_text("migration_action", language), QDialogButtonBox.AcceptRole
        )
        self.cancel_button = self.buttons.addButton(
            desktop_text("cancel", language), QDialogButtonBox.RejectRole
        )
        assert self.migrate_button is not None and self.cancel_button is not None
        self.migrate_button.setObjectName("calculateButton")
        self.migrate_button.setToolTip(desktop_text("migration_action_tip", language))
        self.cancel_button.setToolTip(desktop_text("migration_cancel_tip", language))
        self.buttons.accepted.connect(self.attempt_migration)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def attempt_migration(self) -> None:
        """Run the consented callback once; keep failures visible until Cancel.

        Args:
            None.

        Returns:
            None.
        """
        assert self.migrate_button is not None
        self.migrate_button.setEnabled(False)
        try:
            completed = self._migrate()
        except (OSError, ValueError) as error:
            _LOG.exception("External project migration failed")
            self.error.setText(
                desktop_text("migration_failed", self.language) + "\n" + str(error)
            )
            self.error.show()
        else:
            if completed:
                self.accept()
            else:
                self.reject()
