"""Original Help commands preserve pending assessment state and use package assets.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.settings import Language
from ergotools.infrastructure.resources import read_asset
from ergotools.presentation.desktop.authors_dialog import AuthorsDialog
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.manual_launcher import open_user_guide
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("index", [0, 1, 2])
def test_help_and_repeated_about_preserve_pending_inputs(
    window: LifftWindow, index: int, tmp_path: Path, language: Language
) -> None:
    """Menu/toolbar Help and About never parse or implicitly save invalid fields.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    window.language = language
    window.translate()
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    active = workspace.active
    before = active.state
    settings = window._settings_store.load()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    opened = []

    def accept_url(url: QUrl) -> bool:
        """Verify the platform-launch URL resolves.

        Verify the platform-launch URL resolves to the exact packaged localized guide
        bytes and record one successful launch.

        Args:
            url: Qt local-file URL supplied to the patched platform guide launcher.

        Returns:
            True after verifying and recording the exact packaged local guide URL.
        """
        path = Path(url.toLocalFile())
        assert path.read_bytes() == read_asset(
            f"documents/user_guide_{language.value}.html"
        )
        opened.append(path)
        return True

    with (
        patch(
            "ergotools.presentation.desktop.manual_launcher.QStandardPaths.writableLocation",
            return_value=str(tmp_path),
        ),
        patch(
            "ergotools.presentation.desktop.manual_launcher.QDesktopServices.openUrl",
            side_effect=accept_url,
        ),
    ):
        window._assessment_menu.user_guide.trigger()
        window.main_navigation.toolbar_actions["help"].trigger()
    assert len(opened) == 2 and opened[0].exists()

    def close_authors() -> None:
        """Check real Authors attribution and decoded logo, then reject the modal.

        Check real Authors attribution and decoded logo, then reject the modal while
        retaining pending assessment input.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, AuthorsDialog)
        assert not dialog.logo.pixmap().isNull()
        assert "Mauricio Henriquez-Schott" in dialog.credits.text()
        dialog.reject()

    for _ in range(2):
        QTimer.singleShot(0, close_authors)
        window._assessment_menu.about.trigger()
    assert workspace.active is active and active.state is before
    assert field.text() == "bad" and panel.pending
    assert window._settings_store.load() == settings


@pytest.mark.parametrize("failure", ["cache", "viewer"])
def test_guide_failure_is_owned_and_preserves_input(
    window: LifftWindow, tmp_path: Path, failure: str
) -> None:
    """Missing cache or failed platform launch produces an owned localized error.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        failure: Named fault-injection stage/outcome used to verify rollback and
            retained ownership.

    Returns:
        None.
    """
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    active = window.presenter.workspace.active
    before = active.state
    window.language = Language.SPANISH
    window.translate()
    with (
        patch(
            "ergotools.presentation.desktop.manual_launcher.QStandardPaths.writableLocation",
            return_value="" if failure == "cache" else str(tmp_path),
        ),
        patch(
            "ergotools.presentation.desktop.manual_launcher.QDesktopServices.openUrl",
            return_value=False,
        ),
        patch.object(QMessageBox, "critical") as message,
    ):
        window._assessment_menu.user_guide.trigger()
    assert message.call_args.args[0] is window
    assert message.call_args.args[1] == "Ayuda no disponible"
    assert active.state is before and field.text() == "bad"


def test_manual_cache_write_failure_does_not_launch(tmp_path: Path) -> None:
    """An incomplete atomic publication never launches an incomplete PDF.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        patch(
            "ergotools.presentation.desktop.manual_launcher.QStandardPaths.writableLocation",
            return_value=str(tmp_path),
        ),
        patch(
            "ergotools.presentation.desktop.manual_launcher.QSaveFile.write",
            return_value=-1,
        ),
        patch(
            "ergotools.presentation.desktop.manual_launcher.QDesktopServices.openUrl"
        ) as launch,
        pytest.raises(OSError, match="written completely"),
    ):
        open_user_guide(read_asset("documents/reference_manual.pdf"))
    launch.assert_not_called()
    assert not (tmp_path / "ergotools_manual/reference_manual.pdf").exists()


@pytest.mark.parametrize("language", list(Language))
def test_authors_localization_preserves_attribution_and_link(
    window: LifftWindow, language: Language
) -> None:
    """Translate credit prose without changing attribution or the external target.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    from html.parser import HTMLParser

    class Links(HTMLParser):
        """Collect external hyperlink targets from the actual credit HTML."""

        def __init__(self) -> None:
            """Initialize the HTML parser with an empty owned hyperlink-target list.

            Args:
                None.

            Returns:
                None.
            """
            super().__init__()
            self.targets: list[str] = []

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            """Collect nonempty href values only.

            Collect nonempty href values only from anchor tags in the packaged credit
            HTML.

            Args:
                tag: HTML tag delivered by HTMLParser while checking packaged
                    credit/guide content.
                attrs: HTML attributes supplied by HTMLParser; link targets/anchor IDs
                    are inspected literally.

            Returns:
                None.
            """
            if tag == "a":
                self.targets.extend(
                    value for name, value in attrs if name == "href" and value
                )

    dialog = AuthorsDialog(
        language, read_asset("images/ergotools_main_logo.png"), parent=window
    )
    text = dialog.credits.text()
    for name in (
        "Mauricio Henriquez-Schott",
        "Ivan Nail-Ulloa",
        "INES 52 R+D",
        "ANID",
        "Auburn University",
        "Sean Gallagher",
        "Richard Sesek",
        "Mark Schall",
        "Dania Bani Hani",
        "Rong Huangfu",
    ):
        assert name in text
    parser = Links()
    parser.feed(text)
    assert parser.targets == [
        "https://eng.auburn.edu/occupational-safety-ergonomics-injury-prevention/"
        "research/research-2.html"
    ]
    assert ("Desarrollado por:" in text) is (language is Language.SPANISH)
    assert ("Developed by:" in text) is (language is Language.ENGLISH)
    assert dialog.credits.openExternalLinks()
    dialog.close()


@pytest.mark.parametrize("language", list(Language))
def test_current_guide_is_self_contained_and_linked(language: Language) -> None:
    """Both packaged guides expose all current workflow sections offline.

    Args:
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    from html.parser import HTMLParser

    class Guide(HTMLParser):
        """Inspect packaged guide IDs/links and reject script.

        Inspect packaged guide IDs/links and reject script, iframe or image
        dependencies.
        """

        def __init__(self) -> None:
            """Initialize independent owned anchor-ID and link sets.

            Initialize independent owned anchor-ID and link sets for one packaged guide.

            Args:
                None.

            Returns:
                None.
            """
            super().__init__()
            self.ids: set[str] = set()
            self.links: set[str] = set()

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            """Collect literal anchor IDs/hrefs.

            Collect literal anchor IDs/hrefs and assert the offline guide contains no
            script, iframe or image tags.

            Args:
                tag: HTML tag delivered by HTMLParser while checking packaged
                    credit/guide content.
                attrs: HTML attributes supplied by HTMLParser; link targets/anchor IDs
                    are inspected literally.

            Returns:
                None.
            """
            for name, value in attrs:
                if name == "id" and value:
                    self.ids.add(value)
                if name == "href" and value:
                    self.links.add(value)
            assert tag not in ("script", "iframe", "img")

    data = read_asset(f"documents/user_guide_{language.value}.html").decode()
    parser = Guide()
    parser.feed(data)
    assert parser.ids == {
        "start",
        "projects",
        "management",
        "assessments",
        "units",
        "plot",
        "jrot",
        "transfer",
        "recovery",
    }
    assert parser.links and all(
        link.startswith("#") and link[1:] in parser.ids for link in parser.links
    )
    assert "CBC" in data and "HiGHS" in data
