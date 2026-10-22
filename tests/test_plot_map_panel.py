"""Original map controls: native modal consent and real preview/save regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.settings import Language
from ergotools.bootstrap import load_icons
from ergotools.domain.plot_scope import PlotScope
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.plot_map_panel import PlotMapPanel
from tests.test_plant_layout_persistence import create_project, image_file
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def test_original_map_buttons_preview_save_cancel_failure_and_scope(
    tmp_path: Path,
) -> None:
    """Actual button intent preserves map/project on cancel/error and retries saves.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.ergprj"
    imported = image_file(tmp_path / "map.png")
    with create_project(path, 8) as project:
        panel = PlotMapPanel(
            project.load_hierarchy(),
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
        )
        panel.message = Mock(return_value=int(QMessageBox.Ok))
        panel.choose_image = Mock(return_value=str(imported))
        assert not any(button.isEnabled() for button in panel.buttons.values())
        panel.open_image()
        panel.save_image()
        assert panel.set_scope(PlotScope((("P",),)))
        assert (
            panel.buttons["open"].isEnabled() and not panel.buttons["save"].isEnabled()
        )
        before = path.read_bytes()
        panel.buttons["open"].click()
        image = panel.pending_image
        assert image is not None and panel.canvas.loaded_layout.image == image.data
        assert project.load_plant_image("P") is None and path.read_bytes() == before
        panel.choose_image.return_value = ""
        panel.buttons["open"].click()
        assert panel.pending_image is image
        bad = tmp_path / "bad.png"
        bad.write_bytes(b"bad")
        panel.choose_image.return_value = str(bad)
        panel.buttons["open"].click()
        assert panel.pending_image is image and path.read_bytes() == before
        assert panel.message.call_args.args[2] == QMessageBox.Critical
        panel.confirm_discard = Mock(return_value=False)
        assert not panel.set_scope(PlotScope((("Empty",),)))
        assert panel.scope == PlotScope((("P",),)) and panel.pending_image is image
        assert panel.set_scope(panel.scope)
        panel.confirm_discard.assert_called_once()
        with patch.object(
            project,
            "save_plant_image",
            side_effect=sqlite3.OperationalError("disk failure"),
        ):
            panel.buttons["save"].click()
        assert panel.pending_image is image and panel.buttons["save"].isEnabled()
        assert project.format_version == 8 and path.read_bytes() == before
        panel.buttons["save"].click()
        assert panel.pending_image is None and project.load_plant_image("P") == image
        assert project.format_version == 9 and not panel.buttons["save"].isEnabled()
        panel.choose_image.return_value = str(imported)
        panel.buttons["open"].click()
        panel.confirm_discard.return_value = True
        assert panel.set_scope(PlotScope((("Empty",),)))
        assert panel.pending_image is None and not panel.canvas.scene().items()
        previous = panel.scope
        assert not panel.set_scope(PlotScope((("Missing",),)))
        assert panel.scope == previous
        project.save_plant_image("Empty", image)
        panel.reader = Mock(read=Mock(return_value=b"invalid saved image"))
        assert not panel.set_scope(PlotScope((("P",),)))
        assert panel.scope == previous and panel.pending_image is None
        panel.close()
        panel.deleteLater()


@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
def test_owned_modal_messages_and_discard_consent(
    tmp_path: Path, language: Language
) -> None:
    """Native consent defaults to No; messages retain local language/literal text.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    with create_project(tmp_path / "project.ergprj", 8) as project:
        panel = PlotMapPanel(
            project.load_hierarchy(),
            project,
            project,
            lambda filename: import_plant_image(Path(filename)),
            load_icons(),
            language=language,
        )
        answers = []

        def no() -> None:
            """Assert native No-default consent and localized Yes wording.

            Assert native No-default consent and localized Yes wording before refusing
            image discard.

            Args:
                None.

            Returns:
                None.
            """
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            assert box.defaultButton() is box.button(QMessageBox.No)
            assert box.button(QMessageBox.Yes).text() == (
                "Sí" if language is Language.SPANISH else "Yes"
            )
            answers.append(box.windowTitle())
            box.button(QMessageBox.No).click()

        QTimer.singleShot(0, no)
        assert not panel.confirm_discard()

        def yes() -> None:
            """Accept explicit discard consent through the native Yes button.

            Args:
                None.

            Returns:
                None.
            """
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            box.button(QMessageBox.Yes).click()

        QTimer.singleShot(0, yes)
        assert panel.confirm_discard()

        def error() -> None:
            """Verify literal error markup is plain text.

            Verify literal error markup is plain text, then acknowledge the real owned
            message.

            Args:
                None.

            Returns:
                None.
            """
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            assert (
                box.textFormat() == Qt.PlainText and box.text() == "Literal <b>path</b>"
            )
            box.button(QMessageBox.Ok).click()

        QTimer.singleShot(0, error)
        panel.show_error("Literal <b>path</b>")
        assert len(answers) == 1
        panel.close()
        panel.deleteLater()


@pytest.mark.parametrize("tab", [0, 1, 2])
def test_map_buttons_do_not_accept_pending_assessments(
    window: LifftWindow, tmp_path: Path, tab: int
) -> None:
    """Open/Save buttons affect only plant images, preserving all three tool drafts.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        tab: Zero-based integrated tool-tab position used by the actual Qt interaction.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(tab)
    task_panel = window.task_panel if tab == 0 else window.secondary_panel()
    field = task_panel.inputs[0][2 if tab == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    workspace = window.presenter.workspace
    active, state = workspace.active, workspace.active.state
    settings = window._settings_store.load()
    project = workspace._project
    hierarchy = project.load_hierarchy()
    panel = PlotMapPanel(
        hierarchy,
        project,
        project,
        lambda filename: import_plant_image(Path(filename)),
        load_icons(),
        parent=window,
    )
    assert panel.set_scope(PlotScope(((hierarchy.plants[0],),)))
    panel.choose_image = Mock(return_value=str(image_file(tmp_path / "map.png")))
    panel.message = Mock(return_value=int(QMessageBox.Ok))
    panel.buttons["open"].click()
    panel.buttons["save"].click()
    assert field.text() == "bad" and task_panel.pending
    assert workspace.active is active and active.state is state
    assert window._settings_store.load() == settings
    assert window.main_navigation.toolbar_actions["plot"].isEnabled()
    panel.close()
    panel.deleteLater()
