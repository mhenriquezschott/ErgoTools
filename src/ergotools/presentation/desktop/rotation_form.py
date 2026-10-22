"""Original responsive JROT form controls, independent of storage and solvers.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QIcon, QIntValidator
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QStyledItemDelegate,
    QTableWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.presentation.desktop.rotation_display import rotation_text
from ergotools.presentation.desktop.theme.jrot import JROT_STYLE


class RotationForm(QDialog):
    """Build the source 1480x900 form with its 1480x740 minimum and original assets.

    This view constructs controls only. The containing controller owns catalog access,
    scheme commands and modal child dialog lifetimes.
    """

    def __init__(
        self,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Arrange original setup, workplace path, two panels and bottom rail.

        Args:
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.icons = icons
        self.language = language
        self.setObjectName("jrotWindow")
        self.setWindowTitle(
            self.text(
                "Job Rotation Optimization Tool (JROT)",
                "Herramienta de rotación de trabajos (JROT)",
            )
        )
        self.setWindowIcon(icons["jrot"])
        self.resize(1480, 900)
        self.setMinimumSize(1480, 740)
        self.setStyleSheet(JROT_STYLE)
        font = QFont("Segoe UI")
        font.setPixelSize(12)
        self.setFont(font)
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)
        self.title_row = QHBoxLayout()
        self.title = QLabel(
            self.text(
                "Job Rotation Optimization Tool", "Herramienta de rotación de trabajos"
            )
        )
        self.title.setObjectName("dialogTitle")
        self.subtitle = QLabel(
            self.text(
                "Define, optimize, and compare job rotation schemes",
                "Defina, optimice y compare esquemas de rotación",
            )
        )
        self.subtitle.setObjectName("supportingText")
        self.title_row.addWidget(self.title)
        self.title_row.addSpacing(12)
        self.title_row.addWidget(self.subtitle)
        self.title_row.addStretch(1)
        root.addLayout(self.title_row)
        self.setup_group = QGroupBox(
            self.text("Rotation setup", "Configuración de rotación")
        )
        filters = QVBoxLayout(self.setup_group)
        filters.setContentsMargins(10, 8, 10, 10)
        filters.setSpacing(8)
        top = QHBoxLayout()
        top.setSpacing(10)
        risk_group = QGroupBox(self.text("Risk basis", "Base de riesgo"))
        risk_layout = QHBoxLayout(risk_group)
        risk_layout.setContentsMargins(8, 8, 8, 8)
        risk_layout.setSpacing(0)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_buttons: dict[AssessmentKind, QPushButton] = {}
        for kind, label, spanish, icon in (
            (AssessmentKind.LIFFT, "LiFFT", "LiFFT", "lifft"),
            (AssessmentKind.DUET, "DUET", "DUET", "duet"),
            (AssessmentKind.TST, "Shoulder", "Hombro", "shoulder"),
        ):
            button = self.button(self.text(label, spanish), icon)
            button.setObjectName("toolSegment")
            button.setCheckable(True)
            button.setIconSize(QSize(24, 24))
            button.setMinimumWidth(122)
            button.setToolTip(
                self.text(
                    f"Use {label} job-risk measurements.",
                    f"Usar mediciones de riesgo de {spanish}.",
                )
            )
            self.tool_group.addButton(button)
            self.tool_buttons[kind] = button
            risk_layout.addWidget(button)
        self.tool_buttons[AssessmentKind.LIFFT].setChecked(True)
        top.addWidget(risk_group, 0)
        workplace = QGroupBox(self.text("Workplace", "Lugar de trabajo"))
        workplace.setMinimumHeight(88)
        places = QHBoxLayout(workplace)
        places.setContentsMargins(10, 10, 10, 8)
        places.setSpacing(8)
        scope_mode = QFrame(workplace)
        mode = QVBoxLayout(scope_mode)
        mode.setContentsMargins(0, 0, 0, 0)
        mode.setSpacing(2)
        scope_label = QLabel(self.text("Rotation scope", "Ámbito de rotación"))
        scope_label.setObjectName("workplaceScopeType")
        mode.addWidget(scope_label)
        scope_buttons = QHBoxLayout()
        scope_buttons.setSpacing(0)
        self.scope_group = QButtonGroup(self)
        self.scope_group.setExclusive(True)
        self.all_scope_button = self.button(self.text("All Jobs", "Todos"))
        self.workplace_scope_button = self.button(self.text("Workplace", "Lugar"))
        for button in (self.all_scope_button, self.workplace_scope_button):
            button.setObjectName("scopeSegment")
            button.setCheckable(True)
            self.scope_group.addButton(button)
            scope_buttons.addWidget(button)
        self.all_scope_button.setFixedWidth(82)
        self.workplace_scope_button.setFixedWidth(110)
        self.all_scope_button.setChecked(True)
        self.all_scope_button.setToolTip(
            self.text(
                "Use all active Jobs and Workers in the organization.",
                "Usar trabajos activos y trabajadores de la organización.",
            )
        )
        self.workplace_scope_button.setToolTip(
            self.text(
                "Use active Job placements and Worker assignments "
                "in selected Stations and one Shift.",
                "Usar puestos y asignaciones activos en estaciones y un turno.",
            )
        )
        mode.addLayout(scope_buttons)
        places.addWidget(scope_mode)
        path = QWidget(workplace)
        path_layout = QHBoxLayout(path)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(5)
        self.scope_values: list[QLabel] = []
        for index, (english, spanish, path_icon, width) in enumerate(
            (
                ("Plant", "Planta", None, 118),
                ("Section", "Sección", "section", 88),
                ("Line", "Línea", "line", 70),
                ("Station", "Estación", "station", 90),
                ("Shift", "Turn.", "shift", 68),
            )
        ):
            if index:
                arrow = QLabel(path)
                arrow.setPixmap(
                    icons["next"]
                    .pixmap(icons["next"].availableSizes()[0])
                    .scaled(
                        14,
                        24,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                arrow.setFixedSize(16, 26)
                arrow.setToolTip(
                    self.text(
                        "The next level is contained within "
                        "the preceding workplace level.",
                        "Cada nivel está contenido en el nivel laboral anterior.",
                    )
                )
                path_layout.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)
            block = QFrame(path)
            block.setObjectName(
                "workplacePlantScope" if not index else "workplaceScopeBlock"
            )
            block.setMinimumWidth(
                72 if index == 4 and language is Language.SPANISH else width
            )
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(6, 2, 6, 2)
            block_layout.setSpacing(0)
            heading_row = QHBoxLayout()
            heading_row.setContentsMargins(0, 0, 0, 0)
            heading_row.setSpacing(3)
            if path_icon:
                entity = QLabel(block)
                entity.setPixmap(icons[path_icon].pixmap(QSize(20, 20)))
                entity.setFixedSize(21, 21)
                heading_row.addWidget(entity)
            heading = QLabel(self.text(english, spanish), block)
            heading.setObjectName("workplaceScopeType")
            heading.setToolTip(self.text(english, "Turno" if index == 4 else spanish))
            if language is Language.SPANISH:
                heading.ensurePolished()
                block.setMinimumWidth(
                    max(
                        width,
                        heading.sizeHint().width() + 12 + (24 if path_icon else 0),
                    )
                )
            heading_row.addWidget(heading)
            heading_row.addStretch(1)
            value = QLabel(self.text("All", "Todos"), block)
            value.setObjectName(
                "workplacePlantValue" if not index else "workplaceScopeValue"
            )
            self.scope_values.append(value)
            block_layout.addLayout(heading_row)
            block_layout.addWidget(value)
            path_layout.addWidget(block, 2 if not index else 1)
        path_layout.addStretch(1)
        self.choose_scope_button = self.button(
            self.text("Choose\nScope", "Elegir\námbito"), "station"
        )
        self.choose_scope_button.setIconSize(QSize(34, 34))
        self.choose_scope_button.setFixedSize(120, 52)
        self.choose_scope_button.setEnabled(False)
        self.choose_scope_button.setToolTip(
            self.text(
                "Select Stations and a Shift for this rotation scope.",
                "Seleccionar estaciones y un turno para esta rotación.",
            )
        )
        places.addWidget(path, 1)
        places.addWidget(self.choose_scope_button)
        top.addWidget(workplace, 1)
        scope_actions = QVBoxLayout()
        self.clear_scope_button = self.button(
            self.text("Clear Scope", "Limpiar ámbito"), "filter_reset"
        )
        self.apply_scope_button = self.button(
            self.text("Apply Scope", "Aplicar ámbito"), "filter_apply"
        )
        self.apply_scope_button.setObjectName("primaryButton")
        for button in (self.clear_scope_button, self.apply_scope_button):
            button.setIconSize(QSize(26, 26))
            button.setMinimumWidth(145)
            button.setToolTip(
                self.text(
                    "Apply or clear the selected rotation scope.",
                    "Aplicar o limpiar el ámbito de rotación.",
                )
            )
            scope_actions.addWidget(button)
        top.addLayout(scope_actions)
        filters.addLayout(top)
        self.scheme_group = QGroupBox(
            self.text("Rotation scheme", "Esquema de rotación")
        )
        scheme_layout = QHBoxLayout(self.scheme_group)
        scheme_layout.setContentsMargins(10, 8, 10, 8)
        scheme_layout.setSpacing(14)
        fields = QGridLayout()
        fields.setHorizontalSpacing(8)
        fields.setVerticalSpacing(5)
        self.scheme_combo = QComboBox()
        self.scheme_combo.setEditable(True)
        self.scheme_combo.setMinimumWidth(210)
        self.workers_combo = QComboBox()
        self.workers_combo.addItems([str(n) for n in range(1, 11)])
        self.blocks_combo = QComboBox()
        self.blocks_combo.addItems([str(n) for n in range(2, 11)])
        self.blocks_combo.setCurrentText("4")
        self.time_limit_input = QLineEdit("1")
        self.time_limit_input.setValidator(QIntValidator(1, 180, self))
        self.time_limit_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_limit_input.setFixedWidth(58)
        for combo in (self.scheme_combo, self.workers_combo, self.blocks_combo):
            combo.setItemDelegate(QStyledItemDelegate(combo))
        for label, widget, row, column in (
            (self.text("Rotation ID", "ID de rotación"), self.scheme_combo, 0, 0),
            (self.text("Workers", "Trabajadores"), self.workers_combo, 0, 2),
            (self.text("Time blocks", "Bloques"), self.blocks_combo, 1, 0),
            (
                self.text("Optimization limit (minutes)", "Límite (minutos)"),
                self.time_limit_input,
                1,
                2,
            ),
        ):
            fields.addWidget(QLabel(label), row, column)
            fields.addWidget(widget, row, column + 1)
        scheme_layout.addLayout(fields)
        scheme_layout.addStretch(1)
        actions = QHBoxLayout()
        actions.setSpacing(7)
        actions.setAlignment(
            Qt.Alignment(Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter
        )
        self.navigation: list[QPushButton] = []
        for icon, english, spanish in (
            ("first", "First rotation", "Primera rotación"),
            ("previous", "Previous rotation", "Rotación anterior"),
            ("next", "Next rotation", "Siguiente rotación"),
            ("last", "Last rotation", "Última rotación"),
        ):
            button = self.button("", icon)
            button.setIconSize(QSize(24, 24))
            button.setFixedSize(42, 36)
            button.setToolTip(self.text(english, spanish))
            actions.addWidget(button)
            self.navigation.append(button)
        actions.addSpacing(8)
        self.new_button = self.button(self.text("New", "Nuevo"), "new")
        self.save_button = self.button(self.text("Save", "Guardar"), "save")
        self.delete_button = self.button(self.text("Delete", "Eliminar"), "delete")
        self.search_button = self.button(self.text("Search", "Buscar"), "search")
        self.cancel_button = self.button(self.text("Cancel", "Cancelar"), "undo")
        for button in (
            self.new_button,
            self.save_button,
            self.delete_button,
            self.search_button,
            self.cancel_button,
        ):
            button.setIconSize(QSize(24, 24))
            button.setMinimumHeight(36)
            actions.addWidget(button)
        scheme_layout.addLayout(actions)
        filters.addWidget(self.scheme_group)
        root.addWidget(self.setup_group)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        current = QFrame()
        current.setObjectName("workspacePanel")
        self.current_layout = QVBoxLayout(current)
        self.current_layout.setContentsMargins(8, 8, 8, 8)
        self.current_title = QLabel(self.text("Current Rotation", "Rotación actual"))
        self.current_title.setObjectName("panelTitle")
        self.current_title.setFixedHeight(50)
        self.current_title.setAlignment(
            Qt.Alignment(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter
        )
        self.current_layout.addWidget(self.current_title)
        self.splitter.addWidget(current)
        optimized = QFrame()
        optimized.setObjectName("workspacePanel")
        optimized_layout = QVBoxLayout(optimized)
        optimized_layout.setContentsMargins(8, 8, 8, 8)
        optimized_heading = QHBoxLayout()
        self.optimized_title = QLabel(
            self.text("Optimized Rotation", "Rotación optimizada")
        )
        self.optimized_title.setObjectName("panelTitle")
        self.optimized_title.setFixedHeight(50)
        self.optimized_title.setAlignment(
            Qt.Alignment(Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter
        )
        optimized_heading.addWidget(self.optimized_title)
        optimized_heading.addStretch(1)
        self.transfer_button = self.button(
            self.text("Use as Current", "Usar como actual"), "apply_rotation"
        )
        self.transfer_button.setIconSize(QSize(44, 44))
        self.transfer_button.setMinimumWidth(185)
        self.transfer_button.setFixedHeight(50)
        optimized_heading.addWidget(self.transfer_button)
        optimized_layout.addLayout(optimized_heading)
        self.optimized_table = QTableWidget()
        optimized_layout.addWidget(self.optimized_table, 1)
        self.splitter.addWidget(optimized)
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 5)
        root.addWidget(self.splitter, 1)
        rail = QHBoxLayout()
        rail.setSpacing(8)
        self.compare_button = QToolButton()
        self.optimize_button = QToolButton()
        self.optimize_all_button = QToolButton()
        self.close_button = QToolButton()
        self.optimize_all_button.setProperty("primaryAction", True)
        for button, english, spanish, icon, width, iw, ih in (
            (
                self.compare_button,
                "Compare",
                "Comparar",
                "compare_rotation",
                128,
                100,
                52,
            ),
            (
                self.optimize_button,
                "Optimize Tool",
                "Optimizar actual",
                "optimize_selected_tool",
                156,
                62,
                62,
            ),
            (
                self.optimize_all_button,
                "Optimize All Tools",
                "Optimizar todas",
                "optimize_all_tools",
                184,
                62,
                62,
            ),
            (self.close_button, "Close", "Cerrar", "close", 92, 54, 54),
        ):
            button.setText(self.text(english, spanish))
            button.setIcon(icons[icon])
            button.setObjectName("jrotActionButton")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setIconSize(QSize(iw, ih))
            button.setFixedSize(width, 94)
            if button is self.close_button:
                rail.addStretch(1)
            rail.addWidget(button)
        self.close_button.clicked.connect(self.reject)
        root.addLayout(rail)
        disclaimer = QLabel(
            self.text(
                "Rotation estimates use job-level LiFFT, DUET, and Shoulder Tool "
                "measurements. Interpret optimized schedules together with "
                "job redesign and other ergonomic controls.",
                "Las estimaciones usan mediciones de trabajos de LiFFT, DUET y hombro. "
                "Interprete las rotaciones junto con el rediseño de trabajos "
                "y otros controles ergonómicos.",
            )
        )
        disclaimer.setObjectName("supportingText")
        disclaimer.setWordWrap(True)
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(disclaimer)
        pending = self.text(
            "Optimization/comparison integration is pending.",
            "La integración de optimización y comparación está pendiente.",
        )
        for button in (
            self.transfer_button,
            self.compare_button,
            self.optimize_button,
            self.optimize_all_button,
        ):
            button.setEnabled(False)
            button.setToolTip(pending)

    def text(self, english: str, spanish: str) -> str:
        """Select form text without translating project identifiers or evidence.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return rotation_text(english, spanish, self.language)

    def button(self, label: str, icon: str | None = None) -> QPushButton:
        """Create an original styled button without accidental Enter activation.

        Args:
            label: Visible label/legend caption; None omits an optional chart series
                label.
            icon: Stable packaged icon identity; None omits the optional button icon.

        Returns:
            New styled button with automatic Enter/default activation disabled.
        """
        button = QPushButton(label)
        button.setAutoDefault(False)
        if icon is not None:
            button.setIcon(self.icons[icon])
        return button
