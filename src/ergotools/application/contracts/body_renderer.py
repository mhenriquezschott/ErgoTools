"""Keep anatomical rendering independent of VTK and desktop widget ownership.

The adapter receives display state only. It cannot calculate risk, query a project
database or interpret a worker record. Camera controls expose the reviewed original
interactions without leaking backend camera or widget types.

Application contract layer. The desktop owns backend lifecycle and event-loop timing;
this port exposes neither VTK types nor Qt widgets.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class BodyRegion(StrEnum):
    """Anatomical areas already displayed by the integrated application."""

    # Full anatomical scene used when active-region animation/focus is disabled.
    FULL_BODY = "full_body"
    # LiFFT display region: lower-back mesh.
    LOW_BACK = "low_back"
    # DUET display region: forearm/hand meshes.
    DISTAL_UPPER_EXTREMITIES = "distal_upper_extremities"
    # Shoulder Tool display region: both shoulder meshes.
    SHOULDERS = "shoulders"


@dataclass(frozen=True, slots=True)
class RgbColor:
    """Finite red, green and blue display channels in the inclusive range 0-1.

    Attributes:
        red: Normalized finite red channel in the inclusive range 0-1.
        green: Normalized finite green channel in the inclusive range 0-1.
        blue: Normalized finite blue channel in the inclusive range 0-1.
    """

    red: float
    green: float
    blue: float

    def __post_init__(self) -> None:
        """Reject invalid channel values before a rendering backend receives them.

        Args:
            None.

        Returns:
            None. Validate all three normalized display channels before publishing the
            frozen color.

        Raises:
            ValueError: A red, green or blue channel is nonfinite or outside 0-1.
        """
        channels = (self.red, self.green, self.blue)
        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in channels
        ):
            raise ValueError("RGB channels must be finite values between 0 and 1.")


@dataclass(frozen=True, slots=True)
class BodyViewState:
    """Immutable display request; absent color means no risk overlay is available.

    Attributes:
        region: Typed anatomical display region, independent of translated tool
            captions.
        region_colors: All available anatomical overlays. Empty retains the original
            single-overlay adapter contract for diagnostic clients.
        overlay_color: Optional normalized existing risk color; None means no available
            overlay, not zero risk.
    """

    region: BodyRegion
    overlay_color: RgbColor | None = None
    region_colors: tuple[tuple[BodyRegion, RgbColor], ...] = ()


class BodyRenderer(Protocol):
    """A renderer port with lifecycle owned by the desktop presentation adapter."""

    def set_state(self, state: BodyViewState) -> None:
        """Display anatomical overlays independently of the requested camera region.

        Args:
            state: Typed anatomical region and optional already calculated display
                color; no worker/database interpretation.

        Returns:
            None. Update backend display state on its owner thread without calculating
            or saving assessment data.
        """
        ...

    def reset_view(self) -> None:
        """Restore established camera framing under the active renderer view policy.

        Args:
            None.

        Returns:
            None. Restore established camera framing for the active region/full-body
            policy.
        """
        ...

    def rotate_view(self) -> None:
        """Apply the established clockwise model-view rotation step.

        Args:
            None.

        Returns:
            None. Apply the established clockwise view step; backend angles stay inside
            the adapter.
        """
        ...

    def zoom_view(self) -> None:
        """Apply the established active-view zoom step.

        Args:
            None.

        Returns:
            None. Apply the established zoom step without changing stored model/task
            units.
        """
        ...

    def close(self) -> None:
        """Release backend resources; repeated calls must be safe.

        Args:
            None.

        Returns:
            None. Release backend resources; repeated close calls must remain safe.
        """
        ...


@runtime_checkable
class AnimatedBodyRenderer(Protocol):
    """Optional renderer capability for original explicit tool-selection focus."""

    def set_animation_enabled(self, enabled: bool) -> None:
        """Apply active-region focus or full-body policy, cancelling any transition.

        Args:
            enabled: Explicit per-user body-animation policy, independent of source
                assessment history.

        Returns:
            None. Cancel an active transition and apply active-region focus or full-body
            policy.
        """
        ...

    def begin_region_selection(self) -> None:
        """Retain current camera while the desktop resolves a user tab selection.

        Args:
            None.

        Returns:
            None. Retain the present camera while the GUI resolves an explicit user tab
            selection.
        """
        ...

    def end_region_selection(self) -> None:
        """Animate only if the resolved source changed anatomical region.

        Args:
            None.

        Returns:
            None. Animate only a resolved anatomical-region change; unchanged regions do
            not restart transitions.
        """
        ...


@runtime_checkable
class SelectableBodyRenderer(Protocol):
    """Optional picking capability without exposing backend meshes or mouse events."""

    def set_region_selected(
        self, selected: Callable[[BodyRegion], None] | None
    ) -> None:
        """Register GUI-owned selection for a clicked available colored region.

        Args:
            selected: Callback receiving an anatomical region, or None to disconnect.

        Returns:
            None; never interpret a worker, save data or change tools inside a renderer.
        """
        ...
