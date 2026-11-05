"""Owned ErgoTools and JROT attribution forms with no project or global lookup.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme
from ergotools.presentation.desktop.workflow_action_style import set_action_icon

# Application developer and original-tool attribution; funding removed by the owner.
CREDITS = (
    "<b>Developed by:</b><br><br>Dr. Mauricio Henriquez-Schott & Dr. Ivan "
    "Nail-Ulloa<br><br>Based on the Fatigue Failure tools from Auburn University, "
    "led by Sean Gallagher, Richard Sesek, Mark Schall, Dania Bani Hani "
    "and Rong Huangfu.<br><br>Original tools can be found here:<br>"
    "<a href='https://eng.auburn.edu/occupational-safety-ergonomics-injury-"
    "prevention/research/research-2.html'>https://eng.auburn.edu/occupational-"
    "safety-ergonomics-injury-prevention/research/research-2.html</a>"
)

# Spanish prose retains the same developer names, scientific attribution and link.
SPANISH_CREDITS = (
    "<b>Desarrollado por:</b><br><br>Dr. Mauricio Henriquez-Schott & Dr. Ivan "
    "Nail-Ulloa<br><br>Basado en las herramientas Fatigue Failure "
    "de Auburn University, "
    "dirigidas por Sean Gallagher, Richard Sesek, Mark Schall, Dania Bani Hani "
    "y Rong Huangfu.<br><br>Las herramientas originales se encuentran aquí:<br>"
    "<a href='https://eng.auburn.edu/occupational-safety-ergonomics-injury-"
    "prevention/research/research-2.html'>https://eng.auburn.edu/occupational-"
    "safety-ergonomics-injury-prevention/research/research-2.html</a>"
)

# Exact contributor order/initials from the 2025 showAuthorsDialogJrot source.
JROT_CONTRIBUTORS = (
    "Henriquez-Schott, M.",
    "Nail-Ulloa, I.",
    "Kotowski, S.E.",
    "Gallagher, S.",
    "Jorgensen, M.",
    "Davis, K.G.",
)


class AuthorsDialog(QDialog):
    """Show developer/tool attribution with the original logo and dimensions."""

    def __init__(
        self, language: Language, logo_data: bytes, *, parent: QWidget
    ) -> None:
        """Create a fresh owned form; repeated opens never reuse an installed layout.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            logo_data: Complete packaged logo bytes decoded by Qt before display.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.

        Raises:
            ValueError: The packaged authors logo cannot be decoded.
        """
        super().__init__(parent)
        self.setWindowTitle("Autores" if language is Language.SPANISH else "Authors")
        self.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(self)
        # Localize prose only: keep the original attribution, link and logo.
        self.credits = QLabel(
            SPANISH_CREDITS if language is Language.SPANISH else CREDITS
        )
        self.credits.setWordWrap(True)
        self.credits.setTextFormat(Qt.TextFormat.RichText)
        self.credits.setOpenExternalLinks(True)
        layout.addWidget(self.credits)
        logo = QPixmap()
        if not logo.loadFromData(logo_data):
            raise ValueError("The packaged authors logo cannot be decoded.")
        self.logo = QLabel()
        self.logo.setPixmap(logo.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo)
        self.setFixedSize(600, 700)


class JrotAuthorsDialog(QDialog):
    """Present historical JROT research credits independently of project state."""

    def __init__(
        self, language: Language, icons: Mapping[str, QIcon], *, parent: QWidget
    ) -> None:
        """Create a fresh localized research attribution dialog using packaged icons.

        Args:
            language: Owned UI language; contributor initials/order remain unchanged.
            icons: Packaged JROT and Close action icons from the application host.
            parent: Qt owner; no workspace, repository or pending editor is inspected.

        Returns:
            None; closing the modal accepts no input and performs no project write.
        """
        super().__init__(parent)
        spanish = language is Language.SPANISH
        self.setWindowTitle("Acerca de JROT" if spanish else "About JROT")
        apply_dialog_theme(self)
        self.resize(540, 360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(14)
        heading = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(icons.get("jrot", QIcon()).pixmap(44, 44))
        heading.addWidget(icon)
        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size:22px;font-weight:700;color:#0B326C;")
        heading.addWidget(title, 1)
        layout.addLayout(heading)
        caption = (
            "Colaboradores de la investigación sobre optimización de rotación laboral:"
            if spanish
            else "Research contributors to Job Rotation Optimization:"
        )
        self.credits = QLabel(
            "<b>" + caption + "</b><br><br>" + "<br>".join(JROT_CONTRIBUTORS)
        )
        self.credits.setTextFormat(Qt.TextFormat.RichText)
        self.credits.setWordWrap(True)
        layout.addWidget(self.credits)
        explanation = QLabel(
            "Basado en investigaciones que incluyen evaluaciones integrales de la "
            "rotación laboral como intervención ergonómica administrativa."
            if spanish
            else "Based on research involving comprehensive evaluations "
            "of job rotation "
            "as an administrative ergonomic intervention."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        layout.addStretch(1)
        actions = QHBoxLayout()
        actions.addStretch(1)
        close = QPushButton("Cerrar" if spanish else "Close")
        set_action_icon(close, icons.get("close", QIcon()))
        close.setToolTip(
            "Cerrar los créditos de JROT." if spanish else "Close JROT credits."
        )
        close.clicked.connect(self.reject)
        actions.addWidget(close)
        layout.addLayout(actions)
