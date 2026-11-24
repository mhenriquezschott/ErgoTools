"""Owned JROT report preview and atomic explicit PDF export using existing Qt.

The preview and PDF share one immutable report/document. QPrintPreviewWidget draws
that document inside ErgoTools without an embedded browser or extra PDF dependency.
Only Save PDF writes an external file; no project data or acceptance state changes.
"""

import logging
import os
import re
from collections.abc import Mapping
from pathlib import Path
from tempfile import NamedTemporaryFile

from PyQt5.QtCore import QRectF, QSignalBlocker, QSize, QSizeF, Qt
from PyQt5.QtGui import QFont, QIcon, QPainter, QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewWidget
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.rotation_report import RotationReport
from ergotools.domain.language import Language
from ergotools.presentation.desktop.jrot_report_document import report_document
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme


def report_printer() -> QPrinter:
    """Use a PDF device so preview never depends on installed physical printers.

    Args:
        None.

    Returns:
        High-resolution A4 portrait device with consistent report margins.
    """
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setResolution(144)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setCreator("ErgoTools")
    printer.setPageSize(QPrinter.PageSize.A4)
    printer.setOrientation(QPrinter.Orientation.Portrait)
    printer.setPageMargins(12, 10, 12, 12, QPrinter.Unit.Millimeter)
    return printer


def paint_report(document: QTextDocument, printer: QPrinter) -> None:
    """Render identical paginated content and page numbers to preview or PDF.

    Args:
        document: Owned immutable-content rich text, laid out for this paint device.
        printer: PDF or Qt preview device with the standard report page geometry.

    Returns:
        None; only the supplied output device receives rendered pages.

    Raises:
        OSError: Qt cannot start painting or allocate a subsequent page.
    """
    width, height = (
        printer.pageRect(QPrinter.Unit.DevicePixel).size().width(),
        printer.pageRect(QPrinter.Unit.DevicePixel).size().height(),
    )
    footer = printer.resolution() * 0.24
    content_height = height - footer
    layout = document.documentLayout()
    if layout is None:
        raise OSError("Qt could not create the report layout.")
    layout.setPaintDevice(printer)
    document.setPageSize(QSizeF(width, content_height))
    printer.setDocName(
        document.metaInformation(QTextDocument.MetaInformation.DocumentTitle)
    )
    painter = QPainter(printer)
    if not painter.isActive():
        raise OSError("Qt could not start the report renderer.")
    try:
        count = document.pageCount()
        for page in range(count):
            if page and not printer.newPage():
                raise OSError("Qt could not allocate the next report page.")
            painter.save()
            painter.translate(0, -page * content_height)
            document.drawContents(
                painter, QRectF(0, page * content_height, width, content_height)
            )
            painter.restore()
            painter.setFont(QFont("Arial", 9))
            painter.drawText(
                QRectF(0, content_height + 3, width, footer - 3),
                Qt.AlignmentFlag.AlignRight,
                f"JROT · {page + 1} / {count}",
            )
    finally:
        painter.end()


def save_report_pdf(document: QTextDocument, destination: Path) -> None:
    """Publish a completed PDF atomically without leaving a truncated old report.

    Args:
        document: The same immutable-content document used by preview.
        destination: Explicit user-chosen local PDF path; parent must already exist.

    Returns:
        None after replacing the target with a verified PDF container.

    Raises:
        OSError: Target is inaccessible or Qt fails to produce a nonempty PDF.
    """
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            prefix=".ergotools-report-",
            suffix=".pdf",
            dir=destination.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
        printer = report_printer()
        printer.setOutputFileName(str(temporary))
        paint_report(document, printer)
        if printer.printerState() == QPrinter.PrinterState.Error:
            raise OSError("Qt could not render the report PDF.")
        with temporary.open("rb") as stream:
            valid = stream.read(5) == b"%PDF-"
        if temporary.stat().st_size >= 100:
            with temporary.open("rb") as stream:
                stream.seek(-100, 2)
                valid = valid and stream.read().rstrip().endswith(b"%%EOF")
        if not valid or temporary.stat().st_size < 100:
            raise OSError("Qt did not produce a complete PDF report.")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class JrotReportDialog(QDialog):
    """Scrollable/zoomable report pages with explicit file Save and local status."""

    def __init__(
        self,
        report: RotationReport,
        language: Language,
        icons: Mapping[str, QIcon],
        parent: QWidget,
    ) -> None:
        """Compose a modal snapshot preview without repository or solver access.

        Args:
            report: Exact validated evidence, including preview and stale flags.
            language: English/Spanish captions and report content.
            icons: Existing packaged icons, shared with the owning application.
            parent: JROT dialog lifetime owner.

        Returns:
            None; no PDF is written until the user chooses Save PDF.
        """
        super().__init__(parent)
        self.report, self.language = report, language
        self.setWindowTitle(self.text("JROT report", "Informe JROT"))
        screen = self.screen()
        area = screen.availableGeometry() if screen is not None else None
        self.resize(
            min(1180, area.width() - 32) if area is not None else 1180,
            min(850, area.height() - 48) if area is not None else 850,
        )
        apply_dialog_theme(self)
        root = QVBoxLayout(self)
        heading = QLabel(self.text("JROT rotation report", "Informe de rotación JROT"))
        heading.setStyleSheet("font-size:20px;font-weight:bold;color:#0B326C;")
        root.addWidget(heading)
        context = QLabel(report.project_title + " · " + report.rotation_name)
        context.setTextFormat(Qt.TextFormat.PlainText)
        context.setWordWrap(True)
        root.addWidget(context)
        self.status = QLabel(
            self.text(
                (
                    "Preview the pages, then Save PDF. This does not save the project"
                    " or keep an optimization preview."
                ),
                (
                    "Revise las páginas y guarde el PDF. Esto no guarda el proyecto "
                    "ni conserva una optimización previa."
                ),
            )
        )
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.status.setStyleSheet("background:#EAF7F9;color:#0B326C;padding:8px;")
        root.addWidget(self.status)
        self.document = report_document(report, language, self)
        self.printer = report_printer()
        self.preview = QPrintPreviewWidget(self.printer, self)
        self.preview.paintRequested.connect(self.paint_preview)
        bar = QHBoxLayout()
        self.page = QSpinBox()
        self.page.setMinimum(1)
        self.page.setToolTip(
            self.text("Go to report page", "Ir a la página del informe")
        )
        self.page.valueChanged.connect(self.preview.setCurrentPage)
        self.pages = QLabel()
        for en, es, icon, action in (
            ("Previous", "Anterior", "previous", self.previous_page),
            ("Next", "Siguiente", "next", self.next_page),
            ("Zoom in", "Acercar", "zoom_in", lambda: self.preview.zoomIn()),
            ("Zoom out", "Alejar", "zoom_out", lambda: self.preview.zoomOut()),
            ("Fit page", "Ajustar página", "actual_size", self.preview.fitInView),
        ):
            button = QPushButton(icons[icon], self.text(en, es))
            button.setIconSize(QSize(22, 22))
            button.setToolTip(self.text(en, es))
            button.clicked.connect(action)
            bar.addWidget(button)
        bar.addStretch(1)
        bar.addWidget(self.page)
        bar.addWidget(self.pages)
        root.addLayout(bar)
        root.addWidget(self.preview, 1)
        self.preview.previewChanged.connect(self.sync_page)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.save_button = QPushButton(
            icons["export"], self.text("Save PDF…", "Guardar PDF…")
        )
        self.save_button.setIconSize(QSize(26, 26))
        self.save_button.setToolTip(
            self.text(
                "Save these report pages as a PDF file",
                "Guardar estas páginas como un archivo PDF",
            )
        )
        self.save_button.clicked.connect(self.save_pdf)
        bottom.addWidget(self.save_button)
        close = QPushButton(icons["close"], self.text("Close", "Cerrar"))
        close.setIconSize(QSize(24, 24))
        close.clicked.connect(self.accept)
        bottom.addWidget(close)
        root.addLayout(bottom)
        self.preview.fitInView()

    def text(self, english: str, spanish: str) -> str:
        """Choose owned UI captions while retaining literal record labels.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Caption for the active report language.
        """
        return spanish if self.language is Language.SPANISH else english

    def paint_preview(self, printer: QPrinter) -> None:
        """Contain preview rendering failures inside the owned dialog.

        Args:
            printer: Qt-owned preview device for the current requested layout.

        Returns:
            None; an error updates local status instead of escaping a Qt signal.
        """
        try:
            paint_report(self.document, printer)
        except OSError:
            logging.getLogger(__name__).exception("Unable to preview JROT report")
            self.status.setText(
                self.text("Report preview failed.", "Falló la vista del informe.")
            )

    def sync_page(self) -> None:
        """Refresh page navigation after a preview layout or zoom operation.

        Args:
            None.

        Returns:
            None; signals are blocked while reflecting the current page.
        """
        with QSignalBlocker(self.page):
            self.page.setMaximum(max(1, self.preview.pageCount()))
            self.page.setValue(self.preview.currentPage())
        self.pages.setText("/ " + str(self.preview.pageCount()))

    def previous_page(self) -> None:
        """Move to the prior page without passing the first page.

        Args:
            None.

        Returns:
            None; PDF content stays unchanged.
        """
        self.preview.setCurrentPage(max(1, self.preview.currentPage() - 1))

    def next_page(self) -> None:
        """Move to the next page without passing the last page.

        Args:
            None.

        Returns:
            None; PDF content stays unchanged.
        """
        self.preview.setCurrentPage(
            min(self.preview.pageCount(), self.preview.currentPage() + 1)
        )

    def save_pdf(self) -> None:
        """Choose a native destination and publish the currently previewed snapshot.

        Args:
            None.

        Returns:
            None; cancellation and export failures preserve project and existing files.
        """
        slug = (
            re.sub(r"[^\w-]+", "-", self.report.rotation_name).strip("-") or "rotation"
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.text("Save JROT report", "Guardar informe JROT"),
            slug + ".pdf",
            "PDF (*.pdf)",
        )
        if not path:
            return
        destination = Path(path)
        if destination.suffix.lower() != ".pdf":
            destination = destination.with_suffix(destination.suffix + ".pdf")
            if (
                destination.exists()
                and QMessageBox.question(
                    self,
                    self.text("Replace PDF?", "¿Reemplazar PDF?"),
                    str(destination),
                )
                != QMessageBox.StandardButton.Yes
            ):
                return
        try:
            save_report_pdf(self.document, destination)
        except OSError:
            logging.getLogger(__name__).exception("Unable to save JROT report PDF")
            QMessageBox.critical(
                self,
                self.text("Report not saved", "Informe no guardado"),
                self.text(
                    "The PDF could not be saved. Check the folder and permissions.",
                    "No se pudo guardar el PDF. Revise la carpeta y los permisos.",
                ),
            )
            return
        self.status.setText(
            self.text("PDF saved: ", "PDF guardado: ") + str(destination)
        )
