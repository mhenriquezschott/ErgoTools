"""Modal Job workplace lifecycle with explicit context and resource ownership.

Presentation layer. The contracts below define owned controls/view values and injected
operations. Qt components run on the GUI thread; scientific calculations, canonical
source state and repository lifetime remain with the named application/domain ports and
host owners.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QWidget

from ergotools.application.project_workspace import ProjectWorkspace
from ergotools.application.settings import Language
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.presentation.desktop.job_workplace_dialog import JobWorkplaceDialog
from ergotools.presentation.job_workplaces import JobWorkplaces, JobWorkplaceView


@dataclass(frozen=True, slots=True)
class JobWorkplaceResult:
    """Saved view and optional shift for the caller's project-scoped preferences.

    Attributes:
        view: Accepted workplace view; integrated changes await the main project Save.
        preferred_shift: Optional accepted shift for project-scoped caller preferences.
    """

    view: JobWorkplaceView
    preferred_shift: str | None


class JobWorkplaceHost:
    """Own one modal editor lifetime without reaching into parent window state."""

    def __init__(
        self,
        workspace: ProjectWorkspace[AssessmentDraft],
        icons: Mapping[str, QIcon],
        *,
        parent: QWidget | None = None,
    ) -> None:
        """Inject dependencies without I/O or implicit assessment save decisions.

        Args:
            workspace: Existing project/session owner; this component borrows its
                capabilities.
            icons: Processed packaged icons indexed by stable asset identity, not system
                theme names.
            parent: Qt owner of the new control; None leaves top-level ownership to the
                caller.

        Returns:
            None.
        """
        self._workspace = workspace
        self._presenter = JobWorkplaces(workspace)
        self._icons = icons
        self._parent = parent
        self._busy = False

    def edit(
        self,
        job_id: str,
        *,
        language: Language = Language.ENGLISH,
        preferred_shift: str | None = None,
    ) -> JobWorkplaceResult | None:
        """Load, execute and release the editor; return None on cancellation.

        Errors before opening propagate to the owning window for localized display. The
        dialog handles acceptance failures and stays open. Integrated acceptance stages
        placements privately; the main Save publishes them. Diagnostic workspaces
        retain explicit durable writes. Neither outcome accepts assessment field text.

        Args:
            job_id: Exact saved job identity whose workplace placements are edited.
            language: UI language only; does not reinterpret saved names, numeric inputs
                or units.
            preferred_shift: Remembered project shift identifier; None selects the
                dialog's available default.

        Returns:
            Accepted view and remembered shift, or None on cancellation. Integrated
            acceptance writes no project file and leaves assessment field text alone.

        Raises:
            RuntimeError: Workplace editor is already open.
        """
        if self._busy:
            raise RuntimeError("Workplace editor is already open.")
        self._busy = True
        try:
            view = self._presenter.load(job_id)
            dialog = JobWorkplaceDialog(
                self._presenter,
                view,
                self._icons,
                parent=self._parent,
                language=language,
                preferred_shift=preferred_shift,
            )
            if self._workspace.editing is not None:
                dialog.save_button.setText(
                    "Aplicar" if language is Language.SPANISH else "Apply"
                )
                dialog.save_button.setIcon(self._icons["filter_apply"])
            try:
                if dialog.exec() != QDialog.Accepted:
                    return None
                return JobWorkplaceResult(dialog.view, dialog.preferred_shift)
            finally:
                dialog.close()
                dialog.deleteLater()
        finally:
            self._busy = False
