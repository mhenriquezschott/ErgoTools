"""Standalone-first worker navigation and alphabetical fallback without new sources."""

from dataclasses import replace
from pathlib import Path

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.bootstrap import create_window
from ergotools.domain.assessment_history import AssignmentAssessment
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import JobCatalog, WorkerJobAssignment
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from tests.test_optional_assessment_context import source_for

# Native controls share one process-owned Qt application across these disposable cases.
_APP = QApplication.instance() or QApplication([])


def seed_defaults(path: Path) -> None:
    """Build mixed, workplace-only and empty workers with deliberately reversed sources.

    Args:
        path: Disposable native project destination.

    Returns:
        None; all tools have matching ownership, including an empty active assignment
        sharing an older saved owner's path. No operational fixture is used.
    """
    stations = (
        StationKey("Zulu Plant", "Packing", "Line Z", "ST02"),
        StationKey("Alpha Plant", "Packing", "Line A", "ST01"),
        StationKey("Alpha Plant", "Assembly", "Line B", "ST02"),
        StationKey("Alpha Plant", "Assembly", "Line A", "ST01"),
    )
    work = WorkCatalog(
        "defaults",
        tuple(WorkerEntry(w) for w in ("W01", "W02", "W03")),
        stations,
        ("Night", "Day"),
    )
    hierarchy = WorkHierarchy(
        work,
        ("Alpha Plant", "Zulu Plant"),
        tuple({SectionKey(s.plant_name, s.section_name) for s in stations}),
        tuple({LineKey(s.plant_name, s.section_name, s.line_name) for s in stations}),
    )
    owners = [
        WorkerJobAssignment(
            1, work.worker_context("W01", stations[0].at_shift("Night")), None
        )
    ]
    owners.extend(
        WorkerJobAssignment(
            i + 2,
            work.worker_context("W02", station.at_shift("Day")),
            None,
            active=i != 3,
        )
        for i, station in enumerate(stations)
    )
    owners.append(replace(owners[-1], assignment_id=6, active=True))
    metadata = ProjectMetadata(
        work.project_id, "Default navigation", MeasurementSystem.METRIC
    )
    with AssessmentProjectFile.create_empty(path, metadata) as project:
        project.save_hierarchy(hierarchy)
        project.save_jobs(JobCatalog(work.project_id, assignments=tuple(owners)))
        for kind in AssessmentKind:
            for identity, assignment_id, worker in (
                ("standalone", None, "W01"),
                ("workplace", 1, "W01"),
                ("zulu", 2, "W02"),
                ("packing", 3, "W02"),
                ("assembly-b", 4, "W02"),
                ("alpha-first", 5, "W02"),
            ):
                project.create_historical_assessment(
                    AssignmentAssessment(
                        f"{identity}-{kind.value}", assignment_id, kind, worker
                    ),
                    source_for(kind),
                )


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_worker_default_prefers_standalone_then_exact_sorted_saved_source(
    tmp_path: Path, kind: AssessmentKind
) -> None:
    """Worker defaults ignore remembered paths and never select an empty active owner.

    Args:
        tmp_path: Disposable project/settings directory.
        kind: Each tool has an independent default source and filtered catalog.

    Returns:
        None; existing exact identities and history counts remain unchanged.
    """
    path = tmp_path / "defaults.ergprj"
    seed_defaults(path)
    window = create_window(
        tmp_path / "settings.json", original_navigation=True, enable_vtk=False
    )
    try:
        window.open_project_location(str(path))
        window.assessment_tabs.setCurrentIndex(list(AssessmentKind).index(kind))
        browser = window.assessment_navigation
        current = window.presenter.workspace.read_history().history
        owner = window.presenter.workspace.read_jobs().jobs.assignments[0]
        browser.select(
            "W01",
            kind,
            lambda: window._blank_kind(kind),
            workplace=owner.worker.workplace,
            explicit=True,
            assignment_id=1,
        )
        window.refresh()
        window.navigate_worker("W02")
        assert browser.view.document_id == f"alpha-first-{kind.value}"
        assert (
            browser.view.assignment_id == 5
        )  # Six is active but has no saved assessment.
        nav = window.main_navigation
        places = nav.location_browser.combos
        assert [c.count() for c in places[:3]] == [3, 3, 3]
        places[2].setCurrentIndex(places[2].findData("Line B"))
        assert browser.view.document_id == f"assembly-b-{kind.value}"
        places[1].setCurrentIndex(places[1].findData("Packing"))
        assert browser.view.document_id == f"packing-{kind.value}"
        assert places[2].count() == 2  # No Assembly-only Line B in Packing.
        places[0].setCurrentIndex(places[0].findData("Zulu Plant"))
        assert browser.view.document_id == f"zulu-{kind.value}"
        assert [c.count() for c in places[1:]] == [2, 2, 2, 2]
        places[0].setCurrentIndex(places[0].findData("Alpha Plant"))
        assert browser.view.document_id == f"alpha-first-{kind.value}"
        window.navigate_worker("W01")
        assert browser.view.document_id == f"standalone-{kind.value}"
        assert nav.standalone_button.property("assessmentCurrent") is True
        assert nav.location_browser.property("assessmentCurrent") is False
        assert nav.location_browser.combos[0].count() == 2  # Only the saved Zulu path.
        assert nav.location_browser.combos[1].count() == 1
        assert nav.location_browser.summary.parentWidget() is not nav.location_browser
        assert window.presenter.workspace.read_history().history == current
        window.history_actions.replay(redo=False)
        assert browser.view.document_id == f"alpha-first-{kind.value}"
        assert nav.location_browser.property("assessmentCurrent") is True
        assert nav.standalone_button.property("assessmentCurrent") is False
        window.navigate_worker("W03")
        assert not browser.view.saved and browser.view.workplace is None
        assert window.presenter.workspace.read_history().history == current
    finally:
        window.presenter.workspace.close(choice=CloseChoice.DISCARD)
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        _APP.processEvents()
