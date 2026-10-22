"""Typed adapters routing model-specific edits into a mixed-assessment session.

Application layer. Coordinate immutable domain sources and the explicit ports shown
below; GUI controls, SQL and filesystem policy belong to adapters. These operations run
synchronously on their owning session thread; no background or multi-user coordination
is introduced.
"""

from dataclasses import dataclass

from ergotools.application.session import DocumentKey, EditCommand
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst_draft import TstDraft


@dataclass(frozen=True, slots=True)
class LifftProjectEdit:
    """Apply a LiFFT command only to a LiFFT source in the owning project session.

    Attributes:
        command: Typed model-specific pure command; the adapter rejects a different
            model before invoking it.
    """

    command: EditCommand[LifftDraft]

    @property
    def document(self) -> DocumentKey:
        """Preserve the wrapped command's document scope.

        Args:
            None.

        Returns:
            The wrapped command's exact project/document scope.
        """
        return self.command.document

    @property
    def label_key(self) -> str:
        """Preserve the wrapped command's localized history label.

        Args:
            None.

        Returns:
            The wrapped command's stable history localization key, without translating
            it.
        """
        return self.command.label_key

    def apply(self, state: AssessmentDraft) -> AssessmentDraft:
        """Reject another model before applying any task edits.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            ValueError: The active source has a different assessment model.
            DraftError: The wrapped command rejects its task/source edit preconditions.
        """
        if not isinstance(state, LifftDraft):
            raise ValueError("LiFFT edit requires a LiFFT assessment.")
        return self.command.apply(state)


@dataclass(frozen=True, slots=True)
class DuetProjectEdit:
    """Apply a DUET command only to a DUET source in the owning project session.

    Attributes:
        command: Typed model-specific pure command; the adapter rejects a different
            model before invoking it.
    """

    command: EditCommand[DuetDraft]

    @property
    def document(self) -> DocumentKey:
        """Preserve the wrapped command's document scope.

        Args:
            None.

        Returns:
            The wrapped command's exact project/document scope.
        """
        return self.command.document

    @property
    def label_key(self) -> str:
        """Preserve the wrapped command's localized history label.

        Args:
            None.

        Returns:
            The wrapped command's stable history localization key, without translating
            it.
        """
        return self.command.label_key

    def apply(self, state: AssessmentDraft) -> AssessmentDraft:
        """Reject another model before applying any task edits.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            ValueError: The active source has a different assessment model.
            DraftError: The wrapped command rejects its task/source edit preconditions.
        """
        if not isinstance(state, DuetDraft):
            raise ValueError("DUET edit requires a DUET assessment.")
        return self.command.apply(state)


@dataclass(frozen=True, slots=True)
class TstProjectEdit:
    """Apply a TST command only to a TST source in the owning project session.

    Attributes:
        command: Typed model-specific pure command; the adapter rejects a different
            model before invoking it.
    """

    command: EditCommand[TstDraft]

    @property
    def document(self) -> DocumentKey:
        """Preserve the wrapped command's document scope.

        Args:
            None.

        Returns:
            The wrapped command's exact project/document scope.
        """
        return self.command.document

    @property
    def label_key(self) -> str:
        """Preserve the wrapped command's localized history label.

        Args:
            None.

        Returns:
            The wrapped command's stable history localization key, without translating
            it.
        """
        return self.command.label_key

    def apply(self, state: AssessmentDraft) -> AssessmentDraft:
        """Reject another model before applying any task edits.

        Args:
            state: Current immutable source snapshot; successful edits return a
                replacement rather than mutating it.

        Returns:
            Immutable edited draft for the same assessment; source order/identity/unit
            rules are enforced by the command described above.

        Raises:
            ValueError: The active source has a different assessment model.
            DraftError: The wrapped command rejects its task/source edit preconditions.
        """
        if not isinstance(state, TstDraft):
            raise ValueError("TST edit requires a TST assessment.")
        return self.command.apply(state)
