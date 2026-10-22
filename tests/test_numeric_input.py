"""Explicit decimal parsing and text edits with exact source/history preservation.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import math
import tempfile
import unittest
from pathlib import Path

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.assessments.unit_view import prepare_unit_view
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.presentation.assessment_input import edit_display_text
from ergotools.presentation.localization import Language, Translator
from ergotools.presentation.numeric_input import (
    DecimalConvention,
    format_input_number,
    parse_input_number,
)


class NumericInputTests(unittest.TestCase):
    """Keep language, decimal convention and source/display units independent."""

    def test_complete_decimal_grammar_and_missing_values(self) -> None:
        """Accept signed decimals and exponents; blank is absent rather than zero.

        Args:
            None.

        Returns:
            None.
        """
        cases = {
            "": None,
            " \t\n": None,
            "0": 0,
            "+12": 12,
            "-12": -12,
            "1.25": 1.25,
            ".5": 0.5,
            "1.": 1.0,
            "-.5": -0.5,
            "  +1.25e2  ": 125.0,
            "1E-3": 0.001,
            "0e9999": 0.0,
            "1e308": 1e308,
            "5e-324": 5e-324,
        }
        for convention in DecimalConvention:
            for text, expected in cases.items():
                actual = parse_input_number(
                    text.replace(".", convention.value), convention, "load", "a"
                )
                self.assertEqual(actual, expected)
            self.assertEqual(
                parse_input_number(
                    "1" + convention.value + "234", convention, "load", "a"
                ),
                1.234,
            )

    def test_ambiguous_grouped_partial_and_non_ascii_inputs_are_rejected(self) -> None:
        """Never strip grouping or silently guess another decimal convention.

        Args:
            None.

        Returns:
            None.
        """
        common = [
            "1,234.5",
            "1.234,5",
            "1 234",
            "1\u00a0234",
            "1_234",
            "1\t2",
            "+",
            "-",
            ".",
            ",",
            "1e",
            "1e+",
            "--1",
            "NaN",
            "inf",
            "-Infinity",
            "12 N",
            "1/2",
            "\uff11\uff12",
            "\u0661\u0662",
            "\u22121",
            "0x10",
            "1\n2",
            "9" * 257,
        ]
        for convention in DecimalConvention:
            other = "1,25" if convention is DecimalConvention.POINT else "1.25"
            for text in (*common, other):
                with (
                    self.subTest(text=text, convention=convention),
                    self.assertRaises(DraftError) as caught,
                ):
                    parse_input_number(text, convention, "lever_arm", "row")
                self.assertEqual(caught.exception.issue.code, "validation.number")
                self.assertEqual(caught.exception.issue.field, "lever_arm")
                self.assertEqual(caught.exception.issue.task_id, "row")
        with self.assertRaises(DraftError):
            parse_input_number(True, DecimalConvention.POINT, "load", "a")

    def test_overflow_and_nonzero_underflow_do_not_become_valid_values(self) -> None:
        """Reject nonrepresentable floats; exact decimal zero remains a valid zero.

        Args:
            None.

        Returns:
            None.
        """
        for convention in DecimalConvention:
            for token in ("1e309", "-1e309", "1e-9999", "-1e-9999", "0.1e-9999"):
                with self.assertRaises(DraftError) as caught:
                    parse_input_number(
                        token.replace(".", convention.value), convention, "load", "a"
                    )
                self.assertEqual(caught.exception.issue.code, "validation.overflow")
            self.assertEqual(parse_input_number("-0e-9999", convention, "load", "a"), 0)

    def test_edit_format_roundtrips_precision_and_negative_zero(self) -> None:
        """Editor text preserves supported float/int values without display rounding.

        Args:
            None.

        Returns:
            None.
        """
        values = [
            None,
            0,
            -0.0,
            2**54 + 1,
            -(2**54 + 1),
            10**255,
            1.2345678901234567,
            math.nextafter(1.0, 2.0),
            1e308,
            5e-324,
            -5e-324,
        ]
        for convention in DecimalConvention:
            for value in values:
                text = format_input_number(value, convention)
                parsed = parse_input_number(text, convention, "load", "a")
                self.assertEqual(parsed, value)
                if isinstance(value, int):
                    self.assertIsInstance(parsed, int)
                if isinstance(value, float):
                    self.assertEqual(math.copysign(1, parsed), math.copysign(1, value))

    def test_unsupported_conventions_and_bad_editor_values_fail(self) -> None:
        """Configuration failures never silently fall back to OS or language locale.

        Args:
            None.

        Returns:
            None.
        """
        for value in (True, "1", float("nan"), float("inf"), 10**400, 10**256):
            with self.assertRaises(ValueError):
                format_input_number(value, DecimalConvention.POINT)
        for convention in (".", ",", None, "en_US"):
            with self.assertRaises(ValueError):
                parse_input_number("1", convention, "load", "a")
            with self.assertRaises(ValueError):
                format_input_number(None, convention)

    def test_text_edits_across_models_units_conventions_and_languages(self) -> None:
        """The same explicit text convention works with either UI language/units.

        Args:
            None.

        Returns:
            None.
        """
        key = DocumentKey("p", "assessment")
        for system in MeasurementSystem:
            for target in MeasurementSystem:
                for convention in DecimalConvention:
                    for language in Language:
                        for source in (
                            LifftDraft(system, (LifftTask("a", 12.345, 10, 100),)),
                            TstDraft(
                                system,
                                (TstTask("a", TstDirection.DOWNWARD, 12.345, 10, 100),),
                            ),
                        ):
                            session = DocumentSession(key, source, persisted=True)
                            view = prepare_unit_view(session, target)
                            self.assertTrue(
                                edit_display_text(
                                    session,
                                    view,
                                    "a",
                                    "load",
                                    "22" + convention.value + "25",
                                    convention,
                                )
                            )
                            expected = (
                                22.25
                                if system is target
                                else (
                                    5
                                    if target is MeasurementSystem.METRIC
                                    else 22.25 * 4.45
                                )
                            )
                            self.assertEqual(session.state.tasks[0].load, expected)
                            self.assertEqual(session.state.tasks[0].lever_arm, 12.345)
                            self.assertTrue(
                                Translator(language).text(session.undo_label_key)
                            )
                            session.undo()
                            self.assertIs(session.state, source)
                            self.assertFalse(session.is_dirty)
                            session.redo()
                            self.assertEqual(session.state.tasks[0].load, expected)

    def test_invalid_text_preserves_source_result_and_redo(self) -> None:
        """Bad text cannot clear source, dirty a session or discard cached results.

        Args:
            None.

        Returns:
            None.
        """
        key = DocumentKey("p", "a")
        source = LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("a", 12, 10, 100),))
        session = DocumentSession(key, source, persisted=True)
        view = prepare_unit_view(session, MeasurementSystem.IMPERIAL)
        edit_display_text(session, view, "a", "load", "20", DecimalConvention.POINT)
        session.undo()
        evaluator = AssessmentEvaluator()
        result = evaluator.evaluate(session)
        redo = session.redo_label_key
        for text in ("1,2", "-", "NaN", "1e9999", "1 234"):
            with self.assertRaises(DraftError):
                edit_display_text(
                    session, view, "a", "load", text, DecimalConvention.POINT
                )
            self.assertIs(session.state, source)
            self.assertFalse(session.is_dirty)
            self.assertEqual(session.redo_label_key, redo)
            self.assertIs(evaluator.current(session), result)
        self.assertFalse(
            edit_display_text(
                session, view, "a", "load", "10.0", DecimalConvention.POINT
            )
        )
        self.assertEqual(session.redo_label_key, redo)
        self.assertTrue(
            edit_display_text(session, view, "a", "load", " ", DecimalConvention.COMMA)
        )
        self.assertIsNone(session.state.tasks[0].load)
        self.assertIsNone(evaluator.current(session))
        self.assertEqual(
            evaluator.evaluate(session).status, EvaluationStatus.INVALID_INPUT
        )

    def test_stale_source_takes_precedence_over_malformed_text(self) -> None:
        """An obsolete editor cannot parse its way into a different source revision.

        Args:
            None.

        Returns:
            None.
        """
        key = DocumentKey("p", "a")
        source = LifftDraft(MeasurementSystem.IMPERIAL, (LifftTask("a", 1, 1, 1),))
        session = DocumentSession(key, source)
        view = prepare_unit_view(session, MeasurementSystem.METRIC)
        edit_display_text(session, view, "a", "load", "44,5", DecimalConvention.COMMA)
        with self.assertRaises(DraftError) as caught:
            edit_display_text(
                session, view, "a", "load", "bad", DecimalConvention.COMMA
            )
        self.assertEqual(caught.exception.issue.code, "validation.stale_view")
        self.assertEqual(session.state.tasks[0].load, 10)

    def test_formatted_projection_reentry_is_exact_noop(self) -> None:
        """Full-precision editor initialization cannot introduce conversion drift.

        Args:
            None.

        Returns:
            None.
        """
        source = LifftDraft(
            MeasurementSystem.IMPERIAL,
            (LifftTask("a", 12.3456789012345, 2**54 + 1, 100),),
        )
        session = DocumentSession(DocumentKey("p", "a"), source, persisted=True)
        for target in MeasurementSystem:
            for convention in DecimalConvention:
                view = prepare_unit_view(session, target)
                for field in ("lever_arm", "load"):
                    text = format_input_number(
                        getattr(view.tasks[0], field), convention
                    )
                    self.assertFalse(
                        edit_display_text(session, view, "a", field, text, convention)
                    )
                    self.assertIs(session.state, source)
                    self.assertFalse(session.is_dirty)

    def test_comma_edit_saves_and_evaluates_recorded_units(
        self,
    ) -> None:
        """Locale text never leaks into persistence or changes recorded source units.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "numeric.sqlite"
            key = DocumentKey("p", "a")
            source = LifftDraft(
                MeasurementSystem.METRIC, (LifftTask("a", 30.48, 44.5, 100),)
            )
            session = DocumentSession(key, source, persisted=True)
            edit_display_text(
                session,
                prepare_unit_view(session, MeasurementSystem.IMPERIAL),
                "a",
                "load",
                "22,25",
                DecimalConvention.COMMA,
            )
            with AssessmentProjectFile.create(
                path, ProjectMetadata("p", "Input", MeasurementSystem.IMPERIAL)
            ) as project:
                session.save(project)
            with AssessmentProjectFile.open(path) as project:
                loaded = project.load(key)
                self.assertEqual(loaded.tasks[0].load, 22.25 * 4.45)
                self.assertEqual(loaded.system, MeasurementSystem.METRIC)
                self.assertEqual(
                    AssessmentEvaluator().evaluate(DocumentSession(key, loaded)).status,
                    EvaluationStatus.COMPLETE,
                )
