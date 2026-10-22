"""Preserve source precision, exposure, history and review gates during unit display.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
)
from ergotools.application.assessments.lifft_commands import ReplaceLifftTask
from ergotools.application.assessments.project_edits import LifftProjectEdit
from ergotools.application.assessments.unit_view import prepare_unit_view
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import (
    MeasurementSystem,
    normalize_model_load,
    project_model_input,
)
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_serialization import encode_assessment


class UnitViewTests(unittest.TestCase):
    """Unit projections are read-only; conversion never silently reinterprets source."""

    def setUp(self) -> None:
        """Create a source with unrounded decimal inputs.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("p", "lifft")
        self.task = LifftTask("a", 12.3456789012345, 10.987654321, 100.25)
        self.draft = LifftDraft(MeasurementSystem.IMPERIAL, (self.task,))
        self.session = DocumentSession(self.key, self.draft, persisted=True)

    def test_reference_menu_only_relabels_unchanged_source(self) -> None:
        """Record the approved workflow correction against 24 actual-method captures.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/unit_switch_reference.json").read_text()
        )
        self.assertEqual(len(fixture["records"]), 24)
        self.assertEqual(fixture["reference_python"], "3.10.18")
        for record in fixture["records"]:
            self.assertEqual(record["input_texts"], ["12.345", "10", "27", "22.25"])
            self.assertEqual(record["lifft_recorded"], record["lifft_source"])
            self.assertEqual(record["tst_recorded"], record["tst_source"])
            self.assertEqual(record["selected"], record["target"])
            metric = record["target"] == "Metric"
            self.assertEqual(
                record["lifft_headers"][1],
                "Lever Arm (cm)" if metric else "Lever Arm (in)",
            )
            self.assertEqual(
                record["tst_headers"][3], "Load (N)" if metric else "Load (lb)"
            )

    def test_model_normalization_vectors_match_metric_projection(self) -> None:
        """Retain all 48 previously captured normalization vectors and constants.

        Args:
            None.

        Returns:
            None.
        """
        fixture = json.loads(
            (Path(__file__).parent / "fixtures/model_units_reference.json").read_text()
        )
        for record in fixture["records"]:
            system = MeasurementSystem(record["system"])
            self.assertEqual(
                project_model_input(
                    record["lever_arm"],
                    "lever_arm",
                    "a",
                    system,
                    MeasurementSystem.IMPERIAL,
                ),
                record["lever_arm_in"],
            )
            self.assertEqual(
                project_model_input(
                    record["load"], "load", "a", system, MeasurementSystem.IMPERIAL
                ),
                record["load_lbf"],
            )
        self.assertEqual(
            project_model_input(
                1, "load", "a", MeasurementSystem.IMPERIAL, MeasurementSystem.METRIC
            ),
            4.45,
        )
        self.assertEqual(
            project_model_input(
                1,
                "lever_arm",
                "a",
                MeasurementSystem.IMPERIAL,
                MeasurementSystem.METRIC,
            ),
            2.54,
        )

    def test_repeated_switches_keep_source_results_clean_marker_and_bytes_exact(
        self,
    ) -> None:
        """No float round-trip is applied to source; all toggles reproject originals.

        Args:
            None.

        Returns:
            None.
        """
        evaluator = AssessmentEvaluator()
        evaluated = evaluator.evaluate(self.session)
        before = encode_assessment(self.draft)
        for _ in range(50):
            metric = prepare_unit_view(self.session, MeasurementSystem.METRIC)
            imperial = prepare_unit_view(self.session, MeasurementSystem.IMPERIAL)
            self.assertEqual(metric.tasks[0].lever_arm, self.task.lever_arm * 2.54)
            self.assertEqual(metric.tasks[0].load, self.task.load * 4.45)
            self.assertEqual(imperial.tasks[0].lever_arm, self.task.lever_arm)
            self.assertEqual(imperial.tasks[0].load, self.task.load)
            self.assertIs(self.session.state, self.draft)
            self.assertFalse(self.session.is_dirty)
            self.assertEqual(self.session.revision, 0)
            self.assertIsNone(self.session.undo_label_key)
            self.assertIs(evaluator.current(self.session), evaluated)
            self.assertEqual(encode_assessment(self.session.state), before)
        self.assertEqual(evaluator.evaluate(self.session).summary, evaluated.summary)
        with self.assertRaises(FrozenInstanceError):
            metric.system = MeasurementSystem.IMPERIAL

    def test_tst_directions_missing_signed_and_repetitions_survive(self) -> None:
        """Display projection does not require complete physically valid task rows.

        Args:
            None.

        Returns:
            None.
        """
        for system in MeasurementSystem:
            source = TstDraft(
                system,
                tuple(
                    TstTask(str(i), direction, -1, None, 0.25)
                    for i, direction in enumerate(TstDirection)
                ),
            )
            session = DocumentSession(self.key, source)
            for target in MeasurementSystem:
                view = prepare_unit_view(session, target)
                self.assertEqual([t.direction for t in view.tasks], list(TstDirection))
                self.assertTrue(
                    all(
                        t.lever_arm < 0 and t.load is None and t.repetitions == 0.25
                        for t in view.tasks
                    )
                )
                self.assertTrue(view.preparation.issues)
                self.assertTrue(view.is_current(session))
        view = prepare_unit_view(
            DocumentSession(self.key, LifftDraft(MeasurementSystem.METRIC)),
            MeasurementSystem.IMPERIAL,
        )
        self.assertEqual(view.tasks, ())

    def test_metric_source_projection_does_not_reinterpret_calculation_units(
        self,
    ) -> None:
        """Imperial display leaves the metric source and calculated result unchanged.

        Args:
            None.

        Returns:
            None.
        """
        source = TstDraft(
            MeasurementSystem.METRIC,
            (TstTask("a", TstDirection.DOWNWARD, 12, 10, 100),),
        )
        session = DocumentSession(self.key, source)
        evaluator = AssessmentEvaluator()
        before = evaluator.evaluate(session)
        prepare_unit_view(session, MeasurementSystem.IMPERIAL)
        after = evaluator.evaluate(session)
        self.assertEqual(before.summary, after.summary)
        self.assertIs(session.state, source)
        self.assertEqual(after.status, EvaluationStatus.COMPLETE)

    def test_edit_undo_redo_and_reload_freshness(self) -> None:
        """Projections obey history identity and never survive equal-valued reloads.

        Args:
            None.

        Returns:
            None.
        """
        view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
        changed = replace(self.task, load=5)
        self.session.execute(
            LifftProjectEdit(ReplaceLifftTask(self.key, self.task, changed))
        )
        self.assertFalse(view.is_current(self.session))
        self.assertEqual(
            prepare_unit_view(self.session, MeasurementSystem.METRIC).tasks[0].load,
            22.25,
        )
        self.session.undo()
        self.assertTrue(view.is_current(self.session))
        self.session.redo()
        self.assertFalse(view.is_current(self.session))
        self.assertFalse(view.is_current(DocumentSession(self.key, self.draft)))
        self.assertFalse(view.is_current(None))

    def test_save_reopen_keeps_original_units_and_project_defaults(self) -> None:
        """Only source is persisted, regardless of current display or project units.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "units.sqlite"
            metadata = ProjectMetadata("p", "Units", MeasurementSystem.METRIC)
            view = prepare_unit_view(self.session, MeasurementSystem.METRIC)
            with AssessmentProjectFile.create(path, metadata) as project:
                self.session.save(project)
                self.assertTrue(view.is_current(self.session))
            with AssessmentProjectFile.open(path) as project:
                loaded = project.load(self.key)
                self.assertEqual(loaded, self.draft)
                self.assertEqual(loaded.system, MeasurementSystem.IMPERIAL)
                self.assertEqual(
                    project.metadata.default_units, MeasurementSystem.METRIC
                )
                reopened = DocumentSession(self.key, loaded, persisted=True)
                self.assertEqual(
                    prepare_unit_view(reopened, MeasurementSystem.METRIC).tasks,
                    view.tasks,
                )
                self.assertFalse(view.is_current(reopened))

    def test_invalid_inputs_and_conversion_overflow_are_atomic(self) -> None:
        """Reject unsafe numbers without partial display rows or changed history.

        Args:
            None.

        Returns:
            None.
        """
        for value, code in (
            (True, "validation.number"),
            ("1", "validation.number"),
            (float("nan"), "validation.nonfinite"),
            (float("inf"), "validation.nonfinite"),
            (10**400, "validation.overflow"),
            (1e308, "validation.overflow"),
        ):
            source = TstDraft(
                MeasurementSystem.IMPERIAL,
                (TstTask("good", load=1), TstTask("bad", load=value)),
            )
            session = DocumentSession(self.key, source, persisted=True)
            with self.assertRaises(DraftError) as caught:
                prepare_unit_view(session, MeasurementSystem.METRIC)
            self.assertEqual(caught.exception.issue.code, code)
            self.assertEqual(caught.exception.issue.task_id, "bad")
            self.assertIs(session.state, source)
            self.assertFalse(session.is_dirty)

    def test_unsupported_units_quantities_and_unitless_models_fail(self) -> None:
        """No guessed units and no force conversion applied to DUET scales.

        Args:
            None.

        Returns:
            None.
        """
        for source, target, field in (
            ("metric", MeasurementSystem.IMPERIAL, "load"),
            (MeasurementSystem.METRIC, "imperial", "load"),
            (MeasurementSystem.METRIC, MeasurementSystem.IMPERIAL, "mass"),
        ):
            with self.assertRaises(ValueError):
                project_model_input(None, field, "a", source, target)
        with self.assertRaises(ValueError):
            prepare_unit_view(self.session, "metric")
        with self.assertRaises(ValueError):
            prepare_unit_view(
                DocumentSession(self.key, DuetDraft()), MeasurementSystem.METRIC
            )

    def test_same_units_preserve_large_integer_and_zero(self) -> None:
        """Avoid unnecessary float coercion or rounding when units already match.

        Args:
            None.

        Returns:
            None.
        """
        for value in (2**54 + 1, 0, -0.0, None):
            for system in MeasurementSystem:
                self.assertIs(
                    project_model_input(value, "load", "a", system, system), value
                )
        normalized = normalize_model_load(2.54, 4.45, MeasurementSystem.METRIC)
        self.assertEqual((normalized.lever_arm_in, normalized.load_lbf), (1, 1))

    def test_nonzero_conversion_underflow_is_not_displayed_as_zero(self) -> None:
        """An unrepresentable projected exposure is an error, not a plausible zero.

        Args:
            None.

        Returns:
            None.
        """
        for value in (5e-324, -5e-324):
            with self.assertRaises(DraftError) as caught:
                project_model_input(
                    value,
                    "load",
                    "a",
                    MeasurementSystem.METRIC,
                    MeasurementSystem.IMPERIAL,
                )
            self.assertEqual(caught.exception.issue.code, "validation.overflow")
