"""Compose the context dialog with pending-text and workspace dirty decisions.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Callable, Mapping

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QWidget

from ergotools.application.document_lifecycle import CloseChoice
from ergotools.application.project_workspace import ProjectWorkspace, TransitionOutcome
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import (
    AssessmentDraft,
    AssessmentKind,
    assessment_kind,
)
from ergotools.presentation.assignment_selection import (
    AssignmentRequest,
    AssignmentSelector,
)
from ergotools.presentation.desktop.assessment_context_dialog import (
    AssessmentContextDialog,
)


class AssignmentDialogHost:
    """Coordinate assessment selection and creation without owning editor widgets.

    resolve_pending must return True only after text was applied or explicitly
    discarded; False cancels. choose_dirty returns the user's decision. Neither callback
    may silently discard edits. Exceptions propagate to the owning window for display.
    Successful callers rebind/render the workspace's active source.
    """

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        *,
        resolve_pending: Callable[[], bool],
        choose_dirty: Callable[[], CloseChoice | None],
        parent: QWidget | None = None,
    ) -> None:
        """Inject editor decisions and styled icons without opening a dialog.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            resolve_pending: Callback returning True only after pending text is applied
                or explicitly discarded.
            choose_dirty: Callback collecting Save/Discard/Cancel for the active dirty
                source.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        self._workspace = workspace
        self._selector = AssignmentSelector(workspace)
        self._icons = icons
        self._resolve_pending = resolve_pending
        self._choose_dirty = choose_dirty
        self._parent = parent
        self._busy = False

    def select(
        self,
        worker_id: str,
        kind: AssessmentKind,
        *,
        current: WorkplaceContext | None = None,
    ) -> TransitionOutcome:
        """Resolve text, show the dialog, then decide dirty source disposition.

        Text application is a separate edit: cancelling the later dialog does not undo
        it. Missing current assessments raise KeyError; creation is deliberate, never an
        automatic fallback. The modal dialog is released on every exit.

        Args:
            worker_id: Exact stored worker identifier; captions and surname sorting are
                not identities.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.
            current: Currently committed workplace, or None when no assignment is
                selected.

        Returns:
            Transition outcome identifying accepted activation and any warnings;
            cancelled text/dialog/dirty consent returns an incomplete outcome.
        """
        return self._run(worker_id, kind, current=current)

    def create(
        self, worker_id: str, document_id: str, initial: AssessmentDraft
    ) -> TransitionOutcome:
        """Create an assessment for an explicitly selected assignment/tool.

        Existing assignment/tool ownership conflicts fail before old-source save. This
        never clones tasks or replaces an existing assessment.

        Args:
            worker_id: Exact stored worker identifier; captions and surname sorting are
                not identities.
            document_id: New stable assessment identity supplied by the caller.
            initial: Initial typed assessment source for explicit creation; never
                inferred from an existing result.

        Returns:
            Transition outcome for explicit assessment creation; cancellation returns
            an incomplete outcome without implicit replacement.
        """
        return self._run(
            worker_id, assessment_kind(initial), creation=(document_id, initial)
        )

    def _run(
        self,
        worker_id: str,
        kind: AssessmentKind,
        *,
        current: WorkplaceContext | None = None,
        creation: tuple[str, AssessmentDraft] | None = None,
    ) -> TransitionOutcome:
        """Own one exact assignment selection transition.

        Resolve pending text, own one modal selection, then apply explicit dirty-source
        consent to select or create the exact assignment.

        The dialog is released and the reentrancy flag restored on every exit.

        Args:
            worker_id: Exact stored worker identifier; captions and surname sorting are
                not identities.
            kind: Exact ergonomic tool identity (LiFFT, DUET or Shoulder Tool); display
                captions are not keys.
            current: Currently committed workplace, or None when no assignment is
                selected.
            creation: Optional new document identity and source; None selects existing
                data.

        Returns:
            Completed/cancelled typed transition outcome; the owned modal and reentrancy
            flag are released on every exit.

        Raises:
            RuntimeError: Assignment dialog transition is already in progress.
            ValueError: The dialog did not return an assignment request. Work hierarchy
        """
        if self._busy:
            raise RuntimeError("Assignment dialog transition is already in progress.")
        self._busy = True
        try:
            if not self._resolve_pending():
                return TransitionOutcome(False)
            hierarchy = self._workspace.read_hierarchy()
            catalog = self._selector.refresh()
            dialog = AssessmentContextDialog(
                self._selector,
                catalog,
                worker_id,
                kind,
                (),
                self._icons,
                current=current,
                shifts=hierarchy.hierarchy.work.shifts,
                parent=self._parent,
            )
            try:
                if dialog.exec() != QDialog.Accepted:
                    return TransitionOutcome(False)
                request = dialog.selected
                if not isinstance(request, AssignmentRequest):
                    raise ValueError("The dialog did not return an assignment request.")
                if not self._workspace.hierarchy_is_current(hierarchy):
                    raise ValueError(
                        "Work hierarchy changed while the dialog was open."
                    )
                active = self._workspace.active
                choice = (
                    self._choose_dirty()
                    if active is not None and active.is_dirty
                    else None
                )
                # Modal callbacks can change the source/catalog; the presenter
                # rechecks both before any lookup, save or activation.
                if not self._workspace.hierarchy_is_current(hierarchy):
                    raise ValueError(
                        "Work hierarchy changed during the dirty decision."
                    )
                if creation is not None:
                    document_id, initial = creation
                    return self._selector.create(
                        request, document_id, initial, choice=choice
                    )
                return self._selector.select(request, choice=choice)
            finally:
                dialog.close()
                dialog.deleteLater()
        finally:
            self._busy = False
