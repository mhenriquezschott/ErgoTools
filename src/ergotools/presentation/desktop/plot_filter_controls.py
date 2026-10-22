"""Original PLOT workplace path and ergonomic-tool controls with typed intent.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping
from html import escape

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QResizeEvent
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.plot_scope import PlotScope
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.presentation.desktop.plot_workplace_dialog import PlotWorkplaceDialog
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE

# Original workplace path ordering and matching packaged icon identities.
_LEVELS = (
    ("Plant", "Planta", "plant"),
    ("Section", "Sección", "section"),
    ("Line", "Línea", "line"),
    ("Station", "Estación", "station"),
    ("Shift", "Turno", "shift"),
)
# Original ergonomic tool identities, branded captions and packaged icon keys.
_TOOLS = (
    (AssessmentKind.LIFFT, "LiFFT", "LiFFT", "lifft"),
    (AssessmentKind.DUET, "DUET", "DUET", "duet"),
    (AssessmentKind.TST, "Shoulder", "Hombro", "shoulder"),
)


class PlotScopeValue(QLabel):
    """Keep literal full values accessible while fitting the original path block."""

    def __init__(self, parent: QWidget) -> None:
        """Build a plain-text label that cannot widen the entire PLOT window.

        Args:
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        super().__init__(parent)
        self.value = ""
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def show_value(self, value: str, tooltip: str) -> None:
        """Update display and full identity without translating stored names.

        Args:
            value: Full literal value to display/elide or worker alphabet filter
                sentinel, as specified by this helper.
            tooltip: Full literal scope value retained for accessible/hover display when
                the label is elided.

        Returns:
            None.
        """
        self.value = value
        self.setToolTip("<qt>" + escape(tooltip).replace("\n", "<br>") + "</qt>")
        self.setAccessibleDescription(value)
        self._render()

    def _render(self) -> None:
        """Elide the visible label to its current width.

        Elide the visible label to its current width while retaining the complete
        literal value in its tooltip/accessibility text.

        Args:
            None.

        Returns:
            None.
        """
        self.setText(
            self.fontMetrics().elidedText(
                self.value.replace("\n", " ").replace("\r", " "),
                Qt.TextElideMode.ElideMiddle,
                max(0, self.width()),
            )
        )

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        """Refit the displayed value after Qt allocates the original scope blocks.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        super().resizeEvent(event)
        self._render()


class PlotWorkplaceControls(QGroupBox):
    """Retain original path blocks and modal scope selection with map acceptance."""

    scope_changed = pyqtSignal()

    def __init__(
        self,
        hierarchy: WorkHierarchy,
        icons: Mapping[str, QIcon],
        apply_scope: Callable[[PlotScope], bool],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build the original 88-pixel workplace region without initial project I/O.

        Args:
            hierarchy: Immutable saved workplace/shift catalog used to build the local
                selection tree.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            apply_scope: Host callback returning True only after the map accepts the
                requested scope.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.hierarchy = hierarchy
        self.icons = icons
        self.apply_scope = apply_scope
        self.language = language
        self.scope: PlotScope | None = None
        self.setTitle(self.text("Workplace", "Lugar de trabajo"))
        self.setFixedHeight(88)
        self.setStyleSheet(PLOT_STYLE)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)
        plant_icon = QLabel()
        plant_icon.setPixmap(icons["plant"].pixmap(QSize(34, 34)))
        plant_icon.setFixedSize(36, 36)
        plant_icon.setToolTip(
            self.text(
                "The selected plant supplies the layout image displayed below.",
                "La planta seleccionada proporciona la imagen del plano mostrado.",
            )
        )
        layout.addWidget(plant_icon)
        path_widget = QWidget(self)
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(5)
        self.values: dict[str, PlotScopeValue] = {}
        self.blocks: dict[str, QFrame] = {}
        for index, (english, spanish, asset) in enumerate(_LEVELS):
            if index:
                arrow = QLabel(path_widget)
                arrow.setPixmap(
                    icons["next"]
                    .pixmap(QSize(24, 24))
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
                        "The next level is contained within the "
                        "preceding workplace level.",
                        "El siguiente nivel está contenido en el nivel anterior.",
                    )
                )
                path_layout.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)
            block = QFrame(path_widget)
            block.setObjectName(
                "workplacePlantScope" if index == 0 else "workplaceScopeBlock"
            )
            if index == 0:
                block.setMinimumWidth(118)
            column = QVBoxLayout(block)
            column.setContentsMargins(6, 2, 6, 2)
            column.setSpacing(0)
            heading = QHBoxLayout()
            heading.setContentsMargins(0, 0, 0, 0)
            heading.setSpacing(3)
            if index:
                icon = QLabel(block)
                icon.setPixmap(icons[asset].pixmap(QSize(24, 24)))
                icon.setFixedSize(25, 25)
                heading.addWidget(icon)
            caption = QLabel(self.text(english, spanish), block)
            caption.setObjectName("workplaceScopeType")
            caption.ensurePolished()
            caption.setMinimumWidth(
                caption.fontMetrics().horizontalAdvance(caption.text()) + 2
            )
            heading.addWidget(caption)
            heading.addStretch(1)
            value = PlotScopeValue(block)
            value.setObjectName(
                "workplacePlantValue" if index == 0 else "workplaceScopeValue"
            )
            column.addLayout(heading)
            column.addWidget(value)
            path_layout.addWidget(block, 2 if index == 0 else 1)
            self.blocks[english] = block
            self.values[english] = value
        path_layout.addStretch(1)
        layout.addWidget(path_widget, 1)
        self.choose_button = QPushButton(
            self.text("Choose\nWorkplace", "Elegir lugar\nde trabajo")
        )
        self.choose_button.setIcon(icons["station"])
        self.choose_button.setIconSize(QSize(34, 34))
        self.choose_button.setFixedSize(132, 52)
        self.choose_button.setToolTip(
            self.text(
                "Choose a workplace scope and shift from the organization hierarchy.",
                "Elija un ámbito de trabajo y turno de la "
                "jerarquía de la organización.",
            )
        )
        self.choose_button.setEnabled(bool(hierarchy.plants))
        self.choose_button.clicked.connect(self.choose_workplace)
        layout.addWidget(self.choose_button)
        self.refresh_values()

    def text(self, english: str, spanish: str) -> str:
        """Translate owned labels only; scope identity remains unchanged.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def choose_workplace(self) -> None:
        """Commit labels only after actual modal acceptance and successful map load.

        Args:
            None.

        Returns:
            None.
        """
        dialog = PlotWorkplaceDialog(
            self.hierarchy,
            self.icons,
            language=self.language,
            initial=self.scope,
            parent=self,
        )
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                assert dialog.selection is not None
                self.set_scope(dialog.selection)
        finally:
            dialog.deleteLater()

    def set_scope(self, scope: PlotScope) -> bool:
        """Keep path labels and map scope consistent.

        Args:
            scope: Exact typed workplace filter; no selection is reconstructed from
                displayed labels.

        Returns:
            True when scope/map acceptance succeeds (including an unchanged scope);
            False after rejection or handled failure.
        """
        scope.validate(self.hierarchy)
        if scope == self.scope:
            return True
        if not self.apply_scope(scope):
            return False
        self.scope = scope
        self.refresh_values()
        self.scope_changed.emit()
        return True

    def refresh_values(self) -> None:
        """Retain original All/single/count summaries.

        Args:
            None.

        Returns:
            None.
        """
        scope = self.scope
        details = (
            "\n".join(" \u203a ".join(path) for path in scope.paths) if scope else ""
        )
        for index, (english, spanish, _) in enumerate(_LEVELS):
            if index == 0:
                value = scope.plant if scope else "\u2013"
            elif index == 4:
                value = (
                    scope.shift
                    if scope and scope.shift is not None
                    else self.text("All", "Todos")
                )
            else:
                explicit = (
                    sorted({path[index] for path in scope.paths if len(path) > index})
                    if scope
                    else []
                )
                value = (
                    (
                        explicit[0]
                        if len(explicit) == 1
                        else self.text(
                            f"{len(explicit)} selected",
                            f"{len(explicit)} seleccionados",
                        )
                    )
                    if explicit
                    else self.text("All", "Todos")
                )
            tooltip = f"{self.text(english, spanish)}: {value}"
            if details:
                tooltip += (
                    "\n"
                    + self.text("Included scopes:", "Ámbitos incluidos:")
                    + "\n"
                    + details
                )
            self.values[english].show_value(value, tooltip)
            self.blocks[english].setToolTip(self.values[english].toolTip())


class PlotToolControls(QGroupBox):
    """Original exclusive tool buttons; publish one typed selection per change."""

    def __init__(
        self,
        icons: Mapping[str, QIcon],
        on_selected: Callable[[AssessmentKind], None],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Build original 88-pixel tool filter.

        Args:
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            on_selected: Callback publishing one typed tool-selection intent after a
                real change.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.language = language
        self.on_selected = on_selected
        self.selected = AssessmentKind.LIFFT
        self.setTitle(
            "Herramienta ergonómica"
            if language is Language.SPANISH
            else "Ergonomic Tool"
        )
        self.setFixedHeight(88)
        self.setStyleSheet(PLOT_STYLE)
        column = QVBoxLayout(self)
        column.setContentsMargins(10, 10, 10, 8)
        column.setSpacing(6)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.buttons: dict[AssessmentKind, QToolButton] = {}
        for kind, english, spanish, asset in _TOOLS:
            button = QToolButton(self)
            button.setObjectName("plotFilterTool")
            caption = spanish if language is Language.SPANISH else english
            button.setText(caption)
            button.setIcon(icons[asset])
            button.setIconSize(QSize(28, 28))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setToolTip(
                f"Mostrar trabajadores y resúmenes de {caption}."
                if language is Language.SPANISH
                else f"Show workers and summaries for the {caption} assessment tool."
            )
            button.clicked.connect(lambda checked, value=kind: self.select_tool(value))
            row.addWidget(button)
            self.buttons[kind] = button
        column.addLayout(row)
        self.buttons[self.selected].setChecked(True)

    def select_tool(self, kind: AssessmentKind) -> None:
        """Skip duplicate intent; do not reload the map or apply result filters here.

        Args:
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.

        Returns:
            None.

        Raises:
            ValueError: PLOT requires a typed ergonomic tool identity.
        """
        if not isinstance(kind, AssessmentKind):
            raise ValueError("PLOT requires a typed ergonomic tool identity.")
        if kind == self.selected:
            return
        self.selected = kind
        self.buttons[kind].setChecked(True)
        self.on_selected(kind)
