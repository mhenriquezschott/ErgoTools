"""Explicit decimal conventions for editable numbers, independent of OS locale.

Presentation layer. Interpret explicit user selections and project immutable values for
controls or interchange, independently of widget construction. Persistence and source
history use injected application services. Do not infer identity from captions, units
from interface language, or missing scientific quantities from zero. Storage errors
propagate to the host for localized reporting; user data remains literal.
"""

import math
import re

from ergotools.domain.assessments.validation import DraftError, InputIssue
from ergotools.domain.decimal_convention import DecimalConvention as DecimalConvention

# Maximum trimmed editable numeric token length, bounding parsing and editor text.
_MAX_INPUT_LENGTH = 256
# ASCII number grammar with optional sign, point decimal and scientific exponent;
# grouping/units are rejected.
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _require_convention(convention: DecimalConvention) -> None:
    """Validate the numeric parsing/formatting policy without I/O.

    Args:
        convention: Explicit typed point/comma convention; never infer from OS locale.

    Returns:
        None when the convention is a supported enum value.

    Raises:
        ValueError: Convention is untyped or unsupported.
    """
    if not isinstance(convention, DecimalConvention):
        raise ValueError("Unsupported decimal convention.")


def parse_input_number(
    text: str, convention: DecimalConvention, field: str, task_id: str
) -> float | None:
    """Parse a complete entered number or raise a field-specific DraftError.

    Blank text means absent. Accept ASCII digits, sign, the selected decimal mark and
    optional scientific exponent. Trim surrounding whitespace; reject internal
    whitespace, grouping, other decimal marks, units, NaN and infinity. The maximum
    trimmed length is 256 characters. Whole-number tokens retain integer precision;
    decimal/exponent tokens use binary floats without display rounding. Reject overflow
    and nonzero values that underflow to zero. No locale is inferred.

    Args:
        text: Complete edited text with optional surrounding whitespace.
        convention: Explicit decimal mark; grouping separators are unsupported.
        field: Stable input field identity used in structured error issues.
        task_id: Stable row identity attached to validation issues.

    Returns:
        None for blank input, an exact integer for whole-number tokens or finite float
        for decimal/exponent tokens.

    Raises:
        ValueError: Decimal convention is invalid.
        DraftError: Token is untyped/malformed/too long or float overflow/nonzero
            underflow would lose the value.
    """
    _require_convention(convention)
    if not isinstance(text, str):
        raise DraftError(InputIssue("validation.number", field, task_id))
    token = text.strip()
    if not token:
        return None
    if len(token) > _MAX_INPUT_LENGTH:
        raise DraftError(InputIssue("validation.number", field, task_id))
    if convention is DecimalConvention.COMMA:
        if "." in token:
            raise DraftError(InputIssue("validation.number", field, task_id))
        token = token.replace(",", ".")
    if _NUMBER.fullmatch(token) is None:
        raise DraftError(InputIssue("validation.number", field, task_id))
    if "." not in token and "e" not in token.lower():
        return int(token)
    number = float(token)
    mantissa = token.lower().split("e")[0]
    if not math.isfinite(number) or (
        number == 0 and any(digit in "123456789" for digit in mantissa)
    ):
        raise DraftError(InputIssue("validation.overflow", field, task_id))
    return number


def format_input_number(value: float | None, convention: DecimalConvention) -> str:
    """Produce ungrouped editable text that round-trips supported source values.

    This is full-precision editor text, not rounded result/report formatting. Preserve
    integer precision and float repr; None becomes blank. Invalid types and nonfinite
    values raise ValueError before any view can display them.

    Args:
        value: Finite supported integer/float source value, or None for absent input; no
            display rounding.
        convention: Explicit point/comma decimal mark independent of UI language.

    Returns:
        Ungrouped round-trip editor text; empty string for None.

    Raises:
        ValueError: Convention/type/value/range or resulting text length is unsupported.
    """
    _require_convention(convention)
    if value is None:
        return ""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Editor values must be finite numbers or absent.")
    try:
        finite = math.isfinite(value)
    except OverflowError as error:
        raise ValueError("Editor value exceeds the numeric range.") from error
    if not finite:
        raise ValueError("Editor values must be finite.")
    text = repr(value)
    if len(text) > _MAX_INPUT_LENGTH:
        raise ValueError("Editor value exceeds the supported text length.")
    return text.replace(".", convention.value)
