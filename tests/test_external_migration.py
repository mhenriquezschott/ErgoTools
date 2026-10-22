"""Exercise removable migration entry points and native-only result persistence.

Tests own temporary projects and never modify the reference checkout. They cover process
argument handling, refusal to overwrite, previous-format upgrades and separate
imported/fresh provenance. Native package isolation is also checked by the independent
wheel acceptance recorded with M1.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
import sys
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.project_migration import ExternalProjectMigration
from ergotools.infrastructure.project_snapshot import ProjectSnapshot
from tests.test_project_snapshot import archived as archived
from tests.test_project_snapshot import legacy_catalog as legacy_catalog
from tests.test_project_snapshot import mapped as mapped
from tests.test_project_snapshot import old_source as old_source
from tests.test_project_snapshot import previous_converted
from tests.test_project_snapshot import rotated as rotated
from tests.test_project_snapshot import snapshot as snapshot
from tests.test_saved_results import calculate
from tools.project_migration.ergotools_migration.cli import main
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)

# Absolute tool entry point is independent of the subprocess working directory.
UTILITY = (
    Path(__file__).resolve().parents[1] / "tools/project_migration/migrate_project.py"
)


def test_external_process_handles_spaces_and_native_open(
    mapped: Path, old_source: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Convert with literal path arguments, then open without invoking the tool.

    Args:
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        monkeypatch: Pytest patch fixture; environment/adapter substitutions are
            restored after the test.

    Returns:
        None.
    """
    assert mapped == old_source
    destination = tmp_path / "native with spaces.ergprj"
    original = mapped.read_bytes()
    adapter = ExternalProjectMigration((sys.executable, str(UTILITY)))
    monkeypatch.chdir(tmp_path)
    assert adapter.requires_conversion(str(mapped))
    adapter.convert(str(mapped), str(destination))
    assert mapped.read_bytes() == original
    assert not adapter.requires_conversion(str(destination))
    with AssessmentProjectFile.open(destination) as project:
        assert project.format_version == 19
        assert project.load_plant_image("P") is not None
        assert any(
            project.load_saved_result(
                DocumentKey(project.metadata.project_id, item.document_id)
            )
            is not None
            for item in project.load_history().entries
        )
    with closing(sqlite3.connect(destination)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert "saved_assessment_results" in names
        assert "recorded_assessment_results" not in names
        assert not any(name.startswith("legacy_") for name in names)


def test_cli_failure_never_overwrites(
    mapped: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Reject an existing destination and invalid input without publishing data.

    Args:
        mapped: Disposable original-format fixture containing plant images and
            assignment-owned map geometry.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        capsys: Pytest terminal capture used to assert CLI diagnostics without changing
            application state.

    Returns:
        None.
    """
    destination = tmp_path / "existing.ergprj"
    destination.write_bytes(b"do not replace")
    assert main([str(mapped), "--output", str(destination)]) == 1
    assert json.loads(capsys.readouterr().err)["status"] == "error"
    assert destination.read_bytes() == b"do not replace"
    invalid = tmp_path / "invalid.ergprj"
    invalid.write_text("not a project", encoding="utf-8")
    target = tmp_path / "never-published.ergprj"
    assert main([str(invalid), "--output", str(target)]) == 1
    assert json.loads(capsys.readouterr().err)["status"] == "error"
    assert not target.exists()


def test_missing_utility_does_not_affect_native_project(
    archived: ProjectSnapshot, tmp_path: Path
) -> None:
    """Native Open and Backup do not require the optional executable to exist.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    adapter = ExternalProjectMigration((str(tmp_path / "missing-utility"),))
    with pytest.raises(OSError):
        adapter.convert("unused", str(tmp_path / "unused-output"))
    with AssessmentProjectFile.create_from_snapshot(
        tmp_path / "native.ergprj", archived
    ) as project:
        identity, expected = archived.saved_results[0]
        key = DocumentKey(project.metadata.project_id, identity)
        assert not adapter.requires_conversion(str(tmp_path / "native.ergprj"))
        with project.snapshot(str(tmp_path / "backup.ergprj"), None, None) as backup:
            assert backup.load_saved_result(key) == expected


def test_previous_upgrade_preserves_fresh_and_original_results(
    archived: ProjectSnapshot, mapped: Path, tmp_path: Path
) -> None:
    """Recalculate current inputs and discard every old result during native upgrade.

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
    identity, observation = archived.saved_results[0]
    key = DocumentKey(archived.metadata.project_id, identity)
    fresh = calculate(DocumentSession(key, observation.source))
    historical = previous_converted(
        replace(archived, saved_results=((identity, fresh),)),
        mapped,
        tmp_path / "previous.ergprj",
    )
    original = historical.read_bytes()
    adapter = ExternalProjectMigration()
    assert adapter.requires_conversion(str(historical))
    destination = tmp_path / "upgraded.ergprj"
    with upgrade_previous_project(historical, destination) as project:
        assert project.load_saved_result(key) == fresh
        assert project.load_hierarchy() == archived.hierarchy
        assert project.load_jobs() == archived.jobs
        assert project.load_job_risk() == archived.risks
        assert project.load_plot_positions() == archived.positions
        assert project.load_rotation_schemes() == archived.rotations
        assert all(
            project.load_plant_image(plant) == image for plant, image in archived.images
        )
        with project.snapshot(str(tmp_path / "saved-copy.ergprj"), None, None) as copy:
            assert copy.load_saved_result(key) == fresh
    assert historical.read_bytes() == original
    assert not adapter.requires_conversion(str(destination))


@pytest.mark.parametrize("field", ["saved_results"])
def test_snapshot_result_ownership_validation(
    archived: ProjectSnapshot, field: str
) -> None:
    """Reject duplicate observations and outputs without a matching source owner.

    Args:
        archived: Prior-format source/result fixture or scenario flag; current native
            output still has one authoritative result.
        field: Explicit input field identity targeted by the parametrized invalid/change
            scenario.

    Returns:
        None.
    """
    results = archived.saved_results
    with pytest.raises(ValueError, match="duplicate"):
        replace(archived, **{field: results * 2})
    with pytest.raises(ValueError, match="owner"):
        replace(archived, **{field: (("missing", results[0][1]),)})
