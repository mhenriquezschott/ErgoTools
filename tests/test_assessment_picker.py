"""Assessment selection retains readable selected text and exact choice identity.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox, QInputDialog

from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window
from tools.capture_desktop import render_widget


def test_selected_assessment_is_visible_and_returns_exact_caption(
    window: LifftWindow,
) -> None:
    """The native selected row has both branded background and readable white ink.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    choices = [
        "LiFFT · Worker A · Plant/Section/Line/ST01/1 · v1 · #1",
        "ST · Worker B · Plant/Section/Line/ST02/2 · v2 · #2",
    ]
    failures: list[BaseException] = []

    def inspect() -> None:
        """Inspect the native selected popup row for reference teal background.

        Inspect the native selected popup row for reference teal background and readable
        white ink, accept the second caption, and return callback failures to the
        enclosing test.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        try:
            assert isinstance(dialog, QInputDialog)
            combo = dialog.findChild(QComboBox)
            assert combo is not None
            combo.setCurrentIndex(1)
            combo.showPopup()
            QApplication.processEvents()
            QTest.qWait(30)
            view = combo.view()
            assert view is not None
            index = view.model().index(1, 0)
            rect = view.visualRect(index)
            viewport = view.viewport()
            assert viewport is not None and viewport.rect().contains(rect)
            image = render_widget(viewport).copy(rect)
            teal = white = 0
            for y in range(image.height()):
                for x in range(image.width()):
                    color = image.pixelColor(x, y)
                    teal += color.name() == "#087e91"
                    white += color.name() == "#ffffff"
            assert teal > 20 and white > 3, (teal, white)
            combo.hidePopup()
            dialog.accept()
        except BaseException as error:
            failures.append(error)
            if dialog is not None:
                dialog.reject()

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(inspect)
    timer.start(0)
    selected, accepted = window.choose_item("Open", "Select assessment", choices)
    timer.stop()
    assert not failures, failures
    assert accepted and selected == choices[1]
