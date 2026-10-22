"""Fresh Save provenance, transaction failure and pending-input regressions.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ergotools.application.assessment_export import saved_summary_rows
from ergotools.application.assessments.evaluation import (
    AssessmentEvaluator,
)
from ergotools.application.historical_results import HistoricalAssessmentResult
from ergotools.application.saved_results import ResultSave, result_snapshot
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft, AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft, DuetTask
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_json import DocumentFormatError
from ergotools.infrastructure.saved_result_store import SavedResultStore
from ergotools.presentation.desktop.lifft_window import LifftWindow
from tests.test_legacy_catalogs import legacy_catalog as legacy_catalog
from tests.test_legacy_reconciliation import old_source as old_source
from tests.test_saved_tool_data import window as window
from tools.project_migration.ergotools_migration.legacy_conversion import (
    convert_legacy_project,
)

# Representative LiFFT/DUET/ST source drafts with explicit units/directions used for
# authoritative result persistence.
SOURCES = (
    LifftDraft(MeasurementSystem.METRIC, (LifftTask("l", 42, 80, 123),)),
    DuetDraft((DuetTask("d", 6, 123),)),
    TstDraft(
        MeasurementSystem.IMPERIAL, (TstTask("s", TstDirection.DOWNWARD, 12, 20, 123),)
    ),
)


def calculate(session: DocumentSession[AssessmentDraft]) -> HistoricalAssessmentResult:
    """Use the same characterized grid path as the integrated tool controls.

    Args:
        session: Test-owned active source history; evaluation must not create edits or
            persistence implicitly.

    Returns:
        Detached matching authoritative result cache from the real tool grid evaluator;
        calculation itself does not save source state.
    """
    evaluator = AssessmentEvaluator()
    source = session.state
    outcome = (
        evaluator.evaluate_lifft_grid(session)
        if isinstance(source, LifftDraft)
        else evaluator.evaluate_duet_grid(session)
        if isinstance(source, DuetDraft)
        else evaluator.evaluate_tst_grid(session)
    )
    result = result_snapshot(
        outcome,
        source.system
        if not isinstance(source, DuetDraft)
        else MeasurementSystem.IMPERIAL,
    )

    assert result is not None
    return result


@pytest.mark.parametrize("source", SOURCES)
def test_source_and_results_survive_reopen_and_snapshot(
    tmp_path: Path, source: AssessmentDraft
) -> None:
    """All tools persist detached results despite an unchanged clean source.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        source: Immutable draft or disposable source path supplied by the stated
            storage/publication scenario.

    Returns:
        None.
    """
    path = tmp_path / "project.ergprj"
    key = DocumentKey("p", "d")
    metadata = ProjectMetadata("p", "Fresh", MeasurementSystem.IMPERIAL)
    with AssessmentProjectFile.create_with_document(
        path, metadata, "d", source
    ) as project:
        session = DocumentSession(key, source, persisted=True)
        result = calculate(session)
        session.save(ResultSave(project, result))
        assert not session.is_dirty and session.state is source
        assert project.load_saved_result(key) == result
        with project.snapshot(str(tmp_path / "copy.ergprj"), None, None) as copied:
            assert copied.load_saved_result(key) == result
    with AssessmentProjectFile.open(path) as reopened:
        assert (
            reopened.load(key) == source and reopened.load_saved_result(key) == result
        )


def test_imported_unchanged_calculate_save_supersedes_archive_only_for_display(
    old_source: Path, tmp_path: Path
) -> None:
    """Calculate/Save replaces the sole converted result and retains source inputs.

    Args:
        old_source: Disposable original-format fixture containing unversioned LiFFT rows
            and exact saved ownership.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "converted.ergprj"
    with convert_legacy_project(old_source, path, "p") as project:
        (old_row,) = saved_summary_rows(project, AssessmentKind.LIFFT)
        source = project.load(old_row.document)
        session = DocumentSession(old_row.document, source, persisted=True)
        result = calculate(session)
        session.save(ResultSave(project, result))
        (new_row,) = saved_summary_rows(project, AssessmentKind.LIFFT)
        assert new_row.status is result.calculation_status
        assert new_row.total_damage == result.damage
        assert new_row.recorded_probability_percent == result.probability_percent
        assert project.load_saved_result(old_row.document) == result
        assert project.load(old_row.document) == source
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_saved_result(old_row.document) == result
        assert saved_summary_rows(reopened, AssessmentKind.LIFFT) == (new_row,)


def test_failed_result_write_rolls_back_source_schema_and_format(
    tmp_path: Path,
) -> None:
    """A result write failure leaves the old source/version and clean marker intact.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "failure.ergprj"
    source = SOURCES[0]
    key = DocumentKey("p", "d")
    with AssessmentProjectFile.create_with_document(
        path, ProjectMetadata("p", "Failure", MeasurementSystem.METRIC), "d", source
    ) as project:
        changed = replace(source, tasks=(replace(source.tasks[0], repetitions=321),))
        session = DocumentSession(key, changed)
        result = calculate(session)
        with (
            patch.object(
                SavedResultStore,
                "write",
                side_effect=sqlite3.OperationalError("fixture"),
            ),
            pytest.raises(sqlite3.OperationalError),
        ):
            session.save(ResultSave(project, result))
        assert session.is_dirty and project.load(key) == source
        assert project.load_saved_result(key) is None
        session.save(ResultSave(project, result))
        assert not session.is_dirty and project.load(key) == changed


@pytest.mark.parametrize("index", [0, 1, 2])
def test_integrated_save_reopen_and_pending_edit_never_reuses_previous_result(
    window: LifftWindow, index: int
) -> None:
    """Native Save uses each tool evaluator and suppresses pending input output.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    source = workspace.active.state
    window.calculate()
    result = window.current_result_snapshot()
    assert result is not None and result.source == source
    window.save_project()
    window.presenter.evaluator.clear()
    window.duet_presenter.evaluator.clear()
    window.tst_presenter.evaluator.clear()
    window.refresh()
    assert workspace.historical_result() == result
    assert window.results_sidebar.assessment_status_label.text() == "Ready"
    panel = window.task_panel if index == 0 else window.secondary_panel()
    field = panel.inputs[0][2 if index == 0 else -1]
    field.setText("bad")
    field.textEdited.emit("bad")
    window.run(window.save_project)
    assert field.text() == "bad" and workspace.active.state == source
    assert window.current_result_snapshot() is None
    assert workspace.historical_result() == result


@pytest.mark.parametrize(
    "change",
    [
        {"version": 2},
        {"status": "recorded"},
        {"tasks": []},
        {"damage": True},
        {"percent": float("inf")},
        {"units": "unknown"},
        {"issues": "bad"},
    ],
)
def test_saved_result_codec_rejects_invalid_evidence(change: dict[str, object]) -> None:
    """Malformed records cannot become displayed fresh calculations.

    Args:
        change: Parametrized mutation applied to an isolated snapshot/source to exercise
            a rejection boundary.

    Returns:
        None.
    """
    result = calculate(DocumentSession(DocumentKey("p", "d"), SOURCES[0]))
    data = json.loads(SavedResultStore.encode(result))
    data.update(change)
    with pytest.raises(DocumentFormatError):
        SavedResultStore.decode(json.dumps(data))
