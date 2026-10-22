"""New-format project ownership and recent-history integration acceptance tests.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ergotools.application.document_lifecycle import CloseChoice, DocumentLifecycle
from ergotools.application.open_document import open_document
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.lifft_store import LifftSqliteStore, StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.localization import Language, Translator


class ProjectFileTests(unittest.TestCase):
    """Keep all file creation, corruption and fault injection inside temp space."""

    def setUp(self) -> None:
        """Prepare a fresh project destination, identity and representative draft.

        Args:
            None.

        Returns:
            None.
        """
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "project #ñ?.sqlite"
        self.metadata = ProjectMetadata(
            "stable-id", "Proyecto", MeasurementSystem.METRIC
        )
        self.key = DocumentKey("stable-id", "lifft")
        self.draft = LifftDraft(
            MeasurementSystem.IMPERIAL, (LifftTask("task", 12, 1, None),)
        )

    def test_create_close_reopen_preserves_metadata_and_record_units(self) -> None:
        """Project defaults never overwrite an existing assessment's input units.

        Args:
            None.

        Returns:
            None.
        """
        with ProjectFile.create(self.path, self.metadata) as project:
            project.save(self.key, self.draft)
            self.assertEqual(project.metadata, self.metadata)
        with ProjectFile.open(self.path) as reopened:
            self.assertEqual(reopened.metadata, self.metadata)
            self.assertEqual(reopened.load(self.key), self.draft)
            self.assertEqual(reopened.load(self.key).system, MeasurementSystem.IMPERIAL)

    def test_existing_destination_is_never_overwritten(self) -> None:
        """Exclusive creation preserves unrelated and already initialized files.

        Args:
            None.

        Returns:
            None.
        """
        self.path.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            ProjectFile.create(self.path, self.metadata)
        self.assertEqual(self.path.read_bytes(), b"existing")

    def test_missing_open_does_not_create_a_file(self) -> None:
        """Opening a missing recent location cannot silently create a blank project.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(sqlite3.OperationalError):
            ProjectFile.open(self.path)
        self.assertFalse(self.path.exists())

    def test_wrong_project_is_rejected_before_read_or_write(self) -> None:
        """An owned repository accepts only its stable project identity.

        Args:
            None.

        Returns:
            None.
        """
        with ProjectFile.create(self.path, self.metadata) as project:
            other = DocumentKey("other", "lifft")
            with self.assertRaises(ValueError):
                project.save(other, self.draft)
            with self.assertRaises(ValueError):
                project.load(other)
            with self.assertRaises(KeyError):
                project.load(self.key)

    def test_close_is_idempotent_and_context_errors_do_not_leak_handle(self) -> None:
        """Closing twice is safe; closed repositories reject later operations.

        Args:
            None.

        Returns:
            None.

        Raises:
            RuntimeError: The controlled reentrancy/owned-resource failure is triggered.
        """
        project = ProjectFile.create(self.path, self.metadata)
        with self.assertRaisesRegex(RuntimeError, "test body"), project:
            raise RuntimeError("test body")
        project.close()
        with self.assertRaises(RuntimeError):
            project.load(self.key)
        with self.assertRaises(RuntimeError):
            project.__enter__()

    def test_create_failure_removes_only_the_new_incomplete_file(self) -> None:
        """Initialization errors release the connection and permit a clean retry.

        Args:
            None.

        Returns:
            None.
        """
        with (
            patch.object(LifftSqliteStore, "create", side_effect=OSError("injected")),
            self.assertRaises(OSError),
        ):
            ProjectFile.create(self.path, self.metadata)
        self.assertFalse(self.path.exists())
        with ProjectFile.create(self.path, self.metadata) as project:
            self.assertEqual(project.metadata, self.metadata)

    def test_connection_failure_also_cleans_exclusive_creation(self) -> None:
        """Handle setup failure even before a connection exists.

        Args:
            None.

        Returns:
            None.
        """
        with (
            patch(
                "ergotools.infrastructure.project_file.sqlite3.connect",
                side_effect=OSError("injected"),
            ),
            self.assertRaises(OSError),
        ):
            ProjectFile.create(self.path, self.metadata)
        self.assertFalse(self.path.exists())

    def test_unknown_versions_and_foreign_records_are_rejected(self) -> None:
        """Reject incompatible containers without migrating their metadata or rows.

        Args:
            None.

        Returns:
            None.
        """
        ProjectFile.create(self.path, self.metadata).close()
        connection = sqlite3.connect(self.path)
        self.addCleanup(connection.close)
        with connection:
            connection.execute("UPDATE project_metadata SET version=2")
        before = self.path.read_bytes()
        with self.assertRaises(StoreFormatError):
            ProjectFile.open(self.path)
        self.assertEqual(self.path.read_bytes(), before)
        with connection:
            connection.execute("UPDATE project_metadata SET version=1")
        LifftSqliteStore(connection).save(DocumentKey("foreign", "lifft"), self.draft)
        with self.assertRaises(StoreFormatError):
            ProjectFile.open(self.path)

    def test_invalid_project_metadata_is_rejected(self) -> None:
        """Require stable identity, usable title and an explicit unit enum.

        Args:
            None.

        Returns:
            None.
        """
        for identity, title in (("", "title"), ("id", " "), (None, "title")):
            with self.assertRaises(ValueError):
                ProjectMetadata(identity, title, MeasurementSystem.METRIC)
        with self.assertRaises(ValueError):
            ProjectMetadata("id", "title", "metric")

    def test_successful_open_records_recency_after_document_load(self) -> None:
        """Real project and settings adapters integrate without changing source data.

        Args:
            None.

        Returns:
            None.
        """
        with ProjectFile.create(self.path, self.metadata) as project:
            project.save(self.key, self.draft)
            lifecycle = DocumentLifecycle(project)
            settings = JsonSettingsStore(self.path.parent / "settings.json")
            outcome = open_document(lifecycle, self.key, str(self.path), settings)
            self.assertTrue(outcome.opened)
            self.assertIsNone(outcome.warning_key)
            self.assertEqual(lifecycle.active.state, self.draft)
            self.assertEqual(settings.load().recent_documents, (str(self.path),))

    def test_settings_failure_reports_warning_without_undoing_open(self) -> None:
        """Both corrupt settings and write failures leave the document open.

        Args:
            None.

        Returns:
            None.
        """
        with ProjectFile.create(self.path, self.metadata) as project:
            project.save(self.key, self.draft)
            lifecycle = DocumentLifecycle(project)
            path = self.path.parent / "settings.json"
            settings = JsonSettingsStore(path)
            path.write_text("invalid json")
            outcome = open_document(lifecycle, self.key, str(self.path), settings)
            self.assertTrue(outcome.opened)
            self.assertEqual(outcome.warning_key, "settings.recent_update_failed")
            self.assertEqual(lifecycle.active.state, self.draft)
            path.unlink()
            with patch.object(settings, "save", side_effect=OSError("injected")):
                outcome = open_document(lifecycle, self.key, str(self.path), settings)
            self.assertTrue(outcome.opened)
            for language in Language:
                self.assertTrue(Translator(language).text(outcome.warning_key))
            self.assertEqual(lifecycle.active.state, self.draft)

    def test_cancel_or_document_failure_leaves_settings_untouched(self) -> None:
        """No recent entry is recorded for a cancelled or unsuccessful open.

        Args:
            None.

        Returns:
            None.
        """
        with ProjectFile.create(self.path, self.metadata) as project:
            project.save(self.key, self.draft)
            lifecycle = DocumentLifecycle(
                project, DocumentSession(self.key, self.draft)
            )
            settings_path = self.path.parent / "settings.json"
            settings = JsonSettingsStore(settings_path)
            outcome = open_document(
                lifecycle, self.key, str(self.path), settings, choice=CloseChoice.CANCEL
            )
            self.assertFalse(outcome.opened)
            self.assertFalse(settings_path.exists())
            missing = DocumentKey(self.key.project_id, "missing")
            with self.assertRaises(KeyError):
                open_document(
                    lifecycle,
                    missing,
                    str(self.path),
                    settings,
                    choice=CloseChoice.DISCARD,
                )
            self.assertFalse(settings_path.exists())
            with self.assertRaises(ValueError):
                open_document(lifecycle, self.key, " ", settings)
            self.assertFalse(settings_path.exists())
