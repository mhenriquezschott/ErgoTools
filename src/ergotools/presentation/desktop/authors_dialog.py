"""Original owned Authors form with packaged credits/logo and no global lookup.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget

from ergotools.application.settings import Language

# Original English author and funding credit HTML; links are explicit packaged
# application content.
CREDITS = (
    "<b>Developed by:</b><br><br>Dr. Mauricio Henriquez-Schott & Dr. I"
    "van Nail-Ulloa<br><br>Project funded by INES 52 R+D, through the "
    "Office of Research and Innovation of Universidad Austral de Chile"
    ", and the National Agency of Innovation and Development (ANID).<b"
    "r><br>Based on the Fatigue Failure tools from Auburn University, "
    "led by Sean Gallagher, Richard Sesek, Mark Schall, Dania Bani Han"
    "i and Rong Huangfu.<br><br>Original tools can be found here:<br><"
    "a href='https://eng.auburn.edu/occupational-safety-ergonomics-inj"
    "ury-prevention/research/research-2.html'>https://eng.auburn.edu/o"
    "ccupational-safety-ergonomics-injury-prevention/research/research"
    "-2.html</a>"
)


# Spanish author/funding credit HTML matching the original attribution.
SPANISH_CREDITS = (
    "<b>Desarrollado por:</b><br><br>Dr. Mauricio Henriquez-Schott & Dr. Ivan "
    "Nail-Ulloa<br><br>Proyecto financiado por INES 52 R+D, a través de la "
    "Dirección de Investigación e Innovación de la Universidad Austral de Chile "
    "y la Agencia Nacional de Innovación y Desarrollo (ANID).<br><br>"
    "Basado en las herramientas Fatigue Failure de Auburn University, "
    "dirigidas por Sean Gallagher, Richard Sesek, Mark Schall, Dania Bani Hani "
    "y Rong Huangfu.<br><br>Las herramientas originales se encuentran aquí:<br>"
    "<a href='https://eng.auburn.edu/occupational-safety-ergonomics-injury-"
    "prevention/research/research-2.html'>https://eng.auburn.edu/occupational-"
    "safety-ergonomics-injury-prevention/research/research-2.html</a>"
)


class AuthorsDialog(QDialog):
    """Retain reference authors text, logo, dimensions and close interaction."""

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
