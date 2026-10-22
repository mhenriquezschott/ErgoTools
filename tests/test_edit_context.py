"""Presenter edit ownership across source, unit, decimal and lifecycle changes.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import unittest
from dataclasses import FrozenInstanceError, replace

from ergotools.application.assessments.lifft_commands import ReplaceLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.edit_context import AssessmentEditor
from ergotools.presentation.localization import Language, Translator
from ergotools.presentation.numeric_input import DecimalConvention


class EditContextTests(unittest.TestCase):
    """Delayed editor callbacks cannot reinterpret text under new preferences."""

    def setUp(self) -> None:
        """Create an imperial assessment displayed as metric with decimal commas.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("p", "a")
        self.task = LifftTask("a", 12, 10, 100)
        self.source = LifftDraft(MeasurementSystem.IMPERIAL, (self.task,))
        self.session = DocumentSession(self.key, self.source, persisted=True)
        self.editor = AssessmentEditor()
        self.context = self.editor.bind(
            self.session, MeasurementSystem.METRIC, DecimalConvention.COMMA
        )

    def test_submit_uses_captured_units_and_convention_then_releases_context(
        self,
    ) -> None:
        """A successful edit is undoable and permanently consumes this context.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(FrozenInstanceError):
            self.context.convention = DecimalConvention.POINT
        self.assertTrue(
            self.editor.submit(self.session, self.context, "a", "load", "22,25")
        )
        self.assertEqual(self.session.state.tasks[0].load, 5)
        self.assertIsNone(self.editor.current(self.session))
        self.session.undo()
        self.assertIs(self.session.state, self.source)
        with self.assertRaises(DraftError):
            self.editor.submit(self.session, self.context, "a", "load", "22,25")
        self.session.redo()
        self.assertEqual(self.session.state.tasks[0].load, 5)

    def test_unit_or_convention_switch_rejects_old_context_even_after_toggle_back(
        self,
    ) -> None:
        """Value-equal preferences cannot revive an editor with obsolete ownership.

        Args:
            None.

        Returns:
            None.
        """
        for system, convention in (
            (MeasurementSystem.IMPERIAL, DecimalConvention.COMMA),
            (MeasurementSystem.METRIC, DecimalConvention.POINT),
            (MeasurementSystem.METRIC, DecimalConvention.COMMA),
        ):
            self.editor.bind(self.session, system, convention)
            with self.assertRaises(DraftError) as caught:
                self.editor.submit(self.session, self.context, "a", "load", "bad")
            self.assertEqual(caught.exception.issue.code, "validation.stale_editor")
            self.assertIs(self.session.state, self.source)
            self.assertFalse(self.session.is_dirty)
        latest = self.editor.current(self.session)
        self.assertTrue(self.editor.submit(self.session, latest, "a", "load", "22,25"))

    def test_other_owner_and_reconstructed_equal_context_are_rejected(self) -> None:
        """Identity guards do not accept dataclass equality as callback authority.

        Args:
            None.

        Returns:
            None.
        """
        other = AssessmentEditor()
        foreign = other.bind(
            self.session, MeasurementSystem.METRIC, DecimalConvention.COMMA
        )
        for context in (foreign, replace(self.context)):
            self.assertEqual(context, self.context)
            with self.assertRaises(DraftError):
                self.editor.submit(self.session, context, "a", "load", "22,25")
        self.assertIs(self.editor.current(self.session), self.context)

    def test_invalid_text_and_noop_retain_context_for_correction(self) -> None:
        """Typing errors neither consume valid context nor clear entered source.

        Args:
            None.

        Returns:
            None.
        """
        for text in ("22.25", "invalid", "1e9999"):
            with self.assertRaises(DraftError):
                self.editor.submit(self.session, self.context, "a", "load", text)
            self.assertIs(self.editor.current(self.session), self.context)
            self.assertIs(self.session.state, self.source)
        self.assertFalse(
            self.editor.submit(self.session, self.context, "a", "load", "44,5")
        )
        self.assertIs(self.editor.current(self.session), self.context)
        self.assertTrue(self.editor.submit(self.session, self.context, "a", "load", ""))
        self.assertIsNone(self.session.state.tasks[0].load)

    def test_clear_close_reload_and_switch_reject_callbacks(self) -> None:
        """Closed or nonactive document contexts fail before parsing incoming text.

        Args:
            None.

        Returns:
            None.
        """
        for active in (
            None,
            DocumentSession(self.key, self.source),
            DocumentSession(DocumentKey("other", "a"), self.source),
        ):
            self.assertIsNone(self.editor.current(active))
            with self.assertRaises(DraftError):
                self.editor.submit(active, self.context, "a", "load", "bad")
        self.editor.clear()
        self.editor.clear()
        self.assertIsNone(self.editor.current(self.session))
        with self.assertRaises(DraftError):
            self.editor.submit(self.session, self.context, "a", "load", "22,25")

    def test_failed_bind_does_not_leave_previous_editor_usable(self) -> None:
        """Failed preference/project changes invalidate old interpretation first.

        Args:
            None.

        Returns:
            None.
        """
        for active, system, convention in (
            (self.session, "metric", DecimalConvention.COMMA),
            (self.session, MeasurementSystem.METRIC, ","),
            (
                DocumentSession(self.key, DuetDraft()),
                MeasurementSystem.METRIC,
                DecimalConvention.COMMA,
            ),
            (
                DocumentSession(
                    self.key,
                    TstDraft(MeasurementSystem.IMPERIAL, (TstTask("a", load=1e308),)),
                ),
                MeasurementSystem.METRIC,
                DecimalConvention.COMMA,
            ),
        ):
            old = self.editor.bind(
                self.session, MeasurementSystem.METRIC, DecimalConvention.COMMA
            )
            with self.assertRaises(ValueError):
                self.editor.bind(active, system, convention)
            self.assertIsNone(self.editor.current(self.session))
            with self.assertRaises(DraftError):
                self.editor.submit(self.session, old, "a", "load", "22,25")
        self.assertIs(self.session.state, self.source)

    def test_external_edits_stale_source_and_refresh_invalidates_undo_revival(
        self,
    ) -> None:
        """Rebinding after an external edit prevents callbacks from older renders.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(
            LifftProjectEdit(
                ReplaceLifftTask(self.key, self.task, replace(self.task, load=20))
            )
        )
        self.assertIsNone(self.editor.current(self.session))
        with self.assertRaises(DraftError):
            self.editor.submit(self.session, self.context, "a", "load", "22,25")
        new = self.editor.bind(
            self.session, MeasurementSystem.METRIC, DecimalConvention.COMMA
        )
        self.session.undo()
        self.assertIsNone(self.editor.current(self.session))
        for context in (self.context, new):
            with self.assertRaises(DraftError):
                self.editor.submit(self.session, context, "a", "load", "22,25")

    def test_tst_and_independent_presenters_keep_units_and_history_separate(
        self,
    ) -> None:
        """Two owners do not share preferences, documents or mutable input state.

        Args:
            None.

        Returns:
            None.
        """
        source = TstDraft(
            MeasurementSystem.METRIC,
            (TstTask("a", TstDirection.HORIZONTAL, 30.48, 44.5, 100),),
        )
        session = DocumentSession(self.key, source, persisted=True)
        other = AssessmentEditor()
        context = other.bind(
            session, MeasurementSystem.IMPERIAL, DecimalConvention.POINT
        )
        self.assertTrue(other.submit(session, context, "a", "load", "22.25"))
        self.assertEqual(session.state.tasks[0].load, 22.25 * 4.45)
        self.assertIs(session.state.tasks[0].direction, TstDirection.HORIZONTAL)
        self.assertIs(session.state.system, MeasurementSystem.METRIC)
        self.assertIs(self.editor.current(self.session), self.context)
        self.assertIs(self.session.state, self.source)
        for language in Language:
            self.assertTrue(Translator(language).text("validation.stale_editor"))
