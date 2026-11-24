"""Validated personal tablet display preferences, separate from all native projects.

Only presentation/animation choices persist here. Loading malformed preferences never
rewrites a file or changes assessment data; explicit Apply publishes atomically.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from project_session import atomic_write

from ergotools.domain.assessments.document import AssessmentKind

# Stable source order for three per-tool presentation flags in preference version one.
KINDS = tuple(AssessmentKind)


@dataclass(frozen=True, slots=True)
class TabletPreferences:
    """Immutable display-only configuration; scientific inputs always stay visible.

    Attributes:
        tick_interval: Gauge interval in percent; zero hides interval ticks.
        range_labels: Show 25/37.5/50 range boundaries.
        scale_labels: Show the 0/100 gauge limits.
        gauge_animation: Animate the needle when a new result is accepted.
        damage_animation: Animate the cumulative-damage bar independently.
        body_animation: Animate the selected body region when results change.
        animation_ms: Shared duration from 100 to 1000 milliseconds.
        body_visible: Offer the expandable body illustration in task editors.
        task_names: Per-tool optional name field/list visibility; hidden names are kept.
        task_details: Per-tool derived moment/damage/share visibility.
    """

    tick_interval: int = 10
    range_labels: bool = True
    scale_labels: bool = True
    gauge_animation: bool = True
    damage_animation: bool = True
    body_animation: bool = True
    animation_ms: int = 650
    body_visible: bool = True
    task_names: tuple[bool, ...] = (True, True, True)
    task_details: tuple[bool, ...] = (True, True, True)

    def __post_init__(self) -> None:
        """Reject unsupported or coerced values before applying presentation settings.

        Args:
            None; dataclass arguments are described above.

        Returns:
            None; no file or native project is touched.

        Raises:
            ValueError: Interval, duration, booleans or per-tool flags are invalid.
        """
        if type(self.tick_interval) is not int or self.tick_interval not in (
            0,
            5,
            10,
            20,
        ):
            raise ValueError("Choose a supported gauge tick interval.")
        if type(self.animation_ms) is not int or not 100 <= self.animation_ms <= 1000:
            raise ValueError("Animation duration must be 100-1000 ms.")
        for key, value in asdict(self).items():
            if key in ("tick_interval", "animation_ms"):
                continue
            if key in ("task_names", "task_details"):
                if (
                    not isinstance(value, tuple)
                    or len(value) != 3
                    or any(type(flag) is not bool for flag in value)
                ):
                    raise ValueError("Each tool needs an explicit presentation flag.")
            elif type(value) is not bool:
                raise ValueError("Presentation switches must be true or false.")

    def names_for(self, kind: AssessmentKind) -> bool:
        """Read name visibility for one exact tool without changing its source.

        Args:
            kind: Selected assessment model.

        Returns:
            Whether optional task names are presented.
        """
        return self.task_names[KINDS.index(kind)]

    def details_for(self, kind: AssessmentKind) -> bool:
        """Read derived-detail visibility independently for one tool.

        Args:
            kind: Selected assessment model.

        Returns:
            Whether moment/damage/share detail text is shown.
        """
        return self.task_details[KINDS.index(kind)]


class PreferenceStore:
    """Own one personal JSON file beside, never inside, tablet project storage.

    Attributes:
        path: Dedicated view_settings.json; not a native project location.
        warning: Nonfatal load explanation; malformed files are retained until Apply.
    """

    def __init__(self, folder: Path) -> None:
        """Bind existing private storage without changing it.

        Args:
            folder: App-private data folder.

        Returns:
            None; load/save are explicit operations.
        """
        self.path = folder / "view_settings.json"
        self.warning = ""

    def load(self) -> TabletPreferences:
        """Load valid preferences or explain safe defaults without overwriting evidence.

        Args:
            None.

        Returns:
            Immutable settings; projects and damaged preference files are unchanged.
        """
        self.warning = ""
        if not self.path.exists():
            return TabletPreferences()
        try:
            values = json.loads(self.path.read_text())
            if not isinstance(values, dict) or values.pop("version", None) != 1:
                raise ValueError("Unsupported preference version.")
            defaults = asdict(TabletPreferences())
            for key in defaults:
                if key not in values:
                    continue
                value = values[key]
                defaults[key] = (
                    tuple(value[k.value] for k in KINDS)
                    if key in ("task_names", "task_details")
                    else value
                )
            return TabletPreferences(**defaults)
        except (OSError, ValueError, TypeError, KeyError):
            self.warning = (
                "Tablet display settings could not be loaded. Defaults are in "
                "use; Apply Settings to replace them."
            )
            return TabletPreferences()

    def save(self, preferences: TabletPreferences) -> None:
        """Publish explicit Apply atomically; no project/history operation is performed.

        Args:
            preferences: Validated immutable configuration.

        Returns:
            None after successful publication; prior settings survive write failure.
        """
        values = asdict(preferences)
        for key in ("task_names", "task_details"):
            values[key] = {
                kind.value: flag for kind, flag in zip(KINDS, values[key], strict=True)
            }
        values["version"] = 1
        atomic_write(self.path, json.dumps(values, indent=2).encode())
        self.warning = ""
