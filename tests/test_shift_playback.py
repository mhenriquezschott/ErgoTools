"""Known weighted exposure, paired map playback and developer-only native UI tests.

All editable test projects are disposable copies. The maintained demo is read only;
source bytes, positions, schemes and assessments must survive playback unchanged.
"""

import hashlib
from dataclasses import replace
from pathlib import Path
from shutil import copyfile

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from ergotools.application.shift_playback import (
    ShiftDestination,
    ShiftPlayback,
    playback_stages,
    prepare_shift,
)
from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_positions import PlotPoint
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_timing import MinuteInterval, RotationTiming, TimedBreak
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.presentation.desktop.plot_window import PlotWindow

# Keep one native Qt application alive across owned widgets and scene teardown.
_APP = QApplication.instance() or QApplication([])
# The owner-authorized fixture supplies task-based risks, map geometry and real solves.
_DEMO = Path("test_projects/native/shift_view_demo.ergprj")


def tiny_playback(subtract: bool = True) -> ShiftPlayback:
    """Give an exact two-Job duration example independent of calculators/solvers.

    Args:
        subtract: Exclude the ten-minute break from the fixed score divisor.

    Returns:
        One worker spends 30 minutes at zero and 60 at 90 percent risk.
    """
    timing = RotationTiming(
        100, (TimedBreak(MinuteInterval(30, 40), "Pause"),), (30, 60), False, subtract
    )
    return ShiftPlayback(
        "Known",
        "Plant",
        480,
        timing,
        (WorkerRotation("W1", ("A", "B")),),
        (
            ShiftDestination("A", "A", "Low", PlotPoint(0, 0), 0),
            ShiftDestination("B", "B", "High", PlotPoint(500, 0), 90),
        ),
        (("W1", "Example", None),),
        False,
    )


@pytest.mark.parametrize(
    ("elapsed", "expected"), [(0, 0), (30, 0), (35, 0), (40, 0), (70, 30), (100, 60)]
)
def test_known_partial_and_final_index(elapsed: float, expected: float) -> None:
    """Check progressive contribution and exact final weighted average.

    Args:
        elapsed: Real shift minute, including the break.
        expected: Known percentage-point contribution over ninety work minutes.

    Returns:
        None; no worker injury probability or break recovery is invented.
    """
    assert tiny_playback().index(0, elapsed) == pytest.approx(expected)
    assert tiny_playback(False).index(0, 100) == 54


def test_break_easing_and_no_break_transition() -> None:
    """Separate player seconds from exposure minutes and insert zero-gap movement.

    Args:
        None.

    Returns:
        None; break midpoint is halfway between locations with no exposure increment.
    """
    data = tiny_playback()
    assert data.phase(35) == (0, 1, 0.5)
    assert data.phase(100) == (1, 1, 0)
    stages = playback_stages(data, 2, 1)
    assert sum(s.seconds for s in stages) == 5
    no_break = replace(data, timing=RotationTiming(90, (), (30, 60), False, True))
    stages = playback_stages(no_break, 2, 1)
    assert stages[1].begin == stages[1].end == 30
    assert stages[1].seconds == 0.5
    with pytest.raises(ValueError):
        playback_stages(data, 0, 1)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_complete_demo_mapping_and_retained_constraints(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Verify exact destinations, paired coefficients and meaningful rule examples.

    Args:
        tmp_path: Disposable project directory.
        kind: Each tool uses its own task-based recorded risk values.

    Returns:
        None; all twenty targets are mapped and constraints change actual schedules.
    """
    path = tmp_path / "copy.ergprj"
    copyfile(_DEMO, path)
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        scenarios = project.load_rotation_scenarios()
        for scenario in scenarios:
            baseline = prepare_shift(project, scenario, kind, False)
            optimized = prepare_shift(project, scenario, kind, True)
            assert len(baseline.workers) == len(baseline.destinations) == 20
            assert baseline.destinations == optimized.destinations
            assert max(optimized.index(i, 600) for i in range(20)) < max(
                baseline.index(i, 600) for i in range(20)
            )
            assert all(
                c.measurement.source is not None for c in scenario.run.coefficients
            )
        restricted = scenarios[1].run
        assert restricted is not None
        high = {
            c.target_key
            for c in restricted.coefficients
            if c.measurement.probability_percent is not None
            and c.measurement.probability_percent > 50
        }
        assert any(
            a in high and b in high
            for row in restricted.inputs.baseline
            for a, b in zip(row.target_keys, row.target_keys[1:], strict=False)
        )
        assert not any(
            a in high and b in high
            for row in restricted.arrangement
            for a, b in zip(row.target_keys, row.target_keys[1:], strict=False)
        )
        scenario = scenarios[0]
        with pytest.raises(ValueError, match="timing"):
            prepare_shift(
                project,
                replace(
                    scenario,
                    run=None,
                    inputs=replace(scenario.inputs, timing=None, start_minute=None),
                ),
                kind,
                False,
            )
        with pytest.raises(ValueError, match="Keep"):
            prepare_shift(project, replace(scenario, run=None), kind, True)
    assert path.read_bytes() == before


def test_native_player_is_read_only_and_preserves_normal_modes(tmp_path: Path) -> None:
    """Exercise opt-in, seek, variant switching, finite playback and teardown.

    Args:
        tmp_path: Disposable native project; maintained file stays unchanged.

    Returns:
        None; player actions leave the complete project byte-identical.
    """
    path = tmp_path / "copy.ergprj"
    copyfile(_DEMO, path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with AssessmentProjectFile.open(path) as project:
        normal = PlotWindow(
            project,
            project,
            project,
            lambda p: import_plant_image(Path(p)),
            load_icons(),
            current_year=2026,
        )
        assert normal.shift_button.isHidden()
        normal.close()
        dialog = PlotWindow(
            project,
            project,
            project,
            lambda p: import_plant_image(Path(p)),
            load_icons(),
            current_year=2026,
            shift_repository=project,
        )
        dialog.show()
        dialog.shift_button.click()
        player = dialog.shift_player
        assert player is not None and player.data is not None
        assert player.active and len(player.people) == 20
        player.variant.setFocus()
        _APP.processEvents()
        assert not dialog.history_actions.undo_action.isEnabled()
        assert not dialog.history_actions.redo_action.isEnabled()
        fixed = [(g.pos(), g.color.name()) for g in player.glyphs if g.job]
        player.seek(300)
        assert player.elapsed == 300
        player.variant.setCurrentIndex(1)
        assert player.elapsed == 300 and player.data is not None
        dialog.filters.tools.select_tool(AssessmentKind.DUET)
        dialog.filters.apply_filters()
        assert player.elapsed == 300
        assert [p for p, _c in fixed] == [g.pos() for g in player.glyphs if g.job]
        fixed = [(g.pos(), g.color.name()) for g in player.glyphs if g.job]
        player.speed.setValue(0.5)
        player.motion.setValue(0.3)
        assert player.elapsed == 300
        player.toggle()
        QTest.qWait(80)
        assert player.elapsed > 300
        player.pause()
        player.seek(600)
        assert fixed == [(g.pos(), g.color.name()) for g in player.glyphs if g.job]
        assert all(not g.flags() & g.ItemIsMovable for g in player.glyphs)
        player.stop()
        assert player.elapsed == 0
        dialog.filters.risk_buttons[dialog.filters.risk_view].click()
        assert not player.active and not player.timer.isActive()
        assert dialog.layer.results is not None
        dialog.close()
        _APP.processEvents()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_integrated_shift_view_never_dirties_project_history(tmp_path: Path) -> None:
    """Keep the real shared editing session clean through playback and mode return.

    Args:
        tmp_path: Disposable native file and personal preferences.

    Returns:
        None; neither opaque project state nor Undo history changes.
    """
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.application.project_workspace import ProjectWorkspace
    from ergotools.infrastructure.settings_store import JsonSettingsStore

    path = tmp_path / "demo.ergprj"
    copyfile(_DEMO, path)
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
        unified_saving=True,
    )
    workspace.switch(str(path), "worker-1-lifft")
    editing = workspace.editing
    assert editing is not None
    repository = workspace.plot_repository()
    dialog = PlotWindow(
        repository,
        repository,
        repository,
        lambda p: import_plant_image(Path(p)),
        load_icons(),
        current_year=2026,
        shift_repository=repository,
        editing=editing,
    )
    dialog.show()
    _APP.processEvents()
    before = editing.history.state.data
    assert not workspace.has_unsaved_changes
    dialog.shift_button.click()
    player = dialog.shift_player
    assert player is not None
    player.seek(280)
    player.variant.setCurrentIndex(1)
    player.seek(600)
    player.leave()
    assert editing.history.state.data == before
    assert not workspace.has_unsaved_changes
    dialog.close()
    workspace.close(choice=CloseChoice.DISCARD)
