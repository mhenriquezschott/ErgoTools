"""Original PLOT station warning details using typed saved observations.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QBrush, QColor, QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.plot_summaries import StationHighlight
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.risk import classify_probability
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.localization import Translator


class PlotHighlightDialog(QDialog):
    """Present original station/count/average/maximum columns without storage I/O."""

    def __init__(
        self,
        details: tuple[StationHighlight, ...],
        tool: AssessmentKind,
        icons: Mapping[str, QIcon],
        *,
        job_view: bool = False,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Retain reference dialog geometry, table styling and close interaction.

        Args:
            details: Saved station highlight observations for the current filtered
                dataset.
            tool: Selected ergonomic tool whose saved risk evidence is presented.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            job_view: True shows job-placement warnings rather than individual-worker
                warnings.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.language = language
        tool_name = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: self.text("Shoulder", "Hombro"),
        }[tool]
        subject = (
            self.text("Job", "trabajo")
            if job_view
            else self.text("worker", "trabajador")
        )
        self.setWindowTitle(
            self.text(
                f"PLOT {tool_name} Highlight Details",
                f"PLOT {tool_name}: detalles destacados",
            )
        )
        self.resize(760, 420)
        self.setMinimumSize(720, 390)
        self.setStyleSheet(PLOT_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(10)
        title = QLabel(
            self.text(
                f"{tool_name} High-risk station details",
                f"{tool_name}: estaciones de alto riesgo",
            )
        )
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        subtitle = QLabel(
            self.text(
                f"Stations containing one or more {subject} results above 50% "
                "in the current filter scope.",
                f"Estaciones con resultados de {subject} superiores al 50% "
                "en los filtros actuales.",
            )
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        self.table = QTreeWidget()
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(True)
        self.table.setHeaderLabels(
            (
                self.text("Station", "Estación"),
                self.text("High-risk Jobs", "Trabajos de alto riesgo")
                if job_view
                else self.text("High-risk workers", "Trabajadores de alto riesgo"),
                self.text("Average outcome", "Resultado medio"),
                self.text("Maximum outcome", "Resultado máximo"),
            )
        )
        header = self.table.header()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 4):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setToolTip(
            self.text(
                "High-risk station results calculated from the active PLOT filters.",
                "Resultados de alto riesgo de los filtros PLOT activos.",
            )
        )
        for detail in details:
            station = detail.station.station_id
            if sum(row.station.station_id == station for row in details) > 1:
                station = " / ".join(
                    (
                        detail.station.plant_name,
                        detail.station.section_name,
                        detail.station.line_name,
                        station,
                    )
                )
            item = QTreeWidgetItem(
                (
                    station,
                    str(detail.count),
                    f"{detail.average_percent:.1f}%",
                    f"{detail.maximum_percent:.1f}%",
                )
            )
            item.setToolTip(
                0,
                " / ".join(
                    (
                        detail.station.plant_name,
                        detail.station.section_name,
                        detail.station.line_name,
                        detail.station.station_id,
                    )
                ),
            )
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
            for column, value in (
                (2, detail.average_percent),
                (3, detail.maximum_percent),
            ):
                item.setTextAlignment(
                    column, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                appearance = RISK_APPEARANCES[classify_probability(value)]
                color = QColor(appearance.color_hex)
                luminance = (
                    0.2126 * color.redF()
                    + 0.7152 * color.greenF()
                    + 0.0722 * color.blueF()
                )
                foreground = QColor("#102A43" if luminance > 0.58 else "#FFFFFF")
                item.setBackground(column, QBrush(color))
                item.setForeground(column, QBrush(foreground))
                severity = Translator(language).text(appearance.message_key)
                item.setToolTip(column, f"{severity}: {value:.1f}%")
            self.table.addTopLevelItem(item)
        root.addWidget(self.table, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.close_button = QPushButton(self.text("Close", "Cerrar"))
        self.close_button.setIcon(icons["close"])
        self.close_button.setIconSize(QSize(22, 22))
        self.close_button.setToolTip(
            self.text("Close the highlight details.", "Cerrar los detalles destacados.")
        )
        self.close_button.clicked.connect(self.accept)
        buttons.addWidget(self.close_button)
        root.addLayout(buttons)

    def text(self, english: str, spanish: str) -> str:
        """Translate controls without translating saved station identities.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english
