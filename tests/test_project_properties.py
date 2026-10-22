"""Read-only native project Properties with saved defaults and safe record text.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.project_properties_dialog import (
    ProjectPropertiesDialog,
)
from tests.test_history_persistence import META
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_properties_preserve_invalid_pending_text_and_saved_defaults(
    window: LifftWindow, index: int
) -> None:
    """Repeated actual modal opens never parse, save or change tool selection.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    active = workspace.active
    state = active.state
    settings = window._settings_store.load()
    window.presenter.system = MeasurementSystem.METRIC
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    opened = []

    def close_properties() -> None:
        """Assert applicable fields, saved units/path and real Close acceptance.

        Opening the resizable, read-only native Properties modal must never parse or
        save the deliberately invalid assessment input behind it.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, ProjectPropertiesDialog)
        assert dialog.parent() is window
        assert len(dialog.fields) == 6
        assert dialog.fields["name"].text() == META.title
        assert dialog.fields["units"].text() == "Imperial"
        assert dialog.fields["location"].text() == workspace.location
        assert dialog.width() >= 620 and dialog.height() >= 460
        opened.append(dialog)
        dialog.close_button.click()
        assert dialog.result() == QDialog.Accepted

    for _ in range(2):
        QTimer.singleShot(0, close_properties)
        window._assessment_menu.properties.trigger()
    assert opened[0] is not opened[1]
    assert workspace.project_metadata == META
    assert workspace.active is active and active.state is state
    assert field.text() == "bad" and panel.pending
    assert window.assessment_tabs.currentIndex() == index
    assert window._settings_store.load() == settings


def test_properties_long_literal_values_and_absent_legacy_metadata(
    window: LifftWindow,
) -> None:
    """Long names/paths remain copyable without markup or invented metadata.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    title = "<b>Record & title</b> " + "Long name " * 50
    location = "/" + "long directory/" * 25 + "example.ergprj"
    dialog = ProjectPropertiesDialog(
        replace(META, title=title, default_units=MeasurementSystem.METRIC),
        location,
        Language.SPANISH,
        parent=window,
    )
    dialog.show()
    QApplication.processEvents()
    assert dialog.windowTitle() == "Propiedades del proyecto"
    assert dialog.close_button.text() == "Cerrar"
    assert dialog.fields["units"].text() == "Métrico"
    assert dialog.fields["name"].text() == title
    assert dialog.fields["name"].isReadOnly()
    assert dialog.fields["location"].text() == location
    assert dialog.fields["location"].cursorPosition() == 0
    assert dialog.fields["location"].toolTip() == location
    assert dialog.fields["location"].accessibleDescription() == location
    assert dialog.description.toPlainText() == ""
    assert all(
        dialog.fields[key].text() == "Sin registro" for key in ("created", "language")
    )
    assert all(field.isVisible() for field in dialog.fields.values())
    assert dialog.rect().contains(dialog.close_button.geometry())
    dialog.reject()
    dialog.deleteLater()


def test_properties_follow_save_as_and_disable_after_close(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Details use the current connection location, not a stale cached original.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    destination = tmp_path / "copy.ergprj"
    assert workspace.save_as(str(destination)).completed
    window.refresh()

    def close_properties() -> None:
        """Assert native filename/location follow the active Save As copy.

        Duplicate database/sidecar paths are not meaningful fields in this format.
        Rejecting this read-only modal must not alter the copied project.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, ProjectPropertiesDialog)
        assert dialog.fields["file"].text() == destination.name
        assert dialog.fields["location"].text() == str(destination)
        assert (
            "database_path" not in dialog.fields and "images_path" not in dialog.fields
        )
        dialog.reject()

    QTimer.singleShot(0, close_properties)
    window._assessment_menu.properties.trigger()
    window.language = Language.SPANISH
    window.translate()
    assert window._assessment_menu.properties.text() == "Propiedades"
    assert workspace.close(choice=CloseChoice.DISCARD).completed
    window.refresh()
    assert workspace.project_metadata is None
    assert not window._assessment_menu.properties.isEnabled()
    window.open_project_properties()
    assert QApplication.activeModalWidget() is None
