"""Independent database and GUI acceptance of one assessment per assignment/tool.

Test layer. Convert read-only fixture inputs only into pytest-owned destinations;
compare real task/result/analysis data, enforce unique/FK ownership and prove ambiguous
populated duplicates stop before SQL changes. No production/reference file is mutated.
"""

import hashlib
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import fields, replace
from pathlib import Path

import pytest

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.session import DocumentKey
from ergotools.application.settings import Language
from ergotools.domain.assessment_history import AssessmentHistory, AssignmentAssessment
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_saved_tool_data import window as window
from tools.project_migration.ergotools_migration.ownership_upgrade import (
    upgrade_assessment_ownership,
)
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)


def previous_fixture(source: Path, destination: Path) -> Path:
    """Build an obsolete schema only inside a disposable conversion test database.

    Args:
        source: Maintained current fixture opened strictly read-only.
        destination: Pytest-owned temporary path; never an application fixture path.

    Returns:
        Format-14 conversion input with one proven empty duplicate LiFFT draft. Real
        inputs/results and all unrelated tables remain byte-identical to the source.
        No outdated fixture is retained in the project tree.
    """
    with (
        closing(
            sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        ) as old,
        closing(sqlite3.connect(destination)) as copy,
    ):
        old.backup(copy)
        with copy:
            rows = copy.execute(
                "SELECT document_id,assignment_id,kind,position "
                "FROM assessment_ownership ORDER BY position"
            ).fetchall()
            copy.execute("DROP TABLE assessment_ownership")
            copy.execute(
                "CREATE TABLE assessment_history(document_id TEXT PRIMARY KEY,"
                "assignment_id INTEGER,kind TEXT,version INTEGER,"
                "is_current INTEGER,"
                "position INTEGER UNIQUE)"
            )
            copy.executemany("INSERT INTO assessment_history VALUES(?,?,?,1,1,?)", rows)
            copy.execute("CREATE TABLE assessment_bindings(document_id TEXT)")
            first = next(row for row in rows if row[2] == "lifft")
            copy.execute(
                "INSERT INTO assessment_history VALUES(?,?,?,2,0,?)",
                ("empty-duplicate", first[1], first[2], len(rows)),
            )
            project_id = copy.execute(
                "SELECT project_id FROM project_metadata"
            ).fetchone()[0]
            copy.execute(
                "INSERT INTO draft_documents VALUES(?,?,?)",
                (
                    project_id,
                    "empty-duplicate",
                    encode_assessment(LifftDraft(MeasurementSystem.METRIC)),
                ),
            )
            copy.execute("UPDATE project_metadata SET version=14")
    return destination


@pytest.mark.parametrize("name", ["comparative_risk_test", "integrated_test"])
def test_conversion_preserves_real_data_and_removes_version_schema(
    tmp_path: Path, name: str
) -> None:
    """Check actual comprehensive conversions rather than synthetic version assertions.

    Args:
        tmp_path: Pytest-owned directory for converted, Save As and backup files.
        name: One of the two read-only comprehensive input fixture basenames.

    Returns:
        None; retained sources/results/catalogs/layouts/schemes match exactly, and both
        copy workflows reopen with one assessment per assignment/tool and no old tables.
    """
    original = (
        Path(__file__).resolve().parents[1]
        / "test_projects/native"
        / (name + ".ergprj")
    )
    original = previous_fixture(original, tmp_path / "previous.ergprj")
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    with closing(
        sqlite3.connect(original.resolve().as_uri() + "?mode=ro", uri=True)
    ) as old:
        results = dict(
            old.execute("SELECT document_id,payload FROM saved_assessment_results")
        )
        real_sources = {
            key: old.execute(
                "SELECT payload FROM draft_documents WHERE document_id=?", (key,)
            ).fetchone()[0]
            for key in results
        }
        untouched = {
            table: old.execute('SELECT * FROM "' + table + '"').fetchall()
            for table in (
                "jobs",
                "job_placements",
                "worker_assignments",
                "work_catalog",
                "risk_measurements",
                "plant_layout_images",
                "plot_worker_markers",
                "plot_station_positions",
                "rotation_schemes",
            )
        }
    if name == "comparative_risk_test":
        # A removed empty draft can occur in the middle, not only at the end.
        # Compact ownership positions so the next normal insert cannot collide.
        with (
            closing(
                sqlite3.connect(original.resolve().as_uri() + "?mode=ro", uri=True)
            ) as old,
            closing(sqlite3.connect(":memory:")) as copy,
        ):
            old.backup(copy)
            with copy:
                copy.execute("UPDATE assessment_history SET position=position+1000")
                copy.execute("UPDATE assessment_history SET position=0 WHERE version>1")
                copy.execute(
                    "UPDATE assessment_history SET position=position-999 "
                    "WHERE version=1"
                )
            with copy:
                copy.execute("BEGIN")
                upgrade_assessment_ownership(copy)
            positions = [
                row[0]
                for row in copy.execute(
                    "SELECT position FROM assessment_ownership ORDER BY position"
                )
            ]
            assert positions == list(range(194))
            assert (
                dict(
                    copy.execute(
                        "SELECT document_id,payload FROM saved_assessment_results"
                    )
                )
                == results
            )
    destination = tmp_path / "converted.ergprj"
    with upgrade_previous_project(original, destination) as project:
        assert project.format_version == 19
        assert len(project.load_history().entries) == 194
        project.load_plot_positions().validate(
            project.load_hierarchy(), project.load_jobs()
        )
        project.load_rotation_schemes()
        for entry in project.load_history().entries:
            key = DocumentKey(project.metadata.project_id, entry.document_id)
            assert (
                encode_assessment(project.load(key)) == real_sources[entry.document_id]
            )
            assert project.load_saved_result(key) is not None
        for copy_name in ("save_as.ergprj", "backup.ergprj"):
            with project.snapshot(str(tmp_path / copy_name), None, None) as copy:
                assert copy.load_history() == project.load_history()
                assert copy.load_plot_positions() == project.load_plot_positions()
                assert copy.load_rotation_schemes() == project.load_rotation_schemes()
    for file in (destination, tmp_path / "save_as.ergprj", tmp_path / "backup.ergprj"):
        with closing(sqlite3.connect(file)) as new:
            assert new.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
            assert not new.execute("PRAGMA foreign_key_check").fetchall()
            tables = {
                r[0]
                for r in new.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            assert "assessment_ownership" in tables
            assert not tables & {"assessment_history", "assessment_bindings"}
            assert [
                r[1] for r in new.execute("PRAGMA table_info(assessment_ownership)")
            ] == ["document_id", "worker_id", "assignment_id", "kind", "position"]
            assert (
                dict(
                    new.execute(
                        "SELECT document_id,payload FROM saved_assessment_results"
                    )
                )
                == results
            )
            for table, rows in untouched.items():
                assert Counter(
                    new.execute('SELECT * FROM "' + table + '"').fetchall()
                ) == Counter(rows)
    assert hashlib.sha256(original.read_bytes()).hexdigest() == digest


def test_populated_duplicate_conversion_refuses_before_mutation(tmp_path: Path) -> None:
    """Never choose/drop competing real data when removing the version model.

    Args:
        tmp_path: Pytest-owned directory for an obsolete-schema conversion input.

    Returns:
        None; ambiguous duplicate inputs raise and the private snapshot is unchanged.
    """
    path = (
        Path(__file__).resolve().parents[1]
        / "test_projects/native/comparative_risk_test.ergprj"
    )
    path = previous_fixture(path, tmp_path / "conflicting.ergprj")
    with (
        closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        ) as original,
        closing(sqlite3.connect(":memory:")) as copy,
    ):
        original.backup(copy)
        identity = copy.execute(
            "SELECT document_id FROM assessment_history WHERE version>1"
        ).fetchone()[0]
        payload = copy.execute(
            "SELECT payload FROM draft_documents WHERE document_id=?", (identity,)
        ).fetchone()[0]
        source = decode_assessment(payload)
        source = replace(
            source,
            tasks=(LifftTask("populated", 12, 20, 100),),
        )
        with copy:
            copy.execute(
                "UPDATE draft_documents SET payload=? WHERE document_id=?",
                (encode_assessment(source), identity),
            )
        before = copy.serialize()
        with copy:
            copy.execute("BEGIN")
            with pytest.raises(ValueError, match="populated"):
                upgrade_assessment_ownership(copy)
        assert copy.serialize() == before


@pytest.mark.parametrize("language", list(Language))
@pytest.mark.parametrize("index", [0, 1, 2])
def test_no_version_controls_and_save_keeps_unique_owner(
    window: LifftWindow, language: Language, index: int
) -> None:
    """All tool/language routes lack version actions and retain ordinary Save behavior.

    Args:
        window: Fixture-owned integrated Qt window on a disposable native project.
        language: Supported initial UI language.
        index: LiFFT, DUET or ST tab position.

    Returns:
        None; unwanted buttons/handlers/menu entries are absent and Save creates no
        duplicate owner or source. Other assignments/tools remain unchanged.
    """
    window.language = language
    window.translate()
    window.assessment_tabs.setCurrentIndex(index)
    window.refresh()
    assert not {"new_version", "current_version"} & window.buttons.keys()
    assert (
        not {"new_version", "current_version"}
        & window._assessment_menu.actions_by_key.keys()
    )
    assert not hasattr(window, "create_blank_version") and not hasattr(
        window, "choose_current_version"
    )
    assert {f.name for f in fields(AssignmentAssessment)} == {
        "document_id",
        "assignment_id",
        "kind",
        "worker_id",
    }
    workspace = window.presenter.workspace
    before = workspace.read_history().history
    window.main_navigation.toolbar_actions["save"].trigger()
    assert workspace.read_history().history == before
    owner = before.entries[0]
    with pytest.raises(ValueError, match="assignment/tool"):
        AssessmentHistory(
            before.project_id,
            (*before.entries, replace(owner, document_id="duplicate")),
        )


def test_sql_constraints_reject_duplicate_owner_and_missing_assignment(
    tmp_path: Path,
) -> None:
    """Enforce unique owners and deferred foreign keys inside actual repository writes.

    Args:
        tmp_path: Test-owned synthetic project directory; no operational data is used.

    Returns:
        None; both corrupt writes roll back and the original source/ownership reopens.
    """
    from tests.test_workspace_job_risk import workspace_at

    workspace = workspace_at(tmp_path)
    try:
        with AssessmentProjectFile.open(Path(workspace.location)) as project:
            connection = project._connection
            assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
            entry = project.load_history().entries[0]
            before = project.load_history()
            with pytest.raises(sqlite3.IntegrityError), connection:
                connection.execute(
                    "INSERT INTO assessment_ownership VALUES (?,?,?,?,?)",
                    (
                        "duplicate",
                        entry.worker_id,
                        entry.assignment_id,
                        entry.kind.value,
                        10,
                    ),
                )
            with pytest.raises(sqlite3.IntegrityError), connection:
                connection.execute(
                    "INSERT INTO assessment_ownership VALUES (?,?,?,?,?)",
                    ("dangling", entry.worker_id, 999999, entry.kind.value, 10),
                )
            assert project.load_history() == before
            assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
