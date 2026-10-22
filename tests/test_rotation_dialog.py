"""Original JROT form commands, scoped draft cancellation and persistence failures.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QMessageBox,
)

from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation_scheme import RotationMode
from ergotools.presentation.desktop.rotation_dialog import RotationDialog
from ergotools.presentation.desktop.rotation_scope_dialog import RotationScopeDialog
from tests.test_history_persistence import OWNER
from tests.test_rotation_persistence import scheme, seed

# One retained QApplication for native Qt tests; keeps widgets alive and uses the
# approved display/backend baseline.
_APP = QApplication.instance() or QApplication([])


def fill(dialog: RotationDialog, identity: str) -> None:
    """Enter one complete manual rotation through the migrated cell API.

    Args:
        dialog: Live modal/form under test; the caller owns its lifetime and event-loop
            scheduling.
        identity: Exact saved worker/task/scheme identity or deliberately malformed
            boundary value.

    Returns:
        None.
    """
    dialog.scheme_combo.setEditText(identity)
    grid = dialog.grid
    assert grid is not None
    grid.set_choice(0, 0, "w")
    key = grid.pool.targets[0].target.key
    for column in range(1, grid.blocks + 1):
        grid.set_choice(0, column, key)


@pytest.mark.parametrize("language", list(Language))
def test_actual_buttons_save_new_cancel_navigation_delete(
    tmp_path: Path, language: Language
) -> None:
    """Execute form commands and verify saved links after closing/reopening.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    path = tmp_path / "scheme.ergprj"
    with seed(path) as project, patch.object(RotationDialog, "_message") as message:
        before = path.read_bytes()
        dialog = RotationDialog(project, load_icons(), language=language)
        dialog.show()
        assert path.read_bytes() == before and project.format_version == 7
        assert not dialog.delete_button.isEnabled()
        assert all(not button.isEnabled() for button in dialog.navigation)
        assert dialog.grid.blocks == 4
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        assert (
            message.call_args.kwargs["error"] and project.load_rotation_schemes() == ()
        )
        fill(dialog, "B-ñ")
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        (saved,) = project.load_rotation_schemes()
        assert saved.scheme_id == "B-ñ" and saved.targets[0].job_id == "j"
        assert saved.workers[0].assignment_id is None
        assert dialog.delete_button.isEnabled()
        QTest.mouseClick(dialog.new_button, Qt.MouseButton.LeftButton)
        assert (
            dialog.scheme_combo.currentText() == ""
            and not dialog.delete_button.isEnabled()
        )
        fill(dialog, "A")
        QTest.mouseClick(dialog.cancel_button, Qt.MouseButton.LeftButton)
        assert dialog.loaded == saved and dialog.scheme_combo.currentText() == "B-ñ"
        QTest.mouseClick(dialog.new_button, Qt.MouseButton.LeftButton)
        fill(dialog, "A")
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        assert [item.scheme_id for item in project.load_rotation_schemes()] == [
            "A",
            "B-ñ",
        ]
        assert dialog.navigation[2].isEnabled()
        QTest.mouseClick(dialog.navigation[3], Qt.MouseButton.LeftButton)
        assert dialog.loaded == saved
        QTest.mouseClick(dialog.navigation[0], Qt.MouseButton.LeftButton)
        assert dialog.loaded.scheme_id == "A"
        with patch.object(RotationDialog, "_confirm_delete", return_value=False):
            QTest.mouseClick(dialog.delete_button, Qt.MouseButton.LeftButton)
        assert len(project.load_rotation_schemes()) == 2
        with patch.object(RotationDialog, "_confirm_delete", return_value=True):
            QTest.mouseClick(dialog.delete_button, Qt.MouseButton.LeftButton)
            assert dialog.loaded == saved
            QTest.mouseClick(dialog.delete_button, Qt.MouseButton.LeftButton)
        assert project.load_rotation_schemes() == () and dialog.grid.rowCount() == 0
        QTest.mouseClick(dialog.new_button, Qt.MouseButton.LeftButton)
        fill(dialog, "Last")
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        QTest.mouseClick(dialog.close_button, Qt.MouseButton.LeftButton)
        dialog.deleteLater()
        _APP.processEvents()
    with type(project).open(path) as reopened:
        (last,) = reopened.load_rotation_schemes()
        assert last.scheme_id == "Last" and last.targets == saved.targets
        assert reopened.load_job_risk().for_job("j").measurements[0].unit == "Imperial"


def test_scope_modal_pending_apply_counts_clear_and_cancel(tmp_path: Path) -> None:
    """Choosing scope never rebuilds until Apply; Cancel restores exact saved scope.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "scope.ergprj") as project,
        patch.object(RotationDialog, "_message"),
    ):
        project.save_rotation_scheme(scheme())
        dialog = RotationDialog(project, load_icons())
        dialog.show()
        original = dialog.loaded
        grid = dialog.grid

        def reject_scope() -> None:
            """Reject the actual JROT scope modal without changing its applied grid.

            Args:
                None.

            Returns:
                None.
            """
            child = _APP.activeModalWidget()
            assert isinstance(child, RotationScopeDialog)
            child.reject()

        QTimer.singleShot(0, reject_scope)
        QTest.mouseClick(dialog.choose_scope_button, Qt.MouseButton.LeftButton)
        assert dialog.scope == original.scope and dialog.grid is grid

        def accept_scope() -> None:
            """Check the actual scope tree root.

            Check the actual scope tree root and accept its complete eligible station
            selection.

            Args:
                None.

            Returns:
                None.
            """
            child = _APP.activeModalWidget()
            assert isinstance(child, RotationScopeDialog)
            child.tree.topLevelItem(0).setCheckState(0, Qt.CheckState.Checked)
            child.accept()

        QTimer.singleShot(0, accept_scope)
        QTest.mouseClick(dialog.choose_scope_button, Qt.MouseButton.LeftButton)
        assert dialog.pending_scope == (OWNER.workplace,) and dialog.grid is grid
        dialog.blocks_combo.setCurrentText("3")
        QTest.mouseClick(dialog.apply_scope_button, Qt.MouseButton.LeftButton)
        assert dialog.grid is not grid and dialog.grid.blocks == 3
        assert (
            dialog.scope == (OWNER.workplace,) and not dialog.delete_button.isEnabled()
        )
        fill(dialog, "R-ñ")
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        (saved,) = project.load_rotation_schemes()
        assert saved.name == original.name and saved.description == original.description
        assert saved.workers[0].assignment_id == 1
        QTest.mouseClick(dialog.clear_scope_button, Qt.MouseButton.LeftButton)
        assert dialog.pending_scope == dialog.scope == ()
        QTest.mouseClick(dialog.cancel_button, Qt.MouseButton.LeftButton)
        assert (
            dialog.loaded == saved
            and dialog.grid.blocks == 3
            and dialog.scope == saved.scope
        )
        dialog.select_kind(AssessmentKind.DUET)
        assert dialog.grid.choice_key(0, 1) == saved.targets[0].key
        assert dialog.grid.item(0, 4).text() == "Unavailable"
        dialog.close()


def test_storage_failures_retain_edits_and_selected_record(tmp_path: Path) -> None:
    """Failed writes/reads never publish success, replace cells or delete the record.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "failure.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        project.save_rotation_scheme(scheme())
        repository = Mock(wraps=project)
        dialog = RotationDialog(repository, load_icons())
        dialog.show()
        original = dialog.loaded
        grid = dialog.grid
        dialog.grid.set_choice(0, 2, None)
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        repository.save_rotation_scheme.assert_not_called()
        dialog.grid.set_choice(0, 2, original.targets[0].key)
        repository.save_rotation_scheme.side_effect = OSError("disk full")
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        assert message.call_args.kwargs["error"] and dialog.grid is grid
        assert dialog.loaded == original and project.load_rotation_schemes() == (
            original,
        )
        repository.delete_rotation_scheme.side_effect = OSError("blocked")
        with patch.object(RotationDialog, "_confirm_delete", return_value=True):
            QTest.mouseClick(dialog.delete_button, Qt.MouseButton.LeftButton)
        assert dialog.grid is grid and dialog.loaded == original
        repository.load_jobs.side_effect = OSError("read failed")
        QTest.mouseClick(dialog.new_button, Qt.MouseButton.LeftButton)
        assert (
            dialog.grid is grid
            and dialog.scheme_combo.currentText() == original.scheme_id
        )
        dialog.close()


def test_search_and_unchanged_optimized_provenance(tmp_path: Path) -> None:
    """Search exact IDs, retain untouched provenance and reset it after manual edits.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.

    Returns:
        None.
    """
    with (
        seed(tmp_path / "search.ergprj") as project,
        patch.object(RotationDialog, "_message") as message,
    ):
        original = replace(
            scheme(), mode=RotationMode.SINGLE_TOOL, primary_kind=AssessmentKind.LIFFT
        )
        project.save_rotation_scheme(original)
        other = replace(scheme(False), scheme_id="Other")
        project.save_rotation_scheme(other)
        dialog = RotationDialog(project, load_icons())
        dialog.show()

        def search(identity: str) -> None:
            """Enter an exact saved scheme ID into the original search child.

            Enter an exact saved scheme ID into the original search child and emit its
            accepted action.

            Args:
                identity: Exact saved worker/task/scheme identity or deliberately
                    malformed boundary value.

            Returns:
                None.
            """
            child = _APP.activeModalWidget()
            assert isinstance(child, QDialog)
            child.findChild(QLineEdit).setText(identity)
            child.findChild(QDialogButtonBox).accepted.emit()

        QTimer.singleShot(0, lambda: search(original.scheme_id))
        QTest.mouseClick(dialog.search_button, Qt.MouseButton.LeftButton)
        assert dialog.loaded == original
        dialog.select_kind(AssessmentKind.DUET)
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        assert project.load_rotation_schemes()[1] == original
        dialog.select_kind(AssessmentKind.LIFFT)
        dialog.grid.set_choice(0, 2, None)
        dialog.grid.set_choice(0, 2, original.targets[0].key)
        QTest.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        saved = project.load_rotation_schemes()[1]
        assert saved.mode is RotationMode.MANUAL and saved.primary_kind is None
        QTimer.singleShot(0, lambda: search("missing"))
        QTest.mouseClick(dialog.search_button, Qt.MouseButton.LeftButton)
        assert "No rotation scheme" in message.call_args.args[0]
        dialog.close()


@pytest.mark.parametrize("language", list(Language))
def test_native_messages_localize_buttons_and_use_packaged_icons(
    tmp_path: Path, language: Language
) -> None:
    """Exercise actual modal buttons without changing global Qt translations.

    Args:
        tmp_path: Pytest-owned temporary directory; all created projects, images and
            settings stay inside it.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    with seed(tmp_path / "messages.ergprj") as project:
        before = (tmp_path / "messages.ergprj").read_bytes()
        dialog = RotationDialog(project, load_icons(), language=language)

        def confirm() -> None:
            """Assert localized Yes/No, packaged icons and No-default consent.

            Assert localized Yes/No, packaged icons and No-default consent before
            clicking Yes.

            Args:
                None.

            Returns:
                None.
            """
            box = _APP.activeModalWidget()
            assert isinstance(box, QMessageBox)
            yes = box.button(QMessageBox.StandardButton.Yes)
            no = box.button(QMessageBox.StandardButton.No)
            assert yes.text() == ("Sí" if language is Language.SPANISH else "Yes")
            assert no.text() == "No" and not yes.icon().isNull()
            assert box.defaultButton() is no
            yes.click()

        QTimer.singleShot(0, confirm)
        assert dialog._confirm_delete()

        def acknowledge() -> None:
            """Assert the localized acknowledgement and packaged icon.

            Assert the localized acknowledgement and packaged icon before dismissing the
            owned JROT message.

            Args:
                None.

            Returns:
                None.
            """
            box = _APP.activeModalWidget()
            assert isinstance(box, QMessageBox)
            ok = box.button(QMessageBox.StandardButton.Ok)
            assert ok.text() == ("Aceptar" if language is Language.SPANISH else "OK")
            assert not ok.icon().isNull()
            ok.click()

        QTimer.singleShot(0, acknowledge)
        dialog._message("Example", error=True)
        assert (tmp_path / "messages.ergprj").read_bytes() == before
        dialog.close()
