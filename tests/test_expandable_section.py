"""Disclosure motion changes geometry only, including rapid reversals and teardown."""

from PyQt5.QtCore import QAbstractAnimation
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from ergotools.presentation.desktop.expandable_section import ExpandableSection

# Retain a single native application for widget/animation lifetime verification.
_APP = QApplication.instance() or QApplication([])


def test_reveal_reversal_and_immediate_projection_keep_content() -> None:
    """User motion has intermediate heights; load projection settles immediately.

    Args:
        None.

    Returns:
        None; content identity/text survive reveal, reversal and collapse.
    """
    host = QWidget()
    layout = QVBoxLayout(host)
    content = QLabel("Existing assessment controls")
    content.setFixedHeight(90)
    section = ExpandableSection(content)
    layout.addWidget(section)
    host.show()
    _APP.processEvents()
    try:
        assert section.isHidden()
        section.set_expanded(True, animate=True)
        QTest.qWait(65)
        assert 0 < section.height() < 90
        section.set_expanded(False, animate=True)
        assert section.animation.state() == QAbstractAnimation.State.Running
        section.set_expanded(True, animate=True)
        QTest.qWait(230)
        assert section.height() == 90 and section.isVisible()
        assert (
            section.content is content
            and content.text() == "Existing assessment controls"
        )
        section.set_expanded(False, animate=False)
        assert section.isHidden() and section.maximumHeight() == 0
        section.set_expanded(True, animate=False)
        assert (
            section.isVisible()
            and section.animation.state() == QAbstractAnimation.State.Stopped
        )
    finally:
        host.close()
        host.deleteLater()
        _APP.processEvents()
