"""Bilingual form workflows without changing stored evidence or unit identities.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
from pathlib import Path
from string import Formatter
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language, UserSettings
from ergotools.bootstrap import (
    create_job_management_demo,
    load_icons,
    run_job_management,
)
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.job_management_dialog import JobManagementDialog
from ergotools.presentation.desktop.text import _MESSAGES, job_management_error
from tests.test_job_management_dialog import enter_new
from tests.test_workspace_job_risk import workspace_at

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def test_spanish_current_values_preserve_units(tmp_path: Path) -> None:
    """Spanish labels do not reinterpret entered damage or recorded units.

    Args:
        tmp_path: Disposable native project and preference directory.

    Returns:
        None; no obsolete profile/evidence controls remain.
    """
    workspace = workspace_at(tmp_path)
    path = tmp_path / "project.sqlite"
    before = path.read_bytes()
    dialog = JobManagementDialog(
        workspace, load_icons(), MeasurementSystem.IMPERIAL, language=Language.SPANISH
    )
    try:
        assert path.read_bytes() == before
        assert dialog.windowTitle() == "Gestión de trabajos"
        assert dialog.first_button.toolTip() == "Primer trabajo"
        assert not hasattr(dialog, "profile_tabs")
        enter_new(dialog)
        dialog.save_button.click()
        with AssessmentProjectFile.open(path) as project:
            current = project.load_job_risk().for_job("assembly")
            assert current.measurements[0].unit == "Imperial"
            assert current.measurements[0].cumulative_damage == 1
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_spanish_confirmation_and_error_buttons(tmp_path: Path) -> None:
    """Real modal messages have Spanish bodies/buttons and retain protected jobs.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = JobManagementDialog(
        workspace, load_icons(), MeasurementSystem.IMPERIAL, language=Language.SPANISH
    )
    seen = []
    try:

        def cancel() -> None:
            """Assert Spanish deletion title and Yes/No labels.

            Assert Spanish deletion title and Yes/No labels, then click No and record
            cancellation.

            Args:
                None.

            Returns:
                None.
            """
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            assert box.windowTitle() == "Confirmar eliminación"
            yes, no = box.button(QMessageBox.Yes), box.button(QMessageBox.No)
            assert yes is not None and no is not None
            assert yes.text() == "Sí" and no.text() == "No"
            seen.append("cancel")
            no.click()

        QTimer.singleShot(0, cancel)
        dialog.delete_button.click()
        assert dialog.job_id_combo.currentText() == "j"

        def error() -> None:
            """Assert localized protected-assessment failure.

            Assert localized protected-assessment failure and Aceptar acknowledgement,
            then dismiss the owned message.

            Args:
                None.

            Returns:
                None.
            """
            box = QApplication.activeModalWidget()
            assert isinstance(box, QMessageBox)
            assert "evaluación" in box.text()
            ok = box.button(QMessageBox.Ok)
            assert ok is not None and ok.text() == "Aceptar"
            seen.append("error")
            ok.click()

        QTimer.singleShot(0, error)
        with patch.object(dialog, "_question", return_value=int(QMessageBox.Yes)):
            dialog.delete_button.click()
        assert dialog.job_id_combo.currentText() == "j"
        assert seen == ["cancel", "error"]
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_launcher_honors_saved_language_and_temporary_override(tmp_path: Path) -> None:
    """Use saved preferences unless explicitly overridden for this preview.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "demo.ergprj"
    create_job_management_demo(path)
    settings_path = tmp_path / "settings.json"
    store = JsonSettingsStore(settings_path)
    store.save(UserSettings(language=Language.SPANISH))
    seen = []

    def close() -> None:
        """Record the real launched form title before clicking Close.

        Record the real launched form title before clicking Close to characterize
        saved/overridden language.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, JobManagementDialog)
        seen.append(dialog.windowTitle())
        dialog.close_button.click()

    for language in (None, Language.ENGLISH):
        QTimer.singleShot(0, close)
        assert run_job_management(path, settings_path, language=language) == 0
    assert seen == ["Gestión de trabajos", "Job Management"]
    assert store.load().language is Language.SPANISH


def test_form_catalog_preserves_template_fields_and_error_language() -> None:
    """Localized job/version/count messages keep their required placeholders.

    Args:
        None.

    Returns:
        None.
    """
    formatter = Formatter()
    for key, (english, spanish) in _MESSAGES.items():
        if key.startswith("job_form_"):
            english_fields = {
                name for _, name, _, _ in formatter.parse(english) if name
            }
            spanish_fields = {
                name for _, name, _, _ in formatter.parse(spanish) if name
            }
            assert english_fields == spanish_fields
            assert english and spanish
    assert (
        job_management_error("Unknown adapter validation", Language.SPANISH)
        == "Revise los valores del formulario e inténtelo de nuevo."
    )
    assert (
        job_management_error("Unknown adapter validation", Language.ENGLISH)
        == "Unknown adapter validation"
    )
