"""Original JROT comparison windows over frozen schedules and current Job values.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.rotation_pool import RotationPool
from ergotools.application.rotation_preparation import prepare_rotation_problem
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.presentation.desktop.rotation_display import rotation_text
from ergotools.presentation.desktop.rotation_result_table import render_rotation_result
from ergotools.presentation.desktop.theme.jrot import JROT_STYLE


def rotation_tool_label(kind: AssessmentKind) -> str:
    """Keep branded tool names independent of persisted enum values.

    Args:
        kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
            captions are not keys.

    Returns:
        Unchanged branded caption corresponding to the typed ergonomic tool.
    """
    return {
        AssessmentKind.LIFFT: "LiFFT",
        AssessmentKind.DUET: "DUET",
        AssessmentKind.TST: "ST",
    }[kind]


class RotationComparisonDialog(QDialog):
    """Show the source side-by-side or tabbed comparison without persistence.

    The caller supplies complete immutable schedules and owns result application. This
    normal child window emits intent only; it never discovers parent controls, queries
    current Job values, parses cells or writes project data.
    """

    apply_requested = pyqtSignal()

    def __init__(
        self,
        current: RotationScheme,
        optimized: RotationScheme,
        pool: RotationPool,
        icons: Mapping[str, QIcon],
        *,
        selected_kind: AssessmentKind,
        all_tools: bool = False,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build original dimensions/layouts; reject missing displayed risks.

        Args:
            current: Complete frozen current schedule used for comparison.
            optimized: Validated frozen optimized schedule with exact pool/Job
                links.
            pool: Immutable worker/target/current Job values against which grid choices
                and schedules are validated.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            selected_kind: Primary selected ergonomic tool used by the comparison view.
            all_tools: True selects HiGHS multi-tool optimization; False selects CBC
                single-tool optimization.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.

        Raises:
            ValueError: A displayed scheduled Job lacks its tool probability.
        """
        kinds = tuple(
            kind for kind in AssessmentKind if all_tools or kind is not selected_kind
        )
        for scheme in (current, optimized):
            prepare_rotation_problem(scheme, pool, kinds, time_limit_seconds=60)
        super().__init__(parent)
        self.language = language
        self.setObjectName("jrotComparisonWindow")
        self.setWindowFlags(Qt.WindowType.Window)
        self.setStyleSheet(JROT_STYLE)
        self.setWindowTitle(
            self.text(
                "All Tools - Optimized vs Current Rotation"
                if all_tools
                else "Rotation Comparison (Non-Optimized Tools)",
                "Todas las herramientas: rotación optimizada y actual"
                if all_tools
                else "Comparación de rotación (otras herramientas)",
            )
        )
        self.resize(1400 if all_tools else 1300, 1000 if all_tools else 900)
        self.setMinimumSize(1000 if all_tools else 960, 700 if all_tools else 650)
        layout = QVBoxLayout(self)
        title = QLabel(
            self.text(
                "All-Tool Rotation Comparison" if all_tools else "Rotation Comparison",
                "Comparación de todas las herramientas"
                if all_tools
                else "Comparación de rotación",
            )
        )
        title.setObjectName("dialogTitle")
        label = (
            rotation_tool_label(optimized.primary_kind)
            if optimized.primary_kind
            else self.text("All-tool", "Todas las herramientas")
        )
        subtitle = QLabel(
            self.text(
                "Compare current and optimized risk distributions across LiFFT, "
                "DUET, and Shoulder Tool."
                if all_tools
                else f"Evaluate the {label}-optimized schedule "
                "using the other ergonomic tools.",
                "Compare la distribución del riesgo actual y optimizado "
                "en LiFFT, DUET y Hombro."
                if all_tools
                else f"Evalúe la rotación optimizada ({label}) "
                "con las otras herramientas ergonómicas.",
            )
        )
        subtitle.setObjectName("supportingText")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        self.tabs: QTabWidget | None = None
        self.apply_button: QPushButton | None = None
        self.tables: dict[AssessmentKind, tuple[QTableWidget, QTableWidget]] = {}
        if all_tools:
            self.tabs = QTabWidget()
            self.tabs.setObjectName("comparisonTabs")
            layout.addWidget(self.tabs, 1)
        for kind in kinds:
            tool = rotation_tool_label(kind)
            section = QWidget()
            row = QHBoxLayout(section)
            if not all_tools:
                row.setContentsMargins(0, 4, 0, 4)
            pair = []
            for scheme, is_optimized in ((current, False), (optimized, True)):
                heading = self.text(
                    f"Current Rotation for {tool}", f"Rotación actual para {tool}"
                )
                if is_optimized:
                    heading = (
                        self.text(
                            f"Optimized Rotation for {tool}",
                            f"Rotación optimizada para {tool}",
                        )
                        if all_tools
                        else self.text(
                            f"{label} Optimized Rotation Applied to {tool}",
                            f"Rotación optimizada ({label}) aplicada a {tool}",
                        )
                    )
                panel_title = QLabel(heading)
                panel_title.setObjectName("panelTitle")
                panel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                font = QFont()
                font.setBold(True)
                panel_title.setFont(font)
                table = QTableWidget()
                render_rotation_result(table, scheme, pool, kind, language)
                header = table.horizontalHeader()
                assert header is not None
                header.setMinimumSectionSize(96)
                if table.columnCount() <= 5:
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                else:
                    header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                    table.setColumnWidth(0, 100)
                    for column in range(1, table.columnCount() - 1):
                        table.setColumnWidth(column, 110)
                    table.setColumnWidth(table.columnCount() - 1, 100)
                for index in range(table.rowCount()):
                    worker = table.item(index, 0)
                    assert worker is not None
                    worker.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                panel = QVBoxLayout()
                panel.addWidget(panel_title)
                panel.addWidget(table)
                if all_tools:
                    row.addLayout(panel)
                else:
                    container = QWidget()
                    container.setLayout(panel)
                    row.addWidget(container)
                pair.append(table)
            self.tables[kind] = (pair[0], pair[1])
            if self.tabs is not None:
                tab_label = (
                    self.text("Shoulder", "Hombro")
                    if kind is AssessmentKind.TST
                    else tool
                )
                self.tabs.addTab(section, tab_label)
            else:
                layout.addWidget(section)
        if all_tools:
            self.apply_button = QPushButton(
                self.text(
                    "Apply This Optimized Rotation to Current Tool",
                    "Aplicar esta rotación optimizada a la herramienta actual",
                )
            )
            self.apply_button.setFixedHeight(40)
            self.apply_button.setObjectName("primaryButton")
            self.apply_button.setIcon(icons["apply_rotation"])
            self.apply_button.setIconSize(QSize(28, 28))
            self.apply_button.setAutoDefault(False)
            self.apply_button.clicked.connect(self.apply_requested.emit)
            layout.addWidget(self.apply_button)

    def text(self, english: str, spanish: str) -> str:
        """Select localized UI text without changing schedule/Job identities.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return rotation_text(english, spanish, self.language)
