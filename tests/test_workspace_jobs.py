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
from datetime import date
from pathlib import Path
from unittest.mock import patch

from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.job_access import JobSnapshot
from ergotools.application.job_assignment import assign_worker
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import AssessmentContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class WorkspaceJobTests(unittest.TestCase):
    """Use only temporary version-five files and real SQL transactions."""

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
        self.hierarchy = WorkHierarchy(
            WorkCatalog(
                "p", (WorkerEntry("w"),), (StationKey("P", "S", "L", "1"),), ("Day",)
            ),
            ("P",),
            (SectionKey("P", "S"),),
            (LineKey("P", "S", "L"),),
        )
        self.context = AssessmentContext(
            self.hierarchy.work.worker_context(
                "w", self.hierarchy.work.available_workplaces()[0]
            ),
            AssessmentKind.LIFFT,
        )
        owner = self.context.worker
        self.catalog = JobCatalog(
            "p",
            (Job("j", "Job"),),
            (JobPlacement(1, "j", owner.workplace),),
            (WorkerJobAssignment(1, owner, 1),),
        )
        with AssessmentProjectFile.create_with_jobs(self.path, self.meta) as project:
            project.save_hierarchy(self.hierarchy)
            project.save_jobs(self.catalog)
            project.insert_assessment(self.key, self.source)
            project.insert_assessment(DocumentKey("p", "b"), self.source)
            project.bind_assessment(AssessmentBinding(self.key, self.context))
        self.workspace = self.make_workspace()
        self.workspace.switch(str(self.path), "a")
        self.changed = replace(self.catalog, jobs=(Job("j", "Renamed"),))

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
        """Job commits do not save tasks, change active selection or clear undo.

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
        snapshot = self.workspace.read_jobs()
        refreshed = self.workspace.replace_jobs(snapshot, self.changed)
        self.assertEqual(refreshed.jobs, self.changed)
        self.assertIs(self.workspace.active, active)
        self.assertTrue(active.is_dirty)
        self.assertIsNotNone(active.undo_label_key)
        self.assertEqual(self.settings_path.read_bytes(), before)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load_jobs(), self.changed)
            self.assertEqual(project.load(self.key), self.source)
            self.assertEqual(project.find_assessment(self.context), self.key)
        active.undo()
        self.assertFalse(active.is_dirty)
        self.assertEqual(self.workspace.read_jobs().jobs, self.changed)

    def test_refresh_save_and_copied_snapshots_reject_stale_callbacks(self) -> None:
        """Snapshot value equality cannot revive old or forged workspace authority.

        Args:
            None.

        Returns:
            None.
        """
        old = self.workspace.read_jobs()
        current = self.workspace.read_jobs()
        for invalid in (old, JobSnapshot(current.jobs)):
            with self.assertRaises(ValueError):
                self.workspace.replace_jobs(invalid, self.changed)
        refreshed = self.workspace.replace_jobs(current, self.changed)
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(current, self.catalog)
        self.workspace.replace_jobs(refreshed, self.catalog)
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(old, self.changed)

    def test_foreign_workspace_and_reopened_project_do_not_share_authority(
        self,
    ) -> None:
        """Equal project IDs and locations cannot transfer snapshot authority.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_jobs()
        other = self.make_workspace()
        other.switch(str(self.path), "a")
        foreign = other.read_jobs()
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(foreign, self.changed)
        self.workspace.close()
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(snapshot, self.changed)
        self.workspace.switch(str(self.path), "a")
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(snapshot, self.changed)

    def test_same_project_document_switch_retains_catalog_snapshot(self) -> None:
        """Job ownership is project-scoped rather than assessment-scoped.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_jobs()
        self.workspace.switch(str(self.path), "b")
        self.workspace.replace_jobs(snapshot, self.changed)
        self.assertEqual(self.workspace.active.document.document_id, "b")

    def test_failed_refresh_invalidates_old_snapshot_and_allows_retry(self) -> None:
        """Do not keep write authority after a failed attempt to refresh saved data.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_jobs()
        with (
            patch.object(
                AssessmentProjectFile, "load_jobs", side_effect=OSError("read")
            ),
            self.assertRaises(OSError),
        ):
            self.workspace.read_jobs()
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(snapshot, self.changed)
        refreshed = self.workspace.read_jobs()
        self.workspace.replace_jobs(refreshed, self.changed)

    def test_expected_catalog_conflict_is_atomic_and_requires_refresh(self) -> None:
        """A stale expected value cannot overwrite a separately saved catalog.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_jobs()
        separate = replace(self.catalog, jobs=(Job("j", "Concurrent"),))
        with AssessmentProjectFile.open(self.path) as project:
            project.save_jobs(separate)
        with self.assertRaisesRegex(ValueError, "changed since"):
            self.workspace.replace_jobs(snapshot, self.changed)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load_jobs(), separate)
        refreshed = self.workspace.read_jobs()
        self.workspace.replace_jobs(refreshed, self.changed)

    def test_sql_failure_and_invalid_removal_preserve_retry_snapshot(self) -> None:
        """Rollback leaves active source, bindings and snapshot usable for retry.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_jobs()
        invalid = replace(
            self.catalog,
            assignments=(
                replace(
                    self.catalog.assignments[0],
                    worker=replace(self.context.worker, worker_id="missing"),
                ),
            ),
        )
        with self.assertRaises(KeyError):
            self.workspace.replace_jobs(snapshot, invalid)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER fail BEFORE INSERT ON worker_assignments "
                "BEGIN SELECT RAISE(ABORT, 'injected'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.workspace.replace_jobs(snapshot, self.changed)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DROP TRIGGER fail")
        self.workspace.replace_jobs(snapshot, self.changed)

    def test_cross_project_values_and_nested_transitions_fail(self) -> None:
        """Validate adapter data and prevent reentrant saves during catalog I/O.

        Args:
            None.

        Returns:
            None.
        """
        foreign = JobCatalog("other")
        with (
            patch.object(AssessmentProjectFile, "load_jobs", return_value=foreign),
            self.assertRaises(ValueError),
        ):
            self.workspace.read_jobs()
        snapshot = self.workspace.read_jobs()
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(snapshot, foreign)
        with (
            patch.object(
                AssessmentProjectFile,
                "replace_jobs",
                side_effect=lambda *_: self.workspace.save(),
            ),
            self.assertRaisesRegex(RuntimeError, "already in progress"),
        ):
            self.workspace.replace_jobs(snapshot, self.changed)
        self.workspace.replace_jobs(snapshot, self.changed)

    def test_failed_switch_retains_snapshot_successful_switch_invalidates_it(
        self,
    ) -> None:
        """Keep authority until project ownership actually changes.

        Args:
            None.

        Returns:
            None.
        """
        snapshot = self.workspace.read_jobs()
        with self.assertRaises(KeyError):
            self.workspace.switch(str(self.path), "missing")
        refreshed = self.workspace.replace_jobs(snapshot, self.changed)
        path = self.path.parent / "other.sqlite"
        with AssessmentProjectFile.create_with_jobs(path, self.meta) as project:
            project.insert_assessment(self.key, self.source)
        self.workspace.switch(str(path), "a")
        with self.assertRaises(ValueError):
            self.workspace.replace_jobs(refreshed, self.catalog)
        self.assertEqual(self.workspace.read_jobs().jobs.project_id, "p")

    def test_no_project_and_unsupported_repository_are_explicit(self) -> None:
        """Job APIs do not silently initialize unsupported project formats.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.close()
        with self.assertRaisesRegex(RuntimeError, "No project"):
            self.workspace.read_jobs()
        path = self.path.parent / "old.sqlite"
        with ProjectFile.create_with_document(path, self.meta, "a", self.source):
            pass
        self.workspace.switch(str(path), "a")
        with self.assertRaises(StoreFormatError):
            self.workspace.read_jobs()
        legacy = ProjectWorkspace(
            lambda location: ProjectFile.open(Path(location)),
            JsonSettingsStore(self.settings_path),
        )
        try:
            legacy.switch(str(path), "a")
            with self.assertRaisesRegex(RuntimeError, "adapter is not configured"):
                legacy.read_jobs()
        finally:
            legacy.close()

    def test_assignment_transition_commits_history_without_moving_assessment(
        self,
    ) -> None:
        """Compose the pure transition with guarded persistence and saved bindings.

        Args:
            None.

        Returns:
            None.
        """
        catalog = replace(
            self.catalog,
            jobs=(*self.catalog.jobs, Job("other", "Other")),
            placements=(
                *self.catalog.placements,
                JobPlacement(2, "other", self.context.worker.workplace),
            ),
        )
        snapshot = self.workspace.replace_jobs(self.workspace.read_jobs(), catalog)
        change = assign_worker(
            snapshot.jobs,
            self.context.worker,
            2,
            effective_date=date(2026, 10, 1),
            new_assignment_id=2,
        )
        self.workspace.replace_jobs(snapshot, change.jobs)
        with AssessmentProjectFile.open(self.path) as project:
            saved = project.load_jobs()
            assert saved.assignments[0].placement_id == 1
            assert not saved.assignments[0].active
            assert saved.assignments[0].ended_at == "2026-10-01"
            assert saved.assignments[1].placement_id == 2
            assert saved.assignments[1].active
            assert project.find_assessment(self.context) == self.key
            assert project.load(self.key) == self.source
