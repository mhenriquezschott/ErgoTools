"""Original body-region panel composing the replaceable native renderer widget.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.contracts.body_renderer import BodyRenderer
from ergotools.application.settings import Language
from ergotools.presentation.desktop.theme.risk import RISK_APPEARANCES
from ergotools.presentation.desktop.workspace_text import workspace_text


class _ModelViewport(QFrame):
    """Reserve the reference QVTK widget's preferred space before adapter wiring."""

    def sizeHint(self) -> QSize:  # noqa: N802
        """Match the reviewed QVTKRenderWindowInteractor 400-by-400 size hint.

        Args:
            None.

        Returns:
            Reference preferred viewport size of 400 by 400 Qt logical pixels.
        """
        return QSize(400, 400)


class BodyRegionPanel(QFrame):
    """Own original left-panel controls and attach a replaceable native renderer.

    Own original left-panel controls and attach a replaceable native renderer through
    its port.
    """

    def __init__(self, icons: Mapping[str, QIcon], *, parent: QWidget) -> None:
        """Port the model-frame layout and setupControlPanel using packaged assets.

        Args:
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            parent: Required Qt owner of the new control; ownership follows the parent
                widget lifetime.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setObjectName("bodyRegionPanel")
        self.setMinimumWidth(240)
        self.setMaximumWidth(285)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(8)
        self._captions: list[tuple[QLabel | QToolButton, str, str]] = []
        title_row = QHBoxLayout()
        title = self._label("LiFFT Body Region", "bodyRegionTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)
        self.viewport = _ModelViewport()
        self.viewport.setObjectName("vtkWorkspace")
        self.viewport.setMinimumHeight(315)
        viewport_layout = QVBoxLayout(self.viewport)
        pending = self._label("3D view unavailable", "bodyRiskLabel")
        pending.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pending.setWordWrap(True)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        viewport_layout.addWidget(pending)
        self._pending = pending
        layout.addWidget(self.viewport, 1)
        active = QFrame()
        active.setObjectName("activeRegionPanel")
        active.setFixedHeight(56)
        active_layout = QVBoxLayout(active)
        active_layout.setContentsMargins(4, 2, 4, 2)
        active_layout.setSpacing(0)
        region = self._label("Lower Back", "activeRegionName")
        region.setAlignment(Qt.AlignmentFlag.AlignCenter)
        region.setFixedHeight(28)
        caption = self._label("Active Region", "activeRegionCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setFixedHeight(22)
        active_layout.addWidget(region)
        active_layout.addWidget(caption)
        layout.addWidget(active)
        layout.addWidget(self._divider())
        layout.addWidget(self._label("LiFFT Individual Risk Score", "bodySectionTitle"))
        for appearance in RISK_APPEARANCES.values():
            row = QHBoxLayout()
            swatch = QLabel()
            swatch.setFixedSize(12, 12)
            swatch.setStyleSheet(
                f"background: {appearance.color_hex}; border-radius: 6px;"
            )
            row.addWidget(swatch)
            row.addWidget(self._label(appearance.english_label, "bodyRiskLabel"), 1)
            range_label = self._label(appearance.range_label, "bodyRiskRange")
            range_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(range_label)
            layout.addLayout(row)
        layout.addWidget(self._divider())
        controls = QHBoxLayout()
        controls.setSpacing(4)
        self.view_buttons = []
        for text, icon, tip in (
            ("Rotate", "view_3d_rotate_light", "Rotate the model clockwise."),
            ("Zoom", "view_3d_zoom_light", "Zoom in on the active body region."),
            ("Reset View", "view_3d_reset_light", "Restore the initial model view."),
        ):
            button = QToolButton()
            button.setObjectName("modelViewButton")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setIcon(icons[icon])
            button.setIconSize(QSize(28, 28))
            button.setEnabled(False)  # No renderer is installed; never fake actions.
            self._captions.append((button, text, tip))
            self.view_buttons.append(button)
            controls.addWidget(button, 1)
        layout.addLayout(controls)
        self.translate(Language.ENGLISH)

    def _label(self, text: str, name: str) -> QLabel:
        """Create a styled body-panel label and register its source caption.

        Create a styled body-panel label and register its source caption for later
        translation.

        Args:
            text: Literal control text or user input; interpretation follows this
                method's stated policy.
            name: Control object name used by the application stylesheet.

        Returns:
            Owned styled label registered for subsequent language updates.
        """
        label = QLabel(text)
        label.setObjectName(name)
        self._captions.append((label, text, ""))
        return label

    @staticmethod
    def _divider() -> QFrame:
        """Create the original fixed-height horizontal divider.

        Create the original fixed-height horizontal divider with the established
        object-name styling.

        Args:
            None.

        Returns:
            Owned original fixed-height horizontal divider.
        """
        divider = QFrame()
        divider.setObjectName("bodyPanelDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        return divider

    def attach_renderer(self, widget: QWidget, renderer: BodyRenderer) -> None:
        """Replace the explicit temporary viewport with the owned native widget.

        Args:
            widget: Qt component to attach or inspect; lifetime remains with its owning
                window.
            renderer: Replaceable body-renderer port; native VTK objects remain inside
                its adapter.

        Returns:
            None.
        """
        layout = self.viewport.layout()
        assert layout is not None
        self._pending.hide()
        layout.removeWidget(self._pending)
        layout.addWidget(widget)
        for button, action in zip(
            self.view_buttons,
            (renderer.rotate_view, renderer.zoom_view, renderer.reset_view),
            strict=True,
        ):
            button.clicked.connect(action)
            button.setEnabled(True)

    def translate(self, language: Language) -> None:
        """Update original captions without recreating viewport or control widgets.

        Args:
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.

        Returns:
            None.
        """
        for widget, text, tip in self._captions:
            widget.setText(workspace_text(text, language))
            widget.setToolTip(workspace_text(tip, language))

    def set_tool(
        self, duet: bool, language: Language, *, shoulder: bool = False
    ) -> None:
        """Replace reference tool/region captions without recreating the viewport.

        Args:
            duet: True selects the distal upper-extremity body-region captions.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            shoulder: True selects Shoulder Tool captions; otherwise use the LiFFT/DUET
                selection.

        Returns:
            None.
        """
        replacements = {
            "LiFFT Body Region": "DUET Body Region",
            "Lower Back": "Distal Upper Extremity",
            "LiFFT Individual Risk Score": "DUET Individual Risk Score",
        }
        if shoulder:
            replacements = {
                "LiFFT Body Region": "Shoulder Body Region",
                "Lower Back": "Shoulders",
                "LiFFT Individual Risk Score": "Shoulder Individual Risk Score",
            }
        for widget, text, _tip in self._captions:
            if text in replacements:
                widget.setText(
                    workspace_text(
                        replacements[text] if duet or shoulder else text, language
                    )
                )
