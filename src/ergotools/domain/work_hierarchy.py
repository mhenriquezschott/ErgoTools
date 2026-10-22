"""Complete selection hierarchy, retaining parents without descendant stations.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

from dataclasses import dataclass

from ergotools.domain.assessments.context import _require_identity
from ergotools.domain.organization_record import OrganizationKind, OrganizationRecord
from ergotools.domain.work_catalog import StationKey, WorkCatalog


@dataclass(frozen=True, slots=True)
class SectionKey:
    """Section names are unique within their plant, not across the project.

    Attributes:
        plant_name: Literal plant identity; case and nonblank whitespace are preserved.
        section_name: Literal section identity scoped by its owning plant.
    """

    plant_name: str
    section_name: str

    def __post_init__(self) -> None:
        """Require explicit ancestry without normalizing stored identity.

        Args:
            None. Dataclass construction supplies the fields documented on SectionKey.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: The typed record or one of its referenced identities violates
                the invariants described above.
        """
        _require_identity(self.plant_name, self.section_name)


@dataclass(frozen=True, slots=True)
class LineKey:
    """Line identity includes both plant and section ancestry.

    Attributes:
        plant_name: Literal plant identity; case and nonblank whitespace are preserved.
        section_name: Literal section identity scoped by its owning plant.
        line_name: Literal line identity scoped by its plant and section.
    """

    plant_name: str
    section_name: str
    line_name: str

    def __post_init__(self) -> None:
        """Reject incomplete ancestry before hierarchy validation.

        Args:
            None. Dataclass construction supplies the fields documented on LineKey.

        Returns:
            None. Construction validates this record before publishing it.

        Raises:
            ValueError: The typed record or one of its referenced identities violates
                the invariants described above.
        """
        _require_identity(self.plant_name, self.section_name, self.line_name)

    @property
    def section(self) -> SectionKey:
        """Return the exact parent section; no lookup or inferred parent creation.

        Args:
            None.

        Returns:
            Typed parent section constructed directly from this line's saved ancestry.
        """
        return SectionKey(self.plant_name, self.section_name)


@dataclass(frozen=True, slots=True)
class WorkHierarchy:
    """Validated parents for one project-owned worker/station/shift snapshot.

    Keep every plant, section and line, including empty parents. Collections preserve
    adapter-supplied order. No PLOT geometry or editing/delete policy is implied by
    these selection keys; shifts remain project-wide.

    Attributes:
        work: Complete worker/station/shift selection snapshot for this project.
        plants: Ordered plant identities, including plants without descendant sections.
        sections: Ordered complete plant/section keys, including empty sections.
        lines: Ordered complete plant/section/line keys, including empty lines.
        organization: Optional entity detail records whose exact keys exist in this
            hierarchy.
    """

    work: WorkCatalog
    plants: tuple[str, ...] = ()
    sections: tuple[SectionKey, ...] = ()
    lines: tuple[LineKey, ...] = ()
    organization: tuple[OrganizationRecord, ...] = ()

    def __post_init__(self) -> None:
        """Reject duplicates and orphans before publishing a complete snapshot.

        Args:
            None. Dataclass construction supplies the fields documented on
            WorkHierarchy.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            plants, sections, lines, organization as immutable tuples on the new frozen
            instance.

        Raises:
            ValueError: Hierarchy requires a typed work catalog. Hierarchy sections must
                be typed keys. Hierarchy lines must be typed keys. Hierarchy identities
                must be unique within their scope. Section references a missing plant.
                Line references a missing section. Station references a missing line.
                Organization details reference a missing location. Duplicate
                organization details.
        """
        if not isinstance(self.work, WorkCatalog):
            raise ValueError("Hierarchy requires a typed work catalog.")
        object.__setattr__(self, "plants", tuple(self.plants))
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "lines", tuple(self.lines))
        _require_identity(*self.plants)
        if any(not isinstance(section, SectionKey) for section in self.sections):
            raise ValueError("Hierarchy sections must be typed keys.")
        if any(not isinstance(line, LineKey) for line in self.lines):
            raise ValueError("Hierarchy lines must be typed keys.")
        if any(
            len(set(values)) != len(values)
            for values in (self.plants, self.sections, self.lines)
        ):
            raise ValueError("Hierarchy identities must be unique within their scope.")
        plants, sections, lines = set(self.plants), set(self.sections), set(self.lines)
        if any(section.plant_name not in plants for section in sections):
            raise ValueError("Section references a missing plant.")
        if any(line.section not in sections for line in lines):
            raise ValueError("Line references a missing section.")
        if any(
            LineKey(station.plant_name, station.section_name, station.line_name)
            not in lines
            for station in self.work.stations
        ):
            raise ValueError("Station references a missing line.")

        object.__setattr__(self, "organization", tuple(self.organization))
        memberships: dict[OrganizationKind, set[tuple[str, ...]]] = {
            OrganizationKind.PLANT: {(p,) for p in self.plants},
            OrganizationKind.SECTION: {
                (s.plant_name, s.section_name) for s in self.sections
            },
            OrganizationKind.LINE: {
                (line.plant_name, line.section_name, line.line_name)
                for line in self.lines
            },
            OrganizationKind.STATION: {
                (s.plant_name, s.section_name, s.line_name, s.station_id)
                for s in self.work.stations
            },
            OrganizationKind.SHIFT: {(s,) for s in self.work.shifts},
        }
        seen: set[tuple[OrganizationKind, tuple[str, ...]]] = set()
        for record in self.organization:
            if (
                not isinstance(record, OrganizationRecord)
                or record.keys not in memberships[record.kind]
            ):
                raise ValueError("Organization details reference a missing location.")
            identity = (record.kind, record.keys)
            if identity in seen:
                raise ValueError("Duplicate organization details.")
            seen.add(identity)

    def sections_in(self, plant_name: str) -> tuple[SectionKey, ...]:
        """Return children in snapshot order; unknown parents raise KeyError.

        Args:
            plant_name: Exact parent plant identity; an absent parent is an error rather
                than an empty result.

        Returns:
            Immediate child sections in snapshot order; an existing empty plant yields
            an empty tuple.

        Raises:
            KeyError: The requested saved identity or required catalog member does not
                exist.
        """
        if plant_name not in self.plants:
            raise KeyError(plant_name)
        return tuple(
            section for section in self.sections if section.plant_name == plant_name
        )

    def lines_in(self, section: SectionKey) -> tuple[LineKey, ...]:
        """Distinguish an empty known section from an absent or stale selection.

        Args:
            section: Complete parent plant/section identity from the hierarchy snapshot.

        Returns:
            Immediate child lines in snapshot order; an existing empty section yields an
            empty tuple.

        Raises:
            KeyError: The requested saved identity or required catalog member does not
                exist.
        """
        if section not in self.sections:
            raise KeyError(section)
        return tuple(line for line in self.lines if line.section == section)

    def stations_in(self, line: LineKey) -> tuple[StationKey, ...]:
        """Filter by full ancestry, retaining exact station identifiers and order.

        Args:
            line: Complete parent plant/section/line identity from the hierarchy
                snapshot.

        Returns:
            Stations matching the complete parent ancestry in snapshot order, possibly
            empty.

        Raises:
            KeyError: The requested saved identity or required catalog member does not
                exist.
        """
        if line not in self.lines:
            raise KeyError(line)
        return tuple(
            station
            for station in self.work.stations
            if (station.plant_name, station.section_name, station.line_name)
            == (line.plant_name, line.section_name, line.line_name)
        )
