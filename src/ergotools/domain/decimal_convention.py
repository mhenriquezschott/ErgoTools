"""Explicit user decimal mark, independent of language, locale and source units.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from enum import StrEnum


class DecimalConvention(StrEnum):
    """Decimal separator only; grouping is unsupported and never guessed."""

    # User-selected decimal point; independent of interface language.
    POINT = "."
    # User-selected decimal comma; independent of interface language.
    COMMA = ","
