"""Original JROT scope selection, checkbox batching and read-only catalog tests.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QSignalSpy, QTest
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.application.rotation_scope import (
    RotationScopeOptions,
    rotation_scope_options,
)
from ergotools.bootstrap import load_icons
from ergotools.domain.job_catalog import Job, JobCatalog, JobPlacement
from ergotools.domain.language import Language
from ergotools.domain.work_catalog import StationKey
from ergotools.presentation.desktop.rotation_scope_dialog import RotationScopeDialog
from tests.test_history_persistence import HIERARCHY, JOBS, OWNER, STATION
from tests.test_rotation_persistence import seed

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def options() -> RotationScopeOptions:
    """Provide two selectable stations, another shift and a source empty shift.

    Args:
        None.

    Returns:
        Immutable eligible station/shift choices with an intentionally empty shift for
        scope-dialog tests.
    """
    second = StationKey("P", "S", "L", "2")
    hierarchy = replace(
        HIERARCHY,
        work=replace(
            HIERARCHY.work, stations=(STATION, second), shifts=("Day", "Night", "Late")
        ),
    )
    jobs = replace(
        JOBS,
        jobs=(*JOBS.jobs, Job("z", "Inactive", active=False)),
        placements=(
            *JOBS.placements,
            JobPlacement(3, "k", second.at_shift("Day")),
            JobPlacement(4, "z", second.at_shift("Late")),
            JobPlacement(5, "j", STATION.at_shift("Night")),
        ),
    )
    repository = Mock(
        load_hierarchy=Mock(return_value=hierarchy), load_jobs=Mock(return_value=jobs)
    )
    result = rotation_scope_options(repository)
    assert repository.load_hierarchy.call_count == repository.load_jobs.call_count == 1
    assert result.shifts == ("Day", "Late", "Night")
    assert len(result.contexts) == 3
    assert all(context.shift_id != "Late" for context in result.contexts)
    return result


def test_saved_scope_options_deduplicate_and_do_not_write(tmp_path: Path) -> None:
    """Active jobs without profiles remain scope choices, as in the original query.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    options()
    path = tmp_path / "scope.sqlite"
    with seed(path) as project:
        before = path.read_bytes()
        result = rotation_scope_options(project)
        assert result == RotationScopeOptions(("Day",), (OWNER.workplace,))
        assert project.format_version == 7 and path.read_bytes() == before
        with pytest.raises(ValueError):
            rotation_scope_options(
                Mock(
                    load_hierarchy=Mock(return_value=HIERARCHY),
                    load_jobs=Mock(return_value=JobCatalog("foreign")),
                )
            )


@pytest.mark.parametrize("language", list(Language))
def test_initial_mixed_parents_batched_group_click_and_shift_accept(
    language: Language,
) -> None:
    """Parent state matches checked leaves on open; cascade emits only one update.

    Args:
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    dialog = RotationScopeDialog(
        options(), load_icons(), selected=(OWNER.workplace,), language=language
    )
    dialog.show()
    _APP.processEvents()
    assert dialog.selected_contexts() == (OWNER.workplace,)
    parent = dialog.tree.topLevelItem(0)
    assert parent is not None
    assert parent.checkState(0) == Qt.CheckState.PartiallyChecked
    signals = QSignalSpy(dialog.tree.itemChanged)
    with patch.object(
        dialog, "_update_selection_label", wraps=dialog._update_selection_label
    ) as update:
        parent.setCheckState(0, Qt.CheckState.Checked)
    assert len(signals) == 1 and update.call_count == 1
    assert len(dialog.selected_contexts()) == 2
    assert dialog.selection_label.text() == (
        "2 estaciones seleccionadas"
        if language == Language.SPANISH
        else "2 Stations selected"
    )
    dialog.shift_combo.setCurrentText("Night")
    assert dialog.selected_contexts() == ()
    QTest.mouseClick(dialog.use_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible() and dialog.result() == QDialog.Rejected
    night = dialog.tree.topLevelItem(0)
    assert night is not None
    night.setCheckState(0, Qt.CheckState.Checked)
    QTest.mouseClick(dialog.use_button, Qt.MouseButton.LeftButton)
    assert dialog.result() == QDialog.Accepted
    assert dialog.selected_contexts() == (STATION.at_shift("Night"),)
    dialog.deleteLater()


def test_scope_cancel_escape_and_empty_shift_preserve_input() -> None:
    """Cancel and Escape do not publish selected drafts or erase the applied scope.

    Args:
        None.

    Returns:
        None.
    """
    selected = (OWNER.workplace,)
    for escape in (False, True):
        dialog = RotationScopeDialog(options(), load_icons(), selected=selected)
        dialog.show()
        dialog.shift_combo.setCurrentText("Late")
        assert dialog.tree.topLevelItemCount() == 0
        QTest.mouseClick(dialog.use_button, Qt.MouseButton.LeftButton)
        assert dialog.isVisible() and "at least" in dialog.selection_label.text()
        if escape:
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
        else:
            QTest.mouseClick(dialog.cancel_button, Qt.MouseButton.LeftButton)
        assert dialog.result() == QDialog.Rejected and not dialog.isVisible()
        assert selected == (OWNER.workplace,)
        dialog.deleteLater()


def test_empty_scope_minimum_resize_and_no_modal_accept() -> None:
    """An empty hierarchy remains usable at minimum/enlarged sizes without selection.

    Args:
        None.

    Returns:
        None.
    """
    dialog = RotationScopeDialog(
        RotationScopeOptions((), ()), load_icons(), language=Language.SPANISH
    )
    dialog.show()
    for width, height in ((680, 560), (1000, 800)):
        dialog.resize(width, height)
        _APP.processEvents()
        assert dialog.rect().contains(dialog.tree.geometry())
        assert dialog.rect().contains(dialog.buttons.geometry())
        assert dialog.tree.columnWidth(0) > 300
        assert dialog.tree.topLevelItemCount() == 0
    QTest.mouseClick(dialog.use_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible() and "al menos" in dialog.selection_label.text()
    QTest.mouseClick(dialog.cancel_button, Qt.MouseButton.LeftButton)
    dialog.deleteLater()
