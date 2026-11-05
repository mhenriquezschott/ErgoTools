"""Shared task-name and spreadsheet actions bound to explicit assessment host ports.

Presentation layer. Main panels and Job editors inject source acceptance, catalog
operations and pending-input validation. This controller never owns document history,
SQL or calculation and never accepts an obsolete clipboard preview into another source.
"""

import csv
import logging
from collections.abc import Callable
from io import StringIO
from uuid import uuid4

from PyQt5 import sip
from PyQt5.QtCore import QObject, QSignalBlocker
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
)

from ergotools.application.assessment_clipboard import assessment_clipboard_text
from ergotools.application.assessment_import import (
    ImportProfile,
    parse_import_text,
    prepare_import,
)
from ergotools.application.assessment_task_rows import remove_assessment_rows
from ergotools.application.project_editing import ProjectEditingSession
from ergotools.application.settings import Language
from ergotools.application.task_catalog import TaskSourceAcceptor, label_assessment_task
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    assessment_kind,
    task_has_content,
)
from ergotools.domain.assessments.duet import DuetTask
from ergotools.domain.assessments.lifft_draft import LifftTask
from ergotools.domain.assessments.tst import TstTask
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.presentation.desktop.assessment_import_panel import clipboard_field
from ergotools.presentation.desktop.assessment_paste_dialog import AssessmentPasteDialog
from ergotools.presentation.desktop.assessment_task_grid import AssessmentTaskGrid
from ergotools.presentation.desktop.assessment_task_text import task_input_error


class AssessmentTaskActions(QObject):
    """Bind shared grid actions without imposing a main/Job history implementation."""

    def __init__(
        self,
        grid: AssessmentTaskGrid,
        *,
        source: Callable[[], AssessmentDraft | None],
        accept: Callable[[AssessmentDraft, AssessmentDraft, str, bool], bool],
        accept_paste: Callable[
            [AssessmentDraft, AssessmentDraft, frozenset[str], TaskSourceAcceptor], bool
        ],
        definitions: Callable[[], tuple[TaskDefinition, ...]],
        replace_definitions: Callable[
            [tuple[TaskDefinition, ...], tuple[TaskDefinition, ...]], None
        ],
        before_action: Callable[[], bool],
        system: Callable[[], MeasurementSystem],
        convention: Callable[[], DecimalConvention],
    ) -> None:
        """Connect native actions to current project/source callbacks.

        Args:
            grid: Shared native editor; owns this controller's Qt lifetime.
            source: Read exact canonical source, not a unit-projected UI draft.
            accept: Expected/replacement/label/rebuild acceptance owned by the host.
            accept_paste: Shared atomic source/catalog/history acceptance.
            definitions: Read current reusable names without creating records.
            replace_definitions: Guarded catalog acceptance through project history.
            before_action: Commit pending inputs before an action; False blocks.
            system: Current input/display measurement system.
            convention: Current explicit decimal separator.

        Returns:
            None; construction reads/writes no project data.
        """
        super().__init__(grid)
        self.grid = grid
        self.source = source
        self.accept_source = accept
        self.accept_paste = accept_paste
        self.definitions = definitions
        self.replace_definitions = replace_definitions
        self.before_action = before_action
        self.system = system
        self.convention = convention
        self._finishing = False
        self._catalog_owner: ProjectEditingSession | None = None
        self._catalog_cleanup: list[Callable[[], None]] = []
        cleanup = self._catalog_cleanup

        def stop_catalog() -> None:
            """Detach catalog notifications when Qt destroys this editor controller.

            Args:
                None.

            Returns:
                None; the callback retains no Qt owner or project writer.
            """
            while cleanup:
                cleanup.pop()()

        self.destroyed.connect(stop_catalog)
        grid.task_name_finished.connect(self.finish_name)
        grid.copy_cells_button.clicked.connect(self.copy)
        grid.paste_cells_button.clicked.connect(self.paste)
        grid.import_settings_button.clicked.connect(lambda: self.paste(configure=True))
        grid.task_names_button.clicked.connect(self.task_names_menu)

    def bind_catalog(self, editing: ProjectEditingSession | None) -> None:
        """Follow the current project's catalog without retaining a closed editor.

        Args:
            editing: Shared project owner, or None when the project closes.

        Returns:
            None; project switching detaches the prior weak listener. Notifications
            refresh choices only when definitions changed, never numeric fields.
        """
        if editing is self._catalog_owner:
            return
        while self._catalog_cleanup:
            self._catalog_cleanup.pop()()
        self._catalog_owner = editing
        if editing is not None:
            self._catalog_cleanup.append(editing.subscribe(self.refresh_catalog))

    def refresh_catalog(self) -> None:
        """Publish new reusable choices across open grids without losing typed names.

        Args:
            None.

        Returns:
            None; destroyed Qt grids are ignored. Pending literal names defer refresh
            until completion. Source
            loading/replay owns full rebinding; catalog changes never accept inputs.
        """
        if sip.isdeleted(self) or sip.isdeleted(self.grid):
            return
        if self.source() is None or self.pending_names():
            return
        if self.definitions() != self.grid.task_definitions:
            self.refresh_names()

    def remove_selected(self, fallback: int | None = None) -> bool:
        """Confirm and accept one ordered multi-row removal through the existing host.

        Args:
            fallback: Host default when no explicit range/header is selected.

        Returns:
            True after one source replacement; invalid inputs, cancellation or a stale
            source preserve existing data. Removing all rows leaves one blank starter.
        """
        rows = self.grid.selected_task_rows(fallback)
        if not rows or not self.before_action():
            return False
        source = self.source()
        if source is None or any(r >= len(source.tasks) for r in rows):
            return False
        if any(task_has_content(source.tasks[r]) for r in rows):
            answer = QMessageBox.question(
                self.grid,
                self.text("Remove tasks", "Quitar tareas"),
                self.text(
                    f"Remove {len(rows)} selected task(s) and their data? "
                    "Undo restores them.",
                    f"¿Quitar {len(rows)} tarea(s) seleccionada(s) y sus datos? "
                    "Deshacer las restaura.",
                ),
                QMessageBox.StandardButtons(
                    QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes)
                    | QMessageBox.StandardButtons(QMessageBox.StandardButton.Cancel)
                ),
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return False
        if self.source() != source:
            return False
        return self.accept_source(
            source,
            remove_assessment_rows(source, rows),
            "assessment.remove_tasks",
            True,
        )

    def text(self, english: str, spanish: str) -> str:
        """Resolve interface text using the grid's current language.

        Args:
            english: English caption/message.
            spanish: Spanish caption/message.

        Returns:
            Requested caption without changing literal task names.
        """
        return spanish if self.grid.language is Language.SPANISH else english

    def finish_name(self, task_id: str, name: str | None, identity: str | None) -> None:
        """Accept one completed descriptive cell through the host source command.

        Args:
            task_id: Exact currently displayed task row.
            name: Optional literal fallback activity name.
            identity: Optional explicitly chosen reusable definition reference.

        Returns:
            None; stale or no-source completions do not create an edit.
        """
        self.refresh_catalog()
        source = self.source()
        if source is None or not any(t.task_id == task_id for t in source.tasks):
            return
        original = next(t for t in source.tasks if t.task_id == task_id)
        definition = next(
            (d for d in self.definitions() if d.definition_id == identity), None
        )
        if (
            identity == original.task_definition_id
            and definition is not None
            and definition.name == name
        ):
            return
        replacement = label_assessment_task(source, task_id, name, identity)
        if replacement != source:
            self.accept_source(source, replacement, "assessment.task_name", False)
        self.refresh_catalog()

    def pending_names(self) -> bool:
        """Inspect pending name text without accepting it or truncating Redo.

        Args:
            None.

        Returns:
            True if a displayed editable name differs from its canonical live label.
        """
        source = self.source()
        if source is None or len(source.tasks) != len(self.grid.task_names):
            return False
        tasks: tuple[LifftTask | DuetTask | TstTask, ...] = source.tasks
        names = {d.definition_id: d.name for d in self.definitions()}
        return any(
            isinstance(control, QComboBox)
            and control.currentText()
            != names.get(task.task_definition_id or "", task.task_name or "")
            for task, control in zip(tasks, self.grid.task_names, strict=True)
        )

    def finish_names(self) -> bool:
        """Commit remaining name text before Save/close without recursive completion.

        Args:
            None.

        Returns:
            True if any source name changed; fields retain separate history actions.
        """
        if self._finishing:
            return False
        self._finishing = True
        before = self.source()
        try:
            source = before
            if source is None or len(source.tasks) != len(self.grid.task_names):
                return False
            tasks: tuple[LifftTask | DuetTask | TstTask, ...] = source.tasks
            for task, control in zip(tasks, self.grid.task_names, strict=True):
                if isinstance(control, QComboBox):
                    name = (
                        control.currentText() if control.currentText().strip() else None
                    )
                    identity = control.currentData()
                    match = next(
                        (
                            d
                            for d in self.definitions()
                            if d.definition_id == identity and d.name == name
                        ),
                        None,
                    )
                    self.finish_name(task.task_id, name, identity if match else None)
        finally:
            self._finishing = False
        return before != self.source()

    def refresh_names(self) -> None:
        """Refresh reusable choices after a catalog edit without touching numeric cells.

        Args:
            None.

        Returns:
            None; source fallback labels/results and row identities remain unchanged.
        """
        source = self.source()
        self.grid.task_definitions = self.definitions()
        if source is None:
            return
        tasks: tuple[LifftTask | DuetTask | TstTask, ...] = source.tasks
        for task, control in zip(tasks, self.grid.task_names, strict=True):
            if not isinstance(control, QComboBox):
                continue
            name = next(
                (
                    d.name
                    for d in self.grid.task_definitions
                    if d.definition_id == task.task_definition_id
                ),
                task.task_name or "",
            )
            with QSignalBlocker(control):
                control.clear()
                control.addItem("", None)
                for definition in sorted(
                    self.grid.task_definitions,
                    key=lambda d: (d.name.casefold(), d.definition_id),
                ):
                    control.addItem(definition.name, definition.definition_id)
                control.setCurrentIndex(
                    max(0, control.findData(task.task_definition_id))
                )
                control.setEditText(name)
                control.setToolTip(name)

    def copy(self) -> None:
        """Copy the explicit input rectangle, or all inputs, after pending validation.

        Args:
            None.

        Returns:
            None; TSV retains headers, quoting, units and full precision. Range
            selection is captured before a pending-input commit can rebuild controls.
            Clipboard replacement never edits assessment/project history.
        """
        selection = self.grid.selected_cell_range()
        if not self.before_action():
            return
        source = self.source()
        clipboard = QApplication.clipboard()
        if source is not None and clipboard is not None:
            text = assessment_clipboard_text(
                source, self.definitions(), self.convention(), self.system()
            )
            if selection is not None:
                rows, fields = selection
                all_fields = ("task_name", *self.grid.input_fields)
                columns = tuple(all_fields.index(field) for field in fields)
                values = list(csv.reader(StringIO(text), delimiter="\t"))
                stream = StringIO()
                writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
                for index in (0, *(row + 1 for row in rows)):
                    if index < len(values):
                        writer.writerow([values[index][column] for column in columns])
                text = stream.getvalue()
            clipboard.setText(text)

    def paste(self, *, configure: bool = False) -> None:
        """Paste validated configured values or open the shared import preview.

        Args:
            configure: True always opens mapping/file import rather than quick paste.

        Returns:
            None; cancellation/invalid previews do not change the assessment.
        """
        if not self.before_action():
            return
        source = self.source()
        clipboard = QApplication.clipboard()
        if source is None or clipboard is None:
            return
        service = self.grid.editor_preferences
        try:
            profile = (
                service.profile(
                    assessment_kind(source), self.system(), self.convention()
                )
                if service
                else None
            )
            if profile and profile.configured and not configure:
                try:
                    rows = parse_import_text(clipboard.text(), profile.delimiter)
                    if profile.header:
                        for index, (caption, field) in enumerate(
                            zip(rows[0], profile.fields, strict=True)
                        ):
                            guessed = clipboard_field(caption)
                            expected = profile.headers[index] if profile.headers else ""
                            if field is not None and (
                                guessed not in (None, field)
                                or (
                                    guessed is None
                                    and caption.strip().casefold()
                                    != expected.strip().casefold()
                                )
                            ):
                                raise ValueError(
                                    "Headers differ from the saved mapping."
                                )
                    replacement = prepare_import(
                        source, rows, profile, max(0, self.grid.selected_task_index)
                    )
                except ValueError:
                    # Review invalid/ambiguous data without silently skipping cells.
                    pass
                else:
                    self.apply_paste(
                        source,
                        replacement,
                        profile,
                        len(rows) - int(profile.header),
                        max(0, self.grid.selected_task_index),
                    )
                    return
            dialog = AssessmentPasteDialog(
                source,
                clipboard.text(),
                self.grid.language,
                self.convention(),
                self.system(),
                max(0, self.grid.selected_task_index),
                self.grid,
                icons=self.grid.icons,
                start_field=self.grid.selected_input_field,
                profile=profile,
                file_reader=service.reader if service else None,
            )
            try:
                if (
                    dialog.exec() == QDialog.Accepted
                    and dialog.replacement is not None
                    and self.apply_paste(
                        source,
                        dialog.replacement,
                        dialog.panel.profile(),
                        len(dialog.panel.included_rows())
                        - int(dialog.panel.header_option.isChecked()),
                        dialog.panel.start.value() - 1,
                    )
                    and service is not None
                ):
                    try:
                        service.save(dialog.panel.profile())
                    except (OSError, ValueError) as error:
                        QMessageBox.warning(
                            self.grid,
                            self.text("Paste preferences", "Preferencias de pegado"),
                            self.text(
                                "Inputs were applied, but paste defaults "
                                "could not be saved.\n",
                                "Se aplicaron los datos, pero no se "
                                "guardaron las preferencias.\n",
                            )
                            + str(error),
                        )
            finally:
                dialog.deleteLater()
        except Exception as error:
            logging.getLogger(__name__).exception("Assessment paste failed")
            QMessageBox.warning(
                self.grid,
                self.text("Paste task inputs", "Pegar tareas"),
                task_input_error(
                    error if isinstance(error, ValueError) else ValueError(str(error)),
                    self.grid.language,
                ),
            )

    def apply_paste(
        self,
        expected: AssessmentDraft,
        replacement: AssessmentDraft,
        profile: ImportProfile,
        row_count: int,
        start_row: int,
    ) -> bool:
        """Accept exact pasted name cells and inputs in one shared project action.

        Args:
            expected: Canonical source captured before preparation.
            replacement: Complete validated replacement, with unmapped cells retained.
            profile: Actual accepted per-column mapping.
            row_count: Included body rows, excluding header and skipped source rows.
            start_row: Zero-based destination row chosen in the preview/quick paste.

        Returns:
            True after source/catalog acceptance and choice refresh. Unmapped name
            columns and task rows outside this rectangle create no catalog entries.
        """
        named = (
            frozenset(
                task.task_id
                for task in replacement.tasks[start_row : start_row + row_count]
                if task.task_name is not None
            )
            if "task_name" in profile.fields
            else frozenset()
        )
        accepted = self.accept_paste(expected, replacement, named, self.accept_source)
        if accepted:
            self.refresh_names()
        return accepted

    def task_names_menu(self) -> None:
        """Offer optional creation/rename of reusable project labels beside the grid.

        Args:
            None.

        Returns:
            None; creating a definition and selecting it are explicit separate actions.
        """
        if not self.before_action():
            return
        self.refresh_names()
        menu = QMenu(self.grid)
        add = menu.addAction(
            self.text("Add reusable name…", "Agregar nombre reutilizable…")
        )
        rename = menu.addAction(
            self.text(
                "Rename selected reusable name…",
                "Renombrar nombre reutilizable seleccionado…",
            )
        )
        source = self.source()
        index = self.grid.selected_task_index
        identity = (
            source.tasks[index].task_definition_id
            if source is not None and 0 <= index < len(source.tasks)
            else None
        )
        assert add is not None and rename is not None
        rename.setEnabled(identity is not None)
        selected = menu.exec(
            self.grid.task_names_button.mapToGlobal(
                self.grid.task_names_button.rect().bottomLeft()
            )
        )
        if selected not in (add, rename):
            return
        old = self.definitions()
        current = next((d for d in old if d.definition_id == identity), None)
        name, ok = QInputDialog.getText(
            self.grid,
            self.text("Reusable task name", "Nombre de tarea reutilizable"),
            self.text(
                "Name (renaming updates every linked occurrence)",
                "Nombre (renombrar actualiza todas las referencias)",
            ),
            text=current.name if selected == rename and current else "",
        )
        if not ok or not name.strip():
            return
        definition = TaskDefinition(
            current.definition_id if selected == rename and current else uuid4().hex,
            name.strip(),
            current.description if selected == rename and current else None,
        )
        replacement = tuple(
            sorted(
                (
                    *[d for d in old if d.definition_id != definition.definition_id],
                    definition,
                ),
                key=lambda d: d.definition_id,
            )
        )
        try:
            self.replace_definitions(old, replacement)
            self.refresh_names()
        except (ValueError, RuntimeError) as error:
            QMessageBox.warning(
                self.grid, self.text("Task names", "Nombres de tareas"), str(error)
            )
