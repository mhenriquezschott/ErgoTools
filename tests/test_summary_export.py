"""Saved-tool CSV scope, historical identity, review gates and failure isolation.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import codecs
import csv
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QApplication

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.summary_export import load_summary_rows, write_summary_csv
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.summary_csv import SUMMARY_HEADERS, summary_csv_table
from tests.test_saved_tool_data import KINDS
from tests.test_saved_tool_data import window as window


@pytest.mark.parametrize("index", [0, 1, 2])
def test_saved_export_scope_and_menu_preserve_pending_editor(
    window: LifftWindow, tmp_path: Path, index: int
) -> None:
    """Export current saved versions for all owners, retaining closed assignments.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        index: Zero-based selected input/row/case index used by the parametrized
            regression.

    Returns:
        None.
    """
    window.assessment_tabs.setCurrentIndex(index)
    workspace = window.presenter.workspace
    active, location = workspace.active, workspace.location
    settings = window._settings_store.load()
    source = active.state
    path = tmp_path / "summaries.csv"
    rows = load_summary_rows(location, KINDS[index])
    assert len(rows) == 3 and {row.assignment_id for row in rows} == {1, 2, 3}
    assert len({row.document for row in rows}) == 3
    assert (
        next(row for row in rows if row.assignment_id == 2).assignment_active is False
    )
    field = (window.task_panel if index == 0 else window.secondary_panel()).inputs[0][
        2 if index == 0 else -1
    ]
    field.setText("bad")
    field.textEdited.emit("bad")
    with patch.object(window, "choose_file", return_value=str(path)):
        window._assessment_menu.export_csv.trigger()
    assert workspace.active is active and workspace.location == location
    assert active.state is source and field.text() == "bad" and not active.is_dirty
    assert window._settings_store.load() == settings
    assert path.read_bytes().startswith(codecs.BOM_UTF8)
    with path.open(newline="", encoding="utf-8-sig") as output:
        exported = list(csv.DictReader(output))
    assert len(exported) == 3 and list(exported[0]) == list(SUMMARY_HEADERS)
    assert {row["Tool ID"] for row in exported} == {("LiFFT", "DUET", "ST")[index]}
    assert all(row["Evaluation Status"] == "complete" for row in exported)
    assert all(float(row["Total Cumulative Damage"]) > 0 for row in exported)
    for row, record in zip(exported, rows, strict=True):
        assert float(row["Probability Outcome"]) == record.probability * 100


def test_toolbar_cancel_and_failures_retain_pending_text(
    window: LifftWindow, tmp_path: Path
) -> None:
    """Toolbar uses the same noncommitting export path as the menu.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    active = window.presenter.workspace.active
    field = window.task_panel.inputs[0][2]
    field.setText("bad")
    field.textEdited.emit("bad")
    action = window.main_navigation.toolbar_actions["export"]
    with patch.object(window, "choose_file", return_value=""):
        action.trigger()
    assert field.text() == "bad" and window.presenter.workspace.active is active
    QApplication.processEvents()
    status_height = window.message.height()
    target = tmp_path / "existing.csv"
    target.write_bytes(b"keep")
    with patch.object(window, "choose_file", return_value=str(target)):
        action.trigger()
    assert target.read_bytes() == b"keep" and field.text() == "bad"
    QApplication.processEvents()
    assert window.message.height() == status_height
    target = tmp_path / "failed.csv"
    with (
        patch.object(window, "choose_file", return_value=str(target)),
        patch(
            "ergotools.infrastructure.summary_export.os.link",
            side_effect=OSError("publication failed"),
        ),
    ):
        action.trigger()
    assert not target.exists() and not list(tmp_path.glob(".ergotools-export-*"))
    assert field.text() == "bad" and window.presenter.workspace.active is active


def test_metric_review_and_missing_inputs_export_absence(
    window: LifftWindow,
) -> None:
    """Metric review and missing-data failures remain explicit export states.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    location = window.presenter.workspace.location
    key = DocumentKey(window.presenter.workspace.active.document.project_id, "lifft-1")
    with AssessmentProjectFile.open(Path(location)) as project:
        original = project.load(key)
        project.save(key, replace(original, system=MeasurementSystem.METRIC))
    rows = load_summary_rows(location, KINDS[0])
    gated = next(row for row in rows if row.assignment_id == 1)
    assert gated.status is EvaluationStatus.COMPLETE
    assert gated.total_damage is not None and gated.probability is not None
    assert gated.units is MeasurementSystem.METRIC
    assert gated.issue_keys == ()
    with AssessmentProjectFile.open(Path(location)) as project:
        project.save(key, LifftDraft(original.system, (LifftTask("l", -1, 20, 100),)))
    invalid = next(
        row for row in load_summary_rows(location, KINDS[0]) if row.assignment_id == 1
    )
    assert invalid.status is EvaluationStatus.INVALID_INPUT
    assert invalid.total_damage is None and invalid.probability is None


def test_csv_quotes_unicode_and_delimiters(window: LifftWindow, tmp_path: Path) -> None:
    """BOM/quoting round-trip exact owner identities rather than trimming them.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    row = load_summary_rows(window.presenter.workspace.location, KINDS[0])[0]
    owner = replace(row.owner, worker_id='árbol,"worker"' + chr(10) + "other")
    row = replace(row, owner=owner)
    table = summary_csv_table((row,), "2026-10-05 12:00:00")
    target = tmp_path / "quoted.csv"
    write_summary_csv(str(target), table)
    with target.open(newline="", encoding="utf-8-sig") as output:
        exported = list(csv.DictReader(output))
    assert exported[0]["Worker ID"] == owner.worker_id
    assert exported[0]["Export DateTime"] == "2026-10-05 12:00:00"


def test_empty_current_tool_reports_no_data_without_picker(window: LifftWindow) -> None:
    """No matching current versions opens no file chooser and changes no editor.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    active = window.presenter.workspace.active
    with (
        patch.object(window, "_summary_loader", return_value=()),
        patch.object(window, "choose_file") as picker,
    ):
        window._assessment_menu.export_csv.trigger()
    picker.assert_not_called()
    assert window.presenter.workspace.active is active
    assert window.message.text() == window.text("export_empty")


def test_unused_task_slots_retain_completed_totals_and_complete_status(
    window: LifftWindow,
) -> None:
    """Blank slots do not suppress the original grid's completed-row summary.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    location = window.presenter.workspace.location
    key = window.presenter.workspace.active.document
    before = next(
        row for row in load_summary_rows(location, KINDS[0]) if row.assignment_id == 1
    )
    with AssessmentProjectFile.open(Path(location)) as project:
        source = project.load(key)
        project.save(key, replace(source, tasks=(*source.tasks, LifftTask("unused"))))
    after = next(
        row for row in load_summary_rows(location, KINDS[0]) if row.assignment_id == 1
    )
    assert after.status is EvaluationStatus.COMPLETE
    assert after.total_damage == before.total_damage
    assert after.probability == before.probability
    assert not after.issue_keys
