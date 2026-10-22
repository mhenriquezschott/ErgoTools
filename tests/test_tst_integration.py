"""Integrated ST ownership, editing, review gates and native camera workflows.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.contracts.body_renderer import BodyRegion
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window, list_desktop_documents
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_history_persistence import ENTRY, HIERARCHY, JOBS, META

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """All three source kinds share one classified synthetic assignment.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; fixture cleanup closes the window and releases
        its temporary project after the test.
    """
    path = tmp_path / "integrated.ergprj"
    with AssessmentProjectFile.create_with_job_risks(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(JOBS)
        project.create_historical_assessment(
            ENTRY, LifftDraft(META.default_units, (LifftTask("l", 12, 20, 100),))
        )
        for identity, kind, source in (
            ("duet", AssessmentKind.DUET, DuetDraft((DuetTask("d", 6, 100),))),
            (
                "st",
                AssessmentKind.TST,
                TstDraft(
                    META.default_units,
                    (TstTask("s", TstDirection.DOWNWARD, 12, 20, 100),),
                ),
            ),
        ):
            project.create_historical_assessment(
                AssignmentAssessment(
                    identity,
                    ENTRY.assignment_id,
                    kind,
                    worker_id=next(
                        a.worker.worker_id
                        for a in project.load_jobs().assignments
                        if a.assignment_id == ENTRY.assignment_id
                    ),
                ),
                source,
            )
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.switch(
        str(path), ENTRY.document_id, choice=CloseChoice.DISCARD
    )
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def edit(window: LifftWindow, text: str) -> None:
    """Emit user input on ST repetitions without committing it silently.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        text: Literal typed/control input, including invalid/incomplete cases where
            specified.

    Returns:
        None.
    """
    field = window.tst_panel.inputs[0][3]
    field.setText(text)
    field.textEdited.emit(text)


def test_three_tabs_save_reopen_review_and_return(window: LifftWindow) -> None:
    """ST edits persist to its own source; review clears the previous DUET risk.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(1)
    window.duet_panel.calculate_button.click()
    assert window.results_sidebar.risk_gauge.has_value
    window.assessment_tabs.setCurrentIndex(2)
    assert window.tst_active and window.active_kind() is AssessmentKind.TST
    assert window.presenter.workspace.active.document.document_id == "st"
    assert window.results_sidebar.individual_risk_title.text() == "Individual Shoulder"
    assert not window.results_sidebar.risk_gauge.has_value
    assert window.main_navigation.tool_label.text() == "Tool: ST"
    edit(window, "200")
    window.navigation_action(window.save_project)
    with AssessmentProjectFile.open(
        Path(window.presenter.workspace.location)
    ) as project:
        assert (
            project.load(window.presenter.workspace.active.document)
            .tasks[0]
            .repetitions
            == 200
        )
    assert set(list_desktop_documents(window.presenter.workspace.location)) == {
        ENTRY.document_id,
        "duet",
        "st",
    }
    window.run(window.calculate)
    result = window.tst_presenter.evaluator.current(window.presenter.workspace.active)
    assert result.status in (EvaluationStatus.COMPLETE, EvaluationStatus.PARTIAL)
    assert result.summary is not None
    assert window.results_sidebar.assessment_status_label.text() != "Review required"
    assert window.results_sidebar.risk_gauge.has_value
    assert "review" not in window.message.text().lower()
    window.assessment_tabs.setCurrentIndex(0)
    assert window.presenter.source().tasks[0].load == 20
    window.assessment_tabs.setCurrentIndex(2)
    assert window.tst_panel.inputs[0][3].text() == "200"


def test_invalid_switch_preferences_close_and_dirty_cancel(window: LifftWindow) -> None:
    """Invalid edits remain visible; canceled dirty transitions retain the ST tab.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(2)
    before = window.tst_presenter.source()
    edit(window, "bad")
    window.assessment_tabs.setCurrentIndex(1)
    assert window.assessment_tabs.currentIndex() == 2 and window.tst_panel.pending
    assert window.tst_presenter.source() is before
    window.units.setCurrentIndex(1)
    assert (
        window.units.currentIndex() == 0
        and window.tst_panel.inputs[0][3].text() == "bad"
    )
    assert not window.close()
    edit(window, "201")
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        window.assessment_tabs.setCurrentIndex(0)
    assert (
        window.assessment_tabs.currentIndex() == 0
        and window.presenter.workspace.has_unsaved_changes
    )
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.assessment_tabs.setCurrentIndex(0)
    window.assessment_tabs.setCurrentIndex(2)
    assert window.tst_presenter.source().tasks[0].repetitions == 201


def test_localization_clear_worker(window: LifftWindow) -> None:
    """Original ST captions and worker routes retain the selected tool kind.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(2)
    window.language = Language.SPANISH
    window.translate()
    window.refresh()
    assert window.main_navigation.tool_label.text() == "Herramienta: ST"
    assert window.results_sidebar.individual_risk_title.text() == "ST individual"
    gauge = window.results_sidebar.risk_gauge
    font = QFont(gauge.font())
    font.setPointSize(9)
    font.setBold(True)
    assert all(
        QFontMetrics(font).horizontalAdvance(line) <= gauge.width()
        for line in gauge.outcome_text.splitlines()
    )
    window.tst_panel.calculate_button.click()
    assert window.results_sidebar.assessment_status_label.text() == "Listo"
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        window.tst_panel.clear_button.click()
    assert not window.message.text()
    assert all(not e.text() for e in window.tst_panel.inputs[0][1:])
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.navigate_worker("w")
    assert window.active_kind() is AssessmentKind.TST
    assert window.presenter.workspace.active.document.document_id == "st"
    source = window.blank_active_source()
    assert isinstance(source, TstDraft)
    assert len(source.tasks) == 15 and all(
        t.direction is TstDirection.HANDLING_LOADS for t in source.tasks
    )
    assert window.main_navigation.toolbar_actions["settings"].isEnabled()


def test_missing_st_creation_keeps_assignment(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Missing ST creation requires consent and retains assignment ownership.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "only-lifft.ergprj"
    with AssessmentProjectFile.create_with_job_risks(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(JOBS)
        project.create_historical_assessment(
            ENTRY, LifftDraft(META.default_units, (LifftTask("l", 12, 20, 100),))
        )
    workspace = window.presenter.workspace
    workspace.switch(str(path), ENTRY.document_id, choice=CloseChoice.DISCARD)
    window.refresh()
    with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
        window.assessment_tabs.setCurrentIndex(2)
    assert window.assessment_tabs.currentIndex() == 2
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        window.assessment_tabs.setCurrentIndex(2)
    assert window.tst_active and len(window.tst_presenter.source().tasks) == 15
    assert not any(
        e.kind is AssessmentKind.TST for e in workspace.read_history().history.entries
    )
    edit(window, "10")
    window.navigation_action(window.save_project)
    entry = next(
        e
        for e in workspace.read_history().history.entries
        if e.document_id == workspace.active.document.document_id
    )
    assert (
        entry.assignment_id == ENTRY.assignment_id and entry.kind is AssessmentKind.TST
    )


@pytest.mark.skipif(
    _APP.platformName() == "offscreen", reason="Native OpenGL display required."
)
def test_native_shoulder_camera_preserves_other_tool_overlays(
    window: LifftWindow, tmp_path: Path
) -> None:
    """ST uses its real shoulder camera; gated results never color shoulder actors.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    view = create_window(
        tmp_path / "native.json", original_navigation=True, enable_vtk=True
    )
    view.presenter.workspace.switch(window.presenter.workspace.location, "duet")
    view.refresh()
    view.show()
    _APP.processEvents()
    try:
        view.duet_panel.calculate_button.click()
        renderer = view._body_renderer
        assert renderer.actors["left_arm"].GetVisibility()
        view.assessment_tabs.setCurrentIndex(2)
        assert renderer.renderer.GetActiveCamera().GetPosition() == pytest.approx(
            renderer.shots[BodyRegion.SHOULDERS].position
        )
        view.tst_panel.calculate_button.click()
        assert {
            key for key, actor in renderer.actors.items() if actor.GetVisibility()
        } == {
            "human",
            "back",
            "left_arm",
            "left_hand",
            "right_arm",
            "right_hand",
            "left_shoulder",
            "right_shoulder",
        }
        assert view.results_sidebar.risk_gauge.has_value
        edit(view, "250")
        with patch.object(view, "dirty_choice", return_value=CloseChoice.CANCEL):
            assert not view.close()
        assert not renderer._closed
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        _APP.processEvents()
    assert renderer._closed
