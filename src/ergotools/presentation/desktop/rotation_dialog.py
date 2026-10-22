"""Original modal JROT scheme commands over a borrowed project repository.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from functools import partial

from PyQt5.QtCore import QSignalBlocker, QSize
from PyQt5.QtGui import QCloseEvent, QIcon, QResizeEvent
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ergotools.application.project_editing import ProjectEditingSession
from ergotools.application.rotation_access import RotationRepository
from ergotools.application.rotation_draft import (
    RotationProjectDraft,
    refresh_rotation_draft,
    stage_rotation_draft,
)
from ergotools.application.rotation_history import (
    ReplaceRotationEdit,
    RotationEditState,
)
from ergotools.application.rotation_optimization import RotationOptimizer
from ergotools.application.rotation_pool import rotation_pool
from ergotools.application.rotation_scope import rotation_scope_options
from ergotools.application.session import DocumentKey, DocumentSession
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.domain.rotation_scheme import RotationScheme
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions
from ergotools.presentation.desktop.rotation_form import RotationForm
from ergotools.presentation.desktop.rotation_history import RotationHistoryActions
from ergotools.presentation.desktop.rotation_scope_dialog import RotationScopeDialog
from ergotools.presentation.desktop.rotation_solve import RotationSolveController
from ergotools.presentation.desktop.rotation_table import RotationTable

# Module-scoped diagnostic logger for owned rotation command/solver failures.
_LOGGER = logging.getLogger(__name__)
# Match the repository's SQLite NOCASE order (ASCII case folding only).
_ID_CASE_ORDER = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)


class RotationDialog(RotationForm):
    """Own scheme editing, keeping persistence separate from the original view.

    The caller owns the repository and executes this dialog modally. Commands publish
    saved state only after repository success. Catalog preparation before replacing the
    grid keeps failed reads from discarding the user's current edits. An injected
    optimizer enables owned CBC/HiGHS solves and original comparison workflows. Draft
    history is scoped to the currently selected scheme.
    """

    def __init__(
        self,
        repository: RotationRepository,
        icons: Mapping[str, QIcon],
        *,
        language: Language = Language.ENGLISH,
        optimizer: RotationOptimizer | None = None,
        editing: ProjectEditingSession | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Read schemes and build the original form without writes or upgrades.

        Args:
            repository: Borrowed active-project capability; the caller retains
                connection lifetime.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            editing: Shared project session; retains partial drafts across
                window closing.
            optimizer: Injected CBC/HiGHS solver capability; None keeps solve actions
                unavailable.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        self.editing = editing
        self._accepting_rotation = True
        self.history: DocumentSession[RotationEditState] | None = None
        self._replaying_history = False
        self.history_actions: RotationHistoryActions | ProjectHistoryActions | None = (
            None
        )
        self.optimization: RotationSolveController | None = None
        self.repository = repository
        self.schemes = repository.load_rotation_schemes()
        self.loaded: RotationScheme | None = None
        self._cancel_id: str | None = None
        self._draft = False
        self._manual_edit = False
        self.scope: tuple[WorkplaceContext, ...] = ()
        self.pending_scope: tuple[WorkplaceContext, ...] = ()
        self.kind = AssessmentKind.LIFFT
        self.grid: RotationTable | None = None
        super().__init__(icons, language=language, parent=parent)
        self._list_schemes(None)
        if self.schemes:
            self._show_scheme(self.schemes[0])
        else:
            self._replace_grid(self._new_grid(()))
        for kind, button in self.tool_buttons.items():
            button.clicked.connect(lambda checked, value=kind: self.select_kind(value))
        self.scheme_combo.activated.connect(self._select_index)
        self.scheme_combo.editTextChanged.connect(self._states)
        for button, index in zip(self.navigation, (0, -1, 1, 2), strict=True):
            button.clicked.connect(lambda checked, value=index: self._navigate(value))
        self.new_button.clicked.connect(lambda: self._guard(self.new_scheme))
        self.save_button.clicked.connect(lambda: self._guard(self.save_scheme))
        self.delete_button.clicked.connect(lambda: self._guard(self.delete_scheme))
        self.cancel_button.clicked.connect(lambda: self._guard(self.cancel_scheme))
        self.search_button.clicked.connect(self.search_scheme)
        self.apply_scope_button.clicked.connect(lambda: self._guard(self.apply_scope))
        self.clear_scope_button.clicked.connect(lambda: self._guard(self.clear_scope))
        self.choose_scope_button.clicked.connect(lambda: self._guard(self.choose_scope))
        self.all_scope_button.clicked.connect(self._organization_scope)
        self.workplace_scope_button.clicked.connect(self._workplace_scope)
        if optimizer is not None:
            self.optimization = RotationSolveController(self, optimizer)
        self.reset_history()
        if editing is None:
            self.history_actions = RotationHistoryActions(self)
        else:
            self.save_button.hide()
            self.history_actions = ProjectHistoryActions(
                self,
                editing,
                icons,
                language,
                restored=self.restore_project_rotation,
                blocked=lambda: (
                    self.optimization is not None and self.optimization.busy
                ),
            )
            self.title_row.addWidget(self.history_actions.undo_button)
            self.title_row.addWidget(self.history_actions.redo_button)
            editing.validate_on_save(
                "rotation.view", partial(stage_rotation_draft, repository)
            )
            retained = editing.editor("rotation.view")
            if isinstance(retained, RotationProjectDraft):
                self.restore_project_rotation()
            else:
                draft = RotationProjectDraft(
                    self.scheme_combo.currentText().strip(),
                    self._edit_state(),
                    self.loaded,
                )
                editing.seed_editor("rotation.view", draft)
            field = self.scheme_combo.lineEdit()
            assert field is not None
            field.editingFinished.connect(self.accept_rotation_state)
        self._accepting_rotation = False
        self._states()

    def accept_rotation_state(self) -> None:
        """Retain partial rotation intent and stage complete schemes privately.

        Args:
            None.

        Returns:
            None; incomplete grids remain available after reopening and block the
            main project Save until completed or explicitly cancelled.
        """
        editing = self.editing
        if editing is None or self._accepting_rotation or editing.replaying:
            return
        self._accepting_rotation = True
        try:
            draft = RotationProjectDraft(
                self.scheme_combo.currentText().strip(),
                self._edit_state(),
                self.loaded,
            )
            try:
                candidate = draft.scheme() if draft.has_data else None
            except ValueError:
                candidate = None
            with editing.suspend():
                editing.set_editor("rotation.view", draft, "rotation.edit")
                if (
                    candidate is not None
                    and candidate not in self.repository.load_rotation_schemes()
                ):
                    try:
                        self.repository.save_rotation_scheme(candidate)
                    except Exception:
                        _LOGGER.exception(
                            "Unable to stage rotation; retained for project Save retry"
                        )
            pending = (
                draft.data_token
                if draft.has_data
                and (
                    candidate is None
                    or candidate not in self.repository.load_rotation_schemes()
                )
                else None
            )
            editing.set_editor(
                "rotation.pending", pending, "rotation.edit", persistent=True
            )
        finally:
            self._accepting_rotation = False

    def restore_project_rotation(self) -> None:
        """Rebind JROT to the same project cursor used by every other editor.

        Args:
            None.

        Returns:
            None; frozen pools, partial cells, IDs and solver provenance are restored.
            Solver ownership blocks invoking this callback during a running solve.
        """
        editing = self.editing
        if editing is None:
            return
        self._accepting_rotation = True
        try:
            self.schemes = self.repository.load_rotation_schemes()
            draft = editing.editor("rotation.view")
            if not isinstance(draft, RotationProjectDraft):
                self.cancel_scheme()
                return
            self.loaded = next(
                (s for s in self.schemes if s.scheme_id == draft.scheme_id), None
            )
            self._list_schemes(draft.scheme_id if self.loaded else None)
            with QSignalBlocker(self.scheme_combo):
                self.scheme_combo.setEditText(draft.scheme_id)
            draft = refresh_rotation_draft(self.repository, draft)
            state = draft.state
            self._restore_rotation_state(state)
            self.history = DocumentSession(
                DocumentKey(draft.state.pool.project_id, "rotation-draft"),
                state,
                persisted=True,
            )
        finally:
            self._accepting_rotation = False

    def _edit_state(self) -> RotationEditState:
        """Freeze partial grid choices, exact evidence pool, applied/pending scope.

        Freeze partial grid choices, exact evidence pool, applied/pending scope and
        optimization provenance for one scheme-local undo value.

        Args:
            None.

        Returns:
            Immutable partial scheme draft including exact pool, opaque cells, scope and
            provenance for Undo/Redo.
        """
        assert self.grid is not None
        mode = self.optimization.applied_mode if self.optimization is not None else None
        kind = self.optimization.applied_kind if self.optimization is not None else None
        if (
            mode is None
            and not self._manual_edit
            and not self._draft
            and self.loaded is not None
        ):
            mode, kind = self.loaded.mode, self.loaded.primary_kind
        return RotationEditState(
            self.grid.pool,
            max(2, self.grid.blocks),
            tuple(
                tuple(
                    self.grid.choice_key(row, column)
                    for column in range(self.grid.blocks + 1)
                )
                for row in range(self.grid.rowCount())
            ),
            self.scope,
            self._manual_edit,
            mode,
            kind,
            self.kind,
            self.pending_scope,
            self.workplace_scope_button.isChecked(),
        )

    def reset_history(self) -> None:
        """Start a scheme-local history after New, load, Cancel or deletion.

        Args:
            None.

        Returns:
            None.
        """
        state = self._edit_state()
        self.history = DocumentSession(
            DocumentKey(state.pool.project_id, "rotation-draft"),
            state,
            persisted=self.loaded is not None and not self._draft,
        )
        self.accept_rotation_state()
        if self.history_actions is not None:
            self.history_actions.refresh()

    def record_history(self) -> None:
        """Capture one accepted cell, batch, scope or optimized-Apply command.

        Args:
            None.

        Returns:
            None.
        """
        if self.history is not None and not self._replaying_history:
            self.history.execute(
                ReplaceRotationEdit(
                    self.history.document, self.history.state, self._edit_state()
                )
            )
        self.accept_rotation_state()
        if self.history_actions is not None:
            self.history_actions.refresh()

    def replay_history(self, *, redo: bool) -> None:
        """Restore exact links and provenance without repository reads or writes.

        Args:
            redo: True replays the next operation; False restores the previous
                operation.

        Returns:
            None.
        """
        if self.history is None or (
            self.optimization is not None and self.optimization.busy
        ):
            return
        if not (self.history.redo() if redo else self.history.undo()):
            return
        state = self.history.state
        self._restore_rotation_state(state)

    def _restore_rotation_state(self, state: RotationEditState) -> None:
        """Project an exact immutable grid/scope revision without recording an edit.

        Args:
            state: Accepted source pool, partial cells and optimization provenance.

        Returns:
            None; selection changes are suppressed during historical projection.
        """
        grid = RotationTable(
            state.pool,
            workers=max(1, len(state.cells)),
            blocks=state.blocks,
            kind=state.display_kind,
            language=self.language,
            parent=self,
            clear_icon=self.icons["delete"],
        )
        grid.restore_choices(state.cells)
        self._replace_grid(grid)
        self.scope = state.scope
        self.pending_scope = state.pending_scope
        self._replaying_history = True
        try:
            self.select_kind(state.display_kind)
        finally:
            self._replaying_history = False
        # Saved identity is lifecycle state, not part of the source undo stack.
        self._draft = self.loaded is None
        self._manual_edit = state.manual_edit
        if self.optimization is not None:
            self.optimization.applied_mode = state.mode
            self.optimization.applied_kind = state.primary_kind
        self._scope_controls(workplace=state.workplace_scope)
        self._states()
        if self.history_actions is not None:
            self.history_actions.refresh()

    def reject(self) -> None:
        """Defer Escape/Close until the owned solver has actually finished.

        Args:
            None.

        Returns:
            None.
        """
        if self.optimization is not None and self.optimization.request_close():
            return
        self.accept_rotation_state()
        super().reject()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        """Apply the same owned-worker rule to the window-manager close action.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        if self.optimization is not None and self.optimization.request_close():
            if event is not None:
                event.ignore()
            return
        self.accept_rotation_state()
        super().closeEvent(event)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        """Keep the source-centered busy overlay covering the local dialog.

        Args:
            event: Qt event delivered on the GUI thread; optional overrides tolerate
                None.

        Returns:
            None.
        """
        super().resizeEvent(event)
        if self.optimization is not None:
            self.optimization.resize_overlay()

    def _guard(self, operation: Callable[[], None]) -> None:
        """Invoke one explicit rotation operation and report failures.

        Invoke one explicit rotation operation and report failures without silently
        discarding the current draft.

        Args:
            operation: One explicit command invoked through the dialog's
                failure-preserving boundary.

        Returns:
            None.
        """
        try:
            operation()
        except Exception:
            # GUI command boundary: log diagnostics and report failure, never hide it.
            _LOGGER.exception("JROT scheme command failed")
            self._message(
                self.text(
                    "Unable to complete the rotation operation. "
                    "Your edits are retained.",
                    "No se pudo completar la operación de rotación. "
                    "Se conservan sus cambios.",
                ),
                error=True,
            )

    def _message(self, message: str, *, error: bool = False) -> None:
        """Execute an owned localized message dialog and release its Qt resources.

        Execute an owned localized message dialog and release its Qt resources after the
        user responds.

        Args:
            message: Literal user-facing notification/error content.
            error: True displays the failure title; False displays the normal
                informational title.

        Returns:
            None.
        """
        title = self.text("Rotation scheme", "Esquema de rotación")
        if error:
            title = self.text(
                "Incomplete or unavailable rotation",
                "Rotación incompleta o no disponible",
            )
        self._message_box(title, message)

    def _message_box(self, title: str, body: str, *, question: bool = False) -> int:
        """Execute an owned styled JROT message with localized buttons.

        Execute an owned styled JROT message with localized buttons and explicit
        No-default deletion consent.

        Args:
            title: Localized message/window title; never used as a stored identifier.
            body: Literal message content shown by the owned styled dialog.
            question: True presents Yes/No consent; False presents an informational
                acknowledgement.

        Returns:
            Qt standard-button integer chosen by the user after the owned message
            closes.
        """
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(body)
        box.setIconPixmap(self.icons["jrot"].pixmap(QSize(40, 40)))
        labels: tuple[tuple[QMessageBox.StandardButton, str, str], ...]
        if question:
            box.setStandardButtons(
                QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes)
                | QMessageBox.StandardButton.No
            )
            box.setDefaultButton(QMessageBox.StandardButton.No)
            labels = (
                (
                    QMessageBox.StandardButton.Yes,
                    self.text("Yes", "Sí"),
                    "filter_apply",
                ),
                (QMessageBox.StandardButton.No, self.text("No", "No"), "cancel"),
            )
        else:
            box.setStandardButtons(QMessageBox.StandardButton.Ok)
            labels = (
                (
                    QMessageBox.StandardButton.Ok,
                    self.text("OK", "Aceptar"),
                    "filter_apply",
                ),
            )
        for standard, label, icon in labels:
            button = box.button(standard)
            assert button is not None
            button.setText(label)
            button.setIcon(self.icons[icon])
        try:
            return box.exec()
        finally:
            box.deleteLater()

    def _confirm_delete(self) -> bool:
        """Collect explicit confirmation before deleting a saved rotation identity.

        Args:
            None.

        Returns:
            True only for explicit Yes to deleting the selected saved rotation scheme.
        """
        return (
            self._message_box(
                self.text("Confirm Deletion", "Confirmar eliminación"),
                self.text(
                    "Are you sure you want to delete this rotation scheme?",
                    "¿Desea eliminar este esquema de rotación?",
                ),
                question=True,
            )
            == QMessageBox.StandardButton.Yes
        )

    def _list_schemes(self, selected: str | None) -> None:
        """Rebuild saved scheme identities under signal blocking.

        Rebuild saved scheme identities under signal blocking and restore the requested
        selection or empty New state.

        Args:
            selected: Saved Job/worker identity to reselect, or None for the local
                default.

        Returns:
            None.
        """
        with QSignalBlocker(self.scheme_combo):
            self.scheme_combo.clear()
            self.scheme_combo.addItems([scheme.scheme_id for scheme in self.schemes])
            self.scheme_combo.setCurrentIndex(
                self.scheme_combo.findText(selected or "")
            )
            if selected is None:
                self.scheme_combo.setEditText("")

    def _new_grid(self, scope: tuple[WorkplaceContext, ...]) -> RotationTable:
        """Prepare a source-bounded manual grid from the exact applied scope.

        Prepare a source-bounded manual grid from the exact applied scope and current
        row/block counts before replacing the old grid.

        Args:
            scope: Exact typed workplace filter; no selection is reconstructed from
                displayed labels.

        Returns:
            New owned manual grid prepared from the exact scope and bounded requested
            counts.
        """
        pool = rotation_pool(self.repository, scope)
        grid = RotationTable(
            pool,
            kind=self.kind,
            language=self.language,
            blocks=int(self.blocks_combo.currentText()),
            clear_icon=self.icons["delete"],
        )
        eligible = len(grid.choice_options(0, 1))
        count = min(
            int(self.workers_combo.currentText()), len(pool.workers), eligible, 10
        )
        grid.reset_grid(max(1, count), grid.blocks)
        return grid

    def _replace_grid(self, grid: RotationTable) -> None:
        """Detach and release the old grid.

        Detach and release the old grid, connect the new owned grid once, synchronize
        counts and invalidate obsolete optimized preview.

        Args:
            grid: New owned editable grid, fully prepared before replacing the old Qt
                component.

        Returns:
            None.
        """
        old = self.grid
        if old is not None:
            self.current_layout.removeWidget(old)
            old.hide()
            old.deleteLater()
        self.grid = grid
        self.current_layout.addWidget(grid, 1)
        grid.changed.connect(self._edited)
        with QSignalBlocker(self.workers_combo):
            self.workers_combo.setCurrentText(str(grid.rowCount()))
        with QSignalBlocker(self.blocks_combo):
            self.blocks_combo.setCurrentText(str(grid.blocks))
        self.optimized_table.clear()
        self.optimized_table.setRowCount(0)
        self.optimized_table.setColumnCount(0)
        if self.optimization is not None:
            self.optimization.clear_result()

    def _show_scheme(self, scheme: RotationScheme) -> None:
        """Prepare the exact saved scheme and frozen evidence pool.

        Prepare the exact saved scheme and frozen evidence pool before replacing
        controls and resetting scheme-local history.

        Args:
            scheme: Immutable complete saved or proposed rotation scheme with exact
                evidence links.

        Returns:
            None.
        """
        pool = rotation_pool(self.repository, scheme.scope, saved=scheme)
        grid = RotationTable(
            pool,
            kind=scheme.primary_kind or self.kind,
            language=self.language,
            clear_icon=self.icons["delete"],
        )
        grid.load_scheme(scheme)
        self._replace_grid(grid)
        self.loaded = scheme
        self._cancel_id = scheme.scheme_id
        self._draft = False
        self._manual_edit = False
        self.scope = scheme.scope
        self.pending_scope = scheme.scope
        self._list_schemes(scheme.scheme_id)
        self.select_kind(scheme.primary_kind or self.kind)
        self._scope_controls()
        self._states()
        self.reset_history()

    def _select_index(self, index: int) -> None:
        """Load a valid saved scheme through the failure boundary.

        Load a valid saved scheme through the failure boundary; invalid indices retain
        the current selection.

        Args:
            index: Zero-based combo/tab/directory position within the current local
                selection.

        Returns:
            None.
        """
        if 0 <= index < len(self.schemes):
            previous = self.loaded.scheme_id if self.loaded else None
            self._guard(lambda: self._show_scheme(self.schemes[index]))
            # A rejected read must not leave the selector claiming another scheme.
            if (
                self.loaded is None
                or self.loaded.scheme_id != self.schemes[index].scheme_id
            ):
                self._list_schemes(previous)

    def _navigate(self, direction: int) -> None:
        """Navigate to the requested saved scheme.

        Resolve the original first/previous/next/last navigation command into a saved
        scheme index.

        Args:
            direction: Navigation command; the source first/previous/next/last sentinel
                values are retained.

        Returns:
            None.
        """
        index = self.scheme_combo.currentIndex()
        target = (
            0
            if direction == 0
            else len(self.schemes) - 1
            if direction == 2
            else index + direction
        )
        self._select_index(target)

    def _states(self) -> None:
        """Refresh scheme navigation/delete/search/solve/history availability.

        Refresh scheme navigation/delete/search/solve/history availability without
        issuing persistence commands.

        Args:
            None.

        Returns:
            None.
        """
        index = self.scheme_combo.currentIndex()
        saved = (
            not self._draft
            and self.loaded is not None
            and index >= 0
            and self.scheme_combo.currentText() == self.loaded.scheme_id
        )
        for button, enabled in zip(
            self.navigation,
            (
                saved and index > 0,
                saved and index > 0,
                saved and index < len(self.schemes) - 1,
                saved and index < len(self.schemes) - 1,
            ),
            strict=True,
        ):
            button.setEnabled(enabled)
        self.delete_button.setEnabled(saved)
        self.search_button.setEnabled(not self._draft and bool(self.schemes))
        if self.optimization is not None:
            self.optimization.refresh_states()
        if self.history_actions is not None:
            self.history_actions.refresh()

    def _edited(self) -> None:
        """Mark the grid as manually edited, invalidate optimized preview.

        Mark the grid as manually edited, invalidate optimized preview and record one
        accepted history operation.

        Args:
            None.

        Returns:
            None.
        """
        self._manual_edit = True
        if self.optimization is not None:
            self.optimization.clear_result()
        self.record_history()

    def select_kind(self, kind: AssessmentKind) -> None:
        """Change displayed evidence without discarding unsaved cells or saving.

        Args:
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.

        Returns:
            None.
        """
        assert self.grid is not None
        changed = self.kind is not kind
        self.grid.set_kind(kind)
        self.kind = kind
        if changed and self.optimization is not None:
            self.optimization.clear_result(clear_provenance=False)
        for value, button in self.tool_buttons.items():
            button.setChecked(value is kind)
        label = {
            AssessmentKind.LIFFT: "LiFFT",
            AssessmentKind.DUET: "DUET",
            AssessmentKind.TST: "ST",
        }[kind]
        self.current_title.setText(
            self.text(f"Current {label} Rotation", f"Rotación actual {label}")
        )

        if changed:
            self.record_history()

    def new_scheme(self) -> None:
        """Start an empty manual draft; Cancel can restore the selected saved scheme.

        Args:
            None.

        Returns:
            None.
        """
        grid = self._new_grid(self.scope)
        self._replace_grid(grid)
        self._draft = True
        self._manual_edit = False
        with QSignalBlocker(self.scheme_combo):
            self.scheme_combo.setCurrentIndex(-1)
            self.scheme_combo.setEditText("")
        self._states()
        self.reset_history()

    def cancel_scheme(self) -> None:
        """Discard the draft and restore the previous saved scheme or an empty grid.

        Args:
            None.

        Returns:
            None.
        """
        selected = next(
            (scheme for scheme in self.schemes if scheme.scheme_id == self._cancel_id),
            None,
        )
        if selected is None and self.schemes:
            selected = self.schemes[0]
        if selected is not None:
            self._show_scheme(selected)
        else:
            self._replace_grid(self._new_grid(()))
            self.loaded = None
            self._draft = False
            self._manual_edit = False
            self.scope = ()
            self.pending_scope = ()
            self._list_schemes(None)
            self._scope_controls()
            self._states()
            self.reset_history()

    def save_scheme(self) -> None:
        """Validate complete cells and publish only after the explicit save commits.

        Args:
            None.

        Returns:
            None.
        """
        assert self.grid is not None
        identity = self.scheme_combo.currentText().strip()
        if not identity:
            self._message(
                self.text("Rotation ID is required.", "Se requiere el ID de rotación."),
                error=True,
            )
            return
        try:
            candidate = self.grid.current_scheme(identity, scope=self.scope)
        except ValueError:
            self._message(
                self.text(
                    "Select an eligible Worker and Job in every row and time block.",
                    "Seleccione un trabajador y un trabajo en cada fila y bloque.",
                ),
                error=True,
            )
            return
        if self.loaded is not None and self.loaded.scheme_id == identity:
            candidate = replace(
                candidate, name=self.loaded.name, description=self.loaded.description
            )
        if self.history is not None and not self._manual_edit:
            state = self.history.state
            if state.mode is not None:
                candidate = replace(
                    candidate, mode=state.mode, primary_kind=state.primary_kind
                )
        if self.optimization is not None:
            candidate = self.optimization.prepare_save(candidate)
        assert self.history is not None
        self.history.save(_RotationStore(self.repository, candidate))
        self.schemes = tuple(
            sorted(
                (
                    *(
                        scheme
                        for scheme in self.schemes
                        if scheme.scheme_id != identity
                    ),
                    candidate,
                ),
                key=lambda scheme: scheme.scheme_id.translate(_ID_CASE_ORDER),
            )
        )
        self.loaded = candidate
        self._cancel_id = identity
        self._draft = False
        self._manual_edit = False
        self._list_schemes(identity)
        self._states()
        self._message(
            self.text(
                f"Rotation scheme '{identity}' was saved "
                "with its worker and Job arrangements.",
                f"Se guardó la rotación '{identity}' con sus trabajadores y trabajos.",
            )
        )

    def delete_scheme(self) -> None:
        """Delete only the selected saved identity after the original confirmation.

        Args:
            None.

        Returns:
            None.
        """
        if self._draft or self.loaded is None:
            return
        identity = self.loaded.scheme_id
        if not self._confirm_delete():
            return
        # Prepare the following view before committing deletion, so reads cannot
        # fail after a successful delete and misleadingly report a retained record.
        remaining = tuple(
            scheme for scheme in self.schemes if scheme.scheme_id != identity
        )
        next_scheme = remaining[0] if remaining else None
        pool = rotation_pool(
            self.repository, next_scheme.scope if next_scheme else (), saved=next_scheme
        )
        grid = RotationTable(
            pool,
            kind=self.kind,
            language=self.language,
            clear_icon=self.icons["delete"],
        )
        if next_scheme is not None:
            grid.load_scheme(next_scheme)
        self.repository.delete_rotation_scheme(identity)
        self.schemes = remaining
        self._replace_grid(grid)
        self.loaded = next_scheme
        self._cancel_id = next_scheme.scheme_id if next_scheme else None
        self._draft = False
        self._manual_edit = False
        self.scope = next_scheme.scope if next_scheme else ()
        self.pending_scope = self.scope
        if next_scheme is None:
            grid.clear()
            grid.setRowCount(0)
            grid.setColumnCount(0)
        self.select_kind(
            next_scheme.primary_kind or self.kind if next_scheme else self.kind
        )
        self._list_schemes(self._cancel_id)
        self._scope_controls()
        self._states()
        self.reset_history()
        self._message(
            self.text(
                f"Rotation scheme '{identity}' has been deleted successfully.",
                f"Se eliminó la rotación '{identity}'.",
            )
        )

    def _organization_scope(self) -> None:
        """Select organization-wide pending scope and record the accepted filter state.

        Select organization-wide pending scope and record the accepted filter state
        without applying a new grid.

        Args:
            None.

        Returns:
            None.
        """
        self.pending_scope = ()
        self._scope_controls(workplace=False)
        self.record_history()

    def _workplace_scope(self) -> None:
        """Select workplace-filter mode, request exact pending scope if needed.

        Select workplace-filter mode, request exact pending scope if needed, and record
        accepted configuration.

        Args:
            None.

        Returns:
            None.
        """
        self.choose_scope_button.setEnabled(True)
        if not self.pending_scope:
            self._guard(self.choose_scope)
        else:
            self._scope_controls(workplace=True)
            self.record_history()

    def _scope_controls(self, *, workplace: bool | None = None) -> None:
        """Project pending scope mode and chooser availability.

        Project pending scope mode and chooser availability without applying or saving
        it.

        Args:
            workplace: True selects workplace-filter mode; False selects
                organization-wide mode; None derives the pending scope state.

        Returns:
            None.
        """
        selected = bool(self.pending_scope) if workplace is None else workplace
        self.workplace_scope_button.setChecked(selected)
        self.all_scope_button.setChecked(not selected)
        self.choose_scope_button.setEnabled(selected)
        self._summary()

    def _summary(self) -> None:
        """Show the pending scope's all/single/count path summaries.

        Show the pending scope's all/single/count path summaries and full literal
        tooltips.

        Args:
            None.

        Returns:
            None.
        """
        for index, label in enumerate(self.scope_values):
            values = {
                (
                    place.plant_name,
                    place.section_name,
                    place.line_name,
                    place.station_id,
                    place.shift_id,
                )[index]
                for place in self.pending_scope
            }
            value = (
                next(iter(values))
                if len(values) == 1
                else self.text(f"{len(values)} sel.", f"{len(values)} selec.")
                if values
                else self.text("All", "Todos")
            )
            label.setText(value)
            label.setToolTip(" / ".join(sorted(values)) if values else value)

    def choose_scope(self) -> None:
        """Accept exact pending stations from the original modal scope chooser.

        Args:
            None.

        Returns:
            None.
        """
        dialog = RotationScopeDialog(
            rotation_scope_options(self.repository),
            self.icons,
            selected=self.pending_scope or self.scope,
            language=self.language,
            parent=self,
        )
        previous = self.history.state.workplace_scope if self.history else False
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.pending_scope = dialog.selected_contexts()
                self._scope_controls(workplace=True)
                self.record_history()
            else:
                self._scope_controls(workplace=previous)
        finally:
            dialog.deleteLater()

    def apply_scope(self) -> None:
        """Rebuild the manual draft using explicitly applied scope and counts.

        Args:
            None.

        Returns:
            None.
        """
        if self.workplace_scope_button.isChecked() and not self.pending_scope:
            self._message(
                self.text(
                    "Select at least one Workplace Station.",
                    "Seleccione al menos una estación.",
                ),
                error=True,
            )
            return
        grid = self._new_grid(self.pending_scope)
        self._replace_grid(grid)
        self.scope = self.pending_scope
        self._draft = True
        self._manual_edit = False
        self._states()
        self.record_history()
        if not grid.pool.workers or not grid.pool.targets:
            self._message(
                self.text(
                    "The selected scope needs at least one active Job placement "
                    "and one active Worker assignment.",
                    "El ámbito requiere un puesto activo "
                    "y una asignación activa de trabajador.",
                ),
                error=True,
            )

    def clear_scope(self) -> None:
        """Apply the original organization-wide empty manual draft operation.

        Args:
            None.

        Returns:
            None.
        """
        grid = self._new_grid(())
        self._replace_grid(grid)
        self.scope = ()
        self.pending_scope = ()
        self._draft = True
        self._manual_edit = False
        self._scope_controls()
        self._states()
        self.record_history()

    def search_scheme(self) -> None:
        """Search exact saved IDs in the original 400x150 modal child form.

        Args:
            None.

        Returns:
            None.
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(
            self.text("Search Rotation Scheme", "Buscar esquema de rotación")
        )
        dialog.setFixedSize(400, 150)
        layout = QVBoxLayout(dialog)
        row = QHBoxLayout()
        entry = QLineEdit()
        row.addWidget(QLabel(self.text("Search by Rotation ID:", "Buscar por ID:")))
        row.addWidget(entry)
        layout.addLayout(row)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButtons(QDialogButtonBox.StandardButton.Ok)
            | QDialogButtonBox.StandardButton.Cancel
        )
        accept = buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        assert accept is not None and cancel is not None
        accept.setText(self.text("OK", "Aceptar"))
        accept.setIcon(self.icons["filter_apply"])
        cancel.setText(self.text("Cancel", "Cancelar"))
        cancel.setIcon(self.icons["cancel"])
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            identity = entry.text().strip()
            index = next(
                (
                    i
                    for i, scheme in enumerate(self.schemes)
                    if scheme.scheme_id == identity
                ),
                -1,
            )
            if index >= 0:
                self._select_index(index)
            else:
                self._message(
                    self.text(
                        "No rotation scheme found with the given ID.",
                        "No se encontró un esquema con ese ID.",
                    )
                )
        dialog.deleteLater()


@dataclass(frozen=True, slots=True)
class _RotationStore:
    """Scheme-local history store forwarding only the already validated complete scheme.

    Scheme-local history store forwarding only the already validated complete scheme to
    the existing atomic repository writer.
    """

    repository: RotationRepository
    scheme: RotationScheme

    def save(self, document: DocumentKey, state: RotationEditState) -> None:
        """Mark history clean only after the existing atomic scheme write commits.

        Args:
            document: Project-scoped history identity; must belong to this repository.
            state: Immutable source/view snapshot to project without recording another
                edit.

        Returns:
            None.

        Raises:
            ValueError: Rotation save belongs to another project.
        """
        if (
            document.project_id != self.scheme.project_id
            or state.pool.project_id != document.project_id
        ):
            raise ValueError("Rotation save belongs to another project.")
        self.repository.save_rotation_scheme(self.scheme)
