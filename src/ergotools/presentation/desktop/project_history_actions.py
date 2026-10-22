"""Shared project Undo/Redo controls with native typing and removal consent.

Presentation layer. Every window borrows the same application history. This adapter
owns QAction/Qt lifetimes, bilingual descriptions and confirmations; repository state,
chronology and durable saving remain with the application session.
"""

import logging
from collections.abc import Callable, Mapping

from PyQt5 import sip
from PyQt5.QtCore import QObject, QSize, Qt
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QToolButton,
    QWidget,
)

from ergotools.application.project_editing import ProjectEditingSession
from ergotools.domain.language import Language
from ergotools.presentation.desktop.optional_date_edit import OptionalDateEdit
from ergotools.presentation.desktop.optional_duration_edit import OptionalDurationEdit
from ergotools.presentation.desktop.style import HISTORY_BUTTON_STYLE

# Stable repository operations mapped to owner-facing action descriptions in EN/ES.
_LABELS = {
    "replace_worker_catalogs": ("Edit worker", "Editar trabajador"),
    "replace_hierarchy": ("Edit organization", "Editar organización"),
    "associate_assessment_at_workplace": (
        "Associate assessment with workplace",
        "Asociar evaluación con lugar de trabajo",
    ),
    "associate_assessment": (
        "Associate assessment with workplace",
        "Asociar evaluación con lugar de trabajo",
    ),
    "replace_jobs": ("Edit assignments", "Editar asignaciones"),
    "save_job_details": ("Edit Job", "Editar trabajo"),
    "delete_job": ("Delete Job", "Eliminar trabajo"),
    "create_historical_assessment": ("Create assessment", "Crear evaluación"),
    "assessment.edit": ("Edit assessment", "Editar evaluación"),
    "assessment.clear": ("Clear assessment", "Limpiar evaluación"),
    "assessment.calculate": ("Calculate assessment", "Calcular evaluación"),
    "assessment.view": ("Change assessment selection", "Cambiar selección"),
    "save_plot_positions": ("Edit plant layout", "Editar plano de planta"),
    "save_plant_image": ("Change plant image", "Cambiar imagen de planta"),
    "plot.edit": ("Edit PLOT", "Editar PLOT"),
    "rotation.edit": ("Edit rotation", "Editar rotación"),
    "save_rotation_scheme": ("Edit rotation scheme", "Editar esquema de rotación"),
}
# Business kinds emitted by the repository, localized only for confirmation text.
_KINDS = {
    "worker": ("Worker", "Trabajador"),
    "assessment": ("Assessment", "Evaluación"),
    "assignment": ("Assignment", "Asignación"),
    "job": ("Job", "Trabajo"),
    "placement": ("Job placement", "Ubicación de trabajo"),
    "rotation": ("Rotation", "Rotación"),
    "plant": ("Plant", "Planta"),
    "section": ("Section", "Sección"),
    "line": ("Line", "Línea"),
    "station": ("Station", "Estación"),
    "shift": ("Shift", "Turno"),
}


class ProjectHistoryActions(QObject):
    """Adapt the single project history to one window's buttons and shortcuts."""

    def __init__(
        self,
        window: QWidget,
        editing: ProjectEditingSession,
        icons: Mapping[str, QIcon],
        language: Language,
        *,
        prepare: Callable[[], bool] | None = None,
        restored: Callable[[], None] | None = None,
        blocked: Callable[[], bool] | None = None,
        pending: Callable[[], str | None] | None = None,
    ) -> None:
        """Borrow one project session and connect controls for this window only.

        Args:
            window: Owner of actions, buttons and confirmation dialogs.
            editing: Shared project history; never a window-local Undo stack.
            icons: Existing processed Undo/Redo icons.
            language: UI language; user record identities remain literal.
            prepare: Optional acceptance/validation of pending form edits before replay.
            restored: Optional rebind callback after project replay, never after edits.
            blocked: Optional solver/invalid-input interlock.
            pending: Optional stable action label for a valid pending form edit.
                Enables Undo before acceptance; replay still uses prepare and the
                same shared cursor. No independent form history is introduced.

        Returns:
            None; the subscription holds this adapter weakly, so window teardown
            never invokes Python callbacks from QObject.destroyed during collection.
        """
        super().__init__(window)
        self.window = window
        self.editing = editing
        self.language = language
        self.prepare = prepare
        self.restored = restored
        self._restored_step: tuple[int | None, int] | None = None
        self.blocked = blocked
        self.pending = pending
        self.undo_action = QAction(icons["undo"], "", self)
        self.redo_action = QAction(icons["redo"], "", self)
        self._undo_button: QToolButton | None = None
        self._redo_button: QToolButton | None = None
        for action, key in (
            (self.undo_action, QKeySequence.Undo),
            (self.redo_action, QKeySequence.Redo),
        ):
            action.setShortcuts(QKeySequence.keyBindings(key))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            window.addAction(action)
        self.undo_action.triggered.connect(lambda: self.replay(redo=False))
        self.redo_action.triggered.connect(lambda: self.replay(redo=True))
        editing.subscribe(self.refresh)
        self.refresh()

    def _button(self, action: QAction) -> QToolButton:
        """Create an owned title-row button only when a dialog requests one.

        Args:
            action: Shared Undo or Redo action displayed by this button.

        Returns:
            Window-owned themed button. The main window reuses its existing toolbar
            and never requests these buttons, avoiding unpositioned child controls.
        """
        button = QToolButton(self.window)
        button.setDefaultAction(action)
        button.setStyleSheet(HISTORY_BUTTON_STYLE)
        button.setIconSize(QSize(24, 24))
        button.setFixedSize(36, 36)
        return button

    @property
    def undo_button(self) -> QToolButton:
        """Borrow the lazily created Undo title-row control.

        Args:
            None.

        Returns:
            The same window-owned button on every access.
        """
        if self._undo_button is None:
            self._undo_button = self._button(self.undo_action)
        return self._undo_button

    @property
    def redo_button(self) -> QToolButton:
        """Borrow the lazily created Redo title-row control.

        Args:
            None.

        Returns:
            The same window-owned button on every access.
        """
        if self._redo_button is None:
            self._redo_button = self._button(self.redo_action)
        return self._redo_button

    def text(self, english: str, spanish: str) -> str:
        """Select owned wording without translating user data.

        Args:
            english: English caption.
            spanish: Equivalent Spanish caption.

        Returns:
            Caption for this window's configured language.
        """
        return spanish if self.language is Language.SPANISH else english

    def description(self, label: str | None) -> str:
        """Resolve a stable action identity for both buttons and confirmations.

        Args:
            label: Application/repository operation identity, or None at a boundary.

        Returns:
            Localized action description; unknown accepted edits use generic wording.
        """
        if label and label.startswith("worker.add:"):
            return (
                self.text("Add worker ", "Agregar trabajador ") + label.split(":", 1)[1]
            )
        if label and label.startswith("worker.delete:"):
            return (
                self.text("Delete worker ", "Eliminar trabajador ")
                + label.split(":", 1)[1]
            )
        pair = _LABELS.get(label or "", ("Edit project", "Editar proyecto"))
        return self.text(*pair)

    def refresh(self) -> None:
        """Synchronize action labels and availability with the shared cursor.

        Args:
            None.

        Returns:
            None; refreshing never records a project edit.
        """
        if sip.isdeleted(self) or sip.isdeleted(self.window):
            return
        pending = self.pending() if self.pending is not None else None
        for action, label, caption in (
            (
                self.undo_action,
                pending or self.editing.history.undo_label_key,
                self.text("Undo", "Deshacer"),
            ),
            (
                self.redo_action,
                None if pending else self.editing.history.redo_label_key,
                self.text("Redo", "Rehacer"),
            ),
        ):
            action.setText(caption + (": " + self.description(label) if label else ""))
            action.setToolTip(action.text())
            action.setEnabled(
                label is not None and not (self.blocked and self.blocked())
            )
        # A new branch can Undo back to the same destination revision. Suppress
        # reentrant notifications only for the same operation AND destination;
        # destination alone leaves widgets stale on the next branch reversal.
        step = (self.editing.replay_revision, self.editing.history.revision)
        if (
            self.editing.replaying
            and self.restored is not None
            and self._restored_step != step
        ):
            self._restored_step = step
            self.restored()

    def replay(self, *, redo: bool) -> None:
        """Keep failed project replay inside the owned UI error boundary.

        Args:
            redo: True reapplies the next action; False reverses the latest action.

        Returns:
            None; failures retain the project/cursor and explain retry to the user.
        """
        try:
            self._replay(redo=redo)
        except Exception:
            logging.getLogger(__name__).exception("Shared project history failed")
            QMessageBox.warning(
                self.window,
                self.text("Project history", "Historial del proyecto"),
                self.text(
                    "The history operation could not be completed. "
                    "Your changes are kept.",
                    "No se pudo completar la operación de historial. "
                    "Se conservan sus cambios.",
                ),
            )

    def _replay(self, *, redo: bool) -> None:
        """Replay globally, retaining native field Undo and selective removal consent.

        Args:
            redo: True reapplies the next project action; False reverses the latest.

        Returns:
            None; rejected confirmation leaves project data and the cursor unchanged.
        """
        field = QApplication.focusWidget()
        if isinstance(field, (QTimeEdit, OptionalDateEdit)) or (
            isinstance(field, QSpinBox)
            and isinstance(field.parentWidget(), OptionalDurationEdit)
        ):
            # Standard date/time/quantity editors retain native typing history.
            field = field.findChild(QLineEdit)
        if isinstance(field, QComboBox) and field.isEditable():
            field = field.lineEdit()
        if (
            isinstance(field, (QLineEdit, QPlainTextEdit, QTextEdit))
            and field.window() is self.window
        ):
            field.redo() if redo else field.undo()
            return
        if self.blocked is not None and self.blocked():
            return
        if self.prepare is not None and not self.prepare():
            return
        removals = self.editing.removals(redo=redo)
        if removals:
            details = "\n".join(
                f"{self.text(*_KINDS.get(kind, ('Record', 'Registro')))}: {identity}"
                for kind, identity in sorted(removals)
            )
            question = (
                self.text(
                    "This operation removes these records from the open project. "
                    "You can restore them with the opposite history action.\n\n",
                    "Esta operación quita estos registros del proyecto abierto. "
                    "Puede restaurarlos con la acción de historial opuesta.\n\n",
                )
                + details
            )
            if (
                QMessageBox.question(
                    self.window,
                    self.text(
                        "Confirm history operation", "Confirmar operación de historial"
                    ),
                    question,
                    QMessageBox.Yes | QMessageBox.Cancel,
                    QMessageBox.Cancel,
                )
                != QMessageBox.Yes
            ):
                return
        self.editing.replay(redo=redo)
        self.refresh()
