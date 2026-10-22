"""Original worker-form workflows with synthetic saved projects and actual Qt.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QDate, QPoint, Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import list_lifft_documents, load_icons
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.worker_details import WorkerDetails
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.work_hierarchy_store import (
    decode_hierarchy,
    encode_hierarchy,
)
from ergotools.presentation.desktop.lifft_presenter import LifftPresenter
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from tests.test_history_persistence import HIERARCHY
from tests.test_workspace_job_risk import workspace_at

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_empty_birth_calendar_browses_adult_year_without_setting_date(
    tmp_path: Path, language: Language
) -> None:
    """Calendar browsing keeps missing birthdays absent and saved dates intact.

    Args:
        tmp_path: Disposable project directory owned by pytest.
        language: Supported UI language; calendar policy is language independent.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, language=language
    )
    try:
        dialog.show()
        _APP.processEvents()
        dialog.new_worker()
        dialog.worker_id_combo.setEditText("calendar-worker")
        calendar = dialog.dob_input.calendarWidget()
        assert calendar is not None
        QTest.mouseClick(
            dialog.dob_input,
            Qt.LeftButton,
            pos=QPoint(dialog.dob_input.width() - 8, dialog.dob_input.height() // 2),
        )
        _APP.processEvents()
        expected = QDate.currentDate().addYears(-18)
        assert (calendar.yearShown(), calendar.monthShown()) == (
            expected.year(),
            expected.month(),
        )
        assert dialog.dob_input.date() == dialog.dob_input.minimumDate()
        calendar.window().hide()
        dialog.save_worker()
        worker = next(
            worker
            for worker in dialog._hierarchy.hierarchy.work.workers
            if worker.worker_id == "calendar-worker"
        )
        assert worker.details.birth_date is None
        birthday = QDate(1981, 1, 15)
        dialog.dob_input.setDate(birthday)
        calendar.setCurrentPage(birthday.year(), birthday.month())
        QTest.mouseClick(
            dialog.dob_input,
            Qt.LeftButton,
            pos=QPoint(dialog.dob_input.width() - 8, dialog.dob_input.height() // 2),
        )
        _APP.processEvents()
        assert (calendar.yearShown(), calendar.monthShown()) == (1981, 1)
        assert dialog.dob_input.date() == birthday
        calendar.window().hide()
        dialog.save_worker()
        dialog.load_worker_details()
        assert dialog.dob_input.date() == birthday
        dialog.new_worker()
        QTest.mouseClick(
            dialog.dob_input,
            Qt.LeftButton,
            pos=QPoint(dialog.dob_input.width() - 8, dialog.dob_input.height() // 2),
        )
        _APP.processEvents()
        assert calendar.yearShown() == expected.year()
        assert dialog.dob_input.date() == dialog.dob_input.minimumDate()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("system", list(MeasurementSystem))
def test_details_save_reopen_units_and_cancel(
    tmp_path: Path, system: MeasurementSystem
) -> None:
    """A complete optional record survives reopen and unit projection without drift.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        system: Explicit metric/imperial display or source system exercised by this
            scenario.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = WorkerManagementDialog(workspace, load_icons(), system)
    try:
        dialog.new_button.click()
        dialog.worker_id_combo.setEditText("new-worker")
        dialog.first_name_input.setText("María")
        dialog.last_name_input.setText("Muñoz")
        dialog.height_input.setText(
            "170" if system is MeasurementSystem.METRIC else "70"
        )
        dialog.weight_input.setText(
            "80" if system is MeasurementSystem.METRIC else "180"
        )
        dialog.date_of_hiring_input.setDate(QDate(2000, 6, 8))
        dialog.dob_input.setDate(QDate(1990, 5, 7))
        dialog.gender_combo.setCurrentIndex(1)
        dialog.save_button.click()
        assert dialog.selected_worker_id == "new-worker"
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            worker = next(
                w
                for w in project.load_hierarchy().work.workers
                if w.worker_id == "new-worker"
            )
        assert worker.details.birth_date == "1990-05-07"
        assert worker.details.hiring_date == "2000-06-08"
        assert worker.details.sex == "Female"
        assert worker.details.weight_kg == pytest.approx(
            80 if system is MeasurementSystem.METRIC else 180 * 0.45359237
        )
        assert worker.details.height_cm == pytest.approx(
            170 if system is MeasurementSystem.METRIC else 177.8
        )
        dialog.first_name_input.setText("discard me")
        dialog.cancel_button.click()
        dialog.worker_id_combo.setCurrentIndex(
            dialog.worker_id_combo.findText("new-worker")
        )
        assert dialog.first_name_input.text() == "María"
        dialog.close()
        dialog = WorkerManagementDialog(
            workspace,
            load_icons(),
            MeasurementSystem.IMPERIAL
            if system is MeasurementSystem.METRIC
            else MeasurementSystem.METRIC,
            selected_worker="new-worker",
            language=Language.SPANISH,
        )
        assert dialog.windowTitle() == "Gestión de trabajadores"
        assert float(dialog.height_input.text()) == pytest.approx(
            worker.details.height_cm / 2.54
            if system is MeasurementSystem.METRIC
            else worker.details.height_cm
        )
        assert float(dialog.weight_input.text()) == pytest.approx(
            worker.details.weight_kg / 0.45359237
            if system is MeasurementSystem.METRIC
            else worker.details.weight_kg
        )
        assert dialog.notification_label.text().startswith("Nota: ")
        dialog.save_button.click()
        assert (
            next(
                w
                for w in workspace.read_hierarchy().hierarchy.work.workers
                if w.worker_id == "new-worker"
            )
            == worker
        )
        dialog.worker_id_combo.setEditText("invalid id")
        dialog.save_button.click()
        assert dialog.notification_area.property("severity") == "error"
        assert dialog.worker_id_combo.currentText() == "invalid id"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_assignment_save_rolls_back_worker_and_classification(tmp_path: Path) -> None:
    """A rejected assignment write leaves both original records and editable text.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.IMPERIAL, selected_worker="w"
    )
    before = dialog._hierarchy.hierarchy
    jobs = dialog._jobs.jobs
    combo = dialog.assignment_table.cellWidget(0, 5)
    assert isinstance(combo, QComboBox)
    combo.setCurrentIndex(combo.findData(2))
    dialog.first_name_input.setText("Changed name")
    try:
        with patch.object(
            workspace._project,
            "replace_worker_catalogs",
            side_effect=ValueError("write failed"),
        ):
            dialog.save_button.click()
        assert dialog.first_name_input.text() == "Changed name"
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            assert project.load_hierarchy() == before
            assert project.load_jobs() == jobs
        dialog.save_button.click()
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            assert (
                next(
                    w
                    for w in project.load_hierarchy().work.workers
                    if w.worker_id == "w"
                ).first_name
                == "Changed name"
            )
            assignments = project.load_jobs().assignments
            assert assignments[0].placement_id == 1 and not assignments[0].active
            assert assignments[-1].placement_id == 2 and assignments[-1].active
            assert project.load_history().entries[0].assignment_id == 1
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_add_assignment_preserves_existing_assessment(tmp_path: Path) -> None:
    """Nested real workplace picker accepts assignment without selecting an assessment.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    window = LifftWindow(LifftPresenter(workspace), load_icons(), list_lifft_documents)
    completed = []

    def use_picker() -> None:
        """Select the first actual placement and accept its exact saved identity.

        Args:
            None.

        Returns:
            None.
        """
        picker = _APP.activeModalWidget()
        assert isinstance(picker, WorkplaceAssignmentDialog)
        placement = next(p for p in picker._jobs.placements if p.active)
        picker.select_workplace(placement.workplace, placement.placement_id)
        picker.accept_button.click()

    def use_workers() -> None:
        """Add the chosen assignment for saved worker w.

        Select saved worker w, schedule the real placement picker, add one assignment
        and record its accepted assignment identity.

        Args:
            None.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, WorkerManagementDialog)
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("w"))
        QTimer.singleShot(0, use_picker)
        dialog.add_assignment_button.click()
        completed.append(dialog._jobs.jobs.assignments[-1].assignment_id)
        dialog.close()

    try:
        QTimer.singleShot(0, use_workers)
        window.buttons["worker_management"].click()
        assert completed == [1]
        assert workspace.active.document.document_id == "a"
        assert window._worker_selection == (workspace.location, "w")
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
        window.close()


def test_legacy_payload_and_invalid_details() -> None:
    """Version-one catalogs remain readable; malformed new details fail closed.

    Args:
        None.

    Returns:
        None.
    """
    payload = json.loads(encode_hierarchy(HIERARCHY))
    payload["version"] = 1
    payload["hierarchy"].pop("organization")
    for worker in payload["hierarchy"]["work"]["workers"]:
        worker.pop("details")
    assert decode_hierarchy(json.dumps(payload)) == HIERARCHY
    for fields in (
        {"height_cm": float("nan")},
        {"weight_kg": -1},
        {"birth_date": "2025-02-30"},
        {"sex": "unknown"},
    ):
        with pytest.raises(ValueError):
            WorkerDetails(**fields)
    details = WorkerDetails(height_cm=170, weight_kg=80)
    hierarchy = replace(
        HIERARCHY,
        work=replace(
            HIERARCHY.work,
            workers=(replace(HIERARCHY.work.workers[0], details=details),),
        ),
    )
    assert decode_hierarchy(encode_hierarchy(hierarchy)) == hierarchy


def test_database_failure_is_atomic_and_retryable(tmp_path: Path) -> None:
    """An actual SQLite failure after job writes rolls back classification and name.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    import sqlite3

    workspace = workspace_at(tmp_path)
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, selected_worker="w"
    )
    before = dialog._hierarchy.hierarchy
    jobs = dialog._jobs.jobs
    combo = dialog.assignment_table.cellWidget(0, 5)
    assert isinstance(combo, QComboBox)
    combo.setCurrentIndex(combo.findData(2))
    dialog.first_name_input.setText("Retry me")
    try:
        with (
            closing(sqlite3.connect(tmp_path / "project.sqlite")) as connection,
            connection,
        ):
            connection.execute(
                "CREATE TRIGGER fail_worker BEFORE UPDATE ON work_catalog "
                "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
            )
        dialog.save_button.click()
        assert dialog.notification_area.property("severity") == "error"
        with AssessmentProjectFile.open(tmp_path / "project.sqlite") as project:
            assert project.load_hierarchy() == before
            assert project.load_jobs() == jobs
        with (
            closing(sqlite3.connect(tmp_path / "project.sqlite")) as connection,
            connection,
        ):
            connection.execute("DROP TRIGGER fail_worker")
        dialog.save_button.click()
        assert dialog.notification_label.text() == "Note: Worker changes saved."
        assert workspace.active.document.document_id == "a"
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_directory_filter_paging_and_protected_delete(tmp_path: Path) -> None:
    """Filters navigate saved workers; delete cannot remove a history owner.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    hierarchy = workspace.read_hierarchy()
    from ergotools.domain.work_catalog import WorkerEntry

    workers = (
        *hierarchy.hierarchy.work.workers,
        *(WorkerEntry(f"z{i:02}", "Ada", "Smith") for i in range(15)),
    )
    workspace.replace_hierarchy(
        hierarchy,
        replace(
            hierarchy.hierarchy, work=replace(hierarchy.hierarchy.work, workers=workers)
        ),
    )
    dialog = WorkerManagementDialog(workspace, load_icons(), MeasurementSystem.METRIC)
    try:
        dialog.optional_toggle.click()
        assert not dialog.optional_details.isHidden()
        dialog.worker_search_input.setText("Smith")
        assert len(dialog._filtered) == 15
        dialog.next_page_button.click()
        assert dialog.selected_worker_id == "z10"
        dialog.set_alphabet_filter("B")
        assert not dialog._filtered
        dialog.set_alphabet_filter("All")
        dialog.worker_search_input.clear()
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("w"))
        dialog.delete_button.click()
        assert (
            dialog.notification_label.text()
            == "Note: Workers with saved assignments cannot be deleted."
        )
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("z00"))

        def confirm() -> None:
            """Accept protected-worker deletion consent.

            Accept the real deletion consent so protected-reference rejection can be
            asserted.

            Args:
                None.

            Returns:
                None.
            """
            box = _APP.activeModalWidget()
            assert isinstance(box, QMessageBox)
            box.done(QMessageBox.Yes)

        QTimer.singleShot(0, confirm)
        dialog.delete_button.click()
        assert not any(
            w.worker_id == "z00" for w in dialog._hierarchy.hierarchy.work.workers
        )
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)


def test_new_assignment_never_prompts_or_creates_assessment(tmp_path: Path) -> None:
    """Assigning another worker retains work without a close-time assessment prompt.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    workspace = workspace_at(tmp_path)
    window = LifftWindow(LifftPresenter(workspace), load_icons(), list_lifft_documents)

    def choose_placement() -> None:
        """Select the first real placement and accept it.

        Select the first real placement and accept it without implicitly creating an
        assessment.

        Args:
            None.

        Returns:
            None.
        """
        picker = _APP.activeModalWidget()
        assert isinstance(picker, WorkplaceAssignmentDialog)
        placement = next(p for p in picker._jobs.placements if p.active)
        picker.select_workplace(placement.workplace, placement.placement_id)
        picker.accept_button.click()

    def assign_worker() -> None:
        """Select saved worker x, add the actual chosen placement and close.

        Select saved worker x, add the actual chosen placement and close before the
        host returns without changing the active assessment.

        Args:
            None.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, WorkerManagementDialog)
        dialog.worker_id_combo.setCurrentIndex(dialog.worker_id_combo.findText("x"))
        QTimer.singleShot(0, choose_placement)
        dialog.add_assignment_button.click()
        dialog.close()

    try:
        with patch.object(
            QMessageBox,
            "question",
            side_effect=AssertionError("Unexpected assessment prompt"),
        ):
            QTimer.singleShot(0, assign_worker)
            window.buttons["worker_management"].click()
        history = workspace.read_history().history
        assert len(history.entries) == 1
        assert len(workspace.read_jobs().jobs.assignments) == 2
        assert workspace.active.document.document_id == "a"
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
        window.close()
