"""Launch packaged current or historical help through Qt platform services.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from pathlib import Path

from PyQt5.QtCore import QIODevice, QSaveFile, QStandardPaths, QUrl
from PyQt5.QtGui import QDesktopServices

from ergotools.domain.language import Language


def open_user_guide(data: bytes, *, language: Language | None = None) -> None:
    """Publish a guide atomically in a durable cache and request its default viewer.

    The viewer may consume the file after this call returns, so a temporary-file context
    would delete it too soon. Qt owns platform dispatch; no shell command or
    platform-specific executable is required. The cache contains no project data.

    Args:
        data: Complete packaged guide bytes; viewer dispatch uses an owned durable
            cache.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        None.

    Raises:
        OSError: If caching or the platform document-opening request fails.
    """
    cache = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    if not cache:
        raise OSError("No writable document cache is available.")
    filename = (
        "reference_manual.pdf"
        if language is None
        else {
            Language.ENGLISH: "user_guide_en.html",
            Language.SPANISH: "user_guide_es.html",
        }[language]
    )
    destination = Path(cache) / "ergotools_manual" / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = QSaveFile(str(destination))
    if not output.open(QIODevice.OpenModeFlag.WriteOnly):
        raise OSError("The user guide cache cannot be opened.")
    if output.write(data) != len(data):
        output.cancelWriting()
        raise OSError("The user guide cache could not be written completely.")
    if not output.commit():
        raise OSError("The user guide cache could not be published.")
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(destination))):
        raise OSError("The platform did not accept the user guide opening request.")
