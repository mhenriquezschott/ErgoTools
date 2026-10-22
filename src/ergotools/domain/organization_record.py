"""Typed optional organization records, separate from hierarchy identities.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

import math
from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class OrganizationKind(StrEnum):
    """Stable original entity names; translated labels never establish identity."""

    # Plant entity; its key is the plant identity.
    PLANT = "Plant"
    # Section entity; its key includes the owning plant.
    SECTION = "Section"
    # Line entity; its key includes plant and section.
    LINE = "Line"
    # Station entity; its key includes plant, section and line.
    STATION = "Station"
    # Project-wide shift entity, independent of station ancestry.
    SHIFT = "Shift"


# Optional organization fields and editor kinds; recurring shifts deliberately
# exclude dated incident/event records. Units are defined on OrganizationRecord.
ORGANIZATION_FIELDS: dict[str, tuple[tuple[str, str], ...]] = {
    "Plant": (
        ("description", ("text")),
        (("location"), ("line")),
        (("type"), ("line")),
        (("area"), ("number")),
        (("start_time"), ("line")),
        (("end_time"), ("line")),
        (("operational_hours"), ("number")),
        (("production_capacity"), ("number")),
        (("opening_date"), ("date")),
        (("years_of_operation"), ("number")),
    ),
    ("Section"): (
        (("description"), ("text")),
        (("location"), ("line")),
        (("capacity"), ("number")),
        (("area"), ("number")),
        (("creation_date"), ("date")),
    ),
    ("Line"): (
        (("description"), ("text")),
        (("location"), ("line")),
        (("products"), ("line")),
        (("creation_date"), ("date")),
    ),
    ("Station"): (
        (("location"), ("line")),
        (("cycle_time"), ("number")),
        (("capacity"), ("number")),
        (("creation_date"), ("date")),
    ),
    ("Shift"): (
        (("description"), ("text")),
        (("start_time"), ("line")),
        (("end_time"), ("line")),
        (("shift_type"), ("line")),
        (("tasks_performed"), ("text")),
        (("product_output"), ("number")),
        (("downtime"), ("number")),
        (("notes"), ("text")),
    ),
}


@dataclass(frozen=True, slots=True)
class OrganizationRecord:
    """Exact ancestry and typed optional reference fields.

    Numeric fields retain the reference field's meaning/unit, e.g. cycle_time seconds,
    downtime hours and daily operational_hours in decimal hours (0-24, whole minutes).
    No label-based conversion is implied for generic capacity/area fields whose
    reference units are absent. Organization dates are canonical ISO calendar dates.

    Attributes:
        kind: Stable assessment model identity; displayed tool names are localized
            separately.
        keys: Exact entity ancestry tuple; shifts are project-wide and therefore have a
            one-part key.
        attributes: Ordered unique optional fields from ORGANIZATION_FIELDS; numeric
            units retain the reference field meaning.
    """

    kind: OrganizationKind
    keys: tuple[str, ...]
    attributes: tuple[tuple[str, str | float | None], ...] = ()

    def __post_init__(self) -> None:
        """Reject ambiguous keys/fields and nonfinite numeric metadata.

        Args:
            None. Dataclass construction supplies the fields documented on
            OrganizationRecord.

        Returns:
            None. Construction validates this record before publishing it. Snapshot
            keys, attributes as immutable tuples on the new frozen instance.

        Raises:
            ValueError: Organization kind requires an explicit identity. Organization
                identifiers require complete ancestry. Unknown or duplicate organization
                field. Organization numbers must be finite. Organization descriptions
                must be text. Dates require canonical ISO dates; operational hours
                require a daily duration representable in whole minutes.
        """
        if not isinstance(self.kind, OrganizationKind):
            raise ValueError("Organization kind requires an explicit identity.")
        object.__setattr__(self, "keys", tuple(self.keys))
        object.__setattr__(self, "attributes", tuple(self.attributes))
        count = {
            OrganizationKind.PLANT: 1,
            OrganizationKind.SECTION: 2,
            OrganizationKind.LINE: 3,
            OrganizationKind.STATION: 4,
            OrganizationKind.SHIFT: 1,
        }[self.kind]
        if len(self.keys) != count or any(
            not isinstance(k, str) or not k.strip() for k in self.keys
        ):
            raise ValueError("Organization identifiers require complete ancestry.")
        fields = dict(ORGANIZATION_FIELDS[self.kind.value])
        seen: set[str] = set()
        for name, value in self.attributes:
            if name not in fields or name in seen:
                raise ValueError("Unknown or duplicate organization field.")
            seen.add(name)
            if value is None:
                continue
            if fields[name] == "number":
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                ):
                    raise ValueError("Organization numbers must be finite.")
            elif not isinstance(value, str):
                raise ValueError("Organization descriptions must be text.")
            if (
                fields[name] == "date"
                and value
                and (
                    not isinstance(value, str)
                    or date.fromisoformat(value).isoformat() != value
                )
            ):
                raise ValueError("Organization dates require ISO yyyy-MM-dd.")
            if name == "operational_hours" and (
                not isinstance(value, (int, float))
                or not 0 <= value <= 24
                or value != round(value * 60) / 60
            ):
                raise ValueError(
                    "Operational hours require whole minutes from 0 to 24 hours."
                )
