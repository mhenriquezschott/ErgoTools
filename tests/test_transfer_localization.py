"""Owned transfer translations must never alter user records or consent semantics.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from ergotools.application.settings import Language
from ergotools.presentation.desktop.lifft_window import LifftWindow
from ergotools.presentation.desktop.worker_transfer_dialog import WorkerTransferDialog
from tests.test_assessment_transfer import add_destination, select_y
from tests.test_saved_tool_data import window as window


def form(window: LifftWindow, language: Language) -> WorkerTransferDialog:
    """Use exact saved source ownership and no dirty-source resolver action.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        Live owned Worker Transfer modal over exact saved source ownership; caller
        closes it.
    """
    return WorkerTransferDialog(
        window.presenter.workspace,
        1,
        window.icons,
        lambda _: None,
        language=language,
        parent=window,
    )


@pytest.mark.parametrize("language", list(Language))
def test_actual_consent_and_conflict_keep_source(
    window: LifftWindow, language: Language
) -> None:
    """Localized No remains default, and conflict rejects the full selection.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    add_destination(window)
    dialog = form(window, language)
    try:
        select_y(dialog)
        history = window.presenter.workspace.read_history().history

        def refuse() -> None:
            """Assert No-default localized transfer consent.

            Assert No-default localized transfer consent and refuse the actual message
            without source writes.

            Args:
                None.

            Returns:
                None.
            """
            message = QApplication.activeModalWidget()
            assert isinstance(message, QMessageBox)
            assert message.defaultButton() is message.button(QMessageBox.No)
            assert message.button(QMessageBox.Yes).text().replace("&", "") == (
                "Sí" if language is Language.SPANISH else "Yes"
            )
            message.button(QMessageBox.No).click()

        QTimer.singleShot(0, refuse)
        dialog.perform_transfer()
        assert not dialog.completed
        assert window.presenter.workspace.read_history().history == history
        # x already owns all three tools; actual conflict must explain the rejection.
        for row in range(dialog.worker_table.rowCount()):
            if dialog.worker_table.item(row, 0).text() == "x":
                dialog.worker_table.selectRow(row)
                break

        def close_warning() -> None:
            """Assert localized existing-destination conflict text and acknowledgement.

            Assert localized existing-destination conflict text and acknowledgement,
            then dismiss the actual warning.

            Args:
                None.

            Returns:
                None.
            """
            message = QApplication.activeModalWidget()
            assert isinstance(message, QMessageBox)
            assert message.text() == (
                "El destino ya contiene datos de las herramientas seleccionadas."
                if language is Language.SPANISH
                else "Destination already contains selected assessment data."
            )
            assert message.button(QMessageBox.Ok).text().replace("&", "") == (
                "Aceptar" if language is Language.SPANISH else "OK"
            )
            message.button(QMessageBox.Ok).click()

        QTimer.singleShot(0, close_warning)
        dialog.perform_transfer()
        assert not dialog.completed
        assert window.presenter.workspace.read_history().history == history
    finally:
        dialog.close()


@pytest.mark.parametrize("language", list(Language))
def test_owned_controls_and_tooltips_are_localized(
    window: LifftWindow, language: Language
) -> None:
    """Filters use typed keys even when visible All and operation labels change.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.
        language: Parametrized English/Spanish UI language; source values and unit
            interpretation stay unchanged.

    Returns:
        None.
    """
    dialog = form(window, language)
    try:
        spanish = language is Language.SPANISH
        assert dialog.alphabet_buttons["All"].text() == ("Todos" if spanish else "All")
        assert dialog.buttons.button(dialog.buttons.Cancel).text().replace("&", "") == (
            "Cancelar" if spanish else "Cancel"
        )
        assert dialog.tool_table.toolTip() == (
            "Elija las herramientas que desea copiar o mover."
            if spanish
            else "Select the assessment tools to copy or move."
        )
        assert dialog.tool_table.item(0, 1).toolTip() == (
            "Herramienta de extremidad superior distal"
            if spanish
            else "Distal Upper Extremity Tool"
        )
        dialog.alphabet_buttons["All"].click()
        assert dialog.active_letter is None
        assert dialog.worker_table.rowCount() == 2
    finally:
        dialog.close()


def test_record_label_matching_caption_is_never_translated(window: LifftWindow) -> None:
    """A user name equal to an English caption is data, not a catalog key.

    Args:
        window: Live synthetic Qt form supplied by the test fixture; fixture/caller owns
            its close and repository cleanup.

    Returns:
        None.
    """
    with patch(
        "ergotools.presentation.desktop.worker_transfer_dialog.worker_options",
        return_value=[SimpleNamespace(worker_id="w", label="Shift")],
    ):
        dialog = form(window, Language.SPANISH)
    try:
        assert dialog.source_worker_label.text() == "Shift"
        assert "Turno: Day" in dialog.source_path_label.text()
    finally:
        dialog.close()
