"""Management modal integration without disturbing the active assessment.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window, list_lifft_documents, load_icons
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.lifft_presenter import LifftPresenter
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_job_management_dialog import enter_new
from tests.test_workspace_job_risk import workspace_at

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def test_management_modal_preserves_assessment_and_remembers_job(
    tmp_path: Path,
) -> None:
    """Real modal save/reopen retains source edits, selection and input binding.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    window = LifftWindow(LifftPresenter(workspace), load_icons(), list_lifft_documents)
    window.presenter.add()
    window.refresh()
    active = workspace.active
    assert active is not None
    source = active.state
    context = window.context
    observed: list[str | None] = []

    def save_job() -> None:
        """Assert modal parent ownership, enter.

        Assert modal parent ownership, enter and save a complete job, record the exact
        selected identity and close.

        Args:
            None.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, JobManagementDialog)
        assert dialog.parent() is window
        enter_new(dialog)
        with patch.object(QMessageBox, "information"):
            dialog.save_button.click()
        observed.append(dialog.selected_job_id)
        dialog.close()

    def reopen() -> None:
        """Check remembered exact job selection and Spanish title on reopening.

        Check remembered exact job selection and Spanish title on reopening, then close
        the real modal.

        Args:
            None.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, JobManagementDialog)
        observed.append(dialog.selected_job_id)
        assert dialog.windowTitle() == "Gestión de trabajos"
        dialog.close()

    try:
        window.show()
        QTimer.singleShot(0, save_job)
        window.buttons["job_form_title"].click()
        assert active.state is source
        assert active.is_dirty
        assert window.context is context
        window.language = Language.SPANISH
        window.translate()
        QTimer.singleShot(0, reopen)
        window.buttons["job_form_title"].click()
        assert observed == ["assembly", "assembly"]
        window.presenter.workspace.active.undo()
        assert not window.presenter.source().tasks
        window.pending = True
        window.enable_controls()
        assert not window.buttons["job_form_title"].isEnabled()
        window.open_job_management()
    finally:
        window.pending = False
        workspace.close(choice=CloseChoice.DISCARD)
        window.close()
        window.deleteLater()


def test_save_preserves_selected_job_and_only_current_values(tmp_path: Path) -> None:
    """Saving current Job values does not change selection or add alternate risk rows.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; literal draft identity remains editable until accepted.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(workspace, load_icons(), MeasurementSystem.IMPERIAL)
    try:
        enter_new(dialog)
        dialog.save_button.click()
        assert dialog.selected_job_id == "assembly"
        dialog.save_button.click()
        assert len(dialog._risk.risk.values) == 1
        dialog.job_id_combo.setEditText("unsaved-id")
        assert dialog.selected_job_id is None
        dialog.new_job()
        assert dialog.selected_job_id is None
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_empty_preview_cannot_open_management(tmp_path: Path) -> None:
    """No implicit project creation or format upgrade occurs on this action.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    window = create_window(tmp_path / "settings.json")
    try:
        assert not window.buttons["job_form_title"].isEnabled()
        window.open_job_management()
        assert window.presenter.workspace.active is None
    finally:
        window.close()
        window.deleteLater()
