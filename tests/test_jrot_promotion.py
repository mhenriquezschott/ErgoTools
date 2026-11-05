"""Production/Legacy entry separation, session options and lossless compatibility.

Native dialogs use private projects/settings. Tests assert normal routing without a
Developer switch, guarded pending input, independent Legacy visibility and exact guided
record preservation alongside edits to an older compatible scheme.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window, load_icons
from ergotools.domain.language import Language
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.domain.rotation_timing import RotationTiming
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from ergotools.presentation.desktop.legacy_jrot_dialog import LegacyJrotDialog
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_rotation_scenario_storage import scenario_workspace
from tests.test_rotation_scenarios import (
    balanced_rows,
    scenario_catalogs,
    scenario_inputs,
    scenario_with_run,
)
from tools.check_architecture import inspect_package

# Retain QApplication for owned modal preferences and deferred native widget cleanup.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_normal_toolbar_and_menu_open_guided_without_opt_ins(
    tmp_path: Path, language: Language
) -> None:
    """Normal toolbar/menu share production composition without sample-data writes.

    Args:
        tmp_path: Disposable project and personal settings directory.
        language: English or Spanish presentation, leaving literal data unchanged.

    Returns:
        None; opening and closing empty catalogs do not dirty or publish the project.
    """
    workspace = scenario_workspace(tmp_path)
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    main = create_window(tmp_path / "settings.json", original_navigation=True)
    try:
        main.presenter.workspace.switch(str(path), None)
        main.language = language
        main.translate()
        main.refresh()
        before = path.read_bytes()
        assert not main._developer_enabled and not main._legacy_enabled
        assert main.main_navigation is not None and main._assessment_menu is not None
        with (
            patch.object(JrotDialog, "exec", return_value=0) as guided,
            patch.object(
                LegacyJrotDialog, "exec", side_effect=AssertionError("wrong entry")
            ),
        ):
            main.main_navigation.toolbar_actions["jrot"].trigger()
            action = main._assessment_menu.tools.actions()[1]
            assert (
                main._assessment_menu.tools.actions()[0]
                is main.main_navigation.toolbar_actions["plot"]
            )
            assert action is main.main_navigation.toolbar_actions["jrot"]
            action.trigger()
            assert guided.call_count == 2
        assert (
            not main.presenter.workspace.rotation_scenarios().load_rotation_scenarios()
        )
        assert not main.presenter.workspace.has_unsaved_changes
        assert path.read_bytes() == before
        with (
            patch.object(main, "resolve_context_text", return_value=False),
            patch.object(
                JrotDialog, "exec", side_effect=AssertionError("unresolved input")
            ),
        ):
            main.open_rotation()
    finally:
        main.presenter.workspace.close(choice=CloseChoice.DISCARD)
        main.close()
        main.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize(
    "legacy,developer", [(False, False), (True, False), (False, True), (True, True)]
)
def test_independent_session_menu_visibility(
    tmp_path: Path, legacy: bool, developer: bool
) -> None:
    """Legacy and Developer switches remain independent and never enter settings files.

    Args:
        tmp_path: Private personal settings location, with no project loaded.
        legacy: Requested older-editor visibility.
        developer: Requested development visibility.

    Returns:
        None; neither mode enables JROT without a compatible project.
    """
    path = tmp_path / "settings.json"
    main = create_window(path, original_navigation=True)
    try:
        main.set_developer_mode(developer)
        main.set_legacy_mode(legacy)
        main.refresh_navigation()
        assert main._developer_menu is not None and main._legacy_menu is not None
        assert main._developer_menu.menuAction().isVisible() == developer
        assert main._legacy_menu.menuAction().isVisible() == legacy
        assert main._legacy_action is not None and not main._legacy_action.isEnabled()
        assert main.main_navigation is not None
        assert not main.main_navigation.toolbar_actions["jrot"].isEnabled()
        assert not path.exists()
    finally:
        main.close()
        main.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("flag", ["legacy_option", "developer_option"])
def test_settings_apply_cancel_and_restart_keep_menu_flags_session_only(
    tmp_path: Path, flag: str
) -> None:
    """Actual preference Apply changes only menu state; Cancel and restart are safe.

    Args:
        tmp_path: Private preferences directory, with no open project.
        flag: Session checkbox manipulated through the actual owned modal.

    Returns:
        None; existing application settings and project mutations are not invoked.
    """
    path = tmp_path / "settings.json"
    main = create_window(path, original_navigation=True)
    failures: list[BaseException] = []

    def choose(accept: bool) -> None:
        """Drive one modal checkbox and capture callback assertions outside Qt.

        Args:
            accept: Accept enabling, or cancel disabling, the requested menu flag.

        Returns:
            None; failures are asserted after modal lifetime rather than escaping Qt.
        """
        modal = _APP.activeModalWidget()
        try:
            assert isinstance(modal, PreferencesDialog)
            getattr(modal, flag).setChecked(accept)
            modal.accept() if accept else modal.reject()
        except BaseException as error:
            failures.append(error)
            if isinstance(modal, PreferencesDialog):
                modal.reject()

    try:
        with patch.object(
            main.presenter.workspace,
            "update_display_settings",
            side_effect=AssertionError("menu-only project mutation"),
        ):
            QTimer.singleShot(0, lambda: choose(True))
            main.open_preferences()
        assert not failures and not path.exists()
        attribute = (
            "_legacy_enabled" if flag == "legacy_option" else "_developer_enabled"
        )
        assert getattr(main, attribute)
        QTimer.singleShot(0, lambda: choose(False))
        main.open_preferences()
        assert not failures and getattr(main, attribute) and not path.exists()
        fresh = create_window(path, original_navigation=True)
        assert not fresh._legacy_enabled and not fresh._developer_enabled
        fresh.close()
        fresh.deleteLater()
    finally:
        main.close()
        main.deleteLater()
        _APP.processEvents()


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("model", [1, 2, 99])
def test_legacy_open_save_preserves_guided_evidence_and_blocks_identity_collision(
    tmp_path: Path, language: Language, model: int
) -> None:
    """Legacy sees only old schemes; saving another scheme retains guided run context.

    Args:
        tmp_path: Disposable mixed-codec current project.
        language: Owned compatibility-window captions.
        model: Current, historical or unsupported positive saved result contract.

    Returns:
        None; guided timing, rules, baseline and run survive Main Save/reopen.
    """
    workspace = scenario_workspace(tmp_path)
    repo = workspace.rotation_scenarios()
    _, jobs, risks = scenario_catalogs()
    for job in jobs.jobs:
        workspace.save_job_details(
            workspace.read_jobs(),
            workspace.read_job_risk(),
            job,
            risks.for_job(job.job_id),
        )
    source = scenario_with_run()
    assert source.run is not None
    source = replace(
        source,
        inputs=replace(
            source.inputs,
            timing=RotationTiming(480, (), (120, 360), equal_blocks=False),
            rules=(NoAdjacentHigh("W1"),),
            baseline=balanced_rows(source.inputs),
        ),
        run=replace(source.run, contract_version=model),
    )
    inputs = scenario_inputs()
    old = RotationScheme(
        "timing", "old", "Older", inputs.workers, inputs.targets, balanced_rows(inputs)
    )
    repo.save_rotation_scheme(old)
    repo.replace_rotation_scenario(None, source)
    assert workspace.save()
    path = Path(workspace.location)
    before = path.read_bytes()
    dialog = LegacyJrotDialog(
        repo, load_icons(), language=language, editing=workspace.editing
    )
    try:
        assert dialog.schemes == (old,)
        assert dialog.scheme_combo.findText(source.scenario_id) == -1
        assert source in repo.load_rotation_scenarios()
        with pytest.raises(ValueError, match="guided"):
            repo.save_rotation_scheme(replace(old, scheme_id=source.scenario_id))
        with pytest.raises(ValueError, match="guided"):
            repo.delete_rotation_scheme(source.scenario_id)
        assert path.read_bytes() == before
        assert dialog.grid is not None
        a, b = (target.key for target in old.targets)
        dialog.grid.set_choice(0, 1, None)
        dialog.grid.set_choice(1, 1, a)
        dialog.grid.set_choice(0, 1, b)
        dialog.accept_rotation_state()
        assert repo.load_rotation_schemes()[0].current != old.current
        assert (
            next(
                s
                for s in repo.load_rotation_scenarios()
                if s.scenario_id == source.scenario_id
            )
            == source
        )
        dialog.reject()
        assert workspace.save()
        assert workspace.switch(str(path), None)
        assert (
            next(
                s
                for s in workspace.rotation_scenarios().load_rotation_scenarios()
                if s.scenario_id == source.scenario_id
            )
            == source
        )
    finally:
        dialog.reject()
        dialog.deleteLater()
        workspace.close(choice=CloseChoice.DISCARD)
        _APP.processEvents()


def test_legacy_module_exception_does_not_allow_old_schema_readers(
    tmp_path: Path,
) -> None:
    """Only explicitly approved presentation modules may use the legacy prefix.

    Args:
        tmp_path: Private source tree for negative architecture probes.

    Returns:
        None; infrastructure and lookalike presentation converters remain rejected.
    """
    package = tmp_path / "ergotools"
    desktop = package / "presentation" / "desktop"
    desktop.mkdir(parents=True)
    accepted = desktop / "legacy_jrot_dialog.py"
    accepted.write_text('"""Compatibility presentation."""\n')
    assert inspect_package(package) == []
    rejected = desktop / "legacy_project.py"
    rejected.write_text('"""Unapproved reader."""\n')
    assert len(inspect_package(package)) == 1
    rejected.unlink()
    infrastructure = package / "infrastructure"
    infrastructure.mkdir()
    (infrastructure / "legacy_jrot_dialog.py").write_text(accepted.read_text())
    assert len(inspect_package(package)) == 1
