"""Original shared controls activate saved assessments and preserve modal edits.

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
from PyQt5.QtCore import QCoreApplication, QEvent, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey
from ergotools.application.settings import Language
from ergotools.bootstrap import create_window
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.job_catalog import WorkerJobAssignment
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.work_catalog import WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_management_dialog import (
    WorkerManagementDialog,
)
from tests.test_history_persistence import ENTRY, HIERARCHY, JOBS, META, STATION
from tests.test_lifft_task_panel import enter

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def window(tmp_path: Path) -> Iterator[LifftWindow]:
    """Build two fully classified sources plus a worker without a saved assessment.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live synthetic integrated window; teardown releases the temporary project and
        processes native deferred widget deletion before another fixture can run.
    """
    path = tmp_path / "navigation.ergprj"
    hierarchy = replace(
        HIERARCHY,
        work=replace(
            HIERARCHY.work,
            workers=(
                WorkerEntry("w", "Ada", "O'Connor, Smith"),
                WorkerEntry("x", "Grace", "Zulu"),
                WorkerEntry("y", "Lin", "Young"),
            ),
        ),
    )
    owner = hierarchy.work.worker_context("x", STATION.at_shift("Day"))
    jobs = replace(
        JOBS, assignments=(*JOBS.assignments, WorkerJobAssignment(2, owner, 2))
    )
    with AssessmentProjectFile.create_with_job_risks(path, META) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(jobs)
        project.create_historical_assessment(
            ENTRY,
            LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("w-task", 12, 20, 100),)),
        )
        project.create_historical_assessment(
            AssignmentAssessment(
                "b",
                2,
                AssessmentKind.LIFFT,
                worker_id=next(
                    a.worker.worker_id for a in jobs.assignments if a.assignment_id == 2
                ),
            ),
            LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("x-task", 21, 25, 50),)),
        )
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.switch(str(path), "a")
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    view.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    _APP.processEvents()


def test_worker_navigation_retains_edits_until_main_save(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Worker navigation retains accepted edits without a local Save prompt.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    nav = window.main_navigation
    assert nav is not None
    toolbar_layout = nav.toolbar.layout()
    assert toolbar_layout is not None
    assert toolbar_layout.spacing() == 3
    margins = toolbar_layout.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        7,
        7,
        7,
        7,
    )
    assert nav.workers.currentData() == "w"
    assert "O'Connor, Smith" in nav.workers.currentText()
    assert nav.location_browser.job_combo.currentData() == "a"
    enter(window, 0, 0, "16")
    with patch.object(
        window,
        "dirty_choice",
        side_effect=AssertionError("Navigation must not ask to Save"),
    ):
        nav.nav_buttons[2].click()
    assert nav.workers.currentData() == "x"
    assert window.presenter.workspace.active.document.document_id == "b"
    assert nav.location_browser.job_combo.currentData() == "b"
    assert window.task_panel.inputs[0][0].text() == "21.0"
    with AssessmentProjectFile.open(tmp_path / "navigation.ergprj") as project:
        assert project.load(DocumentKey("p", "a")).tasks[0].lever_arm == 12
    nav.nav_buttons[0].click()
    assert nav.workers.currentData() == "w"
    assert window.task_panel.inputs[0][0].text() == "16.0"
    window.save_project()
    with AssessmentProjectFile.open(tmp_path / "navigation.ergprj") as project:
        assert project.load(DocumentKey("p", "a")).tasks[0].lever_arm == 16


def test_surname_order_filter_and_missing_assessment(window: LifftWindow) -> None:
    """Stored surnames/IDs drive filters and never label old data as another worker.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    nav = window.main_navigation
    assert nav is not None
    state = window.presenter.workspace.active
    nav.order_button.click()
    assert nav.workers.currentData() == "w"
    assert window.presenter.workspace.active is state
    nav.alphabet_buttons["Z"].click()
    assert nav.workers.currentData() == "x"
    assert nav.workers.count() == 1
    nav.alphabet_buttons["All"].click()
    assert nav.workers.count() == 3
    nav.alphabet_buttons["Y"].click()
    assert nav.workers.currentData() == "y"
    assert nav.alphabet_buttons["Y"].isChecked()
    assert window.assessment_navigation.view.workplace is None
    assert window.results_sidebar.assessment_status_label.text() == "No assessment"
    assert (
        "No LiFFT assessment exists for y"
        in window.results_sidebar.assessment_status_detail.text()
    )
    nav.alphabet_buttons["All"].click()
    nav.nav_buttons[0].click()
    assert nav.workers.currentData() == "w"
    assert not nav.alphabet_buttons["A"].isEnabled()


def test_worker_modal_refreshes_labels_without_rebuilding_grid(
    window: LifftWindow,
) -> None:
    """Real management save updates navigation while retaining the assessment view.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    nav = window.main_navigation
    assert nav is not None
    grid_field = window.task_panel.inputs[0][0]
    context = window.task_panel.context

    def save_worker() -> None:
        """Change the actual worker surname to Modernized, commit its visible form.

        Change the actual worker surname to Modernized, commit its visible form and
        close the modal.

        Args:
            None.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, WorkerManagementDialog)
        dialog.last_name_input.setText("Modernized")
        dialog.save_button.click()
        dialog.close()

    QTimer.singleShot(0, save_worker)
    nav.buttons["workers"].click()
    assert "Modernized" in nav.workers.currentText()
    assert window.task_panel.inputs[0][0] is grid_field
    assert window.task_panel.context is context
    assert window.presenter.workspace.active.document.document_id == "a"


def test_original_layout_translation_and_incomplete_actions(
    window: LifftWindow,
) -> None:
    """Preserve original dimensions, Spanish captions and available workflow actions.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    nav = window.main_navigation
    assert nav is not None
    window.language = Language.SPANISH
    window.translate()
    window.refresh_navigation()
    assert window.size().width() == 1550 and window.size().height() == 1015
    assert nav.toolbar_title.text() == "Proyecto"
    assert (
        nav.toolbar_title.contentsRect().height()
        >= nav.toolbar_title.fontMetrics().height()
    )
    assert nav.buttons["workers"].text() == "Trabajadores"
    assert nav.standalone_button.text().startswith("Evaluación independiente")
    assert nav.location_browser.headings[0].text() == "Planta (1)"
    assert nav.unit_label.text() == "Unidades: Imperial"
    assert nav.buttons["transfer"].isEnabled()
    assert nav.toolbar_actions["help"].isEnabled()
    assert window.main_navigation.toolbar_actions["plot"].isEnabled()
    assert nav.toolbar_actions["jrot"].isEnabled()
    assert not nav.toolbar_actions["jrot"].icon().isNull()
    assert nav.toolbar_actions["export"].isEnabled()
    assert not nav.toolbar_actions["export"].icon().isNull()
    assert window.assessment_tabs.count() == 3
    assert window.assessment_tabs.isTabEnabled(1)
    assert window.assessment_tabs.isTabEnabled(2)
    assert window.rect().contains(
        nav.location_browser.mapTo(window, nav.location_browser.rect().bottomRight())
    )


def test_empty_window_and_no_implicit_worker_activation(tmp_path: Path) -> None:
    """Building or rendering the shared controls performs no automatic selection.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    view = create_window(tmp_path / "empty.json", original_navigation=True)
    try:
        nav = view.main_navigation
        assert nav is not None
        assert nav.workers.count() == 0
        assert nav.project_label.text() == "Current Project: No project loaded"
        assert not nav.toolbar_actions["save"].isEnabled()
        assert not nav.toolbar_actions["export"].isEnabled()
        assert nav.toolbar_actions["new"].isEnabled()
        assert nav.toolbar_actions["open"].isEnabled()
        assert view.presenter.workspace.active is None
    finally:
        view.close()


def test_context_button_uses_selected_worker_without_another_prompt(
    window: LifftWindow,
) -> None:
    """The shared context button opens the existing owned assignment dialog directly.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    from ergotools.presentation.desktop.assessment_context_dialog import (
        AssessmentContextDialog,
    )

    nav = window.main_navigation
    assert nav is not None
    seen = []

    def use_context() -> None:
        """Verify worker w in the actual assignment chooser.

        Verify worker w in the actual chooser, skip standalone navigation, then
        select the first exact workplace leaf and accept it.

        Args:
            None.

        Returns:
            None.
        """
        dialog = _APP.activeModalWidget()
        assert isinstance(dialog, AssessmentContextDialog)
        assert dialog.worker_id == "w"
        assert dialog.standalone_button is not None
        leaf = dialog.tree.topLevelItem(0)
        while leaf.childCount():
            leaf = leaf.child(0)
        dialog.tree.setCurrentItem(leaf)
        seen.append(True)
        dialog.use.click()

    with patch.object(
        window, "choose_item", side_effect=AssertionError("Unexpected worker prompt")
    ):
        QTimer.singleShot(0, use_context)
        window.select_navigation_context()
    assert seen == [True]
    assert window.presenter.workspace.active.document.document_id == "a"


def test_new_project_has_no_unowned_assessment_or_artificial_organization(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Toolbar New creates a genuinely empty project before worker selection.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    nav = window.main_navigation
    assert nav is not None
    with (
        patch.object(window, "choose_file", return_value=str(tmp_path / "new.ergprj")),
        patch.object(window, "choose_project_details", return_value=("", "")),
    ):
        nav.toolbar_actions["new"].trigger()
    assert window.presenter.workspace.active is None
    assert len(window.task_panel.inputs) == 0
    assert nav.workers.count() == 0
    assert nav.toolbar_actions["save"].isEnabled()
    with AssessmentProjectFile.open(Path(window.presenter.workspace.location)) as empty:
        assert not empty.list_assessments()
        assert not empty.load_history().entries
        assert not empty.load_hierarchy().plants


@pytest.mark.parametrize("language", list(Language))
def test_project_captions_keep_pending_assessment_and_literal_title(
    window: LifftWindow, language: Language
) -> None:
    """Refresh original localized captions without committing the task editor.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    nav = window.main_navigation
    assert nav is not None
    active = window.presenter.workspace.active
    before = active.state
    field = window.task_panel.inputs[0][0]
    original = field.text()
    field.setText("bad")
    field.textEdited.emit("bad")
    window.languages.setCurrentIndex(list(Language).index(language))
    window.refresh_navigation()
    caption = (
        "Proyecto actual: History"
        if language is Language.SPANISH
        else "Current Project: History"
    )
    suffix = "Cargado" if language is Language.SPANISH else "Loaded"
    assert nav.project_label.text() == caption + "  •  " + suffix
    assert nav.file_label.text() == caption
    assert field.text() == "bad" and window.task_panel.pending
    assert window.presenter.workspace.active is active and active.state is before
    field.setText(original)
    field.textEdited.emit(original)


@pytest.mark.parametrize("language", list(Language))
def test_project_caption_first_save_and_close(
    window: LifftWindow, tmp_path: Path, language: Language
) -> None:
    """Unsaved backing is not labeled Loaded; first Save and Close update captions.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    window.languages.setCurrentIndex(list(Language).index(language))
    window.new_project()
    nav = window.main_navigation
    assert nav is not None
    empty = (
        "Proyecto actual: Sin proyecto abierto"
        if language is Language.SPANISH
        else "Current Project: No project loaded"
    )
    assert window._is_unsaved_project()
    assert nav.project_label.text() == nav.file_label.text() == empty
    destination = tmp_path / "saved-caption.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(
            window, "choose_project_details", return_value=("Literal title", "")
        ),
    ):
        window.save_project()
    assert destination.is_file() and not window._is_unsaved_project()
    caption = (
        "Proyecto actual: Literal title"
        if language is Language.SPANISH
        else "Current Project: Literal title"
    )
    suffix = "Cargado" if language is Language.SPANISH else "Loaded"
    assert nav.project_label.text() == caption + "  •  " + suffix
    assert nav.file_label.text() == caption
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.close_project()
    assert window.presenter.workspace.location is None
    assert nav.project_label.text() == nav.file_label.text() == empty


def test_worker_popup_hover_has_readable_reference_contrast(
    window: LifftWindow,
) -> None:
    """Paint the actual hovered worker row, rather than only inspecting CSS strings.

    Args:
        window: Disposable native main window with three workers and owned Qt lifetime.

    Returns:
        None; a noncurrent hovered item paints teal with visible white text, and closing
        the popup leaves the selected worker unchanged.
    """
    combo = window.main_navigation.workers
    before = combo.currentData()
    combo.showPopup()
    view = combo.view()
    index = combo.model().index(1, 0)
    rect = view.visualRect(index)
    QTest.mouseMove(view.viewport(), rect.center())
    _APP.processEvents()
    image = view.viewport().grab(rect).toImage()
    colors = [
        image.pixelColor(x, y).name()
        for y in range(image.height())
        for x in range(image.width())
    ]
    assert colors.count("#087e91") > image.width()
    assert colors.count("#ffffff") > 0
    combo.hidePopup()
    assert combo.currentData() == before
