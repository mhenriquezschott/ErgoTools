"""Version-four catalog round trips, binding integrity and transaction recovery.

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

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import AssessmentContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.work_hierarchy_store import (
    decode_hierarchy,
    encode_hierarchy,
)

# Explicit synthetic project identity/title/default units; assessment units are
# preserved independently.
META = ProjectMetadata("p", "Catalog", MeasurementSystem.IMPERIAL)
# Exact synthetic station ancestry; repeated station captions on other branches remain
# distinct.
STATION = StationKey("Plant", "Section", "Line", "001")
# Immutable synthetic complete hierarchy, including the empty branches/shifts needed by
# these tests.
HIERARCHY = WorkHierarchy(
    WorkCatalog(
        "p",
        (WorkerEntry("w 1", "Ana", None), WorkerEntry("w2", "", "Last")),
        (STATION,),
        ("Night", "Day"),
    ),
    ("Plant", "Empty plant"),
    (SectionKey("Plant", "Section"), SectionKey("Plant", "Empty section")),
    (LineKey("Plant", "Section", "Line"), LineKey("Plant", "Section", "Empty line")),
)
# Exact synthetic project/document key; tests verify isolation without deriving identity
# from row position.
KEY = DocumentKey("p", "lifft")
# Immutable synthetic imperial LiFFT draft; missing inputs remain absent rather than
# becoming zeros.
SOURCE = LifftDraft(MeasurementSystem.IMPERIAL)
# Exact worker/workplace/tool assessment context for binding and lookup tests.
CONTEXT = AssessmentContext(
    HIERARCHY.work.worker_context("w 1", STATION.at_shift("Day")), AssessmentKind.LIFFT
)
# Exact assessment document-to-context link; source and ownership must persist
# atomically.
BINDING = AssessmentBinding(KEY, CONTEXT)


def seed(path: Path) -> None:
    """Create a fully bound synthetic project, never touch operational data.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    with AssessmentProjectFile.create_catalogued(path, META) as project:
        project.save_hierarchy(HIERARCHY)
        project.insert_assessment(KEY, SOURCE)
        project.bind_assessment(BINDING)


def test_ordered_catalog_and_bindings_survive_reopen(tmp_path: Path) -> None:
    """Retain empty parents, missing names, exact IDs and array ordering.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "catalog.sqlite"
    with AssessmentProjectFile.create_catalogued(path, META) as project:
        assert project.format_version == 4
        assert project.load_hierarchy() == WorkHierarchy(WorkCatalog("p"))
        project.save_hierarchy(HIERARCHY)
        project.insert_assessment(KEY, SOURCE)
        project.bind_assessment(BINDING)
    with AssessmentProjectFile.open(path) as project:
        assert project.load_hierarchy() == HIERARCHY
        assert project.assessment_binding(KEY) == BINDING
        assert project.find_assessment(CONTEXT) == KEY
        renamed = replace(
            HIERARCHY,
            work=replace(
                HIERARCHY.work,
                workers=(
                    WorkerEntry("w2", "Changed", "Name"),
                    WorkerEntry("w 1", "New", "Name"),
                ),
            ),
        )
        project.save_hierarchy(renamed)
        assert project.load_hierarchy() == renamed
        assert project.find_assessment(CONTEXT) == KEY
        assert project.load(KEY) == SOURCE


def test_catalog_cannot_orphan_bound_assessments(tmp_path: Path) -> None:
    """Removing a referenced worker, station or shift rolls back the entire save.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "catalog.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        for work in (
            replace(HIERARCHY.work, workers=(WorkerEntry("w2"),)),
            replace(HIERARCHY.work, stations=()),
            replace(HIERARCHY.work, shifts=("Night",)),
        ):
            with pytest.raises(KeyError):
                project.save_hierarchy(replace(HIERARCHY, work=work))
            assert project.load_hierarchy() == HIERARCHY
            assert project.find_assessment(CONTEXT) == KEY
        with pytest.raises(ValueError, match="another project"):
            project.save_hierarchy(
                replace(HIERARCHY, work=replace(HIERARCHY.work, project_id="other"))
            )
        project.save_hierarchy(replace(HIERARCHY, plants=("Plant",)))
        assert project.load_hierarchy().plants == ("Plant",)


def test_new_binding_requires_catalog_membership_and_is_retryable(
    tmp_path: Path,
) -> None:
    """A saved draft stays unbound after failure until its owner exists.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "catalog.sqlite"
    with AssessmentProjectFile.create_catalogued(path, META) as project:
        project.insert_assessment(KEY, SOURCE)
        with pytest.raises(KeyError):
            project.bind_assessment(BINDING)
        assert project.assessment_binding(KEY) is None
        project.save_hierarchy(HIERARCHY)
        project.bind_assessment(BINDING)
        project.bind_assessment(BINDING)
        assert project.assessment_binding(KEY) == BINDING


def test_sql_failure_retains_catalog_and_bindings_then_retry_succeeds(
    tmp_path: Path,
) -> None:
    """Inject an actual SQL abort, then verify the complete old snapshot survives.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "catalog.sqlite"
    seed(path)
    changed = replace(HIERARCHY, plants=(*HIERARCHY.plants, "New plant"))
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER fail_catalog BEFORE UPDATE ON work_catalog "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(sqlite3.IntegrityError):
            project.save_hierarchy(changed)
        assert project.load_hierarchy() == HIERARCHY
        assert project.find_assessment(CONTEXT) == KEY
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER fail_catalog")
        project.save_hierarchy(changed)
    with AssessmentProjectFile.open(path) as project:
        assert project.load_hierarchy() == changed


@pytest.mark.parametrize("version", [1, 2, 3])
def test_old_project_formats_are_unchanged(tmp_path: Path, version: int) -> None:
    """No implicit upgrade occurs when the new capability is requested.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "old.sqlite"
    factory = {
        1: ProjectFile.create,
        2: AssessmentProjectFile.create,
        3: AssessmentProjectFile.create_contextual,
    }[version]
    with factory(path, META):
        pass
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(StoreFormatError):
            project.load_hierarchy()
        with pytest.raises(StoreFormatError):
            project.save_hierarchy(HIERARCHY)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "damage", ["absent", "foreign", "orphan", "binding", "malformed"]
)
def test_corrupt_catalogs_fail_on_open_without_repair(
    tmp_path: Path, damage: str
) -> None:
    """Do not silently recreate catalogs or erase damaged ownership evidence.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        damage: Dimensionless damage boundary input (or deliberate invalid text) for the
            stated scenario.

    Returns:
        None.
    """
    path = tmp_path / "catalog.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        if damage == "absent":
            connection.execute("DELETE FROM work_catalog")
        elif damage == "binding":
            connection.execute("UPDATE assessment_bindings SET project_id='foreign'")
        else:
            value = json.loads(encode_hierarchy(HIERARCHY))
            if damage == "foreign":
                value["hierarchy"]["work"]["project_id"] = "foreign"
            elif damage == "orphan":
                value["hierarchy"]["work"]["workers"] = []
            payload = "{}" if damage == "malformed" else json.dumps(value)
            connection.execute("UPDATE work_catalog SET payload=?", (payload,))
    before = path.read_bytes()
    with pytest.raises((ValueError, KeyError)):
        AssessmentProjectFile.open(path)
    assert path.read_bytes() == before


def test_codec_rejects_malformed_versions_fields_and_relationships() -> None:
    """Strict decoding rejects ambiguous or structurally invalid payloads.

    Args:
        None.

    Returns:
        None.
    """
    assert decode_hierarchy(encode_hierarchy(HIERARCHY)) == HIERARCHY
    invalid = ['{"version":1,"version":1,"hierarchy":{}}', "{", "[]"]
    for version in (True, 1.0, 4, None):
        value = json.loads(encode_hierarchy(HIERARCHY))
        value["version"] = version
        invalid.append(json.dumps(value))
    for field in ("workers", "stations", "shifts"):
        value = json.loads(encode_hierarchy(HIERARCHY))
        value["hierarchy"]["work"][field] = None
        invalid.append(json.dumps(value))
    for field in ("first_name", "last_name"):
        value = json.loads(encode_hierarchy(HIERARCHY))
        value["hierarchy"]["work"]["workers"][0][field] = 1
        invalid.append(json.dumps(value))
    for field in ("plants", "sections", "lines"):
        value = json.loads(encode_hierarchy(HIERARCHY))
        value["hierarchy"][field] = []
        invalid.append(json.dumps(value))
    value = json.loads(encode_hierarchy(HIERARCHY))
    value["hierarchy"]["work"]["workers"] *= 2
    invalid.append(json.dumps(value))
    for payload in invalid:
        with pytest.raises(ValueError):
            decode_hierarchy(payload)


def test_failed_creation_cleanup_and_closed_repository(tmp_path: Path) -> None:
    """An incomplete new file is removed; existing destinations remain protected.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "catalog.sqlite"
    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.create_hierarchy_schema",
            side_effect=sqlite3.OperationalError("injected"),
        ),
        pytest.raises(sqlite3.OperationalError),
    ):
        AssessmentProjectFile.create_catalogued(path, META)
    assert not path.exists()
    seed(path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        AssessmentProjectFile.create_catalogued(path, META)
    assert path.read_bytes() == before
    project = AssessmentProjectFile.open(path)
    project.close()
    with pytest.raises(RuntimeError, match="closed"):
        project.load_hierarchy()
    with pytest.raises(RuntimeError, match="closed"):
        project.save_hierarchy(HIERARCHY)
