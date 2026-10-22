"""Real Qt widget events and temporary-project lifecycle for the LiFFT preview.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import PropertyMock, patch

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import TransitionOutcome
from ergotools.application.session import DocumentKey
from ergotools.bootstrap import create_window, list_lifft_documents
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.numeric_input import DecimalConvention

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


class DesktopTests(unittest.TestCase):
    """Exercise UI actions with injected file dialogs and isolated SQLite files."""

    def setUp(self) -> None:
        """Build a real offscreen window with no user settings or operational data.

        Args:
            None.

        Returns:
            None.
        """
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.window = create_window(self.directory / "settings.json")
        self.window.show()
        _APP.processEvents()
        self.addCleanup(self.cleanup_window)
        self.workspace = self.window.presenter.workspace
        self.path = self.directory / "project.sqlite"

    def cleanup_window(self) -> None:
        """Release every project/window without prompting or leaking connections.

        Args:
            None.

        Returns:
            None.
        """
        self.window.pending = False
        self.workspace.close(choice=CloseChoice.DISCARD)
        self.window.close()
        self.window.deleteLater()
        _APP.processEvents()

    def seed(self, system: MeasurementSystem = MeasurementSystem.IMPERIAL) -> None:
        """Create an ordinary project and refresh its committed task source.

        Args:
            system: Explicit metric/imperial display or source system exercised by this
                scenario.

        Returns:
            None.
        """
        self.workspace.create(
            str(self.path),
            ProjectMetadata("p", "Test", system),
            "lifft",
            LifftDraft(system, (LifftTask("a", 12, 10, 100),)),
        )
        self.window.refresh()

    def type_value(self, text: str) -> None:
        """Use actual keyboard events so pending-text signals are exercised.

        Args:
            text: Literal typed/control input, including invalid/incomplete cases where
                specified.

        Returns:
            None.
        """
        self.window.entry.setFocus()
        self.window.entry.selectAll()
        QTest.keyClicks(self.window.entry, text)
        _APP.processEvents()

    def test_empty_and_populated_layout_and_icon_assets(self) -> None:
        """Window and bottom controls fit; asset icons load independently of cwd.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(self.window.table.rowCount(), 0)
        self.assertFalse(self.window.buttons["save"].isEnabled())
        self.assertFalse(self.window.buttons["new"].icon().isNull())
        self.seed()
        self.assertEqual(self.window.table.item(0, 1).text(), "12")
        self.assertTrue(self.window.entry.isEnabled())
        for width, height in ((1200, 780), (960, 680)):
            self.window.resize(width, height)
            _APP.processEvents()
            for widget in (
                self.window.table,
                self.window.entry,
                self.window.message,
                self.window.buttons["calculate"],
            ):
                point = widget.mapTo(self.window, widget.rect().bottomRight())
                self.assertLess(point.x(), self.window.width())
                self.assertLess(point.y(), self.window.height())

    def test_real_edit_pending_protection_apply_undo_redo(self) -> None:
        """Unit changes/close cannot reinterpret pending text; apply is one command.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        self.window.field.setCurrentIndex(1)
        self.type_value("20")
        self.assertTrue(self.window.pending)
        self.assertFalse(self.window.units.isEnabled())
        self.assertFalse(self.window.table.isEnabled())
        self.assertFalse(self.window.close())
        self.assertEqual(self.window.entry.text(), "20")
        QTest.mouseClick(self.window.buttons["apply"], Qt.LeftButton)
        self.assertFalse(self.window.pending)
        self.assertEqual(self.workspace.active.state.tasks[0].load, 20)
        QTest.mouseClick(self.window.buttons["undo"], Qt.LeftButton)
        self.assertEqual(self.workspace.active.state.tasks[0].load, 10)
        QTest.mouseClick(self.window.buttons["redo"], Qt.LeftButton)
        self.assertEqual(self.workspace.active.state.tasks[0].load, 20)

    def test_invalid_text_retry_discard_repetition_and_blank(self) -> None:
        """Invalid text remains visible, and empty input creates an unfinished field.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        self.window.field.setCurrentIndex(2)
        self.type_value("bad")
        QTest.mouseClick(self.window.buttons["apply"], Qt.LeftButton)
        self.assertTrue(self.window.pending)
        self.assertEqual(self.window.entry.text(), "bad")
        self.assertEqual(self.workspace.active.state.tasks[0].repetitions, 100)
        QTest.mouseClick(self.window.buttons["discard"], Qt.LeftButton)
        self.assertEqual(self.window.entry.text(), "100")
        self.type_value("125.5")
        QTest.keyClick(self.window.entry, Qt.Key_Return)
        self.assertEqual(self.workspace.active.state.tasks[0].repetitions, 125.5)
        self.window.entry.selectAll()
        QTest.keyClick(self.window.entry, Qt.Key_Backspace)
        QTest.mouseClick(self.window.buttons["apply"], Qt.LeftButton)
        self.assertIsNone(self.workspace.active.state.tasks[0].repetitions)
        self.window.calculate()
        self.assertEqual(self.window.damage_value.text(), "—")

    def test_units_language_decimal_and_results(self) -> None:
        """Independent language/units affect editors without changing source units.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        self.window.calculate()
        original = self.window.damage_value.text()
        self.assertNotEqual(original, "—")
        self.window.units.setCurrentIndex(1)
        self.window.decimal.setCurrentIndex(1)
        self.window.languages.setCurrentIndex(1)
        self.assertEqual(self.window.presenter.convention, DecimalConvention.COMMA)
        self.assertEqual(self.window.buttons["calculate"].text(), "Calcular")
        self.assertEqual(self.window.damage_value.text(), original)
        self.window.field.setCurrentIndex(1)
        self.assertEqual(self.window.entry.text(), "44,5")
        self.type_value("22,25")
        QTest.mouseClick(self.window.buttons["apply"], Qt.LeftButton)
        self.assertEqual(self.workspace.active.state.tasks[0].load, 5)
        self.assertEqual(self.window.damage_value.text(), "—")
        self.window.save_project()
        self.assertFalse(self.workspace.active.is_dirty)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(project.load(DocumentKey("p", "lifft")).tasks[0].load, 5)

    def test_metric_source_calculates_under_both_interface_languages(self) -> None:
        """Interface language never changes the recorded metric calculation.

        Args:
            None.

        Returns:
            None.
        """
        self.seed(MeasurementSystem.METRIC)
        self.window.calculate()
        self.assertEqual(self.window.message.text(), "")
        self.assertNotEqual(self.window.probability_value.text(), "—")
        self.window.languages.setCurrentIndex(1)
        self.window.calculate()
        self.assertEqual(self.window.message.text(), "")

    def test_add_remove_and_empty_selection(self) -> None:
        """Task commands are undoable and empty forms disable row editors.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        self.window.add_task()
        self.assertEqual(self.window.table.rowCount(), 2)
        self.window.remove_task()
        self.assertEqual(self.window.table.rowCount(), 1)
        self.window.undo()
        self.assertEqual(self.window.table.rowCount(), 2)
        self.window.redo()
        self.window.remove_task()
        self.assertEqual(self.window.table.rowCount(), 0)
        self.assertFalse(self.window.entry.isEnabled())
        self.window.apply_edit()
        self.window.remove_task()

    def test_new_open_cancellation_and_catalog_filtering(self) -> None:
        """Dialogs route to actual workspace files; another model is not adopted.

        Args:
            None.

        Returns:
            None.
        """
        with patch(
            "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_file",
            return_value="",
        ):
            self.window.new_project()
        with patch(
            "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_file",
            return_value="",
        ):
            self.window.open_project()
        with (
            patch(
                "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_file",
                return_value=str(self.path),
            ),
            patch(
                "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_item",
                return_value=("Metric (cm / N)", False),
            ),
        ):
            self.window.new_project()
        self.assertFalse(self.path.exists())
        with (
            patch(
                "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_file",
                return_value=str(self.path),
            ),
            patch(
                "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_item",
                return_value=("Metric (cm / N)", True),
            ),
        ):
            self.window.new_project()
        self.assertEqual(self.workspace.active.state.system, MeasurementSystem.METRIC)
        self.assertEqual(list_lifft_documents(str(self.path)), ("lifft",))
        self.workspace.close()
        with (
            patch(
                "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_file",
                return_value=str(self.path),
            ),
            patch(
                "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_item",
                return_value=("lifft", True),
            ),
        ):
            self.window.open_project()
        self.assertEqual(self.workspace.active.state.system, MeasurementSystem.METRIC)
        other = self.directory / "duet.sqlite"
        with AssessmentProjectFile.create_with_document(
            other,
            ProjectMetadata("d", "Duet", MeasurementSystem.IMPERIAL),
            "duet",
            DuetDraft(),
        ):
            pass
        with patch(
            "ergotools.presentation.desktop.lifft_window.LifftWindow.choose_file",
            return_value=str(other),
        ):
            self.window.open_project()
        self.assertIn("no LiFFT", self.window.message.text())

    def test_close_dirty_choices_and_save_failure_retains_state(self) -> None:
        """Cancel, failed saves and successful saves preserve correct ownership.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        self.window.add_task()
        with patch.object(self.window, "dirty_choice", return_value=CloseChoice.CANCEL):
            self.assertFalse(self.window.close())
        with (
            patch.object(self.workspace, "save", side_effect=OSError("test")),
            self.assertLogs(
                "ergotools.presentation.desktop.lifft_window", level="ERROR"
            ),
        ):
            self.window.run(self.window.save_project)
        self.assertTrue(self.workspace.active.is_dirty)
        with patch.object(self.window, "dirty_choice", return_value=CloseChoice.SAVE):
            self.assertTrue(self.window.close())
        self.assertIsNone(self.workspace.active)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(len(project.load(DocumentKey("p", "lifft")).tasks), 2)

    def test_dirty_dialog_buttons_and_cleanup_failure(self) -> None:
        """All dirty decisions are reachable; cleanup failures remain visible.

        Args:
            None.

        Returns:
            None.
        """
        self.seed()
        self.assertIsNone(self.window.dirty_choice())
        self.window.add_task()
        for index, expected in (
            (QMessageBox.AcceptRole, CloseChoice.SAVE),
            (QMessageBox.DestructiveRole, CloseChoice.DISCARD),
            (QMessageBox.RejectRole, CloseChoice.CANCEL),
        ):
            with (
                patch.object(QMessageBox, "exec", return_value=0),
                patch.object(
                    QMessageBox,
                    "clickedButton",
                    lambda dialog, role=index: next(
                        button
                        for button in dialog.buttons()
                        if dialog.buttonRole(button) == role
                    ),
                ),
            ):
                self.assertEqual(self.window.dirty_choice(), expected)
        with (
            patch.object(
                self.workspace,
                "close",
                return_value=TransitionOutcome(True, ("project.cleanup_failed",)),
            ),
            patch.object(self.window, "dirty_choice", return_value=CloseChoice.DISCARD),
        ):
            event = QCloseEvent()
            self.window.closeEvent(event)
            self.assertFalse(event.isAccepted())
        with (
            patch.object(self.workspace, "close", side_effect=OSError("test")),
            patch.object(self.window, "dirty_choice", return_value=CloseChoice.DISCARD),
            self.assertLogs(
                "ergotools.presentation.desktop.lifft_window", level="ERROR"
            ),
        ):
            event = QCloseEvent()
            self.window.closeEvent(event)
            self.assertFalse(event.isAccepted())
        self.window.closeEvent(None)

    def test_close_retries_detached_connection_cleanup(self) -> None:
        """A failed release must be retried before the window can exit.

        Args:
            None.

        Returns:
            None.
        """
        with (
            patch.object(
                type(self.workspace),
                "pending_release_count",
                new_callable=PropertyMock,
                return_value=1,
            ),
            patch.object(self.workspace, "retry_releases", return_value=1) as retry,
        ):
            event = QCloseEvent()
            self.window.closeEvent(event)
            self.assertFalse(event.isAccepted())
            retry.assert_called_once()
        with (
            patch.object(
                type(self.workspace),
                "pending_release_count",
                new_callable=PropertyMock,
                return_value=1,
            ),
            patch.object(self.workspace, "retry_releases", return_value=0),
        ):
            event = QCloseEvent()
            self.window.closeEvent(event)
            self.assertTrue(event.isAccepted())

    def test_real_dialog_accept_and_cancel(self) -> None:
        """Exercise real styled dialog construction and selected-value returns.

        Args:
            None.

        Returns:
            None.
        """

        def accept_file(dialog: QFileDialog) -> int:
            """Select the disposable file without opening the platform's system picker.

            Args:
                dialog: Standard Qt wrapper configured with product filter/save policy.

            Returns:
                Accepted result; platform-native UI is reserved for owner testing.
            """
            self.assertFalse(dialog.testOption(QFileDialog.DontUseNativeDialog))
            dialog.selectFile(str(self.path))
            return QFileDialog.Accepted

        with patch.object(QFileDialog, "exec", accept_file):
            self.assertEqual(self.window.choose_file(True), str(self.path))
        with patch.object(QFileDialog, "exec", return_value=QFileDialog.Rejected):
            self.assertEqual(self.window.choose_file(False), "")

        def accept_item() -> None:
            """Select exact caption B in the actual item chooser and accept it.

            Args:
                None.

            Returns:
                None.
            """
            dialog = QApplication.activeModalWidget()
            self.assertIsInstance(dialog, QInputDialog)
            dialog.setTextValue("B")
            dialog.accept()

        QTimer.singleShot(0, accept_item)
        self.assertEqual(
            self.window.choose_item("Choose", "Item", ["A", "B"]), ("B", True)
        )
        QTimer.singleShot(0, lambda: QApplication.activeModalWidget().reject())
        self.assertFalse(self.window.choose_item("Choose", "Item", ["A"])[1])

    def seed_historical(self, *, include_second: bool = True) -> None:
        """Populate two distinct LiFFT assignment contexts in a temporary project.

        Args:
            include_second: True adds the second synthetic source/owner; False retains a
                single-document fixture.

        Returns:
            None.
        """
        from ergotools.domain.assessment_history import AssignmentAssessment
        from ergotools.domain.assessments.document import AssessmentKind
        from ergotools.domain.job_catalog import (
            Job,
            JobCatalog,
            JobPlacement,
            WorkerJobAssignment,
        )
        from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
        from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy

        stations = (
            StationKey("Plant", "Assembly", "Line", "1"),
            StationKey("Plant", "Assembly", "Line", "2"),
        )
        hierarchy = WorkHierarchy(
            WorkCatalog("p", (WorkerEntry("worker"),), stations, ("Day", "Empty")),
            ("Plant",),
            (SectionKey("Plant", "Assembly"),),
            (LineKey("Plant", "Assembly", "Line"),),
        )
        owners = tuple(
            hierarchy.work.worker_context("worker", station.at_shift("Day"))
            for station in stations
        )
        jobs = JobCatalog(
            "p",
            (Job("j", "Assembly"),),
            tuple(
                JobPlacement(i, "j", owner.workplace)
                for i, owner in enumerate(owners, 1)
            ),
            tuple(
                WorkerJobAssignment(i, owner, i) for i, owner in enumerate(owners, 1)
            ),
        )
        with AssessmentProjectFile.create_historical(
            self.path, ProjectMetadata("p", "Test", MeasurementSystem.IMPERIAL)
        ) as project:
            project.save_hierarchy(hierarchy)
            project.save_jobs(jobs)
            for identity in (1, 2) if include_second else (1,):
                project.create_historical_assessment(
                    AssignmentAssessment(
                        str(identity),
                        identity,
                        AssessmentKind.LIFFT,
                        worker_id=next(
                            a.worker.worker_id
                            for a in jobs.assignments
                            if a.assignment_id == identity
                        ),
                    ),
                    LifftDraft(
                        MeasurementSystem.IMPERIAL,
                        (LifftTask("t", 12 * identity, 10, 100),),
                    ),
                )
        self.workspace.switch(str(self.path), "1")
        self.window.refresh()

    def test_context_action_capability_pending_and_selection(self) -> None:
        """The real window action respects pending text and rebinds selected source.

        Args:
            None.

        Returns:
            None.
        """
        from ergotools.presentation.desktop.assessment_context_dialog import (
            AssessmentContextDialog,
        )

        self.assertFalse(self.window.buttons["assessment_context"].isEnabled())
        self.seed_historical()
        self.assertTrue(self.window.buttons["assessment_context"].isEnabled())
        self.type_value("15")
        self.assertFalse(self.window.buttons["assessment_context"].isEnabled())
        self.window.choose_assessment_context()
        self.assertTrue(self.window.pending)
        self.window.discard_edit()
        self.window.refresh()

        def accept_second(dialog: AssessmentContextDialog) -> int:
            """Select the second exact station leaf and click Use.

            Select the second exact station leaf and click Use, returning the actual
            context dialog result.

            Args:
                dialog: Live modal/form under test; the caller owns its lifetime and
                    event-loop scheduling.

            Returns:
                Actual Qt dialog result after selecting the second exact station leaf
                and clicking Use.
            """
            leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(1)
            dialog.tree.setCurrentItem(leaf)
            dialog.use.click()
            return dialog.result()

        with (
            patch.object(self.window, "choose_item", return_value=("worker", True)),
            patch.object(AssessmentContextDialog, "exec", accept_second),
        ):
            self.window.buttons["assessment_context"].click()
        self.assertEqual(self.workspace.active.document.document_id, "2")
        self.assertEqual(self.window.table.item(0, 1).text(), "24")
        self.assertEqual(self.window.damage_value.text(), "—")
        with patch.object(self.window, "choose_item", return_value=("", False)):
            self.window.choose_assessment_context()
        self.assertEqual(self.workspace.active.document.document_id, "2")

    def test_old_project_context_action_disabled(self) -> None:
        """Opening an older project keeps its format and management interlocks.

        Args:
            None.

        Returns:
            None.
        """
        with AssessmentProjectFile.create_with_document(
            self.path,
            ProjectMetadata("p", "Old", MeasurementSystem.IMPERIAL),
            "lifft",
            LifftDraft(MeasurementSystem.IMPERIAL),
        ):
            pass
        self.workspace.switch(str(self.path), "lifft")
        self.window.refresh()
        self.assertFalse(self.window.buttons["assessment_context"].isEnabled())
        self.window.choose_assessment_context()
        self.assertEqual(self.workspace.active.document.document_id, "lifft")

    def test_first_assessment_creation_from_window(self) -> None:
        """Create current version one without replacing another assignment's data.

        Args:
            None.

        Returns:
            None.
        """
        from ergotools.domain.assessments.document import AssessmentKind
        from ergotools.presentation.desktop.assessment_context_dialog import (
            AssessmentContextDialog,
        )

        self.seed_historical(include_second=False)
        old = self.workspace.active

        def accept_second(dialog: AssessmentContextDialog) -> int:
            """Select the second exact station leaf and click Use.

            Select the second exact station leaf and click Use, returning the actual
            context dialog result.

            Args:
                dialog: Live modal/form under test; the caller owns its lifetime and
                    event-loop scheduling.

            Returns:
                Actual Qt dialog result after selecting the second exact station leaf
                and clicking Use.
            """
            leaf = dialog.tree.topLevelItem(0).child(0).child(0).child(1)
            dialog.tree.setCurrentItem(leaf)
            dialog.use.click()
            return dialog.result()

        with (
            patch.object(self.window, "choose_item", return_value=("worker", True)),
            patch.object(AssessmentContextDialog, "exec", accept_second),
        ):
            self.window.buttons["new_assessment"].click()
        active = self.workspace.active
        self.assertIsNot(active, old)
        self.assertEqual(active.state.tasks, ())
        self.assertFalse(active.is_dirty)
        with AssessmentProjectFile.open(self.path) as project:
            history = project.load_history()
            created = history.current_for(2, AssessmentKind.LIFFT)
            self.assertEqual(created.document_id, active.document.document_id)
            self.assertEqual(created.assignment_id, 2)
            self.assertFalse(hasattr(created, "version"))
            self.assertEqual(
                history.current_for(1, AssessmentKind.LIFFT).document_id, "1"
            )
        with (
            patch.object(self.window, "choose_item", return_value=("worker", True)),
            patch.object(AssessmentContextDialog, "exec", accept_second),
            self.assertRaises(ValueError),
        ):
            self.window.choose_assessment_context(create=True)
        self.assertIs(self.workspace.active, active)

    def test_first_assessment_dirty_cancel_and_stale_hierarchy(self) -> None:
        """Creation rejects cancelled dirty consent and stale hierarchy callbacks.

        Args:
            None.

        Returns:
            None.
        """
        from ergotools.presentation.desktop.assessment_context_dialog import (
            AssessmentContextDialog,
        )

        self.seed_historical(include_second=False)
        self.type_value("15")
        self.window.apply_edit()
        old = self.workspace.active

        def accept_second(dialog: AssessmentContextDialog) -> int:
            """Select the second exact station leaf and click Use.

            Select the second exact station leaf and click Use, returning the actual
            context dialog result.

            Args:
                dialog: Live modal/form under test; the caller owns its lifetime and
                    event-loop scheduling.

            Returns:
                Actual Qt dialog result after selecting the second exact station leaf
                and clicking Use.
            """
            dialog.tree.setCurrentItem(
                dialog.tree.topLevelItem(0).child(0).child(0).child(1)
            )
            dialog.use.click()
            return dialog.result()

        def change_hierarchy() -> CloseChoice:
            """Refresh saved hierarchy during dirty consent and return Discard.

            Refresh saved hierarchy during dirty consent and return Discard, ensuring
            stale first-assessment intent is rejected.

            Args:
                None.

            Returns:
                Explicit Discard after hierarchy refresh; cannot authorize the prior
                first-assessment request.
            """
            self.workspace.read_hierarchy()
            return CloseChoice.DISCARD

        with (
            patch.object(self.window, "choose_item", return_value=("worker", True)),
            patch.object(AssessmentContextDialog, "exec", accept_second),
        ):
            with patch.object(
                self.window, "dirty_choice", return_value=CloseChoice.CANCEL
            ):
                self.window.choose_assessment_context(create=True)
            with (
                patch.object(self.window, "dirty_choice", side_effect=change_hierarchy),
                self.assertRaises(ValueError),
            ):
                self.window.choose_assessment_context(create=True)
        self.assertIs(self.workspace.active, old)
        self.assertTrue(old.is_dirty)
        with AssessmentProjectFile.open(self.path) as project:
            self.assertEqual(len(project.load_history().entries), 1)
            self.assertEqual(project.load(old.document).tasks[0].lever_arm, 12)
