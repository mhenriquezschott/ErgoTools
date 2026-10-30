"""Project-caption fitting and preservation of the complete main toolbar.

Test layer. Exercise native text layout at realistic/extreme widths and the actual
integrated header. Captions must preserve branding, source text and action access.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from PyQt5.QtGui import QFont
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QLabel

from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.project_caption import ProjectCaption
from tests.test_main_navigation import window as navigation_fixture

# Retain native Qt lifetime while source-free caption widgets are exercised.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def header_window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Reuse the private integrated navigation fixture without another UI harness.

    Args:
        tmp_path: Disposable project and preference directory.

    Yields:
        Native integrated Main with owned cleanup supplied by the existing fixture.
    """
    yield from navigation_fixture.__wrapped__(tmp_path)


@pytest.mark.parametrize("width", (180, 330, 655, 900))
@pytest.mark.parametrize(
    "title",
    ("Workflow", "Comparative Individual and Job Risk Test", "x" * 900 + ".ergprj"),
)
def test_caption_fits_two_lines_and_keeps_full_value(width: int, title: str) -> None:
    """Normal captions wrap before shrinking; extreme names retain their full tooltip.

    Args:
        width: Available brand-column width in pixels, independent of content length.
        title: Short, typical long and extreme project/filename-like metadata.

    Returns:
        None; complete source text remains available even when paint uses an ellipsis.
    """
    label = ProjectCaption()
    font = QFont()
    font.setPixelSize(16)
    font.setBold(True)
    label.setFont(font)
    label.resize(width, 54)
    caption = "Current Project: " + title + "  •  Loaded  •  Modified"
    try:
        hint = label.sizeHint()
        label.setText(caption)
        fit = label.presentation()
        assert 1 <= fit.lines <= 2
        assert 12 <= fit.font_pixels <= 16
        assert label.text() == label.toolTip() == caption
        assert label.sizeHint() == hint
        if fit.elided:
            assert "…" in fit.text and fit.text.endswith("Modified")
        else:
            assert fit.text.replace("\u2028", "  •  ") == caption
        if width >= 655 and len(title) < 100:
            assert fit.font_pixels == 16 and not fit.elided
    finally:
        label.close()


@pytest.mark.parametrize("width", (1550, 1660))
def test_modified_caption_never_hides_jobs_or_moves_brand(
    header_window: LifftWindow, width: int
) -> None:
    """Loaded-to-modified transitions cannot take width from any toolbar action.

    Args:
        header_window: Private integrated project and native Main fixture.
        width: Existing minimum/default-size header allocation.

    Returns:
        None; full action access and fixed ErgoTools branding survive extreme names.
    """
    window = header_window
    window.resize(width, 1015)
    window.show()
    _APP.processEvents()
    nav = window.main_navigation
    assert nav is not None
    brand = nav.findChild(QLabel, "brandName")
    assert brand is not None
    origin, height, pixels = brand.pos(), brand.height(), brand.font().pixelSize()
    toolbar_width = nav.toolbar.width()
    for title in (
        "ErgoTools Comparative Individual and Job Risk Test",
        "Nombre de proyecto largo para la comparación de riesgos "
        "individuales y de trabajos",
        "very_long_filename_" * 70 + ".ergprj",
    ):
        nav.update_state(
            nav._catalog,
            nav._current_worker,
            title,
            window.presenter.system,
            window.language,
        )
        nav.project_label.setText(nav.project_label.text() + "  •  Modified")
        _APP.processEvents()
        QTest.qWait(10)
        assert brand.pos() == origin and brand.height() == height
        assert brand.font().pixelSize() == pixels == 36
        assert window.width() == width
        assert nav.toolbar.width() == toolbar_width
        for key in (
            "undo",
            "redo",
            "new",
            "open",
            "save",
            "plot",
            "jrot",
            "organization",
            "jobs",
        ):
            button = nav.toolbar.widgetForAction(nav.toolbar_actions[key])
            assert button is not None and button.isVisible()
            assert nav.toolbar.rect().contains(button.geometry())
        assert nav.project_label.presentation().lines <= 2
