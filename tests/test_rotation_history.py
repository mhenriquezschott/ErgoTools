"""JROT partial source history and actual solver Apply/Undo/persistence contracts.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QTableWidgetSelectionRange

from ergotools.application.rotation_history import ReplaceRotationEdit
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import RotationMode
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.pulp_rotation_optimizer import PulpRotationOptimizer
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from tests.test_rotation_comparison import all_risks
from tests.test_rotation_dialog import fill
from tests.test_rotation_persistence import seed
from tests.test_rotation_solve import fill_rotation, wait_for

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


@pytest.mark.parametrize("language", list(Language))
def test_partial_grid_delete_batch_branch_and_save_failure(
    tmp_path: Path, language: Language
) -> None:
    """Incomplete cell edits, one Delete batch and failed Save retain exact intent.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    path = tmp_path / "partial.ergprj"
    with seed(path) as project, patch.object(RotationDialog, "_message"):
        dialog = RotationDialog(project, load_icons(), language=language)
        dialog.new_scheme()
        initial = dialog.history.state
        fill(dialog, "history")
        filled = dialog.history.state
        grid = dialog.grid
        grid.setRangeSelected(QTableWidgetSelectionRange(0, 1, 0, grid.blocks), True)
        before = dialog.history.revision
        grid.clear_selected()
        assert dialog.history.revision == before + 1
        dialog.history_actions.refresh()
        dialog.history_actions.undo_button.click()
        assert dialog.history.state == filled
        dialog.history_actions.redo_button.click()
        assert dialog.grid.choice_key(0, 1) is None
        dialog.replay_history(redo=False)
        redo = dialog.history.redo_label_key
        dialog.grid.set_choice(0, 1, dialog.grid.choice_key(0, 1))
        assert dialog.history.redo_label_key == redo
        with (
            patch.object(
                project, "save_rotation_scheme", side_effect=OSError("disk full")
            ),
            pytest.raises(OSError),
        ):
            dialog.save_scheme()
        assert dialog.history.is_dirty and dialog.history.state == filled
        dialog.save_scheme()
        saved = project.load_rotation_schemes()[0]
        assert not dialog.history.is_dirty
        dialog.replay_history(redo=False)
        assert dialog.history.is_dirty and project.load_rotation_schemes() == (saved,)
        dialog.replay_history(redo=True)
        assert not dialog.history.is_dirty
        while dialog.history.undo_label_key is not None:
            dialog.replay_history(redo=False)
        assert dialog.history.state == initial
        dialog.grid.set_choice(0, 0, "x")
        assert dialog.history.redo_label_key is None
        dialog.cancel_scheme()
        assert dialog.loaded == saved and dialog.history.undo_label_key is None
        dialog.close()


@pytest.mark.parametrize("all_tools", [False, True])
@pytest.mark.parametrize("language", list(Language))
def test_actual_apply_one_command_undo_redo_save_reopen(
    tmp_path: Path, all_tools: bool, language: Language
) -> None:
    """CBC/HiGHS application restores exact schedules, metadata and frozen links.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        all_tools: True exercises HiGHS multi-tool routing; False exercises CBC
            single-tool routing.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    path = tmp_path / "apply.ergprj"
    with seed(path) as project, patch.object(RotationDialog, "_message"):
        all_risks(project)
        dialog = RotationDialog(
            project, load_icons(), optimizer=PulpRotationOptimizer(), language=language
        )
        fill_rotation(dialog)
        before = path.read_bytes()
        state = dialog.history.state
        revision = dialog.history.revision
        controller = dialog.optimization
        if all_tools:
            controller.start_all()
        else:
            controller.start()
        wait_for(lambda: not controller.busy)
        assert dialog.history.revision == revision
        if all_tools:
            controller.comparison.apply_button.click()
        else:
            controller.transfer()
        applied = dialog.history.state
        assert applied.mode is (
            RotationMode.ALL_TOOLS if all_tools else RotationMode.SINGLE_TOOL
        )
        assert applied.primary_kind is (None if all_tools else AssessmentKind.LIFFT)
        assert dialog.history.revision == revision + 1 and path.read_bytes() == before
        dialog.replay_history(redo=False)
        assert dialog.history.state == state
        assert dialog.grid.current_scheme("test").current != tuple(
            WorkerRotation(row[0], row[1:]) for row in applied.cells
        )
        dialog.replay_history(redo=True)
        assert dialog.history.state == applied
        assert controller.applied_mode is applied.mode
        dialog.select_kind(AssessmentKind.DUET)
        assert dialog.history.state == replace(
            applied, display_kind=AssessmentKind.DUET
        )
        dialog.save_scheme()
        saved = project.load_rotation_schemes()[0]
        assert saved.mode is applied.mode and saved.primary_kind is applied.primary_kind
        assert {t.job_id for t in saved.targets} == {"j", "k"}
        assert not dialog.history.is_dirty
        dialog.replay_history(redo=False)
        assert project.load_rotation_schemes() == (saved,)
        dialog.replay_history(redo=True)
        dialog.save_scheme()
        assert project.load_rotation_schemes() == (saved,)
        dialog.close()
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_rotation_schemes() == (saved,)


def test_history_rejects_foreign_stale_and_native_typing_ownership(
    tmp_path: Path,
) -> None:
    """Identity validation and text shortcuts cannot replay unrelated grid changes.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "keys.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        dialog = RotationDialog(project, load_icons())
        dialog.show()
        fill(dialog, "keys")
        session = dialog.history
        state = session.state
        with pytest.raises(ValueError):
            ReplaceRotationEdit(DocumentKey("foreign", "rotation"), state, state).apply(
                state
            )
        with pytest.raises(ValueError):
            ReplaceRotationEdit(
                session.document, replace(state, manual_edit=False), state
            ).apply(state)
        field = dialog.scheme_combo.lineEdit()
        dialog.activateWindow()
        QTest.qWait(80)
        field.setFocus()
        _APP.processEvents()
        field.setText("clean")
        QTest.keyClick(field, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
        assert session.state == state
        QTest.keyClicks(field, "typed")
        dialog.history_actions.replay(redo=False)
        assert field.text() == "clean" and session.state == state
        dialog.grid.setFocus()
        _APP.processEvents()
        dialog.history_actions.replay(redo=False)
        assert session.state != state
        dialog.history_actions.replay(redo=True)
        assert session.state == state
        dialog.close()


def test_scope_undo_restores_frozen_pool_and_pending_selection(tmp_path: Path) -> None:
    """Applied scope is one edit; undo restores exact prior choices and links.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "scope-history.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        dialog = RotationDialog(project, load_icons(), language=Language.SPANISH)
        fill(dialog, "scope-history")
        dialog.save_scheme()
        original = dialog.history.state
        contexts = project.load_hierarchy().work.available_workplaces()
        dialog.pending_scope = (contexts[0],)
        dialog.workplace_scope_button.setChecked(True)
        dialog.apply_scope()
        scoped = dialog.history.state
        assert scoped.scope == (contexts[0],) and scoped.pool != original.pool
        dialog.replay_history(redo=False)
        assert dialog.history.state == original
        assert dialog.grid.pool == original.pool and dialog.scope == ()
        dialog.replay_history(redo=True)
        assert dialog.history.state == scoped
        assert dialog.pending_scope == scoped.scope
        dialog.cancel_scheme()
        assert dialog.history.state.cells == original.cells
        assert dialog.history.undo_label_key is None
        dialog.close()


def test_undo_manual_save_restores_loaded_optimization_provenance(
    tmp_path: Path,
) -> None:
    """Undo after Save can restore original optimized provenance without a solver.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "saved-provenance.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        from tests.test_rotation_persistence import scheme

        optimized = replace(
            scheme(), mode=RotationMode.SINGLE_TOOL, primary_kind=AssessmentKind.LIFFT
        )
        project.save_rotation_scheme(optimized)
        dialog = RotationDialog(project, load_icons())
        initial = dialog.history.state
        dialog.grid.set_choice(0, 1, None)
        dialog.grid.set_choice(0, 1, initial.cells[0][1])
        dialog.save_scheme()
        assert project.load_rotation_schemes()[0].mode is RotationMode.MANUAL
        dialog.replay_history(redo=False)
        dialog.replay_history(redo=False)
        assert dialog.history.state == initial
        dialog.save_scheme()
        assert project.load_rotation_schemes() == (optimized,)
        dialog.close()


def test_cancel_empty_delete_and_owned_solve_history_boundaries(tmp_path: Path) -> None:
    """Cancelled/deleted drafts cannot replay, and owned solves block Undo.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from tests.test_rotation_solve import ControlledOptimizer

    with (
        seed(tmp_path / "boundaries.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        all_risks(project)
        solver = ControlledOptimizer()
        dialog = RotationDialog(project, load_icons(), optimizer=solver)
        fill(dialog, "discard")
        dialog.cancel_scheme()
        assert dialog.history.undo_label_key is None
        fill_rotation(dialog)
        state = dialog.history.state
        controller = dialog.optimization
        controller.start()
        try:
            wait_for(solver.started.is_set)
            assert not dialog.history_actions.undo_action.isEnabled()
            dialog.replay_history(redo=False)
            dialog.history_actions.replay(redo=False)
            assert dialog.history.state == state
            controller.cancel()
        finally:
            solver.release.set()
            wait_for(lambda: not controller.busy)
        assert controller.preview is None and dialog.history.state == state
        dialog.save_scheme()
        with patch.object(dialog, "_confirm_delete", return_value=True):
            dialog.delete_scheme()
        assert (
            dialog.history.undo_label_key is None
            and project.load_rotation_schemes() == ()
        )
        dialog.close()
