"""Assessment-local capacity, unused rows and reversible counts across all three tools.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QComboBox

from ergotools.application.assessments.duet_commands import SetDuetTaskCount
from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.assessments.lifft_commands import SetLifftTaskCount
from ergotools.application.assessments.tst_commands import SetTstTaskCount
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.bootstrap import create_window
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from ergotools.presentation.localization import Language, Translator
from tests.test_saved_tool_data import window as ownership_fixture

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Create small populated sources; the ST source deliberately uses metric units.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    view = create_window(tmp_path / "preferences.json", original_navigation=True)
    workspace = view.presenter.workspace
    workspace.create(
        str(tmp_path / "counts.ergprj"),
        ProjectMetadata("p", "Counts", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("l", 12, 20, 100),)),
    )
    workspace.create_assessment("duet", DuetDraft((DuetTask("d", 6, 100),)))
    workspace.create_assessment(
        "st",
        TstDraft(
            MeasurementSystem.METRIC,
            (TstTask("s", TstDirection.HORIZONTAL, 30, 40, 50),),
        ),
    )
    view.refresh()
    view.show()
    QTest.qWait(30)
    yield view
    workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


@pytest.mark.parametrize("index", [1, 2])
def test_modal_cancel_accept_undo_redo_and_save(
    window: LifftWindow, index: int
) -> None:
    """Cancel retains text; growth preserves rows and saved tools stay independent.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.secondary_panel()
    presenter = panel.presenter
    active = window.presenter.workspace.active
    source = active.state
    other_sources = {
        e.document.document_id: e.task_count
        for e in window.presenter.workspace.list_assessments()
    }
    # Cancel preserves invalid typing; resize Apply later uses valid repetitions.
    field = panel.inputs[0][-1]
    field.setText("invalid")
    field.textEdited.emit("invalid")
    action = window.main_navigation.toolbar_actions["settings"]
    assert action.isEnabled()

    def cancel() -> None:
        """Check the active assessment count, type 100 and Cancel the actual modal.

        Check the active assessment count, type 100 and Cancel the actual modal without
        resetting any source.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, PreferencesDialog) and modal.parent() is window
        assert modal.count.value() == len(source.tasks)
        modal.count.setValue(100)
        modal.cancel_button.click()

    QTimer.singleShot(0, cancel)
    action.trigger()
    assert active.state is source and panel.inputs[0][-1] is field
    assert panel.pending and field.text() == "invalid"
    field.setText(str(source.tasks[0].repetitions))
    field.textEdited.emit(field.text())
    panel.commit_inputs()
    # Check growth through actual modal acceptance and exact Undo.
    for count in (2, 100):

        def accept(count: int = count) -> None:
            """Set the parametrized count in the actual owned modal.

            Set the parametrized count in the actual owned modal and accept one
            reversible source resize.

            Args:
                count: Accepted task-count case or deliberately invalid boundary
                    replacement.

            Returns:
                None.
            """
            modal = QApplication.activeModalWidget()
            assert isinstance(modal, PreferencesDialog)
            modal.count.setValue(count)
            modal.reset_tasks.setChecked(True)
            modal.apply_button.click()

        with patch.object(
            window,
            "confirm_task_reset",
            return_value=True,
        ):
            QTimer.singleShot(0, accept)
            action.trigger()
        changed = active.state
        assert (
            len(changed.tasks) == count
            and len(panel.inputs) == count
            and not panel.pending
        )
        assert len(set(t.task_id for t in changed.tasks)) == count
        assert changed.tasks[: len(source.tasks)] == source.tasks
        assert all(t.repetitions is None for t in changed.tasks[len(source.tasks) :])
        if isinstance(changed, TstDraft):
            assert changed.system is MeasurementSystem.METRIC
            assert all(
                t.direction is TstDirection.HANDLING_LOADS
                and t.load is None
                and t.lever_arm is None
                for t in changed.tasks[len(source.tasks) :]
            )
        else:
            assert all(
                t.omni_res_scale == 0 for t in changed.tasks[len(source.tasks) :]
            )
        assert not window.results_sidebar.risk_gauge.has_value
        assert presenter.evaluator.current(active) is None
        active.undo()
        window.refresh()
        assert active.state is source
        active.redo()
        window.refresh()
        assert active.state is changed
        window.navigation_action(window.save_project)
        with AssessmentProjectFile.open(
            Path(window.presenter.workspace.location)
        ) as project:
            assert project.load(active.document) == changed
            for e in project.list_assessments():
                if e.document != active.document:
                    assert e.task_count == other_sources[e.document.document_id]
        active.undo()
        window.refresh()
        assert active.state is source
    QTest.qWait(30)
    # A 100-row rebuild can consume the first event pump before its queued sync.
    for _ in range(100):
        if not panel.task_grid.geometry_pending:
            break
        QTest.qWait(10)
    assert not panel.task_grid.geometry_pending
    for c, header in enumerate(panel.headers):
        assert header.width() == panel.grid.itemAtPosition(1, c).widget().width()


@pytest.mark.parametrize("index", [1, 2])
def test_equal_count_preserves_data_without_confirmation(
    window: LifftWindow, index: int
) -> None:
    """Equal count preserves source and history; Settings uses the chosen language.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    window.language = Language.SPANISH
    window.translate()
    window.refresh()
    active = window.presenter.workspace.active
    before = active.state

    def accept() -> None:
        """Check the Spanish unified-settings title.

        Check the Spanish unified-settings title and accept the existing row count to
        preserve its populated inputs.

        Args:
            None.

        Returns:
            None.
        """
        modal = QApplication.activeModalWidget()
        assert isinstance(modal, PreferencesDialog)
        assert modal.windowTitle() == "Configuración"
        modal.count.setValue(len(before.tasks))
        modal.reset_tasks.setChecked(True)
        modal.apply_button.click()

    with patch.object(
        window,
        "confirm_task_reset",
        return_value=True,
    ) as info:
        QTimer.singleShot(0, accept)
        window.main_navigation.toolbar_actions["settings"].trigger()
    assert active.state is before
    info.assert_not_called()
    assert (
        Translator(Language.SPANISH)
        .text("edit.duet.task_count" if index == 1 else "edit.tst.task_count")
        .startswith("Establecer")
    )


@pytest.mark.parametrize("kind", ["duet", "st"])
def test_task_count_validation_is_atomic(window: LifftWindow, kind: str) -> None:
    """Out-of-range counts, populated replacements, duplicates and stale source fail.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        kind: Explicit tool identity or deliberately invalid tool value selected by this
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(1 if kind == "duet" else 2)
    presenter = window.secondary_panel().presenter
    source = presenter.source()
    for count in (0, 101, True):
        with pytest.raises(DraftError):
            presenter.set_task_count(count)
        assert presenter.source() is source
    if kind == "duet":
        command = SetDuetTaskCount
        blank = DuetTask("x", 0)
        empty = DuetDraft()
    else:
        command = SetTstTaskCount
        blank = TstTask("x", TstDirection.HANDLING_LOADS)
        empty = TstDraft(source.system)
    key = DocumentKey("p", kind)
    for rows in ((), (blank,), (blank, blank)):
        with pytest.raises(DraftError):
            command(key, source, rows).apply(source)
    with pytest.raises(DraftError):
        command(key, empty, (blank,)).apply(source)
    window.presenter.workspace.close()
    assert presenter.set_task_count(3) is None
    with pytest.raises(DraftError):
        presenter.set_task_count(0)


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("system", list(MeasurementSystem))
@pytest.mark.parametrize("count", [10, 15, 20])
def test_populated_prefix_resize_and_exact_history(
    index: int, system: MeasurementSystem, count: int
) -> None:
    """All tools preserve retained IDs/values, with exact Undo/Redo and no-op history.

    Args:
        index: LiFFT, DUET or ST source/command selection.
        system: Canonical source units; resizing must never reinterpret quantities.
        count: Shrink, equal-count or growth case starting with fifteen full tasks.

    Returns:
        None; complete immutable sources and history revisions are compared exactly.
    """
    sources = (
        LifftDraft(
            system, tuple(LifftTask(str(i), 30 + i, 49.05, 100 + i) for i in range(15))
        ),
        DuetDraft(tuple(DuetTask(str(i), 6, 100 + i) for i in range(15))),
        TstDraft(
            system,
            tuple(
                TstTask(str(i), TstDirection.HORIZONTAL, 30 + i, 49.05, 100 + i)
                for i in range(15)
            ),
        ),
    )
    source = sources[index]
    blank = (
        tuple(LifftTask(f"new{i}") for i in range(5)),
        tuple(DuetTask(f"new{i}", 0) for i in range(5)),
        tuple(TstTask(f"new{i}", TstDirection.HANDLING_LOADS) for i in range(5)),
    )[index]
    key = DocumentKey("resize", str(index))
    session = DocumentSession(key, source, persisted=True)
    command = (SetLifftTaskCount, SetDuetTaskCount, SetTstTaskCount)[index]
    tasks = source.tasks[:count] + (blank if count > 15 else ())
    revision = session.revision
    session.execute(command(key, source, tasks))
    after = session.state
    assert after.tasks[: min(15, count)] == source.tasks[: min(15, count)]
    assert len(after.tasks) == count
    if count == 15:
        assert session.revision == revision and not session.is_dirty
    else:
        session.undo()
        assert session.state == source
        session.redo()
        assert session.state == after
    with pytest.raises(DraftError):
        command(key, source, (blank[0],)).apply(source)


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("system", list(MeasurementSystem))
def test_unused_slots_do_not_make_entered_assessment_partial(
    index: int, system: MeasurementSystem
) -> None:
    """Unused holes preserve source/order and numerics; started rows remain validated.

    Args:
        index: LiFFT, DUET or ST calculator/grid selection.
        system: Metric/imperial source convention; DUET remains unit-independent.

    Returns:
        None; strict APIs stay strict, grid summaries match one-row calculation and
        missing-field issues refer only to started rows, including entered zero.
    """
    sources = (
        LifftDraft(system, (LifftTask("used", 30, 49.05, 100),)),
        DuetDraft((DuetTask("used", 6, 100),)),
        TstDraft(system, (TstTask("used", TstDirection.HORIZONTAL, 30, 49.05, 100),)),
    )
    blank = (
        LifftTask("blank"),
        DuetTask("blank", 0),
        TstTask("blank", TstDirection.HANDLING_LOADS),
    )[index]
    entered = (
        LifftTask("started", 0),
        DuetTask("started", 6),
        TstTask("started", TstDirection.HANDLING_LOADS, 0),
    )[index]
    source = sources[index]
    evaluator = AssessmentEvaluator()
    method = (
        evaluator.evaluate_lifft_grid,
        evaluator.evaluate_duet_grid,
        evaluator.evaluate_tst_grid,
    )[index]
    key = DocumentKey("unused", str(index))
    reference = method(DocumentSession(key, source)).summary
    holes = replace(source, tasks=(blank, source.tasks[0]))
    session = DocumentSession(key, holes, persisted=True)
    assert evaluator.evaluate(session).status is EvaluationStatus.INVALID_INPUT
    result = method(session)
    assert result.status is EvaluationStatus.COMPLETE and not result.issues
    assert result.summary.total_damage == reference.total_damage
    assert result.summary.probability == reference.probability
    assert len(result.task_results) == 2
    assert session.state is holes and not session.is_dirty
    partial = method(
        DocumentSession(key, replace(holes, tasks=(*holes.tasks, entered)))
    )
    assert partial.status is EvaluationStatus.PARTIAL
    assert partial.issues and {issue.task_id for issue in partial.issues} == {"started"}
    empty = method(DocumentSession(key, replace(source, tasks=(blank,))))
    assert empty.status is not EvaluationStatus.COMPLETE
    assert empty.summary.probability is None


@pytest.mark.parametrize("index", [0, 1, 2])
def test_pending_invalid_text_blocks_resize_without_discard(
    window: LifftWindow, index: int
) -> None:
    """Settings count Apply cannot erase invalid text or change source/preferences.

    Args:
        window: Disposable integrated three-tool project with a populated first task.
        index: Active tool whose pending repetitions are deliberately invalid.

    Returns:
        None; owned dialog acceptance reaches normal validation, retaining retry text.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("invalid")
    field.textEdited.emit("invalid")
    before = window.presenter.workspace.active.state
    settings = window._settings_store.load()

    def apply() -> None:
        """Accept a larger count; invalid retained text must prevent its application.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        dialog.reset_tasks.setChecked(True)
        dialog.count.setValue(20)
        dialog.accept()

    QTimer.singleShot(0, apply)
    with pytest.raises(DraftError):
        window.open_preferences()
    assert window.presenter.workspace.active.state is before
    assert field.text() == "invalid" and panel.pending
    assert window._settings_store.load() == settings
    field.setText(str(before.tasks[0].repetitions))
    field.textEdited.emit(field.text())
    panel.commit_inputs()


@pytest.mark.parametrize("index", [0, 1, 2])
def test_resize_shared_history_restores_truncated_rows_and_result(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Fifteen populated rows survive shared Undo after truncation and Save/reopen.

    Args:
        window: Disposable integrated desktop with shared project history enabled.
        tmp_path: Only project destination used by this regression.
        index: LiFFT, DUET or ST assessment with fifteen populated task rows.

    Returns:
        None; main Save, exact saved result, retained source and replay are checked.
    """
    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    system = MeasurementSystem.METRIC
    source = (
        LifftDraft(
            system, tuple(LifftTask(str(i), 30 + i, 49.05, 100 + i) for i in range(15))
        ),
        DuetDraft(tuple(DuetTask(str(i), 6, 100 + i) for i in range(15))),
        TstDraft(
            system,
            tuple(
                TstTask(str(i), TstDirection.HORIZONTAL, 30 + i, 49.05, 100 + i)
                for i in range(15)
            ),
        ),
    )[index]
    path = tmp_path / "retained.ergprj"
    workspace.create(
        str(path), ProjectMetadata("retained", "Retained", system), "assessment", source
    )
    window.refresh()
    window.assessment_tabs.setCurrentIndex(index)
    window.refresh()
    window.calculate()
    window.save_project()
    key = workspace.active.document
    before_file = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        original_result = project.load_saved_result(key)
    assert original_result is not None
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(10)
    window.refresh()
    assert workspace.active.state.tasks == source.tasks[:10]
    assert path.read_bytes() == before_file
    editing = workspace.editing
    assert editing.replay(redo=False)
    assert workspace.active.state == source
    assert workspace.historical_result() == original_result
    assert editing.replay(redo=True)
    assert workspace.active.state.tasks == source.tasks[:10]
    window.calculate()
    window.save_project()
    with AssessmentProjectFile.open(path) as project:
        assert project.load(key).tasks == source.tasks[:10]
        assert (
            project.load_saved_result(key).calculation_status
            is EvaluationStatus.COMPLETE
        )
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    assert workspace.active.state.tasks == source.tasks[:10]


@pytest.mark.parametrize("index", [0, 1, 2])
def test_trailing_pending_data_requires_consent_and_cancel_keeps_text(
    window: LifftWindow, index: int
) -> None:
    """Consent detects unaccepted tail text; Cancel cannot alter source or preferences.

    Args:
        window: Disposable three-tool integrated desktop.
        index: Active tool with one saved row and a newly entered trailing row.

    Returns:
        None; cancellation retains the exact editor, text and unchanged source.
    """
    window.assessment_tabs.setCurrentIndex(index)
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(3)
    window.refresh()
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[2][2 if index == 0 else -1]
    field.setText("invalid tail")
    field.textEdited.emit(field.text())
    source = window.presenter.workspace.active.state
    settings = window._settings_store.load()
    assert window.task_count_removes_data(1)

    def apply() -> None:
        """Request a shrink without accepting any pending task input first.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        dialog.reset_tasks.setChecked(True)
        dialog.count.setValue(1)
        dialog.accept()

    with patch.object(window, "confirm_task_reset", return_value=False) as consent:
        QTimer.singleShot(0, apply)
        window.open_preferences()
        consent.assert_called_once_with(window.language, 1)
    assert window.presenter.workspace.active.state is source
    assert field.text() == "invalid tail" and panel.pending
    assert window._settings_store.load() == settings
    field.clear()
    field.textEdited.emit("")
    panel.commit_inputs()


@pytest.fixture
def ownership_window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Reuse the maintained real worker/assignment fixture for count isolation.

    Args:
        tmp_path: Pytest-owned project/settings directory.

    Yields:
        Existing integration fixture's window; its generator owns all cleanup.
    """
    yield from ownership_fixture.__wrapped__(tmp_path)


@pytest.mark.parametrize("index", [0, 1, 2])
def test_worker_tool_context_counts_save_independently(
    ownership_window: LifftWindow, index: int
) -> None:
    """Resizing one assignment/tool never changes other workers/tools/contexts.

    Args:
        ownership_window: Disposable real ownership fixture with two workers and
            multiple assignments/tools, all initially saved.
        index: LiFFT, DUET or ST to resize within the selected worker assignment.

    Returns:
        None; Settings context, retained data, all other saved sources and reopen
        ownership/count are checked through the application and native repository.
    """
    view = ownership_window
    workspace = view.presenter.workspace
    path = Path(workspace.location)
    view.assessment_tabs.setCurrentIndex(index)
    view.assessment_navigation.adopt_active()
    position = view.assessment_navigation.view
    key = workspace.active.document
    source = workspace.active.state
    with AssessmentProjectFile.open(path) as project:
        before = {
            entry.document: project.load(entry.document)
            for entry in project.list_assessments()
        }
    label = view.task_count_context()
    assert position.worker_id in label
    assert position.workplace.station_id in label
    assert workspace.project_metadata.title in label
    if position.job is not None:
        assert position.job[0] in label

    def apply() -> None:
        """Check actual Settings identity and accept growth for only that source.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        assert dialog.assessment_context_label.text() == label
        dialog.reset_tasks.setChecked(True)
        dialog.count.setValue(20)
        dialog.accept()

    with patch.object(view, "confirm_task_reset") as consent:
        QTimer.singleShot(0, apply)
        view.open_preferences()
        consent.assert_not_called()
    assert workspace.active.document == key
    assert workspace.active.state.tasks[: len(source.tasks)] == source.tasks
    view.save_project()
    with AssessmentProjectFile.open(path) as project:
        assert len(project.load(key).tasks) == 20
        for other_key, other_source in before.items():
            if other_key != key:
                assert project.load(other_key) == other_source
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    assert len(workspace.active.state.tasks) == 20
    assert workspace.active.state.tasks[: len(source.tasks)] == source.tasks


@pytest.mark.parametrize("index", [0, 1, 2])
def test_same_worker_no_job_station_counts_remain_independent(
    ownership_window: LifftWindow, index: int
) -> None:
    """Two no-Job stations in one shift retain independent counts for one worker.

    Args:
        ownership_window: Disposable project with real workers, stations and history.
        index: Active LiFFT, DUET or ST tool whose two new workplace sources differ.

    Returns:
        None; both counts, retained inputs, complete saved results and nullable Job
        classification are verified without changing pre-existing assessments.
    """
    from ergotools.domain.job_catalog import WorkerJobAssignment
    from ergotools.domain.work_catalog import StationKey

    view = ownership_window
    workspace = view.presenter.workspace
    view.assessment_tabs.setCurrentIndex(index)
    view.assessment_navigation.adopt_active()
    position = view.assessment_navigation.view
    parent = position.workplace
    hierarchy = workspace.read_hierarchy()
    stations = tuple(
        StationKey(parent.plant_name, parent.section_name, parent.line_name, str(i))
        for i in (2, 3)
    )
    proposed = replace(
        hierarchy.hierarchy,
        work=replace(
            hierarchy.hierarchy.work,
            stations=(*hierarchy.hierarchy.work.stations, *stations),
        ),
    )
    workspace.replace_hierarchy(hierarchy, proposed)
    jobs = workspace.read_jobs()
    assignments = tuple(
        WorkerJobAssignment(
            i,
            proposed.work.worker_context(
                position.worker_id, station.at_shift(parent.shift_id)
            ),
            None,
        )
        for i, station in zip((4, 5), stations, strict=True)
    )
    workspace.replace_jobs(
        jobs, replace(jobs.jobs, assignments=(*jobs.jobs.assignments, *assignments))
    )
    path = Path(workspace.location)
    with AssessmentProjectFile.open(path) as project:
        before = {
            e.document: project.load(e.document) for e in project.list_assessments()
        }
    saved = []
    for assignment, count in zip(assignments, (5, 10), strict=True):
        blank = view._blank_kind(position.kind)
        first = blank.tasks[0]
        populated = (
            replace(first, omni_res_scale=6, repetitions=100)
            if index == 1
            else replace(first, lever_arm=12, load=20, repetitions=100)
        )
        source = replace(blank, tasks=(populated, *blank.tasks[1:]))
        view.assessment_navigation.select(
            position.worker_id,
            position.kind,
            lambda source=source: source,
            workplace=assignment.worker.workplace,
            explicit=True,
            assignment_id=assignment.assignment_id,
        )
        view.refresh()
        presenter = (view.presenter, view.duet_presenter, view.tst_presenter)[index]
        presenter.set_task_count(count)
        view.refresh()
        assert "No Job" in view.task_count_context()
        assert assignment.worker.workplace.station_id in view.task_count_context()
        view.calculate()
        view.save_project()
        saved.append((workspace.active.document, count, populated))
    with AssessmentProjectFile.open(path) as project:
        for key, count, first in saved:
            assert len(project.load(key).tasks) == count
            assert project.load(key).tasks[0] == first
            assert (
                project.load_saved_result(key).calculation_status
                is EvaluationStatus.COMPLETE
            )
        for key, source in before.items():
            assert project.load(key) == source
        assert all(
            a.placement_id is None
            for a in project.load_jobs().assignments
            if a.assignment_id in (4, 5)
        )


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
@pytest.mark.parametrize("system", list(MeasurementSystem))
def test_pending_task_input_shared_undo_before_calculate(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    language: Language,
    system: MeasurementSystem,
) -> None:
    """A reopened calculated grid exposes pending edits without another Calculate.

    Args:
        window: Disposable integrated desktop, with real main toolbar controls.
        tmp_path: Private native file destination; owner fixtures remain untouched.
        index: LiFFT, DUET or ST grid; all have fifteen rows and one populated row.
        language: Main history labels and controls use English or Spanish.
        system: Metric or imperial source/display interpretation.

    Returns:
        None; immediate availability, mouse replay, exact result recovery, invalid
        input interlock, retained Redo and durable Save/reopen are checked.
    """
    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    source = (
        LifftDraft(system, (LifftTask("first", 30, 49.05, 100),)),
        DuetDraft((DuetTask("first", 6, 100),)),
        TstDraft(system, (TstTask("first", TstDirection.HORIZONTAL, 30, 49.05, 100),)),
    )[index]
    path = tmp_path / "pending-grid.ergprj"
    workspace.create(
        str(path), ProjectMetadata("pending", "Pending", system), "assessment", source
    )
    window.language = language
    window.assessment_tabs.setCurrentIndex(index)
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(15)
    window.refresh()
    window.calculate()
    window.save_project()
    key = workspace.active.document
    original = workspace.active.state
    calculated = workspace.historical_result()
    assert calculated is not None
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    window.refresh()
    editing = workspace.editing
    history = window.history_actions
    assert editing is not None and history.shared is not None
    assert editing.history.undo_label_key is None
    toolbar = window.main_navigation
    undo = toolbar.toolbar.widgetForAction(toolbar.toolbar_actions["undo"])
    redo = toolbar.toolbar.widgetForAction(toolbar.toolbar_actions["redo"])
    assert not undo.isEnabled()
    before_file = path.read_bytes()
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[1][0 if index == 0 else -1]
    field.setFocus()
    QTest.keyClicks(field, "25")
    assert panel.pending and panel.pending_change() is True
    assert undo.isEnabled() and not redo.isEnabled()
    # Availability inspection has not accepted a source, truncated history or saved.
    assert editing.history.undo_label_key is None
    assert workspace.active.state == original
    assert path.read_bytes() == before_file
    QTest.mouseClick(undo, Qt.MouseButton.LeftButton)
    assert workspace.active.state == original
    assert workspace.historical_result() == calculated
    assert not (window.secondary_panel() or window.task_panel).pending
    assert redo.isEnabled()
    QTest.mouseClick(redo, Qt.MouseButton.LeftButton)
    edited = workspace.active.state
    assert edited != original
    oracle = calculate_saved_result(
        workspace.active.document, edited, window.presenter.system
    )
    expected_result = (
        oracle
        if oracle and oracle.calculation_status is EvaluationStatus.COMPLETE
        else None
    )
    assert workspace.historical_result() == expected_result
    assert path.read_bytes() == before_file
    # Invalid text preserves the accepted state and cursor, including an existing
    # Redo branch. Keyboard editing remains local to the focused text editor.
    QTest.mouseClick(undo, Qt.MouseButton.LeftButton)
    panel = window.secondary_panel() or window.task_panel
    field = panel.inputs[1][0 if index == 0 else -1]
    field.setFocus()
    QTest.keyClicks(field, "bad")
    revision = editing.history.revision
    branch = editing.history.redo_label_key
    assert panel.pending_change() is None
    assert not undo.isEnabled() and not redo.isEnabled()
    QTest.keyClick(field, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert field.text() == ""
    assert workspace.active.state == original
    assert editing.history.revision == revision
    assert editing.history.redo_label_key == branch
    # A no-op typed value allows the existing branch rather than blocking replay.
    field.textEdited.emit(field.text())
    assert redo.isEnabled()
    QTest.mouseClick(redo, Qt.MouseButton.LeftButton)
    assert workspace.active.state == edited
    window.save_project()
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    assert workspace.active.state == edited
    oracle = calculate_saved_result(
        workspace.active.document, edited, window.presenter.system
    )
    expected_result = (
        oracle
        if oracle and oracle.calculation_status is EvaluationStatus.COMPLETE
        else None
    )
    assert workspace.historical_result() == expected_result


@pytest.mark.parametrize(
    ("index", "column"),
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)],
)
@pytest.mark.parametrize("row", [0, 1])
@pytest.mark.parametrize("language", [Language.ENGLISH, Language.SPANISH])
@pytest.mark.parametrize("system", list(MeasurementSystem))
def test_repeated_task_input_undo_branches_refresh_every_control(
    window: LifftWindow,
    tmp_path: Path,
    index: int,
    column: int,
    row: int,
    language: Language,
    system: MeasurementSystem,
) -> None:
    """Repeated branches returning to one revision must always rebind live widgets.

    Args:
        window: Disposable integrated window with real mouse toolbar history.
        tmp_path: Private project destination, never an owner fixture.
        index: LiFFT, DUET or ST; all nine numeric/selector input types are covered.
        column: Tool-specific input widget index, including rating/direction choices.
        row: Populated Task 1 or initially empty Task 2.
        language: English or Spanish application captions.
        system: Source/display metric or imperial interpretation.

    Returns:
        None; five edit/Undo branches and intervening Redo verify exact immutable
        source/result state and actual recreated controls, without durable writes.
    """
    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    source = (
        LifftDraft(system, (LifftTask("first", 30, 49.05, 100),)),
        DuetDraft((DuetTask("first", 6, 100),)),
        TstDraft(system, (TstTask("first", TstDirection.HORIZONTAL, 30, 49.05, 100),)),
    )[index]
    path = tmp_path / "repeated.ergprj"
    workspace.create(
        str(path), ProjectMetadata("repeat", "Repeat", system), "assessment", source
    )
    window.language = language
    window.assessment_tabs.setCurrentIndex(index)
    presenter = (window.presenter, window.duet_presenter, window.tst_presenter)[index]
    presenter.set_task_count(15)
    window.refresh()
    window.calculate()
    window.save_project()
    key = workspace.active.document
    original = workspace.active.state
    calculated = workspace.historical_result()
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(path), key.document_id)
    window.refresh()
    editing = workspace.editing
    nav = window.main_navigation
    undo = nav.toolbar.widgetForAction(nav.toolbar_actions["undo"])
    redo = nav.toolbar.widgetForAction(nav.toolbar_actions["redo"])
    before_file = path.read_bytes()
    for attempt in range(5):
        panel = window.secondary_panel() or window.task_panel
        field = panel.inputs[row][column]
        baseline = (
            field.currentIndex() if isinstance(field, QComboBox) else field.text()
        )
        field.setFocus()
        if isinstance(field, QComboBox):
            field.setCurrentIndex((field.currentIndex() + 1) % field.count())
        else:
            field.selectAll()
            QTest.keyClicks(field, "50" if attempt < 3 else "75")
        assert undo.isEnabled()
        QTest.mouseClick(undo, Qt.MouseButton.LeftButton)
        assert workspace.active.state == original
        assert workspace.historical_result() == calculated
        # Check the actual replacement widget, not just the already restored model.
        restored = (window.secondary_panel() or window.task_panel).inputs[row][column]
        assert (
            restored.currentIndex()
            if isinstance(restored, QComboBox)
            else restored.text()
        ) == baseline
        assert not (window.secondary_panel() or window.task_panel).pending
        assert redo.isEnabled()
        assert path.read_bytes() == before_file
        if attempt % 2 == 0:
            QTest.mouseClick(redo, Qt.MouseButton.LeftButton)
            assert workspace.active.state != original
            oracle = calculate_saved_result(
                workspace.active.document,
                workspace.active.state,
                window.presenter.system,
            )
            expected_result = (
                oracle
                if oracle and oracle.calculation_status is EvaluationStatus.COMPLETE
                else None
            )
            assert workspace.historical_result() == expected_result
            QTest.mouseClick(undo, Qt.MouseButton.LeftButton)
            assert workspace.active.state == original
            restored = (window.secondary_panel() or window.task_panel).inputs[row][
                column
            ]
            assert (
                restored.currentIndex()
                if isinstance(restored, QComboBox)
                else restored.text()
            ) == baseline
        assert editing.history.undo_label_key is None
