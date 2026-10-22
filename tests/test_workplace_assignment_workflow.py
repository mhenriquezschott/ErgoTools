"""Workplace-first optional Job selection and atomic assessment association.

Test layer. Drive native Qt identities and real private SQLite transactions using
synthetic projects only. Creation/reuse, rollback, main Save/reopen and shared replay
must retain exact scientific input/result bytes and never leave orphan assignments.
"""

import sqlite3
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QPushButton,
    QStyle,
    QStyleOptionComboBox,
)

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_assignment import change_worker_assignment
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from ergotools.presentation.desktop.workplace_assignment_dialog import (
    WorkplaceAssignmentDialog,
)
from tests.test_optional_assessment_context import META, source_for

# Retain native Qt ownership until all test controls have been closed.
_APP = QApplication.instance() or QApplication([])
# Synthetic hierarchy uses two real stations and shifts, with no manufactured defaults.
STATION = StationKey("Plant", "Section", "Line", "ST01")
# The business date is injected explicitly; no date interpretation affects the tests.
DAY = date(2026, 10, 19)


def seed_workplace_source(tmp_path: Path, kind: AssessmentKind) -> Path:
    """Create a valid saved standalone assessment with real optional organization.

    Args:
        tmp_path: Pytest-owned destination directory.
        kind: Tool whose complete task/result bytes must survive association.

    Returns:
        Closed native project path containing A/B, two stations/shifts and one source.
        No Job or worker assignment is created as a fixture prerequisite.
    """
    path = tmp_path / "workplace.ergprj"
    hierarchy = WorkHierarchy(
        WorkCatalog(
            META.project_id,
            (WorkerEntry("A"), WorkerEntry("B")),
            (STATION, replace(STATION, station_id="ST02")),
            ("1", "2"),
        ),
        ("Plant",),
        (SectionKey("Plant", "Section"),),
        (LineKey("Plant", "Section", "Line"),),
    )
    with AssessmentProjectFile.create_empty(path, META) as project:
        project.save_hierarchy(hierarchy)
        key = DocumentKey(META.project_id, "source")
        source = source_for(kind)
        project.create_historical_assessment(
            AssignmentAssessment("source", None, kind, "A"),
            source,
            result=calculate_saved_result(key, source, META.default_units),
        )
    return path


def open_private(path: Path) -> ProjectWorkspace[AssessmentDraft]:
    """Open the synthetic source in the normal integrated private editing mode.

    Args:
        path: Disposable saved native project with source document source.

    Returns:
        Owned workspace; callers must close without leaking its private connection.
    """
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(path.parent / "settings.json"),
        unified_saving=True,
    )
    workspace.switch(str(path), "source")
    return workspace


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("with_job", (False, True))
def test_atomic_creation_association_replay_save_preserves_exact_data(
    tmp_path: Path, kind: AssessmentKind, with_job: bool
) -> None:
    """One Undo step owns the new assignment and source association for every tool.

    Args:
        tmp_path: Disposable project and preferences directory.
        kind: LiFFT, DUET or ST source/result model.
        with_job: Exercise both valid optional Job choices.

    Returns:
        None. Private mutation, Undo/Redo and Save/reopen retain exact source/results.
    """
    path = seed_workplace_source(tmp_path, kind)
    if with_job:
        with AssessmentProjectFile.open(path) as project:
            project.save_jobs(
                JobCatalog(
                    META.project_id,
                    (Job("J", "Job"),),
                    (JobPlacement(1, "J", STATION.at_shift("1")),),
                )
            )
    original_bytes = path.read_bytes()
    workspace = open_private(path)
    try:
        assert workspace.editing is not None
        repository = workspace._project
        connection = repository._connection
        before = {
            table: connection.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in ("draft_documents", "saved_assessment_results")
        }
        entry = workspace.associate_assessment_at_workplace(
            "source", STATION.at_shift("1"), 1 if with_job else None, effective_date=DAY
        )
        assert entry.document_id == "source" and entry.assignment_id is not None
        assert len(workspace.read_jobs().jobs.assignments) == 1
        assert workspace.plant_shift_count("Plant") == 1
        assert path.read_bytes() == original_bytes
        assert (
            workspace.editing is not None
            and workspace.editing.history.undo_label_key is not None
        )
        assert workspace.editing.replay(redo=False)
        assert workspace.editing.history.undo_label_key is None
        assert not workspace.read_jobs().jobs.assignments
        assert (
            workspace.read_history().history.standalone_for("A", kind).document_id
            == "source"
        )
        assert workspace.editing.replay(redo=True)
        assert (
            workspace.read_history()
            .history.current_for(entry.assignment_id, kind)
            .document_id
            == "source"
        )
        assert {
            table: connection.execute(f'SELECT * FROM "{table}"').fetchall()
            for table in before
        } == before
        assert workspace.save()
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(path) as project:
        assert (
            project.load_history().current_for(entry.assignment_id, kind).document_id
            == "source"
        )
        assert project.load_jobs().assignments[0].placement_id == (
            1 if with_job else None
        )
        assert (
            project.load_saved_result(DocumentKey(META.project_id, "source"))
            is not None
        )


def test_failed_association_rolls_back_new_assignment_and_history(
    tmp_path: Path,
) -> None:
    """A failure after inserting the assignment leaves no orphan relationship.

    Args:
        tmp_path: Disposable private SQLite project directory.

    Returns:
        None. The original standalone source/results and durable file stay exact.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    before = path.read_bytes()
    workspace = open_private(path)
    try:
        assert workspace.editing is not None
        repository = workspace._project
        connection = repository._connection
        connection.execute(
            "CREATE TRIGGER reject_association BEFORE UPDATE OF assignment_id "
            "ON assessment_ownership BEGIN "
            "SELECT RAISE(ABORT,'association failure'); END"
        )
        with pytest.raises(sqlite3.IntegrityError, match="association failure"):
            workspace.associate_assessment_at_workplace(
                "source", STATION.at_shift("1"), None, effective_date=DAY
            )
        connection.execute("DROP TRIGGER reject_association")
        assert not workspace.read_jobs().jobs.assignments
        assert (
            workspace.read_history().history.standalone_for("A", AssessmentKind.LIFFT)
            is not None
        )
        assert workspace.editing.history.undo_label_key is None
        assert path.read_bytes() == before
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize("language", list(Language))
def test_workplace_picker_filters_optional_jobs_and_locks_reused_owner(
    tmp_path: Path, language: Language
) -> None:
    """Hierarchy and shift lead selection; only compatible Jobs become optional choices.

    Args:
        tmp_path: Disposable native project directory.
        language: English/Spanish captions independent of literal saved identities.

    Returns:
        None. No Job is valid, shift changes filter choices, and reuse keeps the Job.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    with AssessmentProjectFile.open(path) as project:
        hierarchy = project.load_hierarchy()
    jobs = JobCatalog(
        META.project_id,
        (Job("J1", "First"), Job("J2", "Second")),
        (
            JobPlacement(1, "J1", STATION.at_shift("1")),
            JobPlacement(2, "J2", STATION.at_shift("2")),
        ),
    )
    dialog = WorkplaceAssignmentDialog(
        hierarchy, jobs, "A", load_icons(), language=language
    )
    try:
        assert not dialog.accept_button.isEnabled()
        dialog.select_workplace(STATION.at_shift("1"))
        assert dialog.job.count() == 2 and dialog.selected_placement_id is None
        assert dialog.accept_button.isEnabled()
        dialog.job.setCurrentIndex(dialog.job.findData(1))
        assert dialog.selected_placement_id == 1
        dialog.shift.setCurrentIndex(dialog.shift.findData("2"))
        assert dialog.selected_placement_id is None and dialog.job.findData(1) < 0
        assert dialog.job.findData(2) >= 0
        dialog.select_workplace(replace(STATION, station_id="ST02").at_shift("1"))
        assert dialog.job.count() == 1 and not dialog.job.isEnabled()
        dialog.accept_button.click()
        assert dialog.result() == QDialog.Accepted
    finally:
        dialog.close()
    owner = hierarchy.work.worker_context("A", STATION.at_shift("1"))
    jobs = replace(jobs, assignments=(WorkerJobAssignment(1, owner, 1),))
    dialog = WorkplaceAssignmentDialog(
        hierarchy, jobs, "A", load_icons(), language=language, reuse_existing=True
    )
    try:
        dialog.select_workplace(STATION.at_shift("1"))
        assert dialog.selected_placement_id == 1 and not dialog.job.isEnabled()
        assert dialog.accept_button.text() == (
            "Asociar evaluación"
            if language is Language.SPANISH
            else "Associate assessment"
        )
    finally:
        dialog.close()


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_main_associate_creates_workplace_without_worker_window(
    tmp_path: Path, language: Language, kind: AssessmentKind
) -> None:
    """Cancel is inert; accepting association directly creates the missing assignment.

    Args:
        tmp_path: Disposable native project and desktop preferences directory.
        language: Current English/Spanish application captions.
        kind: Each ergonomic tool has the same standalone-to-workplace workflow.

    Returns:
        None. A single main action retains the source identity and calculated output.
    """
    path = seed_workplace_source(tmp_path, kind)
    view = create_window(
        tmp_path / "desktop.json", original_navigation=True, enable_vtk=False
    )
    try:
        view.language = language
        view.open_project_location(str(path))
        workspace = view.presenter.workspace
        view.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        view.assessment_navigation.select(
            "A", kind, lambda: view._blank_kind(kind), explicit=True
        )
        view.refresh()
        source = workspace.active.document
        with patch.object(
            WorkplaceAssignmentDialog, "exec_", return_value=QDialog.Rejected
        ):
            view.main_navigation.associate_button.click()
        assert not workspace.read_jobs().jobs.assignments
        assert workspace.active.document == source

        def choose(dialog: WorkplaceAssignmentDialog) -> int:
            """Accept an actual station/shift with its valid No Job option.

            Args:
                dialog: Real picker opened by the main association action.

            Returns:
                Accepted native result after explicit workplace selection.
            """
            dialog.select_workplace(STATION.at_shift("1"))
            dialog.accept_button.click()
            return dialog.result()

        with patch.object(WorkplaceAssignmentDialog, "exec_", choose):
            view.main_navigation.associate_button.click()
        assert len(workspace.read_jobs().jobs.assignments) == 1
        assert workspace.active.document == source
        assert view.assessment_navigation.view.workplace == STATION.at_shift("1")
        assert workspace.read_history().history.standalone_for("A", kind) is None
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("with_job", (False, True))
def test_existing_assignment_is_reused_without_reclassification(
    tmp_path: Path, with_job: bool
) -> None:
    """Association reuses one existing active workplace owner without changing its Job.

    Args:
        tmp_path: Disposable native source directory.
        with_job: Exercise a workplace-only assignment and one with a real Job.

    Returns:
        None. A conflicting Job fails atomically; a matching selection keeps the row.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    with AssessmentProjectFile.open(path) as project:
        owner = project.load_hierarchy().work.worker_context("A", STATION.at_shift("1"))
        jobs = JobCatalog(
            META.project_id,
            (Job("J", "Job"),),
            (JobPlacement(1, "J", STATION.at_shift("1")),),
            (WorkerJobAssignment(7, owner, 1 if with_job else None),),
        )
        project.save_jobs(jobs)
    workspace = open_private(path)
    try:
        assert workspace.editing is not None
        with pytest.raises(ValueError, match="different Job"):
            workspace.associate_assessment_at_workplace(
                "source",
                STATION.at_shift("1"),
                None if with_job else 1,
                effective_date=DAY,
            )
        assert workspace.read_jobs().jobs == jobs
        assert workspace.editing.history.undo_label_key is None
        entry = workspace.associate_assessment_at_workplace(
            "source",
            STATION.at_shift("1"),
            1 if with_job else None,
            effective_date=DAY,
        )
        assert entry.assignment_id == 7
        assert workspace.read_jobs().jobs == jobs
        assert workspace.editing.replay(redo=False)
        assert workspace.read_jobs().jobs == jobs
        assert (
            workspace.read_history().history.standalone_for("A", AssessmentKind.LIFFT)
            is not None
        )
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_association_rejects_invalid_destinations_without_new_assignment(
    tmp_path: Path,
) -> None:
    """Missing workplace membership and mismatched Jobs cannot leave new assignments.

    Args:
        tmp_path: Disposable real SQLite source/result project.

    Returns:
        None. Rejection preserves source ownership and the shared history boundary.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    workspace = open_private(path)
    try:
        assert workspace.editing is not None
        for workplace, placement in (
            (replace(STATION, station_id="missing").at_shift("1"), None),
            (STATION.at_shift("missing"), None),
            (STATION.at_shift("1"), 999),
        ):
            with pytest.raises((ValueError, KeyError)):
                workspace.associate_assessment_at_workplace(
                    "source", workplace, placement, effective_date=DAY
                )
            assert not workspace.read_jobs().jobs.assignments
            assert workspace.editing.history.undo_label_key is None
            assert (
                workspace.read_history().history.standalone_for(
                    "A", AssessmentKind.LIFFT
                )
                is not None
            )
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_main_association_departure_cancel_creates_no_assignment(
    tmp_path: Path,
) -> None:
    """A departure cancellation after picker acceptance remains an inert operation.

    Args:
        tmp_path: Disposable source and desktop preferences directory.

    Returns:
        None. The standalone source and durable file are unchanged after cancellation.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    before = path.read_bytes()
    view = create_window(
        tmp_path / "cancel.json", original_navigation=True, enable_vtk=False
    )
    try:
        view.open_project_location(str(path))
        workspace = view.presenter.workspace
        source = workspace.active.document

        def choose(dialog: WorkplaceAssignmentDialog) -> int:
            """Select a valid workplace before the separate departure decision.

            Args:
                dialog: Real immutable-context picker opened by the main action.

            Returns:
                Accepted selection; this alone must never write a relationship.
            """
            dialog.select_workplace(STATION.at_shift("1"))
            return QDialog.Accepted

        with (
            patch.object(WorkplaceAssignmentDialog, "exec_", choose),
            patch.object(view, "browse_choice", return_value=CloseChoice.CANCEL),
        ):
            view.main_navigation.associate_button.click()
        assert not workspace.read_jobs().jobs.assignments
        assert workspace.active.document == source
        assert (
            workspace.read_history().history.standalone_for("A", AssessmentKind.LIFFT)
            is not None
        )
        assert path.read_bytes() == before
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        view.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("station_id", ("ST01", "ST02"))
def test_change_workplace_can_explicitly_choose_no_job(
    tmp_path: Path, station_id: str
) -> None:
    """Changing to No Job preserves the historical row and accepts a real destination.

    Args:
        tmp_path: Disposable hierarchy fixture directory.
        station_id: Existing station or another real station in the same line.

    Returns:
        None. A successor remains active and the original Job owner stays historical.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    with AssessmentProjectFile.open(path) as project:
        owner = project.load_hierarchy().work.worker_context("A", STATION.at_shift("1"))
    jobs = JobCatalog(
        META.project_id,
        (Job("J", "Job"),),
        (JobPlacement(1, "J", STATION.at_shift("1")),),
        (WorkerJobAssignment(7, owner, 1),),
    )
    destination = replace(STATION, station_id=station_id).at_shift("1")
    change = change_worker_assignment(
        jobs,
        "A",
        7,
        None,
        workplace=destination,
        effective_date=DAY,
        new_assignment_id=8,
    )
    old, new = change.jobs.assignments
    assert not old.active and old.placement_id == 1 and old.worker == owner
    assert new.active and new.placement_id is None
    assert new.worker.workplace == destination and change.assignment_id == 8
    assert jobs.assignments[0].active


def seed_assignment_table(tmp_path: Path, scenario: str) -> Path:
    """Create realistic compact, long-label or many-row workplace table data.

    Args:
        tmp_path: Disposable project directory; maintained projects are never written.
        scenario: short, long or many controls label lengths and active assignments.

    Returns:
        Closed standalone-assessment project with eligible optional Job choices and
        saved workplace rows; the long choice is deliberately not selected initially.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    long = scenario == "long"
    station = StationKey(
        "Workflow Plant with a complete descriptive name" if long else "Workflow Plant",
        "Packing section with a complete descriptive name" if long else "Packing",
        "Production line with a complete descriptive name" if long else "Line A",
        "ST01",
    )
    stations = tuple(
        replace(station, station_id=f"ST{index + 1:02}")
        for index in range(35 if scenario == "many" else 1)
    )
    with AssessmentProjectFile.open(path) as project:
        previous = project.load_hierarchy()
        hierarchy = WorkHierarchy(
            WorkCatalog(META.project_id, previous.work.workers, stations, ("1",)),
            (station.plant_name,),
            (SectionKey(station.plant_name, station.section_name),),
            (LineKey(station.plant_name, station.section_name, station.line_name),),
        )
        project.save_hierarchy(hierarchy)
        jobs = JobCatalog(
            META.project_id,
            (
                Job("J", "Packing"),
                Job(
                    "LONG",
                    "An optional Job with its full descriptive name visible"
                    if long
                    else "Other",
                ),
            ),
            (
                JobPlacement(1, "J", station.at_shift("1")),
                JobPlacement(2, "LONG", station.at_shift("1")),
            ),
            tuple(
                WorkerJobAssignment(
                    index + 1,
                    hierarchy.work.worker_context("A", item.at_shift("1")),
                    None,
                )
                for index, item in enumerate(stations)
            ),
        )
        project.save_jobs(jobs)
    return path


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("scenario", ("short", "long", "many"))
def test_assignment_table_fits_full_values_and_scrolls_only_when_needed(
    tmp_path: Path, language: Language, scenario: str
) -> None:
    """Full labels and optional Job choices remain readable without inflating stations.

    Args:
        tmp_path: Disposable private project directory.
        language: English/Spanish headers and No Job caption.
        scenario: Compact, wide or vertically overflowing assignment population.

    Returns:
        None. Headers/data/options fit, scrolling follows overflow and layout is clean.
    """
    path = seed_assignment_table(tmp_path, scenario)
    before = path.read_bytes()
    workspace = open_private(path)
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, language=language
    )
    try:
        dialog.resize(1360, 760)
        dialog.tabs.setCurrentIndex(1)
        dialog.show()
        _APP.processEvents()
        QTest.qWait(20)
        table = dialog.assignment_table
        header = table.horizontalHeader()
        assert header is not None
        for column in range(7):
            assert table.columnWidth(column) >= header.sectionSizeHint(column)
        for row in range(table.rowCount()):
            for column in range(5):
                item = table.item(row, column)
                assert item is not None
                assert table.columnWidth(
                    column
                ) >= table.fontMetrics().horizontalAdvance(item.text())
        combo = table.cellWidget(0, 5)
        assert isinstance(combo, QComboBox)
        assert table.columnWidth(5) >= combo.sizeHint().width()
        option = QStyleOptionComboBox()
        combo.initStyleOption(option)
        field = combo.style().subControlRect(
            QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxEditField, combo
        )
        assert field.width() >= max(
            combo.fontMetrics().horizontalAdvance(combo.itemText(i))
            for i in range(combo.count())
        )
        assert table.columnWidth(0) > table.columnWidth(3)
        horizontal_overflow = sum(table.columnWidth(c) for c in range(7)) > (
            table.viewport().width()
        )
        assert table.horizontalScrollBar().isVisible() == horizontal_overflow
        if not horizontal_overflow:
            assert (
                sum(table.columnWidth(c) for c in range(7)) == table.viewport().width()
            )
            assert combo.width() > 150
        actions = table.cellWidget(0, 6)
        assert actions is not None
        buttons = actions.findChildren(QPushButton)
        assert len(buttons) == 2
        assert all(actions.rect().contains(button.geometry()) for button in buttons)
        original_station_width = table.columnWidth(3)
        original_job_width = table.columnWidth(5)
        dialog.resize(1800, 900)
        QTest.qWait(30)
        if scenario != "long":
            assert (
                sum(table.columnWidth(c) for c in range(7)) == table.viewport().width()
            )
            assert table.columnWidth(5) > original_job_width
            assert table.columnWidth(3) == original_station_width
        dialog.resize(1360, 760)
        QTest.qWait(30)
        assert not dialog._assignment_fit_timer.isActive()
        if scenario == "long":
            assert horizontal_overflow
        elif language is Language.ENGLISH:
            assert not horizontal_overflow
        assert table.verticalScrollBar().isVisible() == (scenario == "many")
        if scenario == "long":
            table.horizontalScrollBar().setValue(table.horizontalScrollBar().maximum())
            _APP.processEvents()
            assert header.sectionViewportPosition(6) >= 0
            assert header.sectionViewportPosition(6) + table.columnWidth(6) <= (
                table.viewport().width()
            )
        if scenario == "many":
            table.scrollToBottom()
            _APP.processEvents()
            assert table.visualItemRect(
                table.item(table.rowCount() - 1, 0)
            ).bottom() <= (table.viewport().height())
        assert not workspace.editing.is_dirty
        assert path.read_bytes() == before
        if scenario == "long":
            dialog.new_worker()
            dialog.tabs.setCurrentIndex(1)
            _APP.processEvents()
            QTest.qWait(20)
            assert table.rowCount() == 0
            assert not table.horizontalScrollBar().isVisible()
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
def test_empty_assignment_table_keeps_headers_and_usable_job_width(
    tmp_path: Path, language: Language
) -> None:
    """An empty worker has readable headers and a useful Job column without scrolling.

    Args:
        tmp_path: Disposable standalone worker project directory.
        language: English/Spanish table headers.

    Returns:
        None. Empty rendering adds no project edit or unnecessary scrollbars.
    """
    path = seed_workplace_source(tmp_path, AssessmentKind.LIFFT)
    workspace = open_private(path)
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, language=language
    )
    try:
        dialog.tabs.setCurrentIndex(1)
        dialog.show()
        _APP.processEvents()
        QTest.qWait(20)
        table = dialog.assignment_table
        header = table.horizontalHeader()
        assert header is not None and table.rowCount() == 0
        assert all(table.columnWidth(c) >= header.sectionSizeHint(c) for c in range(7))
        assert sum(table.columnWidth(c) for c in range(7)) == table.viewport().width()
        assert table.columnWidth(5) > 100
        assert not table.horizontalScrollBar().isVisible()
        assert not table.verticalScrollBar().isVisible()
        assert not workspace.editing.is_dirty
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
def test_assignment_tooltips_follow_cell_and_optional_job_choice(
    tmp_path: Path, language: Language
) -> None:
    """Headers, data cells, Job drafts and row actions provide distinct local help.

    Args:
        tmp_path: Disposable native project and preferences directory.
        language: English/Spanish interface; workplace and Job values stay literal.

    Returns:
        None. Blank table space has no misleading Job tooltip and hover help tracks
        the displayed Job selection without changing saved project data.
    """
    path = seed_assignment_table(tmp_path, "short")
    before = path.read_bytes()
    workspace = open_private(path)
    dialog = WorkerManagementDialog(
        workspace, load_icons(), MeasurementSystem.METRIC, language=language
    )
    try:
        dialog.tabs.setCurrentIndex(1)
        dialog.show()
        QTest.qWait(30)
        table = dialog.assignment_table
        assert table.toolTip() == ""
        descriptions = [table.horizontalHeaderItem(c).toolTip() for c in range(7)]
        assert len(set(descriptions)) == 7 and all(descriptions)
        for column in range(5):
            cell = table.item(0, column)
            assert cell is not None
            assert cell.toolTip() == (
                f"{table.horizontalHeaderItem(column).text()}: {cell.text()}"
            )
        combo = table.cellWidget(0, 5)
        assert isinstance(combo, QComboBox)
        assert combo.currentText() in combo.toolTip()
        previous = combo.toolTip()
        combo.setCurrentIndex(combo.findData(1))
        assert combo.currentText() in combo.toolTip() and combo.toolTip() != previous
        actions = table.cellWidget(0, 6)
        assert actions is not None and actions.toolTip() == descriptions[6]
        buttons = actions.findChildren(QPushButton)
        assert {button.toolTip() for button in buttons} == (
            {"Cambiar asignación", "Quitar asignación"}
            if language is Language.SPANISH
            else {"Change assignment", "Remove assignment"}
        )
        combo.setCurrentIndex(combo.findData(None))
        assert path.read_bytes() == before
        assert not workspace.editing.is_dirty
    finally:
        dialog.close()
        workspace.close(choice=CloseChoice.DISCARD)
        dialog.deleteLater()
        _APP.processEvents()
