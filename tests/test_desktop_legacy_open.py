"""Open original files through the integrated desktop without replacing sources.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_legacy_plot import mapped as mapped
from tests.test_legacy_reconciliation import old_source as old_source
from tests.test_legacy_rotations import rotated as rotated
from tests.test_main_navigation import window as window

pytestmark = pytest.mark.usefixtures("accept_migration")


@pytest.fixture
def accept_migration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drive real external conversion after consent without blocking test execution.

    Args:
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    from ergotools.presentation.desktop.project_migration_dialog import (
        ProjectMigrationDialog,
    )

    def execute(dialog: ProjectMigrationDialog) -> int:
        """Trigger Migrate and return the actual dialog result.

        Args:
            dialog: Live modal/form under test; the caller owns its lifetime and
                event-loop scheduling.

        Returns:
            Actual dialog result after attempting conversion; failures remain visible
            in the modal rather than being replaced with an accepted result.
        """
        dialog.attempt_migration()
        return dialog.result()

    monkeypatch.setattr(ProjectMigrationDialog, "exec", execute)


def test_open_converts_temporarily_and_remembers_only_first_save(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Preserve originals and hide temporary locations until explicit first Save.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    assert mapped == old_source == rotated
    before = mapped.read_bytes(), (tmp_path / "data/source.db").read_bytes()
    destination = tmp_path / "converted.ergprj"
    with patch.object(
        window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
    ):
        window.open_project_location(str(mapped))
    temporary = Path(window.presenter.workspace.location)
    assert temporary.exists() and window._is_unsaved_project()
    assert (
        str(temporary)
        not in JsonSettingsStore(tmp_path / "settings.json").load().recent_documents
    )
    with AssessmentProjectFile.open(temporary) as project:
        assert project.format_version == 19
        assert len(project.list_assessments()) == 1
        assert (
            project.load_saved_result(project.list_assessments()[0].document)
            is not None
        )
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(
            window, "choose_project_details", return_value=("Converted", "Test")
        ),
    ):
        window.save_project()
    assert window.presenter.workspace.location == str(destination)
    with patch.object(window._project_conversion, "convert") as convert:
        with patch.object(
            window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
        ):
            window.open_project_location(str(destination))
        convert.assert_not_called()
    assert not temporary.exists() and not window._is_unsaved_project()
    assert JsonSettingsStore(tmp_path / "settings.json").load().recent_documents[
        0
    ] == str(destination)
    assert (mapped.read_bytes(), (tmp_path / "data/source.db").read_bytes()) == before


@pytest.mark.parametrize("cancel_stage", ["dirty"])
def test_open_cancellation_preserves_active_edits(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
    cancel_stage: str,
) -> None:
    """Cancelled activation retains current edits and removes temporary output.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        cancel_stage: Parametrized consent stage where the guided upgrade/first-Save
            path is cancelled.

    Returns:
        None.
    """
    assert mapped == old_source == rotated
    window.presenter.commit(window.presenter.bind(), "w-task", "load", "99")
    active = window.presenter.workspace.active
    state, location = active.state, window.presenter.workspace.location
    before = JsonSettingsStore(tmp_path / "settings.json").load().recent_documents
    with (
        patch.object(
            window,
            "dirty_choice",
            return_value=CloseChoice.CANCEL
            if cancel_stage == "dirty"
            else CloseChoice.DISCARD,
        ),
        patch.object(window, "choose_item", return_value=("", False)),
    ):
        window.open_project_location(str(mapped))
    assert window.presenter.workspace.active is active
    assert active.state == state and active.is_dirty
    assert window.presenter.workspace.location == location
    assert (
        JsonSettingsStore(tmp_path / "settings.json").load().recent_documents == before
    )


def test_failed_conversion_preserves_dirty_workspace(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Missing original images fail without replacing the dirty native workspace.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    assert mapped == old_source == rotated
    for image in (tmp_path / "images").glob("*"):
        image.unlink()
    window.presenter.commit(window.presenter.bind(), "w-task", "load", "99")
    active = window.presenter.workspace.active
    state = active.state
    with patch.object(window, "dirty_choice", return_value=CloseChoice.DISCARD):
        window.open_project_location(str(mapped))
    assert window.presenter.workspace.active is active
    assert active.state == state and active.is_dirty


def test_bom_descriptor_routes_to_conversion_and_missing_source_raises(
    tmp_path: Path,
) -> None:
    """XML routing permits BOM/whitespace; source I/O errors are not hidden.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "bom.ergprj"
    path.write_bytes(b"\xef\xbb\xbf  <ErgoProject/>")
    adapter = ExternalProjectMigration()
    assert adapter.requires_conversion(str(path))
    with pytest.raises(FileNotFoundError):
        adapter.requires_conversion(str(tmp_path / "absent.ergprj"))


def classify_active_for_editing(window: LifftWindow) -> None:
    """Classify the synthetic migrated owner before exercising source edits.

    Args:
        window: Disposable native window with originally unclassified read-only data.

    Returns:
        None; add a real synthetic Job/placement through the existing catalog service,
        preserving every assessment identity and input.
    """
    from dataclasses import replace

    workspace = window.presenter.workspace
    from ergotools.domain.job_catalog import Job, JobPlacement

    hierarchy = workspace.read_hierarchy()
    job_snapshot = workspace.read_jobs()
    jobs = job_snapshot.jobs
    owner_id = workspace.read_history().history.entries[0].assignment_id
    owner = next(a for a in jobs.assignments if a.assignment_id == owner_id)
    placement_id = 1 + max((p.placement_id for p in jobs.placements), default=0)
    replacement = replace(
        jobs,
        jobs=(*jobs.jobs, Job("editing-test", "Editing")),
        placements=(
            *jobs.placements,
            JobPlacement(placement_id, "editing-test", owner.worker.workplace),
        ),
        assignments=tuple(
            replace(a, placement_id=placement_id) if a.assignment_id == owner_id else a
            for a in jobs.assignments
        ),
    )
    workspace.save_worker_catalogs(
        hierarchy, hierarchy.hierarchy, job_snapshot, replacement
    )
    window.refresh_navigation()


def test_converted_desktop_edit_and_jrot_save_retain_archive(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Check Open-to-edit/JROT/backup/reopen as one source-preserving workflow.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from dataclasses import replace

    from ergotools.bootstrap import load_icons
    from ergotools.presentation.desktop.rotation_dialog import RotationDialog

    assert mapped == old_source == rotated
    destination = tmp_path / "integrated.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(
            window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
        ),
    ):
        window.open_project_location(str(mapped))
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=("Integrated", "")),
    ):
        window.save_project()
    workspace = window.presenter.workspace
    repository = workspace.rotation_repository()
    from ergotools.application.session import DocumentKey

    observations = {
        entry.document_id: repository.load_saved_result(
            DocumentKey(repository.metadata.project_id, entry.document_id)
        )
        for entry in repository.load_history().entries
    }
    classify_active_for_editing(window)
    active = workspace.active
    task_id = active.state.tasks[0].task_id
    original = active.state
    window.presenter.commit(window.presenter.bind(), task_id, "repetitions", "321")
    changed = active.state
    active.undo()
    assert active.state == original
    active.redo()
    window.save_project()
    observations[active.document.document_id] = None
    dialog = RotationDialog(repository, load_icons())
    try:
        previous = dialog.loaded
        assert previous is not None
        with patch.object(dialog, "_message"):
            dialog.save_button.click()
        assert dialog.loaded == previous
        assert repository.load_rotation_schemes() == (previous,)
    finally:
        dialog.close()
    with AssessmentProjectFile.open(destination) as project:
        assert project.format_version == 19
        assert project.load(active.document) == changed
        assert {
            identity: project.load_saved_result(
                DocumentKey(project.metadata.project_id, identity)
            )
            for identity in observations
        } == observations
        changed_scheme = replace(previous, description="Reviewed retained source")
        project.save_rotation_scheme(changed_scheme)
        with project.snapshot(str(tmp_path / "backup.ergprj"), None, None) as backup:
            assert {
                identity: backup.load_saved_result(
                    DocumentKey(backup.metadata.project_id, identity)
                )
                for identity in observations
            } == observations
            assert backup.load_rotation_schemes() == (changed_scheme,)
    with AssessmentProjectFile.open(tmp_path / "backup.ergprj") as backup:
        assert backup.format_version == 19
        assert backup.load(active.document) == changed
        assert {
            identity: backup.load_saved_result(
                DocumentKey(backup.metadata.project_id, identity)
            )
            for identity in observations
        } == observations


def test_historical_outputs_follow_original_inputs_not_save_state(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Recorded zeros/missing rows, edits, undo and reopen never imply fresh results.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.application.session import DocumentKey
    from ergotools.domain.model_units import MeasurementSystem

    assert mapped == old_source == rotated
    destination = tmp_path / "historical.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(
            window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
        ),
    ):
        window.open_project_location(str(mapped))
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(window, "choose_project_details", return_value=("Historical", "")),
    ):
        window.save_project()
    workspace = window.presenter.workspace
    recorded = workspace.historical_result()
    from ergotools.application.saved_results import calculate_saved_result

    assert recorded == calculate_saved_result(
        workspace.active.document,
        workspace.active.state,
        workspace.rotation_repository().metadata.default_units,
    )
    assert recorded is not None and recorded.damage != 0
    assert recorded.tasks[0].moment == 20
    assert recorded.calculation_status is not None
    assert window.task_panel.outputs[0][0].text() == "20.0"
    assert window.task_panel.outputs[1][0].text() == "0.0"
    assert window.results_sidebar.assessment_status_label.text() == "Ready"
    assert window.presenter.evaluator.current(workspace.active) is None
    window.units.setCurrentIndex(
        list(MeasurementSystem).index(MeasurementSystem.METRIC)
    )
    assert workspace.historical_result() == recorded
    classify_active_for_editing(window)
    active = workspace.active
    window.presenter.commit(
        window.presenter.bind(), active.state.tasks[0].task_id, "repetitions", "123"
    )
    assert workspace.historical_result() is None
    window.save_project()
    with AssessmentProjectFile.open(destination) as project:
        assert project.load_saved_result(active.document) is None
        with pytest.raises(ValueError):
            project.load_saved_result(DocumentKey("other", active.document.document_id))
    active.undo()
    window.refresh()
    assert workspace.historical_result() is None
    active.redo()
    window.refresh()
    assert workspace.historical_result() is None
    assert window.results_sidebar.assessment_status_label.text() != "Recorded"
    workspace.close(choice=CloseChoice.DISCARD)
    workspace.switch(str(destination), active.document.document_id)
    assert workspace.historical_result() is None


def test_open_options_describe_exact_original_owner_and_version(
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Human labels do not replace stable IDs or drop original context/version.

    Args:
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.bootstrap import desktop_document_options
    from ergotools.domain.language import Language
    from tools.project_migration.ergotools_migration.legacy_conversion import (
        convert_legacy_project,
    )

    assert mapped == old_source == rotated
    destination = tmp_path / "options.ergprj"
    with convert_legacy_project(mapped, destination, "p") as project:
        identity = project.list_assessments()[0].document.document_id
    for language in Language:
        options = desktop_document_options(str(destination), language)
        assert options[0][0] == identity
        assert options[0][1] == "LiFFT · w (ñ, Ada) · P/S/L/1/Day · #31"
        assert identity not in options[0][1]


def test_pending_input_hides_recorded_rows_and_cards(
    window: LifftWindow,
    mapped: Path,
    old_source: Path,
    rotated: Path,
    tmp_path: Path,
) -> None:
    """Uncommitted text must not display cached outputs for the previous inputs.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    assert mapped == old_source == rotated
    destination = tmp_path / "pending.ergprj"
    with (
        patch.object(window, "choose_file", return_value=str(destination)),
        patch.object(
            window, "choose_item", side_effect=lambda _, __, ids: (ids[0], True)
        ),
    ):
        window.open_project_location(str(mapped))
    workspace = window.presenter.workspace
    recorded = workspace.historical_result()
    panel, cards = window.task_panel, window.results_sidebar
    assert recorded is not None and cards.risk_gauge.has_value
    field = panel.inputs[0][2]
    previous = field.text()
    field.setText("invalid")
    field.textEdited.emit("invalid")
    assert panel.pending and workspace.historical_result() == recorded
    assert panel.outputs[0][0].text() == "0.0"
    assert cards.assessment_status_label.text() != "Recorded"
    assert not cards.risk_gauge.has_value
    assert not workspace.active.is_dirty
    field.setText(previous)
    field.textEdited.emit(previous)
    assert not panel.commit_inputs()
    panel.show_result()
    window.show_result()
    assert cards.assessment_status_label.text() == "Ready"
    assert panel.outputs[0][0].text() == "20.0"
    assert not workspace.active.is_dirty


def test_recorded_gauge_refresh_keeps_target_and_clears_missing_evidence(
    window: LifftWindow,
) -> None:
    """Refresh an unchanged result without restarting its animation or stale values.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    from dataclasses import replace

    from ergotools.application.historical_results import HistoricalAssessmentResult

    cards = window.results_sidebar
    source = window.presenter.workspace.active.state
    recorded = HistoricalAssessmentResult(source, 0.1, 51.41, ())
    cards.update_result(source, None, window.language, historical=recorded)
    gauge = cards.risk_gauge
    gauge.animation.setCurrentTime(gauge.animation.duration())
    assert gauge.target_value == gauge.display_value == 51.41
    cards.update_result(source, None, window.language, historical=recorded)
    assert gauge.target_value == gauge.display_value == 51.41
    assert not gauge.animation.state()
    assert "background:" in cards.damage_value_label.styleSheet()
    cards.update_result(
        source,
        None,
        window.language,
        historical=replace(recorded, damage=None, probability_percent=None),
    )
    assert not gauge.has_value and not cards.damage_progress.has_value
    assert cards.damage_value_label.text() == "—"
