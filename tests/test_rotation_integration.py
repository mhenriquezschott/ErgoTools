"""Real main-toolbar JROT composition, saved provenance and editor isolation.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.domain.language import Language
from ergotools.domain.rotation_scheme import RotationMode
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from tests.test_rotation_comparison import all_risks
from tests.test_rotation_persistence import seed
from tests.test_rotation_solve import ControlledOptimizer, fill_rotation, wait_for
from tests.test_saved_tool_data import window as window

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.fixture
def main(tmp_path: Path) -> Iterator[LifftWindow]:
    """Open one synthetic format-seven project through actual bootstrap wiring.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Yields:
        Live bootstrap-wired main window borrowing the temporary rotation-capable
        repository; fixture cleanup releases owned GUI/project resources.
    """
    path = tmp_path / "main.ergprj"
    with seed(path) as project:
        all_risks(project)
    view = create_window(tmp_path / "settings.json", original_navigation=True)
    view.presenter.workspace.switch(str(path), "source")
    view.refresh()
    view.show()
    _APP.processEvents()
    yield view
    view.presenter.workspace.close(choice=CloseChoice.DISCARD)
    view.close()
    _APP.processEvents()


def visit(main: LifftWindow, interact: Callable[[RotationDialog], None]) -> None:
    """Drive the actual modal toolbar path; surface callback failures in pytest.

    Args:
        main: Live synthetic integrated assessment window owning the actual modal JROT
            workflow.
        interact: Callback driving the actual owned JROT dialog; errors are returned to
            the enclosing pytest thread.

    Returns:
        None.
    """
    failures: list[BaseException] = []
    visited = []
    timer = QTimer(main)
    timer.setSingleShot(True)

    def callback() -> None:
        """Assert the actual borrowed JROT modal.

        Assert the actual borrowed JROT modal, run the supplied interaction, retain
        callback failures and reject the owned window on every exit.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QApplication.activeModalWidget()
        try:
            assert isinstance(dialog, RotationDialog)
            visited.append(dialog)
            interact(dialog)
        except BaseException as error:
            failures.append(error)
        finally:
            if isinstance(dialog, RotationDialog):
                dialog.reject()

    timer.timeout.connect(callback)
    timer.start(0)
    action = main.main_navigation.toolbar_actions["jrot"]
    assert action.isEnabled()
    action.trigger()
    timer.stop()
    assert visited and not failures, failures


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("all_tools", [False, True])
def test_main_actual_solver_save_upgrade_and_reopen(
    main: LifftWindow, language: Language, all_tools: bool
) -> None:
    """Real CBC/HiGHS retain exact links privately until the sole main Save.

    Args:
        main: Live synthetic integrated assessment window owning the actual modal JROT
            workflow.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.
        all_tools: True exercises HiGHS multi-tool routing; False exercises CBC
            single-tool routing.

    Returns:
        None.
    """
    main.language = language
    main.translate()
    main.refresh()
    workspace = main.presenter.workspace
    repository = workspace.rotation_repository()
    assert repository is workspace.plot_repository()
    path = Path(workspace.location)
    original = workspace.active.state
    risks = workspace.read_job_risk()
    before = path.read_bytes()
    mode = RotationMode.ALL_TOOLS if all_tools else RotationMode.SINGLE_TOOL
    saved = []

    def solve(dialog: RotationDialog) -> None:
        """Run actual CBC/HiGHS from the modal.

        Run actual CBC/HiGHS from the modal, accept its exact preview, verify
        solve/apply caused no durable write, then retain frozen links/provenance.

        Args:
            dialog: Live modal/form under test; the caller owns its lifetime and
                event-loop scheduling.

        Returns:
            None.
        """
        assert dialog.repository is repository and dialog.language is language
        assert dialog.parent() is main and dialog.isModal()
        fill_rotation(dialog)
        controller = dialog.optimization
        (dialog.optimize_all_button if all_tools else dialog.optimize_button).click()
        wait_for(lambda: not controller.busy)
        if all_tools:
            assert controller.comparison.tabs.count() == 3
            controller.comparison.apply_button.click()
        else:
            assert controller.preview is not None
            dialog.transfer_button.click()
        assert path.read_bytes() == before
        assert dialog.save_button.isHidden()
        dialog.accept_rotation_state()
        (scheme,) = repository.load_rotation_schemes()
        assert scheme.mode is mode and {t.job_id for t in scheme.targets} == {"j", "k"}
        saved.append(scheme)

    with patch.object(RotationDialog, "_message"):
        visit(main, solve)
    assert workspace.active.state == original and workspace.read_job_risk() == risks
    assert workspace.rotation_repository() is repository
    assert workspace.plot_repository() is repository
    assert repository.load_rotation_schemes() == tuple(saved)

    def inspect(dialog: RotationDialog) -> None:
        """Reopen the actual JROT modal.

        Reopen the actual JROT modal and verify its saved exact schedule/identity
        matches the accepted solver result.

        Args:
            dialog: Live modal/form under test; the caller owns its lifetime and
                event-loop scheduling.

        Returns:
            None.
        """
        assert dialog.repository is repository and dialog.schemes == tuple(saved)
        dialog.scheme_combo.setCurrentIndex(0)
        assert dialog.loaded == saved[0]
        assert (
            dialog.grid.current_scheme(saved[0].scheme_id).current == saved[0].current
        )

    visit(main, inspect)
    assert path.read_bytes() == before
    main.save_project()
    # Independent reopening sees the single project Save, including solver provenance.
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_rotation_schemes() == tuple(saved)
        assert reopened.load_job_risk() == risks.risk
    # The workspace adapter tracks its own upgrade and remains writable afterwards.
    workspace.save()
    assert repository.load_rotation_schemes() == tuple(saved)


@pytest.mark.parametrize("index", [0, 1, 2])
def test_main_jrot_keeps_invalid_pending_assessment_text(
    window: LifftWindow, index: int
) -> None:
    """Browsing saved JROT risks never parses or saves any active tool's fields.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    panel = window.task_panel if index == 0 else window.secondary_panel()
    active = window.presenter.workspace.active
    state = active.state
    field = panel.inputs[0][2] if index == 0 else panel.inputs[0][-1]
    field.setText("bad")
    field.textEdited.emit("bad")
    path = Path(window.presenter.workspace.location)
    before = path.read_bytes()
    visit(window, lambda dialog: None)
    assert field.text() == "bad" and window.presenter.workspace.active.state == state
    assert (
        path.read_bytes() == before and window.assessment_tabs.currentIndex() == index
    )


def test_main_capability_and_missing_opener(main: LifftWindow) -> None:
    """JROT is unavailable without a supported project or an installed opener.

    Args:
        main: Live synthetic integrated assessment window owning the actual modal JROT
            workflow.

    Returns:
        None.
    """
    workspace = main.presenter.workspace
    main._rotation_opener = None
    main.refresh_navigation()
    assert not main.main_navigation.toolbar_actions["jrot"].isEnabled()
    main.open_rotation()
    workspace.close(choice=CloseChoice.DISCARD)
    main.refresh()
    assert not workspace.supports_rotations
    with pytest.raises(ValueError, match="full project"):
        workspace.rotation_repository()
    main.open_rotation()


def test_main_modal_close_waits_for_owned_solver(main: LifftWindow) -> None:
    """Bootstrap cannot destroy the modal's QThread before bounded completion.

    Args:
        main: Live synthetic integrated assessment window owning the actual modal JROT
            workflow.

    Returns:
        None.
    """
    optimizer = ControlledOptimizer()

    def cancel(dialog: RotationDialog) -> None:
        """Request close during a controlled solve.

        Request close during a controlled solve, assert the modal retains its live
        worker, release completion and retain only the accepted manual schedule.

        Args:
            dialog: Live modal/form under test; the caller owns its lifetime and
                event-loop scheduling.

        Returns:
            None.
        """
        fill_rotation(dialog)
        dialog.optimize_button.click()
        wait_for(optimizer.started.is_set)
        dialog.reject()
        assert dialog.isVisible() and dialog.optimization.busy
        optimizer.release.set()
        wait_for(lambda: not dialog.optimization.busy)
        assert not dialog.isVisible()
        (manual,) = dialog.repository.load_rotation_schemes()
        assert manual.mode is RotationMode.MANUAL
        with AssessmentProjectFile.open(
            Path(main.presenter.workspace.location)
        ) as saved:
            assert saved.load_rotation_schemes() == ()

    try:
        with patch("ergotools.bootstrap.PulpRotationOptimizer", return_value=optimizer):
            visit(main, cancel)
    finally:
        optimizer.release.set()
    assert optimizer.calls == 1
    (manual,) = main.presenter.workspace.rotation_repository().load_rotation_schemes()
    assert manual.mode is RotationMode.MANUAL
    assert main.presenter.workspace.has_unsaved_changes


def test_main_lightweight_project_disables_jrot(
    main: LifftWindow, tmp_path: Path
) -> None:
    """An assessment-only project must not expose full-project rotation commands.

    Args:
        main: Live synthetic integrated assessment window owning the actual modal JROT
            workflow.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.domain.assessments.lifft_draft import LifftDraft
    from tests.test_history_persistence import META

    path = tmp_path / "assessment-only.ergprj"
    with AssessmentProjectFile.create_with_document(
        path, META, "a", LifftDraft(META.default_units), format_version=2
    ):
        pass
    workspace = main.presenter.workspace
    workspace.switch(str(path), "a")
    main.refresh()
    assert not workspace.supports_rotations
    assert not main.main_navigation.toolbar_actions["jrot"].isEnabled()
    before = path.read_bytes()
    main.open_rotation()
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        workspace.rotation_repository()


def test_main_opener_error_keeps_pending_text(window: LifftWindow) -> None:
    """A concrete opener failure is caught at the existing GUI error boundary.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    main = window
    workspace = main.presenter.workspace
    state = workspace.active.state
    field = main.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    before = Path(workspace.location).read_bytes()
    with patch.object(main, "_rotation_opener", side_effect=OSError("fixture failure")):
        main.main_navigation.toolbar_actions["jrot"].trigger()
    assert main.message.text() == main.text("error")
    assert field.text() == "bad" and workspace.active.state == state
    assert Path(workspace.location).read_bytes() == before


@pytest.mark.parametrize("language", list(Language))
def test_incomplete_rotation_explains_main_save_failure_in_both_languages(
    main: LifftWindow, language: Language, tmp_path: Path
) -> None:
    """Main Save/Save As retain partial JROT data and show actionable localized text.

    Args:
        main: Disposable integrated native project with eligible rotation workers.
        language: English or Spanish owner-facing validation.
        tmp_path: Disposable exclusive Save As destination directory.

    Returns:
        None; neither the current file nor a new destination is published on failure.
    """
    from ergotools.presentation.localization import Translator

    main.language = language
    main.translate()
    workspace = main.presenter.workspace
    before = Path(workspace.location).read_bytes()

    def enter_partial(dialog: RotationDialog) -> None:
        """Accept an incomplete manual row into the shared project session.

        Args:
            dialog: Native integrated modal whose close retains partial intent.

        Returns:
            None; the missing time-block choices remain missing.
        """
        dialog.scheme_combo.setEditText("Partial")
        dialog.grid.set_choice(0, 0, "w")

    visit(main, enter_partial)
    expected = Translator(language).text("project.rotation_draft_incomplete")
    main.run(main.save_project)
    assert main.message.text() == expected and workspace.has_unsaved_changes
    assert Path(workspace.location).read_bytes() == before
    destination = tmp_path / "incomplete.ergprj"
    with (
        patch.object(main, "choose_file", return_value=str(destination)),
        patch.object(main, "choose_project_details", return_value=("Partial", None)),
    ):
        main.run(main.save_project_as)
    assert main.message.text() == expected and not destination.exists()
