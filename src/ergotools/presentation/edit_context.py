"""Presenter-owned edit contexts reject obsolete unit and decimal interpretations.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

from dataclasses import dataclass
from typing import Literal

from ergotools.application.assessments.unit_view import (
    AssessmentUnitView,
    prepare_unit_view,
)
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.model_units import MeasurementSystem
from ergotools.presentation.assessment_input import edit_display_text
from ergotools.presentation.numeric_input import DecimalConvention


@dataclass(frozen=True, slots=True)
class EditContext:
    """Exact source projection and decimal policy retained by editor callbacks.

    Never substitute whichever context happens to be current when an obsolete callback
    arrives.

    Attributes:
        view: Exact source/session/revision-bound display-unit projection.
        convention: Explicit decimal interpretation used when the text editor was
            initialized.
    """

    view: AssessmentUnitView
    convention: DecimalConvention


class AssessmentEditor:
    """Own one active input context on the presentation owner thread.

    Rebind after source/view preference changes; clear on close or workspace
    switch. Caller supplies the actual active session on every submission. This
    owns interpretation, not widgets or pending text: rejected text must remain
    available to the caller for correction, copying or explicit dismissal.
    """

    def __init__(self) -> None:
        """Start without a retained projection or document reference.

        Args:
            None.

        Returns:
            None; start without a source projection or document reference.
        """
        self._context: EditContext | None = None

    def clear(self) -> None:
        """Release this owner's context and permanently reject its old callbacks.

        Args:
            None.

        Returns:
            None; release this interpretation and invalidate its old callbacks.
        """
        self._context = None

    def bind(
        self,
        active: DocumentSession[AssessmentDraft],
        system: MeasurementSystem,
        convention: DecimalConvention,
    ) -> EditContext:
        """Create a fresh context even when preferences/source compare equal.

        Invalidate the old interpretation before preparation, so failed switches cannot
        leave old editors usable. Binding never modifies source or history. Invalid
        conventions/units, unsupported models or projection errors propagate.

        Args:
            active: Current owner-thread source session to project without editing.
            system: Explicit metric/imperial display system, independent of recorded
                source units.
            convention: Explicit point/comma input convention, independent of language.

        Returns:
            Fresh exact editor context; equal units/source values never revive an old
            context.

        Raises:
            ValueError: Convention, system, model or projected numeric values are
                invalid.
        """
        self.clear()
        if not isinstance(convention, DecimalConvention):
            raise ValueError("Unsupported decimal convention.")
        context = EditContext(prepare_unit_view(active, system), convention)
        self._context = context
        return context

    def current(
        self, active: DocumentSession[AssessmentDraft] | None
    ) -> EditContext | None:
        """Expose a context only while its exact source session/revision is active.

        Args:
            active: Actual current session, or None after close/switch.

        Returns:
            Retained context only while exact session/revision still matches; otherwise
            None.
        """
        context = self._context
        return (
            context if context is not None and context.view.is_current(active) else None
        )

    def submit(
        self,
        active: DocumentSession[AssessmentDraft] | None,
        context: EditContext,
        task_id: str,
        field: Literal["lever_arm", "load"],
        text: str,
    ) -> bool:
        """Apply text only under the exact still-current editor interpretation.

        Context identity precedes parsing: toggling units/conventions away and back does
        not revive old editors, nor can equal contexts from another owner pass. Invalid
        text retains context for correction. A successful source edit clears it;
        unchanged input preserves it. Caller must bind before rendering edited source
        again. No automatic retry, text loss, I/O or evaluation occurs.

        Args:
            active: Actual current source session, or None.
            context: Exact context retained when this editor was initialized.
            task_id: Stable row identity whose one dimensional field changes.
            field: lever_arm or load dimensional field identity.
            text: Complete deliberately edited text; blank clears, invalid text must
                remain available in the host.

        Returns:
            True after a source command is recorded and context cleared; False for a
            no-op retaining context.

        Raises:
            DraftError: Context is stale/foreign, text is invalid or source
                conversion/field validation fails.
            RuntimeError: Session operation violates owner-thread/reentrancy guards.
        """
        if active is None or context is not self.current(active):
            raise DraftError(InputIssue("validation.stale_editor", "source", task_id))
        changed = edit_display_text(
            active, context.view, task_id, field, text, context.convention
        )
        if changed:
            self.clear()
        return changed
