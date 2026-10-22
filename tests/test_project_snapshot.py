"""Complete creation, exact historical evidence and exclusive publication failures.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.application.session import DocumentKey
from ergotools.domain.assessment_history import AssessmentHistory
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.infrastructure.assessment_history_store import AssessmentHistoryStore
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.job_risk_store import JobRiskStore
from ergotools.infrastructure.lifft_store import StoreFormatError
from ergotools.infrastructure.plot_position_store import PlotPositionStore
from ergotools.infrastructure.project_snapshot import (
    ProjectSnapshot,
    SnapshotAssessment,
)
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_legacy_plot import mapped as mapped
from tests.test_legacy_reconciliation import old_source as old_source
from tests.test_legacy_rotations import rotated as rotated
from tools.project_migration.ergotools_migration.legacy_assessments import (
    read_legacy_assessments,
)
from tools.project_migration.ergotools_migration.legacy_catalogs import (
    read_legacy_catalogs,
)
from tools.project_migration.ergotools_migration.legacy_plot import read_legacy_plot
from tools.project_migration.ergotools_migration.legacy_project import (
    LegacyProject,
    read_legacy_descriptor,
)
from tools.project_migration.ergotools_migration.legacy_reconciliation import (
    reconcile_legacy_assessments,
)
from tools.project_migration.ergotools_migration.legacy_rotations import (
    read_legacy_rotations,
)


@pytest.fixture
def snapshot(mapped: Path, old_source: Path, rotated: Path) -> ProjectSnapshot:
    """Combine real source shapes with a retired rotation link and recovered source.

    Args:
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        rotated: Disposable original-format fixture containing frozen
            JROT/profile/assignment links.

    Returns:
        Complete immutable native snapshot assembled from synthetic original-shape
        catalogs, maps, sources and frozen rotation links.
    """
    assert mapped == old_source == rotated
    descriptor = read_legacy_descriptor(mapped, "p")
    with LegacyProject(descriptor) as project:
        catalogs = read_legacy_catalogs(project)
        plan = reconcile_legacy_assessments(
            project, catalogs, read_legacy_assessments(project, catalogs)
        )
        plot = read_legacy_plot(project, catalogs)
        rotations = read_legacy_rotations(project, catalogs)
    (recovered,) = plan.recovered
    assert isinstance(recovered.source, LifftDraft)
    return ProjectSnapshot(
        descriptor.metadata,
        catalogs.hierarchy,
        catalogs.jobs,
        catalogs.risks,
        (SnapshotAssessment(recovered.ownership, recovered.source),),
        tuple((image.plant, image.image) for image in plot.images),
        plot.positions,
        rotations.schemes,
    )


def test_complete_creation_reopen_and_backup(
    snapshot: ProjectSnapshot, tmp_path: Path
) -> None:
    """Preserve input units, closed owners, retired profiles and every map byte.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    destination = tmp_path / "converted.ergprj"
    (assessment,) = snapshot.assessments
    key = DocumentKey("p", assessment.ownership.document_id)
    with AssessmentProjectFile.create_from_snapshot(destination, snapshot) as project:
        assert project.format_version == 19
        assert project.metadata == snapshot.metadata
        assert project.load_hierarchy() == snapshot.hierarchy
        assert project.load_jobs() == snapshot.jobs
        assert project.load_job_risk() == snapshot.risks
        assert project.load_history().entries == (assessment.ownership,)
        assert project.load(key) == assessment.source
        assert project.load_plant_image("P") == snapshot.images[0][1]
        assert project.load_plot_positions() == snapshot.positions
        assert project.load_rotation_schemes() == snapshot.rotations
        assert len(project.load_job_risk().values) == 1
        assert (
            next(
                m
                for m in project.load_job_risk().for_job("j").measurements
                if m.kind.value == "lifft"
            ).probability_percent
            == 80
        )
        assert project.load_rotation_schemes()[0].workers[0].assignment_id == 30
        with project.snapshot(str(tmp_path / "backup.ergprj"), None, None) as backup:
            assert backup.load_job_risk() == snapshot.risks
            assert backup.load(key) == assessment.source
    with AssessmentProjectFile.open(destination) as project:
        assert project.load_rotation_schemes() == snapshot.rotations
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


@pytest.mark.parametrize("kind", ["source", "image", "risk", "rotation", "hierarchy"])
def test_invalid_input_never_publishes(
    snapshot: ProjectSnapshot, tmp_path: Path, kind: str
) -> None:
    """Reject wrong model/identity, duplicate references and corrupt pixels.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        kind: Explicit tool identity or deliberately invalid tool value selected by this
            regression.

    Returns:
        None.
    """
    destination = tmp_path / "invalid.ergprj"
    with pytest.raises((ValueError, OSError)):
        if kind == "source":
            from ergotools.domain.assessments.duet_draft import DuetDraft

            snapshot = replace(
                snapshot,
                assessments=(replace(snapshot.assessments[0], source=DuetDraft()),),
            )
        elif kind == "image":
            from ergotools.domain.plant_layout_image import PlantLayoutImage

            snapshot = replace(snapshot, images=(("P", PlantLayoutImage(b"bad")),))
        elif kind == "risk":
            snapshot = replace(
                snapshot, risks=replace(snapshot.risks, project_id="other")
            )
        elif kind == "rotation":
            snapshot = replace(snapshot, rotations=snapshot.rotations * 2)
        else:
            snapshot = replace(
                snapshot,
                hierarchy=replace(
                    snapshot.hierarchy,
                    work=replace(snapshot.hierarchy.work, project_id="other"),
                ),
            )
        AssessmentProjectFile.create_from_snapshot(destination, snapshot)
    assert not destination.exists()
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


def test_existing_destination_is_never_adopted(
    snapshot: ProjectSnapshot, tmp_path: Path
) -> None:
    """Do not remove or change a pre-existing user file, even if not a database.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    destination = tmp_path / "existing.ergprj"
    destination.write_bytes(b"original user data")
    with pytest.raises(FileExistsError):
        AssessmentProjectFile.create_from_snapshot(destination, snapshot)
    assert destination.read_bytes() == b"original user data"
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


def test_write_failure_cleans_unpublished_file(
    snapshot: ProjectSnapshot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fail after source/risk initialization without exposing a partial project.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """

    def fail_write(self: PlotPositionStore, positions: object) -> None:
        """Raise a controlled map-write SQLite failure before publication.

        Raise a controlled map-write SQLite failure before publication to verify
        unpublished-file cleanup.

        Args:
            self: Temporary PlotPositionStore receiver supplied to this patched write
                method; deliberately not written.
            positions: Injected map-position write operand; this failure callback
                deliberately does not persist it.

        Returns:
            None.

        Raises:
            sqlite3.OperationalError: The deliberately injected SQLite write/metadata
                failure is reached.
        """
        raise sqlite3.OperationalError("injected disk write failure")

    monkeypatch.setattr(PlotPositionStore, "write_in_transaction", fail_write)
    destination = tmp_path / "failed.ergprj"
    with pytest.raises(sqlite3.OperationalError, match="disk write"):
        AssessmentProjectFile.create_from_snapshot(destination, snapshot)
    assert not destination.exists()
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


def test_reopened_source_mismatch_blocks_publication(
    snapshot: ProjectSnapshot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The postcondition compares actual reopened sources, not just row counts.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    monkeypatch.setattr(
        AssessmentProjectFile,
        "load",
        lambda self, key: LifftDraft(snapshot.assessments[0].source.system),
    )
    destination = tmp_path / "mismatch.ergprj"
    with pytest.raises(StoreFormatError, match="assessment does not match"):
        AssessmentProjectFile.create_from_snapshot(destination, snapshot)
    assert not destination.exists()
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


@pytest.mark.parametrize("failure", ["race", "unsupported"])
def test_exclusive_publication_has_no_overwrite_fallback(
    snapshot: ProjectSnapshot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    """Retain a racing writer's file and report unsupported hard-link filesystems.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.
        failure: Named fault-injection stage/outcome used to verify rollback and
            retained ownership.

    Returns:
        None.
    """
    destination = tmp_path / "destination.ergprj"
    original_link = os.link

    def fail_link(source: Path, target: Path) -> None:
        """Simulate either a racing destination writer or unavailable hard links.

        Simulate either a racing destination writer or unavailable hard links without an
        overwrite fallback.

        Args:
            source: Immutable draft or disposable source path supplied by the stated
                storage/publication scenario.
            target: Explicit disposable publication destination; racing-writer tests
                protect any pre-existing bytes.

        Returns:
            None.

        Raises:
            OSError: The controlled adapter/resource/publication failure is injected by
                this scenario.
        """
        if failure == "race":
            target.write_bytes(b"racing writer")
            original_link(source, target)
        else:
            raise OSError("hard links unavailable")

    monkeypatch.setattr(os, "link", fail_link)
    with pytest.raises(OSError):
        AssessmentProjectFile.create_from_snapshot(destination, snapshot)
    if failure == "race":
        assert destination.read_bytes() == b"racing writer"
    else:
        assert not destination.exists()
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


def test_final_open_failure_keeps_valid_published_project(
    snapshot: ProjectSnapshot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A published, validated project survives failure to return a live handle.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    destination = tmp_path / "published.ergprj"
    original_open = AssessmentProjectFile.open

    def fail_final_open(
        cls: type[AssessmentProjectFile], path: Path
    ) -> AssessmentProjectFile:
        """Fail only reopening the already published final destination.

        Fail only reopening the already published final destination; temporary
        validation opens still delegate to the actual adapter.

        Args:
            cls: AssessmentProjectFile class supplied to the patched classmethod;
                delegates non-final opens unchanged.
            path: Disposable test file path; the caller controls creation and cleanup.

        Returns:
            Actual native handle for non-final validation opens; the final destination
            deliberately raises instead of returning.

        Raises:
            sqlite3.OperationalError: The deliberately injected SQLite write/metadata
                failure is reached.
        """
        if path == destination:
            raise sqlite3.OperationalError("injected final open failure")
        return original_open(path)

    monkeypatch.setattr(AssessmentProjectFile, "open", classmethod(fail_final_open))
    with pytest.raises(sqlite3.OperationalError, match="final open"):
        AssessmentProjectFile.create_from_snapshot(destination, snapshot)
    with original_open(destination) as project:
        assert project.load_jobs() == snapshot.jobs
        assert project.load_rotation_schemes() == snapshot.rotations
    assert not list(tmp_path.glob(".ergotools-conversion-*"))


def test_initializers_protect_existing_records(
    snapshot: ProjectSnapshot, tmp_path: Path
) -> None:
    """Creation-only access cannot replace an already initialized risk/history store.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "initialized.ergprj"
    with AssessmentProjectFile.create_from_snapshot(path, snapshot):
        pass
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        risks = JobRiskStore(connection, "p", lambda: snapshot.jobs)
        with pytest.raises(ValueError, match="empty store"):
            risks.initialize_in_transaction(snapshot.risks)
        history = AssessmentHistoryStore(connection, "p")
        with pytest.raises(ValueError, match="empty store"):
            history.initialize_in_transaction(AssessmentHistory("p"), snapshot.jobs)
    with AssessmentProjectFile.open(path) as project:
        assert project.load_job_risk() == snapshot.risks
        assert project.load_history().entries == tuple(
            x.ownership for x in snapshot.assessments
        )


@pytest.fixture
def archived(snapshot: ProjectSnapshot, mapped: Path) -> ProjectSnapshot:
    """Build one recalculated native output per source for isolated storage tests.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.

    Returns:
        Complete native snapshot with one freshly recalculated authoritative output per
        source; no duplicate archive is created.
    """
    from ergotools.application.saved_results import calculate_saved_result

    return replace(
        snapshot,
        saved_results=tuple(
            (item.ownership.document_id, result)
            for item in snapshot.assessments
            if (
                result := calculate_saved_result(
                    DocumentKey(
                        snapshot.metadata.project_id, item.ownership.document_id
                    ),
                    item.source,
                    snapshot.metadata.default_units,
                )
            )
            is not None
        ),
    )


def previous_converted(archived: ProjectSnapshot, mapped: Path, path: Path) -> Path:
    """Create a historical format-12 fixture for testing the external upgrade only.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        Disposable historical format-12 project path used only to characterize the
        external upgrade tool.
    """
    from tools.project_migration.ergotools_migration.legacy_evidence import (
        LegacyEvidenceStore,
        create_evidence_schema,
        read_legacy_evidence,
    )

    with AssessmentProjectFile.create_from_snapshot(path, archived):
        pass
    with LegacyProject(read_legacy_descriptor(mapped, "p")) as old:
        evidence = read_legacy_evidence(
            old, read_legacy_plot(old, read_legacy_catalogs(old))
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        create_evidence_schema(connection)
        LegacyEvidenceStore(connection).initialize_in_transaction(evidence)
        connection.execute("UPDATE project_metadata SET version=12")
    return path


def test_source_archive_is_self_contained_and_survives_edits(
    archived: ProjectSnapshot, mapped: Path, tmp_path: Path
) -> None:
    """Native images survive removal of originals; changed sources invalidate output.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    descriptor = read_legacy_descriptor(mapped, "p")
    before = descriptor.database_path.read_bytes(), mapped.read_bytes()
    path = tmp_path / "native.ergprj"
    identity, recorded = archived.saved_results[0]
    key = DocumentKey("p", identity)
    with AssessmentProjectFile.create_from_snapshot(path, archived) as project:
        assert project.format_version == 19
        assert project.load_saved_result(key) == recorded
        project.save_rotation_scheme(
            replace(archived.rotations[0], description="Edited")
        )
        project.save_plot_positions(archived.positions)
        project.save_plant_image("P", archived.images[0][1])
        project.save(key, replace(recorded.source, tasks=recorded.source.tasks[:1]))
        assert project.load_saved_result(key) is None
        with project.snapshot(
            str(tmp_path / "native-backup.ergprj"), None, None
        ) as backup:
            assert backup.load_saved_result(key) is None
    assert (descriptor.database_path.read_bytes(), mapped.read_bytes()) == before
    mapped.unlink()
    descriptor.database_path.unlink()
    (tmp_path / "images/original.png").unlink()
    with AssessmentProjectFile.open(path) as project:
        assert project.load_saved_result(key) is None
        assert project.load_plant_image("P") == archived.images[0][1]
    with closing(sqlite3.connect(path)) as native:
        assert not native.execute(
            "SELECT name FROM sqlite_master WHERE name LIKE 'legacy_%'"
        ).fetchall()


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE legacy_source_evidence SET descriptor=x'00'",
        "UPDATE legacy_source_evidence SET database_sha256='bad'",
        "UPDATE legacy_source_images SET sha256='bad'",
        "UPDATE legacy_source_images SET position=10",
        "UPDATE legacy_source_evidence SET version=2",
        "DELETE FROM legacy_source_evidence",
        "DELETE FROM legacy_source_images",
    ],
)
def test_corrupt_source_archive_rejects_open(
    archived: ProjectSnapshot, mapped: Path, tmp_path: Path, mutation: str
) -> None:
    """External upgrade discards obsolete archives and recalculates current inputs.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        mutation: Named malformed snapshot/catalog mutation selected by the parametrized
            scenario.

    Returns:
        None.
    """
    from tools.project_migration.ergotools_migration.previous_project import (
        upgrade_previous_project,
    )

    path = previous_converted(archived, mapped, tmp_path / "earlier.ergprj")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(mutation)
    destination = tmp_path / "must-not-exist.ergprj"
    before = path.read_bytes()
    with upgrade_previous_project(path, destination) as project:
        assert project.format_version == 19
        identity, expected = archived.saved_results[0]
        assert project.load_saved_result(DocumentKey("p", identity)) == expected
    assert path.read_bytes() == before


def test_source_archive_initializer_cannot_replace_evidence(
    archived: ProjectSnapshot, mapped: Path, tmp_path: Path
) -> None:
    """The external tool's archive validator cannot replace earlier preserved bytes.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from tools.project_migration.ergotools_migration.legacy_evidence import (
        LegacyEvidenceStore,
    )

    path = previous_converted(archived, mapped, tmp_path / "earlier.ergprj")
    with closing(sqlite3.connect(path)) as connection, connection:
        store = LegacyEvidenceStore(connection)
        evidence = store.read()
        connection.execute("BEGIN IMMEDIATE")
        with pytest.raises(ValueError, match="empty storage"):
            store.initialize_in_transaction(evidence)
        assert store.read() == evidence


def test_explicit_converter_preserves_all_records_and_source(
    snapshot: ProjectSnapshot, mapped: Path, tmp_path: Path
) -> None:
    """Run the complete original XML -> separate repository -> workspace workflow.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from PyQt5.QtWidgets import QApplication

    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.bootstrap import create_window
    from tools.project_migration.ergotools_migration.legacy_conversion import (
        convert_legacy_project,
    )

    descriptor = read_legacy_descriptor(mapped, "p")
    before = mapped.read_bytes(), descriptor.database_path.read_bytes()
    path = tmp_path / "converted-workflow.ergprj"
    with convert_legacy_project(mapped, path, "p") as project:
        assert project.metadata == descriptor.metadata
        assert project.load_jobs() == snapshot.jobs
        assert project.load_history().entries == tuple(
            x.ownership for x in snapshot.assessments
        )
        assert project.load_rotation_schemes() == snapshot.rotations
        assert (
            project.load_saved_result(
                DocumentKey("p", snapshot.assessments[0].ownership.document_id)
            )
            is not None
        )
    app = QApplication.instance() or QApplication([])
    window = create_window(
        tmp_path / "isolated-settings.json", original_navigation=True
    )
    try:
        window.presenter.workspace.switch(
            str(path), snapshot.assessments[0].ownership.document_id
        )
        window.refresh()
        assert window.presenter.workspace.active.state == snapshot.assessments[0].source
        assert window.main_navigation.toolbar_actions["jrot"].isEnabled()
        assert window.main_navigation.toolbar_actions["plot"].isEnabled()
        assert (
            window.presenter.workspace.rotation_repository().load_rotation_schemes()
            == snapshot.rotations
        )
    finally:
        window.presenter.workspace.close(choice=CloseChoice.DISCARD)
        window.close()
        window.deleteLater()
        app.processEvents()
    assert (mapped.read_bytes(), descriptor.database_path.read_bytes()) == before


def test_converter_blocks_conflicts_without_partial_output(
    snapshot: ProjectSnapshot, mapped: Path, tmp_path: Path
) -> None:
    """Ambiguous original ownership still blocks conversion without repairs.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from tools.project_migration.ergotools_migration.legacy_conversion import (
        LegacyConversionReviewError,
        convert_legacy_project,
    )

    descriptor = read_legacy_descriptor(mapped, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute("UPDATE WorkerAssignment SET active=0")
    before = descriptor.database_path.read_bytes()
    destination = tmp_path / "must-not-exist.ergprj"
    with pytest.raises(LegacyConversionReviewError) as raised:
        convert_legacy_project(mapped, destination, "p")
    assert raised.value.conflicts[0].reason == "No unique active assignment."
    assert not destination.exists()
    assert not list(tmp_path.glob(".ergotools-conversion-*"))
    assert descriptor.database_path.read_bytes() == before


def test_converter_retains_shoulder_choices_branches_and_original_evidence(
    snapshot: ProjectSnapshot, mapped: Path, tmp_path: Path
) -> None:
    """Full conversion includes ST, without changing its labels or source cache.

    Args:
        snapshot: Immutable complete native/source snapshot used to characterize
            conversion/persistence.
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    from ergotools.domain.assessments.tst import TstDirection
    from ergotools.domain.assessments.tst_draft import TstDirectionConvention, TstDraft
    from tools.project_migration.ergotools_migration.legacy_conversion import (
        convert_legacy_project,
    )

    descriptor = read_legacy_descriptor(mapped, "p")
    with closing(sqlite3.connect(descriptor.database_path)) as connection, connection:
        connection.execute(
            "INSERT INTO IndividualAssessment(id,worker_assignment_id,tool_id,"
            "version,status,is_current,unit,notes) "
            "VALUES (50,30,'ST',1,'complete',1,'Metric','Keep cached results')"
        )
        connection.executemany(
            "INSERT INTO ShoulderAssessmentTask VALUES (50,?,?,10,20,200,100,.2,25)",
            [(index + 1, selector) for index, selector in enumerate((0, 1, 2, None))],
        )
    before = descriptor.database_path.read_bytes()
    with convert_legacy_project(mapped, tmp_path / "all-tools.ergprj", "p") as project:
        source = project.load(DocumentKey("p", "legacy-assessment-50"))
        assert isinstance(source, TstDraft)
        assert source.direction_convention is TstDirectionConvention.REFERENCE_UI
        assert tuple(task.direction for task in source.tasks) == (
            TstDirection.HANDLING_LOADS,
            TstDirection.DOWNWARD,
            TstDirection.HORIZONTAL,
            None,
        )
        assert tuple(
            source.model_task(task.task_id).direction for task in source.tasks
        ) == (
            TstDirection.HANDLING_LOADS,
            TstDirection.HORIZONTAL,
            TstDirection.DOWNWARD,
            None,
        )
        assert len(project.load_history().entries) == 2
        result = project.load_saved_result(DocumentKey("p", "legacy-assessment-50"))
        from ergotools.application.saved_results import calculate_saved_result

        assert result == calculate_saved_result(
            DocumentKey("p", "legacy-assessment-50"),
            source,
            project.metadata.default_units,
        )
        assert result.tasks[0].damage != 0.2
        with closing(sqlite3.connect(descriptor.database_path)) as original:
            assert original.execute(
                "SELECT notes FROM IndividualAssessment"
            ).fetchone() == ("Keep cached results",)
    assert descriptor.database_path.read_bytes() == before
