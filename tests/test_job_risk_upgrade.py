"""External format-18 Job collapse, exact retained values and failure publication.

Test layer. Generate disposable earlier-native schemas, retaining the original input
bytes. Maintained fixtures, reference code and operational databases stay untouched.
"""

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation_scheme import RotationMode
from tests.test_history_persistence import SOURCE
from tests.test_rotation_persistence import scheme, seed
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)


def earlier_job_project(path: Path) -> None:
    """Build an earlier full native Job/profile schema with a frozen old rotation.

    Args:
        path: Nonexistent disposable input location.

    Returns:
        None; current profile has 80 percent while the old optimized target used zero.
        The mismatch must retain arrangement cells and invalidate old provenance.
    """
    with seed(path, version=19) as project:
        project.save_rotation_scheme(
            replace(
                scheme(),
                mode=RotationMode.SINGLE_TOOL,
                primary_kind=AssessmentKind.LIFFT,
            )
        )
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("DROP TABLE risk_measurements")
        connection.execute("CREATE TABLE risk_metadata(project_id TEXT)")
        connection.execute("INSERT INTO risk_metadata VALUES ('p')")
        connection.execute(
            "CREATE TABLE risk_profiles(id INTEGER PRIMARY KEY,job_id TEXT,"
            "is_current INTEGER,position INTEGER,notes TEXT)"
        )
        connection.executemany(
            "INSERT INTO risk_profiles VALUES (?,?,?,?,?)",
            (
                (1, "j", 0, 0, "discard old evidence"),
                (2, "j", 1, 1, "discard selected evidence"),
            ),
        )
        connection.execute(
            "CREATE TABLE risk_measurements(profile_id INTEGER,kind TEXT,damage REAL,"
            "probability REAL,unit TEXT,notes TEXT,position INTEGER)"
        )
        connection.executemany(
            "INSERT INTO risk_measurements VALUES (?,?,?,?,?,?,?)",
            (
                (1, "lifft", 0, 0, "Imperial", "old", 0),
                (2, "lifft", 0.123456789, 80.123456789, "Metric", "remove", 0),
            ),
        )
        payload = json.loads(
            connection.execute("SELECT payload FROM rotation_schemes").fetchone()[0]
        )
        target = payload["targets"][0]
        old_key = f"{len(target[0])}:{target[0]}:{target[1]}:1"
        payload["targets"] = [[target[0], 1, target[1]]]
        payload["current"] = [
            [worker, [old_key for _ in cells]] for worker, cells in payload["current"]
        ]
        payload["version"] = 1
        connection.execute(
            "UPDATE rotation_schemes SET payload=?", (json.dumps(payload),)
        )
        connection.execute("UPDATE project_metadata SET version=18")


def test_selected_values_survive_and_old_schedule_uses_current_values(
    tmp_path: Path,
) -> None:
    """Drop all evidence/version rows, keep exact selected numbers and Job arrangements.

    Args:
        tmp_path: Disposable original/output directory.

    Returns:
        None; conversion does not recalculate selected Job or worker values.
    """
    path, output = tmp_path / "previous.ergprj", tmp_path / "current.ergprj"
    earlier_job_project(path)
    before = path.read_bytes()
    with upgrade_previous_project(path, output) as project:
        assert project.format_version == 19
        values = project.load_job_risk().for_job("j").measurements
        assert len(values) == 1
        assert values[0].cumulative_damage == 0.123456789
        assert values[0].probability_percent == 80.123456789
        assert values[0].source is None and not values[0].task_results
        saved = project.load_rotation_schemes()[0]
        assert saved.current == scheme().current and saved.targets == scheme().targets
        assert saved.mode is RotationMode.MANUAL and saved.primary_kind is None
        assert project.load(DocumentKey("p", "source")) == SOURCE
    assert path.read_bytes() == before
    with closing(sqlite3.connect(output)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert not tables & {"risk_profiles", "risk_metadata"}
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(risk_measurements)")
        }
        assert columns == {
            "job_id",
            "kind",
            "damage",
            "probability",
            "unit",
            "source",
            "position",
            "task_results",
        }
        assert not connection.execute("PRAGMA foreign_key_check").fetchall()


@pytest.mark.parametrize("failure", ("ambiguous", "write", "collapsed_targets"))
def test_failed_upgrade_preserves_input_and_does_not_publish(
    tmp_path: Path, failure: str
) -> None:
    """Ambiguous ownership and failed writes never publish a project.

    Args:
        tmp_path: Disposable input/output directory.
        failure: Deliberate invalid ownership or conversion write failure.

    Returns:
        None; exact original bytes survive without publishing an output file.
    """
    path, output = tmp_path / "previous.ergprj", tmp_path / "must-not-exist.ergprj"
    earlier_job_project(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        if failure == "ambiguous":
            connection.execute("UPDATE risk_profiles SET is_current=1")
        elif failure == "collapsed_targets":
            payload = json.loads(
                connection.execute("SELECT payload FROM rotation_schemes").fetchone()[0]
            )
            payload["targets"].append(["j", 2, 1])
            connection.execute(
                "UPDATE rotation_schemes SET payload=?", (json.dumps(payload),)
            )
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    if failure == "write":
        with (
            patch(
                "tools.project_migration.ergotools_migration.job_risk_upgrade.create_risk_schema",
                side_effect=OSError("injected write"),
            ),
            pytest.raises(OSError),
        ):
            upgrade_previous_project(path, output)
    else:
        with pytest.raises(ValueError):
            upgrade_previous_project(path, output)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert not output.exists()
