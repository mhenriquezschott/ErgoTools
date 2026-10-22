"""Atomic assessment creation, context uniqueness and workspace dirty choices.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import AssessmentContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_binding_store import (
    AssessmentBindingStore,
    create_binding_schema,
)
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.infrastructure.draft_store import DocumentExistsError, StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore

# Explicit synthetic project identity/title/default units; assessment units are
# preserved independently.
META = ProjectMetadata("p", "Atomic", MeasurementSystem.IMPERIAL)
# Immutable synthetic imperial LiFFT draft; missing inputs remain absent rather than
# becoming zeros.
SOURCE = LifftDraft(MeasurementSystem.IMPERIAL)
# Exact synthetic project/document key; tests verify isolation without deriving identity
# from row position.
KEY = DocumentKey("p", "old")
# Immutable exact synthetic worker/job/catalog relationships used by these isolated
# regressions.
CATALOG = WorkHierarchy(
    WorkCatalog("p", (WorkerEntry("w"),), (StationKey("P", "S", "L", "1"),), ("Day",)),
    ("P",),
    (SectionKey("P", "S"),),
    (LineKey("P", "S", "L"),),
)
# Exact worker/workplace/tool assessment context for binding and lookup tests.
CONTEXT = AssessmentContext(
    CATALOG.work.worker_context("w", CATALOG.work.available_workplaces()[0]),
    AssessmentKind.LIFFT,
)
# Exact assessment document-to-context link; source and ownership must persist
# atomically.
BINDING = AssessmentBinding(DocumentKey("p", "new"), CONTEXT)


def seed(path: Path) -> None:
    """Create an unbound initial draft with a complete synthetic owner catalog.

    Args:
        path: Disposable test file path; the caller controls creation and cleanup.

    Returns:
        None.
    """
    with AssessmentProjectFile.create_catalogued(path, META) as project:
        project.save_hierarchy(CATALOG)
        project.insert_assessment(KEY, SOURCE)


@pytest.mark.parametrize("version", [3, 4])
def test_all_models_create_and_bind_together(tmp_path: Path, version: int) -> None:
    """Preserve version-three behavior and version-four membership validation.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        version: Explicit historical/native test-format version used to exercise
            acceptance or rejection boundaries.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    factory = (
        AssessmentProjectFile.create_contextual
        if version == 3
        else AssessmentProjectFile.create_catalogued
    )
    sources = (SOURCE, DuetDraft(), TstDraft(MeasurementSystem.METRIC))
    with factory(path, META) as project:
        if version == 4:
            project.save_hierarchy(CATALOG)
        for kind, source in zip(AssessmentKind, sources, strict=True):
            binding = AssessmentBinding(
                DocumentKey("p", kind.value), replace(CONTEXT, kind=kind)
            )
            project.create_bound_assessment(binding, source)
            assert project.find_assessment(binding.context) == binding.document
    with AssessmentProjectFile.open(path) as project:
        for kind, source in zip(AssessmentKind, sources, strict=True):
            assert project.load(DocumentKey("p", kind.value)) == source


def test_conflicts_and_invalid_owners_leave_no_partial_source(tmp_path: Path) -> None:
    """Reject occupied IDs/contexts and missing owners without modifying old data.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(ValueError, match="model"):
            project.create_bound_assessment(BINDING, DuetDraft())
        missing = replace(CONTEXT, worker=replace(CONTEXT.worker, worker_id="missing"))
        with pytest.raises(KeyError):
            project.create_bound_assessment(replace(BINDING, context=missing), SOURCE)
        with pytest.raises(KeyError):
            project.load(BINDING.document)
        with pytest.raises(DocumentExistsError):
            project.create_bound_assessment(replace(BINDING, document=KEY), SOURCE)
        assert project.assessment_binding(KEY) is None
        project.create_bound_assessment(BINDING, SOURCE)
        duplicate = replace(BINDING, document=DocumentKey("p", "duplicate"))
        with pytest.raises(sqlite3.IntegrityError):
            project.create_bound_assessment(duplicate, SOURCE)
        with pytest.raises(KeyError):
            project.load(duplicate.document)
        assert project.load(KEY) == SOURCE
        assert project.find_assessment(CONTEXT) == BINDING.document


@pytest.mark.parametrize("table", ["draft_documents", "assessment_bindings"])
def test_sql_abort_at_either_insert_rolls_back_then_retry_succeeds(
    tmp_path: Path, table: str
) -> None:
    """A failed second write cannot leave an unbound draft behind.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        table: Owned risk table or explicit SQL table identity selected for fault
            injection.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            f"CREATE TRIGGER fail BEFORE INSERT ON {table} "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
    with AssessmentProjectFile.open(path) as project:
        with pytest.raises(sqlite3.IntegrityError):
            project.create_bound_assessment(BINDING, SOURCE)
        with pytest.raises(KeyError):
            project.load(BINDING.document)
        assert project.find_assessment(CONTEXT) is None
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("DROP TRIGGER fail")
        project.create_bound_assessment(BINDING, SOURCE)
        assert project.assessment_binding(BINDING.document) == BINDING


@pytest.mark.parametrize("choice", [CloseChoice.SAVE, CloseChoice.DISCARD])
def test_workspace_creates_clean_bound_session_after_dirty_choice(
    tmp_path: Path, choice: CloseChoice
) -> None:
    """Keep old save/discard semantics and activate only a committed new document.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        choice: Explicit Save/Discard/Cancel disposition used to verify transition
            ordering.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    try:
        workspace.switch(str(path), "old")
        old = workspace.active
        old.execute(LifftProjectEdit(AddLifftTask(KEY, LifftTask("t", 12, 10, 100), 0)))
        assert workspace.create_assessment(
            "new", SOURCE, context=CONTEXT, choice=choice
        ).completed
        assert workspace.active.document == BINDING.document
        assert not workspace.active.is_dirty
        assert workspace.active.undo_label_key is None
        with AssessmentProjectFile.open(path) as project:
            assert project.load(KEY) == (
                old.state if choice is CloseChoice.SAVE else SOURCE
            )
            assert project.assessment_binding(BINDING.document) == BINDING
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_workspace_cancel_preflight_and_failure_ordering(tmp_path: Path) -> None:
    """Preflight precedes save; later creation failure retains the saved session.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "project.sqlite"
    seed(path)
    workspace = ProjectWorkspace(
        lambda location: AssessmentProjectFile.open(Path(location)),
        JsonSettingsStore(tmp_path / "settings.json"),
    )
    try:
        workspace.switch(str(path), "old")
        old = workspace.active
        old.execute(LifftProjectEdit(AddLifftTask(KEY, LifftTask("t", 12, 10, 100), 0)))
        with patch.object(
            AssessmentProjectFile,
            "list_assessments",
            side_effect=AssertionError("unexpected I/O"),
        ):
            for choice in (None, CloseChoice.CANCEL):
                assert not workspace.create_assessment(
                    "new", SOURCE, context=CONTEXT, choice=choice
                ).completed
        with AssessmentProjectFile.open(path) as project:
            project.create_bound_assessment(BINDING, SOURCE)
        with pytest.raises(ValueError, match="context already"):
            workspace.create_assessment(
                "duplicate", SOURCE, context=CONTEXT, choice=CloseChoice.SAVE
            )
        assert old.is_dirty
        duet_context = replace(CONTEXT, kind=AssessmentKind.DUET)
        with (
            patch.object(
                AssessmentProjectFile,
                "create_bound_assessment",
                side_effect=OSError("create"),
            ),
            pytest.raises(OSError),
        ):
            workspace.create_assessment(
                "duet", DuetDraft(), context=duet_context, choice=CloseChoice.SAVE
            )
        assert workspace.active is old
        assert not old.is_dirty
        assert workspace.create_assessment(
            "duet", DuetDraft(), context=duet_context
        ).completed
    finally:
        workspace.close(choice=CloseChoice.DISCARD)


def test_transaction_helpers_refuse_idle_connections(tmp_path: Path) -> None:
    """Composed operations must never accidentally commit partial standalone work.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with closing(sqlite3.connect(tmp_path / "helpers.sqlite")) as connection:
        store = AssessmentSqliteStore.create(connection)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            create_binding_schema(connection)
        bindings = AssessmentBindingStore(connection, "p")
        with pytest.raises(RuntimeError, match="caller-owned"):
            store.insert_in_transaction(BINDING.document, SOURCE)
        with pytest.raises(RuntimeError, match="caller-owned"):
            bindings.bind_in_transaction(BINDING)


def test_version_two_rejects_atomic_binding_without_modification(
    tmp_path: Path,
) -> None:
    """Older files retain their format and reject the unavailable operation.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "old.sqlite"
    with AssessmentProjectFile.create(path, META):
        pass
    before = path.read_bytes()
    with AssessmentProjectFile.open(path) as project, pytest.raises(StoreFormatError):
        project.create_bound_assessment(BINDING, SOURCE)
    assert path.read_bytes() == before


def test_workspace_rejects_missing_atomic_capability(tmp_path: Path) -> None:
    """A legacy adapter cannot implement atomic creation as two independent saves.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "legacy.sqlite"
    with ProjectFile.create_with_document(path, META, "old", SOURCE):
        pass

    def opener(location: str) -> SimpleNamespace:
        """Open the synthetic project but expose only partial creation capabilities.

        Open the synthetic project but expose only partial creation capabilities to
        verify the workspace rejects non-atomic historical creation.

        Args:
            location: Disposable project location provided to the injected
                adapter/factory.

        Returns:
            Partial synthetic adapter exposing normal source operations but no required
            atomic historical-creation capability.
        """
        project = AssessmentProjectFile.open(Path(location))
        return SimpleNamespace(
            metadata=project.metadata,
            load=project.load,
            save=project.save,
            close=project.close,
            list_assessments=project.list_assessments,
            insert_assessment=project.insert_assessment,
        )

    workspace = ProjectWorkspace(opener, JsonSettingsStore(tmp_path / "settings.json"))
    try:
        workspace.switch(str(path), "old")
        old = workspace.active
        with pytest.raises(RuntimeError, match="adapter is not configured"):
            workspace.create_assessment("new", SOURCE, context=CONTEXT)
        assert workspace.active is old
    finally:
        workspace.close()
