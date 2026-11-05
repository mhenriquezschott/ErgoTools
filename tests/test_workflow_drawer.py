"""Native drawer sizing keeps localized labels visible without overlaying content.

The test uses only a temporary widget; no project, preferences or solver is involved.
"""

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget

from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.presentation.desktop.workflow_drawer import WorkflowDrawer

# Retain the Qt application until the owned animation and widgets retire.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_expanded_drawer_fits_localized_icons_and_text(language: Language) -> None:
    """The real layout allocates sufficient width for the longest translated step.

    Args:
        language: English/Spanish labels, including a literal ampersand.

    Returns:
        None; selected/hover styling and pinning retain readable button bounds.
    """
    owner = QWidget()
    owner.resize(1000, 500)
    layout = QHBoxLayout(owner)
    drawer = WorkflowDrawer(
        (
            "08  Comparación e informe"
            if language is Language.SPANISH
            else "08  Comparison & report",
        ),
        lambda _index: None,
        language=language,
        icons=(load_icons()["compare_rotation"],),
    )
    layout.addWidget(drawer)
    layout.addWidget(QLabel("Page content"), 1)
    try:
        owner.show()
        drawer.reveal()
        QTest.qWait(260)
        assert drawer.buttons[0].width() >= drawer.buttons[0].sizeHint().width()
        assert drawer.pin.text() == ""
        assert drawer.notch.height() == drawer.panel.height()
        assert drawer.notch.x() >= drawer.panel.x() + drawer.panel.width()
        expanded_notch = drawer.notch.x()
        drawer.pin.setChecked(True)
        drawer.reveal(False)
        QTest.qWait(260)
        assert drawer.buttons[0].width() >= drawer.buttons[0].sizeHint().width()
        drawer.pin.setChecked(False)
        drawer.reveal(False)
        QTest.qWait(260)
        assert drawer.notch.x() < expanded_notch
        assert drawer.width() >= 20
    finally:
        owner.close()
        owner.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
