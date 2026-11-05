"""Reusable hover/pin workflow navigation with real layout-width animation.

Presentation layer. The host owns page readiness, data/history and truthful guidance.
The shared control stores only window-local animation/pin state and has no project or
settings writer. The guided host owns consecutive numbering, icons and page selection.
"""

from collections.abc import Callable
from functools import partial

from PyQt5.QtCore import QEasingCurve, QEvent, QPropertyAnimation, QSize, Qt, QTimer
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.language import Language
from ergotools.presentation.desktop.assessment_action_icons import (
    assessment_action_icon,
    drawer_step_icon,
)

# Application navy/teal drawer treatment, with distinct hover/selected/focus states.
WORKFLOW_DRAWER_STYLE = """
QWidget#workflowRail { background:#073E68; border:0;
    border-radius:4px; }
QFrame#stepDrawer { background: #073E68;
    border-right: 0;
    }
QFrame#stepDrawer QLabel { color: white; }
QFrame#stepDrawer QToolButton { color: white; background: #073E68;
    border: 1px solid #87A8BE; padding: 5px; }
QFrame#stepDrawer QToolButton:checked { background:#087E91;
    border-color:#08A9B5; }
QPushButton#drawerStep { text-align: left;
    color: white; background: #073E68;
    min-height: 40px;
    padding: 7px;
    border-color: transparent;
    font-weight: 600;
    }
QPushButton#drawerStep:hover { background: #14567E; border: 1px solid #87A8BE; }
QPushButton#drawerStep:focus { border: 1px solid #08A9B5; }
QPushButton#drawerStep:checked { background: #087E91;
    color: white;
    border-left: 3px solid #08A9B5;
    }
QToolButton#drawerNotch { color: white;
    background: #073E68;
    border: 0;
    border-radius: 0;
    font-size: 22px;
    padding: 0;
    min-height: 84px;
    }
"""


class WorkflowDrawer(QWidget):
    """Window-local hover/pin navigation that reallocates real content width."""

    def __init__(
        self,
        steps: tuple[str, ...],
        select: Callable[[int], None],
        *,
        language: Language = Language.ENGLISH,
        hint: str = "Explore freely.",
        icons: tuple[QIcon, ...] = (),
    ) -> None:
        """Own the notch, drawer and interruptible width animation.

        Args:
            steps: Consecutively numbered localized page captions.
            icons: Optional matching existing application icons, one per step.
            select: Host navigation callback; host validates departures.
            language: Interface language for pin/notch captions.
            hint: Host-owned truthful local/session or project-saving guidance.

        Returns:
            None; initially collapsed and unpinned, with no settings persistence.
        """
        super().__init__()
        self.language = language
        self.setObjectName("workflowRail")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(WORKFLOW_DRAWER_STYLE)
        self.setMouseTracking(True)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.notch = QToolButton()
        self.notch.setObjectName("drawerNotch")
        self.notch.setText(">")
        self.notch.setFixedWidth(20)
        self.notch.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.notch.setAccessibleName(
            "Pasos" if language is Language.SPANISH else "Workflow steps"
        )
        self.notch.setToolTip(
            "Mostrar pasos. Fije el panel para mantenerlo abierto."
            if language is Language.SPANISH
            else "Show workflow steps. Pin the panel to keep it open."
        )
        self.panel = QFrame()
        self.panel.setObjectName("stepDrawer")
        self.panel.setMinimumWidth(0)
        self.panel.setMaximumWidth(0)
        panel = QVBoxLayout(self.panel)
        panel.setContentsMargins(12, 16, 12, 16)
        panel.setSpacing(5)
        title = QLabel("ROTACIÓN" if language is Language.SPANISH else "ROTATION")
        title.setObjectName("eyebrow")
        title.setStyleSheet("font-weight:700;color:white;")
        heading = QHBoxLayout()
        heading.addWidget(title)
        heading.addStretch(1)
        self.pin = QToolButton()
        self.pin.setAccessibleName(
            "Fijar pasos" if language is Language.SPANISH else "Pin steps"
        )
        self.pin.setFixedSize(30, 30)
        self.pin.setIcon(assessment_action_icon("unpin", True))
        self.pin.setIconSize(QSize(22, 22))
        self.pin.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.pin.setCheckable(True)
        self.pin.setToolTip(
            "Mantener los pasos visibles en esta ventana."
            if language is Language.SPANISH
            else "Keep the steps visible for this window only."
        )
        self.pin.toggled.connect(self._pin_changed)
        heading.addWidget(self.pin)
        panel.addLayout(heading)
        self.buttons = []
        for index, text in enumerate(steps):
            button = QPushButton(text.replace("&", "&&"))
            button.setAutoDefault(False)
            if index < len(icons):
                button.setIcon(drawer_step_icon(icons[index]))
                button.setIconSize(QSize(26, 26))
            button.setToolTip(text)
            button.clicked.connect(partial(select, index))
            button.setObjectName("drawerStep")
            button.setCheckable(True)
            panel.addWidget(button)
            self.buttons.append(button)
        panel.addStretch(1)
        hint = QLabel(hint)
        hint.setWordWrap(True)
        hint.setObjectName("supporting")
        panel.addWidget(hint)
        root.addWidget(self.panel)
        root.addWidget(self.notch)
        self.animation = QPropertyAnimation(self.panel, b"maximumWidth", self)
        self.animation.setDuration(220)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.setInterval(420)
        self.hide_timer.timeout.connect(self._hide_if_outside)
        self.notch.clicked.connect(lambda: self.reveal(self.panel.maximumWidth() < 100))
        self.notch.installEventFilter(self)
        self.panel.installEventFilter(self)
        self.installEventFilter(self)

    def reveal(self, shown: bool = True) -> None:
        """Animate from current width; a pinned drawer cannot auto-collapse.

        Args:
            shown: Requested visibility; False is ignored while pinned.

        Returns:
            None; layouts resize the content instead of covering it.
        """
        if not shown and self.pin.isChecked():
            return
        self.hide_timer.stop()
        self.animation.stop()
        self.animation.setStartValue(self.panel.maximumWidth())
        expanded_width = max(
            238, *(button.sizeHint().width() + 32 for button in self.buttons)
        )
        self.animation.setEndValue(expanded_width if shown else 0)
        self.animation.start()
        self.notch.setText("<" if shown else ">")

    def _pin_changed(self, checked: bool) -> None:
        """Keep the pin icon, accessibility and drawer visibility synchronized.

        Args:
            checked: Current user-selected window-local pin state.

        Returns:
            None; no preference writer exists.
        """
        self.pin.setIcon(assessment_action_icon("pin" if checked else "unpin", True))
        self.pin.setAccessibleName(
            ("Liberar pasos" if checked else "Fijar pasos")
            if self.language is Language.SPANISH
            else ("Unpin steps" if checked else "Pin steps")
        )
        self.pin.setToolTip(
            (
                "Liberar el panel para ocultarlo al salir con el puntero."
                if checked
                else "Mantener los pasos visibles en esta ventana."
            )
            if self.language is Language.SPANISH
            else (
                "Unpin to hide the panel when the pointer leaves."
                if checked
                else "Keep steps visible in this window."
            )
        )
        if checked:
            self.reveal()
        elif self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.hide_timer.start()
        else:
            self.reveal(False)

    def _hide_if_outside(self) -> None:
        """Collapse only after the cursor leaves the complete rail/drawer area.

        Args:
            None.

        Returns:
            None; movement between child buttons does not flicker the drawer.
        """
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.reveal(False)

    def eventFilter(self, watched: object, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Reveal on hover and defer collapsing until native child transitions settle.

        Args:
            watched: Owned notch/panel or an unrelated event source.
            event: Native hover transition, forwarded without consumption.

        Returns:
            False; standard control input remains available.
        """
        if watched in (self, self.notch, self.panel) and event is not None:
            if event.type() == QEvent.Type.Enter:
                self.reveal()
            elif event.type() == QEvent.Type.Leave:
                self.hide_timer.start()
        return False
