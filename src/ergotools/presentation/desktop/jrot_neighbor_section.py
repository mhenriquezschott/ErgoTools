"""Compact disclosure and contextual help for optional neighboring rotation evidence.

Presentation layer. Reads supplied restriction/link state without changing it. The
host retains exact neighbor selection, validation, shared history and Main Save.
"""

from collections.abc import Callable, Mapping
from functools import partial

from PyQt5.QtCore import QEvent, QObject, QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ergotools.domain.language import Language
from ergotools.domain.rotation_constraints import NoAdjacentHigh
from ergotools.domain.rotation_scenario import RotationInputs
from ergotools.presentation.desktop.expandable_section import ExpandableSection


class JrotNeighborSection(QWidget):
    """Disclose optional evidence controls only when the user wants their details."""

    def __init__(
        self,
        language: Language,
        choose: Callable[[bool], None],
        clear: Callable[[bool], None],
        *,
        icons: Mapping[str, QIcon] | None = None,
    ) -> None:
        """Compose compact local disclosure with prominent explanatory feedback.

        Args:
            icons: Injected packaged previous/following/clear glyphs.
            language: Interface language; saved names remain literal.
            choose: Host callback selecting a preceding/following retained result.
            clear: Host callback removing a link without removing a restriction.

        Returns:
            None; starts collapsed and creates no history, link or application setting.
        """
        super().__init__()
        self.language = language
        self._help_side: bool | None = None
        self.requested = {True: False, False: False}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QHBoxLayout()
        self.toggle = QToolButton()
        self.toggle.setText(
            self.text(
                "Across-shift checks · Optional",
                "Comprobaciones entre turnos · Opcional",
            )
        )
        self.toggle.setCheckable(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle.setToolTip(
            self.text(
                "Show how retained neighboring rotations constrain shift boundaries.",
                (
                    "Mostrar cómo los resultados de rotaciones vecinas restringen los "
                    "límites del turno."
                ),
            )
        )
        self.toggle.setStyleSheet(
            "QToolButton {padding:7px;color:#0B326C;font-weight:bold;}"
        )
        heading.addWidget(self.toggle)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        heading.addWidget(self.summary, 1)
        layout.addLayout(heading)
        content = QGroupBox()
        body = QHBoxLayout(content)
        buttons = QVBoxLayout()
        self.choose_buttons: dict[bool, QPushButton] = {}
        self.clear_buttons: dict[bool, QPushButton] = {}
        for previous in (True, False):
            row = QHBoxLayout()
            button = QPushButton(
                self.text(
                    "Select preceding rotation result…"
                    if previous
                    else "Select following rotation result…",
                    "Seleccionar resultado de rotación anterior…"
                    if previous
                    else "Seleccionar resultado de rotación siguiente…",
                )
            )
            button.setAutoDefault(False)
            button.clicked.connect(partial(choose, previous))
            button.installEventFilter(self)
            button.setIcon(
                (icons or {}).get(
                    "previous_rotation_result"
                    if previous
                    else "following_rotation_result",
                    QIcon(),
                )
            )
            button.setIconSize(QSize(28, 28))
            self.choose_buttons[previous] = button
            row.addWidget(button, 1)
            remove = QPushButton(self.text("Clear link", "Quitar vínculo"))
            remove.setAutoDefault(False)
            remove.clicked.connect(partial(clear, previous))
            remove.installEventFilter(self)
            remove.setIcon((icons or {}).get("clear_result_link", QIcon()))
            remove.setIconSize(QSize(26, 26))
            self.clear_buttons[previous] = remove
            row.addWidget(remove)
            buttons.addLayout(row)
        self.links = QLabel()
        self.links.setWordWrap(True)
        buttons.addWidget(self.links)
        buttons.addStretch(1)
        body.addLayout(buttons, 2)
        help_group = QGroupBox(
            self.text("What does this check do?", "¿Qué comprueba esta opción?")
        )
        help_group.setMinimumWidth(330)
        help_group.setStyleSheet(
            "QGroupBox {background:#E8F6FA;border:1px solid #85C4CE;border-"
            "radius:5px;margin-top:8px;padding-top:10px;} QGroupBox::title "
            "{font-weight:bold;color:#0B326C;}"
        )
        help_layout = QVBoxLayout(help_group)
        self.help = QLabel()
        self.help.setWordWrap(True)
        self.help.setMinimumHeight(100)
        help_layout.addWidget(self.help)
        body.addWidget(help_group, 3)
        self.disclosure = ExpandableSection(content)
        layout.addWidget(self.disclosure)
        self.toggle.toggled.connect(self.set_expanded)
        self.explain(None)

    def text(self, english: str, spanish: str) -> str:
        """Choose interface wording without translating stored rotation names.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Localized interface caption.
        """
        return spanish if self.language is Language.SPANISH else english

    def set_expanded(self, expanded: bool) -> None:
        """Reveal existing controls without changing their links or restriction state.

        Args:
            expanded: User's window-local disclosure choice.

        Returns:
            None; projection/history changes do not restart this animation.
        """
        self.toggle.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )
        self.disclosure.set_expanded(expanded, animate=True)

    def project(self, inputs: RotationInputs, names: Mapping[str, str]) -> None:
        """Show links and enable selection only for requested per-worker boundaries.

        Args:
            inputs: Current accepted scenario restriction/link state.
            names: Literal current rotation names by stable ID.

        Returns:
            None; unused links are retained and may still be deliberately cleared.
        """
        counts = {
            side: sum(
                isinstance(rule, NoAdjacentHigh)
                and (rule.previous if side else rule.following)
                for rule in inputs.rules
            )
            for side in (True, False)
        }
        descriptions = []
        missing = False
        for side in (True, False):
            boundary = inputs.previous if side else inputs.following
            self.requested[side] = counts[side] > 0
            self.choose_buttons[side].setEnabled(self.requested[side])
            self.clear_buttons[side].setEnabled(boundary is not None)
            label = self.text(
                "Preceding" if side else "Following",
                "Anterior" if side else "Siguiente",
            )
            link = (
                names.get(boundary.scenario_id, boundary.scenario_id)
                if boundary
                else self.text("Not linked", "Sin vínculo")
            )
            descriptions.append(label + ": " + link)
            self.choose_buttons[side].setToolTip(self.explanation(side))
            self.clear_buttons[side].setToolTip(
                self.text(
                    (
                        "Remove only this result link. Requested worker checks still "
                        "require a valid link."
                    ),
                    (
                        "Quitar solo el vínculo. Las comprobaciones solicitadas aún "
                        "necesitan un resultado válido."
                    ),
                )
            )
            missing |= self.requested[side] and boundary is None
        self.links.setText("\n".join(descriptions))
        self.summary.setText(
            self.text(
                "No worker boundary checks enabled",
                "Sin comprobaciones de límites activadas",
            )
            if not any(counts.values())
            else self.text(
                f"Workers requiring checks · Preceding: {counts[True]} · "
                f"Following: {counts[False]}",
                f"Trabajadores con comprobaciones · Anterior: {counts[True]} · "
                f"Siguiente: {counts[False]}",
            )
            + (
                self.text(
                    " · Select missing results",
                    " · Seleccione los resultados faltantes",
                )
                if missing
                else ""
            )
        )
        self.summary.setStyleSheet(
            "color:#9B5B00;font-weight:bold;" if missing else "color:#41617A;"
        )
        self.explain(self._help_side)

    def explanation(self, previous: bool) -> str:
        """Explain chronology, per-worker activation and the exact optimizer effect.

        Args:
            previous: True for the preceding last block; False for the following first.

        Returns:
            Prominent help text also reused as the selection tooltip.
        """
        effect = (
            self.text(
                (
                    "Select a kept optimization result from a rotation that ends "
                    "before this one. For workers with Previous boundary enabled, its "
                    "last Job constrains their first Job here: both cannot be High."
                ),
                (
                    "Seleccione un resultado conservado de una rotación que termina "
                    "antes. Para trabajadores con límite anterior activo, su último "
                    "trabajo restringe el primero aquí: ambos no pueden ser altos."
                ),
            )
            if previous
            else self.text(
                (
                    "Select a kept optimization result from a rotation that starts "
                    "after this one. For workers with Following boundary enabled, its "
                    "first Job constrains their last Job here: both cannot be High."
                ),
                (
                    "Seleccione un resultado conservado de una rotación que empieza "
                    "después. Para trabajadores con límite siguiente activo, su primer"
                    " trabajo restringe el último aquí: ambos no pueden ser altos."
                ),
            )
        )
        activation = (
            ""
            if self.requested[previous]
            else self.text(
                (
                    " Enable the corresponding boundary checkbox in Worker "
                    "restrictions first."
                ),
                (
                    " Primero active el límite correspondiente en Restricciones de "
                    "trabajadores."
                ),
            )
        )
        return (
            effect
            + activation
            + self.text(
                (
                    " This is not an earlier solve attempt or page navigation. It does"
                    " not modify or jointly optimize the linked rotation."
                ),
                (
                    " No es un intento anterior de cálculo ni navegación. No modifica "
                    "ni optimiza conjuntamente la rotación vinculada."
                ),
            )
        )

    def explain(self, previous: bool | None) -> None:
        """Update the visible explanation rather than relying only on a tooltip.

        Args:
            previous: Boundary being examined, or None for the default guidance.

        Returns:
            None; ordinary within-shift constraints need no neighboring links.
        """
        self.help.setText(
            self.explanation(previous)
            if previous is not None
            else self.text(
                (
                    "Optional: prevent consecutive High-risk Jobs across rotations. In"
                    " Worker restrictions, enable No adjacent High and the "
                    "preceding/following boundary for the relevant worker. Then link a"
                    " kept result from the rotation before/after this one. Hover or "
                    "focus a selection button for its exact effect. Within-shift "
                    "checks need no links."
                ),
                (
                    "Opcional: impide trabajos altos consecutivos entre rotaciones. En"
                    " Restricciones, active Sin alto consecutivo y el límite "
                    "anterior/siguiente para el trabajador. Después vincule un "
                    "resultado conservado de la rotación anterior/siguiente. Pase el "
                    "puntero o enfoque un botón para ver su efecto. Los controles "
                    "internos del turno no necesitan vínculos."
                ),
            )
        )

    def eventFilter(self, watched: QObject | None, event: QEvent | None) -> bool:  # noqa: N802 - Qt override
        """Present help on pointer or keyboard focus, including disabled controls.

        Args:
            watched: One of the owned selection or clear controls.
            event: Native event forwarded unchanged.

        Returns:
            False so native focus, mouse and tooltip behavior continue.
        """
        if event is not None and event.type() in (
            QEvent.Type.Enter,
            QEvent.Type.FocusIn,
        ):
            for side in (True, False):
                if watched is self.choose_buttons[side]:
                    self._help_side = side
                    self.explain(side)
                elif watched is self.clear_buttons[side]:
                    self._help_side = None
                    self.help.setText(self.clear_buttons[side].toolTip())
        return super().eventFilter(watched, event)
