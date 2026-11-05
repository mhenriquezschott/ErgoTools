"""HiGHS-only execution with unchanged scientific models and ownership.

Only private preferences/projects are used. Independent finite enumeration verifies
minimax and secondary spread; preference migration discards the retired choice.
"""

import json
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QDialog

from ergotools.application.settings import UserSettings
from ergotools.bootstrap import open_guided_jrot
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.rotation import RotationBackend, RotationProblem
from ergotools.domain.rotation_constraints import (
    ExcludedPosition,
    FixedPosition,
    NoAdjacentHigh,
)
from ergotools.infrastructure.highs_rotation_optimizer import (
    HighsRotationOptimizer,
    HighsRotationPlanner,
)
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.presentation.desktop.jrot_dialog import JrotDialog
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.preferences_dialog import PreferencesDialog
from tests.test_rotation_optimization import averages, feasible_schedules
from tests.test_rotation_optimization import problem as problem
from tests.test_rotation_planning import enumerate_scores, planning
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("rule", ("none", "fixed", "excluded", "adjacent"))
def test_highs_single_tool_matches_independent_two_stage_oracle(
    kind: AssessmentKind, rule: str
) -> None:
    """All single tools and hard rules retain the exact weighted two-stage objectives.

    Args:
        kind: Selected scientific tool.
        rule: Independent fixed/excluded/adjacency case, or unrestricted case.

    Returns:
        None; the HiGHS schedule attains exhaustive minimax and its minimum spread.
    """
    problem = planning(((0, 35, 60),), (30, 90, 120), (kind,))
    worker = problem.worker_ids[0]
    rules = {
        "none": (),
        "fixed": (FixedPosition(worker, problem.target_keys[0]),),
        "excluded": (ExcludedPosition(worker, problem.target_keys[2]),),
        "adjacent": tuple(NoAdjacentHigh(w) for w in problem.worker_ids),
    }[rule]
    problem = replace(problem, inputs=replace(problem.inputs, rules=rules))
    oracle = min((max(s[0]), max(s[0]) - min(s[0])) for s in enumerate_scores(problem))
    result = HighsRotationPlanner().solve(problem)
    problem.validate_schedule(result.schedule)
    scores = problem.scores(result.schedule, kind)
    assert result.backend is RotationBackend.HIGHS and len(result.stages) == 2
    assert (max(scores), max(scores) - min(scores)) == pytest.approx(
        tuple(map(float, oracle)), abs=0.0001
    )


@pytest.mark.parametrize("generation", (False, True))
@pytest.mark.parametrize(
    "tools", [t for n in (1, 2, 3) for t in combinations(tuple(AssessmentKind), n)]
)
def test_highs_comparison_covers_every_tool_subset(
    tools: tuple[AssessmentKind, ...],
    generation: bool,
) -> None:
    """One-, two- and three-tool paths use real HiGHS with complete weighted staffing.

    Args:
        tools: Every nonempty selected-tool combination.
        generation: Feasibility proposal or the ordinary two-stage optimization.

    Returns:
        None; model validation and the known unequal-block lower bound hold.
    """
    problem = replace(
        planning(tuple((0, 60) for _ in tools), (30, 90), tools),
        generation=generation,
    )
    result = HighsRotationPlanner().solve(problem)
    problem.validate_schedule(result.schedule)
    assert result.backend is RotationBackend.HIGHS
    if not generation:
        for kind in tools:
            assert sorted(problem.scores(result.schedule, kind)) == pytest.approx(
                [15, 45]
            )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_legacy_single_tool_highs_matches_existing_model(
    problem: RotationProblem, kind: AssessmentKind
) -> None:
    """The optional legacy adapter changes backend only and preserves its objective.

    Args:
        problem: Tiny native-free original model fixture.
        kind: Each existing single-tool optimization method.

    Returns:
        None; real HiGHS attains the independent original minimax without CBC.
    """
    expected = min(
        max(averages(problem, rows, kind)) for rows in feasible_schedules(problem)
    )
    result = HighsRotationOptimizer().optimize_single_tool(problem, kind)
    problem.validate_schedule(result.schedule)
    assert result.backend is RotationBackend.HIGHS
    assert max(averages(problem, result.schedule, kind)) == pytest.approx(expected)


@pytest.mark.parametrize("old_choice", [False, True])
def test_retired_solver_choice_is_discarded_on_settings_upgrade(
    tmp_path: Path, old_choice: bool
) -> None:
    """Read old personal settings without retaining any selectable solver option.

    Args:
        tmp_path: Private preference folder.
        old_choice: Either previously accepted version10 comparison-switch state.

    Returns:
        None; unrelated preferences survive, read does not write, version11 omits
        the retired key, and reintroducing it into current settings is rejected.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    original = UserSettings(undo_limit=17)
    store.save(original)
    payload = json.loads(path.read_text())
    payload.update(version=10, highs_single_tool=old_choice)
    path.write_text(json.dumps(payload))
    before = path.read_bytes()
    assert store.load() == original and path.read_bytes() == before
    assert not hasattr(store.load(), "highs_single_tool")
    store.save(store.load())
    saved = json.loads(path.read_text())
    assert saved["version"] == 11 and "highs_single_tool" not in saved
    path.write_text(json.dumps({**saved, "highs_single_tool": True}))
    with pytest.raises(SettingsFormatError):
        store.load()


def test_settings_has_no_solver_switch_and_cancel_preserves_pending_inputs(
    window: LifftWindow,
) -> None:
    """Settings exposes neither an active nor a legacy solver-choice control.

    Args:
        window: Disposable integrated owner with private settings and project data.

    Returns:
        None; Cancel preserves pending invalid input and exact document/history state.
    """
    workspace = window.presenter.workspace
    original = workspace.active.state
    revision = workspace.editing.history.revision
    field = window.task_panel.inputs[0][0]
    field.setText("unfinished")
    field.textEdited.emit("unfinished")
    settings = window._settings_store.load()

    def inspect(dialog: PreferencesDialog) -> int:
        """Reject the actual preferences form after checking obsolete UI is absent.

        Args:
            dialog: Real owned preferences editor.

        Returns:
            Rejected without accepting any preference or pending input.
        """
        assert not hasattr(dialog, "highs_single_tool")
        assert not hasattr(dialog, "only_solver_changed")
        return QDialog.Rejected

    with patch.object(PreferencesDialog, "exec", inspect):
        window.open_preferences()
    assert field.text() == "unfinished" and workspace.active.state == original
    assert workspace.editing.history.revision == revision
    assert window._settings_store.load() == settings


def test_guided_composition_always_uses_direct_highs(window: LifftWindow) -> None:
    """Production composition has one direct solver and no preference routing.

    Args:
        window: Borrowed private integrated owner.

    Returns:
        None; opening creates no accepted result or project data.
    """

    def inspect(dialog: JrotDialog) -> int:
        """Inspect the real newly composed planner without accepting edits.

        Args:
            dialog: Owned production guided JROT form.

        Returns:
            Rejected after confirming the only runtime adapter has no engine option.
        """
        assert isinstance(dialog.solve.optimizer, HighsRotationPlanner)
        assert not hasattr(dialog.solve.optimizer, "single_tool_backend")
        return QDialog.Rejected

    with patch.object(JrotDialog, "exec", inspect):
        open_guided_jrot(
            Language.ENGLISH,
            DecimalConvention.POINT,
            window,
            workspace=window.presenter.workspace,
            settings_store=window._settings_store,
        )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_guided_highs_worker_keep_and_reopen(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Real Qt worker accepts selected HiGHS evidence and retains it without CBC.

    Args:
        tmp_path: Disposable complete rotation project.
        kind: Each single-tool guided route.

    Returns:
        None; explicit Keep/Save/reopen preserves actual backend and original baseline.
    """
    from ergotools.application.rotation_entry import RotationEntryChange
    from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
    from tests.test_jrot_planning_ui import await_result, dispose, planning_dialog

    dialog = planning_dialog(tmp_path, Language.ENGLISH)
    try:
        original = dialog.current()
        dialog.edit_inputs(
            original, RotationEntryChange(replace(original.inputs, tools=(kind,)))
        )
        dialog.solve.optimizer = HighsRotationPlanner()
        dialog.solve.start()
        await_result(dialog)
        assert dialog.solve.preview.backend is RotationBackend.HIGHS
        assert dialog.current().inputs.baseline == original.inputs.baseline
        dialog.solve.keep_result()
        assert dialog.workspace.save()
        with AssessmentProjectFile.open(Path(dialog.workspace.location)) as project:
            restored = next(
                r
                for r in project.load_rotation_scenarios()
                if r.scenario_id == dialog.current().scenario_id
            )
            assert restored.run.backend is RotationBackend.HIGHS
            assert restored.inputs.baseline == original.inputs.baseline
    finally:
        dispose(dialog)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_legacy_highs_worker_evidence(
    problem: RotationProblem, kind: AssessmentKind
) -> None:
    """The legacy Qt worker validates the declared comparison backend, not fixed CBC.

    Args:
        problem: Native-free original mathematical fixture.
        kind: Each single-tool legacy route.

    Returns:
        None; validated real HiGHS evidence survives the owned worker boundary.
    """
    from PyQt5.QtCore import QObject

    from ergotools.presentation.desktop.legacy_jrot_solve import _SolveThread

    parent = QObject()
    worker = _SolveThread(HighsRotationOptimizer(), problem, kind, parent)
    worker.start()
    assert worker.wait(10000)
    assert not worker.failed and worker.solution.backend is RotationBackend.HIGHS


@pytest.mark.parametrize("language", list(Language))
def test_workflow_actions_have_legible_icons_and_shared_step_glyphs(
    tmp_path: Path, language: Language
) -> None:
    """Workflow commands expose artwork at useful sizes without changing callbacks.

    Args:
        tmp_path: Private populated rotation project.
        language: Both maintained caption languages, including longer Spanish labels.

    Returns:
        None; every step has a title glyph and result actions use above-caption artwork.
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QLabel, QPushButton

    from tests.test_jrot_planning_ui import dispose, planning_dialog

    dialog = planning_dialog(tmp_path, language)
    try:
        for index in range(8):
            title_icon = dialog.findChild(QLabel, f"stepIcon{index + 1}")
            assert title_icon is not None and not title_icon.pixmap().isNull()
        for button in (
            dialog.back,
            dialog.next,
            dialog.solve.start_button,
            dialog.solve.cancel_button,
            dialog.solve.discard_button,
        ):
            assert not button.icon().isNull() and button.iconSize().width() >= 28
        for button in (
            dialog.comparison.keep_button,
            dialog.comparison.rework_button,
            dialog.comparison.replace_button,
            dialog.comparison.report_button,
        ):
            assert (
                button.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonTextUnderIcon
            )
            assert button.iconSize().width() >= 40 and button.minimumHeight() >= 80
        dialog.go(4)
        assert all(
            not button.icon().isNull() for button in dialog.job_panel.modes.buttons()
        )
        caption = dialog.text("New rotation", "Nueva rotación")
        assert (
            not next(b for b in dialog.findChildren(QPushButton) if b.text() == caption)
            .icon()
            .isNull()
        )
    finally:
        dispose(dialog)
