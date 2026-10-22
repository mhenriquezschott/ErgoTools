"""Presenter ownership and real catalog-to-assessment workflows without widgets.

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
from ergotools.domain.assessments.context import AssessmentContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.assessment_selection import AssessmentSelector
from ergotools.presentation.worker_options import WorkerOrder


class AssessmentSelectionTests(unittest.TestCase):
    """Use synthetic project files to exercise presenter and transactional services."""

    def setUp(self) -> None:
        """Open one bound assessment and retain empty parents in its catalog.

        Args:
            None.

        Returns:
            None.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "selection.sqlite"
        self.key = DocumentKey("p", "old")
        self.source = LifftDraft(MeasurementSystem.IMPERIAL)
        station = StationKey("P", "S", "L", "1")
        self.place = station.at_shift("Day")
        self.hierarchy = WorkHierarchy(
            WorkCatalog(
                "p",
                (WorkerEntry("w 1", "Ana", "Zulu"), WorkerEntry("w 2", "Bea", "Alpha")),
                (station,),
                ("Day",),
            ),
            ("P", "Empty"),
            (SectionKey("P", "S"),),
            (LineKey("P", "S", "L"),),
        )
        with AssessmentProjectFile.create_catalogued(
            self.path, ProjectMetadata("p", "Presenter", MeasurementSystem.IMPERIAL)
        ) as project:
            project.save_hierarchy(self.hierarchy)
            context = AssessmentContext(
                self.hierarchy.work.worker_context("w 1", self.place),
                AssessmentKind.LIFFT,
            )
            project.create_bound_assessment(
                AssessmentBinding(self.key, context), self.source
            )
            project.insert_assessment(DocumentKey("p", "other"), self.source)
        self.workspace = ProjectWorkspace(
            lambda location: AssessmentProjectFile.open(Path(location)),
            JsonSettingsStore(self.path.parent / "settings.json"),
        )
        self.addCleanup(lambda: self.workspace.close(choice=CloseChoice.DISCARD))
        self.workspace.switch(str(self.path), "old")
        self.presenter = AssessmentSelector(self.workspace)

    def dirty(self) -> None:
        """Add a real source edit for dirty-choice and revision checks.

        Args:
            None.

        Returns:
            None.
        """
        self.workspace.active.execute(
            LifftProjectEdit(AddLifftTask(self.key, LifftTask("t", 12, 10, 100), 0))
        )

    def test_explicit_ids_options_empty_parents_and_all_model_creation(self) -> None:
        """Create and reopen all models without deriving identity from captions.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self.presenter.refresh(WorkerOrder.LAST_NAME)
        self.assertEqual([item.worker_id for item in catalog.workers], ["w 2", "w 1"])
        self.assertEqual(catalog.snapshot.hierarchy.sections_in("Empty"), ())
        sources = (self.source, DuetDraft(), TstDraft(MeasurementSystem.METRIC))
        for kind, source in zip(AssessmentKind, sources, strict=True):
            selected = self.presenter.prepare(catalog, "w 2", self.place, kind)
            self.assertTrue(
                self.presenter.create(selected, kind.value, source).completed
            )
            self.assertEqual(self.workspace.active.state, source)
            self.assertFalse(self.workspace.active.is_dirty)
            with self.assertRaises(ValueError):
                self.presenter.create(selected, "again", source)
        selected = self.presenter.prepare(
            catalog, "w 1", self.place, AssessmentKind.LIFFT
        )
        self.assertTrue(self.presenter.select(selected).completed)
        self.assertEqual(self.workspace.active.document, self.key)
        with self.assertRaises(ValueError):
            self.presenter.select(selected)

    def test_cancel_and_missing_consent_preserve_retry_then_save_works(self) -> None:
        """Canceled creation does not save old edits or consume the explicit choice.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        old = self.workspace.active
        catalog = self.presenter.refresh()
        selected = self.presenter.prepare(
            catalog, "w 2", self.place, AssessmentKind.DUET
        )
        for choice in (None, CloseChoice.CANCEL):
            self.assertFalse(
                self.presenter.create(
                    selected, "duet", DuetDraft(), choice=choice
                ).completed
            )
            self.assertIs(self.workspace.active, old)
            self.assertTrue(old.is_dirty)
        self.assertTrue(
            self.presenter.create(
                selected, "duet", DuetDraft(), choice=CloseChoice.SAVE
            ).completed
        )
        self.assertFalse(old.is_dirty)

    def test_wrong_model_fails_before_old_save(self) -> None:
        """A mistaken callback cannot save old data before model validation.

        Args:
            None.

        Returns:
            None.
        """
        self.dirty()
        selected = self.presenter.prepare(
            self.presenter.refresh(), "w 2", self.place, AssessmentKind.DUET
        )
        with self.assertRaises(ValueError):
            self.presenter.create(
                selected, "wrong", self.source, choice=CloseChoice.SAVE
            )
        self.assertTrue(self.workspace.active.is_dirty)
        self.assertTrue(
            self.presenter.create(
                selected, "duet", DuetDraft(), choice=CloseChoice.DISCARD
            ).completed
        )

    def test_copied_foreign_and_superseded_choices_fail(self) -> None:
        """Equal data does not authorize callbacks from another selection owner.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self.presenter.refresh()
        selected = self.presenter.prepare(
            catalog, "w 1", self.place, AssessmentKind.LIFFT
        )
        with self.assertRaises(ValueError):
            self.presenter.select(replace(selected))
        replacement = self.presenter.prepare(
            catalog, "w 2", self.place, AssessmentKind.LIFFT
        )
        with self.assertRaises(ValueError):
            self.presenter.select(selected)
        with self.assertRaises(ValueError):
            AssessmentSelector(self.workspace).select(replacement)
        with self.assertRaises(ValueError):
            self.presenter.prepare(
                replace(catalog), "w 1", self.place, AssessmentKind.LIFFT
            )
        with self.assertRaises(ValueError):
            self.presenter.select(replacement)

    def test_refresh_and_catalog_save_invalidate_existing_views(self) -> None:
        """Refresh, ordering and saved catalog changes invalidate old options.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self.presenter.refresh()
        selected = self.presenter.prepare(
            catalog, "w 1", self.place, AssessmentKind.LIFFT
        )
        refreshed = self.presenter.refresh(WorkerOrder.LAST_NAME)
        with self.assertRaises(ValueError):
            self.presenter.select(selected)
        with self.assertRaises(ValueError):
            self.presenter.prepare(catalog, "w 1", self.place, AssessmentKind.LIFFT)
        self.workspace.replace_hierarchy(refreshed.snapshot, self.hierarchy)
        with self.assertRaises(ValueError):
            self.presenter.prepare(refreshed, "w 1", self.place, AssessmentKind.LIFFT)
        catalog = self.presenter.refresh()
        with (
            patch.object(
                AssessmentProjectFile, "load_hierarchy", side_effect=OSError("read")
            ),
            self.assertRaises(OSError),
        ):
            self.presenter.refresh()
        with self.assertRaises(ValueError):
            self.presenter.prepare(catalog, "w 1", self.place, AssessmentKind.LIFFT)

    def test_active_edits_and_document_switches_invalidate_prepared_requests(
        self,
    ) -> None:
        """Dirty consent must refer to the active source at preparation time.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self.presenter.refresh()
        selected = self.presenter.prepare(
            catalog, "w 1", self.place, AssessmentKind.LIFFT
        )
        self.dirty()
        with self.assertRaisesRegex(ValueError, "Active assessment changed"):
            self.presenter.select(selected, choice=CloseChoice.SAVE)
        selected = self.presenter.prepare(
            catalog, "w 1", self.place, AssessmentKind.LIFFT
        )
        self.workspace.switch(str(self.path), "other", choice=CloseChoice.DISCARD)
        with self.assertRaisesRegex(ValueError, "Active assessment changed"):
            self.presenter.select(selected)

    def test_missing_members_or_bindings_never_choose_a_fallback(self) -> None:
        """Invalid membership clears prior intent; a missing document can be created.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self.presenter.refresh()
        old = self.workspace.active
        for worker, place in (
            ("missing", self.place),
            ("w 1", replace(self.place, shift_id="missing")),
        ):
            with self.assertRaises(KeyError):
                self.presenter.prepare(catalog, worker, place, AssessmentKind.LIFFT)
        selected = self.presenter.prepare(
            catalog, "w 2", self.place, AssessmentKind.LIFFT
        )
        with self.assertRaises(KeyError):
            self.presenter.select(selected)
        self.assertIs(self.workspace.active, old)
        self.assertTrue(self.presenter.create(selected, "new", self.source).completed)

    def test_select_cancel_is_retryable_and_sql_creation_failure_rolls_back(
        self,
    ) -> None:
        """Retry callbacks deliberately after cancellation or a failed transaction.

        Args:
            None.

        Returns:
            None.
        """
        catalog = self.presenter.refresh()
        selected = self.presenter.prepare(
            catalog, "w 1", self.place, AssessmentKind.LIFFT
        )
        self.assertFalse(
            self.presenter.select(selected, choice=CloseChoice.CANCEL).completed
        )
        self.assertTrue(self.presenter.select(selected).completed)
        selected = self.presenter.prepare(
            catalog, "w 2", self.place, AssessmentKind.LIFFT
        )
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TRIGGER fail BEFORE INSERT ON assessment_bindings "
                "BEGIN SELECT RAISE(ABORT, 'injected'); END"
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.presenter.create(selected, "new", self.source)
        with (
            AssessmentProjectFile.open(self.path) as project,
            self.assertRaises(KeyError),
        ):
            project.load(DocumentKey("p", "new"))
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DROP TRIGGER fail")
        self.assertTrue(self.presenter.create(selected, "new", self.source).completed)
