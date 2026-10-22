"""PLOT workplace scope identities, independent of map pixels and risk rendering.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.work_hierarchy import WorkHierarchy


def hierarchy_paths(hierarchy: WorkHierarchy) -> tuple[tuple[str, ...], ...]:
    """Return sorted complete identities, including parents without stations.

    Args:
        hierarchy: Complete project hierarchy, including empty parents and independent
            shifts.

    Returns:
        Sorted unique one-to-four-part ancestry paths, including known parents with no
        descendant stations.
    """
    return tuple(
        sorted(
            {
                *((plant,) for plant in hierarchy.plants),
                *((key.plant_name, key.section_name) for key in hierarchy.sections),
                *(
                    (key.plant_name, key.section_name, key.line_name)
                    for key in hierarchy.lines
                ),
                *(
                    (key.plant_name, key.section_name, key.line_name, key.station_id)
                    for key in hierarchy.work.stations
                ),
            }
        )
    )


@dataclass(frozen=True, slots=True)
class PlotScope:
    """One plant's included hierarchy prefixes and an optional project-wide shift.

    A parent includes all descendants; None includes every shift. Names remain literal
    saved identities, never translated captions or inferred locations.

    Attributes:
        paths: Nonempty ancestry prefixes of one plant; parents cover descendants and
            normalization removes redundant paths.
        shift: Optional exact project-wide shift identity; None includes every shift.
    """

    paths: tuple[tuple[str, ...], ...]
    shift: str | None = None

    def __post_init__(self) -> None:
        """Validate scope shape and normalize duplicate/covered prefixes.

        Args:
            None. Dataclass construction supplies the fields documented on PlotScope.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            paths as immutable tuples on the new frozen instance.

        Raises:
            ValueError: PLOT paths must be explicit identity sequences. PLOT requires
                explicit workplace paths. PLOT scope must belong to one plant. PLOT
                shift must be an identity or absent.
        """
        if any(not isinstance(path, (tuple, list)) for path in self.paths):
            raise ValueError("PLOT paths must be explicit identity sequences.")
        paths = tuple(tuple(path) for path in self.paths)
        if not paths or any(
            not 1 <= len(path) <= 4
            or any(not isinstance(value, str) or not value.strip() for value in path)
            for path in paths
        ):
            raise ValueError("PLOT requires explicit workplace paths.")
        if len({path[0] for path in paths}) != 1:
            raise ValueError("PLOT scope must belong to one plant.")
        if self.shift is not None and (
            not isinstance(self.shift, str) or not self.shift.strip()
        ):
            raise ValueError("PLOT shift must be an identity or absent.")
        normalized: list[tuple[str, ...]] = []
        for path in sorted(set(paths), key=lambda path: (len(path), path)):
            if not any(path[: len(parent)] == parent for parent in normalized):
                normalized.append(path)
        object.__setattr__(self, "paths", tuple(normalized))

    @property
    def plant(self) -> str:
        """Return the single plant supplying the displayed layout image.

        Args:
            None.

        Returns:
            The sole plant identity from the normalized scope; no image is loaded.
        """
        return self.paths[0][0]

    def validate(self, hierarchy: WorkHierarchy) -> None:
        """Reject unavailable hierarchy prefixes or shifts before loading a layout.

        Args:
            hierarchy: Complete project hierarchy, including empty parents and
                independent shifts.

        Returns:
            None. Return normally only when the stated validation succeeds; invalid data
            raises instead.

        Raises:
            ValueError: PLOT scope references an unavailable workplace. PLOT scope
                references an unavailable shift.
        """
        available = set(hierarchy_paths(hierarchy))
        if any(path not in available for path in self.paths):
            raise ValueError("PLOT scope references an unavailable workplace.")
        if self.shift is not None and self.shift not in hierarchy.work.shifts:
            raise ValueError("PLOT scope references an unavailable shift.")
