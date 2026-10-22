"""Original prefilled Save As metadata, copy isolation and failure atomicity.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QDialogButtonBox

from ergotools.application.settings import Language
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.project_details_dialog import ProjectDetailsDialog
from tests.test_history_persistence import META
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_actual_save_as_details_cancel_preserves_invalid_pending_text(
    window: LifftWindow, index: int, tmp_path: Path
) -> None:
    """Cancel a prefilled form before parsing input or changing the current owner.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    state = active.state
    settings = window._settings_store.load()
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    target = tmp_path / "copy.ergprj"

    def cancel() -> None:
        """Check prefilled saved metadata, type unaccepted changes and cancel Save As.

        Check prefilled saved metadata, type unaccepted changes and cancel Save As
        before pending assessment parsing.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, ProjectDetailsDialog)
        assert modal.name_input.text() == META.title
        assert modal.description_input.toPlainText() == ""
        modal.name_input.setText("Unaccepted title")
        modal.description_input.setPlainText("Unaccepted description")
        modal.button_box.button(QDialogButtonBox.Cancel).click()

    with patch.object(window, "choose_file", return_value=str(target)):
        QTimer.singleShot(0, cancel)
        window._assessment_menu.save_as.trigger()
    assert not target.exists() and workspace.location == location
    assert workspace.active is active and active.state is state
    assert field.text() == "bad" and panel.pending
    assert workspace.project_metadata == META
    assert window._settings_store.load() == settings


@pytest.mark.parametrize("index", [0, 1, 2])
def test_actual_save_as_updates_only_copy_metadata_and_current_input(
    window: LifftWindow, index: int, tmp_path: Path
) -> None:
    """Native Spanish form changes copy defaults without rewriting source units/data.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    original = Path(workspace.location)
    with AssessmentProjectFile.open(original) as project:
        sources = {
            entry.document: project.load(entry.document)
            for entry in project.list_assessments()
        }
        hierarchy, jobs, history, risk = (
            project.load_hierarchy(),
            project.load_jobs(),
            project.load_history(),
            project.load_job_risk(),
        )
    before = original.read_bytes()
    old_active = workspace.active
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("350")
    field.textEdited.emit("350")
    window.language = Language.SPANISH
    window.presenter.system = MeasurementSystem.METRIC
    window.translate()
    description = "Descripción & valores\nLiteral <b>text</b>"
    target = tmp_path / "copy.ergprj"
    start = datetime.now().replace(microsecond=0)

    def accept() -> None:
        """Check prefilled metadata and Spanish acknowledgement.

        Check prefilled metadata and Spanish acknowledgement, then accept explicit
        name/description changes for the copy only.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, ProjectDetailsDialog)
        assert modal.name_input.text() == META.title
        assert modal.button_box.button(QDialogButtonBox.Ok).text() == "Aceptar"
        modal.name_input.setText("  Named copy  ")
        modal.description_input.setPlainText(description)
        modal.button_box.button(QDialogButtonBox.Ok).click()

    with patch.object(window, "choose_file", return_value=str(target)):
        QTimer.singleShot(0, accept)
        window._assessment_menu.save_as.trigger()
    metadata = workspace.project_metadata
    assert metadata.project_id == META.project_id and metadata.title == "Named copy"
    assert metadata.description == description and metadata.language is Language.SPANISH
    assert metadata.default_units is MeasurementSystem.METRIC
    assert start <= metadata.created_at <= datetime.now()
    assert (
        window.main_navigation.project_label.text()
        == "Proyecto actual: Named copy  •  Cargado"
    )
    assert workspace.active is not old_active and not workspace.active.is_dirty
    assert workspace.active.state.tasks[0] == replace(
        sources[old_active.document].tasks[0], repetitions=350
    )
    assert original.read_bytes() == before
    with AssessmentProjectFile.open(target) as project:
        assert project.format_version == 8 and project.metadata == metadata
        assert (
            project.load_hierarchy(),
            project.load_jobs(),
            project.load_history(),
            project.load_job_risk(),
        ) == (hierarchy, jobs, history, risk)
        for key, source in sources.items():
            assert project.load(key) == (
                workspace.active.state if key == old_active.document else source
            )
    assert not list(tmp_path.glob(".ergotools-snapshot-*"))


def test_version_eight_prefill_and_blank_name_fallback(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Prefill literal saved descriptions and update an existing format-eight copy.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    metadata = replace(
        META,
        description="First\n<b>literal</b> & description",
        language=Language.SPANISH,
        created_at=datetime(2026, 10, 1, 12),
    )
    path = tmp_path / "v8.ergprj"
    with AssessmentProjectFile.create_with_document(
        path, metadata, "a", LifftDraft(META.default_units), format_version=8
    ):
        pass
    workspace = window.presenter.workspace
    workspace.switch(str(path), "a")
    window.refresh()
    target = tmp_path / "fallback.ergprj"

    def accept() -> None:
        """Check the original saved description, accept a blank proposed name.

        Check the original saved description, accept a blank proposed name and exercise
        the native filename fallback.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, ProjectDetailsDialog)
        assert modal.description_input.toPlainText() == metadata.description
        modal.name_input.setText(" ")
        modal.accept()

    with patch.object(window, "choose_file", return_value=str(target)):
        QTimer.singleShot(0, accept)
        window._assessment_menu.save_as.trigger()
    assert workspace.project_metadata.title == "fallback"
    assert workspace.project_metadata.description == metadata.description
    assert workspace.project_metadata.created_at > metadata.created_at
    with AssessmentProjectFile.open(path) as original:
        assert original.metadata == metadata


def test_copy_metadata_sql_failure_keeps_original_and_removes_temporary_copy(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Failure after details insertion rolls back before exclusive publication.

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
    original = Path(workspace.location)
    before = original.read_bytes()
    target = tmp_path / "failed.ergprj"
    connect = sqlite3.connect

    class FailingConnection(sqlite3.Connection):
        """Inject only the metadata UPDATE failure.

        Temporary SQLite connection injecting failure only at the metadata UPDATE
        publication stage.
        """

        def execute(
            self, statement: str, parameters: tuple[object, ...] = (), /
        ) -> sqlite3.Cursor:
            """Reject the selected metadata UPDATE.

            Reject the selected metadata UPDATE before delegating all other statements
            and bound parameters unchanged.

            Args:
                statement: Explicit SQL statement forwarded to the controlled temporary
                    connection.
                parameters: Bound SQL parameters forwarded unchanged to the controlled
                    temporary connection.

            Returns:
                SQLite cursor from the underlying connection for permitted statements;
                the selected metadata UPDATE raises before executing.

            Raises:
                sqlite3.OperationalError: The deliberately injected SQLite
                    write/metadata failure is reached.
            """
            if statement.startswith("UPDATE project_metadata"):
                raise sqlite3.OperationalError("injected metadata failure")
            return super().execute(statement, parameters)

    def failing_connect(database: Path) -> sqlite3.Connection:
        """Open the disposable SQLite database.

        Open the disposable SQLite database with the controlled metadata-failure
        connection class.

        Args:
            database: Disposable SQLite path opened with the injected failure connection
                class.

        Returns:
            Owned temporary SQLite connection configured to inject metadata-update
            failure; caller closes it.
        """
        return connect(database, factory=FailingConnection)

    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.sqlite3.connect",
            side_effect=failing_connect,
        ),
        pytest.raises(sqlite3.OperationalError, match="injected"),
    ):
        workspace.save_as(
            str(target), metadata=replace(META, title="Copy", description="text")
        )
    assert workspace.active is active and workspace.project_metadata == META
    assert original.read_bytes() == before and not target.exists()
    assert not list(tmp_path.glob(".ergotools-snapshot-*"))


def test_metadata_copy_rejects_identity_changes_and_partial_schema(
    tmp_path: Path,
) -> None:
    """Copy edits never rekey relationships or silently migrate partial projects.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "partial.ergprj"
    with (
        AssessmentProjectFile.create_with_document(
            path, META, "a", LifftDraft(META.default_units)
        ) as project,
        pytest.raises(StoreFormatError, match="full-project"),
    ):
        project.snapshot_with_metadata(
            str(tmp_path / "copy.ergprj"),
            None,
            None,
            replace(META, description="text"),
        )
    path = tmp_path / "full.ergprj"
    with (
        AssessmentProjectFile.create_with_document(
            path, META, "a", LifftDraft(META.default_units), format_version=8
        ) as project,
        pytest.raises(ValueError, match="identity"),
    ):
        project.snapshot_with_metadata(
            str(tmp_path / "copy.ergprj"),
            None,
            None,
            replace(META, project_id="other"),
        )
    assert not (tmp_path / "copy.ergprj").exists()
