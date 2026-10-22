"""Catalog snapshot ownership, atomic conflicts and assessment-history isolation.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.hierarchy_access import HierarchySnapshot
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import AssessmentContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class WorkspaceHierarchyTests(unittest.TestCase):
    """Use only temporary version-four files and real SQL transactions."""

    def setUp(self) -> None:
        """Open a project with a saved catalog and a bound LiFFT source.

        Args:
            None.

        Returns:
            None.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "catalog.sqlite"
        self.settings_path = self.path.parent / "settings.json"
        self.meta = ProjectMetadata("p", "Catalog", MeasurementSystem.IMPERIAL)
        self.key = DocumentKey("p", "a")
        self.source = LifftDraft(MeasurementSystem.IMPERIAL)
        self.catalog = WorkHierarchy(
            WorkCatalog(
                "p", (WorkerEntry("w"),), (StationKey("P", "S", "L", "1"),), ("Day",)
            ),
            ("P",),
            (SectionKey("P", "S"),),
            (LineKey("P", "S", "L"),),
        )
        self.context = AssessmentContext(
            self.catalog.work.worker_context(
                "w", self.catalog.work.available_workplaces()[0]
            ),
            AssessmentKind.LIFFT,
        )
        with AssessmentProjectFile.create_catalogued(self.path, self.meta) as project:
            project.save_hierarchy(self.catalog)
            project.insert_assessment(self.key, self.source)
            project.insert_assessment(DocumentKey("p", "b"), self.source)
            project.bind_assessment(AssessmentBinding(self.key, self.context))
        self.workspace = self.make_workspace()
        self.workspace.switch(str(self.path), "a")
        self.changed = replace(self.catalog, plants=("P", "New empty plant"))

    def make_workspace(self) -> ProjectWorkspace:
        """Own a fresh coordinator and register deterministic resource cleanup.

        Args:
            None.

        Returns:
            Fresh test-owned coordinator registered for deterministic cleanup by the
            enclosing test case.
        """
        workspace = ProjectWorkspace(
            lambda location: AssessmentProjectFile.open(Path(location)),
            JsonSettingsStore(self.settings_path),
        )
        self.addCleanup(lambda: workspace.close(choice=CloseChoice.DISCARD))
        return workspace

    def test_catalog_read_and_save_preserve_dirty_assessment_and_settings(self) -> None:
        """Catalog commits do not save tasks, change active selection or clear undo.

        Args:
            None.

        Returns:
            None.
        """
        active = self.workspace.active
        active.execute(
            LifftProjectEdit(AddLifftTask(self.key, LifftTask("t", 12, 10, 100), 0))
        )
        before = self.settings_path.read_bytes()
        snapshot = self.workspace.read_hierarchy()
        refreshed = self.workspace.replace_hierarchy(snapshot, self.changed)
        self.assertEqual(refreshed.hierarchy, self.changed)
        self.assertIs(self.workspace.active, active)
        self.assertTrue(active.is_dirty)
        self.assertIsNotNone(active.undo_label_key)
        self.assertEqual(self.settings_path.read_bytes(), before)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load_hierarchy(), self.changed)
            self.assertEqual(project.load(self.key), self.source)
            self.assertEqual(project.find_assessment(self.context), self.key)
        active.undo()
        self.assertFalse(active.is_dirty)
        self.assertEqual(self.workspace.read_hierarchy().hierarchy, self.changed)

    def test_refresh_save_and_copied_snapshots_reject_stale_callbacks(self) -> None:
        """Snapshot value equality cannot revive old or forged workspace authority.

        Args:
            None.

        Returns:
            None.
        """
        old = self.workspace.read_hierarchy()
        current = self.workspace.read_hierarchy()
        for invalid in (old, HierarchySnapshot(current.hierarchy)):
            with self.assertRaises(ValueError):
                self.workspace.replace_hierarchy(invalid, self.changed)
        refreshed = self.workspace.replace_hierarchy(current, self.changed)
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(current, self.catalog)
        self.workspace.replace_hierarchy(refreshed, self.catalog)
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(old, self.changed)

    def test_foreign_workspace_and_reopened_project_do_not_share_authority(
        self,
    ) -> None:
        """Equal project IDs and locations cannot transfer snapshot authority.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_hierarchy()
        other = self.make_workspace()
        other.switch(str(self.path), "a")
        foreign = other.read_hierarchy()
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(foreign, self.changed)
        self.workspace.close()
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(snapshot, self.changed)
        self.workspace.switch(str(self.path), "a")
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(snapshot, self.changed)

    def test_same_project_document_switch_retains_catalog_snapshot(self) -> None:
        """Catalog ownership is project-scoped rather than assessment-scoped.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_hierarchy()
        self.workspace.switch(str(self.path), "b")
        self.workspace.replace_hierarchy(snapshot, self.changed)
        self.assertEqual(self.workspace.active.document.document_id, "b")

    def test_failed_refresh_invalidates_old_snapshot_and_allows_retry(self) -> None:
        """Do not keep write authority after a failed attempt to refresh saved data.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_hierarchy()
        with (
            patch.object(
                AssessmentProjectFile, "load_hierarchy", side_effect=OSError("read")
            ),
            self.assertRaises(OSError),
        ):
            self.workspace.read_hierarchy()
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(snapshot, self.changed)
        refreshed = self.workspace.read_hierarchy()
        self.workspace.replace_hierarchy(refreshed, self.changed)

    def test_expected_catalog_conflict_is_atomic_and_requires_refresh(self) -> None:
        """A stale expected value cannot overwrite a separately saved catalog.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_hierarchy()
        separate = replace(self.catalog, plants=("P", "Other change"))
        with AssessmentProjectFile.open(self.path) as project:
            project.save_hierarchy(separate)
        with self.assertRaisesRegex(ValueError, "changed since"):
            self.workspace.replace_hierarchy(snapshot, self.changed)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load_hierarchy(), separate)
        refreshed = self.workspace.read_hierarchy()
        self.workspace.replace_hierarchy(refreshed, self.changed)

    def test_sql_failure_and_invalid_removal_preserve_retry_snapshot(self) -> None:
        """Rollback leaves active source, bindings and snapshot usable for retry.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_hierarchy()
        invalid = replace(self.catalog, work=replace(self.catalog.work, workers=()))
        with self.assertRaises(KeyError):
            self.workspace.replace_hierarchy(snapshot, invalid)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER fail BEFORE UPDATE ON work_catalog "
                "BEGIN SELECT RAISE(ABORT, 'injected'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.workspace.replace_hierarchy(snapshot, self.changed)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DROP TRIGGER fail")
        self.workspace.replace_hierarchy(snapshot, self.changed)

    def test_cross_project_values_and_nested_transitions_fail(self) -> None:
        """Validate adapter data and prevent reentrant saves during catalog I/O.

        Args:
            None.

        Returns:
            None.
        """
        foreign = replace(
            self.catalog, work=replace(self.catalog.work, project_id="other")
        )
        with (
            patch.object(AssessmentProjectFile, "load_hierarchy", return_value=foreign),
            self.assertRaises(ValueError),
        ):
            self.workspace.read_hierarchy()
        snapshot = self.workspace.read_hierarchy()
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(snapshot, foreign)
        with (
            patch.object(
                AssessmentProjectFile,
                "replace_hierarchy",
                side_effect=lambda *_: self.workspace.save(),
            ),
            self.assertRaisesRegex(RuntimeError, "already in progress"),
        ):
            self.workspace.replace_hierarchy(snapshot, self.changed)
        self.workspace.replace_hierarchy(snapshot, self.changed)

    def test_failed_switch_retains_snapshot_successful_switch_invalidates_it(
        self,
    ) -> None:
        """Keep authority until project ownership actually changes.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_hierarchy()
        with self.assertRaises(KeyError):
            self.workspace.switch(str(self.path), "missing")
        refreshed = self.workspace.replace_hierarchy(snapshot, self.changed)
        path = self.path.parent / "other.sqlite"
        with AssessmentProjectFile.create_catalogued(path, self.meta) as project:
            project.insert_assessment(self.key, self.source)
        self.workspace.switch(str(path), "a")
        with self.assertRaises(ValueError):
            self.workspace.replace_hierarchy(refreshed, self.catalog)
        self.assertEqual(self.workspace.read_hierarchy().hierarchy.work.project_id, "p")

    def test_no_project_and_unsupported_repository_are_explicit(self) -> None:
        """Catalog APIs do not silently initialize unsupported project formats.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.close()
        with self.assertRaisesRegex(RuntimeError, "No project"):
            self.workspace.read_hierarchy()
        path = self.path.parent / "old.sqlite"
        with ProjectFile.create_with_document(path, self.meta, "a", self.source):
            pass
        self.workspace.switch(str(path), "a")
        with self.assertRaises(StoreFormatError):
            self.workspace.read_hierarchy()
        legacy = ProjectWorkspace(
            lambda location: ProjectFile.open(Path(location)),
            JsonSettingsStore(self.settings_path),
        )
        try:
            legacy.switch(str(path), "a")
            with self.assertRaisesRegex(RuntimeError, "adapter is not configured"):
                legacy.read_hierarchy()
        finally:
            legacy.close()
