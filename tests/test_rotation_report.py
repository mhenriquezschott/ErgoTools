"""Frozen report semantics, real Qt preview/PDF and atomic export regression checks.

Synthetic exact 0/100 schedules give independent 50/50 expectations. All writes
are pytest-owned; UI/export never touches maintained samples or accepts a preview.
"""

import os
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QFileDialog, QWidget

from ergotools.application.rotation_report import (
    build_rotation_report,
    relative_index_change,
)
from ergotools.bootstrap import load_icons
from ergotools.domain.language import Language
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scenario import RotationRun
from ergotools.presentation.desktop.jrot_report_dialog import (
    JrotReportDialog,
    report_printer,
    save_report_pdf,
)
from ergotools.presentation.desktop.jrot_report_document import (
    ReportContent,
    report_document,
)
from tests.test_rotation_scenarios import scenario_with_run

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Keep one Qt lifetime for real report layout and vector PDF tests.
_APP = QApplication.instance() or QApplication([])


def report_run() -> RotationRun:
    """Return an unbalanced observation and independently balanced result.

    Args:
        None.

    Returns:
        All-tool frozen evidence: before 0/100, after 50/50, unchanged mean 50.
    """
    run = scenario_with_run().run
    assert run is not None
    a, b = (t.key for t in run.inputs.targets)
    baseline = (WorkerRotation("W1", (a, a)), WorkerRotation("W2", (b, b)))
    return replace(run, inputs=replace(run.inputs, baseline=baseline))


def test_frozen_report_keeps_values_and_truthful_preview_stale_flags() -> None:
    """Reports preserve exact evidence and expose changes without re-solving.

    Args:
        None.

    Returns:
        None; original immutable baseline, results and coefficients remain identical.
    """
    run = report_run()
    report = build_rotation_report(
        "Plant <A>", "Trial", run, preview=True, current=False
    )
    assert report.run is run and report.preview and not report.current
    for comparison in report.comparisons:
        assert comparison.before is not None
        assert comparison.before.values == (0, 100)
        assert comparison.after.values == (50, 50)
        assert comparison.changes == (50, -50)
    html = ReportContent(report, Language.ENGLISH).html()
    assert "PREVIEW" in html and "STALE" in html and "Plant &lt;A&gt;" in html
    assert "Increases: LiFFT, DUET, ST" in html
    assert "-50.00%" in html
    assert relative_index_change(100, 50) == -50
    assert relative_index_change(50, 60) == 20
    assert relative_index_change(0, 0) is None
    assert relative_index_change(0, 50) is None


def test_absent_before_and_unknown_model_are_not_fabricated() -> None:
    """No-start reports use missing markers; unsupported evidence refuses export.

    Args:
        None.

    Returns:
        None; displayed zero is never a substitute for an absent observation.
    """
    run = report_run()
    run = replace(run, inputs=replace(run.inputs, baseline=None))
    report = build_rotation_report("Plant", "Trial", run, preview=False, current=True)
    assert all(c.before is None and c.changes is None for c in report.comparisons)
    html = ReportContent(report, Language.ENGLISH).html()
    assert "No starting schedule" in html and "—" in html
    with pytest.raises(ValueError, match="read-only"):
        build_rotation_report(
            "Plant",
            "Trial",
            replace(run, contract_version=99),
            preview=False,
            current=False,
        )
    with pytest.raises(ValueError, match="names"):
        build_rotation_report("", "Trial", run, preview=False, current=True)


@pytest.mark.parametrize("language", list(Language))
def test_real_pdf_and_preview_use_same_two_page_report(
    tmp_path: Path, language: Language
) -> None:
    """Qt produces vector PDF pages; preview controls and cancellation are read-only.

    Args:
        tmp_path: Isolated export folder.
        language: English/Spanish captions and report text.

    Returns:
        None; two-page supervisor/detail structure survives export and preview zoom.
    """
    report = build_rotation_report(
        "Plant", "Morning packing", report_run(), preview=False, current=True
    )
    document = report_document(report, language)
    target = tmp_path / "report.pdf"
    save_report_pdf(document, target)
    assert target.read_bytes().startswith(b"%PDF-")
    page_size = report_printer().paperRect()
    assert page_size.width() < page_size.height()
    assert document.pageCount() == 2
    assert "50.00" in document.toPlainText()
    parent = QWidget()
    dialog = JrotReportDialog(report, language, load_icons(), parent)
    try:
        dialog.show()
        QTest.qWait(50)
        assert dialog.preview.pageCount() == 2
        factor = dialog.preview.zoomFactor()
        dialog.preview.zoomIn()
        assert dialog.preview.zoomFactor() > factor
        dialog.next_page()
        assert dialog.preview.currentPage() == 2
        dialog.previous_page()
        assert dialog.preview.currentPage() == 1
        with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
            dialog.save_pdf()
        assert tuple(tmp_path.iterdir()) == (target,)
        with patch.object(
            QFileDialog,
            "getSaveFileName",
            return_value=(str(tmp_path / "chosen"), "PDF (*.pdf)"),
        ):
            dialog.save_pdf()
        assert (tmp_path / "chosen.pdf").read_bytes().startswith(b"%PDF-")
        assert dialog.report is report and dialog.report.run is report.run
    finally:
        dialog.close()
        dialog.deleteLater()
        parent.deleteLater()
        _APP.processEvents()


def test_failed_export_preserves_existing_file_and_removes_staging(
    tmp_path: Path,
) -> None:
    """A renderer/publish failure cannot replace the old PDF with partial bytes.

    Args:
        tmp_path: Isolated target and sibling staging folder.

    Returns:
        None; the old target remains byte-identical after either failure.
    """
    report = build_rotation_report(
        "Plant", "Trial", report_run(), preview=False, current=True
    )
    document = report_document(report, Language.ENGLISH)
    target = tmp_path / "report.pdf"
    target.write_bytes(b"previous report")
    for method in ("paint_report", "os.replace"):
        with (
            patch(
                "ergotools.presentation.desktop.jrot_report_dialog." + method,
                side_effect=OSError("test failure"),
            ),
            pytest.raises(OSError),
        ):
            save_report_pdf(document, target)
        assert target.read_bytes() == b"previous report"
        assert tuple(tmp_path.iterdir()) == (target,)


@pytest.mark.parametrize("count", (1, 2, 3))
def test_selected_tools_and_zero_start_have_no_invented_relative_percentage(
    count: int,
) -> None:
    """Only analyzed tools appear; a zero maximum cannot produce a relative gain.

    Args:
        count: Number of selected tools in the frozen optimization evidence.

    Returns:
        None; missing relative percentages stay absent and risk warnings stay scoped.
    """
    run = report_run()
    tools = run.inputs.tools[:count]
    run = replace(
        run,
        inputs=replace(run.inputs, tools=tools),
        coefficients=tuple(
            replace(c, measurement=replace(c.measurement, probability_percent=0))
            for c in run.coefficients
            if c.measurement.kind in tools
        ),
    )
    report = build_rotation_report("Plant", "Zero", run, preview=False, current=True)
    content = ReportContent(report, Language.ENGLISH)
    assert len(report.comparisons) == count
    assert "—%" not in content.key_results()
    assert "0.00%" not in content.key_results()
    assert "No selected Job exceeds" in content.warnings()


def test_incomplete_pdf_is_not_published(tmp_path: Path) -> None:
    """A plausible PDF header without its completion trailer cannot replace a file.

    Args:
        tmp_path: Isolated export folder.

    Returns:
        None; the old report and directory contents survive a truncated render.
    """
    report = build_rotation_report(
        "Plant", "Trial", report_run(), preview=False, current=True
    )
    document = report_document(report, Language.ENGLISH)
    target = tmp_path / "report.pdf"
    target.write_bytes(b"old report")

    def incomplete(document: object, printer: object) -> None:
        """Simulate Qt returning after a truncated output write.

        Args:
            document: Unused owned document argument.
            printer: Real output device carrying the temporary destination.

        Returns:
            None; intentionally leaves incomplete bytes for the publication guard.
        """
        from PyQt5.QtPrintSupport import QPrinter

        assert isinstance(printer, QPrinter)
        Path(printer.outputFileName()).write_bytes(b"%PDF-" + b"x" * 200)

    with (
        patch(
            "ergotools.presentation.desktop.jrot_report_dialog.paint_report",
            side_effect=incomplete,
        ),
        pytest.raises(OSError, match="complete PDF"),
    ):
        save_report_pdf(document, target)
    assert target.read_bytes() == b"old report"
    assert tuple(tmp_path.iterdir()) == (target,)
