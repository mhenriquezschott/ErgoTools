"""Strict primitives for reviewed legacy rows; preserve absence and zero.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

import math
from collections.abc import Mapping

from ergotools.domain.assessments.document import AssessmentKind


def legacy_text(value: object) -> str:
    """Require original text without stripping or inventing identifiers.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Original string unchanged, including its whitespace and empty spelling.

    Raises:
        ValueError: The original value is not a string.
    """
    if not isinstance(value, str):
        raise ValueError("Expected legacy text.")
    return value


def optional_text(value: object) -> str | None:
    """Preserve missing text separately from a recorded empty string.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Original unchanged string, or None when the SQL value is absent.

    Raises:
        ValueError: A present original value is not text.
    """
    return None if value is None else legacy_text(value)


def legacy_integer(value: object) -> int:
    """Reject floating IDs, boolean coercion and unknown SQLite storage types.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Original int unchanged; bool and fractional/numeric text values fail.

    Raises:
        ValueError: The value is not exactly an int; bool is rejected.
    """
    if type(value) is not int:
        raise ValueError("Expected a legacy integer.")
    return value


def optional_integer(value: object) -> int | None:
    """Retain missing links rather than substitute a default identity.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Original integer identity, or None for an absent link.

    Raises:
        ValueError: A present original identity is not exactly an int.
    """
    return None if value is None else legacy_integer(value)


def legacy_number(value: object) -> float | None:
    """Read optional finite quantities without conversion, rounding or zero filling.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Finite float or None; preserve numeric zero and perform no unit conversion or
        rounding.

    Raises:
        ValueError: A present original quantity is boolean, nonnumeric or nonfinite.
        OverflowError: An original integer is too large to represent as a float.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a finite legacy quantity.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Expected a finite legacy quantity.")
    return result


def legacy_flag(value: object) -> bool:
    """Accept only original integer 0/1 flags; do not infer from truthiness.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        False for integer 0, True for integer 1; other storage values fail.

    Raises:
        ValueError: The value is not exactly integer zero or one.
    """
    number = legacy_integer(value)
    if number not in (0, 1):
        raise ValueError("Expected a legacy 0/1 flag.")
    return bool(number)


def legacy_kind(value: object) -> AssessmentKind:
    """Map exact original ErgoTool IDs, independently of localized captions.

    Args:
        value: Original SQLite storage value; primitive-specific validation below does
            not infer missing data.

    Returns:
        Stable model identity for exact original LiFFT, DUET or ST spelling.

    Raises:
        ValueError: The tool ID is not exact original supported text.
    """
    kinds = {
        "LiFFT": AssessmentKind.LIFFT,
        "DUET": AssessmentKind.DUET,
        "ST": AssessmentKind.TST,
    }
    name = legacy_text(value)
    if name not in kinds:
        raise ValueError("Unknown legacy ergonomic tool.")
    return kinds[name]


def legacy_keys(row: Mapping[str, object], *names: str) -> tuple[str, ...]:
    """Read exact ordered ancestry; fail on missing or non-text identity fields.

    Args:
        row: Read-only original row mapping with exact version-eight schema column
            names.
        names: Ordered required column names; missing or nontext identities are errors.

    Returns:
        Required original string values in the supplied column order, without
        normalization.

    Raises:
        KeyError: A required identity column is absent.
        ValueError: A required original identity value is not text.
    """
    return tuple(legacy_text(row[name]) for name in names)
