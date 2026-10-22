"""Original PLOT Graph Settings dialog with injected chart export.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.language import Language
from ergotools.presentation.desktop.plot_graph_settings import (
    PlotAxisMode,
    PlotGraphSettings,
)
from ergotools.presentation.desktop.theme.plot import PLOT_STYLE


class PlotGraphDialog(QDialog):
    """Edit a local settings copy; Apply commits and Close discards that copy."""

    show_title: QCheckBox
    show_legend: QCheckBox
    show_grid: QCheckBox
    show_bar_values: QCheckBox
    reset_button: QPushButton
    close_button: QPushButton
    apply_button: QPushButton

    def __init__(
        self,
        settings: PlotGraphSettings,
        icons: Mapping[str, QIcon],
        save_plot: Callable[[QWidget], None],
        *,
        language: Language = Language.ENGLISH,
        parent: QWidget | None = None,
    ) -> None:
        """Retain source geometry, processed assets and explicit modal actions.

        Args:
            settings: Immutable graph presentation preferences; project and assessment
                values are unchanged.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            save_plot: Injected export callback receiving the owned settings dialog as
                parent.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(self.text("Graph Settings", "Configuración del gráfico"))
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setStyleSheet(PLOT_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)
        title = QLabel(self.windowTitle())
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            self.text(
                "Adjust or export charts from the Tools Overview tab.",
                "Ajuste o exporte gráficos de la pestaña de herramientas.",
            )
        )
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)
        content = QGroupBox(self.text("Chart content", "Contenido del gráfico"))
        grid = QGridLayout(content)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        for index, (key, en, es, tip, tip_es) in enumerate(
            (
                (
                    "show_title",
                    "Show chart title",
                    "Mostrar título",
                    "Show or hide the title inside the chart.",
                    "Mostrar u ocultar el título.",
                ),
                (
                    "show_legend",
                    "Show legend",
                    "Mostrar leyenda",
                    "Show or hide the chart legend when one is available.",
                    "Mostrar u ocultar la leyenda disponible.",
                ),
                (
                    "show_grid",
                    "Show grid lines",
                    "Mostrar líneas guía",
                    "Draw subtle horizontal guide lines on standard charts.",
                    "Mostrar líneas guía sutiles.",
                ),
                (
                    "show_bar_values",
                    "Show values on bars",
                    "Mostrar valores en barras",
                    "Display the numeric value above each bar.",
                    "Mostrar el valor numérico en cada barra.",
                ),
            )
        ):
            checkbox = QCheckBox(self.text(en, es))
            checkbox.setToolTip(self.text(tip, tip_es))
            setattr(self, key, checkbox)
            grid.addWidget(checkbox, index // 2, index % 2)
        root.addWidget(content)
        scale = QGroupBox(self.text("Scale and text", "Escala y texto"))
        grid = QGridLayout(scale)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        self.axis_mode = QComboBox()
        for en, es, mode in (
            ("Chart default", "Predeterminada", PlotAxisMode.DEFAULT),
            ("Risk scale (0\u2013100%)", "Riesgo (0\u2013100%)", PlotAxisMode.RISK),
            ("Custom maximum", "Máximo personalizado", PlotAxisMode.CUSTOM),
        ):
            self.axis_mode.addItem(self.text(en, es), mode)
        self.axis_maximum = QDoubleSpinBox()
        self.axis_maximum.setRange(1, 1000000)
        self.axis_maximum.setDecimals(1)
        self.axis_maximum.setSingleStep(5)
        self.text_scale = QSpinBox()
        self.text_scale.setRange(80, 140)
        self.text_scale.setSingleStep(5)
        self.text_scale.setSuffix("%")
        for row, (en, es, control) in enumerate(
            (
                ("Vertical axis", "Eje vertical", self.axis_mode),
                ("Maximum", "Máximo", self.axis_maximum),
                ("Text size", "Tamaño del texto", self.text_scale),
            )
        ):
            grid.addWidget(QLabel(self.text(en, es)), row, 0)
            grid.addWidget(control, row, 1)
        for control, en, es in (
            (
                self.axis_mode,
                "Use the chart's normal scale, the standard risk scale, or "
                "a custom maximum.",
                "Use la escala normal, de riesgo o un máximo personalizado.",
            ),
            (
                self.axis_maximum,
                "Set the top of the vertical axis when Custom maximum is selected.",
                "Defina el máximo del eje con la opción personalizada.",
            ),
            (
                self.text_scale,
                "Scale chart titles, labels, ticks, legends, and annotations.",
                "Cambie el tamaño de títulos, etiquetas, leyendas y anotaciones.",
            ),
        ):
            control.setToolTip(self.text(en, es))
        root.addWidget(scale)
        buttons = QHBoxLayout()
        self.save_button = QPushButton(self.text("Save plot", "Guardar gráfico"))
        self.save_button.setIcon(icons["save"])
        self.save_button.setIconSize(QSize(22, 22))
        self.save_button.setMinimumHeight(38)
        self.save_button.clicked.connect(lambda: save_plot(self))
        self.save_button.setToolTip(
            self.text(
                "Save the current Summary graph as an image or document.",
                "Guardar el gráfico actual como imagen o documento.",
            )
        )
        buttons.addWidget(self.save_button)
        buttons.addStretch(1)
        for key, en, es, asset, tip, tip_es in (
            (
                "reset_button",
                "Reset",
                "Restablecer",
                "undo",
                "Restore the default graph presentation settings.",
                "Restablecer los ajustes del gráfico.",
            ),
            (
                "close_button",
                "Close",
                "Cerrar",
                "close",
                "Close without applying additional changes.",
                "Cerrar sin aplicar cambios.",
            ),
            (
                "apply_button",
                "Apply",
                "Aplicar",
                "filter_apply_light",
                "Apply these settings to the current graph.",
                "Aplicar los ajustes al gráfico actual.",
            ),
        ):
            button = QPushButton(self.text(en, es))
            button.setMinimumHeight(38)
            button.setIconSize(QSize(22, 22))
            button.setToolTip(self.text(tip, tip_es))
            if asset:
                button.setIcon(icons[asset])
            if key == "apply_button":
                button.setObjectName("primaryButton")
            setattr(self, key, button)
            buttons.addWidget(button)
        self.reset_button.clicked.connect(
            lambda: self.load_settings(PlotGraphSettings())
        )
        self.close_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.accept)
        root.addLayout(buttons)
        self.axis_mode.currentIndexChanged.connect(self.update_maximum)
        self.load_settings(settings)

    def text(self, english: str, spanish: str) -> str:
        """Translate controls without changing numeric or graph policy.

        Args:
            english: English UI text; saved user values are never translated by this
                helper.
            spanish: Spanish UI text corresponding to the English caption.

        Returns:
            Localized UI caption/message; saved record identities and numeric values are
            unchanged.
        """
        return spanish if self.language is Language.SPANISH else english

    def load_settings(self, settings: PlotGraphSettings) -> None:
        """Project source values locally; Reset does not change the owner's chart.

        Args:
            settings: Immutable graph presentation preferences; project and assessment
                values are unchanged.

        Returns:
            None.
        """
        for key in ("show_title", "show_legend", "show_grid", "show_bar_values"):
            getattr(self, key).setChecked(getattr(settings, key))
        self.axis_mode.setCurrentIndex(self.axis_mode.findData(settings.axis_mode))
        self.axis_maximum.setValue(settings.axis_maximum)
        self.text_scale.setValue(settings.text_scale)
        self.update_maximum()

    def update_maximum(self) -> None:
        """Enable the original maximum control only for custom scaling.

        Args:
            None.

        Returns:
            None.
        """
        self.axis_maximum.setEnabled(
            self.axis_mode.currentData() == PlotAxisMode.CUSTOM
        )

    def settings(self) -> PlotGraphSettings:
        """Return typed values after explicit acceptance, without project writes.

        Args:
            None.

        Returns:
            Validated immutable presentation choices read from the local controls; no
            project writes occur.
        """
        return PlotGraphSettings(
            self.show_title.isChecked(),
            self.show_legend.isChecked(),
            self.show_grid.isChecked(),
            self.show_bar_values.isChecked(),
            PlotAxisMode(self.axis_mode.currentData()),
            self.axis_maximum.value(),
            self.text_scale.value(),
        )
