"""Persisted catalogs and exclusive in-project creation with failure recovery.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

from ergotools.application.assessments.duet_commands import AddDuetTask
from ergotools.application.assessments.project_edits import DuetProjectEdit
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.document import AssessmentKind, assessment_kind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_json import DocumentFormatError
from ergotools.infrastructure.draft_store import DocumentExistsError, StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class AssessmentCatalogTests(unittest.TestCase):
    """Keep tests on temporary projects and real transactional SQLite operations."""

    def setUp(self) -> None:
        """Open a version-two project with a single saved DUET assessment.

        Args:
            None.

        Returns:
            None.
        """
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "catalog.sqlite"
        self.meta = ProjectMetadata("p", "Catalog", MeasurementSystem.METRIC)
        self.key = DocumentKey("p", "z-duet")
        self.duet = DuetDraft((DuetTask("a", 3, 100),))
        with AssessmentProjectFile.create_with_document(
            self.path, self.meta, self.key.document_id, self.duet
        ):
            pass
        self.workspace = ProjectWorkspace(
            lambda location: AssessmentProjectFile.open(Path(location)),
            JsonSettingsStore(self.path.parent / "settings.json"),
        )
        self.addCleanup(lambda: self.workspace.close(choice=CloseChoice.DISCARD))
        self.workspace.switch(str(self.path), self.key.document_id)

    def dirty(self) -> None:
        """Create an unsaved task edit in the active session.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.active.execute(
            DuetProjectEdit(AddDuetTask(self.key, DuetTask("b"), 1))
        )

    def test_catalog_is_ordered_persisted_and_does_not_save_edits(self) -> None:
        """Listing uses saved counts, preserves history and yields immutable entries.

        Args:
            None.

        Returns:
            None.
        """
        with AssessmentProjectFile.open(self.path) as project:
            project.insert_assessment(
                DocumentKey("p", "a-lifft"), LifftDraft(MeasurementSystem.IMPERIAL)
            )
        self.dirty()
        current = self.workspace.active
        entries = self.workspace.list_assessments()
        self.assertEqual(
            [(e.document.document_id, e.kind, e.task_count) for e in entries],
            [("a-lifft", AssessmentKind.LIFFT, 0), ("z-duet", AssessmentKind.DUET, 1)],
        )
        self.assertIs(self.workspace.active, current)
        self.assertTrue(current.is_dirty)
        self.assertEqual(len(current.state.tasks), 2)
        with self.assertRaises(FrozenInstanceError):
            entries[0].task_count = 99

    def test_cancel_and_missing_dirty_choice_do_no_catalog_or_insert_io(self) -> None:
        """Resolve the dirty decision before looking up or creating an assessment.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        with patch.object(
            AssessmentProjectFile,
            "list_assessments",
            side_effect=AssertionError("unexpected I/O"),
        ):
            self.assertFalse(
                self.workspace.create_assessment("new", DuetDraft()).completed
            )
            self.assertFalse(
                self.workspace.create_assessment(
                    "new", DuetDraft(), choice=CloseChoice.CANCEL
                ).completed
            )
        self.assertTrue(self.workspace.active.is_dirty)

    def test_save_then_create_activates_clean_history_and_survives_reopen(self) -> None:
        """The old edit is committed before the new source is activated.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        old = self.workspace.active
        outcome = self.workspace.create_assessment(
            "new-lifft", LifftDraft(MeasurementSystem.IMPERIAL), choice=CloseChoice.SAVE
        )
        self.assertTrue(outcome.completed)
        self.assertFalse(old.is_dirty)
        self.assertFalse(self.workspace.active.is_dirty)
        self.assertIsNone(self.workspace.active.undo_label_key)
        self.assertEqual(self.workspace.active.document, DocumentKey("p", "new-lifft"))
        self.workspace.close()
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(len(project.load(self.key).tasks), 2)
            self.assertEqual(
                project.load(DocumentKey("p", "new-lifft")),
                LifftDraft(MeasurementSystem.IMPERIAL),
            )

    def test_discard_then_create_leaves_prior_persisted_source_untouched(self) -> None:
        """Discard abandons only unsaved edits when insertion succeeds.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        self.assertTrue(
            self.workspace.create_assessment(
                "new", DuetDraft(), choice=CloseChoice.DISCARD
            ).completed
        )
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(self.key), self.duet)

    def test_duplicate_id_rejected_before_saving_or_replacing_active_state(
        self,
    ) -> None:
        """Duplicate preflight cannot unexpectedly clean the current dirty session.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        with self.assertRaises(ValueError):
            self.workspace.create_assessment(
                self.key.document_id, DuetDraft(), choice=CloseChoice.SAVE
            )
        self.assertIs(self.workspace.active, current)
        self.assertTrue(current.is_dirty)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(self.key), self.duet)
            with self.assertRaises(DocumentExistsError):
                project.insert_assessment(
                    self.key, LifftDraft(MeasurementSystem.METRIC)
                )
            self.assertEqual(project.load(self.key), self.duet)

    def test_insert_failure_keeps_old_session_after_requested_save_and_allows_retry(
        self,
    ) -> None:
        """Real insertion failure rolls back the new row without losing the session.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER reject_new BEFORE INSERT ON draft_documents "
                "WHEN NEW.document_id='new' BEGIN SELECT RAISE(ABORT, 'test'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.workspace.create_assessment(
                "new", DuetDraft(), choice=CloseChoice.SAVE
            )
        self.assertIs(self.workspace.active, current)
        self.assertFalse(current.is_dirty)
        self.assertEqual(len(self.workspace.list_assessments()), 1)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DROP TRIGGER reject_new")
        self.assertTrue(self.workspace.create_assessment("new", DuetDraft()).completed)

    def test_old_save_failure_prevents_new_insertion(self) -> None:
        """An unsuccessful requested save cannot create a second assessment.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        with (
            patch.object(AssessmentProjectFile, "save", side_effect=OSError("test")),
            self.assertRaises(OSError),
        ):
            self.workspace.create_assessment(
                "new", DuetDraft(), choice=CloseChoice.SAVE
            )
        self.assertIs(self.workspace.active, current)
        self.assertTrue(current.is_dirty)
        self.assertEqual(len(self.workspace.list_assessments()), 1)

    def test_version_one_lists_and_inserts_only_lifft_without_upgrade(self) -> None:
        """Compatibility catalog access cannot silently adopt a mixed format.

        Args:
            None.

        Returns:
            None.
        """
        path = self.path.parent / "v1.sqlite"
        source = LifftDraft(MeasurementSystem.METRIC)
        with ProjectFile.create_with_document(path, self.meta, "first", source):
            pass
        with AssessmentProjectFile.open(path) as project:
            self.assertEqual(project.list_assessments()[0].kind, AssessmentKind.LIFFT)
            project.insert_assessment(DocumentKey("p", "second"), source)
            with self.assertRaises(StoreFormatError):
                project.insert_assessment(DocumentKey("p", "duet"), DuetDraft())
            self.assertEqual(project.format_version, 1)
        with ProjectFile.open(path) as project:
            self.assertEqual(project.load(DocumentKey("p", "second")), source)

    def test_corruption_is_reported_without_partial_catalog_or_state_change(
        self,
    ) -> None:
        """A malformed saved entry is not hidden or represented as a valid model.

        Args:
            None.

        Returns:
            None.
        """
        current = self.workspace.active
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("UPDATE draft_documents SET payload='{}'")
        with self.assertRaises(DocumentFormatError):
            self.workspace.list_assessments()
        self.assertIs(self.workspace.active, current)
        self.assertEqual(current.state, self.duet)

    def test_empty_closed_and_unsupported_project_boundaries(self) -> None:
        """No implicit opening/creation or unsupported adapter fallback occurs.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.close()
        self.assertEqual(self.workspace.list_assessments(), ())
        with self.assertRaises(RuntimeError):
            self.workspace.create_assessment("new", DuetDraft())
        project = AssessmentProjectFile.open(self.path)
        project.close()
        with self.assertRaises(RuntimeError):
            project.list_assessments()
        with self.assertRaises(ValueError):
            assessment_kind(object())
        legacy = ProjectWorkspace(
            lambda _: ProjectFile.open(self.path.parent / "v1.sqlite"),
            JsonSettingsStore(self.path.parent / "legacy.json"),
        )
        path = self.path.parent / "v1.sqlite"
        with ProjectFile.create_with_document(
            path, self.meta, "first", LifftDraft(MeasurementSystem.METRIC)
        ):
            pass
        try:
            legacy.switch(str(path), "first")
            with self.assertRaises(RuntimeError):
                legacy.list_assessments()
            with self.assertRaises(RuntimeError):
                legacy.create_assessment("new", LifftDraft(MeasurementSystem.METRIC))
        finally:
            legacy.close()
