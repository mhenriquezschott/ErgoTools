"""Private scenario persistence, old-row preservation and shared project lifecycle.

Synthetic and copied native projects exercise expected-state transactions, rollback,
selection, reference protection and sole main Save. No maintained file is a mutation or
migration test target. Old source/result rows and old rotation payloads stay exact.
"""

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.rotation_scenarios import (
    create_scenario,
    duplicate_scenario,
    opening_scenario,
)
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.display_precision import DisplayPrecision
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.organization_record import OrganizationKind
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.domain.rotation_timing import equal_timing
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.project_snapshot import ProjectSnapshot
from ergotools.infrastructure.settings_store import JsonSettingsStore
from tests.test_rotation_scenarios import (
    balanced_rows,
    scenario_catalogs,
    scenario_inputs,
    scenario_with_run,
)
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)


def scenario_workspace(tmp_path: Path) -> ProjectWorkspace[AssessmentDraft]:
    """Create a native current project with two named workers/Jobs, no saved rotations.

    Args:
        tmp_path: Disposable test directory.

    Returns:
        Open unified workspace; the caller closes it with explicit Discard.
    """
    path = tmp_path / "scenarios.ergprj"
    hierarchy, jobs, _ = scenario_catalogs()
    with AssessmentProjectFile.create_empty(
        path, ProjectMetadata("timing", "Scenarios", MeasurementSystem.METRIC)
    ) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(jobs)
    workspace: ProjectWorkspace[AssessmentDraft] = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
        unified_saving=True,
    )
    workspace.switch(str(path), None)
    return workspace


def test_create_rename_duplicate_delete_replays_and_only_main_save_publishes(
    tmp_path: Path,
) -> None:
    """Scenario and selection form coherent shared history edits through Save/reopen.

    Args:
        tmp_path: Disposable current project directory.

    Returns:
        None; old/current inputs and immutable run evidence survive private replay/copy.
    """
    workspace = scenario_workspace(tmp_path)
    try:
        path = Path(workspace.location)
        before = path.read_bytes()
        repo = workspace.rotation_scenarios()
        assert (
            repo.load_rotation_scenarios() == ()
            and repo.last_rotation_selection() is None
        )
        assert not workspace.has_unsaved_changes and path.read_bytes() == before
        source = scenario_with_run()
        repo.replace_rotation_scenario(None, source)
        assert repo.last_rotation_selection() == source.scenario_id
        assert workspace.editing.removals(redo=False) == frozenset(
            {("rotation", source.scenario_id)}
        )
        renamed = replace(source, name="Renamed", description="Retained calculation")
        repo.replace_rotation_scenario(source, renamed)
        assert renamed.run == source.run and workspace.editing.replay(redo=False)
        assert repo.load_rotation_scenarios() == (source,)
        assert workspace.editing.replay(redo=True)
        duplicate = duplicate_scenario(
            renamed,
            "alternative",
            "Alternative",
            date(2026, 11, 3),
            use_optimized_baseline=True,
        )
        repo.replace_rotation_scenario(None, duplicate)
        assert repo.last_rotation_selection() == "alternative"
        repo.replace_rotation_scenario(duplicate, None)
        assert repo.last_rotation_selection() is None
        assert workspace.editing.replay(redo=False)
        assert repo.last_rotation_selection() == "alternative"
        assert repo.load_rotation_scenarios() == (duplicate, renamed)
        backup = tmp_path / "baseline.ergprj"
        assert workspace.backup(str(backup)).completed
        with AssessmentProjectFile.open(backup) as project:
            assert project.load_rotation_scenarios() == ()
        assert path.read_bytes() == before
        saved = tmp_path / "saved.ergprj"
        assert workspace.save_as(str(saved)).completed
        with AssessmentProjectFile.open(saved) as project:
            assert (
                project.format_version == 24
                and project.load_rotation_scenarios() == (duplicate, renamed)
            )
            assert project.last_rotation_selection() == "alternative"
            assert project.load_rotation_schemes() == ()
            assert (
                project.load_jobs().assignments == ()
                and project.list_assessments() == ()
            )
        assert path.read_bytes() == before
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_last_viewed_fallback_and_other_display_updates_preserve_run(
    tmp_path: Path,
) -> None:
    """View selection is independently saved and never manufactures a scenario/run.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; display edits retain selection; stale choices use read-only fallback.
    """
    workspace = scenario_workspace(tmp_path)
    try:
        repo = workspace.rotation_scenarios()
        a = scenario_with_run()
        b = create_scenario("timing", "b", "Alpha", date(2026, 11, 2))
        repo.replace_rotation_scenario(None, a)
        repo.replace_rotation_scenario(None, b)
        repo.select_rotation_scenario(a.scenario_id)
        assert (
            opening_scenario(
                repo.load_rotation_scenarios(), repo.last_rotation_selection()
            )
            == a
        )
        with pytest.raises(ValueError):
            repo.select_rotation_scenario("missing")
        project = repo
        metadata = project.metadata
        project.update_display_settings(
            replace(
                metadata,
                precision=DisplayPrecision(2, 2, 2, 5, 2),
                assessment_context_expanded=True,
            )
        )
        assert repo.last_rotation_selection() == a.scenario_id
        assert repo.load_rotation_scenarios() == (b, a)
        assert workspace.save()
        with AssessmentProjectFile.open(Path(workspace.location)) as saved:
            assert saved.last_rotation_selection() == a.scenario_id
            assert saved.metadata.assessment_context_expanded is True
        repo.select_rotation_scenario(None)
        assert opening_scenario(repo.load_rotation_scenarios(), None) == b
        assert workspace.editing.replay(redo=False)
        assert repo.last_rotation_selection() == a.scenario_id
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize(
    "case",
    [
        "stale",
        "identity",
        "foreign",
        "missing_worker",
        "missing_job",
        "missing_shift",
        "missing_line",
        "empty_edit",
    ],
)
def test_invalid_or_stale_changes_leave_catalog_history_and_bytes_exact(
    tmp_path: Path, case: str
) -> None:
    """No invalid expected-state or reference edit can partially change accepted data.

    Args:
        tmp_path: Disposable current project directory.
        case: Deliberate ownership/reference/expected-state failure.

    Returns:
        None; shared history revision and durable bytes stay unchanged.
    """
    from ergotools.domain.rotation_scheme import RotationTarget, RotationWorkerLink
    from ergotools.domain.work_hierarchy import LineKey

    workspace = scenario_workspace(tmp_path)
    try:
        repo = workspace.rotation_scenarios()
        source = scenario_with_run()
        repo.replace_rotation_scenario(None, source)
        before = Path(workspace.location).read_bytes()
        revision = workspace.editing.history.revision
        expected, replacement = source, replace(source, name="Edited")
        if case == "stale":
            expected = replace(source, name="Not current")
        elif case == "identity":
            replacement = replace(source, scenario_id="another")
        elif case == "foreign":
            replacement = replace(source, project_id="foreign")
        elif case == "missing_worker":
            replacement = replace(
                source,
                inputs=replace(
                    source.inputs,
                    baseline=None,
                    workers=(RotationWorkerLink("absent"),),
                ),
            )
        elif case == "missing_job":
            replacement = replace(
                source,
                inputs=replace(source.inputs, targets=(RotationTarget("absent"),)),
            )
        elif case == "missing_shift":
            replacement = replace(
                source, inputs=replace(source.inputs, shift_id="absent")
            )
        elif case == "missing_line":
            replacement = replace(
                source,
                inputs=replace(
                    source.inputs, line=LineKey("absent", "section", "line")
                ),
            )
        else:
            expected = replacement = None
        with pytest.raises(ValueError):
            repo.replace_rotation_scenario(expected, replacement)
        assert (
            repo.load_rotation_scenarios() == (source,)
            and repo.last_rotation_selection() == source.scenario_id
        )
        assert workspace.editing.history.revision == revision
        assert Path(workspace.location).read_bytes() == before
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_existing_template_and_catalog_edits_cannot_rewrite_scenario_time(
    tmp_path: Path,
) -> None:
    """Scenario owns copied timing while every hierarchy path protects live identities.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; same-span clock shifts leave the plan's original clocks/run unchanged.
    """
    workspace = scenario_workspace(tmp_path)
    try:
        repo = workspace.rotation_scenarios()
        source = scenario_with_run()
        repo.replace_rotation_scenario(None, source)
        workspace.replace_shift_timing("Day", None, equal_timing(480, 4))
        original = workspace.read_hierarchy()
        moved = replace(
            original.hierarchy,
            organization=tuple(
                replace(r, attributes=(("start_time", "09:00"), ("end_time", "17:00")))
                if r.keys == ("Day",)
                else r
                for r in original.hierarchy.organization
            ),
        )
        workspace.replace_hierarchy(original, moved)
        assert (
            repo.load_rotation_scenarios() == (source,)
            and source.inputs.start_minute == 480
        )
        snapshot = workspace.read_hierarchy()
        removed = replace(
            snapshot.hierarchy, work=replace(snapshot.hierarchy.work, workers=())
        )
        with pytest.raises(ValueError):
            workspace.replace_hierarchy(snapshot, removed)
        with pytest.raises(ValueError):
            repo.replace_worker_catalogs(
                snapshot.hierarchy, removed, repo.load_jobs(), repo.load_jobs()
            )
        jobs = repo.load_jobs()
        with pytest.raises(ValueError):
            repo.replace_jobs(jobs, replace(jobs, jobs=jobs.jobs[1:]))
        assert repo.load_rotation_scenarios() == (source,)
        assert any(r.kind is OrganizationKind.SHIFT for r in moved.organization)
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_older_editor_cannot_overwrite_or_delete_guided_row(tmp_path: Path) -> None:
    """Existing compatible schemes and new plans coexist without silent data loss.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; ordinary old payload bytes remain unchanged next to guided records.
    """
    workspace = scenario_workspace(tmp_path)
    try:
        repo = workspace.rotation_scenarios()
        inputs = scenario_inputs()
        old = RotationScheme(
            "timing",
            "old",
            "Old",
            inputs.workers,
            inputs.targets,
            balanced_rows(inputs),
        )
        repo.save_rotation_scheme(old)
        assert repo.load_rotation_schemes() == (old,)
        source = scenario_with_run()
        repo.replace_rotation_scenario(None, source)
        assert repo.load_rotation_schemes() == (old,)
        overwrite = replace(old, scheme_id=source.scenario_id)
        with pytest.raises(ValueError, match="guided"):
            repo.save_rotation_scheme(overwrite)
        with pytest.raises(ValueError, match="guided"):
            repo.delete_rotation_scheme(source.scenario_id)
        assert repo.load_rotation_schemes() == (old,)
        assert len(repo.load_rotation_scenarios()) == 2
        original = next(
            s for s in repo.load_rotation_scenarios() if s.scenario_id == "old"
        )
        assert original.inputs.planned_date is None and original.inputs.timing is None
        updated = replace(original, name="Old renamed")
        repo.replace_rotation_scenario(original, updated)
        assert repo.load_rotation_schemes() == ()
        assert repo.load_rotation_scenarios() == (source, updated)
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_sqlite_failure_rolls_back_scenario_selection_and_shared_history(
    tmp_path: Path,
) -> None:
    """An actual trigger failure after insert cannot publish a partial selection/edit.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; source catalog, last viewed identity, bytes and history remain unchanged.
    """
    workspace = scenario_workspace(tmp_path)
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER fail_scenario AFTER INSERT ON rotation_schemes "
            "BEGIN SELECT RAISE(ABORT, 'Injected scenario failure'); END"
        )
    workspace.switch(str(path), None)
    try:
        repo = workspace.rotation_scenarios()
        before = path.read_bytes()
        with pytest.raises(sqlite3.IntegrityError, match="Injected"):
            repo.replace_rotation_scenario(None, scenario_with_run())
        assert (
            repo.load_rotation_scenarios() == ()
            and repo.last_rotation_selection() is None
        )
        assert (
            workspace.editing.history.undo_label_key is None
            and not workspace.has_unsaved_changes
        )
        assert path.read_bytes() == before
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_snapshot_retains_guided_and_old_records_and_rejects_identity_collision(
    tmp_path: Path,
) -> None:
    """Full creation owns both codec families and separate last-view state without loss.

    Args:
        tmp_path: Disposable snapshot directory.

    Returns:
        None; exact guided evidence and unknown older metadata reopen.
    """
    hierarchy, jobs, _ = scenario_catalogs()
    source = scenario_with_run()
    inputs = scenario_inputs()
    old = RotationScheme(
        "timing", "old", "Old", inputs.workers, inputs.targets, balanced_rows(inputs)
    )
    from ergotools.domain.job_risk import JobRiskCatalog
    from ergotools.domain.plot_positions import PlotPositions

    snapshot = ProjectSnapshot(
        ProjectMetadata("timing", "Snapshot", MeasurementSystem.METRIC),
        hierarchy,
        jobs,
        JobRiskCatalog("timing"),
        (),
        (),
        PlotPositions("timing"),
        (old,),
        rotation_scenarios=(source,),
        last_rotation_id=source.scenario_id,
    )
    with AssessmentProjectFile.create_from_snapshot(
        tmp_path / "snapshot.ergprj", snapshot
    ) as project:
        assert project.last_rotation_selection() == source.scenario_id
        assert (
            source in project.load_rotation_scenarios()
            and project.load_rotation_schemes() == (old,)
        )
    with pytest.raises(ValueError, match="duplicate"):
        replace(snapshot, rotation_scenarios=(replace(source, scenario_id="old"),))


def test_upgrade21_preserves_every_old_row_and_never_invents_dates(
    tmp_path: Path,
) -> None:
    """Upgrade private native21 with exact timing and older rotation payloads.

    Args:
        tmp_path: Disposable input/output paths.

    Returns:
        None; the current format changes only its marker and retains all old values.
    """
    original = Path("test_projects/native/comparative_risk_test.ergprj")
    source = tmp_path / "prior.ergprj"
    output = tmp_path / "current.ergprj"
    with (
        closing(
            sqlite3.connect(original.resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection,
        closing(sqlite3.connect(source)) as copied,
    ):
        connection.backup(copied)
        with copied:
            copied.execute("UPDATE project_metadata SET version=21")
        tables = [
            r[0]
            for r in copied.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
        before = {t: copied.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables}
    source_bytes = source.read_bytes()
    assert ExternalProjectMigration().requires_conversion(str(source))
    with upgrade_previous_project(source, output) as project:
        assert project.format_version == 24
        assert all(
            s.inputs.planned_date is None and s.inputs.timing is None and s.run is None
            for s in project.load_rotation_scenarios()
        )
        assert project.last_rotation_selection() is None
    with closing(sqlite3.connect(output)) as connection:
        after = {
            t: connection.execute(f'SELECT * FROM "{t}"').fetchall() for t in tables
        }
    expected = json.loads(json.dumps(before["project_metadata"]))[0]
    expected[1] = 24
    assert after["project_metadata"] == [tuple(expected)]
    assert {t: v for t, v in after.items() if t != "project_metadata"} == {
        t: v for t, v in before.items() if t != "project_metadata"
    }
    assert source.read_bytes() == source_bytes
    with (
        patch(
            "tools.project_migration.ergotools_migration.previous_project._publish_native_upgrade",
            side_effect=OSError("Injected publication failure"),
        ),
        pytest.raises(OSError),
    ):
        upgrade_previous_project(source, tmp_path / "failed.ergprj")
    assert (
        not (tmp_path / "failed.ergprj").exists()
        and source.read_bytes() == source_bytes
    )


def test_partial_observation_saves_and_replays_while_new_date_is_required(
    tmp_path: Path,
) -> None:
    """Save draft progress while requiring a new rotation's planned date.

    Args:
        tmp_path: Disposable project directory.

    Returns:
        None; no baseline, unfinished cells and old results remain distinct.
    """
    from ergotools.domain.rotation_scenario import RotationDraftRow, RotationScenario

    workspace = scenario_workspace(tmp_path)
    try:
        repo = workspace.rotation_scenarios()
        with pytest.raises(ValueError, match="date"):
            repo.replace_rotation_scenario(
                None,
                RotationScenario(
                    "timing",
                    "no-date",
                    "Not ready",
                    replace(scenario_inputs(), planned_date=None),
                ),
            )
        assert (
            repo.load_rotation_scenarios() == () and not workspace.has_unsaved_changes
        )
        original = scenario_with_run()
        repo.replace_rotation_scenario(None, original)
        a, b = (t.key for t in original.inputs.targets)
        entered = replace(
            original,
            inputs=replace(
                original.inputs,
                baseline=(
                    RotationDraftRow("W1", (a, None)),
                    RotationDraftRow("W2", (None, b)),
                ),
            ),
        )
        repo.replace_rotation_scenario(original, entered)
        assert not entered.run_matches_inputs and entered.run == original.run
        assert workspace.editing.replay(redo=False)
        assert repo.load_rotation_scenarios() == (original,)
        assert workspace.editing.replay(redo=True)
        assert workspace.save()
        with AssessmentProjectFile.open(Path(workspace.location)) as saved:
            assert saved.load_rotation_scenarios() == (entered,)
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


@pytest.mark.parametrize(
    "change", ["placement_owner", "assignment_owner", "deactivate"]
)
def test_workplace_scenario_protects_exact_ownership_but_retains_inactive_links(
    tmp_path: Path,
    change: str,
) -> None:
    """Guided references distinguish Job positions from physical stations and workers.

    Args:
        tmp_path: Disposable current project directory.
        change: Attempted reownership or a permitted inactive historical link.

    Returns:
        None; scenario edits never reassign permanent workers or mutate PLOT geometry.
    """
    from ergotools.domain.assessments.context import WorkerContext
    from ergotools.domain.job_catalog import JobPlacement, WorkerJobAssignment
    from ergotools.domain.rotation_scheme import RotationTarget, RotationWorkerLink
    from ergotools.domain.work_catalog import StationKey
    from ergotools.domain.work_hierarchy import LineKey, SectionKey

    workspace = scenario_workspace(tmp_path)
    try:
        repo = workspace.rotation_scenarios()
        original = workspace.read_hierarchy()
        stations = tuple(
            StationKey("Plant", "Packing", "Line A", s) for s in ("ST01", "ST02")
        )
        hierarchy = replace(
            original.hierarchy,
            work=replace(original.hierarchy.work, stations=stations),
            plants=("Plant",),
            sections=(SectionKey("Plant", "Packing"),),
            lines=(LineKey("Plant", "Packing", "Line A"),),
        )
        workspace.replace_hierarchy(original, hierarchy)
        contexts = tuple(s.at_shift("Day") for s in stations)
        old_jobs = repo.load_jobs()
        jobs = replace(
            old_jobs,
            placements=tuple(
                JobPlacement(i, f"J{i}", context)
                for i, context in enumerate(contexts, 1)
            ),
            assignments=tuple(
                WorkerJobAssignment(i, WorkerContext("timing", f"W{i}", context), i)
                for i, context in enumerate(contexts, 1)
            ),
        )
        repo.replace_jobs(old_jobs, jobs)
        inputs = replace(
            scenario_inputs(),
            workers=(RotationWorkerLink("W1", 1), RotationWorkerLink("W2", 2)),
            targets=(RotationTarget("J1", 1), RotationTarget("J2", 2)),
            scope=contexts,
            line=hierarchy.lines[0],
        )
        scenario = replace(scenario_with_run(), inputs=inputs, run=None)
        geometry = repo.load_plot_positions()
        repo.replace_rotation_scenario(None, scenario)
        assert repo.load_jobs() == jobs and repo.load_plot_positions() == geometry
        if change == "placement_owner":
            changed = replace(
                jobs,
                placements=(
                    replace(jobs.placements[0], job_id="J2"),
                    jobs.placements[1],
                ),
            )
        elif change == "assignment_owner":
            changed = replace(
                jobs,
                assignments=(
                    replace(
                        jobs.assignments[0],
                        worker=replace(jobs.assignments[0].worker, worker_id="W2"),
                    ),
                    jobs.assignments[1],
                ),
            )
        else:
            changed = replace(
                jobs,
                assignments=tuple(replace(a, active=False) for a in jobs.assignments),
                placements=tuple(replace(p, active=False) for p in jobs.placements),
            )
        if change == "deactivate":
            repo.replace_jobs(jobs, changed)
            assert repo.load_jobs() == changed
        else:
            with pytest.raises(ValueError, match="original"):
                repo.replace_jobs(jobs, changed)
            assert repo.load_jobs() == jobs
        assert repo.load_rotation_scenarios() == (scenario,)
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_guided_data_cannot_hide_behind_an_older_native_marker(tmp_path: Path) -> None:
    """A format marker is a real write/read capability, not just a UI label.

    Args:
        tmp_path: Disposable deliberately malformed native copy.

    Returns:
        None; older marker cannot cause a guided payload to be silently ignored.
    """
    from ergotools.infrastructure.draft_store import StoreFormatError

    workspace = scenario_workspace(tmp_path)
    repo = workspace.rotation_scenarios()
    repo.replace_rotation_scenario(None, scenario_with_run())
    assert workspace.save()
    path = Path(workspace.location)
    workspace.close(choice=CloseChoice.DISCARD)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE project_metadata SET version=21")
    before = path.read_bytes()
    with pytest.raises(StoreFormatError, match="format 22"):
        AssessmentProjectFile.open(path)
    with pytest.raises(ValueError, match="current native marker"):
        upgrade_previous_project(path, tmp_path / "invalid-upgrade.ergprj")
    assert not (tmp_path / "invalid-upgrade.ergprj").exists()
    assert path.read_bytes() == before


def test_native22_upgrade_retains_guided_run_and_rejects_false_old_marker(
    tmp_path: Path,
) -> None:
    """Advance legitimate guided records exactly; never launder new drafts as native22.

    Args:
        tmp_path: Disposable original/output paths.

    Returns:
        None; no current-row value changes beyond the explicit capability marker.
    """
    from ergotools.domain.rotation_scenario import RotationInputs
    from ergotools.infrastructure.draft_store import StoreFormatError

    source = tmp_path / "native22.ergprj"
    hierarchy, jobs, _ = scenario_catalogs()
    record = scenario_with_run()
    record = replace(record, run=replace(record.run, contract_version=1))
    with AssessmentProjectFile.create_empty(
        source, ProjectMetadata("timing", "Prior", MeasurementSystem.METRIC)
    ) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(jobs)
        project.replace_rotation_scenario(None, record)
    with closing(sqlite3.connect(source)) as connection:
        with connection:
            for row_id, payload in connection.execute(
                "SELECT rowid, payload FROM rotation_schemes"
            ).fetchall():
                value = json.loads(payload)
                value["version"] = 1
                for inputs in (value["inputs"], value["run"]["inputs"]):
                    for field in ("rules", "previous", "following"):
                        inputs.pop(field)
                body = {k: v for k, v in value["run"].items() if k != "fingerprint"}
                canonical = json.dumps(
                    body,
                    ensure_ascii=False,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                value["run"]["fingerprint"] = hashlib.sha256(
                    canonical.encode("utf-8")
                ).hexdigest()
                connection.execute(
                    "UPDATE rotation_schemes SET payload=? WHERE rowid=?",
                    (json.dumps(value), row_id),
                )
            connection.execute("UPDATE project_metadata SET version=22")
        before = connection.execute("SELECT * FROM rotation_schemes").fetchall()
    with AssessmentProjectFile.open(source) as diagnostic:
        assert diagnostic.load_rotation_scenarios() == (record,)
        with pytest.raises(RuntimeError, match="current"):
            diagnostic.replace_rotation_scenario(
                record, replace(record, name="No downgrade writes")
            )
    assert ExternalProjectMigration().requires_conversion(str(source))
    with upgrade_previous_project(source, tmp_path / "upgraded.ergprj") as current:
        assert current.format_version == 24
        assert current.load_rotation_scenarios() == (record,)
    with closing(sqlite3.connect(tmp_path / "upgraded.ergprj")) as connection:
        assert connection.execute("SELECT * FROM rotation_schemes").fetchall() == before
    empty = replace(
        record,
        scenario_id="empty",
        inputs=RotationInputs(planned_date=record.inputs.planned_date, baseline=()),
        run=None,
    )
    false_marker = tmp_path / "false22.ergprj"
    with AssessmentProjectFile.create_empty(
        false_marker,
        ProjectMetadata("timing", "False marker", MeasurementSystem.METRIC),
    ) as project:
        project.replace_rotation_scenario(None, empty)
    with closing(sqlite3.connect(false_marker)) as connection, connection:
        connection.execute("UPDATE project_metadata SET version=22")
    before_bytes = false_marker.read_bytes()
    with pytest.raises(StoreFormatError, match="24"):
        AssessmentProjectFile.open(false_marker)
    with pytest.raises(StoreFormatError, match="24"):
        upgrade_previous_project(false_marker, tmp_path / "rejected.ergprj")
    assert false_marker.read_bytes() == before_bytes
    assert not (tmp_path / "rejected.ergprj").exists()
