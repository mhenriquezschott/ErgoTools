"""Mixed-model project versions, transaction isolation and workspace history.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from ergotools.application.assessments.duet_commands import AddDuetTask
from ergotools.application.assessments.lifft_commands import AddLifftTask
from ergotools.application.assessments.project_edits import (
    DuetProjectEdit,
    LifftProjectEdit,
)
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.infrastructure.draft_json import DocumentFormatError
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class AssessmentProjectTests(unittest.TestCase):
    """Use only temporary projects for compatibility, corruption and save failures."""

    def setUp(self) -> None:
        """Prepare distinct model documents with the same project owner.

        Args:
            None.

        Returns:
            None.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "project #ñ?.sqlite"
        self.meta = ProjectMetadata("p", "Mixed", MeasurementSystem.METRIC)
        self.lk = DocumentKey("p", "lifft")
        self.dk = DocumentKey("p", "duet")
        self.lifft = LifftDraft(
            MeasurementSystem.IMPERIAL, (LifftTask("a", 12, 10, 100),)
        )
        self.duet = DuetDraft((DuetTask("a", 3, 100),))

    def seed(self) -> None:
        """Persist both source types under distinct document identities.

        Args:
            None.

        Returns:
            None.
        """
        with AssessmentProjectFile.create(self.path, self.meta) as project:
            project.save(self.lk, self.lifft)
            project.save(self.dk, self.duet)

    def workspace(self) -> ProjectWorkspace:
        """Configure actual adapters with local temporary preferences.

        Args:
            None.

        Returns:
            Test-owned coordinator over actual temporary adapters; caller/test cleanup
            releases it.
        """
        workspace = ProjectWorkspace(
            lambda location: AssessmentProjectFile.open(Path(location)),
            JsonSettingsStore(self.path.parent / "settings.json"),
            creator=lambda location, metadata, document_id, source: (
                AssessmentProjectFile.create_with_document(
                    Path(location), metadata, document_id, source
                )
            ),
        )
        self.addCleanup(lambda: workspace.close(choice=CloseChoice.DISCARD))
        return workspace

    def test_both_models_roundtrip_in_one_version_two_project(self) -> None:
        """Preserve each tool's original fields and LiFFT units across reopening.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.format_version, 2)
            self.assertEqual(project.metadata, self.meta)
            self.assertEqual(project.load(self.lk), self.lifft)
            self.assertEqual(project.load(self.dk), self.duet)
        with self.assertRaises(StoreFormatError):
            ProjectFile.open(self.path)

    def test_existing_document_cannot_change_model_and_transaction_recovers(
        self,
    ) -> None:
        """Identity protection runs under the lock and leaves both sources intact.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        with AssessmentProjectFile.open(self.path) as project:
            for key, source in ((self.lk, self.duet), (self.dk, self.lifft)):
                with self.assertRaises(StoreFormatError):
                    project.save(key, source)
            self.assertEqual(project.load(self.lk), self.lifft)
            self.assertEqual(project.load(self.dk), self.duet)
            project.save(self.dk, DuetDraft())
            self.assertEqual(project.load(self.dk), DuetDraft())

    def test_version_one_remains_unchanged_and_rejects_duet(self) -> None:
        """Read/write LiFFT compatibility never silently migrates existing files.

        Args:
            None.

        Returns:
            None.
        """
        with ProjectFile.create_with_document(
            self.path, self.meta, "lifft", self.lifft
        ):
            pass
        before = self.path.read_bytes()
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.format_version, 1)
            self.assertEqual(project.load(self.lk), self.lifft)
            with self.assertRaises(StoreFormatError):
                project.save(self.dk, self.duet)
        self.assertEqual(self.path.read_bytes(), before)
        with AssessmentProjectFile.open(self.path) as project:
            project.save(self.lk, LifftDraft(MeasurementSystem.METRIC))
        with ProjectFile.open(self.path) as project:
            self.assertEqual(
                project.load(self.lk), LifftDraft(MeasurementSystem.METRIC)
            )

    def test_workspace_switch_save_cancel_undo_and_reload_between_models(self) -> None:
        """Route mixed edits with explicit dirty decisions and independent histories.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        workspace = self.workspace()
        location = str(self.path)
        self.assertTrue(workspace.switch(location, "lifft").completed)
        initial = workspace.active
        initial.execute(
            LifftProjectEdit(AddLifftTask(self.lk, LifftTask("b", 1, 1, 1), 1))
        )
        self.assertFalse(workspace.switch(location, "duet").completed)
        self.assertFalse(
            workspace.switch(location, "duet", choice=CloseChoice.CANCEL).completed
        )
        self.assertIs(workspace.active, initial)
        self.assertTrue(workspace.switch(location, "lifft").completed)
        self.assertIs(workspace.active, initial)
        self.assertTrue(
            workspace.switch(location, "duet", choice=CloseChoice.SAVE).completed
        )
        duet_session = workspace.active
        self.assertEqual(duet_session.state, self.duet)
        self.assertIsNone(duet_session.undo_label_key)
        duet_session.execute(
            DuetProjectEdit(AddDuetTask(self.dk, DuetTask("b", 4, 0.5), 1))
        )
        duet_session.undo()
        self.assertFalse(duet_session.is_dirty)
        duet_session.redo()
        self.assertTrue(workspace.save())
        self.assertTrue(workspace.switch(location, "lifft").completed)
        self.assertEqual(len(workspace.active.state.tasks), 2)
        self.assertIsNone(workspace.active.undo_label_key)
        workspace.close()
        workspace.switch(location, "duet")
        self.assertEqual(len(workspace.active.state.tasks), 2)

    def test_wrong_model_commands_fail_without_mutating_history(self) -> None:
        """Cross-model edits fail before evaluating model-specific task operations.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        workspace = self.workspace()
        workspace.switch(str(self.path), "duet")
        session = workspace.active
        with self.assertRaises(ValueError):
            session.execute(LifftProjectEdit(AddLifftTask(self.dk, LifftTask("b"), 1)))
        self.assertEqual(session.state, self.duet)
        self.assertEqual(session.revision, 0)
        workspace.switch(str(self.path), "lifft")
        with self.assertRaises(ValueError):
            workspace.active.execute(
                DuetProjectEdit(AddDuetTask(self.lk, DuetTask("b"), 1))
            )

    def test_failed_target_load_keeps_dirty_source_and_handle(self) -> None:
        """A missing target never saves or discards the currently edited assessment.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        workspace = self.workspace()
        workspace.switch(str(self.path), "duet")
        current = workspace.active
        current.execute(DuetProjectEdit(AddDuetTask(self.dk, DuetTask("b"), 1)))
        with self.assertRaises(KeyError):
            workspace.switch(str(self.path), "missing", choice=CloseChoice.SAVE)
        self.assertIs(workspace.active, current)
        self.assertTrue(current.is_dirty)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(self.dk), self.duet)

    def test_corrupt_stored_source_cannot_be_silently_overwritten(self) -> None:
        """Refuse overwrite when stored model identity cannot be established.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "UPDATE draft_documents SET payload='{}' WHERE document_id='duet'"
            )
        with AssessmentProjectFile.open(self.path) as project:
            with self.assertRaises(DocumentFormatError):
                project.save(self.dk, self.duet)
            self.assertEqual(project.load(self.lk), self.lifft)

    def test_envelope_rejects_unknown_mismatched_or_ambiguous_tags(self) -> None:
        """Nested codecs remain strict and an outer tag cannot relabel another tool.

        Args:
            None.

        Returns:
            None.
        """
        for source in (self.lifft, self.duet):
            self.assertEqual(decode_assessment(encode_assessment(source)), source)
        data = json.loads(encode_assessment(self.duet))
        cases = [
            None,
            {},
            {**data, "version": True},
            {**data, "version": 2},
            {**data, "format": "other"},
            {**data, "kind": "unknown"},
            {**data, "kind": "lifft"},
            {**data, "source": {}},
            {**data, "extra": 0},
        ]
        for case in cases:
            with self.assertRaises(DocumentFormatError):
                decode_assessment(json.dumps(case))
        with self.assertRaises(DocumentFormatError):
            decode_assessment('{"kind":"duet","kind":"lifft"}')
        with self.assertRaises(DocumentFormatError):
            encode_assessment(object())

    def test_project_lifecycle_protects_missing_existing_and_foreign_paths(
        self,
    ) -> None:
        """Exclusive create and owner guards apply equally to the mixed format.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(sqlite3.OperationalError):
            AssessmentProjectFile.open(self.path)
        self.assertFalse(self.path.exists())
        self.seed()
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            AssessmentProjectFile.create(self.path, self.meta)
        self.assertEqual(self.path.read_bytes(), before)
        project = AssessmentProjectFile.open(self.path)
        with self.assertRaises(ValueError):
            project.load(DocumentKey("foreign", "lifft"))
        project.close()
        project.close()
        with self.assertRaises(RuntimeError):
            project.load(self.lk)
        with self.assertRaises(RuntimeError):
            project.__enter__()

    def test_unknown_version_and_foreign_rows_are_rejected(self) -> None:
        """Project-level identity and version validation precedes activation.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("UPDATE project_metadata SET version=99")
        with self.assertRaises(StoreFormatError):
            AssessmentProjectFile.open(self.path)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("UPDATE project_metadata SET version=2")
            connection.execute("UPDATE draft_documents SET project_id='foreign'")
        with self.assertRaises(StoreFormatError):
            AssessmentProjectFile.open(self.path)

    def test_creation_failures_remove_only_the_incomplete_new_file(self) -> None:
        """Failed schema setup or first save leaves no misleading project file.

        Args:
            None.

        Returns:
            None.
        """
        with (
            patch.object(
                AssessmentSqliteStore, "create", side_effect=OSError("failure")
            ),
            self.assertRaises(OSError),
        ):
            AssessmentProjectFile.create(self.path, self.meta)
        self.assertFalse(self.path.exists())
        with (
            patch.object(AssessmentProjectFile, "save", side_effect=OSError("failure")),
            self.assertRaises(OSError),
        ):
            AssessmentProjectFile.create_with_document(
                self.path, self.meta, "duet", self.duet
            )
        self.assertFalse(self.path.exists())
        workspace = self.workspace()
        self.assertTrue(
            workspace.create(str(self.path), self.meta, "duet", self.duet).completed
        )
        self.assertEqual(workspace.active.state, self.duet)
