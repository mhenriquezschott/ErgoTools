"""JROT explicit save/load/delete, historical provenance and atomic upgrade tests.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_risk import JobRiskMeasurement, JobRiskValues
from ergotools.domain.plot_positions import (
    PlotPoint,
    PlotPositions,
    WorkerAssignmentMarker,
    WorkerPositionSource,
)
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import (
    RotationMode,
    RotationScheme,
    RotationTarget,
    RotationWorkerLink,
)
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.plant_image_import import import_plant_image
from ergotools.infrastructure.rotation_scheme_store import (
    RotationSchemeStore,
    create_rotation_schema,
)
from tests.test_history_persistence import HIERARCHY, JOBS, META, OWNER, SOURCE
from tests.test_plant_layout_persistence import image_file


def seed(path: Path, version: int = 7) -> AssessmentProjectFile:
    """Create an isolated full project and one approved zero-risk job profile.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        Open native project with an approved zero-risk profile; the caller must close
        the returned adapter, normally through a context manager.
    """
    project = AssessmentProjectFile.create_with_document(
        path, META, "source", SOURCE, format_version=version
    )
    project.save_hierarchy(HIERARCHY)
    project.save_jobs(JOBS)
    project.save_job_details(
        project.load_jobs(),
        project.load_job_risk(),
        JOBS.jobs[0],
        JobRiskValues(
            "j", (JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),)
        ),
    )
    return project


def scheme(scoped: bool = True) -> RotationScheme:
    """Retain exact selected profile/assignment and complete manual time blocks.

    Args:
        scoped: True includes the exact workplace restriction; False tests
            organization-wide saved scope.

    Returns:
        Complete immutable manual scheme retaining exact assignment/profile links and
        the requested saved scope.
    """
    target = RotationTarget("j", 1 if scoped else None)
    return RotationScheme(
        "p",
        "R-ñ",
        "Rotation ñ",
        (RotationWorkerLink("w", 1),),
        (target,),
        (WorkerRotation("w", (target.key, target.key)),),
        (OWNER.workplace,) if scoped else (),
        description='Quoted "note"\nsecond line',
    )


@pytest.mark.parametrize("version", [7, 8, 9, 10, 11])
def test_explicit_upgrade_roundtrip_replace_delete_and_copy(
    tmp_path: Path, version: int
) -> None:
    """Reads never migrate; saves retain other project data and ordered rows.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    with seed(path, version) as project:
        before = path.read_bytes()
        assert project.load_rotation_schemes() == ()
        assert path.read_bytes() == before and project.format_version == version
        project.save_rotation_scheme(scheme())
        assert project.format_version == 11
        other = replace(scheme(False), scheme_id="A", name="Other")
        project.save_rotation_scheme(other)
        changed = replace(scheme(), name="Renamed")
        project.save_rotation_scheme(changed)
        assert project.load_rotation_schemes() == (other, changed)
        assert project.load(DocumentKey("p", "source")) == SOURCE
        project.save_plot_positions(PlotPositions("p"))
        assert project.format_version == 11
        assert project.load_rotation_schemes() == (other, changed)
        with project.snapshot(str(tmp_path / "copy.sqlite"), None, None) as copied:
            assert copied.format_version == 11
            assert copied.load_rotation_schemes() == (other, changed)
        project.delete_rotation_scheme("A")
        with pytest.raises(KeyError):
            project.delete_rotation_scheme("missing")
        assert project.load_rotation_schemes() == (changed,)
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_rotation_schemes() == (changed,)
        assert reopened.load_jobs() == JOBS
        assert reopened.load_hierarchy() == HIERARCHY


def test_failed_initial_save_rolls_back_all_schema_and_version(tmp_path: Path) -> None:
    """An upgrade/write failure cannot leave partial tables or a changed handle.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "rollback.sqlite"
    with seed(path) as project:
        with (
            patch.object(
                RotationSchemeStore,
                "write_in_transaction",
                side_effect=sqlite3.IntegrityError("failure"),
            ),
            pytest.raises(sqlite3.IntegrityError),
        ):
            project.save_rotation_scheme(scheme())
        assert project.format_version == 7
        assert project.load_rotation_schemes() == ()
        with closing(sqlite3.connect(path)) as connection:
            names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert not names & {
                "rotation_schemes",
                "project_details",
                "plant_layout_images",
                "plot_station_positions",
            }
        project.save_rotation_scheme(scheme())
        with (
            patch.object(
                RotationSchemeStore,
                "write_in_transaction",
                side_effect=sqlite3.IntegrityError("failure"),
            ),
            pytest.raises(sqlite3.IntegrityError),
        ):
            project.save_rotation_scheme(replace(scheme(), name="Failed"))
        assert project.load_rotation_schemes() == (scheme(),)


def test_current_values_and_closed_assignment_survive_replacement(
    tmp_path: Path,
) -> None:
    """Current risk updates and reassignment retain existing schedule ownership.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with seed(tmp_path / "history.sqlite") as project:
        project.save_rotation_scheme(scheme())
        project.save_job_details(
            project.load_jobs(),
            project.load_job_risk(),
            JOBS.jobs[0],
            JobRiskValues(
                "j", (JobRiskMeasurement(AssessmentKind.LIFFT, 0.1, 50, "Metric"),)
            ),
        )
        changed_jobs = replace(
            JOBS,
            assignments=(
                replace(JOBS.assignments[0], active=False, ended_at="2026-10-08"),
                replace(JOBS.assignments[0], assignment_id=2, placement_id=2),
            ),
        )
        project.save_jobs(changed_jobs)
        assert project.load_rotation_schemes() == (scheme(),)
        project.save_rotation_scheme(replace(scheme(), name="Keep arrangements"))
        assert project.load_rotation_schemes()[0].targets[0].job_id == "j"
        project.save_rotation_scheme(replace(scheme(), scheme_id="new"))
        assert (
            project.load_job_risk().for_job("j").measurements[0].probability_percent
            == 50
        )


def test_referenced_worker_assignment_placement_and_scope_are_protected(
    tmp_path: Path,
) -> None:
    """Allow closure but reject deleting or rewriting frozen record ownership.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with seed(tmp_path / "protected.sqlite") as project:
        project.save_rotation_scheme(scheme())
        for jobs in (
            replace(JOBS, assignments=()),
            replace(JOBS, assignments=(replace(JOBS.assignments[0], placement_id=2),)),
        ):
            with pytest.raises(ValueError, match="original worker assignment"):
                project.save_jobs(jobs)
            assert project.load_jobs() == JOBS
        with pytest.raises((ValueError, KeyError)):
            project.save_hierarchy(
                replace(
                    HIERARCHY,
                    work=replace(HIERARCHY.work, workers=HIERARCHY.work.workers[1:]),
                )
            )
        with pytest.raises(ValueError):
            project.delete_job(project.load_jobs(), project.load_job_risk(), "j")
        assert project.load_jobs() == JOBS
        assert project.load_job_risk().for_job("j").measurements[0].complete
        changed_placement = replace(
            JOBS,
            placements=(
                replace(JOBS.placements[0], job_id="k", active=False),
                JOBS.placements[1],
            ),
        )
        with pytest.raises(ValueError, match="original job placement"):
            project.save_jobs(changed_placement)
        project.delete_rotation_scheme(scheme().scheme_id)
        project.save_jobs(replace(JOBS, assignments=()))


@pytest.mark.parametrize("mutation", ["foreign", "job", "placement", "worker"])
def test_invalid_links_never_upgrade_or_publish(tmp_path: Path, mutation: str) -> None:
    """Explicit identities must belong to the project, job, worker and saved scope.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        mutation: Named malformed snapshot/catalog mutation selected by the parametrized
            scenario.

    Returns:
        None.
    """
    with seed(tmp_path / "invalid.sqlite") as project:
        value = scheme()
        if mutation == "foreign":
            value = replace(value, project_id="foreign")
        elif mutation in ("job", "placement"):
            target = replace(
                value.targets[0],
                **{mutation + "_id": "missing" if mutation == "job" else 99},
            )
            value = replace(
                value,
                targets=(target,),
                current=(WorkerRotation("w", (target.key, target.key)),),
            )
        elif mutation == "worker":
            value = replace(
                value,
                workers=(RotationWorkerLink("x", 1),),
                current=(WorkerRotation("x", value.current[0].target_keys),),
            )
        with pytest.raises((ValueError, KeyError)):
            project.save_rotation_scheme(value)
        assert project.format_version == 7 and project.load_rotation_schemes() == ()


def test_corrupt_scheme_is_rejected_on_open(tmp_path: Path) -> None:
    """Stored shape, identity and referenced profile corruption cannot load silently.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "corrupt.sqlite"
    with seed(path) as project:
        project.save_rotation_scheme(scheme())
    with closing(sqlite3.connect(path)) as connection, connection:
        raw = json.loads(
            connection.execute("SELECT payload FROM rotation_schemes").fetchone()[0]
        )
        raw["workers"] = [["w", True]]
        connection.execute("UPDATE rotation_schemes SET payload=?", (json.dumps(raw),))
    with pytest.raises(StoreFormatError):
        AssessmentProjectFile.open(path)


def test_store_requires_transaction_and_closed_projects_reject_access(
    tmp_path: Path,
) -> None:
    """Borrowed stores cannot commit/schema-create outside the owner's transaction.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with closing(sqlite3.connect(":memory:")) as connection:
        store = RotationSchemeStore(connection, "p")
        for action in (
            lambda: create_rotation_schema(connection),
            lambda: store.write_in_transaction(scheme()),
            lambda: store.delete_in_transaction("R"),
        ):
            with pytest.raises(RuntimeError, match="transaction"):
                action()
    project = seed(tmp_path / "closed.sqlite")
    project.close()
    for action in (
        project.load_rotation_schemes,
        lambda: project.save_rotation_scheme(scheme()),
        lambda: project.delete_rotation_scheme("R"),
    ):
        with pytest.raises(RuntimeError, match="closed"):
            action()


def test_scheme_shape_and_optimization_mode_validation() -> None:
    """Save complete manual cells without claiming optimization feasibility.

    Args:
        None.

    Returns:
        None.
    """
    value = scheme()
    for updates in (
        {"workers": ()},
        {"current": ()},
        {"targets": ()},
        {"mode": RotationMode.SINGLE_TOOL},
        {"primary_kind": AssessmentKind.LIFFT},
        {"scope": (OWNER.workplace, OWNER.workplace)},
    ):
        with pytest.raises(ValueError):
            replace(value, **updates)
    assert (
        replace(
            value, mode=RotationMode.SINGLE_TOOL, primary_kind=AssessmentKind.LIFFT
        ).primary_kind
        == AssessmentKind.LIFFT
    )


def test_rotation_upgrade_preserves_saved_map_geometry_and_source_units(
    tmp_path: Path,
) -> None:
    """Add schemes without resetting existing PLOT or assessment data.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    image = import_plant_image(image_file(tmp_path / "map.png"))
    positions = PlotPositions(
        "p",
        workers=(
            WorkerAssignmentMarker(
                1, PlotPoint(23, 41), source=WorkerPositionSource.MANUAL
            ),
        ),
    )
    with seed(tmp_path / "map.sqlite", 10) as project:
        project.save_plant_image("P", image)
        project.save_plot_positions(positions)
        project.save_rotation_scheme(scheme())
        assert project.load_plant_image("P") == image
        assert project.load_plot_positions() == positions
        assert project.load(DocumentKey("p", "source")) == SOURCE
        project.save_plant_image("P", image)
        assert project.format_version == 11
        assert project.load_job_risk().for_job("j").measurements[0].unit == "Imperial"


def test_unassigned_organization_worker_cannot_be_deleted_when_referenced(
    tmp_path: Path,
) -> None:
    """Rotation-only worker references are protected without assessment/job links.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with seed(tmp_path / "org.sqlite") as project:
        value = scheme(False)
        value = replace(
            value,
            workers=(RotationWorkerLink("x"),),
            current=(WorkerRotation("x", value.current[0].target_keys),),
        )
        project.save_rotation_scheme(value)
        changed = replace(
            HIERARCHY, work=replace(HIERARCHY.work, workers=HIERARCHY.work.workers[:1])
        )
        with pytest.raises(ValueError, match="missing worker"):
            project.save_hierarchy(changed)
        assert project.load_hierarchy() == HIERARCHY
        project.delete_rotation_scheme(value.scheme_id)
        project.save_hierarchy(changed)


@pytest.mark.parametrize(
    "raw", ["null", "[]", "{", '{"version":true}', '{"version":1}', '{"version":2}']
)
def test_malformed_payload_fails_without_loading_partial_scheme(
    tmp_path: Path, raw: str
) -> None:
    """Malformed/non-object/version-incompatible payloads fail closed on reopen.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        raw: Literal malformed or boundary serialization/input value used by this case.

    Returns:
        None.
    """
    path = tmp_path / "bad.sqlite"
    with seed(path) as project:
        project.save_rotation_scheme(scheme())
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE rotation_schemes SET payload=?", (raw,))
    with pytest.raises(StoreFormatError):
        AssessmentProjectFile.open(path)
