"""Original workplace dialog interactions with real Qt and synthetic projects.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication, QDialog, QTreeWidgetItem

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.resources import read_asset
from ergotools.presentation.desktop.job_workplace_dialog import JobWorkplaceDialog
from ergotools.presentation.job_workplaces import JobWorkplaces
from tests.test_job_workplaces import JOBS, PLACES, STATIONS, seed_workspace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


type DialogFixture = tuple[JobWorkplaceDialog, ProjectWorkspace[AssessmentDraft]]


@pytest.fixture
def dialog(tmp_path: Path) -> Iterator[DialogFixture]:
    """Own a real dialog and close its synthetic workspace on every exit.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Owned real workplace dialog plus its synthetic workspace/parent; fixture cleanup
        releases each after the test.
    """
    workspace = seed_workspace(tmp_path)
    presenter = JobWorkplaces(workspace)
    icons = {}
    for name in (
        "plant",
        "section",
        "line",
        "station",
        "filter_reset",
        "save",
        "close",
    ):
        pixmap = QPixmap()
        assert pixmap.loadFromData(read_asset("icons/" + name + ".png"))
        icons[name] = QIcon(pixmap)
    window = JobWorkplaceDialog(presenter, presenter.load("j"), icons)
    window.show()
    _APP.processEvents()
    try:
        yield window, workspace
    finally:
        window.close()
        window.deleteLater()
        _APP.processEvents()
        workspace.close(choice=CloseChoice.DISCARD)


def leaves(window: JobWorkplaceDialog) -> list[QTreeWidgetItem]:
    """Return station nodes regardless of expansion or filtering.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        All station leaf items, including hidden/collapsed nodes; tree retains their
        ownership.
    """
    return [item for item in window.items() if item.childCount() == 0]


def test_shift_render_does_not_emit_item_changes(dialog: DialogFixture) -> None:
    """Repeated shift rendering has no checkbox event cascade or lost selection.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    window, _ = dialog
    spy = QSignalSpy(window.workplace_tree.itemChanged)
    for _ in range(3):
        window.shift_combo.setCurrentText("Night")
        assert all(item.checkState(0) == Qt.Unchecked for item in leaves(window))
        window.shift_combo.setCurrentText("Day")
        assert leaves(window)[0].checkState(0) == Qt.Checked
    assert len(spy) == 0
    assert "1 total" in window.assignment_status.text()


def test_filter_clear_and_save_across_shifts(
    dialog: DialogFixture, tmp_path: Path
) -> None:
    """Hidden checked nodes survive filtering; clear affects only the shown shift.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window, _ = dialog
    window.workplace_tree.expandAll()
    leaves(window)[1].setCheckState(0, Qt.Checked)
    window.filter_input.setText("2")
    assert leaves(window)[0].isHidden()
    window.shift_combo.setCurrentText("Night")
    leaves(window)[2].setCheckState(0, Qt.Checked)
    window.clear_button.click()
    assert all(item.checkState(0) == Qt.Unchecked for item in leaves(window))
    leaves(window)[2].setCheckState(0, Qt.Checked)
    window.save_button.click()
    assert window.result() == QDialog.Accepted
    assert window.preferred_shift == "Night"
    with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
        selected = {
            p.workplace
            for p in project.load_jobs().placements
            if p.job_id == "j" and p.active
        }
        assert selected == {PLACES[0], PLACES[1], STATIONS[2].at_shift("Night")}


def test_cancel_does_not_persist(dialog: DialogFixture, tmp_path: Path) -> None:
    """Cancelling after checkbox edits leaves all saved placement records intact.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window, _ = dialog
    window.clear_button.click()
    window.cancel_button.click()
    assert window.result() == QDialog.Rejected
    with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
        assert project.load_jobs() == JOBS


def test_save_failure_retains_selection_and_blocks_reentry(
    dialog: DialogFixture,
) -> None:
    """A modal warning cannot recursively save; a later deliberate retry succeeds.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    window, _ = dialog
    window.clear_button.click()
    with (
        patch.object(
            window.presenter, "save", side_effect=OSError("write failed")
        ) as save,
        patch(
            "ergotools.presentation.desktop.job_workplace_dialog.QMessageBox.warning",
            side_effect=lambda *_: window.save_assignments(),
        ) as warning,
    ):
        window.save_button.click()
        assert save.call_count == 1
        assert warning.call_count == 1
    assert window.result() != QDialog.Accepted
    assert "Organization-neutral" in window.assignment_status.text()
    window.save_button.click()
    assert window.result() == QDialog.Accepted


def test_parent_checkbox_and_stale_save(dialog: DialogFixture) -> None:
    """Checking a hierarchy parent selects its stations; stale saves stay open.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    window, workspace = dialog
    window.workplace_tree.topLevelItem(0).setCheckState(0, Qt.Checked)
    assert all(item.checkState(0) == Qt.Checked for item in leaves(window))
    workspace.read_jobs()
    with patch(
        "ergotools.presentation.desktop.job_workplace_dialog.QMessageBox.warning"
    ) as warning:
        window.save_button.click()
        assert warning.call_count == 1
    assert window.result() != QDialog.Accepted


def test_empty_view_and_preferred_shift(dialog: DialogFixture) -> None:
    """Empty hierarchy controls remain usable; remembered shifts select explicitly.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    from dataclasses import replace

    window, _ = dialog
    icons = {
        name: QIcon()
        for name in (
            "plant",
            "section",
            "line",
            "station",
            "filter_reset",
            "save",
            "close",
        )
    }
    empty = JobWorkplaceDialog(
        window.presenter,
        replace(window.view, options=(), selected=frozenset()),
        icons,
    )
    preferred = JobWorkplaceDialog(
        window.presenter, window.view, icons, preferred_shift="Night"
    )
    try:
        empty.clear_assignments()
        empty.apply_filter("absent")
        assert empty.workplace_tree.topLevelItemCount() == 0
        assert "Organization-neutral" in empty.assignment_status.text()
        assert preferred.shift_combo.currentText() == "Night"
        assert all(item.checkState(0) == Qt.Unchecked for item in leaves(preferred))
    finally:
        empty.close()
        preferred.close()


def test_spanish_labels_preserve_data_and_selection(dialog: DialogFixture) -> None:
    """Translated chrome leaves exact stored shift IDs and selected owners intact.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    from ergotools.application.settings import Language

    window, _ = dialog
    icons = {
        name: QIcon()
        for name in (
            "plant",
            "section",
            "line",
            "station",
            "filter_reset",
            "save",
            "close",
        )
    }
    spanish = JobWorkplaceDialog(
        window.presenter, window.view, icons, language=Language.SPANISH
    )
    try:
        assert spanish.save_button.text() == "Guardar asignaciones"
        assert spanish.cancel_button.text() == "Cancelar"
        assert spanish.shift_combo.currentText() == "Day"
        assert spanish.workplace_tree.topLevelItem(0).text(2) == "Planta"
        assert spanish._selected == window._selected
        assert "asignación" in spanish.assignment_status.text()
        with (
            patch.object(
                spanish.presenter, "save", side_effect=OSError("private path")
            ),
            patch(
                "ergotools.presentation.desktop.job_workplace_dialog.QMessageBox.warning"
            ) as warning,
        ):
            spanish.save_button.click()
            assert warning.call_args.args[1] == "Asignaciones de puestos"
            assert "No se pudieron guardar" in warning.call_args.args[2]
            assert "private path" not in warning.call_args.args[2]
    finally:
        spanish.close()


def test_workplace_translation_placeholders() -> None:
    """Every translated template preserves the formatting parameters it requires.

    Args:
        None.

    Returns:
        None.
    """
    from string import Formatter

    from ergotools.presentation.desktop.text import _MESSAGES

    formatter = Formatter()
    for key, (english, spanish) in _MESSAGES.items():
        if key.startswith("placements_"):
            assert {f for _, f, _, _ in formatter.parse(english) if f} == {
                f for _, f, _, _ in formatter.parse(spanish) if f
            }


def test_host_actual_save_cancel_and_reentry(dialog: DialogFixture) -> None:
    """The real modal host saves once, returns context and rejects nested opening.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    from PyQt5.QtCore import QTimer

    from ergotools.application.settings import Language
    from ergotools.presentation.desktop.job_workplace_host import JobWorkplaceHost

    _, workspace = dialog
    icons = {
        name: QIcon()
        for name in (
            "plant",
            "section",
            "line",
            "station",
            "filter_reset",
            "save",
            "close",
        )
    }
    host = JobWorkplaceHost(workspace, icons)
    errors = []

    def save() -> None:
        """Attempt prohibited nested host entry.

        Attempt prohibited nested host entry, record its RuntimeError, clear the
        displayed placements and click one real Save.

        Args:
            None.

        Returns:
            None.
        """
        opened = _APP.activeModalWidget()
        try:
            host.edit("j")
        except RuntimeError as error:
            errors.append(str(error))
        opened.clear_button.click()
        opened.save_button.click()

    QTimer.singleShot(0, save)
    result = host.edit("j", language=Language.SPANISH, preferred_shift="Night")
    assert result is not None and result.preferred_shift == "Night"
    assert result.view.selected == frozenset((PLACES[0],))
    assert len(errors) == 1
    QTimer.singleShot(0, lambda: _APP.activeModalWidget().reject())
    assert host.edit("j") is None


def test_host_failure_releases_dialog_and_can_retry(dialog: DialogFixture) -> None:
    """Load/exec failures reset the host guard and release constructed dialogs.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.

    Returns:
        None.
    """
    from PyQt5.QtCore import QTimer

    from ergotools.presentation.desktop.job_workplace_host import JobWorkplaceHost

    _, workspace = dialog
    icons = {
        name: QIcon()
        for name in (
            "plant",
            "section",
            "line",
            "station",
            "filter_reset",
            "save",
            "close",
        )
    }
    host = JobWorkplaceHost(workspace, icons)
    with pytest.raises(ValueError):
        host.edit("missing")
    with (
        patch.object(JobWorkplaceDialog, "exec", side_effect=RuntimeError("exec")),
        patch.object(JobWorkplaceDialog, "close") as close,
        patch.object(JobWorkplaceDialog, "deleteLater") as release,
        pytest.raises(RuntimeError, match="exec"),
    ):
        host.edit("j")
    assert close.call_count == release.call_count == 1
    QTimer.singleShot(0, lambda: _APP.activeModalWidget().reject())
    assert host.edit("j") is None
