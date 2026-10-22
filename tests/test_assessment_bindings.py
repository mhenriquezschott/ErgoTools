"""Context persistence against temporary projects, including rollback and history.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.context import (
    AssessmentContext,
    WorkerContext,
    WorkplaceContext,
)
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile

# Explicit synthetic project identity/title/default units; assessment units are
# preserved independently.
META = ProjectMetadata("p", "Context tests", MeasurementSystem.IMPERIAL)
# Exact synthetic project/document key; tests verify isolation without deriving identity
# from row position.
KEY = DocumentKey("p", "lifft")
# Immutable synthetic imperial LiFFT draft; missing inputs remain absent rather than
# becoming zeros.
SOURCE = LifftDraft(MeasurementSystem.IMPERIAL)
# Exact project/worker/workplace/shift ownership used to distinguish historical
# assignment links.
OWNER = WorkerContext(
    "p", "w", WorkplaceContext("plant", "section", "line", "s", "day")
)
# Exact worker/workplace/tool assessment context for binding and lookup tests.
CONTEXT = AssessmentContext(OWNER, AssessmentKind.LIFFT)
# Exact assessment document-to-context link; source and ownership must persist
# atomically.
BINDING = AssessmentBinding(KEY, CONTEXT)


def seed(path: Path) -> None:
    """Create an unbound version-three source without operational data.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    with AssessmentProjectFile.create_contextual(path, META) as project:
        project.insert_assessment(KEY, SOURCE)


def test_binding_roundtrip_all_models_and_exact_spelling(tmp_path: Path) -> None:
    """Keep independent tools and original source units across close/open.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    sources = (SOURCE, DuetDraft(), TstDraft(MeasurementSystem.METRIC))
    owner = replace(OWNER, worker_id=" worker ' \u00f1 ")
    with AssessmentProjectFile.create_contextual(path, META) as project:
        for kind, source in zip(AssessmentKind, sources, strict=True):
            key = DocumentKey("p", kind.value)
            binding = AssessmentBinding(key, AssessmentContext(owner, kind))
            project.insert_assessment(key, source)
            assert project.assessment_binding(key) is None
            project.bind_assessment(binding)
            project.bind_assessment(binding)
    with AssessmentProjectFile.open(path) as project:
        assert project.format_version == 3
        for kind, source in zip(AssessmentKind, sources, strict=True):
            context = AssessmentContext(owner, kind)
            key = DocumentKey("p", kind.value)
            assert project.find_assessment(context) == key
            assert project.assessment_binding(key) == AssessmentBinding(key, context)
            assert project.load(key) == source


def test_conflicts_rollback_and_leave_sources_retryable(tmp_path: Path) -> None:
    """Reject model mismatch, reassignment and duplicate ownership without damage.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    second = DocumentKey("p", "second")
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(StoreFormatError, match="model"):
            project.bind_assessment(
                replace(BINDING, context=replace(CONTEXT, kind=AssessmentKind.DUET))
            )
        assert project.assessment_binding(KEY) is None
        project.bind_assessment(BINDING)
        changed = replace(CONTEXT, worker=replace(OWNER, worker_id="other"))
        with pytest.raises(ValueError, match="ownership"):
            project.bind_assessment(replace(BINDING, context=changed))
        project.insert_assessment(second, SOURCE)
        with pytest.raises(sqlite3.IntegrityError):
            project.bind_assessment(replace(BINDING, document=second))
        assert project.assessment_binding(second) is None
        project.bind_assessment(AssessmentBinding(second, changed))
        assert project.find_assessment(CONTEXT) == KEY
        assert project.find_assessment(changed) == second
        assert project.load(KEY) == project.load(second) == SOURCE


def test_lookup_isolates_every_context_component(tmp_path: Path) -> None:
    """Matching cannot fall back to another worker, station, shift or model.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        project.bind_assessment(BINDING)
        contexts = [replace(CONTEXT, kind=AssessmentKind.DUET)]
        contexts.append(replace(CONTEXT, worker=replace(OWNER, worker_id="W")))
        for field in (
            "plant_name",
            "section_name",
            "line_name",
            "station_id",
            "shift_id",
        ):
            owner = replace(
                OWNER, workplace=replace(OWNER.workplace, **{field: "other"})
            )
            contexts.append(replace(CONTEXT, worker=owner))
        for context in contexts:
            assert project.find_assessment(context) is None
        foreign = replace(CONTEXT, worker=replace(OWNER, project_id="other"))
        with pytest.raises(ValueError, match="another project"):
            project.find_assessment(foreign)
        with pytest.raises(ValueError, match="cross projects"):
            AssessmentBinding(KEY, foreign)
        with pytest.raises(ValueError, match="another project"):
            project.bind_assessment(
                AssessmentBinding(DocumentKey("other", "x"), foreign)
            )
        with pytest.raises(KeyError):
            project.assessment_binding(DocumentKey("p", "missing"))
        with pytest.raises(KeyError):
            project.bind_assessment(
                replace(BINDING, document=DocumentKey("p", "missing"))
            )


def test_sql_failure_rolls_back_and_binding_does_not_save_dirty_history(
    tmp_path: Path,
) -> None:
    """Failed metadata writes preserve dirty edits and allow deliberate retry.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    session = DocumentSession(KEY, SOURCE)
    session.execute(AddLifftTask(KEY, LifftTask("a", 12, 10, 100), 0))
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_binding BEFORE INSERT ON assessment_bindings "
            "BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
        )
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(sqlite3.IntegrityError, match="injected"):
            project.bind_assessment(BINDING)
        assert project.assessment_binding(KEY) is None
        assert session.is_dirty
        assert project.load(KEY) == SOURCE
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER reject_binding")
        project.bind_assessment(BINDING)
        assert session.is_dirty
        session.save(project)
        assert not session.is_dirty
        session.undo()
        assert session.is_dirty
        assert project.assessment_binding(KEY) == BINDING
    with AssessmentProjectFile.open(path) as project:
        assert project.load(KEY).tasks[0].task_id == "a"
        assert project.find_assessment(CONTEXT) == KEY


@pytest.mark.parametrize("version", [1, 2])
def test_old_formats_are_never_upgraded(tmp_path: Path, version: int) -> None:
    """Unsupported ownership operations leave existing project bytes unchanged.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "old.sqlite"
    factory = ProjectFile if version == 1 else AssessmentProjectFile
    with factory.create_with_document(path, META, KEY.document_id, SOURCE):
        pass
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as project:
        for operation in (
            lambda: project.bind_assessment(BINDING),
            lambda: project.assessment_binding(KEY),
            lambda: project.find_assessment(CONTEXT),
        ):
            with pytest.raises(StoreFormatError, match="version three"):
                operation()
        assert project.load(KEY) == SOURCE
    assert path.read_bytes() == before


@pytest.mark.parametrize("damage", ["kind", "owner", "orphan", "foreign"])
def test_corrupt_bindings_are_rejected_on_open(tmp_path: Path, damage: str) -> None:
    """Reject damaged ownership before returning a usable project handle.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        damage: Dimensionless damage boundary input (or deliberate invalid text) for the
            stated scenario.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        project.bind_assessment(BINDING)
    statements = {
        "kind": "UPDATE assessment_bindings SET kind='duet'",
        "owner": "UPDATE assessment_bindings SET worker_id=''",
        "orphan": "DELETE FROM draft_documents",
        "foreign": "UPDATE assessment_bindings SET project_id='other'",
    }
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(statements[damage])
    before = path.read_bytes()
    with pytest.raises((ValueError, KeyError)):
        AssessmentProjectFile.open(path)
    assert path.read_bytes() == before


def test_closed_handles_and_failed_creation(tmp_path: Path) -> None:
    """Close guards all ownership APIs; failed creation never removes old files.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    with (
        patch(
            "ergotools.infrastructure.assessment_project_file.create_binding_schema",
            side_effect=sqlite3.OperationalError("injected"),
        ),
        pytest.raises(sqlite3.OperationalError),
    ):
        AssessmentProjectFile.create_contextual(path, META)
    assert not path.exists()
    seed(path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        AssessmentProjectFile.create_contextual(path, META)
    assert path.read_bytes() == before
    project = AssessmentProjectFile.open(path)
    project.close()
    for operation in (
        lambda: project.bind_assessment(BINDING),
        lambda: project.assessment_binding(KEY),
        lambda: project.find_assessment(CONTEXT),
    ):
        with pytest.raises(RuntimeError, match="closed"):
            operation()
