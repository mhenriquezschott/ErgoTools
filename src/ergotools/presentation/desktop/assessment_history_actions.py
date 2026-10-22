"""Window-scoped assessment shortcuts with native typing ownership.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

import logging
from typing import TYPE_CHECKING
from weakref import ref

from PyQt5 import sip
from PyQt5.QtCore import QObject, Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QComboBox, QLineEdit, QScrollArea

from ergotools.application.assessment_interactions import (
    AssessmentInteractions,
    InteractionStep,
    same_position,
)
from ergotools.application.assessment_navigation import AssessmentView
from ergotools.application.session import DocumentKey
from ergotools.presentation.desktop.project_history_actions import ProjectHistoryActions

if TYPE_CHECKING:
    from ergotools.presentation.desktop.lifft_window import LifftWindow


class AssessmentHistoryActions(QObject):
    """Route chronological replay and retain edit-time task viewport positions."""

    def __init__(self, view: "LifftWindow") -> None:
        """Bind existing menu actions; no toolbar or global shortcut is added.

        Args:
            view: Owning integrated window whose controls and existing command policy
                are reused.

        Returns:
            None.
        """
        super().__init__(view)
        self.view = view
        self.shared: ProjectHistoryActions | None = None
        self._project_revision = 0
        self._project_scroll: dict[int, tuple[DocumentKey, tuple[int, int]]] = {}
        self.interactions = AssessmentInteractions()
        self._edit_scroll: dict[InteractionStep, tuple[int, int]] = {}
        self._pending_scroll: dict[DocumentKey, tuple[int, int]] = {}
        self._scroll_target: (
            tuple[QScrollArea, tuple[int, int], DocumentKey, int] | None
        ) = None
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._settle_scroll)
        menu = view._assessment_menu
        assert menu is not None
        for key, standard in (
            ("undo", QKeySequence.StandardKey.Undo),
            ("redo", QKeySequence.StandardKey.Redo),
        ):
            action = menu.actions_by_key[key]
            action.setShortcuts(QKeySequence.keyBindings(standard))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            view.addAction(action)
            action.triggered.connect(
                lambda checked=False, redo=key == "redo": self.replay(redo=redo)
            )
        menu.edit.aboutToShow.connect(self.refresh)
        app = QApplication.instance()
        assert isinstance(app, QApplication)
        # The application outlives every editor window. A weak receiver prevents
        # focus notifications from retaining or entering a window during cyclic
        # garbage collection; native destruction also disconnects the callback.
        receiver = ref(self)

        def focus_changed() -> None:
            """Refresh shortcut availability only while the weakly referenced owner.

            Refresh shortcut availability only while the weakly referenced owner and its
            native window remain alive.

            Args:
                None.

            Returns:
                None.
            """
            owner = receiver()
            if owner is not None and not sip.isdeleted(owner.view):
                owner.refresh()

        app.focusChanged.connect(focus_changed)
        view.destroyed.connect(lambda: app.focusChanged.disconnect(focus_changed))
        self.refresh()

    def _pending_grid_action(self) -> str | None:
        """Expose a valid pending task edit through the existing shared cursor.

        Args:
            None.

        Returns:
            Assessment edit label when canonical values differ; None otherwise.
            Inspection never accepts input, calculates or changes the Redo branch.
        """
        panel = self.view.secondary_panel() or self.view.task_panel
        return (
            "assessment.edit"
            if panel is not None and panel.pending_change() is True
            else None
        )

    def _grid_history_blocked(self) -> bool:
        """Keep invalid pending task text and diagnostic field drafts intact.

        Args:
            None.

        Returns:
            True when replay cannot safely accept the current input first.
        """
        panel = self.view.secondary_panel() or self.view.task_panel
        return self.view.pending or (
            panel is not None and panel.pending_change() is None
        )

    def _prepare_grid(self) -> bool:
        """Accept pending grid input as one shared edit immediately before replay.

        Args:
            None.

        Returns:
            True after the existing parser/command boundary and shared staging;
            invalid input is interlocked before entry. No calculation or Save runs.
        """
        panel = self.view.secondary_panel() or self.view.task_panel
        if panel is not None and panel.commit_inputs():
            panel.context = panel.presenter.bind()
            self.refresh()
        return True

    def focused_field(self) -> QLineEdit | None:
        """Keep text undo inside this window, excluding all owned modal dialogs.

        Args:
            None.

        Returns:
            Focused line editor owned by this window, or None when focus belongs
            elsewhere; caller borrows it.
        """
        field = QApplication.focusWidget()
        if isinstance(field, QComboBox) and field.isEditable():
            field = field.lineEdit()
        return (
            field
            if isinstance(field, QLineEdit) and field.window() is self.view
            else None
        )

    def refresh(self) -> None:
        """Observe accepted operations and capture their edit-time scroll position.

        Args:
            None.

        Returns:
            None.
        """
        menu = self.view._assessment_menu
        assert menu is not None
        workspace = self.view.presenter.workspace
        editing = workspace.editing
        if editing is not None:
            if self.shared is None or self.shared.editing is not editing:
                if self.shared is not None:
                    self.shared.deleteLater()
                self.shared = ProjectHistoryActions(
                    self.view,
                    editing,
                    self.view.icons,
                    self.view.language,
                    prepare=self._prepare_grid,
                    pending=self._pending_grid_action,
                    restored=self._restore_shared,
                    blocked=self._grid_history_blocked,
                )
                # Weak session notification also covers edits in open management
                # windows, without catalogue reads or task-widget reconstruction.
                editing.subscribe(self.view.refresh_save_controls)
                self.shared.undo_action.setShortcuts([])
                self.shared.redo_action.setShortcuts([])
            if not editing.replaying:
                active = workspace.active
                panel = self.view.secondary_panel() or self.view.task_panel
                source_changed = active is not None and active.is_dirty
                position_before = (0, 0)
                if active is not None and panel is not None:
                    horizontal = panel.body_scroll.horizontalScrollBar()
                    vertical = panel.body_scroll.verticalScrollBar()
                    assert horizontal is not None and vertical is not None
                    position_before = (horizontal.value(), vertical.value())
                    if self.view.pending:
                        self._pending_scroll.setdefault(
                            active.document, position_before
                        )
                try:
                    workspace.stage_assessments()
                except Exception:
                    logging.getLogger(__name__).exception(
                        "Unable to accept assessment drafts"
                    )
                    self.view.message.setText(self.view.text("error"))
                    self.shared.refresh()
                    return
                if source_changed and active is not None:
                    self._project_scroll[editing.history.revision] = (
                        active.document,
                        self._pending_scroll.pop(active.document, position_before),
                    )
                # Adoption reads catalogue authorities. A focus notification alone
                # must not invalidate snapshots borrowed by open management dialogs.
                if source_changed:
                    if self.view.main_navigation is not None:
                        # A completed cell is now accepted before Calculate. Project
                        # its dirty/context state without rebuilding the task widgets.
                        self.view.refresh_navigation()
                    elif self.view.assessment_navigation.view is not None:
                        self.view.assessment_navigation.adopt_active()
                position = self.view.assessment_navigation.view
                previous_view = editing.editor("assessment.view")
                if previous_view is None:
                    editing.seed_editor("assessment.view", position)
                    previous_view = position
                if not same_position(
                    previous_view
                    if isinstance(previous_view, AssessmentView)
                    else None,
                    position,
                ):
                    if (
                        previous_view is None
                        or position is None
                        or self._project_revision != editing.history.revision
                    ):
                        editing.project_editor("assessment.view", position)
                    else:
                        editing.set_editor(
                            "assessment.view", position, "assessment.view"
                        )
                self._project_revision = editing.history.revision
            self.shared.language = self.view.language
            self.shared.refresh()
            for key, source in (
                ("undo", self.shared.undo_action),
                ("redo", self.shared.redo_action),
            ):
                action = menu.actions_by_key[key]
                action.setEnabled(source.isEnabled())
                action.setText(source.text())
                action.setToolTip(source.toolTip())
                if self.view.main_navigation is not None:
                    button = self.view.main_navigation.toolbar_actions[key]
                    button.setEnabled(action.isEnabled())
                    button.setToolTip(action.toolTip())
            self.view.refresh_save_controls()
            return
        if self.shared is not None:
            self.shared.deleteLater()
            self.shared = None
        field = self.focused_field()
        active = self.view.presenter.workspace.active
        panel = self.view.secondary_panel() or self.view.task_panel
        if panel is not None and active is not None and self.view.pending:
            horizontal = panel.body_scroll.horizontalScrollBar()
            vertical = panel.body_scroll.verticalScrollBar()
            assert horizontal is not None and vertical is not None
            self._pending_scroll.setdefault(
                active.document, (horizontal.value(), vertical.value())
            )
        previous = (
            self.interactions.undo_steps[-1:] if not self.interactions.replaying else []
        )
        self.interactions.observe(
            self.view.presenter.workspace.location,
            self.view.assessment_navigation.view,
            active,
        )
        steps = self.interactions.undo_steps
        panel = self.view.secondary_panel() or self.view.task_panel
        if (
            not self.interactions.replaying
            and steps
            and steps[-1:] != previous
            and steps[-1].session is not None
            and panel is not None
        ):
            area = panel.body_scroll
            horizontal, vertical = area.horizontalScrollBar(), area.verticalScrollBar()
            assert horizontal is not None and vertical is not None
            assert active is not None
            self._edit_scroll[steps[-1]] = self._pending_scroll.pop(
                active.document, (horizontal.value(), vertical.value())
            )
        if active is not None and not self.view.pending:
            self._pending_scroll.pop(active.document, None)
        if active is None:
            self._pending_scroll.clear()
        retained = set((*steps, *self.interactions.redo_steps))
        self._edit_scroll = {
            step: position
            for step, position in self._edit_scroll.items()
            if step in retained
        }
        for key in ("undo", "redo"):
            action = menu.actions_by_key[key]
            action.setEnabled(
                (
                    not field.isReadOnly()
                    and (
                        field.isUndoAvailable()
                        if key == "undo"
                        else field.isRedoAvailable()
                    )
                )
                if field is not None
                else (
                    active is not None
                    and not self.view.pending
                    and bool(
                        self.interactions.undo_steps
                        if key == "undo"
                        else self.interactions.redo_steps
                    )
                )
            )

            navigation = self.view.main_navigation
            if navigation is not None:
                button_action = navigation.toolbar_actions[key]
                button_action.setEnabled(action.isEnabled())
                button_action.setToolTip(action.toolTip())

    def replay(self, *, redo: bool) -> None:
        """Replay one local operation; draft changes still require explicit Save.

        Args:
            redo: True replays the next operation; False restores the previous
                operation.

        Returns:
            None.
        """
        if (
            self.view.presenter.workspace.editing is not None
            and self.shared is not None
        ):
            if self.focused_field() is None:
                self.view.setFocus(Qt.FocusReason.OtherFocusReason)
            self.shared.replay(redo=redo)
            self.refresh()
            return
        field = self.focused_field()
        if field is not None:
            field.redo() if redo else field.undo()
        else:
            self.view.run(lambda: self._replay_interaction(redo))
        self.refresh()

    def _restore_shared(self) -> None:
        """Rebind the main assessment view after any shared project replay.

        Args:
            None.

        Returns:
            None; a deleted selection falls back to the first remaining worker.
        """
        host = self.view
        workspace = host.presenter.workspace
        editing = workspace.editing
        if editing is None:
            return
        position = editing.editor("assessment.view")
        workers = workspace.read_hierarchy().hierarchy.work.workers
        worker_ids = {w.worker_id for w in workers}
        if isinstance(position, AssessmentView) and position.worker_id in worker_ids:
            host.assessment_navigation.select(
                position.worker_id,
                position.kind,
                lambda: host._blank_kind(position.kind),
                workplace=position.workplace,
                keep=True,
                explicit=True,
                assignment_id=position.assignment_id,
            )
        elif workers:
            kind = host.active_kind()
            host.assessment_navigation.select(
                workers[0].worker_id,
                kind,
                lambda: host._blank_kind(kind),
            )
        else:
            host.assessment_navigation.view = None
        host.refresh()
        scroll = self._project_scroll.get(editing.replay_revision or -1)
        panel = host.secondary_panel() or host.task_panel
        active = workspace.active
        if (
            scroll is not None
            and panel is not None
            and active is not None
            and active.document == scroll[0]
        ):
            self._scroll_target = (
                panel.body_scroll,
                scroll[1],
                active.document,
                active.revision,
            )
            self._settle_scroll(keep=True)
            self._scroll_timer.start(0)

    def _restore_view(self, position: AssessmentView) -> bool:
        """Restore exact worker/tool/context through the existing navigation services.

        Args:
            position: Earlier accepted selection; never move or copy assessment data.

        Returns:
            False when dirty consent is cancelled; True after successful selection.
            Save/Discard remain explicit across worker/workplace boundaries.
        """
        host = self.view
        browser = host.assessment_navigation
        current = browser.view
        crossing_owner = current is not None and (
            current.worker_id,
            current.workplace,
            current.assignment_id,
        ) != (position.worker_id, position.workplace, position.assignment_id)
        if crossing_owner and not host.presenter.workspace.resolve_browse(
            host.browse_choice()
        ):
            return False
        browser.select(
            position.worker_id,
            position.kind,
            lambda: host._blank_kind(position.kind),
            workplace=position.workplace,
            keep=True,
            explicit=True,
            assignment_id=position.assignment_id,
        )
        host.refresh()
        return True

    def _replay_interaction(self, redo: bool) -> None:
        """Replay one navigation/source step and rebind controls only after success.

        Args:
            redo: True reapplies the next chronological operation.

        Returns:
            None; rejected transitions leave controls and the history cursor intact.
        """
        timeline = self.interactions
        stack = timeline.redo_steps if redo else timeline.undo_steps
        step = stack[-1] if stack else None
        position = self._edit_scroll.get(step) if step is not None else None
        # Removing a focused combo/editor otherwise advances focus through every
        # rebuilt task and QScrollArea automatically reveals the final task.
        self.view.setFocus(Qt.FocusReason.OtherFocusReason)
        if timeline.replay(
            redo, self._restore_view, self.view.presenter.workspace.active
        ):
            timeline.replaying = True
            try:
                self.view.refresh()
            finally:
                timeline.replaying = False
            panel = self.view.secondary_panel() or self.view.task_panel
            active = self.view.presenter.workspace.active
            if position is not None and panel is not None and active is not None:
                self._scroll_target = (
                    panel.body_scroll,
                    position,
                    active.document,
                    active.revision,
                )
                self._settle_scroll(keep=True)
                self._scroll_timer.start(0)

    def _settle_scroll(self, *, keep: bool = False) -> None:
        """Restore edit-time scroll after synchronous and queued task-grid layout.

        Args:
            keep: Retain the target for the one queued settle pass after grid reflow.

        Returns:
            None; clamp naturally when task counts shrink. Ignore a different source
            or revision and dead widgets; queued restore cannot move another view.
            The owned timer is cancelled automatically when this action owner dies.
        """
        target = self._scroll_target
        if not keep:
            self._scroll_target = None
        if target is None:
            return
        area, position, document, revision = target
        active = self.view.presenter.workspace.active
        if (
            sip.isdeleted(area)
            or active is None
            or active.document != document
            or active.revision != revision
        ):
            return
        horizontal, vertical = area.horizontalScrollBar(), area.verticalScrollBar()
        assert horizontal is not None and vertical is not None
        horizontal.setValue(position[0])
        vertical.setValue(position[1])
