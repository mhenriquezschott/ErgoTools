"""Project-local reusable task-name management using the existing catalog/history ports.

Presentation layer. Names and descriptions are metadata, never shared measurements.
Referenced definitions cannot be deleted; Main Save publishes accepted catalog edits.
"""

import logging
from collections.abc import Mapping
from unicodedata import normalize
from uuid import uuid4

from PyQt5.QtCore import QSignalBlocker, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.language import Language
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.presentation.desktop.alphabet_navigation import AlphabetNavigation
from ergotools.presentation.desktop.jrot_table_style import style_rotation_table
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.secondary_history_controls import (
    add_history_buttons,
)
from ergotools.presentation.desktop.theme.dialogs import apply_dialog_theme

# Unexpected adapter failures stay inside the owned Qt input boundary.
_LOG = logging.getLogger(__name__)


class TaskNameDialog(QDialog):
    """Search, add, edit and remove unused names with synchronized project history."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        language: Language,
        parent: QWidget | None = None,
    ) -> None:
        """Compose owned metadata controls; opening creates no task definitions.

        Args:
            workspace: Open project with the existing reusable-name capability.
            icons: Packaged history icons.
            language: English/Spanish interface; literal names stay unchanged.
            parent: Optional Main window owner.

        Returns:
            None; no separate history stack or database access is introduced.

        Raises:
            ValueError: No project editing owner is available.
        """
        super().__init__(parent)
        self.workspace, self.language = workspace, language
        self.owner = workspace.editing
        if self.owner is None:
            raise ValueError("Open a project before managing task names.")
        self.identity: str | None = None
        self.catalog: tuple[TaskDefinition, ...] = ()
        self._loading = False
        self.setWindowTitle(self.text("Task names", "Nombres de tareas"))
        self.setWindowIcon(icons.get("task_names", QIcon()))
        self.resize(900, 620)
        apply_dialog_theme(self)
        root = QVBoxLayout(self)
        heading = QHBoxLayout()
        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size:22px;font-weight:700;color:#0B326C;")
        heading.addWidget(title)
        heading.addStretch(1)
        self.history = ProjectHistoryActions(
            self, self.owner, icons, language, prepare=self.commit, restored=self.reload
        )
        add_history_buttons(heading, self.history.undo_button, self.history.redo_button)
        root.addLayout(heading)
        hint = QLabel(
            self.text(
                "Reusable names are shared labels, not shared task inputs. "
                "Renaming updates linked occurrences. Main Save stores accepted edits.",
                "Los nombres son etiquetas reutilizables, no datos compartidos. "
                "Renombrar actualiza sus referencias. Guardar almacena los cambios.",
            )
        )
        hint.setWordWrap(True)
        root.addWidget(hint)
        self.initial = "All"
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            self.text("Search names or descriptions", "Buscar nombres o descripciones")
        )
        self.search.setToolTip(self.search.placeholderText())
        self.search.textChanged.connect(self.filter_rows)
        root.addWidget(self.search)
        self.alphabet = AlphabetNavigation(
            self.text("All", "Todos"), self.choose_initial
        )
        root.addWidget(self.alphabet)
        self.table = QTreeWidget()
        style_rotation_table(self.table)
        self.table.setRootIsDecorated(False)
        self.table.setHeaderLabels(
            [
                self.text("Task name", "Nombre de tarea"),
                self.text("Description", "Descripción"),
            ]
        )
        self.table.setToolTip(
            self.text(
                "Choose a name to edit its metadata.",
                "Seleccione un nombre para editar sus detalles.",
            )
        )
        self.table.currentItemChanged.connect(self.select_name)
        root.addWidget(self.table, 1)
        actions = QHBoxLayout()
        self.add = QPushButton(self.text("Add task name", "Añadir nombre de tarea"))
        self.remove = QPushButton(self.text("Delete name", "Eliminar nombre"))
        for button in (self.add, self.remove):
            button.setAutoDefault(False)
            actions.addWidget(button)
        self.add.setToolTip(
            self.text(
                "Enter a new reusable name below.",
                "Ingrese un nuevo nombre reutilizable abajo.",
            )
        )
        self.remove.setToolTip(
            self.text(
                "Delete an unused definition; linked names are protected.",
                "Eliminar un nombre sin referencias; los utilizados están protegidos.",
            )
        )
        self.add.clicked.connect(self.new_name)
        self.remove.clicked.connect(self.delete_name)
        actions.addStretch(1)
        root.addLayout(actions)
        form = QFormLayout()
        self.name, self.description = QLineEdit(), QLineEdit()
        self.name.setToolTip(
            self.text(
                "Required name. Linked task inputs and results do not change.",
                "Nombre obligatorio. No modifica entradas ni resultados.",
            )
        )
        self.description.setToolTip(
            self.text(
                "Optional description of this activity.",
                "Descripción opcional de esta actividad.",
            )
        )
        form.addRow(self.text("Name", "Nombre"), self.name)
        form.addRow(self.text("Description", "Descripción"), self.description)
        for control in (self.name, self.description):
            control.editingFinished.connect(self.form_finished)
        root.addLayout(form)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color:#AD302B;")
        root.addWidget(self.error)
        close = QPushButton(self.text("Close", "Cerrar"))
        close.setAutoDefault(False)
        close.clicked.connect(self.accept)
        root.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)
        self.reload()

    def text(self, english: str, spanish: str) -> str:
        """Choose interface wording while preserving literal project metadata.

        Args:
            english: English caption.
            spanish: Spanish caption.

        Returns:
            Caption in this window's language.
        """
        return spanish if self.language is Language.SPANISH else english

    def reload(self) -> None:
        """Reload the accepted catalog after edits/replay, preserving selection by ID.

        Args:
            None.

        Returns:
            None; empty catalogs do not manufacture placeholder records.
        """
        self._loading = True
        try:
            self.catalog = self.workspace.load_task_definitions()
            self.table.clear()
            selected = None
            for record in sorted(
                self.catalog, key=lambda d: (d.name.casefold(), d.definition_id)
            ):
                item = QTreeWidgetItem([record.name, record.description or ""])
                item.setData(0, Qt.ItemDataRole.UserRole, record.definition_id)
                for column in (0, 1):
                    item.setToolTip(column, item.text(column))
                self.table.addTopLevelItem(item)
                if record.definition_id == self.identity:
                    selected = item
            self.table.setCurrentItem(selected)
            current = next(
                (d for d in self.catalog if d.definition_id == self.identity), None
            )
            self.identity = current.definition_id if current else None
            self.name.setText(current.name if current else "")
            self.description.setText(current.description or "" if current else "")
            self.remove.setEnabled(current is not None)
            self.table.resizeColumnToContents(0)
            self.filter_rows()
        finally:
            self._loading = False

    def filter_rows(self) -> None:
        """Filter metadata without changing selection, definitions or history.

        Args:
            None.

        Returns:
            None; substring search is case insensitive.
        """
        text = self.search.text().casefold()
        available = set()
        for index in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(index)
            assert item is not None
            initial = (
                normalize("NFKD", item.text(0))
                .encode("ascii", "ignore")
                .decode()[:1]
                .upper()
            )
            matches = text in (item.text(0) + " " + item.text(1)).casefold()
            if matches:
                available.add(initial)
            item.setHidden(
                not matches or (self.initial != "All" and initial != self.initial)
            )
        self.alphabet.set_available(frozenset(available), self.initial)

    def choose_initial(self, initial: str) -> None:
        """Apply a local name initial without changing metadata or project history.

        Args:
            initial: All or one enabled shared alphabet letter.

        Returns:
            None; the existing text search remains active.
        """
        self.initial = initial
        self.filter_rows()

    def select_name(self) -> None:
        """Select a stable catalog identity after accepting valid preceding text.

        Args:
            None.

        Returns:
            None; invalid edits keep the old identity and correction fields.
        """
        if self._loading:
            return
        item = self.table.currentItem()
        target = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if self.commit():
            self.identity = target
            self.reload()
        else:
            with QSignalBlocker(self.table):
                for index in range(self.table.topLevelItemCount()):
                    row = self.table.topLevelItem(index)
                    if (
                        row is not None
                        and row.data(0, Qt.ItemDataRole.UserRole) == self.identity
                    ):
                        self.table.setCurrentItem(row)
                        break

    def form_finished(self) -> None:
        """Accept a completed metadata field through the shared validator.

        Args:
            None.

        Returns:
            None; invalid text remains visible with correction guidance.
        """
        self.commit()

    def commit(self) -> bool:
        """Accept one complete metadata edit through the original shared owner.

        Args:
            None.

        Returns:
            False retains invalid/stale text; True accepts a change or exact no-op.
        """
        if self._loading or (self.identity is None and not self.name.text().strip()):
            return True
        try:
            if self.workspace.editing is not self.owner:
                raise ValueError("The original project is no longer open.")
            record = TaskDefinition(
                self.identity or uuid4().hex,
                self.name.text().strip(),
                self.description.text() or None,
            )
            replacement = tuple(
                sorted(
                    (
                        *(
                            d
                            for d in self.catalog
                            if d.definition_id != record.definition_id
                        ),
                        record,
                    ),
                    key=lambda d: d.definition_id,
                )
            )
            if replacement != self.catalog:
                self.workspace.replace_task_definitions(self.catalog, replacement)
            self.identity = record.definition_id
            self.reload()
            self.error.clear()
            self.history.refresh()
            return True
        except Exception as error:
            self.show_failure(error)
            return False

    def new_name(self) -> None:
        """Start a detached empty name after completing any previous metadata edit.

        Args:
            None.

        Returns:
            None; a new definition is accepted only after nonempty name completion.
        """
        if self.commit():
            self.identity = None
            self.reload()
            self.name.setFocus()

    def delete_name(self) -> None:
        """Confirm removal of an unused name; repository protects referenced IDs.

        Args:
            None.

        Returns:
            None; accepted deletion shares Main history and remains unsaved on disk.
        """
        if not self.commit() or self.identity is None:
            return
        if (
            QMessageBox.question(
                self,
                self.windowTitle(),
                self.text(
                    "Delete this reusable name? Undo restores it.",
                    "¿Eliminar este nombre? Deshacer lo restaura.",
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        try:
            self.workspace.replace_task_definitions(
                self.catalog,
                tuple(d for d in self.catalog if d.definition_id != self.identity),
            )
            self.identity = None
            self.reload()
            self.error.clear()
            self.history.refresh()
        except Exception as error:
            self.show_failure(error)

    def show_failure(self, error: Exception) -> None:
        """Explain validation failures and log unexpected adapter failures safely.

        Args:
            error: Failure from the guarded catalog port or metadata validator.

        Returns:
            None; pending fields and accepted data remain available for correction.
        """
        message = str(error)
        if message == "A reusable task is still referenced by an assessment.":
            message = self.text(
                "This name is used by an assessment. Rename it or remove its "
                "task references before deleting it.",
                "Una evaluación usa este nombre. Renómbrelo o quite sus "
                "referencias antes de eliminarlo.",
            )
        elif message in (
            "Task definition requires an identity and fallback name.",
            "Task name must be nonblank text or absent.",
        ):
            message = self.text(
                "Enter a nonempty task name.", "Ingrese un nombre de tarea."
            )
        elif not isinstance(error, (ValueError, RuntimeError)):
            _LOG.exception("Unable to accept reusable task metadata")
            message = self.text(
                "The edit could not be accepted. Your input is kept.",
                "No se aceptó el cambio. Se conservan sus entradas.",
            )
        self.error.setText(message)

    def accept(self) -> None:
        """Close after valid name completion; Main Save remains authoritative.

        Args:
            None.

        Returns:
            None; invalid metadata remains available for correction.
        """
        if self.commit():
            super().accept()

    def reject(self) -> None:
        """Use the same completion policy for the window close control and Escape.

        Args:
            None.

        Returns:
            None; no accepted project edits are discarded.
        """
        self.accept()
