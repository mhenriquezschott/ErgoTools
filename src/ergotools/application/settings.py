"""Immutable user preferences, shared Undo budgets and bounded recent files.

Application layer. Define immutable capability/operation contracts independently of Qt
and storage implementations. Callers own modal consent and borrowed project lifetime;
concrete adapters own I/O and transaction enforcement.
"""

from dataclasses import dataclass, field, replace
from typing import Protocol

from ergotools.application.gauge_preferences import GaugeMarkerSettings
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language as Language
from ergotools.domain.model_units import MeasurementSystem

# Maximum remembered project locations; retain the ten most recently opened paths.
RECENT_LIMIT = 10


# Initial shared project Undo/Redo command budget for every application session.
DEFAULT_UNDO_LIMIT = 25
# Smallest owner-selectable project history budget, in completed operations.
MIN_UNDO_LIMIT = 1
# Largest owner-selectable project history budget, in completed operations.
MAX_UNDO_LIMIT = 50


def validate_undo_limit(value: int) -> None:
    """Reject noninteger or out-of-range application history budgets.

    Args:
        value: Maximum retained shared Undo/Redo operations, inclusive range 1-50.

    Returns:
        None after validating; booleans are not integer preferences.

    Raises:
        ValueError: The preference is not an integer from 1 through 50.
    """
    if type(value) is not int or not MIN_UNDO_LIMIT <= value <= MAX_UNDO_LIMIT:
        raise ValueError("Undo limit must be an integer from 1 through 50.")


@dataclass(frozen=True, slots=True)
class UserSettings:
    """User defaults; existing assessment records retain their own unit metadata.

    Recent locations are opaque caller-normalized strings, ordered newest first. They
    are not opened, resolved, migrated or checked for existence here.

    Attributes:
        language: Per-user translation catalog identity; separate from a saved project's
            original language.
        default_units: Default metric/imperial input/display choice; existing sources
            retain original units.
        recent_documents: Unique caller-normalized locations newest first, bounded by
            RECENT_LIMIT; not opened/resolved here.
        decimal_convention: Explicit decimal separator preference, independent of
            interface language.
        assessment_contexts: Last-used (project, worker, tool, plant, section, line,
            station, shift) identities; independent of project data and display units.
        undo_limit: Personal shared project history budget; independent of saved data.
        gauge_markers: Personal main-risk gauge tick/label visibility and spacing;
            independent of projects and calculator outputs.
        animated_risk_gauge: Animate risk displays; False immediately shows targets.
        animated_cumulative_damage: Animate damage bars; independent of calculated data.
        animated_body_region_focus: Explicit avatar focus/animation preference; False
            uses the established full-body policy.
    """

    language: Language = Language.ENGLISH
    default_units: MeasurementSystem = MeasurementSystem.IMPERIAL
    recent_documents: tuple[str, ...] = ()
    decimal_convention: DecimalConvention = DecimalConvention.POINT
    animated_body_region_focus: bool = True
    assessment_contexts: tuple[tuple[str, ...], ...] = ()
    gauge_markers: GaugeMarkerSettings = field(default_factory=GaugeMarkerSettings)

    undo_limit: int = DEFAULT_UNDO_LIMIT
    animated_risk_gauge: bool = True
    animated_cumulative_damage: bool = True

    def __post_init__(self) -> None:
        """Reject invalid preferences and ambiguous or unbounded recent history.

        Args:
            None.

        Returns:
            None. Validate typed preferences and freeze the unique newest-first
            recent-location tuple, bounded by RECENT_LIMIT.

        Raises:
            ValueError: Language, units, decimal/animation preferences or bounded unique
                recent locations, gauge marker preferences or Undo limit are invalid.
        """
        if not isinstance(self.language, Language) or not isinstance(
            self.default_units, MeasurementSystem
        ):
            raise ValueError("Unsupported language or unit preference.")
        if not isinstance(self.decimal_convention, DecimalConvention):
            raise ValueError("Unsupported decimal convention.")
        if type(self.animated_body_region_focus) is not bool:
            raise ValueError("Camera animation preference must be boolean.")
        if any(
            type(value) is not bool
            for value in (self.animated_risk_gauge, self.animated_cumulative_damage)
        ):
            raise ValueError("Result animation preferences must be boolean.")
        if not isinstance(self.gauge_markers, GaugeMarkerSettings):
            raise ValueError("Unsupported gauge marker preferences.")
        validate_undo_limit(self.undo_limit)
        contexts = tuple(tuple(item) for item in self.assessment_contexts)
        if any(
            len(item) != 8 or any(not isinstance(v, str) or not v.strip() for v in item)
            for item in contexts
        ) or len({item[:3] for item in contexts}) != len(contexts):
            raise ValueError("Invalid remembered assessment contexts.")
        object.__setattr__(self, "assessment_contexts", contexts)
        object.__setattr__(self, "recent_documents", tuple(self.recent_documents))
        locations = self.recent_documents
        if (
            len(locations) > RECENT_LIMIT
            or any(not isinstance(item, str) or not item.strip() for item in locations)
            or len(set(locations)) != len(locations)
        ):
            raise ValueError("Invalid recent-document history.")

    def remember(self, location: str) -> "UserSettings":
        """Move a successfully opened location to the front; never access its file.

        Args:
            location: Caller-normalized project location; treat it as opaque recency
                data, not a path to resolve/open here.

        Returns:
            New settings moving the exact location to the front, removing its prior
            occurrence and truncating to ten entries; no file access.

        Raises:
            ValueError: The location cannot form a valid nonblank-text recent-history
                entry.
        """
        remaining = tuple(item for item in self.recent_documents if item != location)
        return replace(self, recent_documents=(location, *remaining)[:RECENT_LIMIT])

    def forget(self, location: str) -> "UserSettings":
        """Remove a missing/moved entry explicitly without touching any document.

        Args:
            location: Caller-normalized project location; treat it as opaque recency
                data, not a path to resolve/open here.

        Returns:
            New settings excluding exact equal location strings; preserve all other
            preferences and order, without deleting a file.
        """
        return replace(
            self,
            recent_documents=tuple(
                item for item in self.recent_documents if item != location
            ),
        )

    def clear_recent(self) -> "UserSettings":
        """Clear only recent history, retaining language and default units.

        Args:
            None.

        Returns:
            New settings with empty recent history; language, unit/decimal and
            body-animation choices are retained.
        """
        return replace(self, recent_documents=())


class SettingsStore(Protocol):
    """User-scoped persistence separate from project/document storage."""

    def load(self) -> UserSettings:
        """Read settings, returning defaults only when no file exists.

        Args:
            None.

        Returns:
            Validated saved preferences, or defaults only when the preference file does
            not exist; corrupt/unreadable settings must fail explicitly.
        """
        ...

    def save(self, settings: UserSettings) -> None:
        """Persist validated settings without changing any project data.

        Args:
            settings: Validated immutable preferences to persist in the per-user store.

        Returns:
            None after validated per-user preference persistence; never change project
            metadata or assessment source units.
        """
        ...
