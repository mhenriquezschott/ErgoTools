"""Integrated DUET tab, assessment ownership, shared results and lifecycle.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_history_persistence import ENTRY, HIERARCHY, JOBS, META

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Open both tools attached to one real classified synthetic assignment.

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
            ENTRY,
            LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("l", 12, 20, 100),)),
        )
        project.create_historical_assessment(
            AssignmentAssessment(
                "duet",
                ENTRY.assignment_id,
                AssessmentKind.DUET,
                worker_id=next(
                    a.worker.worker_id
                    for a in project.load_jobs().assignments
                    if a.assignment_id == ENTRY.assignment_id
                ),
            ),
            DuetDraft((DuetTask("d", 6, 100), DuetTask("blank", 0, None))),
        )
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.switch(str(path), ENTRY.document_id)
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def test_tab_calculate_cards_edit_save_and_return(window: LifftWindow) -> None:
    """DUET shares the original main layout and saves edits on its own document.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(1)
    assert (
        window.duet_active
        and window.presenter.workspace.active.document.document_id == "duet"
    )
    panel = window.duet_panel
    panel.calculate_button.click()
    sidebar = window.results_sidebar
    assert sidebar.individual_risk_title.text() == "Individual DUET"
    assert sidebar.risk_gauge.has_value
    assert sidebar.assessment_status_label.text() == "Ready"
    assert sidebar.metric_labels["average_load"].text() == "-"
    assert window.main_navigation.tool_label.text() == "Tool: DUET"
    panel.inputs[0][1].setText("200")
    panel.inputs[0][1].textEdited.emit("200")
    assert not sidebar.risk_gauge.has_value
    window.navigation_action(window.save_project)
    assert window.duet_presenter.source().tasks[0].repetitions == 200
    window.assessment_tabs.setCurrentIndex(0)
    assert not window.duet_active
    assert window.presenter.workspace.active.document.document_id == ENTRY.document_id
    window.assessment_tabs.setCurrentIndex(1)
    assert window.duet_panel.inputs[0][1].text() == "200"


def test_invalid_text_and_dirty_cancel_keep_current_tab(window: LifftWindow) -> None:
    """Switching retains valid drafts and never hides invalid pending input.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(1)
    panel = window.duet_panel
    panel.inputs[0][1].setText("bad")
    panel.inputs[0][1].textEdited.emit("bad")
    window.assessment_tabs.setCurrentIndex(0)
    assert window.assessment_tabs.currentIndex() == 1
    assert panel.inputs[0][1].text() == "bad" and panel.pending
    assert not window.close()
    panel.inputs[0][1].setText("201")
    panel.inputs[0][1].textEdited.emit("201")
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        window.assessment_tabs.setCurrentIndex(0)
    assert window.assessment_tabs.currentIndex() == 0
    window.assessment_tabs.setCurrentIndex(1)
    assert window.duet_presenter.source().tasks[0].repetitions == 201
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.assessment_tabs.setCurrentIndex(0)
    window.assessment_tabs.setCurrentIndex(1)
    assert window.duet_presenter.source().tasks[0].repetitions == 201


def test_language_clear_and_navigation_kind(window: LifftWindow) -> None:
    """Localized clearing and context routing keep LiFFT data intact.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(1)
    window.language = Language.SPANISH
    window.translate()
    window.refresh()
    assert window.results_sidebar.individual_risk_title.text() == "DUET individual"
    assert window.main_navigation.tool_label.text() == "Herramienta: DUET"
    window.duet_panel.calculate_button.click()
    with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
        window.duet_panel.clear_button.click()
    assert not window.results_sidebar.risk_gauge.has_value
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.navigate_worker("w")
    assert window.active_kind() is AssessmentKind.DUET
    assert window.presenter.workspace.active.document.document_id == "duet"
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.assessment_tabs.setCurrentIndex(0)
    assert window.presenter.source().tasks[0].load == 20


def test_missing_tool_creation_requires_approval(window: LifftWindow) -> None:
    """A different assignment's tool cannot be selected as the current owner's data.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    workspace = window.presenter.workspace
    workspace.create_assessment("unbound", LifftDraft(MeasurementSystem.IMPERIAL))
    window.refresh()
    # Existing DUET may be explicitly selected for an unbound project.
    window.assessment_tabs.setCurrentIndex(1)
    assert workspace.active.document.document_id == "duet"
    window.assessment_tabs.setCurrentIndex(0)
    with patch.object(window, "dirty_choice", return_value=CloseChoice.CANCEL):
        window.assessment_tabs.setCurrentIndex(1)
    assert window.assessment_tabs.currentIndex() == 1


def test_create_missing_tool_and_native_overlay(
    window: LifftWindow, tmp_path: Path
) -> None:
    """New unbound tool data requires consent and colors only the active anatomy.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from PyQt5.QtWidgets import QMessageBox

    from ergotools.domain.project import ProjectMetadata

    workspace = window.presenter.workspace
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.create(
        str(tmp_path / "blank.ergprj"),
        ProjectMetadata("blank", "Blank", MeasurementSystem.IMPERIAL),
        "lifft",
        LifftDraft(MeasurementSystem.IMPERIAL),
    )
    window.refresh()
    with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
        window.assessment_tabs.setCurrentIndex(1)
    assert not window.duet_active
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        window.assessment_tabs.setCurrentIndex(1)
    assert window.duet_active and len(window.duet_presenter.source().tasks) == 15
    assert all(
        t.omni_res_scale == 0 and t.repetitions is None
        for t in window.duet_presenter.source().tasks
    )

    # A new tool for classified data must keep the original assignment ownership.
    bound_path = tmp_path / "bound-only.ergprj"
    with AssessmentProjectFile.create_with_job_risks(bound_path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.save_jobs(JOBS)
        project.create_historical_assessment(
            ENTRY,
            LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("l", 12, 20, 100),)),
        )
    workspace.switch(str(bound_path), ENTRY.document_id, choice=CloseChoice.DISCARD)
    window.refresh()
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        window.assessment_tabs.setCurrentIndex(1)
    assert window.duet_active
    assert not any(
        e.kind is AssessmentKind.DUET for e in workspace.read_history().history.entries
    )
    field = window.duet_panel.inputs[0][1]
    field.setText("10")
    field.textEdited.emit("10")
    window.navigation_action(window.save_project)
    entry = next(
        e
        for e in workspace.read_history().history.entries
        if e.document_id == workspace.active.document.document_id
    )
    assert entry.assignment_id == ENTRY.assignment_id
    assert entry.kind is AssessmentKind.DUET and entry.assignment_id == 1


@pytest.mark.skipif(
    _APP.platformName() == "offscreen", reason="Native OpenGL display required."
)
def test_native_duet_scene_and_close(window: LifftWindow, tmp_path: Path) -> None:
    """The actual integrated renderer frames arms/hands and clears invalid risk.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.application.contracts.body_renderer import BodyRegion

    view = create_window(
        tmp_path / "native-settings.json", original_navigation=True, enable_vtk=True
    )
    view.presenter.workspace.switch(window.presenter.workspace.location, "duet")
    view.refresh()
    view.show()
    _APP.processEvents()
    try:
        view.duet_panel.calculate_button.click()
        renderer = view._body_renderer
        assert {
            key for key, actor in renderer.actors.items() if actor.GetVisibility()
        } == {"human", "back", "left_arm", "left_hand", "right_arm", "right_hand"}
        assert renderer.renderer.GetActiveCamera().GetPosition() == pytest.approx(
            renderer.shots[BodyRegion.DISTAL_UPPER_EXTREMITIES].position
        )
        view.duet_panel.inputs[0][1].setText("bad")
        view.duet_panel.inputs[0][1].textEdited.emit("bad")
        assert not renderer.actors["left_arm"].GetVisibility()
        assert not view.close() and not renderer._closed
        with patch.object(LifftWindow, "confirm_clear_assessment", return_value=True):
            view.duet_panel.clear_button.click()
    finally:
        view.presenter.workspace.close(choice=CloseChoice.DISCARD)
        view.close()
        _APP.processEvents()
    assert renderer._closed
