"""Strict shared JSON validation primitives for versioned source drafts.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import math
from typing import cast


class DocumentFormatError(ValueError):
    """Malformed, ambiguous or unsupported serialized draft."""


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate members instead of silently overwriting values.

    Args:
        pairs: JSON object members in parser order; duplicate spelling is rejected
            rather than overwritten.

    Returns:
        Dictionary retaining original member order and values when no key repeats.

    Raises:
        DocumentFormatError: A JSON object repeats a member name.
    """
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DocumentFormatError("Duplicate JSON member.")
        result[key] = value
    return result


def document_fields(value: object, expected: set[str]) -> dict[str, object]:
    """Require the exact document field set.

    Args:
        value: Decoded primitive/object to validate without defaulting or unit
            conversion.
        expected: Exact allowed field-name set; both extra and missing members are
            errors.

    Returns:
        Original decoded dictionary with exactly the expected fields; no copy or
        normalization.

    Raises:
        DocumentFormatError: The value is not an object with exactly the expected
            fields.
    """
    if not isinstance(value, dict) or set(value) != expected:
        raise DocumentFormatError("Unexpected or missing document fields.")
    return cast(dict[str, object], value)


def document_text(value: object) -> str:
    """Require nonblank text while preserving the original value.

    Args:
        value: Decoded primitive/object to validate without defaulting or unit
            conversion.

    Returns:
        Original nonblank string, retaining its exact whitespace and spelling.

    Raises:
        DocumentFormatError: The value is not a nonblank string.
    """
    if not isinstance(value, str) or not value.strip():
        raise DocumentFormatError("Expected a nonblank string.")
    return value


def document_number(value: object) -> float | None:
    """Retain finite numeric precision and explicit null; reject booleans.

    Args:
        value: Decoded primitive/object to validate without defaulting or unit
            conversion.

    Returns:
        Original finite int/float or None, preserving numeric precision and the
        distinction between absence and zero.

    Raises:
        DocumentFormatError: A present value is boolean, nonnumeric or nonfinite.
        OverflowError: An integer is too large for the finiteness check; enclosing
            codecs normalize this to a format error.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DocumentFormatError("Expected a number or null.")
    if not math.isfinite(value):
        raise DocumentFormatError("Numbers must be finite.")
    return value
