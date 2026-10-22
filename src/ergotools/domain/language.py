"""Stable language identity shared by project metadata and user preferences.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from enum import StrEnum


class Language(StrEnum):
    """Supported language identities independent of units and display captions."""

    # English translation catalog identity (BCP 47 en).
    ENGLISH = "en"
    # Spanish translation catalog identity (BCP 47 es).
    SPANISH = "es"
