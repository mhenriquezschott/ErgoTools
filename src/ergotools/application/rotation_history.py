"""Immutable JROT partial-grid history, including exact evidence and provenance.

Application layer. Compose immutable domain values through injected read/write ports.
This module owns no widgets, SQL connection, global clock or renderer; persistence and
modal consent belong to its caller.
"""

from dataclasses import dataclass

from ergotools.application.rotation_pool import RotationPool
from ergotools.application.session import DocumentKey
from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.rotation_scheme import RotationMode


@dataclass(frozen=True, slots=True)
class RotationEditState:
    """One immutable JROT history revision.

    Scope edits retain exact Jobs and assignment links; raw name typing and
    solver previews stay transient.

    Attributes:
        pool: Frozen eligible worker/target choices and scientific evidence for this
            revision.
        blocks: Number of displayed rotation periods.
        cells: Worker-by-period target keys; None retains incomplete cells.
        scope: Applied exact workplace identities; empty means organization scope.
        manual_edit: Whether the displayed grid has accepted manual edits.
        mode: Applied job/individual optimization mode, or None before a mode is set.
        primary_kind: Applied primary scientific tool, or None before selection.
        display_kind: Currently displayed risk tool, retained by Undo/Redo.
        pending_scope: Accepted scope controls independent of the applied pool.
        workplace_scope: Whether workplace scope controls are enabled; False means
            organization mode.
    """

    pool: RotationPool
    blocks: int
    cells: tuple[tuple[str | None, ...], ...]
    scope: tuple[WorkplaceContext, ...]
    manual_edit: bool
    mode: RotationMode | None
    primary_kind: AssessmentKind | None
    display_kind: AssessmentKind = AssessmentKind.LIFFT
    pending_scope: tuple[WorkplaceContext, ...] = ()
    workplace_scope: bool = False


@dataclass(frozen=True, slots=True)
class ReplaceRotationEdit:
    """One shared-history command replacing a complete grid/scope snapshot.

    Attributes:
        document: Project/document ownership of the command.
        before: Expected exact current history snapshot.
        after: Proposed snapshot, including frozen pool and accepted controls.
        label_key: Stable localization key for the Undo/Redo menu label.
    """

    document: DocumentKey
    before: RotationEditState
    after: RotationEditState
    label_key: str = "rotation.history.edit"

    def apply(self, state: RotationEditState) -> RotationEditState:
        """Reject foreign or stale snapshots before changing the shared history.

        The command itself performs no persistence or solver work.

        Args:
            state: Current immutable partial grid and frozen pool snapshot.

        Returns:
            The proposed complete replacement snapshot after stale/project validation.

        Raises:
            ValueError: Current state differs from before or the replacement pool
                belongs to another project.
        """
        if (
            state != self.before
            or self.after.pool.project_id != self.document.project_id
        ):
            raise ValueError("Rotation edit belongs to another project or revision.")
        return self.after
