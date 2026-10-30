"""Read-only Job copy browsing, result availability and source revalidation.

Presentation tests use detached values rather than modifying any project. Verify
search/navigation/context selection and explicit Copy/cancel boundaries.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog

from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.job_risk import JobRiskMeasurement
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.desktop.job_copy_picker import (
    CopyCandidate,
    CopySource,
    JobValuePicker,
)
from ergotools.presentation.desktop.theme.job_results import job_damage_color

# Preserve the native application for every owned dialog in this module.
_APP = QApplication.instance() or QApplication([])


def test_source_filters_hierarchy_zero_values_and_explicit_copy() -> None:
    """Browsing is read-only; a valid zero can be selected through a real hierarchy.

    Args:
        None.

    Returns:
        None; only explicit Copy invokes source revalidation and returns its value.
    """
    zero = JobRiskMeasurement(AssessmentKind.LIFFT, 0, 0)
    standalone = CopyCandidate("standalone", ("Standalone assessment",), "", "", zero)
    workplace = CopyCandidate(
        "assigned",
        ("Riverside", "Packing", "Line A", "ST01", "Shift 1"),
        "No Job",
        "1",
        zero,
    )
    missing = CopyCandidate("pending", ("Standalone assessment",), "", "", None)
    calls: list[str] = []

    def resolve(identity: str) -> JobRiskMeasurement:
        """Return the exact source and track the explicit acceptance boundary.

        Args:
            identity: Stable selected assessment identity, separate from labels.

        Returns:
            The existing zero measurement without calculation or mutation.
        """
        calls.append(identity)
        return zero

    picker = JobValuePicker(
        (
            CopySource("W01", "Ruiz, Ana", (standalone, workplace)),
            CopySource("W02", "Silva, Bruno", (missing,)),
        ),
        AssessmentKind.LIFFT,
        load_icons(),
        Language.ENGLISH,
        DecimalConvention.POINT,
        resolve,
        worker_sources=True,
        project_id="project",
        units=MeasurementSystem.METRIC,
    )
    try:
        assert picker.source_combo.count() == 2
        assert {
            token
            for token, button in picker.alphabet_buttons.items()
            if button.isEnabled()
        } == {"All", "R", "S"}
        assert picker.use_button.isEnabled()
        leaf = picker.tree.topLevelItem(0)
        assert (
            leaf.background(3).color().name()
            == job_damage_color(AssessmentKind.LIFFT, 0).lower()
        )
        parent = picker.tree.topLevelItem(1)
        picker.tree.setCurrentItem(parent)
        assert not picker.use_button.isEnabled()
        for _ in range(4):
            parent = parent.child(0)
        picker.tree.setCurrentItem(parent)
        assert parent.data(0, Qt.ItemDataRole.UserRole) == workplace
        assert picker.use_button.isEnabled()
        picker.navigation_buttons[-1].click()
        assert picker.source_combo.currentData() == "W02"
        assert not picker.use_button.isEnabled()
        picker.search.setText("missing worker")
        assert picker.source_combo.count() == 0
        assert picker.tree.topLevelItemCount() == 0
        assert not picker.use_button.isEnabled()
        picker.search.clear()
        picker.alphabet_buttons["R"].click()
        assert picker.alphabet_buttons["S"].isEnabled()
        assert picker.alphabet_buttons["R"].isChecked()
        assert not picker.alphabet_buttons["B"].isEnabled()
        picker.alphabet_buttons["B"].click()
        assert picker.alphabet_buttons["R"].isChecked()
        assert picker.source_combo.count() == 1
        assert picker.source_combo.currentData() == "W01"
        picker.alphabet_buttons["All"].click()
        picker.search.setText("w01")
        assert not calls
        picker.use_button.click()
        assert calls == ["standalone"]
        assert picker.selected is zero
        assert picker.result() == QDialog.Accepted
    finally:
        picker.close()


def test_cancel_and_unavailable_source_never_return_copied_values() -> None:
    """Cancellation skips resolution and stale acceptance keeps the dialog open.

    Args:
        None.

    Returns:
        None; failure cannot expose an earlier successful selection or source value.
    """
    value = JobRiskMeasurement(AssessmentKind.DUET, 0.1, 45.7)
    source = CopySource(
        "J1",
        "Packing",
        (CopyCandidate("J1", ("Job assessment values",), "Packing", "", value),),
    )

    def stale(identity: str) -> JobRiskMeasurement:
        """Simulate a source disappearing between catalog read and acceptance.

        Args:
            identity: Exact stale source identity.

        Returns:
            Never returns a measurement.

        Raises:
            ValueError: The previously visible source is no longer available.
        """
        raise ValueError(f"Unavailable source {identity}")

    picker = JobValuePicker(
        (source,),
        AssessmentKind.DUET,
        load_icons(),
        Language.SPANISH,
        DecimalConvention.COMMA,
        stale,
        worker_sources=False,
        project_id="project",
        units=MeasurementSystem.METRIC,
    )
    try:
        picker.use_button.click()
        assert picker.selected is None
        assert not picker.use_button.isEnabled()
        assert "Origen no disponible" in picker.source_summary.text()
        picker.cancel_button.click()
        assert picker.result() == QDialog.Rejected
        assert picker.selected is None
    finally:
        picker.close()


def test_task_disclosure_is_read_only_and_alphabet_tracks_selector_width() -> None:
    """Inspect copied task details without editing, resolving or accepting the source.

    Args:
        None.

    Returns:
        None; disclosure stays reversible and alphabet hover does not resize its strip.
    """
    from PyQt5.QtCore import QEvent
    from PyQt5.QtWidgets import QToolTip

    from ergotools.application.job_calculation import calculate_job_measurement
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask
    from ergotools.domain.model_units import MeasurementSystem

    value = calculate_job_measurement(
        "project",
        "job",
        LifftDraft(MeasurementSystem.METRIC, (LifftTask("t", 30, 49, 100),)),
        MeasurementSystem.METRIC,
    )
    calls: list[str] = []

    def resolve(identity: str) -> JobRiskMeasurement:
        """Track explicit acceptance separately from preview expansion.

        Args:
            identity: Exact assessment source identity.

        Returns:
            Existing calculated measurement without editing or calculation.
        """
        calls.append(identity)
        return value

    picker = JobValuePicker(
        (
            CopySource(
                "W01",
                "Ruiz, Ana",
                (CopyCandidate("source", ("Standalone assessment",), "", "", value),),
            ),
        ),
        AssessmentKind.LIFFT,
        load_icons(),
        Language.ENGLISH,
        DecimalConvention.POINT,
        resolve,
        worker_sources=True,
        project_id="project",
        units=MeasurementSystem.METRIC,
    )
    try:
        picker.resize(960, 640)
        picker.show()
        _APP.processEvents()
        assert picker.alphabet.width() == picker.source_combo.width()
        assert all(
            button.geometry().right() < picker.alphabet.width()
            for button in picker.alphabet_buttons.values()
        )
        source_node = picker.tree.currentItem()
        assert source_node.childCount() == 1
        source_node.setExpanded(True)
        _APP.processEvents()
        details = picker.task_details["source"]
        assert picker.tree.itemWidget(source_node.child(0), 0) is details
        assert details.grid.task_count == 1
        assert details.grid.inputs[0][0].isReadOnly()
        original = details.grid.source
        details.grid.inputs[0][0].setText("99")
        details.grid.inputs[0][0].editingFinished.emit()
        assert details.grid.source == original == value.source
        details.none_button.click()
        assert not picker.use_button.isEnabled()
        details.all_button.click()
        assert picker.use_button.isEnabled()
        button = picker.alphabet_buttons["R"]
        geometry = button.geometry()
        QToolTip.hideText()
        _APP.sendEvent(button, QEvent(QEvent.Type.Enter))
        assert not QToolTip.isVisible()
        assert button.geometry() == geometry
        _APP.sendEvent(button, QEvent(QEvent.Type.Leave))
        source_node.setExpanded(False)
        _APP.processEvents()
        assert not details.isVisible()
        assert not calls and picker.selected is None
        picker.cancel_button.click()
        assert not calls and picker.selected is None
    finally:
        picker.close()


def test_compact_disclosure_omits_blank_capacity_and_preserves_source_positions() -> (
    None
):
    """Only populated rows are offered; original numbers and matching outputs survive.

    Args:
        None.

    Returns:
        None; selection and disclosure never mutate the complete source.
    """
    from ergotools.application.job_calculation import calculate_job_measurement
    from ergotools.domain.assessments.lifft_draft import LifftDraft, LifftTask

    source = LifftDraft(
        MeasurementSystem.METRIC,
        (
            LifftTask("blank-1"),
            LifftTask("entered-2", 30, 49, 100),
            LifftTask("blank-3"),
            LifftTask("entered-4", 40, 60, 200),
            *(LifftTask(f"blank-{n}") for n in range(5, 16)),
        ),
    )
    value = calculate_job_measurement("project", "job", source, source.system)
    picker = JobValuePicker(
        (
            CopySource(
                "J1",
                "Packing",
                (
                    CopyCandidate(
                        "J1", ("Job assessment values",), "Packing", "", value
                    ),
                ),
            ),
        ),
        AssessmentKind.LIFFT,
        load_icons(),
        Language.ENGLISH,
        DecimalConvention.POINT,
        lambda _identity: value,
        worker_sources=False,
        project_id="project",
        units=source.system,
    )
    try:
        picker.show()
        node = picker.tree.currentItem()
        node.setExpanded(True)
        _APP.processEvents()
        details = picker.task_details["J1"]
        assert details.grid.task_count == 2
        assert [check.text() for check in details.grid.task_checks.values()] == [
            "2",
            "4",
        ]
        assert details.grid.selected_task_ids() == ("entered-2", "entered-4")
        assert [check.toolTip() for check in details.grid.task_checks.values()] == [
            "Copy task 2",
            "Copy task 4",
        ]
        assert details.preferred_height < 150
        assert details.all_button.height() == 18
        assert details.grid.inputs[0][0].height() <= 24
        assert details.grid.outputs[1][-2].toolTip() == str(
            value.task_results[3].damage
        )
        details.none_button.click()
        assert not picker.use_button.isEnabled()
        details.all_button.click()
        picker.use_button.click()
        assert picker.selected is not None
        assert tuple(t.task_id for t in picker.selected.source.tasks) == (
            "entered-2",
            "entered-4",
        )
        assert picker.selected.cumulative_damage == value.cumulative_damage
        assert len(value.source.tasks) == 15
    finally:
        picker.close()
