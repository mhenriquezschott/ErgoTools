"""JROT dropdown identity, row calculations, frozen evidence and saved workflow.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtTest import QSignalSpy, QTest
from PyQt5.QtWidgets import QApplication, QComboBox, QStyleOptionViewItem

from ergotools.application.rotation_pool import rotation_pool
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import Job, JobPlacement, WorkerJobAssignment
from ergotools.domain.job_risk import (
    JobRiskCatalog,
    JobRiskMeasurement,
    JobRiskValues,
)
from ergotools.domain.language import Language
from ergotools.domain.work_catalog import StationKey
from ergotools.domain.work_hierarchy import LineKey
from ergotools.presentation.desktop.rotation_display import rotation_recommendation
from ergotools.presentation.desktop.rotation_table import RotationTable
from tests.test_history_persistence import HIERARCHY, JOBS, OWNER
from tests.test_rotation_persistence import scheme, seed

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def catalog_reader() -> Mock:
    """Duplicate station captions and multiline IDs must not merge identities.

    Args:
        None.

    Returns:
        Mock repository exposing exact duplicate-caption and multiline-ID worker/target
        evidence.
    """
    second = StationKey("P", "S", "Other", "1")
    other = second.at_shift("Day")
    hierarchy = replace(
        HIERARCHY,
        lines=(*HIERARCHY.lines, LineKey("P", "S", "Other")),
        work=replace(
            HIERARCHY.work,
            stations=(*HIERARCHY.work.stations, second),
        ),
    )
    jobs = replace(
        JOBS,
        jobs=(*JOBS.jobs, Job("k\n- ñ", "Multiline")),
        placements=(*JOBS.placements, JobPlacement(3, "j", other)),
        assignments=(
            *JOBS.assignments,
            WorkerJobAssignment(3, replace(OWNER, workplace=other), 3),
        ),
    )
    risks = JobRiskCatalog(
        "p",
        (
            JobRiskValues(
                "j",
                measurements=(
                    JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0, "Imperial"),
                ),
            ),
            JobRiskValues(
                "k",
                measurements=(
                    JobRiskMeasurement(AssessmentKind.LIFFT, 0.2, 80, "Metric"),
                ),
            ),
            JobRiskValues(
                "k\n- ñ",
                measurements=(
                    JobRiskMeasurement(AssessmentKind.DUET, 1, 50, "Metric"),
                ),
            ),
        ),
    )
    return Mock(
        load_hierarchy=Mock(return_value=hierarchy),
        load_jobs=Mock(return_value=jobs),
        load_job_risk=Mock(return_value=risks),
    )


def test_pool_scope_identity_and_saved_history() -> None:
    """Match active source queries and retain historical links only on saved load.

    Args:
        None.

    Returns:
        None.
    """
    reader = catalog_reader()
    organization = rotation_pool(reader)
    assert [item.link.assignment_id for item in organization.workers] == [None, None]
    assert len(organization.targets) == 3
    for method in (reader.load_hierarchy, reader.load_jobs, reader.load_job_risk):
        method.assert_called_once_with()
    scope = tuple(place.workplace for place in reader.load_jobs().placements)
    scope = tuple(dict.fromkeys(scope))
    scoped = rotation_pool(reader, scope)
    assert [item.link.assignment_id for item in scoped.workers] == [1]
    assert [item.target.placement_id for item in scoped.targets] == [1, 3, 2]
    reader.load_jobs.return_value = replace(
        reader.load_jobs(),
        assignments=tuple(
            replace(item, active=False) for item in reader.load_jobs().assignments
        ),
    )
    assert rotation_pool(reader, (OWNER.workplace,)).workers == ()
    historical = rotation_pool(reader, (OWNER.workplace,), saved=scheme())
    assert historical.workers[0].link.assignment_id == 1
    assert historical.targets[0].values == reader.load_job_risk().for_job("j")
    with pytest.raises(ValueError, match="scope differ"):
        rotation_pool(reader, saved=scheme())
    with pytest.raises(ValueError, match="unique workplaces"):
        rotation_pool(reader, (OWNER.workplace, OWNER.workplace))
    reader.load_job_risk.return_value = replace(
        reader.load_job_risk(), project_id="foreign"
    )
    with pytest.raises(ValueError):
        rotation_pool(reader)


@pytest.mark.parametrize("language", list(Language))
def test_edit_average_zero_missing_clear_and_notifications(language: Language) -> None:
    """Each edit recalculates once; basis switches retain links without dirty events.

    Args:
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    pool = rotation_pool(catalog_reader())
    table = RotationTable(pool, workers=2, blocks=2, language=language)
    changed = QSignalSpy(table.changed)
    qt_changed = QSignalSpy(table.cellChanged)
    low, high, missing = (item.target.key for item in pool.targets)
    # Ordering is casefold by job ID: j, k, multiline k.
    table.set_choice(0, 0, "w")
    table.set_choice(0, 1, low)
    table.set_choice(0, 2, high)
    assert table.item(0, 3).text() == "40.0%"
    colors = [table.item(0, col).background().color() for col in (1, 2)]
    expected = QColor(
        *(
            sum(getattr(c, channel)() for c in colors) // 2
            for channel in ("red", "green", "blue")
        )
    )
    assert table.item(0, 3).background().color() == expected
    assert len(changed) == 3 and len(qt_changed) == 0
    assert "Imperial" in table.item(0, 1).toolTip()
    assert low not in dict(table.choice_options(1, 1))
    assert "w" not in dict(table.choice_options(1, 0))
    with pytest.raises(ValueError, match="already used"):
        table.set_choice(1, 1, low)
    with pytest.raises(ValueError, match="unavailable"):
        table.set_choice(0, 1, missing)
    with pytest.raises(ValueError, match="Derived"):
        table.set_choice(0, 3, low)
    table.set_choice(0, 1, low)
    assert len(changed) == 3
    table.set_kind(AssessmentKind.DUET)
    assert table.choice_key(0, 1) == low
    assert table.item(0, 3).text() in ("Unavailable", "No disponible")
    assert len(changed) == 3
    table.set_kind(AssessmentKind.LIFFT)
    table.set_choice(0, 2, low)
    assert table.item(0, 3).text() == "0.0%"
    table.item(0, 1).setSelected(True)
    table.item(0, 3).setSelected(True)
    QTest.keyClick(table, Qt.Key.Key_Delete)
    assert table.choice_key(0, 1) is None and table.item(0, 3).text() == ""
    assert len(changed) == 5
    table.clear_selected()
    assert len(changed) == 5
    table.close()


def test_real_delegate_commit_colliding_captions_and_multiline_identity() -> None:
    """Use Qt's actual delegate API rather than manually setting display labels.

    Args:
        None.

    Returns:
        None.
    """
    reader = catalog_reader()
    scope = tuple(
        dict.fromkeys(place.workplace for place in reader.load_jobs().placements)
    )
    pool = rotation_pool(reader, scope)
    table = RotationTable(pool, blocks=2)
    labels = dict(table.choice_options(0, 1))
    assert len(set(labels.values())) == 3
    assert all(" @ " in label for key, label in labels.items() if key.startswith("1:j"))
    delegate = table.itemDelegate()
    model = table.model()
    index = model.index(0, 1)
    editor = delegate.createEditor(table, QStyleOptionViewItem(), index)
    assert isinstance(editor, QComboBox)
    delegate.setEditorData(editor, index)
    assert editor.currentIndex() == -1
    key = pool.targets[1].target.key
    editor.setCurrentIndex(editor.findData(key))
    delegate.setModelData(editor, model, index)
    assert table.choice_key(0, 1) == key
    # Arbitrary caption changes cannot redirect the stored job/profile identity.
    table.item(0, 1).setText("different\ncaption")
    assert table.choice_key(0, 1) == key
    org = RotationTable(rotation_pool(reader), blocks=2, kind=AssessmentKind.DUET)
    multiline = next(
        item.target.key for item in org.pool.targets if "\n" in item.target.job_id
    )
    org.set_choice(0, 0, "w")
    org.set_choice(0, 1, multiline)
    org.set_choice(0, 2, multiline)
    assert org.current_scheme("R").targets[0].job_id == "k\n- ñ"
    table.close()
    org.close()


def test_grid_save_reopen_edit_delete_and_failed_load_preserves_edits(
    tmp_path: Path,
) -> None:
    """Exercise grid→owned project→reopen→grid with original evidence and units.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    path = tmp_path / "rotation.ergprj"
    with seed(path) as project:
        table = RotationTable(rotation_pool(project, (OWNER.workplace,)), blocks=2)
        with pytest.raises(ValueError, match="worker"):
            table.current_scheme("R")
        table.set_choice(0, 0, "w")
        with pytest.raises(ValueError, match="time block"):
            table.current_scheme("R")
        key = table.pool.targets[0].target.key
        for column in (1, 2):
            table.set_choice(0, column, key)
        saved = table.current_scheme(
            "R-ñ", name="Name", scope=(OWNER.workplace,), description="Note"
        )
        project.save_rotation_scheme(saved)
        table.close()
    with type(project).open(path) as reopened:
        (loaded,) = reopened.load_rotation_schemes()
        table = RotationTable(rotation_pool(reopened, loaded.scope, saved=loaded))
        changes = QSignalSpy(table.changed)
        table.load_scheme(loaded)
        assert (
            table.current_scheme(
                "R-ñ", name="Name", scope=loaded.scope, description="Note"
            )
            == saved
        )
        assert len(changes) == 0
        with pytest.raises(ValueError, match="exact saved evidence"):
            table.load_scheme(replace(loaded, project_id="elsewhere"))
        assert table.choice_key(0, 1) == key
        with pytest.raises(ValueError):
            table.reset_grid(11, 2)
        assert table.choice_key(0, 1) == key
        with pytest.raises(IndexError):
            table.choice_key(-1, 0)
        with pytest.raises(ValueError):
            table.set_kind("other")
        table.set_choice(0, 2, None)
        assert len(changes) == 1
        table.set_choice(0, 2, key)
        reopened.save_rotation_scheme(table.current_scheme("R-ñ", scope=loaded.scope))
        reopened.delete_rotation_scheme("R-ñ")
        assert reopened.load_rotation_schemes() == ()
        table.close()


@pytest.mark.parametrize(
    ("values", "prefix"),
    [
        ((), ""),
        ((0.0, 0.0), "This job"),
        ((25.0, 25.0), "The job"),
        ((50.0, 50.0), "The job"),
        ((51.0, 51.0), "Redesign at least"),
        ((61.0, 61.0, 19.0), "Redesign the high"),
        ((60.0, 60.0, 20.0), "The job"),
    ],
)
def test_reference_recommendation_boundaries(
    values: tuple[float, ...], prefix: str
) -> None:
    """Retain strict >60/<20 and inclusive 25/50 boundaries from source.

    Args:
        values: Explicit numeric boundary/threshold tuple used by the parametrized
            scientific regression.
        prefix: Expected native format/key prefix or test input prefix selected by this
            case.

    Returns:
        None.
    """
    assert rotation_recommendation(values, Language.ENGLISH).startswith(prefix)
