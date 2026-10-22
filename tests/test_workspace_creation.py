"""Workspace Save/New workflows, creation rollback and cleanup diagnostics.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import errno
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class WorkspaceCreationTests(unittest.TestCase):
    """Exercise complete new-project initialization using real temporary files."""

    def setUp(self) -> None:
        """Provide fresh destinations and workspace adapters with explicit ownership.

        Args:
            None.

        Returns:
            None.
        """
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.settings = JsonSettingsStore(self.root / "settings.json")
        self.metadata = ProjectMetadata("first", "First", MeasurementSystem.METRIC)
        self.initial = LifftDraft(
            MeasurementSystem.METRIC, (LifftTask("task", 0, None, 1),)
        )
        self.workspace = ProjectWorkspace(
            lambda location: ProjectFile.open(Path(location)),
            self.settings,
            creator=self.create_file,
        )
        self.addCleanup(lambda: self.workspace.close(choice=CloseChoice.DISCARD))

    def create_file(
        self,
        location: str,
        metadata: ProjectMetadata,
        document_id: str,
        initial: LifftDraft,
    ) -> ProjectFile:
        """Adapt a normalized location to the owned project initializer.

        Args:
            location: Disposable project location provided to the injected
                adapter/factory.
            metadata: Explicit synthetic project metadata; defaults never reinterpret
                source input units.
            document_id: Stable assessment identity supplied to the test project
                initializer.
            initial: Initial LiFFT draft supplied to the synthetic project creator,
                retaining its source units.

        Returns:
            New owned ProjectFile initialized at the normalized disposable path with the
            exact supplied identity/source.
        """
        return ProjectFile.create_with_document(
            Path(location), metadata, document_id, initial
        )

    def create_first(self) -> None:
        """Activate the first project and its initial persisted assessment.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.create(
            str(self.root / "first"), self.metadata, "a", self.initial
        )

    def edit(self) -> None:
        """Add one unsaved source task to the current document.

        Args:
            None.

        Returns:
            None.
        """
        active = self.workspace.active
        active.execute(AddLifftTask(active.document, LifftTask("edited"), 1))

    def test_create_activates_persisted_document_and_records_history(self) -> None:
        """A successful New operation starts clean and can be independently reopened.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        self.assertFalse(self.workspace.active.is_dirty)
        self.assertEqual(self.workspace.active.state, self.initial)
        self.assertIsNone(self.workspace.active.undo_label_key)
        self.assertEqual(
            self.settings.load().recent_documents, (str(self.root / "first"),)
        )
        with ProjectFile.open(self.root / "first") as project:
            self.assertEqual(project.load(DocumentKey("first", "a")), self.initial)

    def test_explicit_save_keeps_session_and_history_and_persists_edits(self) -> None:
        """Save does not switch documents, add history entries or rewrite recency.

        Args:
            None.

        Returns:
            None.
        """
        self.assertFalse(self.workspace.save())
        self.create_first()
        self.edit()
        active = self.workspace.active
        before_settings = (self.root / "settings.json").read_bytes()
        self.assertTrue(self.workspace.save())
        self.assertIs(self.workspace.active, active)
        self.assertFalse(active.is_dirty)
        with ProjectFile.open(self.root / "first") as project:
            self.assertEqual(project.load(active.document), active.state)
        active.undo()
        self.assertTrue(active.is_dirty)
        active.redo()
        self.assertFalse(active.is_dirty)
        self.assertEqual((self.root / "settings.json").read_bytes(), before_settings)

    def test_explicit_save_failure_preserves_dirty_state_and_allows_retry(self) -> None:
        """Storage failure releases the busy guard without falsely marking saved.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        self.edit()
        active = self.workspace.active
        with (
            patch.object(ProjectFile, "save", side_effect=OSError("write failed")),
            self.assertRaises(OSError),
        ):
            self.workspace.save()
        self.assertIs(self.workspace.active, active)
        self.assertTrue(active.is_dirty)
        self.assertTrue(self.workspace.save())
        self.assertFalse(active.is_dirty)

    def test_cancel_or_absent_dirty_consent_creates_no_file(self) -> None:
        """Dirty New follows the same explicit decision policy as project switching.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        self.edit()
        target = self.root / "new"
        for choice in (None, CloseChoice.CANCEL):
            outcome = self.workspace.create(
                str(target),
                replace(self.metadata, project_id="new"),
                "a",
                self.initial,
                choice=choice,
            )
            self.assertFalse(outcome.completed)
        self.assertFalse(target.exists())
        self.assertTrue(self.workspace.active.is_dirty)

    def test_old_save_failure_prevents_creation(self) -> None:
        """Do not create a destination when the requested current save fails.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        self.edit()
        target = self.root / "new"
        with (
            patch.object(ProjectFile, "save", side_effect=OSError("write failed")),
            self.assertRaises(OSError),
        ):
            self.workspace.create(
                str(target),
                replace(self.metadata, project_id="new"),
                "a",
                self.initial,
                choice=CloseChoice.SAVE,
            )
        self.assertFalse(target.exists())
        self.assertTrue(self.workspace.active.is_dirty)

    def test_creation_failure_retains_current_after_requested_save(self) -> None:
        """A creation error retains the current session after its successful save.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        self.edit()
        active = self.workspace.active
        target = self.root / "new"
        with (
            patch.object(
                ProjectFile,
                "create_with_document",
                side_effect=OSError("create failed"),
            ),
            self.assertRaises(OSError),
        ):
            self.workspace.create(
                str(target),
                replace(self.metadata, project_id="new"),
                "a",
                self.initial,
                choice=CloseChoice.SAVE,
            )
        self.assertIs(self.workspace.active, active)
        self.assertFalse(active.is_dirty)
        self.assertFalse(target.exists())

    def test_initial_document_failure_removes_incomplete_new_project(self) -> None:
        """Initialization rollback removes only the newly created incomplete file.

        Args:
            None.

        Returns:
            None.
        """
        target = self.root / "new"
        with (
            patch.object(
                ProjectFile, "save", side_effect=OSError("initial write failed")
            ),
            self.assertRaises(OSError),
        ):
            self.workspace.create(str(target), self.metadata, "a", self.initial)
        self.assertFalse(target.exists())
        self.assertIsNone(self.workspace.active)
        self.assertFalse((self.root / "settings.json").exists())
        self.assertTrue(
            self.workspace.create(
                str(target), self.metadata, "a", self.initial
            ).completed
        )

    def test_existing_and_active_locations_are_not_overwritten(self) -> None:
        """New is not Save As and cannot replace an existing destination.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        with self.assertRaises(ValueError):
            self.workspace.create(
                str(self.root / "first"), self.metadata, "a", self.initial
            )
        target = self.root / "occupied"
        target.write_bytes(b"preserve")
        with self.assertRaises(FileExistsError):
            self.workspace.create(str(target), self.metadata, "a", self.initial)
        self.assertEqual(target.read_bytes(), b"preserve")

    def test_initial_input_validation_happens_before_file_creation(self) -> None:
        """Malformed initial data cannot leave an empty project file behind.

        Args:
            None.

        Returns:
            None.
        """
        target = self.root / "invalid"
        bad = LifftDraft(MeasurementSystem.METRIC, (LifftTask("a", True),))
        with self.assertRaises(ValueError):
            ProjectFile.create_with_document(target, self.metadata, "a", bad)
        self.assertFalse(target.exists())
        with self.assertRaises(ValueError):
            self.workspace.create(" ", self.metadata, "a", self.initial)
        unconfigured = ProjectWorkspace(
            lambda path: ProjectFile.open(Path(path)), self.settings
        )
        with self.assertRaises(RuntimeError):
            unconfigured.create(str(target), self.metadata, "a", self.initial)

    def test_creator_postcondition_failure_does_not_adopt_returned_handle(self) -> None:
        """Require exact metadata and initial source data from the creation adapter.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        active = self.workspace.active
        for wrong_metadata in (True, False):
            returned = Mock()
            returned.metadata = (
                replace(self.metadata, title="wrong")
                if wrong_metadata
                else self.metadata
            )
            returned.load.return_value = LifftDraft(MeasurementSystem.IMPERIAL)
            workspace = ProjectWorkspace(
                lambda path: ProjectFile.open(Path(path)),
                self.settings,
                creator=Mock(return_value=returned),
            )
            with self.assertRaises(ValueError):
                workspace.create("target", self.metadata, "a", self.initial)
            returned.close.assert_called_once()
            self.assertIsNone(workspace.active)
        self.assertIs(self.workspace.active, active)

    def test_edit_during_creation_prevents_stale_activation(self) -> None:
        """A candidate cannot discard source edits made after dirty consent.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        current = self.workspace.active

        def creator(
            location: str,
            metadata: ProjectMetadata,
            document_id: str,
            initial: LifftDraft,
        ) -> ProjectFile:
            """Edit the current draft during candidate creation before delegating.

            Edit the current draft during candidate creation before delegating to the
            actual initializer, verifying stale activation cannot discard it.

            Args:
                location: Disposable project location provided to the injected
                    adapter/factory.
                metadata: Explicit synthetic project metadata; defaults never
                    reinterpret source input units.
                document_id: Stable assessment identity supplied to the test project
                    initializer.
                initial: Initial LiFFT draft supplied to the synthetic project creator,
                    retaining its source units.

            Returns:
                Created candidate handle after deliberately editing the old active
                draft; stale activation must not adopt it.
            """
            self.edit()
            return self.create_file(location, metadata, document_id, initial)

        self.workspace._creator = creator
        target = self.root / "new"
        with self.assertRaises(RuntimeError):
            self.workspace.create(
                str(target),
                replace(self.metadata, project_id="new"),
                "a",
                self.initial,
                choice=CloseChoice.DISCARD,
            )
        self.assertIs(self.workspace.active, current)
        self.assertTrue(current.is_dirty)
        with ProjectFile.open(target) as candidate:
            self.assertEqual(candidate.load(DocumentKey("new", "a")), self.initial)

    def test_cleanup_diagnostics_retain_type_and_errno_without_raw_message(
        self,
    ) -> None:
        """Expose technical context for retries without storing sensitive error text.

        Args:
            None.

        Returns:
            None.
        """
        self.create_first()
        with patch.object(
            ProjectFile, "close", side_effect=OSError(errno.EIO, "private path")
        ):
            result = self.workspace.create(
                str(self.root / "new"),
                replace(self.metadata, project_id="new"),
                "a",
                self.initial,
            )
        self.assertIn("project.cleanup_failed", result.warning_keys)
        diagnostic = self.workspace.release_diagnostics[0]
        self.assertEqual(diagnostic.exception_type, "builtins.OSError")
        self.assertEqual(diagnostic.errno, errno.EIO)
        self.assertNotIn("private path", repr(diagnostic))
        self.assertEqual(self.workspace.retry_releases(), 0)
        self.assertEqual(self.workspace.release_diagnostics, ())

    def test_settings_warning_keeps_created_project_active(self) -> None:
        """Settings failure cannot misreport a fully created project as failed.

        Args:
            None.

        Returns:
            None.
        """
        with patch.object(
            self.settings, "save", side_effect=OSError("settings failure")
        ):
            result = self.workspace.create(
                str(self.root / "new"), self.metadata, "a", self.initial
            )
        self.assertTrue(result.completed)
        self.assertEqual(result.warning_keys, ("settings.recent_update_failed",))
        self.assertEqual(self.workspace.active.state, self.initial)
