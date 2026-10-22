"""Shared assessment issues and numeric validation, independent of any tool.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InputIssue:
    """Stable machine-readable validation context, independent of UI language.

    Attributes:
        code: Stable validation message key; user-facing translation belongs to
            presentation.
        field: Stable source-field key affected by this issue.
        task_id: Optional affected task identity; None denotes a draft/document-level
            issue.
    """

    code: str
    field: str
    task_id: str | None = None


class DraftError(ValueError):
    """Invalid draft structure or edit precondition, with structured context."""

    def __init__(self, issue: InputIssue) -> None:
        """Expose an issue without embedding user input in an exception message.

        Args:
            issue: Machine-readable validation code, field and optional task identity
                retained on the exception.

        Returns:
            None. Store issue on this exception and initialize its code/field diagnostic
            message.
        """
        self.issue = issue
        super().__init__(f"{issue.code}: {issue.field}")


def validate_nonnegative_input(value: float | None, field: str, task_id: str) -> float:
    """Return a finite nonnegative number or a field-specific DraftError.

    Missing values are not zero; booleans are not measurements. Fractional values remain
    supported. This validates source values, not arithmetic/model validity.

    Args:
        value: Source quantity to validate; None denotes absence rather than numeric
            zero.
        field: Stable quantity-field identifier for structured validation issues, never
            a translated caption.
        task_id: Stable task identity used for lookup or field-specific validation
            diagnostics.

    Returns:
        Finite nonnegative float; fractional counts are preserved rather than rounded or
        truncated.

    Raises:
        DraftError: Source structure, completeness, numeric validity or task identity
            violates the constraints described above; issue retains field/task context.
    """
    if value is None:
        raise DraftError(InputIssue("validation.required", field, task_id))
    if isinstance(value, bool):
        raise DraftError(InputIssue("validation.number", field, task_id))
    try:
        number = float(value)
    except (OverflowError, ValueError, TypeError) as error:
        raise DraftError(InputIssue("validation.number", field, task_id)) from error
    if not math.isfinite(number):
        raise DraftError(InputIssue("validation.nonfinite", field, task_id))
    if number < 0:
        raise DraftError(InputIssue("validation.nonnegative", field, task_id))
    return number
