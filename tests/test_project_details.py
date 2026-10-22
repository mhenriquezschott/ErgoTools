"""Original details collection, metadata round trips and backward compatibility.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialogButtonBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.project_details_dialog import ProjectDetailsDialog
from ergotools.presentation.desktop.project_properties_dialog import (
    ProjectPropertiesDialog,
)
from tests.test_history_persistence import META
from tests.test_optional_assessment_context import start_standalone_worker
from tests.test_saved_tool_data import window as window


def test_first_save_details_cancel_preserves_unsaved_project(
    window: LifftWindow, tmp_path: Path
) -> None:
    """New asks nothing; Cancel first Save retains invalid text and temporary owner.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with patch.object(window, "choose_file") as choose:
        window.new_project()
    choose.assert_not_called()
    start_standalone_worker(window)
    active = window.presenter.workspace.active
    state = active.state
    settings = window._settings_store.load()
    panel = window.task_panel
    assert panel is not None
    field = panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    target = tmp_path / "new.ergprj"

    cancelled = []

    def cancel() -> None:
        """Assert first-Save metadata fields are empty and cancel the actual form.

        Assert first-Save metadata fields are empty and cancel the actual form before
        source input is parsed.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, ProjectDetailsDialog)
        assert dialog.name_input.text() == ""
        assert dialog.description_input.toPlainText() == ""
        cancelled.append(True)
        dialog.button_box.button(QDialogButtonBox.Cancel).click()

    with (
        patch.object(window, "choose_file", return_value=str(target)),
        patch.object(
            window, "dirty_choice", side_effect=AssertionError("Consent too early")
        ),
    ):
        QTimer.singleShot(0, cancel)
        window.main_navigation.toolbar_actions["save"].trigger()
    assert cancelled == [True]
    assert not target.exists()
    assert window.presenter.workspace.active is active and active.state is state
    assert field.text() == "bad" and panel.pending
    assert window._settings_store.load() == settings
    field.setText("")
    field.textEdited.emit("")


def test_original_new_details_persist_and_survive_copies(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Accepted text and creation defaults survive reopen and project copies.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window.language = Language.SPANISH
    window.presenter.system = MeasurementSystem.METRIC
    window.translate()
    target = tmp_path / "filename.ergprj"
    start = datetime.now().replace(microsecond=0)
    description = "Primera línea & datos\n<b>Second line</b>"

    def accept() -> None:
        """Assert Spanish project-details title/buttons.

        Assert Spanish project-details title/buttons, enter a literal project
        name/description and accept first Save.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, ProjectDetailsDialog)
        assert dialog.windowTitle() == "Detalles del proyecto"
        assert dialog.button_box.button(QDialogButtonBox.Ok).text() == "Aceptar"
        dialog.name_input.setText("  Named project  ")
        dialog.description_input.setPlainText(description)
        dialog.button_box.button(QDialogButtonBox.Ok).click()

    with patch.object(window, "choose_file", return_value=str(target)):
        window._assessment_menu.actions_by_key["new"].trigger()
        QTimer.singleShot(0, accept)
        window.main_navigation.toolbar_actions["save"].trigger()
    workspace = window.presenter.workspace
    metadata = workspace.project_metadata
    assert metadata.title == "Named project" and metadata.description == description
    assert start <= metadata.created_at <= datetime.now()
    assert metadata.language is Language.SPANISH
    assert metadata.default_units is MeasurementSystem.METRIC
    assert workspace.active is None
    with AssessmentProjectFile.open(target) as empty:
        assert not empty.list_assessments()
        assert not empty.load_hierarchy().plants
    assert (
        window.main_navigation.project_label.text()
        == "Proyecto actual: Named project  •  Cargado"
    )
    properties = ProjectPropertiesDialog(
        metadata, str(target), Language.ENGLISH, parent=window
    )
    assert properties.description.toPlainText() == description
    assert properties.description.isReadOnly()
    assert properties.fields["created"].text() == metadata.created_at.isoformat(sep=" ")
    assert properties.fields["language"].text() == "Spanish"
    properties.deleteLater()
    copy = tmp_path / "copy.ergprj"
    backup = tmp_path / "backup.ergprj"
    assert workspace.backup(str(backup)).completed
    assert workspace.save_as(str(copy)).completed
    assert workspace.close(choice=CloseChoice.DISCARD).completed
    for path in (target, copy, backup):
        with AssessmentProjectFile.open(path) as project:
            assert project.metadata == metadata
            assert not project.list_assessments()
            assert not project.load_hierarchy().plants
    window.refresh()


def test_blank_name_fallback_dirty_cancel_and_existing_destination(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Cancelled New retains owner; first Save never overwrites an existing file.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    active = workspace.active
    target = tmp_path / "fallback.ergprj"
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        window.new_project()
    assert workspace.active is active
    window.new_project()
    unsaved = workspace.active
    target.write_bytes(b"existing contents")
    with patch.object(window, "choose_file", return_value=str(target)):
        window.save_project()
    assert target.read_bytes() == b"existing contents" and workspace.active is unsaved
    target.unlink()
    with (
        patch.object(window, "choose_file", return_value=str(target)),
        patch.object(window, "choose_project_details", return_value=("  ", "")),
    ):
        window.save_project()
    assert workspace.project_metadata.title == "fallback"
    assert workspace.project_metadata.description == ""


def test_old_metadata_reads_without_rewrite_and_extended_fields_require_v8(
    tmp_path: Path,
) -> None:
    """Old versions remain readable; older writers never silently discard details.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    for version in range(2, 8):
        path = tmp_path / f"old-{version}.ergprj"
        with AssessmentProjectFile.create_with_document(
            path, META, "a", LifftDraft(META.default_units), format_version=version
        ):
            pass
        before = path.read_bytes()
        with AssessmentProjectFile.open(path) as project:
            assert project.metadata == META
            assert project.metadata.created_at is None
        assert path.read_bytes() == before
    details = replace(META, description="description")
    target = tmp_path / "rejected.ergprj"
    with pytest.raises(ValueError, match="version eight"):
        AssessmentProjectFile.create_with_document(
            target, details, "a", LifftDraft(META.default_units)
        )
    assert not target.exists()


@pytest.mark.parametrize(
    "column,value",
    [
        ("language", "fr"),
        ("created_at", "2026-02-30T12:00:00"),
        ("created_at", "2026-10-06T12:00:00+00:00"),
        ("created_at", "2026-10-06T12:00:00.100"),
        ("description", b"bytes"),
    ],
)
def test_malformed_saved_details_rejected(
    tmp_path: Path, column: str, value: object
) -> None:
    """Reject invalid types/timestamps/languages before adopting a project handle.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        column: Zero-based visible column or explicit SQL column identity selected by
            the regression.
        value: Parametrized valid/invalid boundary value; expected acceptance is
            asserted before publication.

    Returns:
        None.
    """
    path = tmp_path / "details.ergprj"
    with AssessmentProjectFile.create_with_document(
        path, META, "a", LifftDraft(META.default_units), format_version=8
    ):
        pass
    with closing(sqlite3.connect(path)) as connection, connection:
        # Column identifiers are an explicit test-only whitelist.
        assert column in ("language", "created_at", "description")
        connection.execute(f"UPDATE project_details SET {column} = ?", (value,))
    with pytest.raises(StoreFormatError, match="Invalid project details"):
        AssessmentProjectFile.open(path)


def test_metadata_rejects_invalid_new_values() -> None:
    """Portable metadata requires typed language and second-precision local time.

    Args:
        None.

    Returns:
        None.
    """
    for kwargs in (
        {"description": 1},
        {"created_at": "now"},
        {"created_at": datetime.now(UTC)},
        {"language": "es"},
    ):
        with pytest.raises(ValueError):
            replace(META, **kwargs)
