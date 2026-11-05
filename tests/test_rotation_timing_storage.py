"""Private timing persistence, expected-state guards, migration and shared replay.

Synthetic native projects contain only declared data; all operational/maintained
files stay unchanged. SQL row comparisons distinguish private edits from Main Save.
"""

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.rotation_timing import ShiftTimingTemplate, shift_clock
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation_timing import MinuteInterval, TimedBreak, equal_timing
from ergotools.domain.work_catalog import WorkCatalog
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.rotation_timing_store import (
    decode_rotation_timing,
    encode_rotation_timing,
)
from ergotools.infrastructure.settings_store import JsonSettingsStore
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)


def timing_hierarchy() -> WorkHierarchy:
    """Build independent day/night/full-day Shifts with complete recurring clocks.

    Args:
        None.

    Returns:
        Empty-location project hierarchy with only explicit recurring Shift metadata.
    """
    return WorkHierarchy(
        WorkCatalog("timing", (), (), ("Day", "Night", "Full")),
        organization=tuple(
            OrganizationRecord(
                OrganizationKind.SHIFT,
                (key,),
                (("start_time", start), ("end_time", end)),
            )
            for key, start, end in [
                ("Day", "08:00", "16:00"),
                ("Night", "22:00", "06:00"),
                ("Full", "08:00", "08:00"),
            ]
        ),
    )


def timing_workspace(tmp_path: Path) -> ProjectWorkspace[AssessmentDraft]:
    """Create an owned current project with private integrated editing and no sources.

    Args:
        tmp_path: Pytest-owned project/preferences directory.

    Returns:
        Open workspace; caller closes with explicit Discard after its assertions.
    """
    path = tmp_path / "timing.ergprj"
    with AssessmentProjectFile.create_empty(
        path, ProjectMetadata("timing", "Timing", MeasurementSystem.METRIC)
    ) as project:
        project.save_hierarchy(timing_hierarchy())
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
        unified_saving=True,
    )
    workspace.switch(str(path), None)
    return workspace


def test_template_private_history_save_as_backup_and_reopen(tmp_path: Path) -> None:
    """One source-independent template edit replays and publishes only through Save.

    Args:
        tmp_path: Private native project directory.

    Returns:
        None; backup excludes private timing while Save As retains its exact values.
    """
    workspace = timing_workspace(tmp_path)
    try:
        path = Path(workspace.location)
        before = path.read_bytes()
        assert workspace.load_shift_timings() == ()
        timing = equal_timing(480, 3, (TimedBreak(MinuteInterval(240, 300), "Lunch"),))
        workspace.replace_shift_timing("Day", None, timing)
        assert workspace.has_unsaved_changes and path.read_bytes() == before
        assert workspace.load_shift_timings() == (ShiftTimingTemplate("Day", timing),)
        assert workspace.editing.removals(redo=False) == frozenset(
            {("shift_timing", "Day")}
        )
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings() == ()
        assert workspace.editing.replay(redo=True)
        backup = tmp_path / "backup.ergprj"
        assert workspace.backup(str(backup)).completed
        with AssessmentProjectFile.open(backup) as project:
            assert project.load_shift_timings() == ()
        target = tmp_path / "copy.ergprj"
        assert workspace.save_as(str(target)).completed
        with AssessmentProjectFile.open(target) as project:
            assert project.load_shift_timings() == (ShiftTimingTemplate("Day", timing),)
            assert (
                project.list_assessments() == ()
                and project.load_rotation_schemes() == ()
            )
        assert path.read_bytes() == before
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_expected_state_and_clock_changes_protect_templates(tmp_path: Path) -> None:
    """Duration edits and deletion cannot silently reinterpret or orphan timing.

    Args:
        tmp_path: Private project directory.

    Returns:
        None; same-span clock moves work relatively, stale writes and bad spans fail.
    """
    workspace = timing_workspace(tmp_path)
    try:
        timing = equal_timing(480, 4)
        workspace.replace_shift_timing("Night", None, timing)
        with pytest.raises(ValueError, match="reload"):
            workspace.replace_shift_timing("Night", None, timing)
        snapshot = workspace.read_hierarchy()
        original = snapshot.hierarchy
        day_moved = replace(
            original,
            organization=tuple(
                replace(r, attributes=(("start_time", "23:00"), ("end_time", "07:00")))
                if r.keys == ("Night",)
                else r
                for r in original.organization
            ),
        )
        workspace.replace_hierarchy(snapshot, day_moved)
        assert (
            shift_clock(workspace.read_hierarchy().hierarchy, "Night").start_minute
            == 1380
        )
        snapshot = workspace.read_hierarchy()
        wrong = replace(
            day_moved,
            organization=tuple(
                replace(r, attributes=(("start_time", "23:00"), ("end_time", "08:00")))
                if r.keys == ("Night",)
                else r
                for r in day_moved.organization
            ),
        )
        with pytest.raises(ValueError, match="duration"):
            workspace.replace_hierarchy(snapshot, wrong)
        assert workspace.read_hierarchy().hierarchy == day_moved
        assert workspace.load_shift_timings()[0].timing == timing
        workspace.replace_shift_timing("Night", timing, None)
        snapshot = workspace.read_hierarchy()
        workspace.replace_hierarchy(snapshot, wrong)
        assert (
            shift_clock(workspace.read_hierarchy().hierarchy, "Night").span_minutes
            == 540
        )
        assert workspace.editing.replay(redo=False)
        assert workspace.editing.replay(redo=False)
        assert workspace.load_shift_timings()[0].timing == timing
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize(
    "mutation", ["unknown", "version", "fraction", "boolean", "duplicate", "overlap"]
)
def test_strict_timing_codec_rejects_corrupt_shapes(mutation: str) -> None:
    """No coercion, duplicate fields or overlapping break work enters native storage.

    Args:
        mutation: Deliberate codec/schema/timing corruption.

    Returns:
        None; exact valid roundtrip remains the reference.
    """
    timing = equal_timing(480, 4)
    payload = encode_rotation_timing(timing)
    assert decode_rotation_timing(payload) == timing
    data = json.loads(payload)
    if mutation == "unknown":
        data["unused"] = 1
    elif mutation == "version":
        data["version"] = True
    elif mutation == "fraction":
        data["block_minutes"][0] = 119.5
    elif mutation == "boolean":
        data["subtract_breaks"] = 1
    elif mutation == "overlap":
        data["breaks"] = [
            {"start": 1, "end": 20, "name": None},
            {"start": 10, "end": 30, "name": None},
        ]
    with pytest.raises(StoreFormatError):
        decode_rotation_timing(
            '{"format":"x","format":"y"}'
            if mutation == "duplicate"
            else json.dumps(data)
        )


def test_upgrade20_retains_named_sources_and_every_previous_table(
    tmp_path: Path,
) -> None:
    """Upgrade a disposable real format20 with exact source/result/catalog preservation.

    Args:
        tmp_path: Private input/output paths, never an operational migration target.

    Returns:
        None; only the native marker and new empty timing table differ.
    """
    from ergotools.application.saved_results import calculate_saved_result
    from ergotools.application.session import DocumentKey
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
    from tests.test_history_persistence import ENTRY, HIERARCHY, JOBS, META

    source, output = tmp_path / "old.ergprj", tmp_path / "new.ergprj"
    # Construct genuine prior-format data independently of the owner's editable project.
    with AssessmentProjectFile._create(source, META, version=20) as prior:
        prior.save_hierarchy(HIERARCHY)
        prior.save_jobs(JOBS)
        source_inputs = LifftDraft(
            MeasurementSystem.IMPERIAL, (LifftTask("1", 12, 10, 100),)
        )
        prior.create_historical_assessment(ENTRY, source_inputs)
        key = DocumentKey(META.project_id, ENTRY.document_id)
        result = calculate_saved_result(key, source_inputs, source_inputs.system)
        assert result is not None
        prior.save_result(key, result)
    # Give the private prior-format source a real reusable reference/result binding.
    from ergotools.application.task_catalog import label_assessment_task
    from ergotools.domain.task_catalog import TaskDefinition

    with AssessmentProjectFile.open(source) as prior:
        definitions = prior.load_task_definitions()
        definition = TaskDefinition("migration-name", "Pack cartons")
        prior.replace_task_definitions(definitions, (*definitions, definition))
        key = prior.list_assessments()[0].document
        result = prior.load_saved_result(key)
        named = label_assessment_task(
            prior.load(key),
            prior.load(key).tasks[0].task_id,
            definition.name,
            definition.definition_id,
        )
        if result is not None:
            prior.save_result(key, replace(result, source=named))
        else:
            prior.save(key, named)
    with closing(sqlite3.connect(source)) as copy:
        tables = [
            r[0]
            for r in copy.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if r[0] != "project_metadata"
        ]
        before = {t: copy.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables}
    initial_bytes = source.read_bytes()
    assert ExternalProjectMigration().requires_conversion(str(source))
    with upgrade_previous_project(source, output) as project:
        assert project.format_version == 24 and project.load_shift_timings() == ()
    assert not ExternalProjectMigration().requires_conversion(str(output))
    with closing(sqlite3.connect(output)) as converted:
        assert {
            t: converted.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables
        } == before
    assert source.read_bytes() == initial_bytes
    failure_output = tmp_path / "failure.ergprj"
    with (
        patch(
            "tools.project_migration.ergotools_migration.previous_project.create_rotation_timing_schema",
            side_effect=OSError("Injected schema failure"),
        ),
        pytest.raises(OSError),
    ):
        upgrade_previous_project(source, failure_output)
    assert not failure_output.exists() and source.read_bytes() == initial_bytes


def test_failed_template_write_does_not_create_history_or_publish(
    tmp_path: Path,
) -> None:
    """A real SQLite failure rolls back the new row and the shared project checkpoint.

    Args:
        tmp_path: Disposable project/preferences directory.

    Returns:
        None; failed writes leave durable bytes, source catalog and history unchanged.
    """
    workspace = timing_workspace(tmp_path)
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER fail_timing AFTER INSERT ON shift_timing_templates "
            "BEGIN SELECT RAISE(ABORT, 'Injected timing write failure'); END"
        )
    workspace.switch(str(path), None)
    try:
        before = path.read_bytes()
        with pytest.raises(sqlite3.IntegrityError, match="Injected"):
            workspace.replace_shift_timing("Day", None, equal_timing(480, 4))
        assert workspace.load_shift_timings() == ()
        assert workspace.editing.history.undo_label_key is None
        assert not workspace.has_unsaved_changes and path.read_bytes() == before
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_snapshot_retains_template_and_rejects_orphan_or_wrong_span(
    tmp_path: Path,
) -> None:
    """Complete native creation validates template ownership before publication.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; output includes timing exactly and invalid snapshots publish nothing.
    """
    from ergotools.infrastructure.project_snapshot import ProjectSnapshot

    workspace = timing_workspace(tmp_path)
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(path) as original:
        timing = ShiftTimingTemplate("Day", equal_timing(480, 3))
        snapshot = ProjectSnapshot(
            original.metadata,
            original.load_hierarchy(),
            original.load_jobs(),
            original.load_job_risk(),
            (),
            (),
            original.load_plot_positions(),
            (),
            shift_timings=(timing,),
        )
    target = tmp_path / "snapshot.ergprj"
    with AssessmentProjectFile.create_from_snapshot(target, snapshot) as project:
        assert project.load_shift_timings() == (timing,)
    for invalid in (
        ShiftTimingTemplate("Absent", timing.timing),
        ShiftTimingTemplate("Day", equal_timing(600, 3)),
    ):
        with pytest.raises(ValueError):
            replace(snapshot, shift_timings=(invalid,))
    with pytest.raises(ValueError, match="duplicate"):
        replace(snapshot, shift_timings=(timing, timing))


def test_combined_worker_write_cannot_orphan_shift_timing(tmp_path: Path) -> None:
    """The alternate atomic worker/hierarchy path enforces the same timing ownership.

    Args:
        tmp_path: Disposable native project directory.

    Returns:
        None; rejected combined writes preserve hierarchy, Jobs and timing exactly.
    """
    workspace = timing_workspace(tmp_path)
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    with AssessmentProjectFile.open(path) as project:
        timing = equal_timing(480, 4)
        project.replace_shift_timing("Day", None, timing)
        original, jobs = project.load_hierarchy(), project.load_jobs()
        removed = replace(
            original,
            work=replace(original.work, shifts=("Night", "Full")),
            organization=tuple(r for r in original.organization if r.keys != ("Day",)),
        )
        with pytest.raises(ValueError, match="before removing"):
            project.replace_worker_catalogs(original, removed, jobs, jobs)
        assert project.load_hierarchy() == original and project.load_jobs() == jobs
        assert project.load_shift_timings() == (ShiftTimingTemplate("Day", timing),)
