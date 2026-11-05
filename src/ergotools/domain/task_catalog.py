"""Reusable project task names, independent of measured assessment occurrences.

Domain layer. Definitions carry identity and descriptive text only. Numeric tool
inputs and row identities remain with worker/Job sources. Equal labels need not share
identity; the application may deliberately reuse a matching definition during Paste.
This module performs no storage, calculation or UI operations.
"""

from dataclasses import dataclass


def validate_task_label(name: str | None, definition_id: str | None) -> None:
    """Require literal optional labels and a usable reference with a fallback name.

    Args:
        name: Optional nonblank activity name; no numeric meaning or unit conversion.
        definition_id: Optional exact project definition identity, separate from row ID.

    Returns:
        None when descriptive metadata is structurally valid.

    Raises:
        ValueError: A supplied name/reference is not nonblank text, or a reference
            has no fallback name for portable copies and standalone interchange.
    """
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise ValueError("Task name must be nonblank text or absent.")
    if definition_id is not None and (
        not isinstance(definition_id, str) or not definition_id.strip() or name is None
    ):
        raise ValueError("Task definition requires an identity and fallback name.")


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    """Project-local reusable activity label without shared scientific inputs.

    Attributes:
        definition_id: Stable nonblank identity; equal names may have distinct IDs.
        name: User-entered activity name, not an ergonomic tool or Job identifier.
        description: Optional literal explanatory text.
    """

    definition_id: str
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate definition metadata without normalizing user spelling.

        Args:
            None. Dataclass construction supplies TaskDefinition fields.

        Returns:
            None after validating immutable descriptive fields.

        Raises:
            ValueError: Definition identity/name is invalid or description is not text.
        """
        if not isinstance(self.definition_id, str) or not self.definition_id.strip():
            raise ValueError("Task definition identity must be nonblank text.")
        validate_task_label(self.name, self.definition_id)
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Task description must be text or absent.")
