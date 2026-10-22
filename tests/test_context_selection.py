"""Workspace context selection with real temporary repositories and failure probes.

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
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
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
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_store import StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore


class ContextSelectionTests(unittest.TestCase):
    """Preserve current state until a fully validated target can be activated."""

    def setUp(self) -> None:
        """Create three bound models, then open LiFFT with clean persisted history.

        Args:
            None.

        Returns:
            None.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "contexts.sqlite"
        self.settings_path = self.path.parent / "settings.json"
        self.meta = ProjectMetadata("p", "Contexts", MeasurementSystem.IMPERIAL)
        self.owner = WorkerContext(
            "p", "w", WorkplaceContext("plant", "section", "line", "station", "day")
        )
        self.contexts = tuple(
            AssessmentContext(self.owner, kind) for kind in AssessmentKind
        )
        self.key = DocumentKey("p", "lifft")
        self.sources = (
            LifftDraft(MeasurementSystem.IMPERIAL),
            DuetDraft(),
            TstDraft(MeasurementSystem.METRIC),
        )
        with AssessmentProjectFile.create_contextual(self.path, self.meta) as project:
            for context, source in zip(self.contexts, self.sources, strict=True):
                key = DocumentKey("p", context.kind.value)
                project.insert_assessment(key, source)
                project.bind_assessment(AssessmentBinding(key, context))
        self.workspace = ProjectWorkspace(
            lambda location: AssessmentProjectFile.open(Path(location)),
            JsonSettingsStore(self.settings_path),
        )
        self.addCleanup(lambda: self.workspace.close(choice=CloseChoice.DISCARD))
        self.workspace.switch(str(self.path), self.key.document_id)

    def test_catalog_owner_drives_existing_binding_selection(self) -> None:
        """Typed catalog membership feeds selection without parsing worker labels.

        Args:
            None.

        Returns:
            None.
        """
        catalog = WorkCatalog(
            "p",
            (WorkerEntry("w", "First", "Last"),),
            (StationKey("plant", "section", "line", "station"),),
            ("day",),
        )
        owner = catalog.worker_context("w", catalog.available_workplaces()[0])
        for kind in AssessmentKind:
            context = AssessmentContext(owner, kind)
            self.assertTrue(self.workspace.select_context(context).completed)
            self.assertEqual(self.workspace.active.document.document_id, kind.value)
        renamed = replace(catalog, workers=(WorkerEntry("w", "Renamed", "Worker"),))
        self.assertEqual(renamed.worker_context("w", owner.workplace), owner)
        current = self.workspace.active
        with self.assertRaises(KeyError):
            catalog.worker_context("unknown", owner.workplace)
        self.assertIs(self.workspace.active, current)

    def dirty(self) -> None:
        """Apply one real typed command to the active LiFFT session.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.active.execute(
            LifftProjectEdit(AddLifftTask(self.key, LifftTask("a", 12, 10, 100), 0))
        )

    def test_selects_all_models_without_connection_or_settings_changes(self) -> None:
        """Selection changes only the active document, leaving project recency alone.

        Args:
            None.

        Returns:
            None.
        """
        before = self.settings_path.read_bytes()
        with (
            patch.object(
                AssessmentProjectFile,
                "open",
                side_effect=AssertionError("unexpected open"),
            ),
            patch.object(
                AssessmentProjectFile,
                "close",
                side_effect=AssertionError("unexpected close"),
            ),
        ):
            for context, source in zip(self.contexts, self.sources, strict=True):
                outcome = self.workspace.select_context(context)
                self.assertTrue(outcome.completed)
                self.assertEqual(outcome.warning_keys, ())
                self.assertEqual(self.workspace.active.state, source)
                self.assertEqual(
                    self.workspace.active.document.document_id, context.kind
                )
                self.assertFalse(self.workspace.active.is_dirty)
        self.assertEqual(self.workspace.location, str(self.path))
        self.assertEqual(self.settings_path.read_bytes(), before)

    def test_dirty_without_decision_and_cancel_do_no_lookup(self) -> None:
        """Pending consent does not save, resolve, load or change session identity.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        with patch.object(
            AssessmentProjectFile, "find_assessment", side_effect=AssertionError("I/O")
        ):
            for choice in (None, CloseChoice.CANCEL):
                self.assertFalse(
                    self.workspace.select_context(
                        self.contexts[1], choice=choice
                    ).completed
                )
            self.assertIs(self.workspace.active, current)
            self.assertTrue(current.is_dirty)
            current.undo()
            self.assertFalse(
                self.workspace.select_context(
                    self.contexts[1], choice=CloseChoice.CANCEL
                ).completed
            )

    def test_save_then_select_persists_old_edits_before_activation(self) -> None:
        """Save makes the detached old session clean and survives reopening.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        old = self.workspace.active
        self.assertTrue(
            self.workspace.select_context(
                self.contexts[1], choice=CloseChoice.SAVE
            ).completed
        )
        self.assertFalse(old.is_dirty)
        self.assertIsNot(self.workspace.active, old)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(self.key), old.state)
            self.assertEqual(project.find_assessment(self.contexts[0]), self.key)
        self.workspace.select_context(self.contexts[0])
        self.assertEqual(self.workspace.active.state, old.state)
        self.assertIsNone(self.workspace.active.undo_label_key)

    def test_discard_does_not_write_old_edits(self) -> None:
        """Discard leaves saved ownership intact and abandons unsaved edits.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        old = self.workspace.active
        self.workspace.select_context(self.contexts[2], choice=CloseChoice.DISCARD)
        self.assertTrue(old.is_dirty)
        self.workspace.select_context(self.contexts[0])
        self.assertEqual(self.workspace.active.state, self.sources[0])
        self.assertIsNot(self.workspace.active, old)

    def test_same_context_preserves_history_even_with_save_or_discard(self) -> None:
        """A no-op selection keeps dirty state and redo without an implicit save.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        for choice in (CloseChoice.SAVE, CloseChoice.DISCARD):
            self.assertTrue(
                self.workspace.select_context(self.contexts[0], choice=choice).completed
            )
            self.assertIs(self.workspace.active, current)
            self.assertTrue(current.is_dirty)
        current.undo()
        self.workspace.select_context(self.contexts[0])
        self.assertIsNotNone(current.redo_label_key)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(self.key), self.sources[0])

    def test_missing_or_failed_target_does_not_save_current(self) -> None:
        """Missing contexts and failed target reads leave current history dirty.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        missing = replace(
            self.contexts[0], worker=replace(self.owner, worker_id="absent")
        )
        with self.assertRaises(KeyError):
            self.workspace.select_context(missing, choice=CloseChoice.SAVE)
        for method in ("find_assessment", "assessment_binding", "load"):
            with (
                patch.object(
                    AssessmentProjectFile, method, side_effect=OSError("read")
                ),
                self.assertRaises(OSError),
            ):
                self.workspace.select_context(self.contexts[1], choice=CloseChoice.SAVE)
            self.assertIs(self.workspace.active, current)
            self.assertTrue(current.is_dirty)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(self.key), self.sources[0])
        self.assertTrue(
            self.workspace.select_context(
                self.contexts[1], choice=CloseChoice.SAVE
            ).completed
        )

    def test_sql_save_failure_retains_current_and_allows_retry(self) -> None:
        """Failed commit cannot activate the prepared target or discard old history.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        current = self.workspace.active
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER reject_save BEFORE INSERT ON draft_documents "
                "BEGIN SELECT RAISE(ABORT, 'injected save failure'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.workspace.select_context(self.contexts[1], choice=CloseChoice.SAVE)
        self.assertIs(self.workspace.active, current)
        self.assertTrue(current.is_dirty)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DROP TRIGGER reject_save")
        self.assertTrue(
            self.workspace.select_context(
                self.contexts[1], choice=CloseChoice.SAVE
            ).completed
        )

    def test_foreign_and_inconsistent_adapter_results_are_rejected(self) -> None:
        """The application validates returned project and reverse binding identity.

        Args:
            None.

        Returns:
            None.
        """
        current = self.workspace.active
        foreign = replace(
            self.contexts[0], worker=replace(self.owner, project_id="other")
        )
        with self.assertRaises(ValueError):
            self.workspace.select_context(foreign)
        with (
            patch.object(
                AssessmentProjectFile,
                "find_assessment",
                return_value=DocumentKey("other", "x"),
            ),
            self.assertRaises(ValueError),
        ):
            self.workspace.select_context(self.contexts[1])
        for binding in (None, AssessmentBinding(self.key, self.contexts[0])):
            with (
                patch.object(
                    AssessmentProjectFile, "assessment_binding", return_value=binding
                ),
                self.assertRaises(ValueError),
            ):
                self.workspace.select_context(self.contexts[1])
        self.assertIs(self.workspace.active, current)
        self.assertTrue(self.workspace.select_context(self.contexts[1]).completed)

    def test_nested_transition_and_unexpected_edits_abort_selection(self) -> None:
        """Reject reentrant transitions and retain edits made by a broken adapter.

        Args:
            None.

        Returns:
            None.
        """
        current = self.workspace.active
        with (
            patch.object(
                AssessmentProjectFile,
                "find_assessment",
                side_effect=lambda _: self.workspace.save(),
            ),
            self.assertRaisesRegex(RuntimeError, "already in progress"),
        ):
            self.workspace.select_context(self.contexts[1])
        original = AssessmentProjectFile.find_assessment

        def edit_during_lookup(
            project: AssessmentProjectFile, context: AssessmentContext
        ) -> DocumentKey | None:
            """Edit the active source during the injected lookup.

            Edit the active source during the injected lookup before returning the
            original candidate, verifying stale transition consent cannot discard it.

            Args:
                project: Isolated native project fixture owned by this test; never the
                    reference checkout.
                context: Exact project/worker/workplace/tool ownership request supplied
                    to the test adapter.

            Returns:
                Original lookup candidate key, or None when absent, after deliberately
                invalidating current source consent.
            """
            self.dirty()
            return original(project, context)

        with (
            patch.object(AssessmentProjectFile, "find_assessment", edit_during_lookup),
            self.assertRaisesRegex(RuntimeError, "draft changed"),
        ):
            self.workspace.select_context(self.contexts[1])
        self.assertIs(self.workspace.active, current)
        self.assertTrue(current.is_dirty)
        self.assertTrue(
            self.workspace.select_context(
                self.contexts[1], choice=CloseChoice.DISCARD
            ).completed
        )

    def test_no_project_unsupported_adapter_and_old_format(self) -> None:
        """Capability/version errors are explicit and do not alter an open session.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(ValueError):
            self.workspace.select_context(self.contexts[0], choice="save")
        self.workspace.close()
        with self.assertRaisesRegex(RuntimeError, "No project"):
            self.workspace.select_context(self.contexts[0])
        old_path = self.path.parent / "old.sqlite"
        with ProjectFile.create_with_document(
            old_path, self.meta, "lifft", self.sources[0]
        ):
            pass
        self.workspace.switch(str(old_path), "lifft")
        with self.assertRaises(StoreFormatError):
            self.workspace.select_context(self.contexts[0])
        legacy = ProjectWorkspace(
            lambda location: ProjectFile.open(Path(location)),
            JsonSettingsStore(self.settings_path),
        )
        try:
            legacy.switch(str(old_path), "lifft")
            with self.assertRaisesRegex(RuntimeError, "adapter is not configured"):
                legacy.select_context(self.contexts[0])
        finally:
            legacy.close()
