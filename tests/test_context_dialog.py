"""Qt assignment chooser parity, filtering and safe presenter handoff.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QDialog, QDialogButtonBox

from ergotools.application.assessment_assignment import AssignmentSnapshot
from ergotools.application.assessment_binding import AssessmentBinding
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import AssessmentContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.resources import read_asset
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.presentation.assessment_selection import AssessmentSelector
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
    ClassifiedAssignment,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class ContextDialogTests(unittest.TestCase):
    """Real Qt controls with synthetic classified choices and an owned project."""

    @classmethod
    def setUpClass(cls) -> None:
        """Retain one QApplication for widget tests.

        Args:
            None.

        Returns:
            None.
        """
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        """Build small catalog and assignments, independent of operational files.

        Args:
            None.

        Returns:
            None.
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "project.sqlite"
        stations = (
            StationKey("Plant A", "Assembly", "Line 1", "Station 1"),
            StationKey("Plant A", "Assembly", "Line 1", "Station 2"),
        )
        hierarchy = WorkHierarchy(
            WorkCatalog(
                "p", (WorkerEntry("w 1"),), stations, ("Day", "Night", "Empty")
            ),
            ("Plant A",),
            (SectionKey("Plant A", "Assembly"),),
            (LineKey("Plant A", "Assembly", "Line 1"),),
        )
        places = (
            stations[0].at_shift("Day"),
            stations[1].at_shift("Day"),
            stations[0].at_shift("Night"),
        )
        self.options = tuple(
            ClassifiedAssignment(
                AssignmentSnapshot(
                    hierarchy.work.worker_context("w 1", place),
                    index,
                    True,
                    index,
                    True,
                ),
                f"J{index}",
                "Assembly operator",
            )
            for index, place in enumerate(places, 1)
        )
        self.place = places[0]
        with AssessmentProjectFile.create_catalogued(
            path, ProjectMetadata("p", "Dialog", MeasurementSystem.IMPERIAL)
        ) as project:
            project.save_hierarchy(hierarchy)
            project.create_bound_assessment(
                AssessmentBinding(
                    DocumentKey("p", "a"),
                    AssessmentContext(
                        self.options[0].assignment.worker, AssessmentKind.LIFFT
                    ),
                ),
                LifftDraft(MeasurementSystem.IMPERIAL),
            )
        self.workspace = ProjectWorkspace(
            lambda location: AssessmentProjectFile.open(Path(location)),
            JsonSettingsStore(path.parent / "settings.json"),
        )
        self.addCleanup(lambda: self.workspace.close(choice=CloseChoice.DISCARD))
        self.workspace.switch(str(path), "a")
        self.selector = AssessmentSelector(self.workspace)
        self.catalog = self.selector.refresh()
        self.icons = {}
        for name in ("plant", "section", "line", "station", "job_management", "cancel"):
            pixmap = QPixmap()
            self.assertTrue(pixmap.loadFromData(read_asset("icons/" + name + ".png")))
            self.icons[name] = QIcon(pixmap)

    def dialog(self, **kwargs: object) -> AssessmentContextDialog:
        """Construct a styled dialog and register deterministic widget cleanup.

        Args:
            kwargs: Explicit constructor overrides forwarded to the synthetic
                dialog/host.

        Returns:
            New owned styled context dialog registered for deterministic cleanup by the
            test case.
        """
        dialog = AssessmentContextDialog(
            self.selector,
            self.catalog,
            "w 1",
            AssessmentKind.LIFFT,
            self.options,
            self.icons,
            **kwargs,
        )
        self.addCleanup(dialog.close)
        return dialog

    def test_reference_layout_selected_handoff_does_not_change_session(self) -> None:
        """Current context expands ancestors; acceptance only prepares caller intent.

        Args:
            None.

        Returns:
            None.
        """
        dialog = self.dialog(current=self.place)
        old = self.workspace.active
        dialog.show()
        self.app.processEvents()
        self.assertEqual(dialog.minimumWidth(), 700)
        self.assertEqual(dialog.minimumHeight(), 540)
        self.assertEqual(dialog.tree.columnCount(), 3)
        self.assertTrue(dialog.use.isEnabled())
        self.assertIn("Job: J1", dialog.summary.text())
        QTest.mouseClick(dialog.use, Qt.LeftButton)
        self.assertEqual(dialog.result(), QDialog.Accepted)
        self.assertIs(self.workspace.active, old)
        self.assertEqual(dialog.selected.context.worker.workplace, self.place)
        self.assertTrue(self.selector.select(dialog.selected).completed)

    def test_shift_filter_empty_state_and_parent_nodes_are_not_choices(self) -> None:
        """Filter resets selection and never enables Use for structural tree nodes.

        Args:
            None.

        Returns:
            None.
        """
        dialog = self.dialog()
        dialog.show()
        self.app.processEvents()
        self.assertFalse(dialog.use.isEnabled())
        parent = dialog.tree.topLevelItem(0)
        dialog.tree.setCurrentItem(parent)
        dialog._accept_selection()
        self.assertIsNone(dialog.selected)
        self.assertFalse(dialog.use.isEnabled())
        dialog.tree.expandAll()
        leaf = parent.child(0).child(0).child(0)
        dialog.tree.setCurrentItem(leaf)
        self.assertTrue(dialog.use.isEnabled())
        dialog.shift.setCurrentText("Empty")
        self.assertEqual(dialog.tree.topLevelItemCount(), 0)
        self.assertFalse(dialog.use.isEnabled())
        self.assertIn("no workplace assignments", dialog.summary.text())
        dialog.shift.setCurrentText("Night")
        self.assertEqual(dialog.tree.topLevelItem(0).child(0).child(0).childCount(), 1)

    def test_stale_catalog_blocks_acceptance_and_cancel_keeps_source(self) -> None:
        """Stale catalogs show a retry instruction without switching.

        Args:
            None.

        Returns:
            None.
        """
        dialog = self.dialog(current=self.place)
        old = self.workspace.active
        self.selector.refresh()
        dialog._accept_selection()
        self.assertIsNone(dialog.selected)
        self.assertFalse(dialog.use.isEnabled())
        self.assertIn("Reopen", dialog.summary.text())
        dialog.show()
        QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.Cancel), Qt.LeftButton)
        self.assertEqual(dialog.result(), QDialog.Rejected)
        self.assertIs(self.workspace.active, old)

    def test_ineligible_assignments_are_filtered_and_duplicates_rejected(self) -> None:
        """Inactive/foreign owners stay hidden; a real workplace needs no Job.

        Args:
            None.

        Returns:
            None.
        """
        option = self.options[0]
        invalid = (
            replace(option, assignment=replace(option.assignment, active=False)),
            replace(
                option, assignment=replace(option.assignment, placement_active=False)
            ),
            replace(
                option,
                assignment=replace(
                    option.assignment,
                    worker=replace(option.assignment.worker, worker_id="other"),
                ),
            ),
            replace(
                option,
                assignment=replace(
                    option.assignment,
                    worker=replace(option.assignment.worker, project_id="other"),
                ),
            ),
        )
        self.options = invalid
        dialog = self.dialog()
        self.assertEqual(dialog.tree.topLevelItemCount(), 0)
        unplaced = replace(
            option,
            job_id=None,
            job_name=None,
            assignment=replace(option.assignment, job_placement_id=None),
        )
        self.options = (unplaced,)
        self.assertEqual(self.dialog().tree.topLevelItemCount(), 1)
        self.options = (option, option)
        with self.assertRaises(ValueError):
            self.dialog()

    def test_display_metadata_is_typed(self) -> None:
        """Job labels require explicit IDs and optional text names.

        Args:
            None.

        Returns:
            None.
        """
        option = self.options[0]
        for changes in ({"assignment": None}, {"job_id": ""}, {"job_name": 3}):
            with self.assertRaises(ValueError):
                replace(option, **changes)
        self.options = (replace(option, job_name=None),)
        dialog = self.dialog(current=self.place)
        self.assertTrue(dialog.summary.text().endswith("Job: J1"))

    def enable_historical(self) -> None:
        """Use persisted assignment records with the same native visual fixture.

        Args:
            None.

        Returns:
            None.
        """
        from ergotools.domain.assessment_history import AssignmentAssessment
        from ergotools.domain.job_catalog import (
            Job,
            JobCatalog,
            JobPlacement,
            WorkerJobAssignment,
        )
        from ergotools.presentation.assignment_selection import AssignmentSelector

        hierarchy = self.workspace.read_hierarchy().hierarchy
        self.workspace.close()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "historical.sqlite"
        jobs = JobCatalog(
            "p",
            tuple(Job(option.job_id, option.job_name) for option in self.options),
            tuple(
                JobPlacement(
                    option.assignment.job_placement_id,
                    option.job_id,
                    option.assignment.worker.workplace,
                )
                for option in self.options
            ),
            tuple(
                WorkerJobAssignment(
                    option.assignment.assignment_id,
                    option.assignment.worker,
                    option.assignment.job_placement_id,
                )
                for option in self.options
            ),
        )
        with AssessmentProjectFile.create_historical(
            path, ProjectMetadata("p", "Dialog", MeasurementSystem.IMPERIAL)
        ) as project:
            project.save_hierarchy(hierarchy)
            project.save_jobs(jobs)
            project.create_historical_assessment(
                AssignmentAssessment(
                    "a",
                    1,
                    AssessmentKind.LIFFT,
                    worker_id=next(
                        a.worker.worker_id
                        for a in project.load_jobs().assignments
                        if a.assignment_id == 1
                    ),
                ),
                LifftDraft(MeasurementSystem.IMPERIAL),
            )
        self.workspace.switch(str(path), "a")
        self.selector = AssignmentSelector(self.workspace)
        self.catalog = self.selector.refresh()

    def test_assignment_mode_returns_exact_saved_request(self) -> None:
        """Persisted options produce an assignment request without switching sources.

        Args:
            None.

        Returns:
            None.
        """
        from ergotools.presentation.assignment_selection import AssignmentRequest

        self.enable_historical()
        dialog = self.dialog(current=self.place, shifts=("Day", "Night", "Empty"))
        before = self.workspace.active
        dialog.use.click()
        self.assertEqual(dialog.result(), QDialog.Accepted)
        self.assertIsInstance(dialog.selected, AssignmentRequest)
        self.assertEqual(dialog.selected.target.assignment_id, 1)
        self.assertIs(self.workspace.active, before)
        self.assertTrue(self.selector.select(dialog.selected).completed)

    def test_assignment_mode_stale_and_empty_states(self) -> None:
        """Empty shifts disable acceptance and job refresh invalidates old choices.

        Args:
            None.

        Returns:
            None.
        """
        self.enable_historical()
        dialog = self.dialog(current=self.place, shifts=("Day", "Night", "Empty"))
        dialog.shift.setCurrentText("Empty")
        self.assertFalse(dialog.use.isEnabled())
        dialog.shift.setCurrentText("Day")
        self.workspace.read_jobs()
        dialog.use.click()
        self.assertIsNone(dialog.selected)
        self.assertFalse(dialog.use.isEnabled())
        self.assertIn("Reopen", dialog.summary.text())

    def test_assignment_mode_requires_shifts_and_matching_capabilities(self) -> None:
        """Reject incomplete composition rather than inferring a shift catalog.

        Args:
            None.

        Returns:
            None.
        """
        from ergotools.presentation.assessment_selection import AssessmentSelector

        self.enable_historical()
        with self.assertRaises(ValueError, msg="explicit project shifts"):
            self.dialog()
        self.selector = AssessmentSelector(self.workspace)
        with self.assertRaises(ValueError, msg="capabilities"):
            self.dialog(shifts=("Day",))

    def test_host_pending_cancel_and_modal_selection(self) -> None:
        """Pending text blocks I/O; modal acceptance delegates exact saved ownership.

        Args:
            None.

        Returns:
            None.
        """
        from unittest.mock import patch

        from ergotools.presentation.desktop.assignment_dialog_host import (
            AssignmentDialogHost,
        )

        self.enable_historical()
        events = []
        host = AssignmentDialogHost(
            self.workspace,
            self.icons,
            resolve_pending=lambda: False,
            choose_dirty=lambda: CloseChoice.CANCEL,
        )
        with patch.object(
            AssessmentProjectFile, "load_hierarchy", side_effect=AssertionError("IO")
        ):
            self.assertFalse(host.select("w 1", AssessmentKind.LIFFT).completed)

        def accepted(dialog: AssessmentContextDialog) -> int:
            """Click the real context chooser's Use control.

            Click the real context chooser's Use control and return its actual modal
            result.

            Args:
                dialog: Live modal/form under test; the caller owns its lifetime and
                    event-loop scheduling.

            Returns:
                Actual context dialog Qt result after clicking Use; no fabricated
                acceptance code is returned.
            """
            events.append("dialog")
            dialog.use.click()
            return dialog.result()

        host = AssignmentDialogHost(
            self.workspace,
            self.icons,
            resolve_pending=lambda: events.append("pending") or True,
            choose_dirty=lambda: events.append("dirty") or CloseChoice.CANCEL,
        )
        with patch.object(AssessmentContextDialog, "exec", accepted):
            self.assertTrue(
                host.select("w 1", AssessmentKind.LIFFT, current=self.place).completed
            )
        self.assertEqual(events, ["pending", "dialog"])
        with patch.object(
            AssessmentContextDialog, "exec", return_value=QDialog.Rejected
        ):
            self.assertFalse(host.select("w 1", AssessmentKind.LIFFT).completed)

    def test_host_dirty_cancel_save_and_invalid_modal_result(self) -> None:
        """Dirty consent follows selection; failures preserve source and allow retry.

        Args:
            None.

        Returns:
            None.
        """
        from unittest.mock import patch

        from ergotools.application.assessments.lifft_commands import AddLifftTask
        from ergotools.application.assessments.project_edits import LifftProjectEdit
        from ergotools.domain.assessment_history import AssignmentAssessment
        from ergotools.domain.assessments.lifft_draft import LifftTask
        from ergotools.presentation.desktop.assignment_dialog_host import (
            AssignmentDialogHost,
        )

        self.enable_historical()
        with AssessmentProjectFile.open(Path(self.workspace.location)) as project:
            project.create_historical_assessment(
                AssignmentAssessment(
                    "b",
                    2,
                    AssessmentKind.LIFFT,
                    worker_id=next(
                        a.worker.worker_id
                        for a in project.load_jobs().assignments
                        if a.assignment_id == 2
                    ),
                ),
                LifftDraft(MeasurementSystem.IMPERIAL),
            )
        old = self.workspace.active
        old.execute(
            LifftProjectEdit(AddLifftTask(old.document, LifftTask("t", 12, 10, 100), 0))
        )
        choice = CloseChoice.CANCEL
        host = AssignmentDialogHost(
            self.workspace,
            self.icons,
            resolve_pending=lambda: True,
            choose_dirty=lambda: choice,
        )

        def accepted(dialog: AssessmentContextDialog) -> int:
            """Click the real context chooser's Use control.

            Click the real context chooser's Use control and return its actual modal
            result.

            Args:
                dialog: Live modal/form under test; the caller owns its lifetime and
                    event-loop scheduling.

            Returns:
                Actual context dialog Qt result after clicking Use; no fabricated
                acceptance code is returned.
            """
            dialog.use.click()
            return dialog.result()

        current = self.options[1].assignment.worker.workplace
        with patch.object(AssessmentContextDialog, "exec", accepted):
            self.assertFalse(
                host.select("w 1", AssessmentKind.LIFFT, current=current).completed
            )
            self.assertIs(self.workspace.active, old)
            self.assertTrue(old.is_dirty)
            choice = CloseChoice.SAVE
            self.assertTrue(
                host.select("w 1", AssessmentKind.LIFFT, current=current).completed
            )
        self.assertFalse(old.is_dirty)
        self.assertEqual(self.workspace.active.document.document_id, "b")
        with (
            patch.object(
                AssessmentContextDialog, "exec", return_value=QDialog.Accepted
            ),
            self.assertRaises(ValueError),
        ):
            host.select("w 1", AssessmentKind.LIFFT)
        with patch.object(
            AssessmentContextDialog, "exec", return_value=QDialog.Rejected
        ):
            self.assertFalse(host.select("w 1", AssessmentKind.LIFFT).completed)

    def test_host_reentrant_and_changed_hierarchy_rejected(self) -> None:
        """Reentrant callbacks and hierarchy refresh cannot commit a modal choice.

        Args:
            None.

        Returns:
            None.
        """
        from unittest.mock import patch

        from ergotools.presentation.desktop.assignment_dialog_host import (
            AssignmentDialogHost,
        )

        self.enable_historical()
        host = AssignmentDialogHost(
            self.workspace,
            self.icons,
            resolve_pending=lambda: host.select("w 1", AssessmentKind.LIFFT).completed,
            choose_dirty=lambda: None,
        )
        with self.assertRaisesRegex(RuntimeError, "already in progress"):
            host.select("w 1", AssessmentKind.LIFFT)
        host = AssignmentDialogHost(
            self.workspace,
            self.icons,
            resolve_pending=lambda: True,
            choose_dirty=lambda: None,
        )

        def stale(dialog: AssessmentContextDialog) -> int:
            """Accept the context choice, refresh saved hierarchy before returning.

            Accept the context choice, refresh saved hierarchy before returning and
            expose the stale modal result to the host.

            Args:
                dialog: Live modal/form under test; the caller owns its lifetime and
                    event-loop scheduling.

            Returns:
                Actual accepted Qt result after refreshing hierarchy, so the host must
                reject the now-stale request.
            """
            dialog.use.click()
            self.workspace.read_hierarchy()
            return dialog.result()

        with (
            patch.object(AssessmentContextDialog, "exec", stale),
            self.assertRaisesRegex(ValueError, "hierarchy changed"),
        ):
            host.select("w 1", AssessmentKind.LIFFT, current=self.place)
