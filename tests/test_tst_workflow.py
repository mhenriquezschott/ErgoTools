"""TST source history, strict persistence and mixed-project review gates.

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
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
    EvaluationStatus,
    prepare_assessment,
)
from ergotools.application.assessments.project_edits import TstProjectEdit
from ergotools.application.assessments.tst_commands import (
    AddTstTask,
    RemoveTstTask,
    ReplaceTstTask,
)
from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.document import AssessmentKind, assessment_kind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft, tst_draft_issues
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from ergotools.infrastructure.assessment_store import AssessmentSqliteStore
from ergotools.infrastructure.draft_json import DocumentFormatError
from ergotools.infrastructure.draft_store import DocumentExistsError, StoreFormatError
from ergotools.infrastructure.project_file import ProjectFile
from ergotools.infrastructure.settings_store import JsonSettingsStore
from ergotools.infrastructure.tst_serialization import decode_tst, encode_tst
from ergotools.presentation.localization import Language, Translator


class TstWorkflowTests(unittest.TestCase):
    """Use temporary databases only; no original application or operational data."""

    def setUp(self) -> None:
        """Prepare a valid imperial source with explicit model direction.

        Args:
            None.

        Returns:
            None.
        """
        self.key = DocumentKey("p", "tst")
        self.task = TstTask("a", TstDirection.DOWNWARD, 12, 10, 100)
        self.draft = TstDraft(MeasurementSystem.IMPERIAL, (self.task,))
        self.session = DocumentSession(self.key, self.draft, persisted=True)

    def test_snapshot_units_and_identity_guards(self) -> None:
        """Mutable input collections cannot change history; bad identities fail.

        Args:
            None.

        Returns:
            None.
        """
        tasks = [self.task]
        draft = TstDraft(MeasurementSystem.METRIC, tasks)
        tasks.clear()
        self.assertEqual(draft.tasks, (self.task,))
        self.assertEqual(draft.task_index("a"), 0)
        self.assertEqual(assessment_kind(draft), AssessmentKind.TST)
        with self.assertRaises(FrozenInstanceError):
            draft.system = MeasurementSystem.IMPERIAL
        for action, code in (
            (lambda: TstDraft("metric"), "validation.unit"),
            (
                lambda: replace(draft, tasks=(self.task, self.task)),
                "validation.duplicate",
            ),
            (lambda: draft.task_index("absent"), "validation.missing_task"),
        ):
            with self.assertRaises(DraftError) as caught:
                action()
            self.assertEqual(caught.exception.issue.code, code)

    def test_all_input_issues_preserve_row_and_field_order(self) -> None:
        """Preparation reports all invalid fields without substituting zero.

        Args:
            None.

        Returns:
            None.
        """
        source = TstDraft(
            MeasurementSystem.METRIC,
            (TstTask("missing"), TstTask("invalid", "1", -1, True, float("inf"))),
        )
        issues = tst_draft_issues(source)
        self.assertEqual(len(issues), 8)
        self.assertEqual(
            [(i.task_id, i.field) for i in issues],
            [
                (row, field)
                for row in ("missing", "invalid")
                for field in ("direction", "lever_arm", "load", "repetitions")
            ],
        )
        self.assertEqual(tst_draft_issues(self.draft), ())
        self.assertEqual(
            tst_draft_issues(TstDraft(MeasurementSystem.IMPERIAL))[0].code,
            "validation.tasks_required",
        )
        outcome = AssessmentEvaluator().evaluate(DocumentSession(self.key, source))
        self.assertEqual(outcome.status, EvaluationStatus.INVALID_INPUT)
        self.assertEqual(outcome.issues, issues)
        self.assertEqual(outcome.task_results, ())
        self.assertIsNone(outcome.summary)

    def test_edits_undo_redo_and_preparation_freshness(self) -> None:
        """One atomic replacement restores exact source and direction on undo.

        Args:
            None.

        Returns:
            None.
        """
        prepared = prepare_assessment(self.session)
        replacement = replace(self.task, direction=TstDirection.HORIZONTAL, load=20)
        self.session.execute(
            TstProjectEdit(ReplaceTstTask(self.key, self.task, replacement))
        )
        self.assertEqual(self.session.state.tasks, (replacement,))
        self.assertFalse(prepared.is_current(self.session))
        self.assertTrue(self.session.is_dirty)
        self.session.undo()
        self.assertIs(self.session.state, self.draft)
        self.assertTrue(prepared.is_current(self.session))
        self.assertFalse(self.session.is_dirty)
        self.session.redo()
        self.session.execute(TstProjectEdit(AddTstTask(self.key, TstTask("b"), 0)))
        self.assertEqual([t.task_id for t in self.session.state.tasks], ["b", "a"])
        self.session.execute(TstProjectEdit(RemoveTstTask(self.key, replacement)))
        self.assertEqual(self.session.state.tasks, (TstTask("b"),))
        self.session.undo()
        self.assertEqual(self.session.state.tasks, (TstTask("b"), replacement))
        for language in Language:
            for command in (AddTstTask, ReplaceTstTask, RemoveTstTask):
                self.assertTrue(Translator(language).text(command.label_key))

    def test_rejected_commands_preserve_source_revision_and_redo(self) -> None:
        """Stale, foreign and wrong-model edits never enter the history.

        Args:
            None.

        Returns:
            None.
        """
        self.session.execute(AddTstTask(self.key, TstTask("b"), 1))
        self.session.undo()
        for command in (
            AddTstTask(self.key, TstTask("b"), -1),
            AddTstTask(self.key, self.task, 1),
            ReplaceTstTask(self.key, replace(self.task, load=99), self.task),
            ReplaceTstTask(self.key, self.task, replace(self.task, task_id="other")),
            RemoveTstTask(self.key, TstTask("absent")),
            AddTstTask(DocumentKey("other", "tst"), TstTask("c"), 0),
        ):
            with self.assertRaises(ValueError):
                self.session.execute(command)
            self.assertIs(self.session.state, self.draft)
            self.assertEqual(self.session.revision, 0)
            self.assertIsNotNone(self.session.redo_label_key)
        for source in (DuetDraft(), LifftDraft(MeasurementSystem.METRIC)):
            with self.assertRaisesRegex(ValueError, "TST edit requires"):
                TstProjectEdit(AddTstTask(self.key, TstTask("b"), 0)).apply(source)

    def test_codec_roundtrips_model_ids_units_missing_and_signed_source(self) -> None:
        """Model IDs never pass through the legacy swapped UI-selector adapter.

        Args:
            None.

        Returns:
            None.
        """
        for system in MeasurementSystem:
            tasks = (
                *(
                    TstTask(str(i), direction, -1.25, 2**54 + 1, 0.5)
                    for i, direction in enumerate(TstDirection)
                ),
                TstTask("blank"),
            )
            draft = TstDraft(system, tasks)
            payload = encode_tst(draft)
            self.assertEqual(decode_tst(payload), draft)
            self.assertEqual(encode_tst(decode_tst(payload)), payload)
            self.assertEqual(decode_assessment(encode_assessment(draft)), draft)
            self.assertEqual(
                [t["direction"] for t in json.loads(payload)["tasks"]],
                ["0", "1", "2", None],
            )
        self.assertEqual(decode_tst(encode_tst(TstDraft(system))), TstDraft(system))

    def test_codec_rejects_bad_headers_members_and_versions(self) -> None:
        """Unknown or ambiguous payloads fail as a whole with no guessed defaults.

        Args:
            None.

        Returns:
            None.
        """
        base = json.loads(encode_tst(self.draft))
        for changes in (
            {"format": "ergotools.lifft-draft"},
            {"version": True},
            {"version": 2},
            {"system": "unknown"},
            {"tasks": {}},
            {"unexpected": 1},
        ):
            with self.assertRaises(DocumentFormatError):
                decode_tst(json.dumps({**base, **changes}))
        for payload in (
            "{}",
            "[]",
            "not json",
            '{"version":1,"version":1}',
            "[" * 1100 + "0" + "]" * 1100,
        ):
            with self.assertRaises(DocumentFormatError):
                decode_tst(payload)
        envelope = json.loads(encode_assessment(self.draft))
        envelope["kind"] = "duet"
        with self.assertRaises(DocumentFormatError):
            decode_assessment(json.dumps(envelope))

    def test_codec_rejects_bad_rows_directions_and_numeric_values(self) -> None:
        """Reject UI indices, booleans and nonfinite values before any storage write.

        Args:
            None.

        Returns:
            None.
        """
        base = json.loads(encode_tst(self.draft))
        row = base["tasks"][0]
        cases = [None, {}, {**row, "extra": 1}, {**row, "task_id": " "}]
        for field, values in {
            "direction": [0, 1, 2, True, "3", "DOWNWARD", []],
            "lever_arm": [True, "1", float("nan"), float("inf"), 10**400],
            "load": [False, "2", float("-inf")],
            "repetitions": [True, [], float("nan")],
        }.items():
            cases.extend({**row, field: value} for value in values)
        for row_case in cases:
            with self.subTest(row=row_case), self.assertRaises(DocumentFormatError):
                decode_tst(json.dumps({**base, "tasks": [row_case]}))
        with self.assertRaises(DocumentFormatError):
            decode_tst(json.dumps({**base, "tasks": [row, row]}))
        for invalid in (
            replace(self.task, direction="1"),
            replace(self.task, load=float("nan")),
            replace(self.task, repetitions=True),
        ):
            with self.assertRaises(ValueError):
                encode_tst(replace(self.draft, tasks=(invalid,)))

    def test_valid_tst_evaluates_and_numeric_failure_is_atomic(self) -> None:
        """All directions/units work; overflow never produces a partial summary.

        Args:
            None.

        Returns:
            None.
        """
        evaluator = AssessmentEvaluator()
        for system in MeasurementSystem:
            for direction in TstDirection:
                for load in (0, 10, 1e300):
                    source = TstDraft(
                        system, (replace(self.task, direction=direction, load=load),)
                    )
                    session = DocumentSession(self.key, source)
                    outcome = evaluator.evaluate(session)
                    if load == 1e300:
                        self.assertEqual(
                            outcome.status, EvaluationStatus.CALCULATION_FAILED
                        )
                        self.assertIsNone(outcome.summary)
                        self.assertEqual(outcome.task_results, ())
                    else:
                        self.assertEqual(outcome.status, EvaluationStatus.COMPLETE)
                        self.assertIsNotNone(outcome.summary)
                    self.assertIs(session.state, source)

    def test_review_replaces_previous_result_and_obeys_freshness(self) -> None:
        """Switching to TST cannot expose a prior DUET result; edits stale the gate.

        Args:
            None.

        Returns:
            None.
        """
        evaluator = AssessmentEvaluator()
        duet = DocumentSession(self.key, DuetDraft((DuetTask("a", 3, 100),)))
        self.assertEqual(evaluator.evaluate(duet).status, EvaluationStatus.COMPLETE)
        review = evaluator.evaluate(self.session)
        self.assertIs(evaluator.current(self.session), review)
        self.assertIsNone(evaluator.current(duet))
        self.session.execute(TstProjectEdit(AddTstTask(self.key, TstTask("b"), 1)))
        self.assertIsNone(evaluator.current(self.session))
        self.session.undo()
        self.assertIs(evaluator.current(self.session), review)
        self.assertIsNone(evaluator.current(DocumentSession(self.key, self.draft)))

    def test_real_sql_failure_preserves_previous_source_and_retry(self) -> None:
        """An aborted transaction never marks edited TST source clean.

        Args:
            None.

        Returns:
            None.
        """
        with closing(sqlite3.connect(":memory:")) as connection:
            store = AssessmentSqliteStore.create(connection)
            self.session.save(store)
            self.session.execute(AddTstTask(self.key, TstTask("b"), 1))
            connection.execute(
                "CREATE TRIGGER reject_update BEFORE UPDATE ON draft_documents "
                "BEGIN SELECT RAISE(ABORT, 'test failure'); END"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                self.session.save(store)
            self.assertTrue(self.session.is_dirty)
            self.assertFalse(connection.in_transaction)
            self.assertEqual(store.load(self.key), self.draft)
            connection.execute("DROP TRIGGER reject_update")
            self.session.save(store)
            self.assertFalse(self.session.is_dirty)
            self.assertEqual(store.load(self.key), self.session.state)

    def test_three_models_reopen_with_type_and_duplicate_protection(self) -> None:
        """A TST document coexists with both prior models without changing identity.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.sqlite"
            meta = ProjectMetadata("p", "Mixed", MeasurementSystem.METRIC)
            sources = {
                "tst": self.draft,
                "duet": DuetDraft(),
                "lifft": LifftDraft(MeasurementSystem.METRIC),
            }
            with AssessmentProjectFile.create_with_document(
                path, meta, "tst", self.draft
            ) as project:
                for name in ("duet", "lifft"):
                    project.insert_assessment(DocumentKey("p", name), sources[name])
                for name, source in sources.items():
                    key = DocumentKey("p", name)
                    with self.assertRaises(DocumentExistsError):
                        project.insert_assessment(key, self.draft)
                    for other in sources.values():
                        if type(other) is not type(source):
                            with self.assertRaises(StoreFormatError):
                                project.save(key, other)
            with AssessmentProjectFile.open(path) as project:
                self.assertEqual(project.format_version, 2)
                for name, source in sources.items():
                    self.assertEqual(project.load(DocumentKey("p", name)), source)
                self.assertEqual(
                    [e.kind for e in project.list_assessments()],
                    [AssessmentKind.DUET, AssessmentKind.LIFFT, AssessmentKind.TST],
                )

    def test_version_one_rejects_tst_without_migration(self) -> None:
        """Old LiFFT-only project metadata and documents remain intact.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v1.sqlite"
            meta = ProjectMetadata("p", "Old", MeasurementSystem.IMPERIAL)
            source = LifftDraft(MeasurementSystem.IMPERIAL)
            with ProjectFile.create_with_document(path, meta, "lifft", source):
                pass
            with AssessmentProjectFile.open(path) as project:
                for action in (project.save, project.insert_assessment):
                    with self.assertRaises(StoreFormatError):
                        action(self.key, self.draft)
                self.assertEqual(project.format_version, 1)
                self.assertEqual(project.load(DocumentKey("p", "lifft")), source)

    def test_workspace_create_edit_save_switch_and_reopen(self) -> None:
        """New TST source uses the real catalog/workspace and retains saved edits.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workspace.sqlite"
            meta = ProjectMetadata("p", "Workspace", MeasurementSystem.METRIC)
            with AssessmentProjectFile.create_with_document(
                path, meta, "duet", DuetDraft()
            ):
                pass
            workspace = ProjectWorkspace(
                lambda location: AssessmentProjectFile.open(Path(location)),
                JsonSettingsStore(path.parent / "settings.json"),
            )
            try:
                workspace.switch(str(path), "duet")
                self.assertTrue(
                    workspace.create_assessment("tst", self.draft).completed
                )
                current = workspace.active
                self.assertFalse(current.is_dirty)
                current.execute(TstProjectEdit(AddTstTask(self.key, TstTask("b"), 1)))
                self.assertFalse(
                    workspace.switch(
                        str(path), "duet", choice=CloseChoice.CANCEL
                    ).completed
                )
                self.assertIs(workspace.active, current)
                self.assertTrue(
                    workspace.switch(
                        str(path), "duet", choice=CloseChoice.SAVE
                    ).completed
                )
                self.assertFalse(current.is_dirty)
                workspace.switch(str(path), "tst")
                self.assertEqual(len(workspace.active.state.tasks), 2)
                self.assertIsNone(workspace.active.undo_label_key)
                self.assertEqual(workspace.list_assessments()[1].task_count, 2)
            finally:
                workspace.close(choice=CloseChoice.DISCARD)
            with AssessmentProjectFile.open(path) as project:
                self.assertEqual(len(project.load(self.key).tasks), 2)
